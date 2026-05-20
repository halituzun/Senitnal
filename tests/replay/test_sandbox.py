"""V4 — Replay sandbox tests."""

from __future__ import annotations

import pytest
from sentinel.replay.sandbox import (
    ReplaySandbox,
    ReplaySandboxResult,
    SimulatedEvent,
    run_in_sandbox,
)
from sentinel.replay.session import (
    ReplayEffectChannel,
    ReplayInputSnapshot,
    ReplayPurpose,
    ReplaySession,
    ReplaySessionStatus,
)
from sentinel.types.neural_seed import ProvenanceRef


def _session() -> ReplaySession:
    return ReplaySession(
        session_id="s-1",
        purpose=ReplayPurpose.COUNTERFACTUAL_ABLATION,
        status=ReplaySessionStatus.RUNNING,
        input_snapshot=ReplayInputSnapshot(
            snapshot_id="snap-1",
            source_m1_event_ids=("ev-1",),
            created_at_ms=0,
            provenance_ref=ProvenanceRef(source_event_id="ev-1"),
            hash_ref="sha256:x",
        ),
        started_at_ms=0,
        budget_ref="b-1",
        sandbox_id="sandbox-1",
        effect_channels_requested=(ReplayEffectChannel.AUDIT_ONLY,),
    )


class TestSimulatedEvent:
    def test_replay_simulated_must_be_true(self) -> None:
        with pytest.raises(ValueError, match="replay_simulated"):
            SimulatedEvent(
                simulated_event_id="e1",
                kind="probe",
                payload={"x": 1},
                replay_simulated=False,
            )


class TestSandbox:
    def test_empty_sandbox_accepts(self) -> None:
        sandbox = ReplaySandbox(
            sandbox_id="sandbox-1",
            session_id="s-1",
            source_snapshot_hash="sha256:x",
        )
        result = run_in_sandbox(session=_session(), sandbox=sandbox)
        assert result.simulated_event_count == 0
        assert result.produced_live_event_count == 0
        assert result.produced_action_count == 0
        assert result.produced_memory_write_count == 0

    def test_with_simulated_events(self) -> None:
        sim_events = (
            SimulatedEvent(simulated_event_id="se-1", kind="probe", payload={"x": 1}),
            SimulatedEvent(simulated_event_id="se-2", kind="probe", payload={"x": 2}),
        )
        sandbox = ReplaySandbox(
            sandbox_id="sandbox-1",
            session_id="s-1",
            source_snapshot_hash="sha256:x",
            simulated_events=sim_events,
        )
        result = run_in_sandbox(session=_session(), sandbox=sandbox)
        assert result.simulated_event_count == 2

    def test_live_event_count_nonzero_rejected(self) -> None:
        with pytest.raises(ValueError, match="produced_live_event_count"):
            ReplaySandboxResult(
                sandbox_id="s",
                session_id="t",
                simulated_event_count=1,
                produced_live_event_count=1,
                produced_action_count=0,
                produced_memory_write_count=0,
            )

    def test_action_count_nonzero_rejected(self) -> None:
        with pytest.raises(ValueError, match="produced_action_count"):
            ReplaySandboxResult(
                sandbox_id="s",
                session_id="t",
                simulated_event_count=1,
                produced_live_event_count=0,
                produced_action_count=1,
                produced_memory_write_count=0,
            )

    def test_memory_write_count_nonzero_rejected(self) -> None:
        with pytest.raises(ValueError, match="produced_memory_write_count"):
            ReplaySandboxResult(
                sandbox_id="s",
                session_id="t",
                simulated_event_count=1,
                produced_live_event_count=0,
                produced_action_count=0,
                produced_memory_write_count=1,
            )
