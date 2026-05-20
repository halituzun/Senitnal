"""V8 — Micro-live bounds and fail-closed tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sentinel.canary.limits import (
    CanaryMicroLiveBounds,
    check_canary_bounds,
    reset_window_if_due,
)
from sentinel.canary.veto import VetoReason

from tests.canary._fixtures import make_bounds, make_candidate, make_window


class TestBoundsArtifact:
    def test_fail_closed_flags_must_be_true(self) -> None:
        with pytest.raises(ValidationError):
            CanaryMicroLiveBounds(
                bounds_id="bad",
                max_candidate_notional_ref="tier:micro",
                max_candidates_per_hour=10,
                max_vetoes_per_hour=10,
                max_unvetoed_candidates_per_hour=5,
                max_staleness_ms=1000,
                max_latency_ms=500,
                max_orderbook_age_ms=200,
                min_confidence=0.3,
                min_liquidity_score=0.1,
                max_risk_score=0.85,
                kill_switch_blocks=False,  # type: ignore[arg-type]
            )

    def test_valid_bounds(self) -> None:
        b = make_bounds()
        assert b.kill_switch_blocks is True
        assert b.fail_closed_on_error is True


class TestCheckBounds:
    def test_pass_returns_true_but_not_approval(self) -> None:
        ok, reasons = check_canary_bounds(
            candidate=make_candidate(),
            bounds=make_bounds(),
            state=make_window(),
            now_ms=1_000_001_000,
        )
        assert ok is True
        assert reasons == ()

    def test_expired_blocks(self) -> None:
        ok, reasons = check_canary_bounds(
            candidate=make_candidate(expires_at_ms=1_000_000_500),
            bounds=make_bounds(),
            state=make_window(),
            now_ms=1_000_001_000,
        )
        assert ok is False
        assert VetoReason.EXPIRED_CANDIDATE in reasons

    def test_stale_blocks(self) -> None:
        ok, reasons = check_canary_bounds(
            candidate=make_candidate(staleness_ms=10_000),
            bounds=make_bounds(),
            state=make_window(),
            now_ms=1_000_001_000,
        )
        assert ok is False
        assert VetoReason.STALE_DATA in reasons

    def test_high_risk_blocks(self) -> None:
        ok, reasons = check_canary_bounds(
            candidate=make_candidate(risk_score=0.95),
            bounds=make_bounds(),
            state=make_window(),
            now_ms=1_000_001_000,
        )
        assert ok is False
        assert VetoReason.HIGH_RISK in reasons

    def test_low_confidence_blocks(self) -> None:
        ok, reasons = check_canary_bounds(
            candidate=make_candidate(confidence=0.1),
            bounds=make_bounds(),
            state=make_window(),
            now_ms=1_000_001_000,
        )
        assert ok is False
        assert VetoReason.LOW_CONFIDENCE in reasons

    def test_low_liquidity_blocks(self) -> None:
        ok, reasons = check_canary_bounds(
            candidate=make_candidate(liquidity_score=0.05),
            bounds=make_bounds(),
            state=make_window(),
            now_ms=1_000_001_000,
        )
        assert ok is False
        assert VetoReason.LIQUIDITY_INSUFFICIENT in reasons

    def test_window_cap_blocks(self) -> None:
        state = make_window()
        state.candidates_seen_this_hour = 100
        ok, reasons = check_canary_bounds(
            candidate=make_candidate(),
            bounds=make_bounds(),
            state=state,
            now_ms=1_000_001_000,
        )
        assert ok is False
        assert VetoReason.CANARY_LIMIT_EXCEEDED in reasons


class TestWindowReset:
    def test_reset_after_hour(self) -> None:
        state = make_window()
        state.candidates_seen_this_hour = 50
        reset_window_if_due(state, now_ms=state.last_reset_at_ms + 3_600_001)
        assert state.candidates_seen_this_hour == 0
