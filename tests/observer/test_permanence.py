"""Tests for the observer permanence policy helpers.

Discipline tested here (interpretation layer only):
    - decide_permanence reads from the canonical catalog
    - Routing flags interpret each EventPermanence value correctly:
        ring_buffer_only:        ring, no permanent, no snapshot
        permanent:               permanent, no ring, no snapshot
        permanent_with_snapshot: permanent + ring + snapshot
    - requires_human_alert mirrors the catalog row
    - decide_permanence on unknown event raises KeyError via catalog
    - assert_no_permanence_downgrade:
        same -> same accepted
        weaker -> stronger accepted (all directions)
        stronger -> weaker rejected with InvariantViolation
        evidence carries event_type / old / new
"""

from __future__ import annotations

import pytest
from sentinel.constitution.violations import InvariantViolation
from sentinel.observer.catalog import EventPermanence
from sentinel.observer.permanence import (
    PermanenceDecision,
    assert_no_permanence_downgrade,
    decide_permanence,
    requires_human_alert,
    requires_snapshot,
    should_keep_ring_buffer,
    should_write_permanent,
)


class TestDecidePermanence:
    def test_ring_buffer_only_event(self) -> None:
        d = decide_permanence("WORKSPACE_PULSE")
        assert isinstance(d, PermanenceDecision)
        assert d.permanence is EventPermanence.RING_BUFFER_ONLY
        assert d.write_permanent is False
        assert d.keep_ring_buffer is True
        assert d.requires_snapshot is False
        assert d.human_alert_required is False

    def test_permanent_event(self) -> None:
        d = decide_permanence("MEMORY_RECORD_STATUS_CHANGED")
        assert d.permanence is EventPermanence.PERMANENT
        assert d.write_permanent is True
        assert d.keep_ring_buffer is False
        assert d.requires_snapshot is False

    def test_permanent_with_snapshot_event(self) -> None:
        d = decide_permanence("KILL_SWITCH_ACTIVATED")
        assert d.permanence is EventPermanence.PERMANENT_WITH_SNAPSHOT
        assert d.write_permanent is True
        assert d.keep_ring_buffer is True
        assert d.requires_snapshot is True
        assert d.human_alert_required is True

    def test_unknown_event_raises_keyerror(self) -> None:
        with pytest.raises(KeyError):
            decide_permanence("NOT_AN_EVENT")


class TestShorthands:
    def test_should_write_permanent_false_for_ring_buffer(self) -> None:
        assert should_write_permanent("WORKSPACE_PULSE") is False

    def test_should_write_permanent_true_for_permanent(self) -> None:
        assert should_write_permanent("MEMORY_RECORD_STATUS_CHANGED") is True

    def test_should_keep_ring_buffer_true_for_ring_buffer(self) -> None:
        assert should_keep_ring_buffer("WORKSPACE_PULSE") is True

    def test_should_keep_ring_buffer_true_for_snapshot(self) -> None:
        assert should_keep_ring_buffer("KILL_SWITCH_ACTIVATED") is True

    def test_requires_snapshot_only_for_snapshot_policy(self) -> None:
        assert requires_snapshot("KILL_SWITCH_ACTIVATED") is True
        assert requires_snapshot("MEMORY_RECORD_STATUS_CHANGED") is False
        assert requires_snapshot("WORKSPACE_PULSE") is False

    def test_requires_human_alert(self) -> None:
        assert requires_human_alert("KILL_SWITCH_ACTIVATED") is True
        assert requires_human_alert("DEONTIC_BYPASS_ATTEMPT") is True
        assert requires_human_alert("WORKSPACE_PULSE") is False


class TestNoPermanenceDowngrade:
    def test_same_to_same_accepted(self) -> None:
        for p in EventPermanence:
            assert_no_permanence_downgrade(old=p, new=p, event_type="WORKSPACE_PULSE")

    @pytest.mark.parametrize(
        ("old", "new"),
        [
            (EventPermanence.EPHEMERAL, EventPermanence.RING_BUFFER_ONLY),
            (EventPermanence.EPHEMERAL, EventPermanence.PERMANENT),
            (EventPermanence.EPHEMERAL, EventPermanence.PERMANENT_WITH_SNAPSHOT),
            (EventPermanence.RING_BUFFER_ONLY, EventPermanence.PERMANENT),
            (
                EventPermanence.RING_BUFFER_ONLY,
                EventPermanence.PERMANENT_WITH_SNAPSHOT,
            ),
            (EventPermanence.PERMANENT, EventPermanence.PERMANENT_WITH_SNAPSHOT),
        ],
    )
    def test_strengthening_accepted(self, old: EventPermanence, new: EventPermanence) -> None:
        assert_no_permanence_downgrade(old=old, new=new, event_type="WORKSPACE_PULSE")

    @pytest.mark.parametrize(
        ("old", "new"),
        [
            (
                EventPermanence.PERMANENT_WITH_SNAPSHOT,
                EventPermanence.PERMANENT,
            ),
            (
                EventPermanence.PERMANENT_WITH_SNAPSHOT,
                EventPermanence.RING_BUFFER_ONLY,
            ),
            (
                EventPermanence.PERMANENT_WITH_SNAPSHOT,
                EventPermanence.EPHEMERAL,
            ),
            (EventPermanence.PERMANENT, EventPermanence.RING_BUFFER_ONLY),
            (EventPermanence.PERMANENT, EventPermanence.EPHEMERAL),
            (EventPermanence.RING_BUFFER_ONLY, EventPermanence.EPHEMERAL),
        ],
    )
    def test_weakening_rejected(self, old: EventPermanence, new: EventPermanence) -> None:
        with pytest.raises(InvariantViolation) as exc_info:
            assert_no_permanence_downgrade(old=old, new=new, event_type="WORKSPACE_PULSE")
        assert exc_info.value.violation_code == "OBSERVER_PERMANENCE_DOWNGRADE_FORBIDDEN"

    def test_evidence_carries_event_type_and_policies(self) -> None:
        with pytest.raises(InvariantViolation) as exc_info:
            assert_no_permanence_downgrade(
                old=EventPermanence.PERMANENT_WITH_SNAPSHOT,
                new=EventPermanence.RING_BUFFER_ONLY,
                event_type="KILL_SWITCH_ACTIVATED",
            )
        assert exc_info.value.evidence["event_type"] == "KILL_SWITCH_ACTIVATED"
        assert exc_info.value.evidence["old_permanence"] == "permanent_with_snapshot"
        assert exc_info.value.evidence["new_permanence"] == "ring_buffer_only"
