"""V9 — Governance audit tests."""

from __future__ import annotations

import re
from pathlib import Path  # noqa: TC003

from sentinel.governance.audit import emit_live_governance_decision_recorded
from sentinel.governance.guard import GovernanceGuardContext, evaluate_governance_guard
from sentinel.observer.ledger import JsonlObserverLedger
from sentinel.observer.permanence import decide_permanence
from sentinel.policy.record_builder import build_deontic_policy_candidate_record
from sentinel.types.memory import MemoryRecordStatus
from sentinel.types.neural_seed import ProvenanceRef

from tests.governance._fixtures import make_approval, make_request
from tests.policy._fixtures import make_artifact


def _ctx() -> GovernanceGuardContext:
    rec = build_deontic_policy_candidate_record(
        artifact=make_artifact(effective_at_ms=1_000_000, created_at_ms=1_000_000),
        provenance=ProvenanceRef(source_event_id="ev-1"),
        created_at_ms=1_000_000,
        evidence_refs=("approval",),
    ).model_copy(update={"status": MemoryRecordStatus.ACTIVE})
    return GovernanceGuardContext(
        now_ms=1_500_000,
        hash_chain_valid=True,
        active_policy_record=rec,
        human_approval=make_approval(),
    )


class TestGovernanceAudit:
    def test_event_emitted(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        request = make_request()
        decision = evaluate_governance_guard(request=request, context=_ctx())
        ev = emit_live_governance_decision_recorded(
            ledger=ledger,
            decision=decision,
            request=request,
            provenance=ProvenanceRef(source_event_id=request.request_id),
            now_ms=1_500_000,
        )
        assert ev.event_type == "LIVE_GOVERNANCE_DECISION_RECORDED"

    def test_event_type_in_catalog(self) -> None:
        d = decide_permanence("LIVE_GOVERNANCE_DECISION_RECORDED")
        assert d.permanence.value == "permanent"

    def test_hash_chain_verifies(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        request = make_request()
        decision = evaluate_governance_guard(request=request, context=_ctx())
        emit_live_governance_decision_recorded(
            ledger=ledger,
            decision=decision,
            request=request,
            provenance=ProvenanceRef(source_event_id=request.request_id),
            now_ms=1_500_000,
        )
        emit_live_governance_decision_recorded(
            ledger=ledger,
            decision=decision,
            request=request,
            provenance=ProvenanceRef(source_event_id=request.request_id),
            now_ms=1_500_001,
        )
        assert ledger.verify() is True

    def test_payload_no_raw_domain_labels(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        request = make_request()
        decision = evaluate_governance_guard(request=request, context=_ctx())
        ev = emit_live_governance_decision_recorded(
            ledger=ledger,
            decision=decision,
            request=request,
            provenance=ProvenanceRef(source_event_id=request.request_id),
            now_ms=1_500_000,
        )
        for forbidden in ("symbol", "venue", "strategy_name", "order_side", "api_key"):
            assert forbidden not in ev.payload

    def test_payload_safety_flags(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        request = make_request()
        decision = evaluate_governance_guard(request=request, context=_ctx())
        ev = emit_live_governance_decision_recorded(
            ledger=ledger,
            decision=decision,
            request=request,
            provenance=ProvenanceRef(source_event_id=request.request_id),
            now_ms=1_500_000,
        )
        for flag in (
            "creates_action",
            "writes_external",
            "approves_trade",
            "no_veto_is_approval",
            "monitor_is_approval",
        ):
            assert ev.payload[flag] is False

    def test_reason_no_forbidden_literal(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        request = make_request(risk_score=0.95)
        decision = evaluate_governance_guard(request=request, context=_ctx())
        ev = emit_live_governance_decision_recorded(
            ledger=ledger,
            decision=decision,
            request=request,
            provenance=ProvenanceRef(source_event_id=request.request_id),
            now_ms=1_500_000,
        )
        reason_text = ev.payload["reason"]
        assert isinstance(reason_text, str)
        for needle in ("buy", "sell", "execute", "order", "submit", "_real"):
            assert not re.search(needle, reason_text, re.IGNORECASE)
