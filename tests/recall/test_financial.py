"""V3 — Financial recall tests."""

from __future__ import annotations

import pytest
from sentinel.constitution.violations import InvariantViolation
from sentinel.memory.store import InMemoryExplicitMemoryStore
from sentinel.recall.financial import (
    FinancialRecallRequest,
    FinancialRecallScope,
    build_financial_recall_event,
    select_financial_recall_top_one,
)
from sentinel.recall.protocol import RecallTriggerSource
from sentinel.types.events import IngressEventType, RecallRecordStatus
from sentinel.types.memory import MemoryRecord, MemoryRecordStatus, SubjectClass
from sentinel.types.neural_seed import ProvenanceRef


def _record(
    *,
    record_id: str,
    subject_class: SubjectClass = SubjectClass.SOURCE_TRUST,
    status: MemoryRecordStatus = MemoryRecordStatus.CANDIDATE,
    confidence: float = 0.7,
    external_refs: int = 1,
) -> MemoryRecord:
    return MemoryRecord(
        record_id=record_id,
        subject_class=subject_class,
        payload={"confidence": confidence, "record_key": record_id},
        status=status,
        provenance=ProvenanceRef(source_event_id="src"),
        causal_refs=tuple(f"e-{i}" for i in range(external_refs)),
        external_corroboration_refs=tuple(f"e-{i}" for i in range(external_refs)),
        created_at_ms=0,
        last_status_change_ms=0,
    )


def _scope(
    *, subject_classes: tuple[SubjectClass, ...] = (SubjectClass.SOURCE_TRUST,)
) -> FinancialRecallScope:
    return FinancialRecallScope(
        subject_classes=subject_classes, max_records_considered=10, include_candidates=True
    )


def _request(scope: FinancialRecallScope | None = None) -> FinancialRecallRequest:
    return FinancialRecallRequest(
        request_id="req-1",
        source=RecallTriggerSource.CORE,
        scope=scope or _scope(),
        created_at_ms=0,
    )


class TestRequest:
    def test_non_core_source_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"must be RecallTriggerSource\.CORE"):
            FinancialRecallRequest(
                request_id="r",
                source=RecallTriggerSource.HUMAN_DIRECT,
                scope=_scope(),
                created_at_ms=0,
            )

    @pytest.mark.parametrize(
        "bad_source",
        [
            RecallTriggerSource.HUMAN_DIRECT,
            RecallTriggerSource.LLM,
            RecallTriggerSource.REPLAY,
            RecallTriggerSource.SUMMARIZER,
        ],
    )
    def test_all_non_core_sources_rejected(self, bad_source: RecallTriggerSource) -> None:
        with pytest.raises(ValueError):
            FinancialRecallRequest(
                request_id="r",
                source=bad_source,
                scope=_scope(),
                created_at_ms=0,
            )

    def test_empty_subject_classes_rejected(self) -> None:
        with pytest.raises(ValueError):
            FinancialRecallScope(subject_classes=(), max_records_considered=1)

    def test_zero_max_records_rejected(self) -> None:
        with pytest.raises(ValueError):
            FinancialRecallScope(
                subject_classes=(SubjectClass.SOURCE_TRUST,),
                max_records_considered=0,
            )


class TestSelectTopOne:
    def test_empty_store_returns_none(self) -> None:
        store = InMemoryExplicitMemoryStore()
        assert select_financial_recall_top_one(store=store, request=_request()) is None

    def test_returns_only_record(self) -> None:
        store = InMemoryExplicitMemoryStore()
        store.add(_record(record_id="r1"))
        sel = select_financial_recall_top_one(store=store, request=_request())
        assert sel is not None
        assert sel.record_id == "r1"

    def test_verified_beats_candidate_same_score(self) -> None:
        store = InMemoryExplicitMemoryStore()
        store.add(_record(record_id="cand", status=MemoryRecordStatus.CANDIDATE))
        store.add(_record(record_id="vrfd", status=MemoryRecordStatus.VERIFIED))
        sel = select_financial_recall_top_one(store=store, request=_request())
        assert sel is not None
        assert sel.record_id == "vrfd"

    def test_deterministic_tie_break_smaller_record_id(self) -> None:
        store = InMemoryExplicitMemoryStore()
        store.add(_record(record_id="z-rec"))
        store.add(_record(record_id="a-rec"))
        sel = select_financial_recall_top_one(store=store, request=_request())
        assert sel is not None
        assert sel.record_id == "a-rec"

    def test_rejected_excluded(self) -> None:
        store = InMemoryExplicitMemoryStore()
        store.add(_record(record_id="r", status=MemoryRecordStatus.REJECTED))
        assert select_financial_recall_top_one(store=store, request=_request()) is None

    def test_expired_excluded(self) -> None:
        store = InMemoryExplicitMemoryStore()
        store.add(_record(record_id="r", status=MemoryRecordStatus.EXPIRED))
        assert select_financial_recall_top_one(store=store, request=_request()) is None

    def test_quarantined_excluded(self) -> None:
        store = InMemoryExplicitMemoryStore()
        store.add(_record(record_id="r", status=MemoryRecordStatus.QUARANTINED))
        assert select_financial_recall_top_one(store=store, request=_request()) is None

    def test_structured_fact_candidate_ineligible(self) -> None:
        store = InMemoryExplicitMemoryStore()
        store.add(
            _record(
                record_id="r",
                subject_class=SubjectClass.STRUCTURED_FACT,
                status=MemoryRecordStatus.CANDIDATE,
            )
        )
        request = _request(scope=_scope(subject_classes=(SubjectClass.STRUCTURED_FACT,)))
        assert select_financial_recall_top_one(store=store, request=request) is None

    def test_source_trust_candidate_eligible(self) -> None:
        store = InMemoryExplicitMemoryStore()
        store.add(_record(record_id="r", subject_class=SubjectClass.SOURCE_TRUST))
        sel = select_financial_recall_top_one(store=store, request=_request())
        assert sel is not None

    def test_procedural_candidate_eligible(self) -> None:
        store = InMemoryExplicitMemoryStore()
        store.add(_record(record_id="r", subject_class=SubjectClass.PROCEDURAL))
        request = _request(scope=_scope(subject_classes=(SubjectClass.PROCEDURAL,)))
        sel = select_financial_recall_top_one(store=store, request=request)
        assert sel is not None


