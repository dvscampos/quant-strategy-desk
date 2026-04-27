---
id: 007
title: First-run pre-flight guard for /war-room skill
status: DONE
owner: Daniel Campos
opened: 2026-04-27
updated: 2026-04-27
tags: [skills, onboarding, ux, war-room]
---

# 007 — First-run pre-flight guard for /war-room skill

**Tier: LIGHT**

## Summary
Add a pre-flight block at the top of `.claude/commands/war-room/SKILL.md` that detects a missing `local/INVESTOR_PROFILE.md`, halts the skill before Phase 0, and redirects the agent to the First-Run Detection flow already specified in `CLAUDE.md`. Today the skill silently stalls if onboarding has not run, which is exactly what happened to a Windows-installing user this week.

## Motivation / Problem
Reproduction:
1. `git clone` the repo on a fresh machine (no `local/` artefacts).
2. Open Claude Code, run `/war-room`.
3. Skill enters Phase 0 (Checkpoint Recovery), then Pre-Session Preparation Step A (Portfolio Valuation), which assumes `local/PORTFOLIO.md` exists.
4. The agent hangs with no user-facing error because the failure mode is "missing context" rather than a thrown exception.

The First-Run Detection flow in `CLAUDE.md` (lines 7–48) already specifies the correct behaviour — onboard the user via the 11-question flow, run `scripts/init_workspace.py`, then hydrate `local/INVESTOR_PROFILE.md` and friends. The bug is purely that `/war-room` never consults this flow. CLAUDE.md is loaded into context at session start, but skill files are self-contained — the skill must enforce its own pre-conditions, not rely on the agent remembering CLAUDE.md mid-skill.

## Proposal

Modify `.claude/commands/war-room/SKILL.md` only. Add a new section, **"Pre-Flight: First-Run Detection"**, immediately after the H1 title and before "Phase 0: Checkpoint Recovery".

Block contents (drafted; final wording reviewed in Core Team):

```markdown
## Pre-Flight: First-Run Detection

> **Run this BEFORE Phase 0.** If the workspace has never been initialised,
> a War Room session cannot proceed — Phase 0 checkpoint recovery and
> Pre-Session Preparation both assume `local/` artefacts exist.

```python
import pathlib
profile = pathlib.Path("local/INVESTOR_PROFILE.md")
if not profile.exists():
    print("FIRST_RUN_DETECTED")
```

If `FIRST_RUN_DETECTED` is printed:
1. Stop the skill immediately. Do NOT enter Phase 0.
2. Tell the user verbatim: *"Your investor profile hasn't been set up yet — `/war-room` can't run without it. Onboarding takes about 2 minutes (11 questions + a one-line setup script). Want me to run it now?"*
3. If the user confirms, follow the **First-Run Detection** flow in `CLAUDE.md` (the 11-question onboarding, `scripts/init_workspace.py`, then hydration of `local/INVESTOR_PROFILE.md`). After hydration completes, ask the user whether to proceed with `/war-room` in a fresh session or continue now.
4. If the user declines, exit the skill cleanly without writing any files.

Do NOT auto-trigger onboarding — this is a destructive-adjacent operation (writes to `local/`, modifies `docs/COMPLIANCE.md`, edits `brainstorms/_TEMPLATE.md`). User confirmation is required.
```

## Scope & Out-of-Scope

**In scope:**
- Single-file edit to `.claude/commands/war-room/SKILL.md`.
- Manual smoke test: rename `local/INVESTOR_PROFILE.md` → `local/INVESTOR_PROFILE.md.bak`, run `/war-room`, verify the pre-flight block fires; restore.

**Out of scope (deferred):**
- Pre-flight guards for `/audit`, `/backtest`, `/risk-check`. The CLAUDE.md skills table lists them as Local skills but they don't exist on disk — that's a documentation drift issue (separate proposal).
- Checks for `local/PORTFOLIO.md`, `.env` / FRED key, Python deps, `scripts/init_workspace.py` partial-failure recovery. Each is a real silent-fail vector but warrants its own scoped proposal — see RISK FLAGS.
- Auto-running onboarding without user confirmation.

