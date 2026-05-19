"""Ingress event envelopes — compiler inputs.

Per WORLD_INGRESS.md §6-11:

Four canonical ingress events feed the deterministic ingress compiler.
Each carries only what the **core** needs to see; raw domain payloads
(symbol, venue, raw text) belong to the observer/provenance side, not
to core-facing ingress envelopes.

    ObservationEvent    — structured observation from the world (C §7)
    HumanIntentEvent    — human/LLM-translator intent stimulus (C §11)
    InternalShockEvent  — core-internal critical shock (C §10)
    RecallEvent         — recall from M2 to core (C §10, H §6)

Constitutional rules enforced here (schema layer only):
    - 4 closed event types (no extras)
    - Bounded finite confidence in [0.0, 1.0]
    - Positive ttl_ms
    - Non-negative occurred_at_ms
    - extra="forbid", frozen=True, strict=True
    - Domain labels (symbol, venue, market, BTC, BTCUSDT, raw_payload,
      intent_text, raw_content) rejected at type boundary

What this module deliberately does NOT do:
    - Compiler mapping to neural_seed (`sentinel/ingress/compiler.py`, Phase 4)
    - Profile cap enforcement (`sentinel/ingress/profile_caps.py`, Phase 4)
    - Source trust calculation (`sentinel/adapters/trust.py`, Phase 9)
    - Staleness dampening (`sentinel/recall/protocol.py`, Phase 8)
    - Recall ranking / suppression (Phase 8)
    - M2 lookup
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Closed event-type enumeration
# ---------------------------------------------------------------------------


class IngressEventType(StrEnum):
    """The 4 canonical ingress event types (closed enumeration)."""

    OBSERVATION = "ObservationEvent"
    HUMAN_INTENT = "HumanIntentEvent"
    INTERNAL_SHOCK = "InternalShockEvent"
    RECALL = "RecallEvent"


# ---------------------------------------------------------------------------
# Supporting enums
# ---------------------------------------------------------------------------


class ShockSource(StrEnum):
    """Source channel that produced an InternalShockEvent."""

    DEONTIC_GATE = "deontic_gate"
    KILL_SWITCH = "kill_switch"
    MEMORY_WRITE_GATE = "memory_write_gate"
    OBSERVER_FAILSAFE = "observer_failsafe"


class ShockSeverity(StrEnum):
    """Severity band for an InternalShockEvent."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecallRecordStatus(StrEnum):
    """Status of the M2 record referenced by a RecallEvent.

    All 7 statuses are schema-valid here. Suppression for
    quarantined / rejected / expired (and superseded historical) is the
    recall protocol's job (Phase 8), not the schema's.
    """

    CANDIDATE = "candidate"
    VERIFIED = "verified"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    EXPIRED = "expired"
    QUARANTINED = "quarantined"
    REJECTED = "rejected"


# ---------------------------------------------------------------------------
# Common base
# ---------------------------------------------------------------------------


class IngressEventBase(BaseModel):
    """Common envelope fields for every ingress event.

    Subclasses set `event_type` to one of the canonical IngressEventType
    values; this base contains only fields shared across all four.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    event_id: str = Field(min_length=1)
    occurred_at_ms: int = Field(ge=0)
    ttl_ms: int = Field(gt=0)
    confidence: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)


# ---------------------------------------------------------------------------
# Four envelopes
# ---------------------------------------------------------------------------


class ObservationEvent(IngressEventBase):
    """Structured observation from the world (C §7).

    Domain payloads (symbol, venue, raw price, ...) live on the
    observer/provenance side. Core-facing observation envelope carries only
    abstract magnitudes the compiler can map deterministically.
    """

    event_type: Literal[IngressEventType.OBSERVATION] = IngressEventType.OBSERVATION
    source_adapter_id: str = Field(min_length=1)
    source_reliability_band: int = Field(ge=0, le=5)
    magnitude_normalized: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    novelty_indicator: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    staleness_ms: int = Field(ge=0)


class HumanIntentEvent(IngressEventBase):
    """Human/LLM-translator intent stimulus (C §11).

    Per Madde 6: raw text never reaches the core directly. The envelope
    carries a hash reference only; raw content (if retained) lives in the
    observer/provenance side under M1 audit discipline.
    """

    event_type: Literal[IngressEventType.HUMAN_INTENT] = IngressEventType.HUMAN_INTENT
    intent_text_hash: str = Field(min_length=1)
    ambiguity_score: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    human_confirmed: bool


class InternalShockEvent(IngressEventBase):
    """Core-internal critical shock (C §10).

    Produced by gates or failsafes; bounded by refractory window so the
    compiler cannot be spammed (N §17).
    """

    event_type: Literal[IngressEventType.INTERNAL_SHOCK] = IngressEventType.INTERNAL_SHOCK
    shock_source: ShockSource
    severity: ShockSeverity
    refractory_key: str = Field(min_length=1)


class RecallEvent(IngressEventBase):
    """Recall from M2 to core (C §10, H §6).

    Core-originated RecallRequest produces this event after mechanical
    ranking. Subject_class is one of the 16 B §3 values; we keep it as a
    string here and let the memory schema (next phase) define the enum.
    """

    event_type: Literal[IngressEventType.RECALL] = IngressEventType.RECALL
    source_record_id: str = Field(min_length=1)
    record_status: RecallRecordStatus
    subject_class: str = Field(min_length=1)
    age_ms: int = Field(ge=0)
    contradiction_risk: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
