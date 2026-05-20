"""M1 audit-aware reader.

Per OBSERVER_LEDGER_SCHEMA.md §17 and OBSERVER_LEDGER_NUMERICS.md §12-15:
every read of the M1 ledger emits a meta-event
`M1_READ_AUDIT_RECORDED` describing the reader, the scope of the
read, and the time window inspected. Reads by `ReaderType.LLM` are
further restricted: the requested event_type scope must be a subset
of the LLM read whitelist, otherwise the read is rejected and
nothing is emitted.

Design intent (reader layer only):
    - No silent reads. Every public method on `AuditReader` produces
      a corresponding `M1_READ_AUDIT_RECORDED` event in the same
      JSONL ledger (single chain, single source of truth)
    - LLM scope guard is hard: filter out events the LLM is not
      authorized to see — and if the LLM EXPLICITLY requested a
      forbidden scope, raise `InvariantViolation`
      (`OBSERVER_LLM_READ_SCOPE_FORBIDDEN`)
    - Read audit's own write is itself an observer event; it is
      written to the ledger and forms its own chain link, so the
      audit trail is recursive: even reading the audit emits an
      audit event

What this module deliberately does NOT contain:
    - Snapshot capture
    - Permanence enforcement (the writer is the ledger; this module
      is a read-side facade)
    - Read summarization / batching (Phase 3+)
"""

from __future__ import annotations

from enum import StrEnum

from sentinel.constitution.violations import InvariantViolation, ViolationContext
from sentinel.observer.hash_chain import placeholder_event_hash
from sentinel.observer.ledger import JsonlObserverLedger  # noqa: TC001 (runtime)
from sentinel.types.neural_seed import ProvenanceRef
from sentinel.types.observer import EventFamily, ObserverEvent


class ReaderType(StrEnum):
    """Closed set of M1 reader identities (Q §15)."""

    HUMAN = "human"
    LLM = "llm"
    REPLAY = "replay"
    SUMMARIZER = "summarizer"
    EXTERNAL_AUDIT = "external_audit"
    INTERNAL = "internal"


# LLM read scope whitelist (v0.1 starter, conservative).
# An LLM may only inspect these audit-meta and high-level outcome
# events; raw ingress / observer payloads, deontic detail, and
# memory writes are deliberately excluded until a security review
# expands the whitelist.
LLM_ALLOWED_READ_EVENT_TYPES: frozenset[str] = frozenset(
    {
        "M1_READ_AUDIT_RECORDED",
        "LEDGER_STATE_CHANGED",
        "PHASE_TRANSITION_OCCURRED",
        "NUMERICS_ARTIFACT_STATUS_CHANGED",
        "NUMERICS_VERSION_MISMATCH_DETECTED",
        "ADAPTER_MANIFEST_STATUS_CHANGED",
    }
)


def _make_read_audit_event(
    *,
    event_id: str,
    occurred_at_ms: int,
    reader_type: ReaderType,
    requested_event_types: tuple[str, ...] | None,
    returned_count: int,
    source_event_id: str,
) -> ObserverEvent:
    payload: dict[str, object] = {
        "reader_type": reader_type.value,
        "returned_count": returned_count,
    }
    if requested_event_types is not None:
        payload["requested_event_types"] = list(requested_event_types)
    return ObserverEvent(
        event_id=event_id,
        event_family=EventFamily.LEDGER_META,
        event_type="M1_READ_AUDIT_RECORDED",
        occurred_at_ms=occurred_at_ms,
        payload=payload,
        provenance=ProvenanceRef(source_event_id=source_event_id),
        previous_event_hash=None,
        event_hash=placeholder_event_hash(),
    )


class AuditReader:
    """Read facade over a JsonlObserverLedger.

    Every read method emits a single `M1_READ_AUDIT_RECORDED` event
    via the same ledger, preserving the hash chain.
    """

    def __init__(self, ledger: JsonlObserverLedger) -> None:
        self._ledger = ledger
        self._counter = 0

    def _next_audit_event_id(self) -> str:
        self._counter += 1
        return f"audit-read-{self._counter:08d}"

    def _emit_audit(
        self,
        *,
        reader_type: ReaderType,
        requested_event_types: tuple[str, ...] | None,
        returned_count: int,
        now_ms: int,
    ) -> ObserverEvent:
        return self._ledger.append(
            _make_read_audit_event(
                event_id=self._next_audit_event_id(),
                occurred_at_ms=now_ms,
                reader_type=reader_type,
                requested_event_types=requested_event_types,
                returned_count=returned_count,
                source_event_id=f"reader-{reader_type.value}",
            )
        )

    def read_all(
        self,
        *,
        reader_type: ReaderType,
        now_ms: int,
    ) -> tuple[ObserverEvent, ...]:
        """Return every event; for LLM readers, filter to the whitelist."""
        events = self._ledger.read_all()
        if reader_type is ReaderType.LLM:
            events = tuple(e for e in events if e.event_type in LLM_ALLOWED_READ_EVENT_TYPES)
        self._emit_audit(
            reader_type=reader_type,
            requested_event_types=None,
            returned_count=len(events),
            now_ms=now_ms,
        )
        return events

    def read_by_event_types(
        self,
        *,
        reader_type: ReaderType,
        event_types: tuple[str, ...],
        now_ms: int,
    ) -> tuple[ObserverEvent, ...]:
        """Return events whose event_type is in `event_types`.

        For LLM readers, every requested event_type must be in the
        whitelist; otherwise raises InvariantViolation
        (OBSERVER_LLM_READ_SCOPE_FORBIDDEN) and emits nothing.
        """
        if reader_type is ReaderType.LLM:
            forbidden = tuple(t for t in event_types if t not in LLM_ALLOWED_READ_EVENT_TYPES)
            if forbidden:
                raise InvariantViolation(
                    f"LLM read scope forbidden: {list(forbidden)!r}",
                    ViolationContext(
                        violation_code="OBSERVER_LLM_READ_SCOPE_FORBIDDEN",
                        source_ref="OBSERVER_LEDGER_NUMERICS.md §12-15",
                        evidence={
                            "reader_type": reader_type.value,
                            "forbidden_event_types": list(forbidden),
                        },
                    ),
                )
        wanted = set(event_types)
        events = tuple(e for e in self._ledger.read_all() if e.event_type in wanted)
        self._emit_audit(
            reader_type=reader_type,
            requested_event_types=event_types,
            returned_count=len(events),
            now_ms=now_ms,
        )
        return events
