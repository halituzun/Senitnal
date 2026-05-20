"""Tests for the M0 neuron model."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sentinel.m0.neuron import HOMONYMOUS_BIAS_EPSILON_MAX, Neuron
from sentinel.types.payload import PrimerPayload


def _uniform_profile(value: float = 1.0) -> dict[PrimerPayload, float]:
    return {p: value for p in PrimerPayload}


class TestValidNeuron:
    def test_uniform_profile_accepted(self) -> None:
        n = Neuron(
            neuron_id="n1",
            homonymous_bias_epsilon=0.05,
            receptor_profile=_uniform_profile(1.0),
        )
        assert n.neuron_id == "n1"

    def test_slight_bias_within_epsilon_accepted(self) -> None:
        prof = _uniform_profile(1.0)
        prof[PrimerPayload.URGENCY] = 1.05
        prof[PrimerPayload.NOVELTY] = 0.95
        Neuron(
            neuron_id="n1",
            homonymous_bias_epsilon=0.05,
            receptor_profile=prof,
        )


class TestEpsilonBounds:
    def test_epsilon_zero_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Neuron(
                neuron_id="n1",
                homonymous_bias_epsilon=0.0,
                receptor_profile=_uniform_profile(1.0),
            )

    def test_epsilon_above_max_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Neuron(
                neuron_id="n1",
                homonymous_bias_epsilon=HOMONYMOUS_BIAS_EPSILON_MAX + 0.01,
                receptor_profile=_uniform_profile(1.0),
            )


class TestReceptorCoverage:
    def test_missing_payload_rejected(self) -> None:
        prof = _uniform_profile(1.0)
        prof.pop(PrimerPayload.URGENCY)
        with pytest.raises(ValidationError):
            Neuron(
                neuron_id="n1",
                homonymous_bias_epsilon=0.05,
                receptor_profile=prof,
            )


class TestNoSpecialist:
    def test_outside_epsilon_band_rejected(self) -> None:
        prof = _uniform_profile(1.0)
        prof[PrimerPayload.URGENCY] = 1.5  # way above 1+epsilon
        with pytest.raises(ValidationError):
            Neuron(
                neuron_id="n1",
                homonymous_bias_epsilon=0.05,
                receptor_profile=prof,
            )


class TestFrozen:
    def test_frozen(self) -> None:
        n = Neuron(
            neuron_id="n1",
            homonymous_bias_epsilon=0.05,
            receptor_profile=_uniform_profile(1.0),
        )
        with pytest.raises(ValidationError):
            setattr(n, "neuron_id", "other")  # noqa: B010
