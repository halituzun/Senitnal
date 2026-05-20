"""V6 — Deontic policy record builder tests."""

from __future__ import annotations

from sentinel.policy.record_builder import build_deontic_policy_candidate_record
from sentinel.types.memory import MemoryRecordStatus, SubjectClass
from sentinel.types.neural_seed import ProvenanceRef

from tests.policy._fixtures import make_artifact


class TestRecordBuilder:
    def test_builds_candidate_deontic_policy(self) -> None:
        rec = build_deontic_policy_candidate_record(
            artifact=make_artifact(),
            provenance=ProvenanceRef(source_event_id="ev-1"),
            created_at_ms=1_000_000,
            evidence_refs=("ev-1", "approval-1"),
        )
        assert rec.subject_class is SubjectClass.DEONTIC_POLICY
        assert rec.status is MemoryRecordStatus.CANDIDATE
        assert rec.causal_refs == ("ev-1", "approval-1")
        assert rec.external_corroboration_refs == ("ev-1", "approval-1")
        assert rec.internal_only_refs == ()

    def test_payload_json_compatible(self) -> None:
        rec = build_deontic_policy_candidate_record(
            artifact=make_artifact(),
            provenance=ProvenanceRef(source_event_id="ev-1"),
            created_at_ms=1_000_000,
            evidence_refs=("ev-1",),
        )
        assert isinstance(rec.payload, dict)
        assert rec.payload["policy_id"] == "policy-1"

    def test_no_path_to_verified(self) -> None:
        rec = build_deontic_policy_candidate_record(
            artifact=make_artifact(),
            provenance=ProvenanceRef(source_event_id="ev-1"),
            created_at_ms=1_000_000,
            evidence_refs=("ev-1",),
        )
        # Builder never returns VERIFIED.
        assert rec.status is MemoryRecordStatus.CANDIDATE
