"""Tests for the event-profile cap hierarchy."""

from __future__ import annotations

import pytest
from sentinel.constitution.violations import NumericsGovernanceViolation
from sentinel.ingress.profile_caps import (
    PROFILE_CAPS,
    PROFILE_RANK,
    apply_profile_cap,
    cap_for,
)
from sentinel.types.neural_seed import EventProfile


class TestRankAndCaps:
    def test_all_profiles_have_a_cap(self) -> None:
        assert set(PROFILE_CAPS.keys()) == set(EventProfile)

    def test_rank_covers_all_profiles(self) -> None:
        assert set(PROFILE_RANK) == set(EventProfile)

    def test_rank_order_is_monotone_non_increasing(self) -> None:
        from itertools import pairwise

        caps = [PROFILE_CAPS[p] for p in PROFILE_RANK]
        for a, b in pairwise(caps):
            assert a >= b

    def test_observation_is_highest(self) -> None:
        assert PROFILE_RANK[0] is EventProfile.OBSERVATION_EVENT

    def test_candidate_recall_is_lowest(self) -> None:
        assert PROFILE_RANK[-1] is EventProfile.CANDIDATE_RECALL

    def test_specific_cap_values(self) -> None:
        assert cap_for(EventProfile.OBSERVATION_EVENT) == 1.00
        assert cap_for(EventProfile.INTERNAL_SHOCK_EVENT) == 0.90
        assert cap_for(EventProfile.RECALL_EVENT_ACTIVE) == 0.70
        assert cap_for(EventProfile.RECALL_EVENT_VERIFIED) == 0.60
        assert cap_for(EventProfile.HUMAN_INTENT_EVENT) == 0.35
        assert cap_for(EventProfile.CANDIDATE_RECALL) == 0.20


class TestApplyCap:
    def test_below_cap_returned_unchanged(self) -> None:
        assert apply_profile_cap(EventProfile.HUMAN_INTENT_EVENT, 0.20) == 0.20

    def test_above_cap_clamped(self) -> None:
        assert apply_profile_cap(EventProfile.HUMAN_INTENT_EVENT, 0.9) == 0.35

    def test_equal_to_cap_returns_cap(self) -> None:
        assert apply_profile_cap(EventProfile.HUMAN_INTENT_EVENT, 0.35) == 0.35

    def test_zero_intensity_returned_zero(self) -> None:
        assert apply_profile_cap(EventProfile.OBSERVATION_EVENT, 0.0) == 0.0

    def test_negative_intensity_raises(self) -> None:
        with pytest.raises(NumericsGovernanceViolation) as exc_info:
            apply_profile_cap(EventProfile.OBSERVATION_EVENT, -0.01)
        assert exc_info.value.violation_code == "INGRESS_PROFILE_CAP_INPUT_INVALID"

    def test_above_one_intensity_raises(self) -> None:
        with pytest.raises(NumericsGovernanceViolation) as exc_info:
            apply_profile_cap(EventProfile.OBSERVATION_EVENT, 1.01)
        assert exc_info.value.violation_code == "INGRESS_PROFILE_CAP_INPUT_INVALID"
