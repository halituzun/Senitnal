"""M0 assembly stubs + at-birth zero-count invariants.

Per BOOTSTRAP_GENOME.md §S and BOOTSTRAP_GENOME_NUMERICS.md §8-9:
the MVP tissue contains zero stable assemblies, zero recallable
assemblies, and zero memory-write-eligible assemblies at birth. This
module pins those three counts as constitutional invariants checked
by `AssemblyCensus` at construction time.

Constitutional discipline:
    - stable_assembly_count_at_birth == 0
    - initial_recallable_assembly_count == 0
    - initial_memory_write_eligible_assembly_count == 0
    - candidate_assembly_count >= 0 (no upper bound here; the
      birth-time tissue is allowed to surface candidate patterns,
      but none of them are stable / recallable / memory-eligible)
    - The `Assembly` record itself is a passive struct (id +
      candidate_member_neuron_ids tuple) — there is no stabilization
      logic in MVP (S §20 learning = OFF)
"""

from __future__ import annotations

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Assembly(BaseModel):
    """One candidate assembly (no stabilization in MVP)."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    assembly_id: str = Field(min_length=1)
    candidate_member_neuron_ids: tuple[str, ...]
    is_stable: bool = False
    is_recallable: bool = False
    is_memory_write_eligible: bool = False

    @model_validator(mode="after")
    def _validate_member_ids_non_empty(self) -> Self:
        if len(self.candidate_member_neuron_ids) == 0:
            raise ValueError("candidate_member_neuron_ids must be non-empty for an assembly record")
        if len(set(self.candidate_member_neuron_ids)) != len(self.candidate_member_neuron_ids):
            raise ValueError("candidate_member_neuron_ids must be unique")
        return self

    @model_validator(mode="after")
    def _validate_at_birth_flags(self) -> Self:
        # MVP learning is OFF; no birth-time assembly may already be
        # stable, recallable, or memory-write eligible.
        if self.is_stable:
            raise ValueError("MVP: Assembly.is_stable must be False at birth")
        if self.is_recallable:
            raise ValueError("MVP: Assembly.is_recallable must be False at birth")
        if self.is_memory_write_eligible:
            raise ValueError("MVP: Assembly.is_memory_write_eligible must be False at birth")
        return self


class AssemblyCensus(BaseModel):
    """Tissue-wide assembly counts subject to at-birth zero invariants."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    candidate_assembly_count: int = Field(ge=0)
    stable_assembly_count: int = Field(ge=0)
    recallable_assembly_count: int = Field(ge=0)
    memory_write_eligible_assembly_count: int = Field(ge=0)

    @model_validator(mode="after")
    def _validate_zero_at_birth_counts(self) -> Self:
        if self.stable_assembly_count != 0:
            raise ValueError("MVP: stable_assembly_count must be 0 at birth (S §8)")
        if self.recallable_assembly_count != 0:
            raise ValueError("MVP: recallable_assembly_count must be 0 at birth (S §9)")
        if self.memory_write_eligible_assembly_count != 0:
            raise ValueError("MVP: memory_write_eligible_assembly_count must be 0 at birth (S §9)")
        return self
