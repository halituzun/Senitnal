"""Bounded RAM ring buffer for ring_buffer_only observer events.

Per OBSERVER_LEDGER_SCHEMA.md §10 and the Phase 2 build plan: this
module provides a bounded in-memory ring for events whose permanence
policy keeps them out of the JSONL ledger (e.g. WORKSPACE_PULSE,
OBSERVATION_INGESTED) but which still need a short-window audit
view (snapshot capture, fast diagnostic, replay window source).

Design intent (data-structure layer only):
    - Fixed capacity > 0; oldest item is dropped on overflow
    - Snapshot returns an immutable tuple in insertion order
    - No I/O, no thread/process locking; single-process MVP
    - Catalog-aware accept policy: a writer is expected to consult
      `decide_permanence(event_type)` and only push events whose
      decision sets `keep_ring_buffer=True`. The buffer itself
      defensively rejects events whose canonical policy does NOT
      include ring-buffer participation (raises InvariantViolation
      with `OBSERVER_RING_BUFFER_POLICY_MISMATCH`)

What this module deliberately does NOT contain:
    - Snapshot capture / serialization
    - JSONL writer routing
    - Compaction / rotation
    - Persistent state across process restarts
"""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable  # noqa: TC003 (runtime annotation)

from sentinel.constitution.violations import InvariantViolation, ViolationContext
from sentinel.observer.permanence import should_keep_ring_buffer
from sentinel.types.observer import ObserverEvent  # noqa: TC001 (Pydantic runtime needs)


class ObserverRingBuffer:
    """Bounded in-memory ring of ObserverEvent entries.

    Methods:
        push(event):     append (drop oldest on overflow); raises
                         InvariantViolation if event's catalog policy
                         doesn't include ring-buffer participation
        snapshot():      tuple of buffered events, oldest first
        __len__():       current buffered count
        capacity:        configured max length
    """

    def __init__(self, *, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError("ObserverRingBuffer capacity must be > 0")
        self._capacity = capacity
        self._buf: deque[ObserverEvent] = deque(maxlen=capacity)

    @property
    def capacity(self) -> int:
        return self._capacity

    def __len__(self) -> int:
        return len(self._buf)

    def push(self, event: ObserverEvent) -> None:
        """Append an event. Catalog must allow ring-buffer participation."""
        if not should_keep_ring_buffer(event.event_type):
            raise InvariantViolation(
                (
                    f"event_type {event.event_type!r} permanence policy does "
                    f"not include ring-buffer participation"
                ),
                ViolationContext(
                    violation_code="OBSERVER_RING_BUFFER_POLICY_MISMATCH",
                    source_ref="OBSERVER_LEDGER_SCHEMA.md §10",
                    evidence={"event_type": event.event_type},
                ),
            )
        self._buf.append(event)

    def extend(self, events: Iterable[ObserverEvent]) -> None:
        """Push a batch of events, one at a time, validating each."""
        for ev in events:
            self.push(ev)

    def snapshot(self) -> tuple[ObserverEvent, ...]:
        """Return all buffered events in insertion order (oldest first)."""
        return tuple(self._buf)

    def clear(self) -> None:
        """Drop every buffered event."""
        self._buf.clear()
