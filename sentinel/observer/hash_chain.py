"""Append-only hash-chain primitives for ObserverEvent.

Per OBSERVER_LEDGER_SCHEMA.md §11 (verify_on_read_required) and the
Phase 2 build plan: this module pins the pure functions that compute
and verify the M1 audit-ledger hash chain. JSONL writing,
permanence enforcement, snapshot capture, and read-audit emission
all land in later Phase 2 commits.

Design intent:
    - Deterministic canonical JSON serialization (sort_keys, compact
      separators, no ASCII escaping) so two callers can always agree
      on the byte sequence that feeds the digest
    - One digest format across the whole ledger:
        "sha256:" + 64 lowercase hex characters
    - Event hash is computed over the canonical JSON of the event
      with `event_hash` REMOVED (a value cannot include its own
      digest) and `previous_event_hash` INCLUDED (chain binding)
    - All helpers are pure functions returning new frozen Pydantic
      models via `model_copy`; nothing mutates in place
    - `verify_chain_links` returns a bool for v0.1; richer
      diagnostics (line numbers, broken links) will arrive when the
      JSONL reader lands

What this module deliberately does NOT contain:
    - JSONL writer / reader
    - File / disk I/O
    - Permanence policy enforcement
    - Snapshot capture
    - M1_READ_AUDIT_RECORDED emission
    - HashChainViolation exception (handled as bool in v0.1)
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence  # noqa: TC003 (runtime annotations)
from typing import Any

from sentinel.types.observer import ObserverEvent  # noqa: TC001 (Pydantic runtime needs)

_HASH_PREFIX = "sha256:"
_HEX_LEN = 64
_PLACEHOLDER_EVENT_HASH = "sha256:" + ("0" * _HEX_LEN)


def canonical_json_bytes(value: Mapping[str, Any]) -> bytes:
    """Deterministic canonical JSON encoding used as the digest input.

    Uses sort_keys=True, compact separators, and `ensure_ascii=False`
    so that two callers always produce the same byte sequence for
    the same logical mapping.
    """
    return json.dumps(
        dict(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def sha256_digest(data: bytes) -> str:
    """Return the canonical `sha256:<64-hex>` digest of `data`."""
    return _HASH_PREFIX + hashlib.sha256(data).hexdigest()


def compute_observer_event_hash(event: ObserverEvent) -> str:
    """Compute the canonical hash for an ObserverEvent.

    The hash is taken over the event's `model_dump(mode="json")`
    representation with the `event_hash` field removed (a value
    cannot embed its own digest) and `previous_event_hash` left in
    place (chain binding).
    """
    dump = event.model_dump(mode="json")
    dump.pop("event_hash", None)
    return sha256_digest(canonical_json_bytes(dump))


def with_computed_event_hash(event: ObserverEvent) -> ObserverEvent:
    """Return a copy of `event` with `event_hash` set to its computed value."""
    return event.model_copy(update={"event_hash": compute_observer_event_hash(event)})


def verify_observer_event_hash(event: ObserverEvent) -> bool:
    """True iff `event.event_hash` matches the recomputed canonical hash."""
    return event.event_hash == compute_observer_event_hash(event)


def link_observer_event(
    event: ObserverEvent,
    *,
    previous_event_hash: str | None,
) -> ObserverEvent:
    """Bind `event` to its predecessor and compute its `event_hash`.

    Sets `previous_event_hash` (to None for genesis, or to the
    predecessor's `event_hash`) and then recomputes `event_hash` over
    the resulting payload.
    """
    bound = event.model_copy(update={"previous_event_hash": previous_event_hash})
    return with_computed_event_hash(bound)


def placeholder_event_hash() -> str:
    """A well-formed placeholder digest for callers that must construct
    an `ObserverEvent` before computing the real hash."""
    return _PLACEHOLDER_EVENT_HASH


def verify_chain_links(events: Sequence[ObserverEvent]) -> bool:
    """True iff `events` forms a valid append-only hash chain.

    Rules:
        - An empty sequence is valid (pre-genesis)
        - For each event, `event_hash` must match the recomputed hash
        - `events[0].previous_event_hash` may be None or any string;
          the chain begins at whatever predecessor the genesis event
          declares (None for first-ever, or the last hash of the
          previous segment)
        - For i >= 1, `events[i].previous_event_hash` must equal
          `events[i-1].event_hash`
    """
    for i, ev in enumerate(events):
        if not verify_observer_event_hash(ev):
            return False
        if i == 0:
            continue
        if ev.previous_event_hash != events[i - 1].event_hash:
            return False
    return True
