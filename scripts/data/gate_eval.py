"""Gate evaluator — snapshot → GateReport.

PROJECT_ROOT resolved via sentinel-file walk-up (CLAUDE.md, max 5 levels).
Raises ProjectRootNotFound if the sentinel is not found.

Canonical consumer of config/gates.yml (Proposal 003, Phase 1B).
After Phase 1B, this module is the ONLY evaluator; agents and SKILL.md
consume its pre-built table — they do not re-derive thresholds from recall.

Boundary semantics (encoded in gates.yml and enforced here):
  green_below / red_above notation in the schema comment:
    GREEN tier: value < green.max  (strict less-than)
    AMBER tier: amber.min <= value <= amber.max  (both inclusive)
    RED tier:   value > red.min    (strict greater-than)
  Equality at a boundary bubbles to the tighter (more cautious) tier.

Float-boundary note: computed percentage gates (e.g. stoxx600_vs_50wk_ma)
  can produce values like 2.0000000000000004 due to IEEE-754 arithmetic.
  Boundary tests use a 1e-9 epsilon guard — see _classify_numeric.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import date
from pathlib import Path
from typing import Literal, TypedDict

import yaml

# ---------------------------------------------------------------------------
# Project root resolution (L33, C-C1)
# ---------------------------------------------------------------------------


class ProjectRootNotFound(Exception):
    """Raised when sentinel file 'CLAUDE.md' is not found within max_levels parents."""


def _find_project_root(start: Path, sentinel: str = "CLAUDE.md", max_levels: int = 5) -> Path:
    current = start.resolve()
    for _ in range(max_levels + 1):
        if (current / sentinel).exists():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent
    raise ProjectRootNotFound(
        f"Sentinel file '{sentinel}' not found within {max_levels} parent levels of {start}. "
        "Ensure you are running from inside the project tree."
    )


PROJECT_ROOT = _find_project_root(Path(__file__).parent)
GATES_PATH = PROJECT_ROOT / "config" / "gates.yml"

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

Tier = Literal["GREEN", "AMBER", "RED"]
DataSource = Literal["live", "cached", "unavailable"]
KNOWN_MAX_SCHEMA_VERSION = 1


class GateResult(TypedDict):
    value: float | str | None
    tier: Tier
    threshold_band: str
    source_series_id: str | None
    staleness_days: int | None
    data_source: DataSource


class GateReport(TypedDict):
    gates: dict[str, GateResult]
    Market_Risk_Tier: Tier
    Data_Confidence_Tier: Tier
    gates_yml_sha256: str
    snapshot_sha256: str


# ---------------------------------------------------------------------------
# Series-to-gate mapping
# ---------------------------------------------------------------------------

# Maps snapshot series_id → deployment gate name.
# Only series with automated FRED/ECB providers are listed here.
# Gates absent from this mapping must be supplied via snapshot.manual_gates.
SERIES_TO_GATE: dict[str, str] = {
    "VIXCLS": "vix",
    "PAYEMS": "us_payrolls",
    "EXR.D.USD.EUR.SP00.A": "eur_usd",
    "DCOILBRENTEU": "brent",
}

# Per-gate staleness thresholds (amber/red age in days).
# Must stay consistent with gates.yml data_staleness.series.
_GATE_STALENESS: dict[str, dict[str, int]] = {
    "vix": {"amber": 5, "red": 10},
    "us_payrolls": {"amber": 45, "red": 60},
    "eur_usd": {"amber": 5, "red": 10},
    "brent": {"amber": 5, "red": 10},
}


# ---------------------------------------------------------------------------
# Numeric classification (L12, C-C2)
# ---------------------------------------------------------------------------

_EPSILON = 1e-9


def _classify_numeric(value: float, tiers: dict, order: list[str]) -> Tier:
    """Classify a numeric value against tier bands.

    Boundary convention (strict on open ends, inclusive on closed ends):
      - tier with only max:  value < max   (strict; equality → next tier)
      - tier with min+max:   min <= value <= max  (both inclusive)
      - tier with only min:  value > min   (strict; equality → next tier)

    IEEE-754 epsilon guard: values within 1e-9 of a boundary are resolved
    to the tighter tier (AMBER over GREEN, RED over AMBER).
    """
    for tier_name in order:
        tier = tiers.get(tier_name)
        if not isinstance(tier, dict):
            continue
        lo = tier.get("min")
        hi = tier.get("max")
        if lo is None and hi is not None:
            # Only upper bound — GREEN-style (value strictly below threshold)
            if value < hi - _EPSILON:
                return tier_name
        elif lo is not None and hi is not None:
            # Both bounds — AMBER-style (inclusive)
            if lo - _EPSILON <= value <= hi + _EPSILON:
                return tier_name
        elif lo is not None and hi is None:
            # Only lower bound — RED-style (value strictly above threshold)
            if value > lo + _EPSILON:
                return tier_name
    return order[-1]


def _classify_categorical(value: str, tiers: dict) -> Tier:
    for tier_name, label in tiers.items():
        if value == label:
            return tier_name
    return "RED"


def _staleness_tier(staleness_days: int | None, thresholds: dict | None) -> Tier:
    if staleness_days is None or thresholds is None:
        return "GREEN"
    if staleness_days >= thresholds.get("red", 999_999):
        return "RED"
    if staleness_days >= thresholds.get("amber", 999_999):
        return "AMBER"
    return "GREEN"


def _format_threshold_band(gate_cfg: dict) -> str:
    kind = gate_cfg.get("kind")
    if kind == "categorical":
        tiers = gate_cfg.get("tiers", {})
        return " / ".join(f"{k}: {v}" for k, v in tiers.items())
    tiers = gate_cfg.get("tiers", {})
    bands = []
    for t_name in ("GREEN", "AMBER", "RED"):
        t = tiers.get(t_name, {})
        if not isinstance(t, dict):
            continue
        lo, hi = t.get("min"), t.get("max")
        if lo is None and hi is not None:
            bands.append(f"{t_name}: < {hi}")
        elif lo is not None and hi is not None:
            bands.append(f"{t_name}: {lo}–{hi}")
        elif lo is not None and hi is None:
            bands.append(f"{t_name}: > {lo}")
    return " / ".join(bands)


# ---------------------------------------------------------------------------
# Schema validation (D-C2)
# ---------------------------------------------------------------------------


def _validate_schema(snapshot: dict, gates_config: dict) -> None:
    """Pre-evaluation schema validation.

    - Snapshot.manual_gates keys must all be known deployment gate names.
    - Gates absent from both series and manual_gates trigger Data Failure Protocol
      (treated as unavailable inside evaluate_gates, not raised here).
    - Schema version check: refuses if snapshot.schema_version > KNOWN_MAX.
    """
    schema_version = snapshot.get("schema_version", 1)
    if schema_version > KNOWN_MAX_SCHEMA_VERSION:
        raise ValueError(
            f"Snapshot schema_version {schema_version} exceeds known max "
            f"{KNOWN_MAX_SCHEMA_VERSION}. Upgrade gate_eval to handle this version."
        )

    known_gates = set(gates_config.get("deployment_gates", {}).keys())
    manual_gates = snapshot.get("manual_gates", {})
    unknown = set(manual_gates.keys()) - known_gates
    if unknown:
        raise ValueError(
            f"Unknown gate(s) in snapshot.manual_gates: {sorted(unknown)}. "
            f"Known gates: {sorted(known_gates)}"
        )


# ---------------------------------------------------------------------------
# Hash verification (L5, C-C3)
# ---------------------------------------------------------------------------


def _verify_snapshot_hash(snapshot: dict, path: Path) -> None:
    """Refuse evaluation if snapshot hash is invalid (L5).

    Prints both stored and actual hashes on mismatch (C-C3).
    """
    from scripts.data.snapshot import SnapshotWriter

    claimed = snapshot.get("snapshot_hash", "")
    actual = SnapshotWriter.compute_hash(snapshot)
    if claimed != actual:
        raise ValueError(
            f"Snapshot hash mismatch for {path}:\n"
            f"  Stored : {claimed}\n"
            f"  Actual : {actual}\n"
            "The snapshot file may have been modified. "
            "Re-fetch or restore from a known-good copy."
        )


# ---------------------------------------------------------------------------
# Aggregate tiers (L19)
# ---------------------------------------------------------------------------


def _aggregate_market_tier(market_tiers: list[Tier], gates_config: dict) -> Tier:
    """L19 lattice: 1 RED → portfolio RED; ≥N AMBER → portfolio RED; else AMBER/GREEN."""
    amber_threshold = gates_config.get("gate_aggregate", {}).get("amber_count_escalation", 3)
    n_red = market_tiers.count("RED")
    n_amber = market_tiers.count("AMBER")
    if n_red >= 1 or n_amber >= amber_threshold:
        return "RED"
    if n_amber >= 1:
        return "AMBER"
    return "GREEN"


# ---------------------------------------------------------------------------
# Canonical gates config hash (L34 semantic-content lock)
# ---------------------------------------------------------------------------


def compute_gates_content_sha(gates_config: dict) -> str:
    """Return the canonical SHA256 of a gates config dict.

    Recipe: json.dumps(config, sort_keys=True, separators=(",",":"),
                       ensure_ascii=False, default=str) → SHA256 hex.

    This is the single canonical recipe used by gate_eval output, the
    REPLAY_DELTA artefact, and the proposal Status Log. Changing the recipe
    breaks test_gate_eval.TestGatesContentSha.test_recipe_is_pinned.

    default=str handles YAML-parsed date objects (e.g. last_updated: 2026-04-23).
    """
    return hashlib.sha256(
        json.dumps(
            gates_config, sort_keys=True, separators=(",", ":"),
            ensure_ascii=False, default=str,
        ).encode()
    ).hexdigest()


# ---------------------------------------------------------------------------
# Main evaluator
# ---------------------------------------------------------------------------


def evaluate_gates(
    snapshot: dict,
    gates_config: dict,
    *,
    snapshot_path: Path | None = None,
    verify_hash: bool = True,
) -> GateReport:
    """Evaluate all deployment gates from snapshot + gates_config.

    Args:
        snapshot: Parsed snapshot JSON dict.
        gates_config: Parsed gates.yml dict.
        snapshot_path: Path used in error messages only (optional).
        verify_hash: Set False in unit tests with synthetic snapshots that
                     deliberately omit or stub the hash field.

    Returns:
        GateReport with per-gate results and aggregate tiers.
    """
    if verify_hash and snapshot.get("snapshot_hash"):
        _verify_snapshot_hash(snapshot, snapshot_path or Path("<in-memory>"))

    _validate_schema(snapshot, gates_config)

    deployment_gates = gates_config["deployment_gates"]

    # Build series_id → observation mapping from snapshot
    series_map: dict[str, dict] = {
        obs["series_id"]: obs for obs in snapshot.get("series", [])
    }
    manual_gates: dict[str, object] = snapshot.get("manual_gates", {})

    # Compute gates_yml_sha256 via canonical recipe (L34 semantic-content lock, L37 invariant).
    gates_yml_sha256 = compute_gates_content_sha(gates_config)

    snap_date_str = snapshot.get("as_of", "")[:10]
    try:
        snap_date = date.fromisoformat(snap_date_str) if snap_date_str else None
    except ValueError:
        snap_date = None

    gate_results: dict[str, GateResult] = {}
    market_tiers: list[Tier] = []
    data_staleness_tiers: list[Tier] = []

    for gate_name, gate_cfg in deployment_gates.items():
        kind = gate_cfg.get("kind")
        tiers = gate_cfg.get("tiers", {})

        value = None
        source_series_id = None
        staleness_days = None
        data_source: DataSource = "unavailable"

        # 1. Try automated series first
        for series_id, mapped_gate in SERIES_TO_GATE.items():
            if mapped_gate == gate_name and series_id in series_map:
                obs = series_map[series_id]
                value = obs["value"]
                source_series_id = series_id
                data_source = "live"
                if snap_date:
                    try:
                        vintage_date = date.fromisoformat(obs["vintage"][:10])
                        staleness_days = (snap_date - vintage_date).days
                    except (ValueError, KeyError):
                        staleness_days = None
                break

        # 2. Fall back to manual_gates
        if value is None and gate_name in manual_gates:
            mg = manual_gates[gate_name]
            if isinstance(mg, dict):
                value = mg.get("value")
                staleness_days = mg.get("staleness_days")
            else:
                value = mg
            data_source = "cached"

        threshold_band = _format_threshold_band(gate_cfg)

        # 3. Evaluate tier (unavailable → RED via Data Failure Protocol)
        if value is None:
            tier: Tier = "RED"
        elif kind == "categorical":
            tier = _classify_categorical(str(value), tiers)
        else:
            tier = _classify_numeric(float(value), tiers, ["GREEN", "AMBER", "RED"])
            # L23: stale penalty — force one tier worse when staleness = RED
            stale_t = _staleness_tier(staleness_days, _GATE_STALENESS.get(gate_name))
            if stale_t == "RED":
                if tier == "GREEN":
                    tier = "AMBER"
                elif tier == "AMBER":
                    tier = "RED"

        gate_results[gate_name] = GateResult(
            value=value,
            tier=tier,
            threshold_band=threshold_band,
            source_series_id=source_series_id,
            staleness_days=staleness_days,
            data_source=data_source,
        )

        market_tiers.append(tier)

        # Data confidence staleness (L26)
        if data_source == "unavailable":
            data_staleness_tiers.append("RED")
        else:
            data_staleness_tiers.append(
                _staleness_tier(staleness_days, _GATE_STALENESS.get(gate_name))
            )

    Market_Risk_Tier = _aggregate_market_tier(market_tiers, gates_config)

    # L26: Data_Confidence_Tier
    n_dc_red = data_staleness_tiers.count("RED")
    n_dc_amber = data_staleness_tiers.count("AMBER")
    if n_dc_red >= 1:
        Data_Confidence_Tier: Tier = "RED"
    elif n_dc_amber >= 1:
        Data_Confidence_Tier = "AMBER"
    else:
        Data_Confidence_Tier = "GREEN"

    snapshot_sha256 = snapshot.get("snapshot_hash", "")
    return GateReport(
        gates=gate_results,
        Market_Risk_Tier=Market_Risk_Tier,
        Data_Confidence_Tier=Data_Confidence_Tier,
        gates_yml_sha256=gates_yml_sha256,
        snapshot_sha256=snapshot_sha256,
    )


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------


def render_table(report: GateReport, fmt: Literal["markdown", "json"]) -> str:
    """Render a GateReport to markdown or JSON.

    Markdown output is byte-identical across runs for the same report
    (sort_keys=True, deterministic dict order).
    """
    if fmt == "json":
        return json.dumps(report, indent=2, default=str, sort_keys=True)

    snapshot_sha = report.get("snapshot_sha256", "")
    lines = [
        f"<!-- snapshot_sha256: {snapshot_sha} gates_content_sha256: {report['gates_yml_sha256']} -->",
        "",
        "| Gate | Value | Tier | Threshold Band | Data Source | Staleness (days) |",
        "|---|---|---|---|---|---|",
    ]
    for gate_name, result in report["gates"].items():
        tier_display = f"**{result['tier']}**"
        staleness = (
            str(result["staleness_days"])
            if result["staleness_days"] is not None
            else "—"
        )
        value_display = str(result["value"]) if result["value"] is not None else "—"
        lines.append(
            f"| {gate_name} | {value_display} | {tier_display} "
            f"| {result['threshold_band']} | {result['data_source']} | {staleness} |"
        )

    lines.extend(
        [
            "",
            f"**Market_Risk_Tier**: {report['Market_Risk_Tier']}",
            f"**Data_Confidence_Tier**: {report['Data_Confidence_Tier']}",
        ]
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI helper (called from scripts/data/cli.py)
# ---------------------------------------------------------------------------


def run_gate_eval(session: str, fmt: str, snapshot_path: Path | None = None) -> int:
    """Load snapshot → evaluate gates → print table. Returns exit code."""
    _check_fred_api_key()

    gates_config = yaml.safe_load(GATES_PATH.read_text(encoding="utf-8"))

    if snapshot_path is None:
        snapshot_path = PROJECT_ROOT / "local" / "snapshots" / f"{session}.json"

    if not snapshot_path.exists():
        print(
            f"ERROR: Snapshot not found: {snapshot_path}\n"
            "Run: python -m scripts.data fetch --session {session}\n"
            "If fetch fails, follow the Data Failure Protocol in docs/RISK_FRAMEWORK.md."
        )
        return 1

    snapshot = json.loads(snapshot_path.read_bytes())
    try:
        _verify_snapshot_hash(snapshot, snapshot_path)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1

    try:
        report = evaluate_gates(snapshot, gates_config, snapshot_path=snapshot_path, verify_hash=False)
    except ValueError as exc:
        print(f"ERROR during gate evaluation: {exc}")
        return 1

    print(render_table(report, fmt=fmt))  # type: ignore[arg-type]
    return 0


def _check_fred_api_key() -> None:
    """Strip inline comments before truthiness check (feedback_env_inline_comment_parsing)."""
    raw = os.environ.get("FRED_API_KEY", "")
    key = raw.split("#")[0].strip()
    if not key:
        print(
            "WARNING: FRED_API_KEY not set or empty. "
            "Gate evaluation can proceed from an existing snapshot, "
            "but live fetch will fail. Set FRED_API_KEY in .env to enable fetching.",
            file=sys.stderr,
        )
