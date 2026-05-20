"""V6 — Gel.Al shadow → financial deontic policy bridge.

Pure mapping + thin evaluator wrapper.  No write back to Gel.Al, no
M2 mutation, no action-intent object constructed.
"""

from __future__ import annotations

import hashlib
from typing import Final

from sentinel.integrations.gelal_audit import emit_gelal_shadow_observation_ingested
from sentinel.integrations.gelal_shadow import GelAlShadowEnvelope, GelAlShadowEventType
from sentinel.observer.ledger import JsonlObserverLedger  # noqa: TC001 (runtime arg)
from sentinel.observer.ring_buffer import ObserverRingBuffer  # noqa: TC001 (runtime arg)
from sentinel.policy.evaluator import (
    FinancialPolicyEvaluation,
    FinancialPolicyInput,
    evaluate_financial_policy,
)
from sentinel.types.memory import MemoryRecord  # noqa: TC001 (runtime arg)
from sentinel.types.neural_seed import ProvenanceRef  # noqa: TC001 (runtime arg)

_CONSERVATIVE_RISK_DEFAULT: Final[float] = 0.5
_CONSERVATIVE_CONFIDENCE_DEFAULT: Final[float] = 0.5
_CONSERVATIVE_LIQUIDITY_DEFAULT: Final[float] = 0.5
_CONSERVATIVE_UNKNOWN_RISK_DEFAULT: Final[float] = 0.5


def _payload_float(payload: dict[str, object], key: str, default: float = 0.0) -> float:
    v = payload.get(key)
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return float(v)
    return default


def _payload_int(payload: dict[str, object], key: str, default: int = 0) -> int:
    v = payload.get(key)
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return int(v)
    return default


def _payload_bool(payload: dict[str, object], key: str, default: bool = False) -> bool:
    v = payload.get(key)
    return v if isinstance(v, bool) else default


def _payload_bounded(payload: dict[str, object], key: str, default: float) -> float:
    v = payload.get(key)
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        f = float(v)
        if 0.0 <= f <= 1.0:
            return f
    return default


def _h(value: str) -> str:
    """Short hash for scope identifiers."""
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _scope_id_for_envelope(envelope: GelAlShadowEnvelope) -> str:
    """Deterministic scope id derived from source/system + hashed labels."""
    parts = [
        envelope.source_system,
        envelope.environment,
        _h(envelope.symbol or "*"),
        _h(envelope.venue or "*"),
        _h(envelope.strategy_name or "*"),
    ]
    return "scope:" + "|".join(parts)


def build_policy_input_from_gelal_shadow(
    envelope: GelAlShadowEnvelope,
) -> FinancialPolicyInput:
    """Map a Gel.Al shadow envelope to a core-safe FinancialPolicyInput.

    Raw symbol / venue / strategy names are intentionally absent from
    the produced ``FinancialPolicyInput``; ``scope_id`` carries only
    hashed references.
    """
    payload = envelope.payload

    risk_score = _payload_bounded(payload, "risk_score", _CONSERVATIVE_RISK_DEFAULT)
    confidence = _payload_bounded(payload, "confidence", _CONSERVATIVE_CONFIDENCE_DEFAULT)
    liquidity = _payload_bounded(payload, "liquidity_score", _CONSERVATIVE_LIQUIDITY_DEFAULT)

    latency_ms = _payload_int(payload, "latency_ms")
    depth_age = _payload_int(payload, "depth_age_ms")
    base_lag = max(0, envelope.exported_at_ms - envelope.observed_at_ms)
    staleness_ms = base_lag + latency_ms + depth_age

    bad_order = _payload_bool(payload, "bad_order")

    kill_switch_active = (
        envelope.event_type is GelAlShadowEventType.KILL_SWITCH_OBSERVED
        and _payload_bool(payload, "kill_switch_active")
    )

    provenance_missing = not envelope.source_hash

    unknown_risk = _CONSERVATIVE_UNKNOWN_RISK_DEFAULT
    if envelope.event_type in (
        GelAlShadowEventType.OPPORTUNITY_SEEN,
        GelAlShadowEventType.OPPORTUNITY_BLOCKED,
        GelAlShadowEventType.RISK_GATE_DECISION,
        GelAlShadowEventType.MARKET_OBSERVATION,
        GelAlShadowEventType.SYSTEM_HEALTH_OBSERVED,
        GelAlShadowEventType.KILL_SWITCH_OBSERVED,
    ):
        unknown_risk = 0.1

    return FinancialPolicyInput(
        event_id=envelope.event_id,
        scope_id=_scope_id_for_envelope(envelope),
        environment=envelope.environment,
        risk_score=risk_score,
        confidence=confidence,
        staleness_ms=staleness_ms,
        latency_ms=latency_ms,
        orderbook_age_ms=depth_age,
        spread_pct=_payload_float(payload, "spread_pct"),
        liquidity_score=liquidity,
        bad_order=bad_order,
        kill_switch_active=kill_switch_active,
        provenance_missing=provenance_missing,
        unknown_risk_score=unknown_risk,
        source_event_refs=(envelope.event_id,),
    )


def evaluate_gelal_shadow_with_policy(
    *,
    envelope: GelAlShadowEnvelope,
    active_policy_record: MemoryRecord,
    ledger: JsonlObserverLedger,
    ring_buffer: ObserverRingBuffer,
    provenance: ProvenanceRef,
    now_ms: int | None = None,
) -> FinancialPolicyEvaluation:
    """Run the Gel.Al shadow event through the active policy.

    Routes ``OBSERVATION_INGESTED`` ring-only via the V5 helper, then
    evaluates the active policy and returns the evaluation.  Never
    constructs an action-intent object, never writes back.
    """
    emit_gelal_shadow_observation_ingested(
        envelope=envelope,
        ledger=ledger,
        ring_buffer=ring_buffer,
        provenance=provenance,
    )
    policy_input = build_policy_input_from_gelal_shadow(envelope)
    return evaluate_financial_policy(
        policy_record=active_policy_record,
        policy_input=policy_input,
        now_ms=now_ms,
    )
