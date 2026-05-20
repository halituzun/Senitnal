"""V9 — Governance decision schema tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sentinel.governance.decision import (
    GovernanceDecisionKind,
    GovernanceReason,
    LiveGovernanceDecision,
)
from sentinel.runtime.output import SystemOutput


def _decision(**overrides: object) -> LiveGovernanceDecision:
    kwargs: dict[str, object] = {
        "decision_id": "dec-1",
        "request_id": "req-1",
        "decision": GovernanceDecisionKind.NO_ACTION,
        "system_output": SystemOutput.NO_ACTION,
        "reasons": (GovernanceReason.NO_BLOCK_REASON_FOUND,),
        "confidence": 0.7,
        "live_impact_possible": False,
        "live_impact_allowed": False,
        "created_at_ms": 1_000_000,
        "expires_at_ms": 2_000_000,
    }
    kwargs.update(overrides)
    return LiveGovernanceDecision(**kwargs)  # type: ignore[arg-type]


class TestDecisionSchema:
    def test_no_approve_decision_kind(self) -> None:
        # GovernanceDecisionKind enum has no approve / execute / order value.
        for v in ("approve", "execute", "order", "submit"):
            assert v not in {k.value for k in GovernanceDecisionKind}

    def test_valid_no_action_accepted(self) -> None:
        d = _decision()
        assert d.decision is GovernanceDecisionKind.NO_ACTION

    def test_creates_action_true_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _decision(creates_action=True)  # type: ignore[arg-type]

    def test_writes_external_true_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _decision(writes_external=True)  # type: ignore[arg-type]

    def test_approves_trade_true_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _decision(approves_trade=True)  # type: ignore[arg-type]

    def test_no_veto_is_approval_true_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _decision(no_veto_is_approval=True)  # type: ignore[arg-type]

    def test_monitor_is_approval_true_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _decision(monitor_is_approval=True)  # type: ignore[arg-type]

    def test_block_maps_to_block(self) -> None:
        d = _decision(
            decision=GovernanceDecisionKind.BLOCK_LIVE_CANDIDATE,
            system_output=SystemOutput.BLOCK,
            reasons=(GovernanceReason.HIGH_RISK,),
            live_impact_possible=True,
            live_impact_allowed=True,
        )
        assert d.system_output is SystemOutput.BLOCK

    def test_monitor_maps_to_monitor(self) -> None:
        d = _decision(
            decision=GovernanceDecisionKind.MONITOR_ONLY,
            system_output=SystemOutput.MONITOR,
            reasons=(GovernanceReason.REPLAY_UNCERTAIN,),
        )
        assert d.system_output is SystemOutput.MONITOR

    def test_wait_maps_to_wait(self) -> None:
        d = _decision(
            decision=GovernanceDecisionKind.WAIT_FOR_HUMAN,
            system_output=SystemOutput.WAIT,
            reasons=(GovernanceReason.MISSING_HUMAN_APPROVAL,),
        )
        assert d.system_output is SystemOutput.WAIT

    def test_need_recall_maps_to_need_recall(self) -> None:
        d = _decision(
            decision=GovernanceDecisionKind.NEED_RECALL,
            system_output=SystemOutput.NEED_RECALL,
            reasons=(GovernanceReason.MEMORY_CONFLICT,),
        )
        assert d.system_output is SystemOutput.NEED_RECALL

    def test_no_action_maps_to_no_action(self) -> None:
        d = _decision()
        assert d.system_output is SystemOutput.NO_ACTION

    def test_decision_output_mismatch_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _decision(
                decision=GovernanceDecisionKind.BLOCK_LIVE_CANDIDATE,
                system_output=SystemOutput.MONITOR,
                reasons=(GovernanceReason.HIGH_RISK,),
            )

    def test_live_impact_allowed_only_with_block(self) -> None:
        with pytest.raises(ValidationError):
            _decision(
                decision=GovernanceDecisionKind.MONITOR_ONLY,
                system_output=SystemOutput.MONITOR,
                reasons=(GovernanceReason.REPLAY_UNCERTAIN,),
                live_impact_allowed=True,
            )

    def test_empty_reasons_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _decision(reasons=())
