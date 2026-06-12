---
id: 021
title: Hypothesis-log lifecycle — pointer + plain anti-bias line + stamp-in-place close-out
status: DONE
owner: Daniel
opened: 2026-06-02
updated: 2026-06-02
tags: [skill, war-room, hypothesis-log, governance, anti-bias]
supersedes: 020
---

# 021 — Hypothesis-log lifecycle (plain, final)

**Tier: MEDIUM** (4 functional files) — but deliberately **plain doc edits**, verified by reading, not by a grep-DoD battery. The elaborate DoD scaffolding of v2–v4 became its own defect source across four Challenger rounds (L-counts 8→13→11→12, non-converging); this v5 strips it back to the minimum that delivers the two operator asks on a one-person, fully-reversible markdown tool. See the Status Log + Delta Annexes below for the full adversarial history.

## Summary
Three small additions so the `/war-room` skill and template handle user hypotheses well: (1) the skill names the log; (2) a one-line anti-bias instruction; (3) a stamp-in-place close-out so every open idea records when it was last looked at and the outcome. No idea is ever moved or deleted.

## Motivation / Problem
Operator added QTUM and asked it (a) not bias the War Room and (b) be marked, after a session checks it, with which War Room looked at it and what the finding was. Verified gaps: the skill never names the log; no operative anti-bias line; nothing writes the review back into the log itself.

## The changes (concrete text)

**1. Skill pointer** — `.claude/commands/war-room/SKILL.md`, Phase 4 bullet (~line 280):
> `- Phase 4: Signal & Opportunity (Sonnet sub-agent) — see the template's Phase 4 step for the `local/HYPOTHESIS_LOG.md` open-ideas input.`

**2. Anti-bias line** — `brainstorms/_TEMPLATE.md`, Phase 4 (after line 395):
> *User hypotheses are investigated **alongside** the Signal Generator's own independent search, never in place of it. Report each with a Status (INVESTIGATED / DISMISSED / CARRIED FORWARD) and a one-line Finding on whether the data supported it — an idea may be found unsupported without forcing a trade. The orchestrator records the verdict and is free to dismiss a thinly-supported "confirm".*

(The orchestrator — a separate Opus agent that judges the Sonnet Signal Generator's output — is the independent check against overt parroting; the narrow residual of *subtle* anchoring is accepted for a one-person monthly review. Structural two-pass remains a future upgrade if parroting is ever observed.)

**3. Stamp-in-place close-out** — `brainstorms/_TEMPLATE.md`, after the Hypothesis Log Review (~line 417):
> *Then update `local/HYPOTHESIS_LOG.md` itself: in each Open Idea's "Last Reviewed" column, append `<YYYY-MM>:<STATUS>` for this session (an idea you didn't reach is `CARRIED FORWARD`). Append — never overwrite prior entries — and never move or delete ideas; the one-line finding lives here in the session file.*

**4. Session Close item** — `brainstorms/_TEMPLATE.md`, Session Close Checklist (~line 846):
> `- [ ] Every Open Idea in `local/HYPOTHESIS_LOG.md` has a "Last Reviewed" entry for this session.`

**5/6. Log format** — `local/templates/HYPOTHESIS_LOG.template.md` (tracked) **and** `local/HYPOTHESIS_LOG.md` (live):
- Open Ideas table header gains a 4th column: `| Date | Observation / Idea | Source | Last Reviewed |` (separator row + the existing China-EV / QTUM rows widened to 4 cells; their Last Reviewed = `—`).
- Rewrite the intro so it describes stamp-in-place (drop the "moved to 'Resolved'" prose and the session-*start* move language).
- **Delete the `## Investigated` section entirely** (and its H-001 row) — stamp-in-place makes it redundant; keeping it would create two parallel records (resolves the v4-L6 dead-state / 2026-04-26 anti-pattern).

**7. Protocol Audit row** — `.claude/commands/war-room/SKILL.md` (~line 370):
> `| Hypothesis log updated? | Every Open Idea has a "Last Reviewed" entry for this session | |`
- and replace the stale "(e.g., 9/9)" score example at line 372 with "(e.g., N of N checks)".

## Definition of Done (read, don't grep)
After the edits, read the four files and confirm:
1. The skill Phase 4 bullet names `local/HYPOTHESIS_LOG.md`; the new audit row is present; "9/9" is gone.
2. The template carries the anti-bias line, the close-out instruction, and the Session Close item.
3. Both log files have the 4-column Open Ideas table (header + separator + data rows all 4 cells), an intro describing stamp-in-place, and **no `## Investigated` section**.
4. The live file's China-EV and QTUM rows are intact (data preserved).

