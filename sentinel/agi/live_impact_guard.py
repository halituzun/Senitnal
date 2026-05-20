"""V10 — Financial AGI v1 live impact guard.

Final gate before any live-impacting advisory signal is emitted.
``allowed_to_influence_live=True`` only when ``effective_output==BLOCK``.
No other output ever authorises live influence.

Constitutional discipline:
    - Five safety flags pinned ``Literal[False]``.
    - ``allowed_to_influence_live=True`` iff ``effective_output==BLOCK``.
    - Read-only — no state mutation, no external writes.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from sentinel.agi.consensus import GovernanceConsensusResult  # noqa: TC001
from sentinel.runtime.output import SystemOutput


class LiveImpactGuardInput(BaseModel, frozen=True, extra="forbid"):
    """Input to the live impact guard."""

    guard_id: str = Field(min_length=1)
    consensus_result: GovernanceConsensusResult
    human_approval_present: bool
    kill_switch_observed: bool = False
    hash_chain_valid: bool = True
    now_ms: int = Field(ge=0)


class LiveImpactGuardResult(BaseModel, frozen=True, extra="forbid"):
    """Output of evaluate_live_impact_guard."""

    guard_id: str
    allowed_to_influence_live: bool
    effective_output: SystemOutput
    block_reason: str
    creates_action: Literal[False] = False
    writes_external: Literal[False] = False
    approves_trade: Literal[False] = False
    no_veto_is_approval: Literal[False] = False
    monitor_is_approval: Literal[False] = False

    @model_validator(mode="after")
    def _safety_flags_and_live_allowed_consistent(
        self,
    ) -> LiveImpactGuardResult:
        if self.creates_action is not False:
            raise ValueError("creates_action must be False")
        if self.writes_external is not False:
            raise ValueError("writes_external must be False")
        if self.approves_trade is not False:
            raise ValueError("approves_trade must be False")
        if self.no_veto_is_approval is not False:
            raise ValueError("no_veto_is_approval must be False")
        if self.monitor_is_approval is not False:
            raise ValueError("monitor_is_approval must be False")
        if self.allowed_to_influence_live and self.effective_output is not SystemOutput.BLOCK:
            raise ValueError(
                "allowed_to_influence_live=True is only permitted when effective_output==BLOCK"
            )
        return self


def evaluate_live_impact_guard(
    guard_input: LiveImpactGuardInput,
) -> LiveImpactGuardResult:
    """Evaluate the live impact guard.

    ``allowed_to_influence_live=True`` only when:
    1. Kill switch is NOT observed.
    2. Hash chain IS valid.
    3. consensus ``effective_output == BLOCK``.

    Every other output (MONITOR, WAIT, NEED_RECALL, NO_ACTION)
    produces ``allowed_to_influence_live=False``.
    """
    effective = guard_input.consensus_result.effective_output

    if guard_input.kill_switch_observed:
        return LiveImpactGuardResult(
            guard_id=guard_input.guard_id,
            allowed_to_influence_live=False,
            effective_output=SystemOutput.BLOCK,
            block_reason="kill_switch_observed",
        )

    if not guard_input.hash_chain_valid:
        return LiveImpactGuardResult(
            guard_id=guard_input.guard_id,
            allowed_to_influence_live=False,
            effective_output=SystemOutput.BLOCK,
            block_reason="hash_chain_invalid",
        )

    if effective is SystemOutput.BLOCK:
        return LiveImpactGuardResult(
            guard_id=guard_input.guard_id,
            allowed_to_influence_live=True,
            effective_output=SystemOutput.BLOCK,
            block_reason="consensus_block",
        )

    return LiveImpactGuardResult(
        guard_id=guard_input.guard_id,
        allowed_to_influence_live=False,
        effective_output=effective,
        block_reason="",
    )


__all__ = [
    "LiveImpactGuardInput",
    "LiveImpactGuardResult",
    "evaluate_live_impact_guard",
]
