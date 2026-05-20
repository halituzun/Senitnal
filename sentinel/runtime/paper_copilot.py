"""V7 — Paper co-pilot batch runner + CLI.

Loads a local fixture (market envelopes, Gel.Al shadow envelopes, or
raw paper opportunities), evaluates each through the paper co-pilot
engine, and emits a permanent audit event per result.

No network, no Gel.Al write, no execution.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import ValidationError

from sentinel.adapters.local_jsonl_market import LocalJsonlMarketAdapter
from sentinel.integrations.gelal_jsonl import GelAlShadowJsonlAdapter
from sentinel.observer.ledger import JsonlObserverLedger
from sentinel.observer.ring_buffer import ObserverRingBuffer
from sentinel.paper.audit import emit_paper_copilot_evaluated
from sentinel.paper.copilot import PaperCoPilotContext, evaluate_paper_opportunity
from sentinel.paper.decision import PaperCoPilotResult
from sentinel.paper.opportunity import (
    PaperOpportunity,
    PaperOpportunitySource,
    build_paper_opportunity_from_gelal_shadow,
    build_paper_opportunity_from_market_observation,
)
from sentinel.runtime.output import SystemOutput, assert_no_forbidden_literal
from sentinel.types.neural_seed import ProvenanceRef

SourceKind = Literal["market_jsonl", "gelal_shadow_jsonl", "paper_opportunity_jsonl"]


@dataclass(frozen=True, slots=True)
class PaperCoPilotBatchResult:
    """Aggregated outcome of a paper co-pilot batch run."""

    source_path: str
    opportunities_seen: int
    opportunities_accepted: int
    opportunities_rejected: int
    outputs: tuple[SystemOutput, ...]
    block_count: int
    monitor_count: int
    need_recall_count: int
    wait_count: int
    no_action_count: int
    audit_event_ids: tuple[str, ...]
    permanent_event_ids: tuple[str, ...]
    ring_buffer_event_ids: tuple[str, ...]
    hash_chain_valid: bool
    any_creates_action: bool
    any_writes_external: bool
    any_approved_for_live: bool
    reason: str


def _load_opportunities(
    *,
    path: Path,
    source_kind: SourceKind,
) -> tuple[list[PaperOpportunity], int]:
    """Load opportunities from `path` per `source_kind`.

    Returns ``(opportunities, rejected_count)``.  Rejected entries are
    counted but excluded from the returned list.
    """
    rejected = 0
    out: list[PaperOpportunity] = []
    if source_kind == "market_jsonl":
        adapter = LocalJsonlMarketAdapter(path=path)
        for envelope in adapter.read_all():
            out.append(
                build_paper_opportunity_from_market_observation(
                    envelope,
                    source=PaperOpportunitySource.LOCAL_MARKET_JSONL,
                )
            )
    elif source_kind == "gelal_shadow_jsonl":
        adapter_g = GelAlShadowJsonlAdapter(path=path)
        for envelope in adapter_g.read_all():
            out.append(build_paper_opportunity_from_gelal_shadow(envelope))
    elif source_kind == "paper_opportunity_jsonl":
        with path.open("r", encoding="utf-8") as fh:
            for line_no, raw in enumerate(fh, start=1):
                stripped = raw.strip()
                if not stripped:
                    continue
                try:
                    out.append(PaperOpportunity.model_validate_json(stripped))
                except ValidationError:
                    rejected += 1
                except ValueError as exc:
                    raise ValueError(f"malformed JSON on line {line_no} of {path}: {exc}") from exc
    else:  # pragma: no cover (Literal exhaustion)
        raise ValueError(f"unknown source_kind {source_kind!r}")
    return out, rejected


def run_paper_copilot_file(
    *,
    path: Path,
    source_kind: SourceKind,
    ledger: JsonlObserverLedger,
    ring_buffer: ObserverRingBuffer,
    provenance: ProvenanceRef,
    context: PaperCoPilotContext,
) -> PaperCoPilotBatchResult:
    """Run the paper co-pilot batch evaluator over a local fixture file."""
    opportunities, schema_rejected = _load_opportunities(path=path, source_kind=source_kind)

    audit_ids: list[str] = []
    permanent_ids: list[str] = []
    ring_ids: list[str] = []
    outputs: list[SystemOutput] = []
    block_count = monitor_count = need_recall_count = wait_count = no_action_count = 0
    any_creates_action = False
    any_writes_external = False
    any_approved_for_live = False

    # ``ring_buffer`` is supplied but V7 audit lands permanently in the
    # ledger (LEDGER_STATE_CHANGED).  We keep the parameter for API
    # symmetry with other batch runners.
    _ = ring_buffer

    for opportunity in opportunities:
        decision = evaluate_paper_opportunity(opportunity=opportunity, context=context)
        result = PaperCoPilotResult(
            result_id=f"paper-result-{opportunity.opportunity_id}",
            opportunity=opportunity,
            decision=decision,
            hash_chain_valid=True,
        )
        if decision.creates_action:
            any_creates_action = True
        if decision.writes_external:
            any_writes_external = True
        if decision.approved_for_live:
            any_approved_for_live = True

        audit = emit_paper_copilot_evaluated(
            ledger=ledger,
            result=result,
            provenance=ProvenanceRef(source_event_id=opportunity.opportunity_id),
            now_ms=context.now_ms,
        )
        audit_ids.append(audit.event_id)
        permanent_ids.append(audit.event_id)

        outputs.append(decision.output)
        match decision.output:
            case SystemOutput.BLOCK:
                block_count += 1
            case SystemOutput.MONITOR:
                monitor_count += 1
            case SystemOutput.NEED_RECALL:
                need_recall_count += 1
            case SystemOutput.WAIT:
                wait_count += 1
            case SystemOutput.NO_ACTION:
                no_action_count += 1

    reason = (
        f"paper batch: seen={len(opportunities)} accepted={len(opportunities)} "
        f"rejected={schema_rejected} block={block_count} monitor={monitor_count} "
        f"need_recall={need_recall_count} wait={wait_count} no_action={no_action_count}"
    )
    assert_no_forbidden_literal(reason)

    return PaperCoPilotBatchResult(
        source_path=str(path),
        opportunities_seen=len(opportunities) + schema_rejected,
        opportunities_accepted=len(opportunities),
        opportunities_rejected=schema_rejected,
        outputs=tuple(outputs),
        block_count=block_count,
        monitor_count=monitor_count,
        need_recall_count=need_recall_count,
        wait_count=wait_count,
        no_action_count=no_action_count,
        audit_event_ids=tuple(audit_ids),
        permanent_event_ids=tuple(permanent_ids),
        ring_buffer_event_ids=tuple(ring_ids),
        hash_chain_valid=ledger.verify(),
        any_creates_action=any_creates_action,
        any_writes_external=any_writes_external,
        any_approved_for_live=any_approved_for_live,
        reason=reason,
    )


def cli_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="sentinel.runtime.paper_copilot",
        description="Paper co-pilot batch runner (shadow-only, no Gel.Al write).",
    )
    parser.add_argument(
        "--source-kind",
        required=True,
        choices=("market_jsonl", "gelal_shadow_jsonl", "paper_opportunity_jsonl"),
    )
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--ring-capacity", type=int, default=256)
    parser.add_argument("--now-ms", type=int, default=0)
    args = parser.parse_args(argv)

    ledger = JsonlObserverLedger(args.ledger)
    ring = ObserverRingBuffer(capacity=args.ring_capacity)
    context = PaperCoPilotContext(now_ms=args.now_ms)

    try:
        result = run_paper_copilot_file(
            path=args.input,
            source_kind=args.source_kind,
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id="paper-cli"),
            context=context,
        )
    except (FileNotFoundError, ValueError, ValidationError) as exc:
        print(f"paper-copilot: load/schema error: {exc}", file=sys.stderr)
        return 1

    print(
        "paper-copilot: "
        f"opportunities_seen={result.opportunities_seen} "
        f"accepted={result.opportunities_accepted} "
        f"rejected={result.opportunities_rejected} "
        f"block={result.block_count} "
        f"monitor={result.monitor_count} "
        f"need_recall={result.need_recall_count} "
        f"wait={result.wait_count} "
        f"no_action={result.no_action_count} "
        f"permanent={len(result.permanent_event_ids)} "
        f"ring={len(result.ring_buffer_event_ids)} "
        f"hash_chain_valid={result.hash_chain_valid}"
    )

    if not result.hash_chain_valid:
        return 2
    if result.any_creates_action or result.any_writes_external or result.any_approved_for_live:
        return 3
    return 0


if __name__ == "__main__":  # pragma: no cover (delegated via tests)
    raise SystemExit(cli_main())
