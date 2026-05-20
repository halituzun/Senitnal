"""V4 — Replay session schemas.

A ReplaySession is a single bounded, sandbox-only simulation pass
over historical M1 / M2 / observation refs. It produces only
proposals + evidence; it CANNOT push events into the live core,
CANNOT call the deontic gate, CANNOT write M2 directly, and
CANNOT generate any action output.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sentinel.types.neural_seed import ProvenanceRef  # noqa: TC001 (Pydantic runtime)


class ReplaySessionStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    ABORTED = "aborted"
    BUDGET_EXHAUSTED = "budget_exhausted"
    FAILED = "failed"


class ReplayPurpose(StrEnum):
    SLEEP_SYNAPSE_UPDATE = "sleep_synapse_update"
    ATTENTION_HABITUATION = "attention_habituation"
    INGRESS_CALIBRATION = "ingress_calibration"
    MEMORY_VERIFICATION = "memory_verification"
    OUTCOME_ALIGNMENT_ANALYSIS = "outcome_alignment_analysis"
    COUNTERFACTUAL_ABLATION = "counterfactual_ablation"
    FINANCIAL_MEMORY_REVIEW = "financial_memory_review"


class ReplayEffectChannel(StrEnum):
    SLEEP_SYNAPSE_UPDATE = "sleep_synapse_update"
    ATTENTION_HABITUATION_UPDATE = "attention_habituation_update"
    INGRESS_CALIBRATION_UPDATE = "ingress_calibration_update"
    MEMORY_VERIFICATION_EVIDENCE = "memory_verification_evidence"
    OUTCOME_ALIGNMENT_ANALYSIS = "outcome_alignment_analysis"
    AUDIT_ONLY = "audit_only"


_TERMINAL_STATUSES: frozenset[ReplaySessionStatus] = frozenset(
    {
        ReplaySessionStatus.COMPLETED,
        ReplaySessionStatus.ABORTED,
        ReplaySessionStatus.FAILED,
        ReplaySessionStatus.BUDGET_EXHAUSTED,
    }
)


class ReplayInputSnapshot(BaseModel):
    """Bounded reference set the replay session consumes.

    All references are existing M1 / M2 / observation IDs. No raw
    domain labels (symbol, venue, ...) are carried here directly —
    the underlying refs already encode whatever observer-side
    provenance is allowed.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    snapshot_id: str = Field(min_length=1)
    source_m1_event_ids: tuple[str, ...] = ()
    source_memory_record_ids: tuple[str, ...] = ()
    source_observation_event_ids: tuple[str, ...] = ()
    source_outcome_refs: tuple[str, ...] = ()
    created_at_ms: int = Field(ge=0)
    provenance_ref: ProvenanceRef
    hash_ref: str = Field(min_length=1)

    @model_validator(mode="after")
    def _at_least_one_source(self) -> Self:
        if not (
            self.source_m1_event_ids
            or self.source_memory_record_ids
            or self.source_observation_event_ids
            or self.source_outcome_refs
        ):
            raise ValueError("ReplayInputSnapshot must reference at least one source tuple")
        for collection in (
            self.source_m1_event_ids,
            self.source_memory_record_ids,
            self.source_observation_event_ids,
            self.source_outcome_refs,
        ):
            for sid in collection:
                if not sid:
                    raise ValueError("source refs must be non-empty strings")
        return self


class ReplaySession(BaseModel):
    """One bounded sandbox-only replay pass."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    session_id: str = Field(min_length=1)
    purpose: ReplayPurpose
    status: ReplaySessionStatus
    input_snapshot: ReplayInputSnapshot
    started_at_ms: int = Field(ge=0)
    completed_at_ms: int | None = None
    budget_ref: str = Field(min_length=1)
    sandbox_id: str = Field(min_length=1)
    effect_channels_requested: tuple[ReplayEffectChannel, ...]
    effect_channels_applied: tuple[ReplayEffectChannel, ...] = ()
    audit_event_ids: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _validate(self) -> Self:
        if not self.effect_channels_requested:
            raise ValueError("effect_channels_requested must be non-empty")
        for applied in self.effect_channels_applied:
            if applied not in self.effect_channels_requested:
                raise ValueError(f"applied channel {applied!r} not in requested set")
        if self.status in _TERMINAL_STATUSES:
            if self.completed_at_ms is None:
                raise ValueError(f"status={self.status.value!r} requires completed_at_ms")
            if self.completed_at_ms < self.started_at_ms:
                raise ValueError("completed_at_ms cannot be before started_at_ms")
        return self
