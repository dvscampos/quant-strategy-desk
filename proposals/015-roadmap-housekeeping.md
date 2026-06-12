---
id: 015
title: Roadmap housekeeping — de-date War Room header, refresh S-17/S-18 rationale, record FRED-key decision
status: DONE
owner: Daniel
opened: 2026-05-20
updated: 2026-05-20
tags: [housekeeping, progress, docs]
---

# 015 — Roadmap Housekeeping

## Tier: LIGHT

**Evidence**: 2 files (`PROGRESS.md`, `docs/retros/2026-05-16.md`), ~5 lines net, doc-only prose (no executable content). Within LIGHT ceiling. Per the prose carve-out, `/code-reviewer` is not required.

## Summary

Clear three stale-state items surfaced by the 2026-05-20 reconstruction pass: a fixed-date War Room header that silently went stale, an S-17/S-18 deferral rationale that expired five days ago, and an open "rotate FRED key" action the user has now closed by decision (rotation declined — free read-only key, exposure accepted).

## Motivation

- `PROGRESS.md` line 34 reads `**Immediate — Next War Room session (2026-05-16)**` — a fixed future date that has now passed without the session running. Re-dating it would just recreate the staleness; it should be de-dated to a date-free status line.
- `PROGRESS.md` S-17/S-18 "Why Not Now" columns justify deferral with *"Just shipped S-15 + S-16 the same day; sequential single-file rewrites create churn"* — that rationale expired on 2026-05-16. The current plan is a dedicated HEAVY bundle session.
- The "rotate FRED key" action in `docs/retros/2026-05-16.md` line 21 is **closed by user decision (2026-05-20)**: rotation declined — FRED keys are free and read-only (macro data only), exposure accepted. The decision must be recorded so it stops resurfacing in reconstruction/retro passes.

## Proposal — file manifest

| Action | File | Change |
|---|---|---|
| MODIFY | `PROGRESS.md` | (a) Line 34: de-date the War Room header → `**Next War Room session — when scheduled (overdue: 2026-05 session outstanding)**`. (b) S-17/S-18 "Why Not Now" columns: replace the expired "just shipped same day" rationale with the dedicated-HEAVY-bundle rationale. (c) Known Issues table: add one row recording the FRED-key-exposure decision (closed 2026-05-20). |
| MODIFY | `docs/retros/2026-05-16.md` | Line 21: append an inline `[RESOLVED 2026-05-20 …]` annotation to the "User should rotate FRED key" sentence — historical record kept intact, action visibly closed. |

No key value is written anywhere. PROGRESS.md content rule honoured (no tickers/NAV/P&L).

## Definition of Done

1. `PROGRESS.md` line 34 carries no fixed date; reads as a date-free status line naming the outstanding 2026-05 session.
2. S-17 and S-18 "Why Not Now" columns reference the dedicated HEAVY bundle, not the expired same-day-churn reasoning.
3. `PROGRESS.md` Known Issues table has a FRED-key-exposure row marked closed-by-decision 2026-05-20.
4. `docs/retros/2026-05-16.md` line 21 carries the `[RESOLVED …]` annotation.
5. `grep -n "Next War Room" PROGRESS.md` returns the header line, and that line carries **no full YYYY-MM-DD date**. The month token `2026-05` (in "2026-05 session outstanding") is intended and expected — the criterion is the absence of a fixed *day* date presented as a trigger, not the absence of `2026-05`.

## Adversarial Pass (L1)

**L1 — De-dated header re-drifts after the 2026-05 session runs.** Once a 2026-05 War Room runs, "(overdue: 2026-05 session outstanding)" becomes false. Risk: a new staleness. **Closed by** accepting it: a *status* line that is true-until-acted-on is self-evidently the running session's update target, unlike a silently-passing fixed *date*. The de-dating removes the failure mode where a date passes unnoticed; updating a visible "outstanding" status is normal roadmap maintenance.

## Reversibility

**FULLY REVERSIBLE.** `git revert` restores prior prose (`docs/retros/` is untracked but the edit is a one-line annotation, trivially hand-revertible). No code, no external state.

## Core Team Verdict (LIGHT — one-liner each)

- **A (Quant Architect)**: APPROVE. Doc-only; no code surface.
- **B (Portfolio Manager)**: APPROVE. Minimal scope; clears stale roadmap state before the next session reads it.
- **C (CTO)**: APPROVE. No key value written; PROGRESS.md content rule honoured.
- **D (Risk Officer)**: APPROVE. FRED-key decision is the user's to make; recording it is correct governance.

## Status Log

> Append-only.

- 2026-05-20 — DRAFT created. LIGHT tier. Regression gate satisfied: this session's Phase 1 reconstruction already re-verified Proposal 014 (S-19 guard) and Proposal 011 (dotenv auto-load) — both PASS. Awaiting user approval.
- 2026-05-20 — APPROVED by user after a DoD #5 retarget fix (grep the `Next War Room` header line for absence of a fixed `YYYY-MM-DD`, not `grep "2026-05-16"` which hit unrelated completion dates). Executed: PROGRESS.md (line 34 de-dated, S-17/S-18 rationale refreshed, FRED-key Known Issues row added) + docs/retros/2026-05-16.md (FRED-rotate action annotated closed-by-decision). DoD 1–5 verified green. **STATUS: DONE.**
