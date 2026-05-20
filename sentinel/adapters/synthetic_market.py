"""SyntheticMarketAdapter — observe-only synthetic envelope emitter.

Counterpart of EchoAdapter but for market-shaped observations. Used
for unit tests, replay harness fixtures, and dry-run integration.

Constitutional discipline (v0.1 + V2):
    - Capability surface: (OBSERVE,) only. Manifest construction
      lives in sentinel/adapters/market_manifest.py and refuses
      EXECUTE / INTENT_RELAY / MEMORY_WRITER / RECALL_PROVIDER.
    - emit_market_observation produces ONLY MarketObservationEnvelope.
      The class deliberately has NO emit_neural_seed_directly method —
      the constitutional red line ADAPTER_NEURAL_SEED_EMISSION_DETECTED
      applies; no path here can produce a NeuralSeed.
    - No network. No exchange SDK. No LLM SDK. No execution
      verbs. The module-source boundary tests assert this.
"""

from __future__ import annotations

from dataclasses import dataclass

from sentinel.adapters.market_manifest import build_synthetic_market_manifest
from sentinel.adapters.market_observation import MarketObservationEnvelope
from sentinel.types.adapters import AdapterManifest  # noqa: TC001 (dataclass field at runtime)


def _hash_for(counter: int) -> str:
    return "sha256:synthetic-" + format(counter, "016x") + ("0" * 48)


@dataclass
class SyntheticMarketAdapter:
    """Synthetic outer-limb adapter for market observations."""

    manifest: AdapterManifest
    _counter: int = 0

    @classmethod
    def default(cls) -> SyntheticMarketAdapter:
        return cls(manifest=build_synthetic_market_manifest())

    def emit_market_observation(
        self,
        *,
        symbol: str = "SYNTH/TRY",
        venue: str = "synthetic",
        source_system: str = "synthetic-fixture",
        best_bid: float = 100.0,
        best_ask: float = 100.5,
        volatility_score: float = 0.3,
        imbalance_score: float = 0.4,
        confidence: float = 0.7,
        orderbook_age_ms: int = 50,
        latency_ms: int = 25,
        bid_depth_10: float = 12.5,
        ask_depth_10: float = 13.1,
        bid_value_10: float = 1252.5,
        ask_value_10: float = 1316.55,
    ) -> MarketObservationEnvelope:
        """Emit one synthetic MarketObservationEnvelope.

        mid_price and spread_pct are computed from (best_bid, best_ask)
        so the envelope's cross-field consistency validator passes by
        construction. Caller may inject inconsistent values only by
        invoking MarketObservationEnvelope directly; this method
        refuses to produce a broken envelope.
        """
        self._counter += 1
        mid_price = (best_bid + best_ask) / 2.0
        spread_pct = (best_ask - best_bid) / mid_price * 100.0
        return MarketObservationEnvelope(
            event_id=f"synthetic-market-{self._counter:08d}",
            source_adapter_id=self.manifest.adapter_id,
            source_system=source_system,
            venue=venue,
            symbol=symbol,
            observed_at_ms=self._counter,
            best_bid=best_bid,
            best_ask=best_ask,
            mid_price=mid_price,
            spread_pct=spread_pct,
            orderbook_age_ms=orderbook_age_ms,
            latency_ms=latency_ms,
            bid_depth_10=bid_depth_10,
            ask_depth_10=ask_depth_10,
            bid_value_10=bid_value_10,
            ask_value_10=ask_value_10,
            volatility_score=volatility_score,
            imbalance_score=imbalance_score,
            confidence=confidence,
            raw_ref=None,
            provenance_hash=_hash_for(self._counter),
        )
