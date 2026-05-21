"""V12 — Historical data adapter.

External limb service.  Loads cross-source historical archives
(exchange OHLCV/trades, Gel.Al metrics history, TAAPI historical
indicators, macro/news/social/commodity archives) and writes a
manifest with checksum and time-coverage metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from pydantic import BaseModel, Field


class HistoricalDataSource(StrEnum):
    """Closed set of supported historical data sources."""

    GELAL_METRICS = "gelal_metrics"
    EXCHANGE_OHLCV = "exchange_ohlcv"
    EXCHANGE_TRADES = "exchange_trades"
    TAAPI_HISTORICAL = "taapi_historical"
    MACRO_CALENDAR = "macro_calendar"
    NEWS = "news"
    SOCIAL_X = "social_x"
    COMMODITY = "commodity"
    ONCHAIN = "onchain"


class HistoricalDatasetManifest(BaseModel, frozen=True, extra="forbid"):
    """Manifest describing one historical dataset on disk."""

    manifest_id: str = Field(min_length=1)
    source: HistoricalDataSource
    coverage_start_ms: int = Field(ge=0)
    coverage_end_ms: int = Field(ge=0)
    record_count: int = Field(ge=0)
    checksum_sha256: str = Field(min_length=64, max_length=64)
    storage_path: str = Field(min_length=1)
    notes: str = ""


class HistoricalEventRecord(BaseModel, frozen=True, extra="forbid"):
    """One historical event row sourced from an adapter dataset."""

    event_id: str = Field(min_length=1)
    source: HistoricalDataSource
    family_tag: str = Field(min_length=1)
    occurred_at_ms: int = Field(ge=0)
    severity_score: float = Field(ge=0.0, le=1.0, default=0.0)
    provenance_hash: str = Field(min_length=1)


class HistoricalMarketReactionRecord(BaseModel, frozen=True, extra="forbid"):
    """One measured reaction tied to a HistoricalEventRecord."""

    reaction_id: str = Field(min_length=1)
    event_id: str = Field(min_length=1)
    btc_return: float
    volatility_jump: float = Field(ge=0.0)
    observed_at_ms: int = Field(ge=0)
    provenance_hash: str = Field(min_length=1)


@dataclass(frozen=True, slots=True)
class HistoricalAdapterConfig:
    """Adapter-level configuration for the historical loader."""

    enabled: bool
    source_paths: dict[HistoricalDataSource, str] = field(default_factory=dict)


__all__ = [
    "HistoricalAdapterConfig",
    "HistoricalDataSource",
    "HistoricalDatasetManifest",
    "HistoricalEventRecord",
    "HistoricalMarketReactionRecord",
]
