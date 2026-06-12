---
id: 020
title: Surface HYPOTHESIS_LOG.md read in /war-room SKILL.md Phase 4 (pointer to template)
status: SUPERSEDED
superseded_by: 021
owner: Daniel
opened: 2026-06-02
updated: 2026-06-02
tags: [skill, war-room, hypothesis-log, governance]
---

# 020 — Surface HYPOTHESIS_LOG.md read in /war-room SKILL.md Phase 4

**Tier: LIGHT** — 1 file (`.claude/commands/war-room/SKILL.md`), 1 line extended (a deferring pointer, no net new mechanism), known pattern (the Brainstorm Session outline already defers to the template; this names one more template step).

## Summary
The `/war-room` SKILL.md never names `local/HYPOTHESIS_LOG.md` (`grep -in hypothesis` → NONE), even though the template (`brainstorms/_TEMPLATE.md:395`) reads it at Phase 4 and feeds open ideas to the Signal Generator. This proposal extends the skill's existing Phase 4 outline bullet with a one-clause **pointer** to that template step — so a reader scanning the skill sees the hypothesis log exists as a Phase 4 input — **without re-stating the mechanism, timing, status enum, or any exemption** (all of which stay owned by the template, the single source of truth).

## Motivation / Problem
A user added a candidate (QTUM) to `local/HYPOTHESIS_LOG.md` and asked whether the next War Room would check it. The read is wired only in the template; the skill is silent. Two earlier drafts of this proposal tried to *restate* the read inside the skill (v1 in the Phase 4 bullet, v2 as a new prep-time Step C2). Both drew structural Challenger findings: any restatement creates a second copy of timing/enum/exemption semantics that drifts from the template (R1-L1 placement inertness; R2-L2 prep-vs-run timing contradiction; R2-L5 self-authored independence exemption; R2-L8 status-enum drift). The correct fix is a **pointer, not a copy**: surface the log by name in the skill and defer everything else to the template.

Faithfulness to the war-room ethos: the hypothesis log is a *user scratchpad* whose open ideas are fed to the Signal Generator "alongside their own signal search" (`local/HYPOTHESIS_LOG.md` intro; `_TEMPLATE.md:395`). The pointer surfaces that input without altering the Signal Generator's independent search and without pinning a session-lifecycle moment the canon deliberately leaves loose (the log says "at session start"; the template says "before running" — the pointer asserts neither).

## Proposal
Extend the existing Phase 4 bullet in the skill's "Brainstorm Session" outline (`SKILL.md:280`):

Current:
```
- Phase 4: Signal & Opportunity (Sonnet sub-agent)
```

Proposed:
```
- Phase 4: Signal & Opportunity (Sonnet sub-agent) — see the template's Phase 4 step for the `local/HYPOTHESIS_LOG.md` open-ideas input.
```

Wording notes (Challenger R3 absorbed): "see … for" makes it unambiguously a pointer, not an assertion of a "read" action (R3-L1); "open-ideas" reuses the template's own phrasing at line 395 ("open ideas"); "input" is neutral and avoids the over-promising verb "defined in" (R3-L6).

Placement rationale: the Phase 4 bullet is where the template's read actually lives (R2-verified), so the pointer is timing-faithful; and the whole "Brainstorm Session" section is explicitly an outline that defers to the template ("Follow the full War Room template…", `SKILL.md:276`), so a deferring pointer is the outline's proper function (resolving R1-L1, which objected only to an *actionable* instruction in a non-executable outline).

## Scope & Out-of-Scope
- **In scope**: extend one existing bullet (`SKILL.md:280`) with a deferring pointer.
- **Out of scope**: any restatement of the read mechanism, timing, status enum, or independence-rule exemption (deliberately left to the template); the Protocol Audit table; the template itself (line 395 already correct); the pre-existing template-side gaps the Challenger noted in passing (no source-drain back into the log — R2-L9) which are not introduced by this change and belong on a separate ticket if pursued.

## Definition of Done
- [ ] `grep -cF "local/HYPOTHESIS_LOG.md" .claude/commands/war-room/SKILL.md` returns ≥1 (skill now names the log; closes the silence gap and the exact-filename guard subsumes the `local/local/` typo class).
- [ ] The match sits on the Phase 4 bullet inside the "Brainstorm Session" outline (verify: `grep -n "Phase 4: Signal" SKILL.md` and the hypothesis match share a line region ~280).
- [ ] The added clause contains "template" (it is a pointer) and adds NO status enum — runnable: `git diff HEAD -- .claude/commands/war-room/SKILL.md | grep '^+' | grep -E "INVESTIGATED|DISMISSED|CARRIED FORWARD"` returns nothing (R3-L4).
- [ ] The added clause carries NO lifecycle-timing assertion of any form — runnable: `git diff HEAD -- .claude/commands/war-room/SKILL.md | grep '^+' | grep -iE "prep|before (launching|running)|at session start"` returns nothing (property-based, not a closed blocklist — R3-L3).
- [ ] `git diff --stat` shows 1 file changed; and the added line is the only `^+` content line beyond the bullet itself (verify the diff hunk by eye — `--stat` reports counts, not "one line", R3-L5).

