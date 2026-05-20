"""Cross-key dependency validator for NumericsArtifact.

Per NUMERICS_GOVERNANCE.md §12 and the Phase 3 build plan: this
module checks that every `NumericDependency.target_key` declared by
an entry in a `NumericsArtifact` actually points at another entry
in the same artifact, and that the directed graph induced by those
dependencies has no cycles.

Constitutional discipline (validator layer only):
    - Within-artifact only. Cross-artifact dependency resolution is
      a Phase 3+ concern (it requires the manifest layer)
    - Self-dependencies are always treated as cycles
    - Validation is one-shot; raises on the FIRST violation found
      (a richer multi-error reporter can come later)

What this module deliberately does NOT contain:
    - Cross-artifact key resolution
    - `expression` evaluation (for `computed_*` relationships)
    - Factor numeric satisfiability checks (e.g. is the value
      within `factor` of the target?)
    - Topological sort surfacing for callers (returns None on
      success; the artifact itself is the result)
"""

from __future__ import annotations

from sentinel.constitution.violations import (
    NumericsGovernanceViolation,
    ViolationContext,
)
from sentinel.types.numerics import NumericsArtifact  # noqa: TC001 (runtime)


def validate_dependencies(artifact: NumericsArtifact) -> None:
    """Validate dependency references and detect cycles.

    Raises:
        NumericsGovernanceViolation with violation_code
            "NUMERICS_DEPENDENCY_UNKNOWN_KEY" if any
            NumericDependency.target_key does not appear among the
            artifact's entry keys.
        NumericsGovernanceViolation with violation_code
            "NUMERICS_DEPENDENCY_CYCLE_DETECTED" if the directed
            dependency graph contains a cycle (self-references
            included).
    """
    keys = {entry.key for entry in artifact.entries}
    adjacency: dict[str, list[str]] = {entry.key: [] for entry in artifact.entries}

    for entry in artifact.entries:
        for dep in entry.dependencies:
            if dep.target_key not in keys:
                raise NumericsGovernanceViolation(
                    (
                        f"entry {entry.key!r} declares dependency on unknown "
                        f"target_key {dep.target_key!r}"
                    ),
                    ViolationContext(
                        violation_code="NUMERICS_DEPENDENCY_UNKNOWN_KEY",
                        source_ref="NUMERICS_GOVERNANCE.md §12",
                        evidence={
                            "entry_key": entry.key,
                            "target_key": dep.target_key,
                            "spec_family": artifact.spec_family.value,
                        },
                    ),
                )
            adjacency[entry.key].append(dep.target_key)

    _assert_acyclic(adjacency, artifact)


def _assert_acyclic(
    adjacency: dict[str, list[str]],
    artifact: NumericsArtifact,
) -> None:
    """DFS cycle detection over the dependency adjacency graph."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {key: WHITE for key in adjacency}

    def visit(node: str, path: list[str]) -> None:
        color[node] = GRAY
        path.append(node)
        for nxt in adjacency[node]:
            if color[nxt] == GRAY:
                cycle = [*path[path.index(nxt) :], nxt]
                raise NumericsGovernanceViolation(
                    f"dependency cycle detected: {' -> '.join(cycle)}",
                    ViolationContext(
                        violation_code="NUMERICS_DEPENDENCY_CYCLE_DETECTED",
                        source_ref="NUMERICS_GOVERNANCE.md §12",
                        evidence={
                            "cycle": cycle,
                            "spec_family": artifact.spec_family.value,
                        },
                    ),
                )
            if color[nxt] == WHITE:
                visit(nxt, path)
        path.pop()
        color[node] = BLACK

    for key in adjacency:
        if color[key] == WHITE:
            visit(key, [])
