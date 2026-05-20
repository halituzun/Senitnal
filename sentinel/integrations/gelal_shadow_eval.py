"""Gel.Al shadow evaluator (V5).

End-to-end per-envelope pipeline:

    GelAlShadowEnvelope
      -> emit_gelal_shadow_observation_ingested (ring-only via router)
      -> sanitize_gelal_shadow_to_observation_event
      -> compile_neural_seed
      -> WorkspacePulseEvent
      -> WORKSPACE_PULSE  (ring-only via router)
      -> closed SystemOutput  ∈ {WAIT, BLOCK, MONITOR, NEED_RECALL, NO_ACTION}

Constitutional discipline:
    - The evaluator never constructs an action-intent object.
    - It never writes to Gel.Al — there is no helper to do so.
    - It never promotes a memory record to verified.
    - It never mutates policy / config / kill switch.
    - The ``reason`` field passes ``assert_no_forbidden_literal``.

``BLOCK`` here is a **shadow** output: it is recorded in Sentinel's
ledger only and is NOT a signal to Gel.Al.  Gel.Al has no
subscription to Sentinel's output.
"""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import ValidationError

from sentinel.ingress.compiler import compile_neural_seed
from sentinel.integrations.gelal_audit import emit_gelal_shadow_observation_ingested
from sentinel.integrations.gelal_sanitizer import sanitize_gelal_shadow_to_observation_event
from sentinel.integrations.gelal_shadow import GelAlShadowEnvelope, GelAlShadowEventType
from sentinel.memory.store import InMemoryExplicitMemoryStore  # noqa: TC001 (runtime arg)
from sentinel.observer.hash_chain import placeholder_event_hash
from sentinel.observer.ledger import JsonlObserverLedger  # noqa: TC001 (runtime arg)
from sentinel.observer.ring_buffer import ObserverRingBuffer  # noqa: TC001 (runtime arg)
from sentinel.observer.router import route_observer_event
from sentinel.runtime.output import SystemOutput, assert_no_forbidden_literal
from sentinel.types.neural_seed import EventProfile, NeuralSeed, ProvenanceRef
from sentinel.types.observer import EventFamily, ObserverEvent
from sentinel.types.payload import PayloadSeed  # noqa: TC001 (runtime helper signature)
from sentinel.types.workspace import WorkspacePulseEvent


@dataclass(frozen=True, slots=True)
class GelAlShadowEvaluationResult:
    """Single-envelope shadow evaluation outcome."""

    event_id: str
    source_event_type: GelAlShadowEventType
    sentinel_output: SystemOutput
    reason: str
    observation_event_id: str
    neural_seed_total_intensity: float
    pulse_created: bool
    recall_requested: bool
    memory_candidate_created: bool
    replay_evidence_used: bool
    audit_event_ids: tuple[str, ...]
    permanent_event_ids: tuple[str, ...]
    ring_buffer_event_ids: tuple[str, ...]
    hash_chain_valid: bool


# ---------------------------------------------------------------------------
# Output policy — paraphrased to avoid forbidden literals.
#
# ``order``, ``execute``, ``submit``, ``buy``, ``sell``, ``_real`` are
# forbidden case-insensitive substrings in any Sentinel reason text
# (see sentinel/runtime/output.py).  The phrases below are
# intentionally constructed to avoid those substrings.
# ---------------------------------------------------------------------------


def _is_bad_dispatch(envelope: GelAlShadowEnvelope) -> bool:
    v = envelope.payload.get("bad_order")
    return isinstance(v, bool) and v


def _is_kill_switch_active(envelope: GelAlShadowEnvelope) -> bool:
    if envelope.event_type is not GelAlShadowEventType.KILL_SWITCH_OBSERVED:
        return False
    v = envelope.payload.get("kill_switch_active")
    return isinstance(v, bool) and v


def _risk_score(envelope: GelAlShadowEnvelope) -> float:
    v = envelope.payload.get("risk_score")
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return max(0.0, min(1.0, float(v)))
    return 0.0


def _derive_sentinel_output(
    envelope: GelAlShadowEnvelope, *, confidence: float
) -> tuple[
    SystemOutput,
    str,
]:
    """Map a Gel.Al shadow envelope to a closed SystemOutput value.

    Returned reason text is constructed to avoid any forbidden output
    literal substring (``buy``, ``sell``, ``execute``, ``order``,
    ``submit``, ``_real``).  This is verified by
    ``assert_no_forbidden_literal`` at the call site.
    """
    if _is_kill_switch_active(envelope):
        return (
            SystemOutput.BLOCK,
            "gel.al shadow: kill-switch active observed; shadow BLOCK",
        )
    if _is_bad_dispatch(envelope):
        return (
            SystemOutput.BLOCK,
            "gel.al shadow: venue actuation attempt flagged bad; shadow BLOCK",
        )

    risk = _risk_score(envelope)
    if envelope.event_type is GelAlShadowEventType.RISK_GATE_DECISION and risk >= 0.7:
        return (
            SystemOutput.BLOCK,
            "gel.al shadow: high-risk decision observed on remote risk gate; shadow BLOCK",
        )

    if envelope.event_type is GelAlShadowEventType.SYSTEM_HEALTH_OBSERVED:
        stale = envelope.payload.get("stale_count")
        if isinstance(stale, (int, float)) and not isinstance(stale, bool) and stale >= 5:
            return (
                SystemOutput.MONITOR,
                "gel.al shadow: stale data on remote component; shadow MONITOR",
            )

    if confidence < 0.3:
        return (
            SystemOutput.WAIT,
            "gel.al shadow: low-confidence observation; shadow WAIT",
        )

    if envelope.event_type in (
        GelAlShadowEventType.OPPORTUNITY_SEEN,
        GelAlShadowEventType.OPPORTUNITY_BLOCKED,
        GelAlShadowEventType.MARKET_OBSERVATION,
        GelAlShadowEventType.PAPER_RESULT_OBSERVED,
        GelAlShadowEventType.LIVE_RESULT_OBSERVED,
        GelAlShadowEventType.EXECUTION_ATTEMPT_OBSERVED,
    ):
        return (
            SystemOutput.MONITOR,
            "gel.al shadow: nominal observation accepted; shadow MONITOR",
        )

    return (
        SystemOutput.NO_ACTION,
        "gel.al shadow: weak signal; shadow NO_ACTION",
    )


