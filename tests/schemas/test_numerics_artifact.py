"""Schema tests for NumericsArtifact.

Constitutional discipline tested here (schema layer only):
    - artifact_type literal discriminator pinned to "numerics_artifact"
    - entries non-empty
    - keys unique across entries
    - every entry.spec_family equals artifact.spec_family
    - dev_only ↔ fixture_purpose two-way invariant
    - signed=False with dev_only=False ACCEPTED at schema layer
      (signature policy lives in the loader, not here)
    - Frozen immutability; extra="forbid"
    - Legacy / pre-patch vocabulary rejected:
        compatibility_class="constitutional_amendment" (separate workflow)
        compatibility_class="operational_no_behavior_change" (entry-level
        ChangeClass, not an artifact-level CompatibilityClass)
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sentinel.types.numerics import (
    AllowedRangeMinMax,
    AllowedRangeSingle,
    ChangeClass,
    CompatibilityClass,
    Directionality,
    NumericEntry,
    NumericRiskFamily,
    NumericsArtifact,
    NumericUnit,
    SpecFamily,
)


def _ingress_entry(key: str = "ingress_compiler.max_session_duration_ms") -> NumericEntry:
    return NumericEntry(
        key=key,
        value=30_000,
        unit=NumericUnit.MS,
        allowed_range=AllowedRangeMinMax(min=5_000, max=120_000),
        directionality=Directionality.LOWER_IS_STRICTER,
        change_class_if_increased=ChangeClass.SAFETY_WEAKENING,
        change_class_if_decreased=ChangeClass.SAFETY_TIGHTENING,
        requires_human_approval=True,
        dependencies=(),
        numeric_risk_family=NumericRiskFamily.SAFETY_CRITICAL,
        spec_family=SpecFamily.INGRESS_COMPILER,
        owning_spec_ref="INGRESS_COMPILER_NUMERICS.md §5",
    )


def _backup_immutable_entry() -> NumericEntry:
    return NumericEntry(
        key="backup.restore.max_missing_m1_events_for_full_identity",
        value=0,
        unit=NumericUnit.COUNT,
        allowed_range=AllowedRangeSingle(value=0),
        directionality=Directionality.NEUTRAL,
        change_class_if_increased=ChangeClass.FORBIDDEN,
        change_class_if_decreased=ChangeClass.FORBIDDEN,
        requires_human_approval=True,
        dependencies=(),
        numeric_risk_family=NumericRiskFamily.IDENTITY_RETENTION,
        spec_family=SpecFamily.BACKUP_STRATEGY,
        owning_spec_ref="BACKUP_STRATEGY_NUMERICS.md §12",
    )


# ---------------------------------------------------------------------------
# CompatibilityClass enum
# ---------------------------------------------------------------------------


class TestCompatibilityClass:
    def test_canonical_four_values(self) -> None:
        expected = {
            "clarification",
            "safety_tightening",
            "safety_weakening",
            "genesis_affecting",
        }
        assert {c.value for c in CompatibilityClass} == expected

    def test_four_values(self) -> None:
        assert len(CompatibilityClass) == 4

    def test_constitutional_amendment_not_a_compatibility_class(self) -> None:
        """`constitutional_amendment` is a separate workflow, not an
        artifact-level compatibility class flag.
        """
        values = {c.value for c in CompatibilityClass}
        assert "constitutional_amendment" not in values

    def test_operational_no_behavior_change_not_a_compatibility_class(self) -> None:
        """`operational_no_behavior_change` is an entry-level ChangeClass,
        not an artifact-level CompatibilityClass.
        """
        values = {c.value for c in CompatibilityClass}
        assert "operational_no_behavior_change" not in values


# ---------------------------------------------------------------------------
# Valid construction
# ---------------------------------------------------------------------------


class TestNumericsArtifactValid:
    def test_valid_dev_artifact(self) -> None:
        artifact = NumericsArtifact(
            spec_family=SpecFamily.INGRESS_COMPILER,
            owning_spec_ref="INGRESS_COMPILER_NUMERICS.md@v0.1",
            numerics_version="v0-dev",
            compatibility_class=CompatibilityClass.CLARIFICATION,
            signed=False,
            dev_only=True,
            fixture_purpose="MVP dry simulation only; not for production",
            entries=(_ingress_entry(),),
        )
        assert artifact.artifact_type == "numerics_artifact"
        assert artifact.spec_family is SpecFamily.INGRESS_COMPILER
        assert len(artifact.entries) == 1
        assert artifact.dev_only is True
        assert artifact.signed is False

    def test_valid_signed_production_shaped_artifact(self) -> None:
        artifact = NumericsArtifact(
            spec_family=SpecFamily.BACKUP_STRATEGY,
            owning_spec_ref="BACKUP_STRATEGY_NUMERICS.md@v0.1",
            numerics_version="v0.1.0",
            compatibility_class=CompatibilityClass.GENESIS_AFFECTING,
            signed=True,
            dev_only=False,
            fixture_purpose=None,
            entries=(_backup_immutable_entry(),),
        )
        assert artifact.signed is True
        assert artifact.dev_only is False
        assert artifact.fixture_purpose is None

    def test_unsigned_non_dev_accepted_at_schema_layer(self) -> None:
        """Schema layer is permissive about signature; loader enforces it."""
        artifact = NumericsArtifact(
            spec_family=SpecFamily.INGRESS_COMPILER,
            owning_spec_ref="INGRESS_COMPILER_NUMERICS.md@v0.1",
            numerics_version="v0.1.0",
            compatibility_class=CompatibilityClass.CLARIFICATION,
            signed=False,
            dev_only=False,
            fixture_purpose=None,
            entries=(_ingress_entry(),),
        )
        assert artifact.signed is False
        assert artifact.dev_only is False


# ---------------------------------------------------------------------------
# Structural invariants
# ---------------------------------------------------------------------------


class TestArtifactType:
    def test_wrong_artifact_type_rejected(self) -> None:
        with pytest.raises(ValidationError):
            NumericsArtifact.model_validate(
                {
                    "artifact_type": "adapter_manifest",
                    "spec_family": SpecFamily.INGRESS_COMPILER,
                    "owning_spec_ref": "X.md",
                    "numerics_version": "v0",
                    "compatibility_class": CompatibilityClass.CLARIFICATION,
                    "signed": False,
                    "dev_only": True,
                    "fixture_purpose": "dev",
                    "entries": (_ingress_entry(),),
                }
            )


class TestEntries:
    def test_empty_entries_rejected(self) -> None:
        with pytest.raises(ValidationError):
            NumericsArtifact(
                spec_family=SpecFamily.INGRESS_COMPILER,
                owning_spec_ref="X.md",
                numerics_version="v0",
                compatibility_class=CompatibilityClass.CLARIFICATION,
                signed=False,
                dev_only=True,
                fixture_purpose="dev",
                entries=(),
            )

    def test_duplicate_keys_rejected(self) -> None:
        dup_a = _ingress_entry("ingress_compiler.shared_key")
        dup_b = _ingress_entry("ingress_compiler.shared_key")
        with pytest.raises(ValidationError):
            NumericsArtifact(
                spec_family=SpecFamily.INGRESS_COMPILER,
                owning_spec_ref="X.md",
                numerics_version="v0",
                compatibility_class=CompatibilityClass.CLARIFICATION,
                signed=False,
                dev_only=True,
                fixture_purpose="dev",
                entries=(dup_a, dup_b),
            )

    def test_spec_family_mismatch_rejected(self) -> None:
        """Entry's spec_family must equal artifact's spec_family."""
        ingress = _ingress_entry()  # spec_family=INGRESS_COMPILER
        with pytest.raises(ValidationError):
            NumericsArtifact(
                spec_family=SpecFamily.BACKUP_STRATEGY,
                owning_spec_ref="BACKUP_STRATEGY_NUMERICS.md@v0.1",
                numerics_version="v0",
                compatibility_class=CompatibilityClass.CLARIFICATION,
                signed=False,
                dev_only=True,
                fixture_purpose="dev",
                entries=(ingress,),
            )


# ---------------------------------------------------------------------------
# dev_only ↔ fixture_purpose two-way invariant
# ---------------------------------------------------------------------------


class TestDevOnlyFixturePurpose:
    def test_dev_only_true_requires_fixture_purpose(self) -> None:
        with pytest.raises(ValidationError):
            NumericsArtifact(
                spec_family=SpecFamily.INGRESS_COMPILER,
                owning_spec_ref="X.md",
                numerics_version="v0",
                compatibility_class=CompatibilityClass.CLARIFICATION,
                signed=False,
                dev_only=True,
                fixture_purpose=None,
                entries=(_ingress_entry(),),
            )

    def test_dev_only_true_empty_fixture_purpose_rejected(self) -> None:
        with pytest.raises(ValidationError):
            NumericsArtifact(
                spec_family=SpecFamily.INGRESS_COMPILER,
                owning_spec_ref="X.md",
                numerics_version="v0",
                compatibility_class=CompatibilityClass.CLARIFICATION,
                signed=False,
                dev_only=True,
                fixture_purpose="",
                entries=(_ingress_entry(),),
            )

    def test_dev_only_false_rejects_fixture_purpose(self) -> None:
        with pytest.raises(ValidationError):
            NumericsArtifact(
                spec_family=SpecFamily.INGRESS_COMPILER,
                owning_spec_ref="X.md",
                numerics_version="v0.1.0",
                compatibility_class=CompatibilityClass.CLARIFICATION,
                signed=True,
                dev_only=False,
                fixture_purpose="some purpose",
                entries=(_ingress_entry(),),
            )


# ---------------------------------------------------------------------------
# Required-string / extra / frozen
# ---------------------------------------------------------------------------


class TestRequiredFields:
    def test_empty_owning_spec_ref_rejected(self) -> None:
        with pytest.raises(ValidationError):
            NumericsArtifact(
                spec_family=SpecFamily.INGRESS_COMPILER,
                owning_spec_ref="",
                numerics_version="v0",
                compatibility_class=CompatibilityClass.CLARIFICATION,
                signed=False,
                dev_only=True,
                fixture_purpose="dev",
                entries=(_ingress_entry(),),
            )

    def test_empty_numerics_version_rejected(self) -> None:
        with pytest.raises(ValidationError):
            NumericsArtifact(
                spec_family=SpecFamily.INGRESS_COMPILER,
                owning_spec_ref="X.md",
                numerics_version="",
                compatibility_class=CompatibilityClass.CLARIFICATION,
                signed=False,
                dev_only=True,
                fixture_purpose="dev",
                entries=(_ingress_entry(),),
            )


class TestImmutability:
    def test_extra_field_rejected(self) -> None:
        with pytest.raises(ValidationError):
            NumericsArtifact.model_validate(
                {
                    "spec_family": SpecFamily.INGRESS_COMPILER,
                    "owning_spec_ref": "X.md",
                    "numerics_version": "v0",
                    "compatibility_class": CompatibilityClass.CLARIFICATION,
                    "signed": False,
                    "dev_only": True,
                    "fixture_purpose": "dev",
                    "entries": (_ingress_entry(),),
                    "rogue_field": "nope",
                }
            )

    def test_frozen(self) -> None:
        artifact = NumericsArtifact(
            spec_family=SpecFamily.INGRESS_COMPILER,
            owning_spec_ref="X.md",
            numerics_version="v0",
            compatibility_class=CompatibilityClass.CLARIFICATION,
            signed=False,
            dev_only=True,
            fixture_purpose="dev",
            entries=(_ingress_entry(),),
        )
        with pytest.raises(ValidationError):
            setattr(artifact, "signed", True)  # noqa: B010


# ---------------------------------------------------------------------------
# Legacy / pre-patch rejection at the type boundary
# ---------------------------------------------------------------------------


class TestLegacyRejection:
    def test_constitutional_amendment_rejected(self) -> None:
        """`constitutional_amendment` is NOT a CompatibilityClass value."""
        with pytest.raises(ValidationError):
            NumericsArtifact.model_validate(
                {
                    "spec_family": SpecFamily.INGRESS_COMPILER,
                    "owning_spec_ref": "X.md",
                    "numerics_version": "v0",
                    "compatibility_class": "constitutional_amendment",
                    "signed": False,
                    "dev_only": True,
                    "fixture_purpose": "dev",
                    "entries": (_ingress_entry(),),
                }
            )

    def test_operational_no_behavior_change_rejected(self) -> None:
        """`operational_no_behavior_change` is an entry-level ChangeClass,
        not an artifact-level CompatibilityClass.
        """
        with pytest.raises(ValidationError):
            NumericsArtifact.model_validate(
                {
                    "spec_family": SpecFamily.INGRESS_COMPILER,
                    "owning_spec_ref": "X.md",
                    "numerics_version": "v0",
                    "compatibility_class": "operational_no_behavior_change",
                    "signed": False,
                    "dev_only": True,
                    "fixture_purpose": "dev",
                    "entries": (_ingress_entry(),),
                }
            )
