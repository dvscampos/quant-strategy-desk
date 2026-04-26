# Compliance — European Regulatory Framework

> **Jurisdiction note**: This file ships with Portugal as the worked example — the onboarding flow rewrites it for your jurisdiction. Nothing in this file constitutes tax or legal advice; consult a qualified adviser for your circumstances.

> Owned by Persona F (Compliance Officer). All strategies operating in European markets must comply with this framework.

## Applicable Regulations

### Primary (mandatory for European algo trading)

| Regulation | Scope | Key Requirements |
|---|---|---|
| **MiFID II** | Investment services in the EU | Algo trading authorisation, pre/post-trade transparency, best execution |
| **MiFID II Article 17** | Algorithmic trading specifically | Risk controls, kill switches, annual self-assessment |
| **MAR** (Market Abuse Regulation) | Market manipulation prevention | No spoofing, layering, wash trading, or insider trading |
| **EU Short Selling Regulation (SSR)** | Short positions in EU equities | Disclosure at 0.1% to NCA, public disclosure at 0.5% |
| **EMIR** | Derivatives clearing | Central clearing for standardised OTC derivatives |
| **SFDR** | Sustainability disclosure | Relevant if marketing ESG-related strategies |

### Informational (may apply depending on instruments)

| Regulation | When Relevant |
|---|---|
| **Reg SHO** (US) | If trading US-listed securities |
| **SEC Rule 15c3-5** | If routing orders to US exchanges |
| **UK FCA rules** | If trading LSE-listed securities post-Brexit |
| **Swiss FMIA** | If trading SIX-listed securities |

---

## Pre-Trade Risk Controls

### Mandatory Automated Checks (before every order)

| Control | Rule | Action on Breach |
|---|---|---|
| **Order size limit** | Single order ≤ 2% of instrument ADV | Reject order |
| **Price collar** | Order price within ±5% of last trade | Reject order |
| **Position limit** | Post-trade position ≤ 5% of NAV | Reject order |
| **Sector limit** | Post-trade sector exposure ≤ 20% of NAV | Reject order |
| **Daily order count** | ≤ 500 orders per day | Halt trading; alert user |
| **Daily turnover limit** | ≤ 100% of NAV per day | Halt trading; alert user |
| **Duplicate order check** | No identical order within 5 seconds | Reject duplicate |
| **Market hours check** | Order only during exchange trading hours | Queue for open or reject |

### Kill Switch Requirements (MiFID II Article 17)
- One-click emergency stop accessible at all times
- Must cancel all open orders within 1 second
- Must prevent new order submission
- Must log activation time and reason
- Must require manual re-enable with documented reason

---

## Best Execution Obligations

### Documentation Required
For each trade, record:
- Order timestamp (submission, fill, cancellation)
- Instrument identifier (ISIN)
- Side (buy/sell), quantity, price
- Venue (exchange/dark pool)
- Execution algorithm used
- Slippage vs. arrival price
- Any market impact estimate

### Periodic Best Execution Review
- **Monthly**: Compare execution quality across venues
- **Quarterly**: Review execution algorithm performance
- **Annually**: Publish top 5 execution venues report (if applicable)

---

## Record Keeping Requirements

### What to Store
| Record Type | Retention Period | Format |
|---|---|---|
| All orders (submitted, cancelled, filled) | 5 years | Database + backup |
| Trade confirmations | 7 years | PDF/database |
| Algorithm parameters and changes | 5 years | Git + changelog |
| Risk limit breaches and actions taken | 5 years | Incident log |
| Compliance review reports | 5 years | PDF |
| Data sources and quality reports | 3 years | Database |

### Audit Trail Requirements
- Every order must be traceable to the signal that generated it
- Every signal must be traceable to the data that produced it
- Every parameter change must have a timestamp, reason, and approver

---

## Market Manipulation Prevention

### Prohibited Patterns (detect and prevent)

| Pattern | Description | Detection Method |
|---|---|---|
| **Spoofing** | Placing orders you intend to cancel to move prices | Monitor cancellation rate; alert if > 80% |
| **Layering** | Multiple orders at different levels to create false depth | Monitor multi-level order patterns |
| **Wash trading** | Self-dealing to create false volume | Cross-check buy/sell accounts |
| **Front-running** | Trading ahead of known pending orders | Strict information barriers |
| **Momentum ignition** | Aggressive orders to trigger other algos | Monitor for rapid order sequences |

