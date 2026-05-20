"""Canonical observer event catalog and permanence policy table.

Per OBSERVER_LEDGER_SCHEMA.md §3-19 and the Phase 2 build plan: this
module pins the closed set of canonical observer event types the MVP
ledger may carry, the event family each one belongs to, the permanence
policy that applies to it, and whether a human alert is required on
write.

Constitutional discipline (catalog layer only):
    - Each catalog row is an immutable `CanonicalEventDefinition`
    - `event_type` values are unique across the catalog
    - `event_family` per event_type is fixed; cross-family events are
      rejected via `validate_event_family` (raises InvariantViolation)
    - `permanence` policy is data here; enforcement (move from ring
      buffer to JSONL, snapshot capture, retention) lands in
      `observer/permanence.py` (later Phase 2 commit)
    - No implicit defaults: every row spells out family / permanence /
      alert / severity / source_ref

What this module deliberately does NOT contain:
    - ObserverEvent write path
    - Hash-chain primitives (Commit 14)
    - JSONL append-only writer (Commit 15)
    - Permanence policy enforcement (Commit 16)
    - Snapshot capture
    - M1_READ_AUDIT_RECORDED emission (Commit 17)
    - The full event vocabulary (the v0.1 catalog is the MVP subset;
      later commits add rows without renaming existing codes)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from sentinel.constitution.violations import InvariantViolation, ViolationContext
from sentinel.types.observer import EventFamily


class EventPermanence(StrEnum):
    """Permanence policy for a canonical observer event.

    Values:
        ring_buffer_only:        bounded RAM ring; never promoted to
                                 the JSONL ledger
        permanent:               appended to the JSONL ledger
        permanent_with_snapshot: appended + a snapshot capture is
                                 attached (constitutional-critical
                                 audit anchor)
        ephemeral:               short-lived, not retained; reserved
                                 for narrowly scoped diagnostic uses
    """

    RING_BUFFER_ONLY = "ring_buffer_only"
    PERMANENT = "permanent"
    PERMANENT_WITH_SNAPSHOT = "permanent_with_snapshot"
    EPHEMERAL = "ephemeral"


class SeverityBand(StrEnum):
    """Severity band attached to a canonical event."""

    ROUTINE = "routine"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class CanonicalEventDefinition:
    """One row in the canonical observer event catalog.

    Fields:
        event_type:             closed-set identifier (UPPER_SNAKE_CASE)
        event_family:           the EventFamily this event belongs to
        permanence:             EventPermanence policy
        human_alert_required:   True iff a write of this event must
                                also raise a human-operator alert
        severity_band:          SeverityBand tier
        source_ref:             spec section anchor
    """

    event_type: str
    event_family: EventFamily
    permanence: EventPermanence
    human_alert_required: bool
    severity_band: SeverityBand
    source_ref: str


CANONICAL_EVENT_CATALOG: tuple[CanonicalEventDefinition, ...] = (
    # ---- BOOTSTRAP --------------------------------------------------------
    CanonicalEventDefinition(
        event_type="SELF_GENESIS",
        event_family=EventFamily.BOOTSTRAP,
        permanence=EventPermanence.PERMANENT_WITH_SNAPSHOT,
        human_alert_required=False,
        severity_band=SeverityBand.HIGH,
        source_ref="BOOTSTRAP_GENOME.md §3",
    ),
    CanonicalEventDefinition(
        event_type="BOOTSTRAP_M2_INJECTION",
        event_family=EventFamily.BOOTSTRAP,
        permanence=EventPermanence.PERMANENT,
        human_alert_required=False,
        severity_band=SeverityBand.MEDIUM,
        source_ref="BOOTSTRAP_GENOME.md §6",
    ),
    CanonicalEventDefinition(
        event_type="PHASE_TRANSITION_OCCURRED",
        event_family=EventFamily.BOOTSTRAP,
        permanence=EventPermanence.PERMANENT,
        human_alert_required=False,
        severity_band=SeverityBand.MEDIUM,
        source_ref="BOOTSTRAP_GENOME.md §7",
    ),
    # ---- ATTENTION --------------------------------------------------------
    CanonicalEventDefinition(
        event_type="WORKSPACE_PULSE",
        event_family=EventFamily.ATTENTION,
        permanence=EventPermanence.RING_BUFFER_ONLY,
        human_alert_required=False,
        severity_band=SeverityBand.ROUTINE,
        source_ref="BOOTSTRAP_GENOME.md §B (attention workspace)",
    ),
    # ---- INGRESS ----------------------------------------------------------
    CanonicalEventDefinition(
        event_type="OBSERVATION_INGESTED",
        event_family=EventFamily.INGRESS,
        permanence=EventPermanence.RING_BUFFER_ONLY,
        human_alert_required=False,
        severity_band=SeverityBand.ROUTINE,
        source_ref="WORLD_INGRESS.md §4",
    ),
    CanonicalEventDefinition(
        event_type="HUMAN_INTENT_INGESTED",
        event_family=EventFamily.INGRESS,
        permanence=EventPermanence.PERMANENT,
        human_alert_required=False,
        severity_band=SeverityBand.MEDIUM,
        source_ref="WORLD_INGRESS.md §9",
    ),
    CanonicalEventDefinition(
        event_type="INTERNAL_SHOCK_INGESTED",
        event_family=EventFamily.INGRESS,
        permanence=EventPermanence.PERMANENT_WITH_SNAPSHOT,
        human_alert_required=True,
        severity_band=SeverityBand.HIGH,
        source_ref="WORLD_INGRESS.md §10",
    ),
    CanonicalEventDefinition(
        event_type="RECALL_EVENT_INGESTED",
        event_family=EventFamily.INGRESS,
        permanence=EventPermanence.RING_BUFFER_ONLY,
        human_alert_required=False,
        severity_band=SeverityBand.ROUTINE,
        source_ref="RECALL_PROTOCOL.md §5",
    ),
    # ---- MEMORY -----------------------------------------------------------
    CanonicalEventDefinition(
        event_type="MEMORY_RECORD_STATUS_CHANGED",
        event_family=EventFamily.MEMORY,
        permanence=EventPermanence.PERMANENT,
        human_alert_required=False,
        severity_band=SeverityBand.MEDIUM,
        source_ref="MEMORY_CONTRACT.md §6",
    ),
    CanonicalEventDefinition(
        event_type="MEMORY_WRITE_PROPOSED",
        event_family=EventFamily.MEMORY,
        permanence=EventPermanence.PERMANENT,
        human_alert_required=False,
        severity_band=SeverityBand.MEDIUM,
        source_ref="MEMORY_WRITE_GATE.md §4",
    ),
    # ---- DEONTIC ----------------------------------------------------------
    CanonicalEventDefinition(
        event_type="DEONTIC_BLOCKED",
        event_family=EventFamily.DEONTIC,
        permanence=EventPermanence.PERMANENT,
        human_alert_required=False,
        severity_band=SeverityBand.HIGH,
        source_ref="DEONTIC_GATE.md §6",
    ),
    CanonicalEventDefinition(
        event_type="DEONTIC_BYPASS_ATTEMPT",
        event_family=EventFamily.DEONTIC,
        permanence=EventPermanence.PERMANENT_WITH_SNAPSHOT,
        human_alert_required=True,
        severity_band=SeverityBand.CRITICAL,
        source_ref="DEONTIC_GATE.md §8",
    ),
    CanonicalEventDefinition(
        event_type="KILL_SWITCH_ACTIVATED",
        event_family=EventFamily.DEONTIC,
        permanence=EventPermanence.PERMANENT_WITH_SNAPSHOT,
        human_alert_required=True,
        severity_band=SeverityBand.CRITICAL,
        source_ref="DEONTIC_GATE.md §11",
    ),
    CanonicalEventDefinition(
        event_type="CANARY_VETO_DECISION_RECORDED",
        event_family=EventFamily.DEONTIC,
        permanence=EventPermanence.PERMANENT,
        human_alert_required=False,
        severity_band=SeverityBand.HIGH,
        source_ref="V8 canary micro-live veto layer build plan §17",
    ),
    # ---- LEDGER_META ------------------------------------------------------
    CanonicalEventDefinition(
        event_type="NUMERICS_ARTIFACT_STATUS_CHANGED",
        event_family=EventFamily.LEDGER_META,
        permanence=EventPermanence.PERMANENT,
        human_alert_required=False,
        severity_band=SeverityBand.MEDIUM,
        source_ref="NUMERICS_GOVERNANCE.md §8",
    ),
    CanonicalEventDefinition(
        event_type="ADAPTER_MANIFEST_STATUS_CHANGED",
        event_family=EventFamily.LEDGER_META,
        permanence=EventPermanence.PERMANENT,
        human_alert_required=False,
        severity_band=SeverityBand.MEDIUM,
        source_ref="ADAPTER_MANIFEST_SPEC.md §9",
    ),
    CanonicalEventDefinition(
        event_type="LEDGER_STATE_CHANGED",
        event_family=EventFamily.LEDGER_META,
        permanence=EventPermanence.PERMANENT,
        human_alert_required=False,
        severity_band=SeverityBand.MEDIUM,
        source_ref="OBSERVER_LEDGER_SCHEMA.md §15",
    ),
    CanonicalEventDefinition(
        event_type="M1_READ_AUDIT_RECORDED",
        event_family=EventFamily.LEDGER_META,
        permanence=EventPermanence.PERMANENT,
        human_alert_required=False,
        severity_band=SeverityBand.LOW,
        source_ref="OBSERVER_LEDGER_SCHEMA.md §17",
    ),
    CanonicalEventDefinition(
        event_type="NUMERICS_VERSION_MISMATCH_DETECTED",
        event_family=EventFamily.LEDGER_META,
        permanence=EventPermanence.PERMANENT,
        human_alert_required=False,
        severity_band=SeverityBand.HIGH,
        source_ref="NUMERICS_GOVERNANCE.md §13 + OBSERVER_LEDGER_NUMERICS.md §6",
    ),
    CanonicalEventDefinition(
        event_type="NUMERICS_FAILSAFE_ACTIVATED",
        event_family=EventFamily.LEDGER_META,
        permanence=EventPermanence.PERMANENT_WITH_SNAPSHOT,
        human_alert_required=True,
        severity_band=SeverityBand.CRITICAL,
        source_ref="NUMERICS_GOVERNANCE.md §13 + OBSERVER_LEDGER_NUMERICS.md §7",
    ),
    # ---- REPLAY -----------------------------------------------------------
    CanonicalEventDefinition(
        event_type="REPLAY_SESSION_STATUS_CHANGED",
        event_family=EventFamily.REPLAY,
        permanence=EventPermanence.PERMANENT,
        human_alert_required=False,
        severity_band=SeverityBand.MEDIUM,
        source_ref="REPLAY_PROTOCOL.md §5",
    ),
    CanonicalEventDefinition(
        event_type="SLEEP_REPLAY_SYNAPSE_UPDATE",
        event_family=EventFamily.REPLAY,
        permanence=EventPermanence.PERMANENT,
        human_alert_required=False,
        severity_band=SeverityBand.LOW,
        source_ref="REPLAY_PROTOCOL.md §7 (sleep effect channel)",
    ),
    CanonicalEventDefinition(
        event_type="ATTENTION_REPLAY_HABITUATION_UPDATE",
        event_family=EventFamily.REPLAY,
        permanence=EventPermanence.PERMANENT,
        human_alert_required=False,
        severity_band=SeverityBand.LOW,
        source_ref="REPLAY_PROTOCOL.md §7 (attention habituation channel)",
    ),
    CanonicalEventDefinition(
        event_type="INGRESS_CALIBRATION_UPDATED",
        event_family=EventFamily.REPLAY,
        permanence=EventPermanence.PERMANENT,
        human_alert_required=False,
        severity_band=SeverityBand.LOW,
        source_ref="REPLAY_PROTOCOL.md §7 (ingress calibration channel)",
    ),
    CanonicalEventDefinition(
        event_type="MEMORY_VERIFICATION_EVIDENCE_PROPOSED",
        event_family=EventFamily.MEMORY,
        permanence=EventPermanence.PERMANENT,
        human_alert_required=False,
        severity_band=SeverityBand.LOW,
        source_ref="REPLAY_PROTOCOL.md §8 (memory verification evidence)",
    ),
    # ---- INGRESS (recall protocol audit) ---------------------------------
    CanonicalEventDefinition(
        event_type="RECALL_REQUEST_EMITTED",
        event_family=EventFamily.INGRESS,
        permanence=EventPermanence.PERMANENT,
        human_alert_required=False,
        severity_band=SeverityBand.MEDIUM,
        source_ref="RECALL_PROTOCOL.md §5",
    ),
    CanonicalEventDefinition(
        event_type="RECALL_RESULT_EMPTY",
        event_family=EventFamily.INGRESS,
        permanence=EventPermanence.PERMANENT,
        human_alert_required=False,
        severity_band=SeverityBand.LOW,
        source_ref="RECALL_PROTOCOL.md §20",
    ),
    CanonicalEventDefinition(
        event_type="RECALL_TRIGGER_REJECTED",
        event_family=EventFamily.INGRESS,
        permanence=EventPermanence.PERMANENT,
        human_alert_required=False,
        severity_band=SeverityBand.LOW,
        source_ref="RECALL_PROTOCOL.md §5, §19",
    ),
)


_BY_TYPE: dict[str, CanonicalEventDefinition] = {
    ev.event_type: ev for ev in CANONICAL_EVENT_CATALOG
}


def list_event_definitions() -> tuple[CanonicalEventDefinition, ...]:
    """Return the full canonical event catalog (unfiltered)."""
    return CANONICAL_EVENT_CATALOG


def get_event_definition(event_type: str) -> CanonicalEventDefinition:
    """Look up a canonical event by event_type. Raises KeyError if unknown."""
    return _BY_TYPE[event_type]


def is_canonical_event_type(event_type: str) -> bool:
    """True iff `event_type` is in the canonical catalog."""
    return event_type in _BY_TYPE


def expected_family_for(event_type: str) -> EventFamily:
    """Return the canonical EventFamily for `event_type`."""
    return _BY_TYPE[event_type].event_family


def permanence_for(event_type: str) -> EventPermanence:
    """Return the canonical EventPermanence policy for `event_type`."""
    return _BY_TYPE[event_type].permanence


def validate_event_family(event_type: str, event_family: EventFamily) -> None:
    """Raise `InvariantViolation` if `event_family` doesn't match the catalog.

    Unknown `event_type` also raises (the schema-layer catalog is the
    sole source of truth). On mismatch, raises with
    `violation_code="OBSERVER_EVENT_FAMILY_MATCHES_CATALOG"` and a
    source_ref pointing at OBSERVER_LEDGER_SCHEMA.md §19.
    """
    if event_type not in _BY_TYPE:
        raise InvariantViolation(
            f"unknown canonical event_type: {event_type!r}",
            ViolationContext(
                violation_code="OBSERVER_EVENT_TYPE_UNKNOWN",
                source_ref="OBSERVER_LEDGER_SCHEMA.md §19",
                evidence={"event_type": event_type},
            ),
        )
    expected = _BY_TYPE[event_type].event_family
    if event_family is not expected:
        raise InvariantViolation(
            (
                f"event_type {event_type!r} requires event_family="
                f"{expected.value!r}, got {event_family.value!r}"
            ),
            ViolationContext(
                violation_code="OBSERVER_EVENT_FAMILY_MATCHES_CATALOG",
                source_ref="OBSERVER_LEDGER_SCHEMA.md §19",
                evidence={
                    "event_type": event_type,
                    "expected_family": expected.value,
                    "actual_family": event_family.value,
                },
            ),
        )
