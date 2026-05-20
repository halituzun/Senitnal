"""Tests for the OBSERVATION_INGESTED market-audit routing helper."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003 (pytest tmp_path annotation)

from sentinel.adapters.market_audit import emit_market_observation_ingested
from sentinel.adapters.synthetic_market import SyntheticMarketAdapter
from sentinel.observer.ledger import JsonlObserverLedger
from sentinel.observer.permanence import EventPermanence
from sentinel.observer.ring_buffer import ObserverRingBuffer
from sentinel.types.neural_seed import ProvenanceRef


class TestMarketAudit:
    def test_routes_via_router_to_ring_buffer(self, tmp_path: Path) -> None:
        adapter = SyntheticMarketAdapter.default()
        env = adapter.emit_market_observation()

        ledger = JsonlObserverLedger(tmp_path / "ledger.jsonl")
        ring = ObserverRingBuffer(capacity=16)
        outcome = emit_market_observation_ingested(
            envelope=env,
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id=env.event_id),
        )
        assert outcome.permanence is EventPermanence.RING_BUFFER_ONLY
        assert outcome.pushed_to_ring_buffer is True
        assert outcome.written_to_ledger is False
        assert (tmp_path / "ledger.jsonl").exists() is False or (
            tmp_path / "ledger.jsonl"
        ).read_text() == ""

    def test_no_jsonl_promotion_when_ring_buffer_missing(self, tmp_path: Path) -> None:
        adapter = SyntheticMarketAdapter.default()
        env = adapter.emit_market_observation()
        ledger = JsonlObserverLedger(tmp_path / "ledger.jsonl")
        outcome = emit_market_observation_ingested(
            envelope=env,
            ledger=ledger,
            ring_buffer=None,
            provenance=ProvenanceRef(source_event_id=env.event_id),
        )
        assert outcome.permanence is EventPermanence.RING_BUFFER_ONLY
        assert outcome.written_to_ledger is False
        assert outcome.pushed_to_ring_buffer is False

    def test_payload_preserves_symbol_and_venue(self, tmp_path: Path) -> None:
        adapter = SyntheticMarketAdapter.default()
        env = adapter.emit_market_observation(symbol="ETH/TRY", venue="synthetic-2")
        ledger = JsonlObserverLedger(tmp_path / "ledger.jsonl")
        ring = ObserverRingBuffer(capacity=16)
        outcome = emit_market_observation_ingested(
            envelope=env,
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id=env.event_id),
        )
        payload = outcome.event.payload
        assert payload["symbol"] == "ETH/TRY"
        assert payload["venue"] == "synthetic-2"
        # Observer-side payload carries identity link to envelope.
        assert payload["source_event_id"] == env.event_id

    def test_event_type_and_family(self, tmp_path: Path) -> None:
        adapter = SyntheticMarketAdapter.default()
        env = adapter.emit_market_observation()
        ledger = JsonlObserverLedger(tmp_path / "ledger.jsonl")
        ring = ObserverRingBuffer(capacity=16)
        outcome = emit_market_observation_ingested(
            envelope=env,
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id=env.event_id),
        )
        assert outcome.event.event_type == "OBSERVATION_INGESTED"
        assert outcome.event.event_family.value == "ingress"
