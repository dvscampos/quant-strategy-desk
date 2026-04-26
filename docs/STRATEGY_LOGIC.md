# Strategy Logic — Business Rules & Standards

> Replaces `SHARED_LOGIC.md` from the reference project. Defines the rules every strategy, signal, and backtest must follow.

## Asset-Class Target Framework

> **Post-mortem decision**: Targets are expressed as generic asset classes, not specific tickers. The War Room decides which instruments fill each slot.
> Specific percentage targets are set at the first live War Room session and reviewed annually.

| Asset Class | Role | Range | Notes |
|---|---|---|---|
| Global equity core | Portfolio foundation — broad developed-market exposure | 20–30% | DCA anchor. Cap per individual position: 25% NAV. |
| Emerging markets | Factor diversification — value, size, growth premium | 10–20% | Monitor correlation with global equity core (r > 0.80 triggers alert) |
| Thematic / sector | Targeted structural or cyclical exposure | 5–15% per theme | Max 2 concurrent themes. Each must have a named thesis from the valid types. |
| Decorrelator | Portfolio insurance — negative or zero equity correlation | 5–15% | Must demonstrate r < 0.20 to equity positions over trailing 1-year daily data. |
| Alternative / yield | Income diversification or non-equity factor exposure | 0–15% | Optional. Thesis must stand independently, not just "filling a gap." |
| Cash | Deployment reserve and drawdown buffer | Per tiered floor | See `RISK_FRAMEWORK.md` §Cash Floor. |

> **Constraint**: Total equity-correlated exposure (global equity + EM + thematic with equity beta > 0.5) should not exceed 65% of NAV. Decorrelator + cash should always total at least 20%.

---

## Investor Profile & Operating Cadence

> **This is a monthly-review, long-hold portfolio.** The investor places trades once per month during the War Room session and does not actively monitor positions between sessions.

### Holding Period Rules
| Rule | Constraint |
|---|---|
| Minimum intended hold | 1 month |
| Rebalancing frequency | Monthly (at War Room session) |
| Intraday trading | **Prohibited** |
| Daily monitoring required | **No** — automated alerts handle exit triggers |

### Prohibited Strategy Types
These do not fit the monthly cadence and must not be proposed:
- Day trading or scalping
- High-frequency market making
- Strategies requiring intraday parameter adjustment
- Any strategy that demands daily manual intervention

### Instrument Universe
- **Primary**: European equities and ETFs (Euronext, XETRA, LSE, SIX, BME)
- **Secondary**: Global equities and ETFs — permitted when they offer clearly superior risk-adjusted returns
- **Hard requirement**: Must be accessible on IBKR, Degiro, Trading212, or XTB from a European account
- **Preference, not restriction**: Do not force a weaker European pick when a better global alternative exists

### Exit Alert System *(future implementation — see PROGRESS.md backlog)*
Since the investor does not watch positions between monthly sessions, an automated alert system will notify them if any exit trigger fires:
- Stop-loss breached
- Kill switch condition met (see `docs/RISK_FRAMEWORK.md`)
- Dividend cut or suspension (for quality/defensive positions)
- Macro regime shift trigger (e.g., BTP-Bund spread exceeding threshold)

> Until the alert system is built, the investor should set broker-level stop-loss orders and price alerts at trade entry.

---

## Signal Generation Standards

### Signal Categories
| Category | Description | Example |
|---|---|---|
| **Momentum** | Trend-following based on price/volume patterns | 12-1 month cross-sectional momentum |
| **Value** | Mean-reversion to fundamental value | P/E, P/B, EV/EBITDA relative to sector |
| **Quality** | Profitability and balance sheet health | ROE, gross margin stability, low leverage |
| **Macro** | Economic regime-driven allocation | Yield curve slope, PMI, inflation surprises |
| **Statistical** | Pure price-based statistical relationships | Pairs cointegration, z-score mean reversion |
| **Sentiment** | Alternative data and market positioning | Put/call ratio, fund flows, news sentiment |

### Signal Validation Pipeline
Every signal must pass through these gates before entering a strategy:

