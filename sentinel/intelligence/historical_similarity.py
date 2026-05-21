"""V12 — Historical similarity engine.

Deterministic match of current state against ``ReactionMemoryRecord``
records.  Returns a similarity score, matched pattern refs, expected
reaction band, risk warnings, and confidence.  Never authorises any
action; reaction memory is evidence only.
"""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, Field

from sentinel.intelligence.reaction_memory import (
    InMemoryReactionMemoryStore,
    ReactionMemoryRecord,
    is_record_usable_for_live,
)
from sentinel.intelligence.reaction_taxonomy import (
    HistoricalEventFamily,  # noqa: TC001
    ReactionWindow,  # noqa: TC001
)


@dataclass(frozen=True, slots=True)
class HistoricalSimilarityInput:
    """Inputs to the historical similarity engine."""

    query_id: str
    now_ms: int
    event_family: HistoricalEventFamily
    reaction_window: ReactionWindow
    event_signature_hash: str
    regime_signature_hash: str
    memory_store: InMemoryReactionMemoryStore
    require_usable_for_live: bool = True


class HistoricalSimilarityResult(BaseModel, frozen=True, extra="forbid"):
    """Output of historical similarity matching."""

    query_id: str
    historical_similarity_score: float = Field(ge=0.0, le=1.0)
    matching_pattern_refs: tuple[str, ...] = Field(default_factory=tuple)
    expected_reaction_band: float = Field(ge=-1.0, le=1.0, default=0.0)
    risk_warnings: tuple[str, ...] = Field(default_factory=tuple)
    confidence: float = Field(ge=0.0, le=1.0)


def _hamming_like(a: str, b: str) -> float:
    """Cheap deterministic similarity in [0,1] between two short strings."""
    if a == b:
        return 1.0
    n = max(len(a), len(b))
    if n == 0:
        return 0.0
    common = sum(1 for x, y in zip(a, b, strict=False) if x == y)
    return common / n


def evaluate_historical_similarity(
    inp: HistoricalSimilarityInput,
) -> HistoricalSimilarityResult:
    """Return a deterministic similarity result for the given query."""
    warnings: list[str] = []
    candidates: list[ReactionMemoryRecord] = []

    for record in inp.memory_store.by_family(inp.event_family):
        if record.reaction_window is not inp.reaction_window:
            continue
        if inp.require_usable_for_live and not is_record_usable_for_live(record, now_ms=inp.now_ms):
            continue
        candidates.append(record)

    if not candidates:
        warnings.append("no_matching_pattern_for_event_family_and_window")
        return HistoricalSimilarityResult(
            query_id=inp.query_id,
            historical_similarity_score=0.0,
            matching_pattern_refs=(),
            expected_reaction_band=0.0,
            risk_warnings=tuple(warnings),
            confidence=0.0,
        )

    scored: list[tuple[float, ReactionMemoryRecord]] = []
    for r in candidates:
        ev_sim = _hamming_like(r.event_signature_hash, inp.event_signature_hash)
        re_sim = _hamming_like(r.regime_signature_hash, inp.regime_signature_hash)
        sim = 0.6 * ev_sim + 0.4 * re_sim
        scored.append((sim * r.confidence, r))

    scored.sort(key=lambda t: t[0], reverse=True)
    top = scored[: min(5, len(scored))]
    top_sim_avg = sum(s for s, _ in top) / len(top)

    # Expected reaction band: confidence-weighted average BTC return direction.
    weighted_band = 0.0
    total_weight = 0.0
    for sim_score, rec in top:
        weighted_band += sim_score * rec.market_reaction.btc_return
        total_weight += sim_score
    expected_band = weighted_band / total_weight if total_weight > 0 else 0.0
    expected_band = max(-1.0, min(1.0, expected_band))

    # Low-sample clamp.
    low_sample = all(r.sample_count < 10 for _, r in top)
    if low_sample:
        warnings.append("low_sample_count_clamp")
        top_sim_avg *= 0.5

    confidence = top_sim_avg
    refs = tuple(r.record_id for _, r in top)

    return HistoricalSimilarityResult(
        query_id=inp.query_id,
        historical_similarity_score=top_sim_avg,
        matching_pattern_refs=refs,
        expected_reaction_band=expected_band,
        risk_warnings=tuple(warnings),
        confidence=confidence,
    )


__all__ = [
    "HistoricalSimilarityInput",
    "HistoricalSimilarityResult",
    "evaluate_historical_similarity",
]
