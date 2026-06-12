---
id: 014
title: S-19 — Carry-forward instrument-compliance guard to pimco_curve_strategist + de_shaw_statarb
status: DONE
owner: Daniel Campos
opened: 2026-05-16
updated: 2026-05-16
tags: [persona-polish, light-tier, s-19, proposal-010-followup, compliance-guard]
---

# 014 — S-19: Carry-forward instrument-compliance guard to `pimco_curve_strategist` and `de_shaw_statarb`

> **Numbering note.** Proposal 013 is the `/skill-audit` Gemini→Claude Code port, archived at `~/.claude/governance-overhaul/proposals/013-skill-audit-port.md` (global-governance scope; Investments tree not touched). This proposal (014) continues the Investments numbering sequence — there is no skipped number.

## Summary
Apply the jurisdiction-driven UCITS / broker-availability instrument-compliance guard (already on `citadel_alpha.yml` since Proposal 010 §Amendment 2) to two more signal-pool personas: `pimco_curve_strategist.yml` and `de_shaw_statarb.yml`. Same contract — any specific instrument named must be jurisdiction-compliant and broker-accessible, or the persona must fall back to factor/structural-selection language and flag `compliance_uncertain: true`. Implementation shape differs by output_format style (schema field for pimco's structured YAML; memo-header convention for de_shaw's free-prose), as discovered during pre-flight.

## Motivation / Problem

Proposal 010 §Amendment 2 added a jurisdiction-driven instrument-compliance guard to `citadel_alpha.yml` to prevent US-domiciled-ETF hallucination for the Portugal-resident UCITS-only investor. Same gap exists in two other signal-pool personas:

- `pimco_curve_strategist.yml` outputs `bond_etf_allocation` with sample tickers like "iShares 0-3Y Government", "Vanguard Short-Term Government", etc. (lines 60–66). Without the guard, the persona can name US-domiciled bond ETFs the investor cannot trade.
- `de_shaw_statarb.yml`'s entire purpose is selecting *specific* share classes / listings / ADRs (line 51: "Your output must be framed as 'which version of this instrument should we HOLD'…"). The persona's output is, by design, a specific instrument — making the compliance guard *more* relevant here than for citadel, not less.

Carry-forward was deliberately deferred from Proposal 010 to avoid re-opening Proposal 009 scope and re-triggering the 009 eval cycle. PROGRESS.md S-19 row holds the full spec.

## Proposal

### File 1: `agents/pimco_curve_strategist.yml`

**Edit A** — append to `output_format` block (after line 41, before `system_prompt`):

```yaml
  compliance_uncertain: boolean    # true if a specific instrument cannot be verified against the investor's declared jurisdiction/broker
```

**Edit B** — insert paragraph in `system_prompt` immediately above the existing `INVESTOR PROFILE: See local/INVESTOR_PROFILE.md…` trailer (line 84):

> **Instrument compliance constraint**: If your `bond_etf_allocation` field proposes specific bond ETFs, those instruments MUST be compliant with the regulatory jurisdiction declared in `local/INVESTOR_PROFILE.md` (e.g. UCITS-compliant for EU residents, registered-fund-only for US residents, etc.) AND accessible on the broker(s) declared therein. If you are uncertain whether a specific instrument is compliant or accessible, output the duration-bucket allocation percentages without naming specific tickers, and flag `compliance_uncertain: true`. Never hallucinate a ticker.

### File 2: `agents/de_shaw_statarb.yml`

**Edit A** — insert paragraph in `system_prompt` immediately above the existing `INVESTOR PROFILE: See local/INVESTOR_PROFILE.md…` trailer (line 53):

> **Instrument compliance constraint**: If your memo names a specific share class, ISIN, listing, or ADR, that instrument MUST be compliant with the regulatory jurisdiction declared in `local/INVESTOR_PROFILE.md` AND accessible on the broker(s) declared therein. If you are uncertain whether a specific instrument is compliant or accessible, do NOT name an ISIN — describe the structural-selection rationale (e.g. "prefer EUR-hedged accumulating share class on the most liquid European listing") and let the human resolve the specific instrument. State `compliance_uncertain: true` at the top of your memo when this fallback applies. Never hallucinate a ticker or ISIN.

**No `output_format` change** — de_shaw's `output_format` is free-prose (lines 26–29: "D.E. Shaw-style structural arbitrage memo with share-class comparison tables…"). The `compliance_uncertain` flag is enforced via system_prompt instruction as a memo-header convention, not a schema field. The contract is identical to citadel/pimco; only the carrier differs.

## Scope & Out-of-Scope

**In scope.**
- The two YAML files listed above.

**Out of scope.**
- Restructuring `de_shaw_statarb.yml`'s `output_format` from free-prose to a structured schema. That is a S-17/S-18-class HEAVY rewrite (~3,000-word persona overhaul) and was not surfaced as a S-19 carry-forward. If a uniform schema across all signal-pool personas becomes a strategic priority, file a separate HEAVY proposal.
- Re-running persona-eval on either file. S-19 is documented in PROGRESS.md as "Before 2026-08-15 quarterly re-eval" — the next quarterly captures it.
- Updating gs_compliance or any other Compliance-domain persona. They are not Proposal 010 §Amendment 2 carry-forwards.

## Definition of Done

