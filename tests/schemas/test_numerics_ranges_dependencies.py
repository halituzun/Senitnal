"""Schema tests for AllowedRange and NumericDependency.

Constitutional discipline tested here (schema layer only):
    - AllowedRange has 3 discriminated variants: min_max / set / single
    - min/max ordering and finiteness
    - Set non-empty + no duplicates + finiteness
    - Single value finiteness
    - NumericDependency conditional field requirements:
        computed_* → expression required, factor forbidden
        must_be_within_factor_of → factor required, expression forbidden
        other relationships → both forbidden
    - Legacy relationships (computed_less_than, computed_greater_than)
      already rejected at the enum boundary (test_numerics_enums.py)
"""

from __future__ import annotations

import pytest
from pydantic import TypeAdapter, ValidationError
from sentinel.types.numerics import (
    AllowedRange,
    AllowedRangeMinMax,
    AllowedRangeSet,
    AllowedRangeSingle,
    NumericDependency,
    RelationshipType,
)

# ---------------------------------------------------------------------------
# AllowedRangeMinMax
# ---------------------------------------------------------------------------


class TestAllowedRangeMinMax:
    def test_valid_min_max(self) -> None:
        r = AllowedRangeMinMax(min=0.0, max=1.0)
        assert r.kind == "min_max"
        assert r.min == 0.0
        assert r.max == 1.0

    def test_equal_min_max_accepted(self) -> None:
        r = AllowedRangeMinMax(min=5, max=5)
        assert r.min == r.max

    def test_max_less_than_min_rejected(self) -> None:
        with pytest.raises(ValidationError):
            AllowedRangeMinMax(min=10, max=5)

    def test_nan_rejected(self) -> None:
        with pytest.raises(ValidationError):
            AllowedRangeMinMax(min=float("nan"), max=1.0)
        with pytest.raises(ValidationError):
            AllowedRangeMinMax(min=0.0, max=float("nan"))

    def test_inf_rejected(self) -> None:
        with pytest.raises(ValidationError):
            AllowedRangeMinMax(min=float("-inf"), max=1.0)
        with pytest.raises(ValidationError):
            AllowedRangeMinMax(min=0.0, max=float("inf"))

    def test_extra_field_rejected(self) -> None:
        with pytest.raises(ValidationError):
            AllowedRangeMinMax.model_validate(
                {"kind": "min_max", "min": 0, "max": 1, "extra": "nope"}
            )

    def test_frozen_immutable(self) -> None:
        r = AllowedRangeMinMax(min=0, max=1)
        with pytest.raises(ValidationError):
            setattr(r, "max", 2)  # noqa: B010


# ---------------------------------------------------------------------------
# AllowedRangeSet
# ---------------------------------------------------------------------------


class TestAllowedRangeSet:
    def test_valid_string_set(self) -> None:
        r = AllowedRangeSet(values=("linear", "sigmoid", "step"))
        assert r.kind == "set"
        assert len(r.values) == 3

    def test_valid_int_set(self) -> None:
        r = AllowedRangeSet(values=(0, 1, 2))
        assert r.values == (0, 1, 2)

    def test_empty_set_rejected(self) -> None:
        with pytest.raises(ValidationError):
            AllowedRangeSet(values=())

    def test_duplicate_values_rejected(self) -> None:
        with pytest.raises(ValidationError):
            AllowedRangeSet(values=("a", "b", "a"))

    def test_nan_in_set_rejected(self) -> None:
        with pytest.raises(ValidationError):
            AllowedRangeSet(values=(0.0, float("nan")))

    def test_inf_in_set_rejected(self) -> None:
        with pytest.raises(ValidationError):
            AllowedRangeSet(values=(0.0, float("inf")))

    def test_extra_field_rejected(self) -> None:
        with pytest.raises(ValidationError):
            AllowedRangeSet.model_validate({"kind": "set", "values": ("a", "b"), "extra": "nope"})


# ---------------------------------------------------------------------------
# AllowedRangeSingle
# ---------------------------------------------------------------------------


