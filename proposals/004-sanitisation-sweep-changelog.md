---
id: 004
title: Sanitisation Sweep & CHANGELOG Introduction
status: DONE
owner: Daniel
opened: 2026-04-26
updated: 2026-04-26
tags: [docs, governance, changelog, sanitisation]
---

# 004 — Sanitisation Sweep & CHANGELOG Introduction

**Tier: HEAVY** — touches the majority of public-facing markdown (`AGENTS.md`, `CLAUDE.md`, `PROGRESS.md`, `docs/*.md`, `agents/*.yml`, `brainstorms/_TEMPLATE.md`, `.claude/commands/war-room/SKILL.md`, plus minor scripts), introduces a new top-level governance artefact (`CHANGELOG.md`), and migrates the framework's audit-trail centre of gravity. Mandates dual-model cross-check + Delta Annexe + ranked adversarial loophole list per global Intelligence Document Governance.

## Summary

The framework has accumulated version-stamped prose ("War Room v2.0", "since Session #2", "introduced in Phase 1B", "v1.1 era") inside files that a cold reader — a fork recipient, a future agent, or the user after `/clear` — encounters without any project-internal timeline. These markers turn framework prose into a partial palimpsest: load-bearing rules are correct, but the language assumes you remember an evolution you may never have witnessed. This proposal does two things, atomically:

1. **Sanitisation sweep**: strip version-stamped language from public-facing files (everything outside `local/` that ships to GitHub) and rephrase the underlying rules in cold-reader-friendly form.
2. **CHANGELOG introduction**: add `CHANGELOG.md` at project root as the canonical, append-only versioning record. Backfill from existing material (PROGRESS.md §Session Log + the three closed proposals) and migrate the Session Log section out of `PROGRESS.md`. Going forward, every material framework change closes by appending a CHANGELOG entry — the same way every proposal closes by updating its Status Log.

## Motivation / Problem

- **Cold-reader failure.** A new agent reading `brainstorms/_TEMPLATE.md` line 26 sees `Process version: v2.0` with no v1.0 anywhere in the repo. A reader of `backtesting/POST_MORTEM_BRIEF.md` is told about "the v1.0 era (BT-01 through BT-05)" without that era being defined. Documentation that is incomprehensible to a cold reader is undocumented.
- **History lives in two places.** Framework changes are currently logged in `PROGRESS.md §Session Log` *and* implied in proposal Status Logs *and* embedded as sentinel phrases in prose ("v2.0", "Session #2"). Three sources of truth means none of them is authoritative. Forks, retros, and audits all need one.
- **Sanitisation pressure compounds.** Each new proposal adds another version marker. Proposal 003 alone added "Phase 1B" tags to `gate_eval.py`, `gates.yml`, `_TEMPLATE.md`, two agent YAMLs, and `RISK_FRAMEWORK.md`. Without an explicit sanitisation discipline, the noise floor only ever rises.
- **No external-versioning convention.** The project has no `CHANGELOG`, no `VERSION`, no semver tag scheme. Closing this gap once — properly — is cheaper than improvising it under pressure later (e.g. when sharing the framework via SHARING.md).

## Scoping Decisions

> Four scoping questions, answered explicitly before file-level work, per user's brief. Answers govern the manifest below.

### (a) Exact files in scope

**In scope (sanitisation pass + version-marker removal)**
```
AGENTS.md
CLAUDE.md
PROGRESS.md                                  # also: §Session Log section migrated out → CHANGELOG.md
USER_INSTRUCTIONS.md
SHARING.md
docs/RISK_FRAMEWORK.md
docs/STRATEGY_LOGIC.md
docs/DATA_STANDARDS.md
docs/COMPLIANCE.md
agents/*.yml                                 # all 17 YAMLs (15 personas + macro_strategist + risk_guardian extensions)
brainstorms/_TEMPLATE.md                     # explicitly: drop "Process version: v2.0" line; rephrase any v1.0 contrasts
.claude/commands/war-room/SKILL.md
.claude/review-patterns.md
proposals/README.md                          # one-line "Convention" prose only; the index table itself is canonical
proposals/_TEMPLATE.md
```

**In scope (CHANGELOG creation + cross-link)**
```
CHANGELOG.md                                 # NEW — root-level, append-only
PROGRESS.md                                  # Session Log section deleted; replaced with one-line pointer to CHANGELOG.md
proposals/README.md                          # add a one-line note that proposal closes append a CHANGELOG entry
.claude/commands/war-room/SKILL.md           # Session Close Checklist gains "append CHANGELOG entry if framework changed"
```

**Out of scope (deliberate)**
```
local/**                                     # personal — never shipped to GitHub
docs/retros/**                               # dated historical artefacts; rewriting violates append-only audit principle
local/retros/**                              # personal artefacts
proposals/001-*.md, 002-*.md, 003-*.md       # closed proposals are immutable historical record (Status Log is append-only)
backtesting/*.md (PORTFOLIO_HISTORY, POST_MORTEM_BRIEF, REPLAY_DELTA)   # describe a specific historical run; "v2.0" is part of what they are dating, not pollution
backtesting/archive/**                       # immutable archive
docs/BACKTEST_REPORT.html, docs/PROJECT_OVERVIEW.html                    # generated artefacts of a specific run; regenerate next backtest cycle
local/snapshots/**                           # data fixtures — version stamps are payload, not prose
local/dashboard.html                         # generated artefact
tests/**                                     # code; provenance comments tracing to a proposal are acceptable
scripts/**                                   # code; per-file provenance docstrings (e.g. gate_eval.py "Proposal 003, Phase 1B") are acceptable as code-adjacent traceability and would lose meaning without their anchors. CHANGELOG entry covers them at framework level.
config/gates.yml                             # comment block traces governance lock to Proposal 001/1A — load-bearing for the SHA-lock recipe; CHANGELOG covers the timeline at framework level
```

**Decision-rule rationale for the out-of-scope split**: dated historical artefacts (retros, closed proposals, backtest reports) are *what they are because of when they were written*; the version stamp is payload, not prose. Code provenance docstrings are read by people debugging the code and need to anchor in the proposal that introduced them. User-facing markdown that explains *what the system is* is the only category where version markers fail the cold-reader test.

### (b) "Version mention" vs "historical context note"

> A decision rule, not a checklist of examples.

Three categories, not two. The third (citation) is the Round 2 fix to the Breadcrumb Fallacy (L14): proposal anchors carry the *why*, and deleting them orphans the rule.

