---
id: 019
title: S-20 AGENTS.md archetype-line correction + gs_compliance EN/PT example tidy
status: DONE
owner: Daniel
opened: 2026-05-22
updated: 2026-05-22
tags: [governance, personas, S-20, documentation]
---

# 019 — S-20 AGENTS.md archetype-line correction + gs_compliance EN/PT example tidy

**Tier: LIGHT** — 2 files; ~4 lines touched (+1 net); known pattern (text correction).
`AGENTS.md` is narrative prose; the `gs_compliance.yml` change is a one-string example
tidy in `review_prompt`. Fully reversible. No irreversible step → Step 4b Dual-Model
Cross-Check not formally triggered; a user-requested Isolated-Challenger pass was run
regardless (see Delta Annexe).

## Summary

Two small repo-local corrections batched into one proposal. **Item A (S-20)** fixes two
`AGENTS.md` archetype lines in the Actionability-contract list that became actively
contradictory with their personas after Proposals 017 and 018. **Item B** (optional,
cosmetic) generalises a Portugal-language literal in a `gs_compliance.yml` example
string. S-20 is the sanctioned vehicle for the AGENTS.md edit — Proposals 017 and 018
deliberately deferred it here because editing AGENTS.md re-opens governance-doc scope.

## Motivation / Problem

**Item A.** `AGENTS.md` §"Actionability contract" lists per-archetype `domain-native fix
examples` (line 117). Two lines now contradict the personas they describe (line numbers
verified via `grep -n`):

