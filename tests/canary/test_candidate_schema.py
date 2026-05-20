"""V8 — Canary candidate schema tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sentinel.canary.candidate import (
    CanaryCandidateAction,
    CanaryCandidateSource,
    CanaryEnvironment,
)

from tests.canary._fixtures import make_candidate


class TestCandidateSchema:
    def test_valid_candidate_accepted(self) -> None:
        c = make_candidate()
        assert c.candidate_id == "cand-1"

    def test_expires_before_observed_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CanaryCandidateAction(
                candidate_id="x",
                source=CanaryCandidateSource.GELAL_SHADOW,
                environment=CanaryEnvironment.MICRO_LIVE_CANARY,
                observed_at_ms=1000,
                expires_at_ms=500,
                source_event_refs=("ev-1",),
                provenance_hash="sha256:p",
                scope_hash="sha256:s",
                notional_ref="tier:micro",
                risk_score=0.1,
                confidence=0.7,
                staleness_ms=0,
                latency_ms=0,
                orderbook_age_ms=0,
                spread_pct=0.0,
                liquidity_score=0.5,
                expected_net_edge_pct=0.1,
                expected_slippage_pct=0.0,
                expected_fee_pct=0.0,
            )

    @pytest.mark.parametrize(
        "bad_field",
        [
            "symbol",
            "venue",
            "strategy_name",
            "side",
            "order_side",
            "api_key",
            "balance",
            "position",
            "set_kill_switch",
            "redis_stream",
            "orders_pending_payload",
            "direct_order",
        ],
    )
    def test_forbidden_field_rejected(self, bad_field: str) -> None:
        base: dict[str, object] = {
            "candidate_id": "x",
            "source": CanaryCandidateSource.GELAL_SHADOW,
            "environment": CanaryEnvironment.MICRO_LIVE_CANARY,
            "observed_at_ms": 0,
            "expires_at_ms": 1000,
            "source_event_refs": ("ev-1",),
            "provenance_hash": "sha256:p",
            "scope_hash": "sha256:s",
            "notional_ref": "tier:micro",
            "risk_score": 0.1,
            "confidence": 0.7,
            "staleness_ms": 0,
            "latency_ms": 0,
            "orderbook_age_ms": 0,
            "spread_pct": 0.0,
            "liquidity_score": 0.5,
            "expected_net_edge_pct": 0.1,
            "expected_slippage_pct": 0.0,
            "expected_fee_pct": 0.0,
        }
        base[bad_field] = "x"
        with pytest.raises(ValidationError):
            CanaryCandidateAction(**base)  # type: ignore[arg-type]

    def test_frozen_immutable(self) -> None:
        c = make_candidate()
        with pytest.raises(ValidationError):
            c.candidate_id = "other"  # type: ignore[misc]

    def test_empty_source_event_refs_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CanaryCandidateAction(
                candidate_id="x",
                source=CanaryCandidateSource.GELAL_SHADOW,
                environment=CanaryEnvironment.MICRO_LIVE_CANARY,
                observed_at_ms=0,
                expires_at_ms=1000,
                source_event_refs=(),
                provenance_hash="sha256:p",
                scope_hash="sha256:s",
                notional_ref="tier:micro",
                risk_score=0.1,
                confidence=0.7,
                staleness_ms=0,
                latency_ms=0,
                orderbook_age_ms=0,
                spread_pct=0.0,
                liquidity_score=0.5,
                expected_net_edge_pct=0.1,
                expected_slippage_pct=0.0,
                expected_fee_pct=0.0,
            )
