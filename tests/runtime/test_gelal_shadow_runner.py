"""V5 — Gel.Al shadow batch runner + safety tests."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from sentinel.observer.ledger import JsonlObserverLedger
from sentinel.observer.ring_buffer import ObserverRingBuffer
from sentinel.runtime.gelal_shadow import cli_main, run_gelal_shadow_file
from sentinel.runtime.output import SystemOutput
from sentinel.types.neural_seed import ProvenanceRef

_FIXTURE_DIR = Path("tests/fixtures/gelal_shadow")
_CLOSED_OUTPUTS = {
    SystemOutput.WAIT,
    SystemOutput.BLOCK,
    SystemOutput.MONITOR,
    SystemOutput.NEED_RECALL,
    SystemOutput.NO_ACTION,
}


class TestRunnerLoadsFixtureAndEvaluatesAll:
    def test_opportunity_fixture_runs(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        ring = ObserverRingBuffer(capacity=64)
        result = run_gelal_shadow_file(
            path=_FIXTURE_DIR / "opportunity_seen_positive_edge.jsonl",
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id="batch-1"),
        )
        assert result.events_seen == 1
        assert result.events_accepted == 1
        assert result.hash_chain_valid is True
        assert all(o in _CLOSED_OUTPUTS for o in result.outputs)

    def test_kill_switch_fixture_yields_block(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        ring = ObserverRingBuffer(capacity=64)
        result = run_gelal_shadow_file(
            path=_FIXTURE_DIR / "kill_switch_active_observed.jsonl",
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id="batch-2"),
        )
        assert result.block_count == 1

    def test_bad_order_fixture_yields_block(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        ring = ObserverRingBuffer(capacity=64)
        result = run_gelal_shadow_file(
            path=_FIXTURE_DIR / "bad_order_observed.jsonl",
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id="batch-3"),
        )
        assert result.block_count == 1

    def test_high_risk_fixture_yields_block(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        ring = ObserverRingBuffer(capacity=64)
        result = run_gelal_shadow_file(
            path=_FIXTURE_DIR / "risk_gate_blocked_high_risk.jsonl",
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id="batch-4"),
        )
        assert result.block_count == 1

    def test_outputs_in_closed_set(self, tmp_path: Path) -> None:
        ring = ObserverRingBuffer(capacity=64)
        for fixture in _FIXTURE_DIR.glob("*.jsonl"):
            if "invalid" in fixture.name:
                continue
            sub_ledger = JsonlObserverLedger(tmp_path / f"l-{fixture.stem}.jsonl")
            result = run_gelal_shadow_file(
                path=fixture,
                ledger=sub_ledger,
                ring_buffer=ring,
                provenance=ProvenanceRef(source_event_id="batch-z"),
            )
            for o in result.outputs:
                assert o in _CLOSED_OUTPUTS, f"out-of-set output {o!r} from {fixture.name}"

    def test_permanent_and_ring_ids_separated(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        ring = ObserverRingBuffer(capacity=64)
        result = run_gelal_shadow_file(
            path=_FIXTURE_DIR / "opportunity_seen_positive_edge.jsonl",
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id="batch-x"),
        )
        # OBSERVATION_INGESTED and WORKSPACE_PULSE are ring-only.
        assert all("ingested" in eid or "pulse" in eid for eid in result.ring_buffer_event_ids)
        # No catalog event in V5 emits to the permanent ledger by default.
        assert result.permanent_event_ids == ()


class TestRunnerSafety:
    def test_no_exchange_imports_in_new_modules(self) -> None:
        for module_path in (
            Path("sentinel/integrations/gelal_shadow.py"),
            Path("sentinel/integrations/gelal_jsonl.py"),
            Path("sentinel/integrations/gelal_sanitizer.py"),
            Path("sentinel/integrations/gelal_manifest.py"),
            Path("sentinel/integrations/gelal_audit.py"),
            Path("sentinel/integrations/gelal_shadow_eval.py"),
            Path("sentinel/runtime/gelal_shadow.py"),
        ):
            src = module_path.read_text(encoding="utf-8")
            pattern = re.compile(
                r"^\s*(import|from)\s+("
                r"ccxt|web3|binance|btcturk|pybit|okx|gate_api|kucoin|huobi|"
                r"bitfinex|kraken|openai|anthropic|langchain|requests|httpx|aiohttp"
                r")\b",
                re.MULTILINE,
            )
            assert pattern.findall(src) == [], f"forbidden import found in {module_path}"

    def test_no_forbidden_output_literals_in_new_modules(self) -> None:
        for module_path in (
            Path("sentinel/integrations/gelal_shadow.py"),
            Path("sentinel/integrations/gelal_jsonl.py"),
            Path("sentinel/integrations/gelal_sanitizer.py"),
            Path("sentinel/integrations/gelal_manifest.py"),
            Path("sentinel/integrations/gelal_audit.py"),
            Path("sentinel/integrations/gelal_shadow_eval.py"),
            Path("sentinel/runtime/gelal_shadow.py"),
        ):
            src = module_path.read_text(encoding="utf-8")
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
                assert literal not in src, f"forbidden literal {literal} in {module_path}"

    def test_no_gelal_write_path(self) -> None:
        """No new module helper writes back to Gel.Al."""
        for module_path in (
            Path("sentinel/integrations/gelal_shadow.py"),
            Path("sentinel/integrations/gelal_jsonl.py"),
            Path("sentinel/integrations/gelal_sanitizer.py"),
            Path("sentinel/integrations/gelal_manifest.py"),
            Path("sentinel/integrations/gelal_audit.py"),
            Path("sentinel/integrations/gelal_shadow_eval.py"),
            Path("sentinel/runtime/gelal_shadow.py"),
        ):
            src = module_path.read_text(encoding="utf-8")
            # No module imports a Redis / DB / HTTP client.
            for forbidden in (
                "redis",
                "psycopg",
                "sqlalchemy",
                "pymongo",
                "kafka",
                "boto3",
                "telegram",
            ):
                assert f"import {forbidden}" not in src
                assert f"from {forbidden}" not in src

    def test_existing_dry_sim_unchanged(self, tmp_path: Path) -> None:
        from sentinel import EchoAdapter, run_dry_simulation

        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        result = run_dry_simulation(
            ledger=ledger,
            adapter=EchoAdapter.default(),
            observation_magnitude=0.8,
        )
        assert result.output is SystemOutput.WAIT
        assert ledger.verify() is True


class TestRunnerCli:
    def test_cli_runs_valid_fixture(self, tmp_path: Path) -> None:
        rc = cli_main(
            [
                "--fixture",
                str(_FIXTURE_DIR / "opportunity_seen_positive_edge.jsonl"),
                "--ledger",
                str(tmp_path / "l.jsonl"),
            ]
        )
        assert rc == 0

    def test_cli_load_error_returns_1(self, tmp_path: Path) -> None:
        rc = cli_main(
            [
                "--fixture",
                str(tmp_path / "nope.jsonl"),
                "--ledger",
                str(tmp_path / "l.jsonl"),
            ]
        )
        assert rc == 1

    def test_cli_invalid_fixture_returns_1(self, tmp_path: Path) -> None:
        rc = cli_main(
            [
                "--fixture",
                str(_FIXTURE_DIR / "forbidden_command_fields_invalid.jsonl"),
                "--ledger",
                str(tmp_path / "l.jsonl"),
            ]
        )
        assert rc == 1

    def test_cli_malformed_returns_1(self, tmp_path: Path) -> None:
        rc = cli_main(
            [
                "--fixture",
                str(_FIXTURE_DIR / "malformed_invalid.jsonl"),
                "--ledger",
                str(tmp_path / "l.jsonl"),
            ]
        )
        assert rc == 1


class TestSchemaValueErrorIsValidationError:
    def test_envelope_construct_with_forbidden_key_raises(self) -> None:
        from pydantic import ValidationError
        from sentinel.integrations.gelal_shadow import (
            GelAlShadowEnvelope,
            GelAlShadowEventType,
        )

        with pytest.raises(ValidationError):
            GelAlShadowEnvelope(
                event_id="x",
                event_type=GelAlShadowEventType.MARKET_OBSERVATION,
                source_system="gel_al_borsa",
                observed_at_ms=0,
                exported_at_ms=1,
                source_table="t",
                source_row_id="r",
                source_hash="sha256:x",
                environment="paper",
                payload={"api_key": "leak", "confidence": 0.5},
            )
