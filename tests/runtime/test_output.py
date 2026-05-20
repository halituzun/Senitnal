"""Tests for the SystemOutput enum + forbidden literal guard."""

from __future__ import annotations

import pytest
from sentinel.runtime.output import (
    FORBIDDEN_OUTPUT_LITERALS,
    ForbiddenOutputViolation,
    SystemOutput,
    assert_no_forbidden_literal,
)


class TestSystemOutput:
    def test_exactly_five_values(self) -> None:
        assert len(SystemOutput) == 5

    def test_canonical_values(self) -> None:
        expected = {"WAIT", "BLOCK", "MONITOR", "NEED_RECALL", "NO_ACTION"}
        assert {o.value for o in SystemOutput} == expected

    def test_no_execution_verbs_in_enum(self) -> None:
        values = {o.value for o in SystemOutput}
        for forbidden in ("BUY", "SELL", "EXECUTE", "ORDER", "SUBMIT"):
            assert forbidden not in values


class TestForbiddenLiteralGuard:
    def test_clean_text_passes(self) -> None:
        assert_no_forbidden_literal("WAIT decided by deontic gate")

    @pytest.mark.parametrize(
        "needle",
        sorted(FORBIDDEN_OUTPUT_LITERALS),
    )
    def test_forbidden_literal_rejected(self, needle: str) -> None:
        with pytest.raises(ForbiddenOutputViolation) as exc_info:
            assert_no_forbidden_literal(f"prefix {needle} suffix")
        assert exc_info.value.violation_code == "MVP_FORBIDS_EXECUTION_OUTPUTS"
        # Any forbidden substring within `needle` may be the reported
        # match (since some literals contain others, e.g. "execute" is
        # a substring of "execute_real"). Just assert the reported
        # needle is itself in the forbidden set.
        reported = exc_info.value.evidence["needle"]
        assert reported in FORBIDDEN_OUTPUT_LITERALS

    def test_case_insensitive(self) -> None:
        with pytest.raises(ForbiddenOutputViolation):
            assert_no_forbidden_literal("BUY THIS TICKER")
        with pytest.raises(ForbiddenOutputViolation):
            assert_no_forbidden_literal("Order placed")

    def test_substring_match(self) -> None:
        # "execute_real" appears inside "preexecute_realm" — substring guard
        # fires regardless of word boundaries.
        with pytest.raises(ForbiddenOutputViolation):
            assert_no_forbidden_literal("preexecute_realm thing")


class TestSubclass:
    def test_forbidden_violation_is_constitutional(self) -> None:
        from sentinel.constitution.violations import ConstitutionalViolation

        with pytest.raises(ConstitutionalViolation):
            assert_no_forbidden_literal("buy now")
