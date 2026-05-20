"""V3 — Financial memory candidate write path.

Wraps the v0.1 Memory Write Gate in a discipline-preserving helper
specific to V3 financial payloads. Flow:

    1. build_candidate_financial_memory_record(...)
    2. construct MemoryWriteRequest(requested_status=CANDIDATE, ...)
    3. submit_memory_write(...)
    4. If outcome is ACCEPTED_CANDIDATE or DOWNGRADED_TO_CANDIDATE:
       store.add(final candidate record)
    5. If REJECTED:
       leave store untouched. The gate's M1 audit event already
       records the rejection; the caller may inspect the returned
       outcome.

The gate REMAINS SILENT. The core sees no return value from this
function; only the audit ledger sees the event. V3 callers (e.g.
the financial-memory pipeline runtime) treat this as a fire-and-
audit primitive.
"""

from __future__ import annotations

from dataclasses import dataclass

from sentinel.gates.memory_write import (
    EvidenceAxis,
    MemoryWriteOutcome,
    MemoryWriteRequest,
    MemoryWriteResolution,
    submit_memory_write,
)
from sentinel.memory.builder import build_candidate_financial_memory_record
from sentinel.memory.financial import FinancialPayload  # noqa: TC001 (runtime arg)
from sentinel.memory.store import InMemoryExplicitMemoryStore  # noqa: TC001 (runtime arg)
from sentinel.observer.ledger import JsonlObserverLedger  # noqa: TC001 (runtime arg)
from sentinel.types.memory import MemoryRecord, MemoryRecordStatus
from sentinel.types.neural_seed import ProvenanceRef  # noqa: TC001 (runtime arg)


@dataclass(frozen=True, slots=True)
class FinancialMemoryWriteResult:
    """Result of one financial-memory write attempt.

    `record` is the (candidate-status) MemoryRecord exactly as it
    landed in the store when accepted; for REJECTED outcomes
    `record` is the proposed-but-not-stored MemoryRecord and
    `stored` is False.
    """

    record: MemoryRecord
    outcome: MemoryWriteOutcome
    stored: bool


def submit_financial_memory_candidate(
    *,
    store: InMemoryExplicitMemoryStore,
    ledger: JsonlObserverLedger,
    payload: FinancialPayload,
    provenance: ProvenanceRef,
    created_at_ms: int,
    source_event_ids: tuple[str, ...],
    evidence_axis: EvidenceAxis,
    rationale: str = "V3 financial memory candidate write",
) -> FinancialMemoryWriteResult:
    """Submit a financial memory candidate through the Memory Write Gate.

    Only writes the record into `store` when the gate ACCEPTs or
    DOWNGRADEs to candidate. REJECTED records are NOT stored but
    the M1 audit event from MWG records the rejection. V3 never
    requests VERIFIED status; `requested_status` is fixed to
    CANDIDATE here.
    """
    record = build_candidate_financial_memory_record(
        payload=payload,
        provenance=provenance,
        created_at_ms=created_at_ms,
        source_event_ids=source_event_ids,
    )
    request = MemoryWriteRequest(
        record=record,
        evidence_axis=evidence_axis,
        requested_status=MemoryRecordStatus.CANDIDATE,
        rationale=rationale,
    )
    outcome = submit_memory_write(
        ledger,
        request,
        provenance=provenance,
        now_ms=created_at_ms,
    )
    if outcome.resolution in (
        MemoryWriteResolution.ACCEPTED_CANDIDATE,
        MemoryWriteResolution.DOWNGRADED_TO_CANDIDATE,
    ):
        store.add(record)
        return FinancialMemoryWriteResult(record=record, outcome=outcome, stored=True)
    # REJECTED (or, hypothetically, ACCEPTED_VERIFIED — which MVP
    # never returns).
    return FinancialMemoryWriteResult(record=record, outcome=outcome, stored=False)
