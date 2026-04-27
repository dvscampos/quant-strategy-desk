# CHANGELOG

All notable framework changes are recorded here. Personal session outcomes
(NAV, P&L, holdings) live in `local/SESSIONS.md`.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) — append-only,
reverse chronological by date-of-event. Categories: `Added`, `Changed`, `Removed`,
`Fixed`, `Process`, `Decisions` (architectural decisions, persona-attributed).

## [Unreleased]

## [2026-04-27]

### Removed
- `CLAUDE.md` §Skills table — deleted three phantom Local skill rows (`/audit`, `/backtest`, `/risk-check`) that advertised skills not present on disk; build-out deferred as Staged Improvement S-13 (Proposal 008).

### Changed
- `PROGRESS.md` §Staged Improvements — added S-13 logging the deferred build-out of `/audit`, `/backtest`, `/risk-check` with trigger conditions and portability note.
- `README.md` §Requirements — added Windows-only Git for Windows prerequisite with explanation that Claude Code requires `bash.exe` as its shell (not for version control).
- `README.md` §Quick Start — added Windows callout blockquote above the clone command block.
- `proposals/README.md` — rows 006, 007, 008 added to index.

### Added
- `proposals/006-windows-git-prereq-readme.md` — proposal file for Windows Git prerequisite documentation update.
- `proposals/007-war-room-first-run-guard.md` — proposal file for first-run pre-flight guard.

### Fixed
- `.claude/commands/war-room/SKILL.md` — added Pre-Flight: First-Run Detection block before Phase 0; skill now halts with an onboarding redirect when `local/INVESTOR_PROFILE.md` is missing or empty (zero-byte), instead of silently stalling at Step A (Proposal 007).

### Process
- [Proposal 006](proposals/006-windows-git-prereq-readme.md) DONE — LIGHT doc change; governance 2/2; no code modified.

## [2026-04-26c]

### Added
- `proposals/005-p09-public-release.md` — proposal file for this session's work (P-09 reword + sanitisation sweep + initial public release). Required by `proposals/README.md` convention: every PROPOSE survives `/clear` and session boundaries via its file.

### Changed
- `proposals/README.md` — row 005 added to index.
- `PROGRESS.md` — P-09 reword + initial public release logged as completed; GitHub repo link added.

### Process
- [Proposal 005](proposals/005-p09-public-release.md) DONE — `/code-reviewer` APPROVE; all DoD items green except T3 (pending 2026-05-16 per date-lock).

## [2026-04-26b]

