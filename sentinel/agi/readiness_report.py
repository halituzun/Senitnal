"""V10 — Financial AGI v1 readiness report generator.

Produces a human-readable + machine-parseable readiness report from
an evaluated ``FinancialAGIOutputBundle``.

Status values:
    GREEN                — all windows satisfied, consensus no-block
    PASS-                — conditional pass (pass_conditional gate)
    FAIL                 — blocked by gate or consensus
    RELEASED_NOT_ACTIVATED — 90-day evidence missing; not activated
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from sentinel.agi.consensus import GovernanceConsensusDecision
from sentinel.agi.evidence_gate import EvidenceGateDecision, EvidenceWindowKind
from sentinel.agi.state import FinancialAGIActivationState  # noqa: TC001
from sentinel.runtime.output import SystemOutput  # noqa: TC001

if TYPE_CHECKING:
    from sentinel.agi.orchestrator import FinancialAGIOutputBundle

_STATUS_RELEASED_NOT_ACTIVATED = "RELEASED_NOT_ACTIVATED"
_STATUS_GREEN = "GREEN"
_STATUS_PASS_MINUS = "PASS-"
_STATUS_FAIL = "FAIL"


class FinancialAGIReadinessReport(BaseModel, frozen=True, extra="forbid"):
    """Readiness report for a Financial AGI v1 evaluation cycle."""

    report_id: str = Field(min_length=1)
    status: str
    activation_state: FinancialAGIActivationState
    gate_decision: EvidenceGateDecision
    consensus_decision: GovernanceConsensusDecision
    final_output: SystemOutput
    has_90d_evidence: bool
    all_mandatory_satisfied: bool
    satisfied_windows: tuple[EvidenceWindowKind, ...]
    missing_windows: tuple[EvidenceWindowKind, ...]
    failed_windows: tuple[EvidenceWindowKind, ...]
    block_sources: tuple[str, ...]
    allowed_to_influence_live: bool
    notes: str = ""


def generate_financial_agi_readiness_report(
    *,
    report_id: str,
    output_bundle: FinancialAGIOutputBundle,
) -> FinancialAGIReadinessReport:
    """Generate a readiness report from an evaluated output bundle.

    Status logic:
    - ``RELEASED_NOT_ACTIVATED`` if 90-day evidence is missing.
    - ``FAIL`` if gate is blocked or consensus is block/insufficient.
    - ``PASS-`` if gate is pass_conditional.
    - ``GREEN`` if gate is pass_green and consensus is no-block.
    """
    gate = output_bundle.evidence_gate_result
    consensus = output_bundle.consensus_result
    guard = output_bundle.live_impact_guard_result

    if not gate.has_90d_evidence or gate.decision is EvidenceGateDecision.INSUFFICIENT_EVIDENCE:
        status = _STATUS_RELEASED_NOT_ACTIVATED
    elif gate.decision is EvidenceGateDecision.BLOCKED or consensus.decision in (
        GovernanceConsensusDecision.CONSENSUS_BLOCK,
        GovernanceConsensusDecision.CONSENSUS_INSUFFICIENT_SIGNALS,
    ):
        status = _STATUS_FAIL
    elif gate.decision is EvidenceGateDecision.PASS_CONDITIONAL:
        status = _STATUS_PASS_MINUS
    else:
        status = _STATUS_GREEN

    block_sources = tuple(s.value for s in consensus.block_sources)

    return FinancialAGIReadinessReport(
        report_id=report_id,
        status=status,
        activation_state=output_bundle.activation_state,
        gate_decision=gate.decision,
        consensus_decision=consensus.decision,
        final_output=output_bundle.final_output,
        has_90d_evidence=gate.has_90d_evidence,
        all_mandatory_satisfied=gate.all_mandatory_satisfied,
        satisfied_windows=gate.satisfied_windows,
        missing_windows=gate.missing_windows,
        failed_windows=gate.failed_windows,
        block_sources=block_sources,
        allowed_to_influence_live=guard.allowed_to_influence_live,
        notes=output_bundle.notes,
    )


__all__ = [
    "FinancialAGIReadinessReport",
    "generate_financial_agi_readiness_report",
]
