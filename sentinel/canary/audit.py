"""V8 — Canary veto audit helper.

Emits ``CANARY_VETO_DECISION_RECORDED`` permanent events.  Payload
carries only abstract scalars + closed-enum reason values plus the
four safety flags pinned ``False``.  No raw symbol / venue / strategy
/ order / API field; reason summary passes
``assert_no_forbidden_literal``.
"""

from __future__ import annotations

from sentinel.canary.veto import CanaryVetoDecision, VetoRequest  # noqa: TC001
from sentinel.observer.hash_chain import placeholder_event_hash
from sentinel.observer.ledger import JsonlObserverLedger  # noqa: TC001
from sentinel.runtime.output import assert_no_forbidden_literal
from sentinel.types.neural_seed import ProvenanceRef  # noqa: TC001
from sentinel.types.observer import EventFamily, ObserverEvent


def emit_canary_veto_decision_recorded(
    *,
    ledger: JsonlObserverLedger,
    decision: CanaryVetoDecision,
    request: VetoRequest,
    provenance: ProvenanceRef,
    now_ms: int,
) -> ObserverEvent:
    """Append a permanent canary veto audit event."""
    reason_text = (
        f"canary veto evaluated: decision={decision.decision.value}; "
        f"output={decision.system_output.value}; "
        f"reasons={','.join(r.value for r in decision.reasons)}"
    )
    assert_no_forbidden_literal(reason_text)
    return ledger.append(
        ObserverEvent(
            event_id=f"canary-veto-{decision.decision_id}",
            event_family=EventFamily.DEONTIC,
            event_type="CANARY_VETO_DECISION_RECORDED",
            occurred_at_ms=now_ms,
            payload={
                "request_id": decision.request_id,
                "candidate_id": decision.candidate_id,
                "decision": decision.decision.value,
                "system_output": decision.system_output.value,
                "reasons": [r.value for r in decision.reasons],
                "confidence": decision.confidence,
                "environment": decision.environment.value,
                "shadow_only": decision.shadow_only,
                "can_affect_canary": decision.can_affect_canary,
                "creates_action": False,
                "writes_external": False,
                "approves_trade": False,
                "no_veto_is_approval": False,
                "source_event_refs": list(request.candidate.source_event_refs),
                "active_policy_record_ref": request.active_policy_record_ref,
                "paper_decision_ref": request.paper_decision_ref,
                "replay_evidence_refs": list(request.replay_evidence_refs),
                "memory_record_refs": list(request.memory_record_refs),
                "scope_hash": request.candidate.scope_hash,
                "reason": reason_text,
            },
            provenance=provenance,
            previous_event_hash=None,
            event_hash=placeholder_event_hash(),
        )
    )


__all__ = ["emit_canary_veto_decision_recorded"]
