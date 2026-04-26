# Risk Framework — Limits, Controls & Monitoring

> Owned by Persona D (Risk Officer). Every strategy and portfolio decision must comply with this framework.

## Risk Hierarchy

```
Portfolio Risk → Strategy Risk → Position Risk → Execution Risk
```

Each level has independent controls. A breach at any level triggers escalation.

---

## ⛔ Defined Risk Only — Cardinal Rule

> **You must never be in a position where you can lose more than the capital you have invested.**

This is the highest-priority constraint in the entire framework. It overrides all other rules.

### Prohibited
| Instrument / Action | Why Prohibited |
|---|---|
| **Naked short selling** | Theoretically unlimited loss if the stock rises |
| **Uncovered call options (selling)** | Unlimited loss if underlying rises |
| **Uncovered put options (selling)** | Loss up to full strike price × 100 per contract |
| **CFDs with unlimited loss** | Margin calls can exceed deposited capital |
| **Any margin position where broker can demand more than NAV** | Could result in negative account balance |

### Permitted (defined risk only)
| Instrument / Action | Max Loss |
|---|---|
| **Buying stocks (long)** | Limited to amount invested (stock goes to €0) |
| **Buying ETFs (long)** | Limited to amount invested |
| **Buying put options** | Limited to premium paid |
| **Buying call options** | Limited to premium paid |
| **Inverse ETFs** | Limited to amount invested (no margin) |
| **Covered call writing** | Opportunity cost only (you own the shares) |
| **Cash-secured puts** | Limited to strike price minus premium (cash reserved) |

### Enforcement
- **Pre-trade check**: Every order must pass a `max_loss_check()` before submission. If `potential_loss > capital_invested`, the order is **rejected**.
- **Broker config**: Ensure IBKR account is set to **"No naked short selling"** permission. Do not enable margin beyond Reg-T (or EU equivalent) minimums.
- **Audit**: Weekly check that no position can produce a margin call exceeding available cash.

---

## Portfolio-Level Controls

### Maximum Drawdown
| Threshold | Action |
|---|---|
| -5% from peak | ⚠️ Alert. Review all positions. |
| -10% from peak | 🟡 Reduce all positions by 50%. Mandatory Risk Officer review. |
| -15% from peak | 🔴 Halt all trading. Flatten to cash. User approval required to resume. |
| -20% from peak | 🛑 Kill switch. Full liquidation. Post-mortem before any resumption. |

### Leverage Limits
| Metric | Limit |
|---|---|
| Gross leverage | ≤ 1.0x NAV (no margin; defined risk only) |
| Net exposure | 0x to +1.0x NAV (long-only; no short positions) |
| Margin utilisation | ≤ 0% (no margin trading) |

### Cash Floor (Tiered by NAV)

> A flat percentage cash floor creates disproportionate performance drag at smaller NAV levels. This tiered system balances deployment efficiency against optionality preservation.

Tier boundaries and floor percentages are held in `config/gates.yml` → `cash_floor.tiers`. Do not duplicate values here.

| Tier | Rationale |
|---|---|
| Micro-NAV | Lot-size constraints make percentage floors meaningless at this scale. Floor set at onboarding (see `local/INVESTOR_PROFILE.md` §Investment Constraints). |
| Standard | Positions are diversified enough for a lower floor. |
| Scaled | Portfolio resilience comes from diversification, not cash. |

The cash floor is a **deployment constraint**, not a risk control. Risk is controlled by stop-losses, drawdown thresholds, and deployment gates. The floor exists to preserve optionality (buying power during drawdowns), not to limit losses.

> **Interaction with AMBER gates**: When deployment gates are AMBER, deployment is halved. This naturally conserves cash during elevated volatility without artificially inflating the floor. The two mechanisms are complementary, not redundant.

### Concentration Alert

