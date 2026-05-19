"""Smoke test — package skeleton is importable.

This test exists so `pytest` has at least one test to run at Commit 1.
It will be supplemented by real schema/invariant tests in Phase 1.
"""

from __future__ import annotations

import importlib

import sentinel


def test_package_version() -> None:
    """Sentinel package exposes a version string."""
    assert sentinel.__version__ == "0.1.0"


def test_subpackages_importable() -> None:
    """All 11 subpackages are importable as part of the skeleton."""
    subpackages = [
        "sentinel.adapters",
        "sentinel.constitution",
        "sentinel.gates",
        "sentinel.ingress",
        "sentinel.m0",
        "sentinel.numerics",
        "sentinel.observer",
        "sentinel.recall",
        "sentinel.runtime",
        "sentinel.types",
        "sentinel.workspace",
    ]
    for name in subpackages:
        module = importlib.import_module(name)
        assert module is not None
