"""Live smoke test — requires PYTEST_LIVE=1 and FRED_API_KEY env vars.

Run with:
    PYTEST_LIVE=1 python3 -m pytest tests/test_live_smoke.py -v

This test is explicitly excluded from normal CI. It fetches real data from
FRED and ECB, writes a real snapshot, and verifies the hash.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

LIVE = os.getenv("PYTEST_LIVE") == "1"
pytestmark = pytest.mark.skipif(not LIVE, reason="Set PYTEST_LIVE=1 to run live tests")

ROOT = Path(__file__).parent.parent


def test_live_fetch_and_snapshot(tmp_path):
    """Fetch real FRED + ECB data, write snapshot, verify hash and schema."""
    import yaml
    from scripts.data.http_client import HttpClient
    from scripts.data.providers.fred import FredProvider
    from scripts.data.providers.ecb import EcbProvider
    from scripts.data.snapshot import SnapshotWriter

    gates = yaml.safe_load((ROOT / "config" / "gates.yml").read_text())
    retry = gates["data_staleness"]["retry"]

    http = HttpClient(
        cache_dir=tmp_path / ".cache",
        min_interval=1.0,
        max_retries=retry["max_attempts"],
        backoff_base=retry["backoff_seconds_base"],
        max_retry_after=retry["max_retry_after_seconds"],
    )
    fred = FredProvider(http)
    ecb = EcbProvider(http)

    series_cfg = gates["data_staleness"]["series"]
    observations = []
    for series_id, cfg in series_cfg.items():
        source = cfg["source"]
        provider = fred if source == "FRED" else ecb
        obs = provider.fetch(series_id)
        print(f"  {obs.source} {obs.series_id}: {obs.value} {obs.units} "
              f"(as_of={obs.as_of}, vintage={obs.vintage})")
        observations.append(obs)

    from datetime import datetime, timezone
    as_of = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    writer = SnapshotWriter(out_dir=tmp_path)
    path = writer.write(session="live-smoke", as_of=as_of, observations=observations)

    import json
    payload = json.loads(path.read_bytes())

    # Schema assertions
    assert payload["session"] == "live-smoke"
    assert payload["snapshot_hash"].startswith("sha256:")
    assert len(payload["series"]) == len(series_cfg)
    for obs_dict in payload["series"]:
        assert obs_dict["source"] in ("FRED", "ECB")
        assert isinstance(obs_dict["value"], float)
        assert obs_dict["vintage"] != ""

    # Hash verification
    assert SnapshotWriter.verify(path), "Snapshot hash verification failed"

    # Determinism: build the same payload again, hashes must match
    payload2 = SnapshotWriter.build_payload(
        session="live-smoke", as_of=as_of, observations=observations
    )
    assert payload["snapshot_hash"] == payload2["snapshot_hash"]

    print(f"\nSnapshot written to: {path}")
    print(f"Hash: {payload['snapshot_hash']}")
