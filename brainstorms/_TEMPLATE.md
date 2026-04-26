---
tags: [war-room, brainstorm, YYYY]
date: YYYY-MM-DD
session: "Month YYYY"
session_number: N
status: complete
regime: "[regime classification]"
ecb_rate: "[rate]"
trades:
  - "[TICKER 1]"
  - "[TICKER 2]"
  - "[TICKER 3]"
nav_invested: "[X%]"
nav_cash: "[Y%]"
previous_session: "[[local/brainstorms/YYYY-MM]]"
next_session: "[[local/brainstorms/YYYY-MM]]"
---

# War Room Brainstorm — Month YYYY

> [!INFO] Session Metadata
> **Date**: YYYY-MM-DD
> **Execution date**: YYYY-MM-DD (date trades were / will be placed)
> **NAV tier**: [Micro-NAV (<€2,000) / Standard (€2,000–€10,000) / Full (>€10,000)]
> **Model**: Opus 4.7 (orchestrator) + Sonnet (sub-agents) + Haiku (Phase 7 sign-off)
> **Session cadence**: monthly (third Saturday — see `.claude/commands/war-room/SKILL.md`)
> **Mandate**: [what the session aims to decide]

---

## Critical Events This Month

> Events since the last session that affect the macro regime, existing positions, or deployment gates. List the top 3-5 — no analysis yet, just facts.

1. [e.g. "2026-04-03 — Strait of Hormuz tanker attacks resumed; Brent spiked to $98"]
2. [e.g. "2026-04-10 — ECB held rates at 2.00%; Lagarde rhetoric mildly dovish"]
3. [e.g. "2026-04-15 — US CPI +3.2% YoY, above consensus +3.0%"]

---

## Key Issues Entering This Session

> Problems, uncertainties, or carry-forward decisions from last session that must be resolved today.

- [ ] [e.g. "Gold decorrelation thesis broken — must re-propose or grandfather"]
- [ ] [e.g. "IWDA.AS approaching -8% mental stop — review position"]
- [ ] [e.g. "April deployment tranche gated on 8-gate check — run before any trades"]

---

## Session Staleness Check

*Before anything else, the orchestrator calculates the gap since the previous session.*

