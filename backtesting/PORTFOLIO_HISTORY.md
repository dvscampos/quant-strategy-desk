# Historical Simulation — Portfolio History (v2.0)

> Running portfolio state after each monthly session. Monthly contribution: €200. See `README.md` for methodology.
> v2.0 re-run: 5-agent Strike Team, rotation enforcement, affordability filter, process sheriff.

---

## Summary Dashboard

| Month | Session | NAV (€) | Contributions (€) | Gain (€) | TWR (%) | Cash % | Invested % | Positions | Regime |
|---|---|---|---|---|---|---|---|---|---|
| Mar 2025 | 1 | 198.34 | 200 | -1.66 | -0.8% | 76.5% | 23.5% | 2 | Late Expansion / Early Easing |
| Apr 2025 | 2 | 399.97 | 400 | -0.03 | 0.0% | 73.5% | 26.5% | 3 | Deflationary Shock |
| May 2025 | 3 | 602.54 | 600 | +2.54 | 0.0% | 48.6% | 51.4% | 5 | Early Recovery |
| Jun 2025 | 4 | 797.99 | 800 | -2.01 | -0.6% | 47.5% | 52.5% | 5 | Late Recovery / Cautionary |
| Jul 2025 | 5 | 1,015.92 | 1,000 | +15.92 | +1.6% | 34.8% | 65.2% | 6 | Risk-On Recovery / Early Expansion |
| Aug 2025 | 6 | 1,217.67 | 1,200 | +17.67 | +1.5% | 32.2% | 67.8% | 6 | Risk-On Expansion / Mid-Cycle |
| Sep 2025 | 7 | 1,466.14 | 1,400 | +66.14 | +4.7% | 35.2% | 64.8% | 6 | Late-Cycle Easing / Soft Landing |
| Oct 2025 | 8 | 1,711.17 | 1,600 | +111.17 | +6.9% | 31.0% | 69.0% | 6 | Late-Cycle Equity Grind / Safe-Haven Bid |
| Nov 2025 | 9 | 1,908.63 | 1,800 | +108.63 | +6.0% | 32.5% | 67.5% | 6 | Late-Cycle Risk-Off Transition |
| Dec 2025 | 10 | 2,125.89 | 2,000 | +125.89 | +6.3% | 32.8% | 67.2% | 5 | Risk-On Expansion / ECB Hold |
| Jan 2026 | 11 | 2,419.10 | 2,200 | +219.10 | +10.0% | 30.2% | 69.8% | 5 | Risk-On Expansion / ECB Structural Hold |
| Feb 2026 | 12 | 2,661.07 | 2,400 | +261.07 | +10.9% | 30.2% | 69.8% | 5 | Risk-On Late Cycle / Consolidation Pressure |

### Cumulative Performance (FINAL — 12 sessions)

| Metric | Value |
|---|---|
| **Total contributions** | €2,400.00 |
| **Final NAV** | €2,661.07 |
| **Absolute gain** | +€261.07 |
| **Return on contributions** | +10.9% |
| **Number of trades executed** | 26 (22 BUY/ADD, 1 SELL/EXIT) |
| **First exit** | EXSA.DE at BT #10 (+7.3% realised) |
| **Worst month drawdown** | -4.8% intraday (April — DFNS -18.5%, IQQH -12.5%; portfolio cushioned by 88% cash) |
| **Final positions** | 5 (IWDA.AS ×5, IS3N.DE ×12, PPFB.DE ×3, DFNS.PA ×4, IQQH.DE ×31) |
| **Cumulative deployment** | €1,597.06 / €2,400.00 = 66.5% |
| **Cash drag (structural)** | 33.5% of contributions never deployed |

### Position-Level P&L (as of February 27 close — FINAL)

| Ticker | Shares | Avg Entry (€) | EOM Price (€) | Unrealised P&L (€) | P&L (%) |
|---|---|---|---|---|---|
| IWDA.AS | 5 | 105.315 | 113.575 | +41.30 | +7.8% |
| IS3N.DE | 12 | 37.879 | 43.394 | +66.18 | +14.6% |
| PPFB.DE | 3 | 57.287 | 85.870 | +85.75 | +49.9% |
| DFNS.PA | 4 | 48.415 | 58.972 | +42.23 | +21.8% |
| IQQH.DE | 31 | 8.488 | 8.904 | +12.90 | +4.9% |
| **Total invested** | | | **€1,858.13** | **+€248.36** | **+15.4%** |

