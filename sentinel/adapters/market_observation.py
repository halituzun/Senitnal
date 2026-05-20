"""Read-only market observation adapter (V2 — synthetic / local only).

Per docs/build/0002-read-only-market-observation-plan.md +
docs/build/0003-v2-read-only-market-adapters-build-plan.md +
docs/integrations/gel-al-borsa-readonly-bridge.md +
docs/reviews/0013-v2a-read-only-market-observation-implementation.md +
docs/reviews/0014-v2-read-only-market-adapters-review.md.

This module provides:

    MarketObservationEnvelope            — observer-side schema, frozen
    SanitizedMarketProvenance            — observer-side provenance
                                            wrapper (typed)
    sanitize_market_observation_to_event — pure conversion to v0.1
                                            ObservationEvent
    build_market_observation_audit_payload
                                         — pure observer-side audit
                                            payload builder

Boundary discipline (constitutional, v0.1 + V2):
    - No network I/O. No exchange SDK. No LLM SDK.
    - No order side, no quantity, no API key, no balance, no position,
      no execution verb.
    - Symbol / venue / source_system / raw price fields stay
      observer-side and NEVER cross into the core-facing
      ObservationEvent (v0.1 ObservationEvent already enforces
      extra='forbid' at the type boundary; the sanitizer here is
      defense-in-depth + intentional documentation of the mapping).
    - This module owns NO ledger I/O. Callers wishing to audit a
      market observation must call route_observer_event (the
      sanctioned persistence path) via the helper in
      sentinel/adapters/market_audit.py.
"""

from __future__ import annotations

from typing import Any, Final

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sentinel.types.events import IngressEventType, ObservationEvent

# Static conservative trust band for synthetic-source observations.
# v0.1 source_reliability_band is 0..5; 3 is mid-stream and gives no
# unjustified amplification or suppression on the compiler side.
_DEFAULT_SOURCE_RELIABILITY_BAND: Final[int] = 3

# Cross-field validation tolerances. mid_price/spread_pct are
# derivable from best_bid/best_ask; we accept small floating-point
# drift but reject anything that meaningfully contradicts the
# bid/ask quote.
_MID_PRICE_ABS_TOL: Final[float] = 1e-9
_MID_PRICE_REL_TOL: Final[float] = 1e-9
_SPREAD_PCT_ABS_TOL: Final[float] = 1e-6


class MarketObservationEnvelope(BaseModel):
    """Observer-side envelope for a single market snapshot.

    Carries domain labels (symbol, venue, source_system) and raw
    quote / depth fields. NONE of these may propagate into the
    core-facing ObservationEvent — see
    sanitize_market_observation_to_event for the mapping.

    All fields are validated at construction time. extra='forbid'
    rejects any of the explicitly banned execution/account/order
    fields (side, order_side, amount, quantity, api_key, api_secret,
    balance, position, leverage, take_profit, stop_loss,
    trade_intent, strategy_action, ...) — the v0.1 + V2A
    constitutional surface refuses these by construction.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    # Identity + provenance
    event_id: str = Field(min_length=1)
    source_adapter_id: str = Field(min_length=1)
    source_system: str = Field(min_length=1)
    venue: str = Field(min_length=1)
    symbol: str = Field(min_length=1)
    observed_at_ms: int = Field(ge=0)

    # Quote
    best_bid: float = Field(gt=0.0, allow_inf_nan=False)
    best_ask: float = Field(gt=0.0, allow_inf_nan=False)
    mid_price: float = Field(gt=0.0, allow_inf_nan=False)
    spread_pct: float = Field(ge=0.0, allow_inf_nan=False)

    # Freshness
    orderbook_age_ms: int = Field(ge=0)
    latency_ms: int = Field(ge=0)

    # Depth (top-N aggregated; raw book not propagated)
    bid_depth_10: float = Field(ge=0.0, allow_inf_nan=False)
    ask_depth_10: float = Field(ge=0.0, allow_inf_nan=False)
    bid_value_10: float = Field(ge=0.0, allow_inf_nan=False)
    ask_value_10: float = Field(ge=0.0, allow_inf_nan=False)

    # Scores (normalized; what the sanitizer maps into the core)
    volatility_score: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    imbalance_score: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    confidence: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)

    # Provenance pointers
    raw_ref: str | None = None
    provenance_hash: str = Field(min_length=1)

    @model_validator(mode="after")
    def _check_consistency(self) -> MarketObservationEnvelope:
        if self.best_ask < self.best_bid:
            raise ValueError(
                f"best_ask must be >= best_bid (best_bid={self.best_bid}, best_ask={self.best_ask})"
            )
        expected_mid = (self.best_bid + self.best_ask) / 2.0
        if abs(self.mid_price - expected_mid) > max(
            _MID_PRICE_ABS_TOL, _MID_PRICE_REL_TOL * abs(expected_mid)
        ):
            raise ValueError(
                "mid_price inconsistent with (best_bid + best_ask) / 2 "
                f"(mid_price={self.mid_price}, expected≈{expected_mid})"
            )
        expected_spread = (self.best_ask - self.best_bid) / self.mid_price * 100.0
        if abs(self.spread_pct - expected_spread) > _SPREAD_PCT_ABS_TOL:
            raise ValueError(
                "spread_pct inconsistent with ((best_ask - best_bid) / mid_price * 100) "
                f"(spread_pct={self.spread_pct}, expected≈{expected_spread})"
            )
        return self


class SanitizedMarketProvenance(BaseModel):
    """Observer-side provenance wrapper.

    Bundles the envelope's identity + raw-domain fields that should
    accompany a market observation's M1 audit entry. NEVER embedded
    in an ObservationEvent; only used in observer-side contexts
    (ObserverEvent.payload, replay diagnostics).
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    source_adapter_id: str = Field(min_length=1)
    source_system: str = Field(min_length=1)
    venue: str = Field(min_length=1)
    symbol: str = Field(min_length=1)
    observed_at_ms: int = Field(ge=0)
    raw_ref: str | None = None
    provenance_hash: str = Field(min_length=1)