1. **Hypothesis** — Why should this signal work? Economic rationale required.
2. **In-Sample Test** — Backtest on training data (minimum 5 years for daily, 10 years for monthly).
3. **Out-of-Sample Test** — Walk-forward validation on unseen data (minimum 2 years).
4. **Transaction Cost Survival** — Does alpha survive after commissions, slippage, and bid-ask?
5. **Decay Analysis** — Signal half-life. How quickly does predictive power fade?
6. **Correlation Check** — Is this signal genuinely new or a repackaged known factor?
7. **Regime Robustness** — Does it work in bull, bear, and sideways markets?

### Signal Naming Convention
```
{category}_{description}_{timeframe}
```
Examples: `mom_12m_xsectional`, `val_pe_sector_relative`, `macro_yield_curve_slope`

---

## Backtesting Standards

### Mandatory Requirements
- **Minimum history**: 5 years daily data, 10 years monthly data
- **Walk-forward**: Rolling 3-year train / 1-year test windows
- **Transaction costs**: Include broker commissions + estimated slippage + bid-ask spread
- **Survivorship bias**: Use point-in-time constituent lists (not current index members)
- **Lookahead bias**: No future data in any calculation — enforce programmatically
- **Benchmark**: Strategy must be compared against a relevant benchmark (e.g., STOXX 600 for European equities)

### Required Metrics
| Metric | Minimum Threshold | Notes |
|---|---|---|
| Sharpe Ratio | > 0.5 (net of costs) | Annualised, excess over risk-free |
| Sortino Ratio | > 0.7 | Penalises downside only |
| Max Drawdown | < 25% | Hard limit; strategy halted if breached |
| Win Rate | > 45% | For systematic strategies |
| Profit Factor | > 1.3 | Gross profits / gross losses |
| t-statistic | > 2.0 | Statistical significance of returns |

### Anti-Overfitting Checklist
- [ ] Used walk-forward, not single in-sample period
- [ ] Strategy has ≤ 5 free parameters
- [ ] Tested sensitivity to ±20% parameter changes
- [ ] Monte Carlo simulation run (1000+ iterations)
- [ ] Results robust across 3+ sub-periods
- [ ] Out-of-sample performance within 30% of in-sample

---

## Position Sizing Rules

> ⛔ **Cardinal Rule**: All positions must have **defined, limited risk**. No instrument or position may expose the portfolio to losses exceeding capital invested. See `docs/RISK_FRAMEWORK.md` §Defined Risk Only. No naked shorts. No uncovered options. No exceptions.

### Default Framework: Fractional Kelly
```
f* = (edge / odds) × kelly_fraction
kelly_fraction = 0.25  # Quarter-Kelly for safety
max_position = 0.05    # Never >5% of portfolio in one name
```

### Position Limits
| Level | Limit | Enforcement |
|---|---|---|
| Single position | ≤ 5% of NAV | Hard — automated |
| Sector exposure | ≤ 20% of NAV | Hard — automated |
| Country exposure | ≤ 30% of NAV | Soft — alert + review |
| Strategy allocation | ≤ 40% of NAV | Hard — automated |
| Cash minimum | Per `config/gates.yml` → `cash_floor.tiers` (NAV-tiered: 15% Standard, 10% Scaled, user-defined Micro) | Soft — alert when breached |

---

## Strategy Lifecycle

```
RESEARCH → BACKTEST → PAPER_TRADE → LIVE_PILOT → LIVE_FULL → MONITOR → RETIRE
```

| Stage | Duration | Exit Criteria |
|---|---|---|
| Research | Variable | Signal passes 7-gate validation |
| Backtest | 1–2 weeks | Metrics exceed thresholds; anti-overfitting checklist passes |
| Paper Trade | Minimum 4 weeks | Live results within 30% of backtest; no system bugs |
| Live Pilot | 4–8 weeks | 10% of target capital; stable execution |
| Live Full | Ongoing | Full capital allocation |
| Monitor | Ongoing | Monthly review; edge decay check |
| Retire | — | Triggered by drawdown breach, edge decay, or regime shift |
