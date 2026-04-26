"""Shared HTTP client: exponential backoff + on-disk response cache + rate limit.

Used by every DataProvider. Providers do not call `requests` directly and do
not implement their own backoff — that logic lives here so behaviour is
uniform across FRED, ECB, and whatever lands in later tiers.

Cache keys hash the (method, url, params) tuple. Live fetches write to
data/.http_cache/; the directory is gitignored. vcrpy handles test replay at
a different layer.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Optional

import requests


class HttpError(RuntimeError):
    pass


@dataclass
class HttpClient:
    cache_dir: Path
    min_interval: float = 0.0         # seconds between requests (rate limit)
    max_retries: int = 3
    backoff_base: float = 1.5          # seconds
    max_retry_after: float = 60.0      # L19: cap Retry-After header; abort if exceeded
    timeout: float = 30.0
    skip_cache: bool = False           # set True in tests to bypass on-disk cache
    session: requests.Session = field(default_factory=requests.Session)
    _last_request_at: float = 0.0

    def _cache_path(self, method: str, url: str, params: Optional[Mapping]) -> Path:
        key = json.dumps(
            {"m": method.upper(), "u": url, "p": dict(params or {})},
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        digest = hashlib.sha256(key).hexdigest()
        return self.cache_dir / f"{digest}.json"

    def _respect_rate_limit(self) -> None:
        if self.min_interval <= 0:
            return
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)

    def get(
        self,
        url: str,
        *,
        params: Optional[Mapping] = None,
        headers: Optional[Mapping] = None,
        use_cache: bool = True,
    ) -> str:
        cache_path = self._cache_path("GET", url, params)
        if use_cache and not self.skip_cache and cache_path.exists():
            return cache_path.read_text(encoding="utf-8")

        last_exc: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            self._respect_rate_limit()
            try:
                resp = self.session.get(
                    url, params=params, headers=headers, timeout=self.timeout
                )
                self._last_request_at = time.monotonic()
            except requests.RequestException as exc:
                last_exc = exc
                if attempt == self.max_retries:
                    break
                time.sleep(self.backoff_base ** attempt)
                continue

            if resp.status_code == 429:
                retry_after = float(resp.headers.get("Retry-After", 0))
                if retry_after > self.max_retry_after:
                    # L19: cap exceeded — abort immediately, do not retry.
                    raise HttpError(
                        f"HTTP 429 from {url}: Retry-After={retry_after:.0f}s exceeds "
                        f"cap={self.max_retry_after:.0f}s — aborting, trigger DDP fallback"
                    )
                time.sleep(retry_after or self.backoff_base ** attempt)
                continue
            if resp.status_code >= 500:
                last_exc = HttpError(f"HTTP {resp.status_code} from {url}")
                if attempt == self.max_retries:
                    break
                time.sleep(self.backoff_base ** attempt)
                continue
            try:
                resp.raise_for_status()
            except requests.HTTPError as exc:
                last_exc = exc
                if attempt == self.max_retries:
                    break
                time.sleep(self.backoff_base ** attempt)
                continue

            body = resp.text
            if use_cache:
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                cache_path.write_text(body, encoding="utf-8")
            return body
        raise HttpError(f"GET {url} failed after {self.max_retries} attempts: {last_exc}")
