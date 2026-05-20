"""V10 — Live impact guard tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sentinel.agi.consensus import (
    GovernanceConsensusResult,
    compute_governance_consensus,
)
from sentinel.agi.live_impact_guard import (
    LiveImpactGuardInput,
    LiveImpactGuardResult,
    evaluate_live_impact_guard,
)
from sentinel.governance.decision import GovernanceDecisionKind
from sentinel.runtime.output import SystemOutput


def _block_consensus() -> GovernanceConsensusResult:
    return compute_governance_consensus(
        consensus_id="cons-block",
        signals=(),
        live_governance_decision=GovernanceDecisionKind.BLOCK_LIVE_CANDIDATE,
    )


def _no_action_consensus() -> GovernanceConsensusResult:
    return compute_governance_consensus(
        consensus_id="cons-no-action",
        signals=(),
        live_governance_decision=GovernanceDecisionKind.NO_ACTION,
    )


def _monitor_consensus() -> GovernanceConsensusResult:
    return compute_governance_consensus(
        consensus_id="cons-monitor",
        signals=(),
        live_governance_decision=GovernanceDecisionKind.MONITOR_ONLY,
    )


class TestLiveImpactGuardBlock:
    def test_block_consensus_allows_live_influence(self) -> None:
        inp = LiveImpactGuardInput(
            guard_id="g-1",
            consensus_result=_block_consensus(),
            human_approval_present=True,
            now_ms=1_000,
        )
        result = evaluate_live_impact_guard(inp)
        assert result.allowed_to_influence_live is True
        assert result.effective_output is SystemOutput.BLOCK

    def test_kill_switch_overrides_block(self) -> None:
        inp = LiveImpactGuardInput(
            guard_id="g-2",
            consensus_result=_block_consensus(),
            human_approval_present=True,
            kill_switch_observed=True,
            now_ms=1_000,
        )
        result = evaluate_live_impact_guard(inp)
        assert result.allowed_to_influence_live is False
        assert result.block_reason == "kill_switch_observed"

    def test_hash_chain_invalid_overrides_block(self) -> None:
        inp = LiveImpactGuardInput(
            guard_id="g-3",
            consensus_result=_block_consensus(),
            human_approval_present=True,
            hash_chain_valid=False,
            now_ms=1_000,
        )
        result = evaluate_live_impact_guard(inp)
        assert result.allowed_to_influence_live is False
        assert result.block_reason == "hash_chain_invalid"


class TestLiveImpactGuardNonBlock:
    def test_no_action_does_not_allow_live_influence(self) -> None:
        inp = LiveImpactGuardInput(
            guard_id="g-4",
            consensus_result=_no_action_consensus(),
            human_approval_present=True,
            now_ms=1_000,
        )
        result = evaluate_live_impact_guard(inp)
        assert result.allowed_to_influence_live is False

    def test_monitor_does_not_allow_live_influence(self) -> None:
        inp = LiveImpactGuardInput(
            guard_id="g-5",
            consensus_result=_monitor_consensus(),
            human_approval_present=True,
            now_ms=1_000,
        )
        result = evaluate_live_impact_guard(inp)
        assert result.allowed_to_influence_live is False


class TestLiveImpactGuardSafetyFlags:
    def test_safety_flags_pinned_false(self) -> None:
        inp = LiveImpactGuardInput(
            guard_id="g-6",
            consensus_result=_block_consensus(),
            human_approval_present=True,
            now_ms=1_000,
        )
        result = evaluate_live_impact_guard(inp)
        assert result.creates_action is False
        assert result.writes_external is False
        assert result.approves_trade is False
        assert result.no_veto_is_approval is False
        assert result.monitor_is_approval is False

    def test_allowed_live_only_when_block_enforced(self) -> None:
        with pytest.raises(ValidationError):
            LiveImpactGuardResult(
                guard_id="bad",
                allowed_to_influence_live=True,
                effective_output=SystemOutput.NO_ACTION,
                block_reason="",
            )

    def test_no_action_result_valid(self) -> None:
        result = LiveImpactGuardResult(
            guard_id="g-7",
            allowed_to_influence_live=False,
            effective_output=SystemOutput.NO_ACTION,
            block_reason="",
        )
        assert result.allowed_to_influence_live is False
