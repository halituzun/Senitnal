"""V10 — AGI orchestrator tests."""

from __future__ import annotations

from sentinel.agi.evidence_gate import (
    EvidenceGateDecision,
    EvidenceWindow,
    EvidenceWindowKind,
)
from sentinel.agi.orchestrator import evaluate_financial_agi_v1
from sentinel.agi.state import FinancialAGIActivationState
from sentinel.governance.decision import GovernanceDecisionKind
from sentinel.runtime.output import SystemOutput

from tests.agi._fixtures import make_all_windows_satisfied, make_bundle

_CLOSED = {
    SystemOutput.WAIT,
    SystemOutput.BLOCK,
    SystemOutput.MONITOR,
    SystemOutput.NEED_RECALL,
    SystemOutput.NO_ACTION,
}


class TestOrchestratorBasic:
    def test_all_satisfied_produces_valid_output(self) -> None:
        bundle = make_bundle()
        result = evaluate_financial_agi_v1(bundle)
        assert result.final_output in _CLOSED

    def test_capability_map_flags_pinned(self) -> None:
        bundle = make_bundle()
        result = evaluate_financial_agi_v1(bundle)
        cap = result.agi_state.capability_map
        assert cap.direct_execution is False
        assert cap.exchange_imports is False
        assert cap.llm_imports is False
        assert cap.gelal_write_path is False
        assert cap.approved_action_intent_generation is False

    def test_no_safety_violations(self) -> None:
        bundle = make_bundle()
        result = evaluate_financial_agi_v1(bundle)
        assert result.creates_action is False
        assert result.writes_external is False
        assert result.approves_trade is False
        assert result.no_veto_is_approval is False
        assert result.monitor_is_approval is False

    def test_bundle_id_propagated(self) -> None:
        bundle = make_bundle(bundle_id="my-bundle-99")
        result = evaluate_financial_agi_v1(bundle)
        assert result.bundle_id == "my-bundle-99"


class TestOrchestratorEvidenceGate:
    def test_missing_90d_produces_released_not_activated(self) -> None:
        windows = tuple(
            w
            for w in make_all_windows_satisfied()
            if w.kind is not EvidenceWindowKind.LIMITED_LIVE_90D
        )
        bundle = make_bundle(windows=windows)
        result = evaluate_financial_agi_v1(bundle)
        assert result.activation_state is FinancialAGIActivationState.RELEASED_BUT_NOT_ACTIVATED

    def test_all_windows_satisfied_agi_v1_ready_or_blocked(self) -> None:
        bundle = make_bundle()
        result = evaluate_financial_agi_v1(bundle)
        # Could be AGI_V1_READY or PRODUCTION_BLOCKED depending on governance.
        assert result.activation_state in (
            FinancialAGIActivationState.AGI_V1_READY,
            FinancialAGIActivationState.PRODUCTION_BLOCKED,
        )

    def test_unsatisfied_window_produces_blocked(self) -> None:
        windows = tuple(
            EvidenceWindow(kind=k, satisfied=False, days_observed=0) for k in EvidenceWindowKind
        )
        bundle = make_bundle(windows=windows)
        result = evaluate_financial_agi_v1(bundle)
        assert result.activation_state is FinancialAGIActivationState.PRODUCTION_BLOCKED


class TestOrchestratorGovernance:
    def test_block_live_candidate_produces_block_output(self) -> None:
        bundle = make_bundle(
            live_governance_decision_kind=GovernanceDecisionKind.BLOCK_LIVE_CANDIDATE
        )
        result = evaluate_financial_agi_v1(bundle)
        assert result.final_output is SystemOutput.BLOCK
        assert result.activation_state is FinancialAGIActivationState.PRODUCTION_BLOCKED

    def test_kill_switch_produces_block_output(self) -> None:
        bundle = make_bundle(kill_switch=True)
        result = evaluate_financial_agi_v1(bundle)
        assert result.final_output is SystemOutput.BLOCK

    def test_invalid_hash_chain_produces_block(self) -> None:
        bundle = make_bundle(hash_chain_valid=False)
        result = evaluate_financial_agi_v1(bundle)
        assert result.final_output is SystemOutput.BLOCK

    def test_no_action_with_good_evidence_produces_agi_v1_ready(self) -> None:
        bundle = make_bundle(live_governance_decision_kind=GovernanceDecisionKind.NO_ACTION)
        result = evaluate_financial_agi_v1(bundle)
        assert result.evidence_gate_result.decision is EvidenceGateDecision.PASS_GREEN
        assert result.activation_state is FinancialAGIActivationState.AGI_V1_READY


class TestOrchestratorLiveImpactGuard:
    def test_block_output_allows_live_influence(self) -> None:
        bundle = make_bundle(
            live_governance_decision_kind=GovernanceDecisionKind.BLOCK_LIVE_CANDIDATE
        )
        result = evaluate_financial_agi_v1(bundle)
        assert result.live_impact_guard_result.allowed_to_influence_live is True

    def test_no_action_disallows_live_influence(self) -> None:
        bundle = make_bundle(live_governance_decision_kind=GovernanceDecisionKind.NO_ACTION)
        result = evaluate_financial_agi_v1(bundle)
        assert result.live_impact_guard_result.allowed_to_influence_live is False

    def test_monitor_disallows_live_influence(self) -> None:
        bundle = make_bundle(live_governance_decision_kind=GovernanceDecisionKind.MONITOR_ONLY)
        result = evaluate_financial_agi_v1(bundle)
        assert result.live_impact_guard_result.allowed_to_influence_live is False

    def test_wait_disallows_live_influence(self) -> None:
        bundle = make_bundle(live_governance_decision_kind=GovernanceDecisionKind.WAIT_FOR_HUMAN)
        result = evaluate_financial_agi_v1(bundle)
        assert result.live_impact_guard_result.allowed_to_influence_live is False

    def test_need_recall_disallows_live_influence(self) -> None:
        bundle = make_bundle(live_governance_decision_kind=GovernanceDecisionKind.NEED_RECALL)
        result = evaluate_financial_agi_v1(bundle)
        assert result.live_impact_guard_result.allowed_to_influence_live is False
