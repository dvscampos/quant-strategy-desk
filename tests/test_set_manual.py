"""Tests for set-manual CLI command (Proposal 034 Leg B)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.data.snapshot import SnapshotWriter


@pytest.fixture
def minimal_snapshot(tmp_path: Path) -> tuple[Path, dict]:
    """Build a minimal valid snapshot via SnapshotWriter.build_payload."""
    from scripts.data.provider import SeriesObservation

    obs = SeriesObservation(
        series_id="VIXCLS",
        value=88888.0,
        vintage="2099-06-25",
        as_of="2099-06-25",
        source="FRED",
        units="index",
    )
    payload = SnapshotWriter.build_payload(
        session="test-session", as_of="2099-06-25T10:00:00Z", observations=[obs]
    )
    snapshot_path = tmp_path / "snapshots" / "test-session.json"
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_bytes(SnapshotWriter._canonical_bytes(payload) + b"\n")
    return snapshot_path, payload


def test_inject_round_trips_and_reverifies(minimal_snapshot):
    """inject_manual_gates returns a new payload with valid hash + immutable input."""
    _, original = minimal_snapshot
    manual_gates = {"hormuz": {"value": "Open", "as_of": "2099-06-25"}}

    new_payload = SnapshotWriter.inject_manual_gates(original, manual_gates)

    # Hash round-trips
    assert SnapshotWriter.compute_hash(new_payload) == new_payload["snapshot_hash"]
    # Input immutability
    assert "manual_gates" not in original
    # New payload has manual_gates
    assert new_payload["manual_gates"] == manual_gates


def test_inject_does_not_touch_build_payload_golden(tmp_path: Path):
    """Importing inject_manual_gates does not change build_payload behavior."""
    from scripts.data.provider import SeriesObservation

    obs = SeriesObservation(
        series_id="VIXCLS",
        value=88888.0,
        vintage="2099-06-25",
        as_of="2099-06-25",
        source="FRED",
        units="index",
    )
    payload = SnapshotWriter.build_payload(
        session="test", as_of="2099-06-25T10:00:00Z", observations=[obs]
    )
    # build_payload output has no manual_gates
    assert "manual_gates" not in payload


def test_set_manual_cli_happy_path(minimal_snapshot, tmp_path: Path, monkeypatch):
    """set-manual CLI writes manual_gates with valid hash and no schema_version."""
    from scripts.data import cli

    snapshot_path, _ = minimal_snapshot
    snapshots_dir = snapshot_path.parent
    monkeypatch.setattr(cli, "SNAPSHOTS_DIR", snapshots_dir)

    argv = [
        "set-manual",
        "--session",
        "test-session",
        "--gate",
        "hormuz=Open",
        "--gate",
        "ecb=Hold or cut",
    ]
    with patch.object(sys, "argv", ["cli.py"] + argv):
        cli.main()

    # Reload snapshot
    updated = json.loads(snapshot_path.read_bytes())
    assert "manual_gates" in updated
    assert updated["manual_gates"]["hormuz"]["value"] == "Open"
    assert updated["manual_gates"]["ecb"]["value"] == "Hold or cut"
    assert "as_of" in updated["manual_gates"]["hormuz"]
    # No schema_version key added (DoD #10 — must not bump)
    assert "schema_version" not in updated
    # Hash is valid
    assert SnapshotWriter.compute_hash(updated) == updated["snapshot_hash"]


def test_set_manual_rejects_numeric_gate_key(minimal_snapshot, tmp_path: Path, monkeypatch):
    """set-manual rejects a numeric gate key (WRITE-side strict)."""
    from scripts.data import cli

    snapshot_path, _ = minimal_snapshot
    snapshots_dir = snapshot_path.parent
    monkeypatch.setattr(cli, "SNAPSHOTS_DIR", snapshots_dir)

    # Read original bytes
    original_bytes = snapshot_path.read_bytes()

    argv = ["set-manual", "--session", "test-session", "--gate", "brent=88888"]
    with patch.object(sys, "argv", ["cli.py"] + argv), pytest.raises(SystemExit) as exc:
        cli.main()

    assert exc.value.code != 0
    # File unchanged
    assert snapshot_path.read_bytes() == original_bytes


def test_set_manual_rejects_unknown_gate(minimal_snapshot, tmp_path: Path, monkeypatch):
    """set-manual rejects an unknown gate."""
    from scripts.data import cli

    snapshot_path, _ = minimal_snapshot
    snapshots_dir = snapshot_path.parent
    monkeypatch.setattr(cli, "SNAPSHOTS_DIR", snapshots_dir)

    original_bytes = snapshot_path.read_bytes()

    argv = ["set-manual", "--session", "test-session", "--gate", "nonsense=Open"]
    with patch.object(sys, "argv", ["cli.py"] + argv), pytest.raises(SystemExit) as exc:
        cli.main()

    assert exc.value.code != 0
    assert snapshot_path.read_bytes() == original_bytes


def test_set_manual_rejects_bad_categorical_value(minimal_snapshot, tmp_path: Path, monkeypatch):
    """set-manual rejects a bad categorical value (wrong case)."""
    from scripts.data import cli

    snapshot_path, _ = minimal_snapshot
    snapshots_dir = snapshot_path.parent
    monkeypatch.setattr(cli, "SNAPSHOTS_DIR", snapshots_dir)

    original_bytes = snapshot_path.read_bytes()

    argv = ["set-manual", "--session", "test-session", "--gate", "hormuz=open"]
    with patch.object(sys, "argv", ["cli.py"] + argv), pytest.raises(SystemExit) as exc:
        cli.main()

    assert exc.value.code != 0
    assert snapshot_path.read_bytes() == original_bytes


def test_set_manual_refuses_missing_snapshot(tmp_path: Path, monkeypatch):
    """set-manual exits if snapshot does not exist."""
    from scripts.data import cli

    snapshots_dir = tmp_path / "snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(cli, "SNAPSHOTS_DIR", snapshots_dir)

    argv = ["set-manual", "--session", "missing", "--gate", "hormuz=Open"]
    with patch.object(sys, "argv", ["cli.py"] + argv), pytest.raises(SystemExit) as exc:
        cli.main()

    assert exc.value.code != 0
    # No file created
    assert not (snapshots_dir / "missing.json").exists()


def test_set_manual_refuses_tampered_snapshot(minimal_snapshot, tmp_path: Path, monkeypatch):
    """set-manual refuses to write if snapshot hash is invalid (refuse-on-tamper)."""
    from scripts.data import cli

    snapshot_path, _ = minimal_snapshot
    snapshots_dir = snapshot_path.parent
    monkeypatch.setattr(cli, "SNAPSHOTS_DIR", snapshots_dir)

    # Corrupt the snapshot by changing a value
    snapshot = json.loads(snapshot_path.read_bytes())
    snapshot["series"][0]["value"] = 99999.0  # Break the hash
    snapshot_path.write_bytes(json.dumps(snapshot).encode("utf-8") + b"\n")

    original_bytes = snapshot_path.read_bytes()

    argv = ["set-manual", "--session", "test-session", "--gate", "hormuz=Open"]
    with patch.object(sys, "argv", ["cli.py"] + argv), pytest.raises(SystemExit) as exc:
        cli.main()

    assert exc.value.code != 0
    # File unchanged
    assert snapshot_path.read_bytes() == original_bytes
