"""V14 — Panel snapshot tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sentinel.panel.snapshot import (
    PanelSnapshot,
    build_panel_snapshot,
)
from sentinel.production.portfolio import StrategyAllocation, StrategyPortfolioConfig
from sentinel.production.review import build_daily_report, build_weekly_report
from sentinel.production.strategy_lifecycle import StrategyLifecycleState


def _cfg() -> StrategyPortfolioConfig:
    return StrategyPortfolioConfig(
        portfolio_id="p1",
        approved_capital_mode="FIXED_TRY",
        approved_capital_value=10_000.0,
        max_total_daily_loss_try=500.0,
        max_open_orders=5,
        max_strategy_correlation=0.7,
        max_single_strategy_exposure=0.5,
        max_single_exchange_exposure=0.7,
        kill_switch_required=True,
    )


def _alloc(
    sid: str,
    state: StrategyLifecycleState = StrategyLifecycleState.ACTIVE_LIVE,
    budget: float = 1_000.0,
) -> StrategyAllocation:
    live = {StrategyLifecycleState.ACTIVE_LIVE, StrategyLifecycleState.LIMITED_LIVE}
    return StrategyAllocation(
        strategy_id=sid,
        lifecycle_state=state,
        allocated_budget_try=budget if state in live else 0.0,
        max_entry_try=100.0,
        max_trades_per_day=5,
        current_edge_score=0.1,
        current_risk_score=0.2,
        current_confidence=0.7,
        enabled=state is not StrategyLifecycleState.ROLLBACK_REQUIRED,
    )


class TestBuildPanelSnapshot:
    def test_basic_snapshot(self) -> None:
        allocs = [_alloc("s1"), _alloc("s2", StrategyLifecycleState.PAUSED, 0.0)]
        snap = build_panel_snapshot(
            snapshot_id="snap-1",
            captured_at_ms=1_000,
            portfolio_config=_cfg(),
            allocations=allocs,
        )
        assert snap.snapshot_id == "snap-1"
        assert snap.portfolio_id == "p1"
        assert snap.active_strategy_count == 1
        assert snap.paused_strategy_count == 1
        assert snap.total_allocated_try == 1_000.0

    def test_empty_allocations(self) -> None:
        snap = build_panel_snapshot(
            snapshot_id="snap-empty",
            captured_at_ms=0,
            portfolio_config=_cfg(),
            allocations=[],
        )
        assert snap.active_strategy_count == 0
        assert snap.paused_strategy_count == 0
        assert snap.total_allocated_try == 0.0

    def test_quality_scores_applied(self) -> None:
        allocs = [_alloc("s1")]
        snap = build_panel_snapshot(
            snapshot_id="snap-q",
            captured_at_ms=1_000,
            portfolio_config=_cfg(),
            allocations=allocs,
            quality_scores={"s1": 0.42},
        )
        assert snap.strategies[0].strategy_quality == pytest.approx(0.42)

    def test_quality_clamped(self) -> None:
        allocs = [_alloc("s1")]
        snap = build_panel_snapshot(
            snapshot_id="snap-clamp",
            captured_at_ms=1_000,
            portfolio_config=_cfg(),
            allocations=allocs,
            quality_scores={"s1": 5.0},
        )
        assert snap.strategies[0].strategy_quality <= 1.0

    def test_daily_report_id_linked(self) -> None:
        allocs = [_alloc("s1")]
        dr = build_daily_report(report_id="dr1", report_date_ms=1_000, allocations=tuple(allocs))
        snap = build_panel_snapshot(
            snapshot_id="snap-dr",
            captured_at_ms=1_000,
            portfolio_config=_cfg(),
            allocations=allocs,
            daily_report=dr,
        )
        assert snap.daily_report_id == "dr1"

    def test_weekly_report_id_linked(self) -> None:
        wr = build_weekly_report(report_id="wr1", week_start_ms=1_000)
        snap = build_panel_snapshot(
            snapshot_id="snap-wr",
            captured_at_ms=1_000,
            portfolio_config=_cfg(),
            allocations=[],
            weekly_report=wr,
        )
        assert snap.weekly_report_id == "wr1"

    def test_count_mismatch_raises(self) -> None:
        with pytest.raises(ValidationError):
            PanelSnapshot(
                snapshot_id="bad",
                captured_at_ms=0,
                portfolio_id="p",
                approved_capital_value=1000.0,
                total_allocated_try=0.0,
                active_strategy_count=99,
                paused_strategy_count=0,
                strategies=(),
            )

    def test_limited_live_counts_as_active(self) -> None:
        allocs = [_alloc("s-lim", StrategyLifecycleState.LIMITED_LIVE, 500.0)]
        snap = build_panel_snapshot(
            snapshot_id="snap-lim",
            captured_at_ms=1_000,
            portfolio_config=_cfg(),
            allocations=allocs,
        )
        assert snap.active_strategy_count == 1

    def test_snapshot_is_frozen(self) -> None:
        allocs = [_alloc("s1")]
        snap = build_panel_snapshot(
            snapshot_id="snap-frz",
            captured_at_ms=1_000,
            portfolio_config=_cfg(),
            allocations=allocs,
        )
        with pytest.raises((TypeError, ValidationError)):
            snap.snapshot_id = "mutated"  # type: ignore[misc]
