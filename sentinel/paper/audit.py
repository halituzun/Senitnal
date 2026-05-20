"""V7 — Paper co-pilot audit helper.

Emits ``LEDGER_STATE_CHANGED`` events for paper evaluation audit.
V7 introduces no new catalog row — the existing ledger-meta row
carries the paper evaluation payload.
"""

from __future__ import annotations

from sentinel.observer.hash_chain import placeholder_event_hash
from sentinel.observer.ledger import JsonlObserverLedger  # noqa: TC001
from sentinel.paper.decision import PaperCoPilotResult  # noqa: TC001
from sentinel.runtime.output import assert_no_forbidden_literal
from sentinel.types.neural_seed import ProvenanceRef  # noqa: TC001
from sentinel.types.observer import EventFamily, ObserverEvent


def emit_paper_copilot_evaluated(
    *,
    ledger: JsonlObserverLedger,
    result: PaperCoPilotResult,
    provenance: ProvenanceRef,
    now_ms: int,
) -> ObserverEvent:
    """Append a permanent paper-evaluation audit event.

    Payload carries only abstract scalars + closed-enum reason values;
    no raw symbol / venue / strategy / order field.  Reason string
    passes ``assert_no_forbidden_literal``.
    """
    reason = (
        f"paper co-pilot evaluated: output={result.decision.output.value}; "
        f"reasons={','.join(r.value for r in result.decision.reasons)}"
    )
    assert_no_forbidden_literal(reason)
    return ledger.append(
        ObserverEvent(
            event_id=f"paper-eval-{result.result_id}",
            event_family=EventFamily.LEDGER_META,
            event_type="LEDGER_STATE_CHANGED",
            occurred_at_ms=now_ms,
            payload={
                "opportunity_id": result.opportunity.opportunity_id,
                "decision_id": result.decision.decision_id,
                "output": result.decision.output.value,
                "reasons": [r.value for r in result.decision.reasons],
                "confidence": result.decision.confidence,
                "shadow_only": True,
                "creates_action": False,
                "writes_external": False,
                "approved_for_live": False,
                "policy_record_ref": result.decision.policy_record_ref,
                "memory_record_refs": list(result.decision.memory_record_refs),
                "replay_evidence_refs": list(result.decision.replay_evidence_refs),
                "scope_hash": result.opportunity.scope_hash,
                "source": result.opportunity.source.value,
                "kind": result.opportunity.kind.value,
                "reason": reason,
            },
            provenance=provenance,
            previous_event_hash=None,
            event_hash=placeholder_event_hash(),
        )
    )
