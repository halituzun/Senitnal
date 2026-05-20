"""V3 — Financial M2 memory payload schemas + subject_class mapper.

Per docs/build/0004-v3-financial-m2-memory-recall-build-plan.md.

This module defines the five financial payload families V3 produces
from sanitized read-only market observations. Each family maps to an
**existing** v0.1 SubjectClass — V3 does NOT add new subject_class
values. The mapping is deliberate and exercises both Memory Write
Gate paths:

    MarketRegimeObservationPayload      -> STRUCTURED_FACT
        (claims observed market condition; STRUCTURED_FACT is NOT in
         the MWG MVP whitelist, so submissions are rejected with a
         MEMORY_RECORD_STATUS_CHANGED(new_status=rejected) audit
         event. This is intentional: V3 produces structured facts as
         observations, but does not promote them through MVP MWG.)

    SpreadWindowObservationPayload      -> STRUCTURED_FACT
    LiquidityConditionPayload           -> STRUCTURED_FACT

    LatencyPatternPayload               -> SOURCE_TRUST
        (measures source-adapter quality; (SOURCE_TRUST,
         DIRECT_OBSERVATION) is in the MWG whitelist, so accepted as
         candidate.)

    ExecutionQualityObservationPayload  -> PROCEDURAL
        (simulated/paper/fixture-only quality lookup; (PROCEDURAL,
         INTERNAL_INFERENCE) is in the MWG whitelist, so accepted as
         candidate. V3 ExecutionQuality NEVER carries live execution
         data: no order_id, no live_fill_id, no order_side, no
         account_id.)

All five payloads use extra='forbid' / frozen=True / strict=True and
carry observer-side identity (symbol_hash, venue_hash) rather than
raw symbol/venue strings. Raw labels live ONLY in observer-side
audit payload; never in candidate memory.
"""

from __future__ import annotations

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sentinel.types.memory import SubjectClass

_FROZEN_CONFIG = ConfigDict(extra="forbid", frozen=True, strict=True)


class MarketRegimeObservationPayload(BaseModel):
    """An observed market regime over a finite window."""

    model_config = _FROZEN_CONFIG

    record_key: str = Field(min_length=1)
    symbol_hash: str = Field(min_length=1)
    venue_hash: str = Field(min_length=1)
    regime_label: str = Field(min_length=1)
    observed_window_ms: int = Field(gt=0)
    volatility_score: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    spread_score: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    liquidity_score: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    staleness_score: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    confidence: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    observation_count: int = Field(ge=1)
    source_event_ids: tuple[str, ...]

    @model_validator(mode="after")
    def _validate_source_event_ids(self) -> Self:
        if not self.source_event_ids:
            raise ValueError("source_event_ids must be non-empty")
        for sid in self.source_event_ids:
            if not sid:
                raise ValueError("source_event_ids entries must be non-empty")
        return self


class SpreadWindowObservationPayload(BaseModel):
    """Spread statistics over a finite observed window."""

    model_config = _FROZEN_CONFIG

    record_key: str = Field(min_length=1)
    symbol_hash: str = Field(min_length=1)
    venue_hash: str = Field(min_length=1)
    window_start_ms: int = Field(ge=0)
    window_end_ms: int = Field(ge=0)
    min_spread_pct: float = Field(ge=0.0, allow_inf_nan=False)
    max_spread_pct: float = Field(ge=0.0, allow_inf_nan=False)
    avg_spread_pct: float = Field(ge=0.0, allow_inf_nan=False)
    sample_count: int = Field(ge=1)
    confidence: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    source_event_ids: tuple[str, ...]

    @model_validator(mode="after")
    def _validate_consistency(self) -> Self:
        if self.window_end_ms < self.window_start_ms:
            raise ValueError("window_end_ms must be >= window_start_ms")
        if self.max_spread_pct < self.min_spread_pct:
            raise ValueError("max_spread_pct must be >= min_spread_pct")
        if not (self.min_spread_pct <= self.avg_spread_pct <= self.max_spread_pct):
            raise ValueError("avg_spread_pct must be between min and max")
        if not self.source_event_ids:
            raise ValueError("source_event_ids must be non-empty")
        for sid in self.source_event_ids:
            if not sid:
                raise ValueError("source_event_ids entries must be non-empty")
        return self


