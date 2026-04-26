"""Golden hash determinism test.

Two writes of the same payload (same session, as_of, observations) must
produce byte-identical output with an identical snapshot_hash.

Also verifies that the SnapshotWriter.verify() roundtrip succeeds, and that
mutating any field invalidates the hash.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.data.provider import SeriesObservation
from scripts.data.snapshot import SnapshotWriter

_OBSERVATIONS = [
    SeriesObservation("FRED", "CPIAUCSL", "2026-02-28", 319.082, "2026-04-11", "index_1982_84_eq_100"),
    SeriesObservation("ECB",  "DFR",      "2026-04-17", 2.00,    "2026-04-17", "pct"),
]
_SESSION = "2026-05"
_AS_OF = "2026-05-17T10:00:00Z"

# Golden hash — computed once, pinned. If this test fails, the canonical
# JSON spec or the hash algorithm has changed (both require a new proposal).
_GOLDEN_HASH = "sha256:773dbea35f3e45cf739870938c193a0d955253eb90d50eaadf5c102e787c6447"


def test_golden_hash(tmp_path):
    w = SnapshotWriter(out_dir=tmp_path)
    p = w.write(session=_SESSION, as_of=_AS_OF, observations=_OBSERVATIONS)
    import json
    payload = json.loads(p.read_bytes())
    assert payload["snapshot_hash"] == _GOLDEN_HASH, (
        f"Hash changed — canonical JSON spec or algorithm may have drifted. "
        f"Got: {payload['snapshot_hash']}"
    )


def test_deterministic_across_two_writes(tmp_path):
    w = SnapshotWriter(out_dir=tmp_path)
    p1 = w.write(session=_SESSION, as_of=_AS_OF, observations=_OBSERVATIONS)
    p2 = w.write(session=_SESSION, as_of=_AS_OF, observations=_OBSERVATIONS, filename="dup.json")
    assert p1.read_bytes() == p2.read_bytes()


def test_verify_roundtrip(tmp_path):
    w = SnapshotWriter(out_dir=tmp_path)
    p = w.write(session=_SESSION, as_of=_AS_OF, observations=_OBSERVATIONS)
    assert SnapshotWriter.verify(p)


def test_verify_fails_on_tampered_value(tmp_path):
    import json
    w = SnapshotWriter(out_dir=tmp_path)
    p = w.write(session=_SESSION, as_of=_AS_OF, observations=_OBSERVATIONS)
    payload = json.loads(p.read_bytes())
    payload["series"][0]["value"] = 999.0   # tamper
    p.write_bytes(SnapshotWriter._canonical_bytes(payload) + b"\n")
    assert not SnapshotWriter.verify(p)


def test_as_of_format():
    """as_of must match the locked schema format: YYYY-MM-DDTHH:MM:SSZ."""
    import re
    payload = SnapshotWriter.build_payload(
        session=_SESSION, as_of=_AS_OF, observations=_OBSERVATIONS
    )
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", payload["as_of"]), (
        f"as_of format mismatch: {payload['as_of']!r}"
    )
