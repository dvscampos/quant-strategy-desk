---
id: 005
title: P-09 Cold-Reader Reword + Public Release Sanitisation Sweep
status: DONE
owner: Daniel
opened: 2026-04-26
updated: 2026-04-26
tags: [sanitisation, public-release, governance]
---

# 005 — P-09 Cold-Reader Reword + Public Release Sanitisation Sweep

## Summary

Resolved open process-bias item P-09 (cold-reader fragility in two prose sites) and executed a full public-release sanitisation sweep in preparation for the framework's initial push to `dvscampos/quant-strategy-desk` on GitHub. Includes the first `git init` and initial commit of the Quant Strategy Desk framework.

## Motivation / Problem

P-09 (logged 2026-04-26): two prose sites read fragile to a contributor with no project history:
- `docs/RISK_FRAMEWORK.md` §Evaluator Failure Protocol: "the failure mode the deterministic gate-evaluation pipeline was built to retire" assumed knowledge of a predecessor system.
- `PROGRESS.md` Completed bullet: "First session under the current War Room methodology" implied a prior methodology without naming the change.

Additionally, the framework was ready for external testing by friends, requiring a full sanitisation sweep to ensure nothing personal, sensitive, or misleading was in the tracked files.

## Proposal

**T1 — P-09 rewording (2 sites):**
- T1a: `docs/RISK_FRAMEWORK.md` §Evaluator Failure Protocol — name the prohibited behaviour explicitly.
- T1b: `PROGRESS.md` 2026-04 session bullet — drop temporal anchor, keep descriptive parenthetical.

**T2 — Public-release sanitisation sweep + git init:**
- T2a: Sanitisation audit across all tracked files; action findings.
- T2b: Create `local/.gitkeep`.
- T2c: `git init -b main`, pre-commit security scans, initial commit, push to GitHub.

**T3 — Phase 1B live smoke (date-locked):** SKIPPED — gate is 2026-05-16, today is 2026-04-26.

## Scope & Out-of-Scope

**In scope:** P-09 rewording, sanitisation sweep of tracked files, gitignore hygiene, initial commit and push.

**Out of scope:** T3 live smoke (date-locked), GitHub Actions / CI setup, LICENSE file, platform adaptation guide (S-8).

## Definition of Done

- [x] `grep -n "built to retire" docs/RISK_FRAMEWORK.md` → no matches
- [x] `grep -n "First session under the current War Room methodology" PROGRESS.md` → no matches
- [x] P-09 ticked resolved in PROGRESS.md §Open Process-Bias Items
- [x] SHARING.md §Cross-model critique removed; non-advice disclaimer added
- [x] `docs/COMPLIANCE.md` jurisdiction + non-advice header prepended
- [x] `brainstorms/INDEX.md` converted to stub; personal index at `local/brainstorms/INDEX.md`
- [x] `docs/retros/` deleted (stray duplicate; canonical in `local/retros/`)
- [x] `docs/*.html` moved to `local/` (generated artefacts)
- [x] `**/*.db`, `**/*.sqlite` in `.gitignore` (was `data/*.db` only)
- [x] `local/.gitkeep` created
- [x] Pre-commit security scans clean: `git grep --cached` for credentials, PII, known key prefixes
- [x] `git ls-files | grep -E '^(local/|\.env)'` → empty (allow `.gitkeep` and `templates/`)
- [x] Initial commit `fd4d036` on `main`; pushed to `https://github.com/dvscampos/quant-strategy-desk`
- [ ] T3 (DoD #10b): `python3 -m scripts.data fetch --session 2026-05 && gate_eval --session 2026-05` — **PENDING 2026-05-16**

## Risks & Mitigations

- **Sanitisation is irreversible post-push.** Mitigated by adversarial L1–L10 loophole pass, explicit `git grep --cached` content scans, and canary test before commit.
- **T3 failure could indicate a live-data bug.** Low probability given 82 tests + 12-month replay. Recoverable via patch commit. Framework degrades gracefully without data layer.
- **GitHub noreply email.** Author identity uses `71031575+dvscampos@users.noreply.github.com` to avoid real email in public commit history.

## Core Team Review (A–D)

### Quant Architect
APPROVE WITH CONDITIONS. Keep Proposal 003 citation in §Evaluator Failure Protocol. Stub must explain the convention or new users will be confused. Both conditions met in execution.

### Portfolio Manager
APPROVE. Scope bounded and ships value. P-09 was on the open list — closing it was overdue. Public release is what the framework was designed for from day one.

### CTO
APPROVE WITH CONDITIONS. Three hard checks required before commit: `git check-ignore` for personal files, `git grep --cached` for credentials (content scan, not filename scan), `.obsidian/` and `.DS_Store` confirmed ignored. All conditions met in execution. Gemini tightened the grep to `--cached` flag.

### Risk Officer
APPROVE WITH CONDITIONS. Treat "before push" as the only enforceable gate. Explicit user confirmation of remote URL required after staged-file list shown. Conditions met: user confirmed URL separately.

### Compliance Officer (F — relevant: public distribution)
APPROVE WITH CONDITIONS. Non-advice disclaimer added to SHARING.md and `docs/COMPLIANCE.md`. Conditions met.

## Cross-Model Critique

Gemini review conducted (two rounds):
- **Round 1 catch:** T3 evaporated from DECOMPOSE/ARCHITECT/FILES CHANGED despite being in the brief. Added in amendment with explicit SKIP resolution.
- **Round 2 catch:** CTO's `git ls-files | grep` checked filenames only, not content. Replaced with `git grep --cached` content scans.
- **Amendment:** `--cached` flag added to all `git grep` commands to ensure index is scanned (not working tree).

## Adversarial Loophole Pass (L1–L10)

See proposal amendment in session transcript. Key closures: canary test (L4), PII grep (L5), no symlinks (L3), no remote attached pre-commit (L10), commit message shown to user before execution (L7).

## Status Log

| Date | Status | Note |
|---|---|---|
| 2026-04-26 | DRAFT → APPROVED | Proposal + amendment approved after Gemini Round 2 cross-check |
| 2026-04-26 | APPROVED → DONE | All DoD items complete except T3 (pending 2026-05-16). Commit `fd4d036` pushed to GitHub. Code review: APPROVE. |
