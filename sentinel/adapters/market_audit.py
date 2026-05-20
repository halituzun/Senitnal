"""Market observation observer-audit routing helper.

Builds an OBSERVATION_INGESTED ObserverEvent for a
MarketObservationEnvelope and routes it through the sanctioned
permanence-aware router (`route_observer_event`). Per the catalog,
OBSERVATION_INGESTED is `ring_buffer_only`; this helper does NOT
override or relax that policy, and does NOT call `ledger.append`
directly.

This module owns NO ledger I/O of its own. It defers entirely to
`sentinel.observer.router.route_observer_event`, which is the
single sanctioned write path.
"""

from __future__ import annotations

from sentinel.adapters.market_observation import (
    MarketObservationEnvelope,
    build_market_observation_audit_payload,
)
from sentinel.observer.hash_chain import placeholder_event_hash
from sentinel.observer.ledger import JsonlObserverLedger  # noqa: TC001 (runtime arg)
from sentinel.observer.ring_buffer import ObserverRingBuffer  # noqa: TC001 (runtime arg)
from sentinel.observer.router import (
    RoutingOutcome,
    route_observer_event,
)
from sentinel.types.neural_seed import ProvenanceRef  # noqa: TC001 (runtime arg)
from sentinel.types.observer import EventFamily, ObserverEvent


def _build_market_observation_ingested_event(
    *,
    envelope: MarketObservationEnvelope,
    provenance: ProvenanceRef,
) -> ObserverEvent:
    payload = build_market_observation_audit_payload(envelope)
    # Include the source_event_id for chain-correlation with downstream
    # NeuralSeed / WORKSPACE_PULSE entries derived from this envelope.
    payload_with_link: dict[str, object] = dict(payload)
    payload_with_link["source_event_id"] = envelope.event_id
    return ObserverEvent(
        event_id=f"ingested-{envelope.event_id}",
        event_family=EventFamily.INGRESS,
        event_type="OBSERVATION_INGESTED",
        occurred_at_ms=envelope.observed_at_ms,
        payload=payload_with_link,
        provenance=provenance,
        previous_event_hash=None,
        event_hash=placeholder_event_hash(),
    )


def emit_market_observation_ingested(
    *,
    envelope: MarketObservationEnvelope,
    ledger: JsonlObserverLedger,
    ring_buffer: ObserverRingBuffer | None,
    provenance: ProvenanceRef,
) -> RoutingOutcome:
    """Route an OBSERVATION_INGESTED event for `envelope` through the
    sanctioned router.

    Per the catalog policy, this lands in the ring buffer (or is
    dropped if `ring_buffer` is None). It is NEVER promoted to the
    permanent JSONL ledger by this helper.

    Returns the RoutingOutcome from `route_observer_event`.
    """
    event = _build_market_observation_ingested_event(envelope=envelope, provenance=provenance)
    return route_observer_event(event=event, ledger=ledger, ring_buffer=ring_buffer)
