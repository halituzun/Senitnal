"""V14 — Panel snapshot for portfolio observability."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field, model_validator

from sentinel.production.strategy_lifecycle import StrategyLifecycleState

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sentinel.production.portfolio import StrategyAllocation, StrategyPortfolioConfig
    from sentinel.production.review import DailyProductionReport, WeeklyProductionReport

_ACTIVE_STATES = frozenset(
    {StrategyLifecycleState.ACTIVE_LIVE, StrategyLifecycleState.LIMITED_LIVE}
)
_PAUSED_STATES = frozenset({StrategyLifecycleState.PAUSED})


class PanelStrategyRow(BaseModel, frozen=True, extra="forbid"):
    """Per-strategy view row shown in the panel."""

    strategy_id: str = Field(min_length=1)
    lifecycle_state: StrategyLifecycleState
    allocated_budget_try: float = Field(ge=0.0)
    current_edge_score: float = Field(ge=-1.0, le=1.0)
    current_risk_score: float = Field(ge=0.0, le=1.0)
    current_confidence: float = Field(ge=0.0, le=1.0)
    enabled: bool
    strategy_quality: float = Field(ge=0.0, le=1.0, default=1.0)


class PanelSnapshot(BaseModel, frozen=True, extra="forbid"):
    """Read-only portfolio panel snapshot."""

    snapshot_id: str = Field(min_length=1)
    captured_at_ms: int = Field(ge=0)
    portfolio_id: str = Field(min_length=1)
    approved_capital_value: float = Field(ge=0.0)
    total_allocated_try: float = Field(ge=0.0)
    active_strategy_count: int = Field(ge=0)
    paused_strategy_count: int = Field(ge=0)
    strategies: tuple[PanelStrategyRow, ...]
    daily_report_id: str | None = None
    weekly_report_id: str | None = None

    @model_validator(mode="after")
    def _counts_consistent(self) -> PanelSnapshot:
        active = sum(
            1 for s in self.strategies if s.lifecycle_state in _ACTIVE_STATES
        )
        paused = sum(
            1 for s in self.strategies if s.lifecycle_state in _PAUSED_STATES
        )
        if self.active_strategy_count != active:
            raise ValueError(
                f"active_strategy_count={self.active_strategy_count} "
                f"does not match rows ({active})"
            )
        if self.paused_strategy_count != paused:
            raise ValueError(
                f"paused_strategy_count={self.paused_strategy_count} "
                f"does not match rows ({paused})"
            )
        return self


def build_panel_snapshot(
    snapshot_id: str,
    captured_at_ms: int,
    portfolio_config: StrategyPortfolioConfig,
    allocations: Sequence[StrategyAllocation],
    *,
    daily_report: DailyProductionReport | None = None,
    weekly_report: WeeklyProductionReport | None = None,
    quality_scores: dict[str, float] | None = None,
) -> PanelSnapshot:
    """Build a read-only panel snapshot from live portfolio data."""
    qs = quality_scores or {}
    rows = tuple(
        PanelStrategyRow(
            strategy_id=a.strategy_id,
            lifecycle_state=a.lifecycle_state,
            allocated_budget_try=a.allocated_budget_try,
            current_edge_score=a.current_edge_score,
            current_risk_score=a.current_risk_score,
            current_confidence=a.current_confidence,
            enabled=a.enabled,
            strategy_quality=max(0.0, min(1.0, qs.get(a.strategy_id, 1.0))),
        )
        for a in allocations
    )
    total = sum(r.allocated_budget_try for r in rows)
    active_count = sum(1 for r in rows if r.lifecycle_state in _ACTIVE_STATES)
    paused_count = sum(1 for r in rows if r.lifecycle_state in _PAUSED_STATES)
    return PanelSnapshot(
        snapshot_id=snapshot_id,
        captured_at_ms=captured_at_ms,
        portfolio_id=portfolio_config.portfolio_id,
        approved_capital_value=portfolio_config.approved_capital_value,
        total_allocated_try=total,
        active_strategy_count=active_count,
        paused_strategy_count=paused_count,
        strategies=rows,
        daily_report_id=daily_report.report_id if daily_report else None,
        weekly_report_id=weekly_report.report_id if weekly_report else None,
    )