> **Previous session date**: [from Handoff section of previous session file]
> **Today**: [today's date]
> **Gap**: [X] days
> **Expected cadence**: [monthly / irregular — per `local/INVESTOR_PROFILE.md`]

**If gap ≤ 1.5× expected cadence** (~45 days for monthly users): proceed to Phase 0 normally.

**If gap > 1.5× expected cadence**: run the staleness protocol before Phase 1:

- [ ] **Gate sweep**: Re-evaluate all 8 deployment gates at current levels. Note any gate that crossed a tier boundary during the gap (e.g., VIX was >30 in week 3 but is now 22 — the stress happened and may have affected positions).
- [ ] **Stop-loss audit**: For each open position, check if price moved beyond the stop-loss distance at any point during the gap. If GTC orders were set, check if they fired. If mental triggers (micro-NAV), assume they were NOT acted on — flag any position that breached its trigger.
- [ ] **Expired catalysts**: Review the previous session's "Expiring Catalysts" list. Flag any that have passed. Mark affected position theses for review.
- [ ] **Stale handoff warning**: The previous session's "Positions to Watch" and "Open Issues" may be outdated. Read them, but verify current relevance before acting on them.
- [ ] **NAV reconciliation**: Ask the user to confirm current NAV (contributions + market moves during the gap may have shifted it significantly).

> [!CAUTION] Staleness ≠ Emergency
> A stale session doesn't mean the portfolio is in trouble — it means the *process* has a blind spot. The staleness check fills the gap so the War Room can proceed with current information, not stale assumptions.

---

## Session Go/No-Go Check

*Before selecting the Strike Team, the orchestrator assesses whether today is the right day to run this session — and whether trade execution should proceed, be deferred, or the session postponed entirely.*

> **This is not the deployment gate check** (Phase 1). The deployment gates decide whether to deploy capital this tranche. The Go/No-Go check decides whether to run the session at all. You can run the full session but defer execution; you can also postpone the session entirely if conditions make even the analysis premature.

| Check | Status | Detail |
|---|---|---|
| **Active binary risk event** | CLEAR / ACTIVE | Is there an ongoing event whose resolution in the next 24–72h would materially change the trade plan? Examples: Hormuz closure, active military escalation, imminent sanctions announcement. |
| **Imminent major data release** | CLEAR / PENDING | Is there a scheduled release (NFP, CPI, ECB decision) in the next 48h that would flip the regime call? If PENDING, note it — analysis today may be wasted if the data reverses the macro picture. |
| **VIX Emergency Protocol** | CLEAR / ACTIVE | VIX > 35? If yes, zero deployment is mandatory per `docs/RISK_FRAMEWORK.md` §VIX Emergency Protocol. Session can proceed for planning; no trades execute. |
| **Broker accessibility** | CONFIRMED / ISSUE | Is the broker available for execution this week? Any known account restrictions, KYC holds, or platform outages? |

### Go/No-Go Verdict

- **✅ GO** — Proceed with session and execution as planned. No active binary events; conditions stable enough for new positions.
- **⏸ DEFER EXECUTION** — Run the full session (analyse, plan, document), but hold all trades for 24–72h pending event resolution. Set a named trigger: "execute when [specific condition] is confirmed."
- **🛑 POSTPONE** — Reschedule the session entirely. Use only when conditions are so uncertain that the regime call will likely flip before you can act — making today's analysis premature, not just cautious.

**Verdict**: [GO / DEFER EXECUTION / POSTPONE]

**Rationale**: [1–2 sentences. If DEFER or POSTPONE, name the specific event and the expected resolution window. e.g. "Hormuz closure active since Apr 18 — tanker traffic suspended, Brent at $94. Deferring execution 48–72h pending US/Iran diplomatic signal. Full session proceeds for planning only."]

> [!IMPORTANT] If verdict is POSTPONE, stop here. Record the rationale and set a rescheduled date in the Session Scheduling section at the bottom. Do not run the Strike Team on information that will be obsolete before trades can execute.

---

## Strike Team Selection

Choose 5 agents from the roster. 6 when deploying into new instruments, crossing a NAV threshold, or touching regulatory surface.

> [!IMPORTANT] Anti-Bias Rule
> The orchestrator must **not** default to the same Strike Team every month. Before selecting, check `local/ROTATION_LOG.md` (live) or `backtesting/ROTATION_LOG.md` (backtest). **Max 2 consecutive sessions** for any rotating agent. Fresh perspectives catch blind spots that familiarity misses.

> [!WARNING] Anti-Assumption Rule
> Do **not** predict the brainstorm's output when selecting the Strike Team. You cannot know whether the session will produce ETFs, single stocks, or hybrids until the agents have run. Never justify skipping the Challenger role by assuming the output will be "simple" — that assumption biases the entire session. When in doubt, include the agent.

> [!NOTE] Price Affordability Filter
> Before the Signal Generator runs, calculate: **max affordable share price = 25% of current NAV**. Include this cap in the Signal Generator's prompt. Do not propose instruments above this price.

### Fixed Role

| Role | Purpose | Agent | Upgrade Trigger |
|---|---|---|---|
| **Risk Guardian** | Challenges everything, sets limits, stress-tests | Two Sigma Risk | Upgrade to paired Risk team (Two Sigma + Man Group/Dimensional/Renaissance) at NAV > 5,000 or when non-ETF instruments are introduced |

### Rotating Roles (max 2 consecutive sessions per agent)

| Role | Purpose | Choose From |
|---|---|---|
| **Macro Strategist** | Sets the economic regime, identifies tailwinds/headwinds | Bridgewater Macro, AQR Factor Model, Man Group Portfolio* |
| **Signal Generator** | Proposes alpha signals and data-driven opportunities | Citadel Alpha, Point72 ML, D.E. Shaw StatArb, AQR Factor Model*, Dimensional Factor Backtester |
| **Strategy Architect** | Structures signals into implementable strategies with rules | GS Quant Architect, Jane Street MM, Man Group Portfolio* |
| **Challenger** | Domain-specific challenge from outside the core team | Any agent not already on the Strike Team. Prioritise risk-adjacent agents (Man Group, Dimensional, Renaissance) when a second risk perspective is needed; Execution (Virtu, Millennium, Bloomberg) or Compliance (GS Compliance) when instrument/regulatory surface warrants it. |

*Man Group and AQR can each fill **one slot per session**, not multiple.

### Example Strike Teams (5 agents standard, 6 when warranted)

| Session Topic | Risk | Macro | Signal | Architect | Challenger |
|---|---|---|---|---|---|
| **Monthly general review** | Two Sigma | Bridgewater | Citadel | GS Architect | Man Group |
| **Factor rotation focus** | Two Sigma | AQR Factor | Point72 ML | GS Architect | Dimensional |
| **New instrument deployment** | Two Sigma | Bridgewater | D.E. Shaw | Jane Street | GS Compliance |
| **Post-shock recovery** | Two Sigma | Man Group | Citadel | GS Architect | Renaissance |
| **Going live with a strategy** | Two Sigma | Bridgewater | Citadel | Millennium | Virtu (+GS Compliance = 6) |

### Today's Strike Team

> **Selected**: [List the 5 agents chosen and why. Check local/ROTATION_LOG.md for anti-bias compliance.]

| Role | Agent | Consecutive Sessions | Rationale |
|---|---|---|---|
| Risk Guardian | Two Sigma Risk | [N] | Fixed role |
| Macro Strategist | [Agent] | [N] | [Why] |
| Signal Generator | [Agent] | [N] | [Why] |
| Strategy Architect | [Agent] | [N] | [Why] |
| Challenger | [Agent] | [N] | [Why] |

### Rotation Check

| Agent | Framework | Sessions in a Row | Last Session | Must Rotate Out? |
|---|---|---|---|---|
| [Agent] | [macro-narrative / quantitative / fundamental / behavioural / flow-based] | [N] | [YYYY-MM] | YES — must be replaced / NO |
| [Agent] | [framework] | [N] | [YYYY-MM] | YES — must be replaced / NO |

> Source: `backtesting/ROTATION_LOG.md` (or `local/ROTATION_LOG.md` for live sessions). Any agent at 2 consecutive sessions is mandatory rotation next month.
> **Framework diversity check**: Strike Team must include ≥ 2 distinct `analytical_framework` values. If all selected agents share the same framework, swap one for a different framework before proceeding.

---

## Strike Team Output Standards

> Each Strike Team agent must produce structured output in the format below for their role. This standardises cross-session comparability without constraining the agent's analysis.
> **Independence rule**: Form your own assessment from the data provided. If your analysis contradicts the orchestrator's framing or other agents' views, state your disagreement explicitly — that's the point.

### Macro Strategist Output Format
```
## Regime Classification
[Label] | Confidence: HIGH / MEDIUM / LOW
## Key Indicators (max 5)
| Indicator | Level | Direction (vs last session) | Implication |
## Trade Implications (max 3)
- [Implication]
## Risks to This View (max 2)
- [Risk]
```

### Signal Generator Output Format
```
## Top Signals (max 5, ranked)
| # | Ticker | ISIN | Name | Price | Thesis Type | Thesis (1 sentence) | Key Risk |
## Signals to Avoid (max 3)
| Ticker | Why to Avoid |
## Hypothesis Log Review
[Comment on any open hypotheses from local/HYPOTHESIS_LOG.md — investigated or dismissed with reason]
```

### Strategy Architect Output Format
```
## Proposed Trades (max 3)
| # | Action | Instrument | ISIN | Allocation (% NAV) | Entry Logic | Stop-Loss | Thesis Type |
## Sizing Rationale
[Why this allocation, referencing cash floor and deployment gates]
## Alternative Considered but Rejected
[At least 1 alternative with reason for rejection]
```

### Risk Guardian Output Format
```
## Risk Dashboard
| Metric | Value |
| Portfolio VaR (95%) | [X%] |
| Max single-position weight | [X%] |
| Equity-correlated exposure | [X%] (cap: 65%) |
| Correlation alert (any r > 0.80 pair) | [YES/NO — detail if YES] |
| Stop-loss proximity (nearest) | [Ticker at X% from stop] |
## Stress Test: -10% Equity Correction
| Position | Estimated Impact | Survives? |
## Verdict on Proposed Trades
[APPROVE / CONDITIONAL / BLOCK per trade, with specific concern if not APPROVE]
```

### Challenger Output Format
```
## Challenge Focus
[The single most important blind spot or assumption being challenged]
## Evidence Against the Consensus View
- [Point 1]
- [Point 2]
## What the Strike Team Is Missing
[1-2 specific risks or considerations not raised in Phases 1–4]
## Verdict
[ENDORSE with caveats / CHALLENGE — redesign required / BLOCK — thesis is broken]
## Conditions for Endorsement (if CHALLENGE)
[What would need to change for the Challenger to approve]
```

---

## Phase 1: Portfolio Review

*Before discussing new ideas, the orchestrator reads [[local/PORTFOLIO]] and presents the current state.*

> [!NOTE] Clean-Start Sessions (No Existing Positions)
> If the portfolio is empty (first deployment or post-liquidation), skip the Health Check, Pivot Candidates, Position Age Tracker, and Thesis Status Check. Instead:
> 1. State the starting NAV and cash floor tier (see `docs/RISK_FRAMEWORK.md` §Cash Floor)
> 2. Calculate the maximum deployable amount: NAV minus cash floor
> 3. Calculate the price affordability ceiling: 25% of NAV (no single instrument above this price)
> 4. The session focuses on building the initial portfolio — all instruments are evaluated from scratch with no inheritance from prior sessions or backtests
> 5. The Strike Team agents receive NO prior position context — they propose based on current macro conditions only

### Current Holdings Snapshot

[Paste current holdings table from [[local/PORTFOLIO]]]

When briefing Strike Team agents, always include the full holdings context:

```
Current Holdings (include in every Strike Team agent prompt):
- [TICKER]: [Full Name] ([ISIN]) — [1-line description]. Entry [date], P&L [X%], [Y%] NAV.
```

> This prevents agent factual errors (e.g., misidentifying an instrument). The ISIN is the definitive identifier.

### Health Check

- [ ] Any GTC stop-losses triggered since last session?
- [ ] Any dividends received? (update dividends table in [[local/PORTFOLIO]])
- [ ] Allocation drift: has any strategy moved >5% from target?
- [ ] P&L update: unrealised gains/losses on each position
- [ ] Any position in THESIS REVIEW status? (see `AGENTS.md` §Thesis Validation Protocol)

### Position Age & Thesis Tracker

> Surfaces underperformers and stale positions before new ideas are proposed. Without explicit age tracking, weak positions persist unnoticed across multiple sessions.

| Position | Sessions Held | Entry Session | Original Thesis | Current Status |
|---|---|---|---|---|
| [Ticker] | [N] | [YYYY-MM] | [Original thesis at entry] | INTACT / WEAKENING / THESIS REVIEW / BROKEN |

### Pivot Candidates

*Based on current holdings + macro regime, should any position be:*

- **HOLD** — thesis intact, keep it
- **INCREASE** — thesis strengthening, add more
- **REDUCE** — thesis weakening, take some off
- **EXIT** — thesis broken, sell

### Thesis Status Check

> Check each position against the Thesis Validation Protocol in `AGENTS.md`. Any position whose original thesis has been invalidated enters THESIS REVIEW status.

| Position | Original Thesis | Thesis Type | Still Valid? | Action |
|---|---|---|---|---|
| [Ticker] | [Original thesis at entry] | [Macro/Structural/Mean-reversion/Decorrelation/Factor] | YES / THESIS REVIEW | HOLD / RE-PROPOSE / EXIT / GRANDFATHER |

> Valid thesis types: Macro tailwind, Structural trend, Mean-reversion, Decorrelation, Factor exposure. See `AGENTS.md` §Thesis Validation Protocol for definitions.
> "Underweight correction" is NOT a valid standalone thesis.

---

## Phase 2: Macro Context

*The Macro Strategist sets the stage: regime classification, key indicators, and the current environment.*

### Deployment Gate Check

> [!IMPORTANT] Paste the output of `gate_eval` verbatim here.
> Run: `python -m scripts.data gate_eval --session YYYY-MM --format markdown`
> Do NOT hand-fill this table from memory or recall the latest macro prints.
> Thresholds are defined in `config/gates.yml`; the evaluator is `gate_eval`.
> Three tiers: GREEN (deploy normally), AMBER (deploy at half rate), RED (hold tranche).
> Rule: `Market_Risk_Tier` from gate_eval output is the authoritative deployment decision.

<!-- Paste gate_eval markdown output here — byte-identical to CLI stdout -->
[GATE_EVAL_OUTPUT]

> [!NOTE] Data_Confidence_Tier
> If `Data_Confidence_Tier = RED` in the gate_eval output: halt session and re-fetch
> (docs/RISK_FRAMEWORK.md §Evaluator Failure Protocol). Do not proceed with stale data.

**Gate Summary**: [copy from gate_eval output — Market_Risk_Tier] → [DEPLOY NORMALLY / DEPLOY AT HALF RATE / HOLD TRANCHE]

### Regime Classification

> [!CAUTION] Regime: [CLASSIFICATION] | Confidence: HIGH / MEDIUM / LOW
> [One-paragraph summary of the current regime and the 1-2 key events driving it]

### Macro Snapshot

> Delta table vs previous session — makes regime drift visible at a glance.

| Indicator | Previous Session | This Session | Change | Implication |
|---|---|---|---|---|
| Regime | [label] | [label] | → | [note if changed] |
| ECB Rate | [%] | [%] | ↑/↓/→ | |
| STOXX 600 | [level] | [level] | [+/-X%] | |
| Gold | [$X/oz] | [$X/oz] | [+/-X%] | |
| VIX | [level] | [level] | [+/-X] | |
| EUR/USD | [rate] | [rate] | [+/-X%] | |
| Brent | [$/bbl] | [$/bbl] | [+/-X%] | |
| BTP-Bund Spread | [bps] | [bps] | [+/-X bps] | |

### [Macro Agent] Key Points

*Named analysis from the Macro Strategist — distinct views, not a summary of the table above.*

- **[Point 1]**: [e.g. "Stagflation regime now base case — both legs confirmed (CPI reaccelerating + PMI softening)"]
- **[Point 2]**: [e.g. "ECB is trapped — can't cut with CPI above 3%; can't hike without triggering sovereign spreads"]
- **[Point 3]**: [e.g. "Germany fiscal impulse is 2-3 quarter lag — not visible in data yet but structurally positive"]

### Cross-Asset Signals

> Movements in one asset class that carry signal for another. These are early-warning indicators, not trade theses.

| Signal | Observed | Implication |
|---|---|---|
| [e.g. "Gold outperforming equities"] | [+X% vs -Y%] | [Risk-off rotation; check equity stop proximity] |
| [e.g. "BTP-Bund spread widening"] | [+Xbps] | [Sovereign stress early warning; cap European financials] |
| [e.g. "USD strengthening vs EUR"] | [EUR/USD -X%] | [Review non-EUR positions for FX drag] |

[Full macro analysis here]

---

## Phase 3: Counter-Regime Analysis

*Launched in parallel with the Macro Strategist. Same market data inputs; opposite framing instruction. This phase is MANDATORY — a Strike Team without a Counter-Regime agent does not pass protocol audit.*

**Counter-Regime agent**: [Persona name — must differ from Macro Strategist in this session]
**Alternative regime call**: [Named alternative]
**Confidence**: HIGH / MEDIUM / LOW (usually lower than the Macro call by design; that is acceptable)

### Supporting Evidence the Consensus Would Dismiss

- [Point 1 — data the Macro agent is likely to under-weight]
- [Point 2]
- [Point 3]

### Invalidators

- [What would force you back to the consensus regime]

### Sizing Implications That Differ From Macro Consensus

- [e.g. "If the alternative regime is correct, VWCE sizing should be halved and cash floor raised to 40%."]
- [e.g. "Gold sizing unchanged; it hedges both regimes."]

### Orchestrator Resolution (if Counter-Regime shifts sizing by >20%)

> Soft-pedal "noted and dismissed" is NOT acceptable when the alternative regime implies a material sizing shift. Document the resolution in the Orchestrator Conflict Resolution table.

[Explicit resolution or "N/A — Counter-Regime view does not materially change sizing"]

---

## Phase 4: Signal & Opportunity Identification

*The Signal Generator proposes signals relevant to the current regime. Before running, the orchestrator reads `local/HYPOTHESIS_LOG.md` and includes any open ideas in the Signal Generator's prompt for investigation.*

### Top Investment Ideas

| # | Ticker | Name | Price (€) | Signal Type | Thesis | Key Risk |
|---|--------|------|-----------|-------------|--------|----------|
| 1 | | | | | | |
| 2 | | | | | | |
| 3 | | | | | | |

### Signals to Avoid

> [!WARNING] Traps & Crowded Trades
> - **[Name]** — [Why to avoid]
> - **[Name]** — [Why to avoid]

### Hypothesis Log Review

> [!NOTE] Open hypotheses from `local/local/HYPOTHESIS_LOG.md` that the Signal Generator investigated this session.

| Hypothesis | Status | Finding |
|---|---|---|
| [From log] | INVESTIGATED / DISMISSED / CARRIED FORWARD | [1-line result] |

---

## Phase 5: Instrument Verification

*After the Signal Generator proposes tickers, the Strategy Architect runs yfinance verification on each candidate — post-thesis, never before. A failed fetch triggers the Data Failure Protocol before the idea is discarded.*

### Candidate Ticker Verification

| Ticker | Full Name | Exchange | Price (€) | yfinance Status | Notes |
|---|---|---|---|---|---|
| [TICKER] | [Name] | [Exchange] | [€X] | CONFIRMED / FAILED | [retry result / alternative tried] |

> **Data Failure Protocol**: On any yfinance miss: (1) retry once; (2) try alternate ticker format (e.g. `.DE` → `.PA`); (3) try alternate exchange listing; (4) try alternate data source. Only discard the idea if all four rungs fail — and document which rungs were tried.

---

## Phase 6: Strategy Architecture

*The Strategy Architect structures signals into implementable strategies with entry/exit rules.*

> [!NOTE] Execution Specialist (if on Strike Team)
> If an Execution Specialist was selected for this session, include their assessment here as a sub-section: platform availability, bid-ask spread estimate, optimal order type for each instrument on IBKR. Skip this sub-section if no Execution Specialist is on the team.

[Strategies here]

> [!NOTE] Maximum Drawdown Estimate
> [Worst-case drawdown calculation at full deployment]
> See [[docs/RISK_FRAMEWORK]] for kill switch thresholds.

### Target vs Actual Allocation

> Makes allocation drift visible before trades are finalised. Target % is the strategy's stated allocation from [[docs/STRATEGY_LOGIC]]; Actual % is current NAV weight.

| Position | Target % NAV | Actual % NAV | Gap | Action |
|---|---|---|---|---|
| [Ticker / Strategy] | [X%] | [X%] | [+/-X%] | HOLD / TOP UP / TRIM |
| Cash | [X%] | [X%] | [+/-X%] | |

### Deployment Efficiency

> One line, updated each session. Surfaces structural under-deployment before it becomes a habit.

**This session**: €[deployed] / €[contribution] ([Y%] of contribution deployed)
**Cumulative**: €[total deployed] / €[total contributed] ([Y%] of all contributions deployed since inception)

---

## Phase 7: Risk Stress Test

*The Risk Guardian challenges everything. Punches holes. Sets limits.*

> [!NOTE] Compliance Agent (if on Strike Team)
> If a Compliance agent was selected for this session, include their review here as a sub-section: regulatory implications, tax treatment (FTT, Portuguese CGT), MiFID II classification for any new instruments. Skip this sub-section if no Compliance agent is on the team.

### Tier_Override Log (DoD #17, L29)

Record any Risk Guardian escalations applied this session. Leave blank if none.
Entries here are aggregated to `local/AGENT_PERFORMANCE.md` after the session closes.

| Gate | Original Tier | Overridden Tier | Direction | Trigger (RISK_FRAMEWORK.md §ref) |
|---|---|---|---|---|
| [gate_id] | GREEN/AMBER | AMBER/RED | ↑ escalation | [named trigger] |

> [!NOTE] De-escalation (AMBER → GREEN, RED → AMBER) is NOT permitted here.
> De-escalation requires: (1) human edit to config/gates.yml, (2) gate_eval re-run,
> (3) one-line receipt in this table: "gates.yml edited mid-session: [reason]".

### Risk Dashboard

| Metric | Value |
|---|---|
| Portfolio VaR (95%, 1-day) | [X%] |
| Portfolio VaR (95%, 1-month) | [X%] |
| Max single-position weight | [X%] NAV ([Ticker]) |
| Equity-correlated exposure | [X%] (cap: 65%) |
| Correlation alert (r > 0.80) | YES — [pair] / NO |
| Nearest stop-loss proximity | [Ticker] at [X%] from stop |
| Beta to STOXX 600 | [X] |

### Stress Test: −10% Equity Correction

| Position | Weight % NAV | Estimated Impact | Survives Stop? |
|---|---|---|---|
| [Ticker] | [X%] | [−X% on position / −Y% on NAV] | YES / TRIGGERS STOP |
| **Portfolio total** | | **[−X% NAV]** | |

> [!WARNING] Home Bias — Do Not Replicate Home-Country Risk in Your Portfolio
> Your personal real estate, banking relationships, income, and labour market are already concentrated in your home country. The portfolio should be the *diversifier* against that concentration.
> **Check `local/local/INVESTOR_PROFILE.md` §Investment Constraints for home bias exclusions.** Apply them strictly.

> [!NOTE] Stop-Loss Resolution
> The [[docs/RISK_FRAMEWORK]] mandates -3% hard stops for all positions. Use the 2x ATR20 volatility stop as the working stop where it is wider. This is not a relaxation — it uses the framework's own volatility stop mechanism.

[Full risk analysis here]

---

## Phase 8: Challenger Review

*The Challenger agent provides an independent, adversarial assessment of the Strike Team's consensus output. This role is mandatory — it exists to catch groupthink before trades are finalised.*

> [!IMPORTANT] Independence Rule
> The Challenger reads the Phase 2–8 output as a body of evidence and forms its own view. It does NOT attempt to be constructive or supportive — its job is to find the single most dangerous assumption the team is making.

### [Challenger Agent] Assessment

[Challenger's structured output here — using Challenger Output Format from Strike Team Output Standards]

### Orchestrator's Response to Challenge

[Orchestrator's assessment of whether the challenge is valid, partially valid, or addressed. If valid: what changes to the trade plan.]

---

## Orchestrator Conflict Resolution

> [!IMPORTANT] Document ALL conflicts between agents here, with explicit resolution and the key decision taken. This is the audit trail for why the final trades look the way they do.

| Conflict | Agents | Position A | Position B | Resolution | Key Decision |
|---|---|---|---|---|---|
| [e.g. "Position sizing"] | Two Sigma vs GS Architect | [Reduce to 3% NAV] | [Keep at 5% NAV] | [Orchestrator rationale] | [Final decision] |

**Key Decision This Session**: [One sentence — the most important judgement call the orchestrator made, and why.]

---

## Final Strategy Summary

| # | Strategy | Allocation | Core Instruments | Entry Signal | Key Risk Control | Rebalance |
|---|----------|------------|-----------------|-------------|-----------------|-----------|
| 1 | | | | | | |
| 2 | | | | | | |
| 3 | | | | | | |

> [!IMPORTANT] Defined Risk Constraint
> All positions are **long-only**. No shorts, no uncovered options, no CFDs.
> **Max loss = amount invested.** See [[docs/RISK_FRAMEWORK]] §Defined Risk Only.

---

## Exact Trade Instructions

*3 specific, immediately actionable trades. These have passed Full Desk Sign-Off (Phase 9).*

### Trade 1: [ACTION] — [Instrument]

> [!TIP] In Plain English
> [Layman explanation — what you're buying and why, in plain language. No jargon.]

| Field | Detail |
|---|---|
| **Action** | |
| **Instrument** | |
| **ISIN** | |
| **TER** | |
| **Why** | |
| **Allocation** | |
| **Shares to buy** | [X shares @ ~€Y = ~€Z] |
| **Entry** | |
| **Stop-loss** | Hard: [price]. Working vol stop: 2x ATR20 ≈ [price]. Use whichever is wider. |
| **Mental stop (micro-NAV)** | [price / % if applicable] |
| **Max you can lose** | The amount you invest. |

### Trade 2: [ACTION] — [Instrument]

> [!TIP] In Plain English
> [Layman explanation]

| Field | Detail |
|---|---|
| **Action** | |
| **Instrument** | |
| **ISIN** | |
| **TER** | |
| **Why** | |
| **Allocation** | |
| **Shares to buy** | [X shares @ ~€Y = ~€Z] |
| **Entry** | |
| **Stop-loss** | Hard: [price]. Working vol stop: 2x ATR20 ≈ [price]. Use whichever is wider. |
| **Mental stop (micro-NAV)** | [price / % if applicable] |
| **Max you can lose** | The amount you invest. |

### Trade 3: [ACTION] — [Instrument]

> [!TIP] In Plain English
> [Layman explanation]

| Field | Detail |
|---|---|
| **Action** | |
| **Instrument** | |
| **ISIN** | |
| **TER** | |
| **Why** | |
| **Allocation** | |
| **Shares to buy** | [X shares @ ~€Y = ~€Z] |
| **Entry** | |
| **Stop-loss** | Hard: [price]. Working vol stop: 2x ATR20 ≈ [price]. Use whichever is wider. |
| **Mental stop (micro-NAV)** | [price / % if applicable] |
| **Max you can lose** | The amount you invest. |

### Post-Trade Monthly Snapshot

| Position | Ticker | Exchange | % NAV | Stop-Loss | Strategy | Theme |
|---|---|---|---|---|---|---|
| | | | | | | |
| | | | | | | |
| | | | | | | |
| Cash / Short T-Bills | — | — | % | — | Deployment Reserve | |
| **TOTAL** | | | **100%** | | | |

> [!NOTE] Worst-Case Scenario
> If all positions hit stops simultaneously: **[X]% of total NAV**.

### What This Means For You

> [3-4 sentences in plain language — the session-level "so what?" for someone who isn't a quant. Not per-trade (those already have Plain English tips) — this is the overall picture: what you did, why it makes sense given the environment, and what to watch for next month.]

[e.g. "This month you added to your defence position and kept your powder dry on European equities while the Hormuz situation is unresolved. The logic is simple: defence spending is locked in by governments regardless of whether the crisis escalates or de-escalates, so that position works in both scenarios. The gold position continues to act as insurance — if equity markets wobble, gold typically holds or rises. The main thing to watch before next month is whether Brent stays below $100; if it crosses that level you'll get an early warning email from your broker's price alert."]

---

## Phase 9: Full Desk Sign-Off (All 15 Agents)

> [!INFO] Sign-Off Protocol
> After the Strike Team produces the final trades, **every agent on the roster** gets a quick look.
> This is not a deep review — it's a 30-second domain-specific sanity check.
> **Model**: Haiku (cheap, fast — 15 parallel calls)
> **Rule**: If 3+ agents flag the same trade **with unresolved concerns**, it goes back to the Strike Team for redesign.

### Phase 9 Context Brief

> [!IMPORTANT] Phase 7 agents are intentionally kept COLD.
> Do NOT include Strike Team resolutions, Orchestrator synthesis, conflict-resolution outcomes, Challenger assessments, Counter-Regime views, or rationale for chosen-vs-rejected alternatives. The Phase 7 gate only works if the 15 agents are genuinely independent of the synthesis they're reviewing. If an agent re-flags a point the Strike Team already debated, that is acceptable — the 3-flag threshold is what resolves, not pre-loading.

**Session type**: [LIVE / BACKTEST (information cutoff: YYYY-MM-DD)]
**NAV**: €[X] → **Override tier**: [Micro-NAV (<€2,000) / Standard (€2,000–€10,000) / Full (>€10,000)] — see `docs/RISK_FRAMEWORK.md` §Micro-NAV Overrides
**Current holdings** (for coherent N/A judgments): [list tickers + % NAV, one line each]

**Scope instructions for agents**:
- If this is a **BACKTEST session**: Do NOT read `brainstorms/` (live sessions) or `local/PORTFOLIO.md` (live portfolio). All context is provided in this brief and the trade summary below.
- If an agent's speciality is **not applicable** at this NAV/scale (e.g. stat-arb at €400 NAV, execution algos for 1-share trades), reply "N/A — not applicable at current scale" rather than forcing a flag.
- **Flag genuine concerns as you see them.** Do not self-censor because a concern "might already have been debated" — you don't have that context and shouldn't assume it.

### Trade Summary for Sign-Off

[Paste the Final Strategy Summary table and Exact Trade Instructions here]

### Results

| Agent | Verdict | Note |
|---|---|---|
| GS Quant Architect | | |
| Renaissance Backtesting | | |
| Two Sigma Risk | | |
| Citadel Alpha | | |
| Jane Street MM | | |
| AQR Factor Model | | |
| D.E. Shaw StatArb | | |
| Bridgewater Macro | | |
| Bloomberg Data Pipeline | | |
| Virtu Execution | | |
| Point72 ML Alpha | | |
| Man Group Portfolio | | |
| Millennium Live Trading | | |
| Dimensional Backtester | | |
| GS Compliance | | |

**Raw Summary: [X] APPROVE, [Y] FLAG, [Z] N/A.**

### FLAG Categorisation

> [!NOTE] Categorise flags before determining if redesign is needed.
> - **Invalid**: Agent confused context, made factual errors, or read wrong files.
> - **Already resolved**: Concern was debated by Strike Team and documented in context brief.
> - **Legitimate**: New concern not addressed by Strike Team — counts toward the 3-flag threshold.

| Category | Count | Agents |
|---|---|---|
| Invalid | | |
| Already resolved | | |
| Legitimate | | |

**Legitimate flags per trade**:

| Trade | Legitimate Flags | Agents | Threshold (3+)? |
|---|---|---|---|
| [Trade 1] | | | YES / NO |
| [Trade 2] | | | YES / NO |

**FLAG Resolution** (legitimate flags only):

| Flag | Agent | Resolution |
|---|---|---|
| | | |

---

## Comparison to Previous Session

*How has the macro environment changed since last month? What positions are being maintained, added, or exited?*

### Position Changes

| Position from Last Month | Status | Reason |
|---|---|---|
| | HOLD / EXIT / INCREASE / REDUCE | |

### Regime Accuracy Retrospective

> [!NOTE] Compare the previous session's regime classification to what actually happened. This builds an accountability loop for macro calls.

| Question | Answer |
|---|---|
| Previous session regime | [e.g. "Stagflation Active"] |
| What actually happened since then | [e.g. "Gold crashed 12%, STOXX dropped 5.8%, VIX rose to 23.87 — liquidity stress, not pure stagflation"] |
| Was the regime call accurate? | YES / PARTIALLY / NO |
| Did the regime call affect trade selection? | [How — e.g. "led to gold overweight which subsequently crashed"] |
| Lesson for this session | [e.g. "Regime labels should distinguish between stagflation and liquidity stress"] |

### Macro Delta

| Indicator | Last Month | This Month | Change |
|---|---|---|---|
| Regime | | | |
| ECB Rate | | | |
| STOXX 600 | | | |
| Gold | | | |
| VIX | | | |
| EUR/USD | | | |
| Brent | | | |
| BTP-Bund Spread | | | |

### Trade Performance Review

> Track outcomes of closed positions. Running stats build the dataset for future self-improvement (see Staged Improvements in `PROGRESS.md`).

#### Closed Positions Since Last Session

| Position | Entry | Exit | Holding (sessions) | P&L € | P&L % | Thesis Type | Thesis Accurate? | Exit Reason |
|---|---|---|---|---|---|---|---|---|
| [Ticker] | [date] | [date] | [X] | [€X] | [X%] | [type] | YES / PARTIAL / NO | [reason] |

> **Thesis Accurate?** — YES: the thesis played out as expected. PARTIAL: trade was profitable but for different reasons. NO: the thesis was wrong.
> If no positions were closed this session, write "No exits this session" and skip to Running Stats.

#### Running Stats (cumulative — update each session)

| Metric | Value |
|---|---|
| Total trades closed | X |
| Win rate | X% |
| Avg winner | +X% |
| Avg loser | -X% |
| Avg holding period | X sessions |
| Best trade | [Ticker] +X% |
| Worst trade | [Ticker] -X% |
| Thesis accuracy | X% correct |

> First session: all stats will be "N/A — no closed trades yet." The table structure is here for future sessions.

### Next Month Watchlist

> [!IMPORTANT] Deployment Gates — Preview for Next Session
> Update these levels at next session start (Phase 1). They are recorded here as a handoff baseline, not as final verdicts.

| Gate | Level at This Session | Trend | Watch |
|---|---|---|---|
| Strait of Hormuz | | | |
| Brent crude | | | |
| ECB decision | | | |
| US payrolls | | | |
| VIX | | | |
| EUR/USD | | | |
| Tariff severity | | | |
| STOXX 600 vs 50wk MA | | | |

---

## Agent Roster Reference (all 15)

| Agent | Config | Specialty | Best As | Lens |
|---|---|---|---|---|
| GS Quant Architect | `agents/gs_quant_architect.yml` | Strategy design, signal logic, pseudocode | Architect | Institutional strategy structuring |
| Renaissance Backtesting | `agents/renaissance_backtesting.yml` | Backtesting engines, bias prevention | Challenger | Statistical rigour, anti-overfitting |
| Two Sigma Risk | `agents/two_sigma_risk.yml` | Risk management, VaR, stress testing | Risk (fixed) | Tail risk, correlation, drawdown |
| Citadel Alpha | `agents/citadel_alpha.yml` | Alpha signal discovery, feature engineering | Signal | Data-driven signal construction |
| Jane Street MM | `agents/jane_street_mm.yml` | Market making, spread capture, microstructure | Architect | Execution-aware strategy design |
| AQR Factor Model | `agents/aqr_factor_model.yml` | Factor investing, multi-factor portfolios | Macro or Signal | Academic factor decomposition |
| D.E. Shaw StatArb | `agents/de_shaw_statarb.yml` | Pairs trading, cointegration, stat arb | Signal | Statistical relationships, mean-reversion |
| Bridgewater Macro | `agents/bridgewater_macro.yml` | Macro regimes, asset allocation, All-Weather | Macro | Growth/inflation regime framework |
| Bloomberg Data Pipeline | `agents/bloomberg_data_pipeline.yml` | Data engineering, pipelines, feature stores | Challenger | Data quality, pipeline reliability |
| Virtu Execution | `agents/virtu_execution.yml` | Execution algos, TWAP/VWAP, slippage | Challenger | Execution cost, slippage analysis |
| Point72 ML Alpha | `agents/point72_ml_alpha.yml` | ML-based signals, XGBoost, neural nets | Signal | ML-driven pattern detection |
| Man Group Portfolio | `agents/man_group_portfolio.yml` | Portfolio optimisation, risk parity, HRP | Macro or Architect | Portfolio construction, trend-following |
| Millennium Live Trading | `agents/millennium_live_trading.yml` | Live systems, broker APIs, kill switches | Challenger | Operational risk, system resilience |
| Dimensional Backtester | `agents/dimensional_factor_backtester.yml` | Academic factor backtesting, tear sheets | Challenger | Academic evidence, factor premia |
| GS Compliance | `agents/gs_compliance.yml` | MiFID II, MAR, regulatory controls | Challenger | Regulatory surface, FTT, reporting |

---

## Future Enhancement: MCP Elicitation Checkpoints

> **Status**: Not yet implementable. MCP Elicitation requires an MCP server configuration not yet in place. Review at each session whether the feature is stable on Claude Pro. When ready, convert these into structured pause points in the War Room flow.

When available, the following checkpoints would replace manual pre-population and web searches:

| Phase | Elicitation Question | Why |
|---|---|---|
| **Phase 0** | "Have any of your GTC stop-losses been triggered since your last session on [date]?" | Ensures local/PORTFOLIO.md is current before proceeding |
| **Phase 0** | "Current levels for deployment gates: Brent crude, VIX, ECB rate?" | Hard data the model cannot reliably infer from training data |
| **Phase 6** | "Can you confirm the entry price and current GTC status for [existing position] before I recommend adding to it?" | Prevents stale cost basis errors |

---

## Execution Log

> Updated after trades are placed. The authoritative record of what was actually executed vs what was proposed.

| Date | Action | Instrument | ISIN | Shares | Entry Price | Total Cost | Broker | Notes |
|---|---|---|---|---|---|---|---|---|
| [YYYY-MM-DD] | BUY / SELL | [Name] | [ISIN] | [X] | €[Y] | €[Z] | IBKR | [e.g. "Filled at open, 09:05 CET"] |

> If trades are pending execution at session close, mark as "PENDING" and update when filled.

---

## Session Close Checklist

> [!IMPORTANT] Complete ALL items before ending the session. This replaces the former `/commemorate` step.

- [ ] All framework/doc changes approved by user before implementation
- [ ] `PROGRESS.md` updated with session outcomes and decisions
- [ ] `local/PORTFOLIO.md` updated with any trades to be executed (or marked pending)
- [ ] `local/ROTATION_LOG.md` updated with this session's Strike Team
- [ ] Handoff section below is complete
- [ ] Session file passes the section checklist in `CLAUDE.md`
- [ ] Any new `MEMORY.md` entries written for decisions that should persist across conversations

---

## Handoff to Next Session

> [!IMPORTANT] Carry-Forward Brief
> Fill this at session end. The next session reads ONLY this section + `local/PORTFOLIO.md` + `ROTATION_LOG.md` — NOT the full previous session file. Make this brief comprehensive enough to stand alone.

### Session Scorecard

#### (a) Process Compliance
| Metric | Value | Notes |
|---|---|---|
| Gate Score | X/8 GREEN, Y/8 AMBER, Z/8 RED | From deployment gate table |
| Regime Confidence | HIGH / MEDIUM / LOW | Macro agent's self-assessed confidence |
| Deployment Efficiency | X% of available capital deployed | Deployed ÷ (NAV − cash floor) |
| Thesis Diversity | X thesis types represented | Count distinct types from valid taxonomy (including escape-hatch entries) |
| Process Compliance | X/12 checklist items passed | From Protocol Audit (SKILL.md Phase 3) |
| Framework Diversity | X distinct frameworks on Strike Team | From agent YAML `analytical_framework` fields |

#### (b) Ex-Post Outcome Metrics *(fill at next session)*
| Metric | Value | Notes |
|---|---|---|
| Regime-call accuracy (T+30) | CORRECT / PARTIAL / WRONG | Did the classified regime hold for the following month? |
| Trade IRR vs benchmark (T+90) | +X% vs benchmark | Annualised IRR of this session's trades vs STOXX 600; fill at T+90 |
| Phase 7 FLAG resolution rate | X of Y flags resolved correctly | Flags raised in Phase 7 that turned out to be warranted vs noise |

> **Rule origin tagging**: Any new rule adopted from this session's retrospective must be tagged `(origin: session #N, evidence: X observations)` below. Rules are eligible for promotion to canon only after N≥10 observations confirm they hold.

#### New Rules Adopted This Session
<!-- Format: "Rule text." (origin: session #N, evidence: X observations) -->
<!-- None yet — add any rules surfaced in this session's retrospective here. -->
[none — or list rules below]

### Compressed Session Summary (~5 lines)

- **Regime**: [classification]
- **Trades**: [list trades executed or "no trades"]
- **Key decision**: [1 sentence — what the session decided and why]
- **NAV**: €[X] (cash [Y]%, invested [Z]%)
- **Gate status**: [X GREEN, Y AMBER, Z RED]

### Open Issues to Monitor
- [e.g. "July 9 tariff pause expiry — review IWDA.AS thesis if truce collapses"]

### Positions to Watch
- [e.g. "DFNS.PA approaching -8% mental trigger at current trajectory"]

### Positions in THESIS REVIEW
- [e.g. "IQQH — original rate-cut thesis invalidated. Grandfathered until Oct 2026. Must re-propose or exit."]

### Expiring Catalysts
- [e.g. "US-China 90-day tariff pause expires July 9"]

### Next Session Rotation
- Agents who MUST rotate out (hit 2-session consecutive limit): [names]
- Suggested replacements: [names with rationale]

### Concept of the Month

> One paragraph explaining the financial concept most central to this session's decisions, in plain language. Examples: value traps, concentration caps, VIX and volatility regimes, mean-reversion vs momentum, decorrelation. Builds financial literacy incrementally — one concept per session.

[e.g. "**Deployment gates** are a pre-commitment device: a checklist of market conditions you agree to check *before* deploying cash, so that fear or excitement in the moment can't override the plan. Each gate represents a measurable external condition (oil price, volatility index, interest rate) that, if breached, signals the environment is too unstable for new positions. The three-tier system (GREEN / AMBER / RED) avoids binary paralysis — AMBER lets you deploy at half rate, acknowledging that uncertainty is normal but shouldn't stop you entirely. The key insight is that the gates aren't predictions; they're guardrails. You don't need to forecast whether oil will hit $100 — you just agree in advance what you'll do if it does."]

---

## Session Scheduling

> **Recommended cadence**: Monthly, on the **third Saturday of each month** (typically 17th–21st). This ensures:
> - After US Non-Farm Payrolls (1st Friday) ✓
> - After US CPI release (~12th–15th) ✓
> - After ECB/central bank rate decision (when applicable) ✓
> - Weekend — markets closed, time to read and plan ✓
> - 10+ days before month-end for trade execution ✓
>
> **Exception**: If the central bank decision falls after the third Saturday, defer to the following Saturday.
>
> **Irregular contributors**: Run a session whenever you make a contribution, or at least once per quarter — whichever comes first. If more than 45 days have passed since the last session, the Session Staleness Check will trigger automatically.

**Next session date**: [YYYY-MM-DD (third Saturday)]
**Relevant events before next session**: [e.g. "ECB meeting Apr 17, US CPI Apr 15, NFP May 1"]

---

## End-of-Month Mark

> Filled at month-end (last calendar day), not at session time. Captures where positions closed for the month — useful for performance tracking and tax records.

**Mark date**: [YYYY-MM-DD]
**NAV at month-end**: €[X] (contributed: €[X], market move: €[+/-X])

| Position | Ticker | Entry Price | Month-End Price | Month P&L % | Cumulative P&L % | % NAV |
|---|---|---|---|---|---|---|
| [Name] | [Ticker] | €[X] | €[X] | [+/-X%] | [+/-X%] | [X%] |
| Cash | — | — | — | ECB rate / 12 | — | [X%] |

**Month-end notes**: [Any dividends received, corporate actions, price alerts triggered]

---

## Changelog
- YYYY-MM-DD: Initial brainstorm
