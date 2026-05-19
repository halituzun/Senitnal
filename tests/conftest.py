"""Sentinel pytest configuration.

Per build plan §16 (Test-first Discipline):
    - Invariant tests are MVP REQUIRED; no skip / xfail.
    - Test categories: invariant, integration, simulation (markers in pyproject.toml).

This file intentionally minimal at Commit 1; fixtures added in Phase 1+.
"""

from __future__ import annotations
