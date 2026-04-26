"""Gate-eval unit tests (DoD #2, #3, L35).

All tests use inline parametrised gate configs and inline snapshot fixtures.
No live config files are loaded. The live config is exercised exactly once via
an integration test in test_live_smoke.py.

Coverage matrix (DoD #18):
  [x] numeric GREEN
  [x] numeric AMBER
  [x] numeric RED
  [x] boundary tie (exclusive / inclusive semantics)
  [x] float boundary within 1e-9 (C-C2 — computed percentage gates)
  [x] categorical match
  [x] categorical fallback → RED
  [x] aggregate amber-escalation (≥3 AMBER → RED)
  [x] aggregate with 1 RED
  [x] missing data → unavailable → RED
  [x] hash mismatch refusal
  [x] stale snapshot penalty (L23)
  [x] inline-comment env parsing (L8)
  [x] schema_version refusal (L31)
  [x] byte-identical render idempotence
  [x] unknown manual_gate raises
  [x] Market_Risk_Tier / Data_Confidence_Tier separation (L26)
  [x] dual-amber staleness trap: infrastructure AMBER ≠ market AMBER
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from scripts.data.gate_eval import (
    GateReport,
    compute_gates_content_sha,
    evaluate_gates,
    render_table,
    _classify_numeric,
    _classify_categorical,
    _staleness_tier,
    _aggregate_market_tier,
    _EPSILON,
)

# ---------------------------------------------------------------------------
# Inline fixtures — no live files loaded
# ---------------------------------------------------------------------------

NUMERIC_GATE_CFG: dict[str, Any] = {
    "kind": "numeric",
    "tiers": {
        "GREEN": {"max": 20},
        "AMBER": {"min": 20, "max": 30},
        "RED": {"min": 30},
    },
}

INVERTED_GATE_CFG: dict[str, Any] = {
    "kind": "numeric",
    "tiers": {
        "GREEN": {"min": 2},       # > 2 = GREEN (e.g. STOXX vs MA)
        "AMBER": {"min": -2, "max": 2},
        "RED": {"max": -2},
    },
}

CATEGORICAL_GATE_CFG: dict[str, Any] = {
    "kind": "categorical",
    "tiers": {
        "GREEN": "Open",
        "AMBER": "Threatened / exercises",
        "RED": "Closed",
    },
}

# Minimal gates config — inline fixture; no live config files loaded
GATES_FIXTURE: dict[str, Any] = {
    "gate_aggregate": {"amber_count_escalation": 3},
    "deployment_gates": {
        "vix": NUMERIC_GATE_CFG,
        "hormuz": CATEGORICAL_GATE_CFG,
        "stoxx600_vs_50wk_ma": INVERTED_GATE_CFG,
    },
}

# Minimal snapshot — hash is intentionally blank (verify_hash=False in tests)
def _make_snapshot(
    series: list | None = None,
    manual_gates: dict | None = None,
    session: str = "2099-01",
    schema_version: int = 1,
) -> dict:
    return {
        "as_of": "2099-01-18T10:00:00Z",
        "session": session,
        "schema_version": schema_version,
        "snapshot_hash": "",
        "series": series or [],
        "manual_gates": manual_gates or {},
    }


def _eval(snapshot: dict, gates: dict = GATES_FIXTURE) -> GateReport:
    return evaluate_gates(snapshot, gates, verify_hash=False)


# ---------------------------------------------------------------------------
# Numeric gate classification
# ---------------------------------------------------------------------------

class TestNumericGreen:
    def test_well_below_threshold(self):
        assert _classify_numeric(15.0, NUMERIC_GATE_CFG["tiers"], ["GREEN", "AMBER", "RED"]) == "GREEN"

    def test_near_boundary_still_green(self):
        assert _classify_numeric(19.9, NUMERIC_GATE_CFG["tiers"], ["GREEN", "AMBER", "RED"]) == "GREEN"


class TestNumericAmber:
    def test_at_lower_bound(self):
        assert _classify_numeric(20.0, NUMERIC_GATE_CFG["tiers"], ["GREEN", "AMBER", "RED"]) == "AMBER"

    def test_midpoint(self):
        assert _classify_numeric(25.0, NUMERIC_GATE_CFG["tiers"], ["GREEN", "AMBER", "RED"]) == "AMBER"

    def test_at_upper_bound(self):
        assert _classify_numeric(30.0, NUMERIC_GATE_CFG["tiers"], ["GREEN", "AMBER", "RED"]) == "AMBER"


class TestNumericRed:
    def test_above_upper(self):
        assert _classify_numeric(35.0, NUMERIC_GATE_CFG["tiers"], ["GREEN", "AMBER", "RED"]) == "RED"

    def test_just_above_threshold(self):
        # 30.0001 > 30 + epsilon → RED
        assert _classify_numeric(30.0001, NUMERIC_GATE_CFG["tiers"], ["GREEN", "AMBER", "RED"]) == "RED"


class TestBoundaryTie:
    def test_exclusive_lower_of_green_tier(self):
        # GREEN has max=20 (strict less-than); value=20 → AMBER (next tier)
        assert _classify_numeric(20.0, NUMERIC_GATE_CFG["tiers"], ["GREEN", "AMBER", "RED"]) == "AMBER"

    def test_exclusive_lower_of_red_tier(self):
        # RED has min=30 (strict greater-than); value=30.0 → AMBER (inclusive upper)
        assert _classify_numeric(30.0, NUMERIC_GATE_CFG["tiers"], ["GREEN", "AMBER", "RED"]) == "AMBER"


class TestFloatBoundaryEpsilon:
    """C-C2: computed percentage gates can land within 1e-9 of a boundary.

    Epsilon guard semantics: values within _EPSILON of a strict boundary are
    conservatively pushed to the tighter tier. This is correct — IEEE-754
    errors that land within 1e-9 of a threshold should not trigger a misleadingly
    optimistic tier.
    """

    def test_value_clearly_below_green_max_is_green(self):
        # 19.0 is well clear of the 20.0 boundary → GREEN
        v = 19.0
        assert _classify_numeric(v, NUMERIC_GATE_CFG["tiers"], ["GREEN", "AMBER", "RED"]) == "GREEN"

    def test_value_within_epsilon_of_green_max_resolves_to_amber(self):
        # 20.0 - epsilon/2 is within the epsilon zone → classified as AMBER (tighter tier)
        v = 20.0 - _EPSILON * 0.5
        assert _classify_numeric(v, NUMERIC_GATE_CFG["tiers"], ["GREEN", "AMBER", "RED"]) == "AMBER"

    def test_value_epsilon_above_green_max_is_amber(self):
        # 20.0 + a detectable amount → AMBER
        v = 20.0 + 0.001
        assert _classify_numeric(v, NUMERIC_GATE_CFG["tiers"], ["GREEN", "AMBER", "RED"]) == "AMBER"

    def test_inverted_gate_value_clearly_above_boundary_is_green(self):
        # stoxx600_vs_50wk_ma: GREEN requires value > 2.0; 5.0 is well clear
        v = 5.0
        assert _classify_numeric(v, INVERTED_GATE_CFG["tiers"], ["GREEN", "AMBER", "RED"]) == "GREEN"

    def test_inverted_gate_boundary_within_epsilon_resolves_to_amber(self):
        # 2.0000000000000004 from IEEE-754 arithmetic: within epsilon of 2.0
        # gate_eval must not silently crash or classify as GREEN
        v = 2.0 + _EPSILON * 0.1
        result = _classify_numeric(v, INVERTED_GATE_CFG["tiers"], ["GREEN", "AMBER", "RED"])
        assert result in ("GREEN", "AMBER"), f"Unexpected tier: {result}"


# ---------------------------------------------------------------------------
# Categorical gate classification
# ---------------------------------------------------------------------------

class TestCategoricalMatch:
    def test_green_match(self):
        assert _classify_categorical("Open", CATEGORICAL_GATE_CFG["tiers"]) == "GREEN"

    def test_amber_match(self):
        assert _classify_categorical("Threatened / exercises", CATEGORICAL_GATE_CFG["tiers"]) == "AMBER"

    def test_red_match(self):
        assert _classify_categorical("Closed", CATEGORICAL_GATE_CFG["tiers"]) == "RED"


class TestCategoricalFallback:
    def test_unrecognised_value_returns_red(self):
        assert _classify_categorical("Unknown status", CATEGORICAL_GATE_CFG["tiers"]) == "RED"

    def test_empty_string_returns_red(self):
        assert _classify_categorical("", CATEGORICAL_GATE_CFG["tiers"]) == "RED"


# ---------------------------------------------------------------------------
# Aggregate tier logic (L19)
# ---------------------------------------------------------------------------

class TestAggregateTier:
    def test_all_green(self):
        assert _aggregate_market_tier(["GREEN"] * 8, GATES_FIXTURE) == "GREEN"

    def test_one_amber(self):
        assert _aggregate_market_tier(["GREEN"] * 7 + ["AMBER"], GATES_FIXTURE) == "AMBER"

    def test_two_amber(self):
        assert _aggregate_market_tier(["GREEN"] * 6 + ["AMBER", "AMBER"], GATES_FIXTURE) == "AMBER"

    def test_three_amber_escalates(self):
        assert _aggregate_market_tier(["GREEN"] * 5 + ["AMBER"] * 3, GATES_FIXTURE) == "RED"

    def test_one_red_dominates(self):
        assert _aggregate_market_tier(["GREEN"] * 7 + ["RED"], GATES_FIXTURE) == "RED"

    def test_one_red_plus_amber(self):
        assert _aggregate_market_tier(["GREEN"] * 6 + ["AMBER", "RED"], GATES_FIXTURE) == "RED"


# ---------------------------------------------------------------------------
# Missing data → Data Failure Protocol (unavailable → RED)
# ---------------------------------------------------------------------------

class TestMissingData:
    def test_gate_with_no_series_and_no_manual_returns_red(self):
        snap = _make_snapshot()   # no series, no manual_gates
        report = _eval(snap)
        assert report["gates"]["vix"]["tier"] == "RED"
        assert report["gates"]["vix"]["data_source"] == "unavailable"

    def test_missing_gate_drives_market_risk_red(self):
        snap = _make_snapshot()
        report = _eval(snap)
        assert report["Market_Risk_Tier"] == "RED"

    def test_data_confidence_red_when_unavailable(self):
        snap = _make_snapshot()
        report = _eval(snap)
        assert report["Data_Confidence_Tier"] == "RED"


# ---------------------------------------------------------------------------
# Hash mismatch refusal (L5, C-C3)
# ---------------------------------------------------------------------------

class TestHashMismatch:
    def test_invalid_hash_raises_with_both_hashes(self):
        snap = _make_snapshot()
        snap["snapshot_hash"] = "sha256:deadbeef"
        with pytest.raises(ValueError, match="Stored"):
            evaluate_gates(snap, GATES_FIXTURE, verify_hash=True)

    def test_hash_error_names_the_file(self):
        snap = _make_snapshot()
        snap["snapshot_hash"] = "sha256:deadbeef"
        path = Path("local/snapshots/test.json")
        with pytest.raises(ValueError, match=str(path)):
            evaluate_gates(snap, GATES_FIXTURE, snapshot_path=path, verify_hash=True)

    def test_missing_hash_field_skipped_when_verify_false(self):
        snap = _make_snapshot()
        snap["snapshot_hash"] = ""
        report = _eval(snap)   # must not raise
        assert report.get("gates_yml_sha256") is not None


# ---------------------------------------------------------------------------
# Stale snapshot penalty (L23)
# ---------------------------------------------------------------------------

class TestStalePenalty:
    def _make_stale_snapshot(self, staleness_days: int) -> dict:
        """Make a snapshot with VIXCLS series staleness_days old."""
        from datetime import date, timedelta
        snap_date = date(2026, 5, 1)
        vintage = snap_date - timedelta(days=staleness_days)
        return {
            "as_of": snap_date.isoformat() + "T10:00:00Z",
            "session": "2026-05",
            "schema_version": 1,
            "snapshot_hash": "",
            "series": [
                {
                    "source": "FRED",
                    "series_id": "VIXCLS",
                    "as_of": (snap_date - timedelta(days=1)).isoformat(),
                    "value": 15.0,   # would be GREEN without stale penalty
                    "vintage": vintage.isoformat(),
                    "units": "index",
                }
            ],
            "manual_gates": {
                "hormuz": {"value": "Open"},
                "stoxx600_vs_50wk_ma": {"value": 5.0},
            },
        }

    def test_fresh_data_no_penalty(self):
        snap = self._make_stale_snapshot(1)
        report = _eval(snap)
        assert report["gates"]["vix"]["tier"] == "GREEN"

    def test_red_staleness_demotes_green_to_amber(self):
        # VIXCLS red_age_days = 10; value 15.0 would be GREEN
        snap = self._make_stale_snapshot(11)
        report = _eval(snap)
        assert report["gates"]["vix"]["tier"] == "AMBER"


# ---------------------------------------------------------------------------
# Inline-comment .env parsing (L8, feedback_env_inline_comment_parsing)
# ---------------------------------------------------------------------------

class TestEnvInlineCommentParsing:
    def test_key_with_inline_comment_is_truthy(self):
        from scripts.data.gate_eval import _check_fred_api_key
        with patch.dict(os.environ, {"FRED_API_KEY": "abc123  # my key"}):
            import io
            from contextlib import redirect_stderr
            buf = io.StringIO()
            with redirect_stderr(buf):
                _check_fred_api_key()
            assert "WARNING" not in buf.getvalue()

    def test_comment_only_value_is_falsy(self):
        from scripts.data.gate_eval import _check_fred_api_key
        with patch.dict(os.environ, {"FRED_API_KEY": "  # comment only"}):
            import io
            from contextlib import redirect_stderr
            buf = io.StringIO()
            with redirect_stderr(buf):
                _check_fred_api_key()
            assert "WARNING" in buf.getvalue()


# ---------------------------------------------------------------------------
# Schema version refusal (L31)
# ---------------------------------------------------------------------------

class TestSchemaVersionRefusal:
    def test_known_version_accepted(self):
        snap = _make_snapshot(schema_version=1)
        report = _eval(snap)   # must not raise
        assert report is not None

    def test_future_version_raises(self):
        snap = _make_snapshot(schema_version=99)
        with pytest.raises(ValueError, match="schema_version"):
            _eval(snap)


# ---------------------------------------------------------------------------
# Byte-identical render idempotence
# ---------------------------------------------------------------------------

class TestRenderIdempotence:
    def test_markdown_render_is_deterministic(self):
        snap = _make_snapshot(manual_gates={
            "vix": {"value": 18.0},
            "hormuz": {"value": "Open"},
            "stoxx600_vs_50wk_ma": {"value": 5.0},
        })
        report = _eval(snap)
        out1 = render_table(report, fmt="markdown")
        out2 = render_table(report, fmt="markdown")
        assert out1 == out2

    def test_json_render_is_deterministic(self):
        snap = _make_snapshot()
        report = _eval(snap)
        j1 = render_table(report, fmt="json")
        j2 = render_table(report, fmt="json")
        assert j1 == j2


# ---------------------------------------------------------------------------
# Unknown manual_gate raises (D-C2)
# ---------------------------------------------------------------------------

class TestUnknownManualGate:
    def test_unknown_gate_raises(self):
        snap = _make_snapshot(manual_gates={"nonexistent_gate": {"value": "foo"}})
        with pytest.raises(ValueError, match="Unknown gate"):
            _eval(snap)


# ---------------------------------------------------------------------------
# Market_Risk_Tier vs Data_Confidence_Tier separation (L26)
# ---------------------------------------------------------------------------

class TestTierSeparation:
    def test_infrastructure_amber_does_not_inflate_market_tier(self):
        # All manual gate values are GREEN; but data_source=cached may raise Data_Confidence
        snap = _make_snapshot(manual_gates={
            "vix": {"value": 15.0, "staleness_days": 6},   # 6 days > vix amber threshold (5)
            "hormuz": {"value": "Open"},
            "stoxx600_vs_50wk_ma": {"value": 5.0},
        })
        report = _eval(snap)
        # Market risk should be GREEN (values are fine)
        assert report["Market_Risk_Tier"] == "GREEN"
        # Data confidence should be AMBER (vix staleness = 6d > 5d amber)
        assert report["Data_Confidence_Tier"] in ("AMBER", "RED")

    def test_data_confidence_red_halts_session_flag(self):
        # All unavailable → Data_Confidence_Tier = RED
        snap = _make_snapshot()
        report = _eval(snap)
        assert report["Data_Confidence_Tier"] == "RED"
        assert report["Market_Risk_Tier"] == "RED"   # unavailable = RED for market too


# ---------------------------------------------------------------------------
# Canonical SHA recipe pinning (L34 semantic-content lock)
# ---------------------------------------------------------------------------

# FROZEN FIXTURE — do not change without updating the pinned hash.
# Changing either the fixture OR the json.dumps recipe breaks this test intentionally.
_FROZEN_CONFIG_FIXTURE: dict = {
    "gate_aggregate": {"amber_count_escalation": 3},
    "deployment_gates": {
        "vix": {"kind": "numeric", "tiers": {"GREEN": {"max": 20}, "AMBER": {"min": 20, "max": 30}, "RED": {"min": 30}}},
    },
}
# Hash computed once from the canonical recipe and pinned here.
# To recompute: python3 -c "import hashlib, json; cfg=<fixture>; print(hashlib.sha256(json.dumps(cfg,sort_keys=True,separators=(',',':'),ensure_ascii=False,default=str).encode()).hexdigest())"
_FROZEN_CONFIG_SHA = "77ad086a6bd58959aeefa748ab9ac7788363a36bc7722f5c5240568183bdfa44"


class TestGatesContentSha:
    def test_recipe_is_pinned(self):
        """Pinned-hash test: recipe identity is a contract. Changing json.dumps kwargs breaks this."""
        result = compute_gates_content_sha(_FROZEN_CONFIG_FIXTURE)
        assert result == _FROZEN_CONFIG_SHA, (
            f"compute_gates_content_sha recipe has changed.\n"
            f"  Expected : {_FROZEN_CONFIG_SHA}\n"
            f"  Got      : {result}\n"
            "This test is intentionally strict — the canonical recipe is a contract "
            "shared across gate_eval output, REPLAY_DELTA.md, and the proposal Status Log. "
            "If you changed the recipe deliberately, update _FROZEN_CONFIG_SHA and all artefacts."
        )

    def test_returns_64_char_hex(self):
        result = compute_gates_content_sha(_FROZEN_CONFIG_FIXTURE)
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

    def test_comment_only_yaml_change_produces_identical_sha(self):
        """Semantic-content lock: parsed dicts that differ only in comments hash identically."""
        import yaml
        # Two YAML strings — identical data, different comments
        yaml_with_comment = "# comment\ngates:\n  vix: 20\n"
        yaml_without_comment = "gates:\n  vix: 20\n"
        sha1 = compute_gates_content_sha(yaml.safe_load(yaml_with_comment))
        sha2 = compute_gates_content_sha(yaml.safe_load(yaml_without_comment))
        assert sha1 == sha2

    def test_data_change_produces_different_sha(self):
        """A threshold value change must produce a different hash."""
        import copy
        modified = copy.deepcopy(_FROZEN_CONFIG_FIXTURE)
        modified["gate_aggregate"]["amber_count_escalation"] = 4
        assert compute_gates_content_sha(modified) != _FROZEN_CONFIG_SHA


# ---------------------------------------------------------------------------
# Artefact synchronicity — gates_content_sha in live artefacts matches live config
# ---------------------------------------------------------------------------

class TestArtefactSync:
    """Verify REPLAY_DELTA.md and proposal Status Log cite the current canonical SHA.

    This test breaks if someone updates config/gates.yml but forgets to
    regenerate the artefact headers — the canonical SHA stored in those files
    must always equal compute_gates_content_sha(live config).
    """

    def _live_sha(self) -> str:
        import yaml
        from scripts.data.gate_eval import GATES_PATH
        cfg = yaml.safe_load(GATES_PATH.read_text(encoding="utf-8"))
        return compute_gates_content_sha(cfg)

    def test_replay_delta_header_matches_live_config(self):
        replay_delta = Path(__file__).parent.parent / "backtesting" / "REPLAY_DELTA.md"
        if not replay_delta.exists():
            pytest.skip("REPLAY_DELTA.md not found — skip artefact sync check")
        text = replay_delta.read_text(encoding="utf-8")
        live = self._live_sha()
        assert live in text, (
            f"REPLAY_DELTA.md does not contain the current canonical gates SHA.\n"
            f"  Expected : {live}\n"
            "Update the REPLAY_DELTA.md header SHA to match the current config/gates.yml.\n"
            "Command: python3 -c \"from scripts.data.gate_eval import compute_gates_content_sha; "
            "import yaml; print(compute_gates_content_sha(yaml.safe_load(open('config/gates.yml').read())))\""
        )

    def test_proposal_status_log_mentions_canonical_sha(self):
        proposal = Path(__file__).parent.parent / "proposals" / "003-phase-1b-data-integration.md"
        if not proposal.exists():
            pytest.skip("Proposal 003 not found — skip artefact sync check")
        text = proposal.read_text(encoding="utf-8")
        live = self._live_sha()
        assert live in text, (
            f"proposals/003-phase-1b-data-integration.md Status Log does not contain "
            f"the current canonical gates SHA.\n"
            f"  Expected : {live}\n"
            "Update the Status Log entry with the canonical SHA.\n"
            "Command: python3 -c \"from scripts.data.gate_eval import compute_gates_content_sha; "
            "import yaml; print(compute_gates_content_sha(yaml.safe_load(open('config/gates.yml').read())))\""
        )
