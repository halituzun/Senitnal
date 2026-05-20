"""V7 — Paper co-pilot evaluator tests."""

from __future__ import annotations

from pathlib import Path

from sentinel.paper.copilot import PaperCoPilotContext, evaluate_paper_opportunity
from sentinel.paper.decision import PaperDecisionReason
from sentinel.paper.opportunity import PaperOpportunityKind
from sentinel.policy.record_builder import build_deontic_policy_candidate_record
from sentinel.runtime.output import SystemOutput
from sentinel.types.memory import MemoryRecord, MemoryRecordStatus
from sentinel.types.neural_seed import ProvenanceRef

from tests.paper._fixtures import make_opportunity
from tests.policy._fixtures import make_artifact


def _ctx(active: MemoryRecord | None = None) -> PaperCoPilotContext:
    return PaperCoPilotContext(now_ms=1_000_000, active_policy_record=active)


class TestPaperCoPilot:
    def test_high_risk_blocks(self) -> None:
        d = evaluate_paper_opportunity(
            opportunity=make_opportunity(risk_score=0.95),
            context=_ctx(),
        )
        assert d.output is SystemOutput.BLOCK
        assert PaperDecisionReason.HIGH_RISK in d.reasons

    def test_bad_order_blocks(self) -> None:
        d = evaluate_paper_opportunity(
            opportunity=make_opportunity(kind=PaperOpportunityKind.BAD_ORDER_OBSERVATION),
            context=_ctx(),
        )
        assert d.output is SystemOutput.BLOCK
        assert PaperDecisionReason.BAD_ORDER_OBSERVED in d.reasons

    def test_kill_switch_blocks(self) -> None:
        d = evaluate_paper_opportunity(
            opportunity=make_opportunity(kind=PaperOpportunityKind.KILL_SWITCH_OBSERVATION),
            context=_ctx(),
        )
        assert d.output is SystemOutput.BLOCK
        assert PaperDecisionReason.KILL_SWITCH_OBSERVED in d.reasons

    def test_stale_data_extreme_blocks(self) -> None:
        d = evaluate_paper_opportunity(
            opportunity=make_opportunity(staleness_ms=20000),
            context=_ctx(),
        )
        assert d.output is SystemOutput.BLOCK
        assert PaperDecisionReason.STALE_DATA in d.reasons

    def test_low_confidence_waits(self) -> None:
        d = evaluate_paper_opportunity(
            opportunity=make_opportunity(confidence=0.05, risk_score=0.1),
            context=_ctx(),
        )
        assert d.output is SystemOutput.WAIT
        assert PaperDecisionReason.INSUFFICIENT_CONFIDENCE in d.reasons

    def test_no_active_policy_conservative_monitor(self) -> None:
        d = evaluate_paper_opportunity(
            opportunity=make_opportunity(),
            context=_ctx(),
        )
        assert d.output in {SystemOutput.MONITOR, SystemOutput.NO_ACTION, SystemOutput.WAIT}

    def test_active_policy_block_upgrades_to_block(self) -> None:
        rec = build_deontic_policy_candidate_record(
            artifact=make_artifact(),
            provenance=ProvenanceRef(source_event_id="ev-1"),
            created_at_ms=1_000_000,
            evidence_refs=("approval-1",),
        ).model_copy(update={"status": MemoryRecordStatus.ACTIVE})

        # High risk_score is enough to flip the V6 policy to BLOCK.
        d = evaluate_paper_opportunity(
            opportunity=make_opportunity(risk_score=0.75),
            context=_ctx(active=rec),
        )
        # risk_score < 0.85 so paper engine prefers MONITOR; policy
        # upgrades it because the V6 rule fires at >= 0.7.
        assert d.output is SystemOutput.BLOCK
        assert PaperDecisionReason.POLICY_BLOCK in d.reasons

    def test_memory_echo_triggers_need_recall(self) -> None:
        d = evaluate_paper_opportunity(
            opportunity=make_opportunity(memory_echo_score=0.85),
            context=_ctx(),
        )
        assert d.output is SystemOutput.NEED_RECALL
        assert PaperDecisionReason.NEEDS_RECALL in d.reasons

    def test_replay_uncertain_adds_reason(self) -> None:
        d = evaluate_paper_opportunity(
            opportunity=make_opportunity(replay_evidence_score=0.1),
            context=_ctx(),
        )
        # Output is still MONITOR but reason set should include replay_uncertain.
        assert d.output is SystemOutput.MONITOR
        assert PaperDecisionReason.REPLAY_UNCERTAIN in d.reasons

    def test_normal_opportunity_monitor(self) -> None:
        d = evaluate_paper_opportunity(
            opportunity=make_opportunity(),
            context=_ctx(),
        )
        assert d.output is SystemOutput.MONITOR

    def test_deterministic_same_input(self) -> None:
        opp = make_opportunity()
        a = evaluate_paper_opportunity(opportunity=opp, context=_ctx())
        b = evaluate_paper_opportunity(opportunity=opp, context=_ctx())
        assert a == b

    def test_no_action_intent_in_evaluator_source(self) -> None:
        from sentinel.paper import copilot

        src = Path(copilot.__file__).read_text(encoding="utf-8")
        assert "ApprovedActionIntent" not in src
        assert "evaluate_action" not in src

    def test_evaluator_output_in_closed_set(self) -> None:
        for kind in PaperOpportunityKind:
            opp = make_opportunity(opportunity_id=f"po-{kind.value}", kind=kind)
            d = evaluate_paper_opportunity(opportunity=opp, context=_ctx())
            assert d.output in {
                SystemOutput.WAIT,
                SystemOutput.BLOCK,
                SystemOutput.MONITOR,
                SystemOutput.NEED_RECALL,
                SystemOutput.NO_ACTION,
            }