| Trigger | Action |
|---|---|
| Any single position exceeds 25% of NAV | Mandatory Challenger review at next War Room. Document whether the overweight is deliberate or drift. |
| Any two positions with r > 0.80 exceed 40% combined NAV | Alert. Review correlation thesis. Block further adds to either position until combined weight is reduced or correlation is reassessed. |

> **Correlation measurement**: Calculate using 1-year daily returns from yfinance at session start. This is a pre-session data pull, not a rolling in-session calculation. Document the correlation matrix in Phase 4 of the session file.

### Correlation Monitoring
- Calculate 1-year daily return correlations via yfinance at session start (pre-session data pull)
- **Alert** when any pair of "uncorrelated" strategies exceeds ρ = 0.6
- **Alert** when any pair of positions exceeds ρ = 0.80 and combined NAV weight > 40%
- **Block new positions** when average portfolio correlation exceeds 0.5
- During crisis regimes: assume all correlations approach 1.0

---

## Strategy-Level Controls

### Per-Strategy Limits
| Metric | Default Limit | Override Requires |
|---|---|---|
| Max allocation | 40% of NAV | User + Risk Officer approval |
| Max drawdown | 15% of strategy capital | Auto-halt; PROPOSE to resume |
| Daily loss limit | 2% of strategy capital | Auto-halt for the day |
| Monthly loss limit | 5% of strategy capital | Auto-halt; mandatory review |

### Edge Decay Detection
Monitor these monthly:
- Rolling 6-month Sharpe ratio vs. backtest expectation
- Information coefficient trend line
- Hit rate moving average

**Trigger**: If rolling Sharpe drops below 50% of backtest Sharpe for 3 consecutive months → strategy enters REVIEW status.

---

## Position-Level Controls

### Stop-Loss Framework

Instrument-specific stop-losses account for the fact that a flat -3% hard stop fires on daily noise for equity ETFs at VIX 18+. Use the appropriate rule for each instrument type:

| Type | Rule | Application |
|---|---|---|
| **Hard floor** | -3% from entry | Minimum for ALL positions. Non-negotiable. |
| **ETF working stop** | Wider of -3% or (Entry − 2 × ATR₂₀) | Equity/defence/sector ETFs. Avoids noise-firing. |
| **Single stock stop** | -8% to -12% from entry | Individual equities (wider range due to higher vol) |
| **Commodity ETC stop** | -3% from entry | Gold, commodities — lower vol means -3% is a genuine signal |
| **Trailing stop** | Peak − (1.5 × ATR₂₀) | Activated after position is +7% to +10%. Applies to all. |
| **Time stop** | Close if flat after 20 trading days | Mean-reversion strategies only |

> **How to set on IBKR**: Use GTC (Good Till Cancelled) orders. Set the hard floor OR the vol stop — whichever is wider — immediately at entry. Set trailing stops manually once the activation threshold is reached, or review at the monthly War Room.

### Position Sizing Algorithm (Fractional Kelly)
```python
def position_size(edge, win_rate, avg_win, avg_loss, kelly_fraction=0.25):
    """Quarter-Kelly position sizing."""
    odds = avg_win / abs(avg_loss)
    kelly = (win_rate * odds - (1 - win_rate)) / odds
    kelly = max(0, kelly)  # Never negative
    size = kelly * kelly_fraction
    return min(size, 0.05)  # Cap at 5% of NAV
```

---

## Value at Risk (VaR)

### Calculation Methods
1. **Historical VaR**: Rolling 252-day window, percentile method
2. **Parametric VaR**: Assume normal distribution, μ ± zσ
3. **Monte Carlo VaR**: 10,000 simulated paths

### Confidence Levels
| Confidence | Use Case |
|---|---|
| 95% VaR | Daily monitoring, internal risk budget |
| 99% VaR | Stress testing, regulatory reporting |
| 99.9% VaR | Capital reserve calculation |

---

## Stress Testing Scenarios

Run monthly against the full portfolio:

