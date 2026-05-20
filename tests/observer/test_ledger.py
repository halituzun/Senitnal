"""Tests for the append-only JSONL ObserverEvent ledger.

Discipline tested here (writer layer only):
    - New / missing ledger reads as empty
    - First append sets previous_event_hash=None and computes event_hash
    - Subsequent appends link to the prior line's event_hash
    - Caller-supplied event_hash is overwritten with the computed digest
    - read_all returns events in insertion order
    - verify() True after legitimate appends
    - validate_event_family rejects mismatched family or unknown event
      at append time (InvariantViolation)
    - read_all raises ValueError on malformed JSON line
    - Tampering with the file makes verify() False
"""

from __future__ import annotations

from pathlib import Path  # noqa: TC003 (pytest fixture annotation needs runtime)

import pytest
from sentinel.constitution.violations import InvariantViolation
from sentinel.observer.hash_chain import placeholder_event_hash
from sentinel.observer.ledger import JsonlObserverLedger
from sentinel.types.neural_seed import ProvenanceRef
from sentinel.types.observer import EventFamily, ObserverEvent


def _make_event(
    *,
    event_id: str | None = None,
    event_type: str = "WORKSPACE_PULSE",
    event_family: EventFamily = EventFamily.ATTENTION,
    counter: int = 1,
) -> ObserverEvent:
    return ObserverEvent(
        event_id=event_id if event_id is not None else f"evt-{counter}",
        event_family=event_family,
        event_type=event_type,
        occurred_at_ms=counter,
        payload={"reason": "unit_test", "counter": counter},
        provenance=ProvenanceRef(source_event_id=f"src-{counter}"),
        previous_event_hash=None,
        event_hash=placeholder_event_hash(),
    )


@pytest.fixture
def ledger_path(tmp_path: Path) -> Path:
    return tmp_path / "ledger.jsonl"


class TestEmptyLedger:
    def test_read_all_returns_empty_tuple_for_missing_file(self, ledger_path: Path) -> None:
        ledger = JsonlObserverLedger(ledger_path)
        assert ledger.read_all() == ()

    def test_verify_true_for_empty_ledger(self, ledger_path: Path) -> None:
        ledger = JsonlObserverLedger(ledger_path)
        assert ledger.verify() is True


class TestAppendFirst:
    def test_first_append_sets_no_previous_hash(self, ledger_path: Path) -> None:
        ledger = JsonlObserverLedger(ledger_path)
        appended = ledger.append(_make_event(counter=1))
        assert appended.previous_event_hash is None

    def test_first_append_computes_event_hash(self, ledger_path: Path) -> None:
        ledger = JsonlObserverLedger(ledger_path)
        appended = ledger.append(_make_event(counter=1))
        assert appended.event_hash != placeholder_event_hash()
        assert appended.event_hash.startswith("sha256:")

    def test_caller_event_hash_is_overwritten(self, ledger_path: Path) -> None:
        ledger = JsonlObserverLedger(ledger_path)
        ev = _make_event(counter=1).model_copy(update={"event_hash": "sha256:" + ("a" * 64)})
        appended = ledger.append(ev)
        assert appended.event_hash != "sha256:" + ("a" * 64)


class TestAppendChainLinks:
    def test_second_event_links_to_first(self, ledger_path: Path) -> None:
        ledger = JsonlObserverLedger(ledger_path)
        first = ledger.append(_make_event(counter=1))
        second = ledger.append(_make_event(counter=2))
        assert second.previous_event_hash == first.event_hash

    def test_read_all_returns_events_in_order(self, ledger_path: Path) -> None:
        ledger = JsonlObserverLedger(ledger_path)
        ledger.append(_make_event(counter=1))
        ledger.append(_make_event(counter=2))
        ledger.append(_make_event(counter=3))
        events = ledger.read_all()
        assert tuple(e.event_id for e in events) == ("evt-1", "evt-2", "evt-3")

    def test_verify_true_for_valid_chain(self, ledger_path: Path) -> None:
        ledger = JsonlObserverLedger(ledger_path)
        ledger.append(_make_event(counter=1))
        ledger.append(_make_event(counter=2))
        ledger.append(_make_event(counter=3))
        assert ledger.verify() is True


class TestCatalogValidation:
    def test_family_mismatch_rejected_on_append(self, ledger_path: Path) -> None:
        ledger = JsonlObserverLedger(ledger_path)
        bad = _make_event(
            event_type="WORKSPACE_PULSE",
            event_family=EventFamily.MEMORY,  # catalog says ATTENTION
        )
        with pytest.raises(InvariantViolation) as exc_info:
            ledger.append(bad)
        assert exc_info.value.violation_code == "OBSERVER_EVENT_FAMILY_MATCHES_CATALOG"
        # Nothing should have been written
        assert ledger.read_all() == ()

    def test_unknown_event_type_rejected_on_append(self, ledger_path: Path) -> None:
        ledger = JsonlObserverLedger(ledger_path)
        bad = _make_event(
            event_type="NOT_A_CANONICAL_EVENT",
            event_family=EventFamily.LEDGER_META,
        )
        with pytest.raises(InvariantViolation) as exc_info:
            ledger.append(bad)
        assert exc_info.value.violation_code == "OBSERVER_EVENT_TYPE_UNKNOWN"


class TestRead:
    def test_malformed_json_raises_value_error(self, ledger_path: Path) -> None:
        ledger = JsonlObserverLedger(ledger_path)
        ledger.append(_make_event(counter=1))
        with ledger_path.open("ab") as fh:
            fh.write(b"not-valid-json\n")
        with pytest.raises(ValueError):
            ledger.read_all()


class TestTamperDetection:
    def test_tampered_file_makes_verify_false(self, ledger_path: Path) -> None:
        ledger = JsonlObserverLedger(ledger_path)
        ledger.append(_make_event(counter=1))
        ledger.append(_make_event(counter=2))
        # Replace counter=2 line's payload with a different value, keeping
        # JSON structure valid but invalidating the recorded event_hash.
        lines = ledger_path.read_bytes().splitlines()
        tampered = lines[1].replace(b'"counter":2', b'"counter":42')
        ledger_path.write_bytes(lines[0] + b"\n" + tampered + b"\n")
        assert ledger.verify() is False


class TestMultipleEventTypes:
    def test_mixed_canonical_events_link_correctly(self, ledger_path: Path) -> None:
        ledger = JsonlObserverLedger(ledger_path)
        e1 = ledger.append(
            _make_event(
                counter=1,
                event_type="WORKSPACE_PULSE",
                event_family=EventFamily.ATTENTION,
            )
        )
        e2 = ledger.append(
            _make_event(
                counter=2,
                event_type="OBSERVATION_INGESTED",
                event_family=EventFamily.INGRESS,
            )
        )
        e3 = ledger.append(
            _make_event(
                counter=3,
                event_type="LEDGER_STATE_CHANGED",
                event_family=EventFamily.LEDGER_META,
            )
        )
        assert e2.previous_event_hash == e1.event_hash
        assert e3.previous_event_hash == e2.event_hash
        assert ledger.verify() is True
