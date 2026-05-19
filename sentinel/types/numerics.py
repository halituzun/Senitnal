"""Numerics governance enums, ranges, dependencies, and entry schema.

Per NUMERICS_GOVERNANCE.md §6-12 and the patch rounds applied through
phase closure:

This module pins the closed enumerations (Commit 7a), the
AllowedRange + NumericDependency schemas (Commit 7b), the
NumericEntry schema (Commit 7c), and the NumericsArtifact
container (Commit 7d) that completes the Phase 1 numerics schema.

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
    - NumericEntry enforces M §9 no-default rule (12 required fields,
      `dependencies` may be `()` but the field itself is required) and
      schema-level value/unit/allowed_range compatibility
    - NumericsArtifact bundles entries belonging to one spec_family;
      enforces non-empty entries, unique keys, spec_family consistency
      between artifact and entries, and the dev_only ↔ fixture_purpose
      two-way invariant. `signed=False` with `dev_only=False` is
      accepted at the schema layer (signature policy is a loader
      concern landing in Phase 3)
    - CompatibilityClass is intentionally narrower than ChangeClass:
      it carries the artifact-level change posture (clarification /
      safety_tightening / safety_weakening / genesis_affecting). It
      does NOT include `constitutional_amendment` — amendments are a
      separate workflow, not a compatibility class on a numerics
      artifact

What this module deliberately does NOT contain:
    - No-default rule enforcement at the loader (Phase 3)
    - Dependency expression evaluation (Phase 3 validator)
    - Cycle detection in dependencies (Phase 3)
    - Cross-key dependency resolution (Phase 3)
    - Signature verification (Phase 3 loader)
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


# ---------------------------------------------------------------------------
# NumericEntry — per M §8 no-default rule
# ---------------------------------------------------------------------------


# Value union covers every NumericUnit variant including enum_set (tuple of
# canonical strings). Order matters for Pydantic strict-mode dispatch —
# bool comes before int because bool is a subclass of int, and tuple comes
# last so scalars take precedence.
NumericValue = bool | int | float | str | tuple[str, ...]


_INT_UNITS: frozenset[NumericUnit] = frozenset(
    {NumericUnit.COUNT, NumericUnit.MS, NumericUnit.BYTES}
)
_FLOAT_UNITS: frozenset[NumericUnit] = frozenset({NumericUnit.RATIO, NumericUnit.PERCENTAGE})
_STR_UNITS: frozenset[NumericUnit] = frozenset({NumericUnit.ENUM, NumericUnit.BAND_NAME})


def _value_type_compatible(value: NumericValue, unit: NumericUnit) -> bool:
    """Check that a value's concrete Python type matches the declared unit."""
    if unit is NumericUnit.BOOL:
        return type(value) is bool
    if unit in _INT_UNITS:
        return type(value) is int  # exclude bool, which is an int subclass
    if unit in _FLOAT_UNITS:
        if type(value) is bool:
            return False
        return isinstance(value, int | float) and (
            not isinstance(value, float) or math.isfinite(value)
        )
    if unit in _STR_UNITS:
        return isinstance(value, str)
    if unit is NumericUnit.ENUM_SET:
        # Pydantic strict mode has already validated `tuple[str, ...]` shape
        # at the field-coercion boundary; here we only need to confirm the
        # value reached this validator as a tuple rather than as a scalar.
        return isinstance(value, tuple)
    return False  # exhaustive


def _value_in_min_max(value: NumericValue, rng: AllowedRangeMinMax) -> bool:
    if not isinstance(value, int | float) or isinstance(value, bool):
        return False
    return rng.min <= value <= rng.max


def _value_in_set(value: NumericValue, rng: AllowedRangeSet) -> bool:
    return value in rng.values


def _enum_set_in_set(value: tuple[str, ...], rng: AllowedRangeSet) -> bool:
    """Every member of the entry's tuple must appear in the allowed set."""
    return all(item in rng.values for item in value)


def _value_equal_single(value: NumericValue, rng: AllowedRangeSingle) -> bool:
    return value == rng.value


