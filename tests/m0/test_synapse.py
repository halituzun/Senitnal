"""Tests for the M0 synapse and read-only charge propagation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sentinel.m0.synapse import (
    INITIAL_WEAK_BAND_MAX,
    MVP_LEARNING_ENABLED,
    STABLE_PATH_THRESHOLD,
    Synapse,
    propagate_charge,
)


class TestSynapseConstruction:
    def test_valid_weak_synapse(self) -> None:
        s = Synapse(
            synapse_id="s1",
            presynaptic_neuron_id="n1",
            postsynaptic_neuron_id="n2",
            weight=0.10,
        )
        assert s.weight == 0.10

    def test_zero_weight_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Synapse(
                synapse_id="s1",
                presynaptic_neuron_id="n1",
                postsynaptic_neuron_id="n2",
                weight=0.0,
            )

    def test_above_weak_band_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Synapse(
                synapse_id="s1",
                presynaptic_neuron_id="n1",
                postsynaptic_neuron_id="n2",
                weight=INITIAL_WEAK_BAND_MAX + 0.01,
            )

    def test_self_loop_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Synapse(
                synapse_id="s1",
                presynaptic_neuron_id="n1",
                postsynaptic_neuron_id="n1",
                weight=0.10,
            )

    def test_frozen(self) -> None:
        s = Synapse(
            synapse_id="s1",
            presynaptic_neuron_id="n1",
            postsynaptic_neuron_id="n2",
            weight=0.10,
        )
        with pytest.raises(ValidationError):
            setattr(s, "weight", 0.4)  # noqa: B010


class TestConstants:
    def test_weak_band_below_stable_threshold(self) -> None:
        assert INITIAL_WEAK_BAND_MAX < STABLE_PATH_THRESHOLD

    def test_mvp_learning_is_off(self) -> None:
        assert MVP_LEARNING_ENABLED is False


class TestPropagateCharge:
    def test_propagation_is_product(self) -> None:
        s = Synapse(
            synapse_id="s1",
            presynaptic_neuron_id="n1",
            postsynaptic_neuron_id="n2",
            weight=0.10,
        )
        assert propagate_charge(s, 1.0) == pytest.approx(0.10)
        assert propagate_charge(s, 0.5) == pytest.approx(0.05)

    def test_propagation_read_only(self) -> None:
        s = Synapse(
            synapse_id="s1",
            presynaptic_neuron_id="n1",
            postsynaptic_neuron_id="n2",
            weight=0.10,
        )
        before = s.weight
        propagate_charge(s, 0.7)
        assert s.weight == before  # unchanged

    def test_charge_out_of_range_rejected(self) -> None:
        s = Synapse(
            synapse_id="s1",
            presynaptic_neuron_id="n1",
            postsynaptic_neuron_id="n2",
            weight=0.10,
        )
        with pytest.raises(ValueError):
            propagate_charge(s, -0.1)
        with pytest.raises(ValueError):
            propagate_charge(s, 1.1)
