#!/usr/bin/env python3
"""
Benchmark comparison for BT v2.0 (Mar 2025 – Feb 2026).

Compares:
  1. Actual portfolio (+10.9% TWR on contributions)
  2. Pure IWDA DCA — same dates, €200/month, no cash floor, no War Room
  3. Pure S&P 500 EUR DCA — same dates, €200/month (SXR8.DE on XETRA)
  4. Tiered-floor portfolio — re-simulation using current risk framework rules:
       Micro-NAV (NAV < €2,000): €200 absolute minimum cash
       Standard NAV (≥ €2,000):  15% of NAV

Methodology note for the tiered-floor estimate:
  At each session (4 onwards), additional cash freed by the new floor is
  modelled as an extra IWDA purchase at that session's closing price, held
  to the valuation date. Sessions 1–3 are unchanged (the €200 absolute floor
  is MORE restrictive than 30% at NAV < €667, and gates/lot sizes were binding
  anyway). This is a lower-bound estimate — it ignores the compounding cascade
  (extra deployment in session N raises NAV and lowers the floor for session N+1).
"""

import sys
import warnings
import yfinance as yf
import pandas as pd

warnings.filterwarnings("ignore")

# ── Constants ────────────────────────────────────────────────────────────────

CONTRIBUTION     = 200.0
ACTUAL_FINAL_NAV = 2661.07
VALUATION_DATE   = "2026-02-27"

# Execution dates from PORTFOLIO_HISTORY.md
SESSION_DATES = [
    "2025-03-17", "2025-04-22", "2025-05-19", "2025-06-23",
    "2025-07-21", "2025-08-18", "2025-09-22", "2025-10-20",
    "2025-11-17", "2025-12-22", "2026-01-19", "2026-02-21",
]

# Post-execution cash at each session (from PORTFOLIO_HISTORY.md snapshots)
SESSION_CASH = [
    151.75,  # 1 Mar
    293.88,  # 2 Apr
    292.65,  # 3 May
    378.66,  # 4 Jun
    353.42,  # 5 Jul
    392.37,  # 6 Aug
    515.73,  # 7 Sep
    529.69,  # 8 Oct
    619.94,  # 9 Nov
    697.11,  # 10 Dec
    731.28,  # 11 Jan
    802.94,  # 12 Feb
]