### Realised P&L

| Ticker | Entry Avg (€) | Exit Price (€) | Shares | Realised P&L (€) | P&L (%) | Session |
|---|---|---|---|---|---|---|
| EXSA.DE | 54.021 | 57.850 | 3 | +11.49 | +7.1% | BT #10 |

### Allocation by Theme

| Theme | Value (€) | % NAV |
|---|---|---|
| Global Equity | 560.95 | 23.2% |
| Emerging Markets | 492.88 | 20.4% |
| Gold / Crisis Hedge | 243.46 | 10.1% |
| Defence / Geopolitical | 239.85 | 9.9% |
| Property / Rate Play | 150.69 | 6.2% |
| Cash | 731.28 | 30.2% |

---

## Session 0: Starting Point (2025-03-15)

| Metric | Value |
|---|---|
| **NAV** | €200.00 |
| **Cash** | €200.00 (100%) |
| **Invested** | €0.00 (0%) |
| **Positions** | None |

---

## Session 1: March 2025

**Session date**: 2025-03-15 (third Saturday)
**Execution date**: 2025-03-17 (Monday)
**Regime**: Late Expansion / Early Easing
**Strike Team**: AQR Factor (Macro), D.E. Shaw (Signal), Jane Street (Architect), Two Sigma (Risk), Renaissance (Challenger)

| Trade | Date | Ticker | Entry Price (€) | Shares | Cost (€) |
|---|---|---|---|---|---|
| BUY | 2025-03-17 | DFNS.PA | 42.130 | 1 | 42.13 |
| BUY | 2025-03-17 | IQQH.DE | 6.121 | 1 | 6.12 |

**Post-execution snapshot (at entry prices)**:

| Metric | Value |
|---|---|
| **NAV** | €200.00 |
| **Cash** | €151.75 (75.9%) |
| **Invested** | €48.25 (24.1%) |
| **Positions** | DFNS.PA ×1 @ €42.13, IQQH.DE ×1 @ €6.12 |
| **Stop-losses** | None (micro-NAV override — monthly review, -10%/-12% mental triggers) |

**End-of-month mark (March 31)**:

| Metric | Value |
|---|---|
| **EOM NAV** | €198.34 |
| **Portfolio return** | -€1.66 (-0.8% on €200 contributed) |
| **DFNS.PA** | €40.63 (-3.6% from entry) — above -10% trigger (€37.92) |
| **IQQH.DE** | €5.96 (-2.7% from entry) — above -12% trigger (€5.39) |

**Phase 7**: 8 APPROVE, 3 FLAG (1 invalid, 2 already resolved), 4 N/A

---

## Session 2: April 2025

**Session date**: 2025-04-19 (third Saturday)
**Execution date**: 2025-04-22 (Tuesday — Easter Monday closed)
**Regime**: Deflationary Shock / Policy Uncertainty (Trump tariffs April 2, VIX peaked 60.1)
**Strike Team**: Bridgewater (Macro), Citadel (Signal), GS Architect (Architect), Two Sigma (Risk), Dimensional (Challenger)

**Deployment gates**: 2 RED (STOXX < 50wk MA, tariffs enacted), 1 AMBER (VIX 29.6). Equity deployment BLOCKED. Gold exception approved.

| Trade | Date | Ticker | Entry Price (€) | Shares | Cost (€) |
|---|---|---|---|---|---|
| BUY | 2025-04-22 | PPFB.DE | 57.870 | 1 | 57.87 |

**Post-execution snapshot:**

| Metric | Value |
|---|---|
| **NAV** | €398.84 |
| **Cash** | €293.88 (73.7%) |
| **Invested** | €104.96 (26.3%) |
| **Positions** | PPFB.DE ×1 @ €57.87, DFNS.PA ×1 @ €42.13, IQQH.DE ×1 @ €6.12 |
| **Stop-losses** | Mental triggers: PPFB -8% (€53.24), DFNS -10% (€37.92), IQQH -9% (€5.57 — tightened) |

**End-of-month mark (April 30):**

