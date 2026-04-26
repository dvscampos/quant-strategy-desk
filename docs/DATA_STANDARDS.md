# Data Standards — Quality, Pipelines & Bias Prevention

> Owned by Persona C (CTO) and Persona A (Quant Architect). All data flowing into strategies must comply with these standards.

## Data Source Hierarchy

| Priority | Source | Type | Cost | Latency |
|---|---|---|---|---|
| 1 | Interactive Brokers API | Real-time + historical price | Included with account | Real-time |
| 2 | yfinance | Daily OHLCV, basic fundamentals | Free | 15-min delay |
| 3 | EODHD | EOD prices, fundamentals, dividends | Paid | EOD |
| 4 | Alpha Vantage | Intraday, FX, crypto, technicals | Free tier / paid | 1-min delay |
| 5 | ECB Statistical Data Warehouse | Macro data (rates, FX, money supply) | Free | Daily |
| 6 | Eurostat | GDP, inflation, employment | Free | Monthly/quarterly |
| 7 | FRED (St. Louis Fed) | US + global macro indicators | Free | Daily |

### Source Selection Rules
- **Price data**: IBKR primary, yfinance fallback
- **Fundamentals**: EODHD primary, yfinance fallback
- **Macro indicators**: ECB/Eurostat for European, FRED for global
- **Never rely on a single source** — cross-validate critical data points

---

## Data Quality Rules

### Mandatory Checks (Run on Every Ingestion)

| Check | Rule | Action on Failure |
|---|---|---|
| Missing values | No NaN in OHLCV for trading days | Interpolate if 1 day; flag if >1 day |
| Price continuity | Daily return > ±30% → suspicious | Flag for manual review (may be legit) |
| Volume zero | Zero volume on a trading day | Flag; may indicate data gap or halt |
| Negative prices | Price < 0 | Reject — data corruption |
| Timestamp integrity | No duplicate dates; no gaps on trading days | Fill gaps with previous close |
| OHLC consistency | Low ≤ Open,Close ≤ High | Reject bar — data corruption |
| Currency consistency | All prices in same currency per instrument | Convert to EUR using ECB daily rates |

### Corporate Action Handling
| Event | Adjustment |
|---|---|
| Stock split | Adjust all historical prices by split ratio |
| Reverse split | Adjust all historical prices by reverse ratio |
| Dividend (cash) | Adjust pre-ex-date prices downward by dividend amount |
| Spin-off | Adjust parent price; add child as new instrument |
| Merger/acquisition | Close acquired instrument; note event |
| Delisting | Mark instrument as delisted; retain historical data |

---

## Bias Prevention Checklist

### Lookahead Bias
- [ ] Point-in-time data only — no future data in any calculation
- [ ] Index constituents use historical membership, not current
- [ ] Financial statements use report date, not period end date
- [ ] All signals calculated with data available at the signal date

### Survivorship Bias
- [ ] Include delisted and bankrupt companies in historical universe
- [ ] Use point-in-time index constituent lists
- [ ] Never filter the universe based on current market cap

### Selection Bias
- [ ] Strategy universe defined before looking at results
- [ ] No cherry-picking of test periods
- [ ] Report all tested signals, not just successful ones

### Data Snooping Bias
- [ ] Limit free parameters (≤ 5 per strategy)
- [ ] Use Bonferroni correction for multiple hypothesis testing
- [ ] Reserve a final holdout period never touched during development

---

## Database Schema (Conceptual)

### Core Tables
```
instruments
  id, ticker, isin, name, exchange, currency, sector, country, status, listed_date, delisted_date

daily_prices
  instrument_id, date, open, high, low, close, adj_close, volume, source

corporate_actions
  instrument_id, date, action_type, ratio, amount, description

fundamentals
  instrument_id, report_date, period_end, metric_name, value

macro_indicators
  indicator_id, date, value, source

signals
  signal_name, instrument_id, date, value, metadata_json

trades
  strategy_id, instrument_id, date, side, quantity, price, commission, slippage
```

