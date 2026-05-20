"""Memory Write Gate — silent gate, candidate-only writes in MVP.

Per MEMORY_WRITE_GATE.md §4-§8 and the Phase 7 build plan: the
Memory Write Gate is the **only** path through which a candidate
memory record reaches M2. It is *silent* — there is no core-facing
return signal from a write attempt. The only output is an audit
event (`MEMORY_RECORD_STATUS_CHANGED`) appended to the M1 ledger.

In MVP every accepted candidate is written at status
`CANDIDATE` (no verified production). The verified path requires
`mvp_verified_disabled = False` AND a positive evidence-axis match;
both are off by default.

Constitutional discipline:
    - Silent: the gate returns a `MemoryWriteOutcome` for caller
      observability, but the core path NEVER reads this — caller
      contract is "fire-and-audit". The outcome is for tests +
      the integration layer
    - Candidate-only: when mvp_verified_disabled is True, a request
      asking for status=VERIFIED is downgraded to CANDIDATE with
      reason recorded; ACCEPTED at CANDIDATE
    - Subject-class x evidence_axis matrix (G §8) — MVP uses a
      conservative whitelist of (subject_class, evidence_axis)
      pairs that are accepted at all. Anything outside the
      whitelist is REJECTED
    - Every outcome — ACCEPTED at candidate, DOWNGRADED, REJECTED
      — produces a corresponding observer event in the ledger
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from sentinel.observer.hash_chain import placeholder_event_hash
from sentinel.observer.ledger import JsonlObserverLedger  # noqa: TC001 (runtime)
from sentinel.runtime.feature_flags import get_flag
from sentinel.types.memory import (
    MemoryRecord,
    MemoryRecordStatus,
    SubjectClass,
)
from sentinel.types.neural_seed import ProvenanceRef  # noqa: TC001 (runtime)
from sentinel.types.observer import EventFamily, ObserverEvent


class EvidenceAxis(StrEnum):
    """Closed set of evidence axes (MVP working subset of G §8)."""

    DIRECT_OBSERVATION = "direct_observation"
    HUMAN_TESTIMONY = "human_testimony"
    INTERNAL_INFERENCE = "internal_inference"
    REPLAY_CONFIRMED = "replay_confirmed"


class MemoryWriteResolution(StrEnum):
    """Outcome of one memory-write attempt."""

    ACCEPTED_CANDIDATE = "accepted_candidate"
    ACCEPTED_VERIFIED = "accepted_verified"  # MVP never returns this
    DOWNGRADED_TO_CANDIDATE = "downgraded_to_candidate"
    REJECTED = "rejected"


# MVP whitelist: (subject_class, evidence_axis) pairs accepted at all.
# Anything outside this set is REJECTED.
_MVP_ACCEPTED_PAIRS: frozenset[tuple[SubjectClass, EvidenceAxis]] = frozenset(
    {
        (SubjectClass.SOURCE_TRUST, EvidenceAxis.DIRECT_OBSERVATION),
        (SubjectClass.SOURCE_TRUST, EvidenceAxis.HUMAN_TESTIMONY),
        (SubjectClass.PROCEDURAL, EvidenceAxis.INTERNAL_INFERENCE),
        (SubjectClass.PROCEDURAL, EvidenceAxis.HUMAN_TESTIMONY),
        (SubjectClass.EPISODIC, EvidenceAxis.INTERNAL_INFERENCE),
        (SubjectClass.INCIDENT_HUMAN_RECORD, EvidenceAxis.HUMAN_TESTIMONY),
    }
)


@dataclass(frozen=True, slots=True)
class MemoryWriteRequest:
    """One candidate memory-write request presented to the gate."""

    record: MemoryRecord
    evidence_axis: EvidenceAxis
    requested_status: MemoryRecordStatus
    rationale: str

    def __post_init__(self) -> None:
        if self.requested_status not in (
            MemoryRecordStatus.CANDIDATE,
            MemoryRecordStatus.VERIFIED,
        ):
            raise ValueError(
                "MemoryWriteRequest.requested_status must be CANDIDATE or "
                f"VERIFIED at the gate boundary; got {self.requested_status!r}"
            )
        if self.rationale == "":
            raise ValueError("MemoryWriteRequest.rationale must be non-empty")


@dataclass(frozen=True, slots=True)
class MemoryWriteOutcome:
    """Gate outcome (not returned to core; consumed by audit / tests)."""

    record_id: str
    resolution: MemoryWriteResolution
    final_status: MemoryRecordStatus | None
    reason: str


def submit_memory_write(
    ledger: JsonlObserverLedger,
    request: MemoryWriteRequest,
    *,
    provenance: ProvenanceRef,
    now_ms: int,
) -> MemoryWriteOutcome:
    """Run the silent Memory Write Gate.

    Steps:
        1. Pair (subject_class, evidence_axis) not in the MVP whitelist
           → REJECTED, audit event emitted with new_status=REJECTED.
        2. requested_status == VERIFIED and mvp_verified_disabled is
           True → DOWNGRADED_TO_CANDIDATE.
        3. Otherwise → ACCEPTED_CANDIDATE.

    Returns a `MemoryWriteOutcome`. The core MUST NOT read this
    outcome; it is for the audit / integration layer.
    """
    pair = (request.record.subject_class, request.evidence_axis)
    if pair not in _MVP_ACCEPTED_PAIRS:
        outcome = MemoryWriteOutcome(
            record_id=request.record.record_id,
            resolution=MemoryWriteResolution.REJECTED,
            final_status=None,
            reason=(
                f"(subject_class={request.record.subject_class.value!r}, "
                f"evidence_axis={request.evidence_axis.value!r}) not in "
                "MVP accepted pair whitelist"
            ),
        )
        _emit_status_changed(
            ledger=ledger,
            request=request,
            provenance=provenance,
            now_ms=now_ms,
            new_status_value="rejected",
            reason=outcome.reason,
        )
        return outcome

    if request.requested_status is MemoryRecordStatus.VERIFIED and get_flag(
        "mvp_verified_disabled"
    ):
        outcome = MemoryWriteOutcome(
            record_id=request.record.record_id,
            resolution=MemoryWriteResolution.DOWNGRADED_TO_CANDIDATE,
            final_status=MemoryRecordStatus.CANDIDATE,
            reason=(
                "VERIFIED requested but mvp_verified_disabled is True; "
                "downgraded to CANDIDATE"
            ),
        )
        _emit_status_changed(
            ledger=ledger,
            request=request,
            provenance=provenance,
            now_ms=now_ms,
            new_status_value="candidate",
            reason=outcome.reason,
        )
        return outcome
    # Future path: mvp_verified_disabled OFF + acceptance criteria
    # validated → ACCEPTED_VERIFIED. Out of MVP scope.

    outcome = MemoryWriteOutcome(
        record_id=request.record.record_id,
        resolution=MemoryWriteResolution.ACCEPTED_CANDIDATE,
        final_status=MemoryRecordStatus.CANDIDATE,
        reason="MVP candidate-only write accepted",
    )
    _emit_status_changed(
        ledger=ledger,
        request=request,
        provenance=provenance,
        now_ms=now_ms,
        new_status_value="candidate",
        reason=outcome.reason,
    )
    return outcome


def _emit_status_changed(
    *,
    ledger: JsonlObserverLedger,
    request: MemoryWriteRequest,
    provenance: ProvenanceRef,
    now_ms: int,
    new_status_value: str,
    reason: str,
) -> ObserverEvent:
    return ledger.append(
        ObserverEvent(
            event_id=f"mwg-{request.record.record_id}",
            event_family=EventFamily.MEMORY,
            event_type="MEMORY_RECORD_STATUS_CHANGED",
            occurred_at_ms=now_ms,
            payload={
                "record_id": request.record.record_id,
                "subject_class": request.record.subject_class.value,
                "evidence_axis": request.evidence_axis.value,
                "requested_status": request.requested_status.value,
                "new_status": new_status_value,
                "reason": reason,
            },
            provenance=provenance,
            previous_event_hash=None,
            event_hash=placeholder_event_hash(),
        )
    )
