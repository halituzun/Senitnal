"""V3 — builder + store tests."""

from __future__ import annotations

import json

import pytest
from sentinel.memory.builder import build_candidate_financial_memory_record
from sentinel.memory.financial import (
    ExecutionQualityObservationPayload,
    LatencyPatternPayload,
    MarketRegimeObservationPayload,
)
from sentinel.memory.store import InMemoryExplicitMemoryStore
from sentinel.types.memory import MemoryRecord, MemoryRecordStatus, SubjectClass
from sentinel.types.neural_seed import ProvenanceRef


def _latency_payload(record_key: str = "lat-001") -> LatencyPatternPayload:
    return LatencyPatternPayload(
        record_key=record_key,
        source_adapter_id="synthetic-market-adapter",
        venue_hash="sha256:venue",
        avg_latency_ms=10.0,
        p95_latency_ms=50.0,
        max_latency_ms=200.0,
        stale_ratio=0.05,
        sample_count=100,
        confidence=0.9,
        source_event_ids=("ev-1",),
    )


def _exec_quality_payload(record_key: str = "exq-001") -> ExecutionQualityObservationPayload:
    return ExecutionQualityObservationPayload(
        record_key=record_key,
        simulation_id="sim-001",
        expected_fill_quality=0.8,
        estimated_slippage_pct=0.05,
        estimated_fee_pct=0.02,
        estimated_net_edge_pct=0.1,
        sample_count=50,
        confidence=0.75,
        source_event_ids=("ev-1",),
    )


def _regime_payload(record_key: str = "reg-001") -> MarketRegimeObservationPayload:
    return MarketRegimeObservationPayload(
        record_key=record_key,
        symbol_hash="sha256:sym",
        venue_hash="sha256:venue",
        regime_label="calm",
        observed_window_ms=60_000,
        volatility_score=0.2,
        spread_score=0.1,
        liquidity_score=0.8,
        staleness_score=0.1,
        confidence=0.8,
        observation_count=12,
        source_event_ids=("ev-1",),
    )


class TestBuilder:
    def test_builds_candidate_status(self) -> None:
        rec = build_candidate_financial_memory_record(
            payload=_latency_payload(),
            provenance=ProvenanceRef(source_event_id="ev-1"),
            created_at_ms=1000,
            source_event_ids=("ev-1",),
        )
        assert rec.status is MemoryRecordStatus.CANDIDATE
        assert rec.subject_class is SubjectClass.SOURCE_TRUST

    def test_causal_and_external_refs_populated(self) -> None:
        rec = build_candidate_financial_memory_record(
            payload=_latency_payload(),
            provenance=ProvenanceRef(source_event_id="ev-1"),
            created_at_ms=1000,
            source_event_ids=("ev-1", "ev-2"),
        )
        assert rec.causal_refs == ("ev-1", "ev-2")
        assert rec.external_corroboration_refs == ("ev-1", "ev-2")
        assert rec.internal_only_refs == ()

    def test_payload_is_json_compatible(self) -> None:
        rec = build_candidate_financial_memory_record(
            payload=_latency_payload(),
            provenance=ProvenanceRef(source_event_id="ev-1"),
            created_at_ms=1000,
            source_event_ids=("ev-1",),
        )
        encoded = json.dumps(rec.payload)
        roundtrip = json.loads(encoded)
        assert roundtrip["record_key"] == "lat-001"
        assert "symbol" not in roundtrip
        assert "venue" not in roundtrip

    def test_no_verified_path(self) -> None:
        # API has no parameter to request VERIFIED. The function ALWAYS
        # builds CANDIDATE. Build a wide variety and assert.
        for payload in (_latency_payload(), _exec_quality_payload(), _regime_payload()):
            rec = build_candidate_financial_memory_record(
                payload=payload,
                provenance=ProvenanceRef(source_event_id="ev-1"),
                created_at_ms=0,
                source_event_ids=("ev-1",),
            )
            assert rec.status is MemoryRecordStatus.CANDIDATE

    def test_empty_source_event_ids_rejected(self) -> None:
        with pytest.raises(ValueError):
            build_candidate_financial_memory_record(
                payload=_latency_payload(),
                provenance=ProvenanceRef(source_event_id="ev-1"),
                created_at_ms=0,
                source_event_ids=(),
            )