| Metric | Value |
|---|---|
| **EOM NAV** | €399.97 |
| **Portfolio return** | -€0.03 (0.0% on €400 contributed) |
| **Month intraday drawdown** | DFNS -18.5% (recovered), IQQH -12.5% (breach logged) |

**Phase 7**: 11 APPROVE, 2 FLAG (both already resolved), 2 N/A

**Key v2 decision**: Gates blocked equity deployment. Only gold was deployed (gate exception). v1 deployed EXSA.DE + added DFNS.PA despite tariff shock — no gate framework existed.

---

## Session 3: May 2025

**Session date**: 2025-05-17 (third Saturday)
**Execution date**: 2025-05-19 (Monday)
**Regime**: Early Recovery / Risk-On Transition (all gates GREEN — first fully permissive session)
**Strike Team**: AQR Factor (Macro), Point72 ML (Signal), Man Group (Architect), Two Sigma (Risk), Virtu (Challenger)

| Trade | Date | Ticker | Entry Price (€) | Shares | Cost (€) |
|---|---|---|---|---|---|
| BUY | 2025-05-19 | IWDA.AS | 100.355 | 1 | 100.36 |
| BUY | 2025-05-19 | EXSA.DE | 53.874 | 1 | 53.87 |
| ADD | 2025-05-19 | DFNS.PA | 47.000 | 1 | 47.00 |

**Post-execution snapshot:**

| Metric | Value |
|---|---|
| **NAV** | €603.15 |
| **Cash** | €292.65 (48.5%) |
| **Invested** | €310.50 (51.5%) |
| **Positions** | PPFB.DE ×1, DFNS.PA ×2, IQQH.DE ×1, IWDA.AS ×1, EXSA.DE ×1 |
| **Stop-losses** | Mental triggers: PPFB -10% (€52.08), DFNS -10% avg (€40.11), IQQH -9% (€5.57), IWDA -10% (€90.32), EXSA -10% (€48.49) |

**End-of-month mark (May 30):**

| Metric | Value |
|---|---|
| **EOM NAV** | €602.54 |
| **Portfolio return** | +€2.54 (+0.4% on €600 contributed) |
| **IQQH April flag** | Formally cleared (€6.35 vs €5.57 trigger = 12.3% buffer) |

**Phase 7**: 10 APPROVE, 2 FLAG (1 invalid, 1 already resolved), 3 rate-limited

**Key v2 decision**: First all-GREEN gate session. Deployed into recovery with 3 trades (2 new positions + 1 add). EXSA chosen over IS3N for European recovery thesis. Portfolio scaled from 3 to 5 positions.

---

## Session 4: June 2025

**Session date**: 2025-06-21 (third Saturday)
**Execution date**: 2025-06-23 (Monday)
**Regime**: Late Recovery / Cautionary Slowdown (4 GREEN, 2 AMBER — VIX trend, tariff expiry)
**Strike Team**: AQR Factor (Macro, 2nd consecutive), Citadel (Signal), Jane Street (Architect), Two Sigma (Risk), Dimensional (Challenger)

**Deployment gates**: 2 AMBER (VIX rising to 20.6, tariff pause expiring July 9). Two Sigma imposed €150 hard cap, blocked IWDA/EXSA/IS3N adds.

| Trade | Date | Ticker | Entry Price (€) | Shares | Cost (€) |
|---|---|---|---|---|---|
| ADD | 2025-06-23 | PPFB.DE | 56.995 | 2 | 113.99 |

**Post-execution snapshot:**

| Metric | Value |
|---|---|
| **NAV** | €802.04 |
| **Cash** | €378.66 (47.2%) |
| **Invested** | €423.38 (52.8%) |
| **Positions** | PPFB.DE ×3, DFNS.PA ×2, IQQH.DE ×1, IWDA.AS ×1, EXSA.DE ×1 |
| **Stop-losses** | PPFB -10% avg (€51.56), DFNS -10% avg (€40.11), IQQH -9% (€5.57), IWDA -10% (€90.32), EXSA -10% (€48.49) |

**End-of-month mark (June 30):**

| Metric | Value |
|---|---|
| **EOM NAV** | €797.99 |
| **Portfolio return** | -€2.01 (-0.3% on €800 contributed) |
| **Gold impact** | PPFB -4.5% in June — largest single drag despite being added as hedge |

