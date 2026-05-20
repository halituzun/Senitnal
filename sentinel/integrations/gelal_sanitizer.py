"""Gel.Al shadow envelope → core-safe ObservationEvent sanitizer (V5).

Pure functions only.  Maps a ``GelAlShadowEnvelope`` (which may
contain ``symbol``, ``venue``, ``strategy_name``, ``order_sent``,
``bad_order``, ``decision``, raw payload) into the core-facing v0.1
``ObservationEvent`` (which contains only abstract normalized
quantities).  All domain labels are stripped at this layer.

The observer-side audit payload builder preserves Gel.Al provenance
(``source_table``, ``source_row_id``, ``source_hash``, ``environment``,
``strategy_name``, ``symbol``, ``venue`` and a payload **summary**)
for the ``OBSERVATION_INGESTED`` audit event.  It excludes any
credential or command field by construction.
"""

from __future__ import annotations

from typing import Final

from sentinel.integrations.gelal_shadow import GelAlShadowEnvelope, GelAlShadowEventType
from sentinel.types.events import IngressEventType, ObservationEvent

# ---------------------------------------------------------------------------
# Tuning constants
# ---------------------------------------------------------------------------

_DEFAULT_SOURCE_RELIABILITY_BAND: Final[int] = 3
_DEFAULT_TTL_MS: Final[int] = 1000
_GELAL_SOURCE_ADAPTER_ID: Final[str] = "gelal-shadow"
_DEFAULT_CONFIDENCE: Final[float] = 0.5

# Event-type rarity scores (higher = rarer = more novel).
# Calibrated by hand; deterministic.
_EVENT_TYPE_RARITY: Final[dict[GelAlShadowEventType, float]] = {
    GelAlShadowEventType.MARKET_OBSERVATION: 0.05,
    GelAlShadowEventType.OPPORTUNITY_SEEN: 0.20,
    GelAlShadowEventType.OPPORTUNITY_BLOCKED: 0.35,
    GelAlShadowEventType.RISK_GATE_DECISION: 0.50,
    GelAlShadowEventType.EXECUTION_ATTEMPT_OBSERVED: 0.60,
    GelAlShadowEventType.PAPER_RESULT_OBSERVED: 0.40,
    GelAlShadowEventType.LIVE_RESULT_OBSERVED: 0.70,
    GelAlShadowEventType.SYSTEM_HEALTH_OBSERVED: 0.25,
    GelAlShadowEventType.KILL_SWITCH_OBSERVED: 1.0,
}


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def _payload_float(payload: dict[str, object], key: str, default: float = 0.0) -> float:
    v = payload.get(key)
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return float(v)
    return default


def _payload_bool(payload: dict[str, object], key: str, default: bool = False) -> bool:
    v = payload.get(key)
    return v if isinstance(v, bool) else default


def _derive_confidence(envelope: GelAlShadowEnvelope) -> float:
    payload_conf = envelope.payload.get("confidence")
    if isinstance(payload_conf, (int, float)) and not isinstance(payload_conf, bool):
        c = float(payload_conf)
        if 0.0 <= c <= 1.0:
            return c
    return _DEFAULT_CONFIDENCE


def _derive_magnitude(envelope: GelAlShadowEnvelope) -> float:
    """Deterministic bounded magnitude function.

    Combines (where present in the payload):
        - |net_edge_pct| / 5.0   (capped at 1.0)
        - risk_score              (already in [0,1])
        - bad_order               (full magnitude if True)
        - stale_count / 100       (capped at 1.0)
        - latency_ms / 1000       (capped at 1.0)

    A bad-order observation or active kill switch dominates the
    magnitude so the downstream pipeline reacts visibly.
    """
    payload = envelope.payload

    if envelope.event_type is GelAlShadowEventType.KILL_SWITCH_OBSERVED and _payload_bool(
        payload, "kill_switch_active"
    ):
        return 1.0

    if _payload_bool(payload, "bad_order"):
        return 1.0

    edge = abs(_payload_float(payload, "net_edge_pct"))
    risk = _clamp(_payload_float(payload, "risk_score"))
    stale = _clamp(_payload_float(payload, "stale_count") / 100.0)
    latency = _clamp(_payload_float(payload, "latency_ms") / 1000.0)
    edge_term = _clamp(edge / 5.0)

    combined = 0.35 * edge_term + 0.35 * risk + 0.15 * stale + 0.15 * latency
    return _clamp(combined)


