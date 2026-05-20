"""V10 — Governance consensus tests."""

from __future__ import annotations

from sentinel.agi.consensus import (
    GovernanceConsensusDecision,
    GovernanceSignal,
    GovernanceSignalSource,
    compute_governance_consensus,
)
from sentinel.governance.decision import GovernanceDecisionKind
from sentinel.runtime.output import SystemOutput


def _signals(**kwargs: SystemOutput) -> tuple[GovernanceSignal, ...]:
    src_map = {
        "policy": GovernanceSignalSource.POLICY,
        "paper": GovernanceSignalSource.PAPER,
        "canary": GovernanceSignalSource.CANARY,
    }
    return tuple(GovernanceSignal(source=src_map[k], output=v) for k, v in kwargs.items())


class TestConsensusMissingSignal:
    def test_no_live_governance_signal_blocked(self) -> None:
        result = compute_governance_consensus(
            consensus_id="c-1",
            signals=(),
            live_governance_decision=None,
        )
        assert result.decision is GovernanceConsensusDecision.CONSENSUS_INSUFFICIENT_SIGNALS
        assert result.effective_output is SystemOutput.BLOCK
        assert result.has_live_governance_signal is False

    def test_no_veto_is_not_approval(self) -> None:
        result = compute_governance_consensus(
            consensus_id="c-2",
            signals=(),
            live_governance_decision=None,
        )
        assert result.no_veto_is_approval is False

    def test_monitor_is_not_approval(self) -> None:
        result = compute_governance_consensus(
            consensus_id="c-3",
            signals=_signals(policy=SystemOutput.MONITOR),
            live_governance_decision=GovernanceDecisionKind.MONITOR_ONLY,
        )
        assert result.monitor_is_approval is False

    def test_wait_is_not_approval(self) -> None:
        result = compute_governance_consensus(
            consensus_id="c-4",
            signals=(),
            live_governance_decision=GovernanceDecisionKind.WAIT_FOR_HUMAN,
        )
        assert result.wait_is_approval is False

    def test_need_recall_is_not_approval(self) -> None:
        result = compute_governance_consensus(
            consensus_id="c-5",
            signals=(),
            live_governance_decision=GovernanceDecisionKind.NEED_RECALL,
        )
        assert result.need_recall_is_approval is False


class TestConsensusBlock:
    def test_live_gov_block_produces_consensus_block(self) -> None:
        result = compute_governance_consensus(
            consensus_id="c-6",
            signals=(),
            live_governance_decision=GovernanceDecisionKind.BLOCK_LIVE_CANDIDATE,
        )
        assert result.decision is GovernanceConsensusDecision.CONSENSUS_BLOCK
        assert result.effective_output is SystemOutput.BLOCK

    def test_policy_block_signal_produces_consensus_block(self) -> None:
        result = compute_governance_consensus(
            consensus_id="c-7",
            signals=_signals(policy=SystemOutput.BLOCK),
            live_governance_decision=GovernanceDecisionKind.NO_ACTION,
        )
        assert result.decision is GovernanceConsensusDecision.CONSENSUS_BLOCK

    def test_paper_block_signal_produces_consensus_block(self) -> None:
        result = compute_governance_consensus(
            consensus_id="c-8",
            signals=_signals(paper=SystemOutput.BLOCK),
            live_governance_decision=GovernanceDecisionKind.NO_ACTION,
        )
        assert result.decision is GovernanceConsensusDecision.CONSENSUS_BLOCK

    def test_block_sources_populated(self) -> None:
        result = compute_governance_consensus(
            consensus_id="c-9",
            signals=_signals(policy=SystemOutput.BLOCK),
            live_governance_decision=GovernanceDecisionKind.BLOCK_LIVE_CANDIDATE,
        )
        assert len(result.block_sources) >= 1


class TestConsensusNonBlock:
    def test_no_action_produces_consensus_no_action(self) -> None:
        result = compute_governance_consensus(
            consensus_id="c-10",
            signals=_signals(policy=SystemOutput.NO_ACTION),
            live_governance_decision=GovernanceDecisionKind.NO_ACTION,
        )
        assert result.decision is GovernanceConsensusDecision.CONSENSUS_NO_ACTION
        assert result.effective_output is SystemOutput.NO_ACTION

    def test_monitor_produces_consensus_monitor(self) -> None:
        result = compute_governance_consensus(
            consensus_id="c-11",
            signals=_signals(policy=SystemOutput.MONITOR),
            live_governance_decision=GovernanceDecisionKind.MONITOR_ONLY,
        )
        assert result.decision is GovernanceConsensusDecision.CONSENSUS_MONITOR

    def test_wait_produces_consensus_wait(self) -> None:
        result = compute_governance_consensus(
            consensus_id="c-12",
            signals=(),
            live_governance_decision=GovernanceDecisionKind.WAIT_FOR_HUMAN,
        )
        assert result.decision is GovernanceConsensusDecision.CONSENSUS_WAIT

    def test_need_recall_produces_consensus_need_recall(self) -> None:
        result = compute_governance_consensus(
            consensus_id="c-13",
            signals=(),
            live_governance_decision=GovernanceDecisionKind.NEED_RECALL,
        )
        assert result.decision is GovernanceConsensusDecision.CONSENSUS_NEED_RECALL

    def test_block_overrides_monitor(self) -> None:
        result = compute_governance_consensus(
            consensus_id="c-14",
            signals=_signals(policy=SystemOutput.BLOCK, paper=SystemOutput.MONITOR),
            live_governance_decision=GovernanceDecisionKind.NO_ACTION,
        )
        assert result.decision is GovernanceConsensusDecision.CONSENSUS_BLOCK
