"""Tests for the curated `from sentinel import ...` public API."""

from __future__ import annotations

import importlib


class TestPublicApi:
    def test_all_listed_symbols_importable(self) -> None:
        mod = importlib.import_module("sentinel")
        names = list(mod.__all__)
        assert len(names) > 0
        for name in names:
            assert hasattr(mod, name), f"sentinel.__all__ lists {name!r} but it is missing"

    def test_critical_public_types_present(self) -> None:
        from sentinel import (
            EchoAdapter,
            JsonlObserverLedger,
            SystemOutput,
            run_dry_simulation,
        )

        assert SystemOutput.WAIT.value == "WAIT"
        assert callable(run_dry_simulation)
        assert EchoAdapter.__name__ == "EchoAdapter"
        assert JsonlObserverLedger.__name__ == "JsonlObserverLedger"

    def test_violation_hierarchy_exported(self) -> None:
        from sentinel import (
            ConstitutionalViolation,
            InvariantViolation,
            ViolationContext,
        )

        assert issubclass(InvariantViolation, ConstitutionalViolation)
        ctx = ViolationContext(violation_code="X", source_ref="Y")
        assert isinstance(ctx, ViolationContext)

    def test_invariant_catalog_exported(self) -> None:
        from sentinel import MVP_REQUIRED_INVARIANTS, get_invariant

        assert len(MVP_REQUIRED_INVARIANTS) > 0
        any_code = MVP_REQUIRED_INVARIANTS[0].code
        assert get_invariant(any_code).code == any_code


class TestVersion:
    def test_version_string(self) -> None:
        from sentinel import __version__

        assert isinstance(__version__, str)
        # PEP 440 minimal sanity: major.minor.patch
        parts = __version__.split(".")
        assert len(parts) >= 2
