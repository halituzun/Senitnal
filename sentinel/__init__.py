"""Sentinel — Financial AGI core.

Minimum Viable Brain (MVB) v0.1 — shipped.

Conceptual + numerics design phase **closed**:
    22 frozen draft documents (A-U + ATTENTION_WORKSPACE + M) +
    2 reviews (phase closure + implementation readiness) +
    1 build plan (`docs/build/0001-minimum-viable-brain-plan.md`).

Implementation phase **closed**:
    Phases 1-10 (Contracts as Code -> End-to-end Dry Simulation)
    + polish phase (audit wiring, property tests, CLI, public API,
    catalog-consistency guard) — see
    `docs/reviews/0004-mvp-build-closure-review.md` and
    `docs/reviews/0005-mvp-polish-closure-review.md`.

Constitutional MVB invariants (enforced by type boundary + CI
grep + invariant test suite):
    - No live action output. Output set: {WAIT, BLOCK, MONITOR, NEED_RECALL, NO_ACTION}.
    - No live exchange API integration.
    - No LLM integration (intent_relay capability disabled).
    - No M2 verified production (candidate-only writes in MVP).
    - No numerics runtime mutation (signed artifacts only).
    - No cross-instance / fork / migration paths (MVP single-instance).
    - No replay-driven memory update (replay engine disabled in MVP).
    - No silent action (every gate decision audited to M1).

Top-level package re-exports the curated public API (see __all__
below); deeper module paths remain available for explicit imports.

Quick start:
    >>> from sentinel import (
    ...     EchoAdapter, JsonlObserverLedger, run_dry_simulation,
    ... )
    >>> ledger = JsonlObserverLedger(path)
    >>> result = run_dry_simulation(
    ...     ledger=ledger,
    ...     adapter=EchoAdapter.default(),
    ...     observation_magnitude=0.8,
    ... )
    >>> result.output
    <SystemOutput.WAIT: 'WAIT'>
    >>> ledger.verify()
    True
"""

__version__ = "0.1.0"


# ---------------------------------------------------------------------------
# Public API — curated re-exports.
#
# Importing from `sentinel` directly is the supported integration surface
# for downstream callers; deeper paths (e.g. `sentinel.observer.ledger`)
# remain available but may be reorganized in later phases.
# ---------------------------------------------------------------------------

