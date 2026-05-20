"""V9 — Live governance batch runner + CLI.

Loads a local JSONL fixture of ``LiveGovernanceRequest`` records,
evaluates each through ``evaluate_governance_guard``, emits a
permanent ``LIVE_GOVERNANCE_DECISION_RECORDED`` audit per result.

No network, no Gel.Al write, no execution.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from sentinel.governance.audit import emit_live_governance_decision_recorded
from sentinel.governance.decision import GovernanceDecisionKind
from sentinel.governance.guard import GovernanceGuardContext, evaluate_governance_guard
from sentinel.governance.jsonl import LiveGovernanceRequestJsonlAdapter
from sentinel.observer.ledger import JsonlObserverLedger
from sentinel.observer.ring_buffer import ObserverRingBuffer
from sentinel.runtime.output import SystemOutput, assert_no_forbidden_literal
from sentinel.types.neural_seed import ProvenanceRef


@dataclass(frozen=True, slots=True)
class LiveGovernanceBatchResult:
    """Aggregated outcome of a live governance batch run."""

    source_path: str
    requests_seen: int
    requests_valid: int
    requests_rejected: int
    block_count: int
    monitor_count: int
    wait_count: int
    need_recall_count: int
    no_action_count: int
    outputs: tuple[SystemOutput, ...]
    audit_event_ids: tuple[str, ...]
    permanent_event_ids: tuple[str, ...]
    ring_buffer_event_ids: tuple[str, ...]
    hash_chain_valid: bool
    any_creates_action: bool
    any_writes_external: bool
    any_approves_trade: bool
    any_no_veto_is_approval: bool
    any_monitor_is_approval: bool
    reason: str


def run_live_governance_file(
    *,
    path: Path,
    ledger: JsonlObserverLedger,
    ring_buffer: ObserverRingBuffer,
    provenance: ProvenanceRef,
    context: GovernanceGuardContext,
) -> LiveGovernanceBatchResult:
    """Evaluate every governance request in ``path`` and audit each decision."""
    adapter = LiveGovernanceRequestJsonlAdapter(path=path)
    requests = adapter.read_all()

    audit_ids: list[str] = []
    permanent_ids: list[str] = []
    ring_ids: list[str] = []
    outputs: list[SystemOutput] = []
    block_count = monitor_count = wait_count = need_recall_count = no_action_count = 0
    any_creates_action = False
    any_writes_external = False
    any_approves_trade = False
    any_no_veto_is_approval = False
    any_monitor_is_approval = False

    # ``ring_buffer`` is kept for API symmetry; V9 audit is permanent.
    _ = ring_buffer

    for request in requests:
        decision = evaluate_governance_guard(request=request, context=context)
        if decision.creates_action:
            any_creates_action = True
        if decision.writes_external:
            any_writes_external = True
        if decision.approves_trade:
            any_approves_trade = True
        if decision.no_veto_is_approval:
            any_no_veto_is_approval = True
        if decision.monitor_is_approval:
            any_monitor_is_approval = True

        audit = emit_live_governance_decision_recorded(
            ledger=ledger,
            decision=decision,
            request=request,
            provenance=ProvenanceRef(source_event_id=request.request_id),
            now_ms=context.now_ms,
        )
        audit_ids.append(audit.event_id)
        permanent_ids.append(audit.event_id)
        outputs.append(decision.system_output)

        match decision.decision:
            case GovernanceDecisionKind.BLOCK_LIVE_CANDIDATE:
                block_count += 1
            case GovernanceDecisionKind.MONITOR_ONLY:
                monitor_count += 1
            case GovernanceDecisionKind.WAIT_FOR_HUMAN:
                wait_count += 1
            case GovernanceDecisionKind.NEED_RECALL:
                need_recall_count += 1
            case GovernanceDecisionKind.NO_ACTION:
                no_action_count += 1

    reason = (
        f"governance batch: seen={len(requests)} block={block_count} "
        f"monitor={monitor_count} wait={wait_count} "
        f"need_recall={need_recall_count} no_action={no_action_count}"
    )
    assert_no_forbidden_literal(reason)

    return LiveGovernanceBatchResult(
        source_path=str(path),
        requests_seen=len(requests),
        requests_valid=len(requests),
        requests_rejected=0,
        block_count=block_count,
        monitor_count=monitor_count,
        wait_count=wait_count,
        need_recall_count=need_recall_count,
        no_action_count=no_action_count,
        outputs=tuple(outputs),
        audit_event_ids=tuple(audit_ids),
        permanent_event_ids=tuple(permanent_ids),
        ring_buffer_event_ids=tuple(ring_ids),
        hash_chain_valid=ledger.verify(),
        any_creates_action=any_creates_action,
        any_writes_external=any_writes_external,
        any_approves_trade=any_approves_trade,
        any_no_veto_is_approval=any_no_veto_is_approval,
        any_monitor_is_approval=any_monitor_is_approval,
        reason=reason,
    )


def cli_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="sentinel.runtime.live_governance",
        description="Limited live governance batch runner (veto-first, no Gel.Al write).",
    )
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--ring-capacity", type=int, default=256)
    parser.add_argument("--now-ms", type=int, default=0)
    args = parser.parse_args(argv)

    ledger = JsonlObserverLedger(args.ledger)
    ring = ObserverRingBuffer(capacity=args.ring_capacity)
    # The CLI runs with no policy / canary / paper / approval context;
    # by construction every request will fail closed (block) because
    # of the missing-active-policy hard-stop.  This is the intended
    # behaviour: V9 CLI demonstrates fail-closed evaluation without
    # requiring an operator to supply live state via flags.
    context = GovernanceGuardContext(now_ms=args.now_ms)

    try:
        result = run_live_governance_file(
            path=args.input,
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id="governance-cli"),
            context=context,
        )
    except (FileNotFoundError, ValueError, ValidationError) as exc:
        print(f"live-governance: load/schema error: {exc}", file=sys.stderr)
        return 1

    print(
        "live-governance: "
        f"requests_seen={result.requests_seen} "
        f"block={result.block_count} "
        f"monitor={result.monitor_count} "
        f"wait={result.wait_count} "
        f"need_recall={result.need_recall_count} "
        f"no_action={result.no_action_count} "
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
        or result.any_monitor_is_approval
    ):
        return 3
    return 0


if __name__ == "__main__":  # pragma: no cover (delegated via tests)
    raise SystemExit(cli_main())
