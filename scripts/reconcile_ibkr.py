#!/usr/bin/env python3
"""
Post-execution IBKR reconciliation script.
Run after manually placing War Room trades in the IBKR platform.

Connects (read-only) to TWS or IB Gateway, pulls today's BUY fills, and
updates local/PORTFOLIO.md with actual entry prices, quantities, and commissions.
Status changes from PENDING FILL → OPEN.

Usage:
    python3 scripts/reconcile_ibkr.py [--paper] [--date YYYY-MM-DD]

    --paper       Connect to paper trading (TWS port 7497 / Gateway 4002).
                  Default: live (TWS 7496 / Gateway 4001).
    --date        Reconcile fills for this date instead of today.

Requirements:
    pip install ib_insync
    TWS or IB Gateway must be running with API access enabled.
    (TWS: File → Global Configuration → API → Settings → Enable ActiveX and Socket Clients)
"""

import argparse
import re
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

try:
    from ib_insync import IB, util
except ImportError:
    print("ERROR: ib_insync not installed. Run: pip install ib_insync")
    sys.exit(1)

BASE           = Path(__file__).parent.parent
PORTFOLIO_PATH = BASE / "local" / "PORTFOLIO.md"
HOST           = "127.0.0.1"
CLIENT_ID      = 10  # use a non-default ID to avoid conflicts with TWS UI


# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------

def connect(paper: bool) -> IB:
    ib = IB()
    ports = (7497, 4002) if paper else (7496, 4001)
    mode  = "paper" if paper else "live"
    for port in ports:
        try:
            ib.connect(HOST, port, clientId=CLIENT_ID, readonly=True)
            print(f"Connected to IBKR {mode} on port {port}")
            return ib
        except Exception:
            continue
    print(f"ERROR: Could not connect to IBKR {mode}. Is TWS/Gateway running?")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Fill retrieval
# ---------------------------------------------------------------------------

def get_fills(ib: IB, target_date: date) -> dict:
    """
    Return aggregated BUY fills for target_date, keyed by base symbol.
    Multiple partial fills for the same symbol are VWAP-aggregated.
    """
    fills = ib.reqExecutions()
    util.sleep(1)  # allow commission reports to arrive

    aggregated = defaultdict(lambda: {
        "shares": 0.0, "cost": 0.0, "commission": 0.0,
        "exchange": "", "currency": "EUR",
    })

    for fill in fills:
        exec_time = fill.execution.time
        exec_dt = exec_time.date() if isinstance(exec_time, datetime) else datetime.strptime(exec_time[:8], "%Y%m%d").date()
        if exec_dt != target_date:
            continue
        if fill.execution.side != "BOT":
            continue

        symbol = fill.contract.symbol.upper()
        shares = fill.execution.shares
        price  = fill.execution.price
        comm   = fill.commissionReport.commission if fill.commissionReport else 0.0

        agg = aggregated[symbol]
        agg["cost"]       += shares * price
        agg["shares"]     += shares
        agg["commission"] += comm
        agg["exchange"]    = fill.contract.exchange
        agg["currency"]    = fill.contract.currency

    result = {}
    for symbol, agg in aggregated.items():
        if agg["shares"] > 0:
            result[symbol] = {
                "shares":     agg["shares"],
                "avg_price":  round(agg["cost"] / agg["shares"], 4),
                "total_cost": round(agg["cost"], 2),
                "commission": round(agg["commission"], 2),
                "exchange":   agg["exchange"],
                "currency":   agg["currency"],
            }
    return result


def get_fills_since(ib: IB, since_date: date) -> dict:
    """
    Return aggregated BUY fills from since_date up to today, keyed by base symbol.
    Commissions are summed across all fills per symbol.
    """
    fills = ib.reqExecutions()
    util.sleep(1)

    aggregated = defaultdict(lambda: {
        "shares": 0.0, "cost": 0.0, "commission": 0.0,
        "exchange": "", "currency": "EUR",
    })

    for fill in fills:
        exec_time = fill.execution.time
        exec_dt = exec_time.date() if isinstance(exec_time, datetime) else datetime.strptime(exec_time[:8], "%Y%m%d").date()
        if exec_dt < since_date or exec_dt > date.today():
            continue
        if fill.execution.side != "BOT":
            continue

        symbol = fill.contract.symbol.upper()
        shares = fill.execution.shares
        price  = fill.execution.price
        comm   = fill.commissionReport.commission if fill.commissionReport else 0.0

        agg = aggregated[symbol]
        agg["cost"]       += shares * price
        agg["shares"]     += shares
        agg["commission"] += comm
        agg["exchange"]    = fill.contract.exchange
        agg["currency"]    = fill.contract.currency

    result = {}
    for symbol, agg in aggregated.items():
        if agg["shares"] > 0:
            result[symbol] = {
                "shares":     agg["shares"],
                "avg_price":  round(agg["cost"] / agg["shares"], 4),
                "total_cost": round(agg["cost"], 2),
                "commission": round(agg["commission"], 2),
                "exchange":   agg["exchange"],
                "currency":   agg["currency"],
            }
    return result


