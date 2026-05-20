"""Shared builders for V10 AGI tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sentinel.agi.evidence_gate import (
    EvidenceGateInput,
    EvidenceWindow,
    EvidenceWindowKind,
)
from sentinel.agi.orchestrator import FinancialAGIInputBundle
from sentinel.governance.guard import GovernanceGuardContext
from sentinel.policy.record_builder import build_deontic_policy_candidate_record
from sentinel.types.memory import MemoryRecordStatus
from sentinel.types.neural_seed import ProvenanceRef

from tests.governance._fixtures import make_approval, make_request
from tests.policy._fixtures import make_artifact

if TYPE_CHECKING:
    from sentinel.governance.decision import GovernanceDecisionKind

_NOW_MS = 1_700_000_001_000
_EXPIRES_MS = 1_700_000_005_000


def make_all_windows_satisfied() -> tuple[EvidenceWindow, ...]:
    """Return a full set of satisfied evidence windows."""
    return tuple(
        EvidenceWindow(
            kind=k,
            satisfied=True,
            days_observed=100 if "90d" in k.value else 35,
        )
        for k in EvidenceWindowKind
    )


def make_evidence_gate_input(
    *,
    evaluation_id: str = "gate-test-1",
    windows: tuple[EvidenceWindow, ...] | None = None,
    evaluated_at_ms: int = _NOW_MS,
) -> EvidenceGateInput:
    if windows is None:
        windows = make_all_windows_satisfied()
    return EvidenceGateInput(
        evaluation_id=evaluation_id,
        windows=windows,
        evaluated_at_ms=evaluated_at_ms,
    )


def make_ctx(
    *,
    now_ms: int = _NOW_MS,
    request_id: str = "agi-req-001",
    kill_switch: bool = False,
    hash_chain_valid: bool = True,
) -> GovernanceGuardContext:
    rec = build_deontic_policy_candidate_record(
        artifact=make_artifact(
            effective_at_ms=1_700_000_000_000,
            created_at_ms=1_700_000_000_000,
        ),
        provenance=ProvenanceRef(source_event_id="ev-agi-ctx"),
        created_at_ms=1_700_000_000_000,
        evidence_refs=("approval",),
    ).model_copy(update={"status": MemoryRecordStatus.ACTIVE})
    return GovernanceGuardContext(
        now_ms=now_ms,
        hash_chain_valid=hash_chain_valid,
        active_policy_record=rec,
        human_approval=make_approval(
            request_id=request_id,
            expires_at_ms=_EXPIRES_MS,
        ),
        kill_switch_observed=kill_switch,
    )


def make_bundle(
    *,
    bundle_id: str = "bundle-1",
    now_ms: int = _NOW_MS,
    request_id: str = "agi-req-001",
    windows: tuple[EvidenceWindow, ...] | None = None,
    kill_switch: bool = False,
    hash_chain_valid: bool = True,
    live_governance_decision_kind: GovernanceDecisionKind | None = None,
) -> FinancialAGIInputBundle:
    from sentinel.governance.guard import evaluate_governance_guard

    ctx = make_ctx(
        now_ms=now_ms,
        request_id=request_id,
        kill_switch=kill_switch,
        hash_chain_valid=hash_chain_valid,
    )
    req = make_request(
        request_id=request_id,
        deadline_ms=now_ms + 10_000,
        observed_at_ms=now_ms - 100,
    )
    gov_dec = evaluate_governance_guard(request=req, context=ctx)
    lgdk = (
        live_governance_decision_kind
        if live_governance_decision_kind is not None
        else gov_dec.decision
    )

    return FinancialAGIInputBundle(
        bundle_id=bundle_id,
        now_ms=now_ms,
        provenance=ProvenanceRef(source_event_id=request_id),
        evidence_gate_input=make_evidence_gate_input(windows=windows),
        governance_context=ctx,
        live_governance_decision_kind=lgdk,
    )
