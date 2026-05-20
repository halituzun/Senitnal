"""V4 — Effect channel proposal schemas.

These are PROPOSALS only. They do not mutate state. The downstream
consumer (sleep cycle, attention pulse runtime, ingress compiler,
Memory Write Gate) decides whether to act on them. V4 itself only
constructs the proposal records.

Critical bounds:
    - Sleep synapse update has no topology mutation; only a
      bounded delta and an eligibility_trace_id.
    - Attention habituation has NO synapse topology fields.
    - Ingress calibration update has NO new payload type field;
      it can only adjust existing mappings.
    - Memory verification evidence proposal does NOT write the
      store; the existing MWG remains the only write path.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SynapseDirection(StrEnum):
    STRENGTHENING = "strengthening"
    WEAKENING = "weakening"


class SleepSynapseUpdateProposal(BaseModel):
    """Bounded synapse-update proposal from a replay session."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    proposal_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    synapse_id: str = Field(min_length=1)
    direction: SynapseDirection
    delta: float = Field(allow_inf_nan=False)
    capped_delta: float = Field(allow_inf_nan=False)
    eligibility_trace_id: str = Field(min_length=1)
    evidence_ref: str = Field(min_length=1)
    created_at_ms: int = Field(ge=0)

    @model_validator(mode="after")
    def _validate(self) -> Self:
        if abs(self.capped_delta) > abs(self.delta):
            raise ValueError("|capped_delta| must be <= |delta|")
        return self


class AttentionHabituationUpdate(BaseModel):
    """Bounded attention-habituation update from a replay session.

    Constitutional: NO synapse-topology fields. The attention layer
    habituates context signatures, never rewires neurons.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    update_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    assembly_id: str = Field(min_length=1)
    context_signature_hash: str = Field(min_length=1)
    habituation_delta: float = Field(allow_inf_nan=False)
    capped_delta: float = Field(allow_inf_nan=False)
    created_at_ms: int = Field(ge=0)

    @model_validator(mode="after")
    def _validate(self) -> Self:
        if abs(self.capped_delta) > abs(self.habituation_delta):
            raise ValueError("|capped_delta| must be <= |habituation_delta|")
        return self


class IngressCalibrationUpdateProposal(BaseModel):
    """Bounded ingress-calibration proposal.

    Constitutional: NO new payload type. Replay can only adjust
    existing ingress-compiler mappings, never introduce a new
    PrimerPayload value.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    proposal_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    mapping_id: str = Field(min_length=1)
    delta: float = Field(allow_inf_nan=False)
    capped_delta: float = Field(allow_inf_nan=False)
    daily_cap_ref: float = Field(ge=0.0, allow_inf_nan=False)
    created_at_ms: int = Field(ge=0)

    @model_validator(mode="after")
    def _validate(self) -> Self:
        if abs(self.capped_delta) > self.daily_cap_ref:
            raise ValueError("|capped_delta| must be <= daily_cap_ref")
        if abs(self.capped_delta) > abs(self.delta):
            raise ValueError("|capped_delta| must be <= |delta|")
        return self


class MemoryEvidenceKind(StrEnum):
    REPLAY_SURVIVAL = "replay_survival"
    OUTCOME_ALIGNMENT = "outcome_alignment"


class MemoryVerificationEvidenceProposal(BaseModel):
    """Proposal that a memory record gain verification evidence.

    This is NOT a memory write. The Memory Write Gate remains the
    only path that can change a record's verified status. The
    proposal records:
        - which kind of evidence is being offered
        - whether the evidence is even usable for the gate
          (replay survival: min_sessions_satisfied;
           outcome alignment: external + not stale)
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    proposal_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    memory_record_id: str = Field(min_length=1)
    evidence_kind: MemoryEvidenceKind
    evidence_id: str = Field(min_length=1)
    usable_for_gate: bool
    created_at_ms: int = Field(ge=0)
