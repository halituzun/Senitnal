"""V9 — Governance guard tests."""

from __future__ import annotations

from pathlib import Path

from sentinel.canary.candidate import CanaryEnvironment
from sentinel.canary.veto import (
    CanaryVetoDecision,
    VetoDecisionKind,
    VetoReason,
)
from sentinel.governance.decision import (
    GovernanceDecisionKind,
    GovernanceReason,
)
from sentinel.governance.guard import GovernanceGuardContext, evaluate_governance_guard
from sentinel.paper.decision import PaperDecision, PaperDecisionReason
from sentinel.policy.record_builder import build_deontic_policy_candidate_record
from sentinel.runtime.output import SystemOutput
from sentinel.types.memory import MemoryRecord, MemoryRecordStatus
from sentinel.types.neural_seed import ProvenanceRef

from tests.governance._fixtures import make_approval, make_request
from tests.policy._fixtures import make_artifact


def _active_policy() -> MemoryRecord:
    rec = build_deontic_policy_candidate_record(
        artifact=make_artifact(
            effective_at_ms=1_000_000,
            created_at_ms=1_000_000,
        ),
        provenance=ProvenanceRef(source_event_id="ev-1"),
        created_at_ms=1_000_000,
        evidence_refs=("approval",),
    )
    return rec.model_copy(update={"status": MemoryRecordStatus.ACTIVE})


def _ctx(**overrides: object) -> GovernanceGuardContext:
    base: dict[str, object] = {
        "now_ms": 1_500_000,
        "hash_chain_valid": True,
        "active_policy_record": _active_policy(),
        "canary_decision": None,
        "paper_decision": None,
        "human_approval": make_approval(),
        "memory_store": None,
        "replay_evidence_score": None,
        "kill_switch_observed": False,
    }
    base.update(overrides)
    return GovernanceGuardContext(**base)  # type: ignore[arg-type]


def _canary_veto() -> CanaryVetoDecision:
    return CanaryVetoDecision(
        decision_id="canary-veto-1",
        request_id="canary-req-1",
        candidate_id="cand-1",
        decision=VetoDecisionKind.VETO,
        system_output=SystemOutput.BLOCK,
        reasons=(VetoReason.HIGH_RISK,),
        confidence=0.7,
        environment=CanaryEnvironment.MICRO_LIVE_CANARY,
        shadow_only=False,
        can_affect_canary=True,
        created_at_ms=1_000_000,
        expires_at_ms=2_000_000,
    )


def _paper(output: SystemOutput) -> PaperDecision:
    reasons: tuple[PaperDecisionReason, ...]
    if output is SystemOutput.BLOCK:
        reasons = (PaperDecisionReason.HIGH_RISK,)
    elif output is SystemOutput.NEED_RECALL:
        reasons = (PaperDecisionReason.NEEDS_RECALL,)
    else:
        reasons = (PaperDecisionReason.MONITOR_ONLY,)
    return PaperDecision(
        decision_id="pap-1",
        opportunity_id="po-1",
        output=output,
        reasons=reasons,
        confidence=0.7,
        created_at_ms=1_000_000,
    )