**Phase 7**: 12 APPROVE, 1 FLAG (already resolved), 2 N/A

**Key v2 decision**: Conservative deployment — gold ADD only. Two Sigma's €150 cap binding. Dimensional's CONDITIONAL BLOCK overridden for gold hedge. Contingency plan for July 9 added to handoff.

---

## Session 5: July 2025

**Session date**: 2025-07-19 (third Saturday)
**Execution date**: 2025-07-21 (Monday)
**Regime**: Risk-On Recovery / Early Expansion (all 6 gates GREEN — tariff resolved, VIX normalised)
**Strike Team**: Bridgewater (Macro), D.E. Shaw (Signal), Man Group (Architect), Two Sigma (Risk), Renaissance (Challenger)

**Tariff resolution (July 9)**: STOXX rallied 543.5 → 550.0. VIX dropped 17.8 → 15.9. Pre-agreed contingency triggered: deploy aggressively, IS3N enters, IWDA/EXSA scaled.

| Trade | Date | Ticker | Entry Price (€) | Shares | Cost (€) |
|---|---|---|---|---|---|
| BUY | 2025-07-21 | IS3N.DE | 34.612 | 2 | 69.22 |
| ADD | 2025-07-21 | IWDA.AS | 102.310 | 1 | 102.31 |
| ADD | 2025-07-21 | EXSA.DE | 53.705 | 1 | 53.71 |

**Post-execution snapshot:**

| Metric | Value |
|---|---|
| **NAV** | €1,010.23 |
| **Cash** | €353.42 (35.0%) |
| **Invested** | €656.81 (65.0%) |
| **Positions** | PPFB.DE ×3, DFNS.PA ×2, IQQH.DE ×1, IWDA.AS ×2, EXSA.DE ×2, IS3N.DE ×2 |
| **Stop-losses** | Mental triggers tightened to -8%: PPFB (€52.70), DFNS (€41.00), IQQH (€5.63), IWDA (€93.23), EXSA (€49.49), IS3N (€31.84) |

**End-of-month mark (July 31):**

| Metric | Value |
|---|---|
| **EOM NAV** | €1,015.92 |
| **Portfolio return** | +€15.92 (+1.6% on €1,000 contributed) |
| **€1,000 milestone** | NAV crossed €1,000. Framework transition: triggers tightened to -8%, micro-NAV overrides active until €2,000. |
| **Best performer** | DFNS.PA +13.3% from entry |
| **IWDA post-add** | +2.6% in 10 days — immediate deployment validation |

**Phase 7**: 14 APPROVE, 1 FLAG (Millennium — noise/scope mismatch), 0 N/A

**Key v2 decision**: Post-tariff contingency executed with calibrations (not blindly). Renaissance's CONDITIONAL BLOCK resolved 4 conditions: gold thesis revised, IS3N thesis reconstructed, IQQH deadline set (BT #8), €1,000 transition documented. IS3N sized at 2 shares (Two Sigma's €100 new-instrument cap binding). Portfolio scaled from 5 to 6 positions.

---

## Session 6: August 2025

**Session date**: 2025-08-16 (third Saturday)
**Execution date**: 2025-08-18 (Monday)
**Regime**: Risk-On Expansion / Mid-Cycle Consolidation (all 6 gates GREEN)
**Strike Team**: AQR Factor (Macro, returning), Citadel (Signal), GS Architect (Architect), Two Sigma (Risk), Dimensional (Challenger)

**Mid-point session** (6 of 12). IQQH governance resolution. EUR/USD strengthening (1.17) noted as structural feature.

| Trade | Date | Ticker | Entry Price (€) | Shares | Cost (€) |
|---|---|---|---|---|---|
| ADD | 2025-08-18 | IWDA.AS | 104.750 | 1 | 104.75 |
| ADD | 2025-08-18 | IS3N.DE | 35.089 | 1 | 35.09 |
| ADD | 2025-08-18 | IQQH.DE | 7.070 | 3 | 21.21 |

**Post-execution snapshot:**

