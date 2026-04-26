# Strike Team Rotation Log (Live Sessions)

> Tracks which agent filled which role in each live session. Enforces the anti-bias rule: **max 2 consecutive sessions** for any rotating agent.
> For backtest rotation history, see `backtesting/ROTATION_LOG.md`.

## Rotation History

| Session | Date | Risk (fixed) | Macro | Counter-Regime | Signal | Architect | Challenger | Notes |
|---|---|---|---|---|---|---|---|---|
| Live #1 | | Two Sigma | | | | | | |

## Consecutive Count

| Agent | Current Consecutive | Max Before Rotation | Status |
|---|---|---|---|
| Two Sigma Risk | N/A (fixed) | N/A | Fixed role |
| Bridgewater Macro | 0 | 2 | Available |
| Man Group | 0 | 2 | Available |
| Point72 ML | 0 | 2 | Available |
| Jane Street | 0 | 2 | Available |
| Dimensional | 0 | 2 | Available |
| Citadel Alpha | 0 | 2 | Available |
| GS Architect | 0 | 2 | Available |

## Agents Never Used on Strike Team (Live)

- D.E. Shaw StatArb
- AQR Factor Model
- Virtu Execution
- Millennium Live Trading
- Bloomberg Data Pipeline
- Renaissance Backtesting
- GS Compliance

## Rotation Rules (v2.0)

1. **Risk Guardian**: Two Sigma Risk (fixed). Upgrade to paired model at NAV > €5,000.
2. **Macro Strategist**: Rotating. Pool: Bridgewater, AQR Factor, Man Group. Max 2 consecutive.
3. **Counter-Regime**: Rotating. Must be a different persona from Macro in the same session. Pool: same as Macro pool.
4. **Signal Generator**: Rotating. Pool: Citadel, Point72, D.E. Shaw, AQR*, Dimensional. Max 2 consecutive.
5. **Strategy Architect**: Rotating. Pool: GS Architect, Jane Street, Man Group*. Max 2 consecutive.
6. **Challenger**: Rotating. Any agent not already on the Strike Team. Prioritise risk-adjacent agents when a second risk perspective is needed.
7. **Framework diversity**: ≥2 distinct `analytical_framework` values per Strike Team.
8. *Man Group and AQR can each fill one slot per session, not multiple.
