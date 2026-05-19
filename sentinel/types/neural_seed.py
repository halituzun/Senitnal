"""NeuralSeed — composed mental colors as one core-facing payload.

Per INGRESS_COMPILER_SPEC §4-12 + INGRESS_COMPILER_NUMERICS §7:

A NeuralSeed is the **output of the ingress compiler** — what the core
actually receives. It composes multiple PayloadSeed entries (one per primer
payload color) into a single immutable structure tagged with its
event_profile (which ingress channel it came through).

Constitutional rules enforced here (schema layer only):
    - payload_seed is non-empty
    - Every PrimerPayload value appears at most once
    - total_intensity is computed from entries (NOT input)
    - event_profile is one of 6 canonical channels
    - provenance ref is required
    - extra="forbid", frozen=True, strict=True

What this module deliberately does NOT do:
    - Profile cap enforcement (lives in `sentinel/ingress/profile_caps.py`,
      Phase 4; uses INGRESS_COMPILER_NUMERICS dev fixture values)
    - Weighted blend / cap order (lives in `sentinel/ingress/compiler.py`)
    - Forced normalization (forbidden by N §12; not introduced here)
    - Adapter / source trust semantics (live in `sentinel/adapters/trust.py`)
    - Event envelope (lives in `sentinel/types/events.py`)

The constitutional hierarchy among profiles (N §7):
    ObservationEvent
        >= InternalShockEvent (refractory-protected)
        >= RecallEvent.active
        >= RecallEvent.verified
        >= HumanIntentEvent
        >= CandidateRecall

is enforced by Phase 4 (compiler), NOT at this type boundary.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, computed_field, model_validator

from sentinel.types.payload import PayloadSeed  # noqa: TC001 (Pydantic runtime needs)


class EventProfile(StrEnum):
    """The 6 canonical ingress event profiles (closed enumeration).

    Profile values use the same dotted form as INGRESS_COMPILER_NUMERICS §7
    (e.g., ``RecallEvent.active``, ``RecallEvent.verified``) to keep
    cross-document identifiers stable.
    """

    OBSERVATION_EVENT = "ObservationEvent"
    INTERNAL_SHOCK_EVENT = "InternalShockEvent"
    RECALL_EVENT_ACTIVE = "RecallEvent.active"
    RECALL_EVENT_VERIFIED = "RecallEvent.verified"
    HUMAN_INTENT_EVENT = "HumanIntentEvent"
    CANDIDATE_RECALL = "CandidateRecall"


class ProvenanceRef(BaseModel):
    """Minimal provenance reference for traceability.

    Hash chain, signed signatures and audit-chain detail land in the
    Observer ledger phase (Phase 2). Here we only require enough to trace
    a NeuralSeed back to its originating event id.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    source_event_id: str
    source_spec: str | None = None


class NeuralSeed(BaseModel):
    """Composed core-facing payload at one ingress channel.

    Fields:
        event_profile: one of 6 canonical EventProfile values
        payload_seed:  non-empty tuple of unique PayloadSeed entries
                       (each primer payload appears at most once)
        provenance:    required ProvenanceRef for traceability

    Computed:
        total_intensity: sum of intensities across payload_seed (read-only)
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    event_profile: EventProfile
    payload_seed: tuple[PayloadSeed, ...]
    provenance: ProvenanceRef

    @model_validator(mode="after")
    def _validate_payload_seed(self) -> NeuralSeed:
        if len(self.payload_seed) == 0:
            raise ValueError("payload_seed must be non-empty")

        seen: set[str] = set()
        for seed in self.payload_seed:
            key = seed.payload.value
            if key in seen:
                raise ValueError(f"duplicate primer payload in NeuralSeed: {key!r}")
            seen.add(key)

        return self

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_intensity(self) -> float:
        """Sum of intensities across payload_seed entries.

        Bounded by sum of PayloadSeed.intensity each in [0, 1]; thus
        total_intensity ∈ [0, len(payload_seed)]. Profile cap enforcement
        is the compiler's job (Phase 4), not this schema's.
        """
        return sum(seed.intensity for seed in self.payload_seed)
