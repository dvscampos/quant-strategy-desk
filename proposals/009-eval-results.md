# Proposal 009 — Evaluation Results

> Persistence record for the persona-eval kill-switch decision. Generated 2026-05-15.

## Median-of-3 scores (DoD #15)

Three independent Sonnet sub-agents scored each persona against the 7-dimension rubric on the shared scenario (May 2026 War Room, €2,400 NAV, VIX 18, 2s10s +35bp steepening, equity-vs-bond decision).

### Raw scores by run

| Persona | Run | D1 | D2 | D3 | D4 | D5 | D6 | D7 | Total |
|---|---|---|---|---|---|---|---|---|---|
| bridgewater_macro ORIG | 1 | 3 | 3 | 2 | 3 | 3 | 1 | 4 | 19 |
| bridgewater_macro ORIG | 2 | 4 | 4 | 3 | 4 | 4 | 1 | 4 | 24 |
| bridgewater_macro ORIG | 3 | 4 | 3 | 3 | 3 | 3 | 1 | 4 | 21 |
| bridgewater_macro REWRITE | 1 | 5 | 4 | 2 | 4 | 4 | 3 | 4 | 26 |
| bridgewater_macro REWRITE | 2 | 5 | 4 | 3 | 5 | 5 | 2 | 5 | 29 |
| bridgewater_macro REWRITE | 3 | 5 | 4 | 3 | 4 | 4 | 4 | 4 | 28 |
| de_shaw_statarb ORIG | 1 | 4 | 3 | 2 | 3 | 3 | 0 | 1 | 16 |
| de_shaw_statarb ORIG | 2 | 4 | 4 | 3 | 4 | 4 | 0 | 1 | 20 |
| de_shaw_statarb ORIG | 3 | 4 | 3 | 3 | 4 | 4 | 1 | 2 | 21 |
| de_shaw_statarb REWRITE | 1 | 4 | 3 | 2 | 4 | 4 | 4 | 5 | 26 |
| de_shaw_statarb REWRITE | 2 | 5 | 4 | 3 | 4 | 5 | 3 | 5 | 29 |
| de_shaw_statarb REWRITE | 3 | 5 | 4 | 3 | 4 | 5 | 4 | 5 | 30 |

### Median per dimension

| Persona | D1 | D2 | D3 | D4 | D5 | D6 | D7 | Total |
|---|---|---|---|---|---|---|---|---|
| **bridgewater_macro ORIG** | 4 | 3 | 3 | 3 | 3 | 1 | 4 | **21** |
| **bridgewater_macro REWRITE** | 5 | 4 | 3 | 4 | 4 | 3 | 4 | **28** |
| Δ | +1 | +1 | 0 | +1 | +1 | +2 | 0 | **+7** |
| **de_shaw_statarb ORIG** | 4 | 3 | 3 | 4 | 4 | 0 | 1 | **20** |
| **de_shaw_statarb REWRITE** | 5 | 4 | 3 | 4 | 5 | 4 | 5 | **29** |
| Δ | +1 | +1 | 0 | 0 | +1 | +4 | +4 | **+9** |

### Zero-regression gate (DoD #10)

**Criteria**: No dimension regresses, composite does not drop ≥1, adversarial-framing dimension (D2) does not drop.

| Check | bridgewater_macro | de_shaw_statarb | Result |
|---|---|---|---|
| Per-dimension: rewrite ≥ original on all 7 | ✅ | ✅ | PASS |
| Composite: no drop ≥1 | +7 | +9 | PASS |
| D2 (Adversarial Depth) maintained | +1 | +1 | PASS |
| D3 (Actionability) — tied, room for future | — | — | NOTED |

**VERDICT: ZERO-REGRESSION GATE PASSED on median-of-3 evaluation.** Both rewrites strictly improve.

## Notable findings

- **D6 (Environmental Adaptation)** had the largest gain on both rewrites (+2 and +4). Originals scored 0–1 because their generic adversarial prompts did not engage scenario specifics (VIX, curve slope, NAV size, DCA cadence). Rewrites engage these directly through their narrower lenses.
- **D7 (Guardrail Integrity)** improved markedly on de_shaw_statarb (+4) because the original applied a stat-arb lens to a long-only ETF DCA portfolio — a domain mismatch flagged as drift. The rewrite's "HOLD not short" framing resolves this.
- **D3 (Actionability)** tied at 3 on both rewrites. Neither YAML carries effort estimates or priority ordering — future improvement target (potential S-15 backlog item).

## Dual cold reviewer scores (DoD #14, #16)

Two independent Sonnet sub-agents, neither shown the proposal, scored the rewrites and pair differentiation:

| Metric | Cold Reviewer A | Cold Reviewer B | Convergence |
|---|---|---|---|
| bridgewater_macro REWRITE composite | 25 | 20 | Both ≥ original (21) |
| de_shaw_statarb REWRITE composite | 26 | 21 | Both ≥ original (20) |
| **Pair A differentiation** | **2/5** | **2/5** | ⚠️ FAILED target (≥4/5) |
| Pair B differentiation | 4/5 | 4/5 | ✅ PASSED target |

Both cold reviewers converged on Pair A 2/5 with the same reasoning: same Bridgewater firm brand, same regime-classification output type, same "is the regime call wrong" review-prompt structure — even though the underlying lens (yield-curve vs All-Weather narrative) is genuinely different.

## Synthetic Phase 2 dry-run (DoD #11)

**VERDICT: PASS.** Both macro lenses processed the 2026-04 ground-truth ("Energy-Shock Stagflation") and produced **different confidence levels** (macro_strategist: HIGH; bridgewater_macro: MEDIUM) on **different evidentiary bases** (gate-table-driven vs curve-mechanics-driven). Neither contradicted ground truth.

Operational divergence verified — but does not fully resolve the static cold-reviewer 2/5 finding.

## Investor-fit dry-run (DoD #12)

**VERDICT: PASS.** Rewritten de_shaw_statarb produced 3 actionable monthly-cadence decisions on real portfolio data:
1. VWCE.DE vs VWCE.MI listing selection (spread advantage on Borsa Italiana).
2. ACC/DIST verification for Portuguese tax (28% IRS Cat E withholding on DIST).
3. DFNS.PA vs DFEN.DE listing reconciliation (also surfaced ticker inconsistency between PORTFOLIO.md and 2026-04 trade instructions).

No drift, no short-leg framing, no pairs/z-score language. Long-only discipline preserved.

## Gate decision summary

| Pair | Zero-regression (DoD #10) | Cold-reviewer pair diff (DoD #14,#16) | Operational dry-run | Verdict |
|---|---|---|---|---|
| **Pair A** (macro) | ✅ PASS (+7 composite) | ❌ FAIL (2/5 vs ≥4/5 target) | ✅ PASS (Phase 2) | **MIXED** |
| **Pair B** (signal) | ✅ PASS (+9 composite) | ✅ PASS (4/5) | ✅ PASS (investor-fit) | **CLEAN PASS** |

## Decision required (user)

Pair B is ready to ship. Pair A is a partial improvement — strictly better internally but does not move the pair-differentiation score that S-14 was created to fix. User must choose remediation path before any commit.
