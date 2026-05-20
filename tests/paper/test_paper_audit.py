"""V7 — Paper audit helper tests."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003

from sentinel.observer.ledger import JsonlObserverLedger
from sentinel.paper.audit import emit_paper_copilot_evaluated
from sentinel.paper.decision import (
    PaperCoPilotResult,
    PaperDecision,
    PaperDecisionReason,
)
from sentinel.runtime.output import SystemOutput
from sentinel.types.neural_seed import ProvenanceRef

from tests.paper._fixtures import make_opportunity


def _result(output: SystemOutput = SystemOutput.MONITOR) -> PaperCoPilotResult:
    opp = make_opportunity()
    if output is SystemOutput.BLOCK:
        reasons: tuple[PaperDecisionReason, ...] = (PaperDecisionReason.HIGH_RISK,)
    elif output is SystemOutput.NEED_RECALL:
        reasons = (PaperDecisionReason.NEEDS_RECALL,)
    else:
        reasons = (PaperDecisionReason.MONITOR_ONLY,)
    decision = PaperDecision(
        decision_id="dec-1",
        opportunity_id=opp.opportunity_id,
        output=output,
        reasons=reasons,
        confidence=0.7,
        created_at_ms=1_000_000,
    )
    return PaperCoPilotResult(
        result_id="r-1",
        opportunity=opp,
        decision=decision,
        hash_chain_valid=True,
    )


class TestPaperAudit:
    def test_audit_emitted(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        ev = emit_paper_copilot_evaluated(
            ledger=ledger,
            result=_result(),
            provenance=ProvenanceRef(source_event_id="po-1"),
            now_ms=1_000_000,
        )
        assert ev.event_type == "LEDGER_STATE_CHANGED"

    def test_audit_payload_excludes_raw_labels(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        ev = emit_paper_copilot_evaluated(
            ledger=ledger,
            result=_result(),
            provenance=ProvenanceRef(source_event_id="po-1"),
            now_ms=1_000_000,
        )
        payload = ev.payload
        for forbidden in ("symbol", "venue", "strategy_name", "order_side", "api_key"):
            assert forbidden not in payload

    def test_audit_payload_safety_flags(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        ev = emit_paper_copilot_evaluated(
            ledger=ledger,
            result=_result(),
            provenance=ProvenanceRef(source_event_id="po-1"),
            now_ms=1_000_000,
        )
        payload = ev.payload
        assert payload["creates_action"] is False
        assert payload["writes_external"] is False
        assert payload["approved_for_live"] is False
        assert payload["shadow_only"] is True

    def test_hash_chain_valid(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        emit_paper_copilot_evaluated(
            ledger=ledger,
            result=_result(),
            provenance=ProvenanceRef(source_event_id="po-1"),
            now_ms=1_000_000,
        )
        emit_paper_copilot_evaluated(
            ledger=ledger,
            result=_result(SystemOutput.BLOCK),
            provenance=ProvenanceRef(source_event_id="po-1"),
            now_ms=1_000_001,
        )
        assert ledger.verify() is True
