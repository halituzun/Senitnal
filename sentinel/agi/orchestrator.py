"""V10 — Financial AGI v1 orchestrator.

Wires the V2-V9 subsystem signals through the evidence gate,
governance consensus, and live impact guard to produce a final
``FinancialAGIOutputBundle``.

Constitutional discipline:
    - No live order generation.
    - No action-intent objects generated.
    - No Gel.Al DB write.
    - Five capability-map safety flags remain ``Literal[False]``.
    - Evidence gate missing 90d window → activation blocked.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sentinel.agi.consensus import (
    GovernanceConsensusDecision,
    GovernanceConsensusResult,
    GovernanceSignal,
    GovernanceSignalSource,
    compute_governance_consensus,
)
from sentinel.agi.evidence_gate import (
    EvidenceGateDecision,
    EvidenceGateInput,
    EvidenceGateResult,
    evaluate_evidence_gate,
)
from sentinel.agi.live_impact_guard import (
    LiveImpactGuardInput,
    LiveImpactGuardResult,
    evaluate_live_impact_guard,
)
from sentinel.agi.state import (
    FinancialAGIActivationState,
    FinancialAGICapabilityMap,
    FinancialAGIPhase,
    FinancialAGIState,
)
from sentinel.canary.veto import CanaryVetoDecision, VetoDecisionKind
from sentinel.governance.decision import GovernanceDecisionKind  # noqa: TC001
from sentinel.governance.guard import GovernanceGuardContext  # noqa: TC001
from sentinel.paper.decision import PaperDecision  # noqa: TC001
from sentinel.policy.evaluator import (
    FinancialPolicyEvaluation,  # noqa: TC001
)
from sentinel.runtime.output import SystemOutput, assert_no_forbidden_literal
from sentinel.types.neural_seed import ProvenanceRef  # noqa: TC001


@dataclass(frozen=True, slots=True)
class FinancialAGIInputBundle:
    """All subsystem inputs for one AGI v1 evaluation cycle."""

    bundle_id: str
    now_ms: int
    provenance: ProvenanceRef
    evidence_gate_input: EvidenceGateInput
    governance_context: GovernanceGuardContext
    live_governance_decision_kind: GovernanceDecisionKind | None
    policy_evaluation: FinancialPolicyEvaluation | None = None
    paper_decision: PaperDecision | None = None
    canary_decision: CanaryVetoDecision | None = None
    notes: str = ""


@dataclass(frozen=True, slots=True)
class FinancialAGIOutputBundle:
    """Aggregated output of one Financial AGI v1 evaluation cycle."""

    bundle_id: str
    agi_state: FinancialAGIState
    evidence_gate_result: EvidenceGateResult
    consensus_result: GovernanceConsensusResult
    live_impact_guard_result: LiveImpactGuardResult
    final_output: SystemOutput
    activation_state: FinancialAGIActivationState
    creates_action: bool = field(default=False)
    writes_external: bool = field(default=False)
    approves_trade: bool = field(default=False)
    no_veto_is_approval: bool = field(default=False)
    monitor_is_approval: bool = field(default=False)
    notes: str = ""


def _build_signals(bundle: FinancialAGIInputBundle) -> tuple[GovernanceSignal, ...]:
    signals: list[GovernanceSignal] = []

    if bundle.policy_evaluation is not None:
        signals.append(
            GovernanceSignal(
                source=GovernanceSignalSource.POLICY,
                output=bundle.policy_evaluation.output,
                signal_ref=getattr(bundle.policy_evaluation, "evaluation_id", ""),
            )
        )

    if bundle.paper_decision is not None:
        signals.append(
            GovernanceSignal(
                source=GovernanceSignalSource.PAPER,
                output=bundle.paper_decision.output,
                signal_ref=bundle.paper_decision.decision_id,
            )
        )

    if bundle.canary_decision is not None:
        canary_output = (
            SystemOutput.BLOCK
            if bundle.canary_decision.decision is VetoDecisionKind.VETO
            else SystemOutput.NO_ACTION
        )
        signals.append(
            GovernanceSignal(
                source=GovernanceSignalSource.CANARY,
                output=canary_output,
                signal_ref=bundle.canary_decision.decision_id,
            )
        )

    return tuple(signals)


def evaluate_financial_agi_v1(
    bundle: FinancialAGIInputBundle,
) -> FinancialAGIOutputBundle:
    """Orchestrate a full Financial AGI v1 evaluation cycle.

    Steps:
    1. Evaluate evidence gate.
    2. Compute governance consensus.
    3. Run live impact guard.
    4. Derive activation state.
    5. Return output bundle (no external writes, no actions).
    """
    # Step 1: Evidence gate.
    gate_result = evaluate_evidence_gate(bundle.evidence_gate_input)

    # Step 2: Governance consensus.
    signals = _build_signals(bundle)
    consensus = compute_governance_consensus(
        consensus_id=f"cons-{bundle.bundle_id}",
        signals=signals,
        live_governance_decision=bundle.live_governance_decision_kind,
    )

    # Step 3: Live impact guard.
    guard_input = LiveImpactGuardInput(
        guard_id=f"guard-{bundle.bundle_id}",
        consensus_result=consensus,
        human_approval_present=bundle.governance_context.human_approval is not None,
        kill_switch_observed=bundle.governance_context.kill_switch_observed,
        hash_chain_valid=bundle.governance_context.hash_chain_valid,
        now_ms=bundle.now_ms,
    )
    guard_result = evaluate_live_impact_guard(guard_input)

    # Step 4: Derive activation state.
    activation_state = _derive_activation_state(gate_result, consensus)

    # Step 5: AGI state snapshot.
    agi_state = FinancialAGIState(
        state_id=f"agi-state-{bundle.bundle_id}",
        phase=FinancialAGIPhase.AGI_V1,
        activation_state=activation_state,
        capability_map=FinancialAGICapabilityMap(),
        created_at_ms=bundle.now_ms,
        evidence_evaluated_at_ms=bundle.evidence_gate_input.evaluated_at_ms,
    )

    final_output = guard_result.effective_output
    reason_text = (
        f"agi_v1: gate={gate_result.decision.value} "
        f"consensus={consensus.decision.value} "
        f"output={final_output.value} "
        f"activation={activation_state.value}"
    )
    assert_no_forbidden_literal(reason_text)

    return FinancialAGIOutputBundle(
        bundle_id=bundle.bundle_id,
        agi_state=agi_state,
        evidence_gate_result=gate_result,
        consensus_result=consensus,
        live_impact_guard_result=guard_result,
        final_output=final_output,
        activation_state=activation_state,
        creates_action=False,
        writes_external=False,
        approves_trade=False,
        no_veto_is_approval=False,
        monitor_is_approval=False,
        notes=reason_text,
    )


def _derive_activation_state(
    gate: EvidenceGateResult,
    consensus: GovernanceConsensusResult,
) -> FinancialAGIActivationState:
    """Derive the activation state from gate and consensus results."""
    if not gate.has_90d_evidence or gate.decision is EvidenceGateDecision.INSUFFICIENT_EVIDENCE:
        return FinancialAGIActivationState.RELEASED_BUT_NOT_ACTIVATED

    if gate.decision is EvidenceGateDecision.BLOCKED:
        return FinancialAGIActivationState.PRODUCTION_BLOCKED

    if consensus.decision is GovernanceConsensusDecision.CONSENSUS_INSUFFICIENT_SIGNALS:
        return FinancialAGIActivationState.PRODUCTION_BLOCKED

    if consensus.decision is GovernanceConsensusDecision.CONSENSUS_BLOCK:
        return FinancialAGIActivationState.PRODUCTION_BLOCKED

    if gate.decision is EvidenceGateDecision.PASS_GREEN:
        return FinancialAGIActivationState.AGI_V1_READY

    return FinancialAGIActivationState.READINESS_REVIEW


__all__ = [
    "FinancialAGIInputBundle",
    "FinancialAGIOutputBundle",
    "evaluate_financial_agi_v1",
]
