"""V9 — Limited live governance scope schema tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sentinel.governance.scope import (
    GovernanceEnvironment,
    GovernanceScopeKind,
    LimitedLiveGovernanceScope,
)

from tests.governance._fixtures import make_scope


class TestScopeSchema:
    def test_valid_limited_live_accepted(self) -> None:
        s = make_scope()
        assert s.environment is GovernanceEnvironment.LIMITED_LIVE

    def test_symbol_hash_required(self) -> None:
        with pytest.raises(ValidationError):
            LimitedLiveGovernanceScope(
                scope_id="s",
                environment=GovernanceEnvironment.LIMITED_LIVE,
                scope_kind=GovernanceScopeKind.SYMBOL_SCOPE,
                applies_to_all_symbols=False,
                applies_to_all_strategies=False,
                max_candidates_per_hour=100,
                max_live_impacting_blocks_per_hour=50,
                max_governance_latency_ms=2000,
                created_at_ms=1_000_000,
            )

    def test_fail_closed_flags_must_be_true(self) -> None:
        with pytest.raises(ValidationError):
            LimitedLiveGovernanceScope(
                scope_id="s",
                environment=GovernanceEnvironment.LIMITED_LIVE,
                scope_kind=GovernanceScopeKind.SYMBOL_SCOPE,
                symbol_hash="sha256:s",
                venue_hash="sha256:v",
                strategy_hash="sha256:t",
                applies_to_all_symbols=False,
                applies_to_all_strategies=False,
                max_candidates_per_hour=100,
                max_live_impacting_blocks_per_hour=50,
                max_governance_latency_ms=2000,
                fail_closed_on_missing_policy=False,  # type: ignore[arg-type]
                created_at_ms=1_000_000,
            )

    def test_human_approval_required_pinned(self) -> None:
        with pytest.raises(ValidationError):
            LimitedLiveGovernanceScope(
                scope_id="s",
                environment=GovernanceEnvironment.LIMITED_LIVE,
                scope_kind=GovernanceScopeKind.SYMBOL_SCOPE,
                symbol_hash="sha256:s",
                venue_hash="sha256:v",
                strategy_hash="sha256:t",
                applies_to_all_symbols=False,
                applies_to_all_strategies=False,
                max_candidates_per_hour=100,
                max_live_impacting_blocks_per_hour=50,
                max_governance_latency_ms=2000,
                human_approval_required=False,  # type: ignore[arg-type]
                created_at_ms=1_000_000,
            )

    def test_expires_before_created_rejected(self) -> None:
        with pytest.raises(ValidationError):
            LimitedLiveGovernanceScope(
                scope_id="s",
                environment=GovernanceEnvironment.LIMITED_LIVE,
                scope_kind=GovernanceScopeKind.SYMBOL_SCOPE,
                symbol_hash="sha256:s",
                venue_hash="sha256:v",
                strategy_hash="sha256:t",
                applies_to_all_symbols=False,
                applies_to_all_strategies=False,
                max_candidates_per_hour=100,
                max_live_impacting_blocks_per_hour=50,
                max_governance_latency_ms=2000,
                created_at_ms=2_000_000,
                expires_at_ms=1_000_000,
            )

    @pytest.mark.parametrize(
        "bad_field",
        ["symbol", "venue", "strategy_name", "order_side", "api_key", "balance"],
    )
    def test_forbidden_raw_field_rejected(self, bad_field: str) -> None:
        base: dict[str, object] = {
            "scope_id": "s",
            "environment": GovernanceEnvironment.LIMITED_LIVE,
            "scope_kind": GovernanceScopeKind.SYMBOL_SCOPE,
            "symbol_hash": "sha256:s",
            "venue_hash": "sha256:v",
            "strategy_hash": "sha256:t",
            "applies_to_all_symbols": False,
            "applies_to_all_strategies": False,
            "max_candidates_per_hour": 100,
            "max_live_impacting_blocks_per_hour": 50,
            "max_governance_latency_ms": 2000,
            "created_at_ms": 1_000_000,
        }
        base[bad_field] = "x"
        with pytest.raises(ValidationError):
            LimitedLiveGovernanceScope(**base)  # type: ignore[arg-type]

    def test_frozen_immutable(self) -> None:
        s = make_scope()
        with pytest.raises(ValidationError):
            s.scope_id = "other"  # type: ignore[misc]
