"""S-25d (Proposal 033) — parity_check consumer-safety for the ungated per-series block.

The S-25d render block is NON-PIPE; parity_check must stay blind to it and still
extract exactly the deployment gates from the Phase-2 pipe table. The DFR/"ECB deposit
rate" label is the F8 collision risk a pipe form would trigger — these tests lock the
non-pipe block as inert.
"""
from __future__ import annotations

from scripts.data.parity_check import extract_prose_tiers
from scripts.data.gate_eval import render_table

# Minimal Phase-2 prose gate table (pipe form) carrying all 8 deployment-gate labels.
_TABLE = """\
| Gate | Value | Tier | Threshold Band | Data Source | Staleness (days) |
|---|---|---|---|---|---|
| vix | 18.0 | **GREEN** | x | live | 1 |
| hormuz | Open | **GREEN** | x | cached | — |
| brent | 70.0 | **GREEN** | x | live | 1 |
| ecb | 2.0 | **GREEN** | x | cached | — |
| us payrolls | 150 | **GREEN** | x | live | 30 |
| eur_usd | 1.08 | **GREEN** | x | live | 1 |
| tariff | Low | **GREEN** | x | cached | — |
| stoxx600_vs_50wk_ma | 5.0 | **GREEN** | x | live | 1 |
"""

# The S-25d non-pipe block, INCLUDING the DFR/"ECB deposit rate" label (the F8 collision risk).
_BLOCK = """\

**Data Confidence — ungated core series:**
- US CPI — GREEN (18d)
- ECB deposit rate — GREEN (18d)
- US unemployment — GREEN (20d)
- Euro-area HICP — GREEN (50d)
"""

_EIGHT = {"vix", "hormuz", "brent", "ecb", "us_payrolls", "eur_usd", "tariff", "stoxx600_vs_50wk_ma"}


def _write(tmp_path, text):
    p = tmp_path / "session.md"
    p.write_text(text, encoding="utf-8")
    return p


def test_table_alone_yields_exactly_eight_gates(tmp_path):
    assert set(extract_prose_tiers(_write(tmp_path, _TABLE)).keys()) == _EIGHT


def test_block_is_inert_table_plus_block_equals_table_alone(tmp_path):
    # DoD#4 — true collision oracle: the block adds no gate_id and overwrites no tier
    # (tiers[gate_id]=tier overwrites on duplicate, so a bare count of 8 would mask a collision).
    table_only = extract_prose_tiers(_write(tmp_path, _TABLE))
    with_block = extract_prose_tiers(_write(tmp_path, _TABLE + _BLOCK))
    assert with_block == table_only


def test_block_alone_yields_zero_gates(tmp_path):
    assert extract_prose_tiers(_write(tmp_path, _BLOCK)) == {}


def test_real_rendered_output_with_block_yields_zero_gates(tmp_path):
    # DoD#4 ownership — exercise the REAL render_table bytes, not a hand-written block.
    report = {
        "gates": {},
        "Market_Risk_Tier": "GREEN",
        "Data_Confidence_Tier": "RED",
        "gates_yml_sha256": "x",
        "snapshot_sha256": "y",
        "data_confidence_series": [
            {"series_id": "DFR", "label": "ECB deposit rate", "staleness_days": 18, "tier": "GREEN"},
            {"series_id": "CPIAUCSL", "label": "US CPI", "staleness_days": 18, "tier": "GREEN"},
        ],
    }
    real = render_table(report, fmt="markdown")
    assert extract_prose_tiers(_write(tmp_path, real)) == {}


def test_real_render_with_block_round_trips_to_exactly_eight(tmp_path):
    # DoD#4/#7 REALITY CHECK — parse the VERBATIM render_table bytes (gate-id row labels like
    # "us_payrolls", PLUS the non-pipe ungated block) and assert EXACTLY the 8 deployment gate-IDs.
    # A human-label fixture (e.g. "us payrolls") masked that the real render emits "us_payrolls",
    # which was absent from _PROSE_LABEL_TO_GATE_ID — this test reflects the real output.
    def _gr(tier):
        return {
            "value": 1.0, "tier": tier, "threshold_band": "x",
            "source_series_id": None, "staleness_days": 1, "data_source": "live",
        }
    report = {
        "gates": {g: _gr("GREEN") for g in _EIGHT},
        "Market_Risk_Tier": "GREEN",
        "Data_Confidence_Tier": "RED",
        "gates_yml_sha256": "x",
        "snapshot_sha256": "y",
        "data_confidence_series": [
            {"series_id": "DFR", "label": "ECB deposit rate", "staleness_days": 18, "tier": "GREEN"},
            {"series_id": "CPIAUCSL", "label": "US CPI", "staleness_days": 18, "tier": "GREEN"},
            {"series_id": "UNRATE", "label": "US unemployment", "staleness_days": 20, "tier": "GREEN"},
        ],
    }
    md = render_table(report, fmt="markdown")
    assert set(extract_prose_tiers(_write(tmp_path, md)).keys()) == _EIGHT


def test_leading_whitespace_block_line_still_not_a_gate(tmp_path):
    # Adversarial (R1-L10) — parity_check does line.strip() BEFORE startswith("|");
    # an indented bullet must still not parse as a gate row.
    indented = _TABLE + "\n    - ECB deposit rate — GREEN (18d)\n"
    assert extract_prose_tiers(_write(tmp_path, indented)) == extract_prose_tiers(_write(tmp_path, _TABLE))


def test_every_deployment_gate_id_self_maps_in_prose_label_table():
    # CLASS-GUARD (Challenger delta-L4): render_table emits each gate-ID verbatim as col-0
    # (e.g. "us_payrolls"), so EVERY gates.yml deployment_gate name MUST self-map in
    # _PROSE_LABEL_TO_GATE_ID — else that gate's verbatim render row silently drops from
    # parity extraction (the 8-vs-7 us_payrolls miscount). Sourced from gates.yml (the
    # authoritative gate set evaluate_gates/render_table use), NOT a hardcoded list, so a
    # FUTURE gate with an underscore/multi-word id is covered, not just today's instance.
    import yaml
    from scripts.data.gate_eval import GATES_PATH
    from scripts.data.parity_check import _PROSE_LABEL_TO_GATE_ID
    gates = yaml.safe_load(GATES_PATH.read_text(encoding="utf-8"))
    gate_ids = set(gates["deployment_gates"])
    # Non-vacuity (test-the-guard): a misderived/empty gate set must not pass trivially.
    assert gate_ids >= _EIGHT, f"deployment_gates derivation looks wrong: {sorted(gate_ids)}"
    for gate_id in gate_ids:
        assert _PROSE_LABEL_TO_GATE_ID.get(gate_id) == gate_id, (
            f"deployment gate {gate_id!r} is not self-mapped in _PROSE_LABEL_TO_GATE_ID; "
            "its verbatim render row would silently drop from parity extraction "
            "(parity_check would under-count the deployment gates)."
        )
