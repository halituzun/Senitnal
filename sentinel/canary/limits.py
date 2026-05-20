"""V8 — Canary micro-live bounds and fail-closed checks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from sentinel.canary.candidate import CanaryCandidateAction  # noqa: TC001
from sentinel.canary.veto import VetoReason


class CanaryMicroLiveBounds(BaseModel):
    """Per-canary bounds artifact.

    Constitutional hard-stops (``kill_switch_blocks``,
    ``missing_policy_blocks``, ``missing_provenance_blocks``,
    ``expired_candidate_blocks``, ``fail_closed_on_error``) are
    ``Literal[True]`` — V8 cannot weaken them.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    bounds_id: str = Field(min_length=1)
    max_candidate_notional_ref: str = Field(min_length=1)
    max_candidates_per_hour: int = Field(ge=0, le=1000)
    max_vetoes_per_hour: int = Field(ge=0, le=1000)
    max_unvetoed_candidates_per_hour: int = Field(ge=0, le=1000)
    max_staleness_ms: int = Field(ge=0)
    max_latency_ms: int = Field(ge=0)
    max_orderbook_age_ms: int = Field(ge=0)
    min_confidence: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    min_liquidity_score: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    max_risk_score: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    kill_switch_blocks: Literal[True] = True
    missing_policy_blocks: Literal[True] = True
    missing_provenance_blocks: Literal[True] = True
    expired_candidate_blocks: Literal[True] = True
    fail_closed_on_error: Literal[True] = True


@dataclass(slots=True)
class CanaryDecisionWindowState:
    """Rolling per-hour counters for canary throttling."""

    candidates_seen_this_hour: int = 0
    vetoes_this_hour: int = 0
    unvetoed_this_hour: int = 0
    last_reset_at_ms: int = 0


def reset_window_if_due(state: CanaryDecisionWindowState, now_ms: int) -> None:
    """Reset hourly counters when more than one hour has elapsed."""
    if now_ms - state.last_reset_at_ms >= 3_600_000:
        state.candidates_seen_this_hour = 0
        state.vetoes_this_hour = 0
        state.unvetoed_this_hour = 0
        state.last_reset_at_ms = now_ms


def check_canary_bounds(
    *,
    candidate: CanaryCandidateAction,
    bounds: CanaryMicroLiveBounds,
    state: CanaryDecisionWindowState,
    now_ms: int,
) -> tuple[bool, tuple[VetoReason, ...]]:
    """Return ``(ok, reasons)``.

    ``ok=True`` only means **no bounds violation was found**; it is
    *not* trade approval.  Caller must continue evaluation.
    """
    reset_window_if_due(state, now_ms)
    reasons: list[VetoReason] = []

    if now_ms >= candidate.expires_at_ms:
        reasons.append(VetoReason.EXPIRED_CANDIDATE)
    if candidate.staleness_ms > bounds.max_staleness_ms:
        reasons.append(VetoReason.STALE_DATA)
    if candidate.latency_ms > bounds.max_latency_ms:
        reasons.append(VetoReason.STALE_DATA)
    if candidate.orderbook_age_ms > bounds.max_orderbook_age_ms:
        reasons.append(VetoReason.STALE_DATA)
    if candidate.risk_score > bounds.max_risk_score:
        reasons.append(VetoReason.HIGH_RISK)
    if candidate.confidence < bounds.min_confidence:
        reasons.append(VetoReason.LOW_CONFIDENCE)
    if candidate.liquidity_score < bounds.min_liquidity_score:
        reasons.append(VetoReason.LIQUIDITY_INSUFFICIENT)
    if state.candidates_seen_this_hour >= bounds.max_candidates_per_hour:
        reasons.append(VetoReason.CANARY_LIMIT_EXCEEDED)
    if state.unvetoed_this_hour >= bounds.max_unvetoed_candidates_per_hour:
        reasons.append(VetoReason.CANARY_LIMIT_EXCEEDED)
    if not candidate.provenance_hash:
        reasons.append(VetoReason.PROVENANCE_MISSING)

    return (len(reasons) == 0, tuple(reasons))


__all__ = [
    "CanaryDecisionWindowState",
    "CanaryMicroLiveBounds",
    "check_canary_bounds",
    "reset_window_if_due",
]
