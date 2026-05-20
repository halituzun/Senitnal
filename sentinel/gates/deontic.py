"""Deontic gate — constitutional hard-stops + MVP default-deny.

Per DEONTIC_GATE.md §6-8 and the Phase 7 build plan: the deontic
gate is the **single exit point** through which an
ApprovedActionIntent must pass before becoming an effective system
action. It is hard-stop only — no warning, no soft pressure (that
is the self-field's job). In MVP the gate is constitutionally
configured to BLOCK every intent: `mvp_execute_disabled = True`
(see runtime/feature_flags.py).

Constitutional discipline:
    - 11 closed constitutional declaratives (E §8). Each is a
      pre-evaluated hard-stop with a block_class. The MVP gate
      checks the kill switch and feature flag first; if either
      blocks, that block is recorded with its specific declarative
      code. If neither blocks (cannot happen in MVP), the gate
      walks the declaratives and blocks on the first violation
    - Three block classes (E §11): routine, safety, constitutional.
      All three are hard-stops; only post-block observer audit /
      InternalShockEvent triggering / human alert differ
    - The gate NEVER returns ALLOW in MVP. The `DeonticDecision`
      enum carries ALLOW for future phases; MVP code paths that
      observe ALLOW must treat it as a defect (defense-in-depth)

What this module deliberately does NOT contain:
    - Operational policy (DeonticPolicyRecord) layer — that lives
      with memory in Phase 8+
    - Action execution path (deferred)
    - Warning / soft-pressure paths (self-field's job)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sentinel.observer.hash_chain import placeholder_event_hash
from sentinel.observer.ledger import JsonlObserverLedger  # noqa: TC001 (runtime)
from sentinel.runtime.feature_flags import get_flag
from sentinel.types.neural_seed import ProvenanceRef
from sentinel.types.observer import EventFamily, ObserverEvent


class BlockClass(StrEnum):
    """Post-block behaviour classification (E §11)."""

    ROUTINE = "routine"
    SAFETY = "safety"
    CONSTITUTIONAL = "constitutional"


class DeonticDecision(StrEnum):
    """Closed set of gate decisions."""

    BLOCK = "block"
    ALLOW = "allow"  # never returned in MVP


@dataclass(frozen=True, slots=True)
class DeonticDeclarative:
    """One constitutional hard-stop declarative (E §8 row)."""

    code: str
    block_class: BlockClass
    statement: str
    source_ref: str


# 11 constitutional declaratives — MVP working set.
# Each entry is a hard-stop; cumulative ordering matches the
# narrative flow of the constitutional documents.
DEONTIC_DECLARATIVES: tuple[DeonticDeclarative, ...] = (
    DeonticDeclarative(
        code="KILL_SWITCH_ACTIVE_BLOCKS_ALL_ACTION",
        block_class=BlockClass.CONSTITUTIONAL,
        statement=(
            "While kill_switch_active is True, every ApprovedActionIntent "
            "is blocked. Cognition continues; action output halts."
        ),
        source_ref="DEONTIC_GATE.md §8 + §11; agi-core-design L301",
    ),
    DeonticDeclarative(
        code="MVP_EXECUTE_DISABLED_BLOCKS_ALL_ACTION",
        block_class=BlockClass.CONSTITUTIONAL,
        statement=(
            "While mvp_execute_disabled is True, every ApprovedActionIntent "
            "is blocked (MVP default-deny)."
        ),
        source_ref="build plan §12, §18",
    ),
    DeonticDeclarative(
        code="NO_LIVE_EXCHANGE_EXECUTION",
        block_class=BlockClass.CONSTITUTIONAL,
        statement=(
            "No action may execute against a live exchange / venue. "
            "Live-market integrations are forbidden in MVP."
        ),
        source_ref="build plan §3, §20",
    ),
    DeonticDeclarative(
        code="NO_HUMAN_OVERRIDE_OF_GATE",
        block_class=BlockClass.CONSTITUTIONAL,
        statement=(
            "No operator override path may bypass the deontic gate. "
            "operator_override_enabled is constitutionally False in MVP."
        ),
        source_ref="DEONTIC_GATE.md §8; build plan §18, §20",
    ),
    DeonticDeclarative(
        code="NO_INTENT_RELAY_DIRECT_EXECUTION",
        block_class=BlockClass.CONSTITUTIONAL,
        statement=(
            "An adapter declaring `intent_relay` may not also declare "
            "`execute`. Direct human-to-execution bypass is forbidden."
        ),
        source_ref="ADAPTER_MANIFEST_SPEC.md §8",
    ),
    DeonticDeclarative(
        code="NO_ADAPTER_NEURAL_SEED_EMISSION",
        block_class=BlockClass.CONSTITUTIONAL,
        statement=(
            "No adapter output channel may emit NeuralSeed. Only the "
            "core / cortex may produce NeuralSeed."
        ),
        source_ref="ADAPTER_MANIFEST_SPEC.md §7; ADAPTER_TRUST_NUMERICS.md §6",
    ),
    DeonticDeclarative(
        code="NO_NUMERICS_RUNTIME_MUTATION",
        block_class=BlockClass.CONSTITUTIONAL,
        statement=(
            "Numerics governance forbids runtime mutation of numerics "
            "artifacts; an action that would mutate is blocked."
        ),
        source_ref="NUMERICS_GOVERNANCE.md §12-13; build plan §18",
    ),
    DeonticDeclarative(
        code="NO_RECALL_DIRECT_ACTION",
        block_class=BlockClass.SAFETY,
        statement=(
            "Recall results never directly become actions. An action "
            "originating solely from a recall payload is blocked."
        ),
        source_ref="RECALL_PROTOCOL.md §5, §19",
    ),
    DeonticDeclarative(
        code="NO_PRE_BOOTSTRAP_ACTION",
        block_class=BlockClass.SAFETY,
        statement=(
            "Actions are blocked until the SELF_GENESIS event has been "
            "recorded and the bootstrap phase has transitioned."
        ),
        source_ref="BOOTSTRAP_GENOME.md §3, §7",
    ),
    DeonticDeclarative(
        code="NO_MEMORY_WRITE_GATE_BYPASS",
        block_class=BlockClass.SAFETY,
        statement=(
            "Actions that would write to memory without flowing through "
            "the Memory Write Gate are blocked."
        ),
        source_ref="MEMORY_WRITE_GATE.md §4-8",
    ),
    DeonticDeclarative(
        code="NO_UNSIGNED_MANIFEST_ACTION",
        block_class=BlockClass.SAFETY,
        statement=(
            "Adapter actions are blocked when the originating adapter "
            "manifest is unsigned or fails signature verification."
        ),
        source_ref="ADAPTER_MANIFEST_SPEC.md §6, §9",
    ),
)


_DECLARATIVE_BY_CODE: dict[str, DeonticDeclarative] = {d.code: d for d in DEONTIC_DECLARATIVES}


def get_declarative(code: str) -> DeonticDeclarative:
    """Look up a declarative by code; raises KeyError if unknown."""
    return _DECLARATIVE_BY_CODE[code]


class ApprovedActionIntent(BaseModel):
    """A proposed action presented to the deontic gate (MVP shape).

    Schema-only: no execution semantics. The MVP gate uses
    `intent_type` only to record the audit reason; no behaviour
    branches on it because every intent is blocked anyway.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    intent_id: str = Field(min_length=1)
    intent_type: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    requested_at_ms: int = Field(ge=0)