| Scenario | Description | Expected Impact |
|---|---|---|
| 2008 GFC | Equities -50%, credit spreads +500bps, VIX 80 | Measure; must survive |
| 2020 COVID crash | Equities -35% in 4 weeks, then V-recovery | Measure drawdown path |
| Flash crash | -10% in 30 minutes, full recovery in 2 hours | Test kill switch speed |
| ECB surprise | -3% equities, 50bps rate shock, EUR ±3% | Quantify macro sensitivity |
| Sovereign crisis | Peripheral spreads +300bps, EUR -5% | Test country exposure caps |
| Correlation breakdown | All correlations → 0.9 for 30 days | Test diversification assumptions |

---

## Monthly Risk Dashboard (War Room Phase 4)

Check at each War Room session during the Risk Stress Test:

- [ ] Portfolio NAV and change since last session
- [ ] Current drawdown from peak
- [ ] Gross and net exposure
- [ ] Top positions by size (% NAV each)
- [ ] Equity-correlated exposure vs 65% cap
- [ ] VaR (95% and 99%)
- [ ] Any stop-loss triggers since last session
- [ ] Correlation matrix — any r > 0.80 pairs exceeding 40% combined NAV?
- [ ] Stop-loss proximity — which position is closest to its trigger?

---

## Micro-NAV Overrides (NAV < €2,000)

At micro-NAV levels (below €2,000), minimum lot sizes on European exchanges make strict compliance with the standard rules physically impossible — a single share of most ETFs costs €40–110, which exceeds the 5% position cap at €400 NAV. The overrides below apply automatically based on the current NAV tier. Phase 7 sign-off agents must check the NAV tier before applying position sizing rules.

### Position Sizing Override

| Standard Rule | Problem at Micro-NAV | Override |
|---|---|---|
| 5% max per position (Quarter-Kelly) | At €400 NAV, 5% = €20. No European ETF/ETC costs €20/share. | **Replace with: 2% max-loss-per-position budget.** At €400 NAV, max acceptable loss per new position = €8. This permits positions up to €80 notional with a 10% stop, or €160 with a 5% stop. |
| 40% max per strategy | At micro-NAV, a single ETF share can exceed 25% of NAV. | **Accept lot-size-driven concentration.** Cap at 2 positions per theme. Document the forced overweight in the session file. |
| Fractional Kelly algorithm | Requires edge/win-rate estimates that are meaningless for discretionary macro at <5 trades | **Use minimum-lot heuristic instead.** Deploy whole shares only; accept that the resulting allocation is driven by share price, not Kelly optimisation. |

### Stop-Loss Override

| Standard Rule | Problem at Micro-NAV | Override |
|---|---|---|
| -3% hard floor on all positions | At €50 position, -3% = €1.50 gain. With any spread/commission, stop-loss is economically destructive. | **Suspend hard GTC stops below €2,000 NAV.** Replace with monthly review + mental trigger levels (typically -8% to -12%). Document triggers in session file. |
| GTC order at entry | Most brokers don't support GTC stops on fractional shares; at 1-share positions the stop-loss order size is trivial. | **Set price alerts instead of GTC orders.** Review at each monthly session. |

### Deployment Pacing Override

| Standard Rule | Problem at Micro-NAV | Override |
|---|---|---|
| Staged: 15% → 45% → 65% | At €200 NAV, 15% = €30. Cannot buy any instrument for €30. First purchase forces ~25-50% deployment. | **Accept Month 1 overdeployment driven by lot sizes.** The staged plan resumes from Month 2 as NAV grows via contributions. Target the staged percentages as NAV crosses €1,000. |

### When to Exit Micro-NAV Overrides

These overrides phase out progressively:

| NAV Threshold | Action |
|---|---|
| **€1,000** | Re-enable fractional Kelly sizing if broker supports fractional shares. Tighten mental triggers to -5%. |
| **€2,000** | Full framework compliance resumes. GTC hard stops mandatory. 5% position cap enforced. |
| **€5,000** | All standard rules apply without exception. |

