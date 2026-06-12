"""Tests for scripts/reconcile_ibkr.py — 10-column ISIN-schema parse/patch foundation fix (Proposal 025)."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pytest

pytest.importorskip("ib_insync")  # module sys.exit(1)s on missing ib_insync at import

import scripts.reconcile_ibkr as rec  # noqa: E402

FIXTURE = Path(__file__).parent / "fixtures" / "portfolio_10col.md"


def _fixture_text() -> str:
    return FIXTURE.read_text()


def test_parse_open_holdings_10col():
    positions = rec._parse_open_holdings(_fixture_text())
    tickers = {p["ticker"] for p in positions}
    assert "WRLD.DE" in tickers          # OPEN row parses (returns [] pre-fix)
    assert "TSTX.DE" not in tickers       # PENDING FILL row excluded
    vwce = next(p for p in positions if p["ticker"] == "WRLD.DE")
    assert vwce["qty"] == 7.0
    assert vwce["entry_price"] == 842.50
    assert vwce["entry_cost"] == 5899.00


def test_patch_holdings_row_pending_to_open():
    fill = {"shares": 5.0, "avg_price": 10.0, "total_cost": 50.0, "commission": 1.0}
    patched = rec._patch_holdings_row(_fixture_text(), "TSTX.DE", "2026-06-04", fill)
    row = next(l for l in patched.splitlines() if l.startswith("| TSTX.DE"))
    cols = [c.strip() for c in row.strip("|").split("|")]
    assert cols[1] == "IE00TEST0001"      # ISIN preserved (col 1)
    assert cols[2] == "Test Pending Fund" # Name untouched (col 2)
    assert cols[3] == "2026-06-04"        # Entry Date (col 3)
    assert cols[4] == "5"                 # Quantity (col 4)
    assert cols[5] == "10.0"              # Entry Price (col 5)
    assert cols[6] == "€51.0"             # Entry Cost incl comm (col 6)
    assert cols[9] == "OPEN"              # Status flipped (col 9)


def test_update_portfolio_end_to_end(tmp_path, monkeypatch):
    ledger = tmp_path / "PORTFOLIO.md"
    ledger.write_text(_fixture_text())
    monkeypatch.setattr(rec, "PORTFOLIO_PATH", ledger)
    monkeypatch.setattr(rec, "_fetch_live_prices", lambda positions: {})
    fills = {"TSTX": {"shares": 5.0, "avg_price": 10.0, "total_cost": 50.0,
                      "commission": 1.0, "exchange": "IBIS", "currency": "EUR"}}
    updated, warnings = rec.update_portfolio(fills, date(2097, 6, 4))
    out = ledger.read_text()
    assert updated == 1
    row = next(l for l in out.splitlines() if l.startswith("| TSTX.DE"))
    cols = [c.strip() for c in row.strip("|").split("|")]
    assert cols[9] == "OPEN"              # Holdings PENDING FILL -> OPEN
    assert cols[1] == "IE00TEST0001"      # ISIN preserved
    th = next(l for l in out.splitlines() if l.startswith("| 2097-06-04 | BUY | TSTX.DE"))
    assert "(planned)" not in th.lower()  # Trade History planned row filled
    cash_line = next(l for l in out.splitlines() if l.strip().startswith("| **Cash**"))
    assert cash_line.rstrip().endswith("%)") and "€" in cash_line  # Summary now patches: Cash gains a (NN.N%) suffix the pre-patch no-op lacked (economics not hardcoded — fixture carries accepted-exposure values, S-31)


def _ledger_with_summary(summary_rows: str) -> str:
    """A minimal synthetic ledger: one OPEN holding + a Portfolio Summary built from
    the given rows. All values synthetic."""
    return (
        "## Current Holdings\n\n"
        "| Ticker | ISIN | Name | Entry Date | Quantity | Entry Price (€) | Entry Cost (incl. comm.) | Strategy | Stop-Loss | Current Status |\n"
        "|---|---|---|---|---|---|---|---|---|---|\n"
        "| AAA.DE | IE00TEST0001 | Test Fund | 2026-01-01 | 1 | 23815.64 | €23815.64 | Test | Mental -10% | OPEN |\n\n"
        "## Portfolio Summary\n\n"
        "| Metric | Value |\n|---|---|\n"
        + summary_rows +
        "\n## Notes\n"
    )


def test_summary_partial_patch_warns(tmp_path, monkeypatch):
    # 4 of 5 script-patched labels present; Cash drifted to 'Cash Reserve' -> 1 missed.
    rows = (
        "| **Total NAV** | €76,431.85 |\n"
        "| **Cash Reserve** | x |\n"
        "| **Invested (MTM)** | x |\n"
        "| **Unrealised P&L** | x |\n"
        "| **Number of open positions** | x |\n"
        "| **Equity exposure (% NAV)** | x |\n"
    )
    ledger = tmp_path / "PORTFOLIO.md"
    ledger.write_text(_ledger_with_summary(rows))
    monkeypatch.setattr(rec, "PORTFOLIO_PATH", ledger)
    monkeypatch.setattr(rec, "_fetch_live_prices", lambda positions: {})
    _, warnings = rec.update_portfolio({}, date(2097, 6, 10))
    assert any("Summary partially updated — 4/5 script-patched labels matched" in w for w in warnings)


def test_summary_full_noop_warns(tmp_path, monkeypatch):
    # Summary section present (Total NAV readable) but NONE of the 5 script-patched labels.
    rows = (
        "| **Total NAV** | €76,431.85 |\n"
        "| **Cash Reserve** | x |\n"
        "| **Capital Invested** | x |\n"
        "| **P&L** | x |\n"
        "| **Open positions** | x |\n"
        "| **Exposure** | x |\n"
    )
    ledger = tmp_path / "PORTFOLIO.md"
    ledger.write_text(_ledger_with_summary(rows))
    monkeypatch.setattr(rec, "PORTFOLIO_PATH", ledger)
    monkeypatch.setattr(rec, "_fetch_live_prices", lambda positions: {})
    _, warnings = rec.update_portfolio({}, date(2097, 6, 10))
    assert any("Summary not updated — 0/5 script-patched labels matched" in w for w in warnings)


# ---------------------------------------------------------------------------
# Proposal 026 / S-23: ISIN-thread + bare-ticker collision guard tests
# ---------------------------------------------------------------------------


class _FakeFastInfo:
    def __init__(self, price, currency="EUR"):
        self.last_price = price
        self.currency = currency


class _FakeTicker:
    def __init__(self, symbol): self._symbol = symbol

    @property
    def fast_info(self): return _FakeFastInfo(100.0)


class _FakeYF:
    Ticker = _FakeTicker


def _install_fake_yf(monkeypatch):
    monkeypatch.setitem(sys.modules, "yfinance", _FakeYF())


def _install_fake_yf_ccy(monkeypatch, ccy_map):
    """Install a fake yfinance whose fast_info.currency is per-symbol (default EUR)."""
    class _Tk:
        def __init__(self, symbol): self._symbol = symbol
        @property
        def fast_info(self): return _FakeFastInfo(59274.13, ccy_map.get(self._symbol, "EUR"))
    class _YF:
        Ticker = _Tk
    monkeypatch.setitem(sys.modules, "yfinance", _YF())


def test_isin_threaded_into_positions():
    positions = rec._parse_open_holdings(_fixture_text())
    vwce = next(p for p in positions if p["ticker"] == "WRLD.DE")
    assert vwce["isin"] == "IE00TEST0009"   # ISIN threaded from col 1


def test_guard_skips_bare_non_us_ticker(monkeypatch):
    _install_fake_yf(monkeypatch)
    positions = [{"ticker": "DFEN", "isin": "IE000YYE6WK5", "qty": 1.0, "entry_price": 100.0, "entry_cost": 100.0}]
    prices = rec._fetch_live_prices(positions)
    assert "DFEN" not in prices              # bare non-US ISIN skipped


def test_guard_prices_exchange_qualified(monkeypatch):
    _install_fake_yf(monkeypatch)
    positions = [{"ticker": "DFEN.DE", "isin": "IE000YYE6WK5", "qty": 1.0, "entry_price": 100.0, "entry_cost": 100.0}]
    prices = rec._fetch_live_prices(positions)
    assert prices.get("DFEN.DE") == 100.0    # qualified ticker priced


def test_guard_us_isin_bare_ticker_priced(monkeypatch):
    _install_fake_yf(monkeypatch)
    positions = [{"ticker": "SPY", "isin": "US78462F1030", "qty": 1.0, "entry_price": 500.0, "entry_cost": 500.0}]
    prices = rec._fetch_live_prices(positions)
    assert prices.get("SPY") == 100.0        # US-ISIN bare ticker = carve-out, priced


def test_guard_end_to_end_parse_then_fetch(monkeypatch):
    # parse a minimal 10-col holdings table containing a bare non-US OPEN row, then fetch ->
    # the bare row must be skipped, so a forgotten isin thread fails this test loudly.
    _install_fake_yf(monkeypatch)
    ledger = (
        "## Current Holdings\n\n"
        "| Ticker | ISIN | Name | Entry Date | Quantity | Entry Price (€) | Entry Cost (incl. comm.) | Strategy | Stop-Loss | Current Status |\n"
        "|--------|------|------|------------|----------|-----------------|--------------------------|----------|-----------|----------------|\n"
        "| DFEN | IE000YYE6WK5 | Test Defense Fund | 2020-01-01 | 1 | 100.00 | €100.00 | Test | Mental -10% | OPEN |\n\n"
        "## Trade History\n"
    )
    positions = rec._parse_open_holdings(ledger)
    prices = rec._fetch_live_prices(positions)
    assert "DFEN" not in prices


def test_patch_summary_partial_mark_annotation():
    # one priced + one skipped -> "(partial: 1/2 marks)"
    positions = [
        {"ticker": "WRLD.DE", "isin": "IE00TEST0009", "qty": 1.0, "entry_price": 100.0, "entry_cost": 100.0},
        {"ticker": "DFEN", "isin": "IE000YYE6WK5", "qty": 1.0, "entry_price": 100.0, "entry_cost": 100.0},
    ]
    text = "## Portfolio Summary\n\n| **Unrealised P&L** | x |\n\n## Notes\n"
    prices = {"WRLD.DE": 120.0}   # DFEN missing (guard-skipped)
    patched, _, _ = rec._patch_summary(text, positions, total_nav=76431.85, prices=prices)
    assert "partial: 1/2 marks" in patched


def test_s28_non_eur_venue_omitted_partial(tmp_path, monkeypatch, capsys):
    # EUR holding priced + USD holding skipped -> (partial: 1/2 marks) + WARNING, via update_portfolio.
    rows = (
        "| **Total NAV** | €76,431.85 |\n"
        "| **Cash** | x |\n"
        "| **Invested (MTM)** | x |\n"
        "| **Unrealised P&L** | x |\n"
        "| **Number of open positions** | x |\n"
        "| **Equity exposure (% NAV)** | x |\n"
    )
    holdings = (
        "## Current Holdings\n\n"
        "| Ticker | ISIN | Name | Entry Date | Quantity | Entry Price (€) | Entry Cost (incl. comm.) | Strategy | Stop-Loss | Current Status |\n"
        "|---|---|---|---|---|---|---|---|---|---|\n"
        "| EUREUR.DE | IE00TEST0001 | EUR Fund | 2026-01-01 | 1 | 23815.64 | €23815.64 | Test | Mental -10% | OPEN |\n"
        "| USDUSD.DE | IE00TEST0002 | USD Fund | 2026-01-01 | 1 | 48162.30 | €48162.30 | Test | Mental -10% | OPEN |\n\n"
        "## Portfolio Summary\n\n| Metric | Value |\n|---|---|\n" + rows + "\n## Notes\n"
    )
    ledger = tmp_path / "PORTFOLIO.md"
    ledger.write_text(holdings)
    monkeypatch.setattr(rec, "PORTFOLIO_PATH", ledger)
    _install_fake_yf_ccy(monkeypatch, {"EUREUR.DE": "EUR", "USDUSD.DE": "USD"})
    rec.update_portfolio({}, date(2097, 6, 10))
    out = ledger.read_text()
    assert "(partial: 1/2 marks)" in out          # USD mark omitted, EUR mark kept
    captured = capsys.readouterr().out
    assert "USDUSD.DE priced in USD — P&L mark omitted" in captured


def test_s28_all_non_eur_no_live_marks(tmp_path, monkeypatch):
    # Single USD holding -> prices == {} -> 'no live marks' message (not 'yfinance unavailable').
    holdings = (
        "## Current Holdings\n\n"
        "| Ticker | ISIN | Name | Entry Date | Quantity | Entry Price (€) | Entry Cost (incl. comm.) | Strategy | Stop-Loss | Current Status |\n"
        "|---|---|---|---|---|---|---|---|---|---|\n"
        "| USDUSD.DE | IE00TEST0002 | USD Fund | 2026-01-01 | 1 | 23815.64 | €23815.64 | Test | Mental -10% | OPEN |\n\n"
        "## Portfolio Summary\n\n| Metric | Value |\n|---|---|\n"
        "| **Total NAV** | €76,431.85 |\n"
        "| **Cash** | x |\n"
        "| **Invested (MTM)** | x |\n"
        "| **Unrealised P&L** | x |\n"
        "| **Number of open positions** | x |\n"
        "| **Equity exposure (% NAV)** | x |\n\n## Notes\n"
    )
    ledger = tmp_path / "PORTFOLIO.md"
    ledger.write_text(holdings)
    monkeypatch.setattr(rec, "PORTFOLIO_PATH", ledger)
    _install_fake_yf_ccy(monkeypatch, {"USDUSD.DE": "USD"})
    rec.update_portfolio({}, date(2097, 6, 10))
    out = ledger.read_text()
    assert "n/a (no live marks — see warnings above)" in out


def test_s28_gbp_minor_unit_skipped(monkeypatch):
    _install_fake_yf_ccy(monkeypatch, {"LSEX.L": "GBp"})
    positions = [{"ticker": "LSEX.L", "isin": "IE00TEST0003", "qty": 1.0, "entry_price": 59274.13, "entry_cost": 59274.13}]
    prices = rec._fetch_live_prices(positions)
    assert "LSEX.L" not in prices          # minor-unit (pence) treated as non-base -> skipped


def test_s28_unknown_currency_skipped(monkeypatch):
    _install_fake_yf_ccy(monkeypatch, {"NOCCY.DE": None})
    positions = [{"ticker": "NOCCY.DE", "isin": "IE00TEST0004", "qty": 1.0, "entry_price": 59274.13, "entry_cost": 59274.13}]
    prices = rec._fetch_live_prices(positions)
    assert "NOCCY.DE" not in prices         # unconfirmable currency -> skipped (skip-don't-misprice)


def test_s28_eur_venue_priced(monkeypatch):
    _install_fake_yf_ccy(monkeypatch, {"EUREUR.DE": "EUR"})
    positions = [{"ticker": "EUREUR.DE", "isin": "IE00TEST0001", "qty": 1.0, "entry_price": 59274.13, "entry_cost": 59274.13}]
    prices = rec._fetch_live_prices(positions)
    assert prices.get("EUREUR.DE") == 59274.13  # confirmed-EUR venue priced


def test_dod6_invariants_through_update_portfolio(tmp_path, monkeypatch):
    """DoD-6: cost & NAV invariants demonstrated THROUGH the update_portfolio entry-point."""
    import re as _re
    from datetime import date as _date
    ledger = tmp_path / "ledger.md"
    ledger.write_text(
        "## Current Holdings\n"
        "| Ticker | ISIN | Name | Entry Date | Quantity | Entry Price (€) | Entry Cost (incl. comm.) | Strategy | Stop-Loss | Current Status |\n"
        "|--|--|--|--|--|--|--|--|--|--|\n"
        "| WRLD.DE | IE00TEST0001 | Synthetic World ETF | 2099-04-21 | 7 | 842.50 | €5,899.00 | core | Mental -7% (€783.53) | OPEN |\n\n"
        "## Portfolio Summary\n\n| Metric | Value |\n|---|---|\n"
        "| **Total NAV** | €10,000.00 |\n| **Cash** | €0.00 |\n| **Invested (MTM)** | €0.00 |\n"
        "| **Unrealised P&L** | n/a |\n| **Number of open positions** | 0 |\n| **Equity exposure (% NAV)** | 0% |\n",
        encoding="utf-8")
    monkeypatch.setattr(rec, "PORTFOLIO_PATH", ledger)
    monkeypatch.setattr(rec, "_fetch_live_prices", lambda positions: {})
    rec.update_portfolio({}, _date(2097, 6, 10))
    text = ledger.read_text()
    positions = rec._parse_open_holdings(text)
    p = positions[0]
    assert abs(p["entry_cost"] - (p["qty"] * p["entry_price"] + 1.50)) < 0.01  # cost = qty*price + comm
    nav = rec._parse_total_nav(text)
    invested = sum(q["entry_cost"] for q in positions)
    m = _re.search(r"\*\*Cash\*\*\s*\|\s*€([\d,]+\.\d+)", text)
    cash = float(m.group(1).replace(",", ""))
    assert abs(cash - (nav - invested)) < 0.01  # cash = nav - invested (through _patch_summary)
