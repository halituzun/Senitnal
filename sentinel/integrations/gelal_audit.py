"""Gel.Al shadow OBSERVATION_INGESTED routing helper (V5).

Builds an ``OBSERVATION_INGESTED`` ``ObserverEvent`` for a Gel.Al
shadow envelope and routes it through ``route_observer_event`` —
the single sanctioned persistence path.  Per catalog policy,
``OBSERVATION_INGESTED`` is ``ring_buffer_only``; if no ring buffer
is supplied the event is dropped (no implicit JSONL promotion).

This helper owns NO ledger I/O of its own.
"""

from __future__ import annotations

from sentinel.integrations.gelal_sanitizer import build_gelal_shadow_audit_payload
from sentinel.integrations.gelal_shadow import GelAlShadowEnvelope  # noqa: TC001 (runtime arg)
from sentinel.observer.hash_chain import placeholder_event_hash
from sentinel.observer.ledger import JsonlObserverLedger  # noqa: TC001 (runtime arg)
from sentinel.observer.ring_buffer import ObserverRingBuffer  # noqa: TC001 (runtime arg)
from sentinel.observer.router import RoutingOutcome, route_observer_event
from sentinel.types.neural_seed import ProvenanceRef  # noqa: TC001 (runtime arg)
from sentinel.types.observer import EventFamily, ObserverEvent


def _build_gelal_observation_ingested_event(
    *,
    envelope: GelAlShadowEnvelope,
    provenance: ProvenanceRef,
) -> ObserverEvent:
    payload = build_gelal_shadow_audit_payload(envelope)
    payload_with_link: dict[str, object] = dict(payload)
    payload_with_link["source_event_id"] = envelope.event_id
    return ObserverEvent(
        event_id=f"gelal-ingested-{envelope.event_id}",
        event_family=EventFamily.INGRESS,
        event_type="OBSERVATION_INGESTED",
        occurred_at_ms=envelope.observed_at_ms,
        payload=payload_with_link,
        provenance=provenance,
        previous_event_hash=None,
        event_hash=placeholder_event_hash(),
    )


def emit_gelal_shadow_observation_ingested(
    *,
    envelope: GelAlShadowEnvelope,
    ledger: JsonlObserverLedger,
    ring_buffer: ObserverRingBuffer | None,
    provenance: ProvenanceRef,
) -> RoutingOutcome:
    """Route an OBSERVATION_INGESTED event for `envelope` through the router.

    Catalog permanence dictates ring-buffer-only placement; this
    helper does not override that policy and does not call
    ``ledger.append`` directly.
    """
    event = _build_gelal_observation_ingested_event(envelope=envelope, provenance=provenance)
    return route_observer_event(event=event, ledger=ledger, ring_buffer=ring_buffer)
