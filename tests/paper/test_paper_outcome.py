"""V7 — Paper outcome + comparison tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sentinel.paper.decision import PaperDecision, PaperDecisionReason
from sentinel.paper.outcome import (
    PaperOutcome,
    PaperOutcomeKind,
    compare_paper_decision_to_outcome,
)
from sentinel.runtime.output import SystemOutput


def _outcome(
    *, external: bool = True, kind: PaperOutcomeKind = PaperOutcomeKind.OBSERVED_NEUTRAL
) -> PaperOutcome:
    return PaperOutcome(
        outcome_id="out-1",
        decision_id="dec-1",
        opportunity_id="po-1",
        observed_at_ms=2_000_000,
        outcome_kind=kind,
        confidence=0.8,
        external=external,
        source_event_refs=("ev-out-1",),
    )


def _decision(output: SystemOutput) -> PaperDecision:
    reasons: tuple[PaperDecisionReason, ...]
    if output is SystemOutput.BLOCK:
        reasons = (PaperDecisionReason.HIGH_RISK,)
    elif output is SystemOutput.NEED_RECALL:
        reasons = (PaperDecisionReason.NEEDS_RECALL,)
    else:
        reasons = (PaperDecisionReason.MONITOR_ONLY,)
    return PaperDecision(
        decision_id="dec-1",
        opportunity_id="po-1",
        output=output,
        reasons=reasons,
        confidence=0.6,
        created_at_ms=1_000_000,
    )


class TestPaperOutcome:
    def test_external_outcome_accepted(self) -> None:
        o = _outcome(external=True)
        assert o.external is True

    def test_internal_outcome_marks_evidence_unusable(self) -> None:
        comp = compare_paper_decision_to_outcome(
            decision=_decision(SystemOutput.BLOCK),
            outcome=_outcome(external=False, kind=PaperOutcomeKind.OBSERVED_RISK_MATERIALIZED),
        )
        assert comp.evidence_usable_for_replay is False

    def test_empty_source_event_refs_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PaperOutcome(
                outcome_id="x",
                decision_id="dec-1",
                opportunity_id="po-1",
                observed_at_ms=0,
                outcome_kind=PaperOutcomeKind.OBSERVED_NEUTRAL,
                confidence=0.5,
                external=True,
                source_event_refs=(),
            )

    def test_block_with_materialized_helps(self) -> None:
        comp = compare_paper_decision_to_outcome(
            decision=_decision(SystemOutput.BLOCK),
            outcome=_outcome(kind=PaperOutcomeKind.OBSERVED_RISK_MATERIALIZED),
        )
        assert comp.would_have_helped is True
        assert comp.alignment_score >= 0.8

    def test_block_with_no_risk_marks_conservative(self) -> None:
        comp = compare_paper_decision_to_outcome(
            decision=_decision(SystemOutput.BLOCK),
            outcome=_outcome(kind=PaperOutcomeKind.OBSERVED_RISK_DID_NOT_MATERIALIZE),
        )
        assert comp.was_conservative is True
        assert comp.would_have_hurt is True

    def test_monitor_with_materialized_risk_hurts(self) -> None:
        comp = compare_paper_decision_to_outcome(
            decision=_decision(SystemOutput.MONITOR),
            outcome=_outcome(kind=PaperOutcomeKind.OBSERVED_RISK_MATERIALIZED),
        )
        assert comp.would_have_hurt is True

    def test_comparison_alignment_bounded(self) -> None:
        comp = compare_paper_decision_to_outcome(
            decision=_decision(SystemOutput.MONITOR),
            outcome=_outcome(kind=PaperOutcomeKind.OBSERVED_NEUTRAL),
        )
        assert 0.0 <= comp.alignment_score <= 1.0
