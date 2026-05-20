"""Workspace pulse emitter — single mechanism.

Per BOOTSTRAP_GENOME.md §B (attention workspace) and the Phase 6
build plan: this module exposes the **one and only** pulse-emission
path. Pulse character lives in the WorkspacePulseEvent's
`dominant_payload_mix` (the signature). No `pulse_type` /
`pulse_category` enum, no variant dispatch.

Constitutional discipline:
    - One event type: WORKSPACE_PULSE. The schema already enforces
      this; this module just bridges WorkspacePulseEvent →
      ObserverEvent → ledger append, preserving the hash chain
    - Coherence-threshold cross is a *decision*; the emitter
      function returns the appended ObserverEvent, the should-emit
      function answers the threshold question. Combining them is
      the caller's job (keeps both pieces testable in isolation)
    - The pulse does NOT trigger action. Action authorization
      happens at the deontic gate (Phase 7). The emitter never
      constructs any execution intent

What this module deliberately does NOT contain:
    - Coherence-threshold *stateful* "one pulse per cross" book-
      keeping (Phase 6+ runtime; this commit is the emission
      mechanism, not the controller)
    - Pulse scoring algorithm (Phase 7+)
    - Action coupling
"""

from __future__ import annotations

from sentinel.observer.hash_chain import placeholder_event_hash
from sentinel.observer.ledger import JsonlObserverLedger  # noqa: TC001 (runtime)
from sentinel.types.neural_seed import ProvenanceRef  # noqa: TC001 (runtime)
from sentinel.types.observer import EventFamily, ObserverEvent
from sentinel.types.workspace import WorkspacePulseEvent  # noqa: TC001 (runtime)


def should_emit_pulse(
    pulse: WorkspacePulseEvent,
    *,
    coherence_threshold: float,
) -> bool:
    """True iff the pulse's coherence has crossed `coherence_threshold`.

    `coherence_threshold` must be in [0.0, 1.0]; otherwise raises
    ValueError.
    """
    if not (0.0 <= coherence_threshold <= 1.0):
        raise ValueError(f"coherence_threshold {coherence_threshold!r} outside [0.0, 1.0]")
    return pulse.coherence >= coherence_threshold


def emit_workspace_pulse(
    ledger: JsonlObserverLedger,
    pulse: WorkspacePulseEvent,
    *,
    provenance: ProvenanceRef,
) -> ObserverEvent:
    """Append a WORKSPACE_PULSE observer event for `pulse` to `ledger`.

    The payload is the WorkspacePulseEvent's JSON dump (preserving
    `dominant_payload_mix` as the pulse signature). Returns the linked
    ObserverEvent (writer authoritative for previous_event_hash and
    event_hash).
    """
    return ledger.append(
        ObserverEvent(
            event_id=pulse.pulse_id,
            event_family=EventFamily.ATTENTION,
            event_type="WORKSPACE_PULSE",
            occurred_at_ms=pulse.occurred_at_ms,
            payload=pulse.model_dump(mode="json"),
            provenance=provenance,
            previous_event_hash=None,
            event_hash=placeholder_event_hash(),
        )
    )
