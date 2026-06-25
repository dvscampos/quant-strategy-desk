"""Equity Moving Average DataProvider.

Fetches the latest close and computes deviation from a 250-trading-day moving
average as a derived gate value. Used for the equity gate (STOXX 600 vs 50-week MA).

Convention: 50-week MA is computed as a 250-trading-day daily proxy (50 weeks × 5
    trading days). This is the canonical approximation for the `stoxx600_vs_50wk_ma`
    deployment gate.

Stored value: deviation percentage (level - MA) / MA × 100. This parallels PAYEMS
    storing a derived value (monthly change) rather than the level.

Vintage: latest daily close date. Fresh staleness (~1-day) aligns with daily gates
    (VIX, brent, EUR/USD).

Band-guard rationale: the guard is ASYMMETRIC by design. The lower bound (level ≤ 0
    or NaN) is a pure garbage-catcher — a real STOXX-600 level ≤ 0 is not a market
    floor, it is broken data. The upper bound (level > 2000) is a load-bearing
    wrong-symbol guard: ^STOXX → STOXX 600; the wrong sibling ^STOXX50E (EURO STOXX
    50) trades roughly an order of magnitude higher, so a bare-ticker collision would
    produce a level above the upper bound → hard failure, not silent mis-pricing. A
    severe-bear low STOXX-600 print during a 2008-style crash MUST flow through and
    read RED, never raise. The upper bound is calibrated to defeat wrong-symbol
    collisions, not to impose a market ceiling.
"""

from __future__ import annotations

import math

from scripts.data.http_client import HttpError
from scripts.data.provider import DataProvider, SeriesObservation

_MA_WINDOW_DAYS = 250  # 50-week MA computed as the canonical 250-trading-day daily proxy (50 wk × 5 trading days)
_SYMBOL_COLLISION_UPPER = 2000  # asymmetric band-guard UPPER bound: load-bearing wrong-symbol guard (^STOXX50E, the EURO STOXX 50, trades ~10× higher). The lower check (≤0/NaN) is a pure garbage-catcher, NOT a market floor — a severe-bear low STOXX-600 print MUST flow through and read RED, never raise.

_SERIES_REGISTRY: dict[str, str] = {
    "^STOXX": "pct_deviation_from_ma",  # alias -> units_label
}


class EquityMaProvider(DataProvider):
    source_name = "YFINANCE"
    rate_limit = 1.0

    def __init__(self, http_client=None) -> None:
        # http_client accepted for signature parallelism but unused (yfinance has its own HTTP)
        pass

    @classmethod
    def known_series(cls) -> set[str]:
        return set(_SERIES_REGISTRY)

    def fetch(self, series_id: str, *, max_age_days: float | None) -> SeriesObservation:
        if series_id not in _SERIES_REGISTRY:
            raise KeyError(
                f"EquityMaProvider series alias {series_id!r} not in registry. "
                f"Register it in scripts/data/providers/equity_ma.py -> _SERIES_REGISTRY."
            )

        # max_age_days accepted and ignored (yfinance fetches a fixed window)
        try:
            import yfinance as yf
        except ImportError as exc:
            raise HttpError(
                "EquityMaProvider: yfinance not installed — it is a load-bearing dependency for the equity gate"
            ) from exc

        try:
            df = yf.Ticker(series_id).history(period="2y", interval="1d", auto_adjust=True)
        except Exception as exc:
            raise HttpError(
                f"EquityMaProvider {series_id}: yfinance fetch failed — {exc}. "
                f"Re-run fetch after a brief wait."
            ) from exc

        if df is None or df.empty or len(df) < _MA_WINDOW_DAYS:
            actual_len = len(df) if df is not None and not df.empty else 0
            raise HttpError(
                f"EquityMaProvider {series_id}: insufficient history ({actual_len} bars < {_MA_WINDOW_DAYS})"
            )

        # Extract latest close as a scalar (defensive extraction pattern)
        val = df["Close"].iloc[-1]
        if hasattr(val, "iloc"):
            level = float(val.iloc[0])
        elif hasattr(val, "item"):
            level = float(val.item())
        else:
            level = float(val)

        # Band-guard on the latest level
        if level is None or math.isnan(level) or level <= 0:
            raise HttpError(
                f"EquityMaProvider {series_id}: non-finite/non-positive level {level} — garbage/no-data"
            )
        if level > _SYMBOL_COLLISION_UPPER:
            raise HttpError(
                f"EquityMaProvider {series_id}: level {level} > {_SYMBOL_COLLISION_UPPER} — "
                f"likely wrong symbol (e.g. ^STOXX50E)"
            )

        ma = float(df["Close"].tail(_MA_WINDOW_DAYS).mean())
        deviation = round((level - ma) / ma * 100, 4)
        as_of = df.index[-1].strftime("%Y-%m-%d")

        return SeriesObservation(
            source=self.source_name,
            series_id=series_id,
            as_of=as_of,
            value=deviation,
            vintage=as_of,
            units=_SERIES_REGISTRY[series_id],
        )
