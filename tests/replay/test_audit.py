"""V4 — Replay audit emitter tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from sentinel.constitution.violations import ConstitutionalViolation
from sentinel.observer.ledger import JsonlObserverLedger
from sentinel.replay.audit import (
    emit_attention_replay_habituation_update,
    emit_ingress_calibration_updated,
    emit_memory_verification_evidence_proposed,
    emit_replay_session_status_changed,
    emit_sleep_replay_synapse_update,
)
from sentinel.replay.effects import (
    AttentionHabituationUpdate,
    IngressCalibrationUpdateProposal,
    MemoryEvidenceKind,
    MemoryVerificationEvidenceProposal,
    SleepSynapseUpdateProposal,
    SynapseDirection,
)
from sentinel.replay.session import (
    ReplayEffectChannel,
    ReplayInputSnapshot,
    ReplayPurpose,
    ReplaySession,
    ReplaySessionStatus,
)
from sentinel.types.neural_seed import ProvenanceRef

if TYPE_CHECKING:
    from pathlib import Path


def _session() -> ReplaySession:
    return ReplaySession(
        session_id="s-1",
        purpose=ReplayPurpose.MEMORY_VERIFICATION,
        status=ReplaySessionStatus.RUNNING,
        input_snapshot=ReplayInputSnapshot(
            snapshot_id="snap-1",
            source_m1_event_ids=("ev-1",),
            created_at_ms=0,
            provenance_ref=ProvenanceRef(source_event_id="ev-1"),
            hash_ref="sha256:snap-1",
        ),
        started_at_ms=0,
        budget_ref="b-1",
        sandbox_id="sandbox-1",
        effect_channels_requested=(ReplayEffectChannel.AUDIT_ONLY,),
    )


class TestReplayAuditEmitters:
    def test_session_status_emitted(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        ev = emit_replay_session_status_changed(
            ledger, session=_session(), reason="V4 test", now_ms=1
        )
        assert ev.event_type == "REPLAY_SESSION_STATUS_CHANGED"
        assert ev.event_family.value == "replay"

    def test_session_status_rejects_forbidden_literal(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        with pytest.raises(ConstitutionalViolation):
            emit_replay_session_status_changed(
                ledger, session=_session(), reason="reason BUY here", now_ms=1
            )

    def test_sleep_synapse_emitted(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        proposal = SleepSynapseUpdateProposal(
            proposal_id="p1",
            session_id="s1",
            synapse_id="syn-1",
            direction=SynapseDirection.STRENGTHENING,
            delta=0.1,
            capped_delta=0.05,
            eligibility_trace_id="trace-1",
            evidence_ref="ev-1",
            created_at_ms=0,
        )
        ev = emit_sleep_replay_synapse_update(ledger, proposal=proposal, now_ms=1)
        assert ev.event_type == "SLEEP_REPLAY_SYNAPSE_UPDATE"
        assert ev.event_family.value == "replay"

    def test_attention_habituation_emitted(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        update = AttentionHabituationUpdate(
            update_id="u1",
            session_id="s1",
            assembly_id="asm-1",
            context_signature_hash="sha256:ctx",
            habituation_delta=0.1,
            capped_delta=0.05,
            created_at_ms=0,
        )
        ev = emit_attention_replay_habituation_update(ledger, update=update, now_ms=1)
        assert ev.event_type == "ATTENTION_REPLAY_HABITUATION_UPDATE"

    def test_ingress_calibration_emitted(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        proposal = IngressCalibrationUpdateProposal(
            proposal_id="p1",
            session_id="s1",
            mapping_id="map-1",
            delta=0.05,
            capped_delta=0.04,
            daily_cap_ref=0.1,
            created_at_ms=0,
        )
        ev = emit_ingress_calibration_updated(ledger, proposal=proposal, now_ms=1)
        assert ev.event_type == "INGRESS_CALIBRATION_UPDATED"

    def test_memory_evidence_emitted(self, tmp_path: Path) -> None:
        ledger = JsonlObserverLedger(tmp_path / "l.jsonl")
        proposal = MemoryVerificationEvidenceProposal(
            proposal_id="p1",
            session_id="s1",
            memory_record_id="m1",
            evidence_kind=MemoryEvidenceKind.REPLAY_SURVIVAL,
            evidence_id="e1",
            usable_for_gate=True,
            created_at_ms=0,
        )
        ev = emit_memory_verification_evidence_proposed(ledger, proposal=proposal, now_ms=1)
        assert ev.event_type == "MEMORY_VERIFICATION_EVIDENCE_PROPOSED"
        assert ev.event_family.value == "memory"