from sentinel.adapters.audit import (
    emit_manifest_status_changed,
    emit_neural_seed_attempt_revoke,
)
from sentinel.adapters.echo import EchoAdapter
from sentinel.adapters.local_jsonl_market import LocalJsonlMarketAdapter
from sentinel.adapters.market_observation import (
    MarketObservationEnvelope,
    SanitizedMarketProvenance,
    build_market_observation_audit_payload,
    sanitize_market_observation_to_event,
)
from sentinel.adapters.synthetic_market import SyntheticMarketAdapter
from sentinel.adapters.trust import (
    AdapterTrustRecord,
    TrustBand,
    compute_trust,
)
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
from sentinel.canary.candidate import (
    CanaryCandidateAction,
    CanaryCandidateSource,
    CanaryEnvironment,
)
from sentinel.canary.evaluator import CanaryVetoContext, evaluate_canary_veto
from sentinel.canary.limits import (
    CanaryDecisionWindowState,
    CanaryMicroLiveBounds,
)
from sentinel.canary.veto import (
    CanaryVetoDecision,
    VetoDecisionKind,
    VetoReason,
    VetoRequest,
)
from sentinel.constitution.invariants import (
    MVP_REQUIRED_INVARIANTS,
    InvariantCategory,
    InvariantDefinition,
    InvariantSeverity,
    assert_invariant,
    get_invariant,
    list_invariants,
)
from sentinel.constitution.violations import (
    ConstitutionalViolation,
    InvariantViolation,
    ViolationContext,
)
from sentinel.gates.deontic import (
    ApprovedActionIntent,
    BlockClass,
    DeonticDecision,
    DeonticOutcome,
    evaluate_action,
    evaluate_action_with_audit,
)
from sentinel.governance.approval import (
    HumanApprovalRecord,
    HumanApprovalStatus,
    is_human_approval_valid,
)
from sentinel.governance.decision import (
    GovernanceDecisionKind,
    GovernanceReason,
    LiveGovernanceDecision,
)
from sentinel.governance.guard import (
    GovernanceGuardContext,
    evaluate_governance_guard,
)
from sentinel.governance.request import (
    GovernanceRequestKind,
    LiveGovernanceRequest,
)
from sentinel.governance.scope import (
    GovernanceEnvironment,
    GovernanceScopeKind,
    LimitedLiveGovernanceScope,
)
from sentinel.integrations.gelal_jsonl import GelAlShadowJsonlAdapter
from sentinel.integrations.gelal_sanitizer import (
    build_gelal_shadow_audit_payload,
    sanitize_gelal_shadow_to_observation_event,
)
from sentinel.integrations.gelal_shadow import (
    GelAlShadowEnvelope,
    GelAlShadowEventType,
)
from sentinel.integrations.gelal_shadow_eval import (
    GelAlShadowEvaluationResult,
    evaluate_gelal_shadow_event,
)
from sentinel.intelligence.conviction import (
    ActionabilityBand,
    LiveConvictionInput,
    LiveConvictionResult,
    evaluate_live_conviction,
)
from sentinel.intelligence.fusion import (
    SignalFusionInput,
    SignalFusionResult,
    compute_signal_fusion,
)
from sentinel.intelligence.historical_backtest import (
    BacktestAggregate,
    aggregate_records,
)
from sentinel.intelligence.historical_similarity import (
    HistoricalSimilarityInput,
    HistoricalSimilarityResult,
    evaluate_historical_similarity,
)
from sentinel.intelligence.live_activation import (
    LiveActivationInput,
    LiveActivationResult,
    LiveActivationStatus,
    LiveBudgetMode,
    LiveCapitalModel,
    evaluate_live_activation,
)
from sentinel.intelligence.net_edge import (
    NetEdgeBreakdown,
    compute_net_edge,
    is_net_edge_actionable,
)
from sentinel.intelligence.reaction_memory import (
    InMemoryReactionMemoryStore,
    ReactionMemoryRecord,
    ReactionPattern,
    is_record_usable_for_live,
)
from sentinel.intelligence.reaction_taxonomy import (
    HistoricalEventFamily,
    MarketReactionMeasurement,
    ReactionWindow,
)
from sentinel.intelligence.schemas import (
    CommodityMacroSnapshot,
    GelAlMetricsObservation,
    MacroEventKind,
    MacroEventSnapshot,
    MarketMicrostructureSnapshot,
    MultiSourceObservation,
    NewsEventSnapshot,
    NewsFamily,
    SocialPlatform,
    SocialSignalSnapshot,
    SourceFamily,
    TechnicalIndicatorSnapshot,
)
from sentinel.memory.builder import build_candidate_financial_memory_record
from sentinel.memory.financial import (
    ExecutionQualityObservationPayload,
    LatencyPatternPayload,
    LiquidityConditionPayload,
    MarketRegimeObservationPayload,
    SpreadWindowObservationPayload,
)
from sentinel.memory.store import InMemoryExplicitMemoryStore
from sentinel.memory.write_path import (
    FinancialMemoryWriteResult,
    submit_financial_memory_candidate,
)
from sentinel.observer.ledger import JsonlObserverLedger
from sentinel.observer.permanence import EventPermanence
from sentinel.observer.ring_buffer import ObserverRingBuffer
from sentinel.observer.router import RoutingOutcome, route_observer_event
from sentinel.panel.adapter_hub import (
    AdapterHubStatus,
    AdapterSignalStatus,
    build_adapter_hub_status,
)
from sentinel.panel.credential_vault import (
    CredentialKind,
    CredentialReference,
    CredentialVaultConfig,
    is_credential_valid,
    list_expiring_soon,
)
from sentinel.panel.snapshot import (
    PanelSnapshot,
    PanelStrategyRow,
    build_panel_snapshot,
)
from sentinel.paper.copilot import PaperCoPilotContext, evaluate_paper_opportunity
from sentinel.paper.decision import (
    PaperCoPilotResult,
    PaperDecision,
    PaperDecisionReason,
)
from sentinel.paper.gelal_compare import (
    GelAlPaperComparison,
    compare_gelal_shadow_to_paper_decision,
)
from sentinel.paper.opportunity import (
    PaperOpportunity,
    PaperOpportunityKind,
    PaperOpportunitySource,
    build_paper_opportunity_from_gelal_shadow,
    build_paper_opportunity_from_market_observation,
)
from sentinel.paper.outcome import (
    PaperDecisionOutcomeComparison,
    PaperOutcome,
    PaperOutcomeKind,
    compare_paper_decision_to_outcome,
)
from sentinel.policy.evaluator import (
    FinancialPolicyEvaluation,
    FinancialPolicyInput,
    evaluate_financial_policy,
    resolve_policy_conflicts,
)
from sentinel.policy.financial import (
    FinancialDeonticPolicyArtifact,
    FinancialHardStopThresholds,
    FinancialPolicyAction,
    FinancialPolicyOperator,
    FinancialPolicyRule,
    FinancialPolicyScope,
    FinancialPolicySeverity,
)
from sentinel.policy.record_builder import build_deontic_policy_candidate_record
from sentinel.policy.store import InMemoryPolicyStore
from sentinel.policy.write_path import (
    FinancialPolicyWriteResult,
    submit_financial_policy_candidate,
)
from sentinel.production.execution_quality import (
    ExecutionQualityRecord,
    update_strategy_quality_from_record,
)
from sentinel.production.portfolio import (
    LiveProductionDecision,
    LiveProductionDecisionInput,
    StrategyAllocation,
    StrategyPortfolioConfig,
    evaluate_live_production_decision,
)
from sentinel.production.review import (
    DailyProductionReport,
    WeeklyProductionReport,
    build_daily_report,
    build_weekly_report,
)
from sentinel.production.strategy_lifecycle import (
    StrategyLifecycleState,
    transition_state,
)
from sentinel.recall.audit import (
    emit_recall_request,
    emit_recall_result_empty,
    emit_recall_trigger_rejected,
)
from sentinel.recall.financial import (
    FinancialRecallRequest,
    FinancialRecallScope,
    build_financial_recall_event,
    select_financial_recall_top_one,
)
from sentinel.replay.budget import (
    ReplayBudget,
    ReplayBudgetState,
    can_start_replay_session,
)
from sentinel.replay.counterfactual import (
    AblationKind,
    CounterfactualAblation,
    CounterfactualAblationResult,
)
from sentinel.replay.outcome_alignment import (
    OutcomeAlignmentEvidence,
    OutcomeRef,
)
from sentinel.replay.session import (
    ReplayEffectChannel,
    ReplayInputSnapshot,
    ReplayPurpose,
    ReplaySession,
    ReplaySessionStatus,
)
from sentinel.replay.survival import ReplaySurvivalEvidence
from sentinel.runtime.canary_veto import (
    CanaryVetoBatchResult,
    run_canary_veto_file,
)
from sentinel.runtime.dry_sim import DrySimResult, run_dry_simulation
from sentinel.runtime.financial_agi import (
    FinancialAGIBatchResult,
    run_financial_agi_file,
)
from sentinel.runtime.financial_memory_pipeline import (
    FinancialMemoryPipelineResult,
    run_financial_memory_pipeline,
)
from sentinel.runtime.gelal_shadow import (
    GelAlShadowBatchResult,
    run_gelal_shadow_file,
)
from sentinel.runtime.live_governance import (
    LiveGovernanceBatchResult,
    run_live_governance_file,
)
from sentinel.runtime.market_replay import (
    MarketReplayResult,
    run_market_jsonl_file,
    run_market_observations,
)
from sentinel.runtime.output import SystemOutput
from sentinel.runtime.paper_copilot import (
    PaperCoPilotBatchResult,
    run_paper_copilot_file,
)
from sentinel.runtime.replay_financial_pipeline import (
    ReplayFinancialPipelineResult,
    run_replay_financial_pipeline,
)
from sentinel.types.neural_seed import EventProfile, NeuralSeed, ProvenanceRef
from sentinel.types.observer import EventFamily, ObserverEvent
from sentinel.types.payload import PayloadSeed, PrimerPayload

