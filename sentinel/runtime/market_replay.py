"""Synthetic / local-fixture market observation replay harness.

Drives the existing v0.1 pipeline using market-shaped envelopes:

    MarketObservationEnvelope
        -> OBSERVATION_INGESTED (router, ring_buffer_only)
        -> sanitize_market_observation_to_event (pure)
        -> ObservationEvent
        -> compile_neural_seed (existing v0.1 ingress compiler)
        -> WorkspacePulseEvent (existing v0.1 pulse mapping)
        -> WORKSPACE_PULSE (router, ring_buffer_only)
        -> SystemOutput in {WAIT, MONITOR, NO_ACTION}

Constitutional discipline:
    - This module produces ZERO action output. Outputs are restricted
      to the closed {WAIT, MONITOR, NO_ACTION} subset. WAIT is the
      default; MONITOR is used when a non-trivial NeuralSeed compiled
      (i.e. at least one PayloadSeed survived); NO_ACTION is reserved
      for the explicit "observation arrived but produced no signal"
      case.
    - All routing flows through `route_observer_event`. No bypass
      paths.
    - No network. No exchange SDK. No LLM SDK. The replay reads only
      from a local JSONL fixture (via LocalJsonlMarketAdapter) or
      from an in-memory iterable of envelopes.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Iterable  # noqa: TC003 (runtime annotation)
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from sentinel.adapters.local_jsonl_market import LocalJsonlMarketAdapter
from sentinel.adapters.market_audit import emit_market_observation_ingested
from sentinel.adapters.market_observation import (
    MarketObservationEnvelope,
    sanitize_market_observation_to_event,
)
from sentinel.ingress.compiler import compile_neural_seed
from sentinel.observer.hash_chain import placeholder_event_hash
from sentinel.observer.ledger import JsonlObserverLedger
from sentinel.observer.ring_buffer import ObserverRingBuffer
from sentinel.observer.router import route_observer_event
from sentinel.runtime.output import SystemOutput, assert_no_forbidden_literal
from sentinel.types.neural_seed import EventProfile, NeuralSeed, ProvenanceRef
from sentinel.types.observer import EventFamily, ObserverEvent
from sentinel.types.payload import PayloadSeed  # noqa: TC001 (used in runtime helper signature)
from sentinel.types.workspace import WorkspacePulseEvent


@dataclass(frozen=True, slots=True)
class MarketReplayResult:
    """Outcome of a market replay run."""

    source_path: str | None
    observations_seen: int
    observations_accepted: int
    observations_rejected: int
    neural_seed_count: int
    pulse_count: int
    outputs: tuple[SystemOutput, ...]
    audit_event_ids: tuple[str, ...]
    permanent_event_ids: tuple[str, ...]
    ring_buffer_event_ids: tuple[str, ...]
    hash_chain_valid: bool
    reason: str


def _unique_payloads(seeds: tuple[PayloadSeed, ...]) -> tuple[PayloadSeed, ...]:
    seen: set[object] = set()
    out: list[PayloadSeed] = []
    for s in seeds:
        if s.payload not in seen:
            seen.add(s.payload)
            out.append(s)
    return tuple(out)


def _make_pulse_for_seed(
    *,
    seed: NeuralSeed,
    envelope: MarketObservationEnvelope,
    coherence: float,
    ttl_ms: int,
) -> WorkspacePulseEvent:
    """Deterministic mapping from a market-derived seed to a pulse."""
    mass = min(seed.total_intensity, 1.0)
    allocation = mass / 2.0
    return WorkspacePulseEvent(
        pulse_id=f"market-pulse-{envelope.event_id}",
        assembly_id=f"market-assembly-{envelope.event_id}",
        occurred_at_ms=envelope.observed_at_ms + 1,
        dominant_payload_mix=_unique_payloads(seed.payload_seed),
        activation_mass=mass,
        coherence=coherence,
        persistence=allocation,
        habituation_penalty=0.0,
        fatigue_penalty=0.0,
        dissonance_score=0.0,
        allocation_share=allocation,
        ttl_ms=ttl_ms,
        context_signature_hash=f"sha256:market-ctx-{envelope.event_id}",
    )


def _build_pulse_event(
    *,
    pulse: WorkspacePulseEvent,
    provenance: ProvenanceRef,
) -> ObserverEvent:
    return ObserverEvent(
        event_id=pulse.pulse_id,
        event_family=EventFamily.ATTENTION,
        event_type="WORKSPACE_PULSE",
        occurred_at_ms=pulse.occurred_at_ms,
        payload=pulse.model_dump(mode="json"),
        provenance=provenance,
        previous_event_hash=None,
        event_hash=placeholder_event_hash(),
    )


def run_market_observations(
    *,
    observations: Iterable[MarketObservationEnvelope],
    ledger: JsonlObserverLedger,
    ring_buffer: ObserverRingBuffer,
    provenance: ProvenanceRef,
    coherence: float = 0.4,
    ttl_ms: int = 1000,
    source_path: str | None = None,
) -> MarketReplayResult:
    """Run market observations through the v0.1 pipeline.

    For each envelope:
        1. emit_market_observation_ingested  (ring_buffer_only)
        2. sanitize_market_observation_to_event
        3. compile_neural_seed
              if compilation produces an empty NeuralSeed
              (Pydantic ValidationError because payload_seed is
              empty), the observation is counted as rejected and
              no pulse is emitted; the run continues. Output for
              that envelope is NO_ACTION.
        4. If a seed compiled successfully, build a pulse and
           route WORKSPACE_PULSE (ring_buffer_only). Output is
           MONITOR.

    Returns a MarketReplayResult summarizing what happened.
    """
    audit_ids: list[str] = []
    permanent_ids: list[str] = []
    ring_ids: list[str] = []
    outputs: list[SystemOutput] = []

    observations_seen = 0
    observations_accepted = 0
    observations_rejected = 0
    neural_seed_count = 0
    pulse_count = 0

    def _route(event: ObserverEvent) -> None:
        outcome = route_observer_event(event=event, ledger=ledger, ring_buffer=ring_buffer)
        audit_ids.append(outcome.event.event_id)
        if outcome.written_to_ledger:
            permanent_ids.append(outcome.event.event_id)
        if outcome.pushed_to_ring_buffer:
            ring_ids.append(outcome.event.event_id)

    for envelope in observations:
        observations_seen += 1

        ingested = emit_market_observation_ingested(
            envelope=envelope,
            ledger=ledger,
            ring_buffer=ring_buffer,
            provenance=ProvenanceRef(source_event_id=envelope.event_id),
        )
        audit_ids.append(ingested.event.event_id)
        if ingested.written_to_ledger:
            permanent_ids.append(ingested.event.event_id)
        if ingested.pushed_to_ring_buffer:
            ring_ids.append(ingested.event.event_id)

        obs = sanitize_market_observation_to_event(envelope, ttl_ms=ttl_ms)

        try:
            seed = compile_neural_seed(
                profile=EventProfile.OBSERVATION_EVENT,
                event_attributes={
                    "magnitude": obs.magnitude_normalized,
                    "confidence": obs.confidence,
                },
                provenance=ProvenanceRef(source_event_id=obs.event_id),
            )
        except ValidationError:
            # Empty payload_seed: observation produced no signal.
            observations_rejected += 1
            outputs.append(SystemOutput.NO_ACTION)
            continue

        observations_accepted += 1
        neural_seed_count += 1
        pulse = _make_pulse_for_seed(
            seed=seed, envelope=envelope, coherence=coherence, ttl_ms=ttl_ms
        )
        _route(
            _build_pulse_event(
                pulse=pulse, provenance=ProvenanceRef(source_event_id=envelope.event_id)
            )
        )
        pulse_count += 1
        outputs.append(SystemOutput.MONITOR)

    if observations_seen == 0:
        outputs.append(SystemOutput.WAIT)

    reason = (
        f"market replay: seen={observations_seen} accepted={observations_accepted} "
        f"rejected={observations_rejected} pulses={pulse_count}; "
        "no action, observation only"
    )
    assert_no_forbidden_literal(reason)

    return MarketReplayResult(
        source_path=source_path,
        observations_seen=observations_seen,
        observations_accepted=observations_accepted,
        observations_rejected=observations_rejected,
        neural_seed_count=neural_seed_count,
        pulse_count=pulse_count,
        outputs=tuple(outputs),
        audit_event_ids=tuple(audit_ids),
        permanent_event_ids=tuple(permanent_ids),
        ring_buffer_event_ids=tuple(ring_ids),
        hash_chain_valid=ledger.verify(),
        reason=reason,
    )


def run_market_jsonl_file(
    *,
    path: Path,
    ledger: JsonlObserverLedger,
    ring_buffer: ObserverRingBuffer,
    provenance: ProvenanceRef,
    coherence: float = 0.4,
    ttl_ms: int = 1000,
) -> MarketReplayResult:
    """Run a market replay sourced from a local JSONL fixture file."""
    adapter = LocalJsonlMarketAdapter(path=path)
    envelopes = adapter.read_all()
    return run_market_observations(
        observations=envelopes,
        ledger=ledger,
        ring_buffer=ring_buffer,
        provenance=provenance,
        coherence=coherence,
        ttl_ms=ttl_ms,
        source_path=str(path),
    )


def _cli_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="sentinel.runtime.market_replay",
        description="Synthetic / local market observation replay (no network, no live exchange).",
    )
    parser.add_argument(
        "--fixture", required=True, type=Path, help="Path to a JSONL market fixture file."
    )
    parser.add_argument(
        "--ledger",
        required=True,
        type=Path,
        help="Path to write the JSONL observer ledger (created if missing).",
    )
    parser.add_argument("--coherence", type=float, default=0.4)
    parser.add_argument("--ttl-ms", type=int, default=1000)
    parser.add_argument("--ring-capacity", type=int, default=256)
    args = parser.parse_args(argv)

    ledger = JsonlObserverLedger(args.ledger)
    ring = ObserverRingBuffer(capacity=args.ring_capacity)

    try:
        result = run_market_jsonl_file(
            path=args.fixture,
            ledger=ledger,
            ring_buffer=ring,
            provenance=ProvenanceRef(source_event_id="market-replay-cli"),
            coherence=args.coherence,
            ttl_ms=args.ttl_ms,
        )
    except (FileNotFoundError, ValueError, ValidationError) as exc:
        print(f"market-replay: fixture load error: {exc}", file=sys.stderr)
        return 1

    print(
        "market-replay: "
        f"observations_seen={result.observations_seen} "
        f"accepted={result.observations_accepted} "
        f"rejected={result.observations_rejected} "
        f"pulses={result.pulse_count} "
        f"outputs={tuple(o.value for o in result.outputs)} "
        f"permanent={len(result.permanent_event_ids)} "
        f"ring={len(result.ring_buffer_event_ids)} "
        f"hash_chain_valid={result.hash_chain_valid}"
    )

    if not result.hash_chain_valid:
        return 2
    return 0


if __name__ == "__main__":  # pragma: no cover (delegated via tests)
    raise SystemExit(_cli_main())
