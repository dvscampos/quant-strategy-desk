# Quant Strategy Desk — AI Agent Init

> **Session init file for all AI agents.** Read this first, then follow the read order below.

## First-Run Detection

> **Check this before doing anything else.**

If `local/INVESTOR_PROFILE.md` does **not** exist:

**Step 0 — Announce** (say this first):
> *"We'll do an 11-question onboarding to build your profile, then I'll run a one-line setup script to prepare your local workspace. Heads up: you'll need a free FRED API key (fred.stlouisfed.org, 2 minutes) before your first live macro fetch — you can add it after onboarding. Ready?"*

1. Greet the user and say: *"I noticed you don't have an investor profile set up. Is this your first time running this system?"*
2. Offer three options: **A) Yes, first time** / **B) No, I'm taking over from someone else** / **C) Returning user — something went wrong**
3. Based on the answer:
   - **A — First time**: Ask the following 11 questions (one at a time, wait for each answer):
     1. What country do you live in? (This determines your tax rates, regulator, and home-bias rules.)
     2. What currency do you invest in? (EUR, GBP, USD, CHF, other)
     3. Which broker(s) do you use or plan to use? (e.g. IBKR, Degiro, Trading212, XTB, other)
     4. Does your broker support fractional share trading? (Yes / No / Not sure)
     5. How do you plan to contribute? (A: Fixed monthly amount — if so, how much? / B: Irregular — I add money when I can / C: Lump sum — I'm starting with a one-off deposit)
     6. What is the minimum cash reserve you'd want to keep in your portfolio at all times? (This is your "dry powder" for buying opportunities during dips. If unsure, a good starting point is one typical contribution.)
     7. What is your risk tolerance? (Conservative: preserve capital, accept lower returns / Moderate: balanced growth and protection / Aggressive: maximise growth, accept higher drawdowns)
     8. What is your investment horizon? (< 3 years / 3–10 years / 10+ years)
     9. Do you have any existing holdings you want to track from day one? (Yes / No)
     10. Are there any countries or regions you want to overweight or underweight? (e.g. "avoid home country equities", "overweight US tech" — or say "none")
     11. Are there any sectors or instruments you want to exclude for personal or ethical reasons? (e.g. weapons, fossil fuels, gambling — or say "none")
     After Q11, inform the user: *"One thing to note: this framework is currently designed for ETF and index investing, not individual stock picking. The agent roster and risk controls are built around diversified instruments. If you're interested in individual stocks, the framework can still track them, but the War Room agents aren't currently equipped for fundamental company analysis (earnings, balance sheets, competitive positioning) — that's on the roadmap for a future version. Is ETF-focused investing a good fit for you, or would you like to discuss alternatives?"*
     If the user wants individual stocks, note it in `local/INVESTOR_PROFILE.md` §Investment Constraints and flag that the agent roster will need expansion (see Staged Improvements S-5 and S-10 in `PROGRESS.md`).
     Then (**Step 2 — Plumbing**, run before writing any personal files):
     ```bash
     python scripts/init_workspace.py
     ```
     This creates `local/` subdirectories, copies starter templates, and checks for the FRED API key. Output confirms workspace status.

     **Step 3 — Hydrate** (write personal files after plumbing succeeds):
     - Generate `local/INVESTOR_PROFILE.md` using the template structure, adapted to their answers. (Do not use `local/templates/` — generate fully from Q1–Q11 answers.)
     - Update `docs/COMPLIANCE.md` with their jurisdiction's tax section (research the relevant rates).
     - Update the **Home Bias Warning** in `brainstorms/_TEMPLATE.md` to reference their country.
     - Set the micro-NAV cash floor in `docs/RISK_FRAMEWORK.md` §Cash Floor to the user's stated minimum reserve (Q6). For irregular contributors, also note "no fixed contribution cycle" in the profile so the session cadence defaults to "when contributing or quarterly, whichever comes first."
     - If risk tolerance is "Conservative", tighten stop-losses in `docs/RISK_FRAMEWORK.md` by 1-2pp and increase cash floor tiers by 5pp each.
     - If fractional shares are unavailable, ensure the minimum-lot heuristic is active in `docs/RISK_FRAMEWORK.md`.
   - **B — Taking over**: Say *"I'll keep the existing profile structure. What needs to change for you?"* Then make the specific edits to `local/INVESTOR_PROFILE.md`.
   - **C — Returning user**: Say *"No problem — let me recreate it from your existing settings."* Check `PROGRESS.md` and `local/PORTFOLIO.md` for jurisdiction clues and regenerate.

Once `local/INVESTOR_PROFILE.md` exists, proceed with the normal read order below.

---

## Read Order (Tiered)

### Always (every session start)
1. `AGENTS.md` — personas (A–F), governance rules
2. `PROGRESS.md` — state of play, master roadmap
3. `local/INVESTOR_PROFILE.md` — jurisdiction, tax rates, broker preferences, risk constraints
4. `local/PORTFOLIO.md` — current holdings, trade history, P&L, dividends
5. `docs/STRATEGY_LOGIC.md` — signal rules, asset-class targets, backtesting standards
6. `docs/RISK_FRAMEWORK.md` — risk limits, position sizing, cash floor, VIX protocol

### On demand (read when needed for a specific phase or task)
7. `agents/[name].yml` — read only the specific agent YAML when launching that Strike Team sub-agent
8. `docs/DATA_STANDARDS.md` — read when building data pipelines or debugging data quality issues
9. `docs/COMPLIANCE.md` — read when a Compliance agent is on the Strike Team or when instruments touch new regulatory surface

## Stack
- **Language**: Python 3.11+
- **Data**: pandas, numpy, scipy, statsmodels
- **ML**: scikit-learn, XGBoost, LightGBM
- **Backtesting**: vectorbt / custom event-driven engine
- **Visualisation**: matplotlib, plotly
- **Data Sources**: yfinance, EODHD, Alpha Vantage, IBKR API
- **Broker API**: Interactive Brokers (ib_insync / ibapi)
- **Database**: SQLite (local development), PostgreSQL (production)
- **Config**: YAML agent definitions in `agents/`
- **Orchestration**: Python scripts with logging

## Non-Negotiables
- **Never modify strategy code without a PROPOSE summary and explicit user approval** (see `AGENTS.md`)
- **Always read a file before editing it**
- **No hardcoded API keys or secrets** — all credentials via environment variables
- **Paper trading must pass before live deployment** — no exceptions
- **Every signal must have an out-of-sample validation** before entering any strategy
- **Risk parameters are never relaxed without explicit user approval and Risk Officer review**
- **All backtests must include transaction cost modelling** — zero "frictionless" results
- **Proactively fix FutureWarnings and deprecations** in engine code — don't wait to be asked
- **Session files must pass the section checklist** — see "Session File Template Compliance" below. No shortcuts, no "I'll add it later"
- **Data availability does not gate thesis formation.** A ticker failing yfinance during Pre-Session Preparation is a data-fetch problem, not a thesis problem. The Strike Team forms its view first; instrument verification (Phase 5) happens after, and a failed fetch triggers the Data Failure Protocol (retry, alternate ticker format, alternate exchange, alternate source) before the idea is discarded.

## Context Hygiene (Session Rules)
- **`/clear` before each War Room session.** Sessions are self-contained: state lives in `local/brainstorms/YYYY-MM.md`, `MEMORY.md`, and this file. Carrying prior session analysis into the next session wastes ~100k tokens.
- **`/compact` only as a safety net** — if context hits ~80% before a BT session is finished. Instruct it to preserve: current session's trade plan, prices, Phase 7 verdicts, and engine CLI output. Discard: Strike Team raw transcripts, price-fetch output. If the BT is nearly done, finish and `/clear` instead.
- **Edit and regenerate** when a sub-agent hallucinates a price or makes an error — do not stack a correction message on top of the bad output.
- **Batch prompts** — one message with all instructions beats three sequential ones.
- **Disconnect Gmail and Google Calendar MCPs** when running backtests — they are unused here and add ~18k tokens of overhead per message.
- **Read `MEMORY.md` at session start** — before proposing any changes, check for prior agreements. Contradicting a prior decision without acknowledging it is a process failure.

## Session File Template Compliance

> **This is a hard rule, not a suggestion.** Incomplete session files create blind spots for future sessions.

Every War Room session file (`local/brainstorms/YYYY-MM.md`) **must** contain all of the following sections. Before marking a session as complete, **read the previous session file** and verify every section below is present in the new file. If any are missing, add them before moving on.

### Mandatory Sections Checklist

```
[ ] Frontmatter (tags, date, session_number, status, regime, ecb_rate, trades, nav_invested, nav_cash, previous/next_session)
[ ] Session Metadata block (date, execution date, NAV tier, model, process version)
[ ] Critical Events This Month
[ ] Key Issues Entering This Session
[ ] Session Staleness Check (gap calculation; staleness protocol if gap > 1.5× cadence)
[ ] Session Go/No-Go Check (verdict: GO / DEFER EXECUTION / POSTPONE; rationale; binary risk events, imminent data releases, VIX Emergency, broker access)
[ ] Strike Team Selection (with Anti-Bias and Anti-Assumption rules)
  [ ] Today's Strike Team table
  [ ] Rotation Check (consecutive counts, last session for each agent, analytical_framework per agent, ≥2 distinct frameworks enforced)
[ ] Strike Team Output Standards (structured output format per role — independence rule applied)
[ ] Phase 1: Portfolio Review — full holdings snapshot with entry/current/P&L/% NAV
  [ ] Position Age & Thesis Tracker (sessions held, original thesis, current status per position)
[ ] Pre-Session Live Log reference (local/brainstorms/YYYY-MM.pre-session.md written BEFORE Strike Team runs; tamper-resistant "view at T=0")
[ ] Phase 2: Macro Context
  [ ] Deployment Gate Check (8-gate table with GREEN/AMBER/RED tiers)
  [ ] Regime Classification (named agent)
  [ ] Macro Snapshot (delta table: previous session vs current)
  [ ] [Agent] Key Points (named bullet analysis from the Macro agent)
  [ ] Cross-Asset Signals
[ ] Phase 3: Counter-Regime Analysis (MANDATORY — parallel Sonnet sub-agent argues strongest alternative regime; alternative call, supporting evidence, invalidators, sizing implications, orchestrator resolution)
[ ] Phase 4: Signal Identification — ranked signal table + cross-asset signals
[ ] Phase 5: Instrument Verification (yfinance fetch for Strike-Team-proposed tickers only; Data Failure Protocol applied to any missing data before discard)
[ ] Phase 6: Strategy Architecture — trade plan table with sizing rationale
  [ ] Target vs Actual Allocation (target %, actual %, gap per position)
  [ ] Deployment Efficiency (this session: deployed/contribution; cumulative: total deployed/total contributed)
[ ] Phase 7: Risk Stress Test
  [ ] Risk Dashboard (VaR, concentration, beta)
  [ ] Stress Test: -10% Equity Correction (per-position table)
[ ] Phase 8: Challenger Review — assessment + verdict
[ ] Orchestrator Conflict Resolution — resolution log table + Key Decision
[ ] Exact Trade Instructions — per trade: plain-English tip, ISIN, TER, shares, price, cost, post-trade position, mental stop, max loss
  [ ] Post-Trade Monthly Snapshot (position table with themes)
  [ ] What This Means For You (3-4 sentence plain-language session summary — no jargon)
[ ] Phase 9: Full Desk Sign-Off
  [ ] Context Brief — MINIMAL (session type, NAV, holdings, trade plan only; NO Strike Team resolutions, Orchestrator synthesis, Challenger view, or Counter-Regime view — agents judge cold)
  [ ] Results table (15 agents)
  [ ] FLAG Categorisation (by category + per-trade breakdown)
[ ] Comparison to Previous Session
  [ ] Regime Accuracy Retrospective (was previous regime call accurate?)
  [ ] Position Changes table
  [ ] Macro Delta table (includes EUR/USD and Brent)
  [ ] Trade Performance Review (closed positions + running stats)
  [ ] Next Month Watchlist (8-gate table with GREEN/AMBER/RED tiers)
[ ] Execution Log
[ ] Session Close Checklist (all items checked before ending)
[ ] Handoff to Next Session
  [ ] Session Scorecard (5 metrics: gates, regime confidence, deployment efficiency, thesis diversity, process compliance)
  [ ] Compressed Session Summary (~5 lines)
  [ ] Open issues, positions to watch, THESIS REVIEW positions, expiring catalysts, rotation
  [ ] Concept of the Month (1 paragraph explaining the key financial concept from this session in plain terms)
[ ] Session Scheduling (next date, relevant events)
[ ] End-of-Month Mark (summary + per-position EOM detail table)
[ ] Changelog
```

### New Section Guidance

**Position Age & Thesis Tracker** (in Phase 0): Table with columns `Position | Sessions Held | Entry Session | Original Thesis | Current Status`. Surfaces underperformers early — without formal tracking, stale positions can persist for multiple sessions unnoticed.

**Target vs Actual Allocation** (in Phase 3): Table with columns `Position | Target % | Actual % | Gap`. Targets are implicit in the strategy — make them explicit so drift is visible at a glance.

**Deployment Efficiency** (in Phase 3): One line: `This session: [amount] / [contribution] (Y%) | Cumulative: [total deployed] / [total contributed] (Y%)`. Surfaces structural under-deployment early.

**What This Means For You** (after Exact Trade Instructions): 3-4 sentences explaining the session's key decision in plain language. Not per-trade (those already have "In Plain English" tips) — this is the session-level "so what?" for someone who isn't a quant.

**Concept of the Month** (in Handoff): One paragraph explaining the financial concept most central to this session's decisions. Examples: value traps, concentration caps, VIX and volatility gates. Builds financial literacy incrementally.

### Self-Validation Rule

After writing a session file, **count its sections against this checklist**. If the file is significantly shorter than the previous session (~400-500 lines for a 2-trade session, ~500-600 for 3-4 trades), something is missing — find it and fix it before proceeding. Do not rely on the user to catch this.

## Key Paths
| What | Where |
|---|---|
| Agent instructions | `AGENTS.md` |
| Progress & roadmap | `PROGRESS.md` |
| Investor profile | `local/INVESTOR_PROFILE.md` |
| Portfolio ledger | `local/PORTFOLIO.md` |
| Agent persona configs | `agents/*.yml` |
| Strategy modules | `strategies/` |
| Signal generators | `signals/` |
| Risk management | `risk/` |
| Data pipelines | `data/` |
| Utility functions | `utils/` |
| Backtesting engine | `backtesting/` |
| Configuration | `config/` |
| Documentation | `docs/` |
| Brainstorm archive | `local/brainstorms/YYYY-MM.md` |
| Hypothesis log | `local/HYPOTHESIS_LOG.md` |
| Brainstorm template | `brainstorms/_TEMPLATE.md` |
| Proposals archive | `proposals/NNN-slug.md` (index: `proposals/README.md`, template: `proposals/_TEMPLATE.md`) |
| Environment vars | `.env` (gitignored) |
| Env template | `.env.example` |

## Skills (Global & Local)

> `@ import .claude/review-patterns.md` — Loads Investments-specific governance and integrity checks into the global slash commands.

| Command | Purpose | Origin |
|---|---|---|
| `/propose` | Tiered change checkpoint with multi-persona review | Global |
| `/commemorate` | Release gate — audit → review → update PROGRESS/docs → record | Global |
| `/retro` | Session retrospective | Global |
| `/code-reviewer` | Diff review (logic, types, security) | Global |
| `/persona-review` | Post-impl sign-off from War Room personas | Global |
| `/process-sheriff` | Governance audit checkpoint | Global |
| `/war-room` | Launch monthly War Room brainstorm (requires Opus — see below) | Local |

## Agent Model Selection
After a PROPOSE is approved, categorise each sub-task:

| Tier | Model | When to use | Examples |
|---|---|---|---|
| **Mechanical** | Haiku | Pattern-based edits with clear instructions | Config value changes, constant updates, YAML field additions, log level changes |
| **Contextual** | Sonnet | Execution requiring code comprehension | Signal implementation, strategy wiring, data pipeline modifications, test writing |
| **Architectural** | Opus | Genuine reasoning depth needed | New strategy design, risk framework changes, cross-system refactors, ambiguous requirements |

### War Room / Brainstorm Pattern
For multi-persona brainstorming sessions (e.g., the European War Room), use this model allocation:

| Role | Model | Rationale |
|---|---|---|
| **Orchestrator** (runs the session, synthesises, resolves conflicts) | **Opus** | Must hold full macro context, mediate conflicting views, and produce coherent output |
| **Individual persona sub-agents** (each persona via `Task()`) | **Sonnet** | Each has a narrow, well-defined lens; YAML prompts are specific enough for Sonnet to excel |

```
# Opus orchestrates, then launches Sonnet sub-agents in parallel:
# Select agents via brainstorms/_TEMPLATE.md Strike Team rules (anti-bias + anti-assumption)
Task(model="sonnet", subagent="[MACRO_AGENT]",     prompt="Set the macro stage...")
Task(model="sonnet", subagent="[SIGNAL_AGENT]",    prompt="Propose alpha signals...")
Task(model="sonnet", subagent="[ARCHITECT_AGENT]", prompt="Structure into strategies...")
Task(model="sonnet", subagent="[RISK_AGENT]",      prompt="Stress-test the strategies...")
# Add Execution/Compliance agents as needed (see template anti-assumption rule)
# Opus reads all outputs → synthesises final memo
# Then launch 15 Haiku sign-off calls (Phase 7)
```

> [!IMPORTANT]
> **You must start the session in Opus.** Claude Code does not auto-upgrade models. The model you select at session start is the orchestrator. It can delegate *down* (Opus → Sonnet via `Task()`) but never promote itself *up*. If you start in Sonnet, you get Sonnet as orchestrator — which defeats the purpose.
> **Context tip**: War Room sessions consume 80–120k tokens. Run `/clear` before starting. If context hits 60% mid-session, run `/compact` — preserve: trade plan, prices, Phase 7 results. Discard: Strike Team raw transcripts.

> **Why not Opus for all sub-agents?** Opus is ~15× the cost of Sonnet. The quality difference for focused, single-persona analysis with a specific YAML prompt is marginal. Opus adds value at the synthesis/conflict-resolution layer, not at the individual review layer.

### Monthly Brainstorm Archive
Each War Room session is documented in its own file:

```
brainstorms/
├── _TEMPLATE.md          ← Copy this for each new session
├── 2026-03.md            ← March 2026 brainstorm
├── 2026-04.md            ← April 2026 brainstorm
└── ...
```

**Convention**: One session per month. File name is `YYYY-MM.md`. Each session includes a "Comparison to Previous Session" section tracking what changed in the macro environment and which positions are being maintained, added, or exited. This builds a decision audit trail over time.

## Market Context
- **Home jurisdiction**: See `local/INVESTOR_PROFILE.md` §Jurisdiction & Regulation
- **Primary exchanges**: Per broker availability in `local/INVESTOR_PROFILE.md` §Brokers
- **Trading hours**: Check exchange hours for the investor's primary markets
- **Settlement**: T+2 for equities (standard across most markets)
- **Currency**: Per `local/INVESTOR_PROFILE.md` (primary currency determined by jurisdiction)
- **Key indices**: Determined by the investor's market universe and regional preferences
- **Regulatory framework**: Per `local/INVESTOR_PROFILE.md` §Jurisdiction & Regulation and `docs/COMPLIANCE.md`
- **Position type**: Long-only (see Defined Risk Only rule in `docs/RISK_FRAMEWORK.md`)
- **Operating cadence**: Monthly review and rebalance only (no day-trading)