class DeonticOutcome(BaseModel):
    """The gate's verdict on one ApprovedActionIntent."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    intent_id: str = Field(min_length=1)
    decision: DeonticDecision
    block_class: BlockClass | None
    triggered_declarative_code: str | None
    reason: str = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_block_consistency(self) -> Self:
        if self.decision is DeonticDecision.BLOCK:
            if self.block_class is None:
                raise ValueError("BLOCK decision requires a block_class")
            if self.triggered_declarative_code is None:
                raise ValueError("BLOCK decision requires triggered_declarative_code")
        else:
            if self.block_class is not None:
                raise ValueError("ALLOW decision must have block_class=None")
            if self.triggered_declarative_code is not None:
                raise ValueError("ALLOW decision must have triggered_declarative_code=None")
        return self


def evaluate_action(intent: ApprovedActionIntent) -> DeonticOutcome:
    """Evaluate `intent` against the deontic gate. MVP: always BLOCK.

    Order of precedence:
        1. kill_switch_active  → BLOCK (constitutional)
        2. mvp_execute_disabled → BLOCK (constitutional)
        3. First matching declarative (defense-in-depth; in MVP
           we never reach this because (2) is True)
    """
    if get_flag("kill_switch_active"):
        d = _DECLARATIVE_BY_CODE["KILL_SWITCH_ACTIVE_BLOCKS_ALL_ACTION"]
        return DeonticOutcome(
            intent_id=intent.intent_id,
            decision=DeonticDecision.BLOCK,
            block_class=d.block_class,
            triggered_declarative_code=d.code,
            reason=d.statement,
        )
    if get_flag("mvp_execute_disabled"):
        d = _DECLARATIVE_BY_CODE["MVP_EXECUTE_DISABLED_BLOCKS_ALL_ACTION"]
        return DeonticOutcome(
            intent_id=intent.intent_id,
            decision=DeonticDecision.BLOCK,
            block_class=d.block_class,
            triggered_declarative_code=d.code,
            reason=d.statement,
        )
    # Defense-in-depth: even if both safety flags flip OFF in a
    # non-MVP build, the constitutional declaratives below still
    # block every action without a positive go-ahead from a future
    # ALLOW path. MVP never reaches this branch.
    d = _DECLARATIVE_BY_CODE["NO_LIVE_EXCHANGE_EXECUTION"]
    return DeonticOutcome(
        intent_id=intent.intent_id,
        decision=DeonticDecision.BLOCK,
        block_class=d.block_class,
        triggered_declarative_code=d.code,
        reason=d.statement,
    )


def _emit_deontic_block(
    *,
    ledger: JsonlObserverLedger,
    intent: ApprovedActionIntent,
    outcome: DeonticOutcome,
    now_ms: int,
) -> ObserverEvent:
    """Append a DEONTIC_BLOCKED observer event to the ledger.

    Writer-authoritative chain. Callers should pass `now_ms` for
    occurred_at_ms.
    """
    return ledger.append(
        ObserverEvent(
            event_id=f"deontic-block-{intent.intent_id}",
            event_family=EventFamily.DEONTIC,
            event_type="DEONTIC_BLOCKED",
            occurred_at_ms=now_ms,
            payload={
                "intent_id": intent.intent_id,
                "intent_type": intent.intent_type,
                "block_class": (
                    outcome.block_class.value if outcome.block_class is not None else None
                ),
                "triggered_declarative_code": outcome.triggered_declarative_code,
                "rationale": intent.rationale,
                "reason": outcome.reason,
            },
            provenance=ProvenanceRef(source_event_id=intent.intent_id),
            previous_event_hash=None,
            event_hash=placeholder_event_hash(),
        )
    )


def evaluate_action_with_audit(
    ledger: JsonlObserverLedger,
    intent: ApprovedActionIntent,
    *,
    now_ms: int,
) -> DeonticOutcome:
    """Evaluate `intent` and append the audit event in one call.

    Every BLOCK decision is recorded as DEONTIC_BLOCKED in the M1
    ledger. An ALLOW decision (MVP impossible) is NOT audited by
    this helper; future code paths emitting ALLOW must use their
    own audit shape.
    """
    outcome = evaluate_action(intent)
    if outcome.decision is DeonticDecision.BLOCK:
        _emit_deontic_block(ledger=ledger, intent=intent, outcome=outcome, now_ms=now_ms)
    return outcome
