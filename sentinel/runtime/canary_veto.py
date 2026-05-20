"""V8 — Canary veto batch runner + CLI.

Loads a local JSONL fixture of ``CanaryCandidateAction`` records,
evaluates each through the V8 canary veto evaluator, emits a
permanent ``CANARY_VETO_DECISION_RECORDED`` audit per result.

No network, no Gel.Al write, no execution.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from sentinel.canary.audit import emit_canary_veto_decision_recorded
from sentinel.canary.candidate import CanaryEnvironment
from sentinel.canary.evaluator import CanaryVetoContext, evaluate_canary_veto
from sentinel.canary.jsonl import CanaryCandidateJsonlAdapter
from sentinel.canary.limits import CanaryDecisionWindowState, CanaryMicroLiveBounds
from sentinel.canary.veto import VetoDecisionKind, VetoRequest
from sentinel.observer.ledger import JsonlObserverLedger
from sentinel.observer.ring_buffer import ObserverRingBuffer
from sentinel.runtime.output import SystemOutput, assert_no_forbidden_literal
from sentinel.types.neural_seed import ProvenanceRef


@dataclass(frozen=True, slots=True)
class CanaryVetoBatchResult:
    """Aggregated outcome of a canary veto batch run."""

    source_path: str
    candidates_seen: int
    candidates_valid: int
    candidates_rejected: int
    veto_count: int
    monitor_count: int
    no_veto_count: int
    outputs: tuple[SystemOutput, ...]
    audit_event_ids: tuple[str, ...]
    permanent_event_ids: tuple[str, ...]
    ring_buffer_event_ids: tuple[str, ...]
    hash_chain_valid: bool
    any_creates_action: bool
    any_writes_external: bool
    any_approves_trade: bool
    any_no_veto_is_approval: bool
    reason: str


def _default_bounds() -> CanaryMicroLiveBounds:
    """Conservative default bounds for the CLI."""
    return CanaryMicroLiveBounds(
        bounds_id="bounds-default",
        max_candidate_notional_ref="tier:micro",
        max_candidates_per_hour=100,
        max_vetoes_per_hour=100,
        max_unvetoed_candidates_per_hour=50,
        max_staleness_ms=2000,
        max_latency_ms=500,
        max_orderbook_age_ms=200,
        min_confidence=0.3,
        min_liquidity_score=0.1,
        max_risk_score=0.85,
    )


def run_canary_veto_file(
    *,
    path: Path,
    ledger: JsonlObserverLedger,
    ring_buffer: ObserverRingBuffer,
    provenance: ProvenanceRef,
    context: CanaryVetoContext,
) -> CanaryVetoBatchResult:
    """Evaluate every candidate in ``path`` and audit each decision."""
    adapter = CanaryCandidateJsonlAdapter(path=path)
    candidates = adapter.read_all()

    audit_ids: list[str] = []
    permanent_ids: list[str] = []
    ring_ids: list[str] = []
    outputs: list[SystemOutput] = []
    veto_count = monitor_count = no_veto_count = 0
    any_creates_action = False
    any_writes_external = False
    any_approves_trade = False
    any_no_veto_is_approval = False

    # ``ring_buffer`` is supplied for API symmetry; V8 audit is permanent.
    _ = ring_buffer

    for candidate in candidates:
        request = VetoRequest(
            request_id=f"req-{candidate.candidate_id}",
            candidate=candidate,
            requested_at_ms=context.now_ms,
            deadline_ms=context.now_ms + 5000,
            provenance=ProvenanceRef(source_event_id=candidate.candidate_id),
        )
        decision = evaluate_canary_veto(request=request, context=context)
        if decision.creates_action:
            any_creates_action = True
        if decision.writes_external:
            any_writes_external = True
        if decision.approves_trade:
            any_approves_trade = True
        if decision.no_veto_is_approval:
            any_no_veto_is_approval = True

        audit = emit_canary_veto_decision_recorded(
            ledger=ledger,
            decision=decision,
            request=request,
            provenance=ProvenanceRef(source_event_id=candidate.candidate_id),
            now_ms=context.now_ms,
        )
        audit_ids.append(audit.event_id)
        permanent_ids.append(audit.event_id)
        outputs.append(decision.system_output)

        if decision.decision is VetoDecisionKind.VETO:
            veto_count += 1
        elif decision.decision is VetoDecisionKind.MONITOR_ONLY:
            monitor_count += 1
        elif decision.decision is VetoDecisionKind.NO_VETO:
            no_veto_count += 1

    reason = (
        f"canary batch: seen={len(candidates)} veto={veto_count} "
        f"monitor={monitor_count} no_veto={no_veto_count}"
    )
    assert_no_forbidden_literal(reason)

    return CanaryVetoBatchResult(
        source_path=str(path),
        candidates_seen=len(candidates),
        candidates_valid=len(candidates),
        candidates_rejected=0,
        veto_count=veto_count,
        monitor_count=monitor_count,
        no_veto_count=no_veto_count,
        outputs=tuple(outputs),
        audit_event_ids=tuple(audit_ids),
        permanent_event_ids=tuple(permanent_ids),
        ring_buffer_event_ids=tuple(ring_ids),
        hash_chain_valid=ledger.verify(),
        any_creates_action=any_creates_action,
        any_writes_external=any_writes_external,
        any_approves_trade=any_approves_trade,
        any_no_veto_is_approval=any_no_veto_is_approval,
        reason=reason,
    )


def cli_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="sentinel.runtime.canary_veto",
        description="Canary micro-live veto batch runner (veto-only, no Gel.Al write).",
    )
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--ring-capacity", type=int, default=256)
    parser.add_argument("--now-ms", type=int, default=0)
    parser.add_argument(
        "--environment",
        choices=tuple(e.value for e in CanaryEnvironment),
        default=CanaryEnvironment.SHADOW.value,
    )
    args = parser.parse_args(argv)

    ledger = JsonlObserverLedger(args.ledger)
    ring = ObserverRingBuffer(capacity=args.ring_capacity)
    context = CanaryVetoContext(
        bounds=_default_bounds(),
        window_state=CanaryDecisionWindowState(last_reset_at_ms=args.now_ms),
        now_ms=args.now_ms,
    )

    try:
        result = run_canary_veto_file(
            path=args.input,
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id="canary-cli"),
            context=context,
        )
    except (FileNotFoundError, ValueError, ValidationError) as exc:
        print(f"canary-veto: load/schema error: {exc}", file=sys.stderr)
        return 1

    print(
        "canary-veto: "
        f"candidates_seen={result.candidates_seen} "
        f"veto={result.veto_count} "
        f"monitor={result.monitor_count} "
        f"no_veto={result.no_veto_count} "
        f"permanent={len(result.permanent_event_ids)} "
        f"ring={len(result.ring_buffer_event_ids)} "
        f"hash_chain_valid={result.hash_chain_valid}"
    )

    if not result.hash_chain_valid:
        return 2
    if (
        result.any_creates_action
        or result.any_writes_external
        or result.any_approves_trade
        or result.any_no_veto_is_approval
    ):
        return 3
    return 0


if __name__ == "__main__":  # pragma: no cover (delegated via tests)
    raise SystemExit(cli_main())
