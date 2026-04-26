"""FRED (St. Louis Fed) DataProvider.

Fetches the latest observation for a given series via the FRED observations
endpoint. Requires FRED_API_KEY environment variable.

L6:  FRED returns value="." for observations not yet published. The provider
     fetches up to _LOOKBACK observations and returns the most recent
     non-missing one. If all are ".", raises HttpError → CLI fails loudly.

L16: PAYEMS (non-farm payrolls) gates are evaluated on MoM change, not level.
     Per-series units_param config routes PAYEMS to units=chg at fetch time.

ECB vintage is set to as_of (observation date) because SDMX carries no
release timestamp. For FRED, vintage = realtime_start (official release date).
"""

from __future__ import annotations

import os
from pathlib import Path

from scripts.data.http_client import HttpClient, HttpError
from scripts.data.provider import DataProvider, SeriesObservation

_BASE_URL = "https://api.stlouisfed.org/fred"
_LOOKBACK = 5   # max observations to scan past "." sentinel values

# Per-series metadata: (fred_units_param, snapshot_units_label)
# Default: "lin" (unchanged level). Override for series that need transforms.
_SERIES_META: dict[str, dict[str, str]] = {
    "CPIAUCSL": {"units_param": "lin",  "units_label": "index_1982_84_eq_100"},
    "UNRATE":   {"units_param": "lin",  "units_label": "pct"},
    "PAYEMS":   {"units_param": "chg",  "units_label": "chg_thousands"},   # L16
    "VIXCLS":   {"units_param": "lin",  "units_label": "index"},
}
_DEFAULT_META = {"units_param": "lin", "units_label": "index"}


class FredProvider(DataProvider):
    source_name = "FRED"
    rate_limit = 1.0   # seconds between requests

    def __init__(self, http_client: HttpClient) -> None:
        self._client = http_client
        self._api_key = os.environ["FRED_API_KEY"]

    def fetch(self, series_id: str) -> SeriesObservation:
        meta = _SERIES_META.get(series_id, _DEFAULT_META)
        # Pass api_key in params (FRED does not support auth headers).
        # The HTTP cache key hashes (url, params) including the key —
        # this is acceptable since data/.http_cache/ is filesystem-only.
        params = {
            "series_id": series_id,
            "api_key": self._api_key,
            "file_type": "json",
            "sort_order": "desc",
            "limit": str(_LOOKBACK),
            "units": meta["units_param"],
        }
        body = self._client.get(f"{_BASE_URL}/series/observations", params=params)

        import json
        data = json.loads(body)
        observations = data.get("observations", [])
        if not observations:
            raise HttpError(f"FRED {series_id}: empty observations list")

        # L6: scan past "." sentinel values to find most recent real value.
        for obs in observations:
            raw_value = obs.get("value", ".")
            if raw_value == ".":
                continue
            try:
                value = float(raw_value)
            except ValueError:
                continue
            return SeriesObservation(
                source=self.source_name,
                series_id=series_id,
                as_of=obs["date"],
                value=value,
                vintage=obs["realtime_start"],   # official FRED release date
                units=meta["units_label"],
            )

        raise HttpError(
            f"FRED {series_id}: all {_LOOKBACK} recent observations are missing ('.')"
        )
