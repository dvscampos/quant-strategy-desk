# Quant Strategy Desk — Progress & Roadmap

> Last updated: 2026-04-26

## Current State

### ✅ Completed
- **Governance framework**: `AGENTS.md`, `CLAUDE.md`, `PROGRESS.md`, `local/PORTFOLIO.md` established
- **Agent personas**: 15 specialist YAML configs in `agents/` — all updated with shared investor profile
- **Documentation**: Strategy logic, risk framework, data standards, compliance (Portugal-specific) docs created
- **War Room template**: `brainstorms/_TEMPLATE.md` with 7 phases, anti-bias rule, anti-assumption rule, 15-agent sign-off
- **First War Room session (2026-03)**: Completed. Trade outcomes, regime call, and P&L in `local/SESSIONS.md`.
- **Historical simulation**: 12-month backtest complete (March 2025 → February 2026). See `backtesting/` for methodology, sessions, and results.
- **12-month backtest post-mortem**: Completed. Analysed all 20 topics (12 user questions + 8 orchestrator observations). Strike Team challenged the improvement plan (Two Sigma Risk, Bridgewater Macro, Renaissance Challenger). Output: 18 implemented changes across RISK_FRAMEWORK.md, AGENTS.md, _TEMPLATE.md, CLAUDE.md, STRATEGY_LOGIC.md. Key changes: tiered cash floor (30% → 15% at Standard NAV), AMBER deployment gates, Thesis Validation Protocol, VIX Emergency Protocol, Session Close Checklist (replaces /commemorate), regime accuracy retrospective.
- **Portability refactoring**: In-place genericisation of hardcoded references across framework files. Onboarding expanded to 11 questions (contribution style, cash reserve, ETF-only disclosure). Session Staleness Check added for irregular contributors.
- **Process reform (2026-04-19, post-2026-04 session)**: Fixed availability bias + 4 related loopholes in War Room framework. Triggered by DFNS.PA false-negative investigation (yfinance transient failure mis-read as structural unavailability). Changes: (1) Phase 1 restricted to macro state — no candidate ticker fetches; (2) Phase 2.5 Candidate Instrument Verification added post-thesis with mandatory Data Failure Protocol (retry → alt format → alt exchange → alt source); (3) Phase 1.5 Counter-Regime Analysis (MANDATORY parallel Sonnet agent); (4) Carry-forward brief scoped to Orchestrator only, stripped from Strike Team prompts; (5) Phase 7 context brief gutted — agents now judge cold; (6) Pre-session live log (`local/brainstorms/YYYY-MM.pre-session.md`) written before Strike Team runs for tamper resistance. Files touched: `SKILL.md`, `_TEMPLATE.md`, `CLAUDE.md`, `AGENTS.md`. Protocol Audit checklist expanded 9 → 12 checks.
- **Critical review + improvements**: Implemented 7 improvements: structured agent output templates, trade/session scorecards, tiered read order (~10k tokens saved), Hypothesis Log, enriched agent roster, Monthly Risk Dashboard fix, Staged Improvements list (S-1 to S-10). Dropped MCP data integration (not worth it at current scale) and pre-session script (portability issues).

