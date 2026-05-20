"""V4 — Replay survival score and evidence schema.

Replay survival is the aggregate over multiple counterfactual
ablation results. It is ALWAYS synthetic_only=True and CANNOT be
treated as outcome alignment / real truth.

Verification-use eligibility requires `min_sessions_satisfied=True`
— the consuming MWG wrapper enforces this.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

if TYPE_CHECKING:
    from sentinel.replay.counterfactual import CounterfactualAblationResult


def compute_replay_survival_score(
    results: tuple[CounterfactualAblationResult, ...],
) -> float:
    """Deterministic aggregate survival score in [0, 1].

    Empty input returns 0.0. Otherwise the score is the
    confidence-weighted mean of per-ablation survival scores.
    """
    if not results:
        return 0.0
    total_weight = 0.0
    total = 0.0
    for r in results:
        weight = max(0.0, r.confidence)
        total += r.survival_score * weight
        total_weight += weight
    if total_weight == 0.0:
        return 0.0
    return max(0.0, min(1.0, total / total_weight))


class ReplaySurvivalEvidence(BaseModel):
    """Bounded synthetic evidence from replay survival.

    Constitutional: cannot count as truth. Verification-use
    requires `min_sessions_satisfied=True` — the gate wrapper
    refuses to use this evidence otherwise.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    evidence_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    memory_record_id: str = Field(min_length=1)
    ablation_ids: tuple[str, ...]
    survival_score: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    min_sessions_satisfied: bool
    session_separation_ms: int = Field(ge=0)
    synthetic_only: bool = True
    created_at_ms: int = Field(ge=0)

    @model_validator(mode="after")
    def _validate(self) -> Self:
        if self.synthetic_only is not True:
            raise ValueError("ReplaySurvivalEvidence.synthetic_only must be True")
        if not self.ablation_ids:
            raise ValueError("ablation_ids must be non-empty")
        for aid in self.ablation_ids:
            if not aid:
                raise ValueError("ablation_ids entries must be non-empty")
        return self