class TestAllowedRangeSingle:
    def test_true_accepted(self) -> None:
        r = AllowedRangeSingle(value=True)
        assert r.value is True

    def test_false_accepted(self) -> None:
        r = AllowedRangeSingle(value=False)
        assert r.value is False

    def test_zero_accepted(self) -> None:
        r = AllowedRangeSingle(value=0)
        assert r.value == 0

    def test_string_value_accepted(self) -> None:
        r = AllowedRangeSingle(value="verified")
        assert r.value == "verified"

    def test_lifetime_string_accepted(self) -> None:
        """Used by `tier_cold.retention_ms = lifetime` and similar."""
        r = AllowedRangeSingle(value="lifetime")
        assert r.value == "lifetime"

    def test_nan_rejected(self) -> None:
        with pytest.raises(ValidationError):
            AllowedRangeSingle(value=float("nan"))

    def test_inf_rejected(self) -> None:
        with pytest.raises(ValidationError):
            AllowedRangeSingle(value=float("inf"))


# ---------------------------------------------------------------------------
# AllowedRange discriminated union
# ---------------------------------------------------------------------------


class TestAllowedRangeUnion:
    """The Annotated discriminated union dispatches on `kind`."""

    _adapter: TypeAdapter[AllowedRange] = TypeAdapter(AllowedRange)

    def test_dispatches_to_min_max(self) -> None:
        r = self._adapter.validate_python({"kind": "min_max", "min": 0, "max": 1})
        assert isinstance(r, AllowedRangeMinMax)

    def test_dispatches_to_set(self) -> None:
        r = self._adapter.validate_python({"kind": "set", "values": ("a", "b")})
        assert isinstance(r, AllowedRangeSet)

    def test_dispatches_to_single(self) -> None:
        r = self._adapter.validate_python({"kind": "single", "value": True})
        assert isinstance(r, AllowedRangeSingle)

    def test_invalid_kind_rejected(self) -> None:
        with pytest.raises(ValidationError):
            self._adapter.validate_python({"kind": "not_a_kind", "min": 0, "max": 1})


# ---------------------------------------------------------------------------
# NumericDependency
# ---------------------------------------------------------------------------


class TestNumericDependencySimple:
    """Simple relationships need neither factor nor expression."""

    @pytest.mark.parametrize(
        "rel",
        [
            RelationshipType.IMPLIES_MINIMUM_OF,
            RelationshipType.MUST_BE_LESS_THAN,
            RelationshipType.MUST_BE_GREATER_THAN,
            RelationshipType.MUST_BE_LESS_THAN_OR_EQUAL,
            RelationshipType.MUST_BE_GREATER_THAN_OR_EQUAL,
            RelationshipType.MUST_CHANGE_TOGETHER,
        ],
    )
    def test_simple_relationship_accepted(self, rel: RelationshipType) -> None:
        dep = NumericDependency(
            target_key="some.other.key",
            relationship=rel,
            rationale="audit reason",
        )
        assert dep.relationship == rel
        assert dep.factor is None
        assert dep.expression is None

    @pytest.mark.parametrize(
        "rel",
        [
            RelationshipType.MUST_BE_LESS_THAN,
            RelationshipType.IMPLIES_MINIMUM_OF,
        ],
    )
    def test_simple_relationship_rejects_factor(self, rel: RelationshipType) -> None:
        with pytest.raises(ValidationError):
            NumericDependency(
                target_key="some.key",
                relationship=rel,
                factor=2.0,
                rationale="audit",
            )

    @pytest.mark.parametrize(
        "rel",
        [
            RelationshipType.MUST_BE_GREATER_THAN,
            RelationshipType.MUST_CHANGE_TOGETHER,
        ],
    )
    def test_simple_relationship_rejects_expression(self, rel: RelationshipType) -> None:
        with pytest.raises(ValidationError):
            NumericDependency(
                target_key="some.key",
                relationship=rel,
                expression="a <= b",
                rationale="audit",
            )


