"""Tests for the constitutional violation exception vocabulary.

Discipline tested here:
    - ViolationContext is frozen (dataclass frozen=True)
    - evidence is defensively copied + wrapped in MappingProxyType,
      so mutating the original dict does NOT mutate the context's
      evidence view
    - evidence view itself is read-only (TypeError on item assignment)
    - ConstitutionalViolation surfaces message + context + the three
      context shortcut properties
    - All specialized violation classes inherit from
      ConstitutionalViolation (so a single `except ConstitutionalViolation`
      catches every breach kind)
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from types import MappingProxyType

import pytest
from sentinel.constitution.violations import (
    CapabilityBoundaryViolation,
    ConstitutionalViolation,
    ForbiddenFieldViolation,
    InvariantViolation,
    NumericsGovernanceViolation,
    RuntimeModeViolation,
    SchemaBoundaryViolation,
    ViolationContext,
)

# ---------------------------------------------------------------------------
# ViolationContext immutability
# ---------------------------------------------------------------------------


class TestViolationContextImmutability:
    def test_context_is_frozen(self) -> None:
        ctx = ViolationContext(
            violation_code="FORBIDDEN_FIELD",
            source_ref="CONSTITUTION.md §6",
            evidence={"field": "BTCUSDT"},
        )
        with pytest.raises(FrozenInstanceError):
            ctx.violation_code = "OTHER"  # type: ignore[misc]

    def test_evidence_is_mapping_proxy(self) -> None:
        ctx = ViolationContext(
            violation_code="X",
            source_ref="Y",
            evidence={"a": 1},
        )
        assert isinstance(ctx.evidence, MappingProxyType)

    def test_evidence_view_is_read_only(self) -> None:
        ctx = ViolationContext(
            violation_code="X",
            source_ref="Y",
            evidence={"a": 1},
        )
        with pytest.raises(TypeError):
            ctx.evidence["a"] = 2  # type: ignore[index]

    def test_evidence_defensive_copy(self) -> None:
        """Mutating the original dict must NOT mutate the context view."""
        original = {"a": 1}
        ctx = ViolationContext(
            violation_code="X",
            source_ref="Y",
            evidence=original,
        )
        original["a"] = 99
        original["b"] = 42
        assert ctx.evidence["a"] == 1
        assert "b" not in ctx.evidence

    def test_default_evidence_is_empty(self) -> None:
        ctx = ViolationContext(
            violation_code="X",
            source_ref="Y",
        )
        assert dict(ctx.evidence) == {}


# ---------------------------------------------------------------------------
# ConstitutionalViolation surface
# ---------------------------------------------------------------------------


class TestConstitutionalViolation:
    def test_carries_message_and_context(self) -> None:
        ctx = ViolationContext(
            violation_code="INVARIANT_FAILED",
            source_ref="CONSTITUTION.md §3",
            evidence={"detail": "intensity mismatch"},
        )
        exc = ConstitutionalViolation("intensity mismatch detected", ctx)
        assert exc.message == "intensity mismatch detected"
        assert exc.context is ctx
        assert str(exc) == "intensity mismatch detected"

    def test_violation_code_shortcut(self) -> None:
        ctx = ViolationContext(violation_code="FORBIDDEN_FIELD", source_ref="X")
        exc = ConstitutionalViolation("m", ctx)
        assert exc.violation_code == "FORBIDDEN_FIELD"

    def test_source_ref_shortcut(self) -> None:
        ctx = ViolationContext(violation_code="X", source_ref="CONSTITUTION.md §6")
        exc = ConstitutionalViolation("m", ctx)
        assert exc.source_ref == "CONSTITUTION.md §6"

    def test_evidence_shortcut(self) -> None:
        ctx = ViolationContext(violation_code="X", source_ref="Y", evidence={"k": "v"})
        exc = ConstitutionalViolation("m", ctx)
        assert exc.evidence["k"] == "v"

    def test_is_exception(self) -> None:
        ctx = ViolationContext(violation_code="X", source_ref="Y")
        with pytest.raises(ConstitutionalViolation):
            raise ConstitutionalViolation("m", ctx)


# ---------------------------------------------------------------------------
# Specialized subclasses
# ---------------------------------------------------------------------------


class TestSpecializedViolations:
    @pytest.mark.parametrize(
        "cls",
        [
            SchemaBoundaryViolation,
            ForbiddenFieldViolation,
            InvariantViolation,
            CapabilityBoundaryViolation,
            RuntimeModeViolation,
            NumericsGovernanceViolation,
        ],
    )
    def test_subclasses_inherit_base(self, cls: type[ConstitutionalViolation]) -> None:
        ctx = ViolationContext(violation_code="X", source_ref="Y")
        exc = cls("m", ctx)
        assert isinstance(exc, ConstitutionalViolation)
        assert isinstance(exc, cls)

    def test_single_except_clause_catches_any(self) -> None:
        """A single `except ConstitutionalViolation` catches every breach."""
        ctx = ViolationContext(violation_code="X", source_ref="Y")
        caught: list[type[ConstitutionalViolation]] = []
        for cls in (
            SchemaBoundaryViolation,
            ForbiddenFieldViolation,
            InvariantViolation,
            CapabilityBoundaryViolation,
            RuntimeModeViolation,
            NumericsGovernanceViolation,
        ):
            try:
                raise cls("m", ctx)
            except ConstitutionalViolation as exc:
                caught.append(type(exc))
        assert caught == [
            SchemaBoundaryViolation,
            ForbiddenFieldViolation,
            InvariantViolation,
            CapabilityBoundaryViolation,
            RuntimeModeViolation,
            NumericsGovernanceViolation,
        ]
