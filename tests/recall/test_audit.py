"""Tests for the recall audit emission helpers."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003 (fixture annotation)

import pytest
from sentinel.observer.ledger import JsonlObserverLedger
from sentinel.recall.audit import (
    emit_recall_request,
    emit_recall_result_empty,
    emit_recall_trigger_rejected,
)
from sentinel.recall.protocol import RecallTriggerDecision
from sentinel.runtime.output import ForbiddenOutputViolation
from sentinel.types.memory import MemoryRecord, MemoryRecordStatus, SubjectClass
from sentinel.types.neural_seed import ProvenanceRef


def _record(record_id: str = "rec-1") -> MemoryRecord:
    return MemoryRecord(
        record_id=record_id,
        subject_class=SubjectClass.SOURCE_TRUST,
        payload={"k": "v"},
        status=MemoryRecordStatus.CANDIDATE,
        created_at_ms=1,
        last_status_change_ms=1,
        provenance=ProvenanceRef(source_event_id="src"),
    )


@pytest.fixture
def ledger_path(tmp_path: Path) -> Path:
    return tmp_path / "ledger.jsonl"


@pytest.fixture
def ledger(ledger_path: Path) -> JsonlObserverLedger:
    return JsonlObserverLedger(ledger_path)


class TestTriggerRejected:
    def test_emits_recall_trigger_rejected(self, ledger: JsonlObserverLedger) -> None:
        d = RecallTriggerDecision(triggered=False, reason="below threshold")
        ev = emit_recall_trigger_rejected(ledger, request_id="r-1", decision=d, now_ms=1)
        assert ev.event_type == "RECALL_TRIGGER_REJECTED"
        assert ev.event_family.value == "ingress"
        assert ev.payload["request_id"] == "r-1"
        assert ev.payload["reason"] == "below threshold"

    def test_forbidden_literal_in_reason_rejected(self, ledger: JsonlObserverLedger) -> None:
        d = RecallTriggerDecision(triggered=False, reason="user wants to buy now")
        with pytest.raises(ForbiddenOutputViolation):
            emit_recall_trigger_rejected(ledger, request_id="r-2", decision=d, now_ms=1)


class TestRequestEmitted:
    def test_emits_recall_request_with_score(self, ledger: JsonlObserverLedger) -> None:
        ev = emit_recall_request(
            ledger,
            request_id="r-1",
            selected=_record(),
            score=0.42,
            now_ms=1,
        )
        assert ev.event_type == "RECALL_REQUEST_EMITTED"
        assert ev.payload["record_id"] == "rec-1"
        assert ev.payload["score"] == 0.42
        assert ev.payload["subject_class"] == "source_trust"


class TestResultEmpty:
    def test_emits_recall_result_empty(self, ledger: JsonlObserverLedger) -> None:
        ev = emit_recall_result_empty(ledger, request_id="r-1", candidates_considered=3, now_ms=1)
        assert ev.event_type == "RECALL_RESULT_EMPTY"
        assert ev.payload["candidates_considered"] == 3


class TestChainIntegrity:
    def test_three_audit_events_chain(self, ledger: JsonlObserverLedger) -> None:
        d = RecallTriggerDecision(triggered=False, reason="ok")
        emit_recall_trigger_rejected(ledger, request_id="r-1", decision=d, now_ms=1)
        emit_recall_request(
            ledger,
            request_id="r-2",
            selected=_record(),
            score=0.5,
            now_ms=2,
        )
        emit_recall_result_empty(ledger, request_id="r-3", candidates_considered=0, now_ms=3)
        assert len(ledger.read_all()) == 3
        assert ledger.verify() is True
