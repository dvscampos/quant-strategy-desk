---
id: 012
title: Citadel + Two-Sigma review_prompt example-trio domain polish
status: DONE
owner: Daniel Campos
opened: 2026-05-16
updated: 2026-05-16
tags: [persona-polish, light-tier, audit-close, proposal-010-followup]
---

# 012 — Citadel + Two-Sigma review_prompt example-trio domain polish

## Summary
Replace the generic risk-domain example trio (`"reduce size 8%→4%", "stop at 88.00", "block trade until VIX<22"`) that currently appears verbatim in both `agents/citadel_alpha.yml` (line 108) and `agents/two_sigma_risk.yml` (line 62) with archetype-native trios. Citadel gets quant-signal-validation examples (in-sample IC threshold, OOS t-stat, signal capacity vs AUM bottleneck). Two-Sigma gets portfolio-risk examples anchored in its capability list (Kelly stake, cross-position correlation, VaR contribution). Closes the known deferred polish in [Proposal 010 audit brief §H.1](010-fresh-session-review-brief.md) and the parallel bleed in two_sigma_risk surfaced by today's pre-flight static-label enumeration.

## Motivation / Problem
The Proposal 010 option-b per-archetype example amendment swapped generic examples into archetype-native ones across the persona library, but two files retained the legacy generic trio:

1. `citadel_alpha.yml:108` — documented as deferred polish in Proposal 010 audit brief §H.1.
2. `two_sigma_risk.yml:62` — slipped through the 010 audit; surfaced via 2026-05-16 pre-flight `grep -nE 'e\.g\. "' agents/*.yml` enumeration of all 17 personas' closing examples. Identical generic trio.

The drift cost: at Phase 8 (Full Desk Sign-Off), agents are instructed to reject "generic remediations". When the persona's own example trio is generic, the rejection contract is weakened. Two-Sigma especially: its examples are nominally risk-flavoured but are not anchored in Two-Sigma's actual capability list (Kelly, correlation breakdown, VaR, drawdown halt), leaving the persona's lens softer than risk_guardian's.

## Proposal

### File 1: `agents/citadel_alpha.yml` line 108

**Before:**
> For each risk you raise: tag [HIGH|MEDIUM|LOW] by capital impact, propose a specific fix (not "review this" — e.g. "reduce size 8%→4%", "stop at 88.00", "block trade until VIX<22"), and order your list HIGH→MEDIUM→LOW with irreversible risks first. Generic remediations will be rejected at Phase 8.

**After:**
> For each risk you raise: tag [HIGH|MEDIUM|LOW] by capital impact, propose a specific fix (not "review this" — e.g. "drop in-sample IC threshold from 0.05 to 0.03 and refit", "reject signal unless OOS t-stat >2.5", "cap signal capacity at 50% of estimated AUM bottleneck"), and order your list HIGH→MEDIUM→LOW with irreversible risks first. Generic remediations will be rejected at Phase 8.

### File 2: `agents/two_sigma_risk.yml` line 62

**Before:**
> For each risk you raise: tag [HIGH|MEDIUM|LOW] by capital impact, propose a specific fix (not "review this" — e.g. "reduce size 8%→4%", "stop at 88.00", "block trade until VIX<22"), and order your list HIGH→MEDIUM→LOW with irreversible risks first. Generic remediations will be rejected at Phase 8.

**After:**
> For each risk you raise: tag [HIGH|MEDIUM|LOW] by capital impact, propose a specific fix (not "review this" — e.g. "halve Kelly stake if 30d cross-position correlation >0.85", "trigger drawdown halt at -8% peak-to-trough NAV before next contribution", "reject position if 99% VaR contribution >25% of total portfolio VaR"), and order your list HIGH→MEDIUM→LOW with irreversible risks first. Generic remediations will be rejected at Phase 8.

## Scope & Out-of-Scope

**In scope.**
- The two `review_prompt` closing-example lines listed above.