## Risks & Mitigations
- **Pointer redundancy** (a reader who already follows the template gets the read anyway): accepted — the value is salience for a skill-first reader, at a cost of one clause; this is belt-and-braces, explicitly.
- **Anchor staleness** (if the template's "Phase 4" heading is renumbered): mitigated by referencing the section by its name role ("the template's Phase 4 section" — the template heading is "Phase 4: Signal & Opportunity Identification", the same anchor the skill bullet itself already uses), not a line number.

## Adversarial Loophole Pass
**L1 — Pointer inertness.** Risk: a pointer adds nothing if the reader already follows the template. **Closed by** naming `local/HYPOTHESIS_LOG.md` in the skill (previously absent), giving a skill-scanning orchestrator explicit salience that the log is a Phase 4 input; the template remains the single source for how.
**L2 — Anchor drift.** Risk: "the template's Phase 4 step" goes stale if the template renumbers phases. **Closed by** using the section's name anchor. Note (R3-L7): the match is prefix-partial, not exact — the skill bullet says "Phase 4: Signal & Opportunity" while the template heading is "Phase 4: Signal & Opportunity **Identification**"; the shared "Phase 4: Signal & Opportunity" prefix is the stable anchor and is the token a future anchor-staleness grep should use.

## Delta Annexe (Challenger R3 — v3 pointer)
R3 returned **STRUCTURAL: sound** (ship-authoritative); confidence delta −0.30 from a substantive cluster. Disposition:
- **R3-L1** (coined "open-ideas read") — **absorbed**: clause reworded to "see the template's Phase 4 step for the `local/HYPOTHESIS_LOG.md` open-ideas input"; drops the coined "read" noun, reuses template's "open ideas".
- **R3-L2** (anchor ambiguity vs two "Hypothesis Log Review" headings at template lines 189/411) — **resisted**: v3 points to the Phase 4 *read* (template line 395 prose), not to either "Hypothesis Log Review" heading; v3 dropped the outcome-recording instruction entirely, so the ambiguity the item describes is not reachable from the proposed clause. Verified via grep of `_TEMPLATE.md` (189 `## Hypothesis Log Review`, 411 `### Hypothesis Log Review`, 395 read prose).
- **R3-L3** (timing-check was a closed blocklist) — **absorbed**: DoD timing check rewritten property-based (`prep|before (launching|running)|at session start`).
- **R3-L4** (enum check not runnable) — **absorbed**: DoD enum check now a runnable `git diff | grep -E`.
- **R3-L5** (`--stat` conflates runnable + eyeball) — **absorbed**: DoD reworded to verify the diff hunk by eye, not via `--stat` alone.
- **R3-L6** ("defined in" over-promises completeness) — **absorbed**: replaced with "see … for".
- **R3-L7** (L-pass exact-match mis-cite) — **absorbed**: L2 above now records the prefix-partial match.

## Core Team Review (A–D)
LIGHT tier — one-line verdict:
**Core Team: APPROVE** — a deferring pointer that names the log and leaves all mechanism with the template; no logic, no data, no timing assertion, no irreversible step. Resolves the structural findings of both prior Challenger rounds by *not restating* what the template owns.

## Reversibility
**FULLY REVERSIBLE** — single-line doc edit to a skill body; `git revert` restores prior state.

## Status Log
- 2026-06-02 — DRAFT v1 (restate read in Phase 4 bullet).
- 2026-06-02 — Challenger R1 (isolated-challenger; no external model configured): STRUCTURAL flawed. L1 (outline-bullet inertness) absorbed → v2 relocated to a prep-time Step C2; L2 (independence collision) resisted.
- 2026-06-02 — Challenger R2 (isolated-challenger): STRUCTURAL flawed. Root cause: R1's absorption EXPANDED scope (1-line → 6-line C2 step), re-firing the defect class (CLAUDE.md G15). R2-L2 (prep-vs-run timing), L3 (false Step-C analogy), L5 (self-authored exemption), L8 (status-enum drift) all stemmed from the restatement. Operator decision (user): pivot to the minimal pointer approach — re-state nothing, defer to template. v3 redrafted accordingly; this collapses L2/L3/L5/L7/L8/L10/L11 by construction (no mechanism restated).
- 2026-06-02 — Challenger R3 (isolated-challenger; on v3 pointer): **STRUCTURAL sound** (ship-authoritative per iteration discipline); confidence delta −0.30, substantive cluster. All 7 items substantive-or-below; 6 absorbed (wording precision + runnable DoD), 1 resisted-with-verification (L2). See Delta Annexe.
- 2026-06-02 — **SUPERSEDED by 021.** Operator chose (AskUserQuestion) to bundle this converged pointer with two new mechanism additions (anti-bias guard + close-out write-back) into a single MEDIUM proposal. The pointer (v3, Challenger-sound) carries forward verbatim as 021 item #1; this file is retained as the pointer's design provenance (R1→R3 history).
