"""V10 — Financial AGI v1 evidence gate.

Validates that all mandatory evidence windows have been observed
before a production activation state can be granted.

Constitutional discipline:
    - If ``limited_live_90d`` or ``incident_free_90d`` windows are
      absent, gate always returns ``blocked`` / ``insufficient_evidence``.
    - ``pass_green`` requires all 7 windows present and satisfied.
    - Gate is read-only — no state mutation, no external writes.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, model_validator

_90D_WINDOWS = frozenset(["limited_live_90d", "incident_free_90d"])
_ALL_WINDOWS = frozenset(
    [
        "shadow_30d",
        "paper_30d",
        "canary_30d",
        "limited_live_90d",
        "incident_free_90d",
        "hash_chain_integrity",
        "policy_stability",
    ]
)


class EvidenceWindowKind(StrEnum):
    """Closed set of mandatory evidence window kinds."""

    SHADOW_30D = "shadow_30d"
    PAPER_30D = "paper_30d"
    CANARY_30D = "canary_30d"
    LIMITED_LIVE_90D = "limited_live_90d"
    INCIDENT_FREE_90D = "incident_free_90d"
    HASH_CHAIN_INTEGRITY = "hash_chain_integrity"
    POLICY_STABILITY = "policy_stability"


class EvidenceGateDecision(StrEnum):
    """Closed set of evidence gate outcomes."""

    PASS_GREEN = "pass_green"
    PASS_CONDITIONAL = "pass_conditional"
    BLOCKED = "blocked"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class EvidenceWindow(BaseModel, frozen=True, extra="forbid"):
    """One observed evidence window."""

    kind: EvidenceWindowKind
    satisfied: bool
    days_observed: int = Field(ge=0)
    notes: str = ""


class EvidenceGateInput(BaseModel, frozen=True, extra="forbid"):
    """All evidence windows presented for evaluation."""

    evaluation_id: str = Field(min_length=1)
    windows: tuple[EvidenceWindow, ...] = Field(default_factory=tuple)
    evaluated_at_ms: int = Field(ge=0)

    @model_validator(mode="after")
    def _no_duplicate_kinds(self) -> EvidenceGateInput:
        kinds = [w.kind for w in self.windows]
        if len(kinds) != len(set(kinds)):
            raise ValueError("duplicate EvidenceWindowKind in windows")
        return self


class EvidenceGateResult(BaseModel, frozen=True, extra="forbid"):
    """Output of evaluate_evidence_gate."""

    evaluation_id: str
    decision: EvidenceGateDecision
    satisfied_windows: tuple[EvidenceWindowKind, ...]
    missing_windows: tuple[EvidenceWindowKind, ...]
    failed_windows: tuple[EvidenceWindowKind, ...]
    blocked_reason: str
    all_mandatory_present: bool
    all_mandatory_satisfied: bool
    has_90d_evidence: bool
    direct_execution: Literal[False] = False
    approved_action_intent_generation: Literal[False] = False


def evaluate_evidence_gate(gate_input: EvidenceGateInput) -> EvidenceGateResult:
    """Evaluate all evidence windows and return a gate result.

    Decision logic:
    1. Build index of provided windows by kind.
    2. Identify missing mandatory windows.
    3. If any 90-day window is missing → ``insufficient_evidence`` / blocked.
    4. If any mandatory window is missing → ``insufficient_evidence`` / blocked.
    5. If any mandatory window is unsatisfied → ``blocked``.
    6. All satisfied → ``pass_green``.
    """
    provided: dict[EvidenceWindowKind, EvidenceWindow] = {w.kind: w for w in gate_input.windows}
    all_kinds = set(EvidenceWindowKind)

    missing: list[EvidenceWindowKind] = [k for k in all_kinds if k not in provided]
    present_satisfied: list[EvidenceWindowKind] = [k for k, w in provided.items() if w.satisfied]
    present_failed: list[EvidenceWindowKind] = [k for k, w in provided.items() if not w.satisfied]

    # 90-day windows specifically.
    ninety_day_kinds = {EvidenceWindowKind.LIMITED_LIVE_90D, EvidenceWindowKind.INCIDENT_FREE_90D}
    has_90d = all(k in provided for k in ninety_day_kinds)

    # Determine blocked_reason and decision.
    missing_90d = [k for k in ninety_day_kinds if k not in provided]
    if missing_90d:
        blocked_reason = (
            f"missing 90-day evidence windows: {','.join(k.value for k in missing_90d)}"
        )
        decision = EvidenceGateDecision.INSUFFICIENT_EVIDENCE
    elif missing:
        blocked_reason = f"missing mandatory evidence windows: {','.join(k.value for k in missing)}"
        decision = EvidenceGateDecision.INSUFFICIENT_EVIDENCE
    elif present_failed:
        blocked_reason = (
            f"unsatisfied evidence windows: {','.join(k.value for k in present_failed)}"
        )
        decision = EvidenceGateDecision.BLOCKED
    else:
        blocked_reason = ""
        decision = EvidenceGateDecision.PASS_GREEN

    return EvidenceGateResult(
        evaluation_id=gate_input.evaluation_id,
        decision=decision,
        satisfied_windows=tuple(sorted(present_satisfied, key=lambda k: k.value)),
        missing_windows=tuple(sorted(missing, key=lambda k: k.value)),
        failed_windows=tuple(sorted(present_failed, key=lambda k: k.value)),
        blocked_reason=blocked_reason,
        all_mandatory_present=len(missing) == 0,
        all_mandatory_satisfied=len(missing) == 0 and len(present_failed) == 0,
        has_90d_evidence=has_90d,
        direct_execution=False,
        approved_action_intent_generation=False,
    )


__all__ = [
    "EvidenceGateDecision",
    "EvidenceGateInput",
    "EvidenceGateResult",
    "EvidenceWindow",
    "EvidenceWindowKind",
    "evaluate_evidence_gate",
]
