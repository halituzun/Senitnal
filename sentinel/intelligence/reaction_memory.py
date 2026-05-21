"""V12 — Reaction memory store + selector.

In-memory store of historical reaction patterns.  ``usable_for_live``
gates whether a pattern may contribute to live conviction.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pydantic import BaseModel, Field, model_validator

from sentinel.intelligence.reaction_taxonomy import (
    HistoricalEventFamily,  # noqa: TC001
    MarketReactionMeasurement,  # noqa: TC001
    ReactionWindow,  # noqa: TC001
)

_MIN_SAMPLES_FOR_LIVE_USE = 5
_MAX_CONTRADICTION_FOR_LIVE_USE = 0.4
_STALE_DAYS_THRESHOLD_MS = 30 * 24 * 60 * 60 * 1000


class ReactionMemoryRecord(BaseModel, frozen=True, extra="forbid"):
    """One historical reaction pattern."""

    record_id: str = Field(min_length=1)
    event_family: HistoricalEventFamily
    event_signature_hash: str = Field(min_length=1)
    regime_signature_hash: str = Field(min_length=1)
    reaction_window: ReactionWindow
    market_reaction: MarketReactionMeasurement
    source_refs: tuple[str, ...] = Field(min_length=1)
    sample_count: int = Field(ge=0)
    confidence: float = Field(ge=0.0, le=1.0)
    contradiction_count: int = Field(ge=0)
    last_seen_ms: int = Field(ge=0)
    provenance_hash: str = Field(min_length=1)
    usable_for_live: bool = False

    @model_validator(mode="after")
    def _usable_for_live_consistent(self) -> ReactionMemoryRecord:
        contradiction_ratio = (
            self.contradiction_count / self.sample_count if self.sample_count > 0 else 1.0
        )
        if self.usable_for_live:
            if self.sample_count < _MIN_SAMPLES_FOR_LIVE_USE:
                raise ValueError("usable_for_live=True requires sample_count >= threshold")
            if contradiction_ratio > _MAX_CONTRADICTION_FOR_LIVE_USE:
                raise ValueError("usable_for_live=True requires low contradiction ratio")
        return self


class ReactionPattern(BaseModel, frozen=True, extra="forbid"):
    """Aggregated reaction pattern across multiple records."""

    pattern_id: str = Field(min_length=1)
    event_family: HistoricalEventFamily
    regime_cluster: str = Field(min_length=1)
    expected_reaction_direction: float = Field(ge=-1.0, le=1.0)
    expected_volatility_change: float = Field(ge=0.0)
    expected_liquidity_change: float
    expected_latency_risk: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    sample_count: int = Field(ge=0)
    failure_count: int = Field(ge=0)


@dataclass
class InMemoryReactionMemoryStore:
    """In-memory reaction-memory store keyed by record_id."""

    records: dict[str, ReactionMemoryRecord] = field(
        default_factory=lambda: {},  # type: ignore[arg-type]
    )

    def insert(self, record: ReactionMemoryRecord) -> None:
        self.records[record.record_id] = record

    def by_family(self, family: HistoricalEventFamily) -> tuple[ReactionMemoryRecord, ...]:
        return tuple(r for r in self.records.values() if r.event_family is family)

    def usable_records(self, *, now_ms: int) -> tuple[ReactionMemoryRecord, ...]:
        return tuple(
            r
            for r in self.records.values()
            if r.usable_for_live and (now_ms - r.last_seen_ms) <= _STALE_DAYS_THRESHOLD_MS
        )


def is_record_usable_for_live(record: ReactionMemoryRecord, *, now_ms: int) -> bool:
    """Return True iff the record meets all gating criteria."""
    if not record.usable_for_live:
        return False
    if record.sample_count < _MIN_SAMPLES_FOR_LIVE_USE:
        return False
    contradiction_ratio = record.contradiction_count / max(record.sample_count, 1)
    if contradiction_ratio > _MAX_CONTRADICTION_FOR_LIVE_USE:
        return False
    return (now_ms - record.last_seen_ms) <= _STALE_DAYS_THRESHOLD_MS


__all__ = [
    "InMemoryReactionMemoryStore",
    "ReactionMemoryRecord",
    "ReactionPattern",
    "is_record_usable_for_live",
]
