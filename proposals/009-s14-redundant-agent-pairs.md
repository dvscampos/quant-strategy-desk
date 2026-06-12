---
id: 009
title: S-14 Resolve redundant agent pairs (bridgewater_macro/macro_strategist; citadel_alpha/de_shaw_statarb)
status: APPROVED
owner: Daniel
opened: 2026-05-15
updated: 2026-05-15
tags: [governance, personas, rotation, persona-eval]
---

# 009 — S-14 Resolve Redundant Agent Pairs

## Tier: MEDIUM

**Evidence for tier**: 5 files modified (4 within `agents/` + `AGENTS.md` + `brainstorms/_TEMPLATE.md`), no new infrastructure, no code logic touched. Within-pattern persona-YAML edits. Adding new `analytical_framework` *values* to the enum vocabulary does not change selection-logic — the selector only checks "≥2 distinct values present", agnostic to which values exist. Therefore no HEAVY trigger fires.

## Summary

Phase D `/persona-eval` (2026-05-15) flagged two within-role pairs at 2/5 differentiation: `bridgewater_macro` ↔ `macro_strategist` (both `macro-narrative`, identical Bridgewater All-Weather lens) and `citadel_alpha` ↔ `de_shaw_statarb` (both `quantitative`, subset relationship). Both pairs produce overlapping critiques — "consensus theatre" risk in War Room rotations and in the 15-agent Phase 7 sign-off panel.

Proposal: **Pair A → A2′** (rewrite `bridgewater_macro` to a distinct lens; keep `macro_strategist` as the gate-consuming canonical macro-narrative agent). **Pair B → B2** (rewrite `de_shaw_statarb` as structural-arbitrage specialist with new `analytical_framework: structural`).

## Motivation / Problem

### Pair A — bridgewater_macro ↔ macro_strategist
- Both YAMLs declare `analytical_framework: macro-narrative`.
- `macro_strategist.yml` line 4 explicitly says `persona: Bridgewater Associates — All Weather macro lens`.
- `bridgewater_macro.yml` is "Bridgewater Macro Trading Strategist" with the same Dalio economic-machine framing.
- `macro_strategist` is gate-consuming (Proposal 003 Phase 1B contract); `bridgewater_macro` is not.
- Hidden constraint: `bridgewater_macro` is slot #8 of the 15-agent Phase 7 sign-off panel (`backtesting/engine/config/agents.yml:56-57`). **A1 (delete bridgewater_macro) would break the 15-agent panel.** Brief did not flag this.
- In a single session, `macro_strategist` runs in Phase 2 and `bridgewater_macro` then rubber-stamps it in Phase 7 — same lens, same Dalio framework, no challenge.

### Pair B — citadel_alpha ↔ de_shaw_statarb
- Both declare `analytical_framework: quantitative`.
- D.E. Shaw's capabilities (cointegration, z-score pairs, mean-reversion) are a **strict subset** of Citadel's broader signal-research toolkit.
- The current de_shaw lens is also a poor fit for a long-only, monthly-cadence, €200/month ETF DCA portfolio — stat-arb requires sub-daily monitoring and short-side leverage, neither available to this investor.
- de_shaw_statarb is slot #7 of the Phase 7 panel — same hidden constraint as Pair A.

## Proposal

### Pair A — Decision: A2′ (rewrite `bridgewater_macro`, not `macro_strategist`)

Brief offered A2 as "rewrite macro_strategist with a distinct framework". This proposal inverts: rewrite **bridgewater_macro** instead, because:
1. `macro_strategist` carries the gate-consumption contract (Proposal 003). Rewriting it would break that contract and force re-validation of `gate_eval` integration. Higher blast radius.
2. `bridgewater_macro` has no downstream contract — only rotation membership and Phase 7 slot.
3. Symmetric outcome (two distinct macro lenses available) at lower cost.

**Rewrite target**: `bridgewater_macro` becomes a **yield-curve regime** specialist (firm framing: PIMCO-style fixed-income macro, but file/agent name retained to avoid downstream config churn). New `analytical_framework: yield-curve-regime`. Output: regime classification driven by 2s10s slope, 3m10y term-premium, real-rate path, and bond/equity correlation — a genuinely different evidence base from Dalio growth/inflation matrix.

**Why not A1 (collapse + delete)**: breaks 15-agent Phase 7 panel.
**Why not A3 (accept overlap with non-co-occurrence rule)**: adds enforcement burden to rotation logic; doesn't fix Phase 7 redundancy.

### Pair B — Decision: B2 (structural arbitrage)