__all__ = [
    "MVP_REQUIRED_INVARIANTS",
    "AblationKind",
    "ActionabilityBand",
    "AdapterHubStatus",
    "AdapterSignalStatus",
    "AdapterTrustRecord",
    "ApprovedActionIntent",
    "BacktestAggregate",
    "BlockClass",
    "CanaryCandidateAction",
    "CanaryCandidateSource",
    "CanaryDecisionWindowState",
    "CanaryEnvironment",
    "CanaryMicroLiveBounds",
    "CanaryVetoBatchResult",
    "CanaryVetoContext",
    "CanaryVetoDecision",
    "CommodityMacroSnapshot",
    "ConstitutionalViolation",
    "CounterfactualAblation",
    "CounterfactualAblationResult",
    "CredentialKind",
    "CredentialReference",
    "CredentialVaultConfig",
    "DailyProductionReport",
    "DeonticDecision",
    "DeonticOutcome",
    "DrySimResult",
    "EchoAdapter",
    "EventFamily",
    "EventPermanence",
    "EventProfile",
    "EvidenceGateDecision",
    "EvidenceGateInput",
    "EvidenceGateResult",
    "EvidenceWindow",
    "EvidenceWindowKind",
    "ExecutionQualityObservationPayload",
    "ExecutionQualityRecord",
    "FinancialAGIActivationState",
    "FinancialAGIBatchResult",
    "FinancialAGICapabilityMap",
    "FinancialAGIInputBundle",
    "FinancialAGIOutputBundle",
    "FinancialAGIPhase",
    "FinancialAGIReadinessReport",
    "FinancialAGIState",
    "FinancialDeonticPolicyArtifact",
    "FinancialHardStopThresholds",
    "FinancialMemoryPipelineResult",
    "FinancialMemoryWriteResult",
    "FinancialPolicyAction",
    "FinancialPolicyEvaluation",
    "FinancialPolicyInput",
    "FinancialPolicyOperator",
    "FinancialPolicyRule",
    "FinancialPolicyScope",
    "FinancialPolicySeverity",
    "FinancialPolicyWriteResult",
    "FinancialRecallRequest",
    "FinancialRecallScope",
    "GelAlMetricsObservation",
    "GelAlPaperComparison",
    "GelAlShadowBatchResult",
    "GelAlShadowEnvelope",
    "GelAlShadowEvaluationResult",
    "GelAlShadowEventType",
    "GelAlShadowJsonlAdapter",
    "GovernanceConsensusDecision",
    "GovernanceConsensusResult",
    "GovernanceDecisionKind",
    "GovernanceEnvironment",
    "GovernanceGuardContext",
    "GovernanceReason",
    "GovernanceRequestKind",
    "GovernanceScopeKind",
    "GovernanceSignal",
    "GovernanceSignalSource",
    "HistoricalEventFamily",
    "HistoricalSimilarityInput",
    "HistoricalSimilarityResult",
    "HumanApprovalRecord",
    "HumanApprovalStatus",
    "InMemoryExplicitMemoryStore",
    "InMemoryPolicyStore",
    "InMemoryReactionMemoryStore",
    "InvariantCategory",
    "InvariantDefinition",
    "InvariantSeverity",
    "InvariantViolation",
    "JsonlObserverLedger",
    "LatencyPatternPayload",
    "LimitedLiveGovernanceScope",
    "LiquidityConditionPayload",
    "LiveActivationInput",
    "LiveActivationResult",
    "LiveActivationStatus",
    "LiveBudgetMode",
    "LiveCapitalModel",
    "LiveConvictionInput",
    "LiveConvictionResult",
    "LiveGovernanceBatchResult",
    "LiveGovernanceDecision",
    "LiveGovernanceRequest",
    "LiveImpactGuardInput",
    "LiveImpactGuardResult",
    "LiveProductionDecision",
    "LiveProductionDecisionInput",
    "LocalJsonlMarketAdapter",
    "MacroEventKind",
    "MacroEventSnapshot",
    "MarketMicrostructureSnapshot",
    "MarketObservationEnvelope",
    "MarketReactionMeasurement",
    "MarketRegimeObservationPayload",
    "MarketReplayResult",
    "MultiSourceObservation",
    "NetEdgeBreakdown",
    "NeuralSeed",
    "NewsEventSnapshot",
    "NewsFamily",
    "ObserverEvent",
    "ObserverRingBuffer",
    "OutcomeAlignmentEvidence",
    "OutcomeRef",
    "PanelSnapshot",
    "PanelStrategyRow",
    "PaperCoPilotBatchResult",
    "PaperCoPilotContext",
    "PaperCoPilotResult",
    "PaperDecision",
    "PaperDecisionOutcomeComparison",
    "PaperDecisionReason",
    "PaperOpportunity",
    "PaperOpportunityKind",
    "PaperOpportunitySource",
    "PaperOutcome",
    "PaperOutcomeKind",
    "PayloadSeed",
    "PrimerPayload",
    "ProvenanceRef",
    "ReactionMemoryRecord",
    "ReactionPattern",
    "ReactionWindow",
    "ReplayBudget",
    "ReplayBudgetState",
    "ReplayEffectChannel",
    "ReplayFinancialPipelineResult",
    "ReplayInputSnapshot",
    "ReplayPurpose",
    "ReplaySession",
    "ReplaySessionStatus",
    "ReplaySurvivalEvidence",
    "RoutingOutcome",
    "SanitizedMarketProvenance",
    "SignalFusionInput",
    "SignalFusionResult",
    "SocialPlatform",
    "SocialSignalSnapshot",
    "SourceFamily",
    "SpreadWindowObservationPayload",
    "StrategyAllocation",
    "StrategyLifecycleState",
    "StrategyPortfolioConfig",
    "SyntheticMarketAdapter",
    "SystemOutput",
    "TechnicalIndicatorSnapshot",
    "TrustBand",
    "VetoDecisionKind",
    "VetoReason",
    "VetoRequest",
    "ViolationContext",
    "WeeklyProductionReport",
    "__version__",
    "aggregate_records",
    "assert_invariant",
    "build_adapter_hub_status",
    "build_candidate_financial_memory_record",
    "build_daily_report",
    "build_deontic_policy_candidate_record",
    "build_financial_recall_event",
    "build_gelal_shadow_audit_payload",
    "build_market_observation_audit_payload",
    "build_panel_snapshot",
    "build_paper_opportunity_from_gelal_shadow",
    "build_paper_opportunity_from_market_observation",
    "build_weekly_report",
    "can_start_replay_session",
    "compare_gelal_shadow_to_paper_decision",
    "compare_paper_decision_to_outcome",
    "compute_governance_consensus",
    "compute_net_edge",
    "compute_signal_fusion",
    "compute_trust",
    "emit_financial_agi_readiness_recorded",
    "emit_financial_agi_v1_evaluated",
    "emit_manifest_status_changed",
    "emit_neural_seed_attempt_revoke",
    "emit_recall_request",
    "emit_recall_result_empty",
    "emit_recall_trigger_rejected",
    "evaluate_action",
    "evaluate_action_with_audit",
    "evaluate_canary_veto",
    "evaluate_evidence_gate",
    "evaluate_financial_agi_v1",
    "evaluate_financial_policy",
    "evaluate_gelal_shadow_event",
    "evaluate_governance_guard",
    "evaluate_historical_similarity",
    "evaluate_live_activation",
    "evaluate_live_conviction",
    "evaluate_live_impact_guard",
    "evaluate_live_production_decision",
    "evaluate_paper_opportunity",
    "generate_financial_agi_readiness_report",
    "get_invariant",
    "is_credential_valid",
    "is_human_approval_valid",
    "is_net_edge_actionable",
    "is_record_usable_for_live",
    "list_expiring_soon",
    "list_invariants",
    "resolve_policy_conflicts",
    "route_observer_event",
    "run_canary_veto_file",
    "run_dry_simulation",
    "run_financial_agi_file",
    "run_financial_memory_pipeline",
    "run_gelal_shadow_file",
    "run_live_governance_file",
    "run_market_jsonl_file",
    "run_market_observations",
    "run_paper_copilot_file",
    "run_replay_financial_pipeline",
    "sanitize_gelal_shadow_to_observation_event",
    "sanitize_market_observation_to_event",
    "select_financial_recall_top_one",
    "submit_financial_memory_candidate",
    "submit_financial_policy_candidate",
    "transition_state",
    "update_strategy_quality_from_record",
]
