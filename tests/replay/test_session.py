"""V4 — Replay session schema tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sentinel.replay.session import (
    ReplayEffectChannel,
    ReplayInputSnapshot,
    ReplayPurpose,
    ReplaySession,
    ReplaySessionStatus,
)
from sentinel.types.neural_seed import ProvenanceRef


def _snap() -> ReplayInputSnapshot:
    return ReplayInputSnapshot(
        snapshot_id="snap-1",
        source_m1_event_ids=("ev-1",),
        created_at_ms=0,
        provenance_ref=ProvenanceRef(source_event_id="ev-1"),
        hash_ref="sha256:snap-1",
    )


def _session(**kw: object) -> ReplaySession:
    defaults: dict[str, object] = {
        "session_id": "s-1",
        "purpose": ReplayPurpose.MEMORY_VERIFICATION,
        "status": ReplaySessionStatus.PENDING,
        "input_snapshot": _snap(),
        "started_at_ms": 0,
        "budget_ref": "b-1",
        "sandbox_id": "sandbox-1",
        "effect_channels_requested": (ReplayEffectChannel.MEMORY_VERIFICATION_EVIDENCE,),
    }
    defaults.update(kw)
    return ReplaySession(**defaults)  # type: ignore[arg-type]


class TestSnapshot:
    def test_valid_accepted(self) -> None:
        _snap()

    def test_no_source_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ReplayInputSnapshot(
                snapshot_id="x",
                created_at_ms=0,
                provenance_ref=ProvenanceRef(source_event_id="ev"),
                hash_ref="sha256:x",
            )

    def test_empty_source_string_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ReplayInputSnapshot(
                snapshot_id="x",
                source_m1_event_ids=("ev-1", ""),
                created_at_ms=0,
                provenance_ref=ProvenanceRef(source_event_id="ev"),
                hash_ref="sha256:x",
            )


class TestSession:
    def test_valid_pending_accepted(self) -> None:
        _session()

    def test_completed_without_completed_at_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _session(status=ReplaySessionStatus.COMPLETED)

    def test_applied_must_subset_requested(self) -> None:
        with pytest.raises(ValidationError):
            _session(
                effect_channels_applied=(ReplayEffectChannel.SLEEP_SYNAPSE_UPDATE,),
            )

    def test_completed_at_before_started_at_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _session(
                status=ReplaySessionStatus.COMPLETED,
                started_at_ms=10,
                completed_at_ms=5,
            )

    def test_no_live_core_route_field(self) -> None:
        with pytest.raises(ValidationError):
            _session(live_core_route=True)

    def test_no_execution_field(self) -> None:
        with pytest.raises(ValidationError):
            _session(execution_enabled=True)

    def test_frozen(self) -> None:
        s = _session()
        with pytest.raises(ValidationError):
            s.session_id = "other"  # type: ignore[misc]