class TestNumericDependencyFactor:
    """must_be_within_factor_of requires `factor`, forbids `expression`."""

    def test_with_factor_accepted(self) -> None:
        dep = NumericDependency(
            target_key="some.key",
            relationship=RelationshipType.MUST_BE_WITHIN_FACTOR_OF,
            factor=2.0,
            rationale="audit",
        )
        assert dep.factor == 2.0

    def test_missing_factor_rejected(self) -> None:
        with pytest.raises(ValidationError):
            NumericDependency(
                target_key="some.key",
                relationship=RelationshipType.MUST_BE_WITHIN_FACTOR_OF,
                rationale="audit",
            )

    def test_factor_zero_rejected(self) -> None:
        with pytest.raises(ValidationError):
            NumericDependency(
                target_key="some.key",
                relationship=RelationshipType.MUST_BE_WITHIN_FACTOR_OF,
                factor=0.0,
                rationale="audit",
            )

    def test_factor_negative_rejected(self) -> None:
        with pytest.raises(ValidationError):
            NumericDependency(
                target_key="some.key",
                relationship=RelationshipType.MUST_BE_WITHIN_FACTOR_OF,
                factor=-1.0,
                rationale="audit",
            )

    def test_factor_inf_rejected(self) -> None:
        with pytest.raises(ValidationError):
            NumericDependency(
                target_key="some.key",
                relationship=RelationshipType.MUST_BE_WITHIN_FACTOR_OF,
                factor=float("inf"),
                rationale="audit",
            )

    def test_factor_with_expression_rejected(self) -> None:
        with pytest.raises(ValidationError):
            NumericDependency(
                target_key="some.key",
                relationship=RelationshipType.MUST_BE_WITHIN_FACTOR_OF,
                factor=2.0,
                expression="a <= b",
                rationale="audit",
            )


class TestNumericDependencyComputed:
    """computed_*_or_equal requires `expression`, forbids `factor`."""

    @pytest.mark.parametrize(
        "rel",
        [
            RelationshipType.COMPUTED_LESS_THAN_OR_EQUAL,
            RelationshipType.COMPUTED_GREATER_THAN_OR_EQUAL,
        ],
    )
    def test_with_expression_accepted(self, rel: RelationshipType) -> None:
        dep = NumericDependency(
            target_key="some.key",
            relationship=rel,
            expression="candidate_cap <= verified_cap * ratio",
            rationale="audit",
        )
        assert dep.expression is not None

    @pytest.mark.parametrize(
        "rel",
        [
            RelationshipType.COMPUTED_LESS_THAN_OR_EQUAL,
            RelationshipType.COMPUTED_GREATER_THAN_OR_EQUAL,
        ],
    )
    def test_missing_expression_rejected(self, rel: RelationshipType) -> None:
        with pytest.raises(ValidationError):
            NumericDependency(
                target_key="some.key",
                relationship=rel,
                rationale="audit",
            )

    def test_computed_with_factor_rejected(self) -> None:
        with pytest.raises(ValidationError):
            NumericDependency(
                target_key="some.key",
                relationship=RelationshipType.COMPUTED_LESS_THAN_OR_EQUAL,
                expression="a <= b",
                factor=2.0,
                rationale="audit",
            )


# ---------------------------------------------------------------------------
# Common
# ---------------------------------------------------------------------------


class TestNumericDependencyCommon:
    def test_empty_target_key_rejected(self) -> None:
        with pytest.raises(ValidationError):
            NumericDependency(
                target_key="",
                relationship=RelationshipType.MUST_BE_LESS_THAN,
                rationale="audit",
            )

    def test_empty_rationale_rejected(self) -> None:
        with pytest.raises(ValidationError):
            NumericDependency(
                target_key="some.key",
                relationship=RelationshipType.MUST_BE_LESS_THAN,
                rationale="",
            )

    def test_legacy_relationship_string_rejected(self) -> None:
        """`computed_less_than` (without _or_equal) was never canonical."""
        with pytest.raises(ValidationError):
            NumericDependency.model_validate(
                {
                    "target_key": "some.key",
                    "relationship": "computed_less_than",
                    "expression": "a <= b",
                    "rationale": "audit",
                }
            )

    def test_extra_field_rejected(self) -> None:
        with pytest.raises(ValidationError):
            NumericDependency.model_validate(
                {
                    "target_key": "some.key",
                    "relationship": "must_be_less_than",
                    "rationale": "audit",
                    "extra": "nope",
                }
            )

    def test_frozen_immutable(self) -> None:
        dep = NumericDependency(
            target_key="some.key",
            relationship=RelationshipType.MUST_BE_LESS_THAN,
            rationale="audit",
        )
        with pytest.raises(ValidationError):
            setattr(dep, "target_key", "tampered")  # noqa: B010
