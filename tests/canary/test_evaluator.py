"""V8 — Canary veto evaluator tests."""

from __future__ import annotations

from pathlib import Path

from sentinel.canary.candidate import CanaryEnvironment
from sentinel.canary.evaluator import CanaryVetoContext, evaluate_canary_veto
from sentinel.canary.veto import VetoDecisionKind, VetoReason
from sentinel.paper.decision import PaperDecision, PaperDecisionReason
from sentinel.policy.record_builder import build_deontic_policy_candidate_record
from sentinel.runtime.output import SystemOutput
from sentinel.types.memory import MemoryRecord, MemoryRecordStatus
from sentinel.types.neural_seed import ProvenanceRef

from tests.canary._fixtures import make_bounds, make_candidate, make_request, make_window
from tests.policy._fixtures import make_artifact


def _ctx(**overrides: object) -> CanaryVetoContext:
    base: dict[str, object] = {
        "bounds": make_bounds(),
        "window_state": make_window(),
        "now_ms": 1_000_001_000,
        "active_policy_record": None,
        "memory_store": None,
        "paper_decision": None,
        "replay_evidence_score": None,
        "kill_switch_observed": False,
    }
    base.update(overrides)
    return CanaryVetoContext(**base)  # type: ignore[arg-type]


def _active_policy() -> MemoryRecord:
    rec = build_deontic_policy_candidate_record(
        artifact=make_artifact(),
        provenance=ProvenanceRef(source_event_id="ev-1"),
        created_at_ms=1_000_000,
        evidence_refs=("approval-1",),
    )
    return rec.model_copy(update={"status": MemoryRecordStatus.ACTIVE})


def _paper(output: SystemOutput, *, reason: PaperDecisionReason | None = None) -> PaperDecision:
    if reason is None:
        reasons = (PaperDecisionReason.MONITOR_ONLY,)
        if output is SystemOutput.BLOCK:
            reasons = (PaperDecisionReason.HIGH_RISK,)
        elif output is SystemOutput.NEED_RECALL:
            reasons = (PaperDecisionReason.NEEDS_RECALL,)
    else:
        reasons = (reason,)
    return PaperDecision(
        decision_id="pd-1",
        opportunity_id="po-1",
        output=output,
        reasons=reasons,
        confidence=0.7,
        created_at_ms=1_000_000,
    )