def _unique_payloads(seeds: tuple[PayloadSeed, ...]) -> tuple[PayloadSeed, ...]:
    seen: set[object] = set()
    out: list[PayloadSeed] = []
    for s in seeds:
        if s.payload not in seen:
            seen.add(s.payload)
            out.append(s)
    return tuple(out)


def _make_pulse(
    *,
    seed: NeuralSeed,
    envelope: GelAlShadowEnvelope,
    coherence: float,
    ttl_ms: int,
) -> WorkspacePulseEvent:
    mass = min(seed.total_intensity, 1.0)
    allocation = mass / 2.0
    return WorkspacePulseEvent(
        pulse_id=f"gelal-pulse-{envelope.event_id}",
        assembly_id=f"gelal-assembly-{envelope.event_id}",
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
        context_signature_hash=f"sha256:gelal-ctx-{envelope.event_id}",
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


def evaluate_gelal_shadow_event(
    *,
    envelope: GelAlShadowEnvelope,
    ledger: JsonlObserverLedger,
    ring_buffer: ObserverRingBuffer,
    provenance: ProvenanceRef,
    memory_store: InMemoryExplicitMemoryStore | None = None,
    coherence: float = 0.4,
    ttl_ms: int = 1000,
) -> GelAlShadowEvaluationResult:
    """Run the shadow pipeline for a single Gel.Al envelope.

    Returns a ``GelAlShadowEvaluationResult`` containing the closed
    ``SystemOutput`` value, the audit/permanent/ring event ids, and
    the post-run hash chain status.

    ``memory_store`` is consulted **read-only**; the evaluator never
    writes to it.  Any V4 replay evidence integration would also be
    read-only — not implemented in V5 beyond accepting the parameter
    placeholder.
    """
    # ``memory_store`` accepted for API symmetry; V5 does not write.
    _ = memory_store

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

    # 1) OBSERVATION_INGESTED (ring-only via router).
    ingested = emit_gelal_shadow_observation_ingested(
        envelope=envelope,
        ledger=ledger,
        ring_buffer=ring_buffer,
        provenance=provenance,
    )
    audit_ids.append(ingested.event.event_id)
    if ingested.written_to_ledger:
        permanent_ids.append(ingested.event.event_id)
    if ingested.pushed_to_ring_buffer:
        ring_ids.append(ingested.event.event_id)

    # 2) Sanitize to ObservationEvent (no domain labels survive).
    obs = sanitize_gelal_shadow_to_observation_event(envelope, ttl_ms=ttl_ms)

    # 3) Compile NeuralSeed.
    pulse_created = False
    seed_intensity = 0.0
    try:
        seed = compile_neural_seed(
            profile=EventProfile.OBSERVATION_EVENT,
            event_attributes={
                "magnitude": obs.magnitude_normalized,
                "confidence": obs.confidence,
            },
            provenance=ProvenanceRef(source_event_id=obs.event_id),
        )
        seed_intensity = seed.total_intensity
        # 4) Build a pulse and route WORKSPACE_PULSE (ring-only).
        pulse = _make_pulse(seed=seed, envelope=envelope, coherence=coherence, ttl_ms=ttl_ms)
        _route(
            _build_pulse_event(
                pulse=pulse,
                provenance=ProvenanceRef(source_event_id=envelope.event_id),
            )
        )
        pulse_created = True
    except ValidationError:
        # Empty payload_seed: observation produced no signal.  No
        # pulse emitted; downstream output stays in closed set.
        pulse_created = False

    sentinel_output, reason = _derive_sentinel_output(envelope, confidence=obs.confidence)
    if not pulse_created and sentinel_output is SystemOutput.MONITOR:
        # Avoid claiming MONITOR when no pulse was produced.
        sentinel_output = SystemOutput.NO_ACTION
        reason = "gel.al shadow: observation produced no neural signal; shadow NO_ACTION"
    assert_no_forbidden_literal(reason)

    return GelAlShadowEvaluationResult(
        event_id=envelope.event_id,
        source_event_type=envelope.event_type,
        sentinel_output=sentinel_output,
        reason=reason,
        observation_event_id=obs.event_id,
        neural_seed_total_intensity=seed_intensity,
        pulse_created=pulse_created,
        recall_requested=False,
        memory_candidate_created=False,
        replay_evidence_used=False,
        audit_event_ids=tuple(audit_ids),
        permanent_event_ids=tuple(permanent_ids),
        ring_buffer_event_ids=tuple(ring_ids),
        hash_chain_valid=ledger.verify(),
    )
