"""Recall candidate ranking — mechanical multiplicative score (T §8).

Per RECALL_PROTOCOL.md §8 and the Phase 8 build plan: the ranking
function is mechanical and deterministic. No LLM input, no semantic
similarity.

    score = status_weight
          * provenance_strength
          * freshness_dampening
          * (1.0 - contradiction_penalty)
          * (1.0 - habituation_penalty)
          * scope_match_score

All inputs are in [0.0, 1.0]; output is in [0.0, 1.0].

Constitutional discipline:
    - Top-1 only at the core boundary (T §5). `select_top_one`
      returns at most ONE record; multi-record APIs are forbidden
    - Tie-breaking: stable — when two candidates have identical
      scores, the one with the earlier (lexicographically smaller)
      record_id wins
"""

from __future__ import annotations

from collections.abc import Sequence  # noqa: TC003 (runtime annotation)
from dataclasses import dataclass

from sentinel.types.memory import MemoryRecord  # noqa: TC001 (runtime)


@dataclass(frozen=True, slots=True)
class RankingInputs:
    """Per-candidate scoring inputs. Each in [0.0, 1.0]."""

    status_weight: float
    provenance_strength: float
    freshness_dampening: float
    contradiction_penalty: float
    habituation_penalty: float
    scope_match_score: float

    def __post_init__(self) -> None:
        for name in (
            "status_weight",
            "provenance_strength",
            "freshness_dampening",
            "contradiction_penalty",
            "habituation_penalty",
            "scope_match_score",
        ):
            v = getattr(self, name)
            if not (0.0 <= v <= 1.0):
                raise ValueError(f"RankingInputs.{name}={v!r} outside [0.0, 1.0]")


def compute_recall_score(inputs: RankingInputs) -> float:
    """Multiplicative score in [0.0, 1.0]."""
    return (
        inputs.status_weight
        * inputs.provenance_strength
        * inputs.freshness_dampening
        * (1.0 - inputs.contradiction_penalty)
        * (1.0 - inputs.habituation_penalty)
        * inputs.scope_match_score
    )


def select_top_one(
    scored_candidates: Sequence[tuple[MemoryRecord, float]],
) -> MemoryRecord | None:
    """Return the single top candidate (or None if list is empty).

    Tie-break: when scores are equal, the record with the smaller
    record_id wins (stable, deterministic).
    """
    if not scored_candidates:
        return None
    best = sorted(scored_candidates, key=lambda x: (-x[1], x[0].record_id))[0]
    return best[0]
