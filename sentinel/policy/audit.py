"""V6 — Deontic policy status / revert audit helpers.

Emits ``MEMORY_RECORD_STATUS_CHANGED`` events for policy status
transitions handled by ``InMemoryPolicyStore``.  No new catalog row
is added — V6 reuses the existing M2 status-change row.

Constitutional discipline:
    - Reason strings pass ``assert_no_forbidden_literal``.
    - Emergency revert may only target a previously verified policy.
"""

from __future__ import annotations

from sentinel.observer.hash_chain import placeholder_event_hash
from sentinel.observer.ledger import JsonlObserverLedger  # noqa: TC001 (runtime arg)
from sentinel.runtime.output import assert_no_forbidden_literal
from sentinel.types.neural_seed import ProvenanceRef
from sentinel.types.observer import EventFamily, ObserverEvent


def emit_deontic_policy_status_changed(
    *,
    ledger: JsonlObserverLedger,
    policy_record_id: str,
    policy_id: str,
    old_status: str,
    new_status: str,
    trigger: str,
    approved_by: str | None,
    memory_write_gate_pass_ref: str | None,
    previous_active_policy_ref: str | None,
    evidence_refs: tuple[str, ...],
    reason: str,
    now_ms: int,
) -> ObserverEvent:
    """Emit a status-change audit event for a deontic policy record.

    ``new_status`` and ``old_status`` are the M2 ``MemoryRecordStatus``
    string values (``candidate``, ``verified``, ``active``,
    ``superseded``, …).
    """
    assert_no_forbidden_literal(reason)
    assert_no_forbidden_literal(trigger)
    return ledger.append(
        ObserverEvent(
            event_id=f"policy-status-{policy_record_id}-{now_ms}",
            event_family=EventFamily.MEMORY,
            event_type="MEMORY_RECORD_STATUS_CHANGED",
            occurred_at_ms=now_ms,
            payload={
                "record_id": policy_record_id,
                "policy_id": policy_id,
                "subject_class": "deontic_policy",
                "evidence_axis": "human_testimony",
                "requested_status": new_status,
                "new_status": new_status,
                "old_status": old_status,
                "trigger": trigger,
                "approved_by": approved_by,
                "memory_write_gate_pass_ref": memory_write_gate_pass_ref,
                "previous_active_policy_ref": previous_active_policy_ref,
                "evidence_refs": list(evidence_refs),
                "reason": reason,
            },
            provenance=ProvenanceRef(source_event_id=policy_record_id),
            previous_event_hash=None,
            event_hash=placeholder_event_hash(),
        )
    )


def emit_policy_emergency_revert(
    *,
    ledger: JsonlObserverLedger,
    from_policy_record_id: str,
    to_previous_verified_policy_record_id: str,
    policy_id: str,
    reason: str,
    now_ms: int,
) -> ObserverEvent:
    """Emit an emergency-revert audit event.

    ``to_previous_verified_policy_record_id`` MUST be a policy that
    was previously VERIFIED (or active-then-superseded) in the same
    scope; this is enforced by the store helper.
    """
    assert_no_forbidden_literal(reason)
    return ledger.append(
        ObserverEvent(
            event_id=f"policy-revert-{from_policy_record_id}-{now_ms}",
            event_family=EventFamily.MEMORY,
            event_type="MEMORY_RECORD_STATUS_CHANGED",
            occurred_at_ms=now_ms,
            payload={
                "record_id": from_policy_record_id,
                "policy_id": policy_id,
                "subject_class": "deontic_policy",
                "evidence_axis": "human_testimony",
                "requested_status": "superseded",
                "new_status": "superseded",
                "old_status": "active",
                "trigger": "emergency_revert",
                "revert_target_record_id": to_previous_verified_policy_record_id,
                "reason": reason,
            },
            provenance=ProvenanceRef(source_event_id=from_policy_record_id),
            previous_event_hash=None,
            event_hash=placeholder_event_hash(),
        )
    )
