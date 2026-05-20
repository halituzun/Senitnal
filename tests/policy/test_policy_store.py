"""V6 — InMemoryPolicyStore tests."""

from __future__ import annotations

import pytest
from sentinel.policy.record_builder import build_deontic_policy_candidate_record
from sentinel.policy.store import InMemoryPolicyStore
from sentinel.types.memory import MemoryRecord, MemoryRecordStatus, SubjectClass
from sentinel.types.neural_seed import ProvenanceRef

from tests.policy._fixtures import make_artifact


def _candidate(artifact_id: str = "art-1") -> MemoryRecord:
    return build_deontic_policy_candidate_record(
        artifact=make_artifact(artifact_id=artifact_id),
        provenance=ProvenanceRef(source_event_id=f"ev-{artifact_id}"),
        created_at_ms=1_000_000,
        evidence_refs=("approval-1",),
    )


def _verified(artifact_id: str = "art-1", created_at_ms: int = 1_000_000) -> MemoryRecord:
    return build_deontic_policy_candidate_record(
        artifact=make_artifact(artifact_id=artifact_id, created_at_ms=created_at_ms),
        provenance=ProvenanceRef(source_event_id=f"ev-{artifact_id}"),
        created_at_ms=created_at_ms,
        evidence_refs=("approval-1",),
    ).model_copy(update={"status": MemoryRecordStatus.VERIFIED})


class TestStoreBasics:
    def test_add_candidate(self) -> None:
        store = InMemoryPolicyStore()
        rec = _candidate()
        store.add_candidate(rec)
        assert store.get(rec.record_id) is rec

    def test_duplicate_rejected(self) -> None:
        store = InMemoryPolicyStore()
        store.add_candidate(_candidate())
        with pytest.raises(ValueError, match="duplicate"):
            store.add_candidate(_candidate())

    def test_non_deontic_subject_rejected(self, tmp_path: object) -> None:
        store = InMemoryPolicyStore()
        bad = MemoryRecord(
            record_id="bad-1",
            subject_class=SubjectClass.SOURCE_TRUST,
            payload={"x": 1},
            status=MemoryRecordStatus.CANDIDATE,
            provenance=ProvenanceRef(source_event_id="ev"),
            created_at_ms=0,
            last_status_change_ms=0,
        )
        with pytest.raises(ValueError, match="DEONTIC_POLICY"):
            store.add_candidate(bad)


class TestActivation:
    def test_candidate_cannot_activate(self) -> None:
        store = InMemoryPolicyStore()
        rec = _candidate()
        store.add_candidate(rec)
        with pytest.raises(ValueError, match="VERIFIED"):
            store.activate_verified_policy(
                record_id=rec.record_id,
                human_approval_ref="approval-1",
                now_ms=2_000_000,
            )

    def test_verified_activates_with_approval(self) -> None:
        store = InMemoryPolicyStore()
        rec = _verified()
        store.add_verified(rec)
        outcome = store.activate_verified_policy(
            record_id=rec.record_id,
            human_approval_ref="approval-1",
            now_ms=2_000_000,
        )
        assert outcome.activated_record.status is MemoryRecordStatus.ACTIVE
        assert outcome.superseded_record is None

    def test_activation_without_approval_rejected(self) -> None:
        store = InMemoryPolicyStore()
        rec = _verified()
        store.add_verified(rec)
        with pytest.raises(ValueError, match="human_approval_ref"):
            store.activate_verified_policy(
                record_id=rec.record_id,
                human_approval_ref="",
                now_ms=2_000_000,
            )

    def test_one_active_per_scope_supersede(self) -> None:
        store = InMemoryPolicyStore()
        old = _verified(artifact_id="old", created_at_ms=1_000_000)
        new = _verified(artifact_id="new", created_at_ms=1_500_000)
        store.add_verified(old)
        store.add_verified(new)

        store.activate_verified_policy(
            record_id=old.record_id, human_approval_ref="op-1", now_ms=2_000_000
        )
        outcome = store.activate_verified_policy(
            record_id=new.record_id, human_approval_ref="op-2", now_ms=3_000_000
        )
        assert outcome.superseded_record is not None
        assert outcome.superseded_record.status is MemoryRecordStatus.SUPERSEDED
        assert outcome.activated_record.status is MemoryRecordStatus.ACTIVE
        active = store.get_active_policy_for_scope_id("scope-1")
        assert active is not None
        assert active.record_id == new.record_id


class TestEmergencyRevert:
    def test_revert_to_previous_verified_succeeds(self) -> None:
        store = InMemoryPolicyStore()
        old = _verified(artifact_id="old", created_at_ms=1_000_000)
        new = _verified(artifact_id="new", created_at_ms=1_500_000)
        store.add_verified(old)
        store.add_verified(new)
        store.activate_verified_policy(
            record_id=old.record_id, human_approval_ref="op", now_ms=2_000_000
        )
        store.activate_verified_policy(
            record_id=new.record_id, human_approval_ref="op", now_ms=2_500_000
        )

        outcome = store.revert_to_previous_verified(
            from_record_id=new.record_id,
            to_previous_record_id=old.record_id,
            now_ms=3_000_000,
        )
        assert outcome.activated_record.record_id == old.record_id
        assert outcome.activated_record.status is MemoryRecordStatus.ACTIVE
        assert outcome.superseded_record is not None
        assert outcome.superseded_record.record_id == new.record_id

    def test_revert_forward_to_new_policy_rejected(self) -> None:
        store = InMemoryPolicyStore()
        old = _verified(artifact_id="old", created_at_ms=1_000_000)
        newer = _verified(artifact_id="newer", created_at_ms=1_500_000)
        store.add_verified(old)
        store.add_verified(newer)
        store.activate_verified_policy(
            record_id=old.record_id, human_approval_ref="op", now_ms=2_000_000
        )
        with pytest.raises(ValueError, match="precede"):
            store.revert_to_previous_verified(
                from_record_id=old.record_id,
                to_previous_record_id=newer.record_id,
                now_ms=3_000_000,
            )
