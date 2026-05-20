"""V9 — Live governance audit helper.

Emits permanent ``LIVE_GOVERNANCE_DECISION_RECORDED`` events.
Payload carries only abstract scalars + closed-enum reason values
plus the five safety flags pinned ``False``.  No raw symbol / venue /
strategy / order / API field; reason summary passes
``assert_no_forbidden_literal``.
"""

from __future__ import annotations

from sentinel.governance.decision import LiveGovernanceDecision  # noqa: TC001
from sentinel.governance.request import LiveGovernanceRequest  # noqa: TC001
from sentinel.observer.hash_chain import placeholder_event_hash
from sentinel.observer.ledger import JsonlObserverLedger  # noqa: TC001
from sentinel.runtime.output import assert_no_forbidden_literal
from sentinel.types.neural_seed import ProvenanceRef  # noqa: TC001
from sentinel.types.observer import EventFamily, ObserverEvent


def emit_live_governance_decision_recorded(
    *,
    ledger: JsonlObserverLedger,
    decision: LiveGovernanceDecision,
    request: LiveGovernanceRequest,
    provenance: ProvenanceRef,
    now_ms: int,
) -> ObserverEvent:
    """Append a permanent governance decision audit event."""
    reason_text = (
        f"live governance evaluated: decision={decision.decision.value}; "
        f"output={decision.system_output.value}; "
        f"reasons={','.join(r.value for r in decision.reasons)}"
    )
    assert_no_forbidden_literal(reason_text)
    return ledger.append(
        ObserverEvent(
            event_id=f"gov-{decision.decision_id}",
            event_family=EventFamily.DEONTIC,
            event_type="LIVE_GOVERNANCE_DECISION_RECORDED",
            occurred_at_ms=now_ms,
            payload={
                "request_id": decision.request_id,
                "decision_id": decision.decision_id,
                "decision": decision.decision.value,
                "system_output": decision.system_output.value,
                "reasons": [r.value for r in decision.reasons],
                "confidence": decision.confidence,
                "human_approval_ref": decision.human_approval_ref,
                "policy_record_ref": decision.policy_record_ref,
                "canary_decision_ref": decision.canary_decision_ref,
                "paper_decision_ref": decision.paper_decision_ref,
                "replay_evidence_refs": list(decision.replay_evidence_refs),
                "memory_record_refs": list(decision.memory_record_refs),
                "live_impact_possible": decision.live_impact_possible,
                "live_impact_allowed": decision.live_impact_allowed,
                "creates_action": False,
                "writes_external": False,
                "approves_trade": False,
                "no_veto_is_approval": False,
                "monitor_is_approval": False,
                "source_event_refs": list(request.source_event_refs),
                "environment": request.scope.environment.value,
                "scope_id": request.scope.scope_id,
                "reason": reason_text,
            },
            provenance=provenance,
            previous_event_hash=None,
            event_hash=placeholder_event_hash(),
        )
    )


__all__ = ["emit_live_governance_decision_recorded"]
