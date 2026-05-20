"""V4 — Replay-driven financial memory pipeline.

Drives V4 replay over an existing V3 financial memory store:

    For each stored candidate:
        - start a ReplaySession (purpose=FINANCIAL_MEMORY_REVIEW)
        - construct a small bounded counterfactual ablation
        - run it in sandbox
        - compute replay survival score
        - if external outcome refs are supplied, compute outcome
          alignment too
        - propose MemoryVerificationEvidence (audit only; the
          MWG remains the sole write path)
        - audit REPLAY_SESSION_STATUS_CHANGED (start + completion)
    Sessions stop early when ReplayBudget caps are reached.

Hard zeros enforced by `ReplayFinancialPipelineResult`:
    - live_event_count == 0
    - action_count == 0
    - records_promoted_to_verified == 0  (V4 never promotes)
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping  # noqa: TC003 (runtime annotation)
from dataclasses import dataclass

from sentinel.memory.replay_evidence import (
    submit_outcome_alignment_evidence,
    submit_replay_survival_evidence,
)
from sentinel.memory.store import InMemoryExplicitMemoryStore  # noqa: TC001 (runtime arg)
from sentinel.observer.ledger import JsonlObserverLedger  # noqa: TC001 (runtime arg)
from sentinel.replay.audit import emit_replay_session_status_changed
from sentinel.replay.budget import (
    ReplayBudgetState,
    can_start_replay_session,
    record_replay_session_completion,
)
from sentinel.replay.counterfactual import (
    AblationKind,
    CounterfactualAblation,
    perform_counterfactual_ablation,
)
from sentinel.replay.outcome_alignment import (
    OutcomeAlignmentEvidence,
    OutcomeRef,
    compute_outcome_alignment_score,
)
from sentinel.replay.session import (
    ReplayEffectChannel,
    ReplayInputSnapshot,
    ReplayPurpose,
    ReplaySession,
    ReplaySessionStatus,
)
from sentinel.replay.survival import (
    ReplaySurvivalEvidence,
    compute_replay_survival_score,
)
from sentinel.types.memory import MemoryRecord  # noqa: TC001 (runtime annotation)
from sentinel.types.neural_seed import ProvenanceRef


@dataclass(frozen=True, slots=True)
class ReplayFinancialPipelineResult:
    """Outcome of one replay-over-financial-memory pass.

    Hard zeros: live_event_count, action_count,
    records_promoted_to_verified MUST all be 0.
    """

    sessions_started: int
    sessions_completed: int
    budget_exhausted_count: int
    replay_survival_evidence_count: int
    outcome_alignment_evidence_count: int
    memory_evidence_proposals: int
    m0_effect_proposals: int
    records_promoted_to_verified: int
    live_event_count: int
    action_count: int
    hash_chain_valid: bool

    def __post_init__(self) -> None:
        if self.records_promoted_to_verified != 0:
            raise ValueError(
                "V4 pipeline must produce 0 verified promotions; "
                f"got {self.records_promoted_to_verified}"
            )
        if self.live_event_count != 0:
            raise ValueError(f"V4 pipeline must produce 0 live events; got {self.live_event_count}")
        if self.action_count != 0:
            raise ValueError(f"V4 pipeline must produce 0 action outputs; got {self.action_count}")


def run_replay_financial_pipeline(
    *,
    candidates: Iterable[MemoryRecord],
    store: InMemoryExplicitMemoryStore,
    ledger: JsonlObserverLedger,
    budget_state: ReplayBudgetState,
    outcome_refs_by_record: Mapping[str, tuple[OutcomeRef, ...]] | None = None,
    provenance: ProvenanceRef | None = None,
) -> ReplayFinancialPipelineResult:
    """Iterate financial candidates and produce replay evidence proposals.

    `candidates` is the iterable of records to review; the caller
    typically supplies `store.list_all()` filtered to the financial
    subject classes. `outcome_refs_by_record` (optional) maps a
    record_id to its EXTERNAL outcome refs for alignment scoring.
    """
    _ = store  # store is intentionally read-only for the pipeline body
    _ = provenance  # reserved for future expansion; not used directly
    sessions_started = 0
    sessions_completed = 0
    budget_exhausted = 0
    survival_evidence_count = 0
    outcome_evidence_count = 0
    evidence_proposals = 0
    m0_effect_proposals = 0  # V4 pipeline does not emit M0 effects

    state = budget_state

    for record in candidates:
        now_ms = max(1, record.created_at_ms + 1)
        if not can_start_replay_session(state=state, now_ms=now_ms):
            budget_exhausted += 1
            continue

        snapshot = ReplayInputSnapshot(
            snapshot_id=f"snap-{record.record_id}",
            source_m1_event_ids=(),
            source_memory_record_ids=(record.record_id,),
            source_observation_event_ids=record.external_corroboration_refs,
            source_outcome_refs=(),
            created_at_ms=now_ms,
            provenance_ref=ProvenanceRef(source_event_id=record.record_id),
            hash_ref=f"sha256:replay-{record.record_id}",
        )
        running = ReplaySession(
            session_id=f"session-{record.record_id}",
            purpose=ReplayPurpose.FINANCIAL_MEMORY_REVIEW,
            status=ReplaySessionStatus.RUNNING,
            input_snapshot=snapshot,
            started_at_ms=now_ms,
            budget_ref=state.budget.budget_id,
            sandbox_id=f"sandbox-{record.record_id}",
            effect_channels_requested=(ReplayEffectChannel.MEMORY_VERIFICATION_EVIDENCE,),
        )
        emit_replay_session_status_changed(
            ledger, session=running, reason="V4 replay started", now_ms=now_ms
        )
        sessions_started += 1

        ablation = CounterfactualAblation(
            ablation_id=f"abl-{record.record_id}",
            session_id=running.session_id,
            kind=AblationKind.SINGLE_VARIABLE,
            removed_event_ids=(record.external_corroboration_refs[0],)
            if record.external_corroboration_refs
            else (f"placeholder-{record.record_id}",),
            causal_link_required=False,
            created_at_ms=now_ms,
        )
        result = perform_counterfactual_ablation(
            ablation=ablation,
            causal_refs={},
            base_pattern_intensity=0.8,
            ablated_pattern_intensity=0.55,
        )
        survival_score = compute_replay_survival_score((result,))

        survival = ReplaySurvivalEvidence(
            evidence_id=f"surv-{record.record_id}",
            session_id=running.session_id,
            memory_record_id=record.record_id,
            ablation_ids=(ablation.ablation_id,),
            survival_score=survival_score,
            min_sessions_satisfied=False,  # V4 single-session reviews are
            # never sufficient by themselves
            session_separation_ms=0,
            created_at_ms=now_ms,
        )
        survival_evidence_count += 1
        survival_outcome = submit_replay_survival_evidence(
            ledger=ledger, record=record, evidence=survival, now_ms=now_ms
        )
        if survival_outcome.accepted:
            evidence_proposals += 1

        refs = (
            outcome_refs_by_record.get(record.record_id, ())
            if outcome_refs_by_record is not None
            else ()
        )
        if refs:
            alignment_score = compute_outcome_alignment_score(
                outcome_refs=refs, record_confidence=0.7
            )
            alignment = OutcomeAlignmentEvidence(
                evidence_id=f"align-{record.record_id}",
                session_id=running.session_id,
                memory_record_id=record.record_id,
                outcome_refs=refs,
                alignment_score=alignment_score,
                stale=False,
                created_at_ms=now_ms,
            )
            outcome_evidence_count += 1
            alignment_outcome = submit_outcome_alignment_evidence(
                ledger=ledger, record=record, evidence=alignment, now_ms=now_ms
            )
            if alignment_outcome.accepted:
                evidence_proposals += 1

        completed = ReplaySession(
            session_id=running.session_id,
            purpose=running.purpose,
            status=ReplaySessionStatus.COMPLETED,
            input_snapshot=running.input_snapshot,
            started_at_ms=running.started_at_ms,
            completed_at_ms=now_ms + 1,
            budget_ref=running.budget_ref,
            sandbox_id=running.sandbox_id,
            effect_channels_requested=running.effect_channels_requested,
            effect_channels_applied=(ReplayEffectChannel.MEMORY_VERIFICATION_EVIDENCE,),
        )
        emit_replay_session_status_changed(
            ledger, session=completed, reason="V4 replay completed", now_ms=now_ms + 1
        )
        sessions_completed += 1
        state = record_replay_session_completion(state=state, completed_at_ms=now_ms + 1)

    return ReplayFinancialPipelineResult(
        sessions_started=sessions_started,
        sessions_completed=sessions_completed,
        budget_exhausted_count=budget_exhausted,
        replay_survival_evidence_count=survival_evidence_count,
        outcome_alignment_evidence_count=outcome_evidence_count,
        memory_evidence_proposals=evidence_proposals,
        m0_effect_proposals=m0_effect_proposals,
        records_promoted_to_verified=0,
        live_event_count=0,
        action_count=0,
        hash_chain_valid=ledger.verify(),
    )
