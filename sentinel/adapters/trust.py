"""AdapterTrustRecord + multiplicative composition + hard-gate guard.

Per ADAPTER_TRUST_NUMERICS.md §6 and the Phase 9 build plan: every
adapter has a single `AdapterTrustRecord` carrying a small set of
**hard gates** (must pass exactly) plus a vector of **soft scores**
(each in [0.0, 1.0]) whose product becomes the composite trust
score.

Hard gates (any failure → REVOKED, composite score = 0.0):
    - signature_validity         (must be True)
    - manifest_hash_integrity    (must be True)
    - neural_seed_emission_count (must be == 0; one emission is a
                                  constitutional breach that
                                  irrevocably revokes trust)

Soft scores (in [0.0, 1.0]):
    - channel_binding_compliance
    - rate_compliance
    - declaration_drift
    - reliability_score

Composite trust score is multiplicative across all soft scores.

TrustBand bands (v0.1 dev fixture thresholds; see
adapter_trust_numerics_v0_dev_fixture.json):
    REVOKED       composite == 0.0 OR any hard gate failed
    QUARANTINED   0.0 < composite < 0.3
    LOW           0.3 <= composite < 0.5
    MEDIUM        0.5 <= composite < 0.8
    HIGH          composite >= 0.8

Constitutional discipline:
    - Hard gates are non-negotiable; their failure forces composite
      to 0.0 regardless of the soft score product
    - `compute_trust` is pure
    - A neural_seed_emission_count > 0 raises
      InvariantViolation(ADAPTER_NEURAL_SEED_EMISSION_DETECTED)
      because this is a constitutional red line, not a soft score
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sentinel.constitution.violations import InvariantViolation, ViolationContext


class TrustBand(StrEnum):
    """Trust band classification (v0.1 dev thresholds)."""

    REVOKED = "revoked"
    QUARANTINED = "quarantined"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AdapterTrustRecord(BaseModel):
    """One adapter's hard gates + soft scores snapshot."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    adapter_id: str = Field(min_length=1)

    # Hard gates
    signature_validity: bool
    manifest_hash_integrity: bool
    neural_seed_emission_count: int = Field(ge=0)

    # Soft scores
    channel_binding_compliance: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    rate_compliance: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    declaration_drift: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    reliability_score: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)

    @model_validator(mode="after")
    def _validate_no_neural_seed_emission(self) -> Self:
        if self.neural_seed_emission_count > 0:
            raise InvariantViolation(
                (
                    f"adapter {self.adapter_id!r} has "
                    f"neural_seed_emission_count="
                    f"{self.neural_seed_emission_count} > 0; constitutional "
                    "red line (ADAPTER_TRUST_NUMERICS.md §6)"
                ),
                ViolationContext(
                    violation_code="ADAPTER_NEURAL_SEED_EMISSION_DETECTED",
                    source_ref="ADAPTER_TRUST_NUMERICS.md §6",
                    evidence={
                        "adapter_id": self.adapter_id,
                        "neural_seed_emission_count": (self.neural_seed_emission_count),
                    },
                ),
            )
        return self


@dataclass(frozen=True, slots=True)
class TrustComputation:
    composite_score: float
    band: TrustBand
    hard_gates_passed: bool


def _classify(composite: float, *, hard_gates_passed: bool) -> TrustBand:
    if not hard_gates_passed or composite == 0.0:
        return TrustBand.REVOKED
    if composite < 0.3:
        return TrustBand.QUARANTINED
    if composite < 0.5:
        return TrustBand.LOW
    if composite < 0.8:
        return TrustBand.MEDIUM
    return TrustBand.HIGH


def compute_trust(record: AdapterTrustRecord) -> TrustComputation:
    """Combine hard gates + multiplicative soft-score product."""
    hard_gates_passed = (
        record.signature_validity and record.manifest_hash_integrity
        # neural_seed_emission_count is already validated to be 0 at
        # the schema layer; if we got here, that gate passes too.
    )
    if not hard_gates_passed:
        return TrustComputation(
            composite_score=0.0,
            band=TrustBand.REVOKED,
            hard_gates_passed=False,
        )
    composite = (
        record.channel_binding_compliance
        * record.rate_compliance
        * record.declaration_drift
        * record.reliability_score
    )
    return TrustComputation(
        composite_score=composite,
        band=_classify(composite, hard_gates_passed=True),
        hard_gates_passed=True,
    )
