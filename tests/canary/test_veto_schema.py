"""V8 — Canary veto schema tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sentinel.canary.candidate import CanaryEnvironment
from sentinel.canary.veto import (
    CanaryVetoDecision,
    VetoDecisionKind,
    VetoReason,
    VetoRequest,
)
from sentinel.runtime.output import SystemOutput
from sentinel.types.neural_seed import ProvenanceRef

from tests.canary._fixtures import make_candidate


def _decision(
    *,
    decision: VetoDecisionKind = VetoDecisionKind.NO_VETO,
    output: SystemOutput = SystemOutput.NO_ACTION,
    reasons: tuple[VetoReason, ...] = (VetoReason.NO_VETO_REASON_FOUND,),
    can_affect_canary: bool = False,
    shadow_only: bool = True,
    environment: CanaryEnvironment = CanaryEnvironment.MICRO_LIVE_CANARY,
    **overrides: object,
) -> CanaryVetoDecision:
    kwargs: dict[str, object] = {
        "decision_id": "dec-1",
        "request_id": "req-1",
        "candidate_id": "cand-1",
        "decision": decision,
        "system_output": output,
        "reasons": reasons,
        "confidence": 0.7,
        "environment": environment,
        "shadow_only": shadow_only,
        "can_affect_canary": can_affect_canary,
        "created_at_ms": 1_000_000,
        "expires_at_ms": 1_005_000,
    }
    kwargs.update(overrides)
    return CanaryVetoDecision(**kwargs)  # type: ignore[arg-type]


class TestVetoRequest:
    def test_valid_request_accepted(self) -> None:
        req = VetoRequest(
            request_id="req-1",
            candidate=make_candidate(),
            requested_at_ms=1_000_000,
            deadline_ms=1_005_000,
            provenance=ProvenanceRef(source_event_id="cand-1"),
        )
        assert req.candidate.candidate_id == "cand-1"

    def test_deadline_before_request_rejected(self) -> None:
        with pytest.raises(ValidationError):
            VetoRequest(
                request_id="req-1",
                candidate=make_candidate(),
                requested_at_ms=2_000_000,
                deadline_ms=1_000_000,
                provenance=ProvenanceRef(source_event_id="cand-1"),
            )


class TestVetoDecisionSchema:
    def test_valid_no_veto_accepted(self) -> None:
        d = _decision()
        assert d.decision is VetoDecisionKind.NO_VETO

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

    def test_veto_must_be_block(self) -> None:
        with pytest.raises(ValidationError):
            _decision(
                decision=VetoDecisionKind.VETO,
                output=SystemOutput.MONITOR,
                reasons=(VetoReason.HIGH_RISK,),
            )

    def test_veto_block_accepted(self) -> None:
        d = _decision(
            decision=VetoDecisionKind.VETO,
            output=SystemOutput.BLOCK,
            reasons=(VetoReason.HIGH_RISK,),
            can_affect_canary=True,
            shadow_only=False,
        )
        assert d.decision is VetoDecisionKind.VETO
        assert d.can_affect_canary is True

    def test_veto_can_affect_canary_only_in_micro_live(self) -> None:
        with pytest.raises(ValidationError):
            _decision(
                decision=VetoDecisionKind.VETO,
                output=SystemOutput.BLOCK,
                reasons=(VetoReason.HIGH_RISK,),
                can_affect_canary=True,
                environment=CanaryEnvironment.SHADOW,
            )

    def test_monitor_only_maps_to_monitor(self) -> None:
        d = _decision(
            decision=VetoDecisionKind.MONITOR_ONLY,
            output=SystemOutput.MONITOR,
            reasons=(VetoReason.REPLAY_UNCERTAIN,),
        )
        assert d.system_output is SystemOutput.MONITOR

    def test_monitor_only_cannot_affect_canary(self) -> None:
        with pytest.raises(ValidationError):
            _decision(
                decision=VetoDecisionKind.MONITOR_ONLY,
                output=SystemOutput.MONITOR,
                reasons=(VetoReason.REPLAY_UNCERTAIN,),
                can_affect_canary=True,
            )

    def test_no_veto_maps_to_no_action_or_monitor(self) -> None:
        d = _decision(
            decision=VetoDecisionKind.NO_VETO,
            output=SystemOutput.NO_ACTION,
            reasons=(VetoReason.NO_VETO_REASON_FOUND,),
        )
        assert d.system_output is SystemOutput.NO_ACTION

        d2 = _decision(
            decision=VetoDecisionKind.NO_VETO,
            output=SystemOutput.MONITOR,
            reasons=(VetoReason.NO_VETO_REASON_FOUND,),
        )
        assert d2.system_output is SystemOutput.MONITOR

    def test_no_veto_cannot_affect_canary(self) -> None:
        with pytest.raises(ValidationError):
            _decision(
                decision=VetoDecisionKind.NO_VETO,
                output=SystemOutput.NO_ACTION,
                reasons=(VetoReason.NO_VETO_REASON_FOUND,),
                can_affect_canary=True,
            )

    def test_no_veto_must_remain_shadow_only(self) -> None:
        with pytest.raises(ValidationError):
            _decision(
                decision=VetoDecisionKind.NO_VETO,
                output=SystemOutput.NO_ACTION,
                reasons=(VetoReason.NO_VETO_REASON_FOUND,),
                shadow_only=False,
            )

    def test_veto_empty_reasons_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _decision(
                decision=VetoDecisionKind.VETO,
                output=SystemOutput.BLOCK,
                reasons=(),
                can_affect_canary=True,
                shadow_only=False,
            )
