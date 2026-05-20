"""V6 — Local policy evaluation CLI.

Loads a JSON policy artifact, registers it locally as an ACTIVE
deontic-policy record (dev path only — production activation requires
MWG + verified + human approval), reads a Gel.Al shadow JSONL fixture,
and evaluates every event under the policy.

No network, no Gel.Al write, no execution.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from sentinel.integrations.gelal_jsonl import GelAlShadowJsonlAdapter
from sentinel.integrations.gelal_policy import evaluate_gelal_shadow_with_policy
from sentinel.observer.ledger import JsonlObserverLedger
from sentinel.observer.ring_buffer import ObserverRingBuffer
from sentinel.policy.financial import FinancialDeonticPolicyArtifact
from sentinel.policy.record_builder import build_deontic_policy_candidate_record
from sentinel.runtime.output import SystemOutput
from sentinel.types.memory import MemoryRecordStatus
from sentinel.types.neural_seed import ProvenanceRef


@dataclass(frozen=True, slots=True)
class PolicyEvalResult:
    events_seen: int
    block_count: int
    monitor_count: int
    wait_count: int
    need_recall_count: int
    no_action_count: int
    permanent_count: int
    ring_count: int
    hash_chain_valid: bool
    any_creates_action: bool
    any_writes_external: bool


def _activate_locally(
    artifact: FinancialDeonticPolicyArtifact,
    now_ms: int,
) -> object:
    """Construct an in-memory ACTIVE policy record for the CLI.

    This is the local-dev activation path; production activation
    requires MWG + verified status + human_approval_ref.
    """
    candidate = build_deontic_policy_candidate_record(
        artifact=artifact,
        provenance=ProvenanceRef(source_event_id=artifact.artifact_id),
        created_at_ms=now_ms,
        evidence_refs=("cli-local",),
    )
    return candidate.model_copy(
        update={
            "status": MemoryRecordStatus.ACTIVE,
            "last_status_change_ms": now_ms,
        }
    )


def run_policy_eval(
    *,
    policy_path: Path,
    gelal_path: Path,
    ledger: JsonlObserverLedger,
    ring_buffer: ObserverRingBuffer,
    now_ms: int = 0,
) -> PolicyEvalResult:
    """Load policy + Gel.Al fixture and evaluate every event."""
    artifact_text = policy_path.read_text(encoding="utf-8")
    artifact = FinancialDeonticPolicyArtifact.model_validate_json(artifact_text)
    if now_ms == 0:
        now_ms = artifact.effective_at_ms
    active_record = _activate_locally(artifact, now_ms)

    adapter = GelAlShadowJsonlAdapter(path=gelal_path)
    envelopes = adapter.read_all()

    block = monitor = wait = need_recall = no_action = 0
    any_creates_action = False
    any_writes_external = False

    permanent_ids: list[str] = []
    ring_ids: list[str] = []

    for envelope in envelopes:
        evaluation = evaluate_gelal_shadow_with_policy(
            envelope=envelope,
            active_policy_record=active_record,  # type: ignore[arg-type]
            ledger=ledger,
            ring_buffer=ring_buffer,
            provenance=ProvenanceRef(source_event_id=envelope.event_id),
            now_ms=now_ms,
        )
        if evaluation.creates_action:
            any_creates_action = True
        if evaluation.writes_external:
            any_writes_external = True

        match evaluation.output:
            case SystemOutput.BLOCK:
                block += 1
            case SystemOutput.MONITOR:
                monitor += 1
            case SystemOutput.WAIT:
                wait += 1
            case SystemOutput.NEED_RECALL:
                need_recall += 1
            case SystemOutput.NO_ACTION:
                no_action += 1

    # Ring buffer push count and permanent length come from the ledger
    # / ring_buffer themselves; we approximate by counting via verify.
    return PolicyEvalResult(
        events_seen=len(envelopes),
        block_count=block,
        monitor_count=monitor,
        wait_count=wait,
        need_recall_count=need_recall,
        no_action_count=no_action,
        permanent_count=len(permanent_ids),
        ring_count=len(ring_ids),
        hash_chain_valid=ledger.verify(),
        any_creates_action=any_creates_action,
        any_writes_external=any_writes_external,
    )


def cli_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="sentinel.runtime.policy_eval",
        description="Local financial deontic policy evaluator (shadow-only).",
    )
    parser.add_argument("--policy", required=True, type=Path)
    parser.add_argument("--gelal", required=True, type=Path)
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--ring-capacity", type=int, default=256)
    parser.add_argument("--now-ms", type=int, default=0)
    args = parser.parse_args(argv)

    ledger = JsonlObserverLedger(args.ledger)
    ring = ObserverRingBuffer(capacity=args.ring_capacity)

    try:
        result = run_policy_eval(
            policy_path=args.policy,
            gelal_path=args.gelal,
            ledger=ledger,
            ring_buffer=ring,
            now_ms=args.now_ms,
        )
    except (FileNotFoundError, ValueError, ValidationError, json.JSONDecodeError) as exc:
        print(f"policy-eval: load/schema error: {exc}", file=sys.stderr)
        return 1

    print(
        "policy-eval: "
        f"events_seen={result.events_seen} "
        f"block={result.block_count} "
        f"monitor={result.monitor_count} "
        f"wait={result.wait_count} "
        f"need_recall={result.need_recall_count} "
        f"no_action={result.no_action_count} "
        f"hash_chain_valid={result.hash_chain_valid}"
    )

    if not result.hash_chain_valid:
        return 2
    if result.any_creates_action or result.any_writes_external:
        return 3
    return 0


if __name__ == "__main__":  # pragma: no cover (delegated via tests)
    raise SystemExit(cli_main())