### Safeguards
- Maximum order-to-trade ratio: 4:1 (4 orders per fill)
- Minimum quote lifetime: 100ms (no sub-second cancel-replace loops)
- Independent monitoring of all order patterns

---

## Short Selling Compliance (EU SSR)

> ⛔ **This portfolio operates under the Defined Risk Only rule — short selling is prohibited.** This section is retained for regulatory awareness only, in case future strategies ever require review.

| Net Short Position | Obligation |
|---|---|
| ≥ 0.1% of issued share capital | Report to National Competent Authority (NCA) |
| ≥ 0.5% of issued share capital | Public disclosure |
| Each additional 0.1% above 0.5% | Updated public disclosure |

### Locate Requirement
Not applicable (short selling prohibited). Retained for reference:
- Borrowing source
- Borrow cost
- Availability confirmation timestamp

---

## Algorithm Change Management

### Before Modifying a Live Strategy
1. Document the proposed change (what, why, expected impact)
2. Run PROPOSE with Risk Officer (D) and Compliance Officer (F) review
3. Backtest the modification against historical data
4. Paper trade for minimum 5 trading days
5. Obtain user approval
6. Deploy with monitoring for first 3 trading days
7. Log the change in `PROGRESS.md` and strategy docs

### Annual Self-Assessment (MiFID II)
- [ ] Review all active algorithms and their risk controls
- [ ] Verify kill switch functionality
- [ ] Review all compliance breaches in the past year
- [ ] Update risk parameters based on market conditions
- [ ] Document changes to trading infrastructure

---

## Incident Response Plan

### When an Algorithm Malfunctions

| Step | Action | Timeframe |
|---|---|---|
| 1 | Activate kill switch | Immediately |
| 2 | Document the incident (what happened, when, impact) | Within 1 hour |
| 3 | Assess financial impact | Within 2 hours |
| 4 | Root cause analysis | Within 24 hours |
| 5 | Report to NCA if required (significant market impact) | Within 24 hours |
| 6 | Implement fix and test in paper trading | Before resumption |
| 7 | Resume with enhanced monitoring | After user approval |

### Incident Severity Levels
| Level | Definition | Response |
|---|---|---|
| **P1** | Financial loss > 1% of NAV or regulatory breach | Immediate halt; user notification; NCA assessment |
| **P2** | System error causing unintended trades, no material loss | Halt affected strategy; investigate within 4 hours |
| **P3** | Data quality issue or non-critical system error | Log and fix within 24 hours |
| **P4** | Minor issue, no impact on trading | Fix in next maintenance window |

---

## Tax Considerations — Portugal (IRS)

> ⚠️ Consult a qualified Portuguese tax advisor (contabilista certificado). This section is informational guidance only and may not reflect the latest legislative changes.

### Jurisdiction
- **Resident for tax purposes**: Portugal
- **National Competent Authority (NCA)**: CMVM (Comissão do Mercado de Valores Mobiliários)
- **Tax authority**: Autoridade Tributária e Aduaneira (AT)
- **Tax year**: Calendar year (January–December)
- **Filing deadline**: Typically 30 June for the previous year (IRS Modelo 3)

### Capital Gains Tax (Mais-valias)

| Scenario | Rate | Notes |
|---|---|---|
| Shares/ETFs held < 365 days | **28% flat** | Taxed as Category G income. Can opt to aggregate (englobamento) if marginal rate is lower. |
| Shares/ETFs held ≥ 365 days | **28% flat** (partial exemption may apply) | Check if partial exemption for long holds is in effect — legislation has changed. |
| Commodity ETCs (gold, etc.) | **28% flat** (likely) | See warning below — classification may vary. |
| Losses | Carry forward 5 years | Losses can offset gains within the same category. Must opt for englobamento to offset. |
| Crypto (if applicable) | **28% flat** | Held < 365 days. Exempt if held ≥ 365 days (as of 2023 rules). |

