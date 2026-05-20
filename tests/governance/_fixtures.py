"""Shared builders for V9 governance tests."""

from __future__ import annotations

from sentinel.governance.approval import HumanApprovalRecord, HumanApprovalStatus
from sentinel.governance.request import GovernanceRequestKind, LiveGovernanceRequest
from sentinel.governance.scope import (
    GovernanceEnvironment,
    GovernanceScopeKind,
    LimitedLiveGovernanceScope,
)


def make_scope(
    *,
    scope_id: str = "scope-1",
    environment: GovernanceEnvironment = GovernanceEnvironment.LIMITED_LIVE,
) -> LimitedLiveGovernanceScope:
    return LimitedLiveGovernanceScope(
        scope_id=scope_id,
        environment=environment,
        scope_kind=GovernanceScopeKind.SYMBOL_SCOPE,
        symbol_hash="sha256:sym-1",
        venue_hash="sha256:venue-1",
        strategy_hash="sha256:strat-1",
        applies_to_all_symbols=False,
        applies_to_all_strategies=False,
        max_candidates_per_hour=100,
        max_live_impacting_blocks_per_hour=50,
        max_governance_latency_ms=2000,
        created_at_ms=1_000_000,
    )


def make_request(
    *,
    request_id: str = "gov-req-1",
    request_kind: GovernanceRequestKind = GovernanceRequestKind.CANDIDATE_LIVE_ACTION_REVIEW,
    scope: LimitedLiveGovernanceScope | None = None,
    deadline_ms: int = 2_000_000,
    observed_at_ms: int = 1_000_000,
    risk_score: float = 0.2,
    confidence: float = 0.7,
    staleness_ms: int = 50,
    live_impact_possible: bool = True,
    memory_record_refs: tuple[str, ...] = (),
    replay_evidence_refs: tuple[str, ...] = (),
) -> LiveGovernanceRequest:
    return LiveGovernanceRequest(
        request_id=request_id,
        request_kind=request_kind,
        scope=scope if scope is not None else make_scope(),
        candidate_ref=f"cand-{request_id}",
        source_event_refs=("ev-1",),
        observed_at_ms=observed_at_ms,
        deadline_ms=deadline_ms,
        provenance_hash="sha256:p-1",
        memory_record_refs=memory_record_refs,
        replay_evidence_refs=replay_evidence_refs,
        risk_score=risk_score,
        confidence=confidence,
        staleness_ms=staleness_ms,
        latency_ms=30,
        live_impact_possible=live_impact_possible,
        requires_human_approval=True,
    )


def make_approval(
    *,
    request_id: str = "gov-req-1",
    status: HumanApprovalStatus = HumanApprovalStatus.APPROVED,
    expires_at_ms: int = 2_000_000,
) -> HumanApprovalRecord:
    return HumanApprovalRecord(
        approval_id=f"app-{request_id}",
        request_id=request_id,
        approver_ref="operator-1",
        status=status,
        created_at_ms=900_000,
        decided_at_ms=950_000,
        expires_at_ms=expires_at_ms,
        approval_reason_hash="sha256:reason",
        signed_by="operator-mock-key",
        signature="sig-mock",
        provenance_hash="sha256:approval-1",
    )
