"""Tier 1 data layer — FRED + ECB snapshot substrate.

Phase 1A: snapshots are written, hashed and committed as audit trail.
No agent prompt consumes them yet — that lands in Phase 1B.
"""

from scripts.data.provider import DataProvider, SeriesObservation
from scripts.data.snapshot import SnapshotWriter

__all__ = ["DataProvider", "SeriesObservation", "SnapshotWriter"]
