"""Deployment gate checks. Thresholds are config-driven, data is fetched."""

from __future__ import annotations

from .models import GateResult, GateStatus, MacroSnapshot, PortfolioState


def check_gates(
    macro: MacroSnapshot,
    portfolio: PortfolioState,
    prices: dict[str, float],
    geopolitical_status: str,
    trigger_pct: float = -0.08,
    cash_floor_pct: float = 0.30,
) -> list[GateResult]:
    """Evaluate all 6 deployment gates. Returns list of GateResult."""
    results = []

    # Gate 1: STOXX 600 vs 50wk MA
    stoxx_vs_ma = (macro.stoxx - macro.stoxx_ma50wk) / macro.stoxx_ma50wk
    if macro.stoxx > macro.stoxx_ma50wk:
        status = GateStatus.GREEN
    elif macro.stoxx > macro.stoxx_ma50wk * 0.98:
        status = GateStatus.AMBER
    else:
        status = GateStatus.RED
    results.append(GateResult(
        name="STOXX 600 vs 50wk MA",
        level=f"{macro.stoxx:.1f} vs {macro.stoxx_ma50wk:.1f} ({stoxx_vs_ma:+.1%})",
        status=status,
    ))

    # Gate 2: VIX
    if macro.vix < 20:
        status = GateStatus.GREEN
    elif macro.vix < 30:
        status = GateStatus.AMBER
    else:
        status = GateStatus.RED
    results.append(GateResult(
        name="VIX",
        level=f"{macro.vix:.1f}",
        status=status,
    ))

    # Gate 3: ECB stance
    # Heuristic: rate <= 2.50 and stable/declining = GREEN
    # rate rising or hawkish signals = AMBER
    # active tightening = RED
    # For backtest: we treat the rate level as the signal
    if macro.ecb_rate <= 2.50:
        status = GateStatus.GREEN
        detail = "accommodative"
    elif macro.ecb_rate <= 3.50:
        status = GateStatus.AMBER
        detail = "neutral"
    else:
        status = GateStatus.RED
        detail = "restrictive"
    results.append(GateResult(
        name="ECB stance",
        level=f"{macro.ecb_rate:.2f}% ({detail})",
        status=status,
    ))

    # Gate 4: Positions vs triggers
    triggers = portfolio.trigger_check(prices, trigger_pct)
    any_breached = any(t["breached"] for t in triggers.values())
    min_buffer = min((t["buffer_pct"] for t in triggers.values()), default=100.0)
    if any_breached:
        status = GateStatus.RED
    elif min_buffer < 3.0:
        status = GateStatus.AMBER
    else:
        status = GateStatus.GREEN
    results.append(GateResult(
        name="Positions vs triggers",
        level=f"Min buffer: {min_buffer:+.1f}%",
        status=status,
        detail=f"{'Breach: ' + ', '.join(t for t, v in triggers.items() if v['breached']) if any_breached else 'All above'}",
    ))

    # Gate 5: Tariff / Geopolitical
    geo_upper = geopolitical_status.upper()
    status = GateStatus[geo_upper] if geo_upper in GateStatus.__members__ else GateStatus.AMBER
    results.append(GateResult(
        name="Tariff / Geopolitical",
        level=geopolitical_status,
        status=status,
    ))

    # Gate 6: Cash floor
    cash_pct = portfolio.cash_pct(prices)
    if cash_pct >= cash_floor_pct:
        status = GateStatus.GREEN
    else:
        status = GateStatus.RED
    results.append(GateResult(
        name="Cash floor",
        level=f"€{portfolio.cash:.2f} ({cash_pct:.1%})",
        status=status,
    ))

    return results


def deployment_authorised(gates: list[GateResult]) -> bool:
    """True if no RED gates."""
    return not any(g.status == GateStatus.RED for g in gates)


def count_by_status(gates: list[GateResult]) -> dict[str, int]:
    """Count gates by status."""
    counts = {"GREEN": 0, "AMBER": 0, "RED": 0}
    for g in gates:
        counts[g.status.value] += 1
    return counts


def format_gates_table(gates: list[GateResult]) -> str:
    """Format gates as a markdown table."""
    lines = ["| Gate | Level | Status |", "|---|---|---|"]
    for g in gates:
        status_str = f"**{g.status.value}**" if g.status != GateStatus.GREEN else g.status.value
        lines.append(f"| {g.name} | {g.level} | {status_str} |")
    return "\n".join(lines)
