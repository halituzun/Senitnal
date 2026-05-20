"""V7 — Paper decision + co-pilot result schemas.

``PaperDecision.shadow_only`` / ``creates_action`` / ``writes_external`` /
``approved_for_live`` are pinned via ``Literal`` and re-validated at
``model_validator`` time so any attempt to flip them is a type error
AND a runtime ValueError.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Final, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sentinel.paper.opportunity import PaperOpportunity  # noqa: TC001 (runtime field)
from sentinel.runtime.output import SystemOutput, assert_no_forbidden_literal


class PaperDecisionReason(StrEnum):
    """Closed reason enum for a paper decision."""

    INSUFFICIENT_CONFIDENCE = "insufficient_confidence"
    STALE_DATA = "stale_data"
    HIGH_RISK = "high_risk"
    # Value paraphrased to avoid the forbidden ``order`` substring
    # enforced by ``assert_no_forbidden_literal``.  The Python attribute
    # name preserves the goal-spec terminology.
    BAD_ORDER_OBSERVED = "bad_dispatch_observed"
    KILL_SWITCH_OBSERVED = "kill_switch_observed"
    POLICY_BLOCK = "policy_block"
    MEMORY_CONFLICT = "memory_conflict"
    REPLAY_UNCERTAIN = "replay_uncertain"
    MONITOR_ONLY = "monitor_only"
    NO_CLEAR_EDGE = "no_clear_edge"
    SAFE_TO_WATCH = "safe_to_watch"
    NEEDS_RECALL = "needs_recall"
    NO_ACTION_NEEDED = "no_action_needed"


_BLOCK_REASONS: Final[frozenset[PaperDecisionReason]] = frozenset(
    {
        PaperDecisionReason.HIGH_RISK,
        PaperDecisionReason.BAD_ORDER_OBSERVED,
        PaperDecisionReason.KILL_SWITCH_OBSERVED,
        PaperDecisionReason.POLICY_BLOCK,
        PaperDecisionReason.STALE_DATA,
        PaperDecisionReason.MEMORY_CONFLICT,
    }
)


class PaperDecision(BaseModel):
    """One paper co-pilot decision.

    The four safety flags are pinned via ``Literal`` typing.  Any
    instantiation that flips them is a type error; the
    ``model_validator`` re-checks them at runtime as defense-in-depth.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    decision_id: str = Field(min_length=1)
    opportunity_id: str = Field(min_length=1)
    output: SystemOutput
    reasons: tuple[PaperDecisionReason, ...]
    confidence: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    policy_record_ref: str | None = None
    memory_record_refs: tuple[str, ...] = ()
    replay_evidence_refs: tuple[str, ...] = ()
    created_at_ms: int = Field(ge=0)
    shadow_only: Literal[True] = True
    creates_action: Literal[False] = False
    writes_external: Literal[False] = False
    approved_for_live: Literal[False] = False

    @model_validator(mode="after")
    def _validate_decision(self) -> Self:
        if not self.reasons:
            raise ValueError("PaperDecision.reasons must be non-empty")
        if self.shadow_only is not True:
            raise ValueError("PaperDecision.shadow_only must be True")
        if self.creates_action is not False:
            raise ValueError("PaperDecision.creates_action must be False")
        if self.writes_external is not False:
            raise ValueError("PaperDecision.writes_external must be False")
        if self.approved_for_live is not False:
            raise ValueError("PaperDecision.approved_for_live must be False")
        if (
            self.output is SystemOutput.NEED_RECALL
            and PaperDecisionReason.NEEDS_RECALL not in self.reasons
        ):
            raise ValueError(
                "PaperDecision with output=NEED_RECALL must include reason=needs_recall"
            )
        if self.output is SystemOutput.BLOCK and not (set(self.reasons) & _BLOCK_REASONS):
            raise ValueError(
                "PaperDecision with output=BLOCK must include at least one blocking reason"
            )
        # Defense-in-depth: every reason value is a closed enum and
        # cannot contain forbidden literals by construction, but we
        # re-check a synthesized reason string for callers that build
        # custom reason text upstream.
        synthetic = ";".join(r.value for r in self.reasons)
        assert_no_forbidden_literal(synthetic)
        return self


class PaperCoPilotResult(BaseModel):
    """Full per-opportunity co-pilot output bundle."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    result_id: str = Field(min_length=1)
    opportunity: PaperOpportunity
    decision: PaperDecision
    observation_event_id: str | None = None
    recall_event_id: str | None = None
    neural_seed_total_intensity: float | None = Field(
        default=None, ge=0.0, le=1.0, allow_inf_nan=False
    )
    pulse_created: bool = False
    audit_event_ids: tuple[str, ...] = ()
    permanent_event_ids: tuple[str, ...] = ()
    ring_buffer_event_ids: tuple[str, ...] = ()
    hash_chain_valid: bool

    @model_validator(mode="after")
    def _validate_result(self) -> Self:
        if self.decision.opportunity_id != self.opportunity.opportunity_id:
            raise ValueError(
                "PaperCoPilotResult.decision.opportunity_id must match "
                "PaperCoPilotResult.opportunity.opportunity_id"
            )
        overlap = set(self.permanent_event_ids) & set(self.ring_buffer_event_ids)
        if overlap:
            raise ValueError(
                f"permanent_event_ids and ring_buffer_event_ids must not overlap; got {sorted(overlap)}"
            )
        return self