class TestBuildFinancialRecallEvent:
    def test_verified_record_builds(self) -> None:
        rec = _record(
            record_id="r",
            subject_class=SubjectClass.STRUCTURED_FACT,
            status=MemoryRecordStatus.VERIFIED,
            confidence=0.9,
        )
        ev = build_financial_recall_event(record=rec, request_id="req-1", now_ms=10)
        assert ev.event_type is IngressEventType.RECALL
        assert ev.source_record_id == "r"
        assert ev.record_status is RecallRecordStatus.VERIFIED
        assert ev.subject_class is SubjectClass.STRUCTURED_FACT
        assert ev.confidence == pytest.approx(0.9)
        assert ev.age_ms == 10

    def test_active_record_builds(self) -> None:
        rec = _record(record_id="r", status=MemoryRecordStatus.ACTIVE)
        ev = build_financial_recall_event(record=rec, request_id="req-1", now_ms=0)
        assert ev.record_status is RecallRecordStatus.ACTIVE

    def test_eligible_candidate_builds_low_confidence(self) -> None:
        rec = _record(
            record_id="r",
            subject_class=SubjectClass.SOURCE_TRUST,
            status=MemoryRecordStatus.CANDIDATE,
            confidence=0.9,
        )
        ev = build_financial_recall_event(record=rec, request_id="req-1", now_ms=0)
        # candidate confidence capped at 0.5
        assert ev.confidence <= 0.5

    def test_ineligible_candidate_rejected(self) -> None:
        rec = _record(
            record_id="r",
            subject_class=SubjectClass.STRUCTURED_FACT,
            status=MemoryRecordStatus.CANDIDATE,
        )
        with pytest.raises(InvariantViolation):
            build_financial_recall_event(record=rec, request_id="req-1", now_ms=0)

    @pytest.mark.parametrize(
        "bad_status",
        [
            MemoryRecordStatus.REJECTED,
            MemoryRecordStatus.EXPIRED,
            MemoryRecordStatus.QUARANTINED,
        ],
    )
    def test_terminal_states_rejected(self, bad_status: MemoryRecordStatus) -> None:
        rec = _record(record_id="r", status=bad_status)
        with pytest.raises(ValueError, match="cannot build RecallEvent"):
            build_financial_recall_event(record=rec, request_id="req-1", now_ms=0)

    def test_no_raw_symbol_fields(self) -> None:
        rec = _record(record_id="r", status=MemoryRecordStatus.VERIFIED)
        ev = build_financial_recall_event(record=rec, request_id="req-1", now_ms=0)
        dumped = ev.model_dump()
        forbidden = {
            "symbol",
            "venue",
            "source_system",
            "raw_ref",
            "best_bid",
            "best_ask",
            "mid_price",
            "side",
            "order_side",
        }
        assert forbidden & set(dumped.keys()) == set()

    def test_ttl_required(self) -> None:
        rec = _record(record_id="r", status=MemoryRecordStatus.VERIFIED)
        with pytest.raises(ValueError, match="ttl_ms must be > 0"):
            build_financial_recall_event(record=rec, request_id="req-1", now_ms=0, ttl_ms=0)

    def test_confidence_bounded(self) -> None:
        rec_ok = _record(
            record_id="r2",
            subject_class=SubjectClass.SOURCE_TRUST,
            status=MemoryRecordStatus.CANDIDATE,
            confidence=0.9,
        )
        ev = build_financial_recall_event(record=rec_ok, request_id="req-1", now_ms=0)
        assert 0.0 <= ev.confidence <= 1.0
