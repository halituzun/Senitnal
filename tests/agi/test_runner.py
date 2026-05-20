"""V10 — Financial AGI v1 runner + CLI tests."""

from __future__ import annotations

import re
from pathlib import Path

from sentinel.governance.guard import GovernanceGuardContext
from sentinel.observer.ledger import JsonlObserverLedger
from sentinel.observer.ring_buffer import ObserverRingBuffer
from sentinel.policy.record_builder import build_deontic_policy_candidate_record
from sentinel.runtime.financial_agi import cli_main, run_financial_agi_file
from sentinel.runtime.output import SystemOutput
from sentinel.types.memory import MemoryRecordStatus
from sentinel.types.neural_seed import ProvenanceRef

from tests.agi._fixtures import make_evidence_gate_input
from tests.governance._fixtures import make_approval
from tests.policy._fixtures import make_artifact

_FIX = Path("tests/fixtures/agi")
_CLOSED = {
    SystemOutput.WAIT,
    SystemOutput.BLOCK,
    SystemOutput.MONITOR,
    SystemOutput.NEED_RECALL,
    SystemOutput.NO_ACTION,
}


def _ctx(request_id: str = "agi-req-001") -> GovernanceGuardContext:
    rec = build_deontic_policy_candidate_record(
        artifact=make_artifact(
            effective_at_ms=1_700_000_000_000,
            created_at_ms=1_700_000_000_000,
        ),
        provenance=ProvenanceRef(source_event_id="ev-agi-ctx"),
        created_at_ms=1_700_000_000_000,
        evidence_refs=("approval",),
    ).model_copy(update={"status": MemoryRecordStatus.ACTIVE})
    return GovernanceGuardContext(
        now_ms=1_700_000_001_000,
        hash_chain_valid=True,
        active_policy_record=rec,
        human_approval=make_approval(
            request_id=request_id,
            expires_at_ms=1_700_000_005_000,
        ),
    )


class TestAGIRunner:
    def test_benign_runs(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        ring = ObserverRingBuffer(capacity=32)
        result = run_financial_agi_file(
            path=_FIX / "benign_agi.jsonl",
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id="batch-agi-1"),
            context=_ctx("agi-req-001"),
            evidence_gate_input=make_evidence_gate_input(),
        )
        assert result.requests_seen == 1
        for o in result.outputs:
            assert o in _CLOSED
        assert result.hash_chain_valid is True

    def test_expired_deadline_blocks(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        ring = ObserverRingBuffer(capacity=32)
        result = run_financial_agi_file(
            path=_FIX / "expired_deadline_agi.jsonl",
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id="batch-agi-2"),
            context=_ctx("agi-req-003"),
            evidence_gate_input=make_evidence_gate_input(),
        )
        assert result.block_count == 1

    def test_high_risk_blocks(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        ring = ObserverRingBuffer(capacity=32)
        result = run_financial_agi_file(
            path=_FIX / "high_risk_agi.jsonl",
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id="batch-agi-3"),
            context=_ctx("agi-req-002"),
            evidence_gate_input=make_evidence_gate_input(),
        )
        assert result.block_count == 1

    def test_multi_request_runs(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        ring = ObserverRingBuffer(capacity=32)
        result = run_financial_agi_file(
            path=_FIX / "multi_request_agi.jsonl",
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id="batch-agi-4"),
            context=_ctx("agi-req-005a"),
            evidence_gate_input=make_evidence_gate_input(),
        )
        assert result.requests_seen == 3

    def test_no_external_writes(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        ring = ObserverRingBuffer(capacity=32)
        result = run_financial_agi_file(
            path=_FIX / "benign_agi.jsonl",
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id="batch-agi-x"),
            context=_ctx("agi-req-001"),
            evidence_gate_input=make_evidence_gate_input(),
        )
        assert result.any_creates_action is False
        assert result.any_writes_external is False
        assert result.any_approves_trade is False
        assert result.any_no_veto_is_approval is False
        assert result.any_monitor_is_approval is False

    def test_readiness_report_generated(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        ring = ObserverRingBuffer(capacity=32)
        result = run_financial_agi_file(
            path=_FIX / "benign_agi.jsonl",
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id="batch-rpt"),
            context=_ctx("agi-req-001"),
            evidence_gate_input=make_evidence_gate_input(),
            emit_readiness_report=True,
        )
        assert result.readiness_report is not None
        assert result.readiness_report.status in {
            "GREEN",
            "FAIL",
            "RELEASED_NOT_ACTIVATED",
            "PASS-",
        }


class TestAGIRunnerSafety:
    def test_no_exchange_imports(self) -> None:
        for module_path in (
            Path("sentinel/agi/__init__.py"),
            Path("sentinel/agi/state.py"),
            Path("sentinel/agi/evidence_gate.py"),
            Path("sentinel/agi/consensus.py"),
            Path("sentinel/agi/live_impact_guard.py"),
            Path("sentinel/agi/orchestrator.py"),
            Path("sentinel/agi/audit.py"),
            Path("sentinel/agi/readiness_report.py"),
            Path("sentinel/runtime/financial_agi.py"),
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

    def test_no_action_intent_in_v10_modules(self) -> None:
        for module_path in (
            Path("sentinel/agi/state.py"),
            Path("sentinel/agi/evidence_gate.py"),
            Path("sentinel/agi/consensus.py"),
            Path("sentinel/agi/live_impact_guard.py"),
            Path("sentinel/agi/orchestrator.py"),
            Path("sentinel/agi/audit.py"),
            Path("sentinel/agi/readiness_report.py"),
            Path("sentinel/runtime/financial_agi.py"),
        ):
            src = module_path.read_text(encoding="utf-8")
            assert "ApprovedActionIntent" not in src

    def test_no_gelal_write_imports(self) -> None:
        for module_path in (
            Path("sentinel/agi/orchestrator.py"),
            Path("sentinel/agi/audit.py"),
            Path("sentinel/runtime/financial_agi.py"),
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

    def test_no_orders_pending_in_v10_source(self) -> None:
        for module_path in (
            Path("sentinel/agi/orchestrator.py"),
            Path("sentinel/agi/audit.py"),
            Path("sentinel/runtime/financial_agi.py"),
        ):
            src = module_path.read_text(encoding="utf-8")
            assert "orders.pending" not in src
            assert "gelal:orders" not in src
            assert "approve_trade" not in src
            assert "submit_order" not in src


class TestAGICli:
    def test_cli_benign(self, tmp_path: Path) -> None:
        rc = cli_main(
            [
                "--input",
                str(_FIX / "benign_agi.jsonl"),
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
                str(_FIX / "invalid_fields_agi.jsonl"),
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
