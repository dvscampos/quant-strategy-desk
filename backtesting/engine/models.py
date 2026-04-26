"""Shared data models for the backtesting engine."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional


class GateStatus(Enum):
    GREEN = "GREEN"
    AMBER = "AMBER"
    RED = "RED"


class VerdictResult(Enum):
    APPROVE = "APPROVE"
    FLAG = "FLAG"
    NA = "N/A"


class VerdictCategory(Enum):
    LEGITIMATE = "legitimate"
    NOISE = "noise"
    APPROVE = "approve"
    NA = "na"


class TradeAction(Enum):
    BUY = "BUY"
    ADD = "ADD"
    SELL = "SELL"
    EXIT = "EXIT"


@dataclass
class Position:
    ticker: str
    shares: int
    avg_entry: float
    theme: str

    @property
    def cost_basis(self) -> float:
        return self.shares * self.avg_entry

    def pnl(self, current_price: float) -> tuple[float, float]:
        """Returns (absolute P&L in EUR, percentage P&L)."""
        abs_pnl = self.shares * (current_price - self.avg_entry)
        pct_pnl = (current_price - self.avg_entry) / self.avg_entry if self.avg_entry else 0.0
        return abs_pnl, pct_pnl

    def trigger_price(self, trigger_pct: float = -0.08) -> float:
        return self.avg_entry * (1 + trigger_pct)

    def value(self, price: float) -> float:
        return self.shares * price

    def add_shares(self, new_shares: int, new_price: float) -> Position:
        """Return a new Position with additional shares at new_price."""
        total_shares = self.shares + new_shares
        new_avg = (self.shares * self.avg_entry + new_shares * new_price) / total_shares
        return Position(
            ticker=self.ticker,
            shares=total_shares,
            avg_entry=round(new_avg, 3),
            theme=self.theme,
        )


@dataclass
class PortfolioState:
    date: date
    session_number: int
    positions: dict[str, Position] = field(default_factory=dict)
    cash: float = 0.0
    total_contributions: float = 0.0

    def nav(self, prices: dict[str, float]) -> float:
        invested = sum(p.value(prices[p.ticker]) for p in self.positions.values())
        return invested + self.cash

    def invested_value(self, prices: dict[str, float]) -> float:
        return sum(p.value(prices[p.ticker]) for p in self.positions.values())

    def cash_pct(self, prices: dict[str, float]) -> float:
        n = self.nav(prices)
        return self.cash / n if n else 0.0

    def invested_pct(self, prices: dict[str, float]) -> float:
        return 1.0 - self.cash_pct(prices)

    def max_deployable(self, prices: dict[str, float], floor_pct: float = 0.30) -> float:
        """Max cash that can be deployed while staying above floor_pct."""
        n = self.nav(prices)
        return max(0.0, self.cash - floor_pct * n)

    def affordability_cap(self, prices: dict[str, float], cap_pct: float = 0.25) -> float:
        """Max share price allowed (25% of NAV)."""
        return cap_pct * self.nav(prices)

    def trigger_check(self, prices: dict[str, float], trigger_pct: float = -0.08) -> dict[str, dict]:
        """Check all positions against triggers. Returns {ticker: {price, trigger, buffer_pct, breached}}."""
        results = {}
        for ticker, pos in self.positions.items():
            trigger = pos.trigger_price(trigger_pct)
            price = prices[ticker]
            buffer = (price - trigger) / trigger if trigger else 0.0
            results[ticker] = {
                "price": price,
                "trigger": round(trigger, 2),
                "buffer_pct": round(buffer * 100, 1),
                "breached": price <= trigger,
            }
        return results

    def allocation_by_theme(self, prices: dict[str, float]) -> dict[str, dict]:
        """Returns {theme: {value, pct_nav}} including cash."""
        n = self.nav(prices)
        themes: dict[str, float] = {}
        for pos in self.positions.values():
            val = pos.value(prices[pos.ticker])
            themes[pos.theme] = themes.get(pos.theme, 0.0) + val
        result = {}
        for theme, val in sorted(themes.items(), key=lambda x: -x[1]):
            result[theme] = {"value": round(val, 2), "pct_nav": round(val / n * 100, 1) if n else 0.0}
        result["Cash"] = {"value": round(self.cash, 2), "pct_nav": round(self.cash / n * 100, 1) if n else 0.0}
        return result

    def copy(self) -> PortfolioState:
        return PortfolioState(
            date=self.date,
            session_number=self.session_number,
            positions={k: Position(v.ticker, v.shares, v.avg_entry, v.theme) for k, v in self.positions.items()},
            cash=self.cash,
            total_contributions=self.total_contributions,
        )


@dataclass
class Trade:
    action: TradeAction
    ticker: str
    shares: int
    price: float
    date: date
    theme: str = ""

    @property
    def cost(self) -> float:
        return self.shares * self.price


@dataclass
class GateResult:
    name: str
    level: str
    status: GateStatus
    detail: str = ""


@dataclass
class MacroSnapshot:
    date: date
    stoxx: float
    stoxx_ma50wk: float
    vix: float
    ecb_rate: float
    brent: float
    eurusd: float


@dataclass
class Verdict:
    agent: str
    result: VerdictResult
    note: str = ""
    category: Optional[VerdictCategory] = None
    session_number: int = 0


@dataclass
class AgentScore:
    agent: str
    total_approve: int = 0
    total_flag: int = 0
    total_na: int = 0
    noise_count: int = 0
    legitimate_count: int = 0
    cumulative_score: float = 0.0
    tier: str = ""