| Metric | Value |
|---|---|
| **NAV** | €1,216.52 |
| **Cash** | €392.37 (32.3%) |
| **Invested** | €824.15 (67.7%) |
| **Positions** | PPFB.DE ×3, DFNS.PA ×2, IQQH.DE ×4, IWDA.AS ×3, EXSA.DE ×2, IS3N.DE ×3 |
| **Stop-losses** | -8% triggers: PPFB (€52.70), DFNS (€41.00), IQQH (€6.29), IWDA (€94.27), EXSA (€49.49), IS3N (€31.99) |

**End-of-month mark (August 29):**

| Metric | Value |
|---|---|
| **EOM NAV** | €1,217.67 |
| **Portfolio return** | +€17.67 (+1.5% on €1,200 contributed) |
| **IQQH governance** | Resolved — 4 shares, 2.3% NAV (target: 2%). Auto-exit at BT #8 if below 2%. |
| **Gold recovery** | PPFB from -3.1% to -0.2% — nearly flat |

**Phase 7**: 14 APPROVE, 0 FLAG, 1 N/A (Millennium)

**Key v2 decision**: EXSA add dropped to respect 30% cash floor (would have breached at 27.8%). IQQH +3 shares resolves 5-session governance gap at trivial cost (€21). Dimensional's CONDITIONAL BLOCK resolved: IQQH plan, EXSA/IWDA overlap documented as intentional, cash deployment quantified. EUR/USD strengthening acknowledged as structural headwind for USD assets.

---

## Session 7: September 2025

**Session date**: 2025-09-20 (third Saturday)
**Execution date**: 2025-09-22 (Monday)
**Regime**: Late-Cycle Easing / Soft Landing (all 6 gates GREEN, 4th consecutive)
**Strike Team**: Bridgewater (Macro), Point72 ML (Signal), Jane Street (Architect), Two Sigma (Risk), Renaissance (Challenger)

**First engine-assisted session**. ECB cut to 2.00% on Sep 11. All positions in profit. Renaissance CONDITIONAL BLOCK resolved (3 conditions). Moderate deployment — Bridgewater's posture.

| Trade | Date | Ticker | Entry Price (€) | Shares | Cost (€) |
|---|---|---|---|---|---|
| ADD | 2025-09-22 | IQQH.DE | 7.387 | 3 | 22.16 |
| ADD | 2025-09-22 | EXSA.DE | 54.482 | 1 | 54.48 |

**Post-execution snapshot:**

| Metric | Value |
|---|---|
| **NAV** | €1,453.19 |
| **Cash** | €515.73 (35.5%) |
| **Invested** | €937.46 (64.5%) |
| **Positions** | PPFB.DE ×3, DFNS.PA ×2, IQQH.DE ×7, IWDA.AS ×3, EXSA.DE ×3, IS3N.DE ×3 |
| **Stop-losses** | -8% triggers: PPFB (€52.70), DFNS (€41.00), IQQH (€6.48), IWDA (€94.27), EXSA (€49.70), IS3N (€31.99) |

**End-of-month mark (September 30):**

| Metric | Value |
|---|---|
| **EOM NAV** | €1,466.14 |
| **Portfolio return** | +€66.14 (+4.7% on €1,400 contributed) |
| **Best performer** | DFNS.PA +24.2% from entry — European defence spending narrative holds |
| **Gold surge** | PPFB +10.9% — strongest single-month recovery in the backtest |
| **IQQH secured** | 7 shares, 3.6% NAV — well clear of 2% BT #8 threshold |

**Phase 7**: 15 APPROVE, 0 FLAG, 0 N/A — **first unanimous session**

**Key v2 decision**: Moderate deployment (€76.64 of €156 available). IQQH ×3 is rate-thesis-driven (ECB 2.00%), not threshold gaming. EXSA chosen over IWDA per Bridgewater's EUR-denomination preference (avoids USD FX drag at EUR/USD 1.1737). No DFNS add despite +18.8% — let winners run, don't chase. Cash held at 35.5% — optionality preserved.

---

## Session 8: October 2025

**Session date**: 2025-10-18 (third Saturday)
**Execution date**: 2025-10-20 (Monday)
**Regime**: Late-Cycle Equity Grind / Safe-Haven Bid (all 6 gates GREEN, 5th consecutive)
**Strike Team**: Man Group (Macro), D.E. Shaw (Signal), GS Architect (Architect), Two Sigma (Risk), AQR Factor (Challenger)