- **Line 120** — `- Execution → venue / routing / TWAP / child-order fixes`. The
  Execution archetype now contains only `virtu_execution.yml`, which Proposal 018
  re-architected from an institutional execution-algorithm developer to a retail
  execution-quality analyst. Its `system_prompt` forbidden-phrases line (verified
  `virtu_execution.yml:96`) now **bans** "TWAP" and the smart-order-routing family.
  "venue"/"routing" describe a duty the re-architected persona explicitly assigns to
  the broker, not itself (verified `virtu_execution.yml:90` — "venue routing is the
  broker's delegated best-execution duty"); "child-order" is institutional
  order-slicing the retail persona no longer performs. Every term on line 120 is now
  wrong for the persona it describes.

- **Line 121** — `- Quant signal (Citadel, point72, AQR, dimensional, renaissance) →
  IC / decay / multiple-testing / OOS validation / capacity fixes`. Proposal 017
  re-architected `renaissance_backtesting.yml` into a backtest-overfit researcher; its
  forbidden-phrases line (verified `renaissance_backtesting.yml:84`) now bans
  "information coefficient", "IC decay", and "signal capacity estimate" as Citadel
  territory. So "IC / decay / capacity" on line 121 is **actively contradictory** with
  `renaissance` specifically — but that vocabulary remains correct for the other four
  personas on the line (Citadel especially — it is Citadel's signature required
  vocabulary, verified `citadel_alpha.yml:77`).

**Item B.** `gs_compliance.yml:63` (verified) carries the example-fix string
`"block until PRIIPs KID confirmed EN/PT"`. "PT" is a Portugal-language literal in an
illustrative `e.g.` list. The operative instruction (line 56) is already correctly
parameterised ("for the investor's jurisdiction"). Cosmetic, zero behavioural risk.
Disclosed in the 2026-05-22 no-hardcode audit (`audit_agent_yaml_no_hardcode`), not
actioned then because a persona mutation needs `/propose`.

## Proposal

### Item A — AGENTS.md archetype lines

**Line 120 — re-word in place** to virtu's retail surface:

> `- Execution → order-type / timing / commission-drag / fractional-share fixes`

Verified against `virtu_execution.yml`: "commission drag" and "fractional shares" are
literal Required-vocabulary tokens (line 95); order-type and timing are the first two
of the four retail levers (`system_prompt` lines 67–72). The line matches virtu's
`review_prompt` fix examples (line 110: "switch from market to marketable-limit",
"consolidate 3 monthly contributions", "place the order 30 minutes after the open").

**Line 121 — split `renaissance` out** rather than re-word the shared line.

*Reasoning (the judgement call flagged in the S-20 brief).* Two options were weighed:

1. *Re-word line 121* to drop "IC / decay / capacity" — **rejected**: that vocabulary
   is Citadel's signature Required vocabulary (`citadel_alpha.yml:77`) and apt for
   point72/AQR. Re-wording the shared line to a renaissance-safe common denominator
   would strip the line's accuracy for the other four personas to fix one.
2. *Split `renaissance` onto its own archetype line* — **chosen**: `renaissance`'s
   forbidden-phrases line actively bans the line-121 vocabulary, so it cannot stay on
   that line at all; and Proposal 017 re-scoped it to overfit detection, a recognisably
   different review lens from signal-IC research. The new line uses `renaissance`'s own
   `review_prompt` fix-example vocabulary.

Resulting two lines (line 121 loses `renaissance`; one new line inserted immediately
after it):

> `- Quant signal (Citadel, point72, AQR, dimensional) → IC / decay / multiple-testing / OOS validation / capacity fixes`
> `- Overfit detection (renaissance) → calibration-window / deflated-Sharpe / purged-k-fold / turnover-cost-ratio fixes`

The new line's four terms are all present in `renaissance_backtesting.yml` — its
`review_prompt` fix examples (line 102: "reject signal if deflated Sharpe <2.0",
"require purged k-fold cross-validation", "block deployment if turnover-cost ratio
>30%") plus its core calibration-window check. **The archetype list does not assert
vocabulary exclusivity** — line 121 itself groups four-to-five personas under one shared
vocabulary line — so the fact that `deflated-Sharpe` is also Citadel vocabulary and
`purged-k-fold` also appears in `dimensional`'s review fixes is not a defect; the list
describes each archetype's native fix examples, it does not partition a term-space.
The archetype name "Overfit detection" is deliberately narrower than "Backtesting" so
it scopes to `renaissance`'s lens without implying it is the desk's only backtester
(see Out-of-Scope re `dimensional`).

### Item B — gs_compliance.yml:63 (optional)

Generalise the example string, investor-language-agnostic:

> `"block until PRIIPs KID confirmed EN/PT"` →
> `"block until PRIIPs KID confirmed in the investor's jurisdiction-required language(s)"`

`language(s)` is deliberate — PRIIPs KID language obligations are jurisdiction-dependent
and can require more than one language; the original "EN/PT" encoded exactly that
plurality, and the generalisation preserves it. Only the quoted example string changes;
the surrounding `review_prompt` sentence and the operative line 56 are untouched, and
`analytical_framework` / `gate_consumption` / `role` / `system_prompt` are byte-identical
(`.claude/review-patterns.md` Critical Pattern, line 59, satisfied — the PROPOSE
explicitly targets only the `review_prompt` example string).

Item B is optional and lowest-priority. If the user declines it, only Item A executes;
the DoD below is split so Item A can close independently.

## Scope & Out-of-Scope

**In scope:** the three AGENTS.md line edits (Item A) and the one `gs_compliance.yml`
example-string edit (Item B).

**Out of scope (deliberately deferred):**

- **`dimensional` grouping under "Quant signal".** The Challenger pass correctly noted
  `dimensional_factor_backtester.yml` is itself a *Factor Backtester* (role: Factor
  Investing Strategy Researcher; review fixes use "purged-k-fold" / "rolling Sharpe"),
  so its grouping under "Quant signal → IC / decay / capacity" is a loose fit. But
  `dimensional.yml` was *not changed by Proposals 017/018* — it carries no
  forbidden-phrases block and the line is not *actively contradictory* with it, only
  imperfectly descriptive. That pre-existing editorial imperfection is outside S-20's
  "actively contradictory after 017/018" mandate. **Flagged as a candidate follow-up
  roadmap item** (a future archetype-list completeness review) — not silently ignored,
  not fixed here.
- Any other archetype line (119, 122–128 — verified consistent with their personas);
  any change to the operative fields of `virtu_execution.yml`,
  `renaissance_backtesting.yml`, or `gs_compliance.yml`; the `~/.claude`
  governance-maintenance thread; the 2026-05 War Room rebalance; the MEMORY.md trim
  (handled via `/retro`, not `/propose`).

## Definition of Done

DoD criteria assert properties on the **specific edited line**, not file-global bare
strings (per the 2026-05-20 anti-pattern).

**Item A — mandatory:**

- **A1.** The Execution archetype line in `AGENTS.md` reads
  `- Execution → order-type / timing / commission-drag / fractional-share fixes`, and
  `grep -n "TWAP" AGENTS.md` returns nothing (pre-edit grep verified "TWAP" occurs
  exactly once, on line 120 — so a clean grep validly confirms line 120 was corrected).
- **A2.** The "Quant signal" archetype line no longer contains the token `renaissance`.
- **A3.** A new line `- Overfit detection (renaissance) → calibration-window /
  deflated-Sharpe / purged-k-fold / turnover-cost-ratio fixes` is present immediately
  after the "Quant signal" line.
- **A4.** `git diff AGENTS.md` is confined to the archetype-list region; no other
  AGENTS.md content changed.

**Item B — only if approved:**

- **B1.** `grep -n "EN/PT" agents/gs_compliance.yml` returns nothing (pre-edit grep
  verified "EN/PT" occurs exactly once, on line 63).
- **B2.** `gs_compliance.yml` `analytical_framework`, `gate_consumption`, `role`,
  `system_prompt` byte-identical vs HEAD; `git diff` confined to the line-63 example
  string.
- **B3.** `/code-reviewer` run on `gs_compliance.yml` (behaviour-shaping `review_prompt`).

**Close-out (both):**

- **C1.** PROGRESS.md S-20 row flipped to DONE; CHANGELOG.md entry appended; proposal
  Status Log closed. `/code-reviewer` is exempt for `AGENTS.md` under the prose
  carve-out; it applies to `gs_compliance.yml` (B3) only if Item B is approved.

## Risks & Mitigations

- **Bullet-count drift** — the split makes the contract list a 12th archetype bullet
  (it has 11 today; verified `AGENTS.md:118–128`). *Mitigation:* it is a prose list,
  additive; no count is asserted against it anywhere (downstream grep, below: no
  cascade).
- **Line-number renumbering** — inserting the new line after the "Quant signal" line
  shifts every subsequent archetype line down by one (old 122–128 → 123–129). All line
  numbers cited in this proposal are **pre-edit**. *Mitigation:* DoD criteria are
  content-anchored, not line-anchored, so they survive the renumber.
- **gs_compliance wording regression** — the new example string must remain a
  *language* reference, not a jurisdiction reference (the KID obligation is about the
  document's language availability). *Mitigation:* "jurisdiction-required language(s)"
  keeps the language semantics and the plurality of the original "EN/PT".

## Adversarial Loophole Pass (L1–L10)

L1–L10 raised by the Isolated Challenger (see Delta Annexe); closure mechanisms below.

- **L1 — Split-line vocabulary is not renaissance-exclusive.** Risk: §2 justified the
  split on `renaissance` occupying a vocabulary-distinct domain, but "deflated-Sharpe"
  and "purged-k-fold" also appear in `citadel`/`dimensional`. **Closed by** re-writing
  the §2 justification to *not* claim exclusivity — the archetype list is descriptive,
  not a term-space partition (line 121 already groups four personas under one shared
  line). The split rests on `renaissance`'s *forbidden* line, not on term-exclusivity.
- **L2 — `dimensional` is itself a backtester, also loosely grouped.** Risk: line 121
  stays imperfect after the fix. **Closed by** explicit Out-of-Scope entry — it is a
  pre-existing imperfection, not an 017/018 contradiction; flagged as a follow-up,
  not silently dropped.
- **L3 — new line implies a clean per-archetype partition `dimensional` breaks.**
  **Closed by** the L1 re-justification (list is descriptive) + the "Overfit detection"
  name chosen narrower than "Backtesting" so it does not claim to be the desk's only
  backtest archetype.
- **L4 — DoD bare-string grep asserts a standing uniqueness guarantee.** **Closed by**
  re-targeting DoD A1/B1 to content-anchored line assertions + citing the pre-edit
  uniqueness grep inline.
- **L5 — "required language" lost the EN+PT plurality.** **Closed by** "jurisdiction-
  required language(s)" — plural-tolerant.
- **L6 — Item B "optional" but DoD treated it as mandatory.** **Closed by** splitting
  the DoD into Item A (mandatory) / Item B (if approved) / close-out.
- **L7 — L-pass closure asserted a grep without showing it; under-scoped to one line.**
  **Closed by** the downstream-grep evidence recorded below, covering both edited lines.
- **L8 — Execution-line replacement vocab unverified against virtu Required vocab.**
  **Closed by** verifying line 120's terms against `virtu_execution.yml:95` Required
  vocabulary and the four levers (`system_prompt:67–72`) — cited in §Proposal.
- **L9 — line-number renumber after insertion not flagged.** **Closed by** the
  renumbering Risk entry + content-anchored DoD.
- **L10 — "venue"/"routing"/"child-order" deleted without per-term motivation.**
  **Closed by** the per-term motivation now in §Motivation line 120 (venue/routing =
  broker's delegated duty per `virtu_execution.yml:90`; child-order = institutional
  slicing the retail persona dropped).
- *v1-L1 (superseded) — "Renaissance split orphans a cross-reference", from the
  pre-Challenger draft; renumbered and broadened into L7 above. Retained as a marker
  per the living-artefact rule.*

**Downstream-artefact grep (L7 evidence):** `grep -rn` for `child-order` /
`domain-native fix example` / `TWAP` across `*.md` `*.yml` `*.py` returned only
AGENTS.md (the target), `virtu_execution.yml` (as a *forbidden phrase*, not a consumer),
and historical CHANGELOG/PROGRESS/`proposals/`/retro records — **no programmatic
consumer** of the archetype list. `grep -rn "EN/PT"` returned only `gs_compliance.yml:63`
(target) and historical retro/proposal records. No cascade for either item.

## Files Changed (Proposed)

- `MODIFY` `AGENTS.md` — Item A: 2 lines re-worded (Execution, Quant signal) + 1 line
  inserted (Overfit detection). The insertion renumbers the archetype lines below it.
- `MODIFY` `agents/gs_compliance.yml` — Item B (optional): 1 example-string edit on
  line 63; all operative fields byte-identical.

## Reversibility

Both changes **FULLY REVERSIBLE** — local file edits only; `git revert` restores all
state. No external state, no API calls, no data mutation.

## Core Team Review (A–D)

LIGHT tier — one-line verdicts (per `feedback_light_proposal_verdicts`).

- **A — Quant Architect:** APPROVE. Removes a live doc-vs-persona contradiction; the
  split correctly recognises `renaissance` as a distinct review lens post-017, and the
  re-justification no longer over-claims exclusivity.
- **B — Portfolio Manager:** APPROVE. Minimum scope; Item B explicitly severable;
  `dimensional` correctly flagged out-of-scope rather than scope-crept into S-20.
- **C — CTO:** APPROVE. No code path, no secrets, no pipeline surface; pure text.
- **D — Risk Officer:** APPROVE. Zero capital surface; fully reversible via `git revert`.

## Delta Annexe — Round 1 (Core Team)

- **Absorbed:** none — unanimous APPROVE, no conditions.
- **Resisted:** none.

## Delta Annexe — Round 2 (Isolated-Challenger Cross-Check)

`Cross-Check path: isolated-challenger — reason: user explicitly requested an
adversarial challenger pass on this proposal. Step 4b not formally triggered (LIGHT,
fully reversible); run as a user-requested pass.`

Challenger verdict: **flawed** (R1), L1–L10 raised, L1/L2/L3 tagged `structural`. Every
specific factual claim was verified against the YAMLs before absorption (per CLAUDE.md
"External-agent claim verification" / "FATAL-claim independent verification"):

- **L1 — absorbed.** Verified via Read `dimensional_factor_backtester.yml:62`
  ("require >24-month purged-k-fold OOS window", "block deployment if rolling Sharpe
  falls >50%") and `citadel_alpha.yml:23,63,77` ("deflated Sharpe"). The claim is true:
  the terms are not renaissance-exclusive. Absorbed by re-writing the §2 justification
  to rest on `renaissance`'s *forbidden* line, not on term-exclusivity; the split
  decision itself stands (re-wording the shared line strips Citadel's signature vocab).
- **L2 — absorbed as Out-of-Scope.** Verified via Read `dimensional_factor_backtester.yml:1–23`
  (name "…Factor Backtester", role "Factor Investing Strategy Researcher", capabilities
  "institutional-grade backtesting"). True — `dimensional` is a backtester. But
  `dimensional.yml` was unchanged by 017/018 and carries no forbidden block, so its
  loose grouping is a pre-existing imperfection, not an S-20 active contradiction.
  Recorded as an explicit Out-of-Scope follow-up rather than scope-crept.
- **L3 — absorbed.** Verified via Grep `Required vocabulary|Forbidden phrases` in
  `dimensional_factor_backtester.yml` → 0 matches (no vocab-discipline block). Absorbed
  into the L1 re-justification + the narrower "Overfit detection" archetype name.
- **L4 — absorbed.** DoD A1/B1 re-targeted to content-anchored line assertions; the
  pre-edit uniqueness grep is cited inline. (Also independently raised by the user.)
- **L5 — absorbed.** Replacement string now "jurisdiction-required language(s)".
- **L6 — absorbed.** DoD split into Item A (mandatory) / Item B (if approved).
- **L7 — absorbed.** Downstream-grep evidence recorded in the L-pass section.
- **L8 — absorbed.** Line 120 terms verified against `virtu_execution.yml:95` + levers.
- **L9 — absorbed.** Renumbering Risk entry added; DoD content-anchored.
- **L10 — absorbed.** Per-term motivation added to §Motivation line 120.
- **Resisted:** none. The split decision was *defended* (not changed) against the
  structural L1/L2/L3 — re-wording line 121 would degrade four personas to fix one — but
  every L-item's substance was absorbed.

Structural L-items (L1/L2/L3) were absorbed without restructuring the FILES CHANGED list
or the DECOMPOSE — they targeted justification wording and a missed sibling observation,
both addressable in place. Per the iteration discipline, R1-flawed with structural items
is presented to the user for ship-vs-defer arbitration with the amended draft attached.

## Status Log

> Pre-approval amendments are recorded here and in Delta Annexe R2 — no separate
> `## Amendments` section (that section is reserved for post-approval deviations).

- 2026-05-22 — DRAFT opened.
- 2026-05-22 — DRAFT amended pre-approval: 3 user amendments (DoD re-targeted off bare
  greps; Risk count corrected to 12th-bullet; L-pass extended L1→L10) + 10 absorbed
  Challenger L-items (R1 verdict `flawed`, structural L1/L2/L3 absorbed in place — §2
  justification re-written to drop the exclusivity claim, new line renamed "Overfit
  detection", Item B string changed to "language(s)", `dimensional` recorded
  Out-of-Scope). Per-item detail in Delta Annexe R2.
- 2026-05-22 — APPROVED by user (v2, in substance) + 2 pre-commit tidies (Amendments
  section folded into this log; v1-L1 superseded-marker added to the L-pass).
- 2026-05-22 — DONE. Item A (`AGENTS.md` lines 120–121) and Item B
  (`gs_compliance.yml:63`) implemented via the Sonnet implementation-agent; the
  orchestrator verified the diff against the approved FILES CHANGED list. DoD A1–A4 +
  B1–B3 all verified — "TWAP"/"EN/PT" greps clean; the "Quant signal" line is
  renaissance-free with the new "Overfit detection" line immediately after it;
  `gs_compliance.yml` operative fields byte-identical; `yaml.safe_load` parses.
  `/code-reviewer` APPROVE on `gs_compliance.yml`; `AGENTS.md` prose-exempt under the
  carve-out. PROGRESS.md S-20 → DONE and the CHANGELOG.md `[Unreleased]` entry are
  appended in this same close-out commit.
