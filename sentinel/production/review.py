"""V13 — Production review automation.

Daily and weekly reports for the strategy portfolio.  Reports are
JSON-serialisable Pydantic models — no panel rendering, no live
notification side-effects.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from sentinel.production.portfolio import StrategyAllocation  # noqa: TC001


class DailyProductionReport(BaseModel, frozen=True, extra="forbid"):
    """One daily snapshot of the production portfolio."""

    report_id: str = Field(min_length=1)
    report_date_ms: int = Field(ge=0)
    active_strategy_ids: tuple[str, ...] = Field(default_factory=tuple)
    paused_strategy_ids: tuple[str, ...] = Field(default_factory=tuple)
    opportunities_seen: int = Field(ge=0)
    orders_sent: int = Field(ge=0)
    fills: int = Field(ge=0)
    realized_edge_pct: float
    bad_orders: int = Field(ge=0)
    stale_rejects: int = Field(ge=0)
    finality_locked: int = Field(ge=0)
    allocation_changes: int = Field(ge=0)


class WeeklyProductionReport(BaseModel, frozen=True, extra="forbid"):
    """One weekly snapshot summarising trends."""

    report_id: str = Field(min_length=1)
    week_start_ms: int = Field(ge=0)
    edge_decay_score: float = Field(ge=-1.0, le=1.0)
    promotion_candidate_ids: tuple[str, ...] = Field(default_factory=tuple)
    demotion_candidate_ids: tuple[str, ...] = Field(default_factory=tuple)
    source_trust_drift_score: float = Field(ge=-1.0, le=1.0)
    adapter_trust_drift_score: float = Field(ge=-1.0, le=1.0)
    exchange_health_score: float = Field(ge=0.0, le=1.0)
    incident_count: int = Field(ge=0)


def build_daily_report(
    *,
    report_id: str,
    report_date_ms: int,
    allocations: tuple[StrategyAllocation, ...],
    opportunities_seen: int = 0,
    orders_sent: int = 0,
    fills: int = 0,
    realized_edge_pct: float = 0.0,
    bad_orders: int = 0,
    stale_rejects: int = 0,
    finality_locked: int = 0,
    allocation_changes: int = 0,
) -> DailyProductionReport:
    """Build a daily production report from allocations and counters."""
    from sentinel.production.strategy_lifecycle import StrategyLifecycleState

    active_ids = tuple(
        a.strategy_id
        for a in allocations
        if a.enabled
        and a.lifecycle_state
        in {
            StrategyLifecycleState.LIMITED_LIVE,
            StrategyLifecycleState.ACTIVE_LIVE,
        }
    )
    paused_ids = tuple(
        a.strategy_id for a in allocations if a.lifecycle_state is StrategyLifecycleState.PAUSED
    )
    return DailyProductionReport(
        report_id=report_id,
        report_date_ms=report_date_ms,
        active_strategy_ids=active_ids,
        paused_strategy_ids=paused_ids,
        opportunities_seen=opportunities_seen,
        orders_sent=orders_sent,
        fills=fills,
        realized_edge_pct=realized_edge_pct,
        bad_orders=bad_orders,
        stale_rejects=stale_rejects,
        finality_locked=finality_locked,
        allocation_changes=allocation_changes,
    )


def build_weekly_report(
    *,
    report_id: str,
    week_start_ms: int,
    edge_decay_score: float = 0.0,
    promotion_candidate_ids: tuple[str, ...] = (),
    demotion_candidate_ids: tuple[str, ...] = (),
    source_trust_drift_score: float = 0.0,
    adapter_trust_drift_score: float = 0.0,
    exchange_health_score: float = 1.0,
    incident_count: int = 0,
) -> WeeklyProductionReport:
    """Build a weekly summary report."""
    return WeeklyProductionReport(
        report_id=report_id,
        week_start_ms=week_start_ms,
        edge_decay_score=edge_decay_score,
        promotion_candidate_ids=promotion_candidate_ids,
        demotion_candidate_ids=demotion_candidate_ids,
        source_trust_drift_score=source_trust_drift_score,
        adapter_trust_drift_score=adapter_trust_drift_score,
        exchange_health_score=exchange_health_score,
        incident_count=incident_count,
    )


__all__ = [
    "DailyProductionReport",
    "WeeklyProductionReport",
    "build_daily_report",
    "build_weekly_report",
]
