"""Numerics governance enums and dependency models.

Per NUMERICS_GOVERNANCE.md §6-12 and the patch rounds applied through
phase closure:

This module pins the closed enumerations (Commit 7a) and the
AllowedRange + NumericDependency schemas (Commit 7b) that every numerics
artifact must use. NumericEntry and NumericsArtifact land in 7c → 7d.

Constitutional discipline:
    - Each enum is a closed set; widening requires spec revision
    - Legacy / pre-patch vocabulary (higher_is_weaker, forbidden_in_v0_1,
      numerics_family, low_band) is REJECTED at the type boundary
    - 8 spec_family values (1 per numerics artifact N-U); M itself is a
      meta-spec and does NOT have its own numerics artifact family
    - AllowedRange has 3 variants (min_max / set / single) discriminated
      by `kind` field; immutable single-value constitutional invariants
      use the `single` variant
    - NumericDependency enforces conditional factor / expression presence
      depending on relationship type

What this module deliberately does NOT contain:
    - NumericEntry (Commit 7c)
    - NumericsArtifact (Commit 7d)
    - CompatibilityClass (Commit 7d alongside artifact metadata)
    - No-default rule enforcement (Phase 3 loader)
    - Dependency expression evaluation (Phase 3 validator)
    - Cycle detection in dependencies (Phase 3)
"""

from __future__ import annotations

import math
from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class NumericUnit(StrEnum):
    """Closed set of numeric units (M §8 NumericEntry schema)."""

    COUNT = "count"
    MS = "ms"
    BYTES = "bytes"
    RATIO = "ratio"
    PERCENTAGE = "percentage"
    ENUM = "enum"
    ENUM_SET = "enum_set"
    BAND_NAME = "band_name"
    BOOL = "bool"


class Directionality(StrEnum):
    """How tightening / loosening a key affects safety (M §10)."""

    HIGHER_IS_STRICTER = "higher_is_stricter"
    LOWER_IS_STRICTER = "lower_is_stricter"
    BIDIRECTIONAL_SENSITIVE = "bidirectional_sensitive"
    NEUTRAL = "neutral"


class ChangeClass(StrEnum):
    """Compatibility class for a numeric change (M §7).

    Patched through phase closure. Legacy values such as
    `forbidden_in_v0_1` are NOT in this enum; they collapse to
    `forbidden`. U patches normalized `genesis_affecting` as a shift
    class; it lives here too.
    """

    CLARIFICATION = "clarification"
    OPERATIONAL_NO_BEHAVIOR_CHANGE = "operational_no_behavior_change"
    SAFETY_TIGHTENING = "safety_tightening"
    SAFETY_WEAKENING = "safety_weakening"
    GENESIS_AFFECTING = "genesis_affecting"
    FORBIDDEN = "forbidden"


class NumericRiskFamily(StrEnum):
    """Risk family for a numeric (M §5; 6 closed families)."""

    SAFETY_CRITICAL = "safety_critical"
    RESOURCE_LIMITS = "resource_limits"
    CALIBRATION_BANDS = "calibration_bands"
    IDENTITY_RETENTION = "identity_retention"
    OPERATIONAL_CONVENIENCE = "operational_convenience"
    EXPERIMENTAL = "experimental"


class RelationshipType(StrEnum):
    """NumericDependency relationship types (M §12, patch-applied).

    9 canonical values. Patches added the four `_or_equal` and `computed_*`
    forms; pre-patch vocabulary (e.g. plain `computed_less_than` without
    `_or_equal`) is NOT canonical and is rejected here.

    `computed_less_than_or_equal` / `computed_greater_than_or_equal` require
    the `expression` field on the NumericDependency (Commit 7b will model
    this requirement).
    """

    IMPLIES_MINIMUM_OF = "implies_minimum_of"
    MUST_BE_WITHIN_FACTOR_OF = "must_be_within_factor_of"
    MUST_BE_LESS_THAN = "must_be_less_than"
    MUST_BE_GREATER_THAN = "must_be_greater_than"
    MUST_BE_LESS_THAN_OR_EQUAL = "must_be_less_than_or_equal"
    MUST_BE_GREATER_THAN_OR_EQUAL = "must_be_greater_than_or_equal"
    COMPUTED_LESS_THAN_OR_EQUAL = "computed_less_than_or_equal"
    COMPUTED_GREATER_THAN_OR_EQUAL = "computed_greater_than_or_equal"
    MUST_CHANGE_TOGETHER = "must_change_together"


class SpecFamily(StrEnum):
    """Numerics artifact owning specifications (8 closed families).

    One per numerics artifact (N-U). NUMERICS_GOVERNANCE itself is the
    meta-spec and does NOT have its own numerics artifact family; it
    governs the others.
    """

    INGRESS_COMPILER = "ingress_compiler"
    REPLAY_PROTOCOL = "replay_protocol"
    MEMORY_WRITE_GATE = "memory_write_gate"
    OBSERVER_LEDGER = "observer_ledger"
    BACKUP_STRATEGY = "backup_strategy"
    BOOTSTRAP_GENOME = "bootstrap_genome"
    RECALL_PROTOCOL = "recall_protocol"
    ADAPTER_TRUST = "adapter_trust"


