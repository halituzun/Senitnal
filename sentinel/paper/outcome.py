"""V7 — Paper decision outcome tracking.

Records what was observed *after* a paper decision and produces a
comparison record.  No M2 mutation, no policy mutation; the
comparison is **evidence-candidate only**.  Replay-usable evidence
requires ``PaperOutcome.external == True``.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sentinel.paper.decision import PaperDecision  # noqa: TC001
from sentinel.runtime.output import SystemOutput


class PaperOutcomeKind(StrEnum):
    """Closed observed-outcome enum.  No trade-side terms."""

    OBSERVED_NEUTRAL = "observed_neutral"
    OBSERVED_RISK_MATERIALIZED = "observed_risk_materialized"
    OBSERVED_RISK_DID_NOT_MATERIALIZE = "observed_risk_did_not_materialize"
    OBSERVED_EDGE_DECAYED = "observed_edge_decayed"
    OBSERVED_EDGE_PERSISTED = "observed_edge_persisted"
    OBSERVED_DATA_WAS_STALE = "observed_data_was_stale"
    OBSERVED_UNKNOWN = "observed_unknown"


class PaperOutcome(BaseModel):
    """One observed outcome after a paper decision was issued."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    outcome_id: str = Field(min_length=1)
    decision_id: str = Field(min_length=1)
    opportunity_id: str = Field(min_length=1)
    observed_at_ms: int = Field(ge=0)
    outcome_kind: PaperOutcomeKind
    confidence: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    external: bool
    source_event_refs: tuple[str, ...]
    notes_hash: str | None = None

    @model_validator(mode="after")
    def _validate_outcome(self) -> Self:
        if not self.source_event_refs:
            raise ValueError("PaperOutcome.source_event_refs must be non-empty")
        return self


class PaperDecisionOutcomeComparison(BaseModel):
    """Comparison between a paper decision and the observed outcome.

    ``evidence_usable_for_replay`` is True iff the underlying
    ``PaperOutcome.external`` is True; otherwise the comparison is
    informational only.  Comparisons never mutate M2 or the active
    policy.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    comparison_id: str = Field(min_length=1)
    decision_id: str = Field(min_length=1)
    outcome_id: str = Field(min_length=1)
    was_conservative: bool
    would_have_helped: bool
    would_have_hurt: bool
    alignment_score: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    evidence_usable_for_replay: bool


def compare_paper_decision_to_outcome(
    *,
    decision: PaperDecision,
    outcome: PaperOutcome,
) -> PaperDecisionOutcomeComparison:
    """Deterministic comparison helper.

    Mapping (informational):
        - decision.output == BLOCK + outcome_kind risk_materialized
          → would_have_helped=True
        - decision.output == BLOCK + outcome_kind
          risk_did_not_materialize → was_conservative=True,
          would_have_hurt=True
        - decision.output == MONITOR + outcome_kind risk_materialized
          → would_have_hurt=True (advisor missed it)
        - decision.output == MONITOR + outcome_kind edge_persisted
          → alignment_score raised
    """
    output = decision.output
    kind = outcome.outcome_kind

    was_conservative = False
    would_have_helped = False
    would_have_hurt = False
    alignment_score = 0.5

    if output is SystemOutput.BLOCK:
        if kind is PaperOutcomeKind.OBSERVED_RISK_MATERIALIZED:
            would_have_helped = True
            alignment_score = 0.9
        elif kind is PaperOutcomeKind.OBSERVED_RISK_DID_NOT_MATERIALIZE:
            was_conservative = True
            would_have_hurt = True
            alignment_score = 0.3
        elif kind is PaperOutcomeKind.OBSERVED_DATA_WAS_STALE:
            would_have_helped = True
            alignment_score = 0.8
        else:
            was_conservative = True
            alignment_score = 0.5
    elif output is SystemOutput.MONITOR:
        if kind is PaperOutcomeKind.OBSERVED_RISK_MATERIALIZED:
            would_have_hurt = True
            alignment_score = 0.2
        elif kind is PaperOutcomeKind.OBSERVED_EDGE_PERSISTED:
            alignment_score = 0.7
        elif kind is PaperOutcomeKind.OBSERVED_RISK_DID_NOT_MATERIALIZE:
            alignment_score = 0.75
    elif output is SystemOutput.WAIT or output is SystemOutput.NO_ACTION:
        alignment_score = 0.55 if kind is PaperOutcomeKind.OBSERVED_NEUTRAL else 0.4

    return PaperDecisionOutcomeComparison(
        comparison_id=f"paper-cmp-{decision.decision_id}-{outcome.outcome_id}",
        decision_id=decision.decision_id,
        outcome_id=outcome.outcome_id,
        was_conservative=was_conservative,
        would_have_helped=would_have_helped,
        would_have_hurt=would_have_hurt,
        alignment_score=alignment_score,
        evidence_usable_for_replay=outcome.external,
    )