> **Audit note**: Every session file must state the current NAV and which override tier applies. Phase 7 agents must check the NAV before applying position sizing rules.

---

## Exit & Review Triggers

> Stop-losses alone are insufficient for a monthly-review portfolio. Formal thesis review triggers ensure underperformers and stale positions are surfaced systematically.

### Thesis Review Triggers

| Trigger | Action |
|---|---|
| Original thesis invalidated by macro event | Position enters THESIS REVIEW status. Must be re-proposed or exited at next War Room (see Thesis Validation Protocol in `AGENTS.md`). |
| Position underperforms its asset-class benchmark for 3 consecutive sessions | Mandatory Thesis Review. Strike Team decides: hold, add, reduce, or exit. |
| Position within ±3% of entry price after 4 sessions | Mandatory Thesis Review. Capital may be better deployed elsewhere. |
| Position drifts below target allocation - 5pp for 2 consecutive sessions | Flag: is the underweight reflecting weak thesis or just sizing constraints? |

### Asset-Class Benchmarks (for thesis review triggers)

| Asset Class | Benchmark | Source |
|---|---|---|
| Global equity | MSCI World (via IWDA or equivalent) | yfinance |
| European equity | STOXX Europe 600 | yfinance |
| Emerging markets | MSCI EM (via IS3N or equivalent) | yfinance |
| Defence / thematic | STOXX Europe Total Market (broader market comparison) | yfinance |
| Gold / commodity | Gold spot price in EUR | yfinance / ECB FX |
| Property / alternatives | STOXX Europe 600 Real Estate | yfinance |

> A position "underperforms" when its return over the measurement period is negative while the benchmark is positive, or when the position trails the benchmark by more than 5pp.

---

## VIX Emergency Protocol

VIX band boundaries are held in `config/gates.yml` → `vix_emergency`. Do not duplicate values here. Actions by band:

| Band | Action |
|---|---|
| GREEN | Normal deployment per cash floor and gate rules |
| AMBER | Deploy at half rate (handled by AMBER deployment gate) |
| RED | Deploy nothing. Hold all cash. Review existing positions for stop-loss proximity. |
| EMERGENCY | Deploy nothing. Mandatory full portfolio review. Consider reducing equity exposure by 25–50%. No new positions until VIX returns to AMBER or below. |

> This protocol applies to the deployment decision only. It does not trigger forced selling of existing positions — that is handled by the drawdown thresholds and stop-loss framework.

---

## Data Degradation Protocol (DDP)

> Owned by Risk Officer. See [Proposal 001](../proposals/001-data-layer-upgrade.md) for structural rationale. Applies to Tier 1 macro substrate (FRED + ECB) and any tier added later.

When a snapshot fetch fails or a datapoint is stale, the cognitive layer must never silently substitute training-data recall or a hand-waved estimate. The DDP defines what happens instead.

### On fetch failure (any Tier 1 series)
1. **Retry** the fetch with exponential backoff: up to `retry.max_attempts` attempts, spacing controlled by `retry.backoff_seconds_base` in `config/gates.yml`.
2. If all retries fail, **fall back to the last known snapshot** for that series. The observation is tagged `STALE` with its vintage age in days. The shared HTTP client's on-disk cache (`data/.http_cache/`) may satisfy this step without contacting the source.
3. **Never** replace a failed fetch with a model-recalled value, a rounded plausible number, or a hard-coded default. A missing datapoint is reported as missing.

### Staleness tiers (per-series)
Every Tier 1 series has an AMBER and RED staleness threshold measured in days since the datapoint's `vintage`. These thresholds live in `config/gates.yml` under `data_staleness.series`. Concrete anchors:
- **HICP (euro area)**: `> 45 days` AMBER, `> 60 days` RED.
- **Daily series (VIX, EUR/USD)**: narrower tolerance (≤ 10 days before RED).
- **ECB policy rates (DFR)**: wider tolerance (meetings are scheduled quarterly; up to 90 days before RED).