**Out of scope.**
- Any other field (`system_prompt`, `output_format`, `required_vocabulary`, `capabilities`).
- Any other persona file (audited via 2026-05-16 grep — no third file shares the generic trio).
- S-19 instrument-compliance carry-forward (separate proposal — item 3 in today's queue).
- Re-evaluation against the persona rubric (the change is too small to move composite scores meaningfully; quarterly re-eval 2026-08-15 captures it).

## Definition of Done

1. `grep -nE "reduce size 8%→4%|stop at 88.00|block trade until VIX<22" agents/*.yml` returns zero matches.
2. `grep -n "in-sample IC threshold" agents/citadel_alpha.yml` returns one match (line 108).
3. `grep -n "Kelly stake" agents/two_sigma_risk.yml` returns one match (line 62).
4. `python -c "import yaml; yaml.safe_load(open('agents/citadel_alpha.yml')); yaml.safe_load(open('agents/two_sigma_risk.yml'))"` exits 0.
5. `/code-reviewer` returns APPROVE or APPROVE WITH NOTES.
6. CHANGELOG.md + PROGRESS.md updated at `/commemorate`.

## Risks & Mitigations

- **R1 — Vocabulary collision with peer personas.** *Mitigation:* pre-flight enumeration of all 17 closing-example lines (see Status Log). Citadel-native phrasings (in-sample IC threshold, OOS t-stat, signal capacity vs AUM bottleneck) and Two-Sigma-native phrasings (Kelly stake, cross-position correlation, VaR contribution %) confirmed unique against point72, dimensional, renaissance, aqr, risk_guardian, man_group_portfolio.
- **R2 — Two-Sigma vs risk_guardian overlap.** *Mitigation:* risk_guardian uses absolute-€ VaR thresholds and kill-switch drawdown language; Two-Sigma uses Kelly fractional sizing + correlation-cluster + VaR-contribution-percent. Vectors differ.
- **R3 — YAML parser break.** *Mitigation:* DoD #4 verifies `yaml.safe_load` parses both files post-edit. Edits stay inside a `|`-block scalar so no quoting/colon hazards arise.

## Core Team Review (A–D) — LIGHT one-liners

- **A — Quant Architect**: APPROVE. Pattern-identical to Proposal 010 option-b; no duplication risk.
- **B — Portfolio Manager**: APPROVE. Closes a known audit gap (010 §H.1) plus a parallel one in two_sigma at zero capital risk.
- **C — CTO**: APPROVE. No env/API/schema/dependency surface touched.
- **D — Risk Officer**: APPROVE. Sharpens Phase 8 risk-rejection vocabulary in two of the most-cited personas.

## Adversarial L-Pass

- **L1 — Vocab collision with adjacent quant peers.** New Citadel trio could collide with point72 ("walk-forward OOS hit-rate"), dimensional ("purged-k-fold OOS"), renaissance ("deflated Sharpe"). **Closed by** 2026-05-16 pre-flight grep across all 17 personas: "in-sample IC threshold", "OOS t-stat >2.5" (as a specific assertion), and "signal capacity ÷ AUM bottleneck" are citadel-exclusive phrasings.
- **L2 — Two-Sigma vs risk_guardian overlap.** Both are portfolio-risk personas. **Closed by** Two-Sigma's new trio anchors on Kelly stake (unique), 30d cross-position correlation threshold (unique), and 99% VaR-contribution-percent (risk_guardian uses VaR-absolute-€). Differentiation preserved.
- **L3 — Hidden third occurrence undetected.** **Closed by** pre-flight grep enumerated all 17 personas' closing-example lines. Only citadel and two_sigma carried the generic trio verbatim. No third file exists.
- **L4 — Phase 8 cold-reader fragility.** A reviewing agent unfamiliar with Citadel/Two-Sigma jargon might mis-judge "OOS t-stat >2.5" as a specific signal proposal rather than as a remediation example. **Closed by** the surrounding sentence frames the trio as "e.g. … fix (not 'review this')" — the example position is unambiguous. No prose change needed.

## Reversibility

**FULLY REVERSIBLE.** Two YAML one-line edits inside `|`-block scalars. `git revert` restores both files exactly. No external state, no schema migration, no cache, no downstream consumer change.

## Status Log

> Append-only. The closing entry (status → DONE) MUST be paired with a corresponding line in [CHANGELOG.md](../CHANGELOG.md).

- 2026-05-16 — DRAFT opened. Pre-flight grep across all 17 `agents/*.yml` closing-example lines confirmed citadel_alpha.yml and two_sigma_risk.yml are the only two files carrying the generic trio verbatim. Static-label enumeration rule honoured: proposed replacement phrasings audited against the other 15 personas for vocabulary collisions; none found. Awaiting user approval.
- 2026-05-16 — APPROVED by user. Edits executed inline (orchestrator-direct, justified by LIGHT-tier 2-line scope under the dispatch-overhead exception). DoD #1–4 verified green: zero generic-trio matches across all `agents/*.yml`; one Citadel-native match at `citadel_alpha.yml:108`; one Two-Sigma-native match at `two_sigma_risk.yml:62`; `yaml.safe_load` parses both files cleanly. `/code-reviewer` returned APPROVE WITH NOTES (single NOTE on the `0.05` IC threshold magic number being illustrative not authoritative; user waived). Status → DONE. CHANGELOG.md `[Unreleased]` ### Changed entry appended.