# Post-execution NAV at each session
SESSION_NAV = [
    200.00,   # 1
    398.84,   # 2
    603.15,   # 3
    802.04,   # 4
    1010.23,  # 5
    1216.52,  # 6
    1453.19,  # 7
    1709.05,  # 8
    1897.52,  # 9
    2119.49,  # 10
    2424.51,  # 11
    2666.92,  # 12
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def nearest_price(prices: pd.Series, date: str) -> float:
    """Return closing price on or after date (skip weekends/holidays)."""
    target = pd.Timestamp(date)
    idx = prices.index.searchsorted(target)
    if idx >= len(prices):
        raise ValueError(f"No price found on or after {date}")
    return float(prices.iloc[idx])


def dca_return(prices: pd.Series, session_dates: list, contribution: float,
               valuation_date: str) -> dict:
    """Simulate monthly DCA and return performance metrics."""
    val_price = nearest_price(prices, valuation_date)
    shares = 0.0
    total_contributed = 0.0
    for d in session_dates:
        buy_price = nearest_price(prices, d)
        shares += contribution / buy_price
        total_contributed += contribution
    final_value = shares * val_price
    gain = final_value - total_contributed
    twr  = gain / total_contributed * 100
    return {
        "final_value":       round(final_value, 2),
        "total_contributed": round(total_contributed, 2),
        "gain":              round(gain, 2),
        "twr_pct":           round(twr, 2),
        "shares":            round(shares, 4),
        "val_price":         round(val_price, 2),
    }


def tiered_floor(nav: float) -> float:
    """Current risk framework cash floor."""
    if nav < 2000:
        return 200.0          # Micro-NAV: €200 absolute
    else:
        return nav * 0.15     # Standard: 15%


def old_floor(nav: float) -> float:
    """Backtest cash floor (flat 30%)."""
    return nav * 0.30


# ── Fetch price data ──────────────────────────────────────────────────────────

print("Fetching price data …")
start = "2025-03-01"
end   = "2026-03-01"

iwda_data  = yf.download("IWDA.AS",  start=start, end=end, auto_adjust=True, progress=False)
sp500_data = yf.download("SXR8.DE",  start=start, end=end, auto_adjust=True, progress=False)

for name, data in [("IWDA.AS", iwda_data), ("SXR8.DE", sp500_data)]:
    if data.empty:
        print(f"ERROR: could not fetch {name}. Check connectivity.")
        sys.exit(1)

iwda_close  = iwda_data["Close"].squeeze()
sp500_close = sp500_data["Close"].squeeze()

# ── 1 & 2. DCA benchmarks ─────────────────────────────────────────────────────

iwda_bench  = dca_return(iwda_close,  SESSION_DATES, CONTRIBUTION, VALUATION_DATE)
sp500_bench = dca_return(sp500_close, SESSION_DATES, CONTRIBUTION, VALUATION_DATE)

# ── 3. Tiered-floor estimate ───────────────────────────────────────────────────
#
# Cascade model: extra deployment in session N reduces available cash in N+1.
#
#   adj_cash[i] = SESSION_CASH[i] - cumulative_extra_deployed_before_i
#   extra_dep   = max(0, adj_cash - new_floor) - max(0, adj_cash - old_floor)
#
# This correctly captures the diminishing returns: once you've deployed more
# in early sessions, later sessions have less cash sitting above the floor.
# Sessions 1–3 are naturally unchanged (new floor ≥ old floor at NAV < €667;
# floor wasn't the binding constraint there — gates and lot sizes were).

extra_value      = 0.0
cumulative_extra = 0.0
val_price_iwda   = nearest_price(iwda_close, VALUATION_DATE)
extra_log        = []

for i, (d, cash, nav) in enumerate(zip(SESSION_DATES, SESSION_CASH, SESSION_NAV)):
    adj_cash = cash - cumulative_extra
    old_f    = old_floor(nav)
    new_f    = tiered_floor(nav)

    extra_dep = max(0.0, adj_cash - new_f) - max(0.0, adj_cash - old_f)
    extra_dep = max(0.0, extra_dep)

    if extra_dep < 1.0:
        extra_log.append((i + 1, d, round(old_f, 2), round(new_f, 2),
                          round(adj_cash, 2), 0.0, 0.0, 0.0))
        continue

    buy_price    = nearest_price(iwda_close, d)
    extra_shares = extra_dep / buy_price
    end_value    = extra_shares * val_price_iwda  # value at Feb-27

    cumulative_extra += extra_dep
    extra_value      += end_value  # total value of extra IWDA at valuation date

    extra_log.append((
        i + 1, d,
        round(old_f, 2), round(new_f, 2),
        round(adj_cash, 2),
        round(extra_dep, 2),
        round(extra_shares, 4),
        round(end_value, 2),
    ))

# The extra_value replaces the cash that was deployed (still in portfolio, now
# as IWDA shares). The net change to final NAV = extra_value - cumulative_extra.
tiered_nav  = ACTUAL_FINAL_NAV + (extra_value - cumulative_extra)
tiered_gain = tiered_nav - 2400.0
tiered_twr  = tiered_gain / 2400.0 * 100


# ── Output ────────────────────────────────────────────────────────────────────

SEP = "─" * 62

print()
print(SEP)
print("  BT v2.0 BENCHMARK COMPARISON  (Mar 2025 – Feb 2026)")
print(SEP)

rows = [
    ("Portfolio (actual)",       ACTUAL_FINAL_NAV, ACTUAL_FINAL_NAV - 2400, (ACTUAL_FINAL_NAV - 2400) / 2400 * 100),
    ("Portfolio + tiered floor", tiered_nav,       tiered_gain,             tiered_twr),
    ("IWDA DCA benchmark",       iwda_bench["final_value"],  iwda_bench["gain"],  iwda_bench["twr_pct"]),
    ("S&P 500 EUR DCA (SXR8)",   sp500_bench["final_value"], sp500_bench["gain"], sp500_bench["twr_pct"]),
]

print(f"\n{'Strategy':<28} {'Final NAV':>10}  {'Gain':>9}  {'TWR':>7}")
print("─" * 62)
for label, nav, gain, twr in rows:
    marker = " ◀" if label.startswith("Portfolio (actual)") else ""
    print(f"{label:<28} €{nav:>9,.2f}  €{gain:>+8,.2f}  {twr:>+6.1f}%{marker}")

print()
print(SEP)
print("  TIERED FLOOR — SESSION-LEVEL DETAIL")
print(SEP)
print(f"\n{'#':<3} {'Date':<12} {'Old floor':>10} {'New floor':>10} {'Adj cash':>10} {'Extra dep':>10} {'Shares':>8} {'Val@Feb27':>10}")
print("─" * 80)
for row in extra_log:
    n, d, old_f, new_f, adj, extra, shares, val = row
    if extra > 0:
        print(f"{n:<3} {d:<12} €{old_f:>9,.2f} €{new_f:>9,.2f} €{adj:>9,.2f} €{extra:>9,.2f} {shares:>7.4f}sh €{val:>9,.2f}")
    else:
        print(f"{n:<3} {d:<12} €{old_f:>9,.2f} €{new_f:>9,.2f} €{adj:>9,.2f} {'—':>10} {'—':>8} {'—':>10}")

print()
total_extra_dep = sum(r[5] for r in extra_log)
net_gain_extra  = extra_value - cumulative_extra
print(f"  Total additional deployment:    €{total_extra_dep:,.2f}")
print(f"  Value of extra IWDA at Feb-27:  €{extra_value:,.2f}")
print(f"  Net gain from tiered floor:     €{net_gain_extra:+,.2f}")
print(f"  Final NAV with tiered floor:    €{tiered_nav:,.2f}")
print()
print("  Note: lower-bound estimate. Ignores compounding cascade")
print("  (extra deployment in session N raises NAV → lower floor for N+1).")
print()

print(SEP)
print("  OUTPERFORMANCE vs BENCHMARKS")
print(SEP)
actual_twr  = (ACTUAL_FINAL_NAV - 2400) / 2400 * 100
tiered_twr_ = tiered_twr

for label, twr in [("IWDA DCA", iwda_bench["twr_pct"]), ("S&P 500 EUR DCA", sp500_bench["twr_pct"])]:
    delta_actual = actual_twr - twr
    delta_tiered = tiered_twr_ - twr
    sign_a = "+" if delta_actual >= 0 else ""
    sign_t = "+" if delta_tiered >= 0 else ""
    print(f"\n  vs {label}:")
    print(f"    Actual portfolio:       {sign_a}{delta_actual:.1f}pp")
    print(f"    Tiered-floor portfolio: {sign_t}{delta_tiered:.1f}pp")

print()
print(SEP)
print("  CONTEXT")
print(SEP)
print(f"\n  Portfolio cash drag (actual):   33.5% of contributions never deployed")
print(f"  IWDA DCA: 100% deployment, no floor, no gates, no process overhead")
print(f"  S&P 500 EUR DCA: same, tracking US large-cap via SXR8.DE (XETRA)")
print(f"  Gold (PPFB.DE) contributed +49.9% individual return — key outperformance driver")
print(f"  Tariff shock (Apr 2025): portfolio gates blocked equity, cash preserved")
print()
