"""Tests for the V2 observe-only market manifests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sentinel.adapters.market_manifest import (
    build_local_jsonl_market_manifest,
    build_synthetic_market_manifest,
)
from sentinel.types.adapters import (
    AdapterCapability,
    AdapterInputChannel,
    AdapterManifest,
    AdapterManifestStatus,
    AdapterOutputChannel,
    CapabilityBinding,
    RequiredGateRef,
)


class TestSyntheticMarketManifest:
    def test_observe_only_capability(self) -> None:
        m = build_synthetic_market_manifest()
        assert m.capabilities == (AdapterCapability.OBSERVE,)

    def test_observe_binding_canonical(self) -> None:
        m = build_synthetic_market_manifest()
        assert len(m.bindings) == 1
        b = m.bindings[0]
        assert b.capability is AdapterCapability.OBSERVE
        assert b.input_channel is AdapterInputChannel.EXTERNAL_SOURCE
        assert b.output_channel is AdapterOutputChannel.OBSERVATION_EVENT
        assert b.required_gate_ref is RequiredGateRef.INGRESS_COMPILER

    def test_no_execute_or_intent_relay_or_memory_writer(self) -> None:
        m = build_synthetic_market_manifest()
        forbidden = {
            AdapterCapability.EXECUTE,
            AdapterCapability.INTENT_RELAY,
            AdapterCapability.MEMORY_WRITER,
            AdapterCapability.RECALL_PROVIDER,
        }
        assert set(m.capabilities).isdisjoint(forbidden)

    def test_neural_seed_not_a_valid_output_channel(self) -> None:
        # Constitutional v0.1: AdapterOutputChannel intentionally has
        # no NeuralSeed member. This test pins that invariant.
        assert not hasattr(AdapterOutputChannel, "NEURAL_SEED")
        for member in AdapterOutputChannel:
            assert "neural" not in member.value.lower()

    def test_manifest_hash_and_signature_well_formed(self) -> None:
        m = build_synthetic_market_manifest()
        assert m.manifest_hash.startswith("sha256:")
        assert len(m.signature) > 0

    def test_executes_capability_combo_rejected_at_schema(self) -> None:
        # Building a manifest with EXECUTE but only OBSERVE binding
        # is illegal — the schema validator enforces capability ⇔
        # binding consistency.
        with pytest.raises(ValidationError):
            AdapterManifest(
                manifest_id="bad-001",
                adapter_id="bad-adapter",
                manifest_version="v2-dev",
                manifest_hash="sha256:" + ("b" * 64),
                signed_by="x",
                signature="y",
                status=AdapterManifestStatus.CANDIDATE,
                capabilities=(AdapterCapability.OBSERVE, AdapterCapability.EXECUTE),
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


class TestLocalJsonlMarketManifest:
    def test_observe_only_capability(self) -> None:
        m = build_local_jsonl_market_manifest()
        assert m.capabilities == (AdapterCapability.OBSERVE,)

    def test_binding_is_external_source_to_observation_event(self) -> None:
        m = build_local_jsonl_market_manifest()
        b = m.bindings[0]
        assert b.input_channel is AdapterInputChannel.EXTERNAL_SOURCE
        assert b.output_channel is AdapterOutputChannel.OBSERVATION_EVENT

    def test_distinct_from_synthetic_manifest(self) -> None:
        a = build_synthetic_market_manifest()
        b = build_local_jsonl_market_manifest()
        assert a.adapter_id != b.adapter_id
        assert a.manifest_id != b.manifest_id
        assert a.manifest_hash != b.manifest_hash