- **Second War Room session (2026-04)**: Completed. Ran with Counter-Regime agent and 5-distinct-framework Strike Team. Trade outcomes, regime call, and P&L in `local/SESSIONS.md`.
- **Data Layer Upgrade — Tier 1 macro substrate**: COMPLETE (2026-04-23). FRED + ECB providers, canonical JSON snapshots with SHA256, `config/gates.yml` as single source of gate thresholds, Data Degradation Protocol in `docs/RISK_FRAMEWORK.md`, 54 tests green, live smoke passed. See [Proposal 001](proposals/001-data-layer-upgrade.md).
- **Sanitisation Sweep & CHANGELOG Introduction**: COMPLETE (2026-04-26). Stripped framework-internal version markers from public-facing prose; converted proposal anchors to markdown citations; introduced root-level [`CHANGELOG.md`](CHANGELOG.md) as canonical append-only framework-change record (backfilled 2026-03-01 → 2026-04-26 from PROGRESS.md §Session Log + §Architecture Decisions Log + closed proposals); migrated both Session Log and Architecture Decisions Log out of PROGRESS.md (replaced with pointers); added Sanitisation Lint anchor to `.claude/review-patterns.md` and CHANGELOG-append step to SKILL.md Session Close. See [Proposal 004](proposals/004-sanitisation-sweep-changelog.md).
- **Data Layer Integration**: COMPLETE (2026-04-26). gate_eval wired into War Room workflow; 82 tests green (7 added in post-review hardening); SKILL.md + agent YAMLs rewired; parity check passed (0 tier flips vs 2026-04 prose); 12 BT sessions replayed (0 unexplained divergences); Evaluator Failure Protocol in RISK_FRAMEWORK.md; rollback gate retracted pending 2026-05-16 live smoke. Post-review hardening: `compute_gates_content_sha()` public canonical recipe; artefact-sync tests; dynamic agent invariant test with `gate_consumption: true|false` field on all 17 agents; FRED warning routed to stderr; provenance receipt in pre-session log header; parity_check table parsing rewritten. See [Proposal 003](proposals/003-phase-1b-data-integration.md).
- **P-09 reword + initial public release**: COMPLETE (2026-04-26). Cold-reader rewording of two P-09 sites (RISK_FRAMEWORK.md §Evaluator Failure Protocol, PROGRESS.md 2026-04 session bullet). Full sanitisation sweep; `brainstorms/INDEX.md` converted to stub; `docs/retros/` deleted; generated HTML artefacts moved to `local/`; `.gitignore` expanded to `**/*.db` and `**/*.sqlite`; non-advice disclaimer added to SHARING.md and COMPLIANCE.md; cross-model critique section removed from SHARING.md (user-global, not framework). Initial commit `fd4d036` pushed to [github.com/dvscampos/quant-strategy-desk](https://github.com/dvscampos/quant-strategy-desk). See [Proposal 005](proposals/005-p09-public-release.md).

### 🔄 In Progress

- Nothing currently in progress.

### 🔜 Next Up

**Immediate — Next War Room session (2026-05-16) + data-layer-integration live smoke**
> **DoD #10b**: `python3 -m scripts.data fetch --session 2026-05 && python3 -m scripts.data gate_eval --session 2026-05` must run clean on 2026-05-16. Gates the data-layer-integration rollback-clock retraction (hard limit 2026-06-20).

**Known issues to address**
- `yfinance` Series format error: `TypeError: unsupported format string passed to Series.__format__` — fix is `.iloc[0]` or `.item()` in data-fetching code. Trivial; no proposal needed.

### 🔍 Open Process-Bias Items (from 2026-04-19 Opus audit)

> Tier 1 items (availability bias, carry-forward anchoring, regime-label single anchor, Phase 7 theatre, retrospective-narrative bias) resolved in the 2026-04-19 process reform. Items below are Tier 2/3, logged for later treatment. **Do not let them drift.**

- [ ] **P-01 Orchestrator circularity (Tier 2).** The Opus Orchestrator writes Strike Team prompts AND synthesises their outputs — same entity on both ends. Any Orchestrator framing bias is invisible to the loop. Candidate fix: a second Opus pass acting as "devil's orchestrator" that reads the same raw outputs and produces an independent synthesis, compared before the trade plan is locked.
- [x] **P-02 Small-sample rule overfitting (Tier 2). RESOLVED 2026-04-20.** Session Scorecard now includes a "New Rules Adopted This Session" section; every rule must be tagged `(origin: session #N, evidence: X observations)`. Rules require N≥10 observations before promotion to canon.
- [ ] **P-03 Gate threshold cliff edges (Tier 2).** Brent $99 vs $101 behaves discontinuously despite equivalent signal. Thresholds declared not derived. Candidate fix: graduated gate scoring (0–1 continuous) rather than GREEN/AMBER/RED; or calibrate thresholds against historical regime-change frequency.
- [x] **P-04 Rotation diversifies personas, not viewpoints (Tier 3). RESOLVED 2026-04-20.** `analytical_framework` field added to all 15 agent YAMLs (macro-narrative / quantitative / fundamental / behavioural / flow-based). SKILL.md rotation check and _TEMPLATE.md Rotation table now enforce ≥2 distinct frameworks per Strike Team.
- [x] **P-05 Thesis taxonomy as implicit filter (Tier 3). RESOLVED 2026-04-20.** Added "Crowded trade continuation" and "Narrative-driven flow" as first-class thesis types in `AGENTS.md`. Added escape-hatch option: agent may write "Does not fit taxonomy — [plain-language thesis + invalidator]" to prevent taxonomy pressure distorting honest thesis formation.
- [x] **P-06 Self-congratulating Session Scorecard (Tier 3). RESOLVED 2026-04-20.** Scorecard split into (a) Process Compliance (gates, regime confidence, deployment efficiency, thesis diversity, checklist score, framework diversity) and (b) Ex-Post Outcome Metrics filled at next session (regime-call accuracy T+30, trade IRR vs benchmark T+90, Phase 7 FLAG resolution rate). _TEMPLATE.md updated.
- [ ] **P-07 Streetlight-effect deployment gates (Tier 3).** Gates drift toward what yfinance exposes (VIX, Brent, ECB) rather than what predicts (credit spreads, PMI surprise, funding stress, positioning). Candidate fix: define target gate set independent of data availability; track data-sourcing gap as a separate backlog.
- [ ] **P-08 Implicit cost blindness (Tier 3).** Cost model includes FTT/stamp duty but ignores bid-ask on illiquid UCITS, ETF tracking error, FX spreads, internal fund cash drag. Matters more at micro-NAV. Candidate fix: extend transaction cost model in `docs/STRATEGY_LOGIC.md` with estimated ranges for each.
- [x] **P-09 Cold-reader fragility in proposal-citation prose (Tier 3). RESOLVED 2026-04-26.** Surfaced by the 2026-04-26 cold-reader smoke (Proposal 004 DoD #10). Two prose sites read fragile to a contributor with no project history: (a) `docs/RISK_FRAMEWORK.md` §Evaluator Failure Protocol — "the failure mode the deterministic gate-evaluation pipeline was built to retire" assumes a known predecessor; the cited [Proposal 003](proposals/003-phase-1b-data-integration.md) carries the *why* but the rule should also stand more cleanly on its own; (b) `PROGRESS.md` Completed bullet — "first session under the current War Room methodology" is a temporal anchor that implies a prior methodology without naming the change. Candidate fix: rephrase both to either name the predecessor explicitly or drop the temporal contrast. Logged for follow-up; does not back-pressure Proposal 004's close (B1).

### 📋 Backlog
- [ ] **Exit alert system** — automated notifications for stop-loss, kill switch, dividend cut, and macro triggers (email/SMS/push). Interim: set broker-level GTC stop-losses at trade entry.
- [ ] **CVaR/ES risk module** — conditional value-at-risk for tail risk measurement
- [ ] **Portfolio optimisation module** — Black-Litterman or risk parity for when portfolio exceeds 40% invested
- [ ] **MCP Elicitation checkpoints** — structured pause points in War Room for deployment gates, stop-loss confirmation, and position verification. Requires MCP server setup + Claude Pro support. Review feasibility each session.
- [ ] Data pipeline implementation (market data ingestion)
- [ ] Signal generation module (first alpha signals)
- [ ] Backtesting engine (event-driven with bias checks)
- [ ] Risk management system (position sizing, stop-losses, VaR)
- [ ] Paper trading integration (IBKR)
- [ ] Live execution system architecture
- [ ] Compliance monitoring automation

### 🔮 Staged Improvements (activate when trigger condition is met)

> These are improvements that aren't worth deploying yet but should be activated once the project reaches the right scale or data maturity. Check triggers at each War Room session.

| # | Improvement | Trigger Condition | Why Not Now | Compatible With Current? |
|---|---|---|---|---|
| S-1 | **Numeric scoring framework (0-100)** — weighted composite scores for gates, regime confidence, position health | 6+ live sessions with complete Session Scorecards | Need data to calibrate what scores actually predict. Categorical (GREEN/AMBER/RED) captures the signal for now. | Yes — current categorical scorecards upgrade directly to numeric |
| S-2 | **Karpathy self-improvement loop** — systematic bias detection, agent quality ranking, automated parameter adjustment | 12+ live sessions with complete scorecards AND trade performance data | Requires enough data to detect statistical patterns. Premature with <12 data points. | Yes — scorecards + trade performance are the data collection layer |
| S-3 | **Automated trade performance analysis** — IBKR CSV import, FIFO matching, statistical analysis per thesis type, behavioural pattern detection | 20+ closed trades with complete thesis metadata | Need enough closed trades for statistical significance. Manual tracking works until then. | Yes — manual Trade Scorecard collects the same fields; CSV automation replaces manual entry |
| S-4 | **Backtesting engine (code)** — Python event-driven engine for testing codifiable strategy hypotheses (signal validation, walk-forward, anti-overfitting) | When you have a specific, codifiable strategy hypothesis to test (not discretionary macro allocation) | Current approach is discretionary macro — no codifiable rules to test. BT1-12 tested the *process*, not a *strategy*. | Yes — STRATEGY_LOGIC.md signal validation pipeline is the specification |
| S-5 | **Individual stocks sleeve** — 5-10% NAV allocation for high-conviction single-name positions | NAV > €10k AND weekly (not monthly) review cadence AND fundamental analysis capability added | At current NAV, single stocks = lottery tickets. Monthly cadence is too slow for single-stock risk. ETFs capture thematic tailwinds with diversification. | N/A — would require new agents and data sources |
| S-6 | **Phase 7 reduction** — reduce sign-off from 10 to 6-8 most signal-producing agents | 6+ live sessions with `local/AGENT_PERFORMANCE.md` data showing clear noise vs signal separation | Need performance data to know which agents add value. Haiku cost is negligible, so premature optimisation. | Yes — just remove agents from the roster call |
| S-7 | **Heavyweight edge pipeline** — multi-stage hypothesis → backtest → review → signal aggregation → postmortem with structured skill handoffs | Backtesting engine exists (S-4) AND 12+ sessions of hypothesis log data | Requires codified strategies and automated backtesting. Current hypothesis log + manual War Room review handles the workflow for now. | Yes — Hypothesis Log is stage 1 of the pipeline |
| S-8 | **Platform adaptation guide** — documentation for running the framework on Gemini CLI, OpenAI Codex, Cursor | When sharing the project with someone who uses a non-Claude platform | No one has asked yet. Multi-agent features degrade on other platforms — guide needed to explain what works and what doesn't. | N/A — documentation only |
| S-9 | **Pre-session automation script** — Python script for NAV calculation, gate checks, correlation matrix, stop-loss proximity | When session preparation consistently takes >15 minutes of in-session time | Currently handled by /war-room skill Phase 1. External script adds fragility (timing, portability) without enough payoff at current scale. | Yes — script would output the same data Phase 1 currently computes |
| S-10 | **Fundamental analysis agents** — new agent YAMLs for company-level analysis (earnings, balance sheets, competitive positioning, management quality) to support individual stock picking | When a user indicates interest in individual stocks during onboarding (see CLAUDE.md Q11 follow-up) | Current agent roster is designed for macro/factor/ETF analysis. Individual stocks require a different analytical lens. | Yes — new agents slot into the existing Strike Team rotation system |
| S-11 | **Session checkpoint system** ✅ — writes `local/brainstorms/.checkpoint-YYYY-MM.json` after Phase 1 and Phase 7; `/war-room` skill reads it on resume so mid-session context compaction loses nothing | **ACTIVE** — implemented 2026-04-19 | Was: no recovery path if context compacted mid-session. JSONL transcript existed but required manual digging. | Yes — additive to SKILL.md; no existing files changed |
| S-12 | **HTML dashboard** ✅ — `scripts/generate_dashboard.py` generates `local/dashboard.html` from `local/brainstorms/` session files + `local/PORTFOLIO.md` | **ACTIVE** — implemented 2026-04-19 | Was: data lived only in Markdown. No visual MoM tracking. | Yes — read-only parser; does not modify any framework files |

---


## Architecture Decisions Log

> Architectural decisions (with persona attribution) are recorded in [CHANGELOG.md](CHANGELOG.md) under per-date `### Decisions` subsections.

---

## Known Issues

| Issue | Status | Reference |
|---|---|---|
| Gold ETC Portuguese tax classification uncertain | Open | `docs/COMPLIANCE.md` — confirm with contabilista whether physically-backed ETCs are Category B or G |
| Micro-NAV framework overrides | Active | `docs/RISK_FRAMEWORK.md` §Micro-NAV Overrides — standard rules phase in at €2,000 NAV |
| MCP Elicitation not yet available | Deferred | Review each session whether Claude Pro supports structured pause points |
| Karpathy Loop for strategy iteration | Backlog (Tier 3) | Agent proposes strategy tweaks, runs backtest, keeps improvements. Requires backtesting engine. See [github.com/karpathy/autoresearch](https://github.com/karpathy/autoresearch) and ATLAS (trading adaptation). |
| ReasoningBank (Ruflo-inspired) | Backlog (Tier 3) | Store successful War Room reasoning patterns for future sessions. Lighter than full Ruflo. See [github.com/ruvnet/ruflo](https://github.com/ruvnet/ruflo). |
| Prediction tracking | Backlog (Tier 2) | Log each session's macro predictions and trade theses. Compare prediction vs actual next session. Reveals systematic biases. |
| Agent calibration scores | Backlog (Tier 2) | Derive from `local/AGENT_PERFORMANCE.md` after 12 sessions. Weight Strike Team selection toward high-signal agents. |
| Gold decorrelator thesis broken | Open — requires re-proposal | Post-mortem: gold fell 12% alongside equities in March/April 2026. Decorrelation failed. Must be re-proposed under Thesis Validation Protocol before re-entry. |
| yfinance Series format error | Open | `TypeError: unsupported format string passed to Series.__format__` — needs `.iloc[0]` or `.item()` fix in data-fetching code |

---

## Session Log

> Framework change history lives in [CHANGELOG.md](CHANGELOG.md). This file is forward-looking only.
