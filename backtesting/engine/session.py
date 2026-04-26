"""Session skeleton generation — matches brainstorms/_TEMPLATE.md structure.

Fills in all deterministic data (prices, gates, portfolio, macro, rotation)
and provides proper section headers/placeholders for AI-generated content.
"""

from __future__ import annotations

from .briefs import macro_delta_table
from .gates import format_gates_table, count_by_status
from .models import GateResult, MacroSnapshot, PortfolioState, Trade
from .portfolio import mark_to_market


MONTH_NAMES = {
    1: "January", 2: "February", 3: "March", 4: "April", 5: "May",
    6: "June", 7: "July", 8: "August", 9: "September", 10: "October",
    11: "November", 12: "December",
}


def _nav_tier(nav: float) -> str:
    """Determine the NAV override tier."""
    if nav < 2000:
        return "Micro-NAV (<€2,000)"
    elif nav < 5000:
        return "Standard (€2,000–€5,000)"
    else:
        return "Full (>€5,000)"


def _position_action_table(portfolio: PortfolioState, prices: dict[str, float]) -> str:
    """Generate the Pivot Candidates table from previous session."""
    rows = [
        "| Position | Status | Reason |",
        "|---|---|---|",
    ]
    for ticker, pos in sorted(portfolio.positions.items()):
        price = prices.get(ticker, 0)
        _, pct = pos.pnl(price)
        rows.append(f"| {ticker} ({pos.theme}) | *TBD — HOLD / INCREASE / REDUCE / EXIT* | P&L: {pct:+.1%} |")
    return "\n".join(rows)


