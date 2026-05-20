"""Recall trigger protocol (T §5).

Per RECALL_PROTOCOL.md §5-§6 and the Phase 8 build plan: a recall
request is gated by a **composite AND** trigger. Every condition
must be met; any single failure suppresses the trigger.

Conditions (T §5):
    1. trigger source must be core-originated (whitelist {CORE})
    2. sustained_tension_required=True implies
       sustained_tension_observed=True (no spike triggers)
    3. budget_remaining > 0
    4. global_cooldown_active is False
    5. memory_echo_intensity >= memory_echo_threshold
    6. context_signature_delta >= context_signature_delta_threshold
    7. fatigue_trace_intensity <= fatigue_trace_max

Constitutional discipline:
    - Human-direct, LLM, replay, summarizer trigger sources are
      REJECTED at the protocol layer (T §19)
    - The trigger function is pure: same inputs → same decision
    - Reason strings are stable for audit recording
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class RecallTriggerSource(StrEnum):
    """Closed set of recall trigger origins (T §19)."""

    CORE = "core"
    HUMAN_DIRECT = "human_direct"  # MVP rejected
    LLM = "llm"  # MVP rejected
    REPLAY = "replay"  # MVP rejected
    SUMMARIZER = "summarizer"  # MVP rejected


# MVP whitelist: only CORE may trigger recall.
ALLOWED_TRIGGER_SOURCES: frozenset[RecallTriggerSource] = frozenset({RecallTriggerSource.CORE})


@dataclass(frozen=True, slots=True)
class RecallTriggerInputs:
    """Inputs to the recall trigger decision."""

    memory_echo_intensity: float
    context_signature_delta: float
    fatigue_trace_intensity: float
    budget_remaining: int
    global_cooldown_active: bool
    sustained_tension_required: bool
    sustained_tension_observed: bool


@dataclass(frozen=True, slots=True)
class RecallTriggerDecision:
    triggered: bool
    reason: str


def check_recall_trigger(
    *,
    inputs: RecallTriggerInputs,
    source: RecallTriggerSource,
    memory_echo_threshold: float,
    context_signature_delta_threshold: float,
    fatigue_trace_max: float,
) -> RecallTriggerDecision:
    """Return the composite-AND trigger decision.

    Order is fixed (audit-stable). The first failing condition's
    reason is returned; later conditions are not evaluated.
    """
    if source not in ALLOWED_TRIGGER_SOURCES:
        return RecallTriggerDecision(
            triggered=False,
            reason=f"trigger source {source.value!r} not in allowed set (T §19)",
        )
    if inputs.sustained_tension_required and not inputs.sustained_tension_observed:
        return RecallTriggerDecision(
            triggered=False,
            reason="sustained tension required but not observed (T §5)",
        )
    if inputs.budget_remaining <= 0:
        return RecallTriggerDecision(triggered=False, reason="recall budget exhausted")
    if inputs.global_cooldown_active:
        return RecallTriggerDecision(triggered=False, reason="global cooldown active")
    if inputs.memory_echo_intensity < memory_echo_threshold:
        return RecallTriggerDecision(
            triggered=False,
            reason=(
                f"memory_echo_intensity {inputs.memory_echo_intensity} < "
                f"threshold {memory_echo_threshold}"
            ),
        )
    if inputs.context_signature_delta < context_signature_delta_threshold:
        return RecallTriggerDecision(
            triggered=False,
            reason=(
                f"context_signature_delta {inputs.context_signature_delta} < "
                f"threshold {context_signature_delta_threshold}"
            ),
        )
    if inputs.fatigue_trace_intensity > fatigue_trace_max:
        return RecallTriggerDecision(
            triggered=False,
            reason=(
                f"fatigue_trace_intensity {inputs.fatigue_trace_intensity} > "
                f"max {fatigue_trace_max}"
            ),
        )
    return RecallTriggerDecision(triggered=True, reason="all conditions met")
