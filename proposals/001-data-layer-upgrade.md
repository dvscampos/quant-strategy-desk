---
id: 001
title: Data Layer Upgrade — Phase 1A (Tier 1 macro substrate)
status: DONE
owner: Daniel
opened: 2026-04-21
updated: 2026-04-23
tags: [data, infrastructure, macro, phase-1a]
---

# 001 — Data Layer Upgrade (Phase 1A)

## Summary
Today the War Room agents analyse a thin substrate: yfinance price points, `PORTFOLIO.md`, and model training-data recall. This proposal introduces a locked, auditable **Tier 1 data layer** (FRED + ECB Data Warehouse) with snapshotting, hashing, a Data Degradation Protocol, and a single source of truth for gate thresholds.

- **Phase 1A** (this proposal): data layer proven in isolation from the cognitive layer. Snapshots written, hashed, committed as audit trail. Prose in RISK_FRAMEWORK.md and STRATEGY_LOGIC.md references `config/gates.yml` instead of duplicating values. **No agent prompt changes. No SKILL.md changes.**
- **Phase 1B** (pre-committed in the same breath as 1A): agent prompts consume snapshots; backtest re-scorer re-states prior regime calls. Expected revision 10–20% of historical regime calls.

**Rollback trigger**: if Phase 1B is not scheduled within 2 sessions of 1A close, **Phase 1A is rolled back**. Snapshots without consumers are orphan infrastructure — expensive theatre.

## Motivation / Problem
- Agents speak with authority about macro regimes on a substrate they cannot name.
- Session reproducibility is nil: no macro state is pinned.
- Phase 9 cold sign-off agents have no shared factual basis.
- Backtests recall prices but not the macro state that justified decisions.
- Gate thresholds live in prose (duplicated across RISK_FRAMEWORK.md and STRATEGY_LOGIC.md) and drift silently.

## Proposal (Phase 1A)

### Build order (non-negotiable)
1. `DataProvider` ABC
2. `SnapshotWriter` + canonical JSON + SHA256
3. Schema lock (JSON example below, frozen before provider code lands)
4. `config/gates.yml`
5. Prose de-duplication in RISK_FRAMEWORK.md / STRATEGY_LOGIC.md to reference gates.yml
6. **Then** FRED provider
7. **Then** ECB provider
8. CLI last

Fetchers come last, by design. Writing a provider before the schema and writer are locked invites drift.

### New files
```
scripts/data/__init__.py
scripts/data/provider.py          # DataProvider ABC — fetch(), source_name, rate_limit
scripts/data/http_client.py       # shared HttpClient: exponential backoff + on-disk cache
scripts/data/snapshot.py          # SnapshotWriter: schema + canonicalisation + SHA256
scripts/data/providers/fred.py    # FRED implementation (~50 lines)
scripts/data/providers/ecb.py     # ECB Data Warehouse implementation (~50 lines)
scripts/data/cli.py               # `python -m scripts.data fetch --session YYYY-MM`
config/gates.yml                  # gate thresholds extracted from prose
data/snapshots/.gitkeep
data/.http_cache/.gitkeep
tests/fixtures/data/fred_*.yaml   # vcrpy cassettes (success, 429, malformed)
tests/fixtures/data/ecb_*.yaml
tests/test_data_providers.py      # unit + cassette replay
tests/test_snapshot_hash.py       # golden hash determinism
tests/test_gate_eval.py           # gate GREEN/AMBER/RED eval from frozen snapshots
```

### Modified files
```
.env.example              # + FRED_API_KEY=
.gitignore                # + data/.http_cache/   (snapshots committed deliberately as audit trail)
docs/DATA_STANDARDS.md    # + Snapshot JSON Schema section
docs/RISK_FRAMEWORK.md    # + Data Degradation Protocol; HICP >45d AMBER, >60d RED; reference gates.yml
docs/STRATEGY_LOGIC.md    # reference gates.yml (remove duplicated thresholds)
PROGRESS.md               # + 1B commitment + backtest re-statement expectation (10–20% regime-call revision)
requirements.txt          # + requests, pyyaml, vcrpy (test-only)
```

### Snapshot schema (locked before any provider code lands)
```json
{
  "as_of": "2026-05-17T10:00:00Z",
  "session": "2026-05",
  "snapshot_hash": "sha256:...",
  "series": [
    {"source": "FRED", "series_id": "CPIAUCSL", "as_of": "2026-04-30", "value": 316.7, "vintage": "2026-05-14", "units": "index_1982_84_eq_100"},
    {"source": "ECB",  "series_id": "DFR",      "as_of": "2026-04-17", "value": 2.00,  "vintage": "2026-04-17", "units": "pct"}
  ]
}
```

Canonical JSON: sorted keys, UTF-8, LF line endings, no trailing whitespace. `snapshot_hash` is computed over the canonical form with the field set to empty string, then inserted. Hand-verifiable.

### Data Degradation Protocol (RISK_FRAMEWORK.md)
If any Tier 1 series fails to fetch:
1. Retry: exponential backoff, 3 attempts.
2. Fall back to last known snapshot, tagged `STALE` with vintage age.
3. **HICP staleness: >45d AMBER, >60d RED.** (Other series: thresholds defined per series in gates.yml.)
4. ≥2 Tier 1 series stale/RED → session-level RED: halve deployment or DEFER.
5. Never silently substitute training-data recall.

## Scope & Out-of-Scope

**In scope (1A):** FRED + ECB providers only; snapshot writer; hash; CLI; DDP published; `config/gates.yml` as single source of truth; vcrpy tests; env-gated live smoke test.

