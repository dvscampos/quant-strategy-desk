"""HttpClient unit tests: TTL + DDP fallback + skip_cache semantics.

All tests exercise the real HttpClient.get() entry-point with monkeypatched
requests.Session.get and cache-file mtime manipulation. No live network calls.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Callable

import pytest
import requests

from scripts.data.http_client import HttpClient, HttpError


def test_fresh_within_ttl_serves_cache_no_network(tmp_path: Path):
    """Fresh cache (within TTL) → served from disk; network NOT called."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    client = HttpClient(cache_dir=cache_dir, min_interval=0)

    # Pre-write a cache file for a known (url, params) pair.
    cache_path = client._cache_path("GET", "https://example.com/api", {"key": "value"})
    cache_path.write_text("cached_body", encoding="utf-8")
    # Set mtime to "now" — the cache is fresh.
    os.utime(cache_path, (time.time(), time.time()))

    # Monkeypatch session.get to track calls and raise if called.
    call_count = 0
    def mock_get(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        raise AssertionError("session.get should not be called when cache is fresh")

    client.session.get = mock_get

    # Call get() with max_age_days=10 (cache is fresh, age=0 < 10 days).
    body = client.get("https://example.com/api", params={"key": "value"}, max_age_days=10)

    assert body == "cached_body"
    assert call_count == 0, "Network was called despite fresh cache"


def test_over_age_triggers_refetch(tmp_path: Path):
    """Over-age cache (older than TTL) → network called, new body returned."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    client = HttpClient(cache_dir=cache_dir, min_interval=0)

    # Pre-write a cache file.
    cache_path = client._cache_path("GET", "https://example.com/api", {"key": "value"})
    cache_path.write_text("old_body", encoding="utf-8")
    # Set mtime to 20 days ago.
    old_time = time.time() - (20 * 86400)
    os.utime(cache_path, (old_time, old_time))

    # Monkeypatch session.get to return a fake 200 response with new body.
    def mock_get(*args, **kwargs):
        resp = SimpleNamespace()
        resp.status_code = 200
        resp.text = "new_body"
        resp.headers = {}
        resp.raise_for_status = lambda: None
        return resp

    client.session.get = mock_get

    # Call get() with max_age_days=10 (cache age=20 > 10 → refetch).
    body = client.get("https://example.com/api", params={"key": "value"}, max_age_days=10)

    assert body == "new_body", "Should return the new body from network"
    # Cache file should also be updated.
    assert cache_path.read_text(encoding="utf-8") == "new_body"


def test_refetch_failure_after_expiry_returns_stale_fallback(tmp_path: Path):
    """Re-fetch fails after expiry → over-age cache returned as DDP STALE fallback."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    client = HttpClient(cache_dir=cache_dir, min_interval=0, max_retries=3)

    # Pre-write a cache file.
    cache_path = client._cache_path("GET", "https://example.com/api", {"key": "value"})
    cache_path.write_text("old_body", encoding="utf-8")
    # Set mtime to 20 days ago.
    old_time = time.time() - (20 * 86400)
    os.utime(cache_path, (old_time, old_time))

    # Monkeypatch session.get to raise RequestException.
    def mock_get(*args, **kwargs):
        raise requests.RequestException("Network error")

    client.session.get = mock_get

    # Call get() with max_age_days=10 (cache age=20 > 10 → refetch).
    # Refetch fails → should return the old cached body (DDP fallback).
    body = client.get("https://example.com/api", params={"key": "value"}, max_age_days=10)

    assert body == "old_body", "DDP STALE fallback should return over-age cache"


def test_429_over_cap_after_expiry_returns_stale_fallback(tmp_path: Path):
    """429 over-cap after expiry → over-age cache returned as DDP STALE fallback."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    client = HttpClient(cache_dir=cache_dir, min_interval=0, max_retry_after=60.0)

    # Pre-write a cache file.
    cache_path = client._cache_path("GET", "https://example.com/api", {"key": "value"})
    cache_path.write_text("old_body", encoding="utf-8")
    # Set mtime to 20 days ago.
    old_time = time.time() - (20 * 86400)
    os.utime(cache_path, (old_time, old_time))

    # Monkeypatch session.get to return a 429 response with Retry-After > cap.
    def mock_get(*args, **kwargs):
        resp = SimpleNamespace()
        resp.status_code = 429
        resp.headers = {"Retry-After": "3600"}
        resp.text = ""
        resp.raise_for_status = lambda: None
        return resp

    client.session.get = mock_get

    # Call get() with max_age_days=10 (cache age=20 > 10 → refetch).
    # 429 cap exceeded → should return the old cached body (DDP fallback).
    body = client.get("https://example.com/api", params={"key": "value"}, max_age_days=10)

    assert body == "old_body", "DDP STALE fallback should return over-age cache on 429-cap"


def test_skip_cache_suppresses_fresh_serve_and_fallback(tmp_path: Path):
    """skip_cache=True → fresh cache NOT served, failure raises (no DDP fallback)."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    client = HttpClient(cache_dir=cache_dir, min_interval=0, skip_cache=True, max_retries=3)

    # Pre-write a fresh cache file.
    cache_path = client._cache_path("GET", "https://example.com/api", {"key": "value"})
    cache_path.write_text("cached_body", encoding="utf-8")
    os.utime(cache_path, (time.time(), time.time()))

    # Monkeypatch session.get to raise RequestException.
    def mock_get(*args, **kwargs):
        raise requests.RequestException("Network error")

    client.session.get = mock_get

    # Call get() with max_age_days=10. With skip_cache=True:
    # - Fresh cache is NOT served (cache_available=False)
    # - Fetch fails → raises HttpError (no DDP fallback)
    with pytest.raises(HttpError, match="failed after 3 attempts"):
        client.get("https://example.com/api", params={"key": "value"}, max_age_days=10)