class TestStore:
    def _record(
        self,
        *,
        record_id: str,
        subject_class: SubjectClass,
        status: MemoryRecordStatus,
    ) -> MemoryRecord:
        return MemoryRecord(
            record_id=record_id,
            subject_class=subject_class,
            payload={"k": "v"},
            status=status,
            provenance=ProvenanceRef(source_event_id="src-1"),
            created_at_ms=0,
            last_status_change_ms=0,
        )

    def test_add_and_get(self) -> None:
        s = InMemoryExplicitMemoryStore()
        r = self._record(
            record_id="a",
            subject_class=SubjectClass.SOURCE_TRUST,
            status=MemoryRecordStatus.CANDIDATE,
        )
        s.add(r)
        assert s.get("a") is r
        assert s.get("missing") is None

    def test_duplicate_rejected(self) -> None:
        s = InMemoryExplicitMemoryStore()
        r = self._record(
            record_id="a",
            subject_class=SubjectClass.SOURCE_TRUST,
            status=MemoryRecordStatus.CANDIDATE,
        )
        s.add(r)
        with pytest.raises(ValueError, match="duplicate"):
            s.add(r)

    def test_list_and_query_by_subject_class(self) -> None:
        s = InMemoryExplicitMemoryStore()
        s.add(
            self._record(
                record_id="a",
                subject_class=SubjectClass.SOURCE_TRUST,
                status=MemoryRecordStatus.CANDIDATE,
            )
        )
        s.add(
            self._record(
                record_id="b",
                subject_class=SubjectClass.PROCEDURAL,
                status=MemoryRecordStatus.CANDIDATE,
            )
        )
        assert len(s.list_all()) == 2
        assert {r.record_id for r in s.query_by_subject_class(SubjectClass.SOURCE_TRUST)} == {"a"}

    def test_rejected_quarantined_expired_excluded_from_recallable(self) -> None:
        s = InMemoryExplicitMemoryStore()
        for status in (
            MemoryRecordStatus.REJECTED,
            MemoryRecordStatus.QUARANTINED,
            MemoryRecordStatus.EXPIRED,
        ):
            s.add(
                self._record(
                    record_id=f"rec-{status.value}",
                    subject_class=SubjectClass.SOURCE_TRUST,
                    status=status,
                )
            )
        assert s.query_recallable() == ()

    def test_source_trust_candidate_included(self) -> None:
        s = InMemoryExplicitMemoryStore()
        s.add(
            self._record(
                record_id="r",
                subject_class=SubjectClass.SOURCE_TRUST,
                status=MemoryRecordStatus.CANDIDATE,
            )
        )
        assert len(s.query_recallable()) == 1

    def test_procedural_candidate_included(self) -> None:
        s = InMemoryExplicitMemoryStore()
        s.add(
            self._record(
                record_id="r",
                subject_class=SubjectClass.PROCEDURAL,
                status=MemoryRecordStatus.CANDIDATE,
            )
        )
        assert len(s.query_recallable()) == 1

    def test_structured_fact_candidate_excluded(self) -> None:
        s = InMemoryExplicitMemoryStore()
        s.add(
            self._record(
                record_id="r",
                subject_class=SubjectClass.STRUCTURED_FACT,
                status=MemoryRecordStatus.CANDIDATE,
            )
        )
        assert s.query_recallable() == ()

    def test_narrative_claim_candidate_excluded(self) -> None:
        s = InMemoryExplicitMemoryStore()
        s.add(
            self._record(
                record_id="r",
                subject_class=SubjectClass.NARRATIVE_CLAIM,
                status=MemoryRecordStatus.CANDIDATE,
            )
        )
        assert s.query_recallable() == ()

    def test_verified_included(self) -> None:
        s = InMemoryExplicitMemoryStore()
        s.add(
            self._record(
                record_id="r",
                subject_class=SubjectClass.STRUCTURED_FACT,
                status=MemoryRecordStatus.VERIFIED,
            )
        )
        assert len(s.query_recallable()) == 1

    def test_active_included(self) -> None:
        s = InMemoryExplicitMemoryStore()
        s.add(
            self._record(
                record_id="r",
                subject_class=SubjectClass.PROCEDURAL,
                status=MemoryRecordStatus.ACTIVE,
            )
        )
        assert len(s.query_recallable()) == 1

    def test_superseded_excluded_by_default(self) -> None:
        s = InMemoryExplicitMemoryStore()
        s.add(
            self._record(
                record_id="r",
                subject_class=SubjectClass.PROCEDURAL,
                status=MemoryRecordStatus.SUPERSEDED,
            )
        )
        assert s.query_recallable() == ()
        assert len(s.query_recallable(include_superseded=True)) == 1

    def test_include_candidates_false(self) -> None:
        s = InMemoryExplicitMemoryStore()
        s.add(
            self._record(
                record_id="r",
                subject_class=SubjectClass.SOURCE_TRUST,
                status=MemoryRecordStatus.CANDIDATE,
            )
        )
        assert s.query_recallable(include_candidates=False) == ()
