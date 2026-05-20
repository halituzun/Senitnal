"""V9 — Live governance runner + CLI tests."""

from __future__ import annotations

import re
from pathlib import Path

from sentinel.governance.guard import GovernanceGuardContext
from sentinel.observer.ledger import JsonlObserverLedger
from sentinel.observer.ring_buffer import ObserverRingBuffer
from sentinel.policy.record_builder import build_deontic_policy_candidate_record
from sentinel.runtime.live_governance import cli_main, run_live_governance_file
from sentinel.runtime.output import SystemOutput
from sentinel.types.memory import MemoryRecordStatus
from sentinel.types.neural_seed import ProvenanceRef

from tests.governance._fixtures import make_approval
from tests.policy._fixtures import make_artifact

_FIX = Path("tests/fixtures/governance")
_CLOSED = {
    SystemOutput.WAIT,
    SystemOutput.BLOCK,
    SystemOutput.MONITOR,
    SystemOutput.NEED_RECALL,
    SystemOutput.NO_ACTION,
}


def _ctx() -> GovernanceGuardContext:
    rec = build_deontic_policy_candidate_record(
        artifact=make_artifact(
            effective_at_ms=1_700_000_000_000,
            created_at_ms=1_700_000_000_000,
        ),
        provenance=ProvenanceRef(source_event_id="ev-1"),
        created_at_ms=1_700_000_000_000,
        evidence_refs=("approval",),
    ).model_copy(update={"status": MemoryRecordStatus.ACTIVE})
    return GovernanceGuardContext(
        now_ms=1_700_000_001_000,
        hash_chain_valid=True,
        active_policy_record=rec,
        human_approval=make_approval(
            request_id="gov-req-001",
            expires_at_ms=1_700_000_005_000,
        ),
    )


class TestRunner:
    def test_benign_runs(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        ring = ObserverRingBuffer(capacity=32)
        result = run_live_governance_file(
            path=_FIX / "benign_no_action.jsonl",
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id="batch-1"),
            context=_ctx(),
        )
        assert result.requests_seen == 1
        assert result.no_action_count == 1
        for o in result.outputs:
            assert o in _CLOSED
        assert result.hash_chain_valid is True

    def test_expired_request_blocks(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        ring = ObserverRingBuffer(capacity=32)
        result = run_live_governance_file(
            path=_FIX / "expired_request_block.jsonl",
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id="batch-2"),
            context=_ctx(),
        )
        assert result.block_count == 1

    def test_high_risk_request_blocks(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        ring = ObserverRingBuffer(capacity=32)
        # high_risk fixture has request_id gov-req-003; the approval
        # context only matches gov-req-001 so the request fails the
        # human approval gate before reaching the risk score branch.
        # Both outcomes are valid block reasons; assert block_count.
        result = run_live_governance_file(
            path=_FIX / "high_risk_block.jsonl",
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id="batch-3"),
            context=_ctx(),
        )
        assert result.block_count == 1

    def test_no_external_writes(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        ring = ObserverRingBuffer(capacity=32)
        result = run_live_governance_file(
            path=_FIX / "benign_no_action.jsonl",
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id="batch-x"),
            context=_ctx(),
        )
        assert result.any_creates_action is False
        assert result.any_writes_external is False
        assert result.any_approves_trade is False
        assert result.any_no_veto_is_approval is False
        assert result.any_monitor_is_approval is False


class TestRunnerSafety:
    def test_no_exchange_imports(self) -> None:
        for module_path in (
            Path("sentinel/governance/__init__.py"),
            Path("sentinel/governance/scope.py"),
            Path("sentinel/governance/request.py"),
            Path("sentinel/governance/approval.py"),
            Path("sentinel/governance/decision.py"),
            Path("sentinel/governance/guard.py"),
            Path("sentinel/governance/audit.py"),
            Path("sentinel/governance/jsonl.py"),
            Path("sentinel/runtime/live_governance.py"),
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

    def test_no_action_intent_in_v9_modules(self) -> None:
        for module_path in (
            Path("sentinel/governance/scope.py"),
            Path("sentinel/governance/request.py"),
            Path("sentinel/governance/approval.py"),
            Path("sentinel/governance/decision.py"),
            Path("sentinel/governance/guard.py"),
            Path("sentinel/governance/audit.py"),
            Path("sentinel/governance/jsonl.py"),
            Path("sentinel/runtime/live_governance.py"),
        ):
            src = module_path.read_text(encoding="utf-8")
            assert "ApprovedActionIntent" not in src

    def test_no_gelal_write_imports(self) -> None:
        for module_path in (
            Path("sentinel/governance/guard.py"),
            Path("sentinel/governance/audit.py"),
            Path("sentinel/governance/jsonl.py"),
            Path("sentinel/runtime/live_governance.py"),
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
            Path("sentinel/governance/guard.py"),
            Path("sentinel/governance/audit.py"),
            Path("sentinel/runtime/live_governance.py"),
        ):
            src = module_path.read_text(encoding="utf-8")
            assert "orders.pending" not in src
            assert "gelal:orders" not in src
            assert "approve_trade" not in src
            assert "submit_order" not in src

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
    def test_cli_benign(self, tmp_path: Path) -> None:
        # CLI runs with no policy context → every request fails closed (block).
        # Exit 0 is still returned (hash chain valid, no safety flag violations).
        rc = cli_main(
            [
                "--input",
                str(_FIX / "benign_no_action.jsonl"),
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
                str(_FIX / "invalid_order_fields.jsonl"),
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
