"""V9 — Live governance guard evaluator.

Pure deterministic function.  Never constructs an action-intent
object, never writes to Gel.Al, never mutates the memory store or
active policy record.
"""

from __future__ import annotations

from dataclasses import dataclass

from sentinel.canary.veto import CanaryVetoDecision, VetoDecisionKind
from sentinel.governance.approval import HumanApprovalRecord, is_human_approval_valid
from sentinel.governance.decision import (
    GovernanceDecisionKind,
    GovernanceReason,
    LiveGovernanceDecision,
)
from sentinel.governance.request import LiveGovernanceRequest  # noqa: TC001
from sentinel.memory.store import InMemoryExplicitMemoryStore  # noqa: TC001
from sentinel.paper.decision import PaperDecision  # noqa: TC001
from sentinel.policy.evaluator import (
    FinancialPolicyInput,
    evaluate_financial_policy,
)
from sentinel.runtime.output import SystemOutput
from sentinel.types.memory import MemoryRecord  # noqa: TC001

_HIGH_RISK_THRESHOLD = 0.85
_LOW_CONFIDENCE_THRESHOLD = 0.3
_REPLAY_UNCERTAIN_THRESHOLD = 0.3


@dataclass(slots=True)
class GovernanceGuardContext:
    """Caller-supplied context for one governance evaluation."""

    now_ms: int
    hash_chain_valid: bool = True
    active_policy_record: MemoryRecord | None = None
    canary_decision: CanaryVetoDecision | None = None
    paper_decision: PaperDecision | None = None
    human_approval: HumanApprovalRecord | None = None
    memory_store: InMemoryExplicitMemoryStore | None = None
    replay_evidence_score: float | None = None
    kill_switch_observed: bool = False


def _decision(
    *,
    request: LiveGovernanceRequest,
    decision: GovernanceDecisionKind,
    output: SystemOutput,
    reasons: tuple[GovernanceReason, ...],
    confidence: float,
    live_impact_allowed: bool,
    now_ms: int,
    human_approval_ref: str | None = None,
    canary_decision_ref: str | None = None,
    paper_decision_ref: str | None = None,
    policy_record_ref: str | None = None,
) -> LiveGovernanceDecision:
    return LiveGovernanceDecision(
        decision_id=f"gov-dec-{request.request_id}-{now_ms}",
        request_id=request.request_id,
        decision=decision,
        system_output=output,
        reasons=reasons,
        confidence=confidence,
        human_approval_ref=human_approval_ref,
        policy_record_ref=policy_record_ref,
        canary_decision_ref=canary_decision_ref,
        paper_decision_ref=paper_decision_ref,
        replay_evidence_refs=request.replay_evidence_refs,
        memory_record_refs=request.memory_record_refs,
        live_impact_possible=request.live_impact_possible,
        live_impact_allowed=live_impact_allowed,
        created_at_ms=now_ms,
        expires_at_ms=max(now_ms + 1, request.deadline_ms),
    )


def _block(
    *,
    request: LiveGovernanceRequest,
    reasons: tuple[GovernanceReason, ...],
    now_ms: int,
    confidence: float,
    human_approval_ref: str | None = None,
    canary_decision_ref: str | None = None,
    paper_decision_ref: str | None = None,
    policy_record_ref: str | None = None,
) -> LiveGovernanceDecision:
    return _decision(
        request=request,
        decision=GovernanceDecisionKind.BLOCK_LIVE_CANDIDATE,
        output=SystemOutput.BLOCK,
        reasons=reasons,
        confidence=confidence,
        live_impact_allowed=request.live_impact_possible,
        now_ms=now_ms,
        human_approval_ref=human_approval_ref,
        canary_decision_ref=canary_decision_ref,
        paper_decision_ref=paper_decision_ref,
        policy_record_ref=policy_record_ref,
    )


def _build_policy_input(
    request: LiveGovernanceRequest,
) -> FinancialPolicyInput:
    env_value = request.scope.environment.value
    env_map = {
        "local": "local",
        "shadow": "shadow",
        "paper": "paper",
        "micro_live_canary": "canary",
        "limited_live": "live",
    }
    mapped = env_map.get(env_value, "shadow")
    return FinancialPolicyInput(
        event_id=request.request_id,
        scope_id=request.scope.scope_id,
        environment=mapped,  # type: ignore[arg-type]
        risk_score=request.risk_score,
        confidence=request.confidence,
        staleness_ms=request.staleness_ms,
        latency_ms=request.latency_ms,
        orderbook_age_ms=request.latency_ms,
        spread_pct=0.0,
        liquidity_score=0.5,
        bad_order=False,
        kill_switch_active=False,
        provenance_missing=not request.provenance_hash,
        unknown_risk_score=0.1,
        source_event_refs=request.source_event_refs,
    )


