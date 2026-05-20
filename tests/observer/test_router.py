"""Tests for the permanence-aware observer event router."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003 (fixture annotation)

import pytest
from sentinel.observer.hash_chain import placeholder_event_hash
from sentinel.observer.ledger import JsonlObserverLedger
from sentinel.observer.permanence import EventPermanence
from sentinel.observer.ring_buffer import ObserverRingBuffer
from sentinel.observer.router import route_observer_event
from sentinel.types.neural_seed import ProvenanceRef
from sentinel.types.observer import EventFamily, ObserverEvent


def _event(
    *,
    event_id: str = "ev-1",
    event_type: str = "OBSERVATION_INGESTED",
    event_family: EventFamily = EventFamily.INGRESS,
) -> ObserverEvent:
    return ObserverEvent(
        event_id=event_id,
        event_family=event_family,
        event_type=event_type,
        occurred_at_ms=1,
        payload={"k": "v"},
        provenance=ProvenanceRef(source_event_id="src"),
        previous_event_hash=None,
        event_hash=placeholder_event_hash(),
    )


@pytest.fixture
def ledger_path(tmp_path: Path) -> Path:
    return tmp_path / "ledger.jsonl"


@pytest.fixture
def ledger(ledger_path: Path) -> JsonlObserverLedger:
    return JsonlObserverLedger(ledger_path)


@pytest.fixture
def ring() -> ObserverRingBuffer:
    return ObserverRingBuffer(capacity=16)


class TestRingBufferOnly:
    def test_observation_ingested_lands_in_ring_only(
        self, ledger: JsonlObserverLedger, ring: ObserverRingBuffer
    ) -> None:
        outcome = route_observer_event(
            event=_event(event_type="OBSERVATION_INGESTED"),
            ledger=ledger,
            ring_buffer=ring,
        )
        assert outcome.permanence is EventPermanence.RING_BUFFER_ONLY
        assert outcome.written_to_ledger is False
        assert outcome.pushed_to_ring_buffer is True
        assert len(ledger.read_all()) == 0
        assert len(ring) == 1

    def test_workspace_pulse_lands_in_ring_only(
        self, ledger: JsonlObserverLedger, ring: ObserverRingBuffer
    ) -> None:
        outcome = route_observer_event(
            event=_event(
                event_type="WORKSPACE_PULSE",
                event_family=EventFamily.ATTENTION,
            ),
            ledger=ledger,
            ring_buffer=ring,
        )
        assert outcome.written_to_ledger is False
        assert outcome.pushed_to_ring_buffer is True

    def test_ring_buffer_only_without_buffer_drops(self, ledger: JsonlObserverLedger) -> None:
        outcome = route_observer_event(
            event=_event(event_type="OBSERVATION_INGESTED"),
            ledger=ledger,
            ring_buffer=None,
        )
        assert outcome.written_to_ledger is False
        assert outcome.pushed_to_ring_buffer is False
        assert len(ledger.read_all()) == 0


class TestPermanent:
    def test_memory_record_status_changed_to_ledger_only(
        self, ledger: JsonlObserverLedger, ring: ObserverRingBuffer
    ) -> None:
        outcome = route_observer_event(
            event=_event(
                event_type="MEMORY_RECORD_STATUS_CHANGED",
                event_family=EventFamily.MEMORY,
            ),
            ledger=ledger,
            ring_buffer=ring,
        )
        assert outcome.permanence is EventPermanence.PERMANENT
        assert outcome.written_to_ledger is True
        assert outcome.pushed_to_ring_buffer is False
        assert len(ledger.read_all()) == 1
        assert len(ring) == 0


class TestPermanentWithSnapshot:
    def test_kill_switch_to_both_ledger_and_ring(
        self, ledger: JsonlObserverLedger, ring: ObserverRingBuffer
    ) -> None:
        outcome = route_observer_event(
            event=_event(
                event_type="KILL_SWITCH_ACTIVATED",
                event_family=EventFamily.DEONTIC,
            ),
            ledger=ledger,
            ring_buffer=ring,
        )
        assert outcome.permanence is EventPermanence.PERMANENT_WITH_SNAPSHOT
        assert outcome.written_to_ledger is True
        assert outcome.pushed_to_ring_buffer is True
        assert len(ledger.read_all()) == 1
        assert len(ring) == 1


class TestUnknownEvent:
    def test_unknown_event_type_raises(
        self, ledger: JsonlObserverLedger, ring: ObserverRingBuffer
    ) -> None:
        with pytest.raises(KeyError):
            route_observer_event(
                event=_event(event_type="NOT_A_CANONICAL_EVENT"),
                ledger=ledger,
                ring_buffer=ring,
            )


class TestChainIntegrity:
    def test_ledger_chain_preserved_across_mixed_routing(
        self, ledger: JsonlObserverLedger, ring: ObserverRingBuffer
    ) -> None:
        # Mix permanent + ring_buffer_only events; ledger should
        # only contain the permanent ones and re-verify.
        route_observer_event(
            event=_event(
                event_id="a",
                event_type="OBSERVATION_INGESTED",
            ),
            ledger=ledger,
            ring_buffer=ring,
        )
        route_observer_event(
            event=_event(
                event_id="b",
                event_type="MEMORY_RECORD_STATUS_CHANGED",
                event_family=EventFamily.MEMORY,
            ),
            ledger=ledger,
            ring_buffer=ring,
        )
        route_observer_event(
            event=_event(
                event_id="c",
                event_type="WORKSPACE_PULSE",
                event_family=EventFamily.ATTENTION,
            ),
            ledger=ledger,
            ring_buffer=ring,
        )
        route_observer_event(
            event=_event(
                event_id="d",
                event_type="LEDGER_STATE_CHANGED",
                event_family=EventFamily.LEDGER_META,
            ),
            ledger=ledger,
            ring_buffer=ring,
        )
        events = ledger.read_all()
        assert tuple(e.event_id for e in events) == ("b", "d")
        assert ledger.verify() is True
        # Ring buffer holds the two ring-buffer-only events
        ring_ids = [e.event_id for e in ring.snapshot()]
        assert "a" in ring_ids
        assert "c" in ring_ids
