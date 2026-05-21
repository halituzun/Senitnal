"""V12 — Historical event taxonomy.

Closed-set enums for historical event families, reaction windows,
and the market reaction measurement schema.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class HistoricalEventFamily(StrEnum):
    """Closed set of historical event families (V12)."""

    MACRO_CPI = "macro_cpi"
    MACRO_FOMC = "macro_fomc"
    MACRO_NFP = "macro_nfp"
    RATE_DECISION = "rate_decision"
    DXY_SHOCK = "dxy_shock"
    OIL_SHOCK = "oil_shock"
    GOLD_SHOCK = "gold_shock"
    EQUITY_RISKOFF = "equity_riskoff"
    WAR_HEADLINE = "war_headline"
    REGULATORY_NEWS = "regulatory_news"
    EXCHANGE_OUTAGE = "exchange_outage"
    ETF_NEWS = "etf_news"
    HACK_EXPLOIT = "hack_exploit"
    WHALE_TRANSFER = "whale_transfer"
    LIQUIDATION_CASCADE = "liquidation_cascade"
    SOCIAL_PANIC = "social_panic"
    SOCIAL_EUPHORIA = "social_euphoria"
    FUNDING_DISLOCATION = "funding_dislocation"
    STABLECOIN_DEPEG = "stablecoin_depeg"
    UNKNOWN = "unknown"


class ReactionWindow(StrEnum):
    """Closed set of reaction-window durations."""

    W_1M = "1m"
    W_5M = "5m"
    W_15M = "15m"
    W_1H = "1h"
    W_4H = "4h"
    W_1D = "1d"
    W_3D = "3d"


class MarketReactionMeasurement(BaseModel, frozen=True, extra="forbid"):
    """One measured market reaction to a historical event."""

    measurement_id: str = Field(min_length=1)
    event_family: HistoricalEventFamily
    window: ReactionWindow
    btc_return: float
    eth_return: float
    alt_index_return: float
    volatility_jump: float = Field(ge=0.0)
    spread_change: float
    orderbook_imbalance_change: float
    liquidation_change: float
    funding_change: float
    dxy_change: float
    gold_change: float
    oil_change: float
    nasdaq_change: float
    btcturk_lag_ms: int = Field(ge=0, default=0)
    binance_lead_score: float = Field(ge=0.0, le=1.0, default=0.5)
    confidence: float = Field(ge=0.0, le=1.0)
    observed_at_ms: int = Field(ge=0)
    provenance_hash: str = Field(min_length=1)


__all__ = [
    "HistoricalEventFamily",
    "MarketReactionMeasurement",
    "ReactionWindow",
]
