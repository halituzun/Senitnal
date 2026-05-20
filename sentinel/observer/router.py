"""Permanence-aware observer event router.

Per OBSERVER_LEDGER_SCHEMA.md §10 and OBSERVER_LEDGER_NUMERICS.md §10-12:
an event's catalog permanence policy decides where the writer puts
it. This module is the single sanctioned routing function.

Routing table (catalog-driven; no parallel decision logic):

    ring_buffer_only         -> push to RAM ring buffer only
    permanent                -> append to JSONL ledger only
    permanent_with_snapshot  -> append to JSONL ledger AND push to
                                ring buffer (the ring buffer feeds
                                the snapshot window; snapshot
                                capture itself is a later-phase
                                concern)
    ephemeral                -> drop (no ledger, no ring buffer)

Constitutional discipline:
    - Single source of truth: every observer event flowing through
      the system passes through `route_observer_event`. No
      bypass paths
    - The routing decision comes from
      `sentinel.observer.permanence.decide_permanence` (catalog row).
      Two callers cannot disagree on where an event lands
    - When `route_observer_event` writes to the JSONL ledger, the
      ledger remains writer-authoritative for the chain link (it
      recomputes `previous_event_hash` + `event_hash`)
"""

from __future__ import annotations

from dataclasses import dataclass

from sentinel.observer.ledger import JsonlObserverLedger  # noqa: TC001 (runtime)
from sentinel.observer.permanence import EventPermanence, decide_permanence
from sentinel.observer.ring_buffer import ObserverRingBuffer  # noqa: TC001 (runtime)
from sentinel.types.observer import ObserverEvent  # noqa: TC001 (runtime)


@dataclass(frozen=True, slots=True)
class RoutingOutcome:
    """Where the event went."""

    permanence: EventPermanence
    written_to_ledger: bool
    pushed_to_ring_buffer: bool
    # The observer event as it ended up. For ledger-written events
    # this is the linked event (writer-authoritative chain hash);
    # for ring-buffer-only events this is the original event.
    event: ObserverEvent


def route_observer_event(
    *,
    event: ObserverEvent,
    ledger: JsonlObserverLedger,
    ring_buffer: ObserverRingBuffer | None,
) -> RoutingOutcome:
    """Route `event` per its catalog permanence policy.

    `ring_buffer` may be None. If a ring-buffer-only event arrives
    without a configured buffer, the event is DROPPED (no silent
    promotion to JSONL; the catalog policy is binding). The
    routing outcome records this so callers can detect the loss.

    Raises KeyError (via the catalog helper) if `event.event_type`
    is not in the canonical catalog.
    """
    decision = decide_permanence(event.event_type)
    written = False
    pushed = False
    final_event = event

    if decision.write_permanent:
        final_event = ledger.append(event)
        written = True

    if decision.keep_ring_buffer and ring_buffer is not None:
        # If we just wrote to the ledger the linked event reflects
        # the authoritative chain hash; push that into the ring
        # buffer as well so snapshot windows hold the same shape.
        ring_buffer.push(final_event)
        pushed = True

    return RoutingOutcome(
        permanence=decision.permanence,
        written_to_ledger=written,
        pushed_to_ring_buffer=pushed,
        event=final_event,
    )
