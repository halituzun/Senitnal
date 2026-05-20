"""V10 — Financial AGI v1 batch runner + CLI.

Loads ``LiveGovernanceRequest`` records from a JSONL fixture, evaluates
each through the full Financial AGI v1 stack, emits permanent audit
events, and produces a readiness report.

No network, no Gel.Al write, no execution.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from sentinel.agi.audit import (
    emit_financial_agi_readiness_recorded,
    emit_financial_agi_v1_evaluated,
)
from sentinel.agi.evidence_gate import EvidenceGateInput
from sentinel.agi.orchestrator import (
    FinancialAGIInputBundle,
    FinancialAGIOutputBundle,
    evaluate_financial_agi_v1,
)
from sentinel.agi.readiness_report import (
    FinancialAGIReadinessReport,
    generate_financial_agi_readiness_report,
)
from sentinel.governance.guard import GovernanceGuardContext, evaluate_governance_guard
from sentinel.governance.jsonl import LiveGovernanceRequestJsonlAdapter
from sentinel.observer.ledger import JsonlObserverLedger
from sentinel.observer.ring_buffer import ObserverRingBuffer
from sentinel.runtime.output import SystemOutput, assert_no_forbidden_literal
from sentinel.types.neural_seed import ProvenanceRef


@dataclass(frozen=True, slots=True)
class FinancialAGIBatchResult:
    """Aggregated outcome of a Financial AGI v1 batch run."""

    source_path: str
    requests_seen: int
    block_count: int
    monitor_count: int
    wait_count: int
    need_recall_count: int
    no_action_count: int
    outputs: tuple[SystemOutput, ...]
    audit_event_ids: tuple[str, ...]
    readiness_report: FinancialAGIReadinessReport | None
    hash_chain_valid: bool
    any_creates_action: bool
    any_writes_external: bool
    any_approves_trade: bool
    any_no_veto_is_approval: bool
    any_monitor_is_approval: bool


def run_financial_agi_file(
    *,
    path: Path,
    ledger: JsonlObserverLedger,
    ring_buffer: ObserverRingBuffer,
    provenance: ProvenanceRef,
    context: GovernanceGuardContext,
    evidence_gate_input: EvidenceGateInput,
    emit_readiness_report: bool = True,
) -> FinancialAGIBatchResult:
    """Evaluate every governance request through the full AGI v1 stack."""
    adapter = LiveGovernanceRequestJsonlAdapter(path=path)
    requests = adapter.read_all()

    _ = ring_buffer  # V10 audit is permanent only.

    audit_ids: list[str] = []
    outputs: list[SystemOutput] = []
    block_count = monitor_count = wait_count = need_recall_count = no_action_count = 0
    any_creates_action = False
    any_writes_external = False
    any_approves_trade = False
    any_no_veto_is_approval = False
    any_monitor_is_approval = False
    last_bundle: FinancialAGIOutputBundle | None = None

    for req in requests:
        gov_decision = evaluate_governance_guard(request=req, context=context)

        bundle_input = FinancialAGIInputBundle(
            bundle_id=f"agi-{req.request_id}",
            now_ms=context.now_ms,
            provenance=ProvenanceRef(source_event_id=req.request_id),
            evidence_gate_input=evidence_gate_input,
            governance_context=context,
            live_governance_decision_kind=gov_decision.decision,
            policy_evaluation=None,
            paper_decision=context.paper_decision,
            canary_decision=context.canary_decision,
        )
        output_bundle = evaluate_financial_agi_v1(bundle_input)

        if output_bundle.creates_action:
            any_creates_action = True
        if output_bundle.writes_external:
            any_writes_external = True
        if output_bundle.approves_trade:
            any_approves_trade = True
        if output_bundle.no_veto_is_approval:
            any_no_veto_is_approval = True
        if output_bundle.monitor_is_approval:
            any_monitor_is_approval = True

        audit = emit_financial_agi_v1_evaluated(
            ledger=ledger,
            output_bundle=output_bundle,
            provenance=ProvenanceRef(source_event_id=req.request_id),
            now_ms=context.now_ms,
        )
        audit_ids.append(audit.event_id)
        outputs.append(output_bundle.final_output)
        last_bundle = output_bundle

        match output_bundle.final_output:
            case SystemOutput.BLOCK:
                block_count += 1
            case SystemOutput.MONITOR:
                monitor_count += 1
            case SystemOutput.WAIT:
                wait_count += 1
            case SystemOutput.NEED_RECALL:
                need_recall_count += 1
            case SystemOutput.NO_ACTION:
                no_action_count += 1

    # Readiness report from last bundle (or none if no requests).
    readiness_report: FinancialAGIReadinessReport | None = None
    if emit_readiness_report and last_bundle is not None:
        readiness_report = generate_financial_agi_readiness_report(
            report_id=f"readiness-{provenance.source_event_id}",
            output_bundle=last_bundle,
        )
        emit_financial_agi_readiness_recorded(
            ledger=ledger,
            report=readiness_report,
            provenance=provenance,
            now_ms=context.now_ms,
        )

    reason = (
        f"agi_v1 batch: seen={len(requests)} block={block_count} "
        f"monitor={monitor_count} wait={wait_count} "
        f"need_recall={need_recall_count} no_action={no_action_count}"
    )
    assert_no_forbidden_literal(reason)

    return FinancialAGIBatchResult(
        source_path=str(path),
        requests_seen=len(requests),
        block_count=block_count,
        monitor_count=monitor_count,
        wait_count=wait_count,
        need_recall_count=need_recall_count,
        no_action_count=no_action_count,
        outputs=tuple(outputs),
        audit_event_ids=tuple(audit_ids),
        readiness_report=readiness_report,
        hash_chain_valid=ledger.verify(),
        any_creates_action=any_creates_action,
        any_writes_external=any_writes_external,
        any_approves_trade=any_approves_trade,
        any_no_veto_is_approval=any_no_veto_is_approval,
        any_monitor_is_approval=any_monitor_is_approval,
    )


def cli_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="sentinel.runtime.financial_agi",
        description="Financial AGI v1 batch runner (veto-first, fail-closed, no Gel.Al write).",
    )
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--ring-capacity", type=int, default=256)
    parser.add_argument("--now-ms", type=int, default=0)
    args = parser.parse_args(argv)

    ledger = JsonlObserverLedger(args.ledger)
    ring = ObserverRingBuffer(capacity=args.ring_capacity)
    context = GovernanceGuardContext(now_ms=args.now_ms)
    evidence_gate_input = EvidenceGateInput(
        evaluation_id="cli-gate",
        windows=(),
        evaluated_at_ms=args.now_ms,
    )

    try:
        result = run_financial_agi_file(
            path=args.input,
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id="financial-agi-cli"),
            context=context,
            evidence_gate_input=evidence_gate_input,
        )
    except (FileNotFoundError, ValueError, ValidationError) as exc:
        print(f"financial-agi: load/schema error: {exc}", file=sys.stderr)
        return 1

    print(
        "financial-agi: "
        f"requests_seen={result.requests_seen} "
        f"block={result.block_count} "
        f"monitor={result.monitor_count} "
        f"wait={result.wait_count} "
        f"need_recall={result.need_recall_count} "
        f"no_action={result.no_action_count} "
        f"hash_chain_valid={result.hash_chain_valid}"
    )
    if result.readiness_report is not None:
        print(f"financial-agi: readiness_status={result.readiness_report.status}")

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