Rewrite `de_shaw_statarb` as a **structural-arbitrage** specialist:
- New `analytical_framework: structural`
- New domain: ETF-NAV dislocations, hedged vs unhedged share-class spreads, cross-listed instrument selection (NYSE-vs-Euronext same fund), ADR-vs-local, accumulating-vs-distributing share-class arb.
- Fits the actual decision surface of a long-only ETF DCA investor.
- Connects naturally to Phase 5 (Instrument Verification), where ticker-format choice already determines effective NAV access.

**Why not B1 (event-driven)**: event-driven trades require sub-monthly catalyst timing; awkward at monthly cadence.
**Why not B3 (retire from Signal pool)**: breaks Phase 7 panel and reduces pool depth from 5 → 4.
**Why not B4 (accept)**: same as A3.

### File-level manifest

| Action | File | Reason |
|---|---|---|
| MODIFY | `agents/bridgewater_macro.yml` | Full rewrite: yield-curve regime lens. Change `analytical_framework: macro-narrative` → `yield-curve-regime`. Rewrite `description`, `capabilities`, `system_prompt`, `review_prompt`. Keep `firm`, `role`, file name. |
| MODIFY | `agents/de_shaw_statarb.yml` | Full rewrite: structural arb lens. Change `analytical_framework: quantitative` → `structural`. Rewrite `description`, `capabilities`, `system_prompt`, `review_prompt`. Keep `firm`, `role`, file name. |
| MODIFY | `agents/macro_strategist.yml` | Single-line tighten: `persona:` line is already explicit, no other changes (read-only verification it remains canonical macro-narrative gate-consumer). |
| MODIFY | `AGENTS.md` | Update War Room Strike Team block (lines ~98-103): Macro pool now has two frameworks (macro-narrative via macro_strategist; yield-curve-regime via bridgewater_macro). Signal pool gains structural via de_shaw_statarb. |
| MODIFY | `brainstorms/_TEMPLATE.md` | Update rows 125-126 (rotation pool descriptions) and rows 808-809 (Strike Team table). |

### Out of scope

- Touching `gate_consumption` contract or `format_macro_prompt()` (Proposal 003).
- Renaming files (preserves Phase 7 panel slot keys, backtesting/engine/config/agents.yml references, brainstorm history references).
- Rewriting `macro_strategist` (gate-consumption contract is settled).
- Adding new agents to the rotation pools (S-5/S-10 territory).

## Definition of Done

1. `agents/bridgewater_macro.yml` declares `analytical_framework: yield-curve-regime`; system_prompt asks for yield-curve regime classification (2s10s, term premium, real-rate path), not growth/inflation matrix.
2. `agents/de_shaw_statarb.yml` declares `analytical_framework: structural`; system_prompt asks for ETF-NAV/share-class/cross-listed dislocation analysis, not pairs/cointegration.
3. `AGENTS.md` Strike Team block documents framework distribution across Macro pool (≥2 frameworks) and Signal pool (≥3 frameworks).
4. `brainstorms/_TEMPLATE.md` row entries match the new lenses.
5. `python -c "import yaml; yaml.safe_load(open('agents/bridgewater_macro.yml')); yaml.safe_load(open('agents/de_shaw_statarb.yml'))"` exits cleanly (no YAML breakage).
6. Re-run `/persona-eval` for `bridgewater_macro`, `macro_strategist`, `citadel_alpha`, `de_shaw_statarb` — D3 differentiation rises to ≥4/5 for both pairs.
7. Fresh differentiation pair test post-change: `bridgewater_macro` vs `de_shaw_statarb` (now cross-domain) confirms baseline behaviour holds.
8. Row appended to `~/.claude/persona_eval_history.csv` for the 4 personas post-change so the 2026-08-15 quarterly re-eval has like-for-like baseline.
9. PROGRESS.md S-14 row updated to DONE with proposal-009 link.

## Adversarial Loophole Pass (L1–Ln)

**L1 — Phase 7 panel breakage.** Risk: deleting either persona reduces the 15-agent panel to 14 and breaks `backtesting/engine/config/agents.yml`. **Closed by** rewriting in place, not deleting. File names preserved.

**L2 — Macro pool depth.** Risk: if rewrite makes bridgewater_macro non-fungible with macro_strategist, Macro pool depth drops from 3 to effectively 2 distinct frameworks across 3 agents. **Closed by** acceptance: 3 agents with 2 distinct frameworks satisfies the ≥2-distinct-frameworks invariant; AQR Factor Model and Man Group Portfolio remain in the pool. Counter-Regime agent is independent and not affected.

**L3 — Gate contract regression.** Risk: editing `macro_strategist.yml` could break the Proposal 003 gate_consumption contract. **Closed by** restricting the macro_strategist edit to verification-only; no functional change. If implementation-agent finds the file already optimal, it leaves it untouched.

