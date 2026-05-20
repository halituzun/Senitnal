"""V2A — read-only market observation boundary tests.

Covers:
    Schema validation         (tests 1-12)
    Sanitization mapping      (tests 13-19)
    Audit payload builder     (tests 20-23)
    Module-source boundary    (tests 24-27)
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from pydantic import ValidationError
from sentinel.adapters.market_observation import (
    MarketObservationEnvelope,
    build_market_observation_audit_payload,
    sanitize_market_observation_to_event,
)
from sentinel.types.events import IngressEventType, ObservationEvent

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _valid_envelope_kwargs(**overrides: object) -> dict[str, object]:
    """Construct a canonical valid envelope payload.

    best_bid=100.0, best_ask=100.5, mid_price=100.25, so
    spread_pct = (0.5 / 100.25) * 100 (computed exactly to dodge
    float drift). Tests override individual fields to assert
    rejection paths.
    """
    best_bid = 100.0
    best_ask = 100.5
    mid_price = (best_bid + best_ask) / 2.0
    spread_pct = (best_ask - best_bid) / mid_price * 100.0
    base: dict[str, object] = {
        "event_id": "market-obs-001",
        "source_adapter_id": "market-observation-readonly-v2a",
        "source_system": "synthetic-fixture",
        "venue": "gel-al",
        "symbol": "BTCUSDT",
        "observed_at_ms": 1000,
        "best_bid": best_bid,
        "best_ask": best_ask,
        "mid_price": mid_price,
        "spread_pct": spread_pct,
        "orderbook_age_ms": 50,
        "latency_ms": 25,
        "bid_depth_10": 12.5,
        "ask_depth_10": 13.1,
        "bid_value_10": 1252.5,
        "ask_value_10": 1316.55,
        "volatility_score": 0.3,
        "imbalance_score": 0.4,
        "confidence": 0.8,
        "raw_ref": "ref-abc",
        "provenance_hash": "sha256:" + ("f" * 64),
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Schema tests (1-12)
# ---------------------------------------------------------------------------


class TestMarketObservationEnvelopeSchema:
    def test_01_valid_envelope_accepted(self) -> None:
        envelope = MarketObservationEnvelope(**_valid_envelope_kwargs())  # type: ignore[arg-type]
        assert envelope.event_id == "market-obs-001"
        assert envelope.symbol == "BTCUSDT"

    def test_02_best_ask_below_best_bid_rejected(self) -> None:
        with pytest.raises(ValidationError, match="best_ask must be >= best_bid"):
            MarketObservationEnvelope(
                **_valid_envelope_kwargs(  # type: ignore[arg-type]
                    best_bid=101.0, best_ask=100.0, mid_price=100.5, spread_pct=0.0
                )
            )

    def test_03_inconsistent_mid_price_rejected(self) -> None:
        with pytest.raises(ValidationError, match="mid_price inconsistent"):
            MarketObservationEnvelope(
                **_valid_envelope_kwargs(mid_price=200.0)  # type: ignore[arg-type]
            )

    def test_04_inconsistent_spread_pct_rejected(self) -> None:
        with pytest.raises(ValidationError, match="spread_pct inconsistent"):
            MarketObservationEnvelope(
                **_valid_envelope_kwargs(spread_pct=5.0)  # type: ignore[arg-type]
            )

    def test_05_negative_orderbook_age_rejected(self) -> None:
        with pytest.raises(ValidationError):
            MarketObservationEnvelope(
                **_valid_envelope_kwargs(orderbook_age_ms=-1)  # type: ignore[arg-type]
            )

    def test_06_confidence_out_of_range_rejected(self) -> None:
        with pytest.raises(ValidationError):
            MarketObservationEnvelope(
                **_valid_envelope_kwargs(confidence=1.5)  # type: ignore[arg-type]
            )
        with pytest.raises(ValidationError):
            MarketObservationEnvelope(
                **_valid_envelope_kwargs(confidence=-0.1)  # type: ignore[arg-type]
            )

    def test_07_volatility_score_out_of_range_rejected(self) -> None:
        with pytest.raises(ValidationError):
            MarketObservationEnvelope(
                **_valid_envelope_kwargs(volatility_score=1.5)  # type: ignore[arg-type]
            )

    def test_08_imbalance_score_out_of_range_rejected(self) -> None:
        with pytest.raises(ValidationError):
            MarketObservationEnvelope(
                **_valid_envelope_kwargs(imbalance_score=-0.1)  # type: ignore[arg-type]
            )

    @pytest.mark.parametrize(
        "forbidden_field",
        ["side", "order_side", "order_type", "trade_intent", "strategy_action"],
    )
    def test_09_extra_order_field_rejected(self, forbidden_field: str) -> None:
        kwargs = _valid_envelope_kwargs()
        kwargs[forbidden_field] = "buy"
        with pytest.raises(ValidationError):
            MarketObservationEnvelope(**kwargs)  # type: ignore[arg-type]

    @pytest.mark.parametrize("forbidden_field", ["api_key", "api_secret"])
    def test_10_extra_api_credential_field_rejected(self, forbidden_field: str) -> None:
        kwargs = _valid_envelope_kwargs()
        kwargs[forbidden_field] = "secret-value"
        with pytest.raises(ValidationError):
            MarketObservationEnvelope(**kwargs)  # type: ignore[arg-type]

    @pytest.mark.parametrize(
        "forbidden_field",
        ["balance", "position", "leverage", "take_profit", "stop_loss", "amount", "quantity"],
    )
    def test_11_extra_account_or_execution_field_rejected(self, forbidden_field: str) -> None:
        kwargs = _valid_envelope_kwargs()
        kwargs[forbidden_field] = 1.0
        with pytest.raises(ValidationError):
            MarketObservationEnvelope(**kwargs)  # type: ignore[arg-type]

    def test_12_envelope_is_frozen(self) -> None:
        envelope = MarketObservationEnvelope(**_valid_envelope_kwargs())  # type: ignore[arg-type]
        with pytest.raises(ValidationError):
            envelope.symbol = "ETHUSDT"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Sanitization tests (13-19)
# ---------------------------------------------------------------------------


class TestSanitization:
    def test_13_returns_observation_event(self) -> None:
        envelope = MarketObservationEnvelope(**_valid_envelope_kwargs())  # type: ignore[arg-type]
        event = sanitize_market_observation_to_event(envelope)
        assert isinstance(event, ObservationEvent)
        assert event.event_type is IngressEventType.OBSERVATION

    def test_14_observation_event_carries_no_domain_labels(self) -> None:
        envelope = MarketObservationEnvelope(**_valid_envelope_kwargs())  # type: ignore[arg-type]
        event = sanitize_market_observation_to_event(envelope)
        dumped = event.model_dump()
        forbidden = {
            "symbol",
            "venue",
            "source_system",
            "best_bid",
            "best_ask",
            "mid_price",
            "spread_pct",
            "bid_depth_10",
            "ask_depth_10",
            "bid_value_10",
            "ask_value_10",
            "raw_ref",
            "provenance_hash",
            "volatility_score",
            "imbalance_score",
        }
        leaked = forbidden & set(dumped.keys())
        assert leaked == set(), (
            f"Core-facing ObservationEvent must not contain observer-side "
            f"labels; leaked: {sorted(leaked)}"
        )

    def test_15_magnitude_bounded(self) -> None:
        # Force max-domain inputs; the clamp keeps magnitude <= 1.0
        kwargs = _valid_envelope_kwargs(
            volatility_score=1.0,
            imbalance_score=1.0,
        )
        envelope = MarketObservationEnvelope(**kwargs)  # type: ignore[arg-type]
        event = sanitize_market_observation_to_event(envelope)
        assert 0.0 <= event.magnitude_normalized <= 1.0

    def test_16_novelty_bounded(self) -> None:
        kwargs = _valid_envelope_kwargs(
            volatility_score=1.0,
            imbalance_score=1.0,
        )
        envelope = MarketObservationEnvelope(**kwargs)  # type: ignore[arg-type]
        event = sanitize_market_observation_to_event(envelope)
        assert 0.0 <= event.novelty_indicator <= 1.0
        # at the maximum corners the novelty saturates to 1.0
        assert event.novelty_indicator == pytest.approx(1.0)

    def test_17_staleness_sum(self) -> None:
        envelope = MarketObservationEnvelope(
            **_valid_envelope_kwargs(orderbook_age_ms=120, latency_ms=80)  # type: ignore[arg-type]
        )
        event = sanitize_market_observation_to_event(envelope)
        assert event.staleness_ms == 200

    def test_18_confidence_preserved(self) -> None:
        envelope = MarketObservationEnvelope(
            **_valid_envelope_kwargs(confidence=0.42)  # type: ignore[arg-type]
        )
        event = sanitize_market_observation_to_event(envelope)
        assert event.confidence == pytest.approx(0.42)

    def test_19_sanitization_deterministic(self) -> None:
        envelope = MarketObservationEnvelope(**_valid_envelope_kwargs())  # type: ignore[arg-type]
        first = sanitize_market_observation_to_event(envelope)
        second = sanitize_market_observation_to_event(envelope)
        assert first.model_dump() == second.model_dump()


# ---------------------------------------------------------------------------
# Audit payload tests (20-23)
# ---------------------------------------------------------------------------


class TestAuditPayload:
    def test_20_payload_includes_symbol_and_venue(self) -> None:
        envelope = MarketObservationEnvelope(**_valid_envelope_kwargs())  # type: ignore[arg-type]
        payload = build_market_observation_audit_payload(envelope)
        assert payload["symbol"] == "BTCUSDT"
        assert payload["venue"] == "gel-al"

    def test_21_payload_includes_raw_price_fields(self) -> None:
        envelope = MarketObservationEnvelope(**_valid_envelope_kwargs())  # type: ignore[arg-type]
        payload = build_market_observation_audit_payload(envelope)
        assert payload["best_bid"] == pytest.approx(100.0)
        assert payload["best_ask"] == pytest.approx(100.5)
        assert payload["mid_price"] == pytest.approx(100.25)

    def test_22_payload_excludes_api_credentials(self) -> None:
        envelope = MarketObservationEnvelope(**_valid_envelope_kwargs())  # type: ignore[arg-type]
        payload = build_market_observation_audit_payload(envelope)
        forbidden = {
            "api_key",
            "api_secret",
            "balance",
            "position",
            "leverage",
            "take_profit",
            "stop_loss",
            "side",
            "order_side",
            "order_type",
            "amount",
            "quantity",
            "trade_intent",
            "strategy_action",
        }
        leaked = forbidden & set(payload.keys())
        assert leaked == set(), (
            f"Audit payload must not contain execution/account fields; leaked: {sorted(leaked)}"
        )

    def test_23_payload_is_json_compatible(self) -> None:
        import json

        envelope = MarketObservationEnvelope(**_valid_envelope_kwargs())  # type: ignore[arg-type]
        payload = build_market_observation_audit_payload(envelope)
        encoded = json.dumps(payload)
        roundtrip = json.loads(encoded)
        assert roundtrip["symbol"] == "BTCUSDT"
        assert roundtrip["provenance_hash"].startswith("sha256:")


# ---------------------------------------------------------------------------
# Module-source boundary tests (24-27)
# ---------------------------------------------------------------------------


def _module_source() -> str:
    """Read the V2A module source for static boundary assertions."""
    path = (
        Path(__file__).resolve().parent.parent.parent
        / "sentinel"
        / "adapters"
        / "market_observation.py"
    )
    return path.read_text(encoding="utf-8")


class TestModuleSourceBoundary:
    def test_24_no_neural_seed_emission(self) -> None:
        """Module must not import or emit NeuralSeed; adapters are
        constitutionally forbidden from producing one (v0.1 invariant
        catalog: ADAPTER_NEURAL_SEED_EMISSION_DETECTED)."""
        src = _module_source()
        assert "NeuralSeed" not in src

    def test_25_no_network_imports(self) -> None:
        src = _module_source()
        banned_import_pattern = re.compile(
            r"^\s*(import|from)\s+(requests|httpx|aiohttp|urllib3|socket|asyncio\.subprocess)\b",
            re.MULTILINE,
        )
        matches = banned_import_pattern.findall(src)
        assert matches == [], f"network library imports detected: {matches}"

    def test_26_no_exchange_or_llm_imports(self) -> None:
        src = _module_source()
        banned_import_pattern = re.compile(
            r"^\s*(import|from)\s+("
            r"ccxt|web3|binance|btcturk|pybit|okx|gate_api|"
            r"kucoin|huobi|bitfinex|kraken|"
            r"openai|anthropic|langchain"
            r")\b",
            re.MULTILINE,
        )
        matches = banned_import_pattern.findall(src)
        assert matches == [], f"exchange/LLM imports detected: {matches}"

    def test_27_no_forbidden_output_literals(self) -> None:
        src = _module_source()
        for literal in (
            '"BUY"',
            '"SELL"',
            '"EXECUTE_REAL"',
            '"ORDER_SUBMIT"',
            "'BUY'",
            "'SELL'",
            "'EXECUTE_REAL'",
            "'ORDER_SUBMIT'",
        ):
            assert literal not in src, (
                f"forbidden execution-output literal {literal} present in module source"
            )
