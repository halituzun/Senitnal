"""V9 — Live governance request schema."""

from __future__ import annotations

from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sentinel.governance.scope import (
    GovernanceEnvironment,
    LimitedLiveGovernanceScope,
)


class GovernanceRequestKind(StrEnum):
    """Closed governance request kind enum."""

    CANDIDATE_LIVE_ACTION_REVIEW = "candidate_live_action_review"
    CANARY_ESCALATION_REVIEW = "canary_escalation_review"
    PAPER_TO_LIVE_DISAGREEMENT_REVIEW = "paper_to_live_disagreement_review"
    POLICY_VIOLATION_REVIEW = "policy_violation_review"
    KILL_SWITCH_OBSERVATION_REVIEW = "kill_switch_observation_review"
    BAD_DISPATCH_OBSERVATION_REVIEW = "bad_dispatch_observation_review"
    STALE_DATA_REVIEW = "stale_data_review"
    INCIDENT_FOLLOWUP_REVIEW = "incident_followup_review"


class LiveGovernanceRequest(BaseModel):
    """Observed governance request from Gel.Al / local fixture.

    The request is **observed**: Sentinel does not produce it as an
    action.  Raw symbol / venue / strategy / order / API fields are
    rejected at construction.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    request_id: str = Field(min_length=1)
    request_kind: GovernanceRequestKind
    scope: LimitedLiveGovernanceScope
    candidate_ref: str = Field(min_length=1)
    source_event_refs: tuple[str, ...]
    observed_at_ms: int = Field(ge=0)
    deadline_ms: int = Field(ge=0)
    provenance_hash: str = Field(min_length=1)
    canary_decision_ref: str | None = None
    paper_decision_ref: str | None = None
    policy_record_ref: str | None = None
    memory_record_refs: tuple[str, ...] = ()
    replay_evidence_refs: tuple[str, ...] = ()
    risk_score: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    confidence: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    staleness_ms: int = Field(ge=0)
    latency_ms: int = Field(ge=0)
    live_impact_possible: bool
    requires_human_approval: bool

    @model_validator(mode="after")
    def _validate_request(self) -> Self:
        if self.deadline_ms <= self.observed_at_ms:
            raise ValueError(
                f"deadline_ms ({self.deadline_ms}) must be > observed_at_ms ({self.observed_at_ms})"
            )
        if not self.source_event_refs:
            raise ValueError("source_event_refs must be non-empty")
        if self.live_impact_possible and not self.requires_human_approval:
            raise ValueError("live_impact_possible=True requires requires_human_approval=True")
        if (
            self.scope.environment is GovernanceEnvironment.LIMITED_LIVE
            and not self.requires_human_approval
        ):
            raise ValueError("limited_live environment requires requires_human_approval=True")
        return self


__all__ = ["GovernanceRequestKind", "LiveGovernanceRequest"]
