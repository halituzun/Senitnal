"""V4 — MWG evidence integration + replay financial pipeline tests."""

from __future__ import annotations

from pathlib import Path

from sentinel.memory.builder import build_candidate_financial_memory_record
from sentinel.memory.financial import LatencyPatternPayload
from sentinel.memory.replay_evidence import (
    submit_outcome_alignment_evidence,
    submit_replay_survival_evidence,
)
from sentinel.memory.store import InMemoryExplicitMemoryStore
from sentinel.observer.ledger import JsonlObserverLedger
from sentinel.replay.budget import ReplayBudget, ReplayBudgetState
from sentinel.replay.outcome_alignment import OutcomeAlignmentEvidence, OutcomeRef
from sentinel.replay.survival import ReplaySurvivalEvidence
from sentinel.runtime.replay_financial_pipeline import (
    run_replay_financial_pipeline,
)
from sentinel.types.memory import (
    MemoryRecord,
    MemoryRecordStatus,
    SubjectClass,
)
from sentinel.types.neural_seed import ProvenanceRef


def _latency_payload(record_key: str = "lat-001") -> LatencyPatternPayload:
    return LatencyPatternPayload(
        record_key=record_key,
        source_adapter_id="synthetic",
        venue_hash="sha256:venue",
        avg_latency_ms=10.0,
        p95_latency_ms=20.0,
        max_latency_ms=30.0,
        stale_ratio=0.1,
        sample_count=10,
        confidence=0.8,
        source_event_ids=("ev-1",),
    )


def _candidate(record_key: str = "lat-001") -> MemoryRecord:
    return build_candidate_financial_memory_record(
        payload=_latency_payload(record_key),
        provenance=ProvenanceRef(source_event_id="ev-1"),
        created_at_ms=1000,
        source_event_ids=("ev-1",),
    )


def _rejected_record() -> MemoryRecord:
    return MemoryRecord(
        record_id="rec-rejected",
        subject_class=SubjectClass.SOURCE_TRUST,
        payload={"x": 1},
        status=MemoryRecordStatus.REJECTED,
        provenance=ProvenanceRef(source_event_id="ev-1"),
        created_at_ms=0,
        last_status_change_ms=0,
    )


def _survival_evidence(min_sessions: bool = True) -> ReplaySurvivalEvidence:
    return ReplaySurvivalEvidence(
        evidence_id="surv-1",
        session_id="s-1",
        memory_record_id="rec-1",
        ablation_ids=("a1",),
        survival_score=0.5,
        min_sessions_satisfied=min_sessions,
        session_separation_ms=0,
        created_at_ms=0,
    )


def _outcome_evidence(stale: bool = False) -> OutcomeAlignmentEvidence:
    ref = OutcomeRef(
        outcome_ref_id="or-1",
        source_event_id="ev-x",
        observed_at_ms=200,
        confidence=0.8,
        external=True,
        payload={"observation": "matched"},
    )
    return OutcomeAlignmentEvidence(
        evidence_id="align-1",
        session_id="s-1",
        memory_record_id="rec-1",
        outcome_refs=(ref,),
        alignment_score=0.7,
        stale=stale,
        created_at_ms=0,
    )


def _budget_state() -> ReplayBudgetState:
    budget = ReplayBudget(
        budget_id="b-1",
        max_sessions_per_cycle=5,
        max_sessions_per_24h_window=10,
        max_events_per_session=10,
        max_counterfactual_branches=2,
        max_session_duration_ms=10_000,
        replay_cooldown_ms=0,
        replay_fatigue_accum_rate=0.05,
        restore_continuity_required=True,
    )
    return ReplayBudgetState(budget=budget)


