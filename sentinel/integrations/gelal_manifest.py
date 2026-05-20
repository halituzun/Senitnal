"""Observe-only AdapterManifest builder for the Gel.Al shadow adapter (V5).

Produces an ``AdapterManifest`` with ``capabilities=(OBSERVE,)`` and
the canonical binding (``external_source`` → ``OBSERVATION_EVENT``
via ``ingress_compiler``).  ``EXECUTE`` / ``INTENT_RELAY`` /
``MEMORY_WRITER`` / ``RECALL_PROVIDER`` are constitutionally absent.
``NeuralSeed`` is not a legal adapter output by v0.1 schema, so it
cannot be produced even if the manifest tried.

Pure schema constructor.  No I/O, no network, no LLM imports.
"""

from __future__ import annotations

from sentinel.types.adapters import (
    AdapterCapability,
    AdapterInputChannel,
    AdapterManifest,
    AdapterManifestStatus,
    AdapterOutputChannel,
    CapabilityBinding,
    RequiredGateRef,
)

_OBSERVE_BINDING = CapabilityBinding(
    capability=AdapterCapability.OBSERVE,
    input_channel=AdapterInputChannel.EXTERNAL_SOURCE,
    output_channel=AdapterOutputChannel.OBSERVATION_EVENT,
    required_gate_ref=RequiredGateRef.INGRESS_COMPILER,
    rate_limit_band="default",
)


def build_gelal_shadow_manifest(
    *,
    manifest_id: str = "gelal-shadow-manifest-001",
    adapter_id: str = "gelal-shadow",
    manifest_version: str = "v5-dev",
    status: AdapterManifestStatus = AdapterManifestStatus.ACTIVE,
) -> AdapterManifest:
    """Build the observe-only manifest for the Gel.Al shadow source."""
    return AdapterManifest(
        manifest_id=manifest_id,
        adapter_id=adapter_id,
        manifest_version=manifest_version,
        manifest_hash="sha256:" + ("g" * 64),
        signed_by="gelal-shadow-mock-key",
        signature="sig-gelal-shadow-mock",
        status=status,
        capabilities=(AdapterCapability.OBSERVE,),
        bindings=(_OBSERVE_BINDING,),
    )