1. `grep -c "compliance_uncertain" agents/pimco_curve_strategist.yml` returns ≥1.
2. `grep -c "Instrument compliance constraint" agents/pimco_curve_strategist.yml agents/de_shaw_statarb.yml` returns ≥2.
3. `grep -c "Never hallucinate a ticker" agents/pimco_curve_strategist.yml agents/de_shaw_statarb.yml` returns ≥2.
4. `python3 -c "import yaml; yaml.safe_load(open('agents/pimco_curve_strategist.yml')); yaml.safe_load(open('agents/de_shaw_statarb.yml')); print('OK')"` prints `OK`.
5. `python3 -c "import yaml; d=yaml.safe_load(open('agents/pimco_curve_strategist.yml')); assert 'compliance_uncertain' in d['output_format']; print('OK')"` prints `OK`.
6. `/code-reviewer` returns APPROVE or APPROVE WITH NOTES.

## Risks & Mitigations

- **R1 — Schema vs convention divergence between citadel/pimco and de_shaw.** *Mitigation:* explicit memo-header convention in de_shaw's system_prompt; L2 in adversarial pass; CHANGELOG entry will name the divergence.
- **R2 — Vocabulary collision with gs_compliance.** *Mitigation:* guard does not classify regulatory surface — it only requires named instruments to be verified or replaced with factor language. Same pattern audited at Proposal 010; no boundary blur in practice.
- **R3 — Field-name typo creating silent miss.** *Mitigation:* DoD #5 specifically tests `'compliance_uncertain' in d['output_format']` via Python rather than just grep.

## Core Team Review (A–D) — LIGHT one-liners

- **A — Quant Architect**: APPROVE. Additive only; field-naming consistent with citadel.
- **B — Portfolio Manager**: APPROVE. Closes the deferred carry-forward gap.
- **C — CTO**: APPROVE. No env/API surface; YAML integrity verified by DoD #4–5.
- **D — Risk Officer**: APPROVE. Reduces hallucinated-instrument risk in two more signal personas.

## Adversarial L-Pass

- **L1 — Vocabulary collision with gs_compliance.** *Closed by:* guard does not classify regulatory surface; only requires the signal persona to either name a verified instrument or fall back to factor/structural language. Classification stays with gs_compliance.
- **L2 — Structural-shape divergence (schema vs memo convention).** *Closed by:* system_prompt clause in de_shaw makes the convention explicit; Phase 8 reviewers will see the declaration in memo body. Contract identical; only carrier differs.
- **L3 — Field-name typo silent miss.** *Closed by:* DoD #5 Python-level assertion `'compliance_uncertain' in d['output_format']`.
- **L4 — Guard placement breaks trailer standalone clarity.** *Closed by:* guard goes BEFORE the `INVESTOR PROFILE: See…` trailer; trailer remains the final line of system_prompt. Same shape as citadel:81.
- **L5 — Real-time discovery of de_shaw free-prose escalates scope mid-implementation.** *Closed by:* flagged in pre-flight before approval; user chose option-b memo convention rather than HEAVY rewrite. No silent scope expansion.

## Delta Annexe
n/a — LIGHT tier. Dual-model cross-check is HEAVY-only per global rule.

## Reversibility

**FULLY REVERSIBLE.** Two additive YAML edits; `git revert` restores both files. No downstream consumer currently parses `compliance_uncertain` programmatically (verified: zero references outside `agents/*.yml` and proposal docs). The field is consumed visually by Phase 8 reviewers.

## Status Log

> Append-only. The closing entry (status → DONE) MUST be paired with a CHANGELOG.md entry.

- 2026-05-16 — DRAFT opened. Pre-flight: Proposal 012 regression check PASS (citadel + two_sigma trios intact). citadel guard reference text located (system_prompt:73, output_format:52). Peer scan: `compliance_uncertain` exists only on citadel — clean to add. de_shaw `output_format` discovered to be free-prose, not structured YAML — surfaced as Real-time Execution Stop; user chose option-b memo-header convention. Static-label enumeration honoured: "Instrument compliance constraint" phrasing unique to citadel/pimco/de_shaw signal-pool subset; no collision with gs_compliance, risk_guardian, or other peers. Awaiting user approval.
- 2026-05-16 — APPROVED by user. Edits executed inline (orchestrator-direct, justified by LIGHT-tier ~5 net lines under the dispatch-overhead exception). DoD #1–5 verified green. `/code-reviewer` returned APPROVE WITH NOTES. **Note 2 addressed inline before commit**: de_shaw's memo-header mandate was conditional ("when this fallback applies"); strengthened to require an **unconditional** `compliance_uncertain: [true|false]` header on every memo regardless of state, with explicit Phase 8 grep-target language. Refinement stays within approved system_prompt edit scope; net diff unchanged at +5 lines. **Note 1 deferred** (`compliance_uncertain: boolean` parsing as string `'boolean'` via yaml.safe_load): this is the schema-as-annotation convention used consistently throughout citadel and pimco's `output_format` (mirrors `name: string`, `decay_curve: list`, etc.); fixing requires either out-of-014-scope citadel edits or an inconsistent pimco-only convention break. Logged for future cycle if the whole library moves to real typed schemas. Status → DONE. CHANGELOG.md `[Unreleased] ### Changed` entry appended.
