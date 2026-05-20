"""V8 — Canary veto evaluator.

Pure deterministic function.  Same request + same context → same
decision.  Constitutional discipline:

    - Never constructs an action-intent object.
    - Never writes to Gel.Al.
    - Never mutates memory store or policy record.
    - Output is drawn from the closed v0.1 ``SystemOutput`` set.
    - ``no_veto`` never becomes approval — the decision schema's
      ``no_veto_is_approval`` flag is pinned ``Literal[False]``.
"""

from __future__ import annotations

from dataclasses import dataclass

from sentinel.canary.candidate import CanaryCandidateAction, CanaryEnvironment
from sentinel.canary.limits import (
    CanaryDecisionWindowState,
    CanaryMicroLiveBounds,
    check_canary_bounds,
)
from sentinel.canary.veto import (
    CanaryVetoDecision,
    VetoDecisionKind,
    VetoReason,
    VetoRequest,
)
from sentinel.memory.store import InMemoryExplicitMemoryStore  # noqa: TC001
from sentinel.paper.decision import PaperDecision, PaperDecisionReason
from sentinel.policy.evaluator import (
    FinancialPolicyInput,
    evaluate_financial_policy,
)
from sentinel.runtime.output import SystemOutput
from sentinel.types.memory import MemoryRecord  # noqa: TC001


@dataclass(slots=True)
class CanaryVetoContext:
    """Caller-supplied context for one canary veto evaluation.

    All fields are consulted **read-only**.  The window state is
    updated by the evaluator (counter increment) but no external
    state is mutated.
    """

    bounds: CanaryMicroLiveBounds
    window_state: CanaryDecisionWindowState
    now_ms: int
    active_policy_record: MemoryRecord | None = None
    memory_store: InMemoryExplicitMemoryStore | None = None
    paper_decision: PaperDecision | None = None
    replay_evidence_score: float | None = None
    kill_switch_observed: bool = False


def _decision(
    *,
    request: VetoRequest,
    decision: VetoDecisionKind,
    output: SystemOutput,
    reasons: tuple[VetoReason, ...],
    confidence: float,
    can_affect_canary: bool,
    shadow_only: bool,
    now_ms: int,
) -> CanaryVetoDecision:
    return CanaryVetoDecision(
        decision_id=f"canary-dec-{request.candidate.candidate_id}-{now_ms}",
        request_id=request.request_id,
        candidate_id=request.candidate.candidate_id,
        decision=decision,
        system_output=output,
        reasons=reasons,
        confidence=confidence,
        environment=request.candidate.environment,
        shadow_only=shadow_only,
        can_affect_canary=can_affect_canary,
        created_at_ms=now_ms,
        expires_at_ms=max(now_ms + 1, request.candidate.expires_at_ms),
    )


def _build_policy_input(candidate: CanaryCandidateAction) -> FinancialPolicyInput:
    env_value = candidate.environment.value
    # FinancialPolicyInput.environment is the V6 enum
    # {"local", "shadow", "paper", "canary", "live"}.  Map
    # micro_live_canary to "canary"; others pass-through where valid.
    env_map = {
        "local": "local",
        "shadow": "shadow",
        "paper": "paper",
        "micro_live_canary": "canary",
    }
    mapped_env = env_map.get(env_value, "shadow")
    return FinancialPolicyInput(
        event_id=candidate.candidate_id,
        scope_id=candidate.scope_hash,
        environment=mapped_env,  # type: ignore[arg-type]
        risk_score=candidate.risk_score,
        confidence=candidate.confidence,
        staleness_ms=candidate.staleness_ms,
        latency_ms=candidate.latency_ms,
        orderbook_age_ms=candidate.orderbook_age_ms,
        spread_pct=candidate.spread_pct,
        liquidity_score=candidate.liquidity_score,
        bad_order=False,  # candidate is observed pre-execution
        kill_switch_active=False,  # handled by evaluator hard-stop
        provenance_missing=not candidate.provenance_hash,
        unknown_risk_score=0.1,
        source_event_refs=candidate.source_event_refs,
    )


