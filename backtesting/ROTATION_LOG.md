# Strike Team Rotation Log (Backtest Sessions)

> Tracks which agent filled which role in each backtest session. Enforces the anti-bias rule: **max 2 consecutive sessions** for any rotating agent.
> For live session rotation history, see `ROTATION_LOG.md` in project root.

## Rotation History

| Session | Date | Risk (fixed) | Macro | Signal | Architect | Challenger | Notes |
|---|---|---|---|---|---|---|---|
| BT #1 (Mar 25) | 2025-03-15 | Two Sigma | AQR Factor | D.E. Shaw | Jane Street | Renaissance | v2.0: 5 agents, first session |
| BT #2 (Apr 25) | 2025-04-19 | Two Sigma | Bridgewater | Citadel | GS Architect | Dimensional | Tariff shock. Full rotation from BT #1. |
| BT #3 (May 25) | 2025-05-17 | Two Sigma | AQR Factor | Point72 ML | Man Group | Virtu | First all-GREEN gates. Full rotation from BT #2. |
| BT #4 (Jun 25) | 2025-06-21 | Two Sigma | AQR Factor | Citadel | Jane Street | Dimensional | Tariff cliff. Gold ADD only. AQR retained (2nd consec). |
| BT #5 (Jul 25) | 2025-07-19 | Two Sigma | Bridgewater | D.E. Shaw | Man Group | Renaissance | Post-tariff deployment. AQR forced out. 3 trades. |
| BT #6 (Aug 25) | 2025-08-16 | Two Sigma | AQR Factor | Citadel | GS Architect | Dimensional | Mid-point. IQQH governance. EXSA dropped for cash floor. |
| BT #7 (Sep 25) | 2025-09-20 | Two Sigma | Bridgewater | Point72 ML | Jane Street | Renaissance | First engine-assisted. Rate-thesis IQQH + EUR EXSA. First unanimous Phase 7. |
| BT #8 (Oct 25) | 2025-10-18 | Two Sigma | Man Group | D.E. Shaw | GS Architect | AQR Factor | Challenger BLOCK adopted. Cash drag reduction. EXSA value-trap skip. |
| BT #9 (Nov 25) | 2025-11-15 | Two Sigma | Bridgewater | Citadel | Jane Street | Dimensional | First AMBER gate (VIX 22.4). Challenger BLOCK overridden 3/3. Single IWDA conservative. |
| BT #10 (Dec 25) | 2025-12-20 | Two Sigma | Man Group | D.E. Shaw | GS Architect | AQR Factor | First EXIT (EXSA). Most active session (4 trades). NAV crosses €2,000. Challenger BLOCK auto-lifted. |
| BT #11 (Jan 26) | 2026-01-17 | Two Sigma | Bridgewater | Citadel | Jane Street | Dimensional | Cash floor constrains deployment. IWDA blocked by 25% cap. Structural under-deployment flagged. |
| BT #12 (Feb 26) | 2026-02-21 | Two Sigma | AQR Factor | D.E. Shaw | GS Architect | Renaissance | **FINAL SESSION.** Full rotation from BT #11. IQQH gap closed (5.9%→10.7%). D.E. Shaw exit calls overridden. |

## Consecutive Count (as of last backtest session)

| Agent | Current Consecutive | Max Before Rotation | Status |
|---|---|---|---|
| Two Sigma Risk | N/A (fixed) | N/A | Fixed role |
| AQR Factor Model | 1 (Macro) | 2 | — |
| D.E. Shaw StatArb | 1 (Signal) | 2 | — |
| GS Quant Architect | 1 (Architect) | 2 | — |
| Renaissance Backtesting | 1 (Challenger) | 2 | — |

## Agents Never Used on Strike Team (Backtest v2)

- Millennium Live Trading
- Bloomberg Data Pipeline
- GS Compliance

## Rotation Rules (v2.0)

1. **Risk Guardian**: Two Sigma Risk (fixed). Upgrade to paired model at NAV > €5,000.
2. **Macro Strategist**: Rotating. Pool: Bridgewater, AQR Factor, Man Group. Max 2 consecutive.
3. **Signal Generator**: Rotating. Pool: Citadel, Point72, D.E. Shaw, AQR*, Dimensional. Max 2 consecutive.
4. **Strategy Architect**: Rotating. Pool: GS Architect, Jane Street, Man Group*. Max 2 consecutive.
5. **Challenger**: Rotating. Any agent not already on the Strike Team. Prioritise risk-adjacent agents when a second risk perspective is needed.
6. *Man Group and AQR can each fill one slot per session, not multiple.
