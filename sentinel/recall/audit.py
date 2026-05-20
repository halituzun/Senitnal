"""Recall protocol audit emission helpers.

Per RECALL_PROTOCOL.md §5 + §20 and the Phase 8 / Phase 10 build
plan: every recall trigger evaluation produces exactly one of
three audit events:

    RECALL_TRIGGER_REJECTED     trigger conditions failed
    RECALL_REQUEST_EMITTED      trigger fired + top-1 candidate found
    RECALL_RESULT_EMPTY         trigger fired + no candidate (T §20:
                                audit only; no core-facing payload)

Constitutional discipline:
    - Exactly one event per evaluation. The canonical MVP pipeline
      (`run_dry_simulation`) honors this contract; future trigger
      sites MUST call one of these emit helpers immediately after
      `check_recall_trigger`
    - RECALL_RESULT_EMPTY is audit-only by design: the core never
      sees an absence event — the absence IS the signal
    - All payloads pass through `assert_no_forbidden_literal` so
      execution verbs cannot leak from a rejection reason

Wired callers (v0.1):
    - `sentinel.runtime.dry_sim.run_dry_simulation` emits
      RECALL_TRIGGER_REJECTED after every recall trigger check
      (canonical MVP scenario always fails the trigger).
    The RECALL_REQUEST_EMITTED and RECALL_RESULT_EMPTY paths are
    not exercised in MVP (top-1 ranking and candidate provider
    integration land in later phases).
"""

from __future__ import annotations

from sentinel.observer.hash_chain import placeholder_event_hash
from sentinel.observer.ledger import JsonlObserverLedger  # noqa: TC001 (runtime)
from sentinel.recall.protocol import RecallTriggerDecision  # noqa: TC001 (runtime)
from sentinel.runtime.output import assert_no_forbidden_literal
from sentinel.types.memory import MemoryRecord  # noqa: TC001 (runtime)
from sentinel.types.neural_seed import ProvenanceRef
from sentinel.types.observer import EventFamily, ObserverEvent


def emit_recall_trigger_rejected(
    ledger: JsonlObserverLedger,
    *,
    request_id: str,
    decision: RecallTriggerDecision,
    now_ms: int,
) -> ObserverEvent:
    """Audit a recall trigger that did NOT fire."""
    assert_no_forbidden_literal(decision.reason)
    return ledger.append(
        ObserverEvent(
            event_id=f"recall-rejected-{request_id}",
            event_family=EventFamily.INGRESS,
            event_type="RECALL_TRIGGER_REJECTED",
            occurred_at_ms=now_ms,
            payload={
                "request_id": request_id,
                "reason": decision.reason,
            },
            provenance=ProvenanceRef(source_event_id=request_id),
            previous_event_hash=None,
            event_hash=placeholder_event_hash(),
        )
    )


def emit_recall_request(
    ledger: JsonlObserverLedger,
    *,
    request_id: str,
    selected: MemoryRecord,
    score: float,
    now_ms: int,
) -> ObserverEvent:
    """Audit a recall trigger that fired AND surfaced a top-1 candidate."""
    return ledger.append(
        ObserverEvent(
            event_id=f"recall-emit-{request_id}",
            event_family=EventFamily.INGRESS,
            event_type="RECALL_REQUEST_EMITTED",
            occurred_at_ms=now_ms,
            payload={
                "request_id": request_id,
                "record_id": selected.record_id,
                "subject_class": selected.subject_class.value,
                "score": score,
            },
            provenance=ProvenanceRef(source_event_id=request_id),
            previous_event_hash=None,
            event_hash=placeholder_event_hash(),
        )
    )


def emit_recall_result_empty(
    ledger: JsonlObserverLedger,
    *,
    request_id: str,
    candidates_considered: int,
    now_ms: int,
) -> ObserverEvent:
    """Audit a recall trigger that fired but produced no result.

    Per T §20 this is audit-only. The core does NOT receive an
    absence payload; callers that need to coordinate on emptiness
    do so via this ledger event, not via a return value.
    """
    return ledger.append(
        ObserverEvent(
            event_id=f"recall-empty-{request_id}",
            event_family=EventFamily.INGRESS,
            event_type="RECALL_RESULT_EMPTY",
            occurred_at_ms=now_ms,
            payload={
                "request_id": request_id,
                "candidates_considered": candidates_considered,
            },
            provenance=ProvenanceRef(source_event_id=request_id),
            previous_event_hash=None,
            event_hash=placeholder_event_hash(),
        )
    )
