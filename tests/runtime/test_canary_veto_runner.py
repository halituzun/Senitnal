"""V8 — Canary veto runner + CLI tests."""

from __future__ import annotations

import re
from pathlib import Path

from sentinel.canary.evaluator import CanaryVetoContext
from sentinel.observer.ledger import JsonlObserverLedger
from sentinel.observer.ring_buffer import ObserverRingBuffer
from sentinel.policy.record_builder import build_deontic_policy_candidate_record
from sentinel.runtime.canary_veto import cli_main, run_canary_veto_file
from sentinel.runtime.output import SystemOutput
from sentinel.types.memory import MemoryRecordStatus
from sentinel.types.neural_seed import ProvenanceRef

from tests.canary._fixtures import make_bounds, make_window
from tests.policy._fixtures import make_artifact

_FIX = Path("tests/fixtures/canary")
_CLOSED = {
    SystemOutput.WAIT,
    SystemOutput.BLOCK,
    SystemOutput.MONITOR,
    SystemOutput.NEED_RECALL,
    SystemOutput.NO_ACTION,
}


def _ctx() -> CanaryVetoContext:
    rec = build_deontic_policy_candidate_record(
        artifact=make_artifact(
            effective_at_ms=1_700_000_000_000,
            created_at_ms=1_700_000_000_000,
        ),
        provenance=ProvenanceRef(source_event_id="ev-1"),
        created_at_ms=1_700_000_000_000,
        evidence_refs=("approval-1",),
    ).model_copy(update={"status": MemoryRecordStatus.ACTIVE})
    state = make_window()
    state.last_reset_at_ms = 1_700_000_000_000
    return CanaryVetoContext(
        bounds=make_bounds(),
        window_state=state,
        now_ms=1_700_000_001_000,
        active_policy_record=rec,
    )


class TestRunner:
    def test_benign_fixture_runs(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        ring = ObserverRingBuffer(capacity=32)
        result = run_canary_veto_file(
            path=_FIX / "benign_candidate_no_veto.jsonl",
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id="batch-1"),
            context=_ctx(),
        )
        assert result.candidates_seen == 1
        assert result.no_veto_count == 1
        assert result.hash_chain_valid is True
        for o in result.outputs:
            assert o in _CLOSED

    def test_high_risk_vetoes(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        ring = ObserverRingBuffer(capacity=32)
        result = run_canary_veto_file(
            path=_FIX / "high_risk_candidate_veto.jsonl",
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id="batch-2"),
            context=_ctx(),
        )
        assert result.veto_count == 1

    def test_negative_edge_vetoes(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        ring = ObserverRingBuffer(capacity=32)
        result = run_canary_veto_file(
            path=_FIX / "negative_edge_candidate_veto.jsonl",
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id="batch-3"),
            context=_ctx(),
        )
        assert result.veto_count == 1

    def test_expired_vetoes(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        ring = ObserverRingBuffer(capacity=32)
        result = run_canary_veto_file(
            path=_FIX / "expired_candidate_veto.jsonl",
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id="batch-4"),
            context=_ctx(),
        )
        assert result.veto_count == 1

    def test_no_external_writes(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        ring = ObserverRingBuffer(capacity=32)
        result = run_canary_veto_file(
            path=_FIX / "benign_candidate_no_veto.jsonl",
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id="batch-x"),
            context=_ctx(),
        )
        assert result.any_creates_action is False
        assert result.any_writes_external is False
        assert result.any_approves_trade is False
        assert result.any_no_veto_is_approval is False


class TestRunnerSafety:
    def test_no_exchange_imports(self) -> None:
        for module_path in (
            Path("sentinel/canary/__init__.py"),
            Path("sentinel/canary/candidate.py"),
            Path("sentinel/canary/veto.py"),
            Path("sentinel/canary/limits.py"),
            Path("sentinel/canary/evaluator.py"),
            Path("sentinel/canary/audit.py"),
            Path("sentinel/canary/jsonl.py"),
            Path("sentinel/runtime/canary_veto.py"),
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

    def test_no_action_intent_in_v8_modules(self) -> None:
        for module_path in (
            Path("sentinel/canary/candidate.py"),
            Path("sentinel/canary/veto.py"),
            Path("sentinel/canary/limits.py"),
            Path("sentinel/canary/evaluator.py"),
            Path("sentinel/canary/audit.py"),
            Path("sentinel/canary/jsonl.py"),
            Path("sentinel/runtime/canary_veto.py"),
        ):
            src = module_path.read_text(encoding="utf-8")
            assert "ApprovedActionIntent" not in src

    def test_no_gelal_write_imports(self) -> None:
        for module_path in (
            Path("sentinel/canary/evaluator.py"),
            Path("sentinel/canary/audit.py"),
            Path("sentinel/canary/jsonl.py"),
            Path("sentinel/runtime/canary_veto.py"),
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

    def test_no_orders_pending_in_runtime_source(self) -> None:
        for module_path in (
            Path("sentinel/canary/evaluator.py"),
            Path("sentinel/canary/audit.py"),
            Path("sentinel/runtime/canary_veto.py"),
        ):
            src = module_path.read_text(encoding="utf-8")
            assert "orders.pending" not in src
            assert "gelal:orders" not in src

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
    def test_cli_runs_benign(self, tmp_path: Path) -> None:
        rc = cli_main(
            [
                "--input",
                str(_FIX / "benign_candidate_no_veto.jsonl"),
                "--ledger",
                str(tmp_path / "l.jsonl"),
                "--now-ms",
                "1700000001000",
            ]
        )
        assert rc == 0

    def test_cli_runs_veto_fixture(self, tmp_path: Path) -> None:
        rc = cli_main(
            [
                "--input",
                str(_FIX / "high_risk_candidate_veto.jsonl"),
                "--ledger",
                str(tmp_path / "l.jsonl"),
                "--now-ms",
                "1700000001000",
            ]
        )
        assert rc == 0

    def test_cli_invalid_fixture(self, tmp_path: Path) -> None:
        rc = cli_main(
            [
                "--input",
                str(_FIX / "forbidden_order_fields_invalid.jsonl"),
                "--ledger",
                str(tmp_path / "l.jsonl"),
            ]
        )
        assert rc == 1

    def test_cli_missing_file(self, tmp_path: Path) -> None:
        rc = cli_main(
            [
                "--input",
                str(tmp_path / "nope.jsonl"),
                "--ledger",
                str(tmp_path / "l.jsonl"),
            ]
        )
        assert rc == 1
