"""V11 — Multi-source signal fusion engine.

Deterministic, source-agreement weighted, stale-dampened,
contradiction-aware.  No raw symbol/venue/secret enters the result.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from sentinel.intelligence.schemas import (
        CommodityMacroSnapshot,
        GelAlMetricsObservation,
        MacroEventSnapshot,
        MarketMicrostructureSnapshot,
        NewsEventSnapshot,
        SocialSignalSnapshot,
        TechnicalIndicatorSnapshot,
    )

_STALE_DAMPEN_AFTER_MS = 60_000


@dataclass(frozen=True, slots=True)
class SignalFusionInput:
    """All multi-source snapshots feeding one fusion cycle."""

    fusion_id: str
    now_ms: int
    technical_indicator_snapshots: tuple[TechnicalIndicatorSnapshot, ...] = field(
        default_factory=tuple
    )
    microstructure_snapshots: tuple[MarketMicrostructureSnapshot, ...] = field(
        default_factory=tuple
    )
    macro_snapshots: tuple[MacroEventSnapshot, ...] = field(default_factory=tuple)
    news_snapshots: tuple[NewsEventSnapshot, ...] = field(default_factory=tuple)
    social_snapshots: tuple[SocialSignalSnapshot, ...] = field(default_factory=tuple)
    commodity_snapshots: tuple[CommodityMacroSnapshot, ...] = field(default_factory=tuple)
    gelal_metrics_snapshots: tuple[GelAlMetricsObservation, ...] = field(default_factory=tuple)
    financial_memory_refs: tuple[str, ...] = field(default_factory=tuple)
    replay_evidence_refs: tuple[str, ...] = field(default_factory=tuple)


class SignalFusionResult(BaseModel, frozen=True, extra="forbid"):
    """Deterministic fusion output — evidence, not action."""

    fusion_id: str = Field(min_length=1)
    trend_pressure: float = Field(ge=0.0, le=1.0)
    reversal_suspicion: float = Field(ge=0.0, le=1.0)
    volatility_pressure: float = Field(ge=0.0, le=1.0)
    liquidity_confidence: float = Field(ge=0.0, le=1.0)
    toxic_flow_suspicion: float = Field(ge=0.0, le=1.0)
    macro_shock_pressure: float = Field(ge=0.0, le=1.0)
    social_noise_pressure: float = Field(ge=0.0, le=1.0)
    historical_similarity_score: float = Field(ge=0.0, le=1.0, default=0.0)
    contradiction_pressure: float = Field(ge=0.0, le=1.0)
    source_agreement_score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    reasons: tuple[str, ...] = Field(default_factory=tuple)
    source_refs: tuple[str, ...] = Field(default_factory=tuple)


def _dampen(value: float, age_ms: int) -> float:
    if age_ms <= _STALE_DAMPEN_AFTER_MS:
        return value
    decay = max(0.1, _STALE_DAMPEN_AFTER_MS / max(age_ms, 1))
    return value * decay


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _clip(x: float) -> float:
    return max(0.0, min(1.0, x))


def compute_signal_fusion(inp: SignalFusionInput) -> SignalFusionResult:
    """Aggregate multi-source snapshots into deterministic pressure scores."""
    reasons: list[str] = []
    source_refs: list[str] = []

    # Technical indicators.
    trend_vals: list[float] = []
    momentum_vals: list[float] = []
    volatility_vals: list[float] = []
    reversal_vals: list[float] = []
    for ti in inp.technical_indicator_snapshots:
        age = max(inp.now_ms - ti.observed_at_ms, 0)
        trend_vals.append(_dampen(ti.trend_score, age) * ti.confidence)
        momentum_vals.append(_dampen(ti.momentum_score, age) * ti.confidence)
        volatility_vals.append(_dampen(ti.volatility_score, age) * ti.confidence)
        reversal_vals.append(_dampen(ti.reversal_score, age) * ti.confidence)
        source_refs.append(f"ti:{ti.snapshot_id}")

    # Microstructure.
    liquidity_vals: list[float] = []
    toxic_vals: list[float] = []
    for ms in inp.microstructure_snapshots:
        liquidity_vals.append(ms.liquidity_score * ms.confidence)
        toxic_vals.append(max(ms.vpin_score, ms.hawkes_toxicity_score) * ms.confidence)
        source_refs.append(f"ms:{ms.snapshot_id}")

    # Macro / commodity.
    macro_vals: list[float] = []
    for me in inp.macro_snapshots:
        macro_vals.append(
            max(me.severity_score, me.surprise_score, me.risk_off_score) * me.confidence
        )
        source_refs.append(f"macro:{me.event_id}")
    for cm in inp.commodity_snapshots:
        macro_vals.append(cm.global_risk_off_score * cm.confidence)
        source_refs.append(f"cm:{cm.snapshot_id}")

    # News.
    news_vals: list[float] = []
    contradiction_vals: list[float] = []
    for ne in inp.news_snapshots:
        news_vals.append(ne.severity_score * ne.confidence * ne.source_reliability_score)
        contradiction_vals.append(ne.contradiction_score)
        source_refs.append(f"news:{ne.event_id}")

    # Social.
    social_vals: list[float] = []
    for so in inp.social_snapshots:
        noise = max(so.bot_noise_score, so.crowd_panic_score, so.crowd_euphoria_score)
        social_vals.append(noise * so.confidence)
        contradiction_vals.append(so.contradiction_score)
        source_refs.append(f"social:{so.signal_id}")

    trend_pressure = _clip(_mean(trend_vals) * 0.6 + _mean(momentum_vals) * 0.4)
    reversal_suspicion = _clip(_mean(reversal_vals))
    volatility_pressure = _clip(_mean(volatility_vals) * 0.6 + _mean(macro_vals) * 0.4)
    liquidity_confidence = _clip(_mean(liquidity_vals)) if liquidity_vals else 0.0
    toxic_flow_suspicion = _clip(_mean(toxic_vals)) if toxic_vals else 0.0
    macro_shock_pressure = _clip(_mean(macro_vals) * 0.7 + _mean(news_vals) * 0.3)
    social_noise_pressure = _clip(_mean(social_vals))
    contradiction_pressure = _clip(_mean(contradiction_vals))

    # Source agreement: count distinct populated families with nonzero confidence.
    families_with_signal = 0
    for vs in (trend_vals, liquidity_vals, macro_vals, news_vals, social_vals):
        if any(v > 0 for v in vs):
            families_with_signal += 1
    source_agreement_score = min(1.0, families_with_signal / 5.0)

    # Confidence: average of signal confidences, dampened by contradiction.
    confidences: list[float] = []
    for ti in inp.technical_indicator_snapshots:
        confidences.append(ti.confidence)
    for ms in inp.microstructure_snapshots:
        confidences.append(ms.confidence)
    for me in inp.macro_snapshots:
        confidences.append(me.confidence)
    for ne in inp.news_snapshots:
        confidences.append(ne.confidence)
    for so in inp.social_snapshots:
        confidences.append(so.confidence)
    base_conf = _mean(confidences) if confidences else 0.0
    confidence = _clip(base_conf * (1.0 - contradiction_pressure * 0.5) * source_agreement_score)

    if not confidences:
        reasons.append("no source inputs; fusion confidence=0")
    if contradiction_pressure > 0.5:
        reasons.append("high contradiction across sources")
    if liquidity_confidence < 0.3:
        reasons.append("low liquidity confidence")
    if toxic_flow_suspicion > 0.6:
        reasons.append("toxic flow suspicion")
    if macro_shock_pressure > 0.6:
        reasons.append("macro shock pressure elevated")

    return SignalFusionResult(
        fusion_id=inp.fusion_id,
        trend_pressure=trend_pressure,
        reversal_suspicion=reversal_suspicion,
        volatility_pressure=volatility_pressure,
        liquidity_confidence=liquidity_confidence,
        toxic_flow_suspicion=toxic_flow_suspicion,
        macro_shock_pressure=macro_shock_pressure,
        social_noise_pressure=social_noise_pressure,
        historical_similarity_score=0.0,
        contradiction_pressure=contradiction_pressure,
        source_agreement_score=source_agreement_score,
        confidence=confidence,
        reasons=tuple(reasons),
        source_refs=tuple(source_refs),
    )


__all__ = [
    "SignalFusionInput",
    "SignalFusionResult",
    "compute_signal_fusion",
]
