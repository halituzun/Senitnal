"""Schema tests for numerics governance enums.

Constitutional discipline tested here:
    - Canonical value sets for each enum
    - Legacy / pre-patch vocabulary REJECTED
    - 8 spec families (1 per numerics artifact N-U; M itself excluded)
    - 9 canonical RelationshipType values (post-patch); computed_* forms
      only exist with `_or_equal`
"""

from __future__ import annotations

from sentinel.types.numerics import (
    ChangeClass,
    Directionality,
    NumericRiskFamily,
    NumericUnit,
    RelationshipType,
    SpecFamily,
)


class TestNumericUnit:
    def test_canonical_values(self) -> None:
        expected = {
            "count",
            "ms",
            "bytes",
            "ratio",
            "percentage",
            "enum",
            "enum_set",
            "band_name",
            "bool",
        }
        assert {u.value for u in NumericUnit} == expected

    def test_legacy_units_absent(self) -> None:
        """Free-form units like `events_per_second` are NOT in the closed set."""
        values = {u.value for u in NumericUnit}
        assert "events_per_second" not in values
        assert "epoch_ms" not in values
        assert "string" not in values


class TestDirectionality:
    def test_canonical_values(self) -> None:
        expected = {
            "higher_is_stricter",
            "lower_is_stricter",
            "bidirectional_sensitive",
            "neutral",
        }
        assert {d.value for d in Directionality} == expected

    def test_legacy_directionality_absent(self) -> None:
        """`higher_is_weaker` (pre-patch wording) is NOT canonical."""
        values = {d.value for d in Directionality}
        assert "higher_is_weaker" not in values
        assert "lower_is_weaker" not in values


class TestChangeClass:
    def test_canonical_values(self) -> None:
        expected = {
            "clarification",
            "operational_no_behavior_change",
            "safety_tightening",
            "safety_weakening",
            "genesis_affecting",
            "forbidden",
        }
        assert {c.value for c in ChangeClass} == expected

    def test_six_values(self) -> None:
        assert len(ChangeClass) == 6

    def test_legacy_change_classes_absent(self) -> None:
        """Pre-patch wording (e.g. forbidden_in_v0_1) is NOT canonical."""
        values = {c.value for c in ChangeClass}
        assert "forbidden_in_v0_1" not in values
        assert "constitutional_amendment_required" not in values


class TestNumericRiskFamily:
    def test_canonical_values(self) -> None:
        expected = {
            "safety_critical",
            "resource_limits",
            "calibration_bands",
            "identity_retention",
            "operational_convenience",
            "experimental",
        }
        assert {f.value for f in NumericRiskFamily} == expected

    def test_six_families(self) -> None:
        assert len(NumericRiskFamily) == 6

    def test_legacy_field_absent(self) -> None:
        """`numerics_family` (renamed to `numeric_risk_family`) absent."""
        values = {f.value for f in NumericRiskFamily}
        assert "numerics_family" not in values


class TestRelationshipType:
    def test_nine_canonical_values(self) -> None:
        assert len(RelationshipType) == 9

    def test_canonical_values(self) -> None:
        expected = {
            "implies_minimum_of",
            "must_be_within_factor_of",
            "must_be_less_than",
            "must_be_greater_than",
            "must_be_less_than_or_equal",
            "must_be_greater_than_or_equal",
            "computed_less_than_or_equal",
            "computed_greater_than_or_equal",
            "must_change_together",
        }
        assert {r.value for r in RelationshipType} == expected

    def test_computed_or_equal_present(self) -> None:
        """Patches added the two `computed_*_or_equal` relationships."""
        values = {r.value for r in RelationshipType}
        assert "computed_less_than_or_equal" in values
        assert "computed_greater_than_or_equal" in values

    def test_must_be_or_equal_present(self) -> None:
        """Patches added the two `must_be_*_or_equal` relationships."""
        values = {r.value for r in RelationshipType}
        assert "must_be_less_than_or_equal" in values
        assert "must_be_greater_than_or_equal" in values

    def test_pre_patch_computed_forms_absent(self) -> None:
        """`computed_less_than` and `computed_greater_than` (without
        `_or_equal`) are NOT canonical per M §12 post-patch.
        """
        values = {r.value for r in RelationshipType}
        assert "computed_less_than" not in values
        assert "computed_greater_than" not in values


class TestSpecFamily:
    def test_eight_values(self) -> None:
        assert len(SpecFamily) == 8

    def test_canonical_values(self) -> None:
        expected = {
            "ingress_compiler",
            "replay_protocol",
            "memory_write_gate",
            "observer_ledger",
            "backup_strategy",
            "bootstrap_genome",
            "recall_protocol",
            "adapter_trust",
        }
        assert {s.value for s in SpecFamily} == expected

    def test_numerics_governance_not_a_spec_family(self) -> None:
        """M is the meta-spec; it does NOT have its own numerics artifact
        family (it governs the 8 listed above).
        """
        values = {s.value for s in SpecFamily}
        assert "numerics_governance" not in values