def sanitize_market_observation_to_event(
    envelope: MarketObservationEnvelope,
    *,
    ttl_ms: int = 1000,
    source_reliability_band: int = _DEFAULT_SOURCE_RELIABILITY_BAND,
) -> ObservationEvent:
    """Map a MarketObservationEnvelope to a core-facing ObservationEvent.

    The core never sees symbol, venue, source_system, best_bid,
    best_ask, mid_price, depth, or raw_ref. Only the normalized
    quantities (magnitude_normalized, novelty_indicator,
    staleness_ms, confidence, source_adapter_id) cross the
    boundary. This is a pure function — no I/O, no logging, no
    side effects.

    Mapping (deterministic):
        magnitude_normalized = clamp(
            0.4 * min(spread_pct / 10.0, 1.0)
          + 0.4 * volatility_score
          + 0.2 * imbalance_score,
            0.0, 1.0)
        novelty_indicator = clamp(
            0.5 * volatility_score + 0.5 * imbalance_score,
            0.0, 1.0)
        staleness_ms = orderbook_age_ms + latency_ms
        confidence   = envelope.confidence (pass-through)
        source_reliability_band = caller-supplied
                                  (default _DEFAULT_SOURCE_RELIABILITY_BAND;
                                  must remain in v0.1 range [0, 5])
    """
    magnitude = (
        0.4 * min(envelope.spread_pct / 10.0, 1.0)
        + 0.4 * envelope.volatility_score
        + 0.2 * envelope.imbalance_score
    )
    novelty = 0.5 * envelope.volatility_score + 0.5 * envelope.imbalance_score
    magnitude_clamped = max(0.0, min(1.0, magnitude))
    novelty_clamped = max(0.0, min(1.0, novelty))
    return ObservationEvent(
        event_id=envelope.event_id,
        event_type=IngressEventType.OBSERVATION,
        occurred_at_ms=envelope.observed_at_ms,
        ttl_ms=ttl_ms,
        confidence=envelope.confidence,
        source_adapter_id=envelope.source_adapter_id,
        source_reliability_band=source_reliability_band,
        magnitude_normalized=magnitude_clamped,
        novelty_indicator=novelty_clamped,
        staleness_ms=envelope.orderbook_age_ms + envelope.latency_ms,
    )


def build_market_observation_audit_payload(
    envelope: MarketObservationEnvelope,
) -> dict[str, Any]:
    """Build an observer-side audit payload for the envelope.

    Returned dict is suitable for an ObserverEvent.payload field
    (per OBSERVER_LEDGER_SCHEMA.md the observer ledger payload
    INTENTIONALLY permits domain labels — see
    sentinel/types/observer.py module docstring). Caller is
    responsible for routing through route_observer_event with the
    correct ObserverEvent envelope and catalog event_type.

    The payload contains ONLY observer-side data. No execution
    verbs, no order side, no API credentials.
    """
    return {
        "source_adapter_id": envelope.source_adapter_id,
        "source_system": envelope.source_system,
        "venue": envelope.venue,
        "symbol": envelope.symbol,
        "observed_at_ms": envelope.observed_at_ms,
        "best_bid": envelope.best_bid,
        "best_ask": envelope.best_ask,
        "mid_price": envelope.mid_price,
        "spread_pct": envelope.spread_pct,
        "orderbook_age_ms": envelope.orderbook_age_ms,
        "latency_ms": envelope.latency_ms,
        "bid_depth_10": envelope.bid_depth_10,
        "ask_depth_10": envelope.ask_depth_10,
        "bid_value_10": envelope.bid_value_10,
        "ask_value_10": envelope.ask_value_10,
        "volatility_score": envelope.volatility_score,
        "imbalance_score": envelope.imbalance_score,
        "confidence": envelope.confidence,
        "raw_ref": envelope.raw_ref,
        "provenance_hash": envelope.provenance_hash,
    }
