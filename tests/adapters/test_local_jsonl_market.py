"""Tests for LocalJsonlMarketAdapter (V2 read-only local file source)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from pydantic import ValidationError
from sentinel.adapters.local_jsonl_market import LocalJsonlMarketAdapter

_FIXTURE_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "market"


def _module_source() -> str:
    return (
        Path(__file__).resolve().parent.parent.parent
        / "sentinel"
        / "adapters"
        / "local_jsonl_market.py"
    ).read_text(encoding="utf-8")


class TestLocalJsonlMarketAdapter:
    def test_reads_valid_calm_fixture(self) -> None:
        a = LocalJsonlMarketAdapter(path=_FIXTURE_DIR / "calm_tight_spread.jsonl")
        envelopes = a.read_all()
        assert len(envelopes) == 1
        assert envelopes[0].symbol == "SYNTH/TRY"

    def test_preserves_order(self) -> None:
        a = LocalJsonlMarketAdapter(path=_FIXTURE_DIR / "wide_spread_valid.jsonl")
        envelopes = a.read_all()
        assert [e.event_id for e in envelopes] == ["wide-001", "wide-002"]

    def test_missing_file_raises_filenotfounderror(self) -> None:
        a = LocalJsonlMarketAdapter(path=Path("/nonexistent/fixture.jsonl"))
        with pytest.raises(FileNotFoundError):
            a.read_all()

    def test_malformed_json_line_rejected(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.jsonl"
        bad.write_text('{"event_id":"a", invalid json\n', encoding="utf-8")
        a = LocalJsonlMarketAdapter(path=bad)
        with pytest.raises(ValueError):
            a.read_all()

    def test_invalid_envelope_raises_validation_error(self) -> None:
        a = LocalJsonlMarketAdapter(path=_FIXTURE_DIR / "inconsistent_mid_price_invalid.jsonl")
        with pytest.raises(ValidationError):
            a.read_all()

    def test_forbidden_field_rejected(self) -> None:
        a = LocalJsonlMarketAdapter(path=_FIXTURE_DIR / "forbidden_order_fields_invalid.jsonl")
        with pytest.raises(ValidationError):
            a.read_all()

    def test_iter_observations_is_single_pass(self) -> None:
        a = LocalJsonlMarketAdapter(path=_FIXTURE_DIR / "wide_spread_valid.jsonl")
        it = a.iter_observations()
        first = next(it)
        second = next(it)
        with pytest.raises(StopIteration):
            next(it)
        assert first.event_id == "wide-001"
        assert second.event_id == "wide-002"

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
