"""V11 — Multi-source intelligence schemas.

All schemas are frozen, extra='forbid', and reject execution /
order / API-secret fields by validator.  Raw symbol/venue names
appear only as hashed provenance refs.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, model_validator

_FORBIDDEN_FIELDS = frozenset(
    {
        "order_side",
        "order_qty",
        "order_price",
        "order_type",
        "execute_real",
        "submit_order",
        "approve_trade",
        "api_key",
        "api_secret",
        "secret",
        "withdrawal",
        "balance_change",
        "kill_switch_set",
        "kill_switch_clear",
        "direct_order",
        "orders_pending_payload",
    }
)


class SourceFamily(StrEnum):
    """Closed set of multi-source intelligence families."""

    TECHNICAL_INDICATOR = "technical_indicator"
    EXCHANGE_MICROSTRUCTURE = "exchange_microstructure"
    GELAL_METRICS = "gelal_metrics"
    MACRO = "macro"
    NEWS = "news"
    SOCIAL = "social"
    COMMODITY = "commodity"
    HISTORICAL = "historical"


def _check_no_forbidden_keys(keys: object) -> None:
    bad = _FORBIDDEN_FIELDS & set(keys)  # type: ignore[arg-type]
    if bad:
        raise ValueError(f"forbidden fields in normalized_features: {sorted(bad)}")


class MultiSourceObservation(BaseModel, frozen=True, extra="forbid"):
    """Normalized multi-source observation entering Sentinel core."""

    observation_id: str = Field(min_length=1)
    source_family: SourceFamily
    source_id: str = Field(min_length=1)
    observed_at_ms: int = Field(ge=0)
    exported_at_ms: int = Field(ge=0)
    confidence: float = Field(ge=0.0, le=1.0)
    freshness_ms: int = Field(ge=0)
    provenance_hash: str = Field(min_length=1)
    raw_ref: str = ""
    normalized_features: dict[str, float | int | bool | str] = Field(default_factory=dict)
    source_event_refs: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _no_forbidden_features(self) -> MultiSourceObservation:
        _check_no_forbidden_keys(self.normalized_features)
        return self


class TechnicalIndicatorSnapshot(BaseModel, frozen=True, extra="forbid"):
    """Normalized technical indicator snapshot (e.g. from TAAPI)."""

    snapshot_id: str = Field(min_length=1)
    provider: Literal["taapi", "local", "other"] = "taapi"
    symbol_hash: str = Field(min_length=1)
    venue_hash: str | None = None
    timeframe: str = Field(min_length=1)
    indicators: dict[str, float] = Field(default_factory=dict)
    trend_score: float = Field(ge=0.0, le=1.0, default=0.0)
    momentum_score: float = Field(ge=0.0, le=1.0, default=0.0)
    volatility_score: float = Field(ge=0.0, le=1.0, default=0.0)
    volume_score: float = Field(ge=0.0, le=1.0, default=0.0)
    reversal_score: float = Field(ge=0.0, le=1.0, default=0.0)
    exhaustion_score: float = Field(ge=0.0, le=1.0, default=0.0)
    pattern_score: float = Field(ge=0.0, le=1.0, default=0.0)
    confidence: float = Field(ge=0.0, le=1.0)
    observed_at_ms: int = Field(ge=0)
    provenance_hash: str = Field(min_length=1)

    @model_validator(mode="after")
    def _no_action_fields(self) -> TechnicalIndicatorSnapshot:
        for k in self.indicators:
            if k in _FORBIDDEN_FIELDS:
                raise ValueError(f"forbidden indicator name: {k}")
        return self


class MarketMicrostructureSnapshot(BaseModel, frozen=True, extra="forbid"):
    """Normalized microstructure observation."""

    snapshot_id: str = Field(min_length=1)
    symbol_hash: str = Field(min_length=1)
    venue_hash: str = Field(min_length=1)
    orderbook_age_ms: int = Field(ge=0)
    trade_tape_age_ms: int = Field(ge=0)
    bid_ask_spread_pct: float = Field(ge=0.0)
    bid_depth_score: float = Field(ge=0.0, le=1.0)
    ask_depth_score: float = Field(ge=0.0, le=1.0)
    imbalance_score: float = Field(ge=-1.0, le=1.0)
    ofi_score: float = Field(ge=-1.0, le=1.0)
    vpin_score: float = Field(ge=0.0, le=1.0)
    hawkes_toxicity_score: float = Field(ge=0.0, le=1.0)
    liquidity_score: float = Field(ge=0.0, le=1.0)
    latency_ms: int = Field(ge=0)
    confidence: float = Field(ge=0.0, le=1.0)
    observed_at_ms: int = Field(ge=0)
    provenance_hash: str = Field(min_length=1)


class MacroEventKind(StrEnum):
    CPI = "cpi"
    FOMC = "fomc"
    NFP = "nfp"
    RATE_DECISION = "rate_decision"
    DXY_SHOCK = "dxy_shock"
    OIL_SHOCK = "oil_shock"
    GOLD_SHOCK = "gold_shock"
    EQUITY_RISKOFF = "equity_riskoff"
    WAR_HEADLINE = "war_headline"
    REGULATORY = "regulatory"
    UNKNOWN = "unknown"


class MacroEventSnapshot(BaseModel, frozen=True, extra="forbid"):
    """Normalized macro event observation."""

    event_id: str = Field(min_length=1)
    event_type: MacroEventKind
    country_or_region: str = Field(min_length=1)
    observed_at_ms: int = Field(ge=0)
    severity_score: float = Field(ge=0.0, le=1.0)
    surprise_score: float = Field(ge=0.0, le=1.0)
    risk_off_score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    provenance_hash: str = Field(min_length=1)


class NewsFamily(StrEnum):
    WAR = "war"
    REGULATION = "regulation"
    EXCHANGE_OUTAGE = "exchange_outage"
    ETF = "etf"
    HACK = "hack"
    LIQUIDATION = "liquidation"
    MACRO = "macro"
    COMPANY = "company"
    UNKNOWN = "unknown"


class NewsEventSnapshot(BaseModel, frozen=True, extra="forbid"):
    """Normalized news event observation."""

    event_id: str = Field(min_length=1)
    news_family: NewsFamily
    severity_score: float = Field(ge=0.0, le=1.0)
    novelty_score: float = Field(ge=0.0, le=1.0)
    contradiction_score: float = Field(ge=0.0, le=1.0)
    source_reliability_score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    observed_at_ms: int = Field(ge=0)
    provenance_hash: str = Field(min_length=1)


class SocialPlatform(StrEnum):
    X_TWITTER = "x_twitter"
    TELEGRAM = "telegram"
    REDDIT = "reddit"
    OTHER = "other"


class SocialSignalSnapshot(BaseModel, frozen=True, extra="forbid"):
    """Normalized social platform signal."""

    signal_id: str = Field(min_length=1)
    platform: SocialPlatform
    crowd_panic_score: float = Field(ge=0.0, le=1.0)
    crowd_euphoria_score: float = Field(ge=0.0, le=1.0)
    bot_noise_score: float = Field(ge=0.0, le=1.0)
    influencer_concentration_score: float = Field(ge=0.0, le=1.0)
    contradiction_score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    observed_at_ms: int = Field(ge=0)
    provenance_hash: str = Field(min_length=1)


class CommodityMacroSnapshot(BaseModel, frozen=True, extra="forbid"):
    """Normalized commodity / macro asset snapshot."""

    snapshot_id: str = Field(min_length=1)
    dxy_score: float = Field(ge=0.0, le=1.0)
    oil_score: float = Field(ge=0.0, le=1.0)
    gold_score: float = Field(ge=0.0, le=1.0)
    rates_score: float = Field(ge=0.0, le=1.0)
    nasdaq_risk_score: float = Field(ge=0.0, le=1.0)
    vix_score: float = Field(ge=0.0, le=1.0)
    global_risk_off_score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    observed_at_ms: int = Field(ge=0)
    provenance_hash: str = Field(min_length=1)


class GelAlMetricsObservation(BaseModel, frozen=True, extra="forbid"):
    """Read-only Gel.Al metrics observation entering Sentinel."""

    observation_id: str = Field(min_length=1)
    metric_family: Literal[
        "depth_snapshots",
        "opportunity_history",
        "live_trade_attempts",
        "scout_signals",
        "latency_metrics",
    ]
    symbol_hash: str = Field(min_length=1)
    venue_hash: str = Field(min_length=1)
    sample_count: int = Field(ge=0)
    mean_value: float
    p50_value: float
    p95_value: float
    confidence: float = Field(ge=0.0, le=1.0)
    observed_at_ms: int = Field(ge=0)
    provenance_hash: str = Field(min_length=1)


__all__ = [
    "CommodityMacroSnapshot",
    "GelAlMetricsObservation",
    "MacroEventKind",
    "MacroEventSnapshot",
    "MarketMicrostructureSnapshot",
    "MultiSourceObservation",
    "NewsEventSnapshot",
    "NewsFamily",
    "SocialPlatform",
    "SocialSignalSnapshot",
    "SourceFamily",
    "TechnicalIndicatorSnapshot",
]