> [!WARNING] Commodity ETC Tax Classification
> Physically-backed gold ETCs (e.g., IGLN, A1KWPQ) may be classified by the Autoridade Tributária as **commodities** rather than **securities**. This could change the applicable tax schedule (Category G vs Category B) and filing requirements. **Confirm classification with your contabilista before filing.** If classified as a commodity trade, it may need to be declared differently in your IRS Modelo 3.

> **Englobamento decision**: If your total income is low enough that your marginal IRS rate is below 28%, opting for englobamento (aggregation with other income) may reduce your tax. This decision applies to ALL capital income for the year — you can't cherry-pick.

### Dividend Tax

| Source | Withholding | Filing |
|---|---|---|
| Portuguese dividends | 28% withheld at source | Pre-filled in IRS; can opt for englobamento |
| EU dividends | Withholding varies by country (15–30%) | Declare in Anexo J; claim credit for foreign WHT paid |
| Swiss dividends (Nestlé, Roche, etc.) | 35% Swiss WHT | Reclaim excess via Swiss tax treaty (PT-CH treaty reduces to 15%). File DA-1 form with Swiss tax authorities. |
| UK dividends (BAE, Unilever, etc.) | 0% UK WHT | Declare in Anexo J; taxed at 28% in Portugal |

> **Important**: Swiss withholding tax is painful (35%). For Swiss-listed positions (NESN.SW, ROG.SW, ZURN.SW), you can reclaim 20% of the 35% via the PT-CH double tax treaty, but the process is slow (6–18 months). Factor this into position sizing.

### Foreign Transaction Taxes (FTT)

These are paid at the point of trade and are non-recoverable:

| Country | FTT Rate | Applies To |
|---|---|---|
| France | 0.3% | Buy-side only; French companies with market cap > €1B |
| Italy | 0.1% | Buy-side only; Italian-listed equities |
| Spain | 0.2% | Buy-side only; Spanish companies with market cap > €1B |
| Germany | None | No FTT (as of 2026) |
| UK | 0.5% (Stamp Duty) | Buy-side only; UK-listed shares |

> **Impact on strategies**: French (HO.PA, AM.PA, AIR.PA, MC.PA, BNP.PA) and Italian (LDO.MI, UCG.MI, ISP.MI) positions incur FTT on purchase. Include these costs in backtest transaction cost models.

### IRS Filing Requirements

| Form | Purpose | When |
|---|---|---|
| **Anexo G** | Capital gains from Portuguese securities | Annual (Modelo 3) |
| **Anexo J** | Foreign income (dividends, capital gains from non-PT securities) | Annual (Modelo 3) |
| **Quadro 9 (Anexo J)** | Detailed foreign capital gains — each trade individually | Annual |
| **Anexo H** | Tax credits for foreign WHT paid (to avoid double taxation) | Annual |

### Record Requirements for Portuguese Tax Filing
- All trades with exact dates, quantities, acquisition price, sale price, and fees (per-trade detail required for Anexo J Quadro 9)
- Dividend receipts with gross amount, WHT deducted, and country of source
- Currency conversion rates used (ECB daily reference rate on trade date)
- Broker annual statements (IBKR provides annual activity statements suitable for this)
- Cost basis: **FIFO** (first in, first out) is the standard method in Portugal

### Practical Tax Notes
1. **IBKR annual statement** is your best friend — it provides all trades, dividends, and WHT in one document.
2. **Broker-level tax reporting**: IBKR does NOT report to Portuguese tax authorities. You must self-declare everything.
3. **Multi-currency**: Convert all gains/losses to EUR using ECB reference rate on the date of each transaction.
4. **Cost of reclaiming WHT**: For small dividend amounts, the administrative cost of reclaiming Swiss/other excess WHT may not be worth it. Consider ETF alternatives domiciled in Ireland (0% Irish WHT on accumulating ETFs) to avoid this friction.
5. **Irish-domiciled ETFs**: Most iShares/Vanguard ETFs listed on European exchanges are Irish-domiciled UCITS. These are tax-efficient for Portuguese residents as Ireland has a favourable treaty network and accumulating versions avoid dividend WHT entirely.

