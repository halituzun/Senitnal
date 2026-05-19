"""WorkspacePulseEvent — the single attention-workspace event type.

Per BOOTSTRAP_GENOME §B (attention workspace) and the constitution's
core invariant:

    There is no pulse type. There is a pulse signature.

This module pins the schema for the **one and only** workspace-pulse
event type the system may emit. The character of a pulse — focus,
contradiction, recall, intention, etc. — is expressed through the
`dominant_payload_mix` (which primer payloads dominated the assembly),
NOT through a `pulse_type` / `pulse_category` enum. Adding such an
enum would re-introduce a closed taxonomy that the constitution
explicitly refuses.

Constitutional discipline enforced here (schema layer only):
    - event_type is the literal "WORKSPACE_PULSE"; no other values
    - dominant_payload_mix is the pulse *signature*, non-empty, with
      no duplicate primer payloads
    - All quality fields are bounded in [0.0, 1.0] and finite
      (no NaN, no ±inf)
    - ttl_ms is strictly positive
    - Domain labels (BTC, BTCUSDT, BUY, SELL, ...) are rejected at
      construction time via extra="forbid"

What this module deliberately does NOT contain:
    - Pulse scoring algorithm (Phase 5 attention workspace)
    - Pulse allocation logic (Phase 5)
    - Replay habituation update math (Phase 7)
    - Attention-workspace runtime / assembly construction
    - `pulse_type` / `pulse_category` enums (forbidden by constitution)
"""

from __future__ import annotations

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sentinel.types.payload import PayloadSeed  # noqa: TC001 (Pydantic runtime needs)


class WorkspacePulseEvent(BaseModel):
    """The single workspace pulse event type (B §attention workspace).

    Schema-layer invariants enforced:
        - event_type pinned to "WORKSPACE_PULSE" via Literal
        - pulse_id / assembly_id / context_signature_hash non-empty
        - occurred_at_ms >= 0
        - dominant_payload_mix non-empty, no duplicate primer payloads
          (the mix IS the pulse signature)
        - 7 bounded quality scores in [0.0, 1.0], finite
        - ttl_ms strictly > 0
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    event_type: Literal["WORKSPACE_PULSE"] = "WORKSPACE_PULSE"
    pulse_id: str = Field(min_length=1)
    assembly_id: str = Field(min_length=1)
    occurred_at_ms: int = Field(ge=0)

    dominant_payload_mix: tuple[PayloadSeed, ...]

    activation_mass: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    coherence: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    persistence: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    habituation_penalty: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    fatigue_penalty: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    dissonance_score: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    allocation_share: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)

    ttl_ms: int = Field(gt=0)
    context_signature_hash: str = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_dominant_payload_mix(self) -> Self:
        if len(self.dominant_payload_mix) == 0:
            raise ValueError(
                "dominant_payload_mix must contain at least one PayloadSeed "
                "(the mix is the pulse signature)"
            )
        seen_payloads = {seed.payload for seed in self.dominant_payload_mix}
        if len(seen_payloads) != len(self.dominant_payload_mix):
            raise ValueError("dominant_payload_mix must not contain duplicate primer payloads")
        return self
