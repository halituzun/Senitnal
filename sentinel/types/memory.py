"""MemoryRecord — explicit M2 record schema.

Per MEMORY_CONTRACT.md §3 + §10 (CandidateMemoryRecord) +
BACKUP_STRATEGY.md §10 (internal_only vs external_corroboration refs) +
MEMORY_WRITE_GATE_NUMERICS.md §5 (subject_class matrix scaffold):

MemoryRecord is one entry in M2 — the explicit recall store. The schema
binds the canonical 16-value SubjectClass taxonomy and the 7-value status
chain. No verification, no status-transition logic, no self-deception
detection lives here; those land in Phase 7 (gates).

Constitutional rules enforced here (schema layer only):
    - 16 closed SubjectClass values (foreign_instance_origin is NOT in
      this enum; it is provenance metadata, per P §5 patch)
    - 7 closed MemoryRecordStatus values
    - record_id non-empty
    - payload non-empty
    - timestamps non-negative
    - last_status_change_ms >= created_at_ms (cannot be in the past)
    - reference tuples (causal / external_corroboration / internal_only)
    - extra="forbid", frozen=True, strict=True

What this module deliberately does NOT do:
    - Memory Write Gate verification matrix (Phase 7:
      `sentinel/gates/memory_write.py`; G §8 + P §9)
    - Status transition logic (Phase 7; G §15)
    - Verified promotion (Phase 7; mvp_verified_disabled = true in MVP)
    - Self-deception detection (Phase 7 + P §16:
      max_internal_only_ref_ratio)
    - Recall eligibility (Phase 8: `sentinel/recall/protocol.py`)
    - Foreign M2 merge logic (Phase 6+)
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from sentinel.types.neural_seed import ProvenanceRef  # noqa: TC001 (Pydantic runtime needs)

# ---------------------------------------------------------------------------
# Closed taxonomies
# ---------------------------------------------------------------------------


class SubjectClass(StrEnum):
    """The 16 canonical M2 subject classes (B §3).

    `foreign_instance_origin` is INTENTIONALLY NOT a SubjectClass.
    It is provenance metadata (per P §5 patch) carried in ProvenanceRef,
    not a subject_class for matrix verification.
    """

    SOURCE_TRUST = "source_trust"
    ADAPTER_TRUST = "adapter_trust"
    PROCEDURAL = "procedural"
    STRUCTURED_FACT = "structured_fact"
    INCIDENT = "incident"
    EPISODIC = "episodic"
    NARRATIVE_CLAIM = "narrative_claim"
    CAUSAL_EXPLANATION = "causal_explanation"
    DECISION_RATIONALE = "decision_rationale"
    DEONTIC_POLICY = "deontic_policy"
    BOOTSTRAP_REFERENCE = "bootstrap_reference"
    SIGNED_ADMINISTRATIVE_REFERENCE = "signed_administrative_reference"
    OPERATOR_DECISION_RECORD = "operator_decision_record"
    INCIDENT_HUMAN_RECORD = "incident_human_record"
    DEONTIC_KILL_SWITCH_ACTION_RECORD = "deontic_kill_switch_action_record"
    NUMERICS_ARTIFACT_REFERENCE = "numerics_artifact_reference"


class MemoryRecordStatus(StrEnum):
    """The 7-state lifecycle for a MemoryRecord (G §15)."""

    CANDIDATE = "candidate"
    VERIFIED = "verified"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    REJECTED = "rejected"
    EXPIRED = "expired"
    QUARANTINED = "quarantined"


# ---------------------------------------------------------------------------
# Record
# ---------------------------------------------------------------------------


class MemoryRecord(BaseModel):
    """One M2 record.

    Fields:
        record_id:                    unique non-empty identifier
        subject_class:                one of 16 SubjectClass values
        payload:                      type-specific body (non-empty)
        status:                       one of 7 MemoryRecordStatus values
        provenance:                   ProvenanceRef; required
        causal_refs:                  upstream causal chain (record_ids)
        external_corroboration_refs:  external evidence record_ids
        internal_only_refs:           internal-only evidence (L §10 +
                                      P §16 self-deception risk axis)
        created_at_ms:                creation timestamp (>= 0)
        last_status_change_ms:        last lifecycle update (>= created_at_ms)
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    record_id: str = Field(min_length=1)
    subject_class: SubjectClass
    payload: dict[str, Any]
    status: MemoryRecordStatus
    provenance: ProvenanceRef

    causal_refs: tuple[str, ...] = ()
    external_corroboration_refs: tuple[str, ...] = ()
    internal_only_refs: tuple[str, ...] = ()

    created_at_ms: int = Field(ge=0)
    last_status_change_ms: int = Field(ge=0)

    @field_validator("payload")
    @classmethod
    def _payload_non_empty(cls, value: dict[str, Any]) -> dict[str, Any]:
        if not value:
            raise ValueError("MemoryRecord.payload must be non-empty")
        return value

    @model_validator(mode="after")
    def _validate_timestamp_order(self) -> Self:
        if self.last_status_change_ms < self.created_at_ms:
            raise ValueError("last_status_change_ms cannot be before created_at_ms")
        return self