## Files changed
- `MODIFY` `.claude/commands/war-room/SKILL.md` — pointer (#1) + audit row (#7) + 9/9→N-of-N
- `MODIFY` `brainstorms/_TEMPLATE.md` — anti-bias line (#2) + close-out (#3) + Session Close item (#4)
- `MODIFY` `local/templates/HYPOTHESIS_LOG.template.md` — column + intro rewrite + delete `## Investigated` (#5, tracked)
- `MODIFY` `local/HYPOTHESIS_LOG.md` — same (#6, live gitignored; **pre-edit backup** `cp local/HYPOTHESIS_LOG.md /tmp/HYPOTHESIS_LOG.021-pre.bak` first, since git can't restore it)
- `CREATE`/`MODIFY` self-admin: this artefact, `proposals/README.md` row, 020 → SUPERSEDED.

## Reversibility
Fully reversible via `git revert` for all tracked files; the live `local/HYPOTHESIS_LOG.md` (#6) is gitignored → manual undo only, hence the pre-edit backup. Deleting the `## Investigated` section removes the live H-001 row — captured in the backup; H-001 (DFNS) is also recorded in `local/PORTFOLIO.md` and prior session files, so no history is lost.

## Adversarial note (why no further L-pass)
Four Challenger rounds were run (full record below). The loop stopped converging and began attacking its own DoD scaffolding; the operator directed a strip-back. The two genuine residuals from the last round are resolved here by **removing** surface, not adding it: v4-L6 (parallel records) → delete `## Investigated`; v4-L7 (bias backstop) → already settled (the orchestrator is a separate judging agent). Remaining v4 items were grep-DoD brittleness, dissolved by dropping the grep battery. This is scope-reduction, the safe direction — no further mandatory round.

## Delta Annexe (Challenger 4b — MEDIUM, on v2)
Cross-Check path: isolated-challenger (no external model configured). Verdict: **STRUCTURAL sound**; −0.30 substantive cluster. 8 items: L1 (audit baseline) absorbed → content-based; L2 (dedup) absorbed; L3 (bias rigour) → operator Option-1; L4 (Resolved/Investigated) absorbed; L5 (consumer check) absorbed; L6 (9/9) absorbed; L7 (column ownership) absorbed; L8 (DoD line-anchor) absorbed. *(Re-reviewed in 4b-delta below — several superseded by the v3 redesign.)*

## Delta Annexe (Challenger 4b-delta — on the v2 absorbed delta; led to v3)
Operator-prompted re-check of text authored after 4b. Verdict: **STRUCTURAL flawed**, 13 items. L1/L12 (5-way vocabulary incoherence) → dissolved by v3 single enum; L2 (never-reached) → addressed; L3 (audit vs dedup) → dissolved by stamp-in-place; L4 (column-not-added) → delta-scoping artefact; L5 (forced-ternary false precision) → ternary dropped; **L6 (Phase 3/8 don't backstop parroting) → corrected: the orchestrator-synthesis layer is the backstop, verified `_TEMPLATE.md:411-417, 533-541`**; L7 (no instrument) → orchestrator Finding-review is the instrument for overt parroting; L8/L13 → header sync/framing absorbed; L9 (independence rule) → resisted, user hypothesis ≠ orchestrator carry-forward; L10/L11 → dissolved by stamp-in-place.

## Delta Annexe (Challenger v3 — on the stamp-in-place redesign)
Verdict: **STRUCTURAL sound**; −0.40, one structural (L5). 11 residue items absorbed into v4 (later found to be partly self-inflicted scaffolding — see v4-delta). Key: L4 (`NOT REACHED` 4th token) → dropped, reuse `CARRIED FORWARD`; L5 (un-parseable triple cell) → `Last Reviewed` holds short `<YYYY-MM>:<STATUS>`, detail in session file; L9 (overwrite) → append; L11 (gitignored edit) → pre-edit backup.

## Delta Annexe (Challenger v4-delta — on the v4 absorptions; led to this v5 strip-back)
Verdict: **STRUCTURAL flawed**, 12 items. **L2 (wrong-skill-path) verified FALSE** — Challenger hallucination; proposal path `.claude/commands/war-room/SKILL.md` is correct. Most items (L1/L3/L8/L9/L10) attacked the **grep-DoD scaffolding prior rounds added** — dissolved here by dropping the grep battery in favour of read-verification. Genuine residuals: **L6** (parallel records) → resolved by deleting `## Investigated`; **L7** (bias backstop softening) → already settled (orchestrator is a separate judging agent; only subtle-anchoring residual remains, accepted). Meta-finding: non-converging L-counts (8→13→11→12) → operator-directed strip-back.

## Status Log
- 2026-06-02 — DRAFT created. Supersedes 020 (pointer folded in as item #1).
- 2026-06-02 — Challenger 4b: STRUCTURAL **sound**, 8 items; L3→operator Option-1.
- 2026-06-02 — Challenger 4b-delta: STRUCTURAL **flawed**, 13 items (operator-prompted re-check of absorbed delta). PAUSED → v3.
- 2026-06-02 — v3 redesign (operator-approved): removed move-to-Investigated → stamp-in-place.
- 2026-06-02 — Challenger v3: STRUCTURAL **sound**, 11 items absorbed → v4.
- 2026-06-02 — Challenger v4-delta: STRUCTURAL **flawed**, 12 items (operator-prompted). L2 verified false; most items were self-inflicted DoD scaffolding. Meta-finding: non-converging loop. ESCALATED.
- 2026-06-02 — **v5 strip-back (operator-approved):** reduced to plain doc edits verified by reading; dropped the grep-DoD battery; deleted `## Investigated` (resolves v4-L6); bias backstop settled (v4-L7). Adversarial loop closed by scope-reduction.
- 2026-06-02 — **APPROVED + implemented** via implementation-agent (Sonnet); diff verified against FILES CHANGED (all 4 functional files correct, data rows preserved, live-log backup at /tmp/HYPOTHESIS_LOG.021-pre.bak). `/code-reviewer`: **APPROVE WITH NOTES**. Notes addressed: (1) pre-existing `local/local/INVESTOR_PROFILE.md` typo at `_TEMPLATE.md:511` fixed (in-scope sibling-consistency absorption, same defect class as the line-413 fix); (2) CHANGELOG append deferred to `/commemorate`.
- 2026-06-02 — **DONE** via `/commemorate`: 82 tests green (no doc edit tripped a skill-invariant/template test); PROGRESS.md Completed entry added; CHANGELOG `[Unreleased] → Changed` entry appended; status reconciled DONE across frontmatter / README row / this Status Log (Step 6c PASS); 020 SUPERSEDED. Committed in the same changeset.
