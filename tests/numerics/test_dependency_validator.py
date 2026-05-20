"""Tests for the numerics dependency validator (cycle + reference)."""

from __future__ import annotations

import pytest
from sentinel.constitution.violations import NumericsGovernanceViolation
from sentinel.numerics.dependency_validator import validate_dependencies
from sentinel.types.numerics import (
    AllowedRangeMinMax,
    ChangeClass,
    CompatibilityClass,
    Directionality,
    NumericDependency,
    NumericEntry,
    NumericRiskFamily,
    NumericsArtifact,
    NumericUnit,
    RelationshipType,
    SpecFamily,
)


def _entry(
    key: str,
    *,
    deps: tuple[NumericDependency, ...] = (),
) -> NumericEntry:
    return NumericEntry(
        key=key,
        value=10,
        unit=NumericUnit.COUNT,
        allowed_range=AllowedRangeMinMax(min=1, max=100),
        directionality=Directionality.LOWER_IS_STRICTER,
        change_class_if_increased=ChangeClass.SAFETY_WEAKENING,
        change_class_if_decreased=ChangeClass.SAFETY_TIGHTENING,
        requires_human_approval=False,
        dependencies=deps,
        numeric_risk_family=NumericRiskFamily.OPERATIONAL_CONVENIENCE,
        spec_family=SpecFamily.INGRESS_COMPILER,
        owning_spec_ref="X.md §1",
    )


def _artifact(entries: tuple[NumericEntry, ...]) -> NumericsArtifact:
    return NumericsArtifact(
        spec_family=SpecFamily.INGRESS_COMPILER,
        owning_spec_ref="X.md",
        numerics_version="v0-dev",
        compatibility_class=CompatibilityClass.CLARIFICATION,
        signed=False,
        dev_only=True,
        fixture_purpose="unit_test",
        entries=entries,
    )


def _dep(
    target: str, *, rel: RelationshipType = RelationshipType.MUST_BE_LESS_THAN
) -> NumericDependency:
    return NumericDependency(target_key=target, relationship=rel, rationale="unit test")


class TestNoDependencies:
    def test_artifact_with_no_dependencies_passes(self) -> None:
        validate_dependencies(_artifact((_entry("a"),)))

    def test_two_entries_no_deps_passes(self) -> None:
        validate_dependencies(_artifact((_entry("a"), _entry("b"))))


class TestUnknownTarget:
    def test_unknown_target_key_rejected(self) -> None:
        a = _entry("a", deps=(_dep("missing"),))
        with pytest.raises(NumericsGovernanceViolation) as exc_info:
            validate_dependencies(_artifact((a,)))
        assert exc_info.value.violation_code == "NUMERICS_DEPENDENCY_UNKNOWN_KEY"
        assert exc_info.value.evidence["entry_key"] == "a"
        assert exc_info.value.evidence["target_key"] == "missing"


class TestCycleDetection:
    def test_self_loop_rejected(self) -> None:
        a = _entry("a", deps=(_dep("a"),))
        with pytest.raises(NumericsGovernanceViolation) as exc_info:
            validate_dependencies(_artifact((a,)))
        assert exc_info.value.violation_code == "NUMERICS_DEPENDENCY_CYCLE_DETECTED"
        assert exc_info.value.evidence["cycle"] == ["a", "a"]

    def test_two_node_cycle_rejected(self) -> None:
        a = _entry("a", deps=(_dep("b"),))
        b = _entry("b", deps=(_dep("a"),))
        with pytest.raises(NumericsGovernanceViolation) as exc_info:
            validate_dependencies(_artifact((a, b)))
        assert exc_info.value.violation_code == "NUMERICS_DEPENDENCY_CYCLE_DETECTED"
        cycle = exc_info.value.evidence["cycle"]
        assert cycle[0] == cycle[-1]
        assert set(cycle) == {"a", "b"}

    def test_three_node_cycle_rejected(self) -> None:
        a = _entry("a", deps=(_dep("b"),))
        b = _entry("b", deps=(_dep("c"),))
        c = _entry("c", deps=(_dep("a"),))
        with pytest.raises(NumericsGovernanceViolation) as exc_info:
            validate_dependencies(_artifact((a, b, c)))
        assert exc_info.value.violation_code == "NUMERICS_DEPENDENCY_CYCLE_DETECTED"


class TestAcyclicChain:
    def test_three_node_chain_accepted(self) -> None:
        a = _entry("a", deps=(_dep("b"),))
        b = _entry("b", deps=(_dep("c"),))
        c = _entry("c")
        validate_dependencies(_artifact((a, b, c)))

    def test_diamond_accepted(self) -> None:
        # a -> b, a -> c, b -> d, c -> d (no cycle)
        d = _entry("d")
        b = _entry("b", deps=(_dep("d"),))
        c = _entry("c", deps=(_dep("d"),))
        a = _entry("a", deps=(_dep("b"), _dep("c")))
        validate_dependencies(_artifact((a, b, c, d)))
