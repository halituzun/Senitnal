"""Tests for the MVP REQUIRED invariant catalog and helpers.

Discipline tested here:
    - Catalog is non-empty and codes are unique
    - Every catalog entry has a non-empty source_ref and statement
    - Every catalog entry is `mvp_required=True` (v0.1 set)
    - `get_invariant(code)` returns the row; unknown code raises KeyError
    - `list_invariants(category=...)` filters by category
    - `list_invariants(mvp_required=True)` returns the whole catalog
    - `assert_invariant(True, ...)` does NOT raise
    - `assert_invariant(False, ...)` raises InvariantViolation with the
      catalog code, source_ref, and the caller's evidence
    - Critical MVP red lines are present in the catalog
"""

from __future__ import annotations

import pytest
from sentinel.constitution.invariants import (
    MVP_REQUIRED_INVARIANTS,
    InvariantCategory,
    InvariantDefinition,
    assert_invariant,
    get_invariant,
    list_invariants,
)
from sentinel.constitution.violations import (
    ConstitutionalViolation,
    InvariantViolation,
)

# ---------------------------------------------------------------------------
# Catalog shape
# ---------------------------------------------------------------------------


class TestCatalogShape:
    def test_catalog_non_empty(self) -> None:
        assert len(MVP_REQUIRED_INVARIANTS) > 0

    def test_codes_are_unique(self) -> None:
        codes = [inv.code for inv in MVP_REQUIRED_INVARIANTS]
        assert len(set(codes)) == len(codes)

    def test_codes_are_upper_snake(self) -> None:
        for inv in MVP_REQUIRED_INVARIANTS:
            assert inv.code == inv.code.upper()
            assert " " not in inv.code

    def test_every_row_has_source_ref_and_statement(self) -> None:
        for inv in MVP_REQUIRED_INVARIANTS:
            assert inv.source_ref.strip() != ""
            assert inv.statement.strip() != ""

    def test_every_row_is_mvp_required(self) -> None:
        for inv in MVP_REQUIRED_INVARIANTS:
            assert inv.mvp_required is True

    def test_definition_is_frozen(self) -> None:
        from dataclasses import FrozenInstanceError

        inv = MVP_REQUIRED_INVARIANTS[0]
        with pytest.raises(FrozenInstanceError):
            inv.code = "OTHER"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class TestGetInvariant:
    def test_returns_known_code(self) -> None:
        inv = get_invariant("ADAPTER_CANNOT_OUTPUT_NEURAL_SEED")
        assert isinstance(inv, InvariantDefinition)
        assert inv.code == "ADAPTER_CANNOT_OUTPUT_NEURAL_SEED"
        assert inv.category is InvariantCategory.ADAPTER_BOUNDARY

    def test_unknown_code_raises_keyerror(self) -> None:
        with pytest.raises(KeyError):
            get_invariant("THIS_IS_NOT_AN_INVARIANT")


class TestListInvariants:
    def test_unfiltered_returns_full_catalog(self) -> None:
        assert list_invariants() == MVP_REQUIRED_INVARIANTS

    def test_filter_by_category(self) -> None:
        rows = list_invariants(category=InvariantCategory.ADAPTER_BOUNDARY)
        assert len(rows) > 0
        assert all(r.category is InvariantCategory.ADAPTER_BOUNDARY for r in rows)

    def test_filter_by_mvp_required_true(self) -> None:
        rows = list_invariants(mvp_required=True)
        assert rows == MVP_REQUIRED_INVARIANTS

    def test_filter_by_mvp_required_false_empty(self) -> None:
        rows = list_invariants(mvp_required=False)
        assert rows == ()

    def test_filter_by_category_and_mvp_required(self) -> None:
        rows = list_invariants(category=InvariantCategory.WORKSPACE, mvp_required=True)
        assert len(rows) >= 2
        assert all(r.category is InvariantCategory.WORKSPACE for r in rows)


# ---------------------------------------------------------------------------
# assert_invariant
# ---------------------------------------------------------------------------


class TestAssertInvariant:
    def test_true_condition_does_not_raise(self) -> None:
        assert_invariant(True, "ADAPTER_EXECUTE_REQUIRES_OBSERVE")

    def test_false_condition_raises_invariant_violation(self) -> None:
        with pytest.raises(InvariantViolation):
            assert_invariant(False, "ADAPTER_EXECUTE_REQUIRES_OBSERVE")

    def test_raised_violation_is_constitutional_violation(self) -> None:
        with pytest.raises(ConstitutionalViolation):
            assert_invariant(False, "ADAPTER_EXECUTE_REQUIRES_OBSERVE")

    def test_raised_violation_carries_code_and_source(self) -> None:
        try:
            assert_invariant(False, "WORKSPACE_SINGLE_PULSE_EVENT_TYPE")
        except InvariantViolation as exc:
            assert exc.violation_code == "WORKSPACE_SINGLE_PULSE_EVENT_TYPE"
            assert "BOOTSTRAP_GENOME.md" in exc.source_ref
        else:
            pytest.fail("expected InvariantViolation")

    def test_evidence_is_carried_through(self) -> None:
        try:
            assert_invariant(
                False,
                "ADAPTER_CANNOT_OUTPUT_NEURAL_SEED",
                evidence={"observed_output": "NeuralSeed"},
            )
        except InvariantViolation as exc:
            assert exc.evidence["observed_output"] == "NeuralSeed"
        else:
            pytest.fail("expected InvariantViolation")

    def test_evidence_defaults_to_empty(self) -> None:
        try:
            assert_invariant(False, "MVP_FORBIDS_LIVE_EXCHANGE_IMPORTS")
        except InvariantViolation as exc:
            assert dict(exc.evidence) == {}
        else:
            pytest.fail("expected InvariantViolation")

    def test_unknown_code_raises_keyerror(self) -> None:
        with pytest.raises(KeyError):
            assert_invariant(False, "NO_SUCH_INVARIANT")


# ---------------------------------------------------------------------------
# Critical MVP red lines
# ---------------------------------------------------------------------------


class TestCriticalRedLines:
    """The catalog must enumerate the constitutional red lines for MVP."""

    @pytest.mark.parametrize(
        "code",
        [
            "ADAPTER_CANNOT_OUTPUT_NEURAL_SEED",
            "WORKSPACE_SINGLE_PULSE_EVENT_TYPE",
            "WORKSPACE_NO_PULSE_CATEGORY",
            "MVP_FORBIDS_EXECUTION_OUTPUTS",
            "MVP_FORBIDS_LIVE_EXCHANGE_IMPORTS",
            "MVP_FORBIDS_LLM_IMPORTS",
            "FOREIGN_INSTANCE_ORIGIN_NOT_SUBJECT_CLASS",
            "NUMERIC_IMMUTABLE_SINGLE_RANGE_FORBIDDEN_BOTH_DIRECTIONS",
            "PAYLOAD_CLOSED_PRIMER_PALETTE",
            "INGRESS_EVENT_TYPE_FIXED",
        ],
    )
    def test_red_line_present(self, code: str) -> None:
        inv = get_invariant(code)
        assert inv.code == code