**Out of scope (1A, explicit to prevent drift):**
- Any `.claude/skills/war-room/SKILL.md` change
- Any agent prompt change
- Any backtest re-scoring tool
- Eurostat, VIX term structure, RSS feeds, NewsAPI, GDELT, CFTC, ETF fact sheets
- Dashboard integration of snapshot data
- IBKR / broker data ingestion

## Definition of Done (binary)
1. `python -m scripts.data fetch --session 2026-05` writes a schema-compliant `data/snapshots/2026-05.json` with a deterministic `snapshot_hash`.
2. VCR tests pass fully offline (including 429 and malformed-response cassettes).
3. Gate-eval unit tests pass against **3+ frozen snapshots** covering GREEN / AMBER / RED paths.
4. One env-gated live smoke test (`PYTEST_LIVE=1`) successfully pulls real FRED + ECB.
5. `config/gates.yml` is the **single source of gate thresholds** — prose in `RISK_FRAMEWORK.md` and `STRATEGY_LOGIC.md` references it, does not duplicate values.
6. Data Degradation Protocol published in `RISK_FRAMEWORK.md` with concrete staleness thresholds (HICP >45d AMBER, >60d RED).
7. Unchanged in 1A: `.claude/skills/war-room/SKILL.md`, all agent prompts, `brainstorms/_TEMPLATE.md`. Zero touch on the cognitive layer.

## Risks & Mitigations
| Risk | Mitigation |
|---|---|
| FRED rate limits / outage | Exponential backoff, on-disk HTTP cache, DDP staleness tiers. |
| ECB SDMX schema drift | vcrpy cassettes + pinned endpoint; cassette replay catches drift in CI. |
| 1B slips, agents keep ignoring snapshots | Pre-committed rollback: >2 sessions without 1B scheduled → revert 1A. |
| Snapshot hash non-determinism | Canonical JSON spec + `test_snapshot_hash.py` golden test. |
| Secrets leak (FRED key) | `.env` only (gitignored); `.env.example` placeholder. |
| Drift between prose and gates.yml | DoD #5 makes gates.yml the single source; prose references only. |

## Core Team Review (A–D)

### Quant Architect — FLAG 0.72
Approved shape. Flags absorbed: explicit determinism test (DoD #1); canonical JSON spec; Items 6 (VIX term) and 7 (CFTC COT) pushed out of T1.

### Portfolio Manager — APPROVE
Warns against marketing 1A as a capability upgrade. Absorbed — 1A is plumbing; the visible upgrade is 1B.

### CTO — APPROVE WITH CONDITIONS
Absorbed: one shared HTTP client; backoff + on-disk cache; build order puts ABC/writer/schema/gates.yml before any provider.

### Risk Officer — FLAG 0.55
Absorbed: DDP published in 1A, not deferred; rollback trigger pre-committed; snapshot hash hand-verifiable. **F3**: re-scorer required to re-state prior regime calls — deferred to 1B with expectation noted in PROGRESS.md at 1A close (10–20% revision expected).

## Delta Annexe — Round 1 (Core Team)
- **Absorbed**: determinism test; canonical JSON spec; single HTTP client; DDP lands with 1A; rollback trigger pre-committed; hash hand-verifiable; T1 narrowed to FRED+ECB; build order (ABC → writer → schema → gates.yml → prose de-dup → providers → CLI).
- **Resisted**: pydantic as a dep (project small enough for stdlib dataclasses + manual validation). Marketing 1A as an agent-capability upgrade (it is not).

## Delta Annexe — Round 2 (Gemini cross-model critique)
- **Absorbed**: Phase 1A / 1B split — correct application of Simplicity First. Folding prompt engineering and a historical re-scorer into the same merge inflates blast radius unnecessarily.
- **Absorbed**: Phase 1A definition of done — schema-compliant JSON persisting to disk, VCR tests green, agents don't consume snapshots yet. Data layer proven in isolation from cognitive layer.
- **Absorbed**: Sequential dependency logic — the re-scorer (Risk Officer F3) operates on a stable `config/gates.yml`. Building the scorer while the config is still moving is circular.
- **Resisted**: nothing material. Pushback is correct.

## Amendments
- **A1** (2026-04-21): **Phase 1B is pre-committed in the same breath as 1A approval**, not left as "we'll get to it." 1A ships with a PROGRESS.md note: *"Phase 1B follows within N sessions; backtest re-statement expected at 1B close, expected 10–20% regime-call revision."* Risk Officer's F3 only gets teeth in 1B — but the commitment belongs on the record at 1A. If 1B slips past 2 sessions without being scheduled, Phase 1A gets rolled back. Snapshots without consumers become orphan infrastructure.

## Confidence
0.88 on the revised 1A scope.

## Status Log
- 2026-04-21 — DRAFT opened after user request ("propose this, please. What else did we skip?").
- 2026-04-21 — REVIEWED (Core Team A–D).
- 2026-04-21 — Gemini cross-model critique absorbed; Phase 1A/1B split adopted; amendment A1 added.
- 2026-04-21 — APPROVED by user. Deferred for execution in a cleared session.
- 2026-04-21 — Proposal corrected after drift audit (snapshots committed not ignored; vcrpy; PYTEST_LIVE smoke; gates.yml as single source; HICP thresholds; build order; pyyaml/vcrpy deps).
- 2026-04-22 — IN PROGRESS. Manifest drift correction: `requirements.txt` does not currently exist in repo root; treated as a *new file* in 1A rather than a modified one. No design change.
- 2026-04-23 — DONE. All 7 Definition of Done gates green. 54 tests pass (offline). Live smoke test passed: 7 series fetched (FRED×4 + ECB×3), snapshot written and hash verified. Phase 1B commitment recorded in PROGRESS.md.
