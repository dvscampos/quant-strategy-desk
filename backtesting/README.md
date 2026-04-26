# Historical Simulation — Methodology

> **This is an illustrative simulation, NOT an out-of-sample backtest.**
> See the "Critical Limitations" section below before interpreting any results.

---

## Purpose

Simulate what would have happened if this system had been running for the 12 months prior to the first live War Room (March 2026). The simulation follows the exact same process, governance, and template as the live sessions, applied retrospectively.

## Parameters

| Parameter | Value |
|---|---|
| **Starting NAV** | €200 (monthly €200 contribution) |
| **Starting portfolio** | 100% cash |
| **Session dates** | ~15th of each month (after US CPI/PPI release) |
| **Execution assumption** | T+2 from session date, using closing price |
| **Stop-loss tracking** | Monthly — check at each session whether any position breached its stop-loss during the month (using the month's low price) |
| **Transaction costs** | €0.00 (zero-commission broker assumed per Risk Officer micro-NAV recommendation) + 0.05% bid-ask spread on liquid ETFs |
| **FTT** | Applied where relevant (France 0.3%, Italy 0.1%, Spain 0.2%, UK 0.5%) |
| **Deployment cadence** | Same staged approach as live: 15% → ~45% → ~65% over first 3 months, then monthly review |
| **Benchmarks** | STOXX 600 (EXSA.DE), 60/40 EUR portfolio, MSCI World (IWDA.AS) |

## Session Schedule

| # | Session Date | Execution Date | Information Cutoff |
|---|---|---|---|
| 1 | 2025-03-15 | 2025-03-17 | 2025-03-15 |
| 2 | 2025-04-15 | 2025-04-17 | 2025-04-15 |
| 3 | 2025-05-15 | 2025-05-19 | 2025-05-15 |
| 4 | 2025-06-15 | 2025-06-17 | 2025-06-15 |
| 5 | 2025-07-15 | 2025-07-17 | 2025-07-15 |
| 6 | 2025-08-15 | 2025-08-18 | 2025-08-15 |
| 7 | 2025-09-15 | 2025-09-17 | 2025-09-15 |
| 8 | 2025-10-15 | 2025-10-17 | 2025-10-15 |
| 9 | 2025-11-15 | 2025-11-17 | 2025-11-15 |
| 10 | 2025-12-15 | 2025-12-17 | 2025-12-15 |
| 11 | 2026-01-15 | 2026-01-19 | 2026-01-15 |
| 12 | 2026-02-15 | 2026-02-17 | 2026-02-15 |

## Critical Limitations

### 1. Look-Ahead Bias (the fundamental problem)

The AI model producing these sessions was trained on data that includes the events of 2025–2026. Even when explicitly instructed to reason only from information available at the cutoff date, the model's "intuitions" and "confidence levels" are contaminated by knowledge of subsequent events. For example:

- A model asked to assess defence stocks in March 2025 may unconsciously assign higher confidence because it "knows" the sector subsequently rallied
- A model asked to assess gold in June 2025 may be unconsciously influenced by its knowledge of later price movements
- Regime classifications may be unconsciously informed by hindsight

**This contamination is inherent and cannot be fully eliminated.** The simulation tests the *process and framework*, not the alpha of the recommendations.

### 2. Macro Reasoning vs. Price Data

This simulation separates two layers:
- **Macro reasoning** (subjective, LLM-generated): The regime analysis, theme identification, and instrument selection. This is contaminated by look-ahead bias.
- **Price data** (objective): Entry prices, stop-loss checks, and return calculations use actual historical prices. These are auditable and unbiased.

The returns are real. The question of "would this system have recommended these specific trades" is illustrative.

### 3. Execution Assumptions

- All trades assumed executed at T+2 closing price. In practice, a retail investor would use limit orders and might achieve better or worse execution.
- Stop-losses assumed to fire at exactly the stop-loss price if the month's low breaches it. In practice, slippage could worsen the fill.
- At €200 starting NAV with monthly €200 contributions, positions are constrained by minimum lot sizes. The 5% per-position cap is physically impossible — see `docs/RISK_FRAMEWORK.md` §Micro-NAV Overrides for the approved override rules. Results should be interpreted as percentage returns, not absolute EUR amounts.

### 4. Phase 7 Sign-Off in Backtest Sessions

The 15-agent Phase 7 sign-off runs identically to live sessions (real Haiku sub-agents, independent verdicts). Backtest sessions revealed systematic issues that are addressed by protocol improvements:

- **Context isolation**: Phase 7 agents in backtest sessions must NOT read `brainstorms/` (live sessions) or `PORTFOLIO.md` (live portfolio). All context is provided inline via the Phase 7 Context Brief.
- **Micro-NAV awareness**: Agents must check NAV and apply the correct override tier from `docs/RISK_FRAMEWORK.md` before flagging position sizing violations.
- **Flag categorisation**: Raw flag counts are misleading. The orchestrator categorises flags as Invalid (context confusion), Already Resolved (Strike Team addressed), or Legitimate (new, unresolved). Only legitimate flags count toward the 3-flag redesign threshold.
- **N/A verdicts**: Agents whose speciality is not applicable at current scale (e.g. stat-arb at €400 NAV) should reply "N/A" rather than forcing a flag.

### 5. Micro-NAV Constraints

The simulation starts at €200 NAV and grows by €200/month. At these levels:
- Minimum lot sizes (1 share) force position concentrations above standard limits
- Hard stop-losses are economically destructive (commission/spread > stop-loss gain)
- The 5% position cap, -3% hard floor, and staged deployment targets are overridden per `docs/RISK_FRAMEWORK.md` §Micro-NAV Overrides
- These overrides phase out as NAV crosses €1,000 and €2,000

---

## Folder Structure

```
backtesting/
├── README.md                     ← This file
├── PERFORMANCE.md                ← Final tearsheet (after all 12 sessions)
├── PORTFOLIO_HISTORY.md          ← Running portfolio state after each session
└── sessions/
    ├── 2025-03.md                ← Session 1
    ├── 2025-04.md                ← Session 2
    └── ...
```