### Changed
- `docs/RISK_FRAMEWORK.md` §Evaluator Failure Protocol — cold-reader reword (P-09a): replaced "the failure mode the deterministic gate-evaluation pipeline was built to retire" with explicit description of the prohibited pattern (agents substituting estimated/recalled values for unavailable gate data). [Proposal 003](proposals/003-phase-1b-data-integration.md) citation retained as structural breadcrumb.
- `PROGRESS.md` Completed bullet (2026-04 session) — cold-reader reword (P-09b): dropped temporal anchor "First session under the current War Room methodology"; retained descriptive parenthetical (Counter-Regime agent, 5-distinct-framework Strike Team) as the lead.
- `PROGRESS.md` §Open Process-Bias Items — P-09 ticked RESOLVED 2026-04-26.
- `SHARING.md` — added non-advice disclaimer blockquote at top of file; removed §"Cross-model critique (Delta Annexe)" section (user-global governance convention, not framework content).
- `docs/COMPLIANCE.md` — prepended jurisdiction disclaimer and non-advice header (file ships with Portugal as worked example; onboarding rewrites for new user's jurisdiction).
- `brainstorms/INDEX.md` — converted from personal session index to framework convention stub (personal index moved to `local/brainstorms/INDEX.md`, gitignored under existing `local/*` rule).

### Removed
- `docs/retros/` — stray directory containing a single duplicate retro artefact (`2026-04-26.md`). Canonical copies live in `local/retros/` per `skill-config.yaml`. Deleted to avoid tracking personal session data in the public framework.
- `docs/BACKTEST_REPORT.html`, `docs/PROJECT_OVERVIEW.html` — generated report artefacts moved to `local/` (gitignored). Generated outputs do not belong in the public framework manifest; the source data and generators (`scripts/generate_dashboard.py`, `backtesting/`) ship and recipients regenerate locally.

### Added
- `local/.gitkeep` — empty marker file; ensures `local/` directory is preserved on fresh clone for onboarding (`init_workspace.py` requires the directory to exist).
- `local/brainstorms/INDEX.md` — personal session index (moved from `brainstorms/INDEX.md`; gitignored).
- `.gitignore` — expanded database ignore rule from `data/*.db` to `**/*.db` and `**/*.sqlite`; covers generated SQLite databases in any subdirectory (e.g. `backtesting/engine/backtest.db`).

### Process
- Initial `git init` (this entry) — first public commit of the Quant Strategy Desk framework. Pre-commit sanitisation sweep: secrets scan (`git grep --cached`), PII grep, symlink audit, canary test, staged-file verification.

## [2026-04-26]

### Added
- `CHANGELOG.md` (this file) at project root — canonical, append-only framework-change record. Backfilled from `PROGRESS.md` §Session Log + §Architecture Decisions Log + the three closed proposals (001/002/003). See [Proposal 004](proposals/004-sanitisation-sweep-changelog.md).
- `Sanitisation Lint` anchor in `.claude/review-patterns.md` — semantic instruction (not a literal regex) that flags framework-internal version markers in user-facing markdown while ignoring external dependency / model / library version strings; converts proposal anchors to markdown citations.
- `proposals/_TEMPLATE.md` Status Log preamble — the closing entry MUST be paired with a `CHANGELOG.md` line (entry-or-it-didn't-happen).
- `.claude/commands/war-room/SKILL.md` §3b — explicit Session Close step: "if any file outside `local/` changed in this session, append a `CHANGELOG.md` entry."

### Changed
- `PROGRESS.md` §Session Log section deleted; replaced with a one-line pointer to `CHANGELOG.md`. PROGRESS.md is now forward-looking only.
- `PROGRESS.md` §Architecture Decisions Log section deleted; replaced with a one-line pointer to `CHANGELOG.md`. ADL rows migrated 1:1 into `### Decisions` subsections per dated CHANGELOG entry, with persona attribution preserved (`- (X, Persona Name) <decision> — <rationale>`).
- Sanitisation sweep across the public-facing framework manifest: framework-internal version markers (`War Room v2.0`, `Session #N`, `Phase 1A`, `Phase 1B`) stripped from user-facing prose; proposal anchors (`Proposal 001`, `Proposal 003`) converted to markdown citations linking to the proposal file. Files touched: `PROGRESS.md`, `proposals/README.md`, `.claude/commands/war-room/SKILL.md`, `docs/RISK_FRAMEWORK.md`, `docs/DATA_STANDARDS.md`, `brainstorms/_TEMPLATE.md`. Code provenance comments in `agents/macro_strategist.yml` and `agents/risk_guardian.yml` retained (debugger-facing, not cold-reader-facing).
- `proposals/README.md` Convention section: added the CHANGELOG-append rule on proposal close. Index row 003 title sanitised; row 004 added.

### Process
- [Proposal 004](proposals/004-sanitisation-sweep-changelog.md) DONE — pre-grep candidate scan executed; per-line three-way decision rule (STRIP / CONVERT / KEEP) applied across 8 in-scope files with marker hits and 9 zero-hit candidates recorded as "scanned, no edits needed"; DoD #4 zero-unjustified-matches assertion green; DoD #11 synthetic lint test green (Sanitisation Lint anchor fired on a manufactured `Phase 2A` insertion in `AGENTS.md`); DoD #10 cold-reader sub-agent smoke executed with verbatim findings recorded (one residual cold-reader fragility flagged for PROGRESS.md Open Process-Bias Items, not back-pressuring close per B1).
- (A, Quant Architect / R-A1, Gemini Round 2) Architecture Decisions Log relocated from `PROGRESS.md` into `CHANGELOG.md` `### Decisions` subsections — single canonical historical event log, persona attribution preserved.

### Decisions
- (B, Portfolio Manager / B2, Round 1) Pre-grep drives the actual edit set — proposal manifest is a candidate list; files with zero hits are recorded as scanned without gratuitous touch.
- (D, Risk Officer / D1, Round 1) Fourth-source tripwire — if a fourth source of framework history is discovered mid-execution (not Session Log, not Status Logs, not CHANGELOG, not ADL), execution pauses and the proposal is amended before resuming.

 — snapshot → GateReport evaluator with `Market_Risk_Tier` / `Data_Confidence_Tier` separation; sentinel-file walk-up for `PROJECT_ROOT`; float-boundary epsilon guard; canonical `compute_gates_content_sha()` public function (semantic-content lock recipe). See [Proposal 003](proposals/003-phase-1b-data-integration.md).
- `scripts/data/prompts.py` — `format_macro_prompt()` / `format_risk_prompt()` single-source prompt constructors.
- `scripts/data/parity_check.py` — mechanical parity check vs prose Phase 2 table; split-based parsing replacing fragile regex; header validation for column-order drift.
- `scripts/data/cli.py` + `__main__.py` — `gate_eval` subcommand.
- `tests/test_gate_eval.py` — 39 → 46 tests; `TestGatesContentSha` (recipe pinned, comment-insensitivity, data-change sensitivity); `TestArtefactSync` (REPLAY_DELTA + proposal Status Log must contain live canonical SHA).
- `tests/test_skill_invariants.py` — rewritten with dynamic agent discovery via `gate_consumption: true|false` field; `test_all_agents_declare_gate_consumption`; `_build_watched_files()` regex-based.
- `agents/macro_strategist.yml`, `agents/risk_guardian.yml` — `gate_consumption_rules`, `escalation_rules`, `output_format` added.
- `docs/RISK_FRAMEWORK.md` §Evaluator Failure Protocol.
- `backtesting/REPLAY_DELTA.md` — 12 BT sessions classified (0 BUG); canonical SHA in header.
- `backtesting/POST_MORTEM_BRIEF.md` §Gate Replay Findings.
- `local/snapshots/2026-04.json` + `local/snapshots/backtest/BT-01..BT-12.json` — 13 synthetic fixtures.

### Changed
- All 17 `agents/*.yml` carry a `gate_consumption: true|false` field; `macro_strategist` + `risk_guardian` = `true`.
- `agents/macro_strategist.yml`, `agents/risk_guardian.yml` consume the gate evaluator output; recall paths removed.
- `.claude/commands/war-room/SKILL.md` Step B rewritten with B.1–B.5 gate_eval procedure.
- `brainstorms/_TEMPLATE.md` Phase 2 gate table → `[GATE_EVAL_OUTPUT]` placeholder; Phase 7 `Tier_Override` Log added.
- `config/gates.yml` — schema/semantics comment block; semantic-content SHA lock recipe pinned.
- FRED warning routed to stderr.

### Process
- [Proposal 003](proposals/003-phase-1b-data-integration.md) DONE — 82 tests green / 1 skipped (live smoke); gate_eval CLI live; parity check 0 tier flips vs 2026-04 prose; 12 BT sessions replayed (0 unexplained divergences); rollback gate retracted pending live smoke 2026-05-16.

## [2026-04-25]

### Added
- `local/` segregation: 10 personal artefacts moved; `local/*` gitignore rule; templates created. See [Proposal 002](proposals/002-project-portability.md).
- `scripts/init_workspace.py` — idempotent, never ingests secrets; FRED detection verified.
- `SHARING.md` — fork/share guide for the framework.
- `skill-config.yaml` — root-level skill configuration anchor.

### Changed
- All framework files (`CLAUDE.md`, `AGENTS.md`, `agents/*.yml`, `docs/`, `_TEMPLATE.md`, `scripts/`) updated to `local/` paths.
- `PROGRESS.md` personal content extracted to `local/SESSIONS.md` (per-entry triage).
- Onboarding questionnaire expanded 5 → 11 questions.
- Session Staleness Check added for irregular contributors.

### Process
- [Proposal 002](proposals/002-project-portability.md) DONE — all 11 artefact moves confirmed; init_workspace.py written and tested; grep-clean standard applied across 44 files; Proposal 001 audit clean.
- Dual-model cross-check complete (Gemini Round 2); Delta Annexe captured in [Proposal 002](proposals/002-project-portability.md).

## [2026-04-23]

### Added
- Tier 1 macro data layer: `DataProvider` ABC, `SnapshotWriter` (canonical JSON + SHA256), `HttpClient` (backoff + on-disk cache), FRED provider, ECB provider, CLI (`python -m scripts.data fetch`). See [Proposal 001](proposals/001-data-layer-upgrade.md).
- `config/gates.yml` as single source of gate thresholds; prose de-duplicated to reference it.
- `docs/RISK_FRAMEWORK.md` §Data Degradation Protocol.

### Process
- [Proposal 001](proposals/001-data-layer-upgrade.md) DONE — all 7 DoD gates green; 54 offline tests pass; live smoke test passed (7 series: FRED×4 + ECB×3); snapshot written and hash verified; adversarial review of 14 Gemini loopholes (L1–L14) absorbed; Phase 1B commitment recorded.

## [2026-04-19]

### Process
- Process reform after the 2026-04 War Room (post-DFNS.PA false-negative investigation): Phase 1 restricted to macro state — no candidate ticker fetches; Phase 2.5 Candidate Instrument Verification added post-thesis with mandatory Data Failure Protocol (retry → alt format → alt exchange → alt source); Phase 1.5 Counter-Regime Analysis (mandatory parallel Sonnet agent); carry-forward brief scoped to Orchestrator only, stripped from Strike Team prompts; Phase 7 context brief gutted (agents now judge cold); pre-session live log (`local/brainstorms/YYYY-MM.pre-session.md`) written before Strike Team runs for tamper resistance. Files touched: `SKILL.md`, `_TEMPLATE.md`, `CLAUDE.md`, `AGENTS.md`. Protocol Audit checklist expanded 9 → 12 checks.

### Decisions
- (A, Quant Architect) Session Go/No-Go Check — new mandatory section in `brainstorms/_TEMPLATE.md`, placed between Staleness Check and Strike Team Selection. Three verdicts: GO / DEFER EXECUTION / POSTPONE. Covers binary risk events (Hormuz, escalation), imminent data releases, VIX Emergency Protocol, and broker accessibility. Distinct from deployment gates (Phase 1) — gates govern capital deployment; Go/No-Go governs whether to run the session at all. Added to CLAUDE.md mandatory sections checklist.

## [2026-04-06]

### Decisions
- (D, Risk Officer) ETF-only universe (no individual stocks) — monthly cadence too slow for single-stock event risk (earnings gaps, scandals). Micro-NAV makes single stocks = lottery tickets. Thematic ETFs capture sector tailwinds with diversification. Survivorship bias in stock-picking ("the next Novo Nordisk") ignores the many failures. Review at S-5 trigger.
- (A, Quant Architect) Structured Strike Team output formats — standardises agent outputs (tables, not prose) for cross-session comparability without constraining analysis. Independence rule: agents must disagree with orchestrator framing when their data says otherwise.
- (C, CTO) Tiered read order — Always: AGENTS.md, PROGRESS.md, local/INVESTOR_PROFILE.md, local/PORTFOLIO.md, RISK_FRAMEWORK.md, STRATEGY_LOGIC.md. On-demand: agent YAMLs (at launch), DATA_STANDARDS.md, COMPLIANCE.md. Saves ~10k context tokens per session.
- (B, Portfolio Manager) Hypothesis Log for between-session ideas — natural-language scratchpad for investment observations. Orchestrator formalises at session start. Signal Generator investigates alongside own signals. Precursor to edge pipeline (S-7).
- (A, Quant Architect) Session + Trade Scorecards — Session Scorecard (5 metrics in Handoff) and Trade Performance Review (closed positions + running stats) added to template. Precursor to Karpathy self-improvement (S-2).

## [2026-04-05]

### Decisions
- (D, Risk Officer) Tiered cash floor (30% → 15% Standard) — 30% floor was single biggest performance drag (66.5% deployment). Tiered by NAV: micro €200, Standard 15%, Full 10%.
- (B, Portfolio Manager) AMBER deployment gates — binary GREEN/RED replaced with GREEN/AMBER/RED. AMBER = half-rate deployment. 8 gates (added EUR/USD, reclassified tariff).
- (A, Quant Architect) Thesis Validation Protocol — valid thesis types defined. Invalidated theses must be re-proposed, exited, or grandfathered with sunset. Prevents drift.
- (D, Risk Officer) VIX Emergency Protocol — VIX >35 = zero deployment + mandatory review. Fills gap between AMBER gates and kill switch.
- (A, Quant Architect) Session Close Checklist (replaces /commemorate) — project is not a git repo. /commemorate never ran. Process Sheriff checks embedded in session template.
- (B, Portfolio Manager) Asset-class targets (generic, not ticker-specific) — prevents backtest bias in live portfolio. War Room decides instruments; framework sets asset-class ranges.

## [2026-04]

### Process
- Portability & Critical Review session — in-place genericisation of framework files for shareability; onboarding questionnaire expanded 5 → 11 questions; Session Staleness Check added for irregular contributors; critical review delivered 7 improvements implemented and 2 proposals dropped (MCP, pre-session script); Staged Improvements list created (S-1 to S-10) with trigger conditions.

## [2026-03-28]

### Decisions
- (D, Risk Officer) Risk Guardian fixed (Two Sigma) — risk methodology needs month-to-month consistency; Challenger slot provides secondary risk perspective. Upgrade to paired Risk at NAV > 5,000.
- (B, Portfolio Manager) Macro Strategist now rotating — different lenses (Bridgewater regime, AQR factor, Man Group trend) catch different things. Was incorrectly fixed with no alternatives.
- (A, Quant Architect) 5-agent Strike Team standard — added Challenger role. Execution/Compliance were never included despite own retrospective saying to. 8 of 15 agents had never served on Strike Team.
- (B, Portfolio Manager) Session scheduling: third Saturday — after NFP, CPI, ECB. Weekend for reading. 10+ days before month-end for execution.
- (A, Quant Architect) War Room process refresh — `/war-room` skill (prep+session+sheriff), rotation enforcement, agent performance tracking, price affordability filter, carry-forward briefs.

## [2026-03]

### Process
- Foundation session — created governance framework (6-persona model, 8-step methodology); generated 15 specialist agent persona YAML configurations; established documentation structure (`docs/`, `agents/`, `brainstorms/`); created portfolio ledger and War Room template with 7 phases + 15-agent sign-off.

## [2026-03-01]

### Decisions
- (B, Portfolio Manager) European equities as primary universe — user is Europe-based; accessibility on standard platforms.
- (A, Quant Architect) 6-persona governance model (A–F) — covers architecture, PM, CTO, risk, execution, and compliance perspectives.
- (C, CTO) Python as primary language — industry standard for quant finance; rich ecosystem (pandas, numpy, scipy).
- (B, Portfolio Manager) Monthly cadence, no day-trading — investor places trades once/month at War Room; no intraday monitoring.
- (B, Portfolio Manager) European preference, not restriction — global instruments allowed if clearly superior and accessible on EU brokers.
- (D, Risk Officer) Defined risk only (no naked shorts) — investor must never owe more than capital invested.
- (D, Risk Officer) Instrument-specific stop-losses — -3% floor + vol stops for ETFs; flat -3% fires on ETF noise at VIX 18+.
- (A, Quant Architect) Role-based agent selection — `Task()` examples use role placeholders, not hardcoded agent names, to prevent bias.
- (B, Portfolio Manager) Staged deployment (3-month) — first allocation 15% → 45% → 65% over March–May; binary risks require cash optionality.
