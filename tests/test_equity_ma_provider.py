"""EquityMaProvider unit tests using monkeypatch (not vcrpy).

Builds a fake yf.Ticker whose .history(...) returns a real pandas DataFrame.
"""

from __future__ import annotations

from unittest.mock import MagicMock
import pytest
import pandas as pd
import numpy as np


def _make_fake_ticker(df):
    """Return a fake yf.Ticker whose .history(...) returns df."""
    fake_ticker = MagicMock()
    fake_ticker.history.return_value = df
    return fake_ticker


def _make_df(n_bars, final_close, ma_close=None):
    """Build a DataFrame with DatetimeIndex and Close column.

    Args:
        n_bars: total number of bars
        final_close: the last close value
        ma_close: if provided, the mean of the last 250 bars will equal this value
    """
    dates = pd.date_range(end="2026-06-22", periods=n_bars, freq="D")
    if ma_close is None:
        # Simple linear ramp
        closes = np.linspace(100, final_close, n_bars)
    else:
        # Construct closes such that the last 250 bars have mean = ma_close
        # First n_bars - 250 bars are just a ramp
        if n_bars < 250:
            closes = np.full(n_bars, ma_close)
            closes[-1] = final_close
        else:
            prefix = np.linspace(80, 100, n_bars - 250)
            # Last 250 bars: fill with ma_close, then set the last one to final_close
            # and adjust the rest to maintain the mean
            suffix = np.full(250, ma_close)
            suffix[-1] = final_close
            # Recalculate suffix to preserve mean
            # mean = (sum of 249 values + final_close) / 250 = ma_close
            # sum of 249 values = 250 * ma_close - final_close
            sum_249 = 250 * ma_close - final_close
            suffix[:-1] = sum_249 / 249
            closes = np.concatenate([prefix, suffix])
    df = pd.DataFrame({"Close": closes}, index=dates)
    return df


class TestDeviationMath:
    def test_deviation_math(self, monkeypatch):
        from scripts.data.providers.equity_ma import EquityMaProvider

        # Known final close = 110, known MA250 = 100 → deviation = (110-100)/100*100 = 10.0
        # Build a DataFrame where the last 250 values are exactly 100, except the last which is 110
        dates = pd.date_range(end="2026-06-22", periods=300, freq="D")
        closes = np.concatenate([
            np.full(50, 90.0),    # first 50 bars
            np.full(249, 100.0),  # next 249 bars (part of MA250)
            [110.0]               # last bar
        ])
        df = pd.DataFrame({"Close": closes}, index=dates)

        def fake_yf_ticker(symbol):
            return _make_fake_ticker(df)

        monkeypatch.setattr("yfinance.Ticker", fake_yf_ticker)

        provider = EquityMaProvider()
        obs = provider.fetch("^STOXX", max_age_days=None)

        # MA of last 250 = (249*100 + 110) / 250 = 100.04
        # Deviation = (110 - 100.04) / 100.04 * 100 ≈ 9.96
        # But let's just verify it's close and has correct metadata
        assert 9.9 < obs.value < 10.1
        assert obs.units == "pct_deviation_from_ma"
        assert obs.vintage == obs.as_of
        assert obs.as_of == "2026-06-22"


class TestBandGuardHigh:
    def test_band_guard_high_raises(self, monkeypatch):
        from scripts.data.providers.equity_ma import EquityMaProvider
        from scripts.data.http_client import HttpError

        # Final close 6311 (>2000) → raises HttpError
        df = _make_df(300, final_close=6311)

        def fake_yf_ticker(symbol):
            return _make_fake_ticker(df)

        monkeypatch.setattr("yfinance.Ticker", fake_yf_ticker)

        provider = EquityMaProvider()
        with pytest.raises(HttpError, match="likely wrong symbol"):
            provider.fetch("^STOXX", max_age_days=None)


