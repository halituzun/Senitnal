"""M0 neuron model — receptor profile + homonymous bias epsilon.

Per BOOTSTRAP_GENOME_NUMERICS.md §6 and CONSTITUTION (S §8): a
neuron at birth has a small homonymous bias epsilon and a receptor
profile that does NOT specialize toward any single primer payload —
specialist neurons cannot exist at birth (the bias is small enough
that no payload dominates).

Constitutional discipline (schema-only):
    - Each receptor_profile entry maps a PrimerPayload to a
      sensitivity in [1.0 - epsilon, 1.0 + epsilon]
    - epsilon must be in (0.0, 0.1] (small, S §8)
    - All 10 primer payloads MUST appear in receptor_profile (closed
      coverage; no missing receptor)
    - The max-min sensitivity gap MUST be <= 2 * epsilon (no
      specialist at birth)

What this module deliberately does NOT contain:
    - Charge state (Phase 5 synapse module)
    - Learning / receptor updates
    - Stable-assembly membership
"""

from __future__ import annotations

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sentinel.types.payload import PrimerPayload

HOMONYMOUS_BIAS_EPSILON_MAX: float = 0.10


class Neuron(BaseModel):
    """One M0 neuron with a homonymous-biased receptor profile.

    Fields:
        neuron_id:         non-empty unique identifier
        homonymous_bias_epsilon:
                           bias amplitude in (0.0, 0.10]
        receptor_profile:  one sensitivity per PrimerPayload, each in
                           [1.0 - epsilon, 1.0 + epsilon]
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    neuron_id: str = Field(min_length=1)
    homonymous_bias_epsilon: float = Field(
        gt=0.0, le=HOMONYMOUS_BIAS_EPSILON_MAX, allow_inf_nan=False
    )
    receptor_profile: dict[PrimerPayload, float]

    @model_validator(mode="after")
    def _validate_receptor_profile(self) -> Self:
        all_payloads = set(PrimerPayload)
        if set(self.receptor_profile.keys()) != all_payloads:
            missing = all_payloads - set(self.receptor_profile.keys())
            extra = set(self.receptor_profile.keys()) - all_payloads
            raise ValueError(
                "receptor_profile must cover all PrimerPayload values "
                f"(missing={sorted(p.value for p in missing)!r}, "
                f"extra={sorted(p.value for p in extra)!r})"
            )
        eps = self.homonymous_bias_epsilon
        low_bound = 1.0 - eps
        high_bound = 1.0 + eps
        for payload, sens in self.receptor_profile.items():
            if not (low_bound <= sens <= high_bound):
                raise ValueError(
                    f"receptor_profile[{payload.value!r}] = {sens} outside "
                    f"[{low_bound}, {high_bound}] (epsilon={eps})"
                )
        # No-specialist invariant: max-min gap <= 2*epsilon (already
        # implied by per-key bound; assert explicitly for clarity).
        sens_values = list(self.receptor_profile.values())
        if max(sens_values) - min(sens_values) > 2 * eps + 1e-12:
            raise ValueError(
                "no specialist at birth: receptor sensitivity span "
                f"{max(sens_values) - min(sens_values)} > 2*epsilon={2 * eps}"
            )
        return self
