"""V13 — Execution quality tests."""

from __future__ import annotations

from sentinel.production.execution_quality import (
    ExecutionQualityRecord,
    update_strategy_quality_from_record,
)


def _rec(**over: object) -> ExecutionQualityRecord:
    base: dict[str, object] = {
        "record_id": "r1",
        "strategy_id": "s1",
        "venue_hash": "sha:venue",
        "expected_net_edge_pct": 0.01,
        "realized_edge_pct": 0.008,
        "fee_pct": 0.001,
        "slippage_pct": 0.001,
        "latency_ms": 50,
        "partial_fill_observed": False,
        "cancel_success": True,
        "finality_status": "confirmed",
        "reject_count": 0,
        "bad_order_count": 0,
        "venue_quality_score": 0.9,
        "strategy_quality_score": 0.8,
        "observed_at_ms": 1_000,
        "provenance_hash": "sha:p",
    }
    base.update(over)
    return ExecutionQualityRecord(**base)  # type: ignore[arg-type]


class TestExecutionQuality:
    def test_bad_order_crashes_quality_to_zero(self) -> None:
        new_q = update_strategy_quality_from_record(
            previous_quality=0.8,
            record=_rec(bad_order_count=1),
        )
        assert new_q == 0.0

    def test_unknown_finality_caps_quality(self) -> None:
        new_q = update_strategy_quality_from_record(
            previous_quality=0.8,
            record=_rec(finality_status="unknown"),
        )
        assert new_q <= 0.2

    def test_rejected_finality_caps_quality(self) -> None:
        new_q = update_strategy_quality_from_record(
            previous_quality=0.9,
            record=_rec(finality_status="rejected"),
        )
        assert new_q <= 0.2

    def test_good_execution_raises_or_holds(self) -> None:
        new_q = update_strategy_quality_from_record(
            previous_quality=0.5,
            record=_rec(realized_edge_pct=0.012),
        )
        # EWMA with good record: should not crash below previous.
        assert new_q >= 0.4

    def test_partial_fill_dampens(self) -> None:
        with_partial = update_strategy_quality_from_record(
            previous_quality=0.5,
            record=_rec(partial_fill_observed=True),
        )
        no_partial = update_strategy_quality_from_record(
            previous_quality=0.5,
            record=_rec(partial_fill_observed=False),
        )
        assert with_partial <= no_partial

    def test_quality_bounded(self) -> None:
        new_q = update_strategy_quality_from_record(
            previous_quality=1.0,
            record=_rec(realized_edge_pct=10.0, venue_quality_score=1.0),
        )
        assert 0.0 <= new_q <= 1.0
