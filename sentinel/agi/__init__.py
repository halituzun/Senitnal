"""V10 — Financial AGI v1 package.

Synthesises V2-V9 subsystem signals into a unified Financial AGI v1
evaluation frame.  Sentinel remains a closed-output advisory system;
the five execution safety flags are permanently ``Literal[False]``.
"""

from sentinel.agi.audit import (
    emit_financial_agi_readiness_recorded,
    emit_financial_agi_v1_evaluated,
)
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
    EvidenceWindow,
    EvidenceWindowKind,
    evaluate_evidence_gate,
)
from sentinel.agi.live_impact_guard import (
    LiveImpactGuardInput,
    LiveImpactGuardResult,
    evaluate_live_impact_guard,
)
from sentinel.agi.orchestrator import (
    FinancialAGIInputBundle,
    FinancialAGIOutputBundle,
    evaluate_financial_agi_v1,
)
from sentinel.agi.readiness_report import (
    FinancialAGIReadinessReport,
    generate_financial_agi_readiness_report,
)
from sentinel.agi.state import (
    FinancialAGIActivationState,
    FinancialAGICapabilityMap,
    FinancialAGIPhase,
    FinancialAGIState,
)

__all__ = [
    "EvidenceGateDecision",
    "EvidenceGateInput",
    "EvidenceGateResult",
    "EvidenceWindow",
    "EvidenceWindowKind",
    "FinancialAGIActivationState",
    "FinancialAGICapabilityMap",
    "FinancialAGIInputBundle",
    "FinancialAGIOutputBundle",
    "FinancialAGIPhase",
    "FinancialAGIReadinessReport",
    "FinancialAGIState",
    "GovernanceConsensusDecision",
    "GovernanceConsensusResult",
    "GovernanceSignal",
    "GovernanceSignalSource",
    "LiveImpactGuardInput",
    "LiveImpactGuardResult",
    "compute_governance_consensus",
    "emit_financial_agi_readiness_recorded",
    "emit_financial_agi_v1_evaluated",
    "evaluate_evidence_gate",
    "evaluate_financial_agi_v1",
    "evaluate_live_impact_guard",
    "generate_financial_agi_readiness_report",
]
