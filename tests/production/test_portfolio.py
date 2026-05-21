"""V13 — Portfolio and production decision tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sentinel.intelligence.conviction import ActionabilityBand
from sentinel.intelligence.net_edge import compute_net_edge
from sentinel.production.portfolio import (
    LiveProductionDecisionInput,
    StrategyAllocation,
    StrategyPortfolioConfig,
    evaluate_live_production_decision,
)
from sentinel.production.strategy_lifecycle import StrategyLifecycleState
from sentinel.runtime.output import SystemOutput


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
    *,
    state: StrategyLifecycleState = StrategyLifecycleState.ACTIVE_LIVE,
    budget: float = 1_000.0,
    enabled: bool = True,
) -> StrategyAllocation:
    return StrategyAllocation(
        strategy_id="strat-1",
        lifecycle_state=state,
        allocated_budget_try=budget,
        max_entry_try=100.0,
        max_trades_per_day=10,
        current_edge_score=0.1,
        current_risk_score=0.2,
        current_confidence=0.7,
        enabled=enabled,
    )


def _input(**over: object) -> LiveProductionDecisionInput:
    base: dict[str, object] = {
        "decision_id": "d1",
        "strategy_id": "strat-1",
        "allocation": _alloc(),
        "portfolio_config": _cfg(),
        "net_edge": compute_net_edge(breakdown_id="b", gross_edge_pct=0.01, fee_pct=0.001),
        "fusion_confidence": 0.7,
        "fusion_source_agreement": 0.7,
        "fusion_contradiction": 0.1,
        "reaction_memory_similarity": 0.6,
        "execution_quality": 0.8,
        "market_regime_match": 0.7,
        "exchange_health": 0.9,
        "market_fresh": True,
        "finality_known": True,
        "bad_order_observed": False,
    }
    base.update(over)
    return LiveProductionDecisionInput(**base)  # type: ignore[arg-type]


class TestPortfolioConfig:
    def test_kill_switch_required(self) -> None:
        with pytest.raises(ValidationError):
            StrategyPortfolioConfig(
                portfolio_id="p",
                approved_capital_mode="FIXED_TRY",
                approved_capital_value=1000.0,
                max_total_daily_loss_try=100.0,
                max_open_orders=5,
                max_strategy_correlation=0.7,
                max_single_strategy_exposure=0.5,
                max_single_exchange_exposure=0.7,
                kill_switch_required=False,
            )


class TestAllocation:
    def test_budget_with_research_state_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _alloc(state=StrategyLifecycleState.RESEARCH, budget=100.0)

    def test_budget_with_paper_state_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _alloc(state=StrategyLifecycleState.PAPER, budget=100.0)

    def test_budget_zero_with_research_ok(self) -> None:
        a = _alloc(state=StrategyLifecycleState.RESEARCH, budget=0.0)
        assert a.allocated_budget_try == 0.0

    def test_rollback_state_must_disable(self) -> None:
        with pytest.raises(ValidationError):
            _alloc(state=StrategyLifecycleState.ROLLBACK_REQUIRED, budget=0.0, enabled=True)


class TestProductionDecision:
    def test_bad_order_blocks(self) -> None:
        d = evaluate_live_production_decision(_input(bad_order_observed=True))
        assert d.system_output is SystemOutput.BLOCK
        assert "bad_order_observed" in d.block_reasons

    def test_stale_market_blocks(self) -> None:
        d = evaluate_live_production_decision(_input(market_fresh=False))
        assert d.system_output is SystemOutput.BLOCK

    def test_unknown_finality_blocks(self) -> None:
        d = evaluate_live_production_decision(_input(finality_known=False))
        assert d.system_output is SystemOutput.BLOCK

    def test_negative_net_edge_blocks(self) -> None:
        bad_edge = compute_net_edge(
            breakdown_id="b",
            gross_edge_pct=0.001,
            fee_pct=0.01,
        )
        d = evaluate_live_production_decision(_input(net_edge=bad_edge))
        assert d.system_output is SystemOutput.BLOCK
        assert "net_edge_not_positive" in d.block_reasons

    def test_non_live_state_blocks(self) -> None:
        d = evaluate_live_production_decision(
            _input(allocation=_alloc(state=StrategyLifecycleState.PAPER, budget=0.0))
        )
        assert d.system_output is SystemOutput.BLOCK
        assert "strategy_not_live" in d.block_reasons

    def test_low_agreement_monitor(self) -> None:
        d = evaluate_live_production_decision(_input(fusion_source_agreement=0.2))
        assert d.system_output is SystemOutput.MONITOR

    def test_active_live_no_action_band(self) -> None:
        d = evaluate_live_production_decision(_input())
        assert d.actionability_band is ActionabilityBand.LIVE_CANDIDATE

    def test_safety_flags_pinned(self) -> None:
        d = evaluate_live_production_decision(_input())
        assert d.creates_action is False
        assert d.writes_external is False
        assert d.approves_trade is False

    def test_exchange_unhealthy_blocks(self) -> None:
        d = evaluate_live_production_decision(_input(exchange_health=0.2))
        assert d.system_output is SystemOutput.BLOCK

    def test_disabled_strategy_blocks(self) -> None:
        d = evaluate_live_production_decision(
            _input(
                allocation=_alloc(
                    state=StrategyLifecycleState.ACTIVE_LIVE, budget=0.0, enabled=False
                )
            )
        )
        assert d.system_output is SystemOutput.BLOCK
        assert "strategy_disabled" in d.block_reasons
