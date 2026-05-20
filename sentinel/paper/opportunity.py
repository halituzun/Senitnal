"""V7 — Paper opportunity schemas + adapters.

Frozen Pydantic v2 models.  Raw symbol / venue / strategy / order /
account / API-key fields are rejected at construction.  Conversion
helpers strip those fields when building a ``PaperOpportunity`` from
V2 market envelopes or V5 Gel.Al shadow envelopes.
"""

from __future__ import annotations

import hashlib
from enum import StrEnum
from typing import Final, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sentinel.adapters.market_observation import MarketObservationEnvelope  # noqa: TC001
from sentinel.integrations.gelal_shadow import (
    GelAlShadowEnvelope,
    GelAlShadowEventType,
)


class PaperOpportunitySource(StrEnum):
    """Closed source-kind enum for a paper opportunity."""

    SYNTHETIC_MARKET = "synthetic_market"
    LOCAL_MARKET_JSONL = "local_market_jsonl"
    GELAL_SHADOW = "gelal_shadow"
    FINANCIAL_MEMORY_REPLAY = "financial_memory_replay"
    MANUAL_FIXTURE = "manual_fixture"


class PaperOpportunityKind(StrEnum):
    """Closed kind enum.  Carries no trade-side semantics."""

    MARKET_SPREAD = "market_spread"
    LIQUIDITY_SHIFT = "liquidity_shift"
    STALE_DATA_RISK = "stale_data_risk"
    HIGH_RISK_EVENT = "high_risk_event"
    BAD_ORDER_OBSERVATION = "bad_order_observation"
    KILL_SWITCH_OBSERVATION = "kill_switch_observation"
    SYSTEM_HEALTH_RISK = "system_health_risk"
    EDGE_CANDIDATE = "edge_candidate"
    UNKNOWN = "unknown"


# Forbidden top-level field names.  Pydantic ``extra='forbid'`` already
# blocks unknown attributes, but the explicit denylist documents the
# constitutional intent and is also referenced by adapter helpers.
_FORBIDDEN_FIELD_NAMES: Final[frozenset[str]] = frozenset(
    {
        "symbol",
        "venue",
        "exchange",
        "strategy_name",
        "side",
        "order_side",
        "order_type",
        "amount",
        "quantity",
        "qty",
        "api_key",
        "api_secret",
        "secret",
        "balance",
        "position",
        "leverage",
        "take_profit",
        "stop_loss",
        "trade_intent",
        "strategy_action",
        "execution_hint",
        "account_id",
        "wallet",
        "direct_order",
        "approve_trade",
        "reject_trade",
        "set_kill_switch",
        "clear_kill_switch",
    }
)


