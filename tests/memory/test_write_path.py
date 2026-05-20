"""V3 — Memory write path (MWG wrapper) tests."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003 (pytest tmp_path annotation)

from sentinel.gates.memory_write import EvidenceAxis, MemoryWriteResolution
from sentinel.memory.financial import (
    ExecutionQualityObservationPayload,
    LatencyPatternPayload,
    MarketRegimeObservationPayload,
)
from sentinel.memory.store import InMemoryExplicitMemoryStore
from sentinel.memory.write_path import submit_financial_memory_candidate
from sentinel.observer.ledger import JsonlObserverLedger
from sentinel.types.memory import MemoryRecordStatus
from sentinel.types.neural_seed import ProvenanceRef


def _latency_payload() -> LatencyPatternPayload:
    return LatencyPatternPayload(
        record_key="lat-001",
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


def _exec_quality_payload() -> ExecutionQualityObservationPayload:
    return ExecutionQualityObservationPayload(
        record_key="exq-001",
        simulation_id="sim-001",
        expected_fill_quality=0.8,
        estimated_slippage_pct=0.05,
        estimated_fee_pct=0.02,
        estimated_net_edge_pct=0.1,
        sample_count=50,
        confidence=0.75,
        source_event_ids=("ev-1",),
    )


def _regime_payload() -> MarketRegimeObservationPayload:
    return MarketRegimeObservationPayload(
        record_key="reg-001",
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


class TestSubmitFinancialMemoryCandidate:
    def test_source_trust_accepted(self, tmp_path: Path) -> None:
        store = InMemoryExplicitMemoryStore()
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        result = submit_financial_memory_candidate(
            store=store,
            ledger=ledger,
            payload=_latency_payload(),
            provenance=ProvenanceRef(source_event_id="ev-1"),
            created_at_ms=0,
            source_event_ids=("ev-1",),
            evidence_axis=EvidenceAxis.DIRECT_OBSERVATION,
        )
        assert result.stored is True
        assert result.outcome.resolution is MemoryWriteResolution.ACCEPTED_CANDIDATE
        assert result.record.status is MemoryRecordStatus.CANDIDATE
        assert len(store) == 1

    def test_procedural_accepted(self, tmp_path: Path) -> None:
        store = InMemoryExplicitMemoryStore()
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        result = submit_financial_memory_candidate(
            store=store,
            ledger=ledger,
            payload=_exec_quality_payload(),
            provenance=ProvenanceRef(source_event_id="ev-1"),
            created_at_ms=0,
            source_event_ids=("ev-1",),
            evidence_axis=EvidenceAxis.INTERNAL_INFERENCE,
        )
        assert result.stored is True
        assert result.outcome.resolution is MemoryWriteResolution.ACCEPTED_CANDIDATE

    def test_structured_fact_rejected_not_stored(self, tmp_path: Path) -> None:
        store = InMemoryExplicitMemoryStore()
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        result = submit_financial_memory_candidate(
            store=store,
            ledger=ledger,
            payload=_regime_payload(),
            provenance=ProvenanceRef(source_event_id="ev-1"),
            created_at_ms=0,
            source_event_ids=("ev-1",),
            evidence_axis=EvidenceAxis.DIRECT_OBSERVATION,
        )
        # MarketRegime maps to STRUCTURED_FACT, not in MWG whitelist.
        assert result.stored is False
        assert result.outcome.resolution is MemoryWriteResolution.REJECTED
        assert len(store) == 0

    def test_audit_event_emitted_even_on_rejection(self, tmp_path: Path) -> None:
        store = InMemoryExplicitMemoryStore()
        ledger_path = tmp_path / "l.jsonl"
        ledger = JsonlObserverLedger(ledger_path)
        submit_financial_memory_candidate(
            store=store,
            ledger=ledger,
            payload=_regime_payload(),
            provenance=ProvenanceRef(source_event_id="ev-1"),
            created_at_ms=0,
            source_event_ids=("ev-1",),
            evidence_axis=EvidenceAxis.DIRECT_OBSERVATION,
        )
        # The MWG emits a MEMORY_RECORD_STATUS_CHANGED audit event;
        # the ledger file should now contain at least one line.
        content = ledger_path.read_text(encoding="utf-8")
        assert "MEMORY_RECORD_STATUS_CHANGED" in content
        assert '"new_status":"rejected"' in content

    def test_no_verified_path_in_v3(self, tmp_path: Path) -> None:
        # The wrapper always requests CANDIDATE. ACCEPTED_VERIFIED
        # is never returned in MVP.
        store = InMemoryExplicitMemoryStore()
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        result = submit_financial_memory_candidate(
            store=store,
            ledger=ledger,
            payload=_latency_payload(),
            provenance=ProvenanceRef(source_event_id="ev-1"),
            created_at_ms=0,
            source_event_ids=("ev-1",),
            evidence_axis=EvidenceAxis.DIRECT_OBSERVATION,
        )
        assert result.outcome.resolution is not MemoryWriteResolution.ACCEPTED_VERIFIED
        assert result.record.status is MemoryRecordStatus.CANDIDATE

    def test_invalid_evidence_axis_pair_rejected(self, tmp_path: Path) -> None:
        # (PROCEDURAL, DIRECT_OBSERVATION) is NOT in the MWG whitelist.
        store = InMemoryExplicitMemoryStore()
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        result = submit_financial_memory_candidate(
            store=store,
            ledger=ledger,
            payload=_exec_quality_payload(),
            provenance=ProvenanceRef(source_event_id="ev-1"),
            created_at_ms=0,
            source_event_ids=("ev-1",),
            evidence_axis=EvidenceAxis.DIRECT_OBSERVATION,
        )
        assert result.stored is False
        assert result.outcome.resolution is MemoryWriteResolution.REJECTED
