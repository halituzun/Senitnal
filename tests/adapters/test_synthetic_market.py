"""Tests for SyntheticMarketAdapter (V2 read-only synthetic source)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from pydantic import ValidationError
from sentinel.adapters.market_observation import (
    MarketObservationEnvelope,
    sanitize_market_observation_to_event,
)
from sentinel.adapters.synthetic_market import SyntheticMarketAdapter
from sentinel.types.adapters import AdapterCapability


def _module_source() -> str:
    return (
        Path(__file__).resolve().parent.parent.parent
        / "sentinel"
        / "adapters"
        / "synthetic_market.py"
    ).read_text(encoding="utf-8")


class TestSyntheticMarketAdapter:
    def test_default_manifest_observe_only(self) -> None:
        a = SyntheticMarketAdapter.default()
        assert a.manifest.capabilities == (AdapterCapability.OBSERVE,)

    def test_emit_returns_envelope(self) -> None:
        a = SyntheticMarketAdapter.default()
        env = a.emit_market_observation()
        assert isinstance(env, MarketObservationEnvelope)
        assert env.source_adapter_id == a.manifest.adapter_id
        assert env.symbol == "SYNTH/TRY"

    def test_counter_advances(self) -> None:
        a = SyntheticMarketAdapter.default()
        e1 = a.emit_market_observation()
        e2 = a.emit_market_observation()
        assert e1.event_id != e2.event_id
        assert e2.observed_at_ms > e1.observed_at_ms

    def test_invalid_bid_ask_rejected(self) -> None:
        a = SyntheticMarketAdapter.default()
        with pytest.raises(ValidationError):
            a.emit_market_observation(best_bid=101.0, best_ask=100.0)

    def test_sanitizes_to_valid_observation_event(self) -> None:
        a = SyntheticMarketAdapter.default()
        env = a.emit_market_observation(volatility_score=0.9, imbalance_score=0.9)
        ev = sanitize_market_observation_to_event(env)
        assert 0.0 <= ev.magnitude_normalized <= 1.0
        assert 0.0 <= ev.novelty_indicator <= 1.0

    def test_no_emit_neural_seed_method(self) -> None:
        a = SyntheticMarketAdapter.default()
        assert not hasattr(a, "emit_neural_seed_directly")

    def test_module_has_no_network_imports(self) -> None:
        src = _module_source()
        bad = re.compile(
            r"^\s*(import|from)\s+(requests|httpx|aiohttp|urllib3|socket|asyncio\.subprocess)\b",
            re.MULTILINE,
        )
        assert bad.findall(src) == []

    def test_module_has_no_exchange_or_llm_imports(self) -> None:
        src = _module_source()
        bad = re.compile(
            r"^\s*(import|from)\s+("
            r"ccxt|web3|binance|btcturk|pybit|okx|gate_api|"
            r"kucoin|huobi|bitfinex|kraken|openai|anthropic|langchain"
            r")\b",
            re.MULTILINE,
        )
        assert bad.findall(src) == []

    def test_module_has_no_forbidden_output_literals(self) -> None:
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
            assert literal not in src
