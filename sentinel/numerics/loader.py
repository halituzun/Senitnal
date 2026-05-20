"""Numerics artifact loader.

Per NUMERICS_GOVERNANCE.md §8-13 and the Phase 3 build plan: this
module loads a `NumericsArtifact` from a JSON file, enforces the
`dev_only` mode invariant, and exposes a missing-file failure path
that callers can wrap into `NUMERICS_FAILSAFE_ACTIVATED`.

Constitutional discipline (loader layer only):
    - `LoaderMode.DEVELOPMENT` accepts `dev_only=true` artifacts;
      `LoaderMode.PRODUCTION` rejects them
    - All schema-level invariants (no-default, immutable single
      range, entry-vs-artifact spec_family, etc.) are inherited
      from the `NumericsArtifact` Pydantic model — the loader does
      NOT re-implement them; it lets the schema layer raise
    - The loader does NOT emit ObserverEvents itself; emission is
      the caller's responsibility. The loader just translates JSON
      to typed values and raises `InvariantViolation` on a mode
      mismatch, or `MissingArtifactError` when the file is absent
    - Cross-key dependency validation (cycle detection, undefined
      ref resolution) lives in `dependency_validator.py`

What this module deliberately does NOT contain:
    - Signature verification (Phase 3+)
    - Manifest-level numerics_version reconciliation
    - Observer event emission (caller decides)
    - Dependency cycle detection (Commit 20)
"""

from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path  # noqa: TC003 (runtime annotation)

from sentinel.constitution.violations import InvariantViolation, ViolationContext
from sentinel.types.numerics import NumericsArtifact


class LoaderMode(StrEnum):
    """Loader posture (M §8)."""

    DEVELOPMENT = "development"
    PRODUCTION = "production"


class MissingArtifactError(FileNotFoundError):
    """Raised when a numerics artifact file does not exist.

    Callers should translate this into a `NUMERICS_FAILSAFE_ACTIVATED`
    observer event before re-raising or recovering.
    """


def load_artifact(path: Path, *, mode: LoaderMode) -> NumericsArtifact:
    """Load and validate a NumericsArtifact from `path`.

    Behaviour:
        - Raises `MissingArtifactError` if `path` does not exist
        - Parses JSON; raises `ValueError` on malformed JSON
        - Validates via `NumericsArtifact.model_validate` (all
          schema-level invariants apply: no-default, immutable
          consistency, entry-vs-artifact spec_family, unique keys,
          dev_only ↔ fixture_purpose)
        - If `mode is PRODUCTION` and the loaded artifact has
          `dev_only=True`, raises `InvariantViolation`
          (`NUMERICS_DEV_ONLY_REJECTED_IN_PRODUCTION`) with evidence
          carrying the artifact path and spec_family
    """
    if not path.exists():
        raise MissingArtifactError(f"numerics artifact missing: {path}")
    raw_text = path.read_text(encoding="utf-8")
    # Parse once up front to surface malformed-JSON errors with the
    # artifact path in the message, then hand off to Pydantic's
    # JSON-mode validator (which handles list→tuple, str→enum
    # coercion correctly under strict=True).
    try:
        json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"malformed JSON in numerics artifact {path}: {exc.msg}") from exc

    artifact = NumericsArtifact.model_validate_json(raw_text)

    if mode is LoaderMode.PRODUCTION and artifact.dev_only:
        raise InvariantViolation(
            (
                f"dev_only artifact rejected in production mode: "
                f"{path} (spec_family={artifact.spec_family.value!r})"
            ),
            ViolationContext(
                violation_code="NUMERICS_DEV_ONLY_REJECTED_IN_PRODUCTION",
                source_ref="NUMERICS_GOVERNANCE.md §8 + build plan §8",
                evidence={
                    "path": str(path),
                    "spec_family": artifact.spec_family.value,
                    "numerics_version": artifact.numerics_version,
                },
            ),
        )

    return artifact