class NumericEntry(BaseModel):
    """One numeric entry in a NumericsArtifact (M §8 — no-default rule).

    Every field is required at construction time. `dependencies` may be
    an empty tuple `()`, but the field itself must be supplied by the
    caller — no implicit default applies to absent declaration.

    Schema-level guarantees (validators):
        - value's concrete Python type matches the declared unit
          (bool ↔ BOOL; int ↔ COUNT/MS/BYTES; int|float ↔ RATIO/PERCENTAGE;
           str ↔ ENUM/BAND_NAME; tuple[str, ...] ↔ ENUM_SET)
        - value is inside allowed_range:
            MinMax  → min <= value <= max
            Set     → value (scalar) OR every value-member (enum_set) ∈ values
            Single  → value == range.value
        - enum_set requires AllowedRangeSet; non-empty; no duplicates
        - Constitutional immutable consistency:
            single allowed_range ⇔ both change_class fields == FORBIDDEN
            (one without the other is a schema error)

    What this entry does NOT validate (later phases):
        - Cross-key dependency resolution (Phase 3 loader)
        - Dependency expression semantic correctness (Phase 3)
        - Cycle detection across entries (Phase 3)
        - Sign of change_class against directionality (artifact-level
          governance check; may live in Phase 3 or as a separate
          numerics validator extension)
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    key: str = Field(min_length=1)
    value: NumericValue
    unit: NumericUnit
    allowed_range: AllowedRange
    directionality: Directionality
    change_class_if_increased: ChangeClass
    change_class_if_decreased: ChangeClass
    requires_human_approval: bool
    dependencies: tuple[NumericDependency, ...]
    numeric_risk_family: NumericRiskFamily
    spec_family: SpecFamily
    owning_spec_ref: str = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_value_unit_compatibility(self) -> Self:
        if not _value_type_compatible(self.value, self.unit):
            raise ValueError(
                f"value type {type(self.value).__name__!r} is incompatible "
                f"with unit {self.unit.value!r}"
            )
        # Extra check for enum_set: non-empty + no duplicates
        if self.unit is NumericUnit.ENUM_SET:
            assert isinstance(self.value, tuple)  # narrowed by _value_type_compatible
            if len(self.value) == 0:
                raise ValueError("enum_set value must be non-empty")
            if len(set(self.value)) != len(self.value):
                raise ValueError("enum_set value must not contain duplicates")
        return self

    @model_validator(mode="after")
    def _validate_value_in_allowed_range(self) -> Self:
        rng = self.allowed_range

        if isinstance(rng, AllowedRangeMinMax):
            if not _value_in_min_max(self.value, rng):
                raise ValueError(
                    f"value {self.value!r} not in min_max range [{rng.min}, {rng.max}]"
                )
        elif isinstance(rng, AllowedRangeSet):
            if self.unit is NumericUnit.ENUM_SET:
                assert isinstance(self.value, tuple)
                if not _enum_set_in_set(self.value, rng):
                    raise ValueError(
                        f"enum_set value {self.value!r} contains members "
                        f"outside the allowed set {rng.values!r}"
                    )
            else:
                if not _value_in_set(self.value, rng):
                    raise ValueError(f"value {self.value!r} not in allowed set {rng.values!r}")
        elif not _value_equal_single(self.value, rng):
            # rng narrowed to AllowedRangeSingle (only remaining variant)
            raise ValueError(
                f"value {self.value!r} does not match single allowed value {rng.value!r}"
            )

        return self

    @model_validator(mode="after")
    def _validate_enum_set_requires_set_range(self) -> Self:
        if self.unit is NumericUnit.ENUM_SET and not isinstance(
            self.allowed_range, AllowedRangeSet
        ):
            raise ValueError("unit=enum_set requires allowed_range of kind 'set'")
        return self

    @model_validator(mode="after")
    def _validate_constitutional_immutable_consistency(self) -> Self:
        is_single = isinstance(self.allowed_range, AllowedRangeSingle)
        both_forbidden = (
            self.change_class_if_increased is ChangeClass.FORBIDDEN
            and self.change_class_if_decreased is ChangeClass.FORBIDDEN
        )

        if is_single and not both_forbidden:
            raise ValueError(
                "AllowedRangeSingle requires both change_class_if_increased "
                "and change_class_if_decreased to be FORBIDDEN "
                "(constitutional immutable invariant)"
            )
        if both_forbidden and not is_single:
            raise ValueError(
                "Both change_class fields FORBIDDEN require AllowedRangeSingle "
                "(constitutional immutable invariant)"
            )
        return self


class CompatibilityClass(StrEnum):
    """Artifact-level change posture per M §8.

    Closed set of 4 values. Does NOT include `constitutional_amendment`:
    amendments are a separate workflow (see governance docs), not a
    compatibility class flag on a numerics artifact.
    """

    CLARIFICATION = "clarification"
    SAFETY_TIGHTENING = "safety_tightening"
    SAFETY_WEAKENING = "safety_weakening"
    GENESIS_AFFECTING = "genesis_affecting"


class NumericsArtifact(BaseModel):
    """A numerics artifact bundling all NumericEntry rows for one spec_family.

    Schema-layer invariants enforced:
        - artifact_type is the literal "numerics_artifact" discriminator
        - entries non-empty
        - keys unique across entries
        - every entry.spec_family equals artifact.spec_family
        - dev_only ↔ fixture_purpose two-way:
            * dev_only=True  → fixture_purpose required (non-empty)
            * dev_only=False → fixture_purpose must be None
        - signed=False with dev_only=False is ACCEPTED here; signature
          policy is loader-side (Phase 3)
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    artifact_type: Literal["numerics_artifact"] = "numerics_artifact"
    spec_family: SpecFamily
    owning_spec_ref: str = Field(min_length=1)
    numerics_version: str = Field(min_length=1)
    compatibility_class: CompatibilityClass
    signed: bool
    dev_only: bool
    fixture_purpose: str | None
    entries: tuple[NumericEntry, ...]

    @model_validator(mode="after")
    def _validate_entries_non_empty(self) -> Self:
        if len(self.entries) == 0:
            raise ValueError("entries must contain at least one NumericEntry")
        return self

    @model_validator(mode="after")
    def _validate_unique_keys(self) -> Self:
        seen: set[str] = set()
        for entry in self.entries:
            if entry.key in seen:
                raise ValueError(f"duplicate entry key: {entry.key}")
            seen.add(entry.key)
        return self

    @model_validator(mode="after")
    def _validate_spec_family_consistency(self) -> Self:
        for entry in self.entries:
            if entry.spec_family is not self.spec_family:
                raise ValueError(
                    f"entry {entry.key!r} spec_family={entry.spec_family.value!r} "
                    f"does not match artifact spec_family={self.spec_family.value!r}"
                )
        return self

    @model_validator(mode="after")
    def _validate_dev_only_fixture_purpose(self) -> Self:
        if self.dev_only:
            if self.fixture_purpose is None or self.fixture_purpose == "":
                raise ValueError("dev_only=True requires non-empty fixture_purpose")
        else:
            if self.fixture_purpose is not None:
                raise ValueError("dev_only=False forbids fixture_purpose; must be None")
        return self
