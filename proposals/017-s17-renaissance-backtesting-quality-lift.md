---
id: 017
title: S-17 — renaissance_backtesting persona quality lift
status: DONE
owner: Daniel
opened: 2026-05-21
updated: 2026-05-21
tags: [governance, personas, persona-eval, renaissance_backtesting]
supersedes_context: 016
---

# 017 — S-17: renaissance_backtesting Persona Quality Lift

## Provenance

This proposal is the **standalone S-17 successor** to the superseded bundle [Proposal 016](016-s17-s18-persona-quality-lift.md). 016 bundled S-17 (renaissance) with S-18 (virtu); three isolated-challenger cross-check rounds (R1/R2/R3, 2026-05-20/21) found the **virtu** half structurally unconverged (R3 structural item L6 + an unsourceable-input cluster), while **renaissance carried zero structural items across all three rounds** — R3's renaissance findings were DoD-level and craft only. Per the user's R3 stop-rule the bundle was split: 016 → SUPERSEDED (frozen as the bundle's historical record, full R3 output preserved in its Appendix as Proposal 018 design input); S-17 re-proposed clean here; S-18 deferred to a future Proposal 018 virtu re-architecture.

**Cross-check inheritance** — the renaissance design below is the design that survived 016's R1/R2/R3 (0 structural items ×3). This proposal **reproduces that validated design** and additionally **absorbs the minor R3 renaissance items** (016 Appendix L8, L9, L11, L12, L18, L20, L21 — all DoD-level/craft; none reopens the schema/system_prompt/review_prompt design). See §"R3 absorption" and §"Dual-Model Cross-Check".

## Tier: HEAVY — explicit reasoning (no silent re-tier)

The superseded bundle was HEAVY. This standalone proposal is **also HEAVY**. The governing classifier is **new architecture**, not file count:
- **New architecture** — replaces a free-prose `output_format` blob with a structured YAML schema. This is the same HEAVY trigger Proposal 010 cited for the `citadel_alpha` S-15 rewrite. Quoting [Proposal 010](010-s15-s16-persona-quality-lift.md) §Tier verbatim (016 Appendix L21 — quote inline, do not assert the parallel): *"1 structural rewrite (`agents/citadel_alpha.yml`) … Touches `agents/*.yml` (critical pattern …)."* — 010 classified a single-file structured-schema persona rewrite as a HEAVY-contributing trigger.
- Eval-gated kill-switch infrastructure (median-of-3 + dual cold reviewer + dry-run + zero-regression revert).
- `renaissance_backtesting` is a slot in the 15-agent Phase 7 sign-off panel (`backtesting/engine/config/agents.yml:44-45`) — blast radius onto the panel.
- Touches `agents/*.yml` — a critical-pattern surface per `.claude/review-patterns.md` §Critical Patterns.

File count alone (~6 operations) would read MEDIUM; the new-architecture trigger fires independently of file count and is the governing classifier. **A MEDIUM case is not made** — the structured-schema introduction is genuine new architecture. HEAVY retained.

## Summary

Lift `agents/renaissance_backtesting.yml` from its 2026-05-15 sub-threshold eval score: replace the free-prose `output_format` with a structured backtest-validity schema; rewrite `system_prompt` to mandate the schema and drop the contradictory legacy "full Python code" output mandate; reframe `review_prompt` with a Renaissance-specific adversarial frame and a sixth adversarial check; add vocabulary discipline against `dimensional_factor_backtester`.

**Baseline (verified)** — `~/.claude/persona_eval_history.csv` line 17 (2026-05-15): `renaissance_backtesting,investments,29,30,false,opus-4.7` — score 29, threshold 30, `passed=false`.

## Motivation / Problem

Read of `agents/renaissance_backtesting.yml` (2026-05-20):
- `output_format` is free-prose: *"Quantitative research document with full Python code, statistical validation methodology, and result interpretation guidelines."* No structured schema — unlike the post-009/010/014 baseline (`citadel_alpha`, `pimco_curve_strategist` carry structured YAML schemas).
- A backtesting-engine researcher whose output enforces nothing about rolling-Sharpe stability, OOS method, transaction-cost realism, or turnover drag is a fictional Renaissance — those are the firm's own domain primitives.
- `system_prompt` lines 44, 46 mandate "Complete Python backtesting code" and "Format as a quantitative research document with full Python code" — an output contract that *contradicts* a structured-schema rewrite. The rewrite must remove this legacy paragraph.
- `review_prompt` is already post-010 quality (adversarial frame + 5 numbered checks + the S-16 actionability template). The change is a **reframe + one added check**, not a from-scratch rewrite.
- Stale provenance comment `# Generated: 2026-03-01`.

## Proposal

### Architecture decision (HEAVY — ≥2 approaches)

> **Approach A — Domain-native structured schema, rewrite-in-place.** A schema built from Renaissance's own backtest-validation primitives (citadel S-15 / pimco S-19 precedent). — **Confidence 0.90** (validated — survived 016 R1/R2/R3).
> Pros: schema fits the domain; breaks the dominant pair-diff lever (static output-schema name); rewrite-in-place preserves the Phase 7 panel filename key.
> Cons: one schema to design.
>
> **Approach B — Minimal `output_format` tidy** (convert the free-prose blob to a short bulleted list, no structured schema). — **Confidence 0.40**
> Pros: trivial.
> Cons: does not lift the persona — the eval failure is the *absence* of enforced domain primitives, which a bulleted list does not supply; reproduces the 29/30 failure mode.
>
> **Chosen: A.**

### output_format — structured YAML schema (7 blocks)

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
    frictionless_flag: boolean            # true = transaction costs were not modelled
                                          # (the system_prompt mandates how the persona must act on this)
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

`overfitting_verdict` is an enum scalar (consistent with citadel's `category:` and pimco's stance enums) — a holistic verdict the six review-checks inform.

> **R3-L12 absorption** — the `frictionless_flag` "must raise as HIGH-severity" directive is **not** carried in the YAML comment (a YAML comment is invisible to `yaml.safe_load` and to the persona-delivery path). The behavioural MUST is placed in `system_prompt` (parsed, delivered). The schema comment above is plain documentation only.

### system_prompt — rewrite

- Mandate the 7-block schema; **remove the legacy "full Python code / quantitative research document" output mandate**.
- Require Renaissance vocabulary: "calibration window", "curve-fit noise", "rolling Sharpe stability", "purged k-fold", "out-of-sample", "turnover-cost ratio", "regime-conditioned hit-rate", "look-ahead leakage", "survivorship", "walk-forward".
- **R3-L12** — carry the directive: *"If `transaction_cost_realism.frictionless_flag` is `true`, you MUST raise a HIGH-severity finding — a frictionless backtest is not a deployable result."*
- **R3-L20** — carry the verdict-coherence rule: *"`overfitting_verdict` may NOT be `real-alpha` when `rolling_sharpe_stability.stability_verdict` is `single-window-artefact`; the two verdict fields must be mutually consistent."*

### review_prompt — reframe (6 numbered checks)

New adversarial opening: *"Assume the backtest is overfit to a single calibration window: it was tuned on one historical regime and the parameters will not survive a regime it never saw. Prove the alpha is a calibration artefact."*

The reframe **adds** Calibration-Window Overfit and **keeps Multiple-Testing as a distinct named check** (016 R2-L20 — multiple-testing correction is a different failure mode from single-window overfit; D2 adversarial depth strictly improves vs the current 5-check prompt):
1. **Calibration-Window Overfit** — single-regime tuning; rolling 12-month Sharpe collapse outside the calibration window.
2. **Multiple-Testing & Selection Bias** — how many variants were tried; deflated Sharpe (Bailey & López de Prado); "best of many coin flips".
3. **Look-Ahead & Survivorship Leakage** — restated fundamentals, survivorship-cleaned universes, future-dated corporate actions.
4. **Transaction-Cost & Turnover Realism** — frictionless flag; turnover-cost ratio vs gross alpha.
5. **Out-of-Sample Discipline** — purged k-fold / walk-forward / holdout; OOS-to-IS ratio; OOS-window peeking.
6. **PnL Construction & Attribution Integrity** — **content preserved verbatim from the current file's check #5** (bar-lag attribution, geometric-vs-arithmetic aggregation, compounding bugs).

S-16 actionability template retained.

### Vocabulary discipline — forbidden phrases

"factor premium", "tear sheet", "long-short factor portfolio", "factor crowding" (Dimensional / AQR territory); "information coefficient", "IC decay", "signal capacity estimate" as central output (Citadel territory); "yield curve regime", "duration positioning", "term premium" (PIMCO territory).

### R3 absorption (016 Appendix items)

Directed by the user — 7 minor R3 renaissance items, all DoD/craft, none reopening the design:
- **L8** — kill-switch terminal state → DoD #12 gains an explicit escalate-to-user branch for an unrecoverable regression.
- **L9** — pair-diff floating bar → DoD #9 records the pre-rewrite pair-diff baseline *before* scoring the rewrite.
- **L11** — DoD grep precision → DoD #4 asserts the six review-check *names*, not bare `\nN.` ordinals.
- **L12** — directive in a YAML comment → moved to `system_prompt` (see §system_prompt).
- **L18** — one-branch dry-run → DoD #15 tests both the overfit-detection AND the genuinely-sound (`real-alpha`, no-false-alarm) branch.
- **L20** — independent verdict enums → verdict-coherence rule added to `system_prompt`.
- **L21** — unquoted tier precedent → Proposal 010's HEAVY trigger quoted inline in §Tier.

**Transparency note (non-silent scope):** three 016 Appendix items were *not* in the directed 7 but are renaissance-applicable and have been absorbed — flagged here so the inclusion is not silent: **L13** (CSV-append owner — sub-agents can be `~/.claude/` permission-blocked) → DoD #16; **L14** (median-of-3 arithmetic undefined) → DoD #10; **L17** (`AGENTS.md:121` renaissance archetype line becomes *actively contradictory* with the rewritten persona) → DoD #17, logged as a new Staged-Improvement roadmap row. All three are trivial DoD-hygiene / roadmap-logging closures, not design changes.

### File-level manifest

| Action | File | Reason |
|---|---|---|
| MODIFY | `agents/renaissance_backtesting.yml` | S-17 rewrite: `description`, `capabilities`, `output_format`, `system_prompt`, `review_prompt`. Preserve `name`, `role`, `firm`, `gate_consumption: false`, `analytical_framework: quantitative`. |
| MODIFY | `PROGRESS.md` | S-17 row → DONE with proposal-017 link; S-18 row annotated "deferred to Proposal 018 (virtu re-architecture)". |
| MODIFY | `CHANGELOG.md` | Entry under `[Unreleased] ### Changed`. |
| MODIFY | `proposals/README.md` | Index row 017 (DRAFT → DONE at close). |
| CREATE | `proposals/017-backups/renaissance_backtesting.original.yml` | Pre-rewrite backup. |

**Verify-only no-touch surface**: `backtesting/engine/config/agents.yml` references the file by `yml:` filename (line 45); rewrite-in-place preserves it. No edit.

### Out of scope

- **`virtu_execution`** — deferred to Proposal 018 (virtu re-architecture); the 016 Appendix carries the R3 virtu cluster as 018 design input.
- **`AGENTS.md`** — not touched. 016 Appendix L17 noted `AGENTS.md:121` groups `renaissance` under "Quant signal" with IC/decay/capacity fix-examples, which becomes *actively contradictory* with the rewritten persona (its `review_prompt` forbids that vocabulary). **Per L17 this is logged as a roadmap item** — see DoD #17 (a new `S-NN` row is added to `PROGRESS.md` Staged Improvements rather than left as a buried sentence). The AGENTS.md edit itself is deferred (re-opens doc scope).
- **CSV dedup** — the existing duplicate `virtu_execution` baseline rows are not touched (the `~/.claude`-rooted governance-maintenance session's job).

## Definition of Done

1. `renaissance` `output_format` is a structured YAML mapping with all 7 blocks — `python -c "import yaml; d=yaml.safe_load(open('agents/renaissance_backtesting.yml')); assert isinstance(d['output_format'],dict) and {'backtest_subject','rolling_sharpe_stability','out_of_sample','transaction_cost_realism','turnover_cost_ratio','regime_conditioned_hit_rate','overfitting_verdict'} <= set(d['output_format'])"` exits 0.
2. `system_prompt` mandates the 7-block schema and contains the Renaissance required-vocabulary terms (grep: "calibration window", "rolling Sharpe", "purged k-fold", "turnover-cost ratio").
3. `system_prompt` contains (a) the `frictionless_flag` → HIGH-severity directive and (b) the `overfitting_verdict` / `stability_verdict` coherence rule (grep both). Neither directive is a YAML comment.
4. `review_prompt` opens with the "single calibration window" frame and contains six named checks — a Python assertion loads the YAML and asserts all of `{"Calibration-Window Overfit","Multiple-Testing & Selection Bias","Look-Ahead & Survivorship Leakage","Transaction-Cost & Turnover Realism","Out-of-Sample Discipline","PnL Construction & Attribution Integrity"}` appear in `d['review_prompt']`, and `"bar-lag attribution" in d['review_prompt']` (matches check *names*, not bare ordinals — 016 R3-L11).
5. **Critical-pattern invariant**: `grep -E "^(name|role|firm|gate_consumption|analytical_framework):" agents/renaissance_backtesting.yml` is byte-identical to `proposals/017-backups/renaissance_backtesting.original.yml` (`quantitative`/`false`).
6. **Vocabulary-bleed grep** clean — the forbidden phrases ("factor premium", "tear sheet", "information coefficient", "yield curve regime", "long-short factor") appear **only** on the single `system_prompt` forbidden-phrases *declaration* line and nowhere else: `grep -niE "factor premium|tear sheet|information coefficient|yield curve regime|long-short factor" agents/renaissance_backtesting.yml` returns exactly one line, and that line begins with "- Forbidden phrases". (Re-specified after `/code-reviewer` NOTE — a bare `grep -c … = 0` misfires because the declaration line legitimately quotes the phrases; MEMORY anti-pattern 2026-05-20.)
7. **Legacy-mandate removal** — `grep -cE "full Python code|quantitative research document" agents/renaissance_backtesting.yml` returns 0.
8. `python -c "import yaml,glob; [yaml.safe_load(open(f)) for f in glob.glob('agents/*.yml')]"` exits 0 — all 17 YAMLs parse-valid (parse-validity only).
9. **Pair-diff cross-check** — a cold reviewer **first records the pre-rewrite pair-diff baseline** for `renaissance`×`dimensional_factor_backtester` (role-twin backtester pair) and `renaissance`×`citadel_alpha` (same-framework signal-domain peer); the rewrite must then score ≥ 4/5 on both pairs **and** ≥ the recorded pre-rewrite baseline (016 R3-L9 — no floating bar).
10. **Median-of-3 eval** — `/persona-eval` run 3× on `renaissance` (original vs rewrite). "Median" is defined (016 R3-L14): the per-dimension score is the median of the 3 runs; the composite is the **sum of the per-dimension medians**.
11. **Zero-regression kill switch (revert trigger)** — no 7-dimension median score regresses; D2 (Adversarial Depth) does not drop. Any violation → revert the commit and iterate.
12. **Composite-threshold gate** — median composite ≥ 30. A rewrite that passes #11 but lands < 30 is iterated. **Terminal-state branch (016 R3-L8)**: if iteration cannot both clear a dimension regression AND reach ≥ 30 composite — the two in genuine tension — the orchestrator **escalates to the user**; it does not loop indefinitely or ship a regression.
13. **D3 (Actionability) target** — median D3 ≥ 4.
14. **Dual cold reviewer cross-check** — two independent Sonnet sub-agents, neither shown this proposal, the `persona-eval` rubric embedded inline (permission-block fallback per [[feedback_inline_rubric_fallback]]) — both rate every dimension ≥ original.
15. **Backtest-fit dry-run — both branches (016 R3-L18)** — rewritten `renaissance` is run against (a) a deliberately overfit sample backtest → must produce `overfitting_verdict: likely-overfit` + `stability_verdict: single-window-artefact|degrading`; and (b) a genuinely sound sample backtest (stable rolling Sharpe, clean purged-k-fold, modelled costs) → must produce `overfitting_verdict: real-alpha`. The persona must *discriminate*, not cry wolf.
16. **CSV row appended** to `~/.claude/persona_eval_history.csv` for `renaissance` post-rewrite, dated 2026-05-21. **The orchestrator performs this write** (016 R3-L13 — the delegated Sonnet implementation-agent may be permission-blocked from `~/.claude/`); if the write fails it is retried by the orchestrator, not silently skipped.
17. `PROGRESS.md` S-17 row → DONE with proposal-017 link; S-18 row annotated as deferred to Proposal 018; **a new Staged-Improvement row is added** for the `AGENTS.md:121` renaissance archetype-line correction (016 R3-L17 — logged as a roadmap item, not a buried sentence). `CHANGELOG.md` `[Unreleased]` entry; `proposals/README.md` index row 017 → DONE.
18. **Staged merge** — 2 commits (Commit 1 `renaissance_backtesting.yml` + backup; Commit 2 docs); each invokes `/code-reviewer` and cites the verdict.

## Adversarial Loophole Pass (L1–L11)

Renaissance-relevant items, carried from the 016 L-pass and renumbered, plus the R3 absorptions.

**L1 — renaissance↔dimensional pair-diff regression.** Two backtester personas; a structured schema could pull output shape closer. **Closed by** DoD #9 (recorded baseline + ≥4/5) + static-label fix (renaissance gets a structured schema; dimensional stays free-prose; distinct adversarial frames; distinct firms).
**L2 — Critical-pattern field mutation.** **Closed by** DoD #5 grep vs backup.
**L3 — Adversarial-depth regression from the review_prompt reframe.** **Closed by** the 6-check structure (adds Calibration-Window, demotes nothing — Multiple-Testing kept as a named check); DoD #4 + DoD #11 D2 no-regress.
**L4 — Eval same-session contamination.** **Closed by** cold sub-agent dispatch, inline rubric, no proposal awareness (DoD #14).
**L5 — `purged k-fold` vocab shared with peers.** **Closed by** acceptance: a general López de Prado term — appears in `point72_ml_alpha` capabilities and `dimensional_factor_backtester` `review_prompt:62`. Not a firm-brand collision.
**L6 — Firm-brand continuity.** renaissance keeps `firm: Renaissance Technologies`. **Closed by** breaking output-schema name + adversarial framing; firm-brand continuity is an accepted residual (Proposal 010 L5 precedent).
**L7 — Phase 7 panel breakage.** **Closed by** rewrite-in-place — the panel resolves by `yml:` filename (`backtesting/engine/config/agents.yml:44-45`); filename preserved.
**L8 — Legacy "full Python code" mandate survives the rewrite.** A structured schema + a "full Python code" mandate are contradictory output contracts. **Closed by** DoD #7 negative grep.
**L9 — `overfitting_verdict` / `stability_verdict` incoherence (016 R3-L20).** Two independent holistic enums could contradict. **Closed by** the `system_prompt` coherence rule + DoD #3 + DoD #15 (both branches assert the two verdicts move together).
**L10 — Kill-switch non-termination (016 R3-L8).** A regression that cannot be fixed without sacrificing the composite gain has no terminal state. **Closed by** DoD #12's explicit escalate-to-user branch.
**L11 — Dry-run tests detection but not discrimination (016 R3-L18).** A persona hardcoded to emit `likely-overfit` would pass a one-branch test. **Closed by** DoD #15's two-branch test (overfit → `likely-overfit`; sound → `real-alpha`).

## Core Team Review (A–F) — inline (no `persona-*.md` files in project; consistent with 009/010/016)

**A — Quant Architect.** APPROVE WITH CONDITIONS. *A1*: `gate_consumption: false` + `analytical_framework: quantitative` preserved (DoD #5). *A2*: check #6 (PnL) content preserved verbatim (DoD #4). *A3*: legacy free-prose mandate verified removed (DoD #7).
**B — Portfolio Manager.** APPROVE. renaissance is a sub-threshold Phase 7 panel persona — genuine ROI. Shipping S-17 without waiting on the unconverged S-18 is the right call.
**C — CTO.** APPROVE WITH CONDITIONS. *C1*: `proposals/017-backups/` created before the `agents/*.yml` write. *C2*: DoD #8 YAML-lint passes before each commit message. *C3*: the orchestrator owns the `~/.claude/` CSV write (DoD #16) — the delegated implementation-agent must not be assigned a path it may be blocked from.
**D — Risk Officer.** APPROVE WITH CONDITIONS. *D1*: DoD #12's terminal-state escalate-to-user branch is explicit — a regression is never shipped, the loop never runs unbounded.
**E — The Trader.** APPROVE. No execution surface — renaissance is a backtest-validation persona. Marginal relevance only.
**F — Compliance Officer.** APPROVE. No regulatory surface — internal persona prompt.

Not unanimous — A, C, D carry procedural conditions, all absorbed into DoD #4/#5/#7/#8/#12/#16.

## Dual-Model Cross-Check (Step 4b)

No fresh Step 4b round is run for this proposal, and none is required: the renaissance design is **converged**. It was adversarially reviewed across the three isolated-challenger rounds of the superseded [Proposal 016](016-s17-s18-persona-quality-lift.md) (R1/R2/R3, 2026-05-20/21 — full records in 016's Status Log, Delta Annexes, and R3 Appendix) and carried **zero structural items in all three rounds**. This proposal reproduces that validated design.

The seven R3 renaissance items absorbed here (016 Appendix L8/L9/L11/L12/L18/L20/L21) are minor and non-structural: L8/L9/L11/L18 are DoD wording; L21 is proposal prose; **L12 and L20 are the only post-R3 additions that touch the persona file** — L12 relocates a directive from a YAML comment into `system_prompt` (same content, parsed location); L20 adds a verdict-coherence sentence to `system_prompt` (a strengthening constraint). Neither changes the schema, the adversarial frame, or the 6-check `review_prompt` structure the rounds validated.

The proposal therefore ships on 016's cross-check lineage — the convergence pattern established by the 013→029 split (a converged half ships on the bundle's prior adversarial review when the post-split absorptions are non-structural). As the dedicated verification of the only post-R3 un-reviewed persona content, **`/code-reviewer` on Commit 1 specifically inspects the L12 and L20 `system_prompt` additions** (DoD #18).

## Delta Annexe — inherited

The absorbed/resisted logs for the renaissance design are in [Proposal 016](016-s17-s18-persona-quality-lift.md) Delta Annexe Rounds 1–3 and its R3 Appendix. This proposal adds no new cross-check round and therefore no new Delta Annexe; the R3-absorption table in §"R3 absorption" is the record of what this standalone artefact changed relative to the validated 016 design.

## Confidence

Per CLAUDE.md §Confidence-state distinction — **validated** (the design survived three isolated-challenger rounds + independent verification of every L-item):
- **S-17 (renaissance):** 0.90 — the 6-check D2 improvement and the legacy-mandate-removal gate closed the two real renaissance risks; main residual is the renaissance↔dimensional pair-diff (DoD #9, now baseline-anchored).
- **Validated target** post DoD #9/#14 + user approval: ≥ 0.95.

## Reversibility

**FULLY REVERSIBLE** for all repository changes (`git revert`; backup in `proposals/017-backups/`). The `~/.claude/persona_eval_history.csv` append is an additive write to a non-git global log file — manually removable, harmless if left; not idempotent, not undone by `git revert`. No IRREVERSIBLE step.

## Status Log

> Append-only.

- 2026-05-21 — DRAFT created. HEAVY tier (explicit reasoning — new-architecture trigger). Standalone S-17 successor to the superseded [Proposal 016](016-s17-s18-persona-quality-lift.md) bundle. Reproduces the renaissance design validated across 016 R1/R2/R3 (0 structural items ×3); absorbs the 7 directed R3 renaissance items + 2 flagged DoD-hygiene items (L13/L14). Core Team A–F inline review (3 APPROVE WITH CONDITIONS, 3 APPROVE). Cross-check inherited from 016 R1/R2/R3; no new round (CLAUDE.md §3 condition (c)). 11-item L-pass. Awaiting user approval.
- 2026-05-21 — APPROVED by user (option b — 3 prose amendments: §"Dual-Model Cross-Check" rewritten to drop the non-canonical "inherited path" label and the inverted CLAUDE.md §3 condition-(c) citation, restating the real justification (design converged, ships on 016 lineage per the 013→029 convergence pattern); §"R3 absorption" transparency note extended to L17; amendment-2 "duplicate line" verified non-existent — `grep` found one occurrence only, no deletion made).
- 2026-05-21 — Commit 1 file change implemented (Sonnet implementation-agent): `agents/renaissance_backtesting.yml` rewritten to the approved design; `proposals/017-backups/renaissance_backtesting.original.yml` backup created. Diff independently verified vs the approved design — critical-pattern fields byte-identical, 7-block schema, 6-check `review_prompt`, legacy free-prose mandate removed, YAML lint clean. `/code-reviewer`: **APPROVE WITH NOTES** (file clean; DoD #6 verification command re-specified inline so it does not misfire on the forbidden-phrases declaration line). **PENDING** (not yet done): Commit 1 eval gates (DoD #9 pair-diff w/ recorded baseline, #10 median-of-3, #11 zero-regression, #12 composite ≥30, #13 D3 ≥4, #14 dual cold reviewer, #15 both-branch dry-run) → commit Commit 1 → Commit 2 (docs) + `/code-reviewer` → CSV append (orchestrator-owned) → `/commemorate` + `/retro`. The renaissance YAML change is on disk, **uncommitted**.
- 2026-05-21 — Eval-fidelity re-measure + Commit 1 shipped. The first eval-battery pass embedded condensed/paraphrased persona content in the sub-agent dispatches; a pre-commit fidelity check caught this before any commit. Per user direction the full 8-dispatch battery (3 median-of-3 runs, pair-diff reader, 2 cold reviewers, 2 dry-runs) was re-run with the ORIGINAL and REWRITE persona files embedded **byte-verbatim**, same fixtures. Verbatim result: median-of-3 composite **28→33** — the condensed run had read 34 (D6 Environmental Adaptation 5→4), confirming the condensation was materially optimistic by one composite point on one dimension. All gates PASS: zero-regression — 5 of 7 dimensions +1, D3 and D6 flat, none regressed (#11); composite 33 ≥ 30 (#12); D3 median 4 ≥ 4 (#13); pair-diff renaissance×dimensional 3→4 and renaissance×citadel 4→4, both ≥4 and ≥ recorded baseline (#9); dual cold reviewer both rate every dimension ≥ original (#14); both-branch dry-run discriminates overfit→likely-overfit / sound→real-alpha (#15); planted bugs 3/3 every run, no caps. **Commit 1** (`agents/renaissance_backtesting.yml` + `proposals/017-backups/renaissance_backtesting.original.yml`) committed `6fc4cc7`; `/code-reviewer` APPROVE WITH NOTES cited in the commit message. Remaining: Commit 2 (docs) + `/code-reviewer`, orchestrator-owned CSV append, `/commemorate`, `/retro`.

## AWAITING USER APPROVAL

No file modifications, commits, or eval dispatches until explicit user approval.

- **(a) APPROVE as drafted** — proceed to Commit 1 (renaissance + backup) then Commit 2 (docs), staged, implementation delegated to the Sonnet implementation-agent, the `~/.claude/` CSV write performed by the orchestrator.
- **(b) APPROVE WITH AMENDMENTS** — specify changes.
- **(c) DEFER** — keep as DRAFT.
- **(d) REJECT.**
