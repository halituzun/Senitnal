"""V6 — Policy audit helper tests."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003

import pytest
from sentinel.observer.ledger import JsonlObserverLedger
from sentinel.policy.audit import (
    emit_deontic_policy_status_changed,
    emit_policy_emergency_revert,
)
from sentinel.runtime.output import ForbiddenOutputViolation


class TestPolicyAudit:
    def test_status_changed_event_emitted(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        ev = emit_deontic_policy_status_changed(
            ledger=ledger,
            policy_record_id="policy-art-1",
            policy_id="policy-1",
            old_status="verified",
            new_status="active",
            trigger="activation",
            approved_by="operator",
            memory_write_gate_pass_ref="mwg-1",
            previous_active_policy_ref=None,
            evidence_refs=("approval-1",),
            reason="policy activated under approval",
            now_ms=1_000_000,
        )
        assert ev.event_type == "MEMORY_RECORD_STATUS_CHANGED"

    def test_forbidden_reason_rejected(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        with pytest.raises(ForbiddenOutputViolation):
            emit_deontic_policy_status_changed(
                ledger=ledger,
                policy_record_id="policy-1",
                policy_id="policy-1",
                old_status="verified",
                new_status="active",
                trigger="activation",
                approved_by=None,
                memory_write_gate_pass_ref=None,
                previous_active_policy_ref=None,
                evidence_refs=(),
                reason="activated to submit live orders",
                now_ms=0,
            )

    def test_emergency_revert_audit_emitted(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        ev = emit_policy_emergency_revert(
            ledger=ledger,
            from_policy_record_id="policy-new",
            to_previous_verified_policy_record_id="policy-old",
            policy_id="p",
            reason="rolled back to previous verified policy",
            now_ms=2_000_000,
        )
        assert ev.event_type == "MEMORY_RECORD_STATUS_CHANGED"
        payload = ev.payload
        assert payload["trigger"] == "emergency_revert"

    def test_hash_chain_valid_after_audit(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        emit_deontic_policy_status_changed(
            ledger=ledger,
            policy_record_id="p",
            policy_id="p",
            old_status="candidate",
            new_status="verified",
            trigger="manual_promotion",
            approved_by="operator",
            memory_write_gate_pass_ref="mwg",
            previous_active_policy_ref=None,
            evidence_refs=(),
            reason="policy promoted to verified",
            now_ms=1_000_000,
        )
        assert ledger.verify() is True
