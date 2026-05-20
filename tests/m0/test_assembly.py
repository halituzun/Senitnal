"""Tests for the M0 Assembly + AssemblyCensus invariants."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sentinel.m0.assembly import Assembly, AssemblyCensus


class TestAssembly:
    def test_valid_candidate(self) -> None:
        a = Assembly(
            assembly_id="ass-1",
            candidate_member_neuron_ids=("n1", "n2"),
        )
        assert a.is_stable is False
        assert a.is_recallable is False

    def test_empty_members_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Assembly(assembly_id="ass-1", candidate_member_neuron_ids=())

    def test_duplicate_members_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Assembly(
                assembly_id="ass-1",
                candidate_member_neuron_ids=("n1", "n1"),
            )

    @pytest.mark.parametrize(
        "field",
        ["is_stable", "is_recallable", "is_memory_write_eligible"],
    )
    def test_at_birth_flag_must_be_false(self, field: str) -> None:
        kwargs: dict[str, object] = {
            "assembly_id": "ass-1",
            "candidate_member_neuron_ids": ("n1",),
            field: True,
        }
        with pytest.raises(ValidationError):
            Assembly(**kwargs)  # type: ignore[arg-type]


class TestAssemblyCensus:
    def test_zero_everything_accepted(self) -> None:
        c = AssemblyCensus(
            candidate_assembly_count=0,
            stable_assembly_count=0,
            recallable_assembly_count=0,
            memory_write_eligible_assembly_count=0,
        )
        assert c.candidate_assembly_count == 0

    def test_nonzero_candidate_accepted(self) -> None:
        AssemblyCensus(
            candidate_assembly_count=5,
            stable_assembly_count=0,
            recallable_assembly_count=0,
            memory_write_eligible_assembly_count=0,
        )

    @pytest.mark.parametrize(
        "field",
        [
            "stable_assembly_count",
            "recallable_assembly_count",
            "memory_write_eligible_assembly_count",
        ],
    )
    def test_nonzero_at_birth_count_rejected(self, field: str) -> None:
        kwargs: dict[str, int] = {
            "candidate_assembly_count": 0,
            "stable_assembly_count": 0,
            "recallable_assembly_count": 0,
            "memory_write_eligible_assembly_count": 0,
        }
        kwargs[field] = 1
        with pytest.raises(ValidationError):
            AssemblyCensus(**kwargs)
