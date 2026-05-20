"""V7 — Paper decision + result schema tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sentinel.paper.decision import (
    PaperCoPilotResult,
    PaperDecision,
    PaperDecisionReason,
)
from sentinel.runtime.output import SystemOutput

from tests.paper._fixtures import make_opportunity


def _decision(
    *,
    output: SystemOutput = SystemOutput.MONITOR,
    reasons: tuple[PaperDecisionReason, ...] = (PaperDecisionReason.MONITOR_ONLY,),
) -> PaperDecision:
    return PaperDecision(
        decision_id="dec-1",
        opportunity_id="po-1",
        output=output,
        reasons=reasons,
        confidence=0.7,
        created_at_ms=1_000_000,
    )


class TestPaperDecision:
    def test_valid_decision_accepted(self) -> None:
        d = _decision()
        assert d.output is SystemOutput.MONITOR

    def test_shadow_only_false_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PaperDecision(
                decision_id="x",
                opportunity_id="po-1",
                output=SystemOutput.MONITOR,
                reasons=(PaperDecisionReason.MONITOR_ONLY,),
                confidence=0.7,
                created_at_ms=0,
                shadow_only=False,  # type: ignore[arg-type]
            )

    def test_creates_action_true_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PaperDecision(
                decision_id="x",
                opportunity_id="po-1",
                output=SystemOutput.MONITOR,
                reasons=(PaperDecisionReason.MONITOR_ONLY,),
                confidence=0.7,
                created_at_ms=0,
                creates_action=True,  # type: ignore[arg-type]
            )

    def test_writes_external_true_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PaperDecision(
                decision_id="x",
                opportunity_id="po-1",
                output=SystemOutput.MONITOR,
                reasons=(PaperDecisionReason.MONITOR_ONLY,),
                confidence=0.7,
                created_at_ms=0,
                writes_external=True,  # type: ignore[arg-type]
            )

    def test_approved_for_live_true_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PaperDecision(
                decision_id="x",
                opportunity_id="po-1",
                output=SystemOutput.MONITOR,
                reasons=(PaperDecisionReason.MONITOR_ONLY,),
                confidence=0.7,
                created_at_ms=0,
                approved_for_live=True,  # type: ignore[arg-type]
            )

    def test_need_recall_without_reason_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _decision(
                output=SystemOutput.NEED_RECALL,
                reasons=(PaperDecisionReason.MONITOR_ONLY,),
            )

    def test_block_without_block_reason_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _decision(
                output=SystemOutput.BLOCK,
                reasons=(PaperDecisionReason.MONITOR_ONLY,),
            )

    def test_block_with_high_risk_accepted(self) -> None:
        d = _decision(
            output=SystemOutput.BLOCK,
            reasons=(PaperDecisionReason.HIGH_RISK,),
        )
        assert d.output is SystemOutput.BLOCK

    def test_empty_reasons_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _decision(output=SystemOutput.WAIT, reasons=())


class TestPaperCoPilotResult:
    def test_valid_result_accepted(self) -> None:
        opp = make_opportunity()
        decision = PaperDecision(
            decision_id="dec-x",
            opportunity_id=opp.opportunity_id,
            output=SystemOutput.MONITOR,
            reasons=(PaperDecisionReason.MONITOR_ONLY,),
            confidence=0.7,
            created_at_ms=1_000_000,
        )
        r = PaperCoPilotResult(
            result_id="r-1",
            opportunity=opp,
            decision=decision,
            hash_chain_valid=True,
        )
        assert r.hash_chain_valid is True

    def test_decision_opportunity_mismatch_rejected(self) -> None:
        opp = make_opportunity()
        decision = PaperDecision(
            decision_id="dec-x",
            opportunity_id="other-id",
            output=SystemOutput.MONITOR,
            reasons=(PaperDecisionReason.MONITOR_ONLY,),
            confidence=0.7,
            created_at_ms=1_000_000,
        )
        with pytest.raises(ValidationError):
            PaperCoPilotResult(
                result_id="r-x",
                opportunity=opp,
                decision=decision,
                hash_chain_valid=True,
            )

    def test_permanent_ring_overlap_rejected(self) -> None:
        opp = make_opportunity()
        decision = PaperDecision(
            decision_id="dec-x",
            opportunity_id=opp.opportunity_id,
            output=SystemOutput.MONITOR,
            reasons=(PaperDecisionReason.MONITOR_ONLY,),
            confidence=0.7,
            created_at_ms=1_000_000,
        )
        with pytest.raises(ValidationError):
            PaperCoPilotResult(
                result_id="r-x",
                opportunity=opp,
                decision=decision,
                permanent_event_ids=("ev-shared",),
                ring_buffer_event_ids=("ev-shared",),
                hash_chain_valid=True,
            )
