"""Shared builders for V8 canary tests."""

from __future__ import annotations

from sentinel.canary.candidate import (
    CanaryCandidateAction,
    CanaryCandidateSource,
    CanaryEnvironment,
)
from sentinel.canary.limits import (
    CanaryDecisionWindowState,
    CanaryMicroLiveBounds,
)
from sentinel.canary.veto import VetoRequest
from sentinel.types.neural_seed import ProvenanceRef


def make_candidate(
    *,
    candidate_id: str = "cand-1",
    environment: CanaryEnvironment = CanaryEnvironment.MICRO_LIVE_CANARY,
    expires_at_ms: int = 1_000_005_000,
    risk_score: float = 0.2,
    confidence: float = 0.7,
    staleness_ms: int = 50,
    expected_net_edge_pct: float = 0.4,
    liquidity_score: float = 0.5,
) -> CanaryCandidateAction:
    return CanaryCandidateAction(
        candidate_id=candidate_id,
        source=CanaryCandidateSource.GELAL_SHADOW,
        environment=environment,
        observed_at_ms=1_000_000_000,
        expires_at_ms=expires_at_ms,
        source_event_refs=("ev-1",),
        provenance_hash="sha256:p-1",
        scope_hash="sha256:scope-1",
        strategy_hash="sha256:strat-1",
        symbol_hash="sha256:sym-1",
        venue_hash="sha256:venue-1",
        notional_ref="tier:micro",
        risk_score=risk_score,
        confidence=confidence,
        staleness_ms=staleness_ms,
        latency_ms=30,
        orderbook_age_ms=10,
        spread_pct=0.05,
        liquidity_score=liquidity_score,
        expected_net_edge_pct=expected_net_edge_pct,
        expected_slippage_pct=0.05,
        expected_fee_pct=0.1,
    )


def make_bounds() -> CanaryMicroLiveBounds:
    return CanaryMicroLiveBounds(
        bounds_id="b-1",
        max_candidate_notional_ref="tier:micro",
        max_candidates_per_hour=100,
        max_vetoes_per_hour=100,
        max_unvetoed_candidates_per_hour=50,
        max_staleness_ms=2000,
        max_latency_ms=500,
        max_orderbook_age_ms=200,
        min_confidence=0.3,
        min_liquidity_score=0.1,
        max_risk_score=0.85,
    )


def make_window() -> CanaryDecisionWindowState:
    return CanaryDecisionWindowState(last_reset_at_ms=1_000_000_000)


def make_request(
    *,
    candidate: CanaryCandidateAction | None = None,
    now_ms: int = 1_000_001_000,
) -> VetoRequest:
    cand = candidate if candidate is not None else make_candidate()
    return VetoRequest(
        request_id=f"req-{cand.candidate_id}",
        candidate=cand,
        requested_at_ms=now_ms,
        deadline_ms=now_ms + 5000,
        provenance=ProvenanceRef(source_event_id=cand.candidate_id),
    )
