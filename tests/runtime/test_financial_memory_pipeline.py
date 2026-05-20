"""V3 — Financial memory pipeline end-to-end tests."""

from __future__ import annotations

from pathlib import Path

from sentinel.adapters.market_observation import (
    MarketObservationEnvelope,  # noqa: TC002 (runtime annotation)
)
from sentinel.adapters.synthetic_market import SyntheticMarketAdapter
from sentinel.memory.store import InMemoryExplicitMemoryStore
from sentinel.observer.ledger import JsonlObserverLedger
from sentinel.observer.ring_buffer import ObserverRingBuffer
from sentinel.runtime.financial_memory_pipeline import run_financial_memory_pipeline
from sentinel.types.neural_seed import ProvenanceRef


def _setup(
    tmp_path: Path,
) -> tuple[InMemoryExplicitMemoryStore, JsonlObserverLedger, ObserverRingBuffer]:
    return (
        InMemoryExplicitMemoryStore(),
        JsonlObserverLedger(tmp_path / "ledger.jsonl"),
        ObserverRingBuffer(capacity=64),
    )


def _envelopes(n: int) -> list[MarketObservationEnvelope]:
    adapter = SyntheticMarketAdapter.default()
    return [adapter.emit_market_observation() for _ in range(n)]


class TestFinancialMemoryPipeline:
    def test_valid_observations_produce_candidates(self, tmp_path: Path) -> None:
        store, ledger, ring = _setup(tmp_path)
        result = run_financial_memory_pipeline(
            observations=_envelopes(3),
            store=store,
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id="test"),
        )
        assert result.observations_seen == 3
        assert result.candidate_records_written == 3
        assert result.records_rejected == 0
        assert len(store) == 3
        assert result.hash_chain_valid is True

    def test_recall_request_emitted_after_writes(self, tmp_path: Path) -> None:
        store, ledger, ring = _setup(tmp_path)
        result = run_financial_memory_pipeline(
            observations=_envelopes(2),
            store=store,
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id="test"),
        )
        assert result.recall_requests == 1
        assert result.recall_events_built == 1

    def test_no_observations_no_recall(self, tmp_path: Path) -> None:
        store, ledger, ring = _setup(tmp_path)
        result = run_financial_memory_pipeline(
            observations=[],
            store=store,
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id="test"),
        )
        assert result.observations_seen == 0
        assert result.recall_requests == 0
        assert result.recall_events_built == 0

    def test_emit_recall_after_writes_false(self, tmp_path: Path) -> None:
        store, ledger, ring = _setup(tmp_path)
        result = run_financial_memory_pipeline(
            observations=_envelopes(2),
            store=store,
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id="test"),
            emit_recall_after_writes=False,
        )
        assert result.recall_requests == 0
        assert result.recall_events_built == 0

    def test_memory_status_changed_audit_emitted(self, tmp_path: Path) -> None:
        store, ledger, ring = _setup(tmp_path)
        run_financial_memory_pipeline(
            observations=_envelopes(2),
            store=store,
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id="test"),
        )
        content = (tmp_path / "ledger.jsonl").read_text(encoding="utf-8")
        assert "MEMORY_RECORD_STATUS_CHANGED" in content

    def test_hash_chain_verifies(self, tmp_path: Path) -> None:
        store, ledger, ring = _setup(tmp_path)
        result = run_financial_memory_pipeline(
            observations=_envelopes(2),
            store=store,
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id="test"),
        )
        assert result.hash_chain_valid is True

    def test_no_approved_action_intent_in_source(self) -> None:
        from sentinel.runtime import financial_memory_pipeline

        src = Path(financial_memory_pipeline.__file__).read_text(encoding="utf-8")
        assert "ApprovedActionIntent" not in src
        assert "evaluate_action" not in src

    def test_no_deontic_action_path_invoked(self) -> None:
        from sentinel.runtime import financial_memory_pipeline

        src = Path(financial_memory_pipeline.__file__).read_text(encoding="utf-8")
        assert "DeonticGate" not in src
        # The gate module is allowed to be imported indirectly for
        # EvidenceAxis but the actual evaluate_action / deontic gate
        # entrypoints must not be called.

    def test_no_forbidden_imports_in_source(self) -> None:
        import re

        from sentinel.runtime import financial_memory_pipeline

        src = Path(financial_memory_pipeline.__file__).read_text(encoding="utf-8")
        bad = re.compile(
            r"^\s*(import|from)\s+("
            r"ccxt|web3|binance|btcturk|pybit|okx|gate_api|kucoin|huobi|bitfinex|kraken|"
            r"openai|anthropic|langchain|requests|httpx|aiohttp"
            r")\b",
            re.MULTILINE,
        )
        assert bad.findall(src) == []

    def test_no_forbidden_output_literals_in_source(self) -> None:
        from sentinel.runtime import financial_memory_pipeline

        src = Path(financial_memory_pipeline.__file__).read_text(encoding="utf-8")
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

    def test_observation_ingested_stays_ring_only(self, tmp_path: Path) -> None:
        # After running the pipeline, the ledger should NOT contain
        # OBSERVATION_INGESTED events (those are ring_buffer_only).
        store, ledger, ring = _setup(tmp_path)
        run_financial_memory_pipeline(
            observations=_envelopes(2),
            store=store,
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id="test"),
        )
        content = (tmp_path / "ledger.jsonl").read_text(encoding="utf-8")
        assert "OBSERVATION_INGESTED" not in content
