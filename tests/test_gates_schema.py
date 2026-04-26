"""Test B′ — gates.yml shape validation.

Asserts that gates.yml has the required structure and that numeric gate
tiers are contiguous (no gaps, no overlaps). This catches YAML typos and
structural drift before any provider or eval code runs.
"""

import yaml
from pathlib import Path

ROOT = Path(__file__).parent.parent
GATES = yaml.safe_load((ROOT / "config" / "gates.yml").read_text(encoding="utf-8"))

REQUIRED_DEPLOYMENT_GATES = [
    "hormuz", "brent", "ecb", "us_payrolls", "vix",
    "eur_usd", "tariff", "stoxx600_vs_50wk_ma",
]
REQUIRED_TOP_KEYS = [
    "version", "deployment_gates", "vix_emergency",
    "cash_floor", "data_staleness", "gate_aggregate",
]
REQUIRED_STALENESS_SERIES = [
    "CPIAUCSL", "UNRATE", "PAYEMS", "VIXCLS",
    "DFR", "ICP.M.U2.N.000000.4.ANR", "EXR.D.USD.EUR.SP00.A",
]


def test_top_level_keys():
    for key in REQUIRED_TOP_KEYS:
        assert key in GATES, f"Missing top-level key: {key!r}"


def test_deployment_gate_keys():
    gates = GATES["deployment_gates"]
    for name in REQUIRED_DEPLOYMENT_GATES:
        assert name in gates, f"Missing deployment gate: {name!r}"


def test_each_gate_has_tiers():
    for name, gate in GATES["deployment_gates"].items():
        assert "tiers" in gate, f"Gate {name!r} missing 'tiers'"
        assert "kind" in gate, f"Gate {name!r} missing 'kind'"
        tiers = gate["tiers"]
        assert set(tiers.keys()) >= {"GREEN", "AMBER", "RED"}, (
            f"Gate {name!r} tiers must include GREEN, AMBER, RED"
        )


def test_numeric_tier_contiguity():
    """For numeric gates, assert no gaps or overlaps between tiers."""
    for name, gate in GATES["deployment_gates"].items():
        if gate["kind"] != "numeric":
            continue
        tiers = gate["tiers"]
        _assert_contiguous(name, tiers, list(tiers.keys()))

    # also check vix_emergency
    ve = GATES["vix_emergency"]
    _assert_contiguous("vix_emergency", ve["tiers"], ["GREEN", "AMBER", "RED", "EMERGENCY"])


def _assert_contiguous(gate_name: str, tiers: dict, order: list) -> None:
    """Assert numeric tier ranges are contiguous — no gaps, no overlaps.

    Handles both ascending (lower=better, e.g. VIX: GREEN.max → AMBER.min)
    and descending (higher=better, e.g. payrolls: AMBER.max → GREEN.min)
    directions by detecting from the GREEN tier's shape.
    """
    numeric = [
        (name, tiers[name].get("min"), tiers[name].get("max"))
        for name in order
        if isinstance(tiers[name], dict)
    ]
    if len(numeric) < 2:
        return

    # Detect direction from the GREEN (first) tier:
    # ascending  → GREEN has only max  (e.g. VIX:       GREEN={max:20})
    # descending → GREEN has only min  (e.g. payrolls:  GREEN={min:150})
    green_name, green_lo, green_hi = numeric[0]
    ascending = green_lo is None and green_hi is not None

    if ascending:
        # Walk GREEN→…→RED: each tier's max must equal the next tier's min.
        for i in range(len(numeric) - 1):
            cur_name, _, cur_hi = numeric[i]
            nxt_name, nxt_lo, _ = numeric[i + 1]
            assert cur_hi is not None, (
                f"Gate {gate_name!r}: tier {cur_name!r} has no upper bound (ascending) "
                f"— gap before {nxt_name!r}"
            )
            assert nxt_lo is not None, (
                f"Gate {gate_name!r}: tier {nxt_name!r} has no lower bound (ascending) "
                f"— gap after {cur_name!r}"
            )
            assert cur_hi == nxt_lo, (
                f"Gate {gate_name!r}: boundary mismatch (ascending) between "
                f"{cur_name!r} max={cur_hi} and {nxt_name!r} min={nxt_lo}"
            )
    else:
        # Descending: each tier's min must equal the previous tier's max.
        # Walk GREEN→AMBER→RED: GREEN.min == AMBER.max; AMBER.min == RED.max.
        for i in range(len(numeric) - 1):
            cur_name, cur_lo, _ = numeric[i]
            nxt_name, _, nxt_hi = numeric[i + 1]
            assert cur_lo is not None, (
                f"Gate {gate_name!r}: tier {cur_name!r} has no lower bound (descending) "
                f"— gap before {nxt_name!r}"
            )
            assert nxt_hi is not None, (
                f"Gate {gate_name!r}: tier {nxt_name!r} has no upper bound (descending) "
                f"— gap after {cur_name!r}"
            )
            assert cur_lo == nxt_hi, (
                f"Gate {gate_name!r}: boundary mismatch (descending) between "
                f"{cur_name!r} min={cur_lo} and {nxt_name!r} max={nxt_hi}"
            )


def test_vix_emergency_keys():
    ve = GATES["vix_emergency"]
    assert "tiers" in ve
    assert set(ve["tiers"].keys()) == {"GREEN", "AMBER", "RED", "EMERGENCY"}


def test_cash_floor_tiers():
    tiers = GATES["cash_floor"]["tiers"]
    assert len(tiers) == 3
    labels = [t["label"] for t in tiers]
    assert "Micro-NAV" in labels
    assert "Standard" in labels
    assert "Scaled" in labels


def test_staleness_series_present():
    series = GATES["data_staleness"]["series"]
    for s in REQUIRED_STALENESS_SERIES:
        assert s in series, f"Missing staleness series: {s!r}"


def test_staleness_series_have_thresholds():
    for name, cfg in GATES["data_staleness"]["series"].items():
        assert "source" in cfg, f"Series {name!r} missing 'source'"
        assert "amber_age_days" in cfg, f"Series {name!r} missing 'amber_age_days'"
        assert "red_age_days" in cfg, f"Series {name!r} missing 'red_age_days'"
        assert isinstance(cfg["amber_age_days"], int), f"Series {name!r} amber_age_days must be int"
        assert isinstance(cfg["red_age_days"], int), f"Series {name!r} red_age_days must be int"
        assert cfg["amber_age_days"] < cfg["red_age_days"], (
            f"Series {name!r}: amber_age_days must be < red_age_days"
        )


def test_retry_config():
    retry = GATES["data_staleness"]["retry"]
    assert "max_attempts" in retry
    assert "backoff_seconds_base" in retry
    assert "max_retry_after_seconds" in retry
    assert isinstance(retry["max_attempts"], int)
    assert retry["max_retry_after_seconds"] <= 300, "Cap must be sane (≤ 300s)"
