"""MVP output enum + forbidden-output guard.

Per build plan §15 and §20 (red lines): the system's only sanctioned
output set in MVP is `{WAIT, BLOCK, MONITOR, NEED_RECALL, NO_ACTION}`.
Live-execution verbs (buy / sell / execute_real / order_submit and
friends) MUST NEVER appear as system output — neither as
`SystemOutput` enum values nor as string literals in any
ObserverEvent payload that reaches M1.

This module exposes:
    - `SystemOutput`: the closed 5-value enum
    - `FORBIDDEN_OUTPUT_LITERALS`: a frozenset of substrings that
      MUST NOT appear in any output reason / payload
    - `assert_no_forbidden_literal(text)`: raises
      `InvariantViolation(MVP_FORBIDS_EXECUTION_OUTPUTS)` if `text`
      contains any forbidden literal (case-insensitive substring)
"""

from __future__ import annotations

from enum import StrEnum

from sentinel.constitution.violations import (
    ConstitutionalViolation,
    ViolationContext,
)


class SystemOutput(StrEnum):
    """The closed MVP system-output set (build plan §15)."""

    WAIT = "WAIT"
    BLOCK = "BLOCK"
    MONITOR = "MONITOR"
    NEED_RECALL = "NEED_RECALL"
    NO_ACTION = "NO_ACTION"


# Forbidden substrings: substring match is case-INSENSITIVE so that
# `Buy` / `bUy` / `Execute_Real` all trip the guard.
FORBIDDEN_OUTPUT_LITERALS: frozenset[str] = frozenset(
    {
        "buy",
        "sell",
        "execute_real",
        "order_submit",
        "execute",
        "order",
        "submit",
        "_real",
    }
)


class ForbiddenOutputViolation(ConstitutionalViolation):
    """A forbidden execution-output literal escaped into the output path."""


def assert_no_forbidden_literal(text: str) -> None:
    """Raise ForbiddenOutputViolation if any forbidden literal is in `text`."""
    lower = text.lower()
    for needle in FORBIDDEN_OUTPUT_LITERALS:
        if needle in lower:
            raise ForbiddenOutputViolation(
                f"forbidden output literal {needle!r} present in output text",
                ViolationContext(
                    violation_code="MVP_FORBIDS_EXECUTION_OUTPUTS",
                    source_ref="build plan §15, §20",
                    evidence={
                        "needle": needle,
                        "text_length": len(text),
                    },
                ),
            )
