"""V6 — Deontic policy MemoryRecord candidate builder.

Builds a CANDIDATE-status M2 record carrying the signed policy
artifact as its payload.  This function never returns a record at
VERIFIED or ACTIVE status — those transitions go through MWG +
``InMemoryPolicyStore.activate_verified_policy``.
"""

from __future__ import annotations

from sentinel.policy.financial import FinancialDeonticPolicyArtifact  # noqa: TC001 (runtime arg)
from sentinel.types.memory import MemoryRecord, MemoryRecordStatus, SubjectClass
from sentinel.types.neural_seed import ProvenanceRef  # noqa: TC001 (runtime arg)


def build_deontic_policy_candidate_record(
    *,
    artifact: FinancialDeonticPolicyArtifact,
    provenance: ProvenanceRef,
    created_at_ms: int,
    evidence_refs: tuple[str, ...],
) -> MemoryRecord:
    """Construct a CANDIDATE deontic_policy MemoryRecord."""
    return MemoryRecord(
        record_id=f"policy-{artifact.artifact_id}",
        subject_class=SubjectClass.DEONTIC_POLICY,
        payload=artifact.model_dump(mode="json"),
        status=MemoryRecordStatus.CANDIDATE,
        provenance=provenance,
        causal_refs=evidence_refs,
        external_corroboration_refs=evidence_refs,
        internal_only_refs=(),
        created_at_ms=created_at_ms,
        last_status_change_ms=created_at_ms,
    )