### Session-level escalation
- **≥ 2 Tier 1 series** in the snapshot are `STALE` or `RED` → the session is tagged **session RED**.
- A session RED forces: *halve deployment* OR *DEFER execution* at the Orchestrator's discretion.
- A session RED must be recorded in the Session Go/No-Go Check and the Handoff to next session.

### Hand-verifiability
The snapshot file is the audit artefact. The `snapshot_hash` field is computed over the canonical JSON form with the field itself set to `""` (see `docs/DATA_STANDARDS.md` §Snapshot JSON Schema). Any disagreement between prose claims and the snapshot is resolved by the snapshot.

---

## Evaluator Failure Protocol

> Owned by Risk Officer. See [Proposal 003](../proposals/003-phase-1b-data-integration.md) for structural rationale. Governs what happens when
> `gate_eval` raises an exception or produces an unexpected result during a live session.
> There is NO silent fallback to agent recall — agents must not substitute unavailable gate
> data with estimated or recalled values. Fetch the data or halt the session.

### Failure modes

| Failure | Symptom | Action |
|---|---|---|
| **Hard crash** | `gate_eval` raises exception (any error) | Halt session. Do not proceed to Strike Team. |
| **Snapshot missing** | `local/snapshots/YYYY-MM.json` not found | Run `python -m scripts.data fetch --session YYYY-MM`. If fetch fails after all DDP retries, follow On-fetch-failure steps in §Data Degradation Protocol above. |
| **Hash mismatch** | `gate_eval` prints "Snapshot hash mismatch" | Snapshot file may have been corrupted or manually edited. Re-fetch. Do NOT override the hash check. |
| **Schema version rejected** | `gate_eval` prints "schema_version exceeds known max" | Upgrade `gate_eval` to handle the new version (new proposal required). |
| **Data_Confidence_Tier = RED** | Output row in gate table shows `Data_Confidence_Tier: **RED**` | See §Data Degradation Protocol — session RED triggers: halve deployment OR defer execution. Do not silently ignore. |
| **Partial failure** | `gate_eval` succeeds but ≥1 gate has `data_source: unavailable` | That gate is scored RED (Data Failure Protocol). The Risk Guardian inspects `data_source` per gate — a gate is not "green by omission" when data is missing. |

### Response procedure

1. **Halt** — Stop all session activity. Do not run Strike Team agents with stale or unavailable gate data.
2. **Diagnose** — Check the specific error message (gate_eval exits non-zero and prints the cause).
3. **Re-fetch** — Run `python -m scripts.data fetch --session YYYY-MM`. If FRED_API_KEY is unset or expired, resolve that first.
4. **Re-run gate_eval** — If the re-fetch succeeds, re-run `python -m scripts.data gate_eval --session YYYY-MM`. The pre-session log must be updated with the new output.
5. **Escalate** — If re-fetch fails after all DDP retries: open a `/propose` emergency amendment to defer the session or accept reduced data quality with explicit Risk Officer sign-off. Do NOT absorb the failure silently and proceed.

### What is NOT permitted

- Running the Strike Team while `Data_Confidence_Tier = RED` without explicit Risk Officer sign-off.
- Replacing an unavailable gate with an agent's recalled value or a "reasonable estimate."
- Editing the snapshot file to resolve a hash mismatch.
- Marking a missing gate as GREEN to avoid halting the session.

---

## Kill Switch Specification

### Trigger Conditions (any one activates)
1. Portfolio drawdown exceeds -15%
2. Daily loss exceeds 3% of NAV
3. System malfunction detected (orders not filling, data feed down)
4. Manual activation by user

### Kill Switch Actions (execute in order)
1. Cancel all open orders
2. Flatten all positions at market
3. Send alert (email + SMS)
4. Log all positions, P&L, and market state
5. Disable automated order submission
6. Require manual re-enable with user approval
