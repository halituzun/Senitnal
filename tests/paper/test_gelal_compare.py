"""V7 — Paper / Gel.Al comparison tests."""

from __future__ import annotations

from sentinel.integrations.gelal_shadow import GelAlShadowEventType
from sentinel.paper.decision import PaperDecision, PaperDecisionReason
from sentinel.paper.gelal_compare import compare_gelal_shadow_to_paper_decision
from sentinel.runtime.output import SystemOutput

from tests.paper._fixtures import make_gelal_envelope


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
        created_at_ms=0,
    )


class TestGelAlPaperComparison:
    def test_same_direction_opportunity_seen_monitor(self) -> None:
        env = make_gelal_envelope(event_type=GelAlShadowEventType.OPPORTUNITY_SEEN)
        comp = compare_gelal_shadow_to_paper_decision(
            envelope=env,
            paper_decision=_decision(SystemOutput.MONITOR),
            now_ms=1_000_000,
        )
        assert comp.agreement_band == "same_direction"

    def test_sentinel_more_conservative(self) -> None:
        env = make_gelal_envelope(event_type=GelAlShadowEventType.OPPORTUNITY_SEEN)
        comp = compare_gelal_shadow_to_paper_decision(
            envelope=env,
            paper_decision=_decision(SystemOutput.BLOCK),
            now_ms=1_000_000,
        )
        assert comp.agreement_band == "sentinel_more_conservative"

    def test_sentinel_less_conservative(self) -> None:
        env = make_gelal_envelope(
            event_type=GelAlShadowEventType.EXECUTION_ATTEMPT_OBSERVED,
            payload={"bad_order": True, "order_sent": True, "confidence": 0.5},
        )
        comp = compare_gelal_shadow_to_paper_decision(
            envelope=env,
            paper_decision=_decision(SystemOutput.MONITOR),
            now_ms=1_000_000,
        )
        assert comp.agreement_band == "sentinel_less_conservative"

    def test_kill_switch_same_direction_when_block(self) -> None:
        env = make_gelal_envelope(
            event_type=GelAlShadowEventType.KILL_SWITCH_OBSERVED,
            payload={
                "kill_switch_active": True,
                "source": "operator",
                "observed_by": "gel_al_runtime",
            },
        )
        comp = compare_gelal_shadow_to_paper_decision(
            envelope=env,
            paper_decision=_decision(SystemOutput.BLOCK),
            now_ms=1_000_000,
        )
        assert comp.agreement_band == "same_direction"

    def test_incomparable_when_unknown(self) -> None:
        env = make_gelal_envelope(event_type=GelAlShadowEventType.PAPER_RESULT_OBSERVED)
        comp = compare_gelal_shadow_to_paper_decision(
            envelope=env,
            paper_decision=_decision(SystemOutput.WAIT),
            now_ms=1_000_000,
        )
        assert comp.agreement_band == "incomparable"

    def test_safety_note_no_forbidden_literal(self) -> None:
        env = make_gelal_envelope()
        comp = compare_gelal_shadow_to_paper_decision(
            envelope=env,
            paper_decision=_decision(SystemOutput.MONITOR),
            now_ms=0,
        )
        for needle in ("buy", "sell", "execute", "order", "submit", "_real"):
            assert needle not in comp.safety_note.lower()
