"""V6 — In-memory deontic policy store.

Local / dev / test store for ``MemoryRecord(subject_class=DEONTIC_POLICY)``
records.  Production durable storage is out of V6 scope.

Activation discipline:
    - only ``VERIFIED`` records can activate
    - activation requires ``human_approval_ref``
    - only one ACTIVE policy per scope_id
    - activating a new policy supersedes the previous active policy
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from sentinel.policy.financial import FinancialDeonticPolicyArtifact
from sentinel.types.memory import MemoryRecord, MemoryRecordStatus, SubjectClass


def _scope_id_of(record: MemoryRecord) -> str:
    """Extract scope_id from a deontic_policy record payload."""
    artifact_payload = record.payload
    scope_raw = artifact_payload.get("scope")
    if not isinstance(scope_raw, dict):
        raise ValueError(f"record {record.record_id} payload missing scope dict")
    scope: dict[str, object] = scope_raw  # type: ignore[assignment]
    scope_id_obj = scope.get("scope_id")
    if not isinstance(scope_id_obj, str) or not scope_id_obj:
        raise ValueError(f"record {record.record_id} payload.scope.scope_id missing")
    return scope_id_obj


@dataclass(slots=True)
class _ActivationOutcome:
    """Result of an activate_verified_policy call.

    ``activated_record`` is the freshly active policy; ``superseded_record``
    is the previously active policy in the same scope (or None).
    """

    activated_record: MemoryRecord
    superseded_record: MemoryRecord | None


@dataclass(slots=True)
class InMemoryPolicyStore:
    """In-memory deontic-policy store.

    Only ``DEONTIC_POLICY`` subject_class records are accepted.
    Mutation does not emit M1 audit; callers must route audit through
    ``sentinel.policy.audit`` helpers.
    """

    _records: dict[str, MemoryRecord] = field(default_factory=dict[str, MemoryRecord])
    _active_by_scope: dict[str, str] = field(default_factory=dict[str, str])

    # ------------------------------------------------------------------
    # Read accessors
    # ------------------------------------------------------------------

    def get(self, record_id: str) -> MemoryRecord | None:
        return self._records.get(record_id)

    def list_all(self) -> tuple[MemoryRecord, ...]:
        return tuple(self._records.values())

    def list_by_status(self, status: MemoryRecordStatus) -> tuple[MemoryRecord, ...]:
        return tuple(r for r in self._records.values() if r.status is status)

    def get_active_policy_for_scope_id(self, scope_id: str) -> MemoryRecord | None:
        record_id = self._active_by_scope.get(scope_id)
        if record_id is None:
            return None
        return self._records.get(record_id)

    def get_active_policy_for_scope(
        self,
        scope_id: str,
    ) -> MemoryRecord | None:
        return self.get_active_policy_for_scope_id(scope_id)

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def add_candidate(self, record: MemoryRecord) -> None:
        """Insert a CANDIDATE deontic-policy record.

        Raises:
            ValueError: duplicate record_id, wrong subject_class, or
                non-CANDIDATE status.
        """
        if record.subject_class is not SubjectClass.DEONTIC_POLICY:
            raise ValueError(
                f"InMemoryPolicyStore only accepts DEONTIC_POLICY records; "
                f"got {record.subject_class.value!r}"
            )
        if record.status is not MemoryRecordStatus.CANDIDATE:
            raise ValueError(
                f"InMemoryPolicyStore.add_candidate requires CANDIDATE status; "
                f"got {record.status.value!r}"
            )
        if record.record_id in self._records:
            raise ValueError(f"duplicate record_id {record.record_id!r}")
        self._records[record.record_id] = record

    def add_verified(self, record: MemoryRecord) -> None:
        """Insert a VERIFIED deontic-policy record (test/integration path)."""
        if record.subject_class is not SubjectClass.DEONTIC_POLICY:
            raise ValueError(
                f"InMemoryPolicyStore only accepts DEONTIC_POLICY records; "
                f"got {record.subject_class.value!r}"
            )
        if record.status is not MemoryRecordStatus.VERIFIED:
            raise ValueError(
                f"InMemoryPolicyStore.add_verified requires VERIFIED status; "
                f"got {record.status.value!r}"
            )
        if record.record_id in self._records:
            raise ValueError(f"duplicate record_id {record.record_id!r}")
        self._records[record.record_id] = record

    def activate_verified_policy(
        self,
        *,
        record_id: str,
        human_approval_ref: str,
        now_ms: int,
    ) -> _ActivationOutcome:
        """Promote a VERIFIED record to ACTIVE, superseding any prior active in scope.

        Raises:
            ValueError: record missing, wrong status, missing human approval,
                or scope mismatch.
        """
        if not human_approval_ref:
            raise ValueError("human_approval_ref must be non-empty")
        record = self._records.get(record_id)
        if record is None:
            raise ValueError(f"record_id {record_id!r} not found")
        if record.subject_class is not SubjectClass.DEONTIC_POLICY:
            raise ValueError(f"record {record_id!r} is not a DEONTIC_POLICY record")
        if record.status is not MemoryRecordStatus.VERIFIED:
            raise ValueError(f"only VERIFIED records can activate; got {record.status.value!r}")

        scope_id = _scope_id_of(record)
        previous_record_id = self._active_by_scope.get(scope_id)
        superseded: MemoryRecord | None = None
        if previous_record_id is not None and previous_record_id != record_id:
            prev = self._records[previous_record_id]
            superseded = prev.model_copy(
                update={
                    "status": MemoryRecordStatus.SUPERSEDED,
                    "last_status_change_ms": now_ms,
                }
            )
            self._records[previous_record_id] = superseded

        activated = record.model_copy(
            update={
                "status": MemoryRecordStatus.ACTIVE,
                "last_status_change_ms": now_ms,
            }
        )
        self._records[record_id] = activated
        self._active_by_scope[scope_id] = record_id
        return _ActivationOutcome(activated_record=activated, superseded_record=superseded)

    def revert_to_previous_verified(
        self,
        *,
        from_record_id: str,
        to_previous_record_id: str,
        now_ms: int,
    ) -> _ActivationOutcome:
        """Emergency revert: the currently active policy in scope is superseded
        and the named previously-verified policy is reactivated.

        Validates that the target precedes the current active policy and was
        in the same scope.
        """
        current = self._records.get(from_record_id)
        target = self._records.get(to_previous_record_id)
        if current is None:
            raise ValueError(f"from_record_id {from_record_id!r} not found")
        if target is None:
            raise ValueError(f"to_previous_record_id {to_previous_record_id!r} not found")
        if current.status is not MemoryRecordStatus.ACTIVE:
            raise ValueError("emergency revert requires source to currently be ACTIVE")
        if target.status not in (
            MemoryRecordStatus.VERIFIED,
            MemoryRecordStatus.SUPERSEDED,
        ):
            raise ValueError(
                "emergency revert target must be a previously verified (or superseded) policy"
            )
        if _scope_id_of(current) != _scope_id_of(target):
            raise ValueError("emergency revert target scope mismatch")
        if target.created_at_ms >= current.created_at_ms:
            raise ValueError(
                "emergency revert target must precede the current active policy; "
                "forward-to-new-policy is not permitted via revert"
            )

        scope_id = _scope_id_of(current)
        superseded = current.model_copy(
            update={
                "status": MemoryRecordStatus.SUPERSEDED,
                "last_status_change_ms": now_ms,
            }
        )
        self._records[from_record_id] = superseded

        reactivated = target.model_copy(
            update={
                "status": MemoryRecordStatus.ACTIVE,
                "last_status_change_ms": now_ms,
            }
        )
        self._records[to_previous_record_id] = reactivated
        self._active_by_scope[scope_id] = to_previous_record_id
        return _ActivationOutcome(activated_record=reactivated, superseded_record=superseded)


def parse_artifact_from_record(record: MemoryRecord) -> FinancialDeonticPolicyArtifact:
    """Reconstruct the policy artifact from a deontic_policy record."""
    if record.subject_class is not SubjectClass.DEONTIC_POLICY:
        raise ValueError(f"record {record.record_id!r} is not a DEONTIC_POLICY record")
    # Pydantic accepts dict directly; JSON round-trip ensures tuple fields
    # come back as the right shape.
    return FinancialDeonticPolicyArtifact.model_validate_json(json.dumps(record.payload))
