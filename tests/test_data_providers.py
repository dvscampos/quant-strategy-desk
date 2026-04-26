"""Provider unit tests using vcrpy cassette replay.

Cassette strategy:
  - fred_cpiaucsl_success / ecb_dfr_success: recorded from real API, then
    api_key scrubbed (filter_query_parameters). These are golden fixtures.
  - fred_429, fred_malformed, ecb_malformed: hand-crafted to simulate
    error paths that cannot be reliably triggered on demand.

L1:  VCR is configured to filter 'api_key' query param and 'authorization'
     header so no secrets are ever written to cassette files.
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest
import vcr

from scripts.data.http_client import HttpClient, HttpError
from scripts.data.providers.fred import FredProvider
from scripts.data.providers.ecb import EcbProvider

FIXTURES = Path(__file__).parent / "fixtures" / "data"
CACHE_DIR = Path("/tmp/test_http_cache")

# L1: scrub api_key from query params and any auth headers in all cassettes.
_VCR = vcr.VCR(
    filter_query_parameters=["api_key"],
    filter_headers=["authorization", "Authorization"],
    record_mode="none",   # never make live calls in unit tests
)


def _fred_client(max_retry_after: float = 60.0) -> FredProvider:
    return FredProvider(HttpClient(
        cache_dir=CACHE_DIR, min_interval=0,
        max_retry_after=max_retry_after, skip_cache=True,
    ))


def _ecb_client() -> EcbProvider:
    return EcbProvider(HttpClient(cache_dir=CACHE_DIR, min_interval=0, skip_cache=True))


# ---- FRED success ----

@_VCR.use_cassette(str(FIXTURES / "fred_cpiaucsl_success.yaml"))
def test_fred_success():
    with patch.dict(os.environ, {"FRED_API_KEY": "REDACTED"}):
        obs = _fred_client().fetch("CPIAUCSL")
    assert obs.source == "FRED"
    assert obs.series_id == "CPIAUCSL"
    assert obs.value == pytest.approx(319.082)
    assert obs.as_of == "2026-02-28"
    assert obs.vintage == "2026-04-11"
    assert obs.units == "index_1982_84_eq_100"


# ---- FRED 429 with Retry-After exceeding cap → HttpError ----

@_VCR.use_cassette(str(FIXTURES / "fred_429.yaml"))
def test_fred_429_exceeds_cap():
    with patch.dict(os.environ, {"FRED_API_KEY": "REDACTED"}):
        with pytest.raises(HttpError, match="Retry-After=3600"):
            _fred_client(max_retry_after=60.0).fetch("CPIAUCSL")


# ---- FRED malformed JSON ----

@_VCR.use_cassette(str(FIXTURES / "fred_malformed.yaml"))
def test_fred_malformed_response():
    with patch.dict(os.environ, {"FRED_API_KEY": "REDACTED"}):
        with pytest.raises(Exception):
            _fred_client().fetch("CPIAUCSL")


# ---- ECB success ----

@_VCR.use_cassette(str(FIXTURES / "ecb_dfr_success.yaml"))
def test_ecb_success():
    obs = _ecb_client().fetch("DFR")
    assert obs.source == "ECB"
    assert obs.series_id == "DFR"
    assert obs.value == pytest.approx(2.00)
    assert obs.as_of == "2026-04-17"
    assert obs.vintage == obs.as_of   # L13: vintage == as_of for ECB
    assert obs.units == "pct"


# ---- ECB malformed (empty dataSets) ----

@_VCR.use_cassette(str(FIXTURES / "ecb_malformed.yaml"))
def test_ecb_malformed_response():
    with pytest.raises(HttpError, match="failed to parse SDMX-JSON"):
        _ecb_client().fetch("DFR")


# ---- ECB unknown alias → KeyError ----

def test_ecb_unknown_alias():
    with pytest.raises(KeyError, match="not in registry"):
        _ecb_client().fetch("UNKNOWN_SERIES")
