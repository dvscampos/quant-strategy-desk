# 12-Month Backtest Post-Mortem Brief

> Written after BT #12 completion (Feb 2026). This file captures all questions and topics for the post-mortem analysis.
> The user will be following the post-mortem's recommendations for live investing. Stakes are real.

## Backtest Summary

- **Period**: March 2025 → February 2026 (12 monthly sessions)
- **Contributions**: €2,400 (€200/month)
- **Final NAV**: €2,661.07 (+10.9%)
- **Invested return**: +15.4% on deployed capital
- **Positions**: 5 (IWDA, IS3N, DFNS, PPFB, IQQH) — all in profit
- **One exit**: EXSA.DE (BT #10, +7.3% realised)
- **Cash**: 30.2% at close — never below 30%
- **Deployment efficiency**: 66.5% (€1,597 of €2,400 deployed)

## User Questions (analyse, challenge, counterpropose — do NOT just answer)

### 1. Phase 7 Haiku Agent Execution Inconsistency
In some sessions, Haiku agents were launched as standalone Agent() calls. In others, they were run inline in batches (orchestrator pretending to be them). Which approach is correct? This is separate from the question of whether Phase 7 is useful at all.

### 2. Haiku Agent Performance Since Enrichment
After we gave Phase 7 agents richer context briefs (BT #7 onwards), did their signal quality improve? Data: 1 legitimate flag in ~155 verdicts. Is Phase 7 worth the token cost?

### 3. Rotation Rules — Simultaneous Cycling
Should all 4 rotating roles be allowed to cycle out in the same session? Could this lead to a scenario where 4 agents hit 2 consecutive and must ALL rotate simultaneously, leaving no continuity? Check if this happened or nearly happened.

### 4. Session Continuity — Carry-Forward Mechanism
Currently each session reads the entire previous session file. Alternative: the previous session writes carry-forward info into the next month's session file (a skeleton). Which is better? What are the trade-offs?

### 5. Cash Floor (30%) — Overhaul Needed?
The 30% cash floor was never the user's idea — it was the system's recommendation. After 12 sessions, cash never dropped below 30%. Cumulative deployment was only 66.5%. Is this a feature or a bug? Options: lower to 20%, tier it by NAV, remove it, or keep it. Must be justified by performance impact.

### 6. AMBER Gate Definitions
During BT #12, AQR classified 3 gates as AMBER while the orchestrator kept them GREEN (because gate thresholds are binary). Are the current gate definitions too coarse? Should there be a formal AMBER tier between GREEN and RED? What would the thresholds be?

### 7. Fractional Shares (IBKR)
User will likely open IBKR account where fractional shares are available. How would this have affected the backtest? Specifically: IWDA cap deadlock (couldn't add because 1 share exceeded headroom), IS3N sizing, overall deployment efficiency.

### 8. ETF-Only Portfolio — By Design or Bias?
All 6 positions (including exited EXSA) were ETFs. Was this deliberate, emergent from the process, or bias? Consider: tax efficiency for Portugal, diversification, available instruments, risk framework constraints, agent YAML prompts.

### 9. Target Allocation Percentages
What established the target % for each position (IWDA 25%, IS3N 15-20%, DFNS 10%, PPFB 10%, IQQH 10%, Cash 20-25%)? Were these explicitly decided or did they emerge? Are they appropriate going forward?

### 10. yfinance API Error
BT #12 had a Python error: `TypeError: unsupported format string passed to Series.__format__`. This is a yfinance/pandas API change where `Close` returns a Series not a scalar. Needs a permanent fix in the data fetching code or skill.

### 11. Context Efficiency — Did Mid-BT Changes Help?
Changes were made around BT #7-#8 to reduce context size (skeleton rewrite, compact instructions). Previously 2-3 sessions fit in one quota. Now can't finish one session. Is this due to Anthropic quota reductions, context growth, or both? Review the changes and evaluate.

### 12. BT #11 Improvements — Did They Help BT #12?
BT #11 introduced: Position Age & Thesis Tracker, Target vs Actual Allocation, Deployment Efficiency metric, "What This Means For You" section, Concept of the Month. Did these add value in BT #12?

## Orchestrator Observations (not raised by user — add to analysis)

### 13. Agent Factual Errors in Strike Team
In BT #12, both D.E. Shaw and GS Architect referred to IQQH.DE as a "clean energy" ETF. It is a property yield ETF (IE00B1FZS350). This is a factual error in two independent Sonnet agents. Are agent YAML prompts specific enough? Should Strike Team agents receive the current holdings table with ISINs and descriptions, not just tickers?

### 14. Thesis Drift vs Thesis Reframing
IQQH was entered as a "rate play on ECB cuts" (BT #5). By BT #11, the ECB had held 5 times and cuts were priced out. The thesis was "reframed" to "underweight correction." Is this genuine adaptation or post-hoc rationalisation of a position that should have been exited? The process has no formal mechanism to distinguish reframing from drift. Should there be a rule like: "if the original thesis is invalidated, the position must be exited or re-proposed from scratch"?

### 15. No Profit-Taking / Rebalancing Rules
PPFB reached +49.9% and was never trimmed. The framework has stop-losses (downside protection) but zero take-profit or rebalancing triggers. For a portfolio that explicitly targets allocation percentages, the absence of a sell discipline when positions appreciate past their target weight is a gap.

### 16. Position Count Stagnation
The portfolio has been exactly 5 positions since BT #5 (July 2025) — 8 consecutive sessions with no new instrument added. One instrument was exited (EXSA, BT #10) but nothing replaced it. Is there a structural bias against adding new positions? Are the constraints (cash floor, cap, budget) creating a portfolio that can only add to existing positions?

### 17. Benchmark Comparison — Results

Computed post-BT #12 via `backtesting/benchmark_comparison.py` (live yfinance prices, same session dates and contribution cadence).

| Strategy | Final NAV | TWR |
|---|---|---|
| Portfolio (actual) | €2,661.07 | **+10.9%** |
| Portfolio + tiered floor (modelled) | €2,693.70 | **+12.2%** |
| IWDA DCA (pure MSCI World, no floor) | €2,615.93 | +9.0% |
| S&P 500 EUR DCA (SXR8.DE, XETRA) | €2,565.27 | +6.9% |

**The portfolio beat both benchmarks**: +1.9pp over IWDA DCA, +4.0pp over S&P 500 EUR DCA. Gold (PPFB.DE, +49.9%) was the decisive driver — the multi-position strategy paid off specifically because it included a decorrelated asset that neither benchmark holds.

**Cash floor impact**: The tiered floor (€200 absolute for Micro-NAV, 15% for Standard NAV ≥ €2,000) adds only +1.3pp (+€33 net gain). The cascade model shows only €420 in additional IWDA deployment is possible across sessions 4–9 before the adjusted cash falls below even the 15% floor in sessions 10–12. The tariff shock in April 2025 partially vindicated the conservative cash position: gates blocked equity deployment at VIX 60, preserving capital that was deployed into the recovery. The cost of the floor was structural (psychological drag of 33% idle cash) more than it was financial.

**Questions for post-mortem analysis**: (a) Would the portfolio still have outperformed if gold had not run +49.9%? Strip PPFB returns and recompute. (b) The S&P 500 was significantly impacted by tariff shock; a pre-shock comparison might show a different picture. (c) The IWDA benchmark is unhedged — EUR/USD headwind affected both IWDA DCA and the portfolio's IWDA holding equally, so this comparison is internally consistent.

### 18. Exit Framework Too Passive?
One exit in 12 months. EXSA took 4 sessions of underperformance before being exited. Mental stops were never triggered. Is the exit framework adequate for live trading where losses are real? Should there be automated alerts, formal thesis review triggers, or time-based exit reviews?

### 19. War Room Token Cost vs Value
Each War Room session consumes 80-120k tokens. Over 12 sessions that's ~1M+ tokens. The output is typically 1-2 small trades within a severely constrained budget. Is the full 7-phase process justified at this NAV, or should there be a "light mode" for sessions where constraints make the outcome near-predetermined?

### 20. Macro Regime Classification Accuracy
Each session classified a regime (e.g., "Deflationary Shock," "Risk-On Expansion"). Were these classifications accurate in hindsight? Did they inform trade selection or were they decorative? Could the trades have been the same without the macro analysis?

## Post-Mortem Process

The user wants:
1. **Independent analysis** by the orchestrator (read all 12 sessions, compute metrics, identify patterns)
2. **Independent Strike Team review** (agents analyse the same data separately)
3. **Orchestrator devises improvement plan**
4. **Challenger reviews the plan**
5. **If all sign off, changes are implemented**

The output should be actionable changes to: CLAUDE.md, AGENTS.md, _TEMPLATE.md, RISK_FRAMEWORK.md, agent YAMLs, rotation rules, gate definitions, and any new files needed.

## Key Files to Read

- All 12 session files: `backtesting/sessions/2025-03.md` through `2026-02.md`
- `backtesting/PORTFOLIO_HISTORY.md` — full performance dashboard
- `backtesting/AGENT_PERFORMANCE.md` — Phase 7 verdict history
- `backtesting/ROTATION_LOG.md` — Strike Team rotation history
- `CLAUDE.md` — current rules and template compliance checklist
- `AGENTS.md` — current governance and rotation rules
- `brainstorms/_TEMPLATE.md` — current War Room template
- `docs/RISK_FRAMEWORK.md` — current risk rules including cash floor

---

## Gate Replay Findings

> Added: Proposal 003 Phase 1B execution (2026-04-25).
> Full divergence log: `backtesting/REPLAY_DELTA.md`
> Archive copy: `backtesting/archive/REPLAY_DELTA-2026-04-25.md` (at proposal close)

### Summary

12 BT sessions replayed through `gate_eval` using synthetic vintage snapshots
(`local/snapshots/backtest/BT-01..BT-12.json`). Values sourced from BT session files.
ALFRED/SDW as-of queries deferred to live credentials (target: 2026-05-16, DoD #10b).

| Metric | Result |
|---|---|
| Sessions replayed | 12 |
| Zero divergence | 1 (BT-04, June 2025 — clean GREEN all gates) |
| Acceptable divergences | 11 |
| Unexplained divergences | 0 |
| BUG classifications | 0 |

### Divergence categories

| Category | Count | Sessions |
|---|---|---|
| `threshold_drift` | 8 | BT-01, BT-02, BT-03, BT-05, BT-06, BT-07, BT-08, BT-12 |
| `gates_yml_version` | 2 | BT-10, BT-11 (EUR/USD reclassification) |
| `threshold_drift` + `gates_yml_version` | 1 | BT-09 (amber_count_escalation tightened) |
| No divergence | 1 | BT-04 |

### Key finding

The v1.0 era (BT-01 through BT-05) lacked the AMBER tier entirely. Under v2.0 thresholds,
5 of those 6 sessions would have been RED or AMBER — vs full deployment at the time. This
confirms the post-mortem's recommendation (Q6) to introduce AMBER gates was structurally
correct: the v1.0 system was over-deploying relative to macro conditions.

The EUR/USD reclassification (categorical → numeric, v2.0) caused a tier change in BT-10
and BT-11. Under current thresholds, BT-11 would have been RED (EUR/USD < 1.05) vs AMBER
in the original session. This suggests the reclassification correctly tightened the EUR/USD
exposure signal for Portugal-based EUR investors.

### Process note

Vintage snapshot authenticity: these are synthetic fixtures from BT session file values.
ALFRED/SDW vintage queries (DoD #10b) will provide true as-of data on 2026-05-16.
If real vintages diverge materially from these fixtures, REPLAY_DELTA.md will be updated.
Zero BUG classifications currently — if real-vintage replay surfaces BUG items, proposal
close is blocked pending fixes.