**L4 — Hidden references.** Risk: `bridgewater_macro` or `de_shaw_statarb` referenced in other docs/configs we haven't grepped. **Closed by** pre-flight grep already performed: refs found in `PROGRESS.md` (historical row), `backtesting/sessions/2025-09.md` (frozen archive), `backtesting/engine/config/agents.yml:55,57` (slot names only — names preserved by rewrite-in-place), `brainstorms/_TEMPLATE.md` (handled in manifest), `local/brainstorms/2026-03.md` (historical session — frozen). No live broken references.

**L5 — Persona-name vs framework drift.** Risk: a Bridgewater-branded agent (`firm: Bridgewater Associates`) doing yield-curve regime work is mildly incoherent — Bridgewater is famous for All-Weather/Dalio, not curves. **Closed by** acceptance with caveat: the *role* is "Yield-Curve Regime Strategist"; firm metadata acknowledges Bridgewater's broader macro coverage. Future Pair S-5/S-10 work may rename. Documented as a known cosmetic in proposal Status Log.

**L6 — Differentiation re-eval bias.** Risk: re-running `/persona-eval` immediately after rewrite produces inflated differentiation because the rubric author (this session) and the rewriter overlap. **Closed by** verification plan: run eval on a fresh Sonnet sub-agent with no awareness of this proposal; brief it cold from the YAML files only.

**L7 — Structural arb fit to long-only DCA.** Risk: even rewritten, de_shaw_statarb's structural-arb lens may surface trades the investor cannot execute (some cross-listed arb requires short side). **Closed by** scoping: the rewrite emphasises **selection** of long-only instruments (which share-class to buy, which listing) rather than arb capture. Output framing is "which version of this ETF should we hold?", not "go long X / short Y".

**L8 — Brief deviation.** Risk: this proposal inverts A2 (rewrites bridgewater_macro instead of macro_strategist). **Closed by** explicit inversion rationale in Proposal §"Pair A — Decision" and gate-contract preservation argument. User sign-off on this deviation is part of approval.

**L9 — Verification step ordering.** Risk: implementation-agent appends to persona_eval_history.csv before re-eval is actually run, producing fake row. **Closed by** DoD ordering: DoD #6 (re-run eval) precedes DoD #8 (append CSV row).

## Persona Review

### A — Quant Architect (inline)
APPROVE WITH CONDITIONS. The rewrite-in-place strategy preserves filenames and avoids cascading config churn — clean. Concern: confirm `gate_consumption` field key is preserved in the bridgewater_macro rewrite (currently `false` — must remain `false` since only macro_strategist consumes the gate table). Condition: implementation-agent diff must show `gate_consumption: false` retained in bridgewater_macro post-rewrite.

### B — Portfolio Manager (inline)
APPROVE. The B2 reframe is the genuinely useful one for this investor. Share-class and cross-listing decisions actually surface monthly in Phase 5 and are currently under-analysed. Structural arb is the right lens.

### C — CTO (inline)
APPROVE. No env/secret/data-pipeline surface. YAML schema preserved. Backwards-compatible at the file-key level.

### D — Risk Officer (inline)
APPROVE WITH CONDITIONS. The new yield-curve-regime lens introduces a different evidence base for regime calls in Phase 7 sign-off — that's actually *more* adversarial, not less, which is the point. Condition: the rewritten `review_prompt` for `bridgewater_macro` must keep adversarial framing (≥4 numbered risk checks, "do not rubber-stamp" line preserved). Same for `de_shaw_statarb`.

### Adversarial Note (Orchestrator)
Not unanimous — A and D have conditions, both procedural and small. No Challenger escalation needed.

## Verification Plan

1. **YAML lint**: `python -c "import yaml; [yaml.safe_load(open(f)) for f in ['agents/bridgewater_macro.yml','agents/de_shaw_statarb.yml','agents/macro_strategist.yml','agents/citadel_alpha.yml']]"` exits 0.
2. **Field preservation grep**: `grep -E "^(name|role|firm|gate_consumption):" agents/bridgewater_macro.yml agents/de_shaw_statarb.yml` — confirm each file has all four keys.
3. **Re-run `/persona-eval`** on the 4 modified personas (Sonnet sub-agent, cold-briefed from YAML only).
4. **Cross-pair differentiation test**: re-evaluate bridgewater_macro vs macro_strategist (target ≥4/5) and citadel_alpha vs de_shaw_statarb (target ≥4/5).
5. **Append to `~/.claude/persona_eval_history.csv`** post-change rows for the 4 personas with new scores.
6. **PROGRESS.md update**: mark S-14 DONE, link `[Proposal 009](proposals/009-s14-redundant-agent-pairs.md)`.
7. **CHANGELOG.md**: append entry under `[Unreleased] ### Changed` describing the framework diversification.

## Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Rewritten persona produces lower-quality output than original | Adversarial-framing requirement in DoD; cold re-eval validates |
| User wants A1 (collapse) regardless of Phase 7 breakage | This proposal explicitly surfaces the Phase 7 constraint; if user prefers A1, scope expands to also adding a replacement Macro agent to the panel (separate proposal) |
| `structural` framework label conflicts with existing usage elsewhere | Pre-flight grep: no existing `analytical_framework: structural` in agents/ — clean to introduce |
| Bridgewater firm name + yield-curve framework feels incoherent | L5 documented; can be revisited under S-5/S-10 future agent additions |

## Reversibility

**FULLY REVERSIBLE.** All changes are local YAML/Markdown edits in version control. `git revert` restores all prior content. No external state, no API calls, no data mutations. The persona_eval_history.csv append is additive (no row deletion) and idempotent under date-stamping.

## Amendment (2026-05-15) — Zero-Regression Gate + Confidence Lift to 0.95

Butterfly grep matrix revealed one live downstream surface not in the initial scope:

- `.claude/commands/war-room/SKILL.md:209` hardcodes the framework label enum `(macro-narrative / quantitative / fundamental / behavioural / flow-based)`. New labels `yield-curve-regime` and `structural` must be added or the War Room skill will treat them as invalid.
- `.claude/commands/war-room/SKILL.md:81` example references stale "Bridgewater / macro-narrative" — refresh.

All other downstream surfaces verified safe via grep:
- `backtesting/engine/rotation.py` — reads agent names only, not framework labels.
- `backtesting/engine/config/agents.yml` — name slots preserved by rewrite-in-place.
- `scripts/data/gate_eval.py` and `format_macro_prompt()` — no framework dependency.
- `tests/` — no persona refs.
- 8 other `agents/*.yml` with `quantitative` label — unaffected (citadel_alpha unchanged).

### Added Files

- `MODIFY` `.claude/commands/war-room/SKILL.md` — extend framework enum (line 209) + refresh example (line 81).

### Added DoD items (binding kill switches)

10. **Zero-regression gate**: Run `/persona-eval` on the originals AND the rewritten drafts in the same pass. Reject and iterate if ANY 7-dimension score on the rewrite is strictly lower than the original, OR total composite drops ≥1 point, OR adversarial-framing dimension regresses.
11. **Synthetic Phase 2 dry-run**: Cold Sonnet sub-agent simulates Phase 2 + Counter-Regime exchange on 2026-04 ground truth. Pass condition: rewritten `macro_strategist` and `bridgewater_macro` produce non-identical regime characterisations, neither contradicting 2026-04 truth.
12. **Investor-fit dry-run (Pair B)**: Rewritten `de_shaw_statarb` against 2026-04 portfolio snapshot must produce at least one actionable monthly-cadence decision (share-class / cross-listed selection), not a hypothetical short-leg arb.
13. **Staged merge** — Commit 1: persona YAMLs + war-room skill enum + empirical gates. Commit 2: AGENTS.md + `brainstorms/_TEMPLATE.md` documentation, only after Commit 1 gates pass.
14. **Cold-reviewer cross-check #1**: Sonnet sub-agent reads rewritten YAMLs without seeing this proposal and scores against `persona-eval:references:persona_rubric`. Eliminates L6 same-session bias.
15. **Median-of-3 eval runs**: For the 4 personas (rewritten + originals + cross-pair partners), run `/persona-eval` 3× and take median per dimension. Stabilises against ±1-point model variance.
16. **Cold-reviewer cross-check #2**: Second independent Sonnet session (different sub-agent instance) re-scores the rewritten personas against the rubric. Pass condition: both cold reviewers independently rate every dimension ≥ original.

### Confidence after amendment

- Pair A: 0.92 → **0.95** (with DoD 15/16)
- Pair B: 0.93 → **0.95** (with DoD 15/16)

### Zero-Regression Contract

If the rewritten personas score lower than the originals on any persona-eval dimension at any of the 3 runs (median basis), the proposal is **rejected at the merge gate and reverted**, not patched forward. Strict improvements only.

## Status Log

- 2026-05-15 — DRAFT created.
- 2026-05-15 — AMENDED with zero-regression gate, butterfly grep additions, DoD #10–16.
- 2026-05-15 — APPROVED by user (option b: 0.95 target with median-of-3 + dual cold reviewers).
