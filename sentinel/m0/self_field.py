"""M0 embryo self-field weight bands (S §11).

Per CONSTITUTION (S §11) and the Phase 5 build plan: the M0 embryo
exposes a three-component self-field whose weights satisfy a strict
hierarchy at birth:

    homeostatic_weight > predictive_weight > narrative_weight

All three are positive, finite, and (by convention) sum to a value
in (0.0, 1.0]. The schema does NOT force normalization to exactly
1.0 — the spec only requires that the strict-greater hierarchy
holds and that all weights are positive.

Constitutional invariants enforced at the schema boundary:
    - All three weights > 0.0 and <= 1.0
    - Strict hierarchy: homeostatic > predictive > narrative
    - Sum <= 1.0 (no over-budget self-field at birth)

What this module deliberately does NOT contain:
    - Self-field update math (learning OFF in MVP)
    - Coupling to assembly stability scoring
    - Forced renormalization (allowed loose; loader / runtime can
      normalize if desired, but the schema does not)
"""

from __future__ import annotations

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EmbryoSelfField(BaseModel):
    """The M0 embryo self-field with constitutional weight hierarchy."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    homeostatic_weight: float = Field(gt=0.0, le=1.0, allow_inf_nan=False)
    predictive_weight: float = Field(gt=0.0, le=1.0, allow_inf_nan=False)
    narrative_weight: float = Field(gt=0.0, le=1.0, allow_inf_nan=False)

    @model_validator(mode="after")
    def _validate_strict_hierarchy(self) -> Self:
        if not (self.homeostatic_weight > self.predictive_weight > self.narrative_weight):
            raise ValueError(
                "self-field strict hierarchy violated (S §11): "
                f"homeostatic={self.homeostatic_weight}, "
                f"predictive={self.predictive_weight}, "
                f"narrative={self.narrative_weight}; required "
                "homeostatic > predictive > narrative"
            )
        return self

    @model_validator(mode="after")
    def _validate_sum_within_budget(self) -> Self:
        s = self.homeostatic_weight + self.predictive_weight + self.narrative_weight
        if s > 1.0 + 1e-12:
            raise ValueError(f"self-field weight sum {s} exceeds 1.0 (over-budget)")
        return self
