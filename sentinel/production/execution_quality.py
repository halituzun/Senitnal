"""V13 — Execution quality feedback.

Tracks realized vs expected edge, fee/slippage/latency, finality and
bad-order counts.  Updates strategy quality score deterministically.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ExecutionQualityRecord(BaseModel, frozen=True, extra="forbid"):
    """One execution-quality observation for a strategy."""

    record_id: str = Field(min_length=1)
    strategy_id: str = Field(min_length=1)
    venue_hash: str = Field(min_length=1)
    expected_net_edge_pct: float
    realized_edge_pct: float
    fee_pct: float = Field(ge=0.0)
    slippage_pct: float = Field(ge=0.0)
    latency_ms: int = Field(ge=0)
    partial_fill_observed: bool
    cancel_success: bool
    finality_status: Literal["confirmed", "rejected", "timeout", "unknown"]
    reject_count: int = Field(ge=0)
    bad_order_count: int = Field(ge=0)
    venue_quality_score: float = Field(ge=0.0, le=1.0)
    strategy_quality_score: float = Field(ge=0.0, le=1.0)
    observed_at_ms: int = Field(ge=0)
    provenance_hash: str = Field(min_length=1)


def update_strategy_quality_from_record(
    *,
    previous_quality: float,
    record: ExecutionQualityRecord,
    alpha: float = 0.2,
) -> float:
    """EWMA-style update of strategy quality score.

    Deterministic.  bad_order_count > 0 or finality unknown crashes the
    quality score to zero; otherwise EWMA with ``alpha`` weight.
    """
    if record.bad_order_count > 0:
        return 0.0
    if record.finality_status in ("unknown", "timeout", "rejected"):
        return min(previous_quality, 0.2)
    edge_ratio = 0.0
    if record.expected_net_edge_pct > 0:
        edge_ratio = max(0.0, min(1.0, record.realized_edge_pct / record.expected_net_edge_pct))
    venue_factor = record.venue_quality_score
    candidate = 0.5 * edge_ratio + 0.5 * venue_factor
    if record.partial_fill_observed:
        candidate *= 0.9
    return max(0.0, min(1.0, (1.0 - alpha) * previous_quality + alpha * candidate))


__all__ = [
    "ExecutionQualityRecord",
    "update_strategy_quality_from_record",
]
