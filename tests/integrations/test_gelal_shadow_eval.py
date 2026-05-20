"""V5 — Gel.Al audit routing + shadow evaluator tests."""

from __future__ import annotations

import re
from pathlib import Path

from sentinel.integrations.gelal_audit import emit_gelal_shadow_observation_ingested
from sentinel.integrations.gelal_shadow import (
    GelAlShadowEnvelope,
    GelAlShadowEventType,
)
from sentinel.integrations.gelal_shadow_eval import (
    GelAlShadowEvaluationResult,
    evaluate_gelal_shadow_event,
)
from sentinel.observer.ledger import JsonlObserverLedger
from sentinel.observer.ring_buffer import ObserverRingBuffer
from sentinel.runtime.output import SystemOutput
from sentinel.types.neural_seed import ProvenanceRef


def _env(
    *,
    event_id: str = "evt-1",
    event_type: GelAlShadowEventType = GelAlShadowEventType.OPPORTUNITY_SEEN,
    environment: str = "paper",
    payload: dict[str, object] | None = None,
) -> GelAlShadowEnvelope:
    if payload is None:
        payload = {"confidence": 0.7, "net_edge_pct": 0.4, "latency_ms": 30}
    return GelAlShadowEnvelope(
        event_id=event_id,
        event_type=event_type,
        source_system="gel_al_borsa",
        observed_at_ms=1000,
        exported_at_ms=1010,
        source_table="t",
        source_row_id="r",
        source_hash="sha256:x",
        environment=environment,  # type: ignore[arg-type]
        strategy_name="latency-arb",
        symbol="BTC-USDT",
        venue="binance",
        payload=payload,
    )


