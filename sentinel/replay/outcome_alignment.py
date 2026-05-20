"""V4 — Outcome alignment evidence.

Outcome alignment compares a memory record against EXTERNAL,
recorded outcome refs. Internal-only outcomes are rejected by
construction. Stale outcomes can still be scored but cannot be
used for MWG-verification (`stale=True` blocks evidence-use).

A counterfactual ablation result CANNOT become an OutcomeRef.
Outcomes come from the real recorded world only.
"""

from __future__ import annotations

from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sentinel.runtime.output import assert_no_forbidden_literal


class OutcomeRef(BaseModel):
    """A reference to an externally-recorded outcome."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    outcome_ref_id: str = Field(min_length=1)
    source_event_id: str = Field(min_length=1)
    observed_at_ms: int = Field(ge=0)
    confidence: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    external: bool
    payload: dict[str, Any]

    @model_validator(mode="after")
    def _validate(self) -> Self:
        if self.external is not True:
            raise ValueError(
                "OutcomeRef.external must be True (V4 rejects internal-only "
                "outcomes for alignment evidence)"
            )
        if not self.payload:
            raise ValueError("OutcomeRef.payload must be non-empty")
        # Forbidden literals (execution verbs) must not appear in
        # outcome payload reason strings. `assert_no_forbidden_literal`
        # raises ForbiddenOutputViolation; re-raise as ValueError so
        # Pydantic wraps it in a ValidationError at the boundary.
        from sentinel.runtime.output import ForbiddenOutputViolation

        for value in self.payload.values():
            if isinstance(value, str):
                try:
                    assert_no_forbidden_literal(value)
                except ForbiddenOutputViolation as exc:
                    raise ValueError(
                        f"forbidden execution literal in outcome payload: {exc}"
                    ) from exc
        # Defensive: no API key / account fields allowed in the
        # observer-side payload.
        forbidden_keys = {
            "api_key",
            "api_secret",
            "secret",
            "account_id",
            "balance",
            "position",
            "side",
            "order_side",
            "order_id",
            "live_fill_id",
        }
        leaked = forbidden_keys & set(self.payload.keys())
        if leaked:
            raise ValueError(f"OutcomeRef.payload contains forbidden fields: {sorted(leaked)}")
        return self


class OutcomeAlignmentEvidence(BaseModel):
    """Bounded alignment evidence from external outcomes."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    evidence_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    memory_record_id: str = Field(min_length=1)
    outcome_refs: tuple[OutcomeRef, ...]
    alignment_score: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    stale: bool
    created_at_ms: int = Field(ge=0)

    @model_validator(mode="after")
    def _validate(self) -> Self:
        if not self.outcome_refs:
            raise ValueError("outcome_refs must be non-empty")
        for ref in self.outcome_refs:
            if ref.external is not True:
                raise ValueError("All outcome_refs must have external=True")
        return self


def compute_outcome_alignment_score(
    *,
    outcome_refs: tuple[OutcomeRef, ...],
    record_confidence: float,
) -> float:
    """Deterministic alignment score in [0, 1].

    No semantic / LLM judgment. Simple confidence-weighted average
    of the outcome refs' confidence, multiplied by the record's
    own confidence as a damping factor.
    """
    if not outcome_refs:
        raise ValueError("outcome_refs must be non-empty")
    if not (0.0 <= record_confidence <= 1.0):
        raise ValueError("record_confidence must be in [0.0, 1.0]")
    # Construction-time invariant: every OutcomeRef has
    # external=True (enforced at OutcomeRef.__post_init__-equivalent
    # model_validator). This guard is defensive.
    if not all(ref.external for ref in outcome_refs):
        raise ValueError("all outcome_refs must have external=True")
    weighted_total = 0.0
    total_weight = 0.0
    for ref in outcome_refs:
        weighted_total += ref.confidence * ref.confidence
        total_weight += ref.confidence
    if total_weight == 0.0:
        return 0.0
    base = weighted_total / total_weight
    return max(0.0, min(1.0, base * record_confidence))
