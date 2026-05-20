"""Tests for the ObserverRingBuffer."""

from __future__ import annotations

import pytest
from sentinel.constitution.violations import InvariantViolation
from sentinel.observer.hash_chain import placeholder_event_hash
from sentinel.observer.ring_buffer import ObserverRingBuffer
from sentinel.types.neural_seed import ProvenanceRef
from sentinel.types.observer import EventFamily, ObserverEvent


def _event(
    counter: int,
    *,
    event_type: str = "WORKSPACE_PULSE",
    event_family: EventFamily = EventFamily.ATTENTION,
) -> ObserverEvent:
    return ObserverEvent(
        event_id=f"evt-{counter}",
        event_family=event_family,
        event_type=event_type,
        occurred_at_ms=counter,
        payload={"reason": "unit_test", "counter": counter},
        provenance=ProvenanceRef(source_event_id=f"src-{counter}"),
        previous_event_hash=None,
        event_hash=placeholder_event_hash(),
    )


class TestConstruction:
    def test_zero_capacity_rejected(self) -> None:
        with pytest.raises(ValueError):
            ObserverRingBuffer(capacity=0)

    def test_negative_capacity_rejected(self) -> None:
        with pytest.raises(ValueError):
            ObserverRingBuffer(capacity=-1)

    def test_capacity_exposed(self) -> None:
        buf = ObserverRingBuffer(capacity=4)
        assert buf.capacity == 4
        assert len(buf) == 0


class TestPushSnapshot:
    def test_single_push_visible_in_snapshot(self) -> None:
        buf = ObserverRingBuffer(capacity=4)
        buf.push(_event(1))
        snap = buf.snapshot()
        assert len(snap) == 1
        assert snap[0].event_id == "evt-1"

    def test_snapshot_preserves_order(self) -> None:
        buf = ObserverRingBuffer(capacity=4)
        for i in range(1, 4):
            buf.push(_event(i))
        snap = buf.snapshot()
        assert [e.event_id for e in snap] == ["evt-1", "evt-2", "evt-3"]

    def test_overflow_drops_oldest(self) -> None:
        buf = ObserverRingBuffer(capacity=3)
        for i in range(1, 6):
            buf.push(_event(i))
        snap = buf.snapshot()
        assert [e.event_id for e in snap] == ["evt-3", "evt-4", "evt-5"]
        assert len(buf) == 3

    def test_extend_validates_each_event(self) -> None:
        buf = ObserverRingBuffer(capacity=4)
        buf.extend(_event(i) for i in range(1, 4))
        assert len(buf) == 3

    def test_clear(self) -> None:
        buf = ObserverRingBuffer(capacity=4)
        buf.push(_event(1))
        buf.clear()
        assert len(buf) == 0
        assert buf.snapshot() == ()


class TestPolicyMismatch:
    def test_permanent_only_event_rejected(self) -> None:
        """MEMORY_RECORD_STATUS_CHANGED is permanent, not ring_buffer."""
        buf = ObserverRingBuffer(capacity=4)
        with pytest.raises(InvariantViolation) as exc_info:
            buf.push(
                _event(
                    1,
                    event_type="MEMORY_RECORD_STATUS_CHANGED",
                    event_family=EventFamily.MEMORY,
                )
            )
        assert exc_info.value.violation_code == "OBSERVER_RING_BUFFER_POLICY_MISMATCH"
        assert exc_info.value.evidence["event_type"] == "MEMORY_RECORD_STATUS_CHANGED"
        assert len(buf) == 0

    def test_permanent_with_snapshot_event_accepted(self) -> None:
        """KILL_SWITCH_ACTIVATED uses permanent_with_snapshot, which keeps ring."""
        buf = ObserverRingBuffer(capacity=4)
        buf.push(
            _event(
                1,
                event_type="KILL_SWITCH_ACTIVATED",
                event_family=EventFamily.DEONTIC,
            )
        )
        assert len(buf) == 1
