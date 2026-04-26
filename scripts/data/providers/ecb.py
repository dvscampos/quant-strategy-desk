"""ECB Data Warehouse (SDMX-JSON) DataProvider.

Fetches the latest observation for a given series alias via the ECB
statistical data API. No authentication required.

L13: ECB SDMX responses do not expose an official publication/release date.
     `header.prepared` is the time the API generated the response payload —
     not when the data was released — so it cannot be used as vintage.
     Instead, vintage is set to the observation's as_of (observation date).
     Staleness thresholds in gates.yml are calibrated to account for ECB
     publication lags (e.g. HICP published ~17 days after observation date).

L5:  Series aliases (short names used in gates.yml) are resolved to SDMX
     dataflow + key pairs here. If an alias is not registered, the provider
     raises KeyError at fetch time. The CLI validates all configured aliases
     at startup before any network call (fail fast, no wasted requests).
"""

from __future__ import annotations

import json
from pathlib import Path

from scripts.data.http_client import HttpClient, HttpError
from scripts.data.provider import DataProvider, SeriesObservation

_BASE_URL = "https://data-api.ecb.europa.eu/service/data"

# Alias → (dataflow, key, units_label)
# To add a new series: add an entry here AND in config/gates.yml §data_staleness.
_SERIES_REGISTRY: dict[str, tuple[str, str, str]] = {
    "DFR": (
        "FM",
        "D.U2.EUR.4F.KR.DFR.LEV",
        "pct",
    ),
    "ICP.M.U2.N.000000.4.ANR": (
        "ICP",
        "M.U2.N.000000.4.ANR",
        "pct_annual_rate",
    ),
    "EXR.D.USD.EUR.SP00.A": (
        "EXR",
        "D.USD.EUR.SP00.A",
        "rate",
    ),
}


class EcbProvider(DataProvider):
    source_name = "ECB"
    rate_limit = 1.0   # seconds between requests

    def __init__(self, http_client: HttpClient) -> None:
        self._client = http_client

    @classmethod
    def known_series(cls) -> set[str]:
        return set(_SERIES_REGISTRY.keys())

    def fetch(self, series_id: str) -> SeriesObservation:
        if series_id not in _SERIES_REGISTRY:
            raise KeyError(
                f"ECB series alias {series_id!r} not in registry. "
                f"Register it in scripts/data/providers/ecb.py → _SERIES_REGISTRY."
            )
        dataflow, key, units_label = _SERIES_REGISTRY[series_id]
        url = f"{_BASE_URL}/{dataflow}/{key}"
        params = {"format": "jsondata", "lastNObservations": "1"}
        body = self._client.get(url, params=params)
        value, as_of = _parse_sdmx_json(body, series_id)
        return SeriesObservation(
            source=self.source_name,
            series_id=series_id,
            as_of=as_of,
            value=value,
            vintage=as_of,   # L13: ECB provides no release date; vintage = as_of
            units=units_label,
        )


def _parse_sdmx_json(body: str, series_id: str) -> tuple[float, str]:
    """Extract (value, observation_date) from ECB SDMX-JSON lastNObservations=1."""
    data = json.loads(body)
    try:
        dataset = data["dataSets"][0]
        series_data = dataset["series"]
        # With a single key-series query, there is exactly one series entry.
        series_key = next(iter(series_data))
        observations = series_data[series_key]["observations"]
        # observations is keyed by time-dimension index ("0" for lastN=1).
        obs_key = next(iter(observations))
        value = float(observations[obs_key][0])

        # Resolve the observation date from the time-dimension structure.
        structure = data["structure"]
        time_dim = structure["dimensions"]["observation"][0]
        obs_date = time_dim["values"][int(obs_key)]["id"]
        # ECB time periods: "2026-03" (monthly) → last day of month not needed;
        # store as-is (YYYY-MM for monthly, YYYY-MM-DD for daily).
        return value, obs_date
    except (KeyError, IndexError, StopIteration, ValueError) as exc:
        raise HttpError(f"ECB {series_id}: failed to parse SDMX-JSON — {exc}") from exc
