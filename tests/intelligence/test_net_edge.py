"""V11 — NetEdgeGate tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sentinel.intelligence.net_edge import (
    NetEdgeBreakdown,
    compute_net_edge,
    is_net_edge_actionable,
)


class TestNetEdge:
    def test_compute_subtracts_costs(self) -> None:
        b = compute_net_edge(
            breakdown_id="b1",
            gross_edge_pct=0.01,
            fee_pct=0.001,
            slippage_pct=0.001,
            spread_cost_pct=0.0005,
            latency_decay_pct=0.0002,
            partial_fill_risk_pct=0.0001,
            hedge_risk_pct=0.0,
        )
        assert b.net_edge_pct == pytest.approx(0.01 - 0.0028)

    def test_negative_net_edge_not_actionable(self) -> None:
        b = compute_net_edge(
            breakdown_id="b2",
            gross_edge_pct=0.001,
            fee_pct=0.005,
        )
        assert is_net_edge_actionable(b) is False

    def test_positive_net_edge_actionable(self) -> None:
        b = compute_net_edge(breakdown_id="b3", gross_edge_pct=0.01, fee_pct=0.001)
        assert is_net_edge_actionable(b) is True

    def test_threshold(self) -> None:
        b = compute_net_edge(breakdown_id="b4", gross_edge_pct=0.001)
        assert is_net_edge_actionable(b, threshold_pct=0.002) is False

    def test_inconsistent_breakdown_rejected(self) -> None:
        with pytest.raises(ValidationError):
            NetEdgeBreakdown(
                breakdown_id="bad",
                gross_edge_pct=0.01,
                fee_pct=0.001,
                slippage_pct=0.0,
                spread_cost_pct=0.0,
                latency_decay_pct=0.0,
                partial_fill_risk_pct=0.0,
                hedge_risk_pct=0.0,
                net_edge_pct=0.02,  # inconsistent (greater than gross)
            )

    def test_net_cannot_exceed_gross(self) -> None:
        with pytest.raises(ValidationError):
            NetEdgeBreakdown(
                breakdown_id="bad2",
                gross_edge_pct=0.001,
                fee_pct=0.0,
                slippage_pct=0.0,
                spread_cost_pct=0.0,
                latency_decay_pct=0.0,
                partial_fill_risk_pct=0.0,
                hedge_risk_pct=0.0,
                net_edge_pct=0.005,
            )
