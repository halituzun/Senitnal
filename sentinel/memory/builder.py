"""V3 — Candidate financial memory record builder.

This module provides a single function that constructs a
MemoryRecord at status=CANDIDATE from a financial payload. The
function NEVER produces a verified record; the MVP Memory Write
Gate is the only path to a stored record, and the v0.1 contract
keeps verified production behind `mvp_verified_disabled = True`.
"""

from __future__ import annotations

from sentinel.memory.financial import FinancialPayload, financial_payload_subject_class
from sentinel.types.memory import MemoryRecord, MemoryRecordStatus
from sentinel.types.neural_seed import ProvenanceRef  # noqa: TC001 (Pydantic runtime needs)


def build_candidate_financial_memory_record(
    *,
    payload: FinancialPayload,
    provenance: ProvenanceRef,
    created_at_ms: int,
    source_event_ids: tuple[str, ...],
) -> MemoryRecord:
    """Build a candidate MemoryRecord from a financial payload.

    The status is unconditionally CANDIDATE. The subject_class is
    derived from `financial_payload_subject_class(payload)` using
    only existing v0.1 SubjectClass values.

    `source_event_ids` is recorded as both `causal_refs` (upstream
    causal chain) and `external_corroboration_refs` (these refs come
    from ObservationEvent / observer events, which are external
    corroboration by definition). `internal_only_refs` stays empty.
    """
    if created_at_ms < 0:
        raise ValueError("created_at_ms must be >= 0")
    if not source_event_ids:
        raise ValueError("source_event_ids must be non-empty")
    for sid in source_event_ids:
        if not sid:
            raise ValueError("source_event_ids entries must be non-empty")

    record_id = f"fin-{type(payload).__name__}-{payload.record_key}"
    subject_class = financial_payload_subject_class(payload)

    return MemoryRecord(
        record_id=record_id,
        subject_class=subject_class,
        payload=payload.model_dump(mode="json"),
        status=MemoryRecordStatus.CANDIDATE,
        provenance=provenance,
        causal_refs=source_event_ids,
        external_corroboration_refs=source_event_ids,
        internal_only_refs=(),
        created_at_ms=created_at_ms,
        last_status_change_ms=created_at_ms,
    )