# ---------------------------------------------------------------------------
# AllowedRange — discriminated union of three variants
# ---------------------------------------------------------------------------


# Scalar values permitted inside AllowedRangeSet / AllowedRangeSingle.
# bool comes before int by Pydantic convention because bool is a subclass
# of int; the union order matters for strict-mode discrimination.
_ScalarValue = bool | int | float | str


def _is_finite_scalar(value: _ScalarValue) -> bool:
    """Reject NaN / +inf / -inf for numeric scalars."""
    if isinstance(value, float):
        return math.isfinite(value)
    return True


class AllowedRangeMinMax(BaseModel):
    """Closed numeric interval [min, max].

    Used by most NumericEntry definitions (e.g. ratio in [0.0, 1.0],
    ms in [60_000, 86_400_000]).
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    kind: Literal["min_max"] = "min_max"
    min: int | float
    max: int | float

    @model_validator(mode="after")
    def _validate_bounds(self) -> Self:
        if isinstance(self.min, float) and not math.isfinite(self.min):
            raise ValueError("AllowedRangeMinMax.min must be finite")
        if isinstance(self.max, float) and not math.isfinite(self.max):
            raise ValueError("AllowedRangeMinMax.max must be finite")
        if self.max < self.min:
            raise ValueError("AllowedRangeMinMax.max must be >= min")
        return self


class AllowedRangeSet(BaseModel):
    """Closed set of permitted values (e.g. enum / enum_set / band_name).

    Used by NumericEntry whose unit is `enum`, `enum_set`, or `band_name`
    (e.g. `allowed_range: {linear, sigmoid, step}` for membership function).
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    kind: Literal["set"] = "set"
    values: tuple[_ScalarValue, ...]

    @model_validator(mode="after")
    def _validate_values(self) -> Self:
        if len(self.values) == 0:
            raise ValueError("AllowedRangeSet.values must be non-empty")
        if len(set(self.values)) != len(self.values):
            raise ValueError("AllowedRangeSet.values must not contain duplicates")
        for v in self.values:
            if not _is_finite_scalar(v):
                raise ValueError("AllowedRangeSet.values cannot contain NaN or inf")
        return self


class AllowedRangeSingle(BaseModel):
    """Single permitted value — constitutional immutable shape.

    Used by `{tek_değer}` invariants such as:
        - lossless_required = true
        - chain_gap_tolerance_events = 0
        - replay_can_trigger_replay_max_chain_depth = 0
        - epistemic_staleness_threshold tier_cold.retention_ms = lifetime
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    kind: Literal["single"] = "single"
    value: _ScalarValue

    @model_validator(mode="after")
    def _validate_value(self) -> Self:
        if not _is_finite_scalar(self.value):
            raise ValueError("AllowedRangeSingle.value cannot be NaN or inf")
        return self


AllowedRange = Annotated[
    AllowedRangeMinMax | AllowedRangeSet | AllowedRangeSingle,
    Field(discriminator="kind"),
]


# ---------------------------------------------------------------------------
# NumericDependency — per M §12 (patch-applied)
# ---------------------------------------------------------------------------


_RELATIONSHIPS_REQUIRING_EXPRESSION: frozenset[RelationshipType] = frozenset(
    {
        RelationshipType.COMPUTED_LESS_THAN_OR_EQUAL,
        RelationshipType.COMPUTED_GREATER_THAN_OR_EQUAL,
    }
)

_RELATIONSHIPS_REQUIRING_FACTOR: frozenset[RelationshipType] = frozenset(
    {
        RelationshipType.MUST_BE_WITHIN_FACTOR_OF,
    }
)


class NumericDependency(BaseModel):
    """One dependency between two NumericEntry keys (M §12).

    Conditional field requirements (validator-enforced):
        - relationship in {computed_less_than_or_equal,
                           computed_greater_than_or_equal}
          → `expression` REQUIRED, `factor` FORBIDDEN
        - relationship == must_be_within_factor_of
          → `factor` REQUIRED (positive finite), `expression` FORBIDDEN
        - any other relationship
          → `factor` and `expression` BOTH FORBIDDEN

    No dependency evaluation, no cycle detection, no key existence check
    happens here; those are Phase 3 (numerics loader / validator).
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    target_key: str = Field(min_length=1)
    relationship: RelationshipType
    factor: float | None = Field(default=None, gt=0.0, allow_inf_nan=False)
    expression: str | None = Field(default=None, min_length=1)
    rationale: str = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_conditional_fields(self) -> Self:
        rel = self.relationship

        if rel in _RELATIONSHIPS_REQUIRING_EXPRESSION:
            if self.expression is None:
                raise ValueError(f"relationship {rel.value!r} requires `expression`")
            if self.factor is not None:
                raise ValueError(f"relationship {rel.value!r} forbids `factor`")
        elif rel in _RELATIONSHIPS_REQUIRING_FACTOR:
            if self.factor is None:
                raise ValueError(f"relationship {rel.value!r} requires `factor`")
            if self.expression is not None:
                raise ValueError(f"relationship {rel.value!r} forbids `expression`")
        else:
            if self.expression is not None:
                raise ValueError(f"relationship {rel.value!r} forbids `expression`")
            if self.factor is not None:
                raise ValueError(f"relationship {rel.value!r} forbids `factor`")

        return self
