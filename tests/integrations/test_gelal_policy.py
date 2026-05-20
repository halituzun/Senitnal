"""V6 — Gel.Al shadow → policy integration tests."""

from __future__ import annotations

from pathlib import Path

from sentinel.integrations.gelal_policy import (
    build_policy_input_from_gelal_shadow,
    evaluate_gelal_shadow_with_policy,
)
from sentinel.integrations.gelal_shadow import (
    GelAlShadowEnvelope,
    GelAlShadowEventType,
)
from sentinel.observer.ledger import JsonlObserverLedger
from sentinel.observer.ring_buffer import ObserverRingBuffer
from sentinel.policy.record_builder import build_deontic_policy_candidate_record
from sentinel.runtime.output import SystemOutput
from sentinel.types.memory import MemoryRecordStatus
from sentinel.types.neural_seed import ProvenanceRef

from tests.policy._fixtures import make_artifact


def _envelope(
    *,
    event_id: str = "ev-1",
    event_type: GelAlShadowEventType = GelAlShadowEventType.OPPORTUNITY_SEEN,
    environment: str = "shadow",
    payload: dict[str, object] | None = None,
) -> GelAlShadowEnvelope:
    if payload is None:
        payload = {"confidence": 0.6, "risk_score": 0.2, "latency_ms": 30}
    return GelAlShadowEnvelope(
        event_id=event_id,
        event_type=event_type,
        source_system="gel_al_borsa",
        observed_at_ms=1_000_000,
        exported_at_ms=1_000_020,
        source_table="t",
        source_row_id="r",
        source_hash="sha256:x",
        environment=environment,  # type: ignore[arg-type]
        strategy_name="latency-arb",
        symbol="BTC-USDT",
        venue="binance",
        payload=payload,
    )


def _active_policy() -> object:
    rec = build_deontic_policy_candidate_record(
        artifact=make_artifact(),
        provenance=ProvenanceRef(source_event_id="ev"),
        created_at_ms=1_000_000,
        evidence_refs=("approval",),
    )
    return rec.model_copy(update={"status": MemoryRecordStatus.ACTIVE})


class TestPolicyInputMapping:
    def test_maps_to_policy_input(self) -> None:
        pi = build_policy_input_from_gelal_shadow(_envelope())
        assert pi.event_id == "ev-1"
        assert pi.confidence == 0.6
        assert pi.risk_score == 0.2

    def test_no_symbol_venue_strategy_in_policy_input(self) -> None:
        pi = build_policy_input_from_gelal_shadow(_envelope())
        dumped = pi.model_dump()
        for forbidden in ("symbol", "venue", "strategy_name", "opportunity_id"):
            assert forbidden not in dumped

    def test_scope_id_carries_only_hashed_refs(self) -> None:
        pi = build_policy_input_from_gelal_shadow(_envelope())
        assert "BTC-USDT" not in pi.scope_id
        assert "binance" not in pi.scope_id
        assert "latency-arb" not in pi.scope_id

    def test_kill_switch_envelope_flips_input(self) -> None:
        env = _envelope(
            event_id="kill-1",
            event_type=GelAlShadowEventType.KILL_SWITCH_OBSERVED,
            environment="live",
            payload={
                "kill_switch_active": True,
                "source": "operator",
                "observed_by": "gel_al_runtime",
            },
        )
        pi = build_policy_input_from_gelal_shadow(env)
        assert pi.kill_switch_active is True


