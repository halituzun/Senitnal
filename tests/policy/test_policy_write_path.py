"""V6 — Policy write path tests (MWG integration)."""

from __future__ import annotations

from pathlib import Path

from sentinel.gates.memory_write import MemoryWriteResolution
from sentinel.observer.ledger import JsonlObserverLedger
from sentinel.policy.store import InMemoryPolicyStore
from sentinel.policy.write_path import submit_financial_policy_candidate
from sentinel.types.memory import MemoryRecordStatus
from sentinel.types.neural_seed import ProvenanceRef

from tests.policy._fixtures import make_artifact


class TestPolicyWritePath:
    def test_candidate_submitted_and_stored(self, tmp_path: Path) -> None:
        store = InMemoryPolicyStore()
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        result = submit_financial_policy_candidate(
            store=store,
            ledger=ledger,
            artifact=make_artifact(),
            provenance=ProvenanceRef(source_event_id="ev-1"),
            created_at_ms=1_000_000,
            evidence_refs=("ev-1", "approval-1"),
        )
        assert result.stored is True
        assert result.outcome.resolution is MemoryWriteResolution.ACCEPTED_CANDIDATE
        assert result.record.status is MemoryRecordStatus.CANDIDATE
        assert store.get(result.record.record_id) is not None

    def test_m1_audit_emitted(self, tmp_path: Path) -> None:
        path = tmp_path / "l.jsonl"
        ledger = JsonlObserverLedger(path)
        store = InMemoryPolicyStore()
        submit_financial_policy_candidate(
            store=store,
            ledger=ledger,
            artifact=make_artifact(),
            provenance=ProvenanceRef(source_event_id="ev-1"),
            created_at_ms=1_000_000,
            evidence_refs=("ev-1",),
        )
        content = path.read_text(encoding="utf-8")
        assert "MEMORY_RECORD_STATUS_CHANGED" in content
        assert "deontic_policy" in content

    def test_no_verified_or_active_outcome(self, tmp_path: Path) -> None:
        store = InMemoryPolicyStore()
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        result = submit_financial_policy_candidate(
            store=store,
            ledger=ledger,
            artifact=make_artifact(),
            provenance=ProvenanceRef(source_event_id="ev-1"),
            created_at_ms=1_000_000,
            evidence_refs=("ev-1",),
        )
        assert result.record.status is MemoryRecordStatus.CANDIDATE
        assert result.outcome.final_status is MemoryRecordStatus.CANDIDATE

    def test_write_path_source_has_no_action_intent_or_eval_action(self) -> None:
        from sentinel.policy import write_path

        src = Path(write_path.__file__).read_text(encoding="utf-8")
        assert "ApprovedActionIntent" not in src
        assert "evaluate_action" not in src
