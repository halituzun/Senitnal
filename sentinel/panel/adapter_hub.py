"""V14 — Adapter Hub for intelligence adapter health aggregation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field, model_validator

from sentinel.adapters.trust import TrustBand
from sentinel.intelligence.schemas import SourceFamily  # noqa: TC001

if TYPE_CHECKING:
    from collections.abc import Sequence

_DEFAULT_FRESHNESS_HORIZON_MS: int = 300_000  # 5 minutes


class AdapterSignalStatus(BaseModel, frozen=True, extra="forbid"):
    """Health status for a single intelligence adapter."""

    adapter_id: str = Field(min_length=1)
    source_family: SourceFamily
    last_seen_ms: int | None = None
    trust_band: TrustBand
    is_fresh: bool
    is_healthy: bool


class AdapterHubStatus(BaseModel, frozen=True, extra="forbid"):
    """Aggregated health status across all registered adapters."""

    hub_id: str = Field(min_length=1)
    captured_at_ms: int = Field(ge=0)
    adapters: tuple[AdapterSignalStatus, ...]
    healthy_count: int = Field(ge=0)
    stale_count: int = Field(ge=0)
    degraded: bool

    @model_validator(mode="after")
    def _counts_bounded(self) -> AdapterHubStatus:
        n = len(self.adapters)
        if self.healthy_count + self.stale_count > n:
            raise ValueError(
                f"healthy_count ({self.healthy_count}) + stale_count "
                f"({self.stale_count}) exceeds adapter count ({n})"
            )
        return self


def _is_fresh(last_seen_ms: int | None, now_ms: int, horizon_ms: int) -> bool:
    if last_seen_ms is None:
        return False
    return (now_ms - last_seen_ms) <= horizon_ms


def build_adapter_hub_status(
    hub_id: str,
    captured_at_ms: int,
    adapter_statuses: Sequence[AdapterSignalStatus],
    *,
    freshness_horizon_ms: int = _DEFAULT_FRESHNESS_HORIZON_MS,
) -> AdapterHubStatus:
    """Build an aggregated hub status from individual adapter statuses.

    Freshness is re-evaluated against captured_at_ms using freshness_horizon_ms.
    An adapter is healthy if its trust band is not REVOKED/QUARANTINED and it is fresh.
    """
    enriched: list[AdapterSignalStatus] = []
    for s in adapter_statuses:
        fresh = _is_fresh(s.last_seen_ms, captured_at_ms, freshness_horizon_ms)
        healthy = s.trust_band not in {TrustBand.REVOKED, TrustBand.QUARANTINED} and fresh
        enriched.append(
            AdapterSignalStatus(
                adapter_id=s.adapter_id,
                source_family=s.source_family,
                last_seen_ms=s.last_seen_ms,
                trust_band=s.trust_band,
                is_fresh=fresh,
                is_healthy=healthy,
            )
        )
    healthy_count = sum(1 for s in enriched if s.is_healthy)
    stale_count = sum(1 for s in enriched if not s.is_fresh)
    degraded = healthy_count < len(enriched)
    return AdapterHubStatus(
        hub_id=hub_id,
        captured_at_ms=captured_at_ms,
        adapters=tuple(enriched),
        healthy_count=healthy_count,
        stale_count=stale_count,
        degraded=degraded,
    )