def evaluate_governance_guard(
    *,
    request: LiveGovernanceRequest,
    context: GovernanceGuardContext,
) -> LiveGovernanceDecision:
    """Evaluate a governance request and return a closed-output decision.

    Decision order (fail-closed throughout):

    1. hash_chain invalid              -> block
    2. deadline expired                -> block
    3. kill_switch_observed            -> block
    4. missing active policy           -> block
    5. live_impact + invalid approval  -> block
    6. canary veto                     -> block
    7. paper BLOCK                     -> block
    8. policy BLOCK                    -> block
    9. memory conflict (refs present)  -> need_recall
    10. replay uncertain               -> monitor
    11. high risk                      -> block
    12. low confidence                 -> monitor / wait
    13. otherwise                      -> no_action
    """
    now_ms = context.now_ms

    # 1) Hash chain.
    if not context.hash_chain_valid:
        return _block(
            request=request,
            reasons=(GovernanceReason.HASH_CHAIN_INVALID,),
            now_ms=now_ms,
            confidence=request.confidence,
        )

    # 2) Deadline expired.
    if now_ms >= request.deadline_ms:
        return _block(
            request=request,
            reasons=(GovernanceReason.GOVERNANCE_TIMEOUT,),
            now_ms=now_ms,
            confidence=request.confidence,
        )

    # 3) Kill switch.
    if context.kill_switch_observed:
        return _block(
            request=request,
            reasons=(GovernanceReason.KILL_SWITCH_OBSERVED,),
            now_ms=now_ms,
            confidence=request.confidence,
        )

    # 4) Missing active policy.
    if context.active_policy_record is None:
        return _block(
            request=request,
            reasons=(GovernanceReason.MISSING_ACTIVE_POLICY,),
            now_ms=now_ms,
            confidence=request.confidence,
        )

    policy_record_ref = context.active_policy_record.record_id

    # 5) Human approval gate.
    human_approval_ref: str | None = None
    if request.live_impact_possible:
        approval = context.human_approval
        if approval is None or not is_human_approval_valid(
            approval=approval,
            request_id=request.request_id,
            now_ms=now_ms,
        ):
            reason = GovernanceReason.MISSING_HUMAN_APPROVAL
            if approval is not None:
                if approval.status.value == "rejected":
                    reason = GovernanceReason.HUMAN_REJECTED
                elif now_ms > approval.expires_at_ms:
                    reason = GovernanceReason.HUMAN_APPROVAL_EXPIRED
            return _block(
                request=request,
                reasons=(reason,),
                now_ms=now_ms,
                confidence=request.confidence,
                policy_record_ref=policy_record_ref,
            )
        human_approval_ref = approval.approval_id

    # 6) Canary veto.
    canary_decision_ref: str | None = None
    if context.canary_decision is not None:
        canary_decision_ref = context.canary_decision.decision_id
        if context.canary_decision.decision is VetoDecisionKind.VETO:
            return _block(
                request=request,
                reasons=(GovernanceReason.CANARY_VETO,),
                now_ms=now_ms,
                confidence=request.confidence,
                human_approval_ref=human_approval_ref,
                canary_decision_ref=canary_decision_ref,
                policy_record_ref=policy_record_ref,
            )

    # 7) Paper BLOCK.
    paper_decision_ref: str | None = None
    if context.paper_decision is not None:
        paper_decision_ref = context.paper_decision.decision_id
        if context.paper_decision.output is SystemOutput.BLOCK:
            return _block(
                request=request,
                reasons=(GovernanceReason.PAPER_BLOCK,),
                now_ms=now_ms,
                confidence=request.confidence,
                human_approval_ref=human_approval_ref,
                canary_decision_ref=canary_decision_ref,
                paper_decision_ref=paper_decision_ref,
                policy_record_ref=policy_record_ref,
            )

    # 8) Active policy.
    try:
        policy_eval = evaluate_financial_policy(
            policy_record=context.active_policy_record,
            policy_input=_build_policy_input(request),
            now_ms=now_ms,
        )
        if policy_eval.output is SystemOutput.BLOCK:
            return _block(
                request=request,
                reasons=(GovernanceReason.POLICY_BLOCK,),
                now_ms=now_ms,
                confidence=request.confidence,
                human_approval_ref=human_approval_ref,
                canary_decision_ref=canary_decision_ref,
                paper_decision_ref=paper_decision_ref,
                policy_record_ref=policy_record_ref,
            )
    except ValueError:
        # Policy expired / stale / not ACTIVE — fail closed.
        return _block(
            request=request,
            reasons=(GovernanceReason.MISSING_ACTIVE_POLICY,),
            now_ms=now_ms,
            confidence=request.confidence,
            human_approval_ref=human_approval_ref,
            canary_decision_ref=canary_decision_ref,
            paper_decision_ref=paper_decision_ref,
        )

    # 9) Memory conflict — model as NEED_RECALL when refs are present
    # but no other block reason has fired.
    if (
        request.memory_record_refs
        and (
            context.paper_decision is None
            or context.paper_decision.output is not SystemOutput.MONITOR
        )
        and request.risk_score >= 0.5
    ):
        return _decision(
            request=request,
            decision=GovernanceDecisionKind.NEED_RECALL,
            output=SystemOutput.NEED_RECALL,
            reasons=(GovernanceReason.MEMORY_CONFLICT,),
            confidence=request.confidence,
            live_impact_allowed=False,
            now_ms=now_ms,
            human_approval_ref=human_approval_ref,
            canary_decision_ref=canary_decision_ref,
            paper_decision_ref=paper_decision_ref,
            policy_record_ref=policy_record_ref,
        )

    # 10) Replay uncertain.
    if (
        context.replay_evidence_score is not None
        and context.replay_evidence_score < _REPLAY_UNCERTAIN_THRESHOLD
    ):
        return _decision(
            request=request,
            decision=GovernanceDecisionKind.MONITOR_ONLY,
            output=SystemOutput.MONITOR,
            reasons=(GovernanceReason.REPLAY_UNCERTAIN,),
            confidence=request.confidence,
            live_impact_allowed=False,
            now_ms=now_ms,
            human_approval_ref=human_approval_ref,
            canary_decision_ref=canary_decision_ref,
            paper_decision_ref=paper_decision_ref,
            policy_record_ref=policy_record_ref,
        )

    # 11) High risk.
    if request.risk_score >= _HIGH_RISK_THRESHOLD:
        return _block(
            request=request,
            reasons=(GovernanceReason.HIGH_RISK,),
            now_ms=now_ms,
            confidence=request.confidence,
            human_approval_ref=human_approval_ref,
            canary_decision_ref=canary_decision_ref,
            paper_decision_ref=paper_decision_ref,
            policy_record_ref=policy_record_ref,
        )

    # 12) Low confidence.
    if request.confidence < _LOW_CONFIDENCE_THRESHOLD:
        kind = (
            GovernanceDecisionKind.WAIT_FOR_HUMAN
            if request.live_impact_possible
            else GovernanceDecisionKind.MONITOR_ONLY
        )
        output = (
            SystemOutput.WAIT
            if kind is GovernanceDecisionKind.WAIT_FOR_HUMAN
            else SystemOutput.MONITOR
        )
        return _decision(
            request=request,
            decision=kind,
            output=output,
            reasons=(GovernanceReason.LOW_CONFIDENCE,),
            confidence=request.confidence,
            live_impact_allowed=False,
            now_ms=now_ms,
            human_approval_ref=human_approval_ref,
            canary_decision_ref=canary_decision_ref,
            paper_decision_ref=paper_decision_ref,
            policy_record_ref=policy_record_ref,
        )

    # 13) Otherwise: no_action.  This is NOT approval.
    return _decision(
        request=request,
        decision=GovernanceDecisionKind.NO_ACTION,
        output=SystemOutput.NO_ACTION,
        reasons=(GovernanceReason.NO_BLOCK_REASON_FOUND,),
        confidence=request.confidence,
        live_impact_allowed=False,
        now_ms=now_ms,
        human_approval_ref=human_approval_ref,
        canary_decision_ref=canary_decision_ref,
        paper_decision_ref=paper_decision_ref,
        policy_record_ref=policy_record_ref,
    )


__all__ = ["GovernanceGuardContext", "evaluate_governance_guard"]
