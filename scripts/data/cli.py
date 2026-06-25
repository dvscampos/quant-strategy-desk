"""CLI entry point: python -m scripts.data fetch --session YYYY-MM

Reads the Tier 1 series list from config/gates.yml → data_staleness.series.
Fetches each series via its provider, writes a canonical snapshot to
local/snapshots/<session>.json.

L5:  Validates that every configured series alias resolves to a registered
     provider before any network call (fail fast).
L7:  Writes atomically via a .tmp file + os.replace to prevent partial
     snapshots on crash.
L8:  Refuses to overwrite an existing snapshot file without --force.
     (Project is not a git repo; filesystem is the audit trail.)
L9:  Uses datetime.now(timezone.utc) — datetime.utcnow() is deprecated.
L22: as_of timestamp formatted as YYYY-MM-DDTHH:MM:SSZ (no microseconds,
     Z suffix, matching the locked schema example).
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent.parent
GATES_PATH = ROOT / "config" / "gates.yml"
SNAPSHOTS_DIR = ROOT / "local" / "snapshots"
CACHE_DIR = ROOT / "data" / ".http_cache"

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)


def _load_gates() -> dict:
    return yaml.safe_load(GATES_PATH.read_text(encoding="utf-8"))


def _build_providers(gates: dict, *, no_cache: bool = False) -> dict:
    """Return {series_id: provider_instance} for all configured series.

    L5: Validates every series alias is resolvable before any network I/O.
    """
    from scripts.data.http_client import HttpClient
    from scripts.data.providers.fred import FredProvider
    from scripts.data.providers.ecb import EcbProvider
    from scripts.data.providers.eurostat import EurostatProvider
    from scripts.data.providers.equity_ma import EquityMaProvider

    retry = gates["data_staleness"]["retry"]
    http = HttpClient(
        cache_dir=CACHE_DIR,
        min_interval=1.0,
        max_retries=retry["max_attempts"],
        backoff_base=retry["backoff_seconds_base"],
        max_retry_after=retry["max_retry_after_seconds"],
        skip_cache=no_cache,
    )
    fred = FredProvider(http)
    ecb = EcbProvider(http)
    eurostat = EurostatProvider(http)
    equity = EquityMaProvider()

    providers: dict = {}
    unresolvable = []
    for series_id, cfg in gates["data_staleness"]["series"].items():
        source = cfg["source"]
        if source == "FRED":
            providers[series_id] = fred
        elif source == "ECB":
            if series_id not in ecb.known_series():
                unresolvable.append(series_id)
            else:
                providers[series_id] = ecb
        elif source == "EUROSTAT":
            if series_id not in eurostat.known_series():
                unresolvable.append(series_id)
            else:
                providers[series_id] = eurostat
        elif source == "YFINANCE":
            if series_id not in equity.known_series():
                unresolvable.append(series_id)
            else:
                providers[series_id] = equity
        else:
            unresolvable.append(series_id)

    if unresolvable:
        log.error("Unresolvable series aliases: %s", unresolvable)
        sys.exit(1)

    return providers


def _fetch_all(providers: dict, gates: dict) -> list:
    from scripts.data.http_client import HttpError
    observations = []
    series_cfg = gates["data_staleness"]["series"]
    for series_id, provider in providers.items():
        try:
            max_age = series_cfg[series_id]["amber_age_days"]
            obs = provider.fetch(series_id, max_age_days=max_age)
            observations.append(obs)
            log.info("Fetched %s: %s = %s (vintage %s)", obs.source, series_id, obs.value, obs.vintage)
        except (HttpError, Exception) as exc:
            log.error("Failed to fetch %s: %s", series_id, exc)
            sys.exit(1)
    return observations


def _cmd_fetch(args: argparse.Namespace) -> None:
    raw_key = os.environ.get("FRED_API_KEY", "")
    key = raw_key.split("#")[0].strip()
    if not key:
        print("FRED_API_KEY not set — add it to .env before fetching live data.")
        print("Sign up: https://fred.stlouisfed.org/docs/api/api_key.html")
        sys.exit(1)

    # L22: Z-suffix, no microseconds.
    as_of = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    out_path = SNAPSHOTS_DIR / f"{args.session}.json"
    if out_path.exists() and not args.force:
        log.error(
            "Snapshot %s already exists. Use --force to overwrite.", out_path
        )
        sys.exit(1)

    gates = _load_gates()
    providers = _build_providers(gates, no_cache=args.no_cache)
    observations = _fetch_all(providers, gates)

    from scripts.data.snapshot import SnapshotWriter
    import json

    # L7: atomic write — .tmp in same directory to avoid cross-filesystem EXDEV.
    tmp_path = SNAPSHOTS_DIR / f"{args.session}.tmp"
    payload = SnapshotWriter.build_payload(
        session=args.session, as_of=as_of, observations=observations
    )
    tmp_path.write_bytes(
        SnapshotWriter._canonical_bytes(payload) + b"\n"
    )
    tmp_path.replace(out_path)

    log.info("Snapshot written: %s (hash %s)", out_path, payload["snapshot_hash"][:20] + "…")


def _cmd_gate_eval(args: argparse.Namespace) -> None:
    from scripts.data.gate_eval import run_gate_eval
    from pathlib import Path

    snapshot_path = Path(args.snapshot) if args.snapshot else None
    exit_code = run_gate_eval(args.session, args.format, snapshot_path=snapshot_path)
    sys.exit(exit_code)


def _cmd_set_manual(args: argparse.Namespace) -> None:
    """Set manual categorical gates on an existing snapshot (in-place, atomic write)."""
    import json
    from scripts.data.snapshot import SnapshotWriter

    # Parse gate assignments (GATE=VALUE, split on first =)
    parsed_gates = {}
    for entry in args.gate:
        k, sep, v = entry.partition("=")
        if not sep or not k.strip() or not v.strip():
            log.error("Invalid gate assignment %r — must be GATE=VALUE", entry)
            sys.exit(1)
        parsed_gates[k.strip()] = v.strip()

    # Load gates config for validation
    gates = _load_gates()
    dep = gates["deployment_gates"]

    # WRITE-SIDE STRICT validation — reject unknown/numeric/invalid-value
    for k, v in parsed_gates.items():
        if k not in dep:
            log.error("Unknown gate %r — not in deployment_gates", k)
            sys.exit(1)
        gate_cfg = dep[k]
        if gate_cfg.get("kind") != "categorical":
            log.error("Gate %r is not categorical (kind=%s) — cannot set manually", k, gate_cfg.get("kind"))
            sys.exit(1)
        valid_values = set(gate_cfg.get("tiers", {}).values())
        if v not in valid_values:
            log.error("Gate %r value %r not a valid tier label — must be one of: %s", k, v, sorted(valid_values))
            sys.exit(1)

    # Load existing snapshot (require-exists)
    out_path = SNAPSHOTS_DIR / f"{args.session}.json"
    if not out_path.exists():
        log.error("Snapshot %s does not exist — run fetch first", out_path)
        sys.exit(1)

    snapshot = json.loads(out_path.read_bytes())

    # Verify existing hash (refuse-on-tamper)
    if snapshot.get("snapshot_hash") != SnapshotWriter.compute_hash(snapshot):
        log.error("Snapshot hash mismatch — refusing to modify a tampered snapshot; re-fetch")
        sys.exit(1)

    # Build manual_gates payload (UTC date, matching pipeline tz discipline)
    manual_gates = {
        k: {"value": v, "as_of": datetime.now(timezone.utc).strftime("%Y-%m-%d")}
        for k, v in parsed_gates.items()
    }

    # Inject + recompute hash
    new_payload = SnapshotWriter.inject_manual_gates(snapshot, manual_gates)

    # Atomic write with pid-suffixed tmp (concurrency-safe)
    tmp = SNAPSHOTS_DIR / f"{args.session}.{os.getpid()}.tmp"
    tmp.write_bytes(SnapshotWriter._canonical_bytes(new_payload) + b"\n")
    tmp.replace(out_path)

    log.info("Manual gates set on %s: %s", out_path, sorted(manual_gates))


def main() -> None:
    parser = argparse.ArgumentParser(description="Quant Strategy Desk — data CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    # ---- fetch subcommand ----
    fetch_p = sub.add_parser("fetch", help="Fetch Tier 1 macro snapshot")
    fetch_p.add_argument("--session", required=True, help="Session in YYYY-MM format")
    fetch_p.add_argument("--force", action="store_true", help="Overwrite existing snapshot")
    fetch_p.add_argument("--no-cache", action="store_true", help="Bypass the HTTP cache; force a live fetch for every series (War Room pre-flight). NOTE: disables the DDP stale-cache fallback — a fetch failure raises and aborts the run.")

    # ---- gate_eval subcommand ----
    gate_p = sub.add_parser(
        "gate_eval", help="Evaluate deployment gates from snapshot"
    )
    gate_p.add_argument("--session", required=True, help="Session in YYYY-MM format")
    gate_p.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format (default: markdown)",
    )
    gate_p.add_argument(
        "--snapshot",
        default=None,
        help="Override snapshot path (default: local/snapshots/{session}.json)",
    )

    # ---- set-manual subcommand ----
    manual_p = sub.add_parser(
        "set-manual", help="Set manual categorical gates on an existing snapshot"
    )
    manual_p.add_argument("--session", required=True, help="Session in YYYY-MM format")
    manual_p.add_argument(
        "--gate",
        action="append",
        dest="gate",
        metavar="GATE=VALUE",
        required=True,
        help='Categorical gate assignment, e.g. --gate hormuz=Open --gate "ecb=Hold or cut"',
    )

    args = parser.parse_args()

    if args.command == "fetch":
        _cmd_fetch(args)
    elif args.command == "gate_eval":
        _cmd_gate_eval(args)
    elif args.command == "set-manual":
        _cmd_set_manual(args)


if __name__ == "__main__":
    main()