class TestEvaluator:
    def test_expired_candidate_vetoes(self) -> None:
        candidate = make_candidate(expires_at_ms=1_000_000_500)
        d = evaluate_canary_veto(
            request=make_request(candidate=candidate, now_ms=1_000_001_000),
            context=_ctx(active_policy_record=_active_policy()),
        )
        assert d.decision is VetoDecisionKind.VETO
        assert VetoReason.EXPIRED_CANDIDATE in d.reasons
        assert d.system_output is SystemOutput.BLOCK

    def test_kill_switch_vetoes(self) -> None:
        d = evaluate_canary_veto(
            request=make_request(),
            context=_ctx(active_policy_record=_active_policy(), kill_switch_observed=True),
        )
        assert d.decision is VetoDecisionKind.VETO
        assert VetoReason.KILL_SWITCH_OBSERVED in d.reasons

    def test_high_risk_vetoes_via_bounds(self) -> None:
        d = evaluate_canary_veto(
            request=make_request(candidate=make_candidate(risk_score=0.95)),
            context=_ctx(active_policy_record=_active_policy()),
        )
        assert d.decision is VetoDecisionKind.VETO
        assert VetoReason.HIGH_RISK in d.reasons

    def test_no_active_policy_vetoes(self) -> None:
        d = evaluate_canary_veto(
            request=make_request(),
            context=_ctx(active_policy_record=None),
        )
        assert d.decision is VetoDecisionKind.VETO
        assert VetoReason.NO_ACTIVE_POLICY in d.reasons

    def test_policy_block_vetoes(self) -> None:
        # risk_score 0.75 is above the V6 fixture's high-risk rule (>=0.7).
        d = evaluate_canary_veto(
            request=make_request(candidate=make_candidate(risk_score=0.75)),
            context=_ctx(active_policy_record=_active_policy()),
        )
        assert d.decision is VetoDecisionKind.VETO
        assert VetoReason.POLICY_BLOCK in d.reasons

    def test_paper_block_vetoes(self) -> None:
        d = evaluate_canary_veto(
            request=make_request(),
            context=_ctx(
                active_policy_record=_active_policy(),
                paper_decision=_paper(SystemOutput.BLOCK, reason=PaperDecisionReason.HIGH_RISK),
            ),
        )
        assert d.decision is VetoDecisionKind.VETO
        assert VetoReason.HIGH_RISK in d.reasons

    def test_paper_need_recall_monitor(self) -> None:
        d = evaluate_canary_veto(
            request=make_request(),
            context=_ctx(
                active_policy_record=_active_policy(),
                paper_decision=_paper(SystemOutput.NEED_RECALL),
            ),
        )
        assert d.decision is VetoDecisionKind.MONITOR_ONLY
        assert d.system_output is SystemOutput.MONITOR

    def test_replay_uncertain_monitor(self) -> None:
        d = evaluate_canary_veto(
            request=make_request(),
            context=_ctx(
                active_policy_record=_active_policy(),
                replay_evidence_score=0.1,
            ),
        )
        assert d.decision is VetoDecisionKind.MONITOR_ONLY
        assert VetoReason.REPLAY_UNCERTAIN in d.reasons

    def test_negative_edge_vetoes(self) -> None:
        d = evaluate_canary_veto(
            request=make_request(candidate=make_candidate(expected_net_edge_pct=-0.1)),
            context=_ctx(active_policy_record=_active_policy()),
        )
        assert d.decision is VetoDecisionKind.VETO
        assert VetoReason.INSUFFICIENT_EDGE in d.reasons

    def test_benign_candidate_no_veto_not_approval(self) -> None:
        d = evaluate_canary_veto(
            request=make_request(),
            context=_ctx(active_policy_record=_active_policy()),
        )
        assert d.decision is VetoDecisionKind.NO_VETO
        assert d.system_output is SystemOutput.NO_ACTION
        # The four safety flags remain pinned False.
        assert d.creates_action is False
        assert d.writes_external is False
        assert d.approves_trade is False
        assert d.no_veto_is_approval is False
        assert d.can_affect_canary is False

    def test_no_veto_can_affect_canary_is_false(self) -> None:
        d = evaluate_canary_veto(
            request=make_request(),
            context=_ctx(active_policy_record=_active_policy()),
        )
        assert d.decision is VetoDecisionKind.NO_VETO
        assert d.can_affect_canary is False

    def test_monitor_can_affect_canary_is_false(self) -> None:
        d = evaluate_canary_veto(
            request=make_request(),
            context=_ctx(
                active_policy_record=_active_policy(),
                replay_evidence_score=0.1,
            ),
        )
        assert d.decision is VetoDecisionKind.MONITOR_ONLY
        assert d.can_affect_canary is False

    def test_veto_can_affect_canary_only_micro_live(self) -> None:
        d = evaluate_canary_veto(
            request=make_request(
                candidate=make_candidate(environment=CanaryEnvironment.SHADOW, risk_score=0.95)
            ),
            context=_ctx(active_policy_record=_active_policy()),
        )
        assert d.decision is VetoDecisionKind.VETO
        assert d.can_affect_canary is False

    def test_veto_micro_live_can_affect_canary(self) -> None:
        d = evaluate_canary_veto(
            request=make_request(candidate=make_candidate(risk_score=0.95)),
            context=_ctx(active_policy_record=_active_policy()),
        )
        assert d.decision is VetoDecisionKind.VETO
        assert d.can_affect_canary is True

    def test_no_approved_action_intent_in_source(self) -> None:
        from sentinel.canary import evaluator

        src = Path(evaluator.__file__).read_text(encoding="utf-8")
        assert "ApprovedActionIntent" not in src
        assert "evaluate_action" not in src
