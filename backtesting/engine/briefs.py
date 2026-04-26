"""Context brief generation for Strike Team and Phase 7 agents."""

from __future__ import annotations

from .models import GateResult, GateStatus, MacroSnapshot, PortfolioState, Trade
from .gates import format_gates_table


def strike_team_brief(
    role: str,
    agent_name: str,
    portfolio: PortfolioState,
    prices: dict[str, float],
    macro: MacroSnapshot,
    gates: list[GateResult],
    session_number: int,
    session_date: str,
    execution_date: str,
    handoff_notes: str = "",
    instrument_config: dict | None = None,
) -> str:
    """Generate a context brief for a Strike Team agent."""
    nav = portfolio.nav(prices)
    cash_pct = portfolio.cash_pct(prices)
    max_deploy = portfolio.max_deployable(prices)
    afford_cap = portfolio.affordability_cap(prices)

    # Portfolio table
    pos_lines = ["| Position | Shares | Avg Entry (€) | Current (€) | P&L | % NAV |",
                 "|---|---|---|---|---|---|"]
    for ticker, pos in sorted(portfolio.positions.items(), key=lambda x: -x[1].value(prices[x[0]])):
        price = prices[ticker]
        _, pct = pos.pnl(price)
        val = pos.value(price)
        theme = pos.theme
        pos_lines.append(
            f"| {ticker} ({theme}) | {pos.shares} | {pos.avg_entry:.3f} | {price:.3f} | {pct:+.1%} | {val/nav*100:.1f}% |"
        )
    pos_lines.append(f"| Cash (+€200) | — | — | {portfolio.cash:.2f} | — | {cash_pct:.1%} |")
    pos_lines.append(f"| **Total NAV** | | | **€{nav:.2f}** | | |")
    portfolio_table = "\n".join(pos_lines)

    # Gate table
    gate_table = format_gates_table(gates)
    gate_counts = {"GREEN": 0, "AMBER": 0, "RED": 0}
    for g in gates:
        gate_counts[g.status.value] += 1

    # Triggers
    triggers = portfolio.trigger_check(prices)
    trigger_lines = []
    for ticker, t in triggers.items():
        trigger_lines.append(f"- {ticker}: €{t['price']:.3f} vs trigger €{t['trigger']:.2f} = {t['buffer_pct']:+.1f}% buffer")
    trigger_text = "\n".join(trigger_lines)

    brief = f"""You are the {agent_name} agent acting as **{role.title()}** for Backtest Session #{session_number}.

**Context**:
- Session date: {session_date}. Execution date: {execution_date}.
- This is a BACKTEST — historical simulation, not live trading.
- Monthly contribution: €200. NAV at session: ~€{nav:.2f}
- Micro-NAV overrides active (below €2,000). Mental triggers only, no GTC stops.

**Current Portfolio (at {execution_date} prices)**:
{portfolio_table}

**Macro Data**:
- STOXX 600: {macro.stoxx:.1f} (vs 50wk MA {macro.stoxx_ma50wk:.1f} = {(macro.stoxx-macro.stoxx_ma50wk)/macro.stoxx_ma50wk:+.1%})
- VIX: {macro.vix:.1f}
- ECB rate: {macro.ecb_rate:.2f}%
- Brent crude: ${macro.brent:.2f}
- EUR/USD: {macro.eurusd:.4f}

**Deployment Gates**:
{gate_table}
Gates: {gate_counts['GREEN']} GREEN, {gate_counts['AMBER']} AMBER, {gate_counts['RED']} RED.

**Trigger Check**:
{trigger_text}

**Constraints**:
- Cash floor: 30% NAV (€{nav * 0.30:.2f})
- Max deployable: €{max_deploy:.2f}
- Affordability cap: €{afford_cap:.2f} per share
- Whole shares only
"""
    if handoff_notes:
        brief += f"\n**Handoff from previous session**:\n{handoff_notes}\n"

    return brief


def phase7_brief(
    agent_name: str,
    portfolio_post: PortfolioState,
    trades: list[Trade],
    prices: dict[str, float],
    gates: list[GateResult],
    session_number: int,
    regime: str = "",
    nav_eom: float | None = None,
    extra_context: str = "",
) -> str:
    """Generate a Phase 9 sign-off brief for a single agent."""
    nav = portfolio_post.nav(prices)
    cash_pct = portfolio_post.cash_pct(prices)

    # Trade summary
    trade_lines = []
    total_cost = 0.0
    for t in trades:
        trade_lines.append(f"- {t.action.value} {t.shares}× {t.ticker} @ €{t.price:.3f}")
        total_cost += t.cost
    trade_text = "\n".join(trade_lines) if trade_lines else "- No trades"

    # Gate summary
    gate_counts = {"GREEN": 0, "AMBER": 0, "RED": 0}
    for g in gates:
        gate_counts[g.status.value] += 1

    brief = f"""You are the {agent_name} agent for Phase 9 sign-off on Backtest Session #{session_number}.

CONTEXT BRIEF:
- Backtest session, not live trading. Micro-NAV (€{nav:.0f}). Monthly €200 contribution.
- {gate_counts['GREEN']} GREEN, {gate_counts['AMBER']} AMBER, {gate_counts['RED']} RED deployment gates.{f' Regime: {regime}.' if regime else ''}
- Trades: {len(trades)} total, €{total_cost:.2f} deployed.
{trade_text}
- Post-trade: {len(portfolio_post.positions)} positions, cash {cash_pct:.1%} ({"above" if cash_pct >= 0.30 else "BELOW"} 30% floor).
{f'- EOM NAV: €{nav_eom:.2f}.' if nav_eom else ''}
{extra_context}

DO NOT read any files. Base your verdict solely on this brief.
Reply with exactly: APPROVE, FLAG (with reason), or N/A. One sentence max."""

    return brief


def macro_delta_table(current: MacroSnapshot, previous: MacroSnapshot) -> str:
    """Generate a Macro Delta comparison table."""
    lines = [
        "| Indicator | Previous | Current | Change |",
        "|---|---|---|---|",
    ]

    def _delta(cur: float, prev: float, fmt: str = ".1f", suffix: str = "") -> str:
        diff = cur - prev
        pct = (cur - prev) / prev * 100 if prev else 0
        return f"{diff:+{fmt}}{suffix} ({pct:+.1f}%)"

    lines.append(f"| ECB Rate | {previous.ecb_rate:.2f}% | {current.ecb_rate:.2f}% | {'Held' if current.ecb_rate == previous.ecb_rate else f'{current.ecb_rate - previous.ecb_rate:+.2f}%'} |")
    lines.append(f"| STOXX 600 | {previous.stoxx:.1f} | {current.stoxx:.1f} | {_delta(current.stoxx, previous.stoxx)} |")
    lines.append(f"| VIX | {previous.vix:.1f} | {current.vix:.1f} | {current.vix - previous.vix:+.1f} |")
    lines.append(f"| Brent | ${previous.brent:.2f} | ${current.brent:.2f} | {_delta(current.brent, previous.brent, '.2f')} |")
    lines.append(f"| EUR/USD | {previous.eurusd:.4f} | {current.eurusd:.4f} | {_delta(current.eurusd, previous.eurusd, '.4f')} |")

    return "\n".join(lines)
