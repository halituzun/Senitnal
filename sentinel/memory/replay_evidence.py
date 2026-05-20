"""V4 — Memory Write Gate integration for replay evidence.

V4 replay produces EVIDENCE PROPOSALS for memory records. These
proposals do NOT bypass the Memory Write Gate; they are simply
candidate-side inputs that a future evidence-axis matrix change
could consume.

In V4 the wrapper:
    - rejects rejected / quarantined / expired records
    - rejects unusable evidence (replay survival without
      min_sessions_satisfied; outcome alignment with stale=True
      or external=False)
    - emits the MEMORY_VERIFICATION_EVIDENCE_PROPOSED audit event
    - does NOT mutate the record's status
    - does NOT call submit_memory_write (the v0.1 MWG remains the
      only path that can flip verified status; V4's evidence
      proposal is purely additive audit, not a write)

The function returns an `AttachReplayEvidenceResult` describing
whether the proposal was accepted (audit emitted) or rejected
(no audit emitted by this wrapper). The MWG continues to be the
sole gate for any actual status change.
"""

from __future__ import annotations

from dataclasses import dataclass

from sentinel.observer.ledger import JsonlObserverLedger  # noqa: TC001 (runtime arg)
from sentinel.replay.audit import emit_memory_verification_evidence_proposed
from sentinel.replay.effects import (
    MemoryEvidenceKind,
    MemoryVerificationEvidenceProposal,
)
from sentinel.replay.outcome_alignment import OutcomeAlignmentEvidence  # noqa: TC001 (runtime arg)
from sentinel.replay.survival import ReplaySurvivalEvidence  # noqa: TC001 (runtime arg)
from sentinel.types.memory import MemoryRecord, MemoryRecordStatus

_REJECTED_STATUSES: frozenset[MemoryRecordStatus] = frozenset(
    {
        MemoryRecordStatus.REJECTED,
        MemoryRecordStatus.EXPIRED,
        MemoryRecordStatus.QUARANTINED,
    }
)


@dataclass(frozen=True, slots=True)
class AttachReplayEvidenceResult:
    """Outcome of an evidence-proposal attempt.

    `accepted` is True only when the wrapper emitted a
    MEMORY_VERIFICATION_EVIDENCE_PROPOSED audit. The store and
    the record are untouched in every case.
    """

    proposal: MemoryVerificationEvidenceProposal
    accepted: bool
    reason: str


def _is_replay_survival_usable(evidence: ReplaySurvivalEvidence) -> bool:
    return evidence.min_sessions_satisfied and evidence.synthetic_only


def _is_outcome_alignment_usable(evidence: OutcomeAlignmentEvidence) -> bool:
    if evidence.stale:
        return False
    return all(ref.external for ref in evidence.outcome_refs)


def submit_replay_survival_evidence(
    *,
    ledger: JsonlObserverLedger,
    record: MemoryRecord,
    evidence: ReplaySurvivalEvidence,
    now_ms: int,
) -> AttachReplayEvidenceResult:
    """Propose a replay-survival evidence attachment for `record`.

    Always returns a result; never mutates the record or store.
    Emits a MEMORY_VERIFICATION_EVIDENCE_PROPOSED audit ONLY when
    the proposal is accepted.
    """
    usable = _is_replay_survival_usable(evidence)
    if record.status in _REJECTED_STATUSES:
        return AttachReplayEvidenceResult(
            proposal=MemoryVerificationEvidenceProposal(
                proposal_id=f"prop-{evidence.evidence_id}",
                session_id=evidence.session_id,
                memory_record_id=record.record_id,
                evidence_kind=MemoryEvidenceKind.REPLAY_SURVIVAL,
                evidence_id=evidence.evidence_id,
                usable_for_gate=usable,
                created_at_ms=now_ms,
            ),
            accepted=False,
            reason=f"record at terminal status {record.status.value!r}; rejected",
        )
    if not usable:
        return AttachReplayEvidenceResult(
            proposal=MemoryVerificationEvidenceProposal(
                proposal_id=f"prop-{evidence.evidence_id}",
                session_id=evidence.session_id,
                memory_record_id=record.record_id,
                evidence_kind=MemoryEvidenceKind.REPLAY_SURVIVAL,
                evidence_id=evidence.evidence_id,
                usable_for_gate=False,
                created_at_ms=now_ms,
            ),
            accepted=False,
            reason="replay survival evidence not usable (min_sessions_satisfied=False)",
        )
    proposal = MemoryVerificationEvidenceProposal(
        proposal_id=f"prop-{evidence.evidence_id}",
        session_id=evidence.session_id,
        memory_record_id=record.record_id,
        evidence_kind=MemoryEvidenceKind.REPLAY_SURVIVAL,
        evidence_id=evidence.evidence_id,
        usable_for_gate=True,
        created_at_ms=now_ms,
    )
    emit_memory_verification_evidence_proposed(ledger, proposal=proposal, now_ms=now_ms)
    return AttachReplayEvidenceResult(
        proposal=proposal,
        accepted=True,
        reason="replay survival evidence proposed (no status change)",
    )


def submit_outcome_alignment_evidence(
    *,
    ledger: JsonlObserverLedger,
    record: MemoryRecord,
    evidence: OutcomeAlignmentEvidence,
    now_ms: int,
) -> AttachReplayEvidenceResult:
    """Propose an outcome-alignment evidence attachment for `record`.

    Always returns a result; never mutates the record or store.
    Emits a MEMORY_VERIFICATION_EVIDENCE_PROPOSED audit ONLY when
    the proposal is accepted (record alive + external + non-stale).
    """
    usable = _is_outcome_alignment_usable(evidence)
    if record.status in _REJECTED_STATUSES:
        return AttachReplayEvidenceResult(
            proposal=MemoryVerificationEvidenceProposal(
                proposal_id=f"prop-{evidence.evidence_id}",
                session_id=evidence.session_id,
                memory_record_id=record.record_id,
                evidence_kind=MemoryEvidenceKind.OUTCOME_ALIGNMENT,
                evidence_id=evidence.evidence_id,
                usable_for_gate=usable,
                created_at_ms=now_ms,
            ),
            accepted=False,
            reason=f"record at terminal status {record.status.value!r}; rejected",
        )
    if not usable:
        return AttachReplayEvidenceResult(
            proposal=MemoryVerificationEvidenceProposal(
                proposal_id=f"prop-{evidence.evidence_id}",
                session_id=evidence.session_id,
                memory_record_id=record.record_id,
                evidence_kind=MemoryEvidenceKind.OUTCOME_ALIGNMENT,
                evidence_id=evidence.evidence_id,
                usable_for_gate=False,
                created_at_ms=now_ms,
            ),
            accepted=False,
            reason=("outcome alignment evidence not usable (stale or non-external refs)"),
        )
    proposal = MemoryVerificationEvidenceProposal(
        proposal_id=f"prop-{evidence.evidence_id}",
        session_id=evidence.session_id,
        memory_record_id=record.record_id,
        evidence_kind=MemoryEvidenceKind.OUTCOME_ALIGNMENT,
        evidence_id=evidence.evidence_id,
        usable_for_gate=True,
        created_at_ms=now_ms,
    )
    emit_memory_verification_evidence_proposed(ledger, proposal=proposal, now_ms=now_ms)
    return AttachReplayEvidenceResult(
        proposal=proposal,
        accepted=True,
        reason="outcome alignment evidence proposed (no status change)",
    )
