"""Observe-only AdapterManifest builders for the V2 read-only market
adapter family.

Two builders are exposed:

    build_synthetic_market_manifest(...)     — for SyntheticMarketAdapter
    build_local_jsonl_market_manifest(...)   — for LocalJsonlMarketAdapter

Both produce an AdapterManifest with capabilities=(OBSERVE,) and the
canonical binding (external_source -> ObservationEvent via
ingress_compiler). EXECUTE / INTENT_RELAY / MEMORY_WRITER /
RECALL_PROVIDER are constitutionally absent. NeuralSeed is not a
legal AdapterOutputChannel by v0.1 schema, so neither builder can
produce one even if it wanted to.

This module owns NO ledger I/O, NO network code, NO LLM imports,
NO exchange SDK imports. It is a pure schema-constructor module.
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


def build_synthetic_market_manifest(
    *,
    manifest_id: str = "synthetic-market-manifest-001",
    adapter_id: str = "synthetic-market-adapter",
    manifest_version: str = "v2-dev",
    status: AdapterManifestStatus = AdapterManifestStatus.ACTIVE,
) -> AdapterManifest:
    """Build the manifest for a SyntheticMarketAdapter.

    Capabilities: (OBSERVE,). No EXECUTE, no INTENT_RELAY, no
    MEMORY_WRITER, no RECALL_PROVIDER. The output channel is
    OBSERVATION_EVENT — NeuralSeed is constitutionally not a legal
    adapter output (sentinel/types/adapters.py module docstring).
    """
    return AdapterManifest(
        manifest_id=manifest_id,
        adapter_id=adapter_id,
        manifest_version=manifest_version,
        manifest_hash="sha256:" + ("s" * 64),
        signed_by="synthetic-market-mock-key",
        signature="sig-synthetic-market-mock",
        status=status,
        capabilities=(AdapterCapability.OBSERVE,),
        bindings=(_OBSERVE_BINDING,),
    )


def build_local_jsonl_market_manifest(
    *,
    manifest_id: str = "local-jsonl-market-manifest-001",
    adapter_id: str = "local-jsonl-market-adapter",
    manifest_version: str = "v2-dev",
    status: AdapterManifestStatus = AdapterManifestStatus.ACTIVE,
) -> AdapterManifest:
    """Build the manifest for a LocalJsonlMarketAdapter.

    Same observe-only constitutional posture as the synthetic
    manifest. The local JSONL adapter is read-only with respect
    to the filesystem and has NO network or exchange-SDK surface.
    """
    return AdapterManifest(
        manifest_id=manifest_id,
        adapter_id=adapter_id,
        manifest_version=manifest_version,
        manifest_hash="sha256:" + ("j" * 64),
        signed_by="local-jsonl-market-mock-key",
        signature="sig-local-jsonl-market-mock",
        status=status,
        capabilities=(AdapterCapability.OBSERVE,),
        bindings=(_OBSERVE_BINDING,),
    )
