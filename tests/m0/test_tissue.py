"""Tests for the M0 tissue uniform-seed-allocation invariant."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sentinel.m0.tissue import BirthSeedAllocation, allocate_uniform_birth_seeds
from sentinel.types.payload import PrimerPayload


class TestUniformAllocation:
    def test_divisible_count_allocates_uniformly(self) -> None:
        n = len(PrimerPayload)
        alloc = allocate_uniform_birth_seeds(100 * n)
        assert alloc.global_seed_count == 100 * n
        for p in PrimerPayload:
            assert alloc.per_payload[p] == 100

    def test_zero_global_count_rejected(self) -> None:
        with pytest.raises(ValueError):
            allocate_uniform_birth_seeds(0)

    def test_non_divisible_rejected(self) -> None:
        with pytest.raises(ValueError):
            # 99 not divisible by 10 (PrimerPayload count)
            allocate_uniform_birth_seeds(99)


class TestSchemaInvariants:
    def test_missing_payload_rejected(self) -> None:
        prof = {p: 10 for p in PrimerPayload}
        prof.pop(PrimerPayload.URGENCY)
        with pytest.raises(ValidationError):
            BirthSeedAllocation(
                global_seed_count=90,
                per_payload=prof,
            )

    def test_nonzero_divergence_rejected(self) -> None:
        prof = {p: 10 for p in PrimerPayload}
        prof[PrimerPayload.URGENCY] = 11
        with pytest.raises(ValidationError):
            BirthSeedAllocation(
                global_seed_count=sum(prof.values()),
                per_payload=prof,
            )

    def test_sum_mismatch_rejected(self) -> None:
        prof = {p: 10 for p in PrimerPayload}
        with pytest.raises(ValidationError):
            BirthSeedAllocation(
                global_seed_count=999,  # wrong sum
                per_payload=prof,
            )

    def test_zero_per_payload_rejected(self) -> None:
        # Sum=0, divisible OK, but each entry must be > 0
        prof = {p: 0 for p in PrimerPayload}
        with pytest.raises(ValidationError):
            BirthSeedAllocation(global_seed_count=0, per_payload=prof)
