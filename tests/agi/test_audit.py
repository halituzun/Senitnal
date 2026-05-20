"""V10 — AGI audit emitter tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sentinel.agi.audit import (
    emit_financial_agi_readiness_recorded,
    emit_financial_agi_v1_evaluated,
)
from sentinel.agi.orchestrator import evaluate_financial_agi_v1
from sentinel.agi.readiness_report import generate_financial_agi_readiness_report
from sentinel.observer.ledger import JsonlObserverLedger
from sentinel.types.neural_seed import ProvenanceRef

from tests.agi._fixtures import make_bundle

if TYPE_CHECKING:
    from pathlib import Path


class TestAuditEmitters:
    def test_emit_evaluated_returns_observer_event(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        bundle = make_bundle()
        output = evaluate_financial_agi_v1(bundle)
        event = emit_financial_agi_v1_evaluated(
            ledger=ledger,
            output_bundle=output,
            provenance=ProvenanceRef(source_event_id="audit-test-1"),
            now_ms=1_700_000_001_000,
        )
        assert event.event_type == "FINANCIAL_AGI_V1_EVALUATED"
        assert ledger.verify() is True

    def test_emit_readiness_returns_observer_event(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        bundle = make_bundle()
        output = evaluate_financial_agi_v1(bundle)
        report = generate_financial_agi_readiness_report(
            report_id="rpt-1",
            output_bundle=output,
        )
        event = emit_financial_agi_readiness_recorded(
            ledger=ledger,
            report=report,
            provenance=ProvenanceRef(source_event_id="audit-readiness-1"),
            now_ms=1_700_000_001_000,
        )
        assert event.event_type == "FINANCIAL_AGI_READINESS_RECORDED"
        assert ledger.verify() is True

    def test_both_events_chain_correctly(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        bundle = make_bundle()
        output = evaluate_financial_agi_v1(bundle)
        report = generate_financial_agi_readiness_report(
            report_id="rpt-chain",
            output_bundle=output,
        )
        emit_financial_agi_v1_evaluated(
            ledger=ledger,
            output_bundle=output,
            provenance=ProvenanceRef(source_event_id="chain-1"),
            now_ms=1_700_000_001_000,
        )
        emit_financial_agi_readiness_recorded(
            ledger=ledger,
            report=report,
            provenance=ProvenanceRef(source_event_id="chain-2"),
            now_ms=1_700_000_001_001,
        )
        assert ledger.verify() is True

    def test_safety_flags_in_payload(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        bundle = make_bundle()
        output = evaluate_financial_agi_v1(bundle)
        event = emit_financial_agi_v1_evaluated(
            ledger=ledger,
            output_bundle=output,
            provenance=ProvenanceRef(source_event_id="flags-test"),
            now_ms=1_700_000_001_000,
        )
        assert event.payload["creates_action"] is False
        assert event.payload["writes_external"] is False
        assert event.payload["approves_trade"] is False

    def test_no_forbidden_literals_in_reason(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        bundle = make_bundle()
        output = evaluate_financial_agi_v1(bundle)
        event = emit_financial_agi_v1_evaluated(
            ledger=ledger,
            output_bundle=output,
            provenance=ProvenanceRef(source_event_id="lit-test"),
            now_ms=1_700_000_001_000,
        )
        reason = event.payload["reason"].lower()
        for forbidden in ("buy", "sell", "execute_real", "order_submit"):
            assert forbidden not in reason

    def test_catalog_has_both_new_event_types(self) -> None:
        from sentinel.observer.catalog import CANONICAL_EVENT_CATALOG

        types = {e.event_type for e in CANONICAL_EVENT_CATALOG}
        assert "FINANCIAL_AGI_V1_EVALUATED" in types
        assert "FINANCIAL_AGI_READINESS_RECORDED" in types
