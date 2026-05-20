"""V4 — Replay audit emitters.

Each emitter constructs an ObserverEvent for one of the canonical
catalog rows and appends it to the JSONL ledger directly (these
events are PERMANENT per catalog, so they bypass the router's
ring-only path by design). Caller MUST hand a real ledger; the
emitters never accept simulated events.

All reason strings pass through `assert_no_forbidden_literal` so
execution verbs cannot leak from a replay audit payload.
"""

from __future__ import annotations

from sentinel.observer.hash_chain import placeholder_event_hash
from sentinel.observer.ledger import JsonlObserverLedger  # noqa: TC001 (runtime)
from sentinel.replay.effects import (
    AttentionHabituationUpdate,  # noqa: TC001 (runtime arg)
    IngressCalibrationUpdateProposal,  # noqa: TC001 (runtime arg)
    MemoryVerificationEvidenceProposal,  # noqa: TC001 (runtime arg)
    SleepSynapseUpdateProposal,  # noqa: TC001 (runtime arg)
)
from sentinel.replay.session import ReplaySession  # noqa: TC001 (runtime arg)
from sentinel.runtime.output import assert_no_forbidden_literal
from sentinel.types.neural_seed import ProvenanceRef
from sentinel.types.observer import EventFamily, ObserverEvent


def emit_replay_session_status_changed(
    ledger: JsonlObserverLedger,
    *,
    session: ReplaySession,
    reason: str,
    now_ms: int,
) -> ObserverEvent:
    """Append a REPLAY_SESSION_STATUS_CHANGED audit entry."""
    assert_no_forbidden_literal(reason)
    return ledger.append(
        ObserverEvent(
            event_id=f"replay-status-{session.session_id}-{session.status.value}",
            event_family=EventFamily.REPLAY,
            event_type="REPLAY_SESSION_STATUS_CHANGED",
            occurred_at_ms=now_ms,
            payload={
                "session_id": session.session_id,
                "purpose": session.purpose.value,
                "status": session.status.value,
                "sandbox_id": session.sandbox_id,
                "effect_channels_requested": [c.value for c in session.effect_channels_requested],
                "effect_channels_applied": [c.value for c in session.effect_channels_applied],
                "reason": reason,
            },
            provenance=ProvenanceRef(source_event_id=session.session_id),
            previous_event_hash=None,
            event_hash=placeholder_event_hash(),
        )
    )


def emit_sleep_replay_synapse_update(
    ledger: JsonlObserverLedger,
    *,
    proposal: SleepSynapseUpdateProposal,
    now_ms: int,
) -> ObserverEvent:
    """Append a SLEEP_REPLAY_SYNAPSE_UPDATE audit entry."""
    return ledger.append(
        ObserverEvent(
            event_id=f"sleep-replay-{proposal.proposal_id}",
            event_family=EventFamily.REPLAY,
            event_type="SLEEP_REPLAY_SYNAPSE_UPDATE",
            occurred_at_ms=now_ms,
            payload={
                "proposal_id": proposal.proposal_id,
                "session_id": proposal.session_id,
                "synapse_id": proposal.synapse_id,
                "direction": proposal.direction.value,
                "delta": proposal.delta,
                "capped_delta": proposal.capped_delta,
                "eligibility_trace_id": proposal.eligibility_trace_id,
                "evidence_ref": proposal.evidence_ref,
            },
            provenance=ProvenanceRef(source_event_id=proposal.session_id),
            previous_event_hash=None,
            event_hash=placeholder_event_hash(),
        )
    )


def emit_attention_replay_habituation_update(
    ledger: JsonlObserverLedger,
    *,
    update: AttentionHabituationUpdate,
    now_ms: int,
) -> ObserverEvent:
    """Append an ATTENTION_REPLAY_HABITUATION_UPDATE audit entry."""
    return ledger.append(
        ObserverEvent(
            event_id=f"attn-habituation-{update.update_id}",
            event_family=EventFamily.REPLAY,
            event_type="ATTENTION_REPLAY_HABITUATION_UPDATE",
            occurred_at_ms=now_ms,
            payload={
                "update_id": update.update_id,
                "session_id": update.session_id,
                "assembly_id": update.assembly_id,
                "context_signature_hash": update.context_signature_hash,
                "habituation_delta": update.habituation_delta,
                "capped_delta": update.capped_delta,
            },
            provenance=ProvenanceRef(source_event_id=update.session_id),
            previous_event_hash=None,
            event_hash=placeholder_event_hash(),
        )
    )


def emit_ingress_calibration_updated(
    ledger: JsonlObserverLedger,
    *,
    proposal: IngressCalibrationUpdateProposal,
    now_ms: int,
) -> ObserverEvent:
    """Append an INGRESS_CALIBRATION_UPDATED audit entry."""
    return ledger.append(
        ObserverEvent(
            event_id=f"ingress-calib-{proposal.proposal_id}",
            event_family=EventFamily.REPLAY,
            event_type="INGRESS_CALIBRATION_UPDATED",
            occurred_at_ms=now_ms,
            payload={
                "proposal_id": proposal.proposal_id,
                "session_id": proposal.session_id,
                "mapping_id": proposal.mapping_id,
                "delta": proposal.delta,
                "capped_delta": proposal.capped_delta,
                "daily_cap_ref": proposal.daily_cap_ref,
            },
            provenance=ProvenanceRef(source_event_id=proposal.session_id),
            previous_event_hash=None,
            event_hash=placeholder_event_hash(),
        )
    )


def emit_memory_verification_evidence_proposed(
    ledger: JsonlObserverLedger,
    *,
    proposal: MemoryVerificationEvidenceProposal,
    now_ms: int,
) -> ObserverEvent:
    """Append a MEMORY_VERIFICATION_EVIDENCE_PROPOSED audit entry.

    This event is FAMILY=memory (the proposal concerns a memory
    record). It does NOT actually mutate the record; the Memory
    Write Gate remains the only path that can change verified
    status.
    """
    return ledger.append(
        ObserverEvent(
            event_id=f"mem-evidence-{proposal.proposal_id}",
            event_family=EventFamily.MEMORY,
            event_type="MEMORY_VERIFICATION_EVIDENCE_PROPOSED",
            occurred_at_ms=now_ms,
            payload={
                "proposal_id": proposal.proposal_id,
                "session_id": proposal.session_id,
                "memory_record_id": proposal.memory_record_id,
                "evidence_kind": proposal.evidence_kind.value,
                "evidence_id": proposal.evidence_id,
                "usable_for_gate": proposal.usable_for_gate,
            },
            provenance=ProvenanceRef(source_event_id=proposal.session_id),
            previous_event_hash=None,
            event_hash=placeholder_event_hash(),
        )
    )
