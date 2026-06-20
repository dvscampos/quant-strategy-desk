"""Eurostat dissemination API (JSON-stat) DataProvider.

Fetches the latest observation for a given series alias via the Eurostat
statistical dissemination API. No authentication required.

L13 (mirrors ecb.py): the JSON-stat payload carries a dataset-level `updated`
     timestamp (when Eurostat regenerated the whole dataset), NOT a per-observation
     release date — so it cannot be used as a per-obs vintage. Vintage is set to
     the observation's as_of (the monthly period id, e.g. "2026-05"). Staleness
     thresholds in gates.yml account for HICP's ~17-day publication lag.

L5 (mirrors ecb.py): series aliases are resolved to (dataset, dimension-filter,
     units_label) here. Unknown alias -> KeyError at fetch time; the CLI validates
     all configured aliases at startup (fail fast).

Sparse-encoding note: JSON-stat omits null/suppressed observations from the
     `value` object entirely. The parser selects the value at the HIGHEST time
     ordinal in dimension.time.category.index and looks it up by that exact
     ordinal key; if the latest period has no value entry (sparse/suppressed),
     it raises HttpError (loud fail -> CLI aborts) rather than silently returning
     an older period under the latest period's label.

     This assumes `value` is the OBJECT (ordinal-string-keyed) form — which the
     Eurostat dissemination API returns consistently (it is the sparse-capable
     encoding). JSON-stat also permits a dense ARRAY form; a dense response would
     raise (AttributeError on `.get`) and abort loudly via _fetch_all, never a
     silent wrong value — but if Eurostat ever switches encodings, handle the
     array form here.
"""

from __future__ import annotations

import json

from scripts.data.http_client import HttpClient, HttpError
from scripts.data.provider import DataProvider, SeriesObservation

_BASE_URL = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"

# Alias -> (dataset, dimension-filter, units_label)
# To add a new series: add an entry here AND in config/gates.yml data_staleness.
_SERIES_REGISTRY: dict[str, tuple[str, dict[str, str], str]] = {
    "ei_cphi_m.TOTAL.RT12.EA": (
        "ei_cphi_m",
        {"indic": "TOTAL", "unit": "RT12", "geo": "EA"},
        "pct_annual_rate",
    ),
}


class EurostatProvider(DataProvider):
    source_name = "EUROSTAT"
    rate_limit = 1.0   # seconds between requests

    def __init__(self, http_client: HttpClient) -> None:
        self._client = http_client

    @classmethod
    def known_series(cls) -> set[str]:
        return set(_SERIES_REGISTRY.keys())

    def fetch(self, series_id: str, *, max_age_days: float | None) -> SeriesObservation:
        if series_id not in _SERIES_REGISTRY:
            raise KeyError(
                f"Eurostat series alias {series_id!r} not in registry. "
                f"Register it in scripts/data/providers/eurostat.py -> _SERIES_REGISTRY."
            )
        dataset, dim_filter, units_label = _SERIES_REGISTRY[series_id]
        url = f"{_BASE_URL}/{dataset}"
        params = {"format": "JSON", "lastTimePeriod": "1", **dim_filter}
        body = self._client.get(url, params=params, max_age_days=max_age_days)
        value, as_of = _parse_jsonstat(body, series_id)
        return SeriesObservation(
            source=self.source_name,
            series_id=series_id,
            as_of=as_of,
            value=value,
            vintage=as_of,   # L13: Eurostat `updated` is dataset-level, not per-obs
            units=units_label,
        )


def _parse_jsonstat(body: str, series_id: str) -> tuple[float, str]:
    """Extract (value, period_id) for the latest time period from a JSON-stat body."""
    data = json.loads(body)
    try:
        time_index = data["dimension"]["time"]["category"]["index"]
        value_map = data["value"]
        # Latest = highest time ordinal (robust to lastTimePeriod>1 or reordering).
        latest_period, latest_ord = max(time_index.items(), key=lambda kv: kv[1])
    except (KeyError, TypeError, ValueError) as exc:
        raise HttpError(f"Eurostat {series_id}: failed to parse JSON-stat — {exc}") from exc
    raw = value_map.get(str(latest_ord))
    if raw is None:
        raise HttpError(
            f"Eurostat {series_id}: latest period {latest_period!r} (ordinal {latest_ord}) "
            f"absent/null in value map — sparse/suppressed observation."
        )
    try:
        return float(raw), latest_period
    except (TypeError, ValueError) as exc:
        raise HttpError(f"Eurostat {series_id}: non-numeric value {raw!r} — {exc}") from exc