def evaluate_canary_veto(
    *,
    request: VetoRequest,
    context: CanaryVetoContext,
) -> CanaryVetoDecision:
    """Produce a veto/monitor/no-veto decision for ``request``.

    Decision order:

    1. expired candidate                              -> veto / BLOCK
    2. kill_switch observed                           -> veto / BLOCK
    3. canary bounds violation                        -> veto / BLOCK
    4. missing active policy + missing_policy_blocks  -> veto / BLOCK
    5. V6 active policy outputs BLOCK                 -> veto / BLOCK
    6. V7 paper decision BLOCK                        -> veto / BLOCK
    7. V7 paper decision NEED_RECALL                  -> monitor_only / MONITOR
    8. replay evidence uncertain                      -> monitor_only / MONITOR
    9. expected_net_edge_pct <= 0                     -> veto / BLOCK
    10. otherwise                                     -> no_veto / NO_ACTION

    ``can_affect_canary`` is True only when the final decision is
    ``veto`` AND the candidate's environment is ``micro_live_canary``.
    """
    candidate = request.candidate
    context.window_state.candidates_seen_this_hour += 1

    try:
        # 1) Expired candidate.
        if context.now_ms >= candidate.expires_at_ms:
            return _veto(
                request=request,
                reasons=(VetoReason.EXPIRED_CANDIDATE,),
                context=context,
            )

        # 2) Kill switch.
        if context.kill_switch_observed and context.bounds.kill_switch_blocks:
            return _veto(
                request=request,
                reasons=(VetoReason.KILL_SWITCH_OBSERVED,),
                context=context,
            )

        # 3) Bounds violation.
        ok, bound_reasons = check_canary_bounds(
            candidate=candidate,
            bounds=context.bounds,
            state=context.window_state,
            now_ms=context.now_ms,
        )
        if not ok:
            return _veto(request=request, reasons=bound_reasons, context=context)

        # 4) Missing active policy.
        if context.active_policy_record is None and context.bounds.missing_policy_blocks:
            return _veto(
                request=request,
                reasons=(VetoReason.NO_ACTIVE_POLICY,),
                context=context,
            )

        # 5) Active policy BLOCK.
        if context.active_policy_record is not None:
            try:
                policy_eval = evaluate_financial_policy(
                    policy_record=context.active_policy_record,
                    policy_input=_build_policy_input(candidate),
                    now_ms=context.now_ms,
                )
                if policy_eval.output is SystemOutput.BLOCK:
                    return _veto(
                        request=request,
                        reasons=(VetoReason.POLICY_BLOCK,),
                        context=context,
                    )
            except ValueError:
                # Policy expired / stale / not ACTIVE — fail closed.
                return _veto(
                    request=request,
                    reasons=(VetoReason.NO_ACTIVE_POLICY,),
                    context=context,
                )

        # 6) Paper decision BLOCK.
        paper_decision = context.paper_decision
        if paper_decision is not None and paper_decision.output is SystemOutput.BLOCK:
            paper_reason = VetoReason.POLICY_BLOCK
            if PaperDecisionReason.MEMORY_CONFLICT in paper_decision.reasons:
                paper_reason = VetoReason.MEMORY_CONFLICT
            elif PaperDecisionReason.HIGH_RISK in paper_decision.reasons:
                paper_reason = VetoReason.HIGH_RISK
            return _veto(request=request, reasons=(paper_reason,), context=context)

        # 7) Paper NEED_RECALL → monitor_only.
        if paper_decision is not None and paper_decision.output is SystemOutput.NEED_RECALL:
            return _monitor(
                request=request,
                reasons=(VetoReason.MEMORY_CONFLICT,),
                context=context,
            )

        # 8) Replay uncertain.
        if context.replay_evidence_score is not None and context.replay_evidence_score < 0.3:
            return _monitor(
                request=request,
                reasons=(VetoReason.REPLAY_UNCERTAIN,),
                context=context,
            )

        # 9) Insufficient edge.
        if candidate.expected_net_edge_pct <= 0.0:
            return _veto(
                request=request,
                reasons=(VetoReason.INSUFFICIENT_EDGE,),
                context=context,
            )

        # 10) No-veto.  Important: this is NOT approval.
        return _no_veto(request=request, context=context)
    except Exception:  # pragma: no cover (fail-closed defense-in-depth)
        if context.bounds.fail_closed_on_error:
            return _veto(
                request=request,
                reasons=(VetoReason.FAIL_CLOSED,),
                context=context,
            )
        raise


def _veto(
    *,
    request: VetoRequest,
    reasons: tuple[VetoReason, ...],
    context: CanaryVetoContext,
) -> CanaryVetoDecision:
    context.window_state.vetoes_this_hour += 1
    can_affect = request.candidate.environment is CanaryEnvironment.MICRO_LIVE_CANARY
    return _decision(
        request=request,
        decision=VetoDecisionKind.VETO,
        output=SystemOutput.BLOCK,
        reasons=reasons,
        confidence=max(request.candidate.confidence, 0.5),
        can_affect_canary=can_affect,
        shadow_only=not can_affect,
        now_ms=context.now_ms,
    )


def _monitor(
    *,
    request: VetoRequest,
    reasons: tuple[VetoReason, ...],
    context: CanaryVetoContext,
) -> CanaryVetoDecision:
    return _decision(
        request=request,
        decision=VetoDecisionKind.MONITOR_ONLY,
        output=SystemOutput.MONITOR,
        reasons=reasons,
        confidence=request.candidate.confidence,
        can_affect_canary=False,
        shadow_only=True,
        now_ms=context.now_ms,
    )


def _no_veto(
    *,
    request: VetoRequest,
    context: CanaryVetoContext,
) -> CanaryVetoDecision:
    context.window_state.unvetoed_this_hour += 1
    return _decision(
        request=request,
        decision=VetoDecisionKind.NO_VETO,
        output=SystemOutput.NO_ACTION,
        reasons=(VetoReason.NO_VETO_REASON_FOUND,),
        confidence=request.candidate.confidence,
        can_affect_canary=False,
        shadow_only=True,
        now_ms=context.now_ms,
    )


__all__ = ["CanaryVetoContext", "evaluate_canary_veto"]
