"""Constitutional invariants and violation types.

Source of truth for the MVP REQUIRED invariants harvested from the
22 frozen draft documents (CONSTITUTION.md, DEONTIC_GATE.md,
ADAPTER_MANIFEST_SPEC.md, RECALL_PROTOCOL.md, ...).

Modules:
    violations.py   ViolationContext + ConstitutionalViolation
                    hierarchy (6 specialized subclasses).
    invariants.py   InvariantSeverity / InvariantCategory enums,
                    InvariantDefinition dataclass,
                    MVP_REQUIRED_INVARIANTS catalog (44 rows for
                    v0.1) + assert_invariant / get_invariant /
                    list_invariants helpers.

For ergonomic access prefer `from sentinel import ...`; this
subpackage's deeper paths remain stable for explicit imports.
"""
