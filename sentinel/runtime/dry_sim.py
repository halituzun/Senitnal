"""End-to-end MVP dry simulation driver.

Per build plan §15 and §19: this module wires the MVP pipeline
end-to-end. The canonical run touches every audit helper that
should fire in MVP — adapter activation, observation ingest,
workspace pulse, recall-trigger evaluation — and routes each
event through `sentinel.observer.router.route_observer_event` so
the catalog's permanence policy is the single source of truth for
where events land (JSONL ledger vs. RAM ring buffer).

    EchoAdapter activation        -> ADAPTER_MANIFEST_STATUS_CHANGED  (PERMANENT)
    ObservationEvent              -> OBSERVATION_INGESTED             (RING_BUFFER_ONLY)
    compile_neural_seed           (no audit; pure)
    WorkspacePulseEvent           -> WORKSPACE_PULSE                  (RING_BUFFER_ONLY)
    recall trigger check          -> RECALL_TRIGGER_REJECTED          (PERMANENT)
    (optional) ApprovedActionIntent -> DEONTIC_BLOCKED                (PERMANENT)
    SystemOutput.WAIT

Constitutional discipline:
    - The pipeline produces ZERO action output. Final SystemOutput
      is always WAIT for the MVP-defined scenario, and any
      `exercise_deontic_gate` probe is BLOCKED by the gate
    - All output reason strings go through
      `assert_no_forbidden_literal` to guarantee the M1 ledger
      never carries an execution verb
    - Permanence routing is binding: ring_buffer_only events are
      pushed to the supplied `ring_buffer` if any, dropped
      otherwise (no implicit promotion to JSONL)
    - Single source of truth for ledger: this module accepts a
      `JsonlObserverLedger` and never creates a parallel writer
"""

from __future__ import annotations

from dataclasses import dataclass

from sentinel.adapters.audit import emit_manifest_status_changed
from sentinel.adapters.echo import EchoAdapter  # noqa: TC001 (runtime)
from sentinel.gates.deontic import (
    ApprovedActionIntent,
    evaluate_action_with_audit,
)
from sentinel.ingress.compiler import compile_neural_seed
from sentinel.observer.hash_chain import placeholder_event_hash
from sentinel.observer.ledger import JsonlObserverLedger  # noqa: TC001 (runtime)
from sentinel.observer.ring_buffer import ObserverRingBuffer  # noqa: TC001 (runtime)
from sentinel.observer.router import route_observer_event
from sentinel.recall.audit import emit_recall_trigger_rejected
from sentinel.recall.protocol import (
    RecallTriggerInputs,
    RecallTriggerSource,
    check_recall_trigger,
)
from sentinel.runtime.output import SystemOutput, assert_no_forbidden_literal
from sentinel.types.adapters import AdapterManifestStatus
from sentinel.types.neural_seed import EventProfile, NeuralSeed, ProvenanceRef
from sentinel.types.observer import EventFamily, ObserverEvent
from sentinel.types.payload import PayloadSeed  # noqa: TC001 (runtime)
from sentinel.types.workspace import WorkspacePulseEvent


@dataclass(frozen=True, slots=True)
class DrySimResult:
    """Result of one end-to-end MVP dry simulation pass.

    audit_event_ids:        every event that was routed through the
                            permanence router (ledger AND/OR ring
                            buffer) in this run, in insertion order.
    permanent_event_ids:    subset whose catalog permanence is
                            `permanent` or `permanent_with_snapshot`;
                            these are the events present in the
                            JSONL ledger after this run.
    ring_buffer_event_ids:  subset pushed into the in-memory ring
                            buffer (ring_buffer_only +
                            permanent_with_snapshot).
    """

    output: SystemOutput
    neural_seed: NeuralSeed
    pulse: WorkspacePulseEvent
    audit_event_ids: tuple[str, ...]
    permanent_event_ids: tuple[str, ...]
    ring_buffer_event_ids: tuple[str, ...]
    reason: str


