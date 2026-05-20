"""Tests for the recall ranking + top-1 selector."""

from __future__ import annotations

import pytest
from sentinel.recall.ranking import (
    RankingInputs,
    compute_recall_score,
    select_top_one,
)
from sentinel.types.memory import MemoryRecord, MemoryRecordStatus, SubjectClass
from sentinel.types.neural_seed import ProvenanceRef


def _record(record_id: str) -> MemoryRecord:
    return MemoryRecord(
        record_id=record_id,
        subject_class=SubjectClass.SOURCE_TRUST,
        payload={"k": "v"},
        status=MemoryRecordStatus.CANDIDATE,
        created_at_ms=1,
        last_status_change_ms=1,
        provenance=ProvenanceRef(source_event_id="src"),
    )


class TestRankingInputs:
    def test_all_one_max_score(self) -> None:
        score = compute_recall_score(
            RankingInputs(
                status_weight=1.0,
                provenance_strength=1.0,
                freshness_dampening=1.0,
                contradiction_penalty=0.0,
                habituation_penalty=0.0,
                scope_match_score=1.0,
            )
        )
        assert score == 1.0

    def test_any_zero_factor_zero_score(self) -> None:
        score = compute_recall_score(
            RankingInputs(
                status_weight=0.0,
                provenance_strength=1.0,
                freshness_dampening=1.0,
                contradiction_penalty=0.0,
                habituation_penalty=0.0,
                scope_match_score=1.0,
            )
        )
        assert score == 0.0

    def test_full_contradiction_zero_score(self) -> None:
        score = compute_recall_score(
            RankingInputs(
                status_weight=1.0,
                provenance_strength=1.0,
                freshness_dampening=1.0,
                contradiction_penalty=1.0,
                habituation_penalty=0.0,
                scope_match_score=1.0,
            )
        )
        assert score == 0.0

    def test_out_of_range_input_rejected(self) -> None:
        with pytest.raises(ValueError):
            RankingInputs(
                status_weight=1.5,
                provenance_strength=1.0,
                freshness_dampening=1.0,
                contradiction_penalty=0.0,
                habituation_penalty=0.0,
                scope_match_score=1.0,
            )


class TestTopOne:
    def test_empty_returns_none(self) -> None:
        assert select_top_one(()) is None

    def test_single_returns_only(self) -> None:
        r = _record("a")
        assert select_top_one(((r, 0.5),)) is r

    def test_returns_highest_score(self) -> None:
        a = _record("a")
        b = _record("b")
        c = _record("c")
        out = select_top_one([(a, 0.2), (b, 0.9), (c, 0.5)])
        assert out is b

    def test_tie_breaks_on_smaller_record_id(self) -> None:
        a = _record("apple")
        b = _record("banana")
        out = select_top_one([(b, 0.5), (a, 0.5)])
        assert out is a  # "apple" < "banana"
