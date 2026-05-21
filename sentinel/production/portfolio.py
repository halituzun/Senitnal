"""V13 — Strategy portfolio + production conviction.

Halit-approved portfolio config and per-strategy allocation.  Live
production decision aggregates V11 fusion + V12 reaction memory +
lifecycle + allocation + execution quality + exchange health.
Sentinel produces a closed-output decision; Gel.Al executes.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from sentinel.intelligence.conviction import ActionabilityBand
from sentinel.intelligence.net_edge import NetEdgeBreakdown  # noqa: TC001
from sentinel.production.strategy_lifecycle import StrategyLifecycleState
from sentinel.runtime.output import SystemOutput


class StrategyPortfolioConfig(BaseModel, frozen=True, extra="forbid"):
    """Halit-approved portfolio configuration."""

    portfolio_id: str = Field(min_length=1)
    approved_capital_mode: Literal["FIXED_TRY", "PERCENT_AVAILABLE", "ALL_AVAILABLE_BALANCE"]
    approved_capital_value: float = Field(ge=0.0)
    max_total_daily_loss_try: float = Field(ge=0.0)
    max_open_orders: int = Field(ge=0)
    max_strategy_correlation: float = Field(ge=0.0, le=1.0)
    max_single_strategy_exposure: float = Field(ge=0.0, le=1.0)
    max_single_exchange_exposure: float = Field(ge=0.0, le=1.0)
    kill_switch_required: bool = True

    @model_validator(mode="after")
    def _kill_switch_must_be_required(self) -> StrategyPortfolioConfig:
        if not self.kill_switch_required:
            raise ValueError("kill_switch_required must be True in portfolio config")
        return self


class StrategyAllocation(BaseModel, frozen=True, extra="forbid"):
    """Per-strategy budget and live state."""

    strategy_id: str = Field(min_length=1)
    lifecycle_state: StrategyLifecycleState
    allocated_budget_try: float = Field(ge=0.0)
    max_entry_try: float = Field(ge=0.0)
    max_trades_per_day: int = Field(ge=0)
    current_edge_score: float = Field(ge=-1.0, le=1.0)
    current_risk_score: float = Field(ge=0.0, le=1.0)
    current_confidence: float = Field(ge=0.0, le=1.0)
    enabled: bool = True

    @model_validator(mode="after")
    def _allocation_consistent_with_state(self) -> StrategyAllocation:
        if self.allocated_budget_try > 0 and self.lifecycle_state not in {
            StrategyLifecycleState.LIMITED_LIVE,
            StrategyLifecycleState.ACTIVE_LIVE,
        }:
            raise ValueError(
                "allocated_budget_try > 0 requires lifecycle_state in {limited_live, active_live}"
            )
        if self.lifecycle_state is StrategyLifecycleState.ROLLBACK_REQUIRED and self.enabled:
            raise ValueError("rollback_required strategy must be disabled")
        return self


class LiveProductionDecisionInput(BaseModel, frozen=True, extra="forbid"):
    """Inputs to the live production decision engine."""

    decision_id: str = Field(min_length=1)
    strategy_id: str = Field(min_length=1)
    allocation: StrategyAllocation
    portfolio_config: StrategyPortfolioConfig
    net_edge: NetEdgeBreakdown
    fusion_confidence: float = Field(ge=0.0, le=1.0)
    fusion_source_agreement: float = Field(ge=0.0, le=1.0)
    fusion_contradiction: float = Field(ge=0.0, le=1.0)
    reaction_memory_similarity: float = Field(ge=0.0, le=1.0)
    execution_quality: float = Field(ge=0.0, le=1.0)
    market_regime_match: float = Field(ge=0.0, le=1.0)
    exchange_health: float = Field(ge=0.0, le=1.0)
    market_fresh: bool
    finality_known: bool
    bad_order_observed: bool


class LiveProductionDecision(BaseModel, frozen=True, extra="forbid"):
    """Production decision; Sentinel never executes."""

    decision_id: str
    strategy_id: str
    system_output: SystemOutput
    actionability_band: ActionabilityBand
    edge_score: float = Field(ge=-1.0, le=1.0)
    risk_score: float = Field(ge=0.0, le=1.0)
    allowed_budget_try: float = Field(ge=0.0)
    block_reasons: tuple[str, ...] = Field(default_factory=tuple)
    creates_action: Literal[False] = False
    writes_external: Literal[False] = False
    approves_trade: Literal[False] = False


def evaluate_live_production_decision(
    inp: LiveProductionDecisionInput,
) -> LiveProductionDecision:
    """Aggregate all signals into a closed-output production decision."""
    reasons: list[str] = []

    # Hard gates.
    if inp.bad_order_observed:
        reasons.append("bad_order_observed")
    if not inp.market_fresh:
        reasons.append("market_stale")
    if not inp.finality_known:
        reasons.append("finality_unknown")
    if not inp.allocation.enabled:
        reasons.append("strategy_disabled")
    if inp.allocation.lifecycle_state is StrategyLifecycleState.ROLLBACK_REQUIRED:
        reasons.append("strategy_rollback_required")
    if inp.allocation.lifecycle_state in {
        StrategyLifecycleState.RESEARCH,
        StrategyLifecycleState.HISTORICAL_VALIDATED,
        StrategyLifecycleState.PAPER,
        StrategyLifecycleState.SHADOW,
        StrategyLifecycleState.CANARY,
        StrategyLifecycleState.PAUSED,
        StrategyLifecycleState.RETIRED,
    }:
        reasons.append("strategy_not_live")
    if inp.net_edge.net_edge_pct <= 0:
        reasons.append("net_edge_not_positive")
    if inp.exchange_health < 0.5:
        reasons.append("exchange_unhealthy")

    if reasons:
        return LiveProductionDecision(
            decision_id=inp.decision_id,
            strategy_id=inp.strategy_id,
            system_output=SystemOutput.BLOCK,
            actionability_band=ActionabilityBand.BLOCKED,
            edge_score=0.0,
            risk_score=1.0,
            allowed_budget_try=0.0,
            block_reasons=tuple(reasons),
        )

    edge_score = max(-1.0, min(1.0, inp.net_edge.net_edge_pct * 100.0))
    risk_score = max(
        0.0,
        min(
            1.0,
            inp.fusion_contradiction * 0.6 + (1.0 - inp.execution_quality) * 0.4,
        ),
    )

    if (
        inp.fusion_source_agreement < 0.4
        or inp.fusion_confidence < 0.3
        or inp.reaction_memory_similarity < 0.2
        or inp.market_regime_match < 0.3
    ):
        band = ActionabilityBand.CANDIDATE
        output = SystemOutput.MONITOR
        allowed_budget = 0.0
        reasons.append("insufficient_evidence_for_live")
    else:
        band = ActionabilityBand.LIVE_CANDIDATE
        output = SystemOutput.NO_ACTION
        # Allocation budget capped by strategy max entry.
        allowed_budget = min(inp.allocation.max_entry_try, inp.allocation.allocated_budget_try)

    return LiveProductionDecision(
        decision_id=inp.decision_id,
        strategy_id=inp.strategy_id,
        system_output=output,
        actionability_band=band,
        edge_score=edge_score,
        risk_score=risk_score,
        allowed_budget_try=allowed_budget,
        block_reasons=tuple(reasons),
    )


__all__ = [
    "LiveProductionDecision",
    "LiveProductionDecisionInput",
    "StrategyAllocation",
    "StrategyPortfolioConfig",
    "evaluate_live_production_decision",
]