class TestGelAlAudit:
    def test_observation_ingested_ring_only(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        ring = ObserverRingBuffer(capacity=16)
        outcome = emit_gelal_shadow_observation_ingested(
            envelope=_env(),
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id="evt-1"),
        )
        assert outcome.pushed_to_ring_buffer is True
        assert outcome.written_to_ledger is False

    def test_permanent_ledger_unchanged_for_ring_only(self, tmp_path: Path) -> None:
        path = tmp_path / "l.jsonl"
        ledger = JsonlObserverLedger(path)
        ring = ObserverRingBuffer(capacity=16)
        emit_gelal_shadow_observation_ingested(
            envelope=_env(),
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id="evt-1"),
        )
        # Permanent file should not contain OBSERVATION_INGESTED record.
        content = path.read_text(encoding="utf-8") if path.exists() else ""
        assert "OBSERVATION_INGESTED" not in content

    def test_without_ring_buffer_dropped(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        outcome = emit_gelal_shadow_observation_ingested(
            envelope=_env(),
            ledger=ledger,
            ring_buffer=None,
            provenance=ProvenanceRef(source_event_id="evt-1"),
        )
        assert outcome.pushed_to_ring_buffer is False
        assert outcome.written_to_ledger is False

    def test_hash_chain_remains_valid(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        ring = ObserverRingBuffer(capacity=16)
        emit_gelal_shadow_observation_ingested(
            envelope=_env(),
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id="evt-1"),
        )
        assert ledger.verify() is True


class TestGelAlShadowEvaluator:
    def test_opportunity_seen_closed_output(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        ring = ObserverRingBuffer(capacity=16)
        result = evaluate_gelal_shadow_event(
            envelope=_env(),
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id="evt-1"),
        )
        assert isinstance(result, GelAlShadowEvaluationResult)
        assert result.sentinel_output in {
            SystemOutput.WAIT,
            SystemOutput.MONITOR,
            SystemOutput.NO_ACTION,
        }
        assert result.hash_chain_valid is True

    def test_bad_order_block(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        ring = ObserverRingBuffer(capacity=16)
        env = _env(
            event_id="bad-1",
            event_type=GelAlShadowEventType.EXECUTION_ATTEMPT_OBSERVED,
            environment="live",
            payload={
                "confidence": 0.5,
                "net_edge_pct": -0.2,
                "bad_order": True,
                "order_sent": True,
                "latency_ms": 400,
            },
        )
        result = evaluate_gelal_shadow_event(
            envelope=env,
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id="bad-1"),
        )
        assert result.sentinel_output is SystemOutput.BLOCK

    def test_kill_switch_active_block(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        ring = ObserverRingBuffer(capacity=16)
        env = _env(
            event_id="kill-1",
            event_type=GelAlShadowEventType.KILL_SWITCH_OBSERVED,
            environment="live",
            payload={
                "kill_switch_active": True,
                "source": "operator",
                "observed_by": "gel_al_runtime",
            },
        )
        result = evaluate_gelal_shadow_event(
            envelope=env,
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id="kill-1"),
        )
        assert result.sentinel_output is SystemOutput.BLOCK

    def test_high_risk_decision_block(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        ring = ObserverRingBuffer(capacity=16)
        env = _env(
            event_id="risk-1",
            event_type=GelAlShadowEventType.RISK_GATE_DECISION,
            payload={
                "confidence": 0.8,
                "risk_score": 0.95,
                "decision": "REJECTED_BY_RISK_GATE",
                "order_sent": False,
                "bad_order": False,
            },
        )
        result = evaluate_gelal_shadow_event(
            envelope=env,
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id="risk-1"),
        )
        assert result.sentinel_output is SystemOutput.BLOCK

    def test_low_confidence_wait(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        ring = ObserverRingBuffer(capacity=16)
        env = _env(
            event_id="weak-1",
            event_type=GelAlShadowEventType.MARKET_OBSERVATION,
            payload={"confidence": 0.1, "net_edge_pct": 0.01},
        )
        result = evaluate_gelal_shadow_event(
            envelope=env,
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id="weak-1"),
        )
        assert result.sentinel_output in {SystemOutput.WAIT, SystemOutput.NO_ACTION}

    def test_no_approved_action_intent_constructed(self) -> None:
        from sentinel.integrations import gelal_shadow_eval

        src = Path(gelal_shadow_eval.__file__).read_text(encoding="utf-8")
        assert "ApprovedActionIntent" not in src
        assert "evaluate_action" not in src

    def test_no_forbidden_literal_in_reasons(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        ring = ObserverRingBuffer(capacity=16)
        # All four major branches exercise reason text.
        envs = [
            _env(payload={"confidence": 0.05}),
            _env(
                event_id="bad-1",
                event_type=GelAlShadowEventType.EXECUTION_ATTEMPT_OBSERVED,
                environment="live",
                payload={"confidence": 0.5, "bad_order": True, "order_sent": True},
            ),
            _env(
                event_id="kill-1",
                event_type=GelAlShadowEventType.KILL_SWITCH_OBSERVED,
                environment="live",
                payload={
                    "kill_switch_active": True,
                    "source": "operator",
                    "observed_by": "gel_al_runtime",
                },
            ),
        ]
        for env in envs:
            r = evaluate_gelal_shadow_event(
                envelope=env,
                ledger=ledger,
                ring_buffer=ring,
                provenance=ProvenanceRef(source_event_id=env.event_id),
            )
            for needle in ("buy", "sell", "execute", "order", "submit", "_real"):
                assert not re.search(needle, r.reason, re.IGNORECASE), (
                    f"forbidden literal {needle!r} found in reason: {r.reason!r}"
                )

    def test_no_permanent_observation_ingested(self, tmp_path: Path) -> None:
        path = tmp_path / "l.jsonl"
        ledger = JsonlObserverLedger(path)
        ring = ObserverRingBuffer(capacity=16)
        evaluate_gelal_shadow_event(
            envelope=_env(),
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id="evt-1"),
        )
        content = path.read_text(encoding="utf-8") if path.exists() else ""
        # OBSERVATION_INGESTED and WORKSPACE_PULSE are both ring-only.
        assert "OBSERVATION_INGESTED" not in content
        assert "WORKSPACE_PULSE" not in content

    def test_no_memory_record_status_changed(self, tmp_path: Path) -> None:
        path = tmp_path / "l.jsonl"
        ledger = JsonlObserverLedger(path)
        ring = ObserverRingBuffer(capacity=16)
        evaluate_gelal_shadow_event(
            envelope=_env(),
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id="evt-1"),
        )
        content = path.read_text(encoding="utf-8") if path.exists() else ""
        assert "MEMORY_RECORD_STATUS_CHANGED" not in content
