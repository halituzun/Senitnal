"""V10 — Financial AGI v1 audit helpers.

Emits two permanent observer events:
    FINANCIAL_AGI_V1_EVALUATED   — one per evaluation cycle
    FINANCIAL_AGI_READINESS_RECORDED — one per readiness report
"""

from __future__ import annotations

from sentinel.agi.orchestrator import FinancialAGIOutputBundle  # noqa: TC001
from sentinel.agi.readiness_report import FinancialAGIReadinessReport  # noqa: TC001
from sentinel.observer.hash_chain import placeholder_event_hash
from sentinel.observer.ledger import JsonlObserverLedger  # noqa: TC001
from sentinel.runtime.output import assert_no_forbidden_literal
from sentinel.types.neural_seed import ProvenanceRef  # noqa: TC001
from sentinel.types.observer import EventFamily, ObserverEvent


def emit_financial_agi_v1_evaluated(
    *,
    ledger: JsonlObserverLedger,
    output_bundle: FinancialAGIOutputBundle,
    provenance: ProvenanceRef,
    now_ms: int,
) -> ObserverEvent:
    """Append a permanent FINANCIAL_AGI_V1_EVALUATED audit event."""
    reason_text = (
        f"agi_v1 evaluated: bundle={output_bundle.bundle_id}; "
        f"gate={output_bundle.evidence_gate_result.decision.value}; "
        f"consensus={output_bundle.consensus_result.decision.value}; "
        f"output={output_bundle.final_output.value}; "
        f"activation={output_bundle.activation_state.value}"
    )
    assert_no_forbidden_literal(reason_text)
    return ledger.append(
        ObserverEvent(
            event_id=f"agi-eval-{output_bundle.bundle_id}",
            event_family=EventFamily.DEONTIC,
            event_type="FINANCIAL_AGI_V1_EVALUATED",
            occurred_at_ms=now_ms,
            payload={
                "bundle_id": output_bundle.bundle_id,
                "gate_decision": output_bundle.evidence_gate_result.decision.value,
                "consensus_decision": output_bundle.consensus_result.decision.value,
                "final_output": output_bundle.final_output.value,
                "activation_state": output_bundle.activation_state.value,
                "allowed_to_influence_live": output_bundle.live_impact_guard_result.allowed_to_influence_live,
                "has_90d_evidence": output_bundle.evidence_gate_result.has_90d_evidence,
                "creates_action": False,
                "writes_external": False,
                "approves_trade": False,
                "no_veto_is_approval": False,
                "monitor_is_approval": False,
                "reason": reason_text,
            },
            provenance=provenance,
            previous_event_hash=None,
            event_hash=placeholder_event_hash(),
        )
    )


def emit_financial_agi_readiness_recorded(
    *,
    ledger: JsonlObserverLedger,
    report: FinancialAGIReadinessReport,
    provenance: ProvenanceRef,
    now_ms: int,
) -> ObserverEvent:
    """Append a permanent FINANCIAL_AGI_READINESS_RECORDED audit event."""
    reason_text = (
        f"agi_v1 readiness: report={report.report_id}; "
        f"status={report.status}; "
        f"activation={report.activation_state.value}"
    )
    assert_no_forbidden_literal(reason_text)
    return ledger.append(
        ObserverEvent(
            event_id=f"agi-readiness-{report.report_id}",
            event_family=EventFamily.DEONTIC,
            event_type="FINANCIAL_AGI_READINESS_RECORDED",
            occurred_at_ms=now_ms,
            payload={
                "report_id": report.report_id,
                "status": report.status,
                "activation_state": report.activation_state.value,
                "gate_decision": report.gate_decision.value,
                "consensus_decision": report.consensus_decision.value,
                "has_90d_evidence": report.has_90d_evidence,
                "all_mandatory_satisfied": report.all_mandatory_satisfied,
                "satisfied_window_count": len(report.satisfied_windows),
                "missing_window_count": len(report.missing_windows),
                "reason": reason_text,
            },
            provenance=provenance,
            previous_event_hash=None,
            event_hash=placeholder_event_hash(),
        )
    )


__all__ = [
    "emit_financial_agi_readiness_recorded",
    "emit_financial_agi_v1_evaluated",
]