class TestGuard:
    def test_hash_chain_invalid_blocks(self) -> None:
        d = evaluate_governance_guard(
            request=make_request(),
            context=_ctx(hash_chain_valid=False),
        )
        assert d.decision is GovernanceDecisionKind.BLOCK_LIVE_CANDIDATE
        assert GovernanceReason.HASH_CHAIN_INVALID in d.reasons

    def test_timeout_blocks(self) -> None:
        d = evaluate_governance_guard(
            request=make_request(deadline_ms=1_000_500),
            context=_ctx(now_ms=2_000_000),
        )
        assert d.decision is GovernanceDecisionKind.BLOCK_LIVE_CANDIDATE
        assert GovernanceReason.GOVERNANCE_TIMEOUT in d.reasons

    def test_kill_switch_blocks(self) -> None:
        d = evaluate_governance_guard(
            request=make_request(),
            context=_ctx(kill_switch_observed=True),
        )
        assert d.decision is GovernanceDecisionKind.BLOCK_LIVE_CANDIDATE
        assert GovernanceReason.KILL_SWITCH_OBSERVED in d.reasons

    def test_missing_active_policy_blocks(self) -> None:
        d = evaluate_governance_guard(
            request=make_request(),
            context=_ctx(active_policy_record=None),
        )
        assert d.decision is GovernanceDecisionKind.BLOCK_LIVE_CANDIDATE
        assert GovernanceReason.MISSING_ACTIVE_POLICY in d.reasons

    def test_missing_human_approval_blocks(self) -> None:
        d = evaluate_governance_guard(
            request=make_request(),
            context=_ctx(human_approval=None),
        )
        assert d.decision is GovernanceDecisionKind.BLOCK_LIVE_CANDIDATE
        assert GovernanceReason.MISSING_HUMAN_APPROVAL in d.reasons

    def test_expired_human_approval_blocks(self) -> None:
        d = evaluate_governance_guard(
            request=make_request(),
            context=_ctx(human_approval=make_approval(expires_at_ms=1_100_000)),
        )
        assert d.decision is GovernanceDecisionKind.BLOCK_LIVE_CANDIDATE
        assert GovernanceReason.HUMAN_APPROVAL_EXPIRED in d.reasons

    def test_canary_veto_blocks(self) -> None:
        d = evaluate_governance_guard(
            request=make_request(),
            context=_ctx(canary_decision=_canary_veto()),
        )
        assert d.decision is GovernanceDecisionKind.BLOCK_LIVE_CANDIDATE
        assert GovernanceReason.CANARY_VETO in d.reasons

    def test_paper_block_blocks(self) -> None:
        d = evaluate_governance_guard(
            request=make_request(),
            context=_ctx(paper_decision=_paper(SystemOutput.BLOCK)),
        )
        assert d.decision is GovernanceDecisionKind.BLOCK_LIVE_CANDIDATE
        assert GovernanceReason.PAPER_BLOCK in d.reasons

    def test_policy_block_blocks(self) -> None:
        # risk_score 0.75 triggers the V6 policy's high-risk rule.
        d = evaluate_governance_guard(
            request=make_request(risk_score=0.75),
            context=_ctx(),
        )
        assert d.decision is GovernanceDecisionKind.BLOCK_LIVE_CANDIDATE
        assert GovernanceReason.POLICY_BLOCK in d.reasons

    def test_memory_conflict_need_recall(self) -> None:
        d = evaluate_governance_guard(
            request=make_request(
                memory_record_refs=("mem-1",),
                risk_score=0.6,
            ),
            context=_ctx(),
        )
        assert d.decision is GovernanceDecisionKind.NEED_RECALL
        assert GovernanceReason.MEMORY_CONFLICT in d.reasons

    def test_replay_uncertain_monitor(self) -> None:
        d = evaluate_governance_guard(
            request=make_request(),
            context=_ctx(replay_evidence_score=0.1),
        )
        assert d.decision is GovernanceDecisionKind.MONITOR_ONLY
        assert GovernanceReason.REPLAY_UNCERTAIN in d.reasons

    def test_high_risk_blocks(self) -> None:
        d = evaluate_governance_guard(
            request=make_request(risk_score=0.95),
            context=_ctx(),
        )
        assert d.decision is GovernanceDecisionKind.BLOCK_LIVE_CANDIDATE
        # 0.95 trips both the V6 policy high-risk rule (>= 0.7) and the
        # V9 hard-stop (>= 0.85); the V6 path fires first.
        assert GovernanceReason.HIGH_RISK in d.reasons or GovernanceReason.POLICY_BLOCK in d.reasons

    def test_low_confidence_wait(self) -> None:
        d = evaluate_governance_guard(
            request=make_request(confidence=0.1),
            context=_ctx(),
        )
        assert d.decision in (
            GovernanceDecisionKind.WAIT_FOR_HUMAN,
            GovernanceDecisionKind.MONITOR_ONLY,
        )
        assert GovernanceReason.LOW_CONFIDENCE in d.reasons

    def test_benign_no_action(self) -> None:
        d = evaluate_governance_guard(
            request=make_request(),
            context=_ctx(),
        )
        assert d.decision is GovernanceDecisionKind.NO_ACTION
        # Safety flags pinned False
        assert d.creates_action is False
        assert d.writes_external is False
        assert d.approves_trade is False
        assert d.no_veto_is_approval is False
        assert d.monitor_is_approval is False
        # no_action is not approval
        assert d.live_impact_allowed is False

    def test_monitor_live_impact_allowed_false(self) -> None:
        d = evaluate_governance_guard(
            request=make_request(),
            context=_ctx(replay_evidence_score=0.1),
        )
        assert d.live_impact_allowed is False

    def test_wait_live_impact_allowed_false(self) -> None:
        d = evaluate_governance_guard(
            request=make_request(confidence=0.05),
            context=_ctx(),
        )
        assert d.live_impact_allowed is False

    def test_no_approved_action_intent_in_source(self) -> None:
        from sentinel.governance import guard

        src = Path(guard.__file__).read_text(encoding="utf-8")
        assert "ApprovedActionIntent" not in src
        assert "evaluate_action_with_audit" not in src
