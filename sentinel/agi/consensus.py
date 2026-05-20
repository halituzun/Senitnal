"""V10 — Financial AGI v1 governance consensus.

Aggregates signals from V6 (policy), V7 (paper), V8 (canary veto),
and V9 (live governance) into a single consensus decision.

Constitutional discipline:
    - No-veto, monitor, wait, need_recall are NOT approval signals.
    - Any single BLOCK or veto signal → consensus BLOCK.
    - Missing mandatory V9 governance decision → consensus BLOCK.
    - Read-only — no state mutation.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from sentinel.governance.decision import GovernanceDecisionKind
from sentinel.runtime.output import SystemOutput


class GovernanceSignalSource(StrEnum):
    """Closed set of governance signal sources."""

    POLICY = "policy"
    PAPER = "paper"
    CANARY = "canary"
    LIVE_GOVERNANCE = "live_governance"


class GovernanceConsensusDecision(StrEnum):
    """Closed set of consensus outcomes."""

    CONSENSUS_BLOCK = "consensus_block"
    CONSENSUS_MONITOR = "consensus_monitor"
    CONSENSUS_WAIT = "consensus_wait"
    CONSENSUS_NEED_RECALL = "consensus_need_recall"
    CONSENSUS_NO_ACTION = "consensus_no_action"
    CONSENSUS_INSUFFICIENT_SIGNALS = "consensus_insufficient_signals"


class GovernanceSignal(BaseModel, frozen=True, extra="forbid"):
    """One signal from a governance layer."""

    source: GovernanceSignalSource
    output: SystemOutput
    signal_ref: str = ""


class GovernanceConsensusResult(BaseModel, frozen=True, extra="forbid"):
    """Output of compute_governance_consensus."""

    consensus_id: str = Field(min_length=1)
    decision: GovernanceConsensusDecision
    effective_output: SystemOutput
    signals: tuple[GovernanceSignal, ...]
    block_sources: tuple[GovernanceSignalSource, ...]
    has_live_governance_signal: bool
    notes: str = ""
    no_veto_is_approval: Literal[False] = False
    monitor_is_approval: Literal[False] = False
    wait_is_approval: Literal[False] = False
    need_recall_is_approval: Literal[False] = False

    @model_validator(mode="after")
    def _approval_flags_pinned(self) -> GovernanceConsensusResult:
        if self.no_veto_is_approval is not False:
            raise ValueError("no_veto_is_approval must be False")
        if self.monitor_is_approval is not False:
            raise ValueError("monitor_is_approval must be False")
        if self.wait_is_approval is not False:
            raise ValueError("wait_is_approval must be False")
        if self.need_recall_is_approval is not False:
            raise ValueError("need_recall_is_approval must be False")
        return self


def compute_governance_consensus(
    *,
    consensus_id: str,
    signals: tuple[GovernanceSignal, ...],
    live_governance_decision: GovernanceDecisionKind | None,
) -> GovernanceConsensusResult:
    """Aggregate governance signals into a consensus decision.

    Rules (fail-closed):
    1. No live governance signal → ``consensus_insufficient_signals`` / BLOCK.
    2. Live governance BLOCK_LIVE_CANDIDATE → ``consensus_block`` / BLOCK.
    3. Any signal output BLOCK → ``consensus_block`` / BLOCK.
    4. NEED_RECALL present → ``consensus_need_recall`` / NEED_RECALL.
    5. WAIT present → ``consensus_wait`` / WAIT.
    6. MONITOR present → ``consensus_monitor`` / MONITOR.
    7. All NO_ACTION → ``consensus_no_action`` / NO_ACTION.

    NO_ACTION, MONITOR, WAIT and NEED_RECALL are never treated as
    permission to proceed.
    """
    has_live = live_governance_decision is not None

    if not has_live:
        return GovernanceConsensusResult(
            consensus_id=consensus_id,
            decision=GovernanceConsensusDecision.CONSENSUS_INSUFFICIENT_SIGNALS,
            effective_output=SystemOutput.BLOCK,
            signals=signals,
            block_sources=(),
            has_live_governance_signal=False,
            notes="missing mandatory live governance signal",
        )

    # Collect block sources.
    block_sources: list[GovernanceSignalSource] = []

    # Live governance block.
    if live_governance_decision is GovernanceDecisionKind.BLOCK_LIVE_CANDIDATE:
        block_sources.append(GovernanceSignalSource.LIVE_GOVERNANCE)

    # Other signal blocks.
    for sig in signals:
        if sig.output is SystemOutput.BLOCK and sig.source not in block_sources:
            block_sources.append(sig.source)

    if block_sources:
        return GovernanceConsensusResult(
            consensus_id=consensus_id,
            decision=GovernanceConsensusDecision.CONSENSUS_BLOCK,
            effective_output=SystemOutput.BLOCK,
            signals=signals,
            block_sources=tuple(block_sources),
            has_live_governance_signal=True,
        )

    # Non-block precedence.
    outputs = {sig.output for sig in signals}

    if live_governance_decision is GovernanceDecisionKind.NEED_RECALL:
        return GovernanceConsensusResult(
            consensus_id=consensus_id,
            decision=GovernanceConsensusDecision.CONSENSUS_NEED_RECALL,
            effective_output=SystemOutput.NEED_RECALL,
            signals=signals,
            block_sources=(),
            has_live_governance_signal=True,
        )

    if SystemOutput.NEED_RECALL in outputs:
        return GovernanceConsensusResult(
            consensus_id=consensus_id,
            decision=GovernanceConsensusDecision.CONSENSUS_NEED_RECALL,
            effective_output=SystemOutput.NEED_RECALL,
            signals=signals,
            block_sources=(),
            has_live_governance_signal=True,
        )

    if live_governance_decision is GovernanceDecisionKind.WAIT_FOR_HUMAN:
        return GovernanceConsensusResult(
            consensus_id=consensus_id,
            decision=GovernanceConsensusDecision.CONSENSUS_WAIT,
            effective_output=SystemOutput.WAIT,
            signals=signals,
            block_sources=(),
            has_live_governance_signal=True,
        )

    if SystemOutput.WAIT in outputs:
        return GovernanceConsensusResult(
            consensus_id=consensus_id,
            decision=GovernanceConsensusDecision.CONSENSUS_WAIT,
            effective_output=SystemOutput.WAIT,
            signals=signals,
            block_sources=(),
            has_live_governance_signal=True,
        )

    if (
        live_governance_decision is GovernanceDecisionKind.MONITOR_ONLY
        or SystemOutput.MONITOR in outputs
    ):
        return GovernanceConsensusResult(
            consensus_id=consensus_id,
            decision=GovernanceConsensusDecision.CONSENSUS_MONITOR,
            effective_output=SystemOutput.MONITOR,
            signals=signals,
            block_sources=(),
            has_live_governance_signal=True,
        )

    return GovernanceConsensusResult(
        consensus_id=consensus_id,
        decision=GovernanceConsensusDecision.CONSENSUS_NO_ACTION,
        effective_output=SystemOutput.NO_ACTION,
        signals=signals,
        block_sources=(),
        has_live_governance_signal=True,
    )


__all__ = [
    "GovernanceConsensusDecision",
    "GovernanceConsensusResult",
    "GovernanceSignal",
    "GovernanceSignalSource",
    "compute_governance_consensus",
]
