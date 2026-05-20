"""Tests for the Memory Write Gate (silent, candidate-only in MVP)."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003 (fixture annotation)

import pytest
from sentinel.gates.memory_write import (
    EvidenceAxis,
    MemoryWriteRequest,
    MemoryWriteResolution,
    submit_memory_write,
)
from sentinel.observer.ledger import JsonlObserverLedger
from sentinel.types.memory import MemoryRecord, MemoryRecordStatus, SubjectClass
from sentinel.types.neural_seed import ProvenanceRef


def _record(
    *,
    record_id: str = "rec-1",
    subject_class: SubjectClass = SubjectClass.SOURCE_TRUST,
    status: MemoryRecordStatus = MemoryRecordStatus.CANDIDATE,
) -> MemoryRecord:
    return MemoryRecord(
        record_id=record_id,
        subject_class=subject_class,
        payload={"detail": "test"},
        status=status,
        created_at_ms=42,
        last_status_change_ms=42,
        provenance=ProvenanceRef(source_event_id="src"),
    )


@pytest.fixture
def ledger_path(tmp_path: Path) -> Path:
    return tmp_path / "ledger.jsonl"


@pytest.fixture
def ledger(ledger_path: Path) -> JsonlObserverLedger:
    return JsonlObserverLedger(ledger_path)


class TestRequestValidation:
    def test_invalid_requested_status_rejected(self) -> None:
        with pytest.raises(ValueError):
            MemoryWriteRequest(
                record=_record(),
                evidence_axis=EvidenceAxis.DIRECT_OBSERVATION,
                requested_status=MemoryRecordStatus.ACTIVE,
                rationale="r",
            )

    def test_empty_rationale_rejected(self) -> None:
        with pytest.raises(ValueError):
            MemoryWriteRequest(
                record=_record(),
                evidence_axis=EvidenceAxis.DIRECT_OBSERVATION,
                requested_status=MemoryRecordStatus.CANDIDATE,
                rationale="",
            )


class TestWhitelist:
    def test_accepted_pair_writes_candidate(self, ledger: JsonlObserverLedger) -> None:
        req = MemoryWriteRequest(
            record=_record(subject_class=SubjectClass.SOURCE_TRUST),
            evidence_axis=EvidenceAxis.DIRECT_OBSERVATION,
            requested_status=MemoryRecordStatus.CANDIDATE,
            rationale="ok",
        )
        outcome = submit_memory_write(
            ledger,
            req,
            provenance=ProvenanceRef(source_event_id="src"),
            now_ms=1,
        )
        assert outcome.resolution is MemoryWriteResolution.ACCEPTED_CANDIDATE
        assert outcome.final_status is MemoryRecordStatus.CANDIDATE

    def test_rejected_pair(self, ledger: JsonlObserverLedger) -> None:
        # NARRATIVE_CLAIM + DIRECT_OBSERVATION is NOT in the whitelist.
        req = MemoryWriteRequest(
            record=_record(subject_class=SubjectClass.NARRATIVE_CLAIM),
            evidence_axis=EvidenceAxis.DIRECT_OBSERVATION,
            requested_status=MemoryRecordStatus.CANDIDATE,
            rationale="ok",
        )
        outcome = submit_memory_write(
            ledger,
            req,
            provenance=ProvenanceRef(source_event_id="src"),
            now_ms=1,
        )
        assert outcome.resolution is MemoryWriteResolution.REJECTED
        assert outcome.final_status is None


class TestVerifiedDowngradeInMvp:
    def test_verified_request_downgraded(self, ledger: JsonlObserverLedger) -> None:
        req = MemoryWriteRequest(
            record=_record(),
            evidence_axis=EvidenceAxis.DIRECT_OBSERVATION,
            requested_status=MemoryRecordStatus.VERIFIED,
            rationale="want verified",
        )
        outcome = submit_memory_write(
            ledger,
            req,
            provenance=ProvenanceRef(source_event_id="src"),
            now_ms=1,
        )
        assert outcome.resolution is MemoryWriteResolution.DOWNGRADED_TO_CANDIDATE
        assert outcome.final_status is MemoryRecordStatus.CANDIDATE


class TestAuditEmission:
    def test_accepted_emits_status_changed(self, ledger: JsonlObserverLedger) -> None:
        req = MemoryWriteRequest(
            record=_record(),
            evidence_axis=EvidenceAxis.DIRECT_OBSERVATION,
            requested_status=MemoryRecordStatus.CANDIDATE,
            rationale="ok",
        )
        submit_memory_write(
            ledger,
            req,
            provenance=ProvenanceRef(source_event_id="src"),
            now_ms=1,
        )
        on_disk = ledger.read_all()
        assert len(on_disk) == 1
        assert on_disk[0].event_type == "MEMORY_RECORD_STATUS_CHANGED"
        assert on_disk[0].payload["new_status"] == "candidate"

    def test_rejected_emits_status_changed(self, ledger: JsonlObserverLedger) -> None:
        req = MemoryWriteRequest(
            record=_record(subject_class=SubjectClass.NARRATIVE_CLAIM),
            evidence_axis=EvidenceAxis.DIRECT_OBSERVATION,
            requested_status=MemoryRecordStatus.CANDIDATE,
            rationale="ok",
        )
        submit_memory_write(
            ledger,
            req,
            provenance=ProvenanceRef(source_event_id="src"),
            now_ms=1,
        )
        on_disk = ledger.read_all()
        assert len(on_disk) == 1
        assert on_disk[0].payload["new_status"] == "rejected"


class TestSilent:
    def test_outcome_resolution_is_never_active_in_mvp(self, ledger: JsonlObserverLedger) -> None:
        """No MVP path can return ACCEPTED_VERIFIED."""
        for ax in EvidenceAxis:
            for sc in SubjectClass:
                req = MemoryWriteRequest(
                    record=_record(subject_class=sc),
                    evidence_axis=ax,
                    requested_status=MemoryRecordStatus.VERIFIED,
                    rationale="probe",
                )
                outcome = submit_memory_write(
                    ledger,
                    req,
                    provenance=ProvenanceRef(source_event_id="src"),
                    now_ms=1,
                )
                assert outcome.resolution is not MemoryWriteResolution.ACCEPTED_VERIFIED
