"""Smoke test — package skeleton is importable.

This test exists so `pytest` has at least one test to run at Commit 1.
It will be replaced by real schema/invariant tests in Phase 1.
"""

from __future__ import annotations

import sentinel


def test_package_version() -> None:
    """Sentinel package exposes a version string."""
    assert sentinel.__version__ == "0.1.0"


def test_subpackages_importable() -> None:
    """All 11 subpackages are importable as part of the skeleton."""
    import sentinel.adapters  # noqa: F401
    import sentinel.constitution  # noqa: F401
    import sentinel.gates  # noqa: F401
    import sentinel.ingress  # noqa: F401
    import sentinel.m0  # noqa: F401
    import sentinel.numerics  # noqa: F401
    import sentinel.observer  # noqa: F401
    import sentinel.recall  # noqa: F401
    import sentinel.runtime  # noqa: F401
    import sentinel.types  # noqa: F401
    import sentinel.workspace  # noqa: F401
