"""M0 proto-resonance 5-layer constitutional protection (S §9).

Per CONSTITUTION (S §9) and the Phase 5 build plan: at MVP birth no
proto-resonance pattern may stabilize into an assembly, gain
recallability, or become memory-write eligible. This module pins
the 5-layer invariant in the type system so any value that violates
the bound is rejected at the schema boundary.

5 layers:
    1. recallability == 0.0
    2. assembly_id_at_birth is None
    3. persistence_max_ms < STABLE_ASSEMBLY_MIN_PERSISTENCE_MS
    4. stability_score_cap < ASSEMBLY_STABILIZATION_THRESHOLD
    5. memory_write_eligibility is False

Constants (v0.1 dev band centers):
    STABLE_ASSEMBLY_MIN_PERSISTENCE_MS = 30_000
    ASSEMBLY_STABILIZATION_THRESHOLD = 0.75
"""

from __future__ import annotations

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

STABLE_ASSEMBLY_MIN_PERSISTENCE_MS: int = 30_000
ASSEMBLY_STABILIZATION_THRESHOLD: float = 0.75


class ProtoResonance(BaseModel):
    """A proto-resonance pattern subject to the 5-layer birth invariants."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    pattern_id: str = Field(min_length=1)
    recallability: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    assembly_id_at_birth: str | None
    persistence_max_ms: int = Field(ge=0)
    stability_score_cap: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    memory_write_eligibility: bool

    @model_validator(mode="after")
    def _validate_layer1_recallability_zero(self) -> Self:
        if self.recallability != 0.0:
            raise ValueError(
                f"S §9 layer 1: recallability must be 0.0 at MVP birth; got {self.recallability}"
            )
        return self

    @model_validator(mode="after")
    def _validate_layer2_no_assembly_at_birth(self) -> Self:
        if self.assembly_id_at_birth is not None:
            raise ValueError(
                "S §9 layer 2: assembly_id_at_birth must be None at MVP birth; "
                f"got {self.assembly_id_at_birth!r}"
            )
        return self

    @model_validator(mode="after")
    def _validate_layer3_persistence_below_stable(self) -> Self:
        if self.persistence_max_ms >= STABLE_ASSEMBLY_MIN_PERSISTENCE_MS:
            raise ValueError(
                f"S §9 layer 3: persistence_max_ms {self.persistence_max_ms} "
                f">= STABLE_ASSEMBLY_MIN_PERSISTENCE_MS "
                f"{STABLE_ASSEMBLY_MIN_PERSISTENCE_MS}"
            )
        return self

    @model_validator(mode="after")
    def _validate_layer4_stability_score_below_threshold(self) -> Self:
        if self.stability_score_cap >= ASSEMBLY_STABILIZATION_THRESHOLD:
            raise ValueError(
                f"S §9 layer 4: stability_score_cap {self.stability_score_cap} "
                f">= ASSEMBLY_STABILIZATION_THRESHOLD "
                f"{ASSEMBLY_STABILIZATION_THRESHOLD}"
            )
        return self

    @model_validator(mode="after")
    def _validate_layer5_memory_write_disabled(self) -> Self:
        if self.memory_write_eligibility is not False:
            raise ValueError(
                "S §9 layer 5: memory_write_eligibility must be False at "
                f"MVP birth; got {self.memory_write_eligibility}"
            )
        return self