def _derive_novelty(envelope: GelAlShadowEnvelope) -> float:
    """Deterministic bounded novelty indicator."""
    base = _EVENT_TYPE_RARITY.get(envelope.event_type, 0.3)
    payload = envelope.payload
    if _payload_bool(payload, "bad_order"):
        base = max(base, 0.85)
    if envelope.event_type is GelAlShadowEventType.KILL_SWITCH_OBSERVED and _payload_bool(
        payload, "kill_switch_active"
    ):
        base = 1.0
    risk = _clamp(_payload_float(payload, "risk_score"))
    stale = _clamp(_payload_float(payload, "stale_count") / 100.0)
    bump = 0.20 * risk + 0.15 * stale
    return _clamp(base + bump)


def _derive_staleness_ms(envelope: GelAlShadowEnvelope) -> int:
    """Staleness combines export lag and payload latency hints."""
    base = max(0, envelope.exported_at_ms - envelope.observed_at_ms)
    payload = envelope.payload
    latency = max(0, int(_payload_float(payload, "latency_ms")))
    depth_age = max(0, int(_payload_float(payload, "depth_age_ms")))
    return base + latency + depth_age


def sanitize_gelal_shadow_to_observation_event(
    envelope: GelAlShadowEnvelope,
    *,
    ttl_ms: int = _DEFAULT_TTL_MS,
    source_reliability_band: int = _DEFAULT_SOURCE_RELIABILITY_BAND,
) -> ObservationEvent:
    """Map a Gel.Al shadow envelope into a v0.1 ObservationEvent.

    The resulting ``ObservationEvent`` contains **no** symbol, venue,
    strategy_name, opportunity_id, order_sent, bad_order, decision,
    block_reason, raw payload, account info, API key, or execution
    instruction.  Only the bounded normalized scalars survive.

    Deterministic: identical envelope → identical event (modulo
    caller-supplied ``ttl_ms`` / ``source_reliability_band``).
    """
    return ObservationEvent(
        event_id=envelope.event_id,
        event_type=IngressEventType.OBSERVATION,
        occurred_at_ms=envelope.observed_at_ms,
        ttl_ms=ttl_ms,
        confidence=_derive_confidence(envelope),
        source_adapter_id=_GELAL_SOURCE_ADAPTER_ID,
        source_reliability_band=source_reliability_band,
        magnitude_normalized=_derive_magnitude(envelope),
        novelty_indicator=_derive_novelty(envelope),
        staleness_ms=_derive_staleness_ms(envelope),
    )


def build_gelal_shadow_audit_payload(envelope: GelAlShadowEnvelope) -> dict[str, object]:
    """Build an observer-side audit payload for a Gel.Al shadow envelope.

    The payload may contain ``symbol``, ``venue``, ``strategy_name``
    and a non-sensitive payload summary (because observer-side
    payloads intentionally permit domain labels) but explicitly
    excludes credentials, command fields, and execution instructions
    (which are already rejected at envelope construction).
    """
    payload_summary: dict[str, object] = {}
    for key in (
        "opportunity_id",
        "decision_id",
        "component_name",
        "status",
        "block_reason",
        "decision",
        "confidence",
        "risk_score",
        "net_edge_pct",
        "gross_edge_pct",
        "fee_pct",
        "slip_pct",
        "stale_count",
        "error_count",
        "latency_ms",
        "depth_age_ms",
        "order_sent",
        "bad_order",
        "kill_switch_active",
        "observed_by",
        "source",
        "reason",
    ):
        if key in envelope.payload:
            payload_summary[key] = envelope.payload[key]
    return {
        "source_system": envelope.source_system,
        "source_table": envelope.source_table,
        "source_row_id": envelope.source_row_id,
        "source_hash": envelope.source_hash,
        "environment": envelope.environment,
        "strategy_name": envelope.strategy_name,
        "symbol": envelope.symbol,
        "venue": envelope.venue,
        "event_type": envelope.event_type.value,
        "observed_at_ms": envelope.observed_at_ms,
        "exported_at_ms": envelope.exported_at_ms,
        "payload_summary": payload_summary,
    }
