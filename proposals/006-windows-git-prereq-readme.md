---
id: "006"
title: Add Windows Git prerequisite to README
status: DONE
owner: Daniel Campos
opened: 2026-04-27
updated: 2026-04-27
tags: [docs, onboarding, windows]
---

# 006 — Add Windows Git prerequisite to README

## Summary
A Windows user discovered that Claude Code requires Git for Windows to be installed before it can run local sessions (it needs `bash.exe` as its shell). The README's Requirements and Quick Start sections make no mention of this, causing a confusing mid-setup prompt. This proposal adds a clear prerequisite note so Windows users are not surprised.

## Motivation / Problem
Claude Code on Windows requires `bash.exe`, which it sources from Git for Windows. Without it, the desktop app shows an "Install Git" blocking dialog. The current README lists no Git requirement for Windows users, so the first sign of the problem is that dialog rather than a friendly instruction.

## Proposal
- **Requirements section**: add a Windows-specific line explaining that Git for Windows is required as a shell dependency (not for version control), with a link to git-scm.com.
- **Quick Start section**: add a short callout above the `git clone` command block so Windows users know to install Git first.

### Files changed
- `MODIFY` `README.md`

## Scope & Out-of-Scope
**In scope**: README prose additions only.
**Out of scope**: USER_INSTRUCTIONS.md, SHARING.md, CI, scripts.

## Definition of Done
- [ ] Requirements section includes a Windows Git note with a clear "why" (shell, not version control).
- [ ] Quick Start section has a visible Windows callout before the clone command.
- [ ] No other content in README is altered.

## Risks & Mitigations
None — purely additive documentation change. Fully reversible via `git revert`.

## Core Team Review
N/A — documentation-only LIGHT proposal.
