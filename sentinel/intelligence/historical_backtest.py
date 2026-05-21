"""V12 — Historical backtest aggregator.

Pure helper that aggregates historical reaction evidence by event
family and regime.  Returns distributions, not live proof.
Counterfactual remains synthetic.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from collections.abc import Iterable

from sentinel.intelligence.reaction_memory import ReactionMemoryRecord  # noqa: TC001
from sentinel.intelligence.reaction_taxonomy import HistoricalEventFamily  # noqa: TC001


class BacktestAggregate(BaseModel, frozen=True, extra="forbid"):
    """Aggregated historical evidence over a set of memory records."""

    aggregate_id: str = Field(min_length=1)
    event_family: HistoricalEventFamily
    sample_count: int = Field(ge=0)
    mean_btc_return: float
    failure_rate: float = Field(ge=0.0, le=1.0)
    stale_rate: float = Field(ge=0.0, le=1.0)
    mean_volatility_jump: float = Field(ge=0.0)
    mean_confidence: float = Field(ge=0.0, le=1.0)


def aggregate_records(
    *,
    aggregate_id: str,
    event_family: HistoricalEventFamily,
    records: Iterable[ReactionMemoryRecord],
    now_ms: int,
    stale_ms: int = 30 * 24 * 60 * 60 * 1000,
) -> BacktestAggregate:
    """Aggregate ``records`` for ``event_family`` into one evidence summary."""
    matching = [r for r in records if r.event_family is event_family]
    n = len(matching)
    if n == 0:
        return BacktestAggregate(
            aggregate_id=aggregate_id,
            event_family=event_family,
            sample_count=0,
            mean_btc_return=0.0,
            failure_rate=0.0,
            stale_rate=0.0,
            mean_volatility_jump=0.0,
            mean_confidence=0.0,
        )

    btc_returns = [r.market_reaction.btc_return for r in matching]
    vol_jumps = [r.market_reaction.volatility_jump for r in matching]
    confidences = [r.confidence for r in matching]

    failure_count = sum(r.contradiction_count for r in matching)
    total_sample = sum(max(r.sample_count, 1) for r in matching)
    failure_rate = min(1.0, failure_count / total_sample) if total_sample > 0 else 0.0

    stale_count = sum(1 for r in matching if (now_ms - r.last_seen_ms) > stale_ms)
    stale_rate = stale_count / n

    return BacktestAggregate(
        aggregate_id=aggregate_id,
        event_family=event_family,
        sample_count=n,
        mean_btc_return=sum(btc_returns) / n,
        failure_rate=failure_rate,
        stale_rate=stale_rate,
        mean_volatility_jump=sum(vol_jumps) / n,
        mean_confidence=sum(confidences) / n,
    )


__all__ = ["BacktestAggregate", "aggregate_records"]
