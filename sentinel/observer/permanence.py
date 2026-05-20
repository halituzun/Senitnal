"""Permanence policy helpers (catalog-backed, no I/O).

Per OBSERVER_LEDGER_SCHEMA.md §10-12 and the Phase 2 build plan: this
module interprets the `EventPermanence` field from the canonical
event catalog into routing decisions a writer can act on, and pins
the constitutional invariant that **permanence policy is monotonic**
— storage pressure cannot downgrade an event's permanence.

Constitutional discipline (interpretation layer only):
    - Decisions are pure functions of the canonical catalog row for
      an event_type; no runtime state, no I/O
    - The `ring_buffer_only` flag here means "the writer must keep
      this event in the RAM ring buffer". For
      `permanent_with_snapshot`, both the ring buffer and the JSONL
      ledger participate (the ring buffer feeds the snapshot
      window)
    - `assert_no_permanence_downgrade(old, new, event_type)` raises
      `InvariantViolation` when the new policy is weaker than the
      old — this is the M's constitutional monotonicity rule:
      storage pressure cannot weaken permanence

What this module deliberately does NOT contain:
    - Ring-buffer data structure (Commit 17)
    - Snapshot capture
    - JSONL writer routing (Commit 18 / integration)
    - Compaction / rotation / storage tiering
    - Severity-conditional permanence overrides (later phases)
"""

from __future__ import annotations

from dataclasses import dataclass

from sentinel.constitution.violations import InvariantViolation, ViolationContext
from sentinel.observer.catalog import EventPermanence, get_event_definition

# Strength ordering for the monotonicity invariant.
# A new permanence is rejected if its strength is strictly less than
# the old permanence's strength.
_STRENGTH: dict[EventPermanence, int] = {
    EventPermanence.EPHEMERAL: 0,
    EventPermanence.RING_BUFFER_ONLY: 1,
    EventPermanence.PERMANENT: 2,
    EventPermanence.PERMANENT_WITH_SNAPSHOT: 3,
}


@dataclass(frozen=True, slots=True)
class PermanenceDecision:
    """Routing decision for a single canonical event_type.

    Fields:
        event_type:           the canonical event identifier
        permanence:           the catalog's EventPermanence policy
        write_permanent:      writer must append to the JSONL ledger
        keep_ring_buffer:     writer must keep the event in the RAM
                              ring buffer (also True for snapshot
                              policies, where the ring buffer feeds
                              the snapshot window)
        requires_snapshot:    a snapshot capture must accompany the
                              JSONL write
        human_alert_required: a human-operator alert must be raised
                              on write
    """

    event_type: str
    permanence: EventPermanence
    write_permanent: bool
    keep_ring_buffer: bool
    requires_snapshot: bool
    human_alert_required: bool


def decide_permanence(event_type: str) -> PermanenceDecision:
    """Return the full routing decision for `event_type`.

    Raises `KeyError` (via the catalog) if `event_type` is unknown.
    """
    row = get_event_definition(event_type)
    permanence = row.permanence
    write_permanent = permanence in (
        EventPermanence.PERMANENT,
        EventPermanence.PERMANENT_WITH_SNAPSHOT,
    )
    keep_ring_buffer = permanence in (
        EventPermanence.RING_BUFFER_ONLY,
        EventPermanence.PERMANENT_WITH_SNAPSHOT,
    )
    requires_snapshot_flag = permanence is EventPermanence.PERMANENT_WITH_SNAPSHOT
    return PermanenceDecision(
        event_type=event_type,
        permanence=permanence,
        write_permanent=write_permanent,
        keep_ring_buffer=keep_ring_buffer,
        requires_snapshot=requires_snapshot_flag,
        human_alert_required=row.human_alert_required,
    )


def should_write_permanent(event_type: str) -> bool:
    return decide_permanence(event_type).write_permanent


def should_keep_ring_buffer(event_type: str) -> bool:
    return decide_permanence(event_type).keep_ring_buffer


def requires_snapshot(event_type: str) -> bool:
    return decide_permanence(event_type).requires_snapshot


def requires_human_alert(event_type: str) -> bool:
    return decide_permanence(event_type).human_alert_required


def assert_no_permanence_downgrade(
    *,
    old: EventPermanence,
    new: EventPermanence,
    event_type: str,
) -> None:
    """Constitutional monotonicity: permanence may strengthen, never weaken.

    Raises `InvariantViolation` with
    `violation_code="OBSERVER_PERMANENCE_DOWNGRADE_FORBIDDEN"` if
    `_STRENGTH[new] < _STRENGTH[old]`. Equal strength is accepted.
    """
    if _STRENGTH[new] < _STRENGTH[old]:
        raise InvariantViolation(
            (f"permanence downgrade forbidden for {event_type!r}: {old.value!r} -> {new.value!r}"),
            ViolationContext(
                violation_code="OBSERVER_PERMANENCE_DOWNGRADE_FORBIDDEN",
                source_ref="OBSERVER_LEDGER_NUMERICS.md §10-12",
                evidence={
                    "event_type": event_type,
                    "old_permanence": old.value,
                    "new_permanence": new.value,
                },
            ),
        )
