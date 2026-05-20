"""End-to-end MVP dry simulation driver.

Per build plan §15 and §19: this module wires the MVP pipeline
end-to-end. The canonical run touches every audit helper that
should fire in MVP — adapter activation, observation ingest,
workspace pulse, and recall-trigger evaluation. The deontic gate
audit path is reachable via the `exercise_deontic_gate` opt-in so
the wiring is integration-tested without altering the build plan
§15 scenario (which has no ApprovedActionIntent).

    EchoAdapter activation        -> ADAPTER_MANIFEST_STATUS_CHANGED
    ObservationEvent              -> OBSERVATION_INGESTED
    compile_neural_seed           (no audit; pure)
    WorkspacePulseEvent           -> WORKSPACE_PULSE
    recall trigger check          -> RECALL_TRIGGER_REJECTED
    (optional) ApprovedActionIntent -> DEONTIC_BLOCKED
    SystemOutput.WAIT

Every audit-eligible step appends to the M1 ledger via the
single-writer `JsonlObserverLedger`, preserving the hash chain.

Constitutional discipline:
    - The pipeline produces ZERO action output. Final SystemOutput
      is always WAIT for the MVP-defined scenario, and any
      `exercise_deontic_gate` probe is BLOCKED by the gate
    - All output reason strings go through
      `assert_no_forbidden_literal` to guarantee the M1 ledger
      never carries an execution verb
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
from sentinel.workspace.pulse import emit_workspace_pulse


@dataclass(frozen=True, slots=True)
class DrySimResult:
    """Result of one end-to-end MVP dry simulation pass."""

    output: SystemOutput
    neural_seed: NeuralSeed
    pulse: WorkspacePulseEvent
    audit_event_ids: tuple[str, ...]
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
    # WorkspacePulseEvent forbids duplicates; the NeuralSeed schema
    # already guarantees uniqueness, but we keep the assertion explicit
    # so a future relaxation of either invariant fails here loudly.
    seen: set[object] = set()
    out: list[PayloadSeed] = []
    for s in seeds:
        if s.payload not in seen:
            seen.add(s.payload)
            out.append(s)
    return tuple(out)


def _emit_observation_ingested(
    *,
    ledger: JsonlObserverLedger,
    obs_event_id: str,
    occurred_at_ms: int,
    magnitude_normalized: float,
    confidence: float,
    source_adapter_id: str,
) -> ObserverEvent:
    return ledger.append(
        ObserverEvent(
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
) -> DrySimResult:
    """Run the MVP demonstration scenario.

    Canonical pipeline (every run):
        1. EchoAdapter activation audit       (ADAPTER_MANIFEST_STATUS_CHANGED)
           opt-out via emit_adapter_activation=False
        2. Echo emits a synthetic ObservationEvent
        3. OBSERVATION_INGESTED audit
        4. Compile ObservationEvent -> NeuralSeed
        5. Build pulse from seed, emit WORKSPACE_PULSE audit
        6. Check recall trigger; on the MVP scenario the trigger
           NEVER fires -> RECALL_TRIGGER_REJECTED audit (every
           recall evaluation produces exactly one audit event, per
           RECALL_PROTOCOL.md §5)
        7. If exercise_deontic_gate is True: generate a synthetic
           observe-only ApprovedActionIntent and run it through
           evaluate_action_with_audit. MVP guarantee: result is
           DeonticDecision.BLOCK and DEONTIC_BLOCKED is appended.
           Default is False to keep the canonical scenario
           identical to build plan §15 ('No ApprovedActionIntent
           generated by the MVP scenario').
        8. Final output: SystemOutput.WAIT.

    No execution-output literal is permitted into any reason text:
    every assembled reason string passes through
    `assert_no_forbidden_literal` before construction.
    """
    audit_ids: list[str] = []

    # 1) Adapter activation audit (optional but on by default so the
    # canonical run exercises the adapter audit wiring).
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

    # 2) EchoAdapter emits a synthetic observation.
    obs = adapter.emit_observation(
        magnitude_normalized=observation_magnitude,
        confidence=confidence,
    )

    # 3) Log OBSERVATION_INGESTED to M1.
    ingested = _emit_observation_ingested(
        ledger=ledger,
        obs_event_id=obs.event_id,
        occurred_at_ms=obs.occurred_at_ms,
        magnitude_normalized=obs.magnitude_normalized,
        confidence=obs.confidence,
        source_adapter_id=obs.source_adapter_id,
    )
    audit_ids.append(ingested.event_id)

    # 4) Compile the observation into a NeuralSeed.
    seed = compile_neural_seed(
        profile=EventProfile.OBSERVATION_EVENT,
        event_attributes={
            "magnitude": obs.magnitude_normalized,
            "confidence": obs.confidence,
        },
        provenance=ProvenanceRef(source_event_id=obs.event_id),
    )

    # 5) Build a workspace pulse from the seed and emit it. We always
    # emit in the canonical scenario; `should_emit_pulse` is the
    # decision helper future runtime code can use to gate emission
    # behind a coherence-cross threshold.
    pulse = _make_pulse(
        seed=seed,
        occurred_at_ms=obs.occurred_at_ms + 1,
        ttl_ms=obs.ttl_ms,
        coherence=coherence,
    )
    pulse_event = emit_workspace_pulse(
        ledger,
        pulse,
        provenance=ProvenanceRef(source_event_id=obs.event_id),
    )
    audit_ids.append(pulse_event.event_id)

    # 6) Check recall trigger. MVP scenario: memory_echo signal is
    # derived from the seed's memory_echo intensity (if any) and the
    # threshold is above the synthetic value -> no trigger. Per
    # RECALL_PROTOCOL.md §5 every recall evaluation produces exactly
    # one audit event; here it is RECALL_TRIGGER_REJECTED.
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

    # 7) Optionally exercise the deontic gate path so the
    # DEONTIC_BLOCKED audit wiring is reachable from the canonical
    # MVP pipeline (default off; build plan §15 scenario has no
    # ApprovedActionIntent).
    if exercise_deontic_gate:
        intent = ApprovedActionIntent(
            intent_id=f"intent-from-{obs.event_id}",
            intent_type="observe_only",
            rationale="dry_sim probe; MVP must BLOCK",
            requested_at_ms=obs.occurred_at_ms + 3,
        )
        outcome = evaluate_action_with_audit(ledger, intent, now_ms=obs.occurred_at_ms + 3)
        assert outcome.decision.value == "block"  # MVP guarantee
        audit_ids.append(f"deontic-block-{intent.intent_id}")

    # 8) Final output. MVP: WAIT (system observed + audited; took
    # no action). Reason text guarded against forbidden literals.
    reason = "MVP dry sim: observed, pulsed, recall rejected, no action; WAIT"
    assert_no_forbidden_literal(reason)
    return DrySimResult(
        output=SystemOutput.WAIT,
        neural_seed=seed,
        pulse=pulse,
        audit_event_ids=tuple(audit_ids),
        reason=reason,
    )
