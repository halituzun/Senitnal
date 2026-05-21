"""V13 — Production review automation tests."""

from __future__ import annotations

from sentinel.production.portfolio import StrategyAllocation
from sentinel.production.review import (
    build_daily_report,
    build_weekly_report,
)
from sentinel.production.strategy_lifecycle import StrategyLifecycleState


def _alloc(state: StrategyLifecycleState, sid: str, budget: float = 100.0) -> StrategyAllocation:
    return StrategyAllocation(
        strategy_id=sid,
        lifecycle_state=state,
        allocated_budget_try=budget
        if state in {StrategyLifecycleState.LIMITED_LIVE, StrategyLifecycleState.ACTIVE_LIVE}
        else 0.0,
        max_entry_try=100.0,
        max_trades_per_day=5,
        current_edge_score=0.1,
        current_risk_score=0.2,
        current_confidence=0.7,
        enabled=state is not StrategyLifecycleState.ROLLBACK_REQUIRED,
    )


class TestDailyReport:
    def test_active_and_paused_split(self) -> None:
        allocs = (
            _alloc(StrategyLifecycleState.ACTIVE_LIVE, "s-active"),
            _alloc(StrategyLifecycleState.PAUSED, "s-paused"),
            _alloc(StrategyLifecycleState.LIMITED_LIVE, "s-limited"),
            _alloc(StrategyLifecycleState.RETIRED, "s-ret"),
        )
        r = build_daily_report(
            report_id="d1",
            report_date_ms=1_000,
            allocations=allocs,
            opportunities_seen=12,
            orders_sent=3,
            fills=2,
            realized_edge_pct=0.005,
        )
        assert "s-active" in r.active_strategy_ids
        assert "s-limited" in r.active_strategy_ids
        assert "s-paused" in r.paused_strategy_ids
        assert "s-ret" not in r.active_strategy_ids

    def test_default_counts_zero(self) -> None:
        r = build_daily_report(report_id="d2", report_date_ms=1_000, allocations=())
        assert r.opportunities_seen == 0
        assert r.orders_sent == 0
        assert r.fills == 0


class TestWeeklyReport:
    def test_minimum_valid(self) -> None:
        r = build_weekly_report(report_id="w1", week_start_ms=1_000)
        assert r.edge_decay_score == 0.0
        assert r.incident_count == 0

    def test_carry_promotion_demotion(self) -> None:
        r = build_weekly_report(
            report_id="w2",
            week_start_ms=1_000,
            promotion_candidate_ids=("s1",),
            demotion_candidate_ids=("s2",),
            incident_count=1,
        )
        assert r.promotion_candidate_ids == ("s1",)
        assert r.demotion_candidate_ids == ("s2",)
        assert r.incident_count == 1
