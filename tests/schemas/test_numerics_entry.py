"""Schema tests for NumericEntry.

Constitutional discipline tested here (schema layer only):
    - All 12 required fields enforced (M §9 no-default rule)
    - value's concrete Python type matches unit
    - value falls inside allowed_range (all 3 variants)
    - enum_set requires AllowedRangeSet; non-empty + no duplicates
    - Constitutional immutable consistency:
        single allowed_range ⇔ both change_class fields == FORBIDDEN
    - Frozen immutability; extra="forbid"
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sentinel.types.numerics import (
    AllowedRangeMinMax,
    AllowedRangeSet,
    AllowedRangeSingle,
    ChangeClass,
    Directionality,
    NumericEntry,
    NumericRiskFamily,
    NumericUnit,
    SpecFamily,
)


def _valid_count_kwargs() -> dict[str, object]:
    """A canonical valid NumericEntry for a count-typed key."""
    return {
        "key": "ingress_compiler.max_session_duration_ms",
        "value": 30_000,
        "unit": NumericUnit.MS,
        "allowed_range": AllowedRangeMinMax(min=5_000, max=120_000),
        "directionality": Directionality.LOWER_IS_STRICTER,
        "change_class_if_increased": ChangeClass.SAFETY_WEAKENING,
        "change_class_if_decreased": ChangeClass.SAFETY_TIGHTENING,
        "requires_human_approval": True,
        "dependencies": (),
        "numeric_risk_family": NumericRiskFamily.SAFETY_CRITICAL,
        "spec_family": SpecFamily.INGRESS_COMPILER,
        "owning_spec_ref": "INGRESS_COMPILER_NUMERICS.md §5",
    }


def _valid_immutable_kwargs() -> dict[str, object]:
    """A canonical constitutional immutable NumericEntry (single + forbidden)."""
    return {
        "key": "backup.restore.max_missing_m1_events_for_full_identity",
        "value": 0,
        "unit": NumericUnit.COUNT,
        "allowed_range": AllowedRangeSingle(value=0),
        "directionality": Directionality.NEUTRAL,
        "change_class_if_increased": ChangeClass.FORBIDDEN,
        "change_class_if_decreased": ChangeClass.FORBIDDEN,
        "requires_human_approval": True,
        "dependencies": (),
        "numeric_risk_family": NumericRiskFamily.IDENTITY_RETENTION,
        "spec_family": SpecFamily.BACKUP_STRATEGY,
        "owning_spec_ref": "BACKUP_STRATEGY_NUMERICS.md §12",
    }


# ---------------------------------------------------------------------------
# Valid construction
# ---------------------------------------------------------------------------


class TestNumericEntryValid:
    def test_valid_count_entry(self) -> None:
        entry = NumericEntry.model_validate(_valid_count_kwargs())
        assert entry.unit is NumericUnit.MS
        assert entry.value == 30_000

    def test_valid_ratio_entry(self) -> None:
        entry = NumericEntry(
            key="ingress_compiler.profile_cap.HumanIntentEvent",
            value=0.35,
            unit=NumericUnit.RATIO,
            allowed_range=AllowedRangeMinMax(min=0.1, max=0.5),
            directionality=Directionality.LOWER_IS_STRICTER,
            change_class_if_increased=ChangeClass.SAFETY_WEAKENING,
            change_class_if_decreased=ChangeClass.SAFETY_TIGHTENING,
            requires_human_approval=True,
            dependencies=(),
            numeric_risk_family=NumericRiskFamily.SAFETY_CRITICAL,
            spec_family=SpecFamily.INGRESS_COMPILER,
            owning_spec_ref="INGRESS_COMPILER_NUMERICS.md §7",
        )
        assert entry.value == pytest.approx(0.35)

    def test_valid_bool_immutable_entry(self) -> None:
        entry = NumericEntry(
            key="observer.permanent.lossless_required",
            value=True,
            unit=NumericUnit.BOOL,
            allowed_range=AllowedRangeSingle(value=True),
            directionality=Directionality.NEUTRAL,
            change_class_if_increased=ChangeClass.FORBIDDEN,
            change_class_if_decreased=ChangeClass.FORBIDDEN,
            requires_human_approval=True,
            dependencies=(),
            numeric_risk_family=NumericRiskFamily.SAFETY_CRITICAL,
            spec_family=SpecFamily.OBSERVER_LEDGER,
            owning_spec_ref="OBSERVER_LEDGER_NUMERICS.md §10",
        )
        assert entry.value is True

    def test_valid_enum_entry(self) -> None:
        entry = NumericEntry(
            key="ingress_compiler.membership_function_type",
            value="linear",
            unit=NumericUnit.ENUM,
            allowed_range=AllowedRangeSet(values=("linear", "sigmoid", "step")),
            directionality=Directionality.BIDIRECTIONAL_SENSITIVE,
            change_class_if_increased=ChangeClass.SAFETY_WEAKENING,
            change_class_if_decreased=ChangeClass.SAFETY_WEAKENING,
            requires_human_approval=True,
            dependencies=(),
            numeric_risk_family=NumericRiskFamily.CALIBRATION_BANDS,
            spec_family=SpecFamily.INGRESS_COMPILER,
            owning_spec_ref="INGRESS_COMPILER_NUMERICS.md §6",
        )
        assert entry.value == "linear"

    def test_valid_enum_set_entry(self) -> None:
        entry = NumericEntry(
            key="memory_write.auto_verified_human_subject_classes",
            value=("bootstrap_reference", "operator_decision_record"),
            unit=NumericUnit.ENUM_SET,
            allowed_range=AllowedRangeSet(
                values=(
                    "bootstrap_reference",
                    "signed_administrative_reference",
                    "operator_decision_record",
                    "deontic_kill_switch_action_record",
                )
            ),
            directionality=Directionality.LOWER_IS_STRICTER,
            change_class_if_increased=ChangeClass.SAFETY_WEAKENING,
            change_class_if_decreased=ChangeClass.SAFETY_TIGHTENING,
            requires_human_approval=True,
            dependencies=(),
            numeric_risk_family=NumericRiskFamily.SAFETY_CRITICAL,
            spec_family=SpecFamily.MEMORY_WRITE_GATE,
            owning_spec_ref="MEMORY_WRITE_GATE_NUMERICS.md §18",
        )
        assert len(entry.value) == 2  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Field-level required (M §9 no-default rule)
# ---------------------------------------------------------------------------


class TestNumericEntryNoDefault:
    def test_missing_dependencies_rejected(self) -> None:
        kwargs = _valid_count_kwargs()
        del kwargs["dependencies"]
        with pytest.raises(ValidationError):
            NumericEntry.model_validate(kwargs)

    def test_missing_owning_spec_ref_rejected(self) -> None:
        kwargs = _valid_count_kwargs()
        del kwargs["owning_spec_ref"]
        with pytest.raises(ValidationError):
            NumericEntry.model_validate(kwargs)

    def test_missing_requires_human_approval_rejected(self) -> None:
        kwargs = _valid_count_kwargs()
        del kwargs["requires_human_approval"]
        with pytest.raises(ValidationError):
            NumericEntry.model_validate(kwargs)

    def test_missing_directionality_rejected(self) -> None:
        kwargs = _valid_count_kwargs()
        del kwargs["directionality"]
        with pytest.raises(ValidationError):
            NumericEntry.model_validate(kwargs)

    def test_empty_owning_spec_ref_rejected(self) -> None:
        kwargs = _valid_count_kwargs()
        kwargs["owning_spec_ref"] = ""
        with pytest.raises(ValidationError):
            NumericEntry.model_validate(kwargs)

    def test_empty_key_rejected(self) -> None:
        kwargs = _valid_count_kwargs()
        kwargs["key"] = ""
        with pytest.raises(ValidationError):
            NumericEntry.model_validate(kwargs)

    def test_extra_field_rejected(self) -> None:
        kwargs = _valid_count_kwargs()
        kwargs["tampered"] = "nope"
        with pytest.raises(ValidationError):
            NumericEntry.model_validate(kwargs)


# ---------------------------------------------------------------------------
# Value-unit compatibility
# ---------------------------------------------------------------------------


class TestValueUnitCompatibility:
    def test_bool_value_with_count_rejected(self) -> None:
        kwargs = _valid_count_kwargs()
        kwargs["value"] = True
        with pytest.raises(ValidationError):
            NumericEntry.model_validate(kwargs)

    def test_int_value_with_bool_unit_rejected(self) -> None:
        kwargs = _valid_immutable_kwargs()
        kwargs["unit"] = NumericUnit.BOOL
        kwargs["allowed_range"] = AllowedRangeSingle(value=1)
        # value is int 0 from immutable fixture; unit BOOL expects bool
        with pytest.raises(ValidationError):
            NumericEntry.model_validate(kwargs)

    def test_string_value_with_ratio_rejected(self) -> None:
        kwargs = _valid_count_kwargs()
        kwargs["value"] = "not_a_number"
        kwargs["unit"] = NumericUnit.RATIO
        kwargs["allowed_range"] = AllowedRangeMinMax(min=0.0, max=1.0)
        with pytest.raises(ValidationError):
            NumericEntry.model_validate(kwargs)

    def test_tuple_value_with_enum_rejected(self) -> None:
        kwargs = _valid_count_kwargs()
        kwargs["value"] = ("a", "b")
        kwargs["unit"] = NumericUnit.ENUM
        kwargs["allowed_range"] = AllowedRangeSet(values=("a", "b"))
        with pytest.raises(ValidationError):
            NumericEntry.model_validate(kwargs)

    def test_nan_value_rejected(self) -> None:
        kwargs = _valid_count_kwargs()
        kwargs["value"] = float("nan")
        kwargs["unit"] = NumericUnit.RATIO
        kwargs["allowed_range"] = AllowedRangeMinMax(min=0.0, max=1.0)
        with pytest.raises(ValidationError):
            NumericEntry.model_validate(kwargs)

    def test_inf_value_rejected(self) -> None:
        kwargs = _valid_count_kwargs()
        kwargs["value"] = float("inf")
        kwargs["unit"] = NumericUnit.RATIO
        kwargs["allowed_range"] = AllowedRangeMinMax(min=0.0, max=1.0)
        with pytest.raises(ValidationError):
            NumericEntry.model_validate(kwargs)


# ---------------------------------------------------------------------------
# Value in allowed_range
# ---------------------------------------------------------------------------


class TestValueInAllowedRange:
    def test_value_below_min_rejected(self) -> None:
        kwargs = _valid_count_kwargs()
        kwargs["value"] = 1_000  # below min 5_000
        with pytest.raises(ValidationError):
            NumericEntry.model_validate(kwargs)

    def test_value_above_max_rejected(self) -> None:
        kwargs = _valid_count_kwargs()
        kwargs["value"] = 200_000  # above max 120_000
        with pytest.raises(ValidationError):
            NumericEntry.model_validate(kwargs)

    def test_value_at_min_accepted(self) -> None:
        kwargs = _valid_count_kwargs()
        kwargs["value"] = 5_000
        entry = NumericEntry.model_validate(kwargs)
        assert entry.value == 5_000

    def test_value_not_in_set_rejected(self) -> None:
        with pytest.raises(ValidationError):
            NumericEntry(
                key="x.y",
                value="ternary",
                unit=NumericUnit.ENUM,
                allowed_range=AllowedRangeSet(values=("linear", "sigmoid", "step")),
                directionality=Directionality.BIDIRECTIONAL_SENSITIVE,
                change_class_if_increased=ChangeClass.SAFETY_WEAKENING,
                change_class_if_decreased=ChangeClass.SAFETY_WEAKENING,
                requires_human_approval=True,
                dependencies=(),
                numeric_risk_family=NumericRiskFamily.CALIBRATION_BANDS,
                spec_family=SpecFamily.INGRESS_COMPILER,
                owning_spec_ref="N §6",
            )

    def test_enum_set_member_outside_allowed_rejected(self) -> None:
        with pytest.raises(ValidationError):
            NumericEntry(
                key="memory_write.auto_verified_human_subject_classes",
                value=("bootstrap_reference", "narrative_claim"),  # narrative not allowed
                unit=NumericUnit.ENUM_SET,
                allowed_range=AllowedRangeSet(
                    values=(
                        "bootstrap_reference",
                        "operator_decision_record",
                    )
                ),
                directionality=Directionality.LOWER_IS_STRICTER,
                change_class_if_increased=ChangeClass.SAFETY_WEAKENING,
                change_class_if_decreased=ChangeClass.SAFETY_TIGHTENING,
                requires_human_approval=True,
                dependencies=(),
                numeric_risk_family=NumericRiskFamily.SAFETY_CRITICAL,
                spec_family=SpecFamily.MEMORY_WRITE_GATE,
                owning_spec_ref="P §18",
            )

    def test_enum_set_duplicate_rejected(self) -> None:
        with pytest.raises(ValidationError):
            NumericEntry(
                key="x.y",
                value=("a", "a"),
                unit=NumericUnit.ENUM_SET,
                allowed_range=AllowedRangeSet(values=("a", "b")),
                directionality=Directionality.LOWER_IS_STRICTER,
                change_class_if_increased=ChangeClass.SAFETY_WEAKENING,
                change_class_if_decreased=ChangeClass.SAFETY_TIGHTENING,
                requires_human_approval=True,
                dependencies=(),
                numeric_risk_family=NumericRiskFamily.SAFETY_CRITICAL,
                spec_family=SpecFamily.MEMORY_WRITE_GATE,
                owning_spec_ref="P §18",
            )

    def test_enum_set_empty_rejected(self) -> None:
        with pytest.raises(ValidationError):
            NumericEntry(
                key="x.y",
                value=(),
                unit=NumericUnit.ENUM_SET,
                allowed_range=AllowedRangeSet(values=("a", "b")),
                directionality=Directionality.LOWER_IS_STRICTER,
                change_class_if_increased=ChangeClass.SAFETY_WEAKENING,
                change_class_if_decreased=ChangeClass.SAFETY_TIGHTENING,
                requires_human_approval=True,
                dependencies=(),
                numeric_risk_family=NumericRiskFamily.SAFETY_CRITICAL,
                spec_family=SpecFamily.MEMORY_WRITE_GATE,
                owning_spec_ref="P §18",
            )

    def test_enum_set_requires_set_range(self) -> None:
        """unit=enum_set with AllowedRangeMinMax → reject."""
        with pytest.raises(ValidationError):
            NumericEntry(
                key="x.y",
                value=("a",),
                unit=NumericUnit.ENUM_SET,
                allowed_range=AllowedRangeMinMax(min=0, max=1),
                directionality=Directionality.LOWER_IS_STRICTER,
                change_class_if_increased=ChangeClass.SAFETY_WEAKENING,
                change_class_if_decreased=ChangeClass.SAFETY_TIGHTENING,
                requires_human_approval=True,
                dependencies=(),
                numeric_risk_family=NumericRiskFamily.SAFETY_CRITICAL,
                spec_family=SpecFamily.MEMORY_WRITE_GATE,
                owning_spec_ref="P §18",
            )

    def test_single_range_value_mismatch_rejected(self) -> None:
        kwargs = _valid_immutable_kwargs()
        kwargs["value"] = 1  # range single = 0
        with pytest.raises(ValidationError):
            NumericEntry.model_validate(kwargs)


# ---------------------------------------------------------------------------
# Constitutional immutable consistency
# ---------------------------------------------------------------------------


class TestConstitutionalImmutableConsistency:
    def test_valid_immutable_accepted(self) -> None:
        entry = NumericEntry.model_validate(_valid_immutable_kwargs())
        assert entry.change_class_if_increased is ChangeClass.FORBIDDEN
        assert entry.change_class_if_decreased is ChangeClass.FORBIDDEN

    def test_single_range_without_both_forbidden_rejected(self) -> None:
        """AllowedRangeSingle requires both change_class fields == FORBIDDEN."""
        kwargs = _valid_immutable_kwargs()
        kwargs["change_class_if_increased"] = ChangeClass.SAFETY_WEAKENING
        with pytest.raises(ValidationError):
            NumericEntry.model_validate(kwargs)

    def test_single_range_partial_forbidden_rejected(self) -> None:
        kwargs = _valid_immutable_kwargs()
        kwargs["change_class_if_decreased"] = ChangeClass.SAFETY_TIGHTENING
        with pytest.raises(ValidationError):
            NumericEntry.model_validate(kwargs)

    def test_both_forbidden_without_single_range_rejected(self) -> None:
        """Both change_class == FORBIDDEN require AllowedRangeSingle."""
        kwargs = _valid_count_kwargs()
        kwargs["change_class_if_increased"] = ChangeClass.FORBIDDEN
        kwargs["change_class_if_decreased"] = ChangeClass.FORBIDDEN
        # still has AllowedRangeMinMax from _valid_count_kwargs
        with pytest.raises(ValidationError):
            NumericEntry.model_validate(kwargs)


# ---------------------------------------------------------------------------
# Frozen immutability
# ---------------------------------------------------------------------------


class TestNumericEntryImmutable:
    def test_value_cannot_be_modified(self) -> None:
        entry = NumericEntry.model_validate(_valid_count_kwargs())
        with pytest.raises(ValidationError):
            setattr(entry, "value", 60_000)  # noqa: B010

    def test_unit_cannot_be_modified(self) -> None:
        entry = NumericEntry.model_validate(_valid_count_kwargs())
        with pytest.raises(ValidationError):
            setattr(entry, "unit", NumericUnit.RATIO)  # noqa: B010

    def test_dependencies_cannot_be_replaced(self) -> None:
        entry = NumericEntry.model_validate(_valid_count_kwargs())
        with pytest.raises(ValidationError):
            setattr(entry, "dependencies", ())  # noqa: B010