def _base_symbol(ticker: str) -> str:
    """Strip exchange suffix: 'VWCE.DE' → 'VWCE', 'DFNS.PA' → 'DFNS'."""
    return ticker.split(".")[0].upper()


# ---------------------------------------------------------------------------
# local/PORTFOLIO.md patching
# ---------------------------------------------------------------------------

def _pending_tickers(text: str) -> list[str]:
    """Return tickers that have PENDING FILL status in the Holdings table."""
    tickers = []
    in_holdings = False
    for line in text.splitlines():
        if line.startswith("## Current Holdings"):
            in_holdings = True
        elif line.startswith("## ") and in_holdings:
            break
        if in_holdings and line.startswith("|") and "PENDING FILL" in line and "---" not in line:
            cols = [c.strip() for c in line.strip("|").split("|")]
            if cols and cols[0] not in ("Ticker", ""):
                tickers.append(cols[0])
    return tickers


def _fmt_shares(n: float) -> str:
    return str(int(n)) if n == int(n) else str(n)


def _patch_holdings_row(text: str, ticker: str, date_str: str, fill: dict) -> str:
    """Update the holdings table row for ticker with actual fill data."""
    shares   = fill["shares"]
    price    = fill["avg_price"]
    all_in   = round(fill["total_cost"] + fill["commission"], 2)

    lines = text.split("\n")
    new_lines = []
    for line in lines:
        stripped = line.strip("|").split("|")
        cols = [c.strip() for c in stripped]
        if (
            len(cols) >= 9
            and cols[0] == ticker
            and "PENDING FILL" in cols[8]
        ):
            cols[2] = date_str
            cols[3] = _fmt_shares(shares)
            cols[4] = str(price)
            cols[5] = f"€{all_in}"
            cols[8] = "OPEN"
            line = "| " + " | ".join(cols) + " |"
        new_lines.append(line)
    return "\n".join(new_lines)


def _patch_trade_row(text: str, ticker: str, date_str: str, fill: dict) -> str:
    """Update the trade history row for ticker (planned) with actual fill data."""
    shares = fill["shares"]
    price  = fill["avg_price"]
    total  = fill["total_cost"]
    comm   = fill["commission"]

    lines = text.split("\n")
    new_lines = []
    for line in lines:
        if ticker not in line or "(planned)" not in line.lower():
            new_lines.append(line)
            continue
        cols = [c.strip() for c in line.strip("|").split("|")]
        if len(cols) >= 6 and cols[2] == ticker:
            cols[0] = date_str
            cols[1] = "BUY"
            cols[3] = _fmt_shares(shares)
            cols[4] = str(price)
            cols[5] = str(total)
            if len(cols) > 6:
                cols[6] = str(comm) if comm > 0 else "—"
            if len(cols) > 7:
                cols[7] = cols[7].replace(" (planned)", "").replace("(planned)", "").strip()
            line = "| " + " | ".join(cols) + " |"
        new_lines.append(line)
    return "\n".join(new_lines)


def _parse_open_holdings(text: str) -> list[dict]:
    """Return all OPEN positions from the Current Holdings table."""
    positions = []
    in_holdings = False
    for line in text.splitlines():
        if line.startswith("## Current Holdings"):
            in_holdings = True
        elif line.startswith("## ") and in_holdings:
            break
        if not (in_holdings and line.startswith("|") and "---" not in line):
            continue
        cols = [c.strip() for c in line.strip("|").split("|")]
        if len(cols) < 9 or cols[0] in ("Ticker", "") or cols[8] != "OPEN":
            continue
        try:
            qty   = float(cols[3])
            price = float(cols[4])
            cost  = float(cols[5].lstrip("€~").replace(",", ""))
        except ValueError:
            continue
        positions.append({
            "ticker":     cols[0],
            "qty":        qty,
            "entry_price": price,
            "entry_cost": cost,
        })
    return positions


def _parse_total_nav(text: str) -> float | None:
    """Read Total NAV from the Portfolio Summary table."""
    m = re.search(r"\*\*Total NAV[^|]*\*\*\s*\|\s*€([\d,]+\.?\d*)", text)
    return float(m.group(1).replace(",", "")) if m else None


def _fetch_live_prices(positions: list[dict]) -> dict:
    """Fetch latest prices via yfinance; returns {} if unavailable."""
    try:
        import yfinance as yf
    except ImportError:
        return {}
    prices = {}
    for p in positions:
        try:
            prices[p["ticker"]] = round(float(yf.Ticker(p["ticker"]).fast_info.last_price), 2)
        except Exception:
            pass
    return prices


