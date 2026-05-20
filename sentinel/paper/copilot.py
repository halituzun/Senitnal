"""V7 — Paper co-pilot evaluator.

Pure deterministic function: same ``PaperOpportunity`` + same
``PaperCoPilotContext`` → same ``PaperDecision``.

Constitutional discipline:
    - Never constructs an action-intent object.
    - Never writes to Gel.Al.
    - Never mutates the memory store or active policy record.
    - Output is drawn from the closed v0.1 ``SystemOutput`` set.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from sentinel.memory.store import InMemoryExplicitMemoryStore  # noqa: TC001
from sentinel.paper.decision import PaperDecision, PaperDecisionReason
from sentinel.paper.opportunity import PaperOpportunity, PaperOpportunityKind
from sentinel.policy.evaluator import (
    FinancialPolicyInput,
    evaluate_financial_policy,
)
from sentinel.runtime.output import SystemOutput
from sentinel.types.memory import MemoryRecord  # noqa: TC001

# ---------------------------------------------------------------------------
# Scoring thresholds (deterministic, conservative).
# ---------------------------------------------------------------------------

_RISK_BLOCK_THRESHOLD: Final[float] = 0.85
_STALENESS_BLOCK_THRESHOLD_MS: Final[int] = 5000
_STALENESS_MONITOR_THRESHOLD_MS: Final[int] = 1000
_CONFIDENCE_WAIT_THRESHOLD: Final[float] = 0.2
_REPLAY_UNCERTAIN_THRESHOLD: Final[float] = 0.3
_MEMORY_ECHO_RECALL_THRESHOLD: Final[float] = 0.7


@dataclass(frozen=True, slots=True)
class PaperCoPilotContext:
    """Caller-supplied context for one paper evaluation.

    ``active_policy_record`` is consulted read-only.
    ``memory_store`` is consulted read-only (currently only used for
    its presence flag; raw symbol-bearing recall would violate the
    Recall Protocol, so V7 does not perform direct queries by symbol).
    """

    now_ms: int
    active_policy_record: MemoryRecord | None = None
    memory_store: InMemoryExplicitMemoryStore | None = None
    replay_evidence_score: float | None = None


def _build_policy_input(
    opportunity: PaperOpportunity,
    *,
    environment: str = "shadow",
) -> FinancialPolicyInput:
    return FinancialPolicyInput(
        event_id=opportunity.opportunity_id,
        scope_id=opportunity.policy_scope_id or opportunity.scope_hash,
        environment=environment,  # type: ignore[arg-type]
        risk_score=opportunity.risk_score,
        confidence=opportunity.confidence,
        staleness_ms=opportunity.staleness_ms,
        latency_ms=opportunity.latency_ms,
        orderbook_age_ms=opportunity.latency_ms,
        spread_pct=opportunity.spread_score * 10.0,
        liquidity_score=opportunity.liquidity_score,
        bad_order=opportunity.kind is PaperOpportunityKind.BAD_ORDER_OBSERVATION,
        kill_switch_active=opportunity.kind is PaperOpportunityKind.KILL_SWITCH_OBSERVATION,
        provenance_missing=False,
        unknown_risk_score=0.1,
        source_event_refs=opportunity.source_event_refs,
    )


def evaluate_paper_opportunity(
    *,
    opportunity: PaperOpportunity,
    context: PaperCoPilotContext,
) -> PaperDecision:
    """Produce a deterministic shadow-only paper decision."""
    reasons: list[PaperDecisionReason] = []
    output: SystemOutput
    policy_record_ref: str | None = None
    replay_evidence_refs: tuple[str, ...] = ()
    memory_record_refs: tuple[str, ...] = ()

    # 1) Constitutional hard-stops first.
    if opportunity.kind is PaperOpportunityKind.KILL_SWITCH_OBSERVATION:
        reasons.append(PaperDecisionReason.KILL_SWITCH_OBSERVED)
        output = SystemOutput.BLOCK
    elif opportunity.kind is PaperOpportunityKind.BAD_ORDER_OBSERVATION:
        reasons.append(PaperDecisionReason.BAD_ORDER_OBSERVED)
        output = SystemOutput.BLOCK
    elif opportunity.risk_score >= _RISK_BLOCK_THRESHOLD:
        reasons.append(PaperDecisionReason.HIGH_RISK)
        output = SystemOutput.BLOCK
    elif opportunity.staleness_ms > _STALENESS_BLOCK_THRESHOLD_MS:
        reasons.append(PaperDecisionReason.STALE_DATA)
        output = SystemOutput.BLOCK
    else:
        output = SystemOutput.MONITOR

    # 2) Active policy may upgrade to BLOCK.
    if context.active_policy_record is not None and output is not SystemOutput.BLOCK:
        try:
            policy_eval = evaluate_financial_policy(
                policy_record=context.active_policy_record,
                policy_input=_build_policy_input(opportunity),
                now_ms=context.now_ms,
            )
            policy_record_ref = context.active_policy_record.record_id
            if policy_eval.output is SystemOutput.BLOCK:
                reasons.append(PaperDecisionReason.POLICY_BLOCK)
                output = SystemOutput.BLOCK
        except ValueError:
            # Policy expired / stale / not ACTIVE — treat as advisory
            # absent; conservative path keeps the prior output.
            policy_record_ref = None

    # 3) Memory echo / recall hook.  V7 does not perform raw-symbol
    # recall (Recall Protocol restriction); we use the opportunity's
    # pre-computed memory_echo_score as a softer signal.
    if (
        output is not SystemOutput.BLOCK
        and opportunity.memory_echo_score is not None
        and opportunity.memory_echo_score >= _MEMORY_ECHO_RECALL_THRESHOLD
    ):
        output = SystemOutput.NEED_RECALL
        reasons.append(PaperDecisionReason.NEEDS_RECALL)

    # 4) Replay uncertainty hint.
    if output is SystemOutput.MONITOR:
        score = context.replay_evidence_score
        if score is None:
            score = opportunity.replay_evidence_score
        if score is not None and score < _REPLAY_UNCERTAIN_THRESHOLD:
            reasons.append(PaperDecisionReason.REPLAY_UNCERTAIN)

    # 5) Confidence floor downgrades.
    if output is SystemOutput.MONITOR and opportunity.confidence < _CONFIDENCE_WAIT_THRESHOLD:
        reasons = [PaperDecisionReason.INSUFFICIENT_CONFIDENCE]
        output = SystemOutput.WAIT

    # 6) Staleness MONITOR softening (we only reached here if staleness
    # is not extreme but still above the monitor threshold).
    if (
        output is SystemOutput.MONITOR
        and opportunity.staleness_ms > _STALENESS_MONITOR_THRESHOLD_MS
        and PaperDecisionReason.MONITOR_ONLY not in reasons
    ):
        reasons.append(PaperDecisionReason.MONITOR_ONLY)

    # 7) Default reason if MONITOR with no diagnostic reason set.
    if output is SystemOutput.MONITOR and not reasons:
        reasons.append(PaperDecisionReason.MONITOR_ONLY)

    # 8) Conservative WAIT fallback for very low magnitude + no signal.
    if (
        output is SystemOutput.MONITOR
        and opportunity.magnitude_score < 0.05
        and opportunity.risk_score < 0.1
    ):
        output = SystemOutput.NO_ACTION
        reasons = [PaperDecisionReason.NO_ACTION_NEEDED]

    return PaperDecision(
        decision_id=f"paper-dec-{opportunity.opportunity_id}",
        opportunity_id=opportunity.opportunity_id,
        output=output,
        reasons=tuple(reasons),
        confidence=opportunity.confidence,
        policy_record_ref=policy_record_ref,
        memory_record_refs=memory_record_refs,
        replay_evidence_refs=replay_evidence_refs,
        created_at_ms=context.now_ms,
    )