class TestReplayEvidenceWrapper:
    def test_usable_survival_evidence_accepted(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        rec = _candidate()
        result = submit_replay_survival_evidence(
            ledger=ledger,
            record=rec,
            evidence=_survival_evidence(min_sessions=True),
            now_ms=1000,
        )
        assert result.accepted is True
        assert result.proposal.usable_for_gate is True

    def test_unusable_survival_evidence_rejected(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        rec = _candidate()
        result = submit_replay_survival_evidence(
            ledger=ledger,
            record=rec,
            evidence=_survival_evidence(min_sessions=False),
            now_ms=1000,
        )
        assert result.accepted is False

    def test_rejected_record_rejects_evidence(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        result = submit_replay_survival_evidence(
            ledger=ledger,
            record=_rejected_record(),
            evidence=_survival_evidence(min_sessions=True),
            now_ms=1000,
        )
        assert result.accepted is False
        assert "terminal status" in result.reason

    def test_outcome_alignment_external_accepted(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        rec = _candidate()
        result = submit_outcome_alignment_evidence(
            ledger=ledger,
            record=rec,
            evidence=_outcome_evidence(stale=False),
            now_ms=1000,
        )
        assert result.accepted is True

    def test_outcome_alignment_stale_rejected(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        rec = _candidate()
        result = submit_outcome_alignment_evidence(
            ledger=ledger,
            record=rec,
            evidence=_outcome_evidence(stale=True),
            now_ms=1000,
        )
        assert result.accepted is False

    def test_audit_event_emitted_only_on_accept(self, tmp_path: Path) -> None:
        ledger_path = tmp_path / "l.jsonl"
        ledger = JsonlObserverLedger(ledger_path)
        # Unusable -> no audit.
        submit_replay_survival_evidence(
            ledger=ledger,
            record=_candidate(),
            evidence=_survival_evidence(min_sessions=False),
            now_ms=1000,
        )
        content_before = ledger_path.read_text(encoding="utf-8") if ledger_path.exists() else ""
        assert "MEMORY_VERIFICATION_EVIDENCE_PROPOSED" not in content_before
        # Usable -> audit emitted.
        submit_replay_survival_evidence(
            ledger=ledger,
            record=_candidate(record_key="lat-002"),
            evidence=_survival_evidence(min_sessions=True),
            now_ms=1000,
        )
        content_after = ledger_path.read_text(encoding="utf-8")
        assert "MEMORY_VERIFICATION_EVIDENCE_PROPOSED" in content_after


class TestReplayFinancialPipeline:
    def test_candidate_gets_session_audit(self, tmp_path: Path) -> None:
        store = InMemoryExplicitMemoryStore()
        rec = _candidate()
        store.add(rec)
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        result = run_replay_financial_pipeline(
            candidates=[rec],
            store=store,
            ledger=ledger,
            budget_state=_budget_state(),
        )
        assert result.sessions_started == 1
        assert result.sessions_completed == 1
        assert result.records_promoted_to_verified == 0
        assert result.live_event_count == 0
        assert result.action_count == 0
        assert result.hash_chain_valid is True
        content = (tmp_path / "l.jsonl").read_text(encoding="utf-8")
        assert "REPLAY_SESSION_STATUS_CHANGED" in content

    def test_no_verified_promotion(self, tmp_path: Path) -> None:
        store = InMemoryExplicitMemoryStore()
        rec = _candidate()
        store.add(rec)
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        result = run_replay_financial_pipeline(
            candidates=[rec],
            store=store,
            ledger=ledger,
            budget_state=_budget_state(),
        )
        # Records remain CANDIDATE — pipeline does not modify them.
        same_record = store.get(rec.record_id)
        assert same_record is not None
        assert same_record.status is MemoryRecordStatus.CANDIDATE
        assert result.records_promoted_to_verified == 0

    def test_external_outcome_alignment_produces_evidence(self, tmp_path: Path) -> None:
        store = InMemoryExplicitMemoryStore()
        rec = _candidate()
        store.add(rec)
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        external_ref = OutcomeRef(
            outcome_ref_id="or-1",
            source_event_id="ev-real",
            observed_at_ms=2000,
            confidence=0.9,
            external=True,
            payload={"observation": "matched"},
        )
        result = run_replay_financial_pipeline(
            candidates=[rec],
            store=store,
            ledger=ledger,
            budget_state=_budget_state(),
            outcome_refs_by_record={rec.record_id: (external_ref,)},
        )
        assert result.outcome_alignment_evidence_count >= 1

    def test_budget_exhaustion_stops_sessions(self, tmp_path: Path) -> None:
        store = InMemoryExplicitMemoryStore()
        # Stagger created_at_ms so each iteration's now_ms moves
        # forward; otherwise the cooldown check sees negative
        # elapsed and blocks all but the first.
        recs = [
            build_candidate_financial_memory_record(
                payload=_latency_payload(f"lat-{i:03d}"),
                provenance=ProvenanceRef(source_event_id="ev-1"),
                created_at_ms=1000 + i * 10_000,
                source_event_ids=("ev-1",),
            )
            for i in range(5)
        ]
        for r in recs:
            store.add(r)
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        budget = ReplayBudget(
            budget_id="b-tight",
            max_sessions_per_cycle=2,
            max_sessions_per_24h_window=2,
            max_events_per_session=10,
            max_counterfactual_branches=1,
            max_session_duration_ms=1_000,
            replay_cooldown_ms=0,
            replay_fatigue_accum_rate=0.0,
            restore_continuity_required=True,
        )
        state = ReplayBudgetState(budget=budget)
        result = run_replay_financial_pipeline(
            candidates=recs,
            store=store,
            ledger=ledger,
            budget_state=state,
        )
        assert result.sessions_started == 2
        assert result.budget_exhausted_count == 3

    def test_no_action_intent_in_source(self) -> None:
        from sentinel.runtime import replay_financial_pipeline

        src = Path(replay_financial_pipeline.__file__).read_text(encoding="utf-8")
        assert "ApprovedActionIntent" not in src
        assert "evaluate_action" not in src

    def test_no_forbidden_imports_in_source(self) -> None:
        import re

        from sentinel.runtime import replay_financial_pipeline

        src = Path(replay_financial_pipeline.__file__).read_text(encoding="utf-8")
        bad = re.compile(
            r"^\s*(import|from)\s+("
            r"ccxt|web3|binance|btcturk|pybit|okx|gate_api|kucoin|huobi|bitfinex|kraken|"
            r"openai|anthropic|langchain|requests|httpx|aiohttp"
            r")\b",
            re.MULTILINE,
        )
        assert bad.findall(src) == []

    def test_no_forbidden_output_literals_in_source(self) -> None:
        from sentinel.runtime import replay_financial_pipeline

        src = Path(replay_financial_pipeline.__file__).read_text(encoding="utf-8")
        for literal in (
            '"BUY"',
            '"SELL"',
            '"EXECUTE_REAL"',
            '"ORDER_SUBMIT"',
            "'BUY'",
            "'SELL'",
            "'EXECUTE_REAL'",
            "'ORDER_SUBMIT'",
        ):
            assert literal not in src