def _make_pulse(
    *,
    seed: NeuralSeed,
    occurred_at_ms: int,
    ttl_ms: int,
    coherence: float,
) -> WorkspacePulseEvent:
    # Deterministic mapping: activation_mass = total_intensity (capped),
    # persistence + allocation share = activation/2, penalties = 0.
    mass = min(seed.total_intensity, 1.0)
    allocation = mass / 2.0
    return WorkspacePulseEvent(
        pulse_id=f"pulse-{seed.provenance.source_event_id}",
        assembly_id=f"assembly-{seed.provenance.source_event_id}",
        occurred_at_ms=occurred_at_ms,
        dominant_payload_mix=_unique_payloads(seed.payload_seed),
        activation_mass=mass,
        coherence=coherence,
        persistence=allocation,
        habituation_penalty=0.0,
        fatigue_penalty=0.0,
        dissonance_score=0.0,
        allocation_share=allocation,
        ttl_ms=ttl_ms,
        context_signature_hash=f"sha256:ctx-{seed.provenance.source_event_id}",
    )


def _unique_payloads(seeds: tuple[PayloadSeed, ...]) -> tuple[PayloadSeed, ...]:
    seen: set[object] = set()
    out: list[PayloadSeed] = []
    for s in seeds:
        if s.payload not in seen:
            seen.add(s.payload)
            out.append(s)
    return tuple(out)


def _build_observation_ingested(
    *,
    obs_event_id: str,
    occurred_at_ms: int,
    magnitude_normalized: float,
    confidence: float,
    source_adapter_id: str,
) -> ObserverEvent:
    return ObserverEvent(
        event_id=f"ingested-{obs_event_id}",
        event_family=EventFamily.INGRESS,
        event_type="OBSERVATION_INGESTED",
        occurred_at_ms=occurred_at_ms,
        payload={
            "source_event_id": obs_event_id,
            "source_adapter_id": source_adapter_id,
            "magnitude_normalized": magnitude_normalized,
            "confidence": confidence,
        },
        provenance=ProvenanceRef(source_event_id=obs_event_id),
        previous_event_hash=None,
        event_hash=placeholder_event_hash(),
    )


