"""V10 — Financial AGI v1 state models.

Captures the activation phase, capability map, and overall state
of the Sentinel Financial AGI v1 system.

Constitutional discipline:
    - ``FinancialAGICapabilityMap`` pins five safety flags as
      ``Literal[False]``.  Any attempt to set them True is a
      type error and a runtime ``ValidationError``.
    - ``FinancialAGIActivationState`` is a closed enum — no open
      value accepted.
    - All models are frozen and use ``extra='forbid'``.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class FinancialAGIPhase(StrEnum):
    """Closed set of V10 AGI evaluation phases."""

    SHADOW = "shadow"
    PAPER = "paper"
    CANARY = "canary"
    LIMITED_LIVE = "limited_live"
    AGI_V1 = "agi_v1"


class FinancialAGIActivationState(StrEnum):
    """Closed set of V10 AGI activation states."""

    NOT_READY = "not_ready"
    READINESS_REVIEW = "readiness_review"
    SHADOW_READY = "shadow_ready"
    PAPER_READY = "paper_ready"
    CANARY_READY = "canary_ready"
    LIMITED_LIVE_READY = "limited_live_ready"
    AGI_V1_READY = "agi_v1_ready"
    PRODUCTION_BLOCKED = "production_blocked"
    RELEASED_BUT_NOT_ACTIVATED = "released_but_not_activated"


class FinancialAGICapabilityMap(BaseModel, frozen=True, extra="forbid"):
    """Capability map for Financial AGI v1.

    Five execution safety flags are pinned ``Literal[False]`` and
    cannot be overridden by callers or subclasses.

    Non-execution advisory capabilities:
        - shadow observation: permitted
        - paper co-pilot advisory: permitted
        - canary veto advisory: permitted
        - live governance advisory (block only): permitted
        - readiness reporting: permitted
    """

    model_config = {"strict": True}

    direct_execution: Literal[False] = False
    exchange_imports: Literal[False] = False
    llm_imports: Literal[False] = False
    gelal_write_path: Literal[False] = False
    approved_action_intent_generation: Literal[False] = False

    shadow_observation: bool = True
    paper_copilot_advisory: bool = True
    canary_veto_advisory: bool = True
    live_governance_advisory: bool = True
    readiness_reporting: bool = True

    @model_validator(mode="after")
    def _safety_flags_pinned(self) -> FinancialAGICapabilityMap:
        if self.direct_execution is not False:
            raise ValueError("direct_execution must be False")
        if self.exchange_imports is not False:
            raise ValueError("exchange_imports must be False")
        if self.llm_imports is not False:
            raise ValueError("llm_imports must be False")
        if self.gelal_write_path is not False:
            raise ValueError("gelal_write_path must be False")
        if self.approved_action_intent_generation is not False:
            raise ValueError("approved_action_intent_generation must be False")
        return self


class FinancialAGIState(BaseModel, frozen=True, extra="forbid"):
    """Snapshot of the Financial AGI v1 system state at evaluation time."""

    state_id: str = Field(min_length=1)
    phase: FinancialAGIPhase
    activation_state: FinancialAGIActivationState
    capability_map: FinancialAGICapabilityMap = Field(default_factory=FinancialAGICapabilityMap)
    created_at_ms: int = Field(ge=0)
    evidence_evaluated_at_ms: int | None = None
    notes: str = ""

    @model_validator(mode="after")
    def _timestamps_consistent(self) -> FinancialAGIState:
        if (
            self.evidence_evaluated_at_ms is not None
            and self.evidence_evaluated_at_ms > self.created_at_ms
        ):
            raise ValueError("evidence_evaluated_at_ms must not be after created_at_ms")
        return self


__all__ = [
    "FinancialAGIActivationState",
    "FinancialAGICapabilityMap",
    "FinancialAGIPhase",
    "FinancialAGIState",
]
