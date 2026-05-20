"""Soft-overlap linear membership functions (N §6).

Per INGRESS_COMPILER_NUMERICS.md §6: when an ingress event matches a
rule whose condition is a continuous-valued range, the compiler
computes a deterministic membership value in [0.0, 1.0] using a
linear membership function. v0.1 default is **trapezoidal**, which
degenerates to triangular when `peak_low == peak_high`.

Constitutional discipline:
    - Deterministic. Same `(band, value)` ALWAYS produces the same
      membership. No randomness, no LLM, no semantic interpretation
    - Membership in [0.0, 1.0]; outside the band it is exactly 0.0
    - Band shape constraints: low <= peak_low <= peak_high <= high,
      all finite. Violations rejected at construction time (frozen
      Pydantic model)
    - Triangular degeneracy explicit: low == peak_low or
      peak_high == high → vertical shoulder (membership jumps to 1.0
      at the boundary); the formulation handles this with a
      zero-width-shoulder branch
"""

from __future__ import annotations

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class FuzzyBand(BaseModel):
    """Trapezoidal membership band.

    Shape:
                  1.0  _________________
                      /                 \\
                     /                   \\
                  0 /                     \\
                   low  peak_low  peak_high  high

    Triangular special case: peak_low == peak_high.
    Half-open / shoulder special case: peak_low == low (vertical left
    edge) or peak_high == high (vertical right edge).
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    low: float = Field(allow_inf_nan=False)
    peak_low: float = Field(allow_inf_nan=False)
    peak_high: float = Field(allow_inf_nan=False)
    high: float = Field(allow_inf_nan=False)

    @model_validator(mode="after")
    def _validate_monotone(self) -> Self:
        if not (self.low <= self.peak_low <= self.peak_high <= self.high):
            raise ValueError(
                "FuzzyBand requires low <= peak_low <= peak_high <= high; "
                f"got ({self.low}, {self.peak_low}, {self.peak_high}, {self.high})"
            )
        return self


def membership(band: FuzzyBand, value: float) -> float:
    """Return the membership of `value` in `band` in [0.0, 1.0]."""
    if value <= band.low:
        # If the left shoulder is vertical and value is exactly on it,
        # treat as on the plateau.
        if value == band.low and band.peak_low == band.low:
            return 1.0
        return 0.0
    if value >= band.high:
        if value == band.high and band.peak_high == band.high:
            return 1.0
        return 0.0
    if band.peak_low <= value <= band.peak_high:
        return 1.0
    if value < band.peak_low:
        # Rising edge.
        return (value - band.low) / (band.peak_low - band.low)
    # value > band.peak_high
    return (band.high - value) / (band.high - band.peak_high)