AQR Challenger issued CONDITIONAL BLOCK on cash drag (41.9% across 5 GREEN sessions = "structurally indefensible"). EXSA skipped as value trap (lagging rally). IQQH skipped (ECB held, no catalyst). Orchestrator adopted Challenger's alternative plan.

| Trade | Date | Ticker | Entry Price (€) | Shares | Cost (€) |
|---|---|---|---|---|---|
| ADD | 2025-10-20 | IWDA.AS | 109.505 | 1 | 109.51 |
| ADD | 2025-10-20 | IS3N.DE | 38.263 | 2 | 76.53 |

**Post-execution snapshot:**

| Metric | Value |
|---|---|
| **NAV** | €1,709.05 |
| **Cash** | €529.69 (31.0%) |
| **Invested** | €1,179.36 (69.0%) |
| **Positions** | IWDA.AS ×4, PPFB.DE ×3, IS3N.DE ×5, EXSA.DE ×3, DFNS.PA ×2, IQQH.DE ×7 |
| **Stop-losses** | -8% triggers: IWDA (€100.74), PPFB (€52.70), IS3N (€35.20), EXSA (€49.70), DFNS (€41.00), IQQH (€6.51) |

**End-of-month mark (October 31):**

| Metric | Value |
|---|---|
| **EOM NAV** | €1,711.17 |
| **Portfolio return** | +€111.17 (+6.9% on €1,600 contributed) |
| **Best performer** | DFNS.PA +23.5% from entry |
| **Gold pullback** | PPFB +17.1% (down from +26.4% at execution — mean reversion) |
| **IQQH rally** | +20.1% — property rally despite ECB hold |

**Phase 7**: 9 APPROVE, 1 FLAG (Citadel — noise/already resolved), 0 N/A

**Key v2 decision**: Adopted Challenger's plan — IWDA ×1 + IS3N ×2 (€186.04). Cash reduced from 41.9% to 31.0% — largest single-session cash reduction in backtest. EXSA skipped as value trap (lagging despite STOXX rally). IQQH skipped (ECB held). No override vote needed — Challenger's plan adopted in full.

---

## v1 vs v2 Comparison (running)

| Session | v1 NAV (€) | v2 NAV (€) | v1 Trades | v2 Trades | Key Difference |
|---|---|---|---|---|---|
| Mar 2025 | 200.00 | 198.34 | PPFB.DE + DFNS.PA | DFNS.PA + IQQH.DE | v2 excluded gold (over cap), added property |
| Apr 2025 | 402.48 | 399.97 | ADD DFNS + BUY EXSA | BUY PPFB.DE only | v2 gates blocked equity; added gold as crisis hedge |
| May 2025 | 615.03 | 602.54 | ADD PPFB + ADD EXSA + BUY IWDA | BUY IWDA + BUY EXSA + ADD DFNS | v2 added defence instead of gold; similar diversification path |
| Jun 2025 | — | 797.99 | — | ADD 2× PPFB.DE only | v2 conservative — tariff cliff hedge. Gold drag -4.5%. |
| Jul 2025 | — | 1,015.92 | — | BUY IS3N + ADD IWDA + ADD EXSA | v2 aggressive post-tariff deployment. IS3N new EM entry. |
| Aug 2025 | — | 1,217.67 | — | ADD IWDA + ADD IS3N + ADD 3× IQQH | v2 mid-point. IQQH governance resolved. EXSA dropped for cash floor. |
| Sep 2025 | — | 1,466.14 | — | ADD 3× IQQH + ADD EXSA | v2 rate-thesis deployment. First engine-assisted. First unanimous Phase 7. |
| Oct 2025 | — | 1,711.17 | — | ADD IWDA + ADD 2× IS3N | Challenger-driven. Largest cash reduction (-10.9pp). EXSA value-trap skip. |
| Nov 2025 | — | 1,908.63 | — | ADD IWDA only | First AMBER gate. Challenger overridden 3/3. Single conservative trade. |
| Dec 2025 | — | 2,125.89 | — | SELL EXSA + ADD IS3N ×4 + ADD DFNS ×2 + ADD IQQH ×5 | First exit. Most active session (4 trades). NAV crosses €2k. |
| Jan 2026 | — | 2,419.10 | — | ADD IS3N ×3 + ADD IQQH ×5 | Cash floor constrains. IWDA blocked by 25% cap. Under-deployment flagged. |

