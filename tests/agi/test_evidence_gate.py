"""V10 — Evidence gate tests."""

from __future__ import annotations

import pytest
from sentinel.agi.evidence_gate import (
    EvidenceGateDecision,
    EvidenceGateInput,
    EvidenceWindow,
    EvidenceWindowKind,
    evaluate_evidence_gate,
)

from tests.agi._fixtures import make_all_windows_satisfied


def _gate(windows: tuple[EvidenceWindow, ...]) -> EvidenceGateInput:
    return EvidenceGateInput(
        evaluation_id="ev-gate-1",
        windows=windows,
        evaluated_at_ms=1_700_000_000_000,
    )


class TestEvidenceGatePassGreen:
    def test_all_satisfied_passes_green(self) -> None:
        result = evaluate_evidence_gate(_gate(make_all_windows_satisfied()))
        assert result.decision is EvidenceGateDecision.PASS_GREEN

    def test_all_mandatory_present(self) -> None:
        result = evaluate_evidence_gate(_gate(make_all_windows_satisfied()))
        assert result.all_mandatory_present is True
        assert result.all_mandatory_satisfied is True

    def test_satisfied_windows_correct(self) -> None:
        result = evaluate_evidence_gate(_gate(make_all_windows_satisfied()))
        assert len(result.satisfied_windows) == 7
        assert len(result.missing_windows) == 0

    def test_has_90d_evidence_true(self) -> None:
        result = evaluate_evidence_gate(_gate(make_all_windows_satisfied()))
        assert result.has_90d_evidence is True

    def test_safety_flags_pinned(self) -> None:
        result = evaluate_evidence_gate(_gate(make_all_windows_satisfied()))
        assert result.direct_execution is False
        assert result.approved_action_intent_generation is False


class TestEvidenceGateMissing90d:
    def test_missing_limited_live_90d_blocked(self) -> None:
        windows = tuple(
            w
            for w in make_all_windows_satisfied()
            if w.kind is not EvidenceWindowKind.LIMITED_LIVE_90D
        )
        result = evaluate_evidence_gate(_gate(windows))
        assert result.decision is EvidenceGateDecision.INSUFFICIENT_EVIDENCE
        assert result.has_90d_evidence is False

    def test_missing_incident_free_90d_blocked(self) -> None:
        windows = tuple(
            w
            for w in make_all_windows_satisfied()
            if w.kind is not EvidenceWindowKind.INCIDENT_FREE_90D
        )
        result = evaluate_evidence_gate(_gate(windows))
        assert result.decision is EvidenceGateDecision.INSUFFICIENT_EVIDENCE
        assert result.has_90d_evidence is False

    def test_missing_both_90d_blocked(self) -> None:
        windows = tuple(
            w
            for w in make_all_windows_satisfied()
            if w.kind
            not in (
                EvidenceWindowKind.LIMITED_LIVE_90D,
                EvidenceWindowKind.INCIDENT_FREE_90D,
            )
        )
        result = evaluate_evidence_gate(_gate(windows))
        assert result.decision is EvidenceGateDecision.INSUFFICIENT_EVIDENCE

    def test_missing_90d_blocked_reason_nonempty(self) -> None:
        windows = tuple(
            w
            for w in make_all_windows_satisfied()
            if w.kind is not EvidenceWindowKind.LIMITED_LIVE_90D
        )
        result = evaluate_evidence_gate(_gate(windows))
        assert "limited_live_90d" in result.blocked_reason


class TestEvidenceGateMissingNon90d:
    def test_missing_shadow_30d_insufficient(self) -> None:
        windows = tuple(
            w for w in make_all_windows_satisfied() if w.kind is not EvidenceWindowKind.SHADOW_30D
        )
        result = evaluate_evidence_gate(_gate(windows))
        assert result.decision is EvidenceGateDecision.INSUFFICIENT_EVIDENCE

    def test_missing_window_in_missing_list(self) -> None:
        windows = tuple(
            w for w in make_all_windows_satisfied() if w.kind is not EvidenceWindowKind.PAPER_30D
        )
        result = evaluate_evidence_gate(_gate(windows))
        assert EvidenceWindowKind.PAPER_30D in result.missing_windows


class TestEvidenceGateBlocked:
    def test_unsatisfied_window_blocked(self) -> None:
        windows = tuple(
            EvidenceWindow(kind=k, satisfied=False, days_observed=10) for k in EvidenceWindowKind
        )
        result = evaluate_evidence_gate(_gate(windows))
        assert result.decision is EvidenceGateDecision.BLOCKED

    def test_partial_unsatisfied(self) -> None:
        windows = list(make_all_windows_satisfied())
        # Replace shadow_30d with unsatisfied version.
        windows = [
            EvidenceWindow(kind=w.kind, satisfied=False, days_observed=0)
            if w.kind is EvidenceWindowKind.SHADOW_30D
            else w
            for w in windows
        ]
        result = evaluate_evidence_gate(_gate(tuple(windows)))
        assert result.decision is EvidenceGateDecision.BLOCKED
        assert EvidenceWindowKind.SHADOW_30D in result.failed_windows


class TestEvidenceGateEmpty:
    def test_no_windows_insufficient_evidence(self) -> None:
        result = evaluate_evidence_gate(_gate(()))
        assert result.decision is EvidenceGateDecision.INSUFFICIENT_EVIDENCE
        assert result.has_90d_evidence is False


class TestEvidenceGateDuplicateKinds:
    def test_duplicate_kind_rejected(self) -> None:
        with pytest.raises((ValueError, TypeError)):
            EvidenceGateInput(
                evaluation_id="dup",
                windows=(
                    EvidenceWindow(
                        kind=EvidenceWindowKind.SHADOW_30D, satisfied=True, days_observed=35
                    ),
                    EvidenceWindow(
                        kind=EvidenceWindowKind.SHADOW_30D, satisfied=True, days_observed=35
                    ),
                ),
                evaluated_at_ms=1_000,
            )
