"""Tests for the trapezoidal soft-overlap membership function."""

from __future__ import annotations

import math

import pytest
from pydantic import ValidationError
from sentinel.ingress.soft_overlap import FuzzyBand, membership


class TestBandConstruction:
    def test_valid_trapezoid_accepted(self) -> None:
        b = FuzzyBand(low=0.0, peak_low=0.3, peak_high=0.7, high=1.0)
        assert b.peak_low == 0.3

    def test_triangular_accepted(self) -> None:
        b = FuzzyBand(low=0.0, peak_low=0.5, peak_high=0.5, high=1.0)
        assert b.peak_low == b.peak_high

    def test_non_monotone_rejected(self) -> None:
        with pytest.raises(ValidationError):
            FuzzyBand(low=0.5, peak_low=0.3, peak_high=0.7, high=1.0)
        with pytest.raises(ValidationError):
            FuzzyBand(low=0.0, peak_low=0.7, peak_high=0.3, high=1.0)
        with pytest.raises(ValidationError):
            FuzzyBand(low=0.0, peak_low=0.3, peak_high=0.7, high=0.5)

    def test_nan_inf_rejected(self) -> None:
        with pytest.raises(ValidationError):
            FuzzyBand(low=float("nan"), peak_low=0.3, peak_high=0.7, high=1.0)
        with pytest.raises(ValidationError):
            FuzzyBand(low=0.0, peak_low=0.3, peak_high=0.7, high=float("inf"))

    def test_frozen(self) -> None:
        b = FuzzyBand(low=0.0, peak_low=0.3, peak_high=0.7, high=1.0)
        with pytest.raises(ValidationError):
            setattr(b, "low", 0.1)  # noqa: B010


class TestMembership:
    @pytest.fixture
    def band(self) -> FuzzyBand:
        return FuzzyBand(low=0.0, peak_low=0.3, peak_high=0.7, high=1.0)

    def test_below_low_is_zero(self, band: FuzzyBand) -> None:
        assert membership(band, -0.1) == 0.0
        assert membership(band, -100.0) == 0.0

    def test_above_high_is_zero(self, band: FuzzyBand) -> None:
        assert membership(band, 1.5) == 0.0
        assert membership(band, 100.0) == 0.0

    def test_strictly_at_low_is_zero(self, band: FuzzyBand) -> None:
        assert membership(band, 0.0) == 0.0

    def test_strictly_at_high_is_zero(self, band: FuzzyBand) -> None:
        assert membership(band, 1.0) == 0.0

    def test_in_plateau_is_one(self, band: FuzzyBand) -> None:
        assert membership(band, 0.3) == 1.0
        assert membership(band, 0.5) == 1.0
        assert membership(band, 0.7) == 1.0

    def test_rising_edge_midpoint(self, band: FuzzyBand) -> None:
        # Halfway between low=0.0 and peak_low=0.3 → 0.5
        assert math.isclose(membership(band, 0.15), 0.5)

    def test_falling_edge_midpoint(self, band: FuzzyBand) -> None:
        # Halfway between peak_high=0.7 and high=1.0 → 0.5
        assert math.isclose(membership(band, 0.85), 0.5)


class TestDeterminism:
    def test_same_input_same_output(self) -> None:
        b = FuzzyBand(low=0.0, peak_low=0.4, peak_high=0.6, high=1.0)
        for v in (0.1, 0.25, 0.5, 0.8, 0.95):
            assert membership(b, v) == membership(b, v)


class TestVerticalShoulders:
    def test_vertical_left_edge_membership_one_at_peak_low(self) -> None:
        # peak_low == low → vertical left edge
        b = FuzzyBand(low=0.5, peak_low=0.5, peak_high=0.8, high=1.0)
        assert membership(b, 0.5) == 1.0
        assert membership(b, 0.499) == 0.0
        assert membership(b, 0.8) == 1.0

    def test_vertical_right_edge_membership_one_at_peak_high(self) -> None:
        # peak_high == high → vertical right edge
        b = FuzzyBand(low=0.0, peak_low=0.3, peak_high=0.7, high=0.7)
        assert membership(b, 0.7) == 1.0
        assert membership(b, 0.701) == 0.0


class TestTriangular:
    def test_triangular_peak(self) -> None:
        b = FuzzyBand(low=0.0, peak_low=0.5, peak_high=0.5, high=1.0)
        assert membership(b, 0.5) == 1.0
        assert math.isclose(membership(b, 0.25), 0.5)
        assert math.isclose(membership(b, 0.75), 0.5)
