"""Schema tests for MemoryRecord.

Constitutional discipline tested here (schema layer only):
    - 16 closed SubjectClass values
    - foreign_instance_origin is NOT a SubjectClass (provenance metadata)
    - 7 closed MemoryRecordStatus values
    - record_id / payload non-empty
    - timestamps non-negative; last_status_change_ms >= created_at_ms
    - Reference tuples (causal / external_corroboration / internal_only)
    - extra="forbid"
    - Frozen immutability
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sentinel.types.memory import MemoryRecord, MemoryRecordStatus, SubjectClass
from sentinel.types.neural_seed import ProvenanceRef


def _ref() -> ProvenanceRef:
    return ProvenanceRef(source_event_id="evt-source", source_spec="test")


def _base_kwargs() -> dict[str, object]:
    return {
        "record_id": "rec-0001",
        "subject_class": SubjectClass.SOURCE_TRUST,
        "payload": {"reliability_band": "high"},
        "status": MemoryRecordStatus.CANDIDATE,
        "provenance": _ref(),
        "created_at_ms": 1_700_000_000_000,
        "last_status_change_ms": 1_700_000_000_000,
    }


# ---------------------------------------------------------------------------
# Closed taxonomies
# ---------------------------------------------------------------------------


class TestSubjectClass:
    def test_sixteen_values(self) -> None:
        assert len(SubjectClass) == 16

    def test_canonical_names(self) -> None:
        expected = {
            "source_trust",
            "adapter_trust",
            "procedural",
            "structured_fact",
            "incident",
            "episodic",
            "narrative_claim",
            "causal_explanation",
            "decision_rationale",
            "deontic_policy",
            "bootstrap_reference",
            "signed_administrative_reference",
            "operator_decision_record",
            "incident_human_record",
            "deontic_kill_switch_action_record",
            "numerics_artifact_reference",
        }
        assert {s.value for s in SubjectClass} == expected

    def test_foreign_instance_origin_not_a_subject_class(self) -> None:
        """foreign_instance_origin is provenance metadata, not SubjectClass.

        Per MEMORY_WRITE_GATE_NUMERICS §5 (P §5 patch).
        """
        values = {s.value for s in SubjectClass}
        assert "foreign_instance_origin" not in values

    def test_incident_human_record_is_a_subject_class(self) -> None:
        """incident_human_record is canonical per MEMORY_CONTRACT §3."""
        values = {s.value for s in SubjectClass}
        assert "incident_human_record" in values


class TestMemoryRecordStatus:
    def test_seven_statuses(self) -> None:
        assert len(MemoryRecordStatus) == 7

    def test_canonical_names(self) -> None:
        expected = {
            "candidate",
            "verified",
            "active",
            "superseded",
            "rejected",
            "expired",
            "quarantined",
        }
        assert {s.value for s in MemoryRecordStatus} == expected


# ---------------------------------------------------------------------------
# Valid construction
# ---------------------------------------------------------------------------


class TestMemoryRecordValid:
    def test_minimal_construction(self) -> None:
        rec = MemoryRecord.model_validate(_base_kwargs())
        assert rec.record_id == "rec-0001"
        assert rec.subject_class == SubjectClass.SOURCE_TRUST
        assert rec.status == MemoryRecordStatus.CANDIDATE
        assert rec.causal_refs == ()
        assert rec.external_corroboration_refs == ()
        assert rec.internal_only_refs == ()

    @pytest.mark.parametrize("subject_class", list(SubjectClass))
    def test_every_subject_class_accepted(self, subject_class: SubjectClass) -> None:
        kwargs = _base_kwargs()
        kwargs["subject_class"] = subject_class
        rec = MemoryRecord.model_validate(kwargs)
        assert rec.subject_class == subject_class

    @pytest.mark.parametrize("status", list(MemoryRecordStatus))
    def test_every_status_accepted(self, status: MemoryRecordStatus) -> None:
        """All 7 statuses are schema-valid.

        Status-transition logic (which → which) is Phase 7's Memory Write
        Gate's job, not the schema's.
        """
        kwargs = _base_kwargs()
        kwargs["status"] = status
        rec = MemoryRecord.model_validate(kwargs)
        assert rec.status == status

    def test_reference_tuples_accepted(self) -> None:
        kwargs = _base_kwargs()
        kwargs["causal_refs"] = ("rec-A", "rec-B")
        kwargs["external_corroboration_refs"] = ("rec-C",)
        kwargs["internal_only_refs"] = ("rec-D", "rec-E", "rec-F")
        rec = MemoryRecord.model_validate(kwargs)
        assert rec.causal_refs == ("rec-A", "rec-B")
        assert rec.external_corroboration_refs == ("rec-C",)
        assert len(rec.internal_only_refs) == 3

    def test_last_status_change_after_creation_accepted(self) -> None:
        kwargs = _base_kwargs()
        kwargs["created_at_ms"] = 1_000
        kwargs["last_status_change_ms"] = 2_000
        rec = MemoryRecord.model_validate(kwargs)
        assert rec.last_status_change_ms > rec.created_at_ms


# ---------------------------------------------------------------------------
# Invalid construction
# ---------------------------------------------------------------------------


class TestMemoryRecordInvalid:
    def test_empty_record_id_rejected(self) -> None:
        kwargs = _base_kwargs()
        kwargs["record_id"] = ""
        with pytest.raises(ValidationError):
            MemoryRecord.model_validate(kwargs)

    def test_empty_payload_rejected(self) -> None:
        kwargs = _base_kwargs()
        kwargs["payload"] = {}
        with pytest.raises(ValidationError):
            MemoryRecord.model_validate(kwargs)

    def test_invalid_subject_class_rejected(self) -> None:
        kwargs = _base_kwargs()
        kwargs["subject_class"] = "not_a_subject"
        with pytest.raises(ValidationError):
            MemoryRecord.model_validate(kwargs)

    def test_foreign_instance_origin_as_subject_class_rejected(self) -> None:
        """foreign_instance_origin is provenance metadata, not subject_class.

        Per P §5 patch — it must not be admitted as a SubjectClass value.
        """
        kwargs = _base_kwargs()
        kwargs["subject_class"] = "foreign_instance_origin"
        with pytest.raises(ValidationError):
            MemoryRecord.model_validate(kwargs)

    def test_invalid_status_rejected(self) -> None:
        kwargs = _base_kwargs()
        kwargs["status"] = "not_a_status"
        with pytest.raises(ValidationError):
            MemoryRecord.model_validate(kwargs)

    def test_negative_created_at_rejected(self) -> None:
        kwargs = _base_kwargs()
        kwargs["created_at_ms"] = -1
        with pytest.raises(ValidationError):
            MemoryRecord.model_validate(kwargs)

    def test_negative_last_status_change_rejected(self) -> None:
        kwargs = _base_kwargs()
        kwargs["last_status_change_ms"] = -1
        with pytest.raises(ValidationError):
            MemoryRecord.model_validate(kwargs)

    def test_last_status_change_before_creation_rejected(self) -> None:
        """A status change cannot happen before the record was created."""
        kwargs = _base_kwargs()
        kwargs["created_at_ms"] = 2_000
        kwargs["last_status_change_ms"] = 1_000
        with pytest.raises(ValidationError):
            MemoryRecord.model_validate(kwargs)

    def test_extra_field_rejected(self) -> None:
        kwargs = _base_kwargs()
        kwargs["tampered"] = True
        with pytest.raises(ValidationError):
            MemoryRecord.model_validate(kwargs)

    def test_missing_provenance_rejected(self) -> None:
        kwargs = _base_kwargs()
        del kwargs["provenance"]
        with pytest.raises(ValidationError):
            MemoryRecord.model_validate(kwargs)


# ---------------------------------------------------------------------------
# Frozen immutability
# ---------------------------------------------------------------------------


class TestMemoryRecordImmutable:
    def test_status_cannot_be_modified(self) -> None:
        rec = MemoryRecord.model_validate(_base_kwargs())
        with pytest.raises(ValidationError):
            setattr(rec, "status", MemoryRecordStatus.VERIFIED)  # noqa: B010

    def test_subject_class_cannot_be_modified(self) -> None:
        rec = MemoryRecord.model_validate(_base_kwargs())
        with pytest.raises(ValidationError):
            setattr(rec, "subject_class", SubjectClass.NARRATIVE_CLAIM)  # noqa: B010

    def test_internal_only_refs_cannot_be_replaced(self) -> None:
        rec = MemoryRecord.model_validate(_base_kwargs())
        with pytest.raises(ValidationError):
            setattr(rec, "internal_only_refs", ("rec-X",))  # noqa: B010
