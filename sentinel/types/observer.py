"""ObserverEvent — M1 audit ledger event envelope.

Per OBSERVER_LEDGER_SCHEMA.md §6-§7 + §19:

ObserverEvent is the canonical wrapper for everything written to the M1
ledger. Every other Sentinel schema's audit trail will reference this
envelope; the hash chain runs through `event_hash` / `previous_event_hash`.

Constitutional rules enforced here (schema layer only):
    - 8 closed EventFamily values
    - event_id, event_type, event_hash non-empty
    - occurred_at_ms non-negative
    - previous_event_hash may be None (first / genesis) at schema layer
    - payload is a non-empty mapping (event body cannot be vacuous)
    - extra="forbid", frozen=True, strict=True

Important ingress-vs-observer asymmetry:
    Core-facing ingress envelopes (events.py) REJECT domain labels
    (symbol, venue, raw_payload, intent_text). ObserverEvent.payload
    INTENTIONALLY allows them — audit ledger must record what really
    happened, including raw provenance. The two layers serve different
    constitutional purposes.

What this module deliberately does NOT do:
    - Canonical event_type catalog validation (Phase 2:
      `sentinel/observer/catalog.py`; F §19 registry)
    - Hash computation / chain verification (Phase 2:
      `sentinel/observer/hash_chain.py`; Q §11 verify_on_read_required)
    - Permanence policy enforcement (Phase 2:
      `sentinel/observer/permanence.py`; F §10 monotonic invariant)
    - JSONL writer / reader (Phase 2: `sentinel/observer/ledger.py`)
    - Snapshot window logic (Phase 2; F §11)
    - M1_READ_AUDIT_RECORDED emission (Phase 2; Q §15)
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from sentinel.types.neural_seed import ProvenanceRef  # noqa: TC001 (Pydantic runtime needs)

# ---------------------------------------------------------------------------
# Closed event-family enumeration (F §19)
# ---------------------------------------------------------------------------


class EventFamily(StrEnum):
    """The 8 canonical observer event families."""

    NEURAL = "neural"
    ATTENTION = "attention"
    MEMORY = "memory"
    INGRESS = "ingress"
    BOOTSTRAP = "bootstrap"
    DEONTIC = "deontic"
    REPLAY = "replay"
    LEDGER_META = "ledger_meta"


# ---------------------------------------------------------------------------
# Envelope
# ---------------------------------------------------------------------------


class ObserverEvent(BaseModel):
    """One immutable audit-ledger entry.

    Fields:
        event_id:            unique non-empty identifier
        event_family:        one of 8 EventFamily values
        event_type:          canonical event name (string; catalog validation
                             in Phase 2)
        occurred_at_ms:      timestamp; non-negative
        payload:             non-empty mapping; type-specific schema validated
                             in Phase 2 (F §19 catalog)
        provenance:          ProvenanceRef linking to the originating event
        previous_event_hash: hash of the previous event in the chain;
                             None for genesis events at schema layer
                             (chain integrity is Phase 2's job)
        event_hash:          non-empty self hash (computation is Phase 2)
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    event_id: str = Field(min_length=1)
    event_family: EventFamily
    event_type: str = Field(min_length=1)
    occurred_at_ms: int = Field(ge=0)

    payload: dict[str, Any]
    provenance: ProvenanceRef

    previous_event_hash: str | None = None
    event_hash: str = Field(min_length=1)

    @field_validator("payload")
    @classmethod
    def _payload_non_empty(cls, value: dict[str, Any]) -> dict[str, Any]:
        if not value:
            raise ValueError("ObserverEvent.payload must be non-empty")
        return value
