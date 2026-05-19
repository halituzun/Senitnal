"""PayloadSeed — the smallest constitutional code unit.

Per MEMORY_CONTRACT §3 + WORLD_INGRESS §6-11 + INGRESS_COMPILER_NUMERICS §6:

The primer payload palette is the **closed set** of 10 constitutional
"mental colors" that the core can experience. Payloads are NOT tasks,
NOT commands, NOT domain labels (no BTC, BTCUSDT, BUY, SELL, TRADE).

A PayloadSeed is one color of one event at one intensity. The compiler
combines PayloadSeeds into a NeuralSeed (see neural_seed.py, next commit).

Constitutional rules enforced here:
    - Closed palette (10 values; extra payload kinds rejected at type boundary)
    - Bounded finite intensity in [0.0, 1.0]
    - NaN / +inf / -inf rejected
    - Extra fields rejected (Pydantic extra="forbid")
    - Immutable (frozen=True)
    - Strict type matching (no string→float coercion for intensity)

This module deliberately contains no compiler logic, no profile cap math,
no normalization. Those live in `sentinel/ingress/compiler.py` (Phase 4).
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class PrimerPayload(StrEnum):
    """The 10 constitutional primer payloads (closed palette).

    Adding/removing a primer payload is a constitutional change requiring
    spec revision (see BOOTSTRAP_GENOME §4 + INGRESS_COMPILER_SPEC §11).
    """

    SUSPICION = "suspicion"
    NOVELTY = "novelty"
    AVERSION = "aversion"
    ATTRACTION = "attraction"
    CONTRADICTION = "contradiction"
    URGENCY = "urgency"
    MEMORY_ECHO = "memory_echo"
    FATIGUE_TRACE = "fatigue_trace"
    PAIN_TRACE = "pain_trace"
    REWARD_TRACE = "reward_trace"


class PayloadSeed(BaseModel):
    """One primer payload color at one bounded intensity.

    Fields:
        payload:   one of the 10 PrimerPayload values
        intensity: finite real number in [0.0, 1.0]
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
    )

    payload: PrimerPayload
    intensity: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