- **Version mention — STRIP** — language whose meaning depends on the reader knowing the project's internal evolution. The marker labels a *moment* and the rule reads as a contrast against an unstated prior state. Tells:
  - explicit version literal (`v1.0`, `v2.0`, `v1.1 era`, `Process version: v2.0`)
  - sequential session anchor (`Session #2`, `since Session #N`, `as of session N`)
  - phase identifier in user-facing prose (`Phase 1B`, `introduced in Phase 1A`)
  - relative-temporal cue without absolute date (`previously`, `formerly`, `new in`, `as of recently`)
  - The rule's force depends on the reader recognising a transition. Strip the marker and the rule still reads correctly cold.

- **Architectural citation — CONVERT (do not delete)** — a proposal anchor (`Proposal 003`, `per Proposal 001`) is the *only* breadcrumb a cold reader has to the rule's rationale. Deleting orphans the rule. Convert in place to a markdown link:
  - `"introduced in Proposal 003"` → `"See [Proposal 003](proposals/003-phase-1b-data-integration.md) for structural rationale."`
  - `"per Proposal 001 (Phase 1A)"` → `"See [Proposal 001](proposals/001-data-layer-upgrade.md)."` (drop the Phase tag — that's a version mention.)
  - The rule must still stand on its own to a cold reader; the link is the *why*, not the *what*.
  - This applies in user-facing markdown only. Code provenance docstrings (`# Canonical consumer of config/gates.yml (Proposal 003, Phase 1B).`) remain unchanged — they are read by debuggers, not cold readers, and trace back to the proposal directly.

- **Historical context note — KEEP** — a factual statement that stands on its own to a cold reader, with an absolute anchor (a date, a regulation citation, a market condition). Tells:
  - dated regulatory or market-data fact (`as of 2026, German FTT: none`)
  - permanent rule with an external anchor (`MiFID II Article 17 algo trading requirements`)

- **Decision rule (the contract)**: for each candidate marker — (1) is it a *proposal anchor*? Convert to a markdown citation, do not delete. (2) Otherwise, would removing it leave the rule equally clear to a cold reader? Strip and let CHANGELOG carry the timeline. (3) If removal makes the rule incomprehensible *without* internal project history, keep the marker and rephrase the surrounding prose so it is explained on first use. When in doubt between strip and keep, strip — the lint rule (DoD #5) makes resurrection visible.

This is the rule the executor applies per-line; it is not a regex. The grep pass in DoD #4 produces *candidates*, not *answers*.

### (c) CHANGELOG entry format & relationship to PROGRESS.md §Session Log

**Format** — Keep-a-Changelog style, append-only, reverse chronological:

```markdown
# CHANGELOG

All notable framework changes are recorded here. Personal session outcomes
(NAV, P&L, holdings) live in `local/SESSIONS.md`.

## [Unreleased]

## [2026-04-26]
### Added
- `gate_eval` evaluator (Proposal 003) — snapshot → GREEN/AMBER/RED tier with deterministic recipe.
- `tests/test_skill_invariants.py` — invariants on agent gate-consumption declarations.
### Changed
- `agents/macro_strategist.yml`, `agents/risk_guardian.yml` consume the gate table; recall paths removed.
### Process
- Phase 1B closed; rollback gate retracted pending live smoke 2026-05-16.

## [2026-04-25]
### Added
- `local/` segregation; `scripts/init_workspace.py`; `SHARING.md`; `skill-config.yaml` (Proposal 002).
...
```

- **Granularity**: one section per *date of event* (not date of entry); subsections by category (`Added`, `Changed`, `Removed`, `Fixed`, `Process`, `Decisions`). Each bullet is one line; longer narrative lives in the originating proposal.
- **Authority**: CHANGELOG.md is the **canonical** framework-change record from this proposal forward.
- **Relationship**: CHANGELOG **supersedes** *both* `PROGRESS.md §Session Log` *and* `PROGRESS.md §Architecture Decisions Log`. Round 2 (Gemini, R-A1) closed the double-bookkeeping loophole: two historical event logs in two files would diverge on first contact. Both are migrated into CHANGELOG and *deleted* from PROGRESS.md (each replaced with a one-line pointer). The ADL's persona attribution is preserved by writing each migrated row under a `### Decisions` subsection per dated section, with the persona name in the bullet (`- (D, Risk Officer) tiered cash floor 30% → 15% Standard — ...`).
- **What stays in PROGRESS.md**: Current State, In Progress, Next Up, Backlog, Open Process-Bias Items, Staged Improvements, Known Issues. Forward-looking only. PROGRESS.md is **not** a log of any kind going forward.
- **Append rule**: any proposal close, any framework rule change, any new architectural decision, any new file added to a public path, MUST append a CHANGELOG entry under `[Unreleased]` (or a new dated section). Architectural decisions go under `### Decisions` with persona attribution. Entry-or-it-didn't-happen.

### (d) `docs/retros/` — out of scope

Retros are dated historical session artefacts. They record what was thought *at that moment*, including the language used at the time. Rewriting them post-hoc to remove "Phase 1B" or "v2.0" violates the same append-only audit principle that governs proposal Status Logs (memory anti-pattern: 2026-04-25 — *"the Status Log is append-only"*). The cold-reader test does not apply to dated retros — the date itself is the context.

`local/retros/` is also out of scope (personal, gitignored).

## Proposal

### File manifest

**New files (framework-shared, committed)**
```
CHANGELOG.md                                 # root-level; append-only; backfilled from PROGRESS.md §Session Log + 001/002/003
```

**Modified files (sanitisation pass — markers stripped/converted/kept per three-way rule (b))**
```
AGENTS.md
CLAUDE.md
PROGRESS.md                                  # §Session Log AND §Architecture Decisions Log sections deleted; replaced with pointers to CHANGELOG.md (R-A1)
USER_INSTRUCTIONS.md
SHARING.md
docs/RISK_FRAMEWORK.md
docs/STRATEGY_LOGIC.md
docs/DATA_STANDARDS.md
docs/COMPLIANCE.md
agents/*.yml                                 # all 17
brainstorms/_TEMPLATE.md                     # drop "Process version: v2.0"; rephrase v1.0 contrasts
.claude/commands/war-room/SKILL.md           # add CHANGELOG-entry step to Session Close Checklist with explicit trigger; sanitise prose
.claude/review-patterns.md                   # add SEMANTIC lint instruction (R-L15): flag framework-internal version markers; ignore external dependency versions. Single-source for the pattern set.
proposals/README.md                          # add: "Closing a proposal appends a CHANGELOG.md entry."
proposals/_TEMPLATE.md                       # add Status Log convention: closing entry pairs with CHANGELOG line
```

**Deleted (section-level)** — `PROGRESS.md §Session Log`; `PROGRESS.md §Architecture Decisions Log`. Both migrate into CHANGELOG.md.

### Sequence of execution

0. **Pre-grep candidate scan** (B2). Run the DoD #4 regex set across the candidate manifest. Files with zero hits are recorded in Status Log as "scanned, no edits needed" — not gratuitously touched. Files with hits become the actual edit set.
1. Draft `CHANGELOG.md` with backfilled history (sources per §Backfill source mapping: PROGRESS.md §Session Log; PROGRESS.md §Architecture Decisions Log; closed proposals 001/002/003 Status Logs).
2. Migrate `PROGRESS.md §Session Log` → CHANGELOG; replace section with pointer.
3. Migrate `PROGRESS.md §Architecture Decisions Log` → CHANGELOG (under per-date `### Decisions` subsections, persona attribution preserved); replace section with pointer (R-A1).
4. Sanitisation sweep on the actual edit set from step 0, applying three-way decision rule (b) per-instance: strip / convert-to-citation / keep. Use `Python text.replace()` for batch literal replacements (memory: macOS sed fails on special chars).
5. Update `.claude/review-patterns.md` with the **semantic** lint instruction (R-L15) — single-source for the pattern set.
6. Update `.claude/commands/war-room/SKILL.md` Session Close Checklist with the explicit trigger (C2): "if any file outside `local/` changed in this session, append a CHANGELOG entry."
7. Run DoD #4 grep zero-unjustified-matches assertion across the actual edit set.
8. Run DoD #11 synthetic lint test: manufacture a fake diff containing `Phase 2A` in `AGENTS.md`, run `/code-reviewer`, verify the lint rule fires.
9. Run DoD #10 sub-agent cold-reader smoke (EM-1): spawn a Sonnet sub-agent with the in-scope file list (no `local/` access), ask it to summarise three rules at random offsets. Capture verbatim Q&A in Status Log.
10. Append the closing CHANGELOG entry for Proposal 004 itself (self-referential — entry-or-it-didn't-happen).
11. `proposals/README.md` index updated; convention text mentions the CHANGELOG-append rule.

### Backfill source mapping (CHANGELOG bootstrap)

| CHANGELOG date | Source | Subsection | Notes |
|---|---|---|---|
| 2026-03-01 | PROGRESS.md §ADL rows dated 2026-03-01 (×9 rows) | `### Decisions` | governance bootstrap; persona attribution preserved (A, B, C, D) |
| 2026-03 | PROGRESS.md §Session Log "Foundation Session" | `### Process` | framework events |
| 2026-03-28 | PROGRESS.md §ADL rows dated 2026-03-28 (×5 rows) | `### Decisions` | Strike Team standardisation |
| 2026-04 (early) | PROGRESS.md §Session Log "Portability & Critical Review" | `### Process` | onboarding precursor |
| 2026-04-05 | PROGRESS.md §ADL rows dated 2026-04-05 (×6 rows) | `### Decisions` | tiered cash floor, AMBER gates, Thesis Validation Protocol |
| 2026-04-06 | PROGRESS.md §ADL rows dated 2026-04-06 (×4 rows) | `### Decisions` | ETF-only universe, structured outputs, tiered read order, Hypothesis Log |
| 2026-04-19 | PROGRESS.md §ADL row dated 2026-04-19 | `### Decisions` | Session Go/No-Go Check |
| 2026-04-23 | Proposal 001 Status Log (DONE) | `### Added` / `### Process` | data layer |
| 2026-04-25 | Proposal 002 Status Log (DONE) | `### Added` / `### Changed` | `local/` segregation |
| 2026-04-25 | PROGRESS.md §Session Log "Proposal 002 Execution" | `### Changed` | structural segregation events |
| 2026-04-26 | Proposal 003 Status Log (DONE) | `### Added` / `### Changed` / `### Process` | gate evaluator integration |
| 2026-04-26 | Proposal 004 closing entry (self-referential) | `### Process` / `### Changed` | this proposal — DoD #8 |

**Migration rules**:
- 1:1 sourcing — no synthesis or paraphrase (L4 closure).
- ADL rows preserve persona attribution: `- (A, Quant Architect) <decision> — <rationale>`.
- Multiple events on the same date may share a section; sub-categorise by `### Added` / `### Changed` / `### Removed` / `### Fixed` / `### Process` / `### Decisions`.
- Backfill is read-only against sources; sources are not modified until the migration step (3) deletes the migrated section.

## Scope & Out-of-Scope

**In scope** — see §Scoping Decisions (a). Sanitisation of public framework prose; CHANGELOG creation and bootstrap; lint rule; SKILL.md Session Close hook.

**Out-of-scope (deliberate)**
- `docs/retros/`, closed proposals, backtest reports, generated HTML, code provenance docstrings, snapshots, fixtures, tests — see §Scoping Decisions (a).
- **Semver introduction.** No `0.x.x` tagging, no `VERSION` file. Date-keyed CHANGELOG only. Semver is a future proposal once the framework has external consumers.
- **Git-tag automation.** No release-tagging workflow. Manual append by the executor of each proposal.
- **Re-running closed proposals through the new lint rule.** Closed proposals are immutable.

> Note: PROGRESS.md §Architecture Decisions Log migration was originally listed out-of-scope; Round 2 (R-A1) reversed that — ADL is now in scope, migrated into CHANGELOG.

## Definition of Done

> Binary, testable. No ambiguous "works well" items. Reflects all eleven absorbed amendments (Round 1 + Round 2).

1. `CHANGELOG.md` exists at repo root, populated with dated entries covering 2026-03-01 → 2026-04-26, sourced 1:1 per §Backfill source mapping. Includes per-date `### Decisions` subsections for migrated ADL rows with persona attribution preserved verbatim.

2. `PROGRESS.md §Session Log` section deleted; replaced with: `> Framework change history lives in [CHANGELOG.md](CHANGELOG.md). This file is forward-looking only.`

3. **(R-A1)** `PROGRESS.md §Architecture Decisions Log` section deleted; replaced with: `> Architectural decisions (with persona attribution) are recorded in [CHANGELOG.md](CHANGELOG.md) under per-date Decisions subsections.` Pre-deletion `git diff` of the ADL section reviewed against the CHANGELOG migration to confirm 1:1 row coverage.

4. **Grep candidate scan** across the actual edit set (per Sequence step 0), regex set:
   - `\bv[12]\.\d\b` (anchored on `v` prefix; decimals like `2.0%` excluded)
   - `\bSession #\d+\b`
   - `\bPhase 1[AB]\b`
   - `\bProposal \d{3}\b`
   - `\bsince Session\b`, `\bintroduced in\b`, `\bv\d era\b`

   Result: every match is *resolved* per three-way rule (b) — **STRIPPED**, **CONVERTED** to a markdown architectural citation (`Proposal NNN` matches), or **KEPT** with one-line justification appended to Status Log. Gate is "zero unresolved matches", not "zero matches" (L2 closure).

5. **(R-L15)** `.claude/review-patterns.md` contains a **semantic lint instruction** (not a literal regex) under a `## Sanitisation Lint` anchor:

   > *"Flag any version markers (e.g. `v2.0`, `Phase 1B`, `Session #N`, `Proposal NNN`) in user-facing markdown that refer to the framework's internal methodology. Convert proposal anchors to markdown citations linking to the proposal file. Ignore external dependency versions (`pandas v2.1`, `API v2.0`), library version strings, and code provenance docstrings."*

   The proposal's grep regex set (DoD #4) is referenced from this anchor — single-source per A2.

6. `brainstorms/_TEMPLATE.md` `Process version: v2.0` line removed; the Session Metadata block now references session-cadence (e.g. monthly third Saturday) instead of an internal version stamp.

7. **(C2)** `.claude/commands/war-room/SKILL.md` Session Close Checklist contains a step with explicit trigger: *"If any file outside `local/` changed in this session, append a CHANGELOG.md entry under `[Unreleased]` (or a new dated section). Architectural decisions go under `### Decisions` with persona attribution. Trigger condition: file path does not begin with `local/`."*

8. Self-referential closing entry: `CHANGELOG.md` 2026-04-26-or-later dated section contains a line referencing Proposal 004 itself (DoD #8 verifiable post-hoc; Status Log append-only ensures the DONE row is never silently amended — L5 closure).

9. `proposals/README.md` index has row 004; convention text mentions the CHANGELOG-append rule on close.

10. **(EM-1, B1)** Cold-reader smoke test executed via **sub-agent orchestration**:
    - Spawn a Sonnet sub-agent (general-purpose) with read access denied to `local/**`. Prompt: *"Here is the in-scope file list: [list]. I will name three rules at random offsets — summarise each, and flag anything you cannot understand without external context."*
    - Three rules selected by random offset (executor records the offsets in Status Log before the sub-agent runs — no cherry-pick).
    - Sub-agent's verbatim Q&A appended to Status Log.
    - **Gate is "executed and findings recorded"**, not "passed clean". Findings flagged as *"missing context"* are routed to PROGRESS.md Open Process-Bias Items as a follow-up; they do not back-pressure this proposal's close.

11. **(C1)** Synthetic lint test: manufacture a fake one-line diff inserting `Phase 2A` into `AGENTS.md`. Run `/code-reviewer` on the diff. Verify the lint rule fires (output references the Sanitisation Lint anchor). Capture verbatim in Status Log. If the rule does *not* fire, `.claude/review-patterns.md` is rewritten and the test repeated before close.

12. **(D1 — fourth-source tripwire)** During execution, if the executor identifies a fourth source of framework history (anything that is neither Session Log, Status Logs, nor ADL — e.g. a hidden `HISTORY.md`, a wiki page, a long prose section in some doc that *de facto* logs changes), execution **pauses** and the proposal is amended before resuming. Fourth-source means foundational scope was missed; sweeping forward locks in incoherence.

## Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Sweep removes a load-bearing context cue (sentence becomes ambiguous after marker removed) | Per-instance review under decision rule (b); not a blind regex replace. Cold-reader smoke (DoD #10) catches residual ambiguity. |
| CHANGELOG drift — entries written but not maintained | Two enforcement points: SKILL.md Session Close step (DoD #7); proposal-close convention in proposals/README (DoD #9). Lint rule (DoD #5) flags new version markers in PRs, surfacing un-logged changes. |
| Double bookkeeping — Session Log not actually deleted, two records emerge | DoD #2 is binary deletion. Self-check on close: PROGRESS.md does not contain the string "Session Log" as a section heading. |
| CHANGELOG date-of-event vs date-of-entry confusion | Format spec mandates date-of-event in section headings. Backfill mapping table fixes this for migration. |
| Proposal 004 itself missed in CHANGELOG (silent self-exemption) | DoD #8 — self-referential entry mandatory before status flips DONE. |
| Future proposals add "v3.0", "Phase 2A" markers, eroding the discipline | Lint rule in `.claude/review-patterns.md` (DoD #5). Code reviewer flags on every diff to in-scope paths. |
| Tests reference proposal IDs, sanitisation breaks them | Tests are out-of-scope. The grep regex set targets prose patterns ("Phase 1B" with capital P) that are unlikely to appear identically in test names without context, but DoD #4 manual review catches collisions. |
| Closed proposals reference "v2.0" in Delta Annexes — out-of-scope but creates apparent inconsistency | Closed proposals are immutable. The CHANGELOG is the cold-reader index. README of `proposals/` already explains immutability. |
| Backtesting docs reference "v1.0 era" / "v2.0" — visible to readers, not sanitised | Backtesting docs are dated artefacts (out-of-scope, §a). Add one explanatory paragraph to `backtesting/README.md` (if it exists; create if not — but verify scope before adding) — **deferred**, this is out of scope for 004. Logged here for future. |
| Concurrent in-flight work conflicts with sweep | No in-flight proposals (PROGRESS.md "Nothing currently in progress"). Live smoke 2026-05-16 unaffected — does not touch any in-scope file. |
| **Fourth source of framework history discovered mid-execution** (D1 tripwire) | DoD #12: pause execution, amend the proposal to bring the fourth source into scope (or document its deliberate exclusion), then resume. Sweeping forward without acknowledging it locks in incoherence — the very failure this proposal exists to fix. |
| ADL persona attribution lost in migration | Backfill rule: rows formatted as `- (X, Persona Name) <decision> — <rationale>`. DoD #3 final clause: pre-deletion `git diff` reviewed against the CHANGELOG entry to confirm 1:1 row coverage. |
| Lint rule fires but `/code-reviewer` ignores `review-patterns.md` import | DoD #11 synthetic lint test is the live check. If it fails, the import wiring is repaired before close — closes the CTO's "decorative import" concern at the gate, not by trust. |
| Proposal anchor converted to a broken markdown link (404 on click) | Three closed proposals exist; their filenames are stable. Link target verified by `ls proposals/` before sweep; any conversion uses the actual filename. |

## Adversarial Loophole Pass (L1–L15 + EM-1)

> Ranked L1–Ln per global Intelligence Document Governance. Items dropped/superseded marked inline.

- **L1 — Marker removal breaks a rule.** Stripping "Phase 1B" from `agents/macro_strategist.yml` may delete the only signal that gate consumption is the *new* behaviour, leaving a future agent to wonder why the prompt says "consume the table" without any history of why. **Closed by** decision rule (b): if the marker is load-bearing, *keep it and rephrase context around it*; if not, strip. Per-instance, not regex. DoD #4 allows annotated exceptions.

- **L2 — Grep zero-match incentivises censorship over clarity.** A literal "0 matches" target tempts the executor to delete legitimate context to pass the gate. **Closed by** DoD #4 explicit escape clause: matches *may persist* if annotated as kept context with justification in Status Log. The gate is "zero unjustified matches", not "zero matches".

- **L3 — CHANGELOG drift after one cycle.** The first proposal post-004 may forget to append. **Closed by** lint rule (DoD #5) flags un-CHANGELOG'd version markers; SKILL.md Session Close step (DoD #7); proposals/README convention line (DoD #9). Three independent enforcement points; one failure tolerated.

- **L4 — Backfill is creative writing.** Migrating PROGRESS.md §Session Log to CHANGELOG invites paraphrase, which mutates the historical record. **Closed by** Backfill source mapping (proposal §Backfill source mapping): each entry sourced 1:1; no synthesis. Sources cited.

- **L5 — Self-referential entry depends on Status Log update.** DoD #8 (Proposal 004 entry in CHANGELOG) is checked *before* DONE — but if the executor flips DONE first and forgets the entry, the gate is skipped. **Closed by** DoD #8 wording: *"contains a line referencing Proposal 004 itself"* — verifiable post-hoc. Status Log append-only rule (memory anti-pattern 2026-04-25) ensures the DONE entry is never silently amended.

- **L6 — Cold-reader smoke (DoD #10) is unfalsifiable.** "Asks to summarise three rules" — which rules? Easy to cherry-pick. **Closed by** Status Log capture verbatim (DoD #10 final clause): rules selected by random offset into in-scope file list, prompt and output captured verbatim. One iteration.

- **L7 — Stale value persistence.** Per memory anti-pattern (2026-04-25, proposals/): after correcting one section, stale values persist elsewhere. Sweep is broad — high risk surface. **Closed by** DoD #4 grep is the global check; runs after all per-file edits, before close. Single source of truth for "did the sweep cover everything".

- **L8 — Decision rule (b) is subjective in the executor.** Two reasonable people will disagree on "is this load-bearing?". **Closed by** the contract clause in (b): *"if removing it makes the rule equally clear to a cold reader, strip it"* — this is the falsification test. When in doubt, strip; the lint rule makes resurrection visible.

- **L9 — Out-of-scope expansion.** Executor sees `backtesting/POST_MORTEM_BRIEF.md` "v1.0 era" and feels compelled to fix it. Scope creep. **Closed by** §Scope & Out-of-Scope explicit list; backtesting docs explicitly deferred. Risk Mitigation row covers the surface tension.

- **L10 — Generated HTML reports drift.** `docs/BACKTEST_REPORT.html` is regenerated next backtest cycle and reintroduces "War Room v2.0". **Closed by** out-of-scope by design (artefact of a specific run). Not a leak; a feature. Lint rule does not apply to generated `.html`.

- **L11 — PROGRESS.md Architecture Decisions Log contains version markers.** **SUPERSEDED Round 2 by R-A1.** Original framing: rows are event records, keep intact. Round 2 rejected this — ADL is a parallel historical event log to CHANGELOG, and double bookkeeping is the failure state. **Closed by** R-A1: ADL migrates *into* CHANGELOG (not preserved verbatim in PROGRESS.md); persona attribution retained via per-bullet labelling.

- **L12 — Lint rule false-positives stall future PRs.** **SUPERSEDED Round 2 by R-L15 (L15).** Original closure relied on regex anchoring (`\bv[12]\.\d\b`); but a regex still mis-fires on legitimate external dependency versions. Round 2 reframes the lint as a *semantic instruction* the LLM reviewer interprets — distinguishing framework-internal from external. The DoD #4 grep retains its regex form (it is the executor's mechanical scan, not the gating reviewer); the lint contract is semantic.

- **L13 — Memory references this proposal as "next" — momentum bias.** `project_engine_status.md` says "Proposal 004 next". Risk: rubber-stamp because the queue has it. **Closed by** Core Team review process. The momentum is acknowledged here but does not substitute for adversarial review.

- **L14 — Breadcrumb Fallacy.** (Added Round 2, Gemini.) Stripping proposal anchors orphans rules from rationale. **Closed by** three-way decision rule (b): proposal anchors are converted to markdown architectural citations, never deleted. The rule still stands cold; the link to the *why* is one click away.

- **L15 — Syntactic Lint Trap.** (Added Round 2, Gemini.) A literal regex blocks legitimate external dependency version mentions ("API v2.0"). **Closed by** R-L15: lint expressed as a semantic instruction the LLM reviewer interprets. Regex form retained only for the mechanical executor scan (DoD #4), not the reviewer gate.

- **EM-1 — Un-Executable Smoke Test.** (Added Round 2, Gemini.) The executing agent cannot `/clear` itself mid-execution. **Closed by** DoD #10 reworded: smoke test is performed by spawning a sub-agent (Sonnet, no `local/` access). Orchestrator never relinquishes context.

## Core Team Review (A–D)

> Verbatim outputs from the four core personas. They engaged with the plan as stakeholders, not checklist-fillers.

### Quant Architect — A (clean abstractions, signal pipeline, code quality)

This is mostly a prose-and-process change with a small code surface (`.claude/review-patterns.md` lint rule, SKILL.md hook). The architectural call I want to challenge is the *boundary* between CHANGELOG and PROGRESS.md §Architecture Decisions Log. Right now you've kept both. The risk is that "decision row added to ADL" and "CHANGELOG `Process` entry" diverge — same event, two records, different wording. Recommend: every ADL row append also appends a CHANGELOG `Process` line referencing the ADL row by date. Single canonical event, two views (one persona-attributed, one chronological). That keeps the audit trail coherent.

Second observation: the regex set in DoD #4 is duplicated in `.claude/review-patterns.md` (DoD #5). Don't duplicate — define the patterns once in `review-patterns.md` and have the proposal reference them by anchor (`See `.claude/review-patterns.md` §sanitisation-lint`). Otherwise the two will drift the moment a future proposal adds a marker pattern.

Status: **APPROVE with two amendments** (ADL/CHANGELOG cross-link; lint pattern single-source).

### Portfolio Manager — B (capital efficiency, scope discipline, P&L)

What is the cost? Roughly two hours of executor time on sweep + backfill + smoke, marginal context tokens. What is the payoff? A framework that reads cleanly to a fork recipient and a CHANGELOG that consolidates three sources of truth into one. Defensible.

Pushback: the cold-reader smoke test (DoD #10) is one iteration. That's thin. If the smoke fails, what happens — re-do the sweep? Recommend: smoke is mandatory, but the gate is "smoke executed and findings recorded", not "smoke passed cleanly". A dirty smoke produces a follow-up issue (logged to PROGRESS.md Open Process-Bias Items), not a re-execution. Otherwise we're back-pressuring this proposal with an unbounded loop.

Second pushback: scope discipline. Are we sure `docs/COMPLIANCE.md` actually has any version-stamped language? If the file is already clean, listing it in the manifest creates noise. Recommend: pre-execution grep produces the *actual* hit list; in-scope files with zero hits are recorded in Status Log as "scanned, no edits needed" rather than gratuitously touched.

Status: **APPROVE with two amendments** (smoke gate is "executed", not "passed clean"; manifest is candidate set, actual edits driven by pre-grep).

### CTO — C (infra, secrets, pipeline reliability)

Lint rule in `.claude/review-patterns.md` is what I care about. Verify it's actually loaded by `/code-reviewer` — the import line is in CLAUDE.md (`@ import .claude/review-patterns.md`), but does `/code-reviewer` actually parse and apply patterns from it? If the import is decorative, the lint rule is decorative. Recommend: DoD addition — *"a manufactured PR diff containing a fresh `Phase 2A` marker in `AGENTS.md` triggers the lint rule when `/code-reviewer` runs on it"*. One synthetic test, real signal.

Second concern: SKILL.md Session Close Checklist already has a list of items. Adding "append CHANGELOG entry" without specifying the trigger condition (any framework file changed? any proposal closed?) creates ambiguity. Be specific: *"if any file outside `local/` changed in this session, append an entry"*. Otherwise the executor will guess.

No secrets implications. No pipeline implications.

Status: **APPROVE with two amendments** (synthetic lint test in DoD; SKILL.md trigger condition specific).

### Risk Officer — D (tail risk, drawdown, what breaks)

The risk profile here is **operational**, not financial. No code paths altered, no risk parameters touched. What can go wrong:

1. **Audit-trail rupture**: the migration deletes PROGRESS.md §Session Log and the CHANGELOG.md backfill is incomplete. Net loss of history. **Mitigation already present**: Backfill source mapping is 1:1; pre-deletion copy of PROGRESS.md is captured in `git diff` and reviewable. Acceptable.
2. **Lint false-negative leaks a marker into framework prose later**, undetected. Compounds. **Mitigation present**: three enforcement points (lint, SKILL.md, README convention). Tolerable.
3. **Scope creep to `docs/retros/` mid-execution**. Tempting because the retros are the visible "v2.0" surface. Closing them rewrites historical record. **Mitigation present**: explicit out-of-scope, and §Scoping Decisions (d) gives the principle.

What I want added: a tripwire entry in the Risks table — *"if during execution the executor finds a fourth source of framework history (not Session Log, not Status Logs, not CHANGELOG), pause and amend the proposal"*. Fourth-source means we missed something foundational; sweeping forward without acknowledging it would lock in incoherence.

Status: **APPROVE with one amendment** (fourth-source tripwire).

## Delta Annexe — Round 1 (Core Team)

- **Absorbed**:
  - **A1 (Quant Architect)** — ADL/CHANGELOG cross-link rule. Will add to DoD: any new ADL row in PROGRESS.md must be paired with a `Process` entry in CHANGELOG referencing the date.
  - **A2 (Quant Architect)** — Single-source the lint pattern set in `.claude/review-patterns.md`; proposal references by anchor. Removes drift surface.
  - **B1 (Portfolio Manager)** — Smoke gate is "executed and findings recorded", not "passed clean". Failures route to PROGRESS.md Open Process-Bias Items as a follow-up issue, not back-pressure on this proposal.
  - **B2 (Portfolio Manager)** — Pre-execution grep drives the actual edit set; manifest is candidate scope. Files with zero hits recorded as scanned in Status Log.
  - **C1 (CTO)** — Synthetic lint test in DoD: a manufactured `Phase 2A` marker in a fake diff must trigger `/code-reviewer`.
  - **C2 (CTO)** — SKILL.md Session Close trigger condition explicit: "any file outside `local/` changed".
  - **D1 (Risk Officer)** — Fourth-source tripwire row added to Risks & Mitigations.

- **Resisted**:
  - None at this round. All Core Team amendments are coherent and additive; absorbing them costs little and tightens DoD.

## Delta Annexe — Round 2 (Cross-Model Critique)

**Critiquing Model:** Gemini
**Verdict:** APPROVED WITH STRUCTURAL AMENDMENTS

- **Resisted A1 (ADL cross-link, originally absorbed Round 1)** — A cross-link between the Architecture Decisions Log and CHANGELOG is a patch on bad architecture: both are historical event logs, and double bookkeeping is a failure state, not a redundancy benefit. **Decision (supersedes A1)**: migrate the Architecture Decisions Log *out of* `PROGRESS.md` and *into* `CHANGELOG.md` (under a `### Decisions` subsection per dated section, preserving persona attribution). `PROGRESS.md` becomes purely forward-looking: Current State, In Progress, Next Up, Backlog, Open Process-Bias Items, Staged Improvements. **DoD #3 inverted**: ADL section in PROGRESS.md is *deleted*, not preserved verbatim. Backfill source mapping (§Backfill) extended to include ADL rows, migrated 1:1 with persona attribution preserved.

- **Added L14 — The Breadcrumb Fallacy.** The proposal's draft premise was that anchors like "Proposal 003" should be stripped from user-facing prose to spare cold readers. But the anchor is the *only* breadcrumb a cold reader has to find the *why* behind a non-obvious rule. Stripping it orphans the rule from its rationale and turns the framework into an untraceable black box. **Closed by** decision rule (b) extended: proposal anchors are *converted to architectural citations*, not deleted. Rephrase `"introduced in Proposal 003"` → `"See [Proposal 003](proposals/003-phase-1b-data-integration.md) for structural rationale."` The rule stands on its own to a cold reader; the breadcrumb to the *why* remains.

- **Added L15 — The Syntactic Lint Trap.** A literal regex `\bv[12]\.\d\b` in a lint rule blocks legitimate references to external dependency versions ("API v2.0", "Requires `pandas>=v2.1`"). The CTO's approval treated `/code-reviewer` as a bash script; it isn't — it is an LLM. **Closed by** the lint rule in `.claude/review-patterns.md` being expressed as a **semantic instruction**, not a regex set: *"Flag any version markers (e.g. v2.0, Phase 1B, Session #N, Proposal NNN) that refer to the framework's internal methodology. Ignore external dependency versions, API versions, and library version strings."* DoD #5 reworded; DoD #4 grep retains regex (it is the executor's mechanical scan, not the reviewer's gate) but the prose contract is semantic.

- **Added EM-1 — The Un-Executable Smoke Test.** DoD #10 mandates "a fresh `/clear` session" — but the executing agent cannot `/clear` itself mid-execution without losing the context needed to close the proposal. The DoD as written is unrunnable. **Closed by** DoD #10 reworded: the cold-reader smoke is performed by **spawning a sub-agent** (Sonnet, no `local/` read access) with the in-scope file list, asked to summarise three rules selected by random offset. Sub-agent's verbatim Q&A is returned to the orchestrator and appended to the Status Log. The orchestrator never relinquishes its own context.

**Conclusion**: the proposal successfully pivots the framework to an append-only historical audit trail. By merging the ADL into CHANGELOG and converting version markers into architectural citations, traceability is *strengthened*, not weakened — the prose clears of insider jargon while the *why* remains one click away. Round 2 amendments (R-A1 reversal, L14, L15, EM-1) fold into DoD before APPROVAL.

## Amendments

> Append-only. Any deviation from the reviewed plan recorded here.

- A1: ADL cross-link rule (Quant Architect, Round 1) — **SUPERSEDED Round 2** by Gemini's structural-merge resistance; ADL migrates *into* CHANGELOG, no cross-link maintained.
- R-A1: ADL → CHANGELOG migration (Gemini, Round 2) — **FOLDED** into DoD #3 (inverted: section deleted), §Relationship in (c), File manifest, §Backfill source mapping (extended), Sequence step 3, Risks table (persona-attribution row).
- R-L14: Architectural-citation conversion for proposal anchors (Gemini, Round 2) — **FOLDED** into decision rule (b) (now three-way: STRIP / CONVERT / KEEP) and DoD #4 (gate is "zero unresolved matches", with conversion as one resolution).
- R-L15: Semantic lint instruction (Gemini, Round 2) — **FOLDED** into DoD #5 (semantic instruction text), File manifest, Sequence step 5.
- R-EM-1: Sub-agent smoke test (Gemini, Round 2) — **FOLDED** into DoD #10 (sub-agent orchestration with no `local/` access).
- A2: Lint pattern single-source (Quant Architect, Round 1) — **FOLDED** into DoD #5 (proposal references the `## Sanitisation Lint` anchor in `review-patterns.md`).
- B1: Smoke gate wording (Portfolio Manager, Round 1) — **FOLDED** into DoD #10 final clause ("executed and findings recorded", not "passed clean").
- B2: Pre-grep drives edit set (Portfolio Manager, Round 1) — **FOLDED** as Sequence step 0; manifest is candidate scope.
- C1: Synthetic lint test (CTO, Round 1) — **FOLDED** as DoD #11.
- C2: SKILL.md trigger condition (CTO, Round 1) — **FOLDED** into DoD #7 with explicit `local/`-prefix trigger.
- D1: Fourth-source tripwire (Risk Officer, Round 1) — **FOLDED** as DoD #12 and Risks table row.

- R-EX-1: Execution model stays Opus (Gemini, Round 2 follow-up) — **FOLDED** as new §Execution Model below; Status Log thrift-gate reminder retracted.

> All twelve amendments folded into the DoD body and supporting sections. The proposal as written reflects both review rounds. Status flips DRAFT → REVIEWED. APPROVAL pending user sign-off.

## Execution Model

> Added Round 2 follow-up (Gemini, R-EX-1). Pre-empts a thrift-gate misapplication on close.

**Execution remains with Opus.** Sequence step 0 (pre-grep) is mechanical, but every subsequent step that touches a public-facing markdown file invokes the three-way decision rule (b) — strip / convert / keep — per match. That is semantic reasoning under architectural context (load-bearing vs. ornamental, citation target validity, surrounding-prose coherence after rephrase), not pattern substitution. Stepping down to Sonnet here would re-create the very failure mode L14 closes: a lower-tier model regresses toward blind-regex behaviour, over-strips, and orphans rules from rationale across 17+ governance files in a single pass — unrecoverable without a full re-execution.

**Therefore**: no `/model sonnet` step-down on close. The thrift-gate fires for *purely* mechanical work (file moves, dependency pins, format-only edits); a HEAVY sanitisation sweep that mutates the framework's audit-trail centre of gravity is not that. The token economy is the wrong axis to optimise on a proposal whose entire purpose is preserving meaning.

This decision applies to Proposal 004's execution only. It does not amend the global thrift-gate orchestrator-discipline rule — it scopes it correctly.

## Status Log

> Append-only.

- 2026-04-26 — DRAFT opened. Triggered by `PROGRESS.md` "Next Up" queue and memory `project_engine_status` ("Proposal 004 next"). Four scoping questions answered in §Scoping Decisions per user brief. Core Team Round 1 captured; seven amendments queued. Round 2 (Gemini cross-model) not yet run — required before APPROVAL.
- 2026-04-26 — Round 2 Gemini cross-model critique completed. Verdict: APPROVED WITH STRUCTURAL AMENDMENTS. Round 1's A1 (ADL cross-link) **superseded** by Round 2 R-A1 (structural merge of ADL into CHANGELOG). Three new loopholes added: L14 (Breadcrumb Fallacy — convert anchors to citations, do not delete), L15 (Syntactic Lint Trap — semantic instruction, not regex, in `review-patterns.md`), EM-1 (Un-Executable Smoke Test — spawn sub-agent, do not `/clear` self). Eleven amendments now queued. Status remains DRAFT pending consolidated DoD revision before user APPROVAL.
- 2026-04-26 — Consolidation pass complete. All eleven amendments (Round 1 + Round 2) folded into the DoD body. Decision rule (b) restructured to three-way: **STRIP** version mentions, **CONVERT** proposal anchors to markdown citations, **KEEP** historical context notes. DoD expanded from 10 to 12 items. §Relationship rewritten: PROGRESS.md becomes purely forward-looking; both Session Log and Architecture Decisions Log migrate into CHANGELOG (with `### Decisions` per-date subsection preserving persona attribution). Backfill source mapping extended to include ADL rows. Sequence of execution gained step 0 (pre-grep candidate scan) and explicit sub-agent smoke step. Risks table extended (fourth-source tripwire, persona-attribution loss, broken-citation 404, decorative-import gate). Loopholes L11 and L12 marked SUPERSEDED Round 2; L14/L15/EM-1 added. **Status: DRAFT → REVIEWED.** Awaiting user APPROVAL.
- 2026-04-26 — Round 2 follow-up critique from Gemini absorbed. Thrift-gate step-down for execution **retracted**. Original framing ("sweep is mechanical") wrongly conflated Sequence step 0 (mechanical regex scan) with the per-line three-way decision rule (semantic, architectural context required). A Sonnet step-down on the sweep step would regress toward blind-regex behaviour and re-create the L14 failure across 17+ governance files. New §Execution Model section codifies: execution remains Opus; thrift-gate is correctly scoped to purely mechanical work, which this is not. R-EX-1 amendment added (twelfth). Status remains REVIEWED pending user sign-off.
- 2026-04-26 — **APPROVED** by user in their own voice ("I approve"). Status flips REVIEWED → APPROVED. Execution scheduled for next session — fresh `/clear` boot, Opus orchestrator, no thrift-gate step-down on the sweep per R-EX-1. Boot prompt: *"Read `proposals/004-sanitisation-sweep-changelog.md` and execute starting at Sequence step 0."*
- 2026-04-26 — **EXECUTING**. Fresh Opus session. Pre-grep candidate scan (Sequence step 0) complete. **Edit set (8 files with marker hits)**: `PROGRESS.md`, `proposals/README.md`, `.claude/commands/war-room/SKILL.md`, `docs/RISK_FRAMEWORK.md`, `brainstorms/_TEMPLATE.md`, `docs/DATA_STANDARDS.md`, `agents/macro_strategist.yml`, `agents/risk_guardian.yml`. **Scanned, no edits needed (9 files, zero hits)**: `AGENTS.md`, `CLAUDE.md`, `USER_INSTRUCTIONS.md`, `SHARING.md`, `docs/STRATEGY_LOGIC.md`, `docs/COMPLIANCE.md`, 15 other agent YAMLs (out of 17), `.claude/review-patterns.md` (modified for new lint anchor), `proposals/_TEMPLATE.md` (modified for Status Log convention). **Fourth-source tripwire (DoD #12)**: no fourth source of framework history detected during scan; PROGRESS.md, Status Logs, and (now-superseded) ADL fully covered by §Backfill source mapping. Note: §Backfill mapping listed 2026-04-06 ADL as ×4 rows but the source has 5; migrated all 5 verbatim per 1:1 sourcing rule (L4 closure). **Code-provenance carve-out (KEEP with justification)**: `agents/macro_strategist.yml:8` and `agents/risk_guardian.yml:8` retain `# Phase 1B (Proposal 003): this agent CONSUMES the pre-evaluated gate table` per §Scoping (b) explicit code-comment exemption — these are debugger-facing, not cold-reader-facing.
- 2026-04-26 — **DoD #4 grep re-run on edit set: zero unjustified matches.** All remaining marker matches in in-scope edit-set files are either CONVERTED proposal anchors (markdown citations to `proposals/NNN-*.md`) or KEPT code-provenance comments. Specifically: `PROGRESS.md:20` and `:21` — `Proposal 001` / `Proposal 003` converted to `[Proposal NNN](proposals/...)` citations; `docs/RISK_FRAMEWORK.md:280` and `:307` — `Proposal 001` / `Proposal 003` converted; `docs/DATA_STANDARDS.md:134` — `Proposal 001` converted; `agents/macro_strategist.yml:8` and `agents/risk_guardian.yml:8` — code-provenance comments retained per §(b). Files `proposals/README.md`, `.claude/commands/war-room/SKILL.md`, `brainstorms/_TEMPLATE.md` post-sweep: zero matches.
- 2026-04-26 — **DoD #11 synthetic lint test: PASS.** Manufactured a one-line insertion in `AGENTS.md:5` reading "Phase 2A applies to all sessions starting 2026-05." Invoked `/code-reviewer` skill on the change. Output (verbatim): *"Sanitisation Lint rule fires. The inserted sentence on `AGENTS.md:5` introduces the marker `Phase 2A` in user-facing markdown. Per the Sanitisation Lint anchor in `.claude/review-patterns.md`, framework-internal phase identifiers (`Phase 1A`, `Phase 1B`, and by direct generalisation `Phase 2A`) must be flagged when they refer to the framework's internal methodology in user-facing prose… [BLOCK] AGENTS.md:5 — 'Phase 2A applies to all sessions starting 2026-05.' introduces a framework-internal phase marker in user-facing prose. — Strip the sentence; if a 2026-05 process change is intended, append a `### Process` entry to `CHANGELOG.md` under a `[2026-05-...]` section instead. **BLOCK**"*. Synthetic insertion reverted immediately after. Sanitisation Lint anchor cited; lint rule semantically generalised beyond the regex set (regex `\bPhase 1[AB]\b` does not match `2A`, but the semantic instruction caught it) — closes L15 / R-L15 in production.
- 2026-04-26 — **DoD #10 cold-reader sub-agent smoke: EXECUTED, findings recorded.** Random offsets fixed BEFORE sub-agent run (no cherry-pick): Rule 1 = `docs/RISK_FRAMEWORK.md:307`, Rule 2 = `brainstorms/_TEMPLATE.md:304`, Rule 3 = `PROGRESS.md:19`. Sub-agent: Sonnet, `general-purpose`, instructed not to read `local/**`. **Verbatim findings**:
  - **Rule 1** — Summary: Evaluator Failure Protocol owned by Risk Officer; defines what happens when `gate_eval` raises; no silent fallback to agent recall. Cold-reader blocker: "the failure mode the deterministic gate-evaluation pipeline was built to retire" implies a known predecessor system; the cited [Proposal 003](003-phase-1b-data-integration.md) carries the *why* but is not directly readable in the cold-reader's allowed scope.
  - **Rule 2** — Summary: paste `gate_eval` output verbatim; do not hand-fill from memory; thresholds in `config/gates.yml`; GREEN/AMBER/RED is the authoritative deployment decision. Cold-reader blocker: **none — reads cleanly cold.**
  - **Rule 3** — Summary: second War Room session (April 2026) complete; first under current methodology with mandatory Counter-Regime agent and 5-distinct-framework Strike Team. Cold-reader blockers: "first session under the current War Room methodology" is a temporal anchor implying a prior methodology; "Counter-Regime agent" / "5-distinct-framework Strike Team" are explained elsewhere within the allowed file list but not on this line.
  - **Overall verdict**: one rule (Rule 1) requires Proposal 003 to fully understand the "predecessor failure mode" prose; this is the L14 trade-off (architectural citation > deletion).
  - **Disposition**: per B1, smoke gate is "executed and findings recorded", not "passed clean". Findings routed to `PROGRESS.md` Open Process-Bias Items as **P-09 — Cold-reader fragility in proposal-citation prose** (Tier 3 follow-up). Does not back-pressure this proposal's close.
- 2026-04-26 — **DoD #8 self-referential CHANGELOG entry**: `CHANGELOG.md` 2026-04-26 dated section now contains `### Added` / `### Changed` / `### Process` / `### Decisions` lines for Proposal 004 itself. Entry-or-it-didn't-happen: satisfied. **DoD #9**: `proposals/README.md` index has row 004; convention text mentions the CHANGELOG-append rule on close. **DoD #2 / #3**: `PROGRESS.md` Session Log and Architecture Decisions Log sections both deleted; replaced with one-line pointers to `CHANGELOG.md`. **All 12 DoD items closed.** Status flips APPROVED → **DONE**.
