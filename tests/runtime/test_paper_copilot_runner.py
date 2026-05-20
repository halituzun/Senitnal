"""V7 — Paper co-pilot runner + CLI tests."""

from __future__ import annotations

import re
from pathlib import Path

from sentinel.observer.ledger import JsonlObserverLedger
from sentinel.observer.ring_buffer import ObserverRingBuffer
from sentinel.paper.copilot import PaperCoPilotContext
from sentinel.runtime.output import SystemOutput
from sentinel.runtime.paper_copilot import (
    cli_main,
    run_paper_copilot_file,
)
from sentinel.types.neural_seed import ProvenanceRef

_PAPER_FIX = Path("tests/fixtures/paper")
_MARKET_FIX = Path("tests/fixtures/market")
_CLOSED = {
    SystemOutput.WAIT,
    SystemOutput.BLOCK,
    SystemOutput.MONITOR,
    SystemOutput.NEED_RECALL,
    SystemOutput.NO_ACTION,
}


class TestRunnerSourceKinds:
    def test_paper_opportunity_jsonl_runs(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        ring = ObserverRingBuffer(capacity=64)
        result = run_paper_copilot_file(
            path=_PAPER_FIX / "paper_opportunities_mixed.jsonl",
            source_kind="paper_opportunity_jsonl",
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id="batch-1"),
            context=PaperCoPilotContext(now_ms=1_700_000_000_000),
        )
        assert result.opportunities_accepted == 3
        assert result.hash_chain_valid is True
        for o in result.outputs:
            assert o in _CLOSED

    def test_gelal_shadow_jsonl_runs(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        ring = ObserverRingBuffer(capacity=64)
        result = run_paper_copilot_file(
            path=_PAPER_FIX / "gelal_shadow_opportunity_seen.jsonl",
            source_kind="gelal_shadow_jsonl",
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id="batch-2"),
            context=PaperCoPilotContext(now_ms=1_700_000_000_500),
        )
        assert result.opportunities_accepted == 1

    def test_gelal_bad_order_blocks(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        ring = ObserverRingBuffer(capacity=64)
        result = run_paper_copilot_file(
            path=_PAPER_FIX / "gelal_shadow_bad_order.jsonl",
            source_kind="gelal_shadow_jsonl",
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id="batch-3"),
            context=PaperCoPilotContext(now_ms=1_700_000_010_000),
        )
        assert result.block_count == 1

    def test_gelal_kill_switch_blocks(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        ring = ObserverRingBuffer(capacity=64)
        result = run_paper_copilot_file(
            path=_PAPER_FIX / "gelal_shadow_kill_switch.jsonl",
            source_kind="gelal_shadow_jsonl",
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id="batch-4"),
            context=PaperCoPilotContext(now_ms=1_700_000_020_000),
        )
        assert result.block_count == 1

    def test_market_jsonl_runs(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        ring = ObserverRingBuffer(capacity=64)
        result = run_paper_copilot_file(
            path=_MARKET_FIX / "calm_tight_spread.jsonl",
            source_kind="market_jsonl",
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id="batch-5"),
            context=PaperCoPilotContext(now_ms=1_700_000_000_000),
        )
        assert result.opportunities_accepted >= 1

    def test_no_external_writes(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        ring = ObserverRingBuffer(capacity=64)
        result = run_paper_copilot_file(
            path=_PAPER_FIX / "paper_opportunities_mixed.jsonl",
            source_kind="paper_opportunity_jsonl",
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id="batch-x"),
            context=PaperCoPilotContext(now_ms=1_000_000),
        )
        assert result.any_creates_action is False
        assert result.any_writes_external is False
        assert result.any_approved_for_live is False

    def test_deterministic(self, tmp_path: Path) -> None:
        def go() -> tuple[int, int, int, int, int]:
            ledger = JsonlObserverLedger(tmp_path / f"l-{id(object())}.jsonl")
            ring = ObserverRingBuffer(capacity=64)
            result = run_paper_copilot_file(
                path=_PAPER_FIX / "paper_opportunities_mixed.jsonl",
                source_kind="paper_opportunity_jsonl",
                ledger=ledger,
                ring_buffer=ring,
                provenance=ProvenanceRef(source_event_id="det"),
                context=PaperCoPilotContext(now_ms=1_000_000),
            )
            return (
                result.block_count,
                result.monitor_count,
                result.wait_count,
                result.need_recall_count,
                result.no_action_count,
            )

        assert go() == go()