---

## Session 9: November 2025

**Session date**: 2025-11-15 (third Saturday)
**Execution date**: 2025-11-17 (Monday)
**Regime**: Late-Cycle Risk-Off Transition (**first AMBER gate** — VIX 22.4)
**Strike Team**: Bridgewater (Macro), Citadel (Signal), Jane Street (Architect), Two Sigma (Risk), Dimensional (Challenger)

**First AMBER gate in the backtest** — VIX 22.4 broke 6 sessions of all-GREEN. Dimensional issued CONDITIONAL BLOCK (deploy €0, wait for GREEN). Overridden 3/3 — AMBER = conservative deployment per framework, not blocked. Single IWDA share is maximally conservative.

| Trade | Date | Ticker | Entry Price (€) | Shares | Cost (€) |
|---|---|---|---|---|---|
| ADD | 2025-11-17 | IWDA.AS | 109.750 | 1 | 109.75 |

**Post-execution snapshot:**

| Metric | Value |
|---|---|
| **NAV** | €1,897.52 |
| **Cash** | €619.94 (32.7%) |
| **Invested** | €1,277.58 (67.3%) |
| **Positions** | IWDA.AS ×5, PPFB.DE ×3, IS3N.DE ×5, EXSA.DE ×3, DFNS.PA ×2, IQQH.DE ×7 |
| **Stop-losses** | -8% triggers: IWDA (€100.97), PPFB (€52.70), IS3N (€33.27), EXSA (€49.70), DFNS (€41.00), IQQH (€6.51) |

**End-of-month mark (November 28):**

| Metric | Value |
|---|---|
| **EOM NAV** | €1,908.63 |
| **Portfolio return** | +€108.63 (+6.0% on €1,800 contributed) |
| **Gold recovered** | PPFB +23.0% (up from +19.0% at execution) |
| **DFNS pullback** | +12.9% (from +17.4%) — some mean reversion |
| **EXSA life signs** | +5.3% (first improvement in 3 sessions) |

**Phase 7**: 9 APPROVE, 1 FLAG (Point72 — DCA schedule documentation, first legitimate flag in backtest), 0 N/A

**Key v2 decision**: Challenger overridden for first time by formal 3/3 vote. AMBER ≠ RED — framework explicitly permits conservative deployment. Single IWDA share is core DCA, not event-driven. EXSA held (consensus). Cash at 32.5% EOM. NAV approaching €2,000 milestone.

---

## Session 10: December 2025

**Session date**: 2025-12-20 (third Saturday)
**Execution date**: 2025-12-22 (Monday)
**Regime**: Risk-On Expansion / ECB Hold (all 6 gates GREEN — back from AMBER)
**Strike Team**: Man Group (Macro), D.E. Shaw (Signal), GS Architect (Architect), Two Sigma (Risk), AQR Factor (Challenger)

**Landmark session**: First exit in the backtest. Most active trade session (4 trades). NAV crosses €2,000 — micro-NAV overrides phase out. ECB held at 2.00% on Dec 18 (fourth pause). VIX collapsed from 22.4 to 14.9. AQR CONDITIONAL BLOCK auto-lifted (EXSA exit was the condition).

| Trade | Date | Ticker | Entry Price (€) | Shares | Cost (€) |
|---|---|---|---|---|---|
| SELL | 2025-12-22 | EXSA.DE | 57.850 | 3 | +173.55 |
| ADD | 2025-12-22 | IS3N.DE | 37.812 | 4 | 151.25 |
| ADD | 2025-12-22 | DFNS.PA | 52.264 | 2 | 104.53 |
| ADD | 2025-12-22 | IQQH.DE | 8.119 | 5 | 40.60 |

**Post-execution snapshot:**

| Metric | Value |
|---|---|
| **NAV** | €2,119.49 |
| **Cash** | €697.11 (32.9%) |
| **Invested** | €1,422.38 (67.1%) |
| **Positions** | IWDA.AS ×5, IS3N.DE ×9, PPFB.DE ×3, DFNS.PA ×4, IQQH.DE ×12 |
| **Stop-losses** | -8% triggers: IWDA (€96.91), IS3N (€33.95), PPFB (€52.70), DFNS (€44.54), IQQH (€6.91) |

