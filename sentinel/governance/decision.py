"""V9 — Live governance decision schema."""

from __future__ import annotations

from enum import StrEnum
from typing import Final, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sentinel.runtime.output import SystemOutput


class GovernanceDecisionKind(StrEnum):
    """Closed governance decision kind enum.

    There is no ``approve`` / ``allow`` / ``execute`` / ``submit``
    value.  Even ``no_action`` is not approval.
    """

    BLOCK_LIVE_CANDIDATE = "block_live_candidate"
    MONITOR_ONLY = "monitor_only"
    WAIT_FOR_HUMAN = "wait_for_human"
    NEED_RECALL = "need_recall"
    NO_ACTION = "no_action"


class GovernanceReason(StrEnum):
    """Closed governance reason enum."""

    POLICY_BLOCK = "policy_block"
    CANARY_VETO = "canary_veto"
    PAPER_BLOCK = "paper_block"
    REPLAY_UNCERTAIN = "replay_uncertain"
    MEMORY_CONFLICT = "memory_conflict"
    MISSING_HUMAN_APPROVAL = "missing_human_approval"
    HUMAN_REJECTED = "human_rejected"
    HUMAN_APPROVAL_EXPIRED = "human_approval_expired"
    MISSING_ACTIVE_POLICY = "missing_active_policy"
    MISSING_CANARY_BOUNDS = "missing_canary_bounds"
    STALE_DATA = "stale_data"
    HIGH_RISK = "high_risk"
    LOW_CONFIDENCE = "low_confidence"
    BAD_DISPATCH_HISTORY = "bad_dispatch_history"
    KILL_SWITCH_OBSERVED = "kill_switch_observed"
    PROVENANCE_MISSING = "provenance_missing"
    HASH_CHAIN_INVALID = "hash_chain_invalid"
    GOVERNANCE_TIMEOUT = "governance_timeout"
    NO_LIVE_IMPACT = "no_live_impact"
    NO_ACTION_NEEDED = "no_action_needed"
    NO_BLOCK_REASON_FOUND = "no_block_reason_found"


_DECISION_TO_OUTPUT: Final[dict[GovernanceDecisionKind, SystemOutput]] = {
    GovernanceDecisionKind.BLOCK_LIVE_CANDIDATE: SystemOutput.BLOCK,
    GovernanceDecisionKind.MONITOR_ONLY: SystemOutput.MONITOR,
    GovernanceDecisionKind.WAIT_FOR_HUMAN: SystemOutput.WAIT,
    GovernanceDecisionKind.NEED_RECALL: SystemOutput.NEED_RECALL,
    GovernanceDecisionKind.NO_ACTION: SystemOutput.NO_ACTION,
}


class LiveGovernanceDecision(BaseModel):
    """One V9 governance evaluation outcome.

    Five safety flags are pinned ``Literal[False]`` and revalidated:
    ``creates_action``, ``writes_external``, ``approves_trade``,
    ``no_veto_is_approval``, ``monitor_is_approval``.

    ``live_impact_allowed=True`` is permitted only when
    ``decision=block_live_candidate`` AND ``system_output=BLOCK``.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    decision_id: str = Field(min_length=1)
    request_id: str = Field(min_length=1)
    decision: GovernanceDecisionKind
    system_output: SystemOutput
    reasons: tuple[GovernanceReason, ...]
    confidence: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    human_approval_ref: str | None = None
    policy_record_ref: str | None = None
    canary_decision_ref: str | None = None
    paper_decision_ref: str | None = None
    replay_evidence_refs: tuple[str, ...] = ()
    memory_record_refs: tuple[str, ...] = ()
    live_impact_possible: bool
    live_impact_allowed: bool
    creates_action: Literal[False] = False
    writes_external: Literal[False] = False
    approves_trade: Literal[False] = False
    no_veto_is_approval: Literal[False] = False
    monitor_is_approval: Literal[False] = False
    created_at_ms: int = Field(ge=0)
    expires_at_ms: int = Field(ge=0)

    @model_validator(mode="after")
    def _validate_decision(self) -> Self:
        if not self.reasons:
            raise ValueError("LiveGovernanceDecision.reasons must be non-empty")
        if self.expires_at_ms <= self.created_at_ms:
            raise ValueError(
                f"expires_at_ms ({self.expires_at_ms}) must be > created_at_ms "
                f"({self.created_at_ms})"
            )
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

        expected_output = _DECISION_TO_OUTPUT[self.decision]
        if self.system_output is not expected_output:
            raise ValueError(
                f"decision={self.decision.value} requires "
                f"system_output={expected_output.value}; got "
                f"{self.system_output.value}"
            )

        if self.live_impact_allowed:
            if self.decision is not GovernanceDecisionKind.BLOCK_LIVE_CANDIDATE:
                raise ValueError(
                    "live_impact_allowed=True permitted only when decision=block_live_candidate"
                )
            if self.system_output is not SystemOutput.BLOCK:
                raise ValueError("live_impact_allowed=True permitted only when system_output=BLOCK")
        return self


__all__ = [
    "GovernanceDecisionKind",
    "GovernanceReason",
    "LiveGovernanceDecision",
]
