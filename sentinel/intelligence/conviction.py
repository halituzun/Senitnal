"""V11 — Live conviction engine.

Combines V11 fusion result + net edge + execution quality + policy /
governance status + market freshness into a single live conviction
score and actionability band.  Always fail-closed.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from sentinel.intelligence.fusion import SignalFusionResult  # noqa: TC001
from sentinel.intelligence.net_edge import NetEdgeBreakdown  # noqa: TC001


class ActionabilityBand(StrEnum):
    """Closed set of live actionability bands."""

    BLOCKED = "blocked"
    WATCH = "watch"
    CANDIDATE = "candidate"
    LIVE_CANDIDATE = "live_candidate"


class LiveConvictionInput(BaseModel, frozen=True, extra="forbid"):
    """Inputs to the live conviction engine."""

    conviction_id: str = Field(min_length=1)
    fusion_result: SignalFusionResult
    net_edge: NetEdgeBreakdown
    execution_quality: float = Field(ge=0.0, le=1.0)
    active_policy_ok: bool
    governance_ok: bool
    market_fresh: bool
    balance_available: bool
    exchange_health: float = Field(ge=0.0, le=1.0)


class LiveConvictionResult(BaseModel, frozen=True, extra="forbid"):
    """Live conviction output with closed actionability band."""

    conviction_id: str
    conviction_score: float = Field(ge=0.0, le=1.0)
    actionability_band: ActionabilityBand
    block_reasons: tuple[str, ...] = Field(default_factory=tuple)
    source_refs: tuple[str, ...] = Field(default_factory=tuple)
    confidence: float = Field(ge=0.0, le=1.0)
    creates_action: Literal[False] = False
    approves_trade: Literal[False] = False

    @model_validator(mode="after")
    def _safety_flags_pinned(self) -> LiveConvictionResult:
        if self.creates_action is not False:
            raise ValueError("creates_action must be False")
        if self.approves_trade is not False:
            raise ValueError("approves_trade must be False")
        return self


def evaluate_live_conviction(inp: LiveConvictionInput) -> LiveConvictionResult:
    """Evaluate live conviction.  Fail-closed; never raises on bad input."""
    reasons: list[str] = []

    # Hard gates.
    if inp.net_edge.net_edge_pct <= 0:
        reasons.append("net_edge_not_positive")
    if not inp.market_fresh:
        reasons.append("market_data_stale")
    if not inp.active_policy_ok:
        reasons.append("policy_not_active")
    if not inp.governance_ok:
        reasons.append("governance_blocked")
    if not inp.balance_available:
        reasons.append("no_balance_available")
    if inp.exchange_health < 0.5:
        reasons.append("exchange_unhealthy")

    fusion = inp.fusion_result

    score = (
        max(inp.net_edge.net_edge_pct, 0.0)
        * fusion.liquidity_confidence
        * fusion.source_agreement_score
        * inp.execution_quality
        * inp.exchange_health
        * (1.0 - fusion.contradiction_pressure * 0.7)
    )
    # Normalize: cap to [0, 1].  Edge pct interpreted as fraction (e.g. 0.005).
    conviction_score = max(0.0, min(1.0, score * 100.0))

    if reasons:
        band = ActionabilityBand.BLOCKED
        confidence = 0.0
    elif fusion.confidence < 0.2 or conviction_score < 0.05:
        band = ActionabilityBand.WATCH
        confidence = fusion.confidence
        reasons.append("low_conviction")
    elif (
        fusion.source_agreement_score < 0.4
        or fusion.contradiction_pressure > 0.5
        or fusion.social_noise_pressure > 0.7
    ):
        band = ActionabilityBand.CANDIDATE
        confidence = fusion.confidence
        reasons.append("insufficient_source_agreement_for_live")
    else:
        band = ActionabilityBand.LIVE_CANDIDATE
        confidence = fusion.confidence

    return LiveConvictionResult(
        conviction_id=inp.conviction_id,
        conviction_score=conviction_score,
        actionability_band=band,
        block_reasons=tuple(reasons),
        source_refs=fusion.source_refs,
        confidence=confidence,
    )


__all__ = [
    "ActionabilityBand",
    "LiveConvictionInput",
    "LiveConvictionResult",
    "evaluate_live_conviction",
]
