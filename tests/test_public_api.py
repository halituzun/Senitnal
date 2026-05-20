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

# V2 additive surface — read-only market observation adapters.
# Per v0.1 contract, ADDITIONS to the public API are tolerated; the
# drift test below only fails on REMOVAL of a baseline symbol.
V2_PUBLIC_API_ADDITIONS: frozenset[str] = frozenset(
    {
        "LocalJsonlMarketAdapter",
        "MarketObservationEnvelope",
        "MarketReplayResult",
        "SanitizedMarketProvenance",
        "SyntheticMarketAdapter",
        "build_market_observation_audit_payload",
        "run_market_jsonl_file",
        "run_market_observations",
        "sanitize_market_observation_to_event",
    }
)

# V4 additive surface — replay / counterfactual.
# Additive only; no v0.1 / V2 / V3 baseline removal.
V4_PUBLIC_API_ADDITIONS: frozenset[str] = frozenset(
    {
        "AblationKind",
        "CounterfactualAblation",
        "CounterfactualAblationResult",
        "OutcomeAlignmentEvidence",
        "OutcomeRef",
        "ReplayBudget",
        "ReplayBudgetState",
        "ReplayEffectChannel",
        "ReplayFinancialPipelineResult",
        "ReplayInputSnapshot",
        "ReplayPurpose",
        "ReplaySession",
        "ReplaySessionStatus",
        "ReplaySurvivalEvidence",
        "can_start_replay_session",
        "run_replay_financial_pipeline",
    }
)

# V3 additive surface — financial M2 memory + recall.
# Additive only; no v0.1 / V2 baseline removal.
V3_PUBLIC_API_ADDITIONS: frozenset[str] = frozenset(
    {
        "ExecutionQualityObservationPayload",
        "FinancialMemoryPipelineResult",
        "FinancialMemoryWriteResult",
        "FinancialRecallRequest",
        "FinancialRecallScope",
        "InMemoryExplicitMemoryStore",
        "LatencyPatternPayload",
        "LiquidityConditionPayload",
        "MarketRegimeObservationPayload",
        "SpreadWindowObservationPayload",
        "build_candidate_financial_memory_record",
        "build_financial_recall_event",
        "run_financial_memory_pipeline",
        "select_financial_recall_top_one",
        "submit_financial_memory_candidate",
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

    def test_v2_additions_exported(self) -> None:
        """V2 additive contract: every documented V2 symbol is exported."""
        mod = importlib.import_module("sentinel")
        current = set(mod.__all__)
        missing = V2_PUBLIC_API_ADDITIONS - current
        assert missing == set(), (
            f"V2 additive public API missing exports: {sorted(missing)}. "
            "Either add them to sentinel/__init__.py __all__, or update "
            "V2_PUBLIC_API_ADDITIONS in tests/test_public_api.py."
        )

    def test_v3_additions_exported(self) -> None:
        """V3 additive contract: every documented V3 symbol is exported."""
        mod = importlib.import_module("sentinel")
        current = set(mod.__all__)
        missing = V3_PUBLIC_API_ADDITIONS - current
        assert missing == set(), (
            f"V3 additive public API missing exports: {sorted(missing)}. "
            "Either add them to sentinel/__init__.py __all__, or update "
            "V3_PUBLIC_API_ADDITIONS in tests/test_public_api.py."
        )

    def test_v4_additions_exported(self) -> None:
        """V4 additive contract: every documented V4 symbol is exported."""
        mod = importlib.import_module("sentinel")
        current = set(mod.__all__)
        missing = V4_PUBLIC_API_ADDITIONS - current
        assert missing == set(), (
            f"V4 additive public API missing exports: {sorted(missing)}. "
            "Either add them to sentinel/__init__.py __all__, or update "
            "V4_PUBLIC_API_ADDITIONS in tests/test_public_api.py."
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