def _h(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


class PaperOpportunity(BaseModel):
    """Core-safe paper opportunity record."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    opportunity_id: str = Field(min_length=1)
    source: PaperOpportunitySource
    kind: PaperOpportunityKind
    observed_at_ms: int = Field(ge=0)
    source_event_refs: tuple[str, ...]
    source_adapter_id: str = Field(min_length=1)
    provenance_hash: str = Field(min_length=1)
    scope_hash: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    magnitude_score: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    risk_score: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    staleness_ms: int = Field(ge=0)
    latency_ms: int = Field(ge=0)
    liquidity_score: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    spread_score: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    replay_evidence_score: float | None = Field(default=None, ge=0.0, le=1.0, allow_inf_nan=False)
    memory_echo_score: float | None = Field(default=None, ge=0.0, le=1.0, allow_inf_nan=False)
    policy_scope_id: str | None = None
    observer_payload_ref: str | None = None

    @model_validator(mode="after")
    def _validate_opportunity(self) -> Self:
        if not self.source_event_refs:
            raise ValueError("source_event_refs must be non-empty")
        return self


def _bounded_score(value: object, default: float = 0.0) -> float:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        f = float(value)
        if 0.0 <= f <= 1.0:
            return f
    return default


def build_paper_opportunity_from_market_observation(
    envelope: MarketObservationEnvelope,
    *,
    source: PaperOpportunitySource = PaperOpportunitySource.LOCAL_MARKET_JSONL,
) -> PaperOpportunity:
    """Convert a V2 MarketObservationEnvelope into a PaperOpportunity.

    The raw symbol / venue / source_system are hashed into
    ``scope_hash`` and never propagated into the opportunity record.
    """
    scope_hash = _h(f"{envelope.source_system}|{envelope.venue}|{envelope.symbol}")

    spread_capped = min(envelope.spread_pct / 10.0, 1.0)
    magnitude = max(
        0.0,
        min(1.0, 0.5 * envelope.volatility_score + 0.5 * spread_capped),
    )
    # No risk_score on a pure market envelope; conservative default.
    risk = max(0.0, min(1.0, 0.3 * envelope.imbalance_score + 0.2 * spread_capped))
    liquidity = max(0.0, min(1.0, 0.6 + 0.4 * (1.0 - envelope.imbalance_score)))
    staleness_ms = envelope.orderbook_age_ms + envelope.latency_ms

    return PaperOpportunity(
        opportunity_id=f"paper-mkt-{envelope.event_id}",
        source=source,
        kind=PaperOpportunityKind.MARKET_SPREAD,
        observed_at_ms=envelope.observed_at_ms,
        source_event_refs=(envelope.event_id,),
        source_adapter_id=envelope.source_adapter_id,
        provenance_hash=envelope.provenance_hash,
        scope_hash=scope_hash,
        confidence=envelope.confidence,
        magnitude_score=magnitude,
        risk_score=risk,
        staleness_ms=staleness_ms,
        latency_ms=envelope.latency_ms,
        liquidity_score=liquidity,
        spread_score=spread_capped,
    )


_GELAL_KIND_MAP: Final[dict[GelAlShadowEventType, PaperOpportunityKind]] = {
    GelAlShadowEventType.MARKET_OBSERVATION: PaperOpportunityKind.MARKET_SPREAD,
    GelAlShadowEventType.OPPORTUNITY_SEEN: PaperOpportunityKind.EDGE_CANDIDATE,
    GelAlShadowEventType.OPPORTUNITY_BLOCKED: PaperOpportunityKind.EDGE_CANDIDATE,
    GelAlShadowEventType.RISK_GATE_DECISION: PaperOpportunityKind.HIGH_RISK_EVENT,
    GelAlShadowEventType.EXECUTION_ATTEMPT_OBSERVED: PaperOpportunityKind.EDGE_CANDIDATE,
    GelAlShadowEventType.PAPER_RESULT_OBSERVED: PaperOpportunityKind.EDGE_CANDIDATE,
    GelAlShadowEventType.LIVE_RESULT_OBSERVED: PaperOpportunityKind.EDGE_CANDIDATE,
    GelAlShadowEventType.SYSTEM_HEALTH_OBSERVED: PaperOpportunityKind.SYSTEM_HEALTH_RISK,
    GelAlShadowEventType.KILL_SWITCH_OBSERVED: PaperOpportunityKind.KILL_SWITCH_OBSERVATION,
}


def build_paper_opportunity_from_gelal_shadow(
    envelope: GelAlShadowEnvelope,
) -> PaperOpportunity:
    """Convert a V5 Gel.Al shadow envelope into a PaperOpportunity.

    Raw symbol / venue / strategy hashed into ``scope_hash`` and
    ``provenance_hash``; never propagated as fields on the opportunity.

    Observed ``bad_order`` and ``kill_switch_active`` flags shift the
    ``kind`` to the safe-fail surface; no order side is ever derived.
    """
    payload = envelope.payload

    scope_hash = _h(
        f"{envelope.source_system}|{envelope.environment}|"
        f"{envelope.symbol or '*'}|{envelope.venue or '*'}|{envelope.strategy_name or '*'}"
    )

    kind = _GELAL_KIND_MAP.get(envelope.event_type, PaperOpportunityKind.UNKNOWN)
    bad_order = isinstance(payload.get("bad_order"), bool) and payload["bad_order"]
    if bad_order:
        kind = PaperOpportunityKind.BAD_ORDER_OBSERVATION
    kill_switch_active = (
        envelope.event_type is GelAlShadowEventType.KILL_SWITCH_OBSERVED
        and isinstance(payload.get("kill_switch_active"), bool)
        and bool(payload["kill_switch_active"])
    )
    if kill_switch_active:
        kind = PaperOpportunityKind.KILL_SWITCH_OBSERVATION

    confidence = _bounded_score(payload.get("confidence"), default=0.5)
    risk_score = _bounded_score(payload.get("risk_score"), default=0.3)
    if bad_order or kill_switch_active:
        risk_score = 1.0

    latency_ms_raw = payload.get("latency_ms")
    latency_ms = int(latency_ms_raw) if isinstance(latency_ms_raw, (int, float)) else 0
    depth_age_raw = payload.get("depth_age_ms")
    depth_age = int(depth_age_raw) if isinstance(depth_age_raw, (int, float)) else 0
    base_lag = max(0, envelope.exported_at_ms - envelope.observed_at_ms)
    staleness_ms = base_lag + latency_ms + depth_age

    # Magnitude scales with risk (kill-switch / bad_order get max).
    magnitude = min(
        1.0, 0.5 * risk_score + 0.3 * min(staleness_ms / 5000.0, 1.0) + 0.2 * (1.0 - confidence)
    )
    liquidity_score = _bounded_score(payload.get("liquidity_score"), default=0.5)
    spread_score = _bounded_score(payload.get("spread_pct"), default=0.0)

    return PaperOpportunity(
        opportunity_id=f"paper-gelal-{envelope.event_id}",
        source=PaperOpportunitySource.GELAL_SHADOW,
        kind=kind,
        observed_at_ms=envelope.observed_at_ms,
        source_event_refs=(envelope.event_id,),
        source_adapter_id="gelal-shadow",
        provenance_hash=envelope.source_hash,
        scope_hash=scope_hash,
        confidence=confidence,
        magnitude_score=magnitude,
        risk_score=risk_score,
        staleness_ms=staleness_ms,
        latency_ms=latency_ms,
        liquidity_score=liquidity_score,
        spread_score=spread_score,
    )
