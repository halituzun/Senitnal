"""V4 — Counterfactual ablation + replay survival tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sentinel.replay.counterfactual import (
    AblationKind,
    CounterfactualAblation,
    CounterfactualAblationResult,
    perform_counterfactual_ablation,
    validate_pairwise_causal_link,
)
from sentinel.replay.survival import (
    ReplaySurvivalEvidence,
    compute_replay_survival_score,
)


class TestCounterfactualAblation:
    def test_single_valid(self) -> None:
        CounterfactualAblation(
            ablation_id="a1",
            session_id="s1",
            kind=AblationKind.SINGLE_VARIABLE,
            removed_event_ids=("ev-1",),
            causal_link_required=False,
            created_at_ms=0,
        )

    def test_single_with_two_events_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CounterfactualAblation(
                ablation_id="a1",
                session_id="s1",
                kind=AblationKind.SINGLE_VARIABLE,
                removed_event_ids=("ev-1", "ev-2"),
                causal_link_required=False,
                created_at_ms=0,
            )

    def test_pairwise_requires_causal_link_flag(self) -> None:
        with pytest.raises(ValidationError):
            CounterfactualAblation(
                ablation_id="a1",
                session_id="s1",
                kind=AblationKind.PAIRWISE,
                removed_event_ids=("ev-1", "ev-2"),
                causal_link_required=False,
                created_at_ms=0,
            )

    def test_pairwise_with_one_event_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CounterfactualAblation(
                ablation_id="a1",
                session_id="s1",
                kind=AblationKind.PAIRWISE,
                removed_event_ids=("ev-1",),
                causal_link_required=True,
                created_at_ms=0,
            )

    def test_triple_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CounterfactualAblation(
                ablation_id="a1",
                session_id="s1",
                kind=AblationKind.SINGLE_VARIABLE,
                removed_event_ids=("ev-1", "ev-2", "ev-3"),
                causal_link_required=False,
                created_at_ms=0,
            )


class TestPairwiseCausalLink:
    def test_a_references_b(self) -> None:
        assert validate_pairwise_causal_link(
            event_a_id="a", event_b_id="b", causal_refs={"a": ("b",)}
        )

    def test_b_references_a(self) -> None:
        assert validate_pairwise_causal_link(
            event_a_id="a", event_b_id="b", causal_refs={"b": ("a",)}
        )

    def test_shared_parent(self) -> None:
        assert validate_pairwise_causal_link(
            event_a_id="a",
            event_b_id="b",
            causal_refs={"a": ("p",), "b": ("p",)},
        )

    def test_no_link_returns_false(self) -> None:
        assert not validate_pairwise_causal_link(
            event_a_id="a", event_b_id="b", causal_refs={"a": ("x",)}
        )

    def test_same_event_returns_false(self) -> None:
        assert not validate_pairwise_causal_link(
            event_a_id="a", event_b_id="a", causal_refs={"a": ("a",)}
        )


class TestPerformCounterfactualAblation:
    def test_pattern_survives(self) -> None:
        ablation = CounterfactualAblation(
            ablation_id="a1",
            session_id="s1",
            kind=AblationKind.SINGLE_VARIABLE,
            removed_event_ids=("ev-1",),
            causal_link_required=False,
            created_at_ms=0,
        )
        r = perform_counterfactual_ablation(
            ablation=ablation,
            causal_refs={},
            base_pattern_intensity=0.8,
            ablated_pattern_intensity=0.75,
        )
        assert r.pattern_survived is True
        assert 0.0 <= r.survival_score <= 1.0
        assert r.synthetic_only is True

    def test_pattern_collapses(self) -> None:
        ablation = CounterfactualAblation(
            ablation_id="a1",
            session_id="s1",
            kind=AblationKind.SINGLE_VARIABLE,
            removed_event_ids=("ev-1",),
            causal_link_required=False,
            created_at_ms=0,
        )
        r = perform_counterfactual_ablation(
            ablation=ablation,
            causal_refs={},
            base_pattern_intensity=0.8,
            ablated_pattern_intensity=0.1,
        )
        assert r.pattern_survived is False

    def test_pairwise_requires_causal_link_at_runtime(self) -> None:
        ablation = CounterfactualAblation(
            ablation_id="a1",
            session_id="s1",
            kind=AblationKind.PAIRWISE,
            removed_event_ids=("ev-1", "ev-2"),
            causal_link_required=True,
            created_at_ms=0,
        )
        with pytest.raises(ValueError, match="lacks a causal link"):
            perform_counterfactual_ablation(
                ablation=ablation,
                causal_refs={},
                base_pattern_intensity=0.8,
                ablated_pattern_intensity=0.5,
            )

    def test_synthetic_only_required(self) -> None:
        with pytest.raises(ValueError, match="synthetic_only"):
            CounterfactualAblationResult(
                ablation_id="a",
                removed_event_ids=("e",),
                pattern_survived=True,
                survival_score=0.5,
                confidence=0.5,
                synthetic_only=False,
            )


class TestSurvivalScore:
    def test_empty_returns_zero(self) -> None:
        assert compute_replay_survival_score(()) == 0.0

    def test_bounded(self) -> None:
        results = (
            CounterfactualAblationResult(
                ablation_id="a1",
                removed_event_ids=("e1",),
                pattern_survived=True,
                survival_score=0.7,
                confidence=0.5,
            ),
            CounterfactualAblationResult(
                ablation_id="a2",
                removed_event_ids=("e2",),
                pattern_survived=True,
                survival_score=0.6,
                confidence=0.5,
            ),
        )
        s = compute_replay_survival_score(results)
        assert 0.0 <= s <= 1.0
        assert s == pytest.approx(0.65)

    def test_deterministic(self) -> None:
        results = (
            CounterfactualAblationResult(
                ablation_id="a1",
                removed_event_ids=("e1",),
                pattern_survived=True,
                survival_score=0.5,
                confidence=0.5,
            ),
        )
        a = compute_replay_survival_score(results)
        b = compute_replay_survival_score(results)
        assert a == b


class TestReplaySurvivalEvidence:
    def test_synthetic_only_must_be_true(self) -> None:
        with pytest.raises(ValidationError):
            ReplaySurvivalEvidence(
                evidence_id="e1",
                session_id="s1",
                memory_record_id="m1",
                ablation_ids=("a1",),
                survival_score=0.5,
                min_sessions_satisfied=False,
                session_separation_ms=0,
                synthetic_only=False,
                created_at_ms=0,
            )

    def test_empty_ablation_ids_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ReplaySurvivalEvidence(
                evidence_id="e1",
                session_id="s1",
                memory_record_id="m1",
                ablation_ids=(),
                survival_score=0.5,
                min_sessions_satisfied=True,
                session_separation_ms=0,
                created_at_ms=0,
            )

    def test_min_sessions_false_construct_ok(self) -> None:
        # The schema accepts min_sessions_satisfied=False; the gate
        # wrapper is responsible for refusing to use it.
        ReplaySurvivalEvidence(
            evidence_id="e1",
            session_id="s1",
            memory_record_id="m1",
            ablation_ids=("a1",),
            survival_score=0.5,
            min_sessions_satisfied=False,
            session_separation_ms=0,
            created_at_ms=0,
        )
