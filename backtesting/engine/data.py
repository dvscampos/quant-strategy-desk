"""Market data fetching and caching. All data is fetched, never hardcoded."""

from __future__ import annotations

import io
import sqlite3
from datetime import date, timedelta
from pathlib import Path

import exchange_calendars as xcals
import pandas as pd
import requests
import yfinance as yf

from .models import MacroSnapshot

DB_PATH = Path(__file__).parent / "backtest.db"

# yfinance ticker mapping for macro indicators
MACRO_TICKERS = {
    "stoxx": "^STOXX",
    "vix": "^VIX",
    "brent": "BZ=F",
    "eurusd": "EURUSD=X",
}

# Exchange calendars for holiday detection
# XETRA covers most of our instruments; Euronext Amsterdam for IWDA
_CALENDARS: dict[str, xcals.ExchangeCalendar] = {}


def _get_calendar(exchange: str = "XETR") -> xcals.ExchangeCalendar:
    """Get an exchange calendar (cached)."""
    if exchange not in _CALENDARS:
        _CALENDARS[exchange] = xcals.get_calendar(exchange)
    return _CALENDARS[exchange]


def _get_db(db_path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            ticker TEXT, date TEXT, close REAL,
            PRIMARY KEY (ticker, date)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ecb_rates (
            date TEXT PRIMARY KEY, rate REAL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS macro_cache (
            date TEXT, indicator TEXT, value REAL,
            PRIMARY KEY (date, indicator)
        )
    """)
    conn.commit()
    return conn


def third_saturday(year: int, month: int) -> date:
    """Compute the third Saturday of a given month."""
    # First day of month
    d = date(year, month, 1)
    # Find first Saturday (weekday 5)
    days_until_sat = (5 - d.weekday()) % 7
    first_sat = d + timedelta(days=days_until_sat)
    # Third Saturday = first + 14 days
    return first_sat + timedelta(days=14)


def next_trading_day(d: date, exchange: str = "XETR") -> date:
    """Find the next trading day on or after the given date."""
    cal = _get_calendar(exchange)
    # Move forward until we find a trading day
    check = d
    for _ in range(10):  # max 10 days forward (covers long holidays)
        if cal.is_session(pd.Timestamp(check)):
            return check
        check += timedelta(days=1)
    # Fallback: just return the date (shouldn't happen)
    return d


def execution_date(session_date: date, exchange: str = "XETR") -> date:
    """Get the execution date (next trading day after session Saturday)."""
    monday = session_date + timedelta(days=2)  # Saturday + 2 = Monday
    return next_trading_day(monday, exchange)


def last_trading_day_of_month(year: int, month: int, exchange: str = "XETR") -> date:
    """Find the last trading day of a given month."""
    cal = _get_calendar(exchange)
    # Last day of month
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)
    # Walk backward to find a trading day
    check = last_day
    for _ in range(10):
        if cal.is_session(pd.Timestamp(check)):
            return check
        check -= timedelta(days=1)
    return last_day


def fetch_prices(
    tickers: list[str],
    start: date,
    end: date,
    db_path: Path = DB_PATH,
) -> dict[str, pd.DataFrame]:
    """Fetch closing prices for tickers. Uses cache, fetches delta from yfinance."""
    conn = _get_db(db_path)
    result = {}

    for ticker in tickers:
        # Check cache
        cached = pd.read_sql_query(
            "SELECT date, close FROM prices WHERE ticker = ? AND date >= ? AND date <= ? ORDER BY date",
            conn,
            params=(ticker, start.isoformat(), end.isoformat()),
        )

        if not cached.empty:
            cached["date"] = pd.to_datetime(cached["date"])
            cached = cached.set_index("date")

        # Determine what we need to fetch
        if cached.empty:
            fetch_start = start
        else:
            last_cached = cached.index.max().date()
            if last_cached >= end:
                result[ticker] = cached
                continue
            fetch_start = last_cached + timedelta(days=1)

        # Fetch from yfinance
        df = yf.download(
            ticker,
            start=fetch_start.isoformat(),
            end=(end + timedelta(days=1)).isoformat(),
            progress=False,
        )

        if not df.empty:
            # Cache new data
            for idx, row in df.iterrows():
                val = row["Close"]
                # Extract scalar from Series if needed (yfinance may return either)
                if hasattr(val, "iloc"):
                    close_val = float(val.iloc[0])
                elif hasattr(val, "item"):
                    close_val = float(val.item())
                else:
                    close_val = float(val)
                dt = idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)
                conn.execute(
                    "INSERT OR REPLACE INTO prices (ticker, date, close) VALUES (?, ?, ?)",
                    (ticker, dt, close_val),
                )
            conn.commit()

        # Re-read full range from cache
        full = pd.read_sql_query(
            "SELECT date, close FROM prices WHERE ticker = ? AND date >= ? AND date <= ? ORDER BY date",
            conn,
            params=(ticker, start.isoformat(), end.isoformat()),
        )
        if not full.empty:
            full["date"] = pd.to_datetime(full["date"])
            full = full.set_index("date")
        result[ticker] = full

    conn.close()
    return result


def get_close_price(ticker: str, d: date, db_path: Path = DB_PATH) -> float:
    """Get closing price for a ticker on a specific date. Falls back to nearest prior day."""
    # Try exact date first, then look back up to 5 days
    start = d - timedelta(days=5)
    prices = fetch_prices([ticker], start, d, db_path)
    df = prices.get(ticker, pd.DataFrame())
    if df.empty:
        raise ValueError(f"No price data for {ticker} near {d}")
    return float(df.iloc[-1]["close"])


def get_execution_prices(tickers: list[str], exec_date: date, db_path: Path = DB_PATH) -> dict[str, float]:
    """Get closing prices for all tickers on execution date."""
    result = {}
    for ticker in tickers:
        result[ticker] = get_close_price(ticker, exec_date, db_path)
    return result


def get_eom_prices(tickers: list[str], year: int, month: int, db_path: Path = DB_PATH) -> dict[str, float]:
    """Get end-of-month closing prices for all tickers."""
    eom = last_trading_day_of_month(year, month)
    return get_execution_prices(tickers, eom, db_path)


def fetch_ecb_rate(d: date, db_path: Path = DB_PATH) -> float:
    """Fetch ECB Deposit Facility Rate from ECB Statistical Data Warehouse API.

    The DFR is the standard policy rate quoted for ECB decisions.
    The API provides the Main Refinancing Rate (MRR); DFR = MRR - 0.15
    (since the September 2024 corridor narrowing from 0.50 to 0.15).

    Caches DFR values in DB. Returns the rate effective on the given date.
    """
    conn = _get_db(db_path)

    # Check cache — find the most recent rate on or before the date
    row = conn.execute(
        "SELECT rate FROM ecb_rates WHERE date <= ? ORDER BY date DESC LIMIT 1",
        (d.isoformat(),),
    ).fetchone()

    if row:
        conn.close()
        return row[0]

    # Fetch MRR from ECB API, then compute DFR
    # Corridor: DFR = MRR - 0.15 (since Sep 18, 2024)
    # Before Sep 18, 2024: DFR = MRR - 0.50
    CORRIDOR_CHANGE_DATE = date(2024, 9, 18)
    url = (
        "https://data-api.ecb.europa.eu/service/data/FM/D.U2.EUR.4F.KR.MRR_FR.LEV"
        f"?startPeriod=2024-01-01&endPeriod={d.isoformat()}"
        "&format=csvdata"
    )
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        df = pd.read_csv(io.StringIO(resp.text))
        if "TIME_PERIOD" in df.columns and "OBS_VALUE" in df.columns:
            for _, r in df.iterrows():
                mrr = float(r["OBS_VALUE"])
                rate_date = date.fromisoformat(str(r["TIME_PERIOD"]))
                corridor = 0.15 if rate_date >= CORRIDOR_CHANGE_DATE else 0.50
                dfr = round(mrr - corridor, 2)
                conn.execute(
                    "INSERT OR REPLACE INTO ecb_rates (date, rate) VALUES (?, ?)",
                    (str(r["TIME_PERIOD"]), dfr),
                )
            conn.commit()
            # Re-query
            row = conn.execute(
                "SELECT rate FROM ecb_rates WHERE date <= ? ORDER BY date DESC LIMIT 1",
                (d.isoformat(),),
            ).fetchone()
            if row:
                conn.close()
                return row[0]
    except Exception as e:
        print(f"Warning: ECB API fetch failed ({e}). Using fallback.")

    conn.close()
    raise ValueError(f"Could not determine ECB rate for {d}")


def fetch_macro(d: date, db_path: Path = DB_PATH) -> MacroSnapshot:
    """Fetch all macro indicators for a given date. Everything is fetched, nothing hardcoded."""
    # STOXX 600 — need ~1 year of history for 50wk MA
    ma_start = d - timedelta(days=400)
    stoxx_data = fetch_prices(["^STOXX"], ma_start, d, db_path).get("^STOXX", pd.DataFrame())

    if stoxx_data.empty:
        raise ValueError(f"No STOXX 600 data available near {d}")

    stoxx_close = float(stoxx_data.iloc[-1]["close"])
    stoxx_ma = float(stoxx_data["close"].rolling(250).mean().dropna().iloc[-1]) if len(stoxx_data) >= 250 else stoxx_close

    # VIX
    vix_val = get_close_price("^VIX", d, db_path)

    # Brent
    brent_val = get_close_price("BZ=F", d, db_path)

    # EUR/USD
    eurusd_val = get_close_price("EURUSD=X", d, db_path)

    # ECB rate
    ecb_val = fetch_ecb_rate(d, db_path)

    return MacroSnapshot(
        date=d,
        stoxx=round(stoxx_close, 1),
        stoxx_ma50wk=round(stoxx_ma, 1),
        vix=round(vix_val, 1),
        ecb_rate=ecb_val,
        brent=round(brent_val, 2),
        eurusd=round(eurusd_val, 4),
    )