class LiquidityConditionPayload(BaseModel):
    """Liquidity condition snapshot (top-N aggregated, no raw book)."""

    model_config = _FROZEN_CONFIG

    record_key: str = Field(min_length=1)
    symbol_hash: str = Field(min_length=1)
    venue_hash: str = Field(min_length=1)
    bid_depth_score: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    ask_depth_score: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    imbalance_score: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    liquidity_score: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    confidence: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    source_event_ids: tuple[str, ...]

    @model_validator(mode="after")
    def _validate_source_event_ids(self) -> Self:
        if not self.source_event_ids:
            raise ValueError("source_event_ids must be non-empty")
        for sid in self.source_event_ids:
            if not sid:
                raise ValueError("source_event_ids entries must be non-empty")
        return self


class LatencyPatternPayload(BaseModel):
    """Adapter / venue latency profile (source_trust subject class)."""

    model_config = _FROZEN_CONFIG

    record_key: str = Field(min_length=1)
    source_adapter_id: str = Field(min_length=1)
    venue_hash: str = Field(min_length=1)
    avg_latency_ms: float = Field(ge=0.0, allow_inf_nan=False)
    p95_latency_ms: float = Field(ge=0.0, allow_inf_nan=False)
    max_latency_ms: float = Field(ge=0.0, allow_inf_nan=False)
    stale_ratio: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    sample_count: int = Field(ge=1)
    confidence: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    source_event_ids: tuple[str, ...]

    @model_validator(mode="after")
    def _validate_consistency(self) -> Self:
        if not (self.avg_latency_ms <= self.p95_latency_ms <= self.max_latency_ms):
            raise ValueError("require avg <= p95 <= max")
        if not self.source_event_ids:
            raise ValueError("source_event_ids must be non-empty")
        for sid in self.source_event_ids:
            if not sid:
                raise ValueError("source_event_ids entries must be non-empty")
        return self


class ExecutionQualityObservationPayload(BaseModel):
    """Simulated / paper / fixture execution quality summary.

    V3 has NO live execution. This payload carries only synthetic
    estimates derived from local fixtures or paper-simulator runs.
    The schema deliberately omits order_id, live_fill_id,
    order_side, account_id, and any other execution-surface field.
    Such fields would be rejected by extra='forbid' anyway.
    """

    model_config = _FROZEN_CONFIG

    record_key: str = Field(min_length=1)
    simulation_id: str = Field(min_length=1)
    expected_fill_quality: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    estimated_slippage_pct: float = Field(ge=0.0, allow_inf_nan=False)
    estimated_fee_pct: float = Field(ge=0.0, allow_inf_nan=False)
    estimated_net_edge_pct: float = Field(allow_inf_nan=False)
    sample_count: int = Field(ge=1)
    confidence: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    source_event_ids: tuple[str, ...]

    @model_validator(mode="after")
    def _validate_source_event_ids(self) -> Self:
        if not self.source_event_ids:
            raise ValueError("source_event_ids must be non-empty")
        for sid in self.source_event_ids:
            if not sid:
                raise ValueError("source_event_ids entries must be non-empty")
        return self


FinancialPayload = (
    MarketRegimeObservationPayload
    | SpreadWindowObservationPayload
    | LiquidityConditionPayload
    | LatencyPatternPayload
    | ExecutionQualityObservationPayload
)


def financial_payload_subject_class(payload: FinancialPayload) -> SubjectClass:
    """Map a financial payload to its canonical SubjectClass.

    The mapping is fixed and uses only EXISTING SubjectClass values.
    V3 does NOT extend the v0.1 16-value SubjectClass taxonomy. The
    mapping deliberately routes the three "claim an observed market
    condition" payloads to STRUCTURED_FACT (which the MVP MWG does
    NOT accept) and the two operational / quality payloads to
    SOURCE_TRUST / PROCEDURAL (which ARE in the MWG whitelist).
    """
    if isinstance(payload, MarketRegimeObservationPayload):
        return SubjectClass.STRUCTURED_FACT
    if isinstance(payload, SpreadWindowObservationPayload):
        return SubjectClass.STRUCTURED_FACT
    if isinstance(payload, LiquidityConditionPayload):
        return SubjectClass.STRUCTURED_FACT
    if isinstance(payload, LatencyPatternPayload):
        return SubjectClass.SOURCE_TRUST
    # Final arm is ExecutionQualityObservationPayload — fall-through;
    # the union exhausts all five variants.
    return SubjectClass.PROCEDURAL
