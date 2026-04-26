"""DataProvider ABC and SeriesObservation record.

One observation per (source, series_id) tuple per snapshot. Providers know
nothing about the snapshot format — they return SeriesObservation instances
and the SnapshotWriter assembles them into the locked on-disk schema.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import ClassVar


@dataclass(frozen=True)
class SeriesObservation:
    source: str        # "FRED" | "ECB"
    series_id: str     # e.g. "CPIAUCSL", "DFR"
    as_of: str         # ISO date of the datapoint itself (YYYY-MM-DD)
    value: float
    vintage: str       # ISO date the datapoint was released by the source
    units: str         # free-form but stable per series (e.g. "pct", "index_1982_84_eq_100")

    def to_dict(self) -> dict:
        return asdict(self)


class DataProvider(ABC):
    """Subclasses declare source_name and rate_limit, implement fetch().

    rate_limit is the minimum seconds between requests. The shared HttpClient
    enforces it; providers do not sleep themselves.
    """

    source_name: ClassVar[str]
    rate_limit: ClassVar[float]

    @abstractmethod
    def fetch(self, series_id: str) -> SeriesObservation:
        """Return the latest observation for series_id."""
        raise NotImplementedError
