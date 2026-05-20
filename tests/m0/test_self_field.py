"""Tests for the M0 embryo self-field hierarchy."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sentinel.m0.self_field import EmbryoSelfField


class TestValid:
    def test_strict_descending_accepted(self) -> None:
        sf = EmbryoSelfField(
            homeostatic_weight=0.5,
            predictive_weight=0.3,
            narrative_weight=0.1,
        )
        assert sf.homeostatic_weight > sf.predictive_weight > sf.narrative_weight


class TestHierarchy:
    def test_equal_weights_rejected(self) -> None:
        with pytest.raises(ValidationError):
            EmbryoSelfField(
                homeostatic_weight=0.3,
                predictive_weight=0.3,
                narrative_weight=0.3,
            )

    def test_predictive_above_homeostatic_rejected(self) -> None:
        with pytest.raises(ValidationError):
            EmbryoSelfField(
                homeostatic_weight=0.2,
                predictive_weight=0.4,
                narrative_weight=0.1,
            )

    def test_narrative_above_predictive_rejected(self) -> None:
        with pytest.raises(ValidationError):
            EmbryoSelfField(
                homeostatic_weight=0.5,
                predictive_weight=0.1,
                narrative_weight=0.3,
            )


class TestBudget:
    def test_sum_above_one_rejected(self) -> None:
        with pytest.raises(ValidationError):
            EmbryoSelfField(
                homeostatic_weight=0.5,
                predictive_weight=0.4,
                narrative_weight=0.2,  # 1.1 total
            )

    def test_sum_equal_one_accepted(self) -> None:
        EmbryoSelfField(
            homeostatic_weight=0.5,
            predictive_weight=0.3,
            narrative_weight=0.2,
        )


class TestNonPositiveRejected:
    @pytest.mark.parametrize(
        ("h", "p", "n"),
        [
            (0.0, 0.0, 0.0),
            (-0.1, 0.3, 0.1),
            (0.5, 0.0, 0.1),
            (0.5, 0.3, 0.0),
        ],
    )
    def test_nonpositive_rejected(self, h: float, p: float, n: float) -> None:
        with pytest.raises(ValidationError):
            EmbryoSelfField(
                homeostatic_weight=h,
                predictive_weight=p,
                narrative_weight=n,
            )


class TestFrozen:
    def test_frozen(self) -> None:
        sf = EmbryoSelfField(
            homeostatic_weight=0.5,
            predictive_weight=0.3,
            narrative_weight=0.1,
        )
        with pytest.raises(ValidationError):
            setattr(sf, "homeostatic_weight", 0.6)  # noqa: B010