## Definition of Done
1. `.claude/commands/war-room/SKILL.md` contains the **Pre-Flight: First-Run Detection** section, placed before "Phase 0: Checkpoint Recovery".
2. Smoke test (manual, documented in Status Log): with `local/INVESTOR_PROFILE.md` temporarily renamed, `/war-room` halts at pre-flight and prints the user-facing message instead of entering Phase 0.
3. Smoke test (manual): with `local/INVESTOR_PROFILE.md` present, `/war-room` skips the pre-flight block and proceeds to Phase 0 unchanged.
4. CHANGELOG entry under `### Fixed` linking to this proposal.

## Risks & Mitigations

- **R1 — Documentation drift on phantom skills.** CLAUDE.md advertises `/audit`, `/backtest`, `/risk-check` as Local skills but they don't exist. Users running them today get "skill not found" silently. Out of scope for this proposal but should become Proposal 008. *Mitigation*: flag in commemorate so it's logged.
- **R2 — Other silent-fail surfaces remain.** Even after this fix, `/war-room` can still fail mid-session if `.env` is missing the FRED key, `requirements.txt` was never installed, or `scripts/init_workspace.py` partially failed. *Mitigation*: this proposal only closes the hardest-to-diagnose case (no `INVESTOR_PROFILE.md`); a follow-up "preflight bundle" proposal can extend the guard once we observe which failures users actually hit.
- **R3 — User in workspace with `INVESTOR_PROFILE.md` but no other `local/` files.** E.g. user manually deleted `local/PORTFOLIO.md`. Pre-flight passes but Phase 1 fails. Same mitigation as R2 — out of scope for this proposal.

## Core Team Verdicts (LIGHT — one-line each)

- **A (Quant Architect):** APPROVE — single-file edit, reuses existing skill-file idiom.
- **B (Portfolio Manager):** APPROVE — minimum scope, fixes the reported bug, no P&L impact.
- **C (CTO):** APPROVE WITH CONDITIONS (both met by current draft) — (1) pre-flight must NOT auto-run `scripts/init_workspace.py`; "User confirmation is required" wording must stay verbatim in the block. (2) No new env vars, API surface, or credentials. Any amendment that weakens (1) reverts the verdict to REJECT.
- **D (Risk Officer):** APPROVE — silent stall is the worst failure mode; this closes it. Flag for `/retro`: add a first-run smoke test to the regression gate.

> Verdicts written by Orchestrator (LIGHT tier). No sub-agent consultation — appropriate for a one-file skill edit. If any reviewer wants to escalate, raise it before approval.

## Delta Annexe
N/A — LIGHT.

## Amendments

- **A1 (2026-04-27, post-`/code-reviewer`)** — Tightened the existence check from `not profile.exists()` to `not profile.exists() or profile.stat().st_size == 0` so that a zero-byte profile (left behind by a partial-init failure) is also caught. One-line change, strictly tightens the guard, no behaviour change for valid profiles. Smoke test added: zero-byte file → `FIRST_RUN_DETECTED`. NOTE 2 from the review (advisory vs. enforced check) is **WON'T FIX** — Claude Code skills are prompt scaffolds, hard runtime enforcement is not available in this layer; the pattern is consistent with Phase 0 checkpoint recovery.

## Status Log

- 2026-04-27 — DRAFT opened.
- 2026-04-27 — APPROVED by user (LIGHT tier, A/B/D plain APPROVE; C APPROVE WITH CONDITIONS, both met by current draft).
- 2026-04-27 — IN PROGRESS → DONE. Edit landed in `.claude/commands/war-room/SKILL.md` (Pre-Flight: First-Run Detection block before Phase 0). Smoke tests passed: profile present → `PROFILE_OK`; profile renamed away → `FIRST_RUN_DETECTED`; profile restored. CTO conditions remain satisfied — block does not auto-run `scripts/init_workspace.py` and contains "User confirmation is required" verbatim.
- 2026-04-27 — Amendment A1 applied post-`/code-reviewer`: zero-byte profile also triggers `FIRST_RUN_DETECTED`. Third smoke test passed (touch zero-byte file → `FIRST_RUN_DETECTED`). NOTE 2 marked WON'T FIX (skill-layer limitation).