class TestBandGuardNonpositive:
    def test_band_guard_zero_raises(self, monkeypatch):
        from scripts.data.providers.equity_ma import EquityMaProvider
        from scripts.data.http_client import HttpError

        df = _make_df(300, final_close=0)

        def fake_yf_ticker(symbol):
            return _make_fake_ticker(df)

        monkeypatch.setattr("yfinance.Ticker", fake_yf_ticker)

        provider = EquityMaProvider()
        with pytest.raises(HttpError, match="non-finite/non-positive"):
            provider.fetch("^STOXX", max_age_days=None)

    def test_band_guard_nan_raises(self, monkeypatch):
        from scripts.data.providers.equity_ma import EquityMaProvider
        from scripts.data.http_client import HttpError

        df = _make_df(300, final_close=np.nan)

        def fake_yf_ticker(symbol):
            return _make_fake_ticker(df)

        monkeypatch.setattr("yfinance.Ticker", fake_yf_ticker)

        provider = EquityMaProvider()
        with pytest.raises(HttpError, match="non-finite/non-positive"):
            provider.fetch("^STOXX", max_age_days=None)


class TestLowButPositiveProceeds:
    def test_low_but_positive_proceeds_and_reads_negative(self, monkeypatch):
        from scripts.data.providers.equity_ma import EquityMaProvider

        # Low positive level (50) below the MA (100) → deviation negative
        # Build a DataFrame where the last 250 values are exactly 100, except the last which is 50
        dates = pd.date_range(end="2026-06-22", periods=300, freq="D")
        closes = np.concatenate([
            np.full(50, 90.0),    # first 50 bars
            np.full(249, 100.0),  # next 249 bars (part of MA250)
            [50.0]                # last bar
        ])
        df = pd.DataFrame({"Close": closes}, index=dates)

        def fake_yf_ticker(symbol):
            return _make_fake_ticker(df)

        monkeypatch.setattr("yfinance.Ticker", fake_yf_ticker)

        provider = EquityMaProvider()
        obs = provider.fetch("^STOXX", max_age_days=None)

        # Must not raise; deviation is negative
        assert obs.value < 0


class TestInsufficientHistory:
    def test_insufficient_history_raises(self, monkeypatch):
        from scripts.data.providers.equity_ma import EquityMaProvider
        from scripts.data.http_client import HttpError

        # Only 100 bars (<250) → raises
        df = _make_df(100, final_close=110)

        def fake_yf_ticker(symbol):
            return _make_fake_ticker(df)

        monkeypatch.setattr("yfinance.Ticker", fake_yf_ticker)

        provider = EquityMaProvider()
        with pytest.raises(HttpError, match="insufficient history"):
            provider.fetch("^STOXX", max_age_days=None)


class TestImportError:
    def test_importerror_raises(self, monkeypatch):
        from scripts.data.providers.equity_ma import EquityMaProvider
        from scripts.data.http_client import HttpError
        import sys

        # Exercise the REAL import path: a None entry in sys.modules makes
        # `import yfinance` raise ImportError, so fetch()'s own try/except runs.
        monkeypatch.setitem(sys.modules, "yfinance", None)

        provider = EquityMaProvider()
        with pytest.raises(HttpError, match="yfinance not installed"):
            provider.fetch("^STOXX", max_age_days=None)


class TestBuildProvidersRoutesYfinance:
    def test_build_providers_routes_yfinance(self):
        from scripts.data.cli import _build_providers

        gates = {
            "data_staleness": {
                "retry": {"max_attempts": 1, "backoff_seconds_base": 0.1, "max_retry_after_seconds": 1},
                "series": {
                    "^STOXX": {"source": "YFINANCE", "amber_age_days": 5, "red_age_days": 10}
                },
            }
        }

        providers = _build_providers(gates)

        from scripts.data.providers.equity_ma import EquityMaProvider
        assert isinstance(providers["^STOXX"], EquityMaProvider)

    def test_build_providers_yfinance_fail_fast_on_unknown_alias(self):
        from scripts.data.cli import _build_providers

        gates = {
            "data_staleness": {
                "retry": {"max_attempts": 1, "backoff_seconds_base": 0.1, "max_retry_after_seconds": 1},
                "series": {
                    "^BOGUS": {"source": "YFINANCE", "amber_age_days": 5, "red_age_days": 10}
                },
            }
        }

        with pytest.raises(SystemExit):
            _build_providers(gates)
