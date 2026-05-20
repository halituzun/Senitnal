"""Shared builders for V7 paper tests."""

from __future__ import annotations

from sentinel.integrations.gelal_shadow import GelAlShadowEnvelope, GelAlShadowEventType
from sentinel.paper.opportunity import (
    PaperOpportunity,
    PaperOpportunityKind,
    PaperOpportunitySource,
)


def make_opportunity(
    *,
    opportunity_id: str = "po-1",
    kind: PaperOpportunityKind = PaperOpportunityKind.EDGE_CANDIDATE,
    confidence: float = 0.7,
    risk_score: float = 0.2,
    staleness_ms: int = 50,
    magnitude_score: float = 0.4,
    memory_echo_score: float | None = None,
    replay_evidence_score: float | None = None,
) -> PaperOpportunity:
    return PaperOpportunity(
        opportunity_id=opportunity_id,
        source=PaperOpportunitySource.MANUAL_FIXTURE,
        kind=kind,
        observed_at_ms=1_000_000,
        source_event_refs=("ev-1",),
        source_adapter_id="manual",
        provenance_hash="sha256:p-1",
        scope_hash="sha256:scope-1",
        confidence=confidence,
        magnitude_score=magnitude_score,
        risk_score=risk_score,
        staleness_ms=staleness_ms,
        latency_ms=30,
        liquidity_score=0.5,
        spread_score=0.05,
        memory_echo_score=memory_echo_score,
        replay_evidence_score=replay_evidence_score,
    )


def make_gelal_envelope(
    *,
    event_id: str = "ev-gelal-1",
    event_type: GelAlShadowEventType = GelAlShadowEventType.OPPORTUNITY_SEEN,
    environment: str = "shadow",
    payload: dict[str, object] | None = None,
) -> GelAlShadowEnvelope:
    if payload is None:
        payload = {"confidence": 0.6, "risk_score": 0.3, "latency_ms": 30}
    return GelAlShadowEnvelope(
        event_id=event_id,
        event_type=event_type,
        source_system="gel_al_borsa",
        observed_at_ms=1_000_000,
        exported_at_ms=1_000_020,
        source_table="t",
        source_row_id="r",
        source_hash="sha256:x",
        environment=environment,  # type: ignore[arg-type]
        strategy_name="latency-arb",
        symbol="BTC-USDT",
        venue="binance",
        payload=payload,
    )