### Indexing Strategy
- `daily_prices`: Composite index on `(instrument_id, date)` — most frequent query
- `signals`: Composite index on `(signal_name, date)` — signal lookups
- `instruments`: Index on `ticker`, `isin` — search

---

## Pipeline Architecture

```
[Data Sources] → [Ingestion] → [Validation] → [Storage] → [Feature Store] → [Signals]
                                    ↓
                              [Quarantine]
                          (failed validation)
```

### Update Schedule
| Data Type | Frequency | Time (CET) |
|---|---|---|
| Daily prices | Daily | 18:00 (after market close) |
| Fundamentals | Weekly | Saturday 06:00 |
| Macro indicators | Daily | 07:00 (before market open) |
| Corporate actions | Daily | 18:30 (after prices) |
| Signal recalculation | Daily | 19:00 (after all data updated) |

### Idempotency Rule
Every pipeline step must be safely re-runnable. Use upsert logic (`INSERT ... ON CONFLICT UPDATE`) — never blindly append.

---

## Snapshot JSON Schema (Tier 1 macro substrate)

> See [Proposal 001](../proposals/001-data-layer-upgrade.md) for the structural lock. Any schema change after this point is a new proposal — providers, tests, and the SnapshotWriter all assume this shape.

### File location
`local/snapshots/<session>.json` where `<session>` is `YYYY-MM`.

### Shape
```json
{
  "as_of": "2026-05-17T10:00:00Z",
  "session": "2026-05",
  "snapshot_hash": "sha256:<64 hex chars>",
  "series": [
    {
      "source":    "FRED",
      "series_id": "CPIAUCSL",
      "as_of":     "2026-04-30",
      "value":     316.7,
      "vintage":   "2026-05-14",
      "units":     "index_1982_84_eq_100"
    }
  ]
}
```

### Field spec
| Field | Type | Meaning |
|---|---|---|
| `as_of` | ISO-8601 UTC timestamp | When the snapshot was captured (session run time) |
| `session` | `YYYY-MM` | Session the snapshot belongs to |
| `snapshot_hash` | `sha256:<hex>` | Hash over the canonical form with `snapshot_hash` set to `""` |
| `series` | array of observations | One entry per (source, series_id) |
| `series[].source` | `"FRED"` \| `"ECB"` (T1) | Provider that supplied the datapoint |
| `series[].series_id` | string | Provider-specific series identifier |
| `series[].as_of` | `YYYY-MM-DD` | Date the datapoint itself refers to |
| `series[].value` | number (no NaN/Inf) | Datapoint value |
| `series[].vintage` | `YYYY-MM-DD` | Date the provider released this datapoint |
| `series[].units` | string, stable per series | e.g. `pct`, `index_1982_84_eq_100` |

### Canonicalisation rule (hash input)
1. Sorted keys at every level.
2. UTF-8 encoding.
3. Compact separators: `(",", ":")` — no whitespace between tokens.
4. No trailing whitespace.
5. `snapshot_hash` set to `""` before hashing; the computed digest is then written back into the field.

The file on disk IS the canonical form (with a single trailing `LF`). This makes the hash hand-verifiable:
```bash
jq -cS . local/snapshots/2026-05.json \
  | sed 's/"snapshot_hash":"sha256:[^"]*"/"snapshot_hash":""/' \
  | tr -d '\n' | sha256sum
```

### Governance
* Snapshots are the authoritative audit trail. `local/snapshots/` is the filesystem-level system of record — this is why the CLI refuses silent overwrites (`--force` required).
* The HTTP response cache (`data/.http_cache/`) is excluded from the audit trail.
* `vintage` must be populated from the provider response; never defaulted to the session date.
* Providers raise on unknown/missing fields rather than inventing substitutes (see Data Degradation Protocol in `docs/RISK_FRAMEWORK.md`).
