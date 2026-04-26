"""SnapshotWriter — canonical JSON + SHA256.

Canonicalisation rule (locked, hand-verifiable):
  * sorted keys
  * UTF-8
  * compact separators: (",", ":")
  * no trailing whitespace
  * single trailing LF terminator

The file on disk IS the canonical form. To re-verify the hash by hand:

    jq -cS . snapshot.json \
      | sed 's/"snapshot_hash":"sha256:[^"]*"/"snapshot_hash":""/' \
      | tr -d '\n' | sha256sum

Anything more elaborate than that means the hash is not hand-verifiable.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

from scripts.data.provider import SeriesObservation


@dataclass(frozen=True)
class SnapshotWriter:
    out_dir: Path

    @staticmethod
    def _canonical_bytes(payload: dict) -> bytes:
        return json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")

    @classmethod
    def compute_hash(cls, payload: dict) -> str:
        clone = dict(payload)
        clone["snapshot_hash"] = ""
        return "sha256:" + hashlib.sha256(cls._canonical_bytes(clone)).hexdigest()

    @classmethod
    def build_payload(
        cls,
        *,
        session: str,
        as_of: str,
        observations: Iterable[SeriesObservation],
    ) -> dict:
        payload = {
            "as_of": as_of,
            "session": session,
            "snapshot_hash": "",
            "series": [o.to_dict() for o in observations],
        }
        payload["snapshot_hash"] = cls.compute_hash(payload)
        return payload

    def write(
        self,
        *,
        session: str,
        as_of: str,
        observations: Iterable[SeriesObservation],
        filename: Optional[str] = None,
    ) -> Path:
        payload = self.build_payload(
            session=session, as_of=as_of, observations=observations
        )
        self.out_dir.mkdir(parents=True, exist_ok=True)
        path = self.out_dir / (filename or f"{session}.json")
        path.write_bytes(self._canonical_bytes(payload) + b"\n")
        return path

    @classmethod
    def verify(cls, path: Path) -> bool:
        payload = json.loads(path.read_bytes())
        claimed = payload.get("snapshot_hash", "")
        recomputed = cls.compute_hash(payload)
        return claimed == recomputed
