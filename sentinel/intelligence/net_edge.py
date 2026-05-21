"""V11 — Net edge gate.

Computes net edge from gross edge minus all friction costs.  Rejects
any inconsistent breakdown (net > gross) and any non-positive net
edge for live candidacy.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class NetEdgeBreakdown(BaseModel, frozen=True, extra="forbid"):
    """Net edge breakdown for one candidate opportunity."""

    breakdown_id: str = Field(min_length=1)
    gross_edge_pct: float
    fee_pct: float = Field(ge=0.0)
    slippage_pct: float = Field(ge=0.0)
    spread_cost_pct: float = Field(ge=0.0)
    latency_decay_pct: float = Field(ge=0.0)
    partial_fill_risk_pct: float = Field(ge=0.0)
    hedge_risk_pct: float = Field(ge=0.0)
    net_edge_pct: float

    @model_validator(mode="after")
    def _net_le_gross(self) -> NetEdgeBreakdown:
        expected = (
            self.gross_edge_pct
            - self.fee_pct
            - self.slippage_pct
            - self.spread_cost_pct
            - self.latency_decay_pct
            - self.partial_fill_risk_pct
            - self.hedge_risk_pct
        )
        if self.net_edge_pct > self.gross_edge_pct + 1e-9:
            raise ValueError("net_edge_pct cannot exceed gross_edge_pct")
        if abs(self.net_edge_pct - expected) > 1e-6:
            raise ValueError("net_edge_pct inconsistent with cost components")
        return self


def compute_net_edge(
    *,
    breakdown_id: str,
    gross_edge_pct: float,
    fee_pct: float = 0.0,
    slippage_pct: float = 0.0,
    spread_cost_pct: float = 0.0,
    latency_decay_pct: float = 0.0,
    partial_fill_risk_pct: float = 0.0,
    hedge_risk_pct: float = 0.0,
) -> NetEdgeBreakdown:
    """Compute net edge from gross and component costs."""
    net = (
        gross_edge_pct
        - fee_pct
        - slippage_pct
        - spread_cost_pct
        - latency_decay_pct
        - partial_fill_risk_pct
        - hedge_risk_pct
    )
    return NetEdgeBreakdown(
        breakdown_id=breakdown_id,
        gross_edge_pct=gross_edge_pct,
        fee_pct=fee_pct,
        slippage_pct=slippage_pct,
        spread_cost_pct=spread_cost_pct,
        latency_decay_pct=latency_decay_pct,
        partial_fill_risk_pct=partial_fill_risk_pct,
        hedge_risk_pct=hedge_risk_pct,
        net_edge_pct=net,
    )


def is_net_edge_actionable(breakdown: NetEdgeBreakdown, *, threshold_pct: float = 0.0) -> bool:
    """Return True if net edge exceeds the threshold (default 0)."""
    return breakdown.net_edge_pct > threshold_pct


__all__ = [
    "NetEdgeBreakdown",
    "compute_net_edge",
    "is_net_edge_actionable",
]
