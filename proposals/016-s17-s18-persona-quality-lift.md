---
id: 016
title: S-17 renaissance_backtesting lift + S-18 virtu_execution lift (bundle)
status: SUPERSEDED
superseded_by: [017, 018]
owner: Daniel
opened: 2026-05-20
updated: 2026-05-21
tags: [governance, personas, persona-eval, renaissance_backtesting, virtu_execution]
---

# 016 — S-17 + S-18: Persona Quality Lift (Bundle)

## Tier: HEAVY

**Evidence for tier**:
- 2 structural persona rewrites introducing **new architecture** — structured `output_format` schemas replacing free-prose blobs (same HEAVY trigger as Proposal 010 S-15).
- Eval-gated kill-switch infrastructure (median-of-3 + dual cold reviewer + dry-run + zero-regression revert).
- **WIDE blast radius**: both files are Phase 7 sign-off panel slots (`backtesting/engine/config/agents.yml:45,61`); `virtu_execution` is also the fixed Execution panel member.
- Touches `agents/*.yml` — a critical-pattern surface per `.claude/review-patterns.md` §Critical Patterns.

## Summary

Two follow-on items from the 2026-05-15 persona-eval baseline, bundled because they share one eval cycle, one zero-regression kill switch, and one baseline-row batch (mirrors Proposal 010's S-15+S-16 bundling rationale).

- **S-17** — Lift `renaissance_backtesting`: replace the free-prose `output_format` with a structured backtest-validity schema (rolling Sharpe stability, purged-k-fold OOS window, transaction-cost realism, turnover-cost ratio, regime-conditioned hit-rate, overfitting verdict); rewrite `system_prompt` to mandate the schema and drop the legacy "full Python code" output mandate; reframe `review_prompt` with a Renaissance-specific adversarial frame ("assume the backtest is overfit to a single calibration window"); add vocabulary discipline against `dimensional_factor_backtester`.
- **S-18** — Lift `virtu_execution`: replace the free-prose `output_format` with a structured **retail-honest** execution-cost schema (order type, expected cost in bps with explicit commission decomposition, best-ex routing note); rewrite `system_prompt` to mandate the schema, a retail-scale honesty constraint, and an upstream-instrument boundary; reframe `review_prompt`; add vocabulary discipline against `jane_street_mm` and `millennium_live_trading`.

**Baseline (verified)** — `~/.claude/persona_eval_history.csv` lines 17-18 (2026-05-15): `renaissance_backtesting` score 29, threshold 30, `passed=false`; `virtu_execution` score 29, threshold 30, `passed=false`. These are the only two Investments personas below threshold in that baseline. `PROGRESS.md:89-90` (S-17/S-18 rows) corroborate.

## Motivation / Problem

### S-17 — renaissance_backtesting

Read of `agents/renaissance_backtesting.yml` (2026-05-20):
- `output_format` is free-prose: *"Quantitative research document with full Python code, statistical validation methodology, and result interpretation guidelines."* No structured schema — unlike the post-009/010/014 baseline (`citadel_alpha`, `pimco_curve_strategist` carry structured YAML schemas).
- A backtesting-engine researcher whose output enforces nothing about rolling-Sharpe stability, OOS method, transaction-cost realism, or turnover drag is a fictional Renaissance — those are the firm's own domain primitives.
- `system_prompt` (lines 44, 46) mandates "Complete Python backtesting code" and "Format as a quantitative research document with full Python code" — an output contract that *contradicts* a structured-schema rewrite. The rewrite must remove this legacy paragraph.
- `review_prompt` is already post-010 quality (adversarial frame + 5 numbered checks + the S-16 actionability template). The S-17 change to `review_prompt` is therefore a **reframe + one added check**, not a from-scratch rewrite.
- Stale provenance comment `# Generated: 2026-03-01`.

### S-18 — virtu_execution

Read of `agents/virtu_execution.yml` (2026-05-20):
- `output_format` is free-prose: *"Execution algorithm specification with mathematical models, pseudocode for each algorithm, and performance measurement frameworks."* No structured schema. The `system_prompt` carries the matching legacy free-prose mandate to be removed.
- `review_prompt` is already post-010 quality (adversarial frame + 4 numbered checks + actionability template + effort estimates from Proposal 010 Commit 2a). The S-18 change to `review_prompt` is a **reframe**.
- The underlying structural gap Proposal 010 Commit 2a explicitly did not address: the free-prose `output_format`.

### Why bundle (mirrors Proposal 010 §"Why bundle")

| Option | Verdict |
|---|---|
| **HEAVY single proposal (chosen)** — one eval cycle, one shared kill switch, one CSV baseline batch for the 2026-08-15 quarterly re-eval, lessons carried in one artefact | ✅ Chosen |
| MEDIUM × 2 sequential | ❌ Rejected — 2× eval cost, two baseline rows harder to compare like-for-like, template could drift between cycles |

## Proposal

### Architecture decision (HEAVY — ≥2 approaches)

**Primary sub-problem: schema-rewrite strategy.**

> **Approach A — Per-persona domain-native structured schema, rewrite-in-place, per-persona staged commits.** Each persona gets a schema from its own domain primitives (citadel S-15 / pimco S-19 precedent). — **Confidence 0.88**
> Pros: each schema fits its domain; breaks the dominant pair-diff lever (static output-schema name); per-persona commits give independent eval gating + independent revert.
> Cons: two schemas to design.
>
> **Approach B — Single uniform shared schema applied to both.** — **Confidence 0.45**
> Pros: one schema to design.
> Cons: `renaissance` (backtest-validity) and `virtu` (retail execution-cost) have **disjoint output primitives** — a uniform schema forces a bad fit and reintroduces the static-label homogenisation the memory corpus warns against (MEMORY anti-pattern 2026-05-15).
>
> **Chosen: A.**

**Secondary — staged-merge granularity:** per-persona commits (Commit 1 renaissance, Commit 2 virtu, Commit 3 docs); each persona independently eval-gated. **Kill-switch precedence (resolving the L19 deadlock):**
- DoD #11 (zero-regression) is the **revert** trigger — any 7-dimension drop reverts that commit; the rewrite is then iterated to fix the regression while keeping the gains.
- DoD #13 (≥30 composite) is the **iterate-or-escalate** trigger — a rewrite that passes #11 but lands < 30 has not met the objective; it is iterated within the proposal, and if it cannot reach 30 after iteration the orchestrator escalates to the user. A dimension regression always takes precedence (revert), regardless of composite gain.
- The kill switch operates **per commit**: a renaissance failure blocks Commit 1; a virtu failure blocks Commit 2 but leaves a landed Commit 1 intact.
- **Mid-merge state**: the three commits are intended to land within a single implementation session. Even if a War Room ran between Commit 1 and Commit 2, the Phase 7 panel remains valid — Phase 7 personas sign off independently with no inter-persona contract, so a mixed-vintage roster is coherent (a documented acceptance, not a gated condition).

### SP-1 — renaissance_backtesting structural rewrite

**New `output_format` (structured YAML schema)** — 7 blocks:

```yaml
output_format:
  backtest_subject:
    strategy_name: string
    asset_class: equity-etf|bond-etf|commodity-etc|multi-asset
    calibration_window: string            # e.g. "2015-2021 in-sample"
  rolling_sharpe_stability:
    in_sample_sharpe: number
    rolling_12m_sharpe_min: number        # worst rolling 12-month window
    rolling_12m_sharpe_max: number
    stability_verdict: stable|degrading|single-window-artefact
  out_of_sample:
    oos_method: purged-k-fold|walk-forward|holdout
    oos_window: string                    # e.g. "2022-2025 untouched"
    oos_sharpe: number
    oos_to_is_ratio: number               # OOS Sharpe / IS Sharpe
  transaction_cost_realism:
    cost_model: string                    # commissions + spread + market-impact components
    gross_return_pct: number
    net_return_pct: number
    frictionless_flag: boolean            # true = transaction costs NOT modelled;
                                          # the persona MUST raise this as a HIGH-severity finding
  turnover_cost_ratio:
    annual_turnover_pct: number
    turnover_cost_drag_pct: number
    turnover_cost_ratio: number           # cost drag / gross alpha
  regime_conditioned_hit_rate:
    regimes_tested: list
    hit_rate_by_regime: string
    weakest_regime: string
  overfitting_verdict: real-alpha|likely-overfit|indeterminate
```

`overfitting_verdict` is an **enum scalar** (consistent with citadel's `category:` and pimco's stance enums) — a holistic verdict the six review-checks inform; the `system_prompt` gives decision guidance for choosing among the three values.

**`system_prompt`** rewritten to mandate the 7-block schema, **remove the legacy "full Python code / quantitative research document" output mandate**, and require Renaissance vocabulary: "calibration window", "curve-fit noise", "rolling Sharpe stability", "purged k-fold", "out-of-sample", "turnover-cost ratio", "regime-conditioned hit-rate", "look-ahead leakage", "survivorship", "walk-forward".

**`review_prompt` reframe** — new adversarial opening: *"Assume the backtest is overfit to a single calibration window: it was tuned on one historical regime and the parameters will not survive a regime it never saw. Prove the alpha is a calibration artefact."* — **6 numbered checks** (the reframe *adds* Calibration-Window Overfit and keeps Multiple-Testing as a distinct named check — D2 adversarial depth strictly improves vs the current 5):
1. **Calibration-Window Overfit** — single-regime tuning; rolling 12-month Sharpe collapse outside the calibration window.
2. **Multiple-Testing & Selection Bias** — how many variants were tried; deflated Sharpe (Bailey & López de Prado); "best of many coin flips".
3. **Look-Ahead & Survivorship Leakage** — restated fundamentals, survivorship-cleaned universes, future-dated corporate actions.
4. **Transaction-Cost & Turnover Realism** — frictionless flag; turnover-cost ratio vs gross alpha.
5. **Out-of-Sample Discipline** — purged k-fold / walk-forward / holdout; OOS-to-IS ratio; OOS-window peeking.
6. **PnL Construction & Attribution Integrity** — **content preserved verbatim from the current file's check #5** (bar-lag attribution, geometric-vs-arithmetic aggregation, compounding bugs).

S-16 actionability template retained.

**Vocabulary discipline — forbidden phrases**: "factor premium", "tear sheet", "long-short factor portfolio", "factor crowding" (Dimensional / AQR territory); "information coefficient", "IC decay", "signal capacity estimate" as central output (Citadel territory); "yield curve regime", "duration positioning", "term premium" (PIMCO territory).

### SP-2 — virtu_execution structural rewrite (retail-honest schema; redesigned across R1 + R2 cross-checks)

R1 established that an institutional execution-microstructure schema is wrong for a €200/month long-only DCA investor. R2 (Delta Annexe Round 3) established that the first retail redesign still carried two **null-theatre** fields (`size_vs_liquidity{pct_of_adv}` — unfillable, the desk has no ADV data feed; `broker_accessible` — near-constant `true` for a UCITS-ETF-on-IBKR investor) and that `broker_accessible` **collided** with `de_shaw_statarb`'s already-shipped broker-accessibility responsibility. Both are dropped. The final schema centres on the one execution decision a monthly IBKR ETF buyer genuinely makes and can reason about without a live data feed: **order type and expected cost, where fixed broker commission dominates**.

**New `output_format` (structured YAML schema)** — 4 blocks:

```yaml
output_format:
  order_subject:
    instrument: string                    # the ETF / exposure being bought —
                                          # taken AS DECIDED upstream (Strike Team / structural selection);
                                          # virtu does NOT re-select the instrument
    side: buy|sell
    order_size_eur: number
  execution_method:
    order_type: limit|market              # limit-on-close excluded — concentrates the fill
                                          # at the widest-spread moment of the session
    limit_offset_bps: number              # bps from mid for a limit order; 0 for market
    timing_window: string                 # e.g. "mid-session; avoid first/last 15 min"
  expected_cost:
    spread_cost_bps: number               # half-spread paid
    commission_eur: number                # broker commission on this order (fixed minimum at retail size)
    commission_bps: number                # commission_eur / order_size_eur * 10000 — the size-sensitivity
    total_cost_bps: number                # = spread_cost_bps + commission_bps  (composition is defined; not free)
    cost_verdict: negligible|material|excessive   # negligible <25bps | material 25-75bps | excessive >75bps
  routing_note: string                    # MiFID II Article 27 best-execution reasoning — must state the
                                          # best-ex logic, not merely cite the article; venue routing is
                                          # broker-delegated (IBKR smart router)
```

**Not null theatre**: `expected_cost` is genuinely variable and decision-relevant — for a €200 IBKR ETF order, fixed commission (~60bps) dominates and `cost_verdict` will typically land `material`. That is the *point*: the persona's actionable output is "you pay ~60bps in commission every month; consolidating contributions (e.g. €600 quarterly) dilutes the fixed cost to ~20bps" — a real retail insight, surfaced by `commission_bps` making the size-sensitivity explicit.

**`system_prompt`** rewritten to mandate the 4-block schema; **remove the legacy free-prose "execution algorithm specification" output mandate**; require Virtu vocabulary ("implementation shortfall", "spread cost", "commission drag", "limit order", "participation rate", "MiFID II Article 27", "best execution"); and carry three constraint paragraphs:
- **Retail-scale honesty**: at €200/month order sizes, market impact is near-zero and fixed broker commission is the dominant cost — do not over-engineer an institutional multi-child TWAP; the honest levers are order type, timing, and contribution-consolidation.
- **Upstream-instrument boundary**: the instrument and its listing are decided upstream (Strike Team / structural-selection step — `de_shaw_statarb`'s domain). virtu does **not** re-select the instrument or re-verdict its broker-accessibility; it reasons only about how to place the order for the already-chosen instrument.
- **Best-execution reasoning**: `routing_note` must state the MiFID II Article 27 best-ex *reasoning* (why this order type/timing serves best execution), not merely name the article.

**`review_prompt` reframe** — new adversarial opening (frame option (i), user-selected): *"Assume this execution plan quietly bleeds the edge: the full spread is paid every month, the order is commission-heavy for its size, and the timing is careless — and that small avoidable costs compound against a monthly DCA investor over decades. Find where the edge leaks."* — 4 numbered checks: (1) **Cost Realism** (spread + commission as bps; is `commission_bps` shown and proportionate?), (2) **Order-Type & Timing** (limit vs market; is a market order paying the full spread needlessly?; auction-window avoidance), (3) **Size-vs-Liquidity** (a qualitative check — is the order ever large vs ADV? for a €200 monthly buy essentially never, but flag a lumpy rebalance / grown-NAV exception), (4) **Best-Ex & Routing** (MiFID II Article 27; venue routing broker-delegated; instrument taken as decided upstream). S-16 actionability template **+ the existing effort-estimate clause (`< 1 day / 1-3 days / > 1 week`) preserved verbatim**.

> Note — Size-vs-Liquidity survives as a *review-prompt check* (qualitative adversarial reasoning, no data feed required) even though it is **not** an `output_format` field (a numeric `pct_of_adv` field would be unfillable null theatre — R2-L1).

**Vocabulary discipline — forbidden phrases**: "market making", "inventory management", "quote adjustment", "adverse selection" as central output (Jane Street territory); "kill switch", "reconciliation engine", "state machine", "broker API integration" as central output (Millennium territory); "share-class selection", "structural arbitrage", "cross-listed dislocation" (D.E. Shaw territory).

### File-level manifest

| Action | File | Reason |
|---|---|---|
| MODIFY | `agents/renaissance_backtesting.yml` | S-17: rewrite `description`, `capabilities`, `output_format`, `system_prompt`, `review_prompt`. Preserve `name`, `role`, `firm`, `gate_consumption: false`, `analytical_framework: quantitative`. |
| MODIFY | `agents/virtu_execution.yml` | S-18: rewrite `description`, `capabilities`, `output_format`, `system_prompt`, `review_prompt`. Preserve `name`, `role`, `firm`, `gate_consumption: false`, `analytical_framework: flow-based`. |
| MODIFY | `PROGRESS.md` | S-17 + S-18 rows → DONE with proposal-016 link. |
| MODIFY | `CHANGELOG.md` | Entry under `[Unreleased] ### Changed`. |
| MODIFY | `proposals/README.md` | Index row 016 (DRAFT → DONE at close). |
| CREATE | `proposals/016-backups/renaissance_backtesting.original.yml` | Pre-rewrite backup. |
| CREATE | `proposals/016-backups/virtu_execution.original.yml` | Pre-rewrite backup. |

**Verify-only no-touch surface**: `backtesting/engine/config/agents.yml` references both files by `yml:` filename (lines 45, 61) and carries its own independent short `name:` labels — config-internal, not required to match the YAML `name:` field. Rewrite-in-place preserves the filename; the panel is unaffected. No edit.

### Out of scope

- **`AGENTS.md`** — not touched. The actionability *contract* is unchanged; output schemas live in the YAMLs. Verified observation: `AGENTS.md:121` groups `renaissance` under "Quant signal" with IC/decay/capacity fix-examples — slightly stale for a backtest-validation persona; fixing it re-opens doc scope. Carry-forward.
- **`de_shaw_statarb` structured-`output_format` rewrite** — Proposal 014 (S-19) deferred this as "a S-17/S-18-class HEAVY rewrite" (`PROGRESS.md:91`). Not in this proposal's scope.
- **CSV dedup** — the existing duplicate `virtu_execution` baseline row (`~/.claude/persona_eval_history.csv` lines 18 & 34, both 29/30) is not deduplicated by this session; that is the `~/.claude`-rooted governance-maintenance session's job. This proposal appends only (see DoD #19 for the date-disambiguation).
- **Renaming either file** — preserved to keep the Phase 7 panel slot keys intact.

## Definition of Done

1. `renaissance` `output_format` is a structured YAML mapping with all 7 blocks — `python -c "import yaml; d=yaml.safe_load(open('agents/renaissance_backtesting.yml')); assert isinstance(d['output_format'],dict) and {'rolling_sharpe_stability','out_of_sample','turnover_cost_ratio','overfitting_verdict'} <= set(d['output_format'])"` exits 0.
2. `virtu` `output_format` is a structured YAML mapping with all 4 blocks — `python -c "import yaml; d=yaml.safe_load(open('agents/virtu_execution.yml')); assert isinstance(d['output_format'],dict) and {'order_subject','execution_method','expected_cost','routing_note'} <= set(d['output_format'])"` exits 0. `expected_cost` contains `commission_bps`.
3. `renaissance` `system_prompt` mandates the 7-block schema and contains the Renaissance required-vocabulary terms (grep: "calibration window", "rolling Sharpe", "purged k-fold", "turnover-cost ratio").
4. `renaissance` `review_prompt` opens with the "single calibration window" frame and has exactly **6** numbered checks; check 2 is a named Multiple-Testing check; check 6 retains the distinctive PnL-construction content. Verified by a Python assertion that loads the YAML and asserts `"bar-lag attribution" in d['review_prompt']` and the review_prompt contains six `"\n1." … "\n6."` numbered markers (grep anchored to the `review_prompt` block, not a bare file-wide string — per MEMORY anti-pattern 2026-05-20).
5. `virtu` `system_prompt` mandates the 4-block schema, contains the Virtu required-vocabulary terms (grep: "implementation shortfall", "commission", "MiFID II Article 27"), and contains all three constraint paragraphs (retail-scale honesty; upstream-instrument boundary; best-execution reasoning).
6. `virtu` `review_prompt` opens with the option-(i) retail-honest cost frame, has 4 numbered checks, ends with the S-16 actionability template **and** the preserved effort-estimate clause (`grep -c "1-3 days" agents/virtu_execution.yml` ≥ 1).
7. **Critical-pattern invariant**: `grep -E "^(name|role|firm|gate_consumption|analytical_framework):"` on each file is byte-identical to its `proposals/016-backups/` original (`renaissance`: `quantitative`/`false`; `virtu`: `flow-based`/`false`).
8. **Vocabulary-bleed grep** clean — `renaissance`: zero matches for "factor premium", "tear sheet", "information coefficient", "yield curve regime"; `virtu`: zero matches for "market making", "inventory management", "kill switch", "reconciliation engine".
9. **Legacy-mandate removal** (negative grep) — `grep -cE "full Python code|quantitative research document" agents/renaissance_backtesting.yml` returns 0; `grep -c "execution algorithm specification" agents/virtu_execution.yml` returns 0. The pre-rewrite free-prose output contracts are gone.
10. `python -c "import yaml,glob; [yaml.safe_load(open(f)) for f in glob.glob('agents/*.yml')]"` exits 0 — all 17 YAMLs parse-valid (parse-validity only; not a schema-homogeneity claim).
11. **Median-of-3 eval**: `/persona-eval` run 3× on each of `renaissance` + `virtu` (original vs rewrite); median taken per dimension.
12. **Zero-regression kill switch (revert trigger)**: no 7-dimension score regresses on either persona; D2 (Adversarial Depth) does not drop. Any violation → revert that commit and iterate. A dimension regression takes precedence over any composite gain.
13. **Composite-threshold gate (iterate-or-escalate trigger)**: both rewrites score median composite ≥ 30. A rewrite that passes #12 but lands < 30 is iterated; if it cannot reach 30 after iteration, escalate to the user.
14. **D3 (Actionability) target**: median D3 ≥ 4 on both rewrites.
15. **Dual cold reviewer cross-check**: two independent Sonnet sub-agents, neither shown this proposal, the `persona-eval` rubric embedded inline (permission-block fallback per [[feedback_inline_rubric_fallback]]), score both rewrites — both rate every dimension ≥ original.
16. **Pair-diff cross-check**: a cold reviewer scores `renaissance`×`dimensional_factor_backtester` (role-twin backtester pair), `renaissance`×`citadel_alpha` (same-framework signal-domain peer), `virtu`×`jane_street_mm`, and `virtu`×`millennium_live_trading` — target ≥ 4/5 on all four pairs.
17. **Investor-fit dry-run (virtu) — non-default branch**: rewritten `virtu` is run against a deliberately commission-heavy scenario (a sub-€150 odd-lot order) engineered to warrant a non-`negligible` verdict. Pass: the persona correctly produces `cost_verdict: material` or `excessive` with `commission_bps` shown and an order-type + consolidation recommendation proportionate to retail scale. (Tests the guard at the live branch, not field-presence — per CLAUDE.md "test the guard at the entry-point".)
18. **Backtest-fit dry-run (renaissance) — non-default branch**: rewritten `renaissance` is run against a deliberately overfit sample backtest (tuned on one regime). Pass: the persona produces `overfitting_verdict: likely-overfit` (not `real-alpha`) with a populated `rolling_sharpe_stability` block showing `single-window-artefact` or `degrading`.
19. CSV rows appended to `~/.claude/persona_eval_history.csv` for `renaissance` + `virtu` post-rewrite, **dated 2026-05-21** — the post-016 date is the unambiguous like-for-like anchor for the 2026-08-15 quarterly re-eval, distinct from both 2026-05-15 baseline rows; **append only, no dedup**.
20. **Staged merge** — 3 commits (Commit 1 renaissance + backup; Commit 2 virtu + backup; Commit 3 docs); each invokes `/code-reviewer` and cites the verdict in the commit message. Per-commit kill switch per §"Architecture decision".
21. `PROGRESS.md` S-17 + S-18 rows → DONE with proposal-016 link; `CHANGELOG.md` `[Unreleased]` entry; `proposals/README.md` index row 016 → DONE.

## Adversarial Loophole Pass (L1–L22)

Living artefact — L1–L13 from the initial draft, L14–L16 from R1, L17–L22 from R2.

**L1 — renaissance↔dimensional pair-diff regression.** **Closed by** DoD #16 (≥4/5) + static-label fix (renaissance gets a structured schema; dimensional stays free-prose; distinct adversarial frames; distinct firms).

**L2 — virtu↔jane_street `flow-based` collision.** **Closed by** acceptance (pre-existing, not a regression); DoD #16 pair-diff is the gate; the retail-cost schema is structurally unlike Jane Street's market-making spec.

**L3 — Critical-pattern field mutation.** **Closed by** DoD #7 grep vs backups.

**L4 — Adversarial-depth regression on renaissance from check reframe.** **Closed by** the 6-check structure (adds Calibration-Window, demotes nothing — L20); DoD #4 + DoD #12 D2 no-regress.

**L5 — virtu effort-estimate clause silently dropped.** **Closed by** DoD #6.

**L6 — Schema over-engineered for a €200/month investor.** **Closed by** the SP-2 retail-honest schema (4 blocks, no institutional impact fields) + retail-scale honesty mandate + DoD #17.

**L7 — Eval same-session contamination.** **Closed by** cold sub-agent dispatch, inline rubric, no proposal awareness (DoD #15).

**L8 — Eval cost ceiling.** **Closed by** bounded scope: 2 personas, median-of-3 + dual cold + 4 pair-diffs ≈ 26–32 invocations.

**L9 — `purged k-fold` vocab shared with peers.** **Closed by** acceptance: a general López de Prado term — appears in `point72_ml_alpha` capabilities (ML cross-validation) and `dimensional_factor_backtester` `review_prompt:62` (backtest OOS). Not a firm-brand collision.

**L10 — Firm-brand continuity.** **Closed by** breaking output-schema name + adversarial framing; firm-brand continuity is an accepted residual (Proposal 010 L5 precedent).

**L11 — Phase 7 panel breakage.** **Closed by** rewrite-in-place — panel resolves by `yml:` filename; filename preserved.

**L12 — `broker_accessible` consumed nowhere.** **Superseded by L21** — the field is dropped entirely.

**L13 — Zero-regression vs composite-threshold gap.** **Superseded by L19** — see the explicit precedence rule.

**L14 — virtu `review_prompt` adversarial-depth regression (R1).** **Closed by** DoD #6 (≥4 checks + "Do not rubber-stamp" retention) + DoD #12 D2 no-regress.

**L15 — virtu schema retail-coherence / null-theatre (R1).** **Closed by** the SP-2 retail-honest redesign; further hardened by L17/L21.

**L16 — renaissance↔dimensional collision is panel-redundancy, not rotation-redundancy.** **Closed by** scoping: `renaissance_backtesting` is Phase-7-panel-only (not in any rotation pool — `backtesting/engine/config/agents.yml:15-21`); the DoD #16 pair-diff correctly addresses Phase 7 panel redundancy.

**L17 — `pct_of_adv` is unfillable by a War Room sub-agent (no ADV data feed; `docs/DATA_STANDARDS.md` provisions none).** A numeric ADV field would be left blank, hallucinated, or hardcoded `~0`. **Closed by** dropping the numeric `size_vs_liquidity` block from `output_format`; size-vs-liquidity survives only as a *qualitative* review-prompt check (check 3), which needs no data feed.

**L18 — `total_cost_bps` mis-composes a fixed euro commission with a proportional bps cost.** **Closed by** adding an explicit `commission_bps` field with a defined composition (`commission_eur / order_size_eur * 10000`) and `total_cost_bps = spread_cost_bps + commission_bps`; the size-sensitivity of fixed commission is now a first-class, visible field.

**L19 — DoD #12 (zero-regression) and DoD #13 (≥30 composite) can deadlock.** **Closed by** the explicit precedence rule in §"Architecture decision": #12 is the revert trigger, #13 is the iterate-or-escalate trigger; a dimension regression always reverts regardless of composite gain.

**L20 — renaissance reframe demoted "Multiple-Testing" from a named check to a sub-clause.** Multiple-testing correction ("best of many coin flips") is a distinct failure mode from single-window overfit. **Closed by** the 6-check structure: Calibration-Window Overfit (1) and Multiple-Testing & Selection Bias (2) are both named, distinct checks — D2 strictly improves vs the current 5-check prompt.

**L21 — `broker_accessible` is a near-constant-true dead field and collides with `de_shaw_statarb`'s shipped broker-accessibility verdict.** Verified: `de_shaw_statarb.yml:24` ("Share-class liquidity asymmetry and bid-ask spread analysis") and `:53` (the enforced `compliance_uncertain` memo header, "accessible on the broker(s)"). **Closed by** dropping `broker_accessible` from the virtu schema + the SP-2 upstream-instrument boundary paragraph (virtu does not re-verdict accessibility — that is the structural-selection step's job).

**L22 — `cost_verdict` enum lacked threshold anchors → non-reproducible eval.** **Closed by** anchoring the thresholds in the schema comment (`negligible <25bps | material 25-75bps | excessive >75bps`); the `system_prompt` notes that sub-€500 orders typically land `material` because commission is fixed.

## Core Team Review (A–F) — inline (no `persona-*.md` files in project; consistent with 009/010)

**A — Quant Architect.** APPROVE WITH CONDITIONS. *A1*: `gate_consumption: false` + `analytical_framework` preserved (DoD #7). *A2*: renaissance check #6 (PnL) content preserved (DoD #4). *A3*: legacy free-prose mandates verified removed (DoD #9 — added absorbing R2-L16).

**B — Portfolio Manager.** APPROVE. The retail-honest virtu schema surfaces a genuine €200-investor lever (commission-as-bps + consolidation). The two personas are the only sub-threshold Investments personas — genuine ROI.

**C — CTO.** APPROVE WITH CONDITIONS. *C1*: `proposals/016-backups/` created before any `agents/*.yml` write. *C2*: DoD #10 YAML-lint passes before each commit message.

**D — Risk Officer.** APPROVE WITH CONDITIONS. *D1*: DoD #12/#13 precedence rule (revert vs iterate-or-escalate) is explicit and the revert trigger dominates — confirmed in §"Architecture decision".

**E — The Trader.** APPROVE. Dropping the institutional impact fields and centring on order-type + commission-bps is the honest call. `commission_bps` making the fixed-cost size-sensitivity visible is exactly the lever a €200 DCA investor can act on.

**F — Compliance Officer.** APPROVE. `routing_note` mandating MiFID II Art.27 best-ex *reasoning* (not just the citation) is the right discipline. No new regulatory surface.

Not unanimous — A, C, D carry procedural conditions, all absorbed into DoD #4/#7/#9/#10/#12/#13.

## Delta Annexe — Round 1 (Core Team)

- **Absorbed**: A/C/D conditions → DoD #4, #7, #9, #10, #12, #13.
- **Resisted**: none — all Core Team conditions procedural.

## Delta Annexe — Round 2 (Isolated-Challenger cross-check, R1)

`Cross-Check path: isolated-challenger — reason: no external/alternate model API is configured in this environment (condition (a) of CLAUDE.md §3).`

R1 Isolated Challenger returned `flawed`, 15 L-items (5 tagged structural). Per CLAUDE.md §2 every claim was verified.
- **Absorbed**: virtu `review_prompt` is already post-010 quality → S-18 reframed honestly as an `output_format`+`system_prompt` lift with a `review_prompt` reframe (R1-L2). Institutional virtu schema wrong for a €200 investor → first retail redesign (R1-L6/L7). Staged-merge specified (R1-L8). Reversibility reworded, "idempotent" dropped (R1-L9). "verbatim" wording precision (R1-L11). de_shaw structured rewrite explicitly out of scope (R1-L12). `purged-k-fold` peer attribution corrected (R1-L14). AGENTS.md:121 cite verified (R1-L15). Pair-diff set widened to add `citadel_alpha` (R1-L4 breadth).
- **Resisted (refuted on verification)**: R1-L1 (29/30 unverifiable) — the baseline IS `~/.claude/persona_eval_history.csv:17-18`; the R1 sub-agent was sandbox-blind. R1-L3 (config pins `name:`) — the panel resolves by `yml:` filename. R1-L4 (renaissance×point72 both quantitative) — point72 is `behavioural`; renaissance is not in any rotation pool. R1-L5 (DoD count) — abbreviated-dispatch artefact. R1-L10 (`string` fields = free-prose) — enum scalars + narrative `string` fields are precedent-consistent (citadel/pimco).

## Delta Annexe — Round 3 (Isolated-Challenger cross-check, R2 — user-requested)

`Cross-Check path: isolated-challenger — reason: no external/alternate model API is configured (condition (a)). R2 dispatched at user request (approval option c).`

R2 Isolated Challenger — dispatched with the verified `~/.claude/persona_eval_history.csv` baseline facts embedded inline (so R2 was **not** sandbox-blind, unlike R1), and the redesigned retail-honest virtu SP-2 schema flagged as the priority review target. Returned `flawed`, 16 L-items (2 tagged structural: L3, L16). Per CLAUDE.md §2 every claim was verified before disposition.

**Absorbed (12 items — all verified genuine):**
- **R2-L1 (substantive) — `pct_of_adv` unfillable null theatre.** Verified: `docs/DATA_STANDARDS.md` provisions no ADV/volume data; Phase 5 is a yfinance *price* fetch. → numeric `size_vs_liquidity` block dropped from `output_format`; survives only as qualitative review-check 3. New L17.
- **R2-L2 (substantive) — `total_cost_bps` mis-composes fixed + proportional cost.** → explicit `commission_bps` field + defined composition formula added to `expected_cost`. New L18.
- **R2-L3 (structural) — `broker_accessible` collides with de_shaw's shipped accessibility verdict.** Verified `de_shaw_statarb.yml:24,53`. → `broker_accessible` dropped; SP-2 upstream-instrument-boundary paragraph added. New L21.
- **R2-L4 (substantive) — DoD dry-run gate passes on field presence not correctness.** → DoD #17/#18 rewritten to exercise a deliberately non-default branch (commission-heavy / overfit scenario). Aligns with CLAUDE.md "test the guard at the entry-point".
- **R2-L5 (substantive) — `frictionless_flag` "auto-fail" is an unenforced false promise.** → schema comment corrected to "persona MUST raise this as a HIGH-severity finding" (honest, matches the actionability contract; no fake mechanism claimed).
- **R2-L6 (substantive) — DoD #11/#13 deadlock.** → explicit precedence rule (revert vs iterate-or-escalate) in §"Architecture decision". New L19.
- **R2-L7 (craft) — `routing_note` regulatory citation not reasoning-enforced.** → SP-2 system_prompt now mandates `routing_note` state the best-ex *reasoning*, not just cite the article.
- **R2-L10 (substantive) — renaissance reframe demoted Multiple-Testing.** Verified against the current 5-check `review_prompt`. → renaissance `review_prompt` is now 6 checks; Multiple-Testing kept as a distinct named check. New L20.
- **R2-L11 (craft) — DoD #4 grep `bar-lag attribution` not anchored (the MEMORY 2026-05-20 anti-pattern).** → DoD #4 rewritten as a Python assertion anchored to the `review_prompt` block.
- **R2-L12 (substantive) — `cost_verdict` enum lacked threshold anchors → non-reproducible eval.** → thresholds anchored in the schema comment. New L22.
- **R2-L14 (substantive) — third virtu CSV row reads ambiguously against two existing baselines.** → DoD #19 dates the post-016 rows 2026-05-21; the date is the unambiguous like-for-like anchor (baselines are 2026-05-15).
- **R2-L16 (structural) — no DoD verified the legacy "full Python code" mandate is removed.** Verified `renaissance_backtesting.yml:44,46`. → DoD #9 added — negative grep confirming the legacy free-prose output contracts are gone from both files.

**Absorbed in part:**
- **R2-L13 (craft) — `limit-on-close` operationally questionable.** Absorbed: `limit-on-close` removed from the `order_type` enum (`limit|market`); it concentrates the fill at the widest-spread session moment, contradicting the `timing_window` guidance.
- **R2-L15 (craft) — Confidence labelled "post-adversarial-review" while R2 was still pending.** Absorbed: the Confidence section is relabelled to the honest post-R2 state below.

**Resisted:**
- **R2-L8 — `broker_accessible` dead field.** Not resisted in substance — subsumed by R2-L3's absorption (the field is dropped). Recorded for completeness.
- **R2-L9 (substantive) — mid-merge heterogeneous Phase 7 panel.** Resisted as a *gated* requirement: Phase 7 personas sign off independently with no inter-persona contract, so a mixed-vintage roster mid-merge is coherent (Proposal 010 had mid-merge states across commits 1/2a/2b without a gate). Absorbed as a documented acceptance in §"Architecture decision" (the three commits land in one session regardless).

**Challenger verdict disposition:** R2 `flawed`, 16 items, 2 structural (L3, L16) — **both absorbed**, neither required a change to §"File-level manifest" or the §DECOMPOSE sub-problems (SP-1/SP-2 are unchanged in identity; only the SP-2 schema *content* was refined). Therefore not a scope-change event under the /propose iteration discipline. R2 was a substantially higher-quality round than R1 (not sandbox-blind; 14 of 16 items verified genuine vs R1's 5 of 15) — the cross-check materially improved the proposal, especially the virtu schema. Per the iteration discipline, a `flawed` R2 with structural items absorbed-not-restructured is escalated to the user with the amended draft attached (approval option c→ now resolved; the user may elect R3 as a fresh option).

## Confidence

Per CLAUDE.md §Confidence-state distinction — these are **post-R2-cross-check, validated** numbers (survived two isolated-challenger rounds + independent verification of every L-item):
- **S-17 (renaissance):** 0.90 — the 6-check D2 improvement (L20) and the legacy-mandate-removal gate (L16) closed the two real renaissance risks; main residual is the renaissance↔dimensional pair-diff (DoD #16).
- **S-18 (virtu):** 0.89 — the R2 retail-honest redesign (4 honest blocks, null-theatre fields removed, de_shaw collision closed) is materially more coherent than either prior draft; main residual is whether the lean 4-block schema scores ≥30 (DoD #13).
- **Validated target** post DoD #15/#16 + user approval: ≥ 0.95.

## Reversibility

**FULLY REVERSIBLE** for all repository changes (YAML + docs; `git revert`; backups in `proposals/016-backups/`). The `~/.claude/persona_eval_history.csv` append is an additive write to a non-git global log file — manually removable, harmless if left; *not* idempotent and *not* undone by `git revert`. No IRREVERSIBLE step (no API mutation, no third-party data).

## Status Log

> Append-only.

- 2026-05-20 — DRAFT created. HEAVY tier, S-17 + S-18 bundle. Core Team A–F inline review. R1 Isolated-Challenger cross-check (`flawed`, 15 L-items); Delta Annexe Round 2 records verifications. SP-2 virtu schema redesigned to retail-honest fields absorbing R1-L6/L7.
- 2026-05-21 — R2 Isolated-Challenger cross-check at user request (approval option c), dispatched with the `~/.claude/` baseline facts embedded inline. Returned `flawed`, 16 L-items (2 structural). 14 absorbed (incl. both structural — null-theatre `pct_of_adv` and `broker_accessible` dropped; `de_shaw` collision closed; `commission_bps` composition added; renaissance review_prompt → 6 checks restoring Multiple-Testing; legacy-mandate-removal DoD added; #12/#13 deadlock resolved with explicit precedence; `cost_verdict` thresholds anchored; DoD grep anchored). 2 resisted-in-part / documented. L-pass extended to L22. Confidence relabelled to validated post-R2 state. Awaiting user approval.
- 2026-05-21 — R3 Isolated-Challenger cross-check at user request (approval option c), CSV baseline embedded inline, post-R2 4-block virtu schema as priority target. Returned `flawed`, 22 L-items, **1 structural (L6) — on virtu**: the virtu schema, cut 6→4 blocks across R1/R2, may fall below the HEAVY "structured schema = new architecture" justification for S-18; sharpened by substantive L2/L3 — virtu `expected_cost`'s inputs (`spread_cost_bps` live bid-ask spread; `commission_eur` broker fee schedule) are not sourceable by a data-less War Room sub-agent (the same test R2 used to kill `pct_of_adv`). renaissance carried **zero structural items** across R1/R2/R3 (R3 renaissance items are DoD-level/craft). Per the user's pre-stated R3 stop-rule (flawed + verified structural item on virtu → stop iterating the bundle), **bundle iteration halted; no Delta Annexe Round 4 absorption performed**. Split confirmed: S-17 (renaissance) proceeds standalone; S-18 (virtu) continues solo as a re-architecture. Re-scope plan to be proposed before any file changes.
- 2026-05-21 — Split executed (user decision: Option B). Status → **SUPERSEDED**. 016 is frozen as the bundle's historical record — its 3-round cross-check audit trail is bundle-shaped and is retained intact, not stripped (same pattern as 013→029). S-17 (renaissance — 0 structural items across R1/R2/R3) re-proposed clean and self-contained as **Proposal 017**, reproducing the validated design and absorbing the minor R3 renaissance items (L8/L9/L11/L12/L18/L20/L21); no new Challenger round (cross-check satisfied by the inherited R1/R2/R3 lineage). S-18 (virtu) deferred to a future **Proposal 018** virtu re-architecture. The full R3 Challenger output (all 22 L-items) is recorded verbatim in the Appendix below — **recorded, not absorbed; 018 design input** — because it was transcript-only and would otherwise be lost at the next context boundary.

## AWAITING USER APPROVAL

No file modifications, commits, or eval dispatches until explicit user approval.

- **(a) APPROVE as drafted** — proceed to Commit 1 (renaissance), then Commit 2 (virtu), then Commit 3 (docs), under the staged plan + per-commit kill switch.
- **(b) APPROVE WITH AMENDMENTS** — specify DoD / schema / scope changes.
- **(c) REQUEST R3 CROSS-CHECK** — dispatch a fresh Isolated Challenger against this R2-amended draft before approval.
- **(d) DEFER** — keep as DRAFT.
- **(e) REJECT** — re-scope or split.

> **Resolution (2026-05-21):** option (e) — split. See Status Log. This section is retained as the historical record of the proposal's state at supersession; it is not a live decision point.

---

## Appendix — R3 Isolated-Challenger Output (recorded, NOT absorbed — Proposal 018 design input)

> **Status: recorded, not absorbed.** Per the user's R3 stop-rule, bundle iteration halted at R3 — these 22 L-items were NOT folded into a Delta Annexe Round 4. They are preserved verbatim here because the round was transcript-only. **Renaissance items L8, L9, L11, L12, L18, L20, L21 are absorbed into Proposal 017** (renaissance standalone). **All virtu-surface items are carried forward as design input to Proposal 018** (virtu re-architecture). The trailing "Closed by TBD" phrase on each item is the Challenger's own format and is moot here (no Round 4 occurred).

R3 dispatch: fresh Isolated Challenger, `~/.claude/persona_eval_history.csv` baseline (lines 17-18) embedded inline, post-R2 4-block virtu schema as priority target. Verdict: `CHALLENGER STRUCTURAL: flawed` (1 structural item, L6).

**L1 [substantive] — `cost_verdict` band is pinned to a single value for the in-scope investor.** For a €200 IBKR ETF order, fixed commission alone is ~60bps; the band is `negligible <25bps | material 25-75bps | excessive >75bps`, so the default-path investor sees `material` every month with near-zero variance. The decision-relevant signal (when to consolidate) lives in `commission_bps`, not `cost_verdict` — the latter is a derived restatement, not an independent decision field. Same near-constant null-theatre failure mode R2 closed for `pct_of_adv`/`broker_accessible`, one schema-block over.

**L2 [substantive] — `commission_eur` is not sourceable by a War Room sub-agent without a broker fee schedule.** R2 killed `pct_of_adv` because the desk has no data feed and `docs/DATA_STANDARDS.md` provisions none; the identical test was never applied to `commission_eur`. IBKR's commission is a tiered fee schedule not derivable from a yfinance price fetch. A sub-agent will hardcode/guess/hallucinate it. The whole `expected_cost` block derives from it.

**L3 [substantive] — `spread_cost_bps` has the same unsourceable-input problem and no DoD coverage.** Bid-ask spread for a listing at a moment is live order-book data; Phase 5 fetches prices, not quotes. `total_cost_bps = spread_cost_bps + commission_bps` composes two unsourceable operands. R2's L18 fixed the arithmetic but not the fillability.

**L4 [substantive] — DoD #17's pass condition is unfalsifiable given L1.** DoD #17 engineers a sub-€150 order to "warrant a non-`negligible` verdict" — but per L1 every retail-scale order lands `material`/`excessive` anyway. A persona mechanically emitting `material` passes without performing cost reasoning. A genuine guard test needs an input engineered to land `negligible` (a consolidated €2,000+ order) so the persona must discriminate.

**L5 [substantive] — the upstream-instrument boundary relabels the de_shaw collision but leaves a residual spread/liquidity overlap.** `de_shaw_statarb.yml:24` capability #8 is "Share-class liquidity asymmetry and bid-ask spread analysis". virtu's surviving `spread_cost_bps` + review-check #1 still require virtu to reason about bid-ask spread on the chosen listing. Two Phase 7 panel members both produce a bid-ask-spread judgement on the same instrument — de_shaw's feeds selection, virtu's feeds execution cost. Narrower than the `broker_accessible` collision but genuine and un-disclaimed.

**L6 [structural] — the post-R2 4-block virtu schema has shrunk below the HEAVY tier justification.** Of the 4 blocks: `order_subject` is three trivial pass-through fields virtu does not compute; `routing_note` is a free-prose string; `execution_method` is order_type + offset + a free-prose timing string; only `expected_cost` is computational — and per L1/L2/L3 its inputs are unsourceable and its verdict near-constant. That is closer to a MEDIUM `output_format` tidy than a HEAVY "new architecture". §Tier and Approach-A confidence 0.88 assume two substantial schemas; if virtu's is lightweight the bundle's HEAVY classification is carried entirely by renaissance.

**L7 [substantive] — DoD #13's "≥30 composite" gate can pass while the lean virtu schema fails its objective.** A one-point lift over baseline-29 clears #13 — achievable via a single dimension nudge (e.g. D3 from the pre-existing S-16 template) while the new `output_format` schema contributes nothing. DoD #12 + #13 + #14 can all pass on a virtu rewrite whose schema is the L1/L2/L3 problem; no DoD asserts the schema itself improved the eval, distinct from the review_prompt reframe.

**L8 [substantive] — the kill-switch precedence rule has an unhandled third state.** §Architecture-decision defines revert (dimension regression) and iterate-or-escalate (≥30 fail). It does not define what happens if iteration cannot both fix a regression AND keep the gains (genuine tension — the schema that lifts D2 may be the one that drops D3). DoD #13's escalation path covers only the composite trigger, not the regression trigger. A rewrite that regresses D3 unrecoverably has no defined terminal state.

**L9 [substantive] — DoD #16 pair-diff target ≥4/5 is asserted without a per-pair baseline.** No current pair-diff baseline is recorded. If renaissance×dimensional currently scores 4/5, passing "≥4/5" demonstrates nothing; if it scores 2/5, ≥4/5 may be unreachable in one rewrite. The proposal names this pair as the top S-17 residual risk but the DoD does not anchor it — a floating bar.

**L10 [substantive] — `routing_note` MiFID II Art.27 best-ex is the same un-enforced citation pattern, surviving as free-prose `string`.** R2-L7 was absorbed by a `system_prompt` mandate, but the field stays `routing_note: string` and DoD #5 only greps `system_prompt` for the literal token. A persona can emit `routing_note: "Routing complies with MiFID II Article 27."` and satisfy every DoD — the exact failure R2-L7 named. No DoD exercises a virtu output and asserts substantive best-ex logic.

**L11 [craft] — DoD #4's "six numbered markers" assertion is under-specified.** Counting `\n1.`–`\n6.` substrings within the `review_prompt` block does not assert they are the six review checks (vs five checks plus a `6.` inside an example). The assertion should match the six check names, not bare ordinals.

**L12 [craft] — `frictionless_flag` "HIGH-severity finding" directive sits in a YAML comment, invisible to `yaml.safe_load` and to consumers.** A behavioural MUST in a non-parsed comment is enforced by nothing and grepped by no DoD. If load-bearing it belongs in `system_prompt`; if documentation it should not read as a MUST.

**L13 [substantive] — DoD #19's CSV append writes outside the repo sandbox with no precondition that the delegated implementation-agent can reach it.** The Sonnet implementation-agent's cwd is the project sandbox; sub-agents can be permission-blocked from `~/.claude/` paths. A completion gate that may be structurally unreachable by the executing agent needs an explicit owner (orchestrator fallback) and a defined behaviour on append failure.

**L14 [craft] — "median-of-3" tie/dispersion handling is unspecified.** DoD #11 takes "median per dimension"; DoD #13 gates on "median composite". Sum-of-per-dimension-medians vs median-of-composite-totals are different numbers; the proposal uses both phrasings without reconciling them, and says nothing about wide run dispersion (e.g. D2 = 3/4/5).

**L15 [substantive] — no DoD verifies the rewritten `virtu` `capabilities:` list is consistent with the retail-honest schema.** `virtu_execution.yml:15-22` `capabilities` lists "TWAP and VWAP algorithm design", "Iceberg order logic", "Smart order routing", "Slippage measurement and market impact modeling". `capabilities` is in the rewrite manifest, but no DoD checks it does not still advertise institutional functions the new schema repudiates. The DoD #8 forbidden-vocab grep does not catch "TWAP"/"VWAP"/"iceberg" surviving in `capabilities` — a sibling-inconsistency.

**L16 [substantive] — `order_type: limit|market` with mandatory `limit_offset_bps` creates an unfillable-field condition on the `market` branch.** When `order_type: market`, `limit_offset_bps` is forced to a meaningless `0` — a field existing only to carry a sentinel on one branch. A milder instance of the near-constant-field pattern R2 killed for `broker_accessible`; cleaner if `limit_offset_bps` were omittable/null on the market branch.

**L17 [craft] — §Out-of-scope's `AGENTS.md:121` carry-forward understates the defect.** Post-S-17, renaissance is a backtest-validity persona, but `AGENTS.md:121` will still direct its actionability fixes toward "IC / decay / capacity" vocabulary the rewritten persona's `review_prompt` actively forbids. "Slightly stale" understates "actively contradictory". At minimum it should be logged as a roadmap item (an S-NN), not just an Out-of-scope sentence.

**L18 [substantive] — DoD #18 (renaissance backtest-fit dry-run) does not test the discriminating branch.** It runs renaissance against a deliberately overfit backtest and passes on `overfitting_verdict: likely-overfit` — the positive-detection branch only. A persona hardcoded to emit `likely-overfit` passes. The genuine guard test must also feed a genuinely sound backtest and assert `real-alpha` (the no-false-alarm path). A backtest-validity persona that flags everything is as useless as one that flags nothing.

**L19 [craft] — "mid-merge state" acceptance contradicts its own premise within one paragraph.** §Architecture-decision asserts the three commits "land within a single implementation session" AND reasons about a War Room running between commits. State plainly one or the other — not "intended" + a hedge.

**L20 [substantive] — `overfitting_verdict` and `stability_verdict` are two independent holistic enums with no defined relationship.** A persona can emit `stability_verdict: single-window-artefact` alongside `overfitting_verdict: real-alpha` — self-contradictory, caught by no DoD. The schema needs an explicit coherence rule (e.g. `overfitting_verdict` may not be `real-alpha` if `stability_verdict` is `single-window-artefact`).

**L21 [craft] — §Tier's "same HEAVY trigger as Proposal 010 S-15" parallel is asserted, not quoted inline.** A reader cannot check the parallel from within this proposal. Given L6, leaning on the 010 precedent without quoting 010's actual trigger means the precedent could itself be mis-cited.

**L22 [substantive] — DoD #15's "both rate every dimension ≥ original" can be satisfied by a flat (zero-improvement) result.** `≥` includes equal, which only verifies non-regression — already covered by DoD #12. No DoD has a cold reviewer confirm *improvement* attributable to the schema. Combined with L7, the gate battery can wave through a virtu rewrite that is structurally lighter and demonstrably no better than the free-prose original.

**Challenger stopping condition (verbatim):** "Stopping at L22 ... I have genuinely exhausted distinct loopholes." **Verdict:** `CHALLENGER STRUCTURAL: flawed` — one structural item (L6); the substantive cluster (L1–L5, L7, L9, L10, L13, L15, L16, L18, L20, L22) concentrates on the freshest, least-reviewed surface (the virtu `expected_cost` block and the DoD gate battery).
