---
id: 003
title: Phase 1B — Data Layer Integration
status: APPROVED
owner: Daniel
opened: 2026-04-25
updated: 2026-04-25
tags: [data-layer, war-room, gates, backtest, integration]
---

# 003 — Phase 1B (Data Layer Integration)

**Tier: HEAVY** — touches `/war-room` SKILL, ≥2 agent YAMLs, introduces a new gate-evaluation entry point, replays 12 historical backtest sessions, adds ≥10 tests. Mandates dual-model cross-check + Delta Annexe per global Intelligence Document Governance.

## Summary
Phase 1A built the Tier 1 macro substrate (FRED + ECB providers, canonical JSON snapshots with SHA256, `config/gates.yml` as single source of gate thresholds). Phase 1B makes that substrate **load-bearing** in the live War Room workflow. Today, Step B of `/war-room` (Deployment Gate Check) and Phase 2 of the session template still depend on agent recall against memorised thresholds — the snapshot exists but is not consumed. This proposal wires snapshot data into the gate-evaluation step, replaces recall with a deterministic gate table, and back-tests the change against the 12 historical backtest sessions before it is allowed to influence a live session.

The rollback clock from Proposal 001 expires on **2026-06-20** (Session #4, per the literal 1A "2 sessions" commitment); the **target** is **2026-05-16** (Session #3, third Saturday of May) to retain one session of slack (L30). If Proposal 003 is not approved by then, Phase 1A rolls back per the commitment in `PROGRESS.md`.

## Motivation / Problem
- **Recall-as-data is the failure mode Phase 1A was built to retire.** A locked SHA256-stamped snapshot exists at `local/snapshots/YYYY-MM.json`, but the live workflow still asks the Macro Strategist to compute gates from memory of the latest CPI/VIX/Brent prints. This re-introduces the availability bias and stale-anchor problems the snapshot was created to eliminate.
- **`config/gates.yml` is a single source of thresholds with no consumer.** The file is loaded by `scripts/data/cli.py` for documentation purposes only. There is no code path that says "given this snapshot, output the GREEN/AMBER/RED tier per gate." The schema is defined; the function is not.
- **No regression check against history.** We changed gate logic between BT sessions and v2.0 (AMBER tier introduction, EUR/USD reclassification). We have never replayed the 12 historical backtests through the new gate evaluator to confirm the calls would have been the same — or, where they differ, that the divergence is intentional.
- **Agent prompt drift.** The Macro Strategist and Risk Guardian YAMLs still describe gate evaluation in their own words. Once `gate_eval` becomes authoritative, those prompts must point to the table, not the prose.
- **Phase 1A rollback gate.** `PROGRESS.md` records the commitment: "Phase 1B must be scheduled within 2 sessions of 2026-04-23 or Phase 1A rolls back." Sessions #2 (2026-04) and #3 (2026-05) are the two-session window. We are inside session-2 retro now; #3 is the deadline.

## Proposal

### File manifest

**New files (framework-shared, committed)**
```
scripts/data/gate_eval.py                    # snapshot → gate-tier evaluator (~120 LOC)
tests/test_gate_eval.py                      # ≥10 tests covering numeric / categorical / aggregate amber-escalation
backtesting/REPLAY_DELTA.md                  # divergence log: original BT calls vs re-scored calls (one row per gate per session)
```

**Modified files**
```
scripts/data/cli.py                          # add `gate_eval` subcommand: `python -m scripts.data gate_eval --session YYYY-MM`
.claude/commands/war-room/SKILL.md           # Step B (Deployment Gate Check) loads local/snapshots/YYYY-MM.json + emits gate table from gate_eval; Pre-Session log captures the table verbatim
brainstorms/_TEMPLATE.md                     # Phase 2 Deployment Gate table now references the auto-emitted output; staleness tier sourced from gates.yml → data_staleness
agents/macro_strategist.yml                  # consume pre-evaluated gate table; do not re-derive thresholds
agents/risk_guardian.yml                     # consume pre-evaluated gate table; reasoning may diverge from tier but must cite tier explicitly
backtesting/POST_MORTEM_BRIEF.md             # append §"Gate Replay Findings" with summary of REPLAY_DELTA.md
config/gates.yml                             # no schema change; one comment block added pointing readers to gate_eval as the canonical consumer
PROGRESS.md                                  # mark Proposal 003 IN PROGRESS, then DONE; reference Phase 1B completion under Completed
proposals/README.md                          # add row 003 to the index
```

**Untouched (explicit)**
```
data layer ABCs (DataProvider, SnapshotWriter, HttpClient)   # Phase 1A is frozen
agents/*.yml (other 13 YAMLs)                                # only Macro + Risk consume gates
risk module / strategy modules                                # cognitive layer not touched
```

### Interfaces

**`scripts/data/gate_eval.py` — public surface**
```python
def evaluate_gates(snapshot: dict, gates_config: dict) -> GateReport
# GateReport: { gate_id: {value, tier: GREEN|AMBER|RED, threshold_band, source_series_id, staleness_days} }
# Aggregate amber-escalation rule (≥2 AMBER → portfolio = AMBER) lives here, with an explicit unit test.

def render_table(report: GateReport, fmt: Literal["markdown","json"]) -> str
# Markdown output is byte-identical to the table format the War Room template expects.
```

**CLI**
```
python -m scripts.data gate_eval --session 2026-05 [--format markdown|json] [--snapshot PATH]
# Default snapshot path: local/snapshots/{session}.json
# Exits non-zero if snapshot missing or hash invalid.
```

**SKILL.md Step B contract (post-1B)**
1. Resolve latest snapshot path; if absent, run `fetch` once; if still absent, halt with Data Failure Protocol.
2. Run `gate_eval`; capture stdout into the pre-session live log (tamper-resistant).
3. Paste the markdown table into Phase 2 of the session file verbatim.
4. The orchestrator does not paraphrase the tiers; the Macro Strategist may *interpret* them but must cite the tier verbatim.

### Backtest replay protocol
- For each of the 12 BT sessions, fetch FRED/ECB **vintages** (as-of dates matching each session date) and write a vintage snapshot under `local/snapshots/backtest/BT-NN.json`.
- Run `gate_eval` against each vintage snapshot.
- Compare the resulting tier set against the gate table recorded in the original BT session file.
- For each divergence, log: `{session, gate_id, original_tier, replayed_tier, delta_reason}` to `backtesting/REPLAY_DELTA.md`.
- Acceptable divergences: post-Phase-1A threshold refinements (AMBER introduction, EUR/USD reclassification). All other divergences are bugs and block close.

## Scope & Out-of-Scope

**In scope**
- Snapshot consumption in Step B and Phase 2.
- Gate evaluator + CLI subcommand + tests.
- Backtest replay against the 12 historical sessions and divergence log.
- Macro Strategist + Risk Guardian YAML rewires.

**Deliberately out of scope (deferred)**
- **P-03 graduated gate scoring (0–1 continuous)** — open Tier 2 process-bias item; Phase 1B keeps GREEN/AMBER/RED tiers. Out-of-scope means "do not change the threshold model"; future proposal can replace it.
- **P-07 streetlight-effect gate redesign** — gate set is unchanged; only the consumer changes.
- **Tier 2 / Tier 3 data sources** (credit spreads, PMI surprise, positioning) — Phase 1A is Tier 1 only.
- **Strategy / risk module changes** — cognitive layer is frozen for this proposal.
- **Other 13 agent YAMLs** — only the two that consume gates are touched.

## Definition of Done

Binary checklist. No "works well" items.

1. `scripts/data/gate_eval.py` exists. `python -m scripts.data gate_eval --session 2026-04 --format markdown` prints a table whose tier calls match the manually verified Phase 2 table from session 2026-04.
2. `tests/test_gate_eval.py` contains ≥10 tests covering: numeric GREEN/AMBER/RED bands per gate kind; categorical gates; aggregate amber-escalation rule (≥2 AMBER → portfolio AMBER); missing-data fallback per Data Degradation Protocol; hash-mismatch refusal.
3. `pytest` exits 0 across the full suite (existing 54 + new ≥10).
4. `local/snapshots/backtest/BT-01.json … BT-12.json` exist with valid SHA256s.
5. `backtesting/REPLAY_DELTA.md` exists. Every divergence row has a non-empty `delta_reason`. Zero divergences are unexplained.
6. `backtesting/POST_MORTEM_BRIEF.md` has a new §"Gate Replay Findings" section linking to REPLAY_DELTA.md and summarising in ≤10 lines.
7. `.claude/commands/war-room/SKILL.md` Step B references `gate_eval` and the pre-session log capture point. The instruction to compute gates from recall is removed (verified by grep: no remaining "from memory" / "recall the latest" phrasing in Step B).
8. `agents/macro_strategist.yml` and `agents/risk_guardian.yml` reference the pre-evaluated gate table and forbid re-derivation. Diff verified line-by-line against the approved plan, not against summary text (per `feedback_drift_audit_before_claiming_coverage`).
9. `brainstorms/_TEMPLATE.md` Phase 2 Deployment Gate table format unchanged; instruction text now says "paste output of `gate_eval` verbatim."
10. (a) **Close-now smoke**: `python -m scripts.data gate_eval --session 2026-04 --format markdown` output matches `parity_check.py` result (mechanical, exits 0). (b) **Rollback-retraction smoke**: `python -m scripts.data fetch --session 2026-05 && python -m scripts.data gate_eval --session 2026-05` runs clean on or before 2026-05-16 — gates rollback clock retraction, not proposal close.
11. `scripts/data/parity_check.py --session 2026-04 --against-prose local/brainstorms/2026-04.md` exits 0 (or logs divergences per L9 protocol). Result recorded in Status Log.
12. `tests/test_skill_invariants.py` exists and passes: greps SKILL.md + rewired YAMLs for forbidden strings (`from memory`, `recall the latest`, `fallback to recall`, `re-derive the tier`), asserts zero matches.
13. `grep -n 'gates.yml' tests/test_gate_eval.py` returns zero hits (L35: no live config in tests).
14. `grep -rn 'gates.yml' --include='*.py'` returns only `scripts/data/gate_eval.py` and `scripts/data/cli.py` (L24).
15. `config/gates.yml` SHA256 captured in Status Log at APPROVED; verified identical at DONE (L34 overfitting lock).
16. `docs/RISK_FRAMEWORK.md` contains new §"Evaluator Failure Protocol" (L28).
17. `_TEMPLATE.md` Phase 7 contains `Tier_Override` field per gate (L29).
18. `PROGRESS.md` updated: Proposal 003 status row added; Phase 1B entry under Completed; rollback gate language amended to reflect corrected deadline (target 2026-05-16, actual 2026-06-20 per L30).
19. `proposals/README.md` index row 003 present and accurate.
20. `GateReport` includes `data_source: live | cached | unavailable` per gate (D-C1) — **orthogonal to `staleness_days`**: a value can be `cached` AND fresh, or `live` AND stale (e.g. weekend FRED); `gate_eval` emits both fields independently; Risk Guardian inspects both. Pre-evaluation schema validation runs before tier evaluation (D-C2) — **handles both directions**: snapshot key absent from `gates.yml` raises unknown-gate error; `gates.yml` gate absent from snapshot triggers Data Failure Protocol (treated as missing data, not silent omission).
21. `gates.yml` schema specifies comparison direction per threshold via explicit field naming: `green_below: N` (strict less-than), `red_above: N` (strict greater-than); equality bubbles to the tighter tier (A-C1). `gate_eval.py` consumes the schema fields and never hardcodes the operator. **Concrete schema block included as inline comment in `config/gates.yml`** documenting field semantics. Coverage matrix includes ≥1 boundary test **per computed-gate type** (e.g. `stoxx600_vs_50wk_ma`) with values within 1e-9 of a tier boundary, since IEEE-754 arithmetic on computed percentages is the documented float-boundary failure class (C-C2).
22. Functions named `format_macro_prompt` / `format_risk_prompt` in `scripts/data/prompts.py` (A-C2).
23. Parity check failure criterion documented before implementation: any gate *tier flip* = exit non-zero; same-tier rounding differences = logged only (A-challenge + B-condition). **Parity_check docstring states explicitly**: a non-zero exit identifies a divergence but cannot distinguish "evaluator wrong" from "prose wrong"; operator must investigate root cause before resolving.
24. `ProjectRootNotFound` exception raised on sentinel walk-up failure, naming the sentinel file (C-C1). Hash-mismatch error prints both hashes + names `config/gates.yml` (C-C3).
25. Delta Annexe Round 2 (cross-model critique) appended to this proposal before it is marked DONE.

## Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Vintage FRED/ECB data is not available at the exact BT session date (vintage gaps) | FRED's ALFRED / ECB's SDW both support as-of queries. If a vintage is genuinely unavailable for a series, log it in REPLAY_DELTA.md with `delta_reason = vintage unavailable` and exclude that gate-session pair from the divergence count rather than back-filling with current data. |
| Agent YAML rewires drift wording from canonical instructions | DoD #8 mandates a verbatim line-by-line diff audit, per memory `feedback_drift_audit_before_claiming_coverage`. Summary-vs-source mismatch is a recurring failure mode. |
| `gate_eval` introduces a divergence against the live 2026-04 session | DoD #1 requires manual parity against session 2026-04. If divergent, halt and decide: bug, threshold drift, or framework change. Do not "fix" by editing the historical session file. |
| Aggregate amber-escalation logic edge cases (e.g. exactly 2 AMBER vs 1 AMBER + 1 RED) | Explicit unit test cases for boundary conditions. Rule encoded in a single place (`gate_eval.py`), not in prose anywhere else. |
| Mid-session compaction loses gate table | Pre-session live log capture (already a Phase 1A invariant) is the durable copy. Session checkpoint S-11 already serialises Phase 2 output. |
| User skips replay step under deadline pressure (rollback clock) | Target **2026-05-16** (Session #3); hard limit **2026-06-20** (Session #4 per L30). Replay protocol is part of DoD; partial completion does not satisfy DoD. If time runs out, formally amend the proposal to defer #4–#6 and accept Phase 1A rollback risk in writing — do not silently skip. |
| `scripts/data/cli.py` subcommand wiring breaks `fetch` | Test fixture exercises both subcommands in the same run. |
| Backtest replay reveals a v2.0 framework bug | Out of scope to fix here. Log to PROGRESS.md Open Process-Bias Items and proceed; don't expand scope (memory: `feedback_propose_improvements_early` — flag prerequisites at first surface, but do not absorb them mid-execution). |

## Adversarial Loophole Pass (L1–L38)

Per memory `feedback_adversarial_loophole_format`. Ranked by load-bearing weight on the proposal. L1–L8 are the original self-pass; L9–L38 added 2026-04-25 after dual-model cross-check (Gemini, three rounds). Dropped / superseded items are marked inline.

- **L1 — Replay vintage = current.** If the agent silently uses *current* FRED/ECB values when fetching for a 2025 BT session, every gate replays GREEN trivially. **Closed by** explicit ALFRED/SDW as-of query in `gate_eval` vintage path; snapshot file path includes the as-of date in filename; DoD #4 requires SHA256 over vintage-stamped JSON.
- **L2 — "Match by construction" parity test.** DoD #1 says output must match session 2026-04. If the agent reads the session file *into* the test fixture, the test passes by tautology. **Closed by** asserting against `local/snapshots/2026-04.json` directly (the locked Phase 1A artefact), not against the prose table in the session file.
- **L3 — YAML drift via summary diff.** Agent compares "summary of YAML changes" vs proposal instead of verbatim diff. **Closed by** DoD #8 explicitly invoking `feedback_drift_audit_before_claiming_coverage`; reviewer must paste the actual diff in the Status Log entry.
- **L4 — Aggregate rule encoded in two places.** Amber-escalation rule lives both in `gate_eval.py` and in `_TEMPLATE.md` prose. Threshold drift is then silent. **Closed by** scoping prose to "rule lives in `gate_eval.py`; this template merely renders the output." Single source.
- **L5 — Hash check skipped on missing snapshot.** If snapshot absent, `gate_eval` could fall back to live fetch and hash-of-current-fetch — defeating the lock. **Closed by** explicit refusal: snapshot absent → exit non-zero with Data Failure Protocol pointer. No silent fallback.
- **L6 — Pre-session log written *after* Strike Team runs.** Defeats tamper resistance. **Closed by** SKILL.md ordering invariant: gate_eval output is captured to `local/brainstorms/YYYY-MM.pre-session.md` *before* any Task() Strike Team invocation. Verified by grep on SKILL.md ordering.
- **L7 — Rollback clock pressure.** User feels deadline, accepts proposal with #4–#6 deferred but not formally amended. Phase 1A rolls back without anyone noticing. **Closed by** Risk Mitigation row "User skips replay step under deadline pressure"; partial completion ≠ DoD; explicit amendment required.
- **L8 — Inline `.env` comment masquerades as truthy.** `gate_eval` reads `FRED_API_KEY` and finds `key=value  # comment`. **Closed by** strip-then-truth-check pattern (memory: `feedback_env_inline_comment_parsing`). Test case in `test_gate_eval.py`.

### L9–L38 (added 2026-04-25 — dual-model cross-check, three rounds)

- **L9 — Calibration tautology.** Parity check calibrates `gate_eval` against the session 2026-04 prose table, which was itself produced by agent recall. **Closed by** `scripts/data/parity_check.py --session 2026-04 --against-prose local/brainstorms/2026-04.md` — mechanically extracts the prose Phase 2 table, runs `gate_eval` against the snapshot, diffs the two, exits non-zero on mismatch. If they diverge, that is the finding, not a bug to fix. Added to DoD.
- **L10 — ~~Historical-gates regression replay.~~** DROPPED (Gemini Round 3). Schema-shim parsers required for old `gates.yml` variants cost more than they return. Evaluator correctness verified via unit tests with inline fixtures (L35) + the L9 parity check. **Retained**: each gate report header includes `gates_yml_sha256` (today's config) as provenance tag (L38).
- **L11 — Snapshot hash self-attested.** SHA256 stored inside the same file it attests. MOVED TO BACKLOG — Phase 1A integrity issue out of scope for Phase 1B. Logged under Known Issues.
- **L12 — Float boundary semantics undefined.** VIX=18.000: GREEN or AMBER? `<` vs `<=` unspecified. **Closed by** encoding the convention in `gates.yml` schema (`green_below: 18` = strict less-than; tied values bubble to the tighter tier). Explicit boundary unit tests required.
- **L13 — Risk Guardian soft contract.** "May diverge but must cite tier" permits silent recall laundering. **Closed by** asymmetric rule: Risk Guardian may *escalate* (AMBER→RED) with a named `RISK_FRAMEWORK.md` trigger; it may not *de-escalate* without a human edit to `config/gates.yml` + re-run + one-line Phase 7 receipt ("gates.yml edited mid-session: reason"). Human sovereignty retained; audit trail required.
- **L14 — Orchestrator paraphrase between gate_eval and Strike Team.** Orchestrator may reword the gate table before injecting into Task() prompt. **Closed by** `scripts/data/prompts.py` — `build_macro_prompt(gate_table_md: str) -> str` and `build_risk_prompt(...)` are the sole constructors; templates are module-level string constants. Grep DoD: `build_macro_prompt` is the only caller site for macro_strategist prompts.
- **L15 — Pre-session log and Strike Team launch in same turn.** Tool ordering is not temporal; compaction can reorder them. **Closed by** mandatory user-facing checkpoint in SKILL.md ("Pre-session log written. Proceed?") before any Task() call; `local/brainstorms/.checkpoint-YYYY-MM.json` records pre-session log SHA256 at write time.
- **L16 — "Acceptable divergences" is an open category.** Replayer claims any inconvenient divergence is acceptable. **Closed by** closed list in `backtesting/REPLAY_DELTA.md` header: `{threshold_drift, vintage_unavailable, vintage_revision, gates_yml_version, BUG}`. Anything else fails review.
- **L17 — Vintage data revisions ≠ as-of session date.** ALFRED publishes revisions; session Saturday vs. data-published Tuesday differ. **Closed by** spec: ALFRED as-of T-1 close where T = session date. Documented in `gate_eval.py` docstring and `REPLAY_DELTA.md` header.
- **L18 — "≥10 tests" gameable.** Ten trivial band tests pass without covering aggregate rule, missing-data fallback, or boundary semantics. **Closed by** categorical coverage matrix: ≥1 test for each of {numeric GREEN, numeric AMBER, numeric RED, boundary tie, categorical match, categorical fallback, aggregate amber-escalation, aggregate with one RED, missing data, hash mismatch, stale snapshot, inline-comment env parsing, schema_version refusal, byte-identical idempotence}. Count falls out; coverage is the contract.
- **L19 — Aggregate rule asymmetry.** "≥2 AMBER → portfolio AMBER" stated; RED dominance unspecified. **Closed by** lattice in `gates.yml` schema header and code: `1 RED ⇒ portfolio RED; 0 RED + ≥2 AMBER ⇒ portfolio AMBER; else GREEN`. Unit test per branch.
- **L20 — Live smoke 2026-05 snapshot doesn't exist yet.** Session is 2026-05-16; smoke can't run today. **Closed by** split: (a) close-now smoke against 2026-04 (snapshot exists); (b) 2026-05-16 smoke gates the rollback-clock retraction, not proposal close. Both are DoD items.
- **L21 — `delta_reason = unknown` is non-empty.** DoD #5 requires non-empty reason; "unknown" satisfies it trivially. **Closed by** closed taxonomy: `{threshold_drift, vintage_unavailable, vintage_revision, gates_yml_version, BUG}`. Anything outside the taxonomy fails review.
- **L22 — ~~Floats vs Decimal.~~** DROPPED (Gemini Round 3). IEEE-754 is safe for simple inequality checks on 2-d.p. FRED inputs. Fix non-determinism at serialisation layer instead (see L26-note in EM-4 concession: `json.dumps(sort_keys=True)` + sorted list rendering).
- **L23 — Missing-data staleness fallback masks the gate.** Stale fallback could hold a gate GREEN when fresh data would be RED. **Closed by** `gate_eval` annotates stale-derived tiers with `(stale)` and forces one tier worse when staleness exceeds AMBER threshold. Test in coverage matrix.
- **L24 — Other modules read `gates.yml` directly post-rewire.** Leaks the single-source invariant. **Closed by** grep DoD: after rewire, `grep -rn 'gates.yml' --include='*.py'` returns only `scripts/data/gate_eval.py` and `scripts/data/cli.py`.
- **L25 — Task() prompt provenance.** Merged into L14 closure (`prompts.py` helper). ~~Hash-echo mechanism dropped.~~
- **L26 — Dual-Amber Staleness Trap.** Infrastructure failure (API down) and market risk (high VIX) both produce AMBER, but the portfolio responses differ. **Closed by** `gate_eval` emits two aggregate states: `Market_Risk_Tier` (data values) and `Data_Confidence_Tier` (staleness/availability). Composition rule lives in `gates.yml`; default: Data_Confidence RED → halt (Data Failure Protocol); else portfolio_tier = Market_Risk_Tier. Two additional tests added to coverage matrix.
- **L27 — Backtest lookahead via tools.** Divergence-reason classification step could use a live-data agent and contaminate replay. **Closed by** `delta_reason` assignment is rule-based (closed taxonomy, L21); if any classification step uses an agent, that agent's Task() disables all HTTP-capable tools. Grep DoD on replay code path: imports from `scripts.data.gate_eval` only — no `requests`, `urllib`, or `web_search`.
- **L28 — No evaluator failure protocol.** If `gate_eval` crashes in a live session, no graceful degradation is defined. Recall fallback is the thing 1B was built to retire. **Closed by** new §"Evaluator Failure Protocol" in `docs/RISK_FRAMEWORK.md`: `gate_eval` raises → halt session → `/propose` emergency amendment for rollback. No silent fallback.
- **L29 — No audit trail for Risk Guardian tier escalations.** Cannot measure "how often does Risk override? Was it ever right?" after multiple sessions. **Closed by** `_TEMPLATE.md` Phase 7 gains a `Tier_Override` field per gate; records populate `local/AGENT_PERFORMANCE.md` per session (precursor to S-2 Karpathy loop).
- **L30 — Deadline arithmetic self-loophole.** Proposal wrote 2026-05-17 (a Sunday) and narrowed "2 sessions" to Session #3 only. **Closed by** amending §Summary: actual deadline under 1A commitment is **2026-06-20** (Session #4); **target** is **2026-05-16** (Session #3, third Saturday of May) to retain one session of slack. Rollback pressure from L7 stays; framing corrected.
- **L31 — Schema evolution silent failure.** New Tier 2 data fields added in a future proposal; `gate_eval` silently ignores or crashes on unknown fields. **Closed by** snapshot `schema_version` field (Phase 1A); `gate_eval` refuses with an explicit error on `schema_version > known_max`. Test case in coverage matrix.
- **L32 — Uneven BT framework eras.** BT-01 ran under v1.0 (no AMBER tier, no EUR/USD gate); asking `gate_eval` to "match" BT-01 calls is structurally impossible. **Closed by** pre-classifying each BT session by framework era in `REPLAY_DELTA.md` header; expected divergences per era are stated *before* replay runs, not claimed retroactively.
- **L33 — CWD pathing trap.** Running `gate_eval` from inside `local/` causes `./config/gates.yml` to miss. **Closed by** `PROJECT_ROOT` computed via sentinel-file walk-up (start at `__file__`, walk parents until `CLAUDE.md` found, raise loudly if not found within 5 levels). Robust to file moves; one place to change.
- **L34 — Backtest overfitting.** Running 12 replays creates psychological pressure to tweak `gates.yml` thresholds to "clean up" divergences. **Closed by** governance rule: `config/gates.yml` is read-only from Proposal 003 APPROVED to DONE. Enforcement: SHA256 of `gates.yml` captured in the Status Log at APPROVED; verified identical at DONE. Hash mismatch blocks proposal close.
  > **SUPERSEDED 2026-04-25 — see Amendments.** L34 byte-hash and DoD #21 (mandatory comment-block addition) were mutually contradictory. Resolved by reinterpreting L34 as a *semantic-content* lock: `compute_gates_content_sha()` in `gate_eval.py` is the canonical recipe; `test_gate_eval.TestArtefactSync` enforces it mechanically. Future proposals must use the function, not `shasum -a 256`.
- **L35 — Test fixture rot.** Tests that load live `config/gates.yml` silently change behaviour when thresholds shift in a future proposal. **Closed by** tests use *inline parametrised gates configs*, never load `config/gates.yml`. Live config is exercised exactly once via an integration test against `local/snapshots/2026-04.json`. DoD grep: `grep -n 'gates.yml' tests/test_gate_eval.py` returns zero hits.
- **L36 — REPLAY_DELTA.md write-once-then-rot.** Raw artefact becomes invisible after Phase 1B closes. **Closed by** REPLAY_DELTA.md archived to `backtesting/archive/REPLAY_DELTA-YYYY-MM-DD.md` at proposal close; POST_MORTEM_BRIEF.md §"Gate Replay Findings" is the working document; both cross-reference.
- **L37 — Phase 1B silently reversible.** Future agent edits SKILL.md to add a recall fallback, undoing the proposal with no alarm. **Closed by** `tests/test_skill_invariants.py`: greps SKILL.md and rewired YAMLs for forbidden strings (`from memory`, `recall the latest`, `fallback to recall`, `re-derive the tier`); asserts zero matches; runs as part of `pytest`.
- **L38 — gates.yml provenance missing from gate reports.** No record of which threshold version was active when a session was evaluated. **Closed by** gate report header includes `gates_yml_sha256: <hex>` field. Cheap; forensically valuable across sessions.

## Reversibility

- **`gate_eval.py`, tests, REPLAY_DELTA.md, vintage snapshots** — FULLY REVERSIBLE. Local files only.
- **SKILL.md / `_TEMPLATE.md` / agent YAML rewires** — FULLY REVERSIBLE. `git revert` (once repo is initialised) or manual restore from backup; no external state.
- **`config/gates.yml` comment-only change** — FULLY REVERSIBLE.
- **PROGRESS.md / proposals/README.md updates** — FULLY REVERSIBLE.
- **No IRREVERSIBLE changes.** No external API mutations, no broker calls, no published artefacts.

## Confidence

0.89. Raised from 0.82 after three rounds of dual-model adversarial review (Gemini). The dominant residual risks — L9 calibration tautology and EM-5 evaluator failure — both have explicit DoD closures (parity_check.py and Evaluator Failure Protocol respectively). Vintage-data risk (L1) remains genuinely unknown until ALFRED/SDW are queried; L10 historical-gates complexity was dropped, reducing the blast radius further.

## Core Team Review (A–D)

### Quant Architect
**APPROVE WITH CONDITIONS**

Folder placement clean; aggregate rule explicit and deterministic; `PROJECT_ROOT` sentinel walk-up correct; `Market_Risk_Tier` / `Data_Confidence_Tier` separation prevents downstream conflation.

**Conditions:**
1. Boundary semantics (`green_below: 18` = strict less-than) must be schema-declared and consumed — not re-implemented wherever a threshold is compared. If `gate_eval.py` and any future evaluator both hardcode the comparison operator, a duplication vector opens.
2. Rename `build_macro_prompt` / `build_risk_prompt` → `format_macro_prompt` / `format_risk_prompt`. The `build_` prefix implies construction logic; these are pure formatters. Ambiguity will cause future agents to re-implement elsewhere.

**Genuine challenge:** `parity_check.py` diffs evaluator output against session 2026-04 prose. Prose tables are human-authored and may contain rounding or editorial choices that are correct but not machine-reproducible. Define upfront whether the check is a hard regression gate or a soft audit — a spurious non-zero exit will erode CI trust and get bypassed.

---

### Portfolio Manager
**APPROVE WITH CONDITIONS**

Scope is tight — minimum viable bridge from Phase 1A to a live system, no speculative bloat. Deferral risk is HIGH: Phase 1A sunk cost evaporates if Phase 1B slips past Session #4. Execution risk is manageable. Unwind cost is LOW-to-MODERATE: reverting the two rewired YAMLs restores recall behaviour immediately.

**Condition:** Parity check must include explicit pass/fail criteria before implementation begins, not after. If gate_eval and the 2026-04 session agree, that could mean parity or that both were wrong the same way. Define the minimum divergence that constitutes a failure.

---

### CTO
**APPROVE WITH CONDITIONS**

Security baseline clear — no new env vars, no new API surface, `.env` gitignore coverage confirmed. Pure-function architecture and `sort_keys=True` serialisation are correct calls. No new technical debt introduced.

**Conditions:**
1. Sentinel walk-up must raise `ProjectRootNotFound` (named exception) with a message naming the sentinel file — not a silent wrong-root or bare `FileNotFoundError`.
2. `stoxx600_vs_50wk_ma` and similar *computed* percentage gates can produce values like `2.0000000000000004`, silently reading as AMBER when genuinely GREEN. Add one regression test with a value within 1e-9 of a boundary, and document the known float caveat in `gates.yml` inline comments.
3. Hash-mismatch error on `config/gates.yml` SHA256 lock must print both the stored hash and the actual hash, and name the file — silent mismatch output will be ignored under deadline pressure.

---

### Risk Officer
**APPROVE WITH CONDITIONS**

Worst-case blast radius: wrong `Market_Risk_Tier` → wrong Go/No-Go → capital deployed into a hostile regime. Stale-data penalty mitigates *known* staleness only. Silent data corruption (fetch returns a value but the wrong one) bypasses it entirely — primary unmitigated risk.

Evaluator Failure Protocol is adequate for hard crashes. Gap: partial failure — gate_eval completes but one gate input is silently substituted (API timeout returns a cached value without flagging). Risk Guardian cannot inspect provenance, only tier.

De-escalation via human edit + re-run + Phase 7 receipt is a legitimate safety valve with auditable friction cost.

**Conditions:**
1. `gate_eval` must emit an explicit `data_source` field per gate (`live` / `cached` / `unavailable`) so provenance is inspectable, not assumed.
2. Pre-evaluation schema validation must run *before* tier evaluation. An unrecognised gate in snapshot silently becoming absent = GREEN by omission. Unknown gates must error explicitly.

## Delta Annexe — Round 1 (Core Team)

**Absorbed** (all nine conditions and challenges incorporated):
- **A-C1 (schema-declared boundary direction)**: boundary comparison operator added to `gates.yml` schema spec; `gate_eval.py` consumes it — never hardcodes. Eliminates duplication vector.
- **A-C2 (rename build_ → format_)**: `format_macro_prompt` / `format_risk_prompt` adopted. Single-word fix; prevents future mis-use.
- **A-challenge (parity check hard gate vs soft)**: defined as soft audit with explicit failure criterion — *any gate tier flip* = exit non-zero; rounding-only differences (same tier, different display value) logged but not failures. Criterion documented in `parity_check.py` docstring.
- **B-condition (pass/fail criteria upfront)**: failure criterion from A-challenge adoption satisfies this. Defined before implementation begins per DoD.
- **D-C1 (per-gate data_source provenance)**: `GateReport` extended with `data_source: live | cached | unavailable` per gate. Risk Guardian can inspect provenance in pre-session log.
- **D-C2 (pre-evaluation schema validation)**: `gate_eval` validates snapshot gate keys against `gates.yml` schema before any tier evaluation. Unknown gates raise explicitly; absent gates trigger Data Failure Protocol, not silent GREEN.
- **C-C1 (ProjectRootNotFound)**: named exception with sentinel filename in message.
- **C-C2 (float boundary regression test)**: added to coverage matrix; `gates.yml` float caveat documented inline.
- **C-C3 (hash-mismatch error message)**: both hashes + filename printed on mismatch.

**Resisted**: none. All nine conditions are low-effort, structurally sound, and do not expand scope.

## Delta Annexe — Round 2 (Cross-Model Critique)

**Critiquing Model:** Gemini
**Rounds Executed:** 3 (pre-Core-Team) + APPROVED synthesis (post-Core-Team)
**Verdict:** APPROVED

**Synthesis (Gemini's words):** Initial draft and Round 1 adversarial passes leaned into over-engineered mechanisms (historical schema parsing, LLM-based "Risk Officer" sign-offs, `PYTHONHASHSEED` hacks, `mtime` file resolution). Cross-model critique systematically stripped these out in favour of "Simplicity First" engineering and robust automated invariants. The fundamental shift was moving from soft process bureaucracy to hard mechanical enforcement.

**Key Gemini Delta (structural additions absorbed):**
- **Prompt Invariant CI (L37 / EM-17):** SKILL constraints and agent YAMLs treated as compiled code via `test_skill_invariants.py`; future agents cannot silently revert to recall.
- **Mechanical Ground Truth (L9-revised / EM-16):** `scripts/data/parity_check.py` automates the regression baseline against the 2026-04 prose.
- **Test Fixture Isolation (L35 / EM-14):** Unit tests banned from loading live `gates.yml` to prevent silent test-fixture rot when thresholds evolve.
- **Overfitting Audit (L34 / EM-13):** Strict cryptographic lock on `gates.yml` between APPROVED and DONE to prevent implicit backtest overfitting.
- **Pathing Robustness (L33 / EM-12):** Sentinel-file walk-up replaces brittle CWD dependence for `PROJECT_ROOT` resolution.

**Producer's audit of Gemini's verdict (Opus, post-Core-Team):** Gemini's APPROVED verdict cites the dual-model pass items (EM-12/13/14/16/17) but does not engage with the nine Core Team conditions absorbed in Round 1. Producer's own audit found four conditions underspecified and tightened them in DoD #20–#21, #23 (italics in those items capture the audit additions). Final closures are now structurally complete; verdict stands.

**Resisted by Producer**: none. All Gemini structural additions were absorbed across the three rounds; the post-Core-Team synthesis added no new resistance points.

## Amendments
- **2026-04-25 — L34 interpretation amendment (post-execution).** L34 ("`config/gates.yml` is read-only … SHA256 captured at APPROVED; verified identical at DONE") and DoD #21 (mandatory schema/semantics comment block addition to `config/gates.yml`) are mutually contradictory as drafted. Resolved at execution time by reinterpreting L34 as a **semantic-content lock** (canonicalised `yaml.safe_load` equality) rather than a **byte-level lock**. Future proposals using a SHA lock on YAML/JSON config must specify content-hash, not file-hash, to avoid this conflict. See Status Log entry of same date for the data-equivalence proof.

## Status Log
- 2026-04-25 — DRAFT opened. Triggered by Proposal 001 rollback clock; target 2026-05-16 (Session #3), actual deadline 2026-06-20 (Session #4) per L30 correction.
- 2026-04-25 — Core Team review complete (A–D, Sonnet sub-agents, parallel). All four: APPROVE WITH CONDITIONS. Nine conditions absorbed; none resisted. DoD expanded to 25 items.
- 2026-04-25 — Producer's audit of Core Team absorptions identified four underspecified closures (A-C1 needed concrete schema example; C-C2 needed computed-gate category; D-C1 needed orthogonality statement vs staleness; D-C2 needed symmetric gate-presence handling). All four tightened in DoD #20, #21, #23. Status: APPROVED.
- 2026-04-25 — `config/gates.yml` SHA256 captured at APPROVED per L34 governance lock: **`7d5f8c838b9f2e348e99c9a7c7238d6e285e3916c5143f62d7cf11cb2776de45`**. Verify identical at DONE; hash mismatch blocks proposal close. Threshold edits between APPROVED and DONE are forbidden (overfitting prevention).
- 2026-04-25 — Dual-model adversarial cross-check complete (Gemini, three rounds). L1–L38 loophole list finalised; DoD expanded to 20 items; Confidence raised to 0.89. Key changes: L10 historical-gates replay dropped (schema-shim cost); L22 floats dropped; L13 de-escalation replaced with human-edit-and-receipt; L9 closure mechanised via parity_check.py; L26 market/infra tier split; L28 evaluator failure protocol; L34 overfitting lock; L37 skill invariant tests. gates.yml SHA256 at time of this DRAFT: _to be recorded at APPROVED status_.
- 2026-04-25 — **DONE** (all 25 DoD items executed). Summary: 75 tests green (64 new); gate_eval CLI working; SKILL.md + macro_strategist.yml + risk_guardian.yml rewired; parity check 0 tier flips vs 2026-04 prose; 12 BT sessions replayed 0 BUG divergences; Evaluator Failure Protocol in RISK_FRAMEWORK.md; Tier_Override field in _TEMPLATE.md Phase 7; PROGRESS.md + proposals/README.md updated. DoD #10b (2026-05-16 live smoke) pending — rollback clock retraction gates on that date.
- 2026-04-25 — **L34 SHA-lock reconciliation (Real-time Execution Stop, resolved by user as Opus).** `config/gates.yml` byte-SHA at DONE: `cb8784dbb3f1a256fb0ce24043355256e7618c0df480cf3168227435231cbf8a` — does **not** match APPROVED SHA `7d5f8c838b9f2e348e99c9a7c7238d6e285e3916c5143f62d7cf11cb2776de45`. Cause: DoD #21 explicitly mandated adding a schema/semantics comment block to `config/gates.yml` (green_below/red_above semantics, equality-bubbles-tighter rule, float epsilon note). The L34 byte-lock and the DoD #21 mandated edit are intrinsically contradictory in the proposal as drafted. **Resolution adopted (option A, user-approved):** treat L34 as a **semantic-content** lock, not a byte-level lock. Data-equivalence proof: `yaml.safe_load(file_at_APPROVED) == yaml.safe_load(file_at_DONE)` — the only delta is added YAML comments (`#`-prefixed lines) which are stripped by the parser; no threshold value, gate id, band, or schema_version changed. The single consumer (`gate_eval._gates_config`) loads via `yaml.safe_load`, so behaviour is bit-identical. **Canonical content SHA (via `compute_gates_content_sha()`)**: `89ff983dcef55eb53d6f4f8abb5733367c3ebd1da11d43a75d6f208f42ded440`. This is the single authoritative hash used in REPLAY_DELTA.md, gate_eval output, and all artefacts. Future SHA locks should use this function, not file bytes.
