"""Gel.Al shadow batch runner (V5).

Reads a local Gel.Al shadow JSONL fixture, evaluates each envelope
through the shadow pipeline, and aggregates the closed
``SystemOutput`` distribution.

This module imports **nothing** that talks to Gel.Al's DB, Redis,
or HTTP surface.  It reads only the local file fed in by the
caller.  It writes only to the Sentinel ledger / ring buffer that
the caller supplies.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from sentinel.integrations.gelal_jsonl import GelAlShadowJsonlAdapter
from sentinel.integrations.gelal_shadow_eval import evaluate_gelal_shadow_event
from sentinel.memory.store import InMemoryExplicitMemoryStore  # noqa: TC001 (runtime arg)
from sentinel.observer.ledger import JsonlObserverLedger
from sentinel.observer.ring_buffer import ObserverRingBuffer
from sentinel.runtime.output import SystemOutput, assert_no_forbidden_literal
from sentinel.types.neural_seed import ProvenanceRef


@dataclass(frozen=True, slots=True)
class GelAlShadowBatchResult:
    """Aggregated outcome of a Gel.Al shadow batch run."""

    source_path: str | None
    events_seen: int
    events_accepted: int
    events_rejected: int
    outputs: tuple[SystemOutput, ...]
    monitor_count: int
    block_count: int
    need_recall_count: int
    wait_count: int
    no_action_count: int
    audit_event_ids: tuple[str, ...]
    permanent_event_ids: tuple[str, ...]
    ring_buffer_event_ids: tuple[str, ...]
    hash_chain_valid: bool
    reason: str


def run_gelal_shadow_file(
    *,
    path: Path,
    ledger: JsonlObserverLedger,
    ring_buffer: ObserverRingBuffer,
    provenance: ProvenanceRef,
    memory_store: InMemoryExplicitMemoryStore | None = None,
    coherence: float = 0.4,
    ttl_ms: int = 1000,
) -> GelAlShadowBatchResult:
    """Load a Gel.Al shadow JSONL fixture and evaluate every envelope."""
    adapter = GelAlShadowJsonlAdapter(path=path)
    envelopes = adapter.read_all()

    audit_ids: list[str] = []
    permanent_ids: list[str] = []
    ring_ids: list[str] = []
    outputs: list[SystemOutput] = []

    events_seen = 0
    events_accepted = 0
    events_rejected = 0
    monitor_count = 0
    block_count = 0
    need_recall_count = 0
    wait_count = 0
    no_action_count = 0

    for envelope in envelopes:
        events_seen += 1
        try:
            result = evaluate_gelal_shadow_event(
                envelope=envelope,
                ledger=ledger,
                ring_buffer=ring_buffer,
                provenance=ProvenanceRef(source_event_id=envelope.event_id),
                memory_store=memory_store,
                coherence=coherence,
                ttl_ms=ttl_ms,
            )
        except ValidationError:
            events_rejected += 1
            continue

        events_accepted += 1
        outputs.append(result.sentinel_output)
        audit_ids.extend(result.audit_event_ids)
        permanent_ids.extend(result.permanent_event_ids)
        ring_ids.extend(result.ring_buffer_event_ids)

        match result.sentinel_output:
            case SystemOutput.MONITOR:
                monitor_count += 1
            case SystemOutput.BLOCK:
                block_count += 1
            case SystemOutput.NEED_RECALL:
                need_recall_count += 1
            case SystemOutput.WAIT:
                wait_count += 1
            case SystemOutput.NO_ACTION:
                no_action_count += 1

    if events_seen == 0:
        outputs.append(SystemOutput.WAIT)

    reason = (
        f"gel.al shadow batch: seen={events_seen} accepted={events_accepted} "
        f"rejected={events_rejected} monitor={monitor_count} block={block_count} "
        f"need_recall={need_recall_count} wait={wait_count} no_action={no_action_count}"
    )
    assert_no_forbidden_literal(reason)

    return GelAlShadowBatchResult(
        source_path=str(path),
        events_seen=events_seen,
        events_accepted=events_accepted,
        events_rejected=events_rejected,
        outputs=tuple(outputs),
        monitor_count=monitor_count,
        block_count=block_count,
        need_recall_count=need_recall_count,
        wait_count=wait_count,
        no_action_count=no_action_count,
        audit_event_ids=tuple(audit_ids),
        permanent_event_ids=tuple(permanent_ids),
        ring_buffer_event_ids=tuple(ring_ids),
        hash_chain_valid=ledger.verify(),
        reason=reason,
    )


def cli_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="sentinel.runtime.gelal_shadow",
        description="Gel.Al shadow batch runner (read-only, no network, no Gel.Al write).",
    )
    parser.add_argument(
        "--fixture", required=True, type=Path, help="Path to a Gel.Al shadow JSONL fixture."
    )
    parser.add_argument(
        "--ledger", required=True, type=Path, help="Path to write the JSONL observer ledger."
    )
    parser.add_argument("--coherence", type=float, default=0.4)
    parser.add_argument("--ttl-ms", type=int, default=1000)
    parser.add_argument("--ring-capacity", type=int, default=256)
    args = parser.parse_args(argv)

    ledger = JsonlObserverLedger(args.ledger)
    ring = ObserverRingBuffer(capacity=args.ring_capacity)

    try:
        result = run_gelal_shadow_file(
            path=args.fixture,
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id="gelal-shadow-cli"),
            coherence=args.coherence,
            ttl_ms=args.ttl_ms,
        )
    except (FileNotFoundError, ValueError, ValidationError) as exc:
        print(f"gelal-shadow: fixture load error: {exc}", file=sys.stderr)
        return 1

    print(
        "gelal-shadow: "
        f"events_seen={result.events_seen} "
        f"accepted={result.events_accepted} "
        f"rejected={result.events_rejected} "
        f"outputs={tuple(o.value for o in result.outputs)} "
        f"permanent={len(result.permanent_event_ids)} "
        f"ring={len(result.ring_buffer_event_ids)} "
        f"hash_chain_valid={result.hash_chain_valid}"
    )

    if not result.hash_chain_valid:
        return 2
    return 0


if __name__ == "__main__":  # pragma: no cover (delegated via tests)
    raise SystemExit(cli_main())
