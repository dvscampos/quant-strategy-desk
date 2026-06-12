---
id: 022
title: PORTFOLIO partner-name correction + IBKR read-only snapshot roadmap item
status: DONE
owner: Daniel
opened: 2026-06-02
updated: 2026-06-02
tags: [ledger, roadmap, ibkr]
---

# 022 — PORTFOLIO partner-name correction + IBKR read-only snapshot roadmap item

**Tier: LIGHT** — 2 files (`local/PORTFOLIO.md`, `PROGRESS.md`), ≤12 net lines, known pattern (text correction + roadmap-row append). Fully reversible. No irreversible step.

## Summary
Two unrelated-but-bundled housekeeping edits surfaced while clearing pre-flight for the May 2026 War Room. (1) The Ownership Tracking table in `local/PORTFOLIO.md` records the investor's partner as **"Sofia"** — a name the investor states he never provided; it reads like a template-example placeholder (`€400 Daniel, €200 Sofia`) that was promoted into the live ledger during Session #2 (April 2026). Correct it to **"PPDC"** (investor-supplied) and de-risk the seeding example so a placeholder can't be mistaken for real data again. (2) Add a staged-improvement roadmap item (S-21) for a read-only IBKR snapshot mode so future War Room sessions auto-verify positions + cash at open and reconcile at close, instead of relying on manual entry.

## Motivation / Problem
- **Data integrity:** a fabricated/placeholder partner name in a financial ownership ledger is a correctness defect. Verified the name lives **only** in `local/PORTFOLIO.md` (lines 43, 45, 49, 50) via repo-wide `grep -rliI "sofia"` (clean everywhere else).
- **Manual-entry gap:** `scripts/reconcile_ibkr.py` is post-execution only — `get_fills()` reads today's executions (`ib.reqExecutions()`), with no positions/cash snapshot mode (verified via Read of `scripts/reconcile_ibkr.py:1-80`). This session, the orchestrator verified holdings/cash by an ad-hoc inline `ib.positions()` / `ib.accountValues()` read against live TWS (port 7496). That read should be a first-class, repeatable mode, run at War Room **start** (verify ledger) and **finish** (reconcile).

## Proposal
**Item A — `local/PORTFOLIO.md` partner-name correction:**
- Line 45 (table header): `Sofia (€)` → `PPDC (€)`, `Sofia Cumulative (€)` → `PPDC Cumulative (€)`, `Sofia %` → `PPDC %`.
- Line 49: `Sofia **50.0%**` → `PPDC **50.0%**`.
- Line 50: `Sofia €500` → `PPDC €500`.
- Line 43 (instructional example): de-risk so a placeholder can't be mistaken for live data — `(e.g. "€400 Daniel, €200 Sofia")` → `(e.g. "€300 You, €100 Partner")`.
- Session #2 ownership row values are otherwise unchanged (Daniel €500 / PPDC €500, 50/50).

**Item B — `PROGRESS.md` S-21 staged-improvement row:**
- Append one row to the Staged Improvements table:
  - **#**: S-21
  - **Improvement**: IBKR read-only snapshot mode — add a `--snapshot` path to `scripts/reconcile_ibkr.py` (or a sibling) that pulls live positions + cash via `ib.positions()` / `ib.accountValues()` (read-only, non-default clientId), run at War Room start to verify the ledger and at finish to reconcile.
  - **Trigger Condition**: next time `scripts/reconcile_ibkr.py` is **edited**, or when manual ledger-vs-broker reconciliation first diverges. (This session exercised the API path via an ad-hoc inline read but did **not** edit the script — trigger not yet met. — Challenger R1-L4.)
  - **Why Not Now**: this session's inline read proved the API path works; productionising it (TWS-down fallback, paper/live port selection, output format) is its own small task, not part of running the May session.
  - **Compatible With Current?**: Yes — additive read-only script mode; no framework files change.

