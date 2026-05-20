"""M0 synapse — initial weak band + read-only charge propagation.

Per CONSTITUTION (S §7) and the Phase 5 build plan: every synapse at
birth has a small initial weight in the "weak band" (well below the
stable-path threshold). MVP learning is OFF — the synapse weight is
not mutated by charge propagation; propagation is a read-only
function that returns the effective charge a synapse transmits given
its weight and the presynaptic charge.

Constitutional discipline (schema-only):
    - Initial weight in (0.0, INITIAL_WEAK_BAND_MAX]
      (S §7: 0.0 < w_init <= 0.15; centre around 0.10)
    - STABLE_PATH_THRESHOLD = 0.5; initial weight < threshold is a
      hard schema invariant
    - propagate_charge(synapse, presynaptic_charge) returns
      `synapse.weight * presynaptic_charge` clamped to [0.0, 1.0];
      it never mutates synapse state
    - MVP_LEARNING_ENABLED = False; reserved for the runtime layer
      to consult before any future weight update path

What this module deliberately does NOT contain:
    - Weight updates / Hebbian learning (Phase 9+ when learning_enabled flips)
    - Refractory periods
    - Multi-step propagation through neuron chains (Phase 5
      assembly / tissue modules)
"""

from __future__ import annotations

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

INITIAL_WEAK_BAND_MIN: float = 0.0
INITIAL_WEAK_BAND_MAX: float = 0.15
STABLE_PATH_THRESHOLD: float = 0.50
MVP_LEARNING_ENABLED: bool = False


class Synapse(BaseModel):
    """One directed synapse with a weak initial weight (MVP).

    Fields:
        synapse_id:               non-empty unique identifier
        presynaptic_neuron_id:    source neuron
        postsynaptic_neuron_id:   target neuron (distinct from presynaptic)
        weight:                   in (0.0, INITIAL_WEAK_BAND_MAX]
                                  and < STABLE_PATH_THRESHOLD
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    synapse_id: str = Field(min_length=1)
    presynaptic_neuron_id: str = Field(min_length=1)
    postsynaptic_neuron_id: str = Field(min_length=1)
    weight: float = Field(
        gt=INITIAL_WEAK_BAND_MIN,
        le=INITIAL_WEAK_BAND_MAX,
        allow_inf_nan=False,
    )

    @model_validator(mode="after")
    def _validate_no_self_loop(self) -> Self:
        if self.presynaptic_neuron_id == self.postsynaptic_neuron_id:
            raise ValueError(
                f"Synapse pre and post neuron_id must differ (got {self.presynaptic_neuron_id!r})"
            )
        return self

    @model_validator(mode="after")
    def _validate_weight_below_stable_threshold(self) -> Self:
        # Already enforced by INITIAL_WEAK_BAND_MAX < STABLE_PATH_THRESHOLD,
        # but kept explicit as a constitutional invariant check so a
        # future loosening of the band ceiling is caught here.
        if self.weight >= STABLE_PATH_THRESHOLD:
            raise ValueError(
                f"initial weight {self.weight} >= STABLE_PATH_THRESHOLD "
                f"{STABLE_PATH_THRESHOLD} (S §7)"
            )
        return self


def propagate_charge(synapse: Synapse, presynaptic_charge: float) -> float:
    """Pure-function charge propagation. Returns weight*charge in [0,1].

    Raises ValueError if presynaptic_charge is outside [0.0, 1.0] or
    non-finite.
    """
    if not (0.0 <= presynaptic_charge <= 1.0):
        raise ValueError(f"presynaptic_charge {presynaptic_charge!r} outside [0.0, 1.0]")
    transmitted = synapse.weight * presynaptic_charge
    # Clamp to [0,1] for safety; with weak band weight*charge<=0.15.
    return max(0.0, min(1.0, transmitted))
