"""Constitutional violation exception types.

Per the build plan §6 (Phase 1 — Contracts as Code): this module pins
the **exception vocabulary** that the runtime uses to signal a
constitutional breach. The actual invariant catalog (and the
checker functions that produce these exceptions) lives in
`sentinel/constitution/invariants.py` (next commit).

Design intent:
    - One frozen `ViolationContext` payload carrying:
        * violation_code (closed-set short string identifier)
        * source_ref (path / section anchor to the breached rule)
        * evidence (read-only mapping; defensively copied + proxied)
    - One `ConstitutionalViolation` base exception
    - Specialized subclasses for the breach categories the system
      must distinguish at the catch-site

What this module deliberately does NOT contain:
    - Invariant catalog (Commit 11)
    - Invariant checker functions (Commit 11)
    - Imports from `sentinel.types.*` schemas (kept decoupled so the
      exception module has zero internal dependencies)
    - Runtime enforcement / observer hookup (later phases)
    - Severity / quarantine policy
"""

from __future__ import annotations

from collections.abc import Mapping  # noqa: TC003 (dataclass field runtime annotation)
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any


@dataclass(frozen=True, slots=True)
class ViolationContext:
    """Immutable evidence packet for one constitutional breach.

    Fields:
        violation_code: closed-set short identifier
            (e.g. "FORBIDDEN_FIELD", "SCHEMA_BOUNDARY",
             "INVARIANT_FAILED", "CAPABILITY_BOUNDARY",
             "RUNTIME_MODE", "NUMERICS_GOVERNANCE").
            Treated as opaque here; the invariants module fixes the
            canonical set.
        source_ref: dotted / colon reference into the spec
            (e.g. "CONSTITUTION.md §6:Madde-6" or
             "ADAPTER_MANIFEST_SPEC.md §7.binding-matrix").
        evidence: read-only mapping of structured facts about the
            breach. The constructor defensively copies the input and
            wraps it in a `MappingProxyType` so the payload cannot
            be mutated after construction (even via the original
            dict the caller passed in).
    """

    violation_code: str
    source_ref: str
    evidence: Mapping[str, Any] = field(default_factory=lambda: {})

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "evidence",
            MappingProxyType(dict(self.evidence)),
        )


class ConstitutionalViolation(Exception):
    """Base exception for any constitutional breach.

    Carries both a human-readable `message` and a structured
    `ViolationContext` (`context`). The context is what gets logged
    to the observer / M1 JSONL ledger; the message is for human
    operators.
    """

    def __init__(self, message: str, context: ViolationContext) -> None:
        super().__init__(message)
        self.message = message
        self.context = context

    @property
    def violation_code(self) -> str:
        return self.context.violation_code

    @property
    def source_ref(self) -> str:
        return self.context.source_ref

    @property
    def evidence(self) -> Mapping[str, Any]:
        return self.context.evidence


class SchemaBoundaryViolation(ConstitutionalViolation):
    """A value crossed a schema boundary that should have rejected it
    (e.g. forbidden discriminator, malformed envelope, extra=forbid
    payload made it through despite a defensive call site)."""


class ForbiddenFieldViolation(ConstitutionalViolation):
    """A forbidden field / token reached a layer that must never see
    it (e.g. a domain ticker, an action verb the constitution
    forbids as system output, or a forbidden third-party import
    path)."""


class InvariantViolation(ConstitutionalViolation):
    """A constitutional invariant in the catalog failed
    (e.g. "neural seed total_intensity must equal sum of payload
    intensities"). The invariant catalog lives in `invariants.py`."""


class CapabilityBoundaryViolation(ConstitutionalViolation):
    """An adapter / module exceeded its declared capability boundary
    (e.g. an `observe`-only adapter attempted an `execute` channel
    output)."""


class RuntimeModeViolation(ConstitutionalViolation):
    """An operation incompatible with the current runtime mode was
    attempted (e.g. live-execution call site reached in MVP
    schema-only runtime)."""


class NumericsGovernanceViolation(ConstitutionalViolation):
    """A numerics-governance rule failed at the artifact / entry
    layer (e.g. constitutional immutable invariant breach,
    safety_weakening change without human approval,
    dependency cycle detection)."""
