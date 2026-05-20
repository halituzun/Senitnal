"""V10 — Readiness report generator tests."""

from __future__ import annotations

from sentinel.agi.evidence_gate import (
    EvidenceWindow,
    EvidenceWindowKind,
)
from sentinel.agi.orchestrator import evaluate_financial_agi_v1
from sentinel.agi.readiness_report import generate_financial_agi_readiness_report
from sentinel.agi.state import FinancialAGIActivationState
from sentinel.governance.decision import GovernanceDecisionKind

from tests.agi._fixtures import make_all_windows_satisfied, make_bundle


class TestReadinessReportGreen:
    def test_all_satisfied_no_block_is_green(self) -> None:
        bundle = make_bundle(live_governance_decision_kind=GovernanceDecisionKind.NO_ACTION)
        output = evaluate_financial_agi_v1(bundle)
        report = generate_financial_agi_readiness_report(
            report_id="r-green",
            output_bundle=output,
        )
        assert report.status == "GREEN"
        assert report.activation_state is FinancialAGIActivationState.AGI_V1_READY
        assert report.has_90d_evidence is True
        assert report.all_mandatory_satisfied is True

    def test_green_report_id_propagated(self) -> None:
        bundle = make_bundle(live_governance_decision_kind=GovernanceDecisionKind.NO_ACTION)
        output = evaluate_financial_agi_v1(bundle)
        report = generate_financial_agi_readiness_report(
            report_id="my-rpt-99",
            output_bundle=output,
        )
        assert report.report_id == "my-rpt-99"


class TestReadinessReportFail:
    def test_missing_90d_is_released_not_activated(self) -> None:
        windows = tuple(
            w
            for w in make_all_windows_satisfied()
            if w.kind is not EvidenceWindowKind.LIMITED_LIVE_90D
        )
        bundle = make_bundle(windows=windows)
        output = evaluate_financial_agi_v1(bundle)
        report = generate_financial_agi_readiness_report(
            report_id="r-rnl",
            output_bundle=output,
        )
        assert report.status == "RELEASED_NOT_ACTIVATED"
        assert report.has_90d_evidence is False

    def test_block_governance_is_fail(self) -> None:
        bundle = make_bundle(
            live_governance_decision_kind=GovernanceDecisionKind.BLOCK_LIVE_CANDIDATE
        )
        output = evaluate_financial_agi_v1(bundle)
        report = generate_financial_agi_readiness_report(
            report_id="r-fail",
            output_bundle=output,
        )
        assert report.status == "FAIL"
        assert report.activation_state is FinancialAGIActivationState.PRODUCTION_BLOCKED

    def test_unsatisfied_evidence_is_fail(self) -> None:
        windows = tuple(
            EvidenceWindow(kind=k, satisfied=False, days_observed=0) for k in EvidenceWindowKind
        )
        bundle = make_bundle(windows=windows)
        output = evaluate_financial_agi_v1(bundle)
        report = generate_financial_agi_readiness_report(
            report_id="r-fail2",
            output_bundle=output,
        )
        assert report.status == "FAIL"

    def test_missing_signal_is_fail(self) -> None:
        # Directly pass None live_governance_decision_kind to simulate missing signal.
        from sentinel.agi.orchestrator import FinancialAGIInputBundle
        from sentinel.types.neural_seed import ProvenanceRef

        from tests.agi._fixtures import make_ctx, make_evidence_gate_input

        ctx = make_ctx()
        bundle = FinancialAGIInputBundle(
            bundle_id="bundle-none",
            now_ms=1_700_000_001_000,
            provenance=ProvenanceRef(source_event_id="no-sig"),
            evidence_gate_input=make_evidence_gate_input(),
            governance_context=ctx,
            live_governance_decision_kind=None,
        )
        output = evaluate_financial_agi_v1(bundle)
        report = generate_financial_agi_readiness_report(
            report_id="r-insuf",
            output_bundle=output,
        )
        assert report.status == "FAIL"


class TestReadinessReportLiveInfluence:
    def test_block_allows_live_influence(self) -> None:
        bundle = make_bundle(
            live_governance_decision_kind=GovernanceDecisionKind.BLOCK_LIVE_CANDIDATE
        )
        output = evaluate_financial_agi_v1(bundle)
        report = generate_financial_agi_readiness_report(
            report_id="r-inf",
            output_bundle=output,
        )
        assert report.allowed_to_influence_live is True

    def test_no_action_does_not_allow_live_influence(self) -> None:
        bundle = make_bundle(live_governance_decision_kind=GovernanceDecisionKind.NO_ACTION)
        output = evaluate_financial_agi_v1(bundle)
        report = generate_financial_agi_readiness_report(
            report_id="r-no-inf",
            output_bundle=output,
        )
        assert report.allowed_to_influence_live is False


class TestReadinessReportWindowSummary:
    def test_satisfied_windows_in_report(self) -> None:
        bundle = make_bundle(live_governance_decision_kind=GovernanceDecisionKind.NO_ACTION)
        output = evaluate_financial_agi_v1(bundle)
        report = generate_financial_agi_readiness_report(
            report_id="r-win",
            output_bundle=output,
        )
        assert len(report.satisfied_windows) == 7
        assert len(report.missing_windows) == 0

    def test_missing_windows_in_report(self) -> None:
        windows = tuple(
            w for w in make_all_windows_satisfied() if w.kind is not EvidenceWindowKind.SHADOW_30D
        )
        bundle = make_bundle(windows=windows)
        output = evaluate_financial_agi_v1(bundle)
        report = generate_financial_agi_readiness_report(
            report_id="r-missing",
            output_bundle=output,
        )
        assert EvidenceWindowKind.SHADOW_30D in report.missing_windows
