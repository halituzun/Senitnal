"""Tests for the M0 proto-resonance 5-layer invariant (S §9)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sentinel.m0.proto_resonance import (
    ASSEMBLY_STABILIZATION_THRESHOLD,
    STABLE_ASSEMBLY_MIN_PERSISTENCE_MS,
    ProtoResonance,
)


def _at_birth(**overrides: object) -> ProtoResonance:
    defaults: dict[str, object] = dict(
        pattern_id="pr-1",
        recallability=0.0,
        assembly_id_at_birth=None,
        persistence_max_ms=1000,
        stability_score_cap=0.5,
        memory_write_eligibility=False,
    )
    defaults.update(overrides)
    return ProtoResonance(**defaults)  # type: ignore[arg-type]


class TestValidAtBirth:
    def test_default_passes(self) -> None:
        pr = _at_birth()
        assert pr.recallability == 0.0
        assert pr.assembly_id_at_birth is None
        assert pr.memory_write_eligibility is False


class TestLayer1Recallability:
    def test_nonzero_recallability_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _at_birth(recallability=0.01)


class TestLayer2AssemblyIdAtBirth:
    def test_assembly_id_string_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _at_birth(assembly_id_at_birth="ass-1")


class TestLayer3Persistence:
    def test_at_stable_threshold_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _at_birth(persistence_max_ms=STABLE_ASSEMBLY_MIN_PERSISTENCE_MS)

    def test_above_stable_threshold_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _at_birth(persistence_max_ms=STABLE_ASSEMBLY_MIN_PERSISTENCE_MS + 1)

    def test_below_stable_threshold_accepted(self) -> None:
        _at_birth(persistence_max_ms=STABLE_ASSEMBLY_MIN_PERSISTENCE_MS - 1)


class TestLayer4StabilityScore:
    def test_at_threshold_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _at_birth(stability_score_cap=ASSEMBLY_STABILIZATION_THRESHOLD)

    def test_above_threshold_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _at_birth(stability_score_cap=ASSEMBLY_STABILIZATION_THRESHOLD + 0.01)

    def test_below_threshold_accepted(self) -> None:
        _at_birth(stability_score_cap=ASSEMBLY_STABILIZATION_THRESHOLD - 0.01)


class TestLayer5MemoryWriteEligibility:
    def test_true_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _at_birth(memory_write_eligibility=True)
