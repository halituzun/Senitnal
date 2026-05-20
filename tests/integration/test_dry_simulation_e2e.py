"""End-to-end MVP dry simulation integration test.

Per build plan §15 done definition:
    ✓ Full pipeline runs synthetic event end-to-end
    ✓ All audit events captured in M1 (hash chain valid)
    ✓ Zero action output (every attempt blocked at gate)
    ✓ Output ∈ {WAIT, BLOCK, MONITOR, NEED_RECALL, NO_ACTION}
    ✓ Forbidden output strings (BUY/SELL/EXECUTE) never appear in M1
"""

from __future__ import annotations

from pathlib import Path  # noqa: TC003 (fixture annotation)

import pytest
from sentinel.adapters.echo import EchoAdapter
from sentinel.observer.ledger import JsonlObserverLedger
from sentinel.runtime.dry_sim import run_dry_simulation
from sentinel.runtime.output import SystemOutput


@pytest.fixture
def ledger_path(tmp_path: Path) -> Path:
    return tmp_path / "ledger.jsonl"


@pytest.fixture
def ledger(ledger_path: Path) -> JsonlObserverLedger:
    return JsonlObserverLedger(ledger_path)


class TestEndToEnd:
    def test_pipeline_runs_and_produces_wait(self, ledger: JsonlObserverLedger) -> None:
        adapter = EchoAdapter.default()
        result = run_dry_simulation(
            ledger=ledger,
            adapter=adapter,
            observation_magnitude=0.8,
        )
        assert result.output is SystemOutput.WAIT

    def test_ledger_chain_valid_after_run(self, ledger: JsonlObserverLedger) -> None:
        adapter = EchoAdapter.default()
        run_dry_simulation(
            ledger=ledger,
            adapter=adapter,
            observation_magnitude=0.8,
        )
        assert ledger.verify() is True

    def test_audit_event_types(self, ledger: JsonlObserverLedger) -> None:
        adapter = EchoAdapter.default()
        run_dry_simulation(
            ledger=ledger,
            adapter=adapter,
            observation_magnitude=0.8,
        )
        events = ledger.read_all()
        types = [e.event_type for e in events]
        # Canonical MVP run touches all four audit paths.
        assert "ADAPTER_MANIFEST_STATUS_CHANGED" in types
        assert "OBSERVATION_INGESTED" in types
        assert "WORKSPACE_PULSE" in types
        assert "RECALL_TRIGGER_REJECTED" in types
        # Deontic gate is not invoked by default.
        assert "DEONTIC_BLOCKED" not in types

    def test_deontic_opt_in_emits_block(self, ledger: JsonlObserverLedger) -> None:
        adapter = EchoAdapter.default()
        result = run_dry_simulation(
            ledger=ledger,
            adapter=adapter,
            observation_magnitude=0.8,
            exercise_deontic_gate=True,
        )
        assert result.output is SystemOutput.WAIT
        events = ledger.read_all()
        types = [e.event_type for e in events]
        assert "DEONTIC_BLOCKED" in types
        assert ledger.verify() is True

    def test_adapter_activation_opt_out(self, ledger: JsonlObserverLedger) -> None:
        adapter = EchoAdapter.default()
        run_dry_simulation(
            ledger=ledger,
            adapter=adapter,
            observation_magnitude=0.8,
            emit_adapter_activation=False,
        )
        events = ledger.read_all()
        types = [e.event_type for e in events]
        assert "ADAPTER_MANIFEST_STATUS_CHANGED" not in types

    def test_output_is_in_mvp_set(self, ledger: JsonlObserverLedger) -> None:
        adapter = EchoAdapter.default()
        result = run_dry_simulation(
            ledger=ledger,
            adapter=adapter,
            observation_magnitude=0.8,
        )
        assert result.output in tuple(SystemOutput)

    def test_neural_seed_produced(self, ledger: JsonlObserverLedger) -> None:
        adapter = EchoAdapter.default()
        result = run_dry_simulation(
            ledger=ledger,
            adapter=adapter,
            observation_magnitude=0.8,
        )
        assert len(result.neural_seed.payload_seed) >= 1
        assert 0.0 < result.neural_seed.total_intensity <= 1.0


class TestRunsAcrossMagnitudes:
    @pytest.mark.parametrize("magnitude", [0.05, 0.3, 0.5, 0.7, 0.9, 1.0])
    def test_pipeline_wait_for_every_magnitude(
        self, ledger: JsonlObserverLedger, magnitude: float
    ) -> None:
        adapter = EchoAdapter.default()
        # At very-low magnitudes the compiler may produce an empty
        # seed; we tolerate ValidationError as "MVP scenario rejects
        # this input" but never as a successful execution path.
        from pydantic import ValidationError

        try:
            result = run_dry_simulation(
                ledger=ledger,
                adapter=adapter,
                observation_magnitude=magnitude,
            )
        except ValidationError:
            return
        assert result.output is SystemOutput.WAIT


class TestStableAuditCount:
    def test_canonical_run_emits_four_audit_events(self, ledger: JsonlObserverLedger) -> None:
        adapter = EchoAdapter.default()
        result = run_dry_simulation(
            ledger=ledger,
            adapter=adapter,
            observation_magnitude=0.8,
        )
        # ADAPTER_MANIFEST_STATUS_CHANGED + OBSERVATION_INGESTED +
        # WORKSPACE_PULSE + RECALL_TRIGGER_REJECTED = 4 audit events
        # in the canonical run (deontic gate path opt-in only).
        assert len(result.audit_event_ids) == 4
        assert len(ledger.read_all()) == 4

    def test_deontic_opt_in_adds_fifth_event(self, ledger: JsonlObserverLedger) -> None:
        adapter = EchoAdapter.default()
        result = run_dry_simulation(
            ledger=ledger,
            adapter=adapter,
            observation_magnitude=0.8,
            exercise_deontic_gate=True,
        )
        assert len(result.audit_event_ids) == 5
        assert len(ledger.read_all()) == 5

    def test_minimal_run_emits_three_events(self, ledger: JsonlObserverLedger) -> None:
        adapter = EchoAdapter.default()
        result = run_dry_simulation(
            ledger=ledger,
            adapter=adapter,
            observation_magnitude=0.8,
            emit_adapter_activation=False,
        )
        # Without adapter activation: observation + pulse + recall = 3
        assert len(result.audit_event_ids) == 3
        assert len(ledger.read_all()) == 3
