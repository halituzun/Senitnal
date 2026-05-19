"""Append-only JSONL ObserverEvent ledger (single-process MVP writer).

Per OBSERVER_LEDGER_SCHEMA.md §6-§19 and the Phase 2 build plan: this
module pins a minimal JSONL writer that appends ObserverEvent records
one-per-line, computing the hash-chain link via
`sentinel.observer.hash_chain` and validating event_type/family
against `sentinel.observer.catalog`.

Constitutional discipline (writer layer only):
    - One event per line; line = canonical JSON dump (sort_keys,
      compact separators, ensure_ascii=False, utf-8)
    - The caller may pass a placeholder `event_hash` (and any
      `previous_event_hash`); the ledger ignores those and recomputes
      the correct chain link before writing
    - event_type must be canonical (catalog); event_family must match
      its catalog row. Both raise `InvariantViolation` from the
      catalog helper on violation
    - No file locking, no multi-writer coordination — this MVP ledger
      is single-process only. Concurrent writers will corrupt the
      chain; that's a Phase 3+ concern

What this module deliberately does NOT contain:
    - Permanence policy enforcement (Commit 16)
    - Ring buffer / RAM-only event handling
    - Snapshot capture
    - Compaction / rotation
    - M1_READ_AUDIT_RECORDED emission (Commit 17)
    - File locking / multi-process safety
    - Concurrency / async I/O
"""

from __future__ import annotations

import json
from pathlib import Path  # noqa: TC003 (runtime annotation)

from sentinel.observer.catalog import validate_event_family
from sentinel.observer.hash_chain import (
    canonical_json_bytes,
    link_observer_event,
    verify_chain_links,
)
from sentinel.types.observer import ObserverEvent


class JsonlObserverLedger:
    """Append-only JSONL ObserverEvent ledger (single-process MVP).

    Methods:
        append(event):  validate, link to predecessor, recompute
                        event_hash, write a canonical JSON line, and
                        return the linked event
        read_all():     parse every non-empty line as ObserverEvent
        verify():       True iff the on-disk chain re-verifies
    """

    def __init__(self, path: Path) -> None:
        self._path = path

    @property
    def path(self) -> Path:
        return self._path

    def append(self, event: ObserverEvent) -> ObserverEvent:
        """Validate, link, and persist `event`. Returns the linked event."""
        validate_event_family(event.event_type, event.event_family)

        existing = self.read_all()
        previous_hash = existing[-1].event_hash if existing else None
        linked = link_observer_event(event, previous_event_hash=previous_hash)

        line = canonical_json_bytes(linked.model_dump(mode="json"))
        with self._path.open("ab") as fh:
            fh.write(line)
            fh.write(b"\n")
        return linked

    def read_all(self) -> tuple[ObserverEvent, ...]:
        """Parse every non-empty line of the ledger file as an ObserverEvent.

        Returns an empty tuple if the file does not exist.
        Raises ValueError on malformed JSON or schema-invalid lines.
        """
        if not self._path.exists():
            return ()
        events: list[ObserverEvent] = []
        with self._path.open("rb") as fh:
            for line_no, raw in enumerate(fh, start=1):
                line = raw.strip()
                if not line:
                    continue
                try:
                    json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"malformed JSON on ledger line {line_no}: {exc.msg}"
                    ) from exc
                events.append(ObserverEvent.model_validate_json(line))
        return tuple(events)

    def verify(self) -> bool:
        """True iff the on-disk ledger forms a valid append-only hash chain."""
        return verify_chain_links(self.read_all())