def _patch_summary(text: str, positions: list[dict], total_nav: float, prices: dict) -> str:
    """Rewrite the Portfolio Summary table with computed values."""
    total_invested = sum(p["entry_cost"] for p in positions)
    cash           = round(total_nav - total_invested, 2)
    invested_pct   = round(total_invested / total_nav * 100, 1) if total_nav else 0.0
    cash_pct       = round(cash / total_nav * 100, 1) if total_nav else 0.0
    n_open         = len(positions)

    # Unrealised P&L (requires live prices)
    if prices:
        unrealised = sum(
            round(prices[p["ticker"]] * p["qty"] - p["entry_cost"], 2)
            for p in positions if p["ticker"] in prices
        )
        pnl_str = f"€{unrealised:+.2f}"
    else:
        pnl_str = "n/a (yfinance unavailable)"

    # Equity exposure breakdown
    exposure_parts = [
        f"{p['ticker'].split('.')[0]} {round(p['entry_cost'] / total_nav * 100, 1)}%"
        for p in positions
    ]
    exposure_str = f"{invested_pct}% ({' + '.join(exposure_parts)})" if exposure_parts else "0%"

    def _sub(pattern, value, t):
        return re.sub(pattern, value, t, count=1)

    text = _sub(
        r"(\*\*Cash \(post-fill\)\*\*\s*\|\s*).*",
        rf"\g<1>€{cash:,.2f} ({cash_pct}%)",
        text,
    )
    text = _sub(
        r"(\*\*Invested \(post-fill\)\*\*\s*\|\s*).*",
        rf"\g<1>€{total_invested:,.2f} ({invested_pct}%)",
        text,
    )
    text = _sub(
        r"(\*\*Unrealised P&L\*\*\s*\|\s*).*",
        rf"\g<1>{pnl_str}",
        text,
    )
    text = _sub(
        r"(\*\*Number of open positions\*\*\s*\|\s*).*",
        rf"\g<1>{n_open}",
        text,
    )
    text = _sub(
        r"(\*\*Equity exposure[^|]*\*\*\s*\|\s*).*",
        rf"\g<1>{exposure_str}",
        text,
    )
    return text


def update_portfolio(fills: dict, target_date: date) -> tuple[int, list[str]]:
    text     = PORTFOLIO_PATH.read_text()
    warnings = []
    updated  = 0
    date_str = target_date.isoformat()

    for ticker in _pending_tickers(text):
        symbol = _base_symbol(ticker)
        fill   = fills.get(symbol)

        if not fill:
            warnings.append(f"No fill found for {ticker} ({symbol}) on {target_date}")
            continue

        text    = _patch_holdings_row(text, ticker, date_str, fill)
        text    = _patch_trade_row(text, ticker, date_str, fill)
        updated += 1
        all_in  = round(fill["total_cost"] + fill["commission"], 2)
        print(f"  {ticker}: {_fmt_shares(fill['shares'])} shares @ €{fill['avg_price']} "
              f"(total €{fill['total_cost']} + €{fill['commission']} comm = €{all_in})")

    # Update Portfolio Summary
    positions  = _parse_open_holdings(text)
    total_nav  = _parse_total_nav(text)
    if positions and total_nav:
        print("Fetching live prices for P&L...")
        prices = _fetch_live_prices(positions)
        text   = _patch_summary(text, positions, total_nav, prices)
        print(f"  Portfolio Summary updated (NAV €{total_nav:,.2f}, "
              f"{len(positions)} open position(s))")
    else:
        print("  Skipping Portfolio Summary — no open positions or NAV not found.")

    # Update "Last updated" header
    text = re.sub(
        r"(?m)^(> \*\*Last updated\*\*: ).*$",
        rf"\g<1>{date.today().isoformat()}",
        text,
    )

    PORTFOLIO_PATH.write_text(text)
    return updated, warnings


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Reconcile IBKR fills into local/PORTFOLIO.md"
    )
    parser.add_argument("--paper", action="store_true", help="Use paper trading connection")
    parser.add_argument("--date",  default=None,        help="Fill date YYYY-MM-DD (default: today)")
    parser.add_argument("--since", default=None,        help="Fetch all fills from YYYY-MM-DD up to today")
    args = parser.parse_args()

    if args.since and args.date:
        print("ERROR: use --date or --since, not both.")
        sys.exit(1)

    since_date = date.fromisoformat(args.since) if args.since else None
    target_date = date.fromisoformat(args.date) if args.date else date.today()

    if since_date:
        print(f"Reconciling {'paper' if args.paper else 'live'} fills from {since_date} to {date.today()}...")
    else:
        print(f"Reconciling {'paper' if args.paper else 'live'} fills for {target_date}...")

    ib = connect(args.paper)
    try:
        if since_date:
            fills = get_fills_since(ib, since_date)
        else:
            fills = get_fills(ib, target_date)
    finally:
        ib.disconnect()

    if not fills:
        print(f"No BUY fills found for {target_date}. Nothing to update.")
        sys.exit(0)

    print(f"Fills found: {list(fills.keys())}")
    updated, warnings = update_portfolio(fills, target_date)

    print(f"\n{updated} position(s) reconciled in local/PORTFOLIO.md.")
    for w in warnings:
        print(f"  WARNING: {w}")

    if warnings and not updated:
        print("\nCheck that your local/PORTFOLIO.md has PENDING FILL entries matching the above tickers.")
        print("IBKR uses base symbols (e.g. 'VWCE' not 'VWCE.DE') — the script strips suffixes automatically.")

    if updated:
        print("\nRe-run to refresh the dashboard:")
        print("  python3 scripts/generate_dashboard.py")


if __name__ == "__main__":
    main()