class TestGelAlPolicyEvaluation:
    def test_high_risk_blocks(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        ring = ObserverRingBuffer(capacity=16)
        env = _envelope(
            event_id="high-risk",
            event_type=GelAlShadowEventType.RISK_GATE_DECISION,
            payload={"confidence": 0.8, "risk_score": 0.95},
        )
        ev = evaluate_gelal_shadow_with_policy(
            envelope=env,
            active_policy_record=_active_policy(),  # type: ignore[arg-type]
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id=env.event_id),
        )
        assert ev.output is SystemOutput.BLOCK

    def test_bad_order_blocks(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        ring = ObserverRingBuffer(capacity=16)
        env = _envelope(
            event_id="bad-1",
            event_type=GelAlShadowEventType.EXECUTION_ATTEMPT_OBSERVED,
            payload={"confidence": 0.5, "bad_order": True, "order_sent": True},
        )
        ev = evaluate_gelal_shadow_with_policy(
            envelope=env,
            active_policy_record=_active_policy(),  # type: ignore[arg-type]
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id=env.event_id),
        )
        assert ev.output is SystemOutput.BLOCK

    def test_kill_switch_active_blocks(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        ring = ObserverRingBuffer(capacity=16)
        env = _envelope(
            event_id="kill-1",
            event_type=GelAlShadowEventType.KILL_SWITCH_OBSERVED,
            environment="live",
            payload={
                "kill_switch_active": True,
                "source": "operator",
                "observed_by": "gel_al_runtime",
            },
        )
        ev = evaluate_gelal_shadow_with_policy(
            envelope=env,
            active_policy_record=_active_policy(),  # type: ignore[arg-type]
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id=env.event_id),
        )
        assert ev.output is SystemOutput.BLOCK

    def test_no_observation_ingested_in_permanent_ledger(self, tmp_path: Path) -> None:
        path = tmp_path / "l.jsonl"
        ledger = JsonlObserverLedger(path)
        ring = ObserverRingBuffer(capacity=16)
        evaluate_gelal_shadow_with_policy(
            envelope=_envelope(),
            active_policy_record=_active_policy(),  # type: ignore[arg-type]
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id="ev-1"),
        )
        content = path.read_text(encoding="utf-8") if path.exists() else ""
        assert "OBSERVATION_INGESTED" not in content

    def test_hash_chain_verifies(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        ring = ObserverRingBuffer(capacity=16)
        evaluate_gelal_shadow_with_policy(
            envelope=_envelope(),
            active_policy_record=_active_policy(),  # type: ignore[arg-type]
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id="ev-1"),
        )
        assert ledger.verify() is True

    def test_no_gelal_write_path(self) -> None:
        from sentinel.integrations import gelal_policy

        src = Path(gelal_policy.__file__).read_text(encoding="utf-8")
        for forbidden in ("redis", "psycopg", "sqlalchemy", "pymongo", "kafka", "boto3"):
            assert f"import {forbidden}" not in src
            assert f"from {forbidden}" not in src


class TestSafetyGreps:
    def test_no_exchange_imports(self) -> None:
        for module_path in (
            Path("sentinel/policy/financial.py"),
            Path("sentinel/policy/record_builder.py"),
            Path("sentinel/policy/store.py"),
            Path("sentinel/policy/write_path.py"),
            Path("sentinel/policy/audit.py"),
            Path("sentinel/policy/evaluator.py"),
            Path("sentinel/integrations/gelal_policy.py"),
            Path("sentinel/runtime/policy_eval.py"),
        ):
            src = module_path.read_text(encoding="utf-8")
            import re

            pattern = re.compile(
                r"^\s*(import|from)\s+("
                r"ccxt|web3|binance|btcturk|pybit|okx|gate_api|kucoin|huobi|"
                r"bitfinex|kraken|openai|anthropic|langchain|requests|httpx|aiohttp"
                r")\b",
                re.MULTILINE,
            )
            assert pattern.findall(src) == [], f"forbidden import in {module_path}"

    def test_no_forbidden_output_literals_in_v6_source(self) -> None:
        for module_path in (
            Path("sentinel/policy/financial.py"),
            Path("sentinel/policy/record_builder.py"),
            Path("sentinel/policy/store.py"),
            Path("sentinel/policy/write_path.py"),
            Path("sentinel/policy/audit.py"),
            Path("sentinel/policy/evaluator.py"),
            Path("sentinel/integrations/gelal_policy.py"),
            Path("sentinel/runtime/policy_eval.py"),
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
                assert literal not in src, f"forbidden literal in {module_path}"

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
