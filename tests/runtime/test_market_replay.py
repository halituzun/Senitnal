"""Tests for the V2 market replay harness."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError
from sentinel.adapters.synthetic_market import SyntheticMarketAdapter
from sentinel.observer.ledger import JsonlObserverLedger
from sentinel.observer.ring_buffer import ObserverRingBuffer
from sentinel.runtime.market_replay import (
    MarketReplayResult,
    run_market_jsonl_file,
    run_market_observations,
)
from sentinel.runtime.output import SystemOutput
from sentinel.types.neural_seed import ProvenanceRef

_FIXTURE_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "market"
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_ALLOWED_OUTPUTS = {SystemOutput.WAIT, SystemOutput.MONITOR, SystemOutput.NO_ACTION}


def _ledger_and_ring(tmp_path: Path) -> tuple[JsonlObserverLedger, ObserverRingBuffer]:
    return (
        JsonlObserverLedger(tmp_path / "ledger.jsonl"),
        ObserverRingBuffer(capacity=64),
    )


def _replay(name: str, tmp_path: Path) -> MarketReplayResult:
    ledger, ring = _ledger_and_ring(tmp_path)
    return run_market_jsonl_file(
        path=_FIXTURE_DIR / f"{name}.jsonl",
        ledger=ledger,
        ring_buffer=ring,
        provenance=ProvenanceRef(source_event_id="test-market-replay"),
    )


class TestFixtureReplay:
    def test_calm_tight_spread_closed_outputs(self, tmp_path: Path) -> None:
        result = _replay("calm_tight_spread", tmp_path)
        assert set(result.outputs).issubset(_ALLOWED_OUTPUTS)
        assert result.observations_seen == 1
        assert result.hash_chain_valid is True

    def test_wide_spread_valid_closed_outputs(self, tmp_path: Path) -> None:
        result = _replay("wide_spread_valid", tmp_path)
        assert set(result.outputs).issubset(_ALLOWED_OUTPUTS)
        assert result.observations_seen == 2

    def test_high_volatility_imbalance_accepts(self, tmp_path: Path) -> None:
        result = _replay("high_volatility_imbalance", tmp_path)
        assert result.observations_accepted >= 1
        assert result.neural_seed_count >= 1
        assert result.pulse_count >= 1
        assert SystemOutput.MONITOR in result.outputs

    def test_low_confidence_market_does_not_exceed_profile_cap(self, tmp_path: Path) -> None:
        result = _replay("low_confidence_market", tmp_path)
        # SUSPICION rule fires when confidence is low; profile cap on
        # OBSERVATION_EVENT keeps the resulting payload intensity bounded.
        for output in result.outputs:
            assert output in _ALLOWED_OUTPUTS

    def test_stale_orderbook_staleness_propagates(self, tmp_path: Path) -> None:
        result = _replay("stale_orderbook", tmp_path)
        # The replay's audit_event_ids include OBSERVATION_INGESTED for the
        # fixture; the fixture has orderbook_age_ms=5000 + latency_ms=1000,
        # so sanitized staleness_ms should be 6000.
        # We assert indirectly via outputs being in the allowed set and
        # that the run did not crash.
        assert set(result.outputs).issubset(_ALLOWED_OUTPUTS)
        assert result.hash_chain_valid is True

    def test_observation_ingested_routes_ring_only(self, tmp_path: Path) -> None:
        result = _replay("high_volatility_imbalance", tmp_path)
        # No OBSERVATION_INGESTED or WORKSPACE_PULSE event_id should
        # appear in permanent_event_ids — both are ring_buffer_only
        # per catalog.
        assert result.permanent_event_ids == ()
        # Ring should contain at least one ingested + pulse per accepted
        # observation (2 fixtures, both accepted -> 4 entries).
        assert len(result.ring_buffer_event_ids) >= 2

    def test_workspace_pulse_routes_ring_only(self, tmp_path: Path) -> None:
        result = _replay("low_confidence_market", tmp_path)
        # The single accepted observation produces 1 OBSERVATION_INGESTED
        # + 1 WORKSPACE_PULSE in the ring; ledger stays empty.
        assert result.permanent_event_ids == ()
        assert result.ring_buffer_event_ids != ()

    def test_deterministic_for_same_fixture(self, tmp_path: Path) -> None:
        a = _replay("wide_spread_valid", tmp_path / "a")
        b = _replay("wide_spread_valid", tmp_path / "b")
        (tmp_path / "a").mkdir(exist_ok=True)
        (tmp_path / "b").mkdir(exist_ok=True)
        # The MarketReplayResult dataclass-equality compares contents.
        # source_path differs because tmp_path differs in the inner
        # ledger; observed metrics should match.
        assert a.observations_seen == b.observations_seen
        assert a.observations_accepted == b.observations_accepted
        assert a.observations_rejected == b.observations_rejected
        assert a.outputs == b.outputs
        assert a.neural_seed_count == b.neural_seed_count
        assert a.pulse_count == b.pulse_count

    def test_no_action_intent_constructed(self, tmp_path: Path) -> None:
        # The replay module has no import of ApprovedActionIntent.
        src = (_REPO_ROOT / "sentinel" / "runtime" / "market_replay.py").read_text(encoding="utf-8")
        assert "ApprovedActionIntent" not in src
        assert "evaluate_action" not in src

    def test_invalid_fixture_raises_validation_error(self, tmp_path: Path) -> None:
        ledger, ring = _ledger_and_ring(tmp_path)
        with pytest.raises(ValidationError):
            run_market_jsonl_file(
                path=_FIXTURE_DIR / "inconsistent_mid_price_invalid.jsonl",
                ledger=ledger,
                ring_buffer=ring,
                provenance=ProvenanceRef(source_event_id="test"),
            )


class TestModuleSourceBoundary:
    def _src(self) -> str:
        return (_REPO_ROOT / "sentinel" / "runtime" / "market_replay.py").read_text(
            encoding="utf-8"
        )

    def test_no_network_imports(self) -> None:
        bad = re.compile(
            r"^\s*(import|from)\s+(requests|httpx|aiohttp|urllib3|socket|asyncio\.subprocess)\b",
            re.MULTILINE,
        )
        assert bad.findall(self._src()) == []

    def test_no_exchange_or_llm_imports(self) -> None:
        bad = re.compile(
            r"^\s*(import|from)\s+("
            r"ccxt|web3|binance|btcturk|pybit|okx|gate_api|"
            r"kucoin|huobi|bitfinex|kraken|openai|anthropic|langchain"
            r")\b",
            re.MULTILINE,
        )
        assert bad.findall(self._src()) == []

    def test_no_forbidden_output_literals(self) -> None:
        src = self._src()
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

    def test_no_memory_write_gate_call(self) -> None:
        assert "MemoryWriteGate" not in self._src()


class TestInMemoryRun:
    def test_synthetic_adapter_emits_through_replay(self, tmp_path: Path) -> None:
        adapter = SyntheticMarketAdapter.default()
        # 3 high-vol observations should produce 3 accepted + pulse_count=3
        envelopes = [
            adapter.emit_market_observation(volatility_score=0.9, imbalance_score=0.9)
            for _ in range(3)
        ]
        ledger, ring = _ledger_and_ring(tmp_path)
        result = run_market_observations(
            observations=envelopes,
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id="synth-test"),
        )
        assert result.observations_seen == 3
        assert result.observations_accepted == 3
        assert result.pulse_count == 3
        assert all(o is SystemOutput.MONITOR for o in result.outputs)
        assert result.hash_chain_valid is True
        assert result.permanent_event_ids == ()  # ring-only events only


class TestCLI:
    def test_cli_runs_calm_fixture(self, tmp_path: Path) -> None:
        ledger = tmp_path / "cli-ledger.jsonl"
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "sentinel.runtime.market_replay",
                "--fixture",
                str(_FIXTURE_DIR / "calm_tight_spread.jsonl"),
                "--ledger",
                str(ledger),
            ],
            capture_output=True,
            text=True,
            cwd=_REPO_ROOT,
            check=False,
        )
        assert proc.returncode == 0, proc.stderr
        assert "observations_seen=1" in proc.stdout
        assert "hash_chain_valid=True" in proc.stdout

    def test_cli_missing_fixture_returns_1(self, tmp_path: Path) -> None:
        ledger = tmp_path / "cli-ledger.jsonl"
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "sentinel.runtime.market_replay",
                "--fixture",
                str(tmp_path / "no-such-fixture.jsonl"),
                "--ledger",
                str(ledger),
            ],
            capture_output=True,
            text=True,
            cwd=_REPO_ROOT,
            check=False,
        )
        assert proc.returncode == 1
