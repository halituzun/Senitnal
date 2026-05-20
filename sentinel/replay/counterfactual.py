"""V4 — Counterfactual ablation.

Single-variable or pairwise event removal in a sandbox. V4 forbids
higher-order (>= 3) ablations. Pairwise ablations require a
documented causal link between the two removed events. Results
are SYNTHETIC ONLY — they CANNOT count as outcome alignment.
"""

from __future__ import annotations

from collections.abc import Mapping  # noqa: TC003 (runtime annotation)
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AblationKind(StrEnum):
    SINGLE_VARIABLE = "single_variable"
    PAIRWISE = "pairwise"


class CounterfactualAblation(BaseModel):
    """Specification of an ablation experiment.

    `kind=single_variable` removes exactly 1 event. `kind=pairwise`
    removes exactly 2 events AND requires `causal_link_required=True`.
    More than 2 removed events is a V4 constitutional violation.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    ablation_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    kind: AblationKind
    removed_event_ids: tuple[str, ...]
    causal_link_required: bool
    expected_outcome_ref: str | None = None
    created_at_ms: int = Field(ge=0)

    @model_validator(mode="after")
    def _validate(self) -> Self:
        if self.kind is AblationKind.SINGLE_VARIABLE:
            if len(self.removed_event_ids) != 1:
                raise ValueError("single_variable ablation requires exactly 1 removed_event_id")
        elif self.kind is AblationKind.PAIRWISE:
            if len(self.removed_event_ids) != 2:
                raise ValueError("pairwise ablation requires exactly 2 removed_event_ids")
            if not self.causal_link_required:
                raise ValueError("pairwise ablation requires causal_link_required=True")
        for sid in self.removed_event_ids:
            if not sid:
                raise ValueError("removed_event_ids entries must be non-empty")
        return self


def validate_pairwise_causal_link(
    *,
    event_a_id: str,
    event_b_id: str,
    causal_refs: Mapping[str, tuple[str, ...]],
) -> bool:
    """Return True iff there is a causal link between two events.

    Accepted shapes (any one suffices):
        - A references B in causal_refs[A]
        - B references A in causal_refs[B]
        - A and B share a common parent (intersection non-empty)
    """
    if not event_a_id or not event_b_id:
        return False
    if event_a_id == event_b_id:
        return False
    refs_a = causal_refs.get(event_a_id, ())
    refs_b = causal_refs.get(event_b_id, ())
    if event_b_id in refs_a or event_a_id in refs_b:
        return True
    return bool(refs_a and refs_b and set(refs_a) & set(refs_b))


@dataclass(frozen=True, slots=True)
class CounterfactualAblationResult:
    """Outcome of one ablation experiment.

    `synthetic_only` is True by construction. The result CANNOT
    be used as outcome alignment evidence; it contributes only to
    a replay survival score.
    """

    ablation_id: str
    removed_event_ids: tuple[str, ...]
    pattern_survived: bool
    survival_score: float
    confidence: float
    synthetic_only: bool = True
    notes: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not (0.0 <= self.survival_score <= 1.0):
            raise ValueError("survival_score must be in [0.0, 1.0]")
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError("confidence must be in [0.0, 1.0]")
        if self.synthetic_only is not True:
            raise ValueError("CounterfactualAblationResult.synthetic_only must be True")


def perform_counterfactual_ablation(
    *,
    ablation: CounterfactualAblation,
    causal_refs: Mapping[str, tuple[str, ...]],
    base_pattern_intensity: float,
    ablated_pattern_intensity: float,
) -> CounterfactualAblationResult:
    """Compute an ablation result from base-vs-ablated intensities.

    For pairwise ablations, the causal link is verified; if absent,
    a ValueError is raised. Survival score is a deterministic
    function of the relative intensity preservation.
    """
    if not (0.0 <= base_pattern_intensity <= 1.0):
        raise ValueError("base_pattern_intensity must be in [0.0, 1.0]")
    if not (0.0 <= ablated_pattern_intensity <= 1.0):
        raise ValueError("ablated_pattern_intensity must be in [0.0, 1.0]")

    if ablation.kind is AblationKind.PAIRWISE:
        ev_a, ev_b = ablation.removed_event_ids
        if not validate_pairwise_causal_link(
            event_a_id=ev_a, event_b_id=ev_b, causal_refs=causal_refs
        ):
            raise ValueError(
                f"pairwise ablation {ablation.ablation_id!r} lacks a causal "
                f"link between {ev_a!r} and {ev_b!r}"
            )

    # Survival: high when the pattern intensity is largely preserved
    # after removing the variable; deterministic, bounded.
    if base_pattern_intensity == 0.0:
        survival_score = 0.0
        pattern_survived = False
    else:
        ratio = ablated_pattern_intensity / base_pattern_intensity
        survival_score = max(0.0, min(1.0, ratio))
        pattern_survived = survival_score >= 0.5

    # Confidence: simple bounded mid-band; replay confidence is
    # never claimed truth.
    confidence = 0.5 if pattern_survived else 0.4

    return CounterfactualAblationResult(
        ablation_id=ablation.ablation_id,
        removed_event_ids=ablation.removed_event_ids,
        pattern_survived=pattern_survived,
        survival_score=survival_score,
        confidence=confidence,
    )
