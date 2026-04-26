# Investments Review Patterns

These are project-specific patterns and governance checks that apply to the Quant Strategy Desk (Investments) project. Apply these rules when conducting code reviews, retrospectives, or commemorations.

## Session Close Checklist (Commemorate & Retro)
- War Room sessions are heavily templated. Ensure the Session Close Checklist from `brainstorms/_TEMPLATE.md` is complete before ending the session. 
- Process Sheriff checks are typically embedded in this checklist, but the global `/process-sheriff` can still be run as an additional layer.
- Ensure the `Handoff to Next Session` section is fully filled out.

## Thesis Validation Protocol
- Ensure positions without a valid thesis are placed into **THESIS REVIEW**.
- Ensure they are formally resolved via RE-PROPOSE, EXIT, or GRANDFATHER.

## Risk Check (Code Review)
- Any code changes that alter risk parameters MUST be flagged for mandatory Risk Officer review.
- Any new data source integration MUST pass Data Standards review.

## Backtest Friction
- Backtests MUST include transaction cost modelling. Do not accept frictionless backtest results.
- Ensure paper trading is explicitly flagged as required before live deployment of any new strategy.

## Strike Team Rotation Validation (War Room / Propose)
- Before selecting a Strike Team, check `local/ROTATION_LOG.md` (live) or `backtesting/ROTATION_LOG.md` (backtest) for consecutive-appearance violations (max 2 consecutive for any rotating agent).
- Ensure ≥2 distinct `analytical_framework` values across the team to prevent groupthink.
- The Counter-Regime Agent is MANDATORY and parallel to Macro — it does not count against rotation slots.

## Session File Section Completeness (Commemorate)
- Every `local/brainstorms/YYYY-MM.md` must contain ALL sections from the Mandatory Sections Checklist in `CLAUDE.md`. After writing a session file, count its sections against the checklist.
- If the file is significantly shorter than the previous session (~400–500 lines for a 2-trade session, ~500–600 for 3–4 trades), something is missing — find it before proceeding.

## Data Failure Protocol (Code Review / War Room)
- When a yfinance fetch fails for a Strike-Team-proposed ticker, the agent MUST follow the escalation chain: retry → alternate ticker format → alternate exchange → alternate data source — before declaring an instrument unavailable.
- Data availability does NOT gate thesis formation. The Strike Team forms its view first; instrument verification happens in Phase 5.

## Sanitisation Lint

> Flag any version markers (e.g. `v2.0`, `Phase 1B`, `Session #N`, `Proposal NNN`) in user-facing markdown that refer to the framework's internal methodology. Convert proposal anchors (`Proposal NNN`) to markdown citations linking to the proposal file (e.g. `[Proposal 003](proposals/003-phase-1b-data-integration.md)`) rather than deleting them — the link is the only breadcrumb a cold reader has to the rule's *why*. Strip session sequence anchors (`Session #N`), framework version literals (`v1.0`, `v2.0`, `War Room v2.0`), phase identifiers (`Phase 1A`, `Phase 1B`), and relative-temporal cues without an absolute date (`previously`, `formerly`, `new in`, `as of recently`) — the [CHANGELOG.md](../CHANGELOG.md) carries the timeline. Ignore external dependency versions (`pandas v2.1`, `API v2.0`), library version strings, model version literals (`Opus 4.7`, `Sonnet 4.6`), and code provenance docstrings (e.g. `# Canonical consumer of config/gates.yml (Proposal 003, Phase 1B).`) — these are read by debuggers, not cold readers.

**Decision rule (per match)**: (1) is it a *proposal anchor*? Convert to a markdown citation, do not delete. (2) Otherwise, would removing the marker leave the rule equally clear to a cold reader? Strip and let CHANGELOG carry the timeline. (3) If removal makes the rule incomprehensible without internal project history, keep the marker and rephrase the surrounding prose so it is explained on first use.

**Mechanical scan (executor only)** — the patterns below are the executor's grep candidates; the gating reviewer applies the semantic rule above. Patterns: `\bv[12]\.\d\b`, `\bSession #\d+\b`, `\bPhase 1[AB]\b`, `\bProposal \d{3}\b`, `\bsince Session\b`, `\bintroduced in\b`, `\bv\d era\b`. Zero **unresolved** matches at close — every match is either stripped, converted to a markdown citation, or kept with a one-line justification in the originating proposal's Status Log.

**CHANGELOG-append rule** — every material framework change closes by appending a [`CHANGELOG.md`](../CHANGELOG.md) entry under `[Unreleased]` (or a new dated section). Architectural decisions go under `### Decisions` with persona attribution (`- (X, Persona Name) <decision> — <rationale>`). A pull request that mutates a file outside `local/` without a CHANGELOG entry should be flagged.