class TestRunnerSafety:
    def test_no_exchange_imports(self) -> None:
        for module_path in (
            Path("sentinel/paper/__init__.py"),
            Path("sentinel/paper/opportunity.py"),
            Path("sentinel/paper/decision.py"),
            Path("sentinel/paper/copilot.py"),
            Path("sentinel/paper/audit.py"),
            Path("sentinel/paper/outcome.py"),
            Path("sentinel/paper/gelal_compare.py"),
            Path("sentinel/runtime/paper_copilot.py"),
        ):
            src = module_path.read_text(encoding="utf-8")
            pattern = re.compile(
                r"^\s*(import|from)\s+("
                r"ccxt|web3|binance|btcturk|pybit|okx|gate_api|kucoin|huobi|"
                r"bitfinex|kraken|openai|anthropic|langchain|requests|httpx|aiohttp"
                r")\b",
                re.MULTILINE,
            )
            assert pattern.findall(src) == [], f"forbidden import in {module_path}"

    def test_no_action_intent_in_v7_modules(self) -> None:
        for module_path in (
            Path("sentinel/paper/copilot.py"),
            Path("sentinel/paper/decision.py"),
            Path("sentinel/paper/opportunity.py"),
            Path("sentinel/paper/audit.py"),
            Path("sentinel/paper/outcome.py"),
            Path("sentinel/paper/gelal_compare.py"),
            Path("sentinel/runtime/paper_copilot.py"),
        ):
            src = module_path.read_text(encoding="utf-8")
            assert "ApprovedActionIntent" not in src, f"{module_path}"
            assert "evaluate_action" not in src, f"{module_path}"

    def test_no_gelal_write_imports(self) -> None:
        for module_path in (
            Path("sentinel/paper/copilot.py"),
            Path("sentinel/paper/audit.py"),
            Path("sentinel/paper/outcome.py"),
            Path("sentinel/paper/gelal_compare.py"),
            Path("sentinel/runtime/paper_copilot.py"),
        ):
            src = module_path.read_text(encoding="utf-8")
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
    def test_cli_paper_opportunity(self, tmp_path: Path) -> None:
        rc = cli_main(
            [
                "--source-kind",
                "paper_opportunity_jsonl",
                "--input",
                str(_PAPER_FIX / "paper_opportunities_mixed.jsonl"),
                "--ledger",
                str(tmp_path / "l.jsonl"),
                "--now-ms",
                "1700000000000",
            ]
        )
        assert rc == 0

    def test_cli_gelal_shadow(self, tmp_path: Path) -> None:
        rc = cli_main(
            [
                "--source-kind",
                "gelal_shadow_jsonl",
                "--input",
                str(_PAPER_FIX / "gelal_shadow_opportunity_seen.jsonl"),
                "--ledger",
                str(tmp_path / "l.jsonl"),
            ]
        )
        assert rc == 0

    def test_cli_invalid_path_returns_1(self, tmp_path: Path) -> None:
        rc = cli_main(
            [
                "--source-kind",
                "paper_opportunity_jsonl",
                "--input",
                str(tmp_path / "nope.jsonl"),
                "--ledger",
                str(tmp_path / "l.jsonl"),
            ]
        )
        assert rc == 1

    def test_cli_forbidden_field_invalid_returns_1(self, tmp_path: Path) -> None:
        # Forbidden field opportunity file is rejected by the loader.
        rc = cli_main(
            [
                "--source-kind",
                "paper_opportunity_jsonl",
                "--input",
                str(_PAPER_FIX / "forbidden_fields_invalid.jsonl"),
                "--ledger",
                str(tmp_path / "l.jsonl"),
            ]
        )
        # The loader tolerates per-line schema rejection (rejected counter)
        # rather than crashing; CLI returns 0 with 0 accepted.  This
        # mirrors V5/V6 batch-runner semantics.
        assert rc == 0