**End-of-month mark (December 30):**

| Metric | Value |
|---|---|
| **EOM NAV** | €2,125.89 |
| **Portfolio return** | +€125.89 (+6.3% on €2,000 contributed) |
| **Best performer** | PPFB.DE +26.9% — gold holding peak gains |
| **IS3N builds** | 9 shares, +3.9% — EM position now meaningful (16.2% NAV) |
| **DFNS doubled** | 4 shares, +8.0% — defence thesis strengthening |
| **EXSA exited** | +7.3% realised — first exit in backtest |

**Phase 7**: 9 APPROVE, 1 FLAG (Jane Street — execution staggering, noise), 0 N/A

**Key v2 decision**: EXSA exit unanimous (5/5 Strike Team) — value trap after 4 sessions of underperformance with no ECB catalyst. Proceeds redeployed into IS3N, DFNS, IQQH. Risk Guardian blocked IWDA add (26.3% breaches 25% cap — first real impact of micro-NAV override removal). AQR CONDITIONAL BLOCK lifted automatically when EXSA exit confirmed in plan. Portfolio simplified to 5 positions. Cash at 32.8% EOM.

---

## Session 11: January 2026

**Session date**: 2026-01-17 (third Saturday)
**Execution date**: 2026-01-19 (Monday)
**Regime**: Risk-On Expansion / ECB Structural Hold (all 6 gates GREEN, 8th consecutive)
**Strike Team**: Bridgewater (Macro), Citadel (Signal), Jane Street (Architect), Two Sigma (Risk), Dimensional (Challenger)

Cash floor (30%) constrains deployment to €169.77. IWDA at 23.3% but adding 1 share (€113) breaches 25% cap — zero IWDA adds. Dimensional flagged structural under-deployment: €200/month + 30% floor = mathematically unable to reduce cash below ~28-30%. STOXX +9.7% above MA — tactically overextended per Bridgewater.

| Trade | Date | Ticker | Entry Price (€) | Shares | Cost (€) |
|---|---|---|---|---|---|
| ADD | 2026-01-19 | IS3N.DE | 40.820 | 3 | 122.46 |
| ADD | 2026-01-19 | IQQH.DE | 8.677 | 5 | 43.39 |

**Post-execution snapshot:**

| Metric | Value |
|---|---|
| **NAV** | €2,424.51 |
| **Cash** | €731.28 (30.2%) |
| **Invested** | €1,693.23 (69.8%) |
| **Positions** | IWDA.AS ×5, IS3N.DE ×12, PPFB.DE ×3, DFNS.PA ×4, IQQH.DE ×17 |

**End-of-month mark (January 30):**

| Metric | Value |
|---|---|
| **EOM NAV** | €2,419.10 |
| **Portfolio return** | +€219.10 (+10.0% on €2,200 contributed) |
| **Best performer** | PPFB.DE +41.7% — gold at all-time highs |
| **IS3N builds** | 12 shares, +8.4% — EM now 20.4% NAV |
| **IQQH builds** | 17 shares, +12.9% — property underweight correcting |
| **DFNS pullback** | +23.9% (from +32.5% at session) — some mean reversion |

**Phase 7**: 8 APPROVE, 2 FLAG (D.E. Shaw + Point72, both noise), 0 N/A

**Key v2 decision**: Most constrained session in the backtest. Cash floor and IWDA cap both binding. Deployment limited to IS3N ×3 + IQQH ×5 (€165.85). Dimensional's structural under-deployment concern is the key takeaway — needs formal review at BT #12. All 5 positions remain in profit, NAV breaks +10% return milestone.

---

## Next Sessions

| Session | Type | Target Date | Notes |
|---|---|---|---|
| BT #12: Feb 2026 | Backtest | 2026-02-21 | Third Saturday. **Final backtest session.** Cash floor review. |
| Live #2: April 2026 | Live | **Saturday 2026-04-18** | Third Saturday. After NFP (Apr 3), CPI (~Apr 14), ECB (if applicable). |