## Scope & Out-of-Scope
- **In:** the four PORTFOLIO.md text edits; one PROGRESS.md roadmap row.
- **Out:** actually building the `--snapshot` mode (that's the deferred S-21 work); any change to the Session #2 ownership split or amounts; any `agents/*.yml` or strategy/risk change.

## Definition of Done
- [ ] `grep -niI "sofia" local/PORTFOLIO.md` returns **zero** matches.
- [ ] `grep -oI "PPDC" local/PORTFOLIO.md | wc -l` returns **5** occurrences (3 in the line-45 header + line 49 + line 50). [`grep -c` counts lines, not occurrences — the header trio shares one line — Challenger R1-L1.]
- [ ] `grep -nF '€300 You, €100 Partner' local/PORTFOLIO.md` returns line 43; `grep -niE "sofia" local/PORTFOLIO.md` does not match the line-43 example. [Challenger R1-L6.]
- [ ] `grep -n "S-21" PROGRESS.md` returns the new row, rendered as a well-formed 5-column markdown row matching the table header (`# | Improvement | Trigger Condition | Why Not Now | Compatible With Current?`). [Challenger R1-L8.]
- [ ] Session #2 ownership arithmetic unchanged: Daniel and PPDC, 50/50 split.

**Regression gate (LIGHT, 1 item):** verified Proposal 021 (hypothesis-log lifecycle) shipped — `local/HYPOTHESIS_LOG.md` carries the stamp-in-place "Last Reviewed" column, append-only, no `## Investigated` archive. No regression. [Challenger R1-L10.]

## Risks & Mitigations
- **R1 — over-broad replace.** `Sofia` is a short token; a blind `replace_all` could touch unintended spots. Mitigation: only 4 known lines (verified by grep); use targeted `Edit` calls, then DoD grep confirms zero residual.
- **R2 — `local/` is untracked.** `git revert` won't restore PORTFOLIO.md. Mitigation: edits are trivial text I can re-apply; the prior content is captured verbatim in this proposal body.

## FILES CHANGED (PROPOSED)
- `MODIFY` `local/PORTFOLIO.md` — replace placeholder partner name "Sofia" → "PPDC" (lines 45/49/50); de-risk seeding example (line 43).
- `MODIFY` `PROGRESS.md` — append S-21 staged-improvement row (IBKR read-only snapshot mode).
- `CREATE` `proposals/022-portfolio-partner-name-and-ibkr-snapshot-roadmap.md` — this proposal (self-admin).
- `MODIFY` `proposals/README.md` — add 022 index row (self-admin); flip its status DRAFT→DONE in lockstep with frontmatter at close-out. [Challenger R1-L10 — the recurring 019 stale-status defect class.]

**Aggregate:** 4 files: 2 MODIFY (content) + 1 CREATE + 1 MODIFY (self-admin) = 4 ✓.

## REVERSIBILITY
- `local/PORTFOLIO.md` — **FULLY REVERSIBLE** (trivial text; prior values captured in this proposal). Untracked, so re-edit rather than `git revert`.
- `PROGRESS.md` / `proposals/*` — **FULLY REVERSIBLE** (`git revert`).
- No external state mutated. No IRREVERSIBLE step.

## Core Team Review (LIGHT — one-line verdicts)
- **Portfolio Manager:** APPROVE — ledger names must be accurate; split/amounts untouched.
- **CTO:** APPROVE — S-21 captured as deferred; no code built this session, so no review surface.
- **Risk Officer:** APPROVE — no risk parameter, position, or stop touched.
- **Quant Architect:** APPROVE — no strategy/signal surface.

## Status Log

> Append-only.

- 2026-06-02 — DRAFT opened.
- 2026-06-02 — Cross-Check path: isolated-challenger (no external model configured). Challenger R1: STRUCTURAL sound; 10 L-items. Absorbed L1/L4/L5/L6/L8(partial)/L10 (DoD-correctness, trigger wording, citation, regression gate, README lockstep — all scope-narrowing/correcting). Resisted L2 (proposal/README "Sofia" is correction audit-trail, not live ledger) and L8 label sub-claim (header verified "Why Not Now" at PROGRESS.md:72). L3 (PPDC opacity) + L7 (Daniel-vs-PPDC anonymisation asymmetry) escalated to user as design decisions. No L-item expanded scope.
- 2026-06-02 — User resolved L3 = keep PPDC opaque (no legend); L7 = keep "Daniel" as-is (only the partner placeholder corrected). Draft already matches both; no plan change.
- 2026-06-02 — APPROVED by user. Implemented via implementation-agent (Sonnet, Thrift Gate): 4 edits to `local/PORTFOLIO.md` + S-21 row to `PROGRESS.md`. Orchestrator verification gate PASS — all 5 DoD greps green (sofia=0, PPDC=5, example landed, S-21 well-formed, ownership row intact). **Scope incident:** implementation-agent added then `git checkout`-reverted a README row, which also wiped the orchestrator's legitimate 022 index row; restored by orchestrator (recurrence of the implementation-agent out-of-scope-touch anti-pattern, 2026-05-22). Not yet committed — CHANGELOG append + commit pending `/commemorate`.
- 2026-06-02 — DONE. `/commemorate`: governance 4/4 applicable (code-review N/A prose carve-out); diff matches PROPOSE; CHANGELOG `[Unreleased] ### Changed` entry appended; status flipped DONE across frontmatter / Status Log / README row. Committed with the S-21 roadmap row + this proposal; `local/PORTFOLIO.md` fix is in the untracked private ledger (verified by grep, not committed by design).
