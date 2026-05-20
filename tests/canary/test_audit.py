"""V8 — Canary veto audit helper tests."""

from __future__ import annotations

import re
from pathlib import Path  # noqa: TC003

from sentinel.canary.audit import emit_canary_veto_decision_recorded
from sentinel.canary.evaluator import CanaryVetoContext, evaluate_canary_veto
from sentinel.observer.ledger import JsonlObserverLedger
from sentinel.observer.permanence import decide_permanence
from sentinel.policy.record_builder import build_deontic_policy_candidate_record
from sentinel.types.memory import MemoryRecordStatus
from sentinel.types.neural_seed import ProvenanceRef

from tests.canary._fixtures import make_bounds, make_candidate, make_request, make_window
from tests.policy._fixtures import make_artifact


def _ctx() -> CanaryVetoContext:
    rec = build_deontic_policy_candidate_record(
        artifact=make_artifact(),
        provenance=ProvenanceRef(source_event_id="ev-1"),
        created_at_ms=1_000_000,
        evidence_refs=("approval-1",),
    ).model_copy(update={"status": MemoryRecordStatus.ACTIVE})
    return CanaryVetoContext(
        bounds=make_bounds(),
        window_state=make_window(),
        now_ms=1_000_001_000,
        active_policy_record=rec,
    )


class TestCanaryAudit:
    def test_event_emitted(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        request = make_request()
        decision = evaluate_canary_veto(request=request, context=_ctx())
        ev = emit_canary_veto_decision_recorded(
            ledger=ledger,
            decision=decision,
            request=request,
            provenance=ProvenanceRef(source_event_id=request.candidate.candidate_id),
            now_ms=1_000_001_000,
        )
        assert ev.event_type == "CANARY_VETO_DECISION_RECORDED"

    def test_event_type_in_catalog(self) -> None:
        d = decide_permanence("CANARY_VETO_DECISION_RECORDED")
        assert d.permanence.value == "permanent"

    def test_hash_chain_verifies(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        request = make_request()
        decision = evaluate_canary_veto(request=request, context=_ctx())
        emit_canary_veto_decision_recorded(
            ledger=ledger,
            decision=decision,
            request=request,
            provenance=ProvenanceRef(source_event_id=request.candidate.candidate_id),
            now_ms=1_000_001_000,
        )
        emit_canary_veto_decision_recorded(
            ledger=ledger,
            decision=decision,
            request=request,
            provenance=ProvenanceRef(source_event_id=request.candidate.candidate_id),
            now_ms=1_000_002_000,
        )
        assert ledger.verify() is True

    def test_payload_no_raw_domain_labels(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        request = make_request()
        decision = evaluate_canary_veto(request=request, context=_ctx())
        ev = emit_canary_veto_decision_recorded(
            ledger=ledger,
            decision=decision,
            request=request,
            provenance=ProvenanceRef(source_event_id=request.candidate.candidate_id),
            now_ms=1_000_001_000,
        )
        for forbidden in ("symbol", "venue", "strategy_name", "order_side", "api_key"):
            assert forbidden not in ev.payload

    def test_payload_safety_flags_pinned_false(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        request = make_request()
        decision = evaluate_canary_veto(request=request, context=_ctx())
        ev = emit_canary_veto_decision_recorded(
            ledger=ledger,
            decision=decision,
            request=request,
            provenance=ProvenanceRef(source_event_id=request.candidate.candidate_id),
            now_ms=1_000_001_000,
        )
        assert ev.payload["creates_action"] is False
        assert ev.payload["writes_external"] is False
        assert ev.payload["approves_trade"] is False
        assert ev.payload["no_veto_is_approval"] is False

    def test_payload_reason_no_forbidden_literal(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        request = make_request(candidate=make_candidate(risk_score=0.95))
        decision = evaluate_canary_veto(request=request, context=_ctx())
        ev = emit_canary_veto_decision_recorded(
            ledger=ledger,
            decision=decision,
            request=request,
            provenance=ProvenanceRef(source_event_id=request.candidate.candidate_id),
            now_ms=1_000_001_000,
        )
        reason_text = ev.payload["reason"]
        assert isinstance(reason_text, str)
        for needle in ("buy", "sell", "execute", "order", "submit", "_real"):
            assert not re.search(needle, reason_text, re.IGNORECASE)
