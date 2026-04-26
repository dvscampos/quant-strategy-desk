# Agent Performance Tracker (Backtest Sessions v2)

> Tracks Phase 7 verdicts by agent across backtest sessions. After 12 sessions, reveals which agents produce signal vs noise.
> For live session performance, see `AGENT_PERFORMANCE.md` in project root.

## Phase 7 Verdict History

| Agent | BT #1 | BT #2 | BT #3 | BT #4 | BT #5 | BT #6 | BT #7 | BT #8 | BT #9 | BT #10 | BT #11 | Total APR | Total FLAG | Total N/A | Noise |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Agent | BT #1 | BT #2 | BT #3 | BT #4 | BT #5 | BT #6 | BT #7 | BT #8 | BT #9 | BT #10 | BT #11 | BT #12 | Total APR | Total FLAG | Total N/A | Noise |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| GS Quant Architect | APR | APR | FLAG | APR | APR | APR | APR | *ST* | APR | *ST* | APR | *ST* | 8 | 1 | 0 | 1 |
| Renaissance Backtesting | FLAG | FLAG | APR | APR | APR | APR | APR | APR | APR | APR | APR | *ST* | 9 | 2 | 0 | 2 |
| Two Sigma Risk | APR | APR | APR | APR | APR | APR | APR | *ST* | *ST* | *ST* | *ST* | *ST* | 7 | 0 | 0 | — |
| Citadel Alpha | N/A | APR | APR | APR | APR | APR | APR | FLAG | *ST* | APR | *ST* | APR | 8 | 1 | 1 | 1 |
| Jane Street MM | APR | APR | APR | APR | APR | APR | APR | APR | *ST* | FLAG | *ST* | APR | 9 | 1 | 0 | 1 |
| AQR Factor Model | APR | APR | APR | APR | APR | APR | APR | *ST* | APR | *ST* | APR | *ST* | 9 | 0 | 0 | — |
| D.E. Shaw StatArb | APR | APR | APR | N/A | APR | APR | APR | *ST* | APR | *ST* | FLAG | *ST* | 7 | 1 | 1 | 1 |
| Bridgewater Macro | APR | APR | APR | APR | APR | APR | APR | APR | *ST* | APR | *ST* | APR | 10 | 0 | 0 | — |
| Bloomberg Data Pipeline | FLAG | APR | FLAG | APR | APR | APR | APR | APR | APR | APR | APR | FLAG | 9 | 3 | 0 | 3 |
| Virtu Execution | N/A | APR | — | APR | APR | APR | APR | APR | APR | APR | APR | APR | 10 | 0 | 1 | — |
| Point72 ML Alpha | N/A | N/A | APR | FLAG | APR | APR | APR | APR | FLAG | APR | FLAG | FLAG | 6 | 4 | 2 | 3 |
| Man Group Portfolio | APR | APR | — | APR | APR | APR | APR | *ST* | APR | *ST* | APR | APR | 9 | 0 | 0 | — |
| Millennium Live Trading | N/A | N/A | APR | N/A | FLAG | N/A | APR | APR | APR | APR | APR | APR | 7 | 1 | 4 | 1 |
| Dimensional Backtester | FLAG | FLAG | APR | APR | APR | APR | APR | APR | *ST* | APR | *ST* | APR | 8 | 2 | 0 | 2 |
| GS Compliance | APR | APR | — | APR | APR | APR | APR | APR | APR | APR | APR | APR | 11 | 0 | 0 | — |

## Signal-to-Noise Ratio (after 12 sessions — FINAL)

### Tier Assessment

| Tier | Agents | Criteria |
|---|---|---|
| **Reliable** (0 noise in 8+ sessions) | Two Sigma, AQR Factor, Bridgewater, Man Group, GS Compliance, Virtu | Perfect or near-perfect record across 12 sessions |
| **Clean** (0-1 noise, mostly approve) | Citadel, GS Architect, Jane Street, D.E. Shaw | Low noise, high signal |
| **Improving** (noise trending down) | Renaissance (2→0×9), Dimensional (2→0×7) | Formerly noisy, clean for 7+ sessions |
| **Noisy** | Bloomberg (3 flags, all invalid NAV math errors), Point72 ML Alpha (4 flags, 3 noise, 1 legitimate) | Most flags of any agents. Point72 is the only legitimate signal producer but also the noisiest. Bloomberg consistently misreads NAV reconciliation. |
| **Low Signal** | Millennium (4 N/A + 1 FLAG + 7 APR) | Improving but many N/A — speciality rarely applicable at this scale. |

**BT #12 (FINAL)**: **8 APPROVE, 2 FLAG (Bloomberg invalid NAV math, Point72 invalid context confusion), 0 N/A.** Total across 12 sessions: ~155 verdicts, **1 legitimate flag** (Point72, BT #9 — DCA schedule documentation). Strike Team: Two Sigma, AQR Factor, D.E. Shaw, GS Architect, Renaissance.

## Legitimate Flags (actionable findings)

| Session | Agent | Flag | Impact |
|---|---|---|---|
| BT #9 | Point72 ML Alpha | DCA schedule needs documentation | Procedural — to be addressed in portfolio docs |

> Update this table after each Phase 7. Only legitimate, unresolved flags count.
