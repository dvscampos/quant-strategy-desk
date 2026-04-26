"""Portfolio state machine. Immutable — each operation returns a new state."""

from __future__ import annotations

from datetime import date

from .models import PortfolioState, Position, Trade, TradeAction


class CashFloorBreachError(Exception):
    """Raised when a trade would breach the cash floor."""

    def __init__(self, post_cash_pct: float, floor_pct: float, shortfall: float):
        self.post_cash_pct = post_cash_pct
        self.floor_pct = floor_pct
        self.shortfall = shortfall
        super().__init__(
            f"Cash floor breach: post-trade cash {post_cash_pct:.1%} < floor {floor_pct:.1%} "
            f"(shortfall: €{shortfall:.2f})"
        )


class AffordabilityCapError(Exception):
    """Raised when a share price exceeds the affordability cap."""

    def __init__(self, ticker: str, price: float, cap: float):
        super().__init__(f"{ticker} price €{price:.2f} exceeds affordability cap €{cap:.2f}")


def add_contribution(state: PortfolioState, amount: float, d: date) -> PortfolioState:
    """Add a cash contribution. Returns new state."""
    new = state.copy()
    new.cash += amount
    new.total_contributions += amount
    new.date = d
    return new


def execute_trades(
    state: PortfolioState,
    trades: list[Trade],
    prices: dict[str, float],
    instrument_themes: dict[str, str],
    cash_floor_pct: float = 0.30,
    affordability_cap_pct: float = 0.25,
) -> PortfolioState:
    """Apply trades to portfolio. Returns new state.

    Validates:
    - Whole shares
    - Affordability cap (share price < 25% NAV)
    - Cash floor (post-trade cash >= 30% NAV)

    Raises CashFloorBreachError or AffordabilityCapError on violation.
    """
    new = state.copy()
    nav = new.nav(prices)
    cap = affordability_cap_pct * nav

    total_cost = 0.0

    for trade in trades:
        if trade.shares <= 0:
            raise ValueError(f"Trade shares must be positive: {trade}")

        if trade.shares != int(trade.shares):
            raise ValueError(f"Fractional shares not allowed: {trade.ticker} × {trade.shares}")

        if trade.price > cap:
            raise AffordabilityCapError(trade.ticker, trade.price, cap)

        if trade.action in (TradeAction.BUY, TradeAction.ADD):
            cost = trade.shares * trade.price
            total_cost += cost

            if trade.ticker in new.positions:
                # ADD — recalculate average entry
                new.positions[trade.ticker] = new.positions[trade.ticker].add_shares(
                    trade.shares, trade.price
                )
            else:
                # BUY — new position
                theme = trade.theme or instrument_themes.get(trade.ticker, "Unknown")
                new.positions[trade.ticker] = Position(
                    ticker=trade.ticker,
                    shares=trade.shares,
                    avg_entry=round(trade.price, 3),
                    theme=theme,
                )

        elif trade.action in (TradeAction.SELL, TradeAction.EXIT):
            if trade.ticker not in new.positions:
                raise ValueError(f"Cannot sell {trade.ticker}: not in portfolio")
            pos = new.positions[trade.ticker]
            if trade.action == TradeAction.EXIT:
                proceeds = pos.shares * trade.price
                new.cash += proceeds
                del new.positions[trade.ticker]
            else:
                if trade.shares > pos.shares:
                    raise ValueError(f"Cannot sell {trade.shares} shares of {trade.ticker}: only hold {pos.shares}")
                proceeds = trade.shares * trade.price
                new.cash += proceeds
                remaining = pos.shares - trade.shares
                if remaining == 0:
                    del new.positions[trade.ticker]
                else:
                    new.positions[trade.ticker] = Position(
                        ticker=pos.ticker,
                        shares=remaining,
                        avg_entry=pos.avg_entry,
                        theme=pos.theme,
                    )
            continue

    # Deduct total cost for buys/adds
    new.cash -= total_cost

    # Validate cash floor
    post_cash_pct = new.cash / nav if nav else 0.0
    if post_cash_pct < cash_floor_pct:
        shortfall = (cash_floor_pct * nav) - new.cash
        raise CashFloorBreachError(post_cash_pct, cash_floor_pct, shortfall)

    return new


def mark_to_market(state: PortfolioState, prices: dict[str, float]) -> dict:
    """Compute current P&L and NAV from prices. Returns summary dict."""
    positions = []
    total_invested = 0.0
    total_pnl = 0.0

    for ticker, pos in state.positions.items():
        price = prices[ticker]
        val = pos.value(price)
        abs_pnl, pct_pnl = pos.pnl(price)
        total_invested += val
        total_pnl += abs_pnl
        positions.append({
            "ticker": ticker,
            "shares": pos.shares,
            "avg_entry": pos.avg_entry,
            "price": price,
            "value": round(val, 2),
            "pnl_eur": round(abs_pnl, 2),
            "pnl_pct": round(pct_pnl * 100, 1),
        })

    nav = total_invested + state.cash
    return {
        "positions": sorted(positions, key=lambda x: -x["value"]),
        "invested": round(total_invested, 2),
        "cash": round(state.cash, 2),
        "nav": round(nav, 2),
        "cash_pct": round(state.cash / nav * 100, 1) if nav else 0.0,
        "invested_pct": round(total_invested / nav * 100, 1) if nav else 0.0,
        "total_pnl": round(total_pnl, 2),
        "contributions": state.total_contributions,
        "gain": round(nav - state.total_contributions, 2),
        "gain_pct": round((nav - state.total_contributions) / state.total_contributions * 100, 1)
        if state.total_contributions
        else 0.0,
    }
