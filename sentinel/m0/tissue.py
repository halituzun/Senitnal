"""M0 tissue: uniform per-primer-payload seed allocation at birth.

Per BOOTSTRAP_GENOME.md §S and BOOTSTRAP_GENOME_NUMERICS.md §8: the
embryo tissue at birth is allocated by sampling a single
`global_seed_count`, then distributing it uniformly across all 10
primer payloads. The per-payload divergence must be exactly 0 — no
payload may have more or fewer seeds than any other at birth.

Constitutional invariants:
    - per_payload_seed_count_divergence_at_birth_max == 0
    - global_seed_count > 0 and divisible by len(PrimerPayload)
    - No domain-specific seed allocation (no symbol / venue tagging)
"""

from __future__ import annotations

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sentinel.types.payload import PrimerPayload

PER_PAYLOAD_SEED_COUNT_DIVERGENCE_AT_BIRTH_MAX: int = 0


class BirthSeedAllocation(BaseModel):
    """Per-primer-payload seed allocation snapshot at tissue birth."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    global_seed_count: int = Field(gt=0)
    per_payload: dict[PrimerPayload, int]

    @model_validator(mode="after")
    def _validate_full_coverage(self) -> Self:
        if set(self.per_payload.keys()) != set(PrimerPayload):
            missing = set(PrimerPayload) - set(self.per_payload.keys())
            raise ValueError(
                f"per_payload must cover all PrimerPayload values "
                f"(missing={sorted(p.value for p in missing)!r})"
            )
        return self

    @model_validator(mode="after")
    def _validate_global_sum(self) -> Self:
        s = sum(self.per_payload.values())
        if s != self.global_seed_count:
            raise ValueError(f"per_payload sum {s} != global_seed_count {self.global_seed_count}")
        return self

    @model_validator(mode="after")
    def _validate_zero_divergence(self) -> Self:
        counts = list(self.per_payload.values())
        divergence = max(counts) - min(counts)
        if divergence > PER_PAYLOAD_SEED_COUNT_DIVERGENCE_AT_BIRTH_MAX:
            raise ValueError(
                f"per-payload seed count divergence {divergence} > "
                f"{PER_PAYLOAD_SEED_COUNT_DIVERGENCE_AT_BIRTH_MAX} "
                f"(BOOTSTRAP_GENOME_NUMERICS.md §8)"
            )
        return self

    @model_validator(mode="after")
    def _validate_positive_per_payload(self) -> Self:
        for payload, count in self.per_payload.items():
            if count <= 0:
                raise ValueError(f"per_payload[{payload.value!r}] = {count}; must be > 0")
        return self


def allocate_uniform_birth_seeds(global_seed_count: int) -> BirthSeedAllocation:
    """Distribute `global_seed_count` uniformly across all primer payloads.

    Requires `global_seed_count` to be divisible by len(PrimerPayload).
    Raises ValueError otherwise (the distribution would have a non-zero
    divergence, violating the at-birth invariant).
    """
    n_payloads = len(PrimerPayload)
    if global_seed_count <= 0:
        raise ValueError(f"global_seed_count must be > 0; got {global_seed_count}")
    if global_seed_count % n_payloads != 0:
        raise ValueError(
            f"global_seed_count {global_seed_count} must be divisible "
            f"by {n_payloads} to satisfy zero-divergence invariant"
        )
    per = global_seed_count // n_payloads
    return BirthSeedAllocation(
        global_seed_count=global_seed_count,
        per_payload={p: per for p in PrimerPayload},
    )