def generate_session_skeleton(
    session_number: int,
    session_date: str,
    execution_date: str,
    regime: str,
    portfolio: PortfolioState,
    prices: dict[str, float],
    macro: MacroSnapshot,
    gates: list[GateResult],
    team: dict[str, str],
    rotation_history: list[dict] | None = None,
    previous_macro: MacroSnapshot | None = None,
    handoff_notes: str = "",
    critical_events: str = "",
    key_issues: str = "",
    instrument_config: dict | None = None,
) -> str:
    """Generate the session markdown skeleton with all deterministic data filled in.

    Matches the full structure from brainstorms/_TEMPLATE.md.
    """
    nav = portfolio.nav(prices)
    cash_pct = portfolio.cash_pct(prices)
    max_deploy = portfolio.max_deployable(prices)
    afford_cap = portfolio.affordability_cap(prices)
    gate_counts = count_by_status(gates)
    gate_table = format_gates_table(gates)
    mtm = mark_to_market(portfolio, prices)
    nav_tier = _nav_tier(nav)

    session_month = int(session_date.split("-")[1])
    session_year = session_date.split("-")[0]
    month_name = MONTH_NAMES[session_month]

    prev_month = session_month - 1 if session_month > 1 else 12
    prev_year = int(session_year) if session_month > 1 else int(session_year) - 1
    next_month = session_month + 1 if session_month < 12 else 1
    next_year = int(session_year) if session_month < 12 else int(session_year) + 1

    # ── Portfolio table ──────────────────────────────────────────────
    pos_rows = []
    for p in mtm["positions"]:
        theme = ""
        if p["ticker"] in portfolio.positions:
            theme = f" ({portfolio.positions[p['ticker']].theme})"
        pos_rows.append(
            f"| {p['ticker']}{theme} | {p['shares']} | {p['avg_entry']:.3f} | "
            f"{p['price']:.3f} | {p['pnl_pct']:+.1f}% | {p['value']/nav*100:.1f}% |"
        )
    pos_rows.append(f"| Cash (+€200) | — | — | {portfolio.cash:.2f} | — | {cash_pct:.1%} |")
    pos_rows.append(f"| **Total NAV** | | | **€{nav:.2f}** | | |")
    pos_table = "\n".join(pos_rows)

    # ── Trigger check ────────────────────────────────────────────────
    triggers = portfolio.trigger_check(prices)
    trigger_rows = []
    for ticker, t in sorted(triggers.items()):
        status = "BREACHED" if t["breached"] else f"+{t['buffer_pct']:.1f}% buffer"
        trigger_rows.append(
            f"| {ticker} | €{t['price']:.3f} | €{t['trigger']:.2f} | {status} |"
        )
    trigger_table = "\n".join(trigger_rows)

    # ── Strike Team table ────────────────────────────────────────────
    role_labels = {
        "risk": "Risk Guardian (fixed)",
        "macro": "Macro Strategist",
        "signal": "Signal Generator",
        "architect": "Strategy Architect",
        "challenger": "Challenger",
    }
    team_rows = []
    for role in ["risk", "macro", "signal", "architect", "challenger"]:
        if role in team:
            team_rows.append(f"| {role_labels[role]} | {team[role]} | |")
    team_table = "\n".join(team_rows)

    # ── Rotation check ───────────────────────────────────────────────
    rotation_check = ""
    if rotation_history:
        last = rotation_history[-1] if rotation_history else {}
        prev_last = rotation_history[-2] if len(rotation_history) >= 2 else {}
        consec_notes = []
        for role in ["macro", "signal", "architect", "challenger"]:
            current = team.get(role, "")
            prev_agent = last.get(role, "")
            prev2_agent = prev_last.get(role, "")
            if current == prev_agent == prev2_agent and current:
                consec_notes.append(f"- **VIOLATION**: {current} would be 3rd consecutive as {role}")
            elif current == prev_agent and current:
                consec_notes.append(f"- {current}: 2nd consecutive as {role} (max 2 — must rotate next session)")
            elif current:
                consec_notes.append(f"- {current}: 1st session as {role}")
        rotation_check = "\n".join(consec_notes)

    # ── Macro delta ──────────────────────────────────────────────────
    macro_delta = ""
    if previous_macro:
        macro_delta = macro_delta_table(macro, previous_macro)

    # ── Allocation by theme ──────────────────────────────────────────
    alloc = portfolio.allocation_by_theme(prices)
    alloc_rows = []
    for theme, info in alloc.items():
        alloc_rows.append(f"| {theme} | {info['value']:.2f} | {info['pct_nav']:.1f}% |")
    alloc_table = "\n".join(alloc_rows)

    # ── Pivot candidates ─────────────────────────────────────────────
    pivot_table = _position_action_table(portfolio, prices)

    # ── Phase 7 agent list (excluding Strike Team) ───────────────────
    all_agents = [
        "GS Quant Architect", "Renaissance Backtesting", "Two Sigma Risk",
        "Citadel Alpha", "Jane Street MM", "AQR Factor Model",
        "D.E. Shaw StatArb", "Bridgewater Macro", "Bloomberg Data Pipeline",
        "Virtu Execution", "Point72 ML Alpha", "Man Group Portfolio",
        "Millennium Live Trading", "Dimensional Backtester", "GS Compliance",
    ]
    strike_team_agents = set(team.values())
    phase7_agents = [a for a in all_agents if a not in strike_team_agents]
    phase7_rows = "\n".join(f"| {a} | | |" for a in phase7_agents)
    excluded_list = ", ".join(sorted(strike_team_agents))

    # ── Trade instruction template ───────────────────────────────────
    instruments = instrument_config or {}

    def _trade_card(n: int) -> str:
        return f"""### Trade {n}: [ACTION] — [Instrument]

> [!TIP] In Plain English
> [What you're buying/selling and why, in plain language. No jargon.]

| Field | Detail |
|---|---|
| **Action** | |
| **Instrument** | |
| **ISIN** | |
| **TER** | |
| **Why** | |
| **Allocation** | |
| **Entry** | |
| **Stop-loss** | -8% mental trigger (micro-NAV override) |
| **Max you can lose** | The amount you invest. |"""

    trade_cards = "\n\n".join(_trade_card(i) for i in range(1, 4))

    # ── Gate status text ─────────────────────────────────────────────
    if gate_counts["RED"] > 0:
        gate_verdict = "**RED gates present. Equity deployment BLOCKED.**"
    elif gate_counts["AMBER"] > 0:
        gate_verdict = f"**{gate_counts['AMBER']} AMBER gate(s). Deployment authorised with caution.**"
    else:
        gate_verdict = "**All gates GREEN. Deployment authorised.**"

    # ── Build the skeleton ───────────────────────────────────────────
    skeleton = f"""---
tags: [war-room, brainstorm, {session_year}, backtest-v2]
date: {session_date}
session: "{month_name} {session_year}"
session_number: {session_number}
status: in-progress
regime: "{regime}"
ecb_rate: "{macro.ecb_rate:.2f}%"
trades: []
nav_invested: ""
nav_cash: ""
previous_session: "[[backtesting/sessions/{prev_year}-{prev_month:02d}]]"
next_session: "[[backtesting/sessions/{next_year}-{next_month:02d}]]"
---

# War Room Brainstorm — {month_name} {session_year} (Backtest v2.0, Session #{session_number})

> [!INFO] Session Metadata
> **Date**: {session_date} (third Saturday)
> **Execution date**: {execution_date}
> **NAV tier**: {nav_tier}
> **Model**: Opus (orchestrator) + Sonnet (Strike Team) + Haiku (Phase 7)
> **Process version**: War Room v2.1

{f'''> [!WARNING] Critical Events This Month
> {critical_events}
''' if critical_events else '''> [!WARNING] Critical Events This Month
> *To be filled by orchestrator — ECB meetings, earnings, macro releases, expiring catalysts.*
'''}
{f'''> [!NOTE] Key Issues Entering This Session
> {key_issues}
''' if key_issues else '''> [!NOTE] Key Issues Entering This Session
> *To be filled by orchestrator — carry-forward from previous session handoff.*
'''}
---

## Strike Team Selection

> [!IMPORTANT] Anti-Bias Rule
> Max **2 consecutive sessions** for any rotating agent. Check rotation log below.

> [!WARNING] Anti-Assumption Rule
> Do not predict the brainstorm's output when selecting the Strike Team. Include the Challenger.

> [!NOTE] Price Affordability Filter
> Max affordable share price = 25% of NAV = **€{afford_cap:.2f}**

### Today's Strike Team

| Role | Agent | Rationale |
|---|---|---|
{team_table}

### Rotation Check

{rotation_check if rotation_check else "*No rotation history available.*"}

---

## Phase 1: Portfolio Review

### Current Holdings Snapshot

| Position | Shares | Entry (€) | Current (€) | P&L | % NAV |
|---|---|---|---|---|---|
{pos_table}

### Allocation by Theme

| Theme | Value (€) | % NAV |
|---|---|---|
{alloc_table}

### Deployment Constraints

| Constraint | Value |
|---|---|
| Cash floor | 30% NAV = €{nav * 0.30:.2f} |
| Max deployable | €{max_deploy:.2f} |
| Affordability cap | €{afford_cap:.2f} per share |
| Shares | Whole shares only |
| Monthly contribution | €200 |

### Trigger Check

| Position | Current (€) | Trigger (€) | Status |
|---|---|---|---|
{trigger_table}

### Health Check

- [ ] Any triggers breached since last session?
- [ ] Any dividends received?
- [ ] Allocation drift: any theme moved >5% from target?
- [ ] P&L update: all positions reviewed

### Pivot Candidates

{pivot_table}

{f'''### Handoff Notes (from previous session)

{handoff_notes}
''' if handoff_notes else ''}---

## Phase 2: Macro Context

### Deployment Gate Check

{gate_table}

Gates: {gate_counts['GREEN']} GREEN, {gate_counts['AMBER']} AMBER, {gate_counts['RED']} RED.
{gate_verdict}

### Regime Classification

> [!CAUTION] Regime: {regime if regime and regime != "TBD" else "[TO BE DETERMINED]"}
> *To be filled by Macro Strategist — one-paragraph summary of the current regime and the 1–2 key events driving it.*

### Macro Snapshot

| Indicator | Value | Context |
|---|---|---|
| STOXX 600 | {macro.stoxx:.1f} | vs 50wk MA {macro.stoxx_ma50wk:.1f} ({(macro.stoxx-macro.stoxx_ma50wk)/macro.stoxx_ma50wk:+.1%}) |
| VIX | {macro.vix:.1f} | {"Low fear" if macro.vix < 20 else "Elevated" if macro.vix < 30 else "High stress"} |
| ECB rate | {macro.ecb_rate:.2f}% | {"Accommodative" if macro.ecb_rate <= 2.50 else "Neutral" if macro.ecb_rate <= 3.50 else "Restrictive"} |
| Brent crude | ${macro.brent:.2f} | {"Disinflationary" if macro.brent < 70 else "Neutral" if macro.brent < 90 else "Inflationary"} |
| EUR/USD | {macro.eurusd:.4f} | {"Strong EUR — headwind for USD holdings" if macro.eurusd > 1.15 else "Neutral" if macro.eurusd > 1.05 else "Weak EUR — tailwind for USD holdings"} |

{f'''### Macro Delta (vs previous session)

{macro_delta}
''' if macro_delta else ''}
---

## Phase 4: Signal & Opportunity Identification

*The Signal Generator proposes signals relevant to the current regime.*

### Top Investment Ideas

| # | Ticker | Name | Price (€) | Signal Type | Thesis | Key Risk |
|---|---|---|---|---|---|---|
| 1 | | | | | | |
| 2 | | | | | | |
| 3 | | | | | | |

> [!WARNING] Signals to Avoid / Traps
> *To be filled by Signal Generator.*

---

## Phase 6: Strategy Architecture

*The Strategy Architect structures signals into implementable strategies.*

> [!NOTE] Maximum Drawdown Estimate
> *To be filled — worst-case drawdown at full deployment.*

---

## Phase 7: Risk Stress Test

*The Risk Guardian challenges everything. Punches holes. Sets limits.*

> [!WARNING] Home Bias Reminder
> As a Portugal-based investor, the portfolio should *diversify away* from Iberian risk. Zero exposure to Portuguese equities or government bonds.

---

## Phase 8: Challenger Review

*The Challenger stress-tests the emerging consensus.*

> [!IMPORTANT] Challenger must provide:
> 1. **Verdict**: APPROVE, CONDITIONAL BLOCK (with conditions), or OPPOSE
> 2. **Alternative trade plan** — a concrete counter-proposal if blocking
>
> If the orchestrator overrides a BLOCK, the other 3 Strike Team agents (Macro, Signal, Architect) vote: 2/3 majority required to override.

---

## Orchestrator Conflict Resolution

*Synthesise Strike Team inputs. Resolve conflicts. If Challenger BLOCKed, document the vote.*

### Conflict Resolution Log

| Conflict | Resolution | Override Vote (if applicable) |
|---|---|---|
| | | |

---

## Final Strategy Summary

| # | Strategy | Allocation | Core Instruments | Entry Signal | Key Risk Control | Rebalance |
|---|---|---|---|---|---|---|
| 1 | | | | | | |
| 2 | | | | | | |
| 3 | | | | | | |

> [!IMPORTANT] Defined Risk Constraint
> All positions are **long-only**. No shorts, no uncovered options, no CFDs.
> **Max loss = amount invested.** See `docs/RISK_FRAMEWORK.md`.

---

## Exact Trade Instructions

*Specific, immediately actionable trades. These have passed Full Desk Sign-Off (Phase 9).*

{trade_cards}

### Post-Trade Monthly Snapshot

| Position | Ticker | Exchange | % NAV | Trigger | Theme |
|---|---|---|---|---|---|
| *To be filled after trades are finalised* | | | | | |
| Cash | — | — | % | — | Deployment Reserve |
| **TOTAL** | | | **100%** | | |

> [!NOTE] Worst-Case Scenario
> If all positions hit triggers simultaneously: **[X]% of total NAV**.

---

## Phase 9: Full Desk Sign-Off

> [!INFO] Sign-Off Protocol
> **10 agents** review the final trades (Strike Team excluded — they already reviewed in depth).
> Model: Haiku. If 3+ agents flag the same trade with **unresolved** concerns, it goes back to the Strike Team.
> **Excluded from this Phase 9** (Strike Team): {excluded_list}.

### Phase 9 Context Brief

> [!IMPORTANT] Fill this BEFORE launching Phase 7 agents.

**Session type**: BACKTEST (historical simulation)
**NAV**: €{nav:.0f} → **Override tier**: {nav_tier}
**Strike Team resolutions** (key decisions to prevent re-flagging):
1. *[e.g. "IQQH ADD is rate-thesis-driven, not threshold gaming"]*
2. *[e.g. "EXSA chosen over IWDA for EUR-denomination preference"]*
3. *[...]*

**Challenger concerns (unresolved)**:
- *[Include any Challenger concerns NOT fully resolved — gives Phase 7 agents something real to evaluate]*

**Alternative plan not chosen**:
- *[The Challenger's counter-proposal that was rejected — Phase 7 agents can flag if they prefer it]*

### Results

| Agent | Verdict | Note |
|---|---|---|
{phase7_rows}

**Raw Summary: [X] APPROVE, [Y] FLAG, [Z] N/A.**

### FLAG Categorisation

| Category | Count | Agents |
|---|---|---|
| Invalid | | |
| Already resolved | | |
| Legitimate | | |

| Trade | Legitimate Flags | Agents | Threshold (3+)? |
|---|---|---|---|
| | | | YES / NO |

---

## Comparison to Previous Session

### Position Changes

{pivot_table}

{f'''### Macro Delta

{macro_delta}
''' if macro_delta else ''}
### Next Month Watchlist

> [!IMPORTANT] Deployment Gates — Check Before Next Session

| Trigger | Current Level | Green Threshold | Red → Action |
|---|---|---|---|
| STOXX vs 50wk MA | {macro.stoxx:.1f} vs {macro.stoxx_ma50wk:.1f} | Above MA | Equity deployment blocked |
| VIX | {macro.vix:.1f} | < 20 | Conservative deployment |
| ECB rate | {macro.ecb_rate:.2f}% | ≤ 2.50% | Review rate-sensitive positions |
| EUR/USD | {macro.eurusd:.4f} | Monitor | Adjust IWDA/IS3N weighting |

---

## Execution Log

| Trade | Date | Ticker | Entry Price (€) | Shares | Cost (€) |
|---|---|---|---|---|---|
| *To be filled after execution* | | | | | |

---

## Handoff to Next Session

> [!IMPORTANT] Carry-Forward Brief
> Fill this at session end. The next session's agents receive this as context.

**Open issues to monitor:**
- *[e.g. "IQQH at X% NAV — BT #8 auto-exit deadline if below 2%"]*

**Positions to watch:**
- *[e.g. "EXSA approaching -8% trigger at current trajectory"]*

**Expiring catalysts:**
- *[e.g. "ECB October 16 meeting — potential further cut"]*

**Next session rotation:**
- Agents who MUST rotate out (hit 2-session consecutive limit): *[names]*
- Suggested replacements: *[names with rationale]*

---

## Session Scheduling

> **Rule**: Third Saturday of each month. After NFP, CPI, and ECB (when applicable).

**Next session date**: {next_year}-{next_month:02d} (third Saturday, to be computed)

---

## Changelog
- {session_date}: Session skeleton generated by engine v2.1
"""
    return skeleton
