"""Tests for the curated `from sentinel import ...` public API."""

from __future__ import annotations

import importlib

# v0.1 baseline contract. This snapshot pins the curated public
# surface; the drift test below fails if any symbol is REMOVED
# (breaking change). New symbols added via ADDITION are tolerated —
# update the baseline only when intentionally promoting a symbol
# into the public surface.
V01_PUBLIC_API_BASELINE: frozenset[str] = frozenset(
    {
        "AdapterTrustRecord",
        "ApprovedActionIntent",
        "BlockClass",
        "ConstitutionalViolation",
        "DeonticDecision",
        "DeonticOutcome",
        "DrySimResult",
        "EchoAdapter",
        "EventFamily",
        "EventPermanence",
        "EventProfile",
        "InvariantCategory",
        "InvariantDefinition",
        "InvariantSeverity",
        "InvariantViolation",
        "JsonlObserverLedger",
        "MVP_REQUIRED_INVARIANTS",
        "NeuralSeed",
        "ObserverEvent",
        "ObserverRingBuffer",
        "PayloadSeed",
        "PrimerPayload",
        "ProvenanceRef",
        "RoutingOutcome",
        "SystemOutput",
        "TrustBand",
        "ViolationContext",
        "__version__",
        "assert_invariant",
        "compute_trust",
        "emit_manifest_status_changed",
        "emit_neural_seed_attempt_revoke",
        "emit_recall_request",
        "emit_recall_result_empty",
        "emit_recall_trigger_rejected",
        "evaluate_action",
        "evaluate_action_with_audit",
        "get_invariant",
        "list_invariants",
        "route_observer_event",
        "run_dry_simulation",
    }
)


class TestPublicApi:
    def test_all_listed_symbols_importable(self) -> None:
        mod = importlib.import_module("sentinel")
        names = list(mod.__all__)
        assert len(names) > 0
        for name in names:
            assert hasattr(mod, name), f"sentinel.__all__ lists {name!r} but it is missing"

    def test_baseline_symbols_still_exported(self) -> None:
        """v0.1 contract: no baseline symbol may be REMOVED."""
        mod = importlib.import_module("sentinel")
        current = set(mod.__all__)
        missing = V01_PUBLIC_API_BASELINE - current
        assert missing == set(), (
            f"v0.1 public API contract broken: {sorted(missing)} removed. "
            "If this is intentional, update V01_PUBLIC_API_BASELINE in "
            "tests/test_public_api.py."
        )

    def test_no_internal_modules_in_export(self) -> None:
        """Every public symbol must trace back to sentinel.*"""
        mod = importlib.import_module("sentinel")
        for name in mod.__all__:
            if name == "__version__":
                continue
            obj = getattr(mod, name)
            origin = getattr(obj, "__module__", "") or ""
            if origin:
                assert origin.startswith("sentinel"), (
                    f"{name!r} comes from {origin!r}; public API must only "
                    "expose sentinel.* objects"
                )

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

    def test_version_pinned_to_v0_1(self) -> None:
        """Release contract: v0.1.x line."""
        from sentinel import __version__

        assert __version__.startswith("0.1."), f"v0.1 release line expected; got {__version__!r}"
