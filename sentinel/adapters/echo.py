"""EchoAdapter — synthetic ObservationEvent source for MVP dry sim.

Per the Phase 9 build plan: a fake outer-limb adapter that generates
ObservationEvent instances on demand. Signed mock manifest, observe-
only capability, trust band MEDIUM (configurable by tests).

Constitutional discipline (MVP):
    - Capability surface restricted to {OBSERVE}. Any attempt to
      construct an EchoAdapter manifest with EXECUTE, INTENT_RELAY,
      RECALL_PROVIDER, or MEMORY_WRITER is rejected at the manifest
      schema layer (already enforced in sentinel/types/adapters.py)
    - `emit_observation` ONLY produces ObservationEvent objects.
      Any attempt to call `emit_neural_seed_directly` triggers the
      constitutional red line (raises InvariantViolation +
      mutates the adapter's trust to REVOKED)
    - Tests verify the red-line path forces a revocation

What this module deliberately does NOT contain:
    - Network I/O (synthetic only)
    - LLM translation paths
    - State persistence across process restarts
"""

from __future__ import annotations

from dataclasses import dataclass

from sentinel.adapters.trust import AdapterTrustRecord, TrustBand, compute_trust
from sentinel.constitution.violations import InvariantViolation, ViolationContext
from sentinel.types.adapters import (
    AdapterCapability,
    AdapterInputChannel,
    AdapterManifest,
    AdapterManifestStatus,
    AdapterOutputChannel,
    CapabilityBinding,
    RequiredGateRef,
)
from sentinel.types.events import IngressEventType, ObservationEvent


def build_echo_manifest(
    *,
    manifest_id: str = "echo-manifest-001",
    adapter_id: str = "echo-adapter",
    manifest_version: str = "v0-dev",
) -> AdapterManifest:
    """Build the canonical observe-only EchoAdapter manifest."""
    return AdapterManifest(
        manifest_id=manifest_id,
        adapter_id=adapter_id,
        manifest_version=manifest_version,
        manifest_hash="sha256:" + ("e" * 64),
        signed_by="echo-mock-key",
        signature="sig-echo-mock",
        status=AdapterManifestStatus.ACTIVE,
        capabilities=(AdapterCapability.OBSERVE,),
        bindings=(
            CapabilityBinding(
                capability=AdapterCapability.OBSERVE,
                input_channel=AdapterInputChannel.EXTERNAL_SOURCE,
                output_channel=AdapterOutputChannel.OBSERVATION_EVENT,
                required_gate_ref=RequiredGateRef.INGRESS_COMPILER,
                rate_limit_band="default",
            ),
        ),
    )


def build_echo_trust(
    *,
    adapter_id: str = "echo-adapter",
    band: TrustBand = TrustBand.MEDIUM,
) -> AdapterTrustRecord:
    """Build a synthetic AdapterTrustRecord for the EchoAdapter.

    `band` is a hint; we produce soft scores whose product lands in
    the requested band.
    """
    if band is TrustBand.HIGH:
        soft = 0.95
    elif band is TrustBand.MEDIUM:
        soft = 0.85
    elif band is TrustBand.LOW:
        soft = 0.80
    elif band is TrustBand.QUARANTINED:
        soft = 0.70
    else:  # REVOKED — degenerate; force one hard gate failure instead
        return AdapterTrustRecord(
            adapter_id=adapter_id,
            signature_validity=False,
            manifest_hash_integrity=True,
            neural_seed_emission_count=0,
            channel_binding_compliance=1.0,
            rate_compliance=1.0,
            declaration_drift=1.0,
            reliability_score=1.0,
        )
    return AdapterTrustRecord(
        adapter_id=adapter_id,
        signature_validity=True,
        manifest_hash_integrity=True,
        neural_seed_emission_count=0,
        channel_binding_compliance=soft,
        rate_compliance=soft,
        declaration_drift=soft,
        reliability_score=soft,
    )


@dataclass
class EchoAdapter:
    """Synthetic outer-limb adapter (observe-only)."""

    manifest: AdapterManifest
    trust: AdapterTrustRecord
    _counter: int = 0

    @classmethod
    def default(cls) -> EchoAdapter:
        return cls(
            manifest=build_echo_manifest(),
            trust=build_echo_trust(),
        )

    def trust_band(self) -> TrustBand:
        return compute_trust(self.trust).band

    def emit_observation(
        self,
        *,
        magnitude_normalized: float,
        confidence: float = 0.7,
        novelty_indicator: float = 0.4,
        staleness_ms: int = 0,
        ttl_ms: int = 1000,
    ) -> ObservationEvent:
        """Emit a single synthetic ObservationEvent."""
        self._counter += 1
        return ObservationEvent(
            event_id=f"echo-obs-{self._counter:08d}",
            event_type=IngressEventType.OBSERVATION,
            occurred_at_ms=self._counter,
            ttl_ms=ttl_ms,
            confidence=confidence,
            source_adapter_id=self.manifest.adapter_id,
            source_reliability_band=3,
            magnitude_normalized=magnitude_normalized,
            novelty_indicator=novelty_indicator,
            staleness_ms=staleness_ms,
        )

    def emit_neural_seed_directly(self) -> None:
        """Constitutional red line: adapters NEVER emit NeuralSeed.

        Always raises `InvariantViolation`; the adapter's trust is
        considered REVOKED on this attempt (caller responsibility to
        persist the revocation; this method does NOT mutate, to keep
        the type immutable).
        """
        raise InvariantViolation(
            (
                f"adapter {self.manifest.adapter_id!r} attempted direct "
                "NeuralSeed emission; constitutional red line"
            ),
            ViolationContext(
                violation_code="ADAPTER_NEURAL_SEED_EMISSION_DETECTED",
                source_ref=("ADAPTER_MANIFEST_SPEC.md §7; ADAPTER_TRUST_NUMERICS.md §6"),
                evidence={"adapter_id": self.manifest.adapter_id},
            ),
        )
