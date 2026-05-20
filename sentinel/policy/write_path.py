"""V6 — Financial deontic policy candidate write path.

Submits a candidate DEONTIC_POLICY record through the silent Memory
Write Gate.  This module does not produce VERIFIED or ACTIVE records;
those transitions go through ``InMemoryPolicyStore.activate_verified_policy``
plus the V6 audit helpers.

The gate remains silent: the core path never reads the outcome.
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
from sentinel.observer.ledger import JsonlObserverLedger  # noqa: TC001 (runtime arg)
from sentinel.policy.financial import FinancialDeonticPolicyArtifact  # noqa: TC001 (runtime arg)
from sentinel.policy.record_builder import build_deontic_policy_candidate_record
from sentinel.policy.store import InMemoryPolicyStore  # noqa: TC001 (runtime arg)
from sentinel.types.memory import MemoryRecord, MemoryRecordStatus
from sentinel.types.neural_seed import ProvenanceRef  # noqa: TC001 (runtime arg)


@dataclass(frozen=True, slots=True)
class FinancialPolicyWriteResult:
    """Result of one financial-policy candidate write attempt.

    ``record`` is the candidate as it landed in the store when
    accepted; for REJECTED outcomes ``record`` is the proposed-but-not-
    stored record and ``stored`` is False.
    """

    record: MemoryRecord
    outcome: MemoryWriteOutcome
    stored: bool


def submit_financial_policy_candidate(
    *,
    store: InMemoryPolicyStore,
    ledger: JsonlObserverLedger,
    artifact: FinancialDeonticPolicyArtifact,
    provenance: ProvenanceRef,
    created_at_ms: int,
    evidence_refs: tuple[str, ...],
    rationale: str = "V6 financial deontic policy candidate write",
) -> FinancialPolicyWriteResult:
    """Submit a signed policy artifact as a candidate M2 record.

    The Memory Write Gate evaluates the (subject_class, evidence_axis)
    pair; V6 uses HUMAN_TESTIMONY because deontic policy candidates
    are human-attested signed artifacts.  The gate emits
    MEMORY_RECORD_STATUS_CHANGED audit regardless of outcome; this
    function never escalates beyond CANDIDATE.
    """
    record = build_deontic_policy_candidate_record(
        artifact=artifact,
        provenance=provenance,
        created_at_ms=created_at_ms,
        evidence_refs=evidence_refs,
    )
    request = MemoryWriteRequest(
        record=record,
        evidence_axis=EvidenceAxis.HUMAN_TESTIMONY,
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
        store.add_candidate(record)
        return FinancialPolicyWriteResult(record=record, outcome=outcome, stored=True)
    return FinancialPolicyWriteResult(record=record, outcome=outcome, stored=False)
