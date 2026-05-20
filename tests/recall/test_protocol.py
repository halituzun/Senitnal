"""Tests for the recall trigger protocol (T §5, §19)."""

from __future__ import annotations

import pytest
from sentinel.recall.protocol import (
    ALLOWED_TRIGGER_SOURCES,
    RecallTriggerInputs,
    RecallTriggerSource,
    check_recall_trigger,
)


def _ideal_inputs(**overrides: object) -> RecallTriggerInputs:
    defaults: dict[str, object] = dict(
        memory_echo_intensity=0.8,
        context_signature_delta=0.6,
        fatigue_trace_intensity=0.1,
        budget_remaining=5,
        global_cooldown_active=False,
        sustained_tension_required=True,
        sustained_tension_observed=True,
    )
    defaults.update(overrides)
    return RecallTriggerInputs(**defaults)  # type: ignore[arg-type]


def _trigger(**kwargs: object) -> object:
    return check_recall_trigger(
        inputs=_ideal_inputs(**kwargs.get("input_overrides", {})),  # type: ignore[arg-type]
        source=kwargs.get("source", RecallTriggerSource.CORE),  # type: ignore[arg-type]
        memory_echo_threshold=kwargs.get("memory_echo_threshold", 0.5),  # type: ignore[arg-type]
        context_signature_delta_threshold=kwargs.get("context_signature_delta_threshold", 0.3),  # type: ignore[arg-type]
        fatigue_trace_max=kwargs.get("fatigue_trace_max", 0.5),  # type: ignore[arg-type]
    )


class TestAllowedSources:
    def test_only_core_in_whitelist(self) -> None:
        assert frozenset({RecallTriggerSource.CORE}) == ALLOWED_TRIGGER_SOURCES


class TestComposite:
    def test_all_ideal_inputs_trigger(self) -> None:
        d = _trigger()  # type: ignore[no-untyped-call]
        assert d.triggered is True  # type: ignore[attr-defined]


class TestRejectedSources:
    @pytest.mark.parametrize(
        "source",
        [
            RecallTriggerSource.HUMAN_DIRECT,
            RecallTriggerSource.LLM,
            RecallTriggerSource.REPLAY,
            RecallTriggerSource.SUMMARIZER,
        ],
    )
    def test_non_core_sources_rejected(self, source: RecallTriggerSource) -> None:
        d = _trigger(source=source)  # type: ignore[no-untyped-call]
        assert d.triggered is False  # type: ignore[attr-defined]
        assert "not in allowed set" in d.reason  # type: ignore[attr-defined]


class TestSustainedTension:
    def test_spike_without_sustained_rejected(self) -> None:
        d = _trigger(
            input_overrides={
                "sustained_tension_required": True,
                "sustained_tension_observed": False,
            }
        )  # type: ignore[no-untyped-call]
        assert d.triggered is False  # type: ignore[attr-defined]
        assert "sustained tension" in d.reason  # type: ignore[attr-defined]


class TestThresholds:
    def test_below_memory_echo_threshold_rejected(self) -> None:
        d = _trigger(
            input_overrides={"memory_echo_intensity": 0.1},
            memory_echo_threshold=0.5,
        )  # type: ignore[no-untyped-call]
        assert d.triggered is False  # type: ignore[attr-defined]

    def test_below_context_delta_threshold_rejected(self) -> None:
        d = _trigger(
            input_overrides={"context_signature_delta": 0.0},
            context_signature_delta_threshold=0.3,
        )  # type: ignore[no-untyped-call]
        assert d.triggered is False  # type: ignore[attr-defined]

    def test_above_fatigue_max_rejected(self) -> None:
        d = _trigger(
            input_overrides={"fatigue_trace_intensity": 0.9},
            fatigue_trace_max=0.5,
        )  # type: ignore[no-untyped-call]
        assert d.triggered is False  # type: ignore[attr-defined]


class TestBudgetAndCooldown:
    def test_zero_budget_rejected(self) -> None:
        d = _trigger(input_overrides={"budget_remaining": 0})  # type: ignore[no-untyped-call]
        assert d.triggered is False  # type: ignore[attr-defined]

    def test_global_cooldown_active_rejected(self) -> None:
        d = _trigger(input_overrides={"global_cooldown_active": True})  # type: ignore[no-untyped-call]
        assert d.triggered is False  # type: ignore[attr-defined]
