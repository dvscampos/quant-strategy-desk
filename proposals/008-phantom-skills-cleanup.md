---
id: 008
title: Phantom skills cleanup (first deferral)
status: DONE
owner: Daniel
opened: 2026-04-27
updated: 2026-04-27
tags: [docs, hygiene, skills]
---

# 008 — Phantom Skills Cleanup (First Deferral)

## Summary
`CLAUDE.md` advertises three Local skills — `/audit`, `/backtest`, `/risk-check` — that do not exist on disk (`.claude/commands/` contains only `war-room/`). Documentation drift surfaced during Proposal 007 commemorate. This proposal removes the phantom rows from the Skills table and logs the build-out as a deferred Staged Improvement, rather than building the skills now. Tier **LIGHT** — one-file edit plus a roadmap line.

## Motivation / Problem
- Anyone invoking `/audit`, `/backtest`, or `/risk-check` today gets a silent "skill not found" — the Skill tool ignores unknown names rather than erroring loudly.
- Drift was flagged in `proposals/007-war-room-first-run-guard.md` §R1 and in the 2026-04-27 retro Carry Forward.
- Building all three properly is HEAVY work (per-skill pre-flight, persona wiring, integration with risk/data layers). It is not the right scope for today.

## Proposal
- Delete the three phantom rows from the `## Skills (Global & Local)` table in `CLAUDE.md` (currently lines 213–215).
- Append one line under `PROGRESS.md` Staged Improvements: build `/audit`, `/backtest`, `/risk-check` as a future workstream, attributing the deferral to Proposal 008.
- Do **not** rewrite history in `proposals/003`, `proposals/007`, retros, CHANGELOG, or backtesting docs — those references are historical context, not active commitments.

## Scope & Out-of-Scope
- **In scope**: two file edits (CLAUDE.md row deletion, PROGRESS.md staged-improvement line).
- **Out of scope**: actually building any of the three skills; renaming or re-purposing existing skills; touching the global Skills column.

## Definition of Done
1. `grep -n "^| \\\`/audit\\\`\\|^| \\\`/backtest\\\`\\|^| \\\`/risk-check\\\`" CLAUDE.md` returns no matches.
2. `PROGRESS.md` contains a Staged Improvement line referencing Proposal 008 and the three deferred skills.
3. `proposals/007-war-room-first-run-guard.md` §R1 reference is unchanged.
4. `proposals/README.md` index row for 008 added.
5. CHANGELOG.md `[Unreleased]` entry added on close (per archive convention).

## Risks & Mitigations
- **R1 — Silent loss of intent**. Removing the rows without logging the deferral could erase the build-out idea entirely. *Closed by* the mandatory PROGRESS.md Staged Improvement line in DoD #2.
- **R2 — Future drift**. Other docs may grow new mentions of `/audit` etc. *Closed by* leaving Proposal 007's R1 paragraph and the retro entry intact as breadcrumbs.

## Adversarial Pass (L1–Ln)
- **L1 — Stale `/audit` reference resurfacing.** A future doc edit could re-introduce `/audit`, `/backtest`, or `/risk-check` to `CLAUDE.md` by copy-paste from old retros or `proposals/007` §R1. **Closed by** leaving the deferral logged in `PROGRESS.md` Staged Improvements and in this proposal — anyone re-adding the row will find the "deferred" trail before merging.
- **L2 — PROGRESS.md Staged Improvement rots unactioned.** The line is written but no one ever builds the skills, so the gap persists indefinitely. **Closed by** treating `PROGRESS.md` Staged Improvements as the canonical backlog reviewed at War Room cadence; sustained inaction is a roadmap signal, not a bug.
- **L3 — Skill tool silent-fail UX unaddressed.** Even after this cleanup, any future typo (e.g. `/audti`) silently no-ops because the Skill tool ignores unknown names. **Closed by** flagging as a separate observation outside P008 scope; not blocking.

## Core Team Review (A–D)

### Quant Architect
APPROVE — Skills table should reflect what is on disk; nothing strategic at stake.

### Portfolio Manager
APPROVE — zero portfolio impact.

### CTO
APPROVE — minimal docs hygiene; correct call to defer the actual build.

### Risk Officer
APPROVE WITH CONDITIONS — the deferral must be logged in PROGRESS.md (not just deleted), so the gap is visible at the next roadmap review. Condition is captured in DoD #2.

## Delta Annexe — Round 1 (Core Team)
- **Absorbed**: Risk Officer condition (PROGRESS.md Staged Improvement line) — already in DoD #2.
- **Resisted**: none.

## Amendments
None.

## Status Log
- 2026-04-27 — DRAFT opened.
- 2026-04-27 — DONE. Three phantom rows deleted from CLAUDE.md; S-13 added to PROGRESS.md; CHANGELOG.md entry written; proposals/README.md updated. All DoDs verified.
