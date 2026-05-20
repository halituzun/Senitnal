"""Tests for the deontic ledger audit emission."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003 (fixture annotation)

import pytest
from sentinel.gates.deontic import (
    ApprovedActionIntent,
    BlockClass,
    DeonticDecision,
    evaluate_action_with_audit,
)
from sentinel.observer.ledger import JsonlObserverLedger


def _intent(intent_id: str = "i-1", intent_type: str = "observe_only") -> ApprovedActionIntent:
    return ApprovedActionIntent(
        intent_id=intent_id,
        intent_type=intent_type,
        rationale="audit test",
        requested_at_ms=42,
    )


@pytest.fixture
def ledger_path(tmp_path: Path) -> Path:
    return tmp_path / "ledger.jsonl"


@pytest.fixture
def ledger(ledger_path: Path) -> JsonlObserverLedger:
    return JsonlObserverLedger(ledger_path)


class TestAuditEmission:
    def test_block_emits_deontic_blocked(self, ledger: JsonlObserverLedger) -> None:
        outcome = evaluate_action_with_audit(ledger, _intent(), now_ms=1)
        assert outcome.decision is DeonticDecision.BLOCK
        events = ledger.read_all()
        assert len(events) == 1
        assert events[0].event_type == "DEONTIC_BLOCKED"
        assert events[0].event_family.value == "deontic"
        assert events[0].payload["intent_id"] == "i-1"
        assert events[0].payload["block_class"] == BlockClass.CONSTITUTIONAL.value
        assert events[0].payload["triggered_declarative_code"] == (
            "MVP_EXECUTE_DISABLED_BLOCKS_ALL_ACTION"
        )

    def test_chain_continues_after_audit(self, ledger: JsonlObserverLedger) -> None:
        evaluate_action_with_audit(ledger, _intent(intent_id="a"), now_ms=1)
        evaluate_action_with_audit(ledger, _intent(intent_id="b"), now_ms=2)
        events = ledger.read_all()
        assert len(events) == 2
        assert events[1].previous_event_hash == events[0].event_hash
        assert ledger.verify() is True

    def test_block_class_propagated(self, ledger: JsonlObserverLedger) -> None:
        outcome = evaluate_action_with_audit(ledger, _intent(), now_ms=1)
        events = ledger.read_all()
        assert outcome.block_class is not None
        assert events[0].payload["block_class"] == outcome.block_class.value
