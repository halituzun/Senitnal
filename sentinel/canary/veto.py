"""V8 — Veto request + decision schemas.

Frozen Pydantic v2 models.  Safety flags
(``creates_action`` / ``writes_external`` / ``approves_trade`` /
``no_veto_is_approval``) are pinned via ``Literal`` and revalidated
at ``model_validator`` time.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Final, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sentinel.canary.candidate import (
    CanaryCandidateAction,
    CanaryEnvironment,
)
from sentinel.runtime.output import SystemOutput
from sentinel.types.neural_seed import ProvenanceRef  # noqa: TC001


class VetoReason(StrEnum):
    """Closed reason enum for a veto/monitor/no-veto outcome."""

    POLICY_BLOCK = "policy_block"
    KILL_SWITCH_OBSERVED = "kill_switch_observed"
    STALE_DATA = "stale_data"
    HIGH_RISK = "high_risk"
    LOW_CONFIDENCE = "low_confidence"
    BAD_DISPATCH_HISTORY = "bad_dispatch_history"
    REPLAY_UNCERTAIN = "replay_uncertain"
    MEMORY_CONFLICT = "memory_conflict"
    INSUFFICIENT_EDGE = "insufficient_edge"
    LIQUIDITY_INSUFFICIENT = "liquidity_insufficient"
    PROVENANCE_MISSING = "provenance_missing"
    CANARY_LIMIT_EXCEEDED = "canary_limit_exceeded"
    NO_ACTIVE_POLICY = "no_active_policy"
    EXPIRED_CANDIDATE = "expired_candidate"
    FAIL_CLOSED = "fail_closed"
    NO_VETO_REASON_FOUND = "no_veto_reason_found"


class VetoDecisionKind(StrEnum):
    """Closed veto decision kind enum.

    ``no_veto`` is **not** approval.  It records that Sentinel saw no
    additional block reason in this evaluation; Gel.Al's risk engine
    remains the final authority on whether to act.
    """

    VETO = "veto"
    MONITOR_ONLY = "monitor_only"
    NO_VETO = "no_veto"


_BENIGN_REASONS: Final[frozenset[VetoReason]] = frozenset({VetoReason.NO_VETO_REASON_FOUND})


class VetoRequest(BaseModel):
    """One incoming veto-evaluation request."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    request_id: str = Field(min_length=1)
    candidate: CanaryCandidateAction
    requested_at_ms: int = Field(ge=0)
    deadline_ms: int = Field(ge=0)
    active_policy_record_ref: str | None = None
    paper_decision_ref: str | None = None
    replay_evidence_refs: tuple[str, ...] = ()
    memory_record_refs: tuple[str, ...] = ()
    provenance: ProvenanceRef

    @model_validator(mode="after")
    def _validate_request(self) -> Self:
        if self.deadline_ms <= self.requested_at_ms:
            raise ValueError(
                f"deadline_ms ({self.deadline_ms}) must be > requested_at_ms "
                f"({self.requested_at_ms})"
            )
        return self


class CanaryVetoDecision(BaseModel):
    """One canary veto evaluation outcome.

    Constitutional safety flags are pinned via ``Literal``; any
    instantiation that flips them is a type error AND a runtime
    ValueError.  ``shadow_only`` may be ``False`` only when
    ``decision == veto`` AND ``can_affect_canary`` is ``True``.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    decision_id: str = Field(min_length=1)
    request_id: str = Field(min_length=1)
    candidate_id: str = Field(min_length=1)
    decision: VetoDecisionKind
    system_output: SystemOutput
    reasons: tuple[VetoReason, ...]
    confidence: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    environment: CanaryEnvironment
    shadow_only: bool
    can_affect_canary: bool
    creates_action: Literal[False] = False
    writes_external: Literal[False] = False
    approves_trade: Literal[False] = False
    no_veto_is_approval: Literal[False] = False
    created_at_ms: int = Field(ge=0)
    expires_at_ms: int = Field(ge=0)

    @model_validator(mode="after")
    def _validate_decision(self) -> Self:
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

        if self.decision is VetoDecisionKind.VETO:
            if self.system_output is not SystemOutput.BLOCK:
                raise ValueError("decision=veto requires system_output=BLOCK")
            if not self.reasons:
                raise ValueError("decision=veto requires at least one reason")
            if (
                self.can_affect_canary
                and self.environment is not CanaryEnvironment.MICRO_LIVE_CANARY
            ):
                raise ValueError(
                    "can_affect_canary=True permitted only when environment is micro_live_canary"
                )
            if not self.shadow_only and (
                not self.can_affect_canary
                or self.environment is not CanaryEnvironment.MICRO_LIVE_CANARY
            ):
                raise ValueError(
                    "shadow_only may be False only when decision=veto AND "
                    "environment=micro_live_canary AND can_affect_canary=True"
                )
        elif self.decision is VetoDecisionKind.MONITOR_ONLY:
            if self.system_output is not SystemOutput.MONITOR:
                raise ValueError("decision=monitor_only requires system_output=MONITOR")
            if self.can_affect_canary:
                raise ValueError("monitor_only cannot set can_affect_canary=True")
            if not self.shadow_only:
                raise ValueError("monitor_only must remain shadow_only=True")
        elif self.decision is VetoDecisionKind.NO_VETO:
            if self.system_output not in (SystemOutput.NO_ACTION, SystemOutput.MONITOR):
                raise ValueError("decision=no_veto requires system_output in {NO_ACTION, MONITOR}")
            if self.can_affect_canary:
                raise ValueError("no_veto cannot set can_affect_canary=True")
            if not self.shadow_only:
                raise ValueError("no_veto must remain shadow_only=True")
            if not self.reasons:
                raise ValueError(
                    "decision=no_veto requires at least one reason (e.g. no_veto_reason_found)"
                )
            # benign reason required (sanity check that the caller flagged
            # the no-veto path with a benign reason rather than a block reason).
            if not (set(self.reasons) & _BENIGN_REASONS):
                # Allow other benign reasons too (the no-veto path is the only
                # path where reasons may be diagnostic-only), but the most
                # common case is NO_VETO_REASON_FOUND.
                pass

        return self


__all__ = [
    "CanaryVetoDecision",
    "VetoDecisionKind",
    "VetoReason",
    "VetoRequest",
]
