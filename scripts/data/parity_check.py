"""Parity check: gate_eval output vs. prose Phase 2 table (DoD #11, L9, A-challenge).

Usage:
    python scripts/data/parity_check.py --session 2026-04 \\
        --against-prose local/brainstorms/2026-04.md

Exit codes:
    0 — All gate tiers match (or only same-tier rounding differences found).
    1 — One or more gate tier flips detected (gate_eval says GREEN, prose says AMBER, etc.)
    2 — Snapshot or config file missing / unreadable.

Failure criterion (A-challenge + B-condition, defined BEFORE implementation):
    A tier flip (gate A is GREEN in gate_eval output but AMBER in prose, or vice versa) = exit 1.
    Same-tier differences (different numeric display values, rounding) = logged only, exit 0.

IMPORTANT: A non-zero exit identifies a divergence but CANNOT distinguish
"gate_eval is wrong" from "prose is wrong". The operator must investigate the
root cause before resolving. Do NOT silently fix by editing either source.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Project root — resolved via gate_eval (single threshold-config consumer, DoD #14)
# ---------------------------------------------------------------------------

from scripts.data.gate_eval import PROJECT_ROOT, GATES_PATH

_ROOT = PROJECT_ROOT


def _gates_config() -> dict:
    import yaml
    return yaml.safe_load(GATES_PATH.read_text(encoding="utf-8"))


def _snapshot(session: str) -> dict:
    path = _ROOT / "local" / "snapshots" / f"{session}.json"
    if not path.exists():
        print(f"ERROR: Snapshot not found: {path}", file=sys.stderr)
        sys.exit(2)
    return json.loads(path.read_bytes())


# ---------------------------------------------------------------------------
# Prose extraction
# ---------------------------------------------------------------------------

# Maps prose gate labels (as they appear in the session markdown table) to gate IDs
_PROSE_LABEL_TO_GATE_ID: dict[str, str] = {
    "vix": "vix",
    "strait of hormuz": "hormuz",
    "hormuz": "hormuz",
    "brent": "brent",
    "brent crude": "brent",
    "ecb": "ecb",
    "ecb deposit rate": "ecb",
    "us payrolls": "us_payrolls",
    "payrolls": "us_payrolls",
    "eur/usd": "eur_usd",
    "eur_usd": "eur_usd",
    "tariff": "tariff",
    "us tariff": "tariff",
    "tariff severity": "tariff",
    "stoxx 600 vs 50w ma": "stoxx600_vs_50wk_ma",
    "stoxx 600": "stoxx600_vs_50wk_ma",
    "stoxx600": "stoxx600_vs_50wk_ma",
    "stoxx 600 vs 50wk ma": "stoxx600_vs_50wk_ma",
    "stoxx600_vs_50wk_ma": "stoxx600_vs_50wk_ma",
}

_TIER_PATTERN = re.compile(r"\*\*(GREEN|AMBER|RED)\*\*", re.IGNORECASE)

# Expected column headers for the deployment gate table (Gate | Value | Tier | …)
_EXPECTED_HEADERS = {"gate", "gate name", "signal"}

def extract_prose_tiers(prose_path: Path) -> dict[str, str]:
    """Extract {gate_id: tier} from the Phase 2 deployment gate table in prose.

    Splits each pipe-delimited row by '|' — robust to any number of columns.
    Expects Gate in column 0, Tier in column 2 (0-indexed after stripping outer pipes).
    Validates the header row to catch column-order drift early.
    """
    text = prose_path.read_text(encoding="utf-8")

    tiers: dict[str, str] = {}
    header_validated = False

    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        # Split on | and strip outer empty strings from leading/trailing pipes
        cols = [c.strip() for c in line.split("|")[1:-1]]
        if len(cols) < 3:
            continue

        # Skip separator rows (---|---|---)
        if all(set(c) <= set("-: ") for c in cols):
            continue

        # Validate header row — first non-separator pipe row should have "Gate" in col 0
        if not header_validated:
            if cols[0].lower() in _EXPECTED_HEADERS:
                header_validated = True
                # Optionally verify Tier is in column 2
                if len(cols) >= 3 and "tier" not in cols[2].lower():
                    print(
                        f"WARNING: Expected 'Tier' in column 2 of gate table header, "
                        f"got '{cols[2]}'. Column-order drift may cause incorrect parity results.",
                        file=sys.stderr,
                    )
            continue  # skip header row itself

        label = cols[0].lower()
        tier_col = cols[2]
        tier_match = _TIER_PATTERN.search(tier_col)
        if not tier_match:
            continue
        tier = tier_match.group(1).upper()
        gate_id = _PROSE_LABEL_TO_GATE_ID.get(label)
        if gate_id:
            tiers[gate_id] = tier

    return tiers


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------


def compare(
    eval_tiers: dict[str, str], prose_tiers: dict[str, str], session: str
) -> int:
    """Compare eval_tiers vs prose_tiers. Returns 0 (match) or 1 (tier flip)."""
    all_gates = sorted(set(eval_tiers) | set(prose_tiers))
    tier_flips = 0

    print(f"\nParity check — session {session}\n")
    print(f"{'Gate':<30} {'gate_eval':<12} {'Prose':<12} {'Result'}")
    print("-" * 70)

    for gate_id in all_gates:
        eval_t = eval_tiers.get(gate_id, "MISSING")
        prose_t = prose_tiers.get(gate_id, "MISSING")

        if eval_t == "MISSING" or prose_t == "MISSING":
            status = "SKIP (one side missing)"
        elif eval_t == prose_t:
            status = "OK"
        else:
            status = "TIER FLIP ⚠"
            tier_flips += 1

        print(f"{gate_id:<30} {eval_t:<12} {prose_t:<12} {status}")

    print("-" * 70)
    if tier_flips == 0:
        print("\n✅ Parity check PASSED — no tier flips detected.")
        return 0
    else:
        print(
            f"\n❌ Parity check FAILED — {tier_flips} tier flip(s) detected.\n"
            "A tier flip means gate_eval and the prose session file disagree on the tier.\n"
            "This does NOT automatically mean either is wrong — investigate root cause:\n"
            "  1. Check the snapshot values vs. the prose-recorded values.\n"
            "  2. Check if threshold config changed between session and evaluation.\n"
            "  3. If prose was wrong (agent recall error), document in REPLAY_DELTA.md.\n"
            "  4. If gate_eval is wrong (threshold bug), fix gate_eval and re-run.\n"
            "Do NOT silently edit either source to make them agree."
        )
        return 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Parity check: gate_eval vs prose Phase 2 table"
    )
    parser.add_argument("--session", required=True, help="Session slug YYYY-MM")
    parser.add_argument(
        "--against-prose",
        required=True,
        metavar="PATH",
        help="Path to the session markdown file (e.g. local/brainstorms/2026-04.md)",
    )
    args = parser.parse_args()

    prose_path = _ROOT / args.against_prose
    if not prose_path.exists():
        prose_path = Path(args.against_prose)
    if not prose_path.exists():
        print(f"ERROR: Prose file not found: {args.against_prose}", file=sys.stderr)
        sys.exit(2)

    gates_config = _gates_config()
    snapshot = _snapshot(args.session)

    from scripts.data.gate_eval import evaluate_gates, _verify_snapshot_hash
    try:
        _verify_snapshot_hash(snapshot, _ROOT / "local" / "snapshots" / f"{args.session}.json")
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(2)

    report = evaluate_gates(snapshot, gates_config, verify_hash=False)
    eval_tiers = {gid: result["tier"] for gid, result in report["gates"].items()}

    prose_tiers = extract_prose_tiers(prose_path)
    if not prose_tiers:
        print(
            "WARNING: No gate tiers extracted from prose file. "
            "Check that Phase 2 deployment gate table uses **TIER** format.",
            file=sys.stderr,
        )

    exit_code = compare(eval_tiers, prose_tiers, args.session)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