def _build_workspace_pulse_event(
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


def run_dry_simulation(
    *,
    ledger: JsonlObserverLedger,
    adapter: EchoAdapter,
    observation_magnitude: float,
    confidence: float = 0.7,
    coherence: float = 0.4,
    memory_echo_threshold: float = 0.5,
    emit_adapter_activation: bool = True,
    exercise_deontic_gate: bool = False,
    ring_buffer: ObserverRingBuffer | None = None,
) -> DrySimResult:
    """Run the MVP demonstration scenario.

    Pipeline (per catalog permanence policy):
        1. EchoAdapter activation (PERMANENT) -> JSONL ledger.
           Opt-out via emit_adapter_activation=False.
        2. Echo emits a synthetic ObservationEvent.
        3. OBSERVATION_INGESTED (RING_BUFFER_ONLY) -> router. If a
           ring_buffer is supplied it lands there; otherwise dropped
           (no JSONL promotion).
        4. Compile ObservationEvent -> NeuralSeed (pure).
        5. WORKSPACE_PULSE (RING_BUFFER_ONLY) -> router.
        6. Check recall trigger; on the MVP scenario it NEVER fires
           -> RECALL_TRIGGER_REJECTED (PERMANENT) -> JSONL ledger.
           (Per RECALL_PROTOCOL.md §5: exactly one audit event per
           recall evaluation.)
        7. If exercise_deontic_gate is True: generate a synthetic
           observe-only ApprovedActionIntent and run it through
           evaluate_action_with_audit -> DEONTIC_BLOCKED (PERMANENT)
           -> JSONL ledger. MVP guarantee: result is BLOCK.
        8. Final output: SystemOutput.WAIT.

    No execution-output literal is permitted into any reason text:
    every assembled reason string passes through
    `assert_no_forbidden_literal` before construction.
    """
    audit_ids: list[str] = []
    permanent_ids: list[str] = []
    ring_ids: list[str] = []

    def _route(event: ObserverEvent) -> None:
        outcome = route_observer_event(event=event, ledger=ledger, ring_buffer=ring_buffer)
        audit_ids.append(outcome.event.event_id)
        if outcome.written_to_ledger:
            permanent_ids.append(outcome.event.event_id)
        if outcome.pushed_to_ring_buffer:
            ring_ids.append(outcome.event.event_id)

    # 1) Adapter activation (PERMANENT) -> ledger.
    if emit_adapter_activation:
        activation = emit_manifest_status_changed(
            ledger,
            adapter_id=adapter.manifest.adapter_id,
            manifest_id=adapter.manifest.manifest_id,
            previous_status=AdapterManifestStatus.CANDIDATE,
            new_status=AdapterManifestStatus.ACTIVE,
            reason="dry_sim startup; adapter activated",
            now_ms=0,
        )
        audit_ids.append(activation.event_id)
        permanent_ids.append(activation.event_id)

    # 2) EchoAdapter emits a synthetic observation.
    obs = adapter.emit_observation(
        magnitude_normalized=observation_magnitude,
        confidence=confidence,
    )

    # 3) OBSERVATION_INGESTED (RING_BUFFER_ONLY) -> router.
    _route(
        _build_observation_ingested(
            obs_event_id=obs.event_id,
            occurred_at_ms=obs.occurred_at_ms,
            magnitude_normalized=obs.magnitude_normalized,
            confidence=obs.confidence,
            source_adapter_id=obs.source_adapter_id,
        )
    )

    # 4) Compile the observation into a NeuralSeed.
    seed = compile_neural_seed(
        profile=EventProfile.OBSERVATION_EVENT,
        event_attributes={
            "magnitude": obs.magnitude_normalized,
            "confidence": obs.confidence,
        },
        provenance=ProvenanceRef(source_event_id=obs.event_id),
    )

    # 5) Workspace pulse (RING_BUFFER_ONLY) -> router.
    pulse = _make_pulse(
        seed=seed,
        occurred_at_ms=obs.occurred_at_ms + 1,
        ttl_ms=obs.ttl_ms,
        coherence=coherence,
    )
    _route(
        _build_workspace_pulse_event(
            pulse=pulse,
            provenance=ProvenanceRef(source_event_id=obs.event_id),
        )
    )

    # 6) Recall trigger check (RECALL_TRIGGER_REJECTED is PERMANENT
    # so it lands in the JSONL chain).
    memory_echo_intensity = next(
        (s.intensity for s in seed.payload_seed if s.payload.value == "memory_echo"),
        0.0,
    )
    decision = check_recall_trigger(
        inputs=RecallTriggerInputs(
            memory_echo_intensity=memory_echo_intensity,
            context_signature_delta=0.0,
            fatigue_trace_intensity=0.0,
            budget_remaining=1,
            global_cooldown_active=False,
            sustained_tension_required=True,
            sustained_tension_observed=False,
        ),
        source=RecallTriggerSource.CORE,
        memory_echo_threshold=memory_echo_threshold,
        context_signature_delta_threshold=0.3,
        fatigue_trace_max=0.5,
    )
    assert decision.triggered is False  # MVP scenario guarantee
    assert_no_forbidden_literal(decision.reason)
    recall_audit = emit_recall_trigger_rejected(
        ledger,
        request_id=f"recall-from-{obs.event_id}",
        decision=decision,
        now_ms=obs.occurred_at_ms + 2,
    )
    audit_ids.append(recall_audit.event_id)
    permanent_ids.append(recall_audit.event_id)

    # 7) Optional deontic gate path -> DEONTIC_BLOCKED (PERMANENT).
    if exercise_deontic_gate:
        intent = ApprovedActionIntent(
            intent_id=f"intent-from-{obs.event_id}",
            intent_type="observe_only",
            rationale="dry_sim probe; MVP must BLOCK",
            requested_at_ms=obs.occurred_at_ms + 3,
        )
        outcome = evaluate_action_with_audit(ledger, intent, now_ms=obs.occurred_at_ms + 3)
        assert outcome.decision.value == "block"  # MVP guarantee
        deontic_event_id = f"deontic-block-{intent.intent_id}"
        audit_ids.append(deontic_event_id)
        permanent_ids.append(deontic_event_id)

    # 8) Final output. MVP: WAIT.
    reason = "MVP dry sim: observed, pulsed, recall rejected, no action; WAIT"
    assert_no_forbidden_literal(reason)
    return DrySimResult(
        output=SystemOutput.WAIT,
        neural_seed=seed,
        pulse=pulse,
        audit_event_ids=tuple(audit_ids),
        permanent_event_ids=tuple(permanent_ids),
        ring_buffer_event_ids=tuple(ring_ids),
        reason=reason,
    )
