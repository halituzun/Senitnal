"""Tests for the synthetic EchoAdapter."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sentinel.adapters.echo import (
    EchoAdapter,
    build_echo_manifest,
    build_echo_trust,
)
from sentinel.adapters.trust import TrustBand
from sentinel.constitution.violations import InvariantViolation
from sentinel.types.adapters import (
    AdapterCapability,
    AdapterInputChannel,
    AdapterManifest,
    AdapterManifestStatus,
    AdapterOutputChannel,
    CapabilityBinding,
    RequiredGateRef,
)


class TestManifest:
    def test_default_manifest_observe_only(self) -> None:
        m = build_echo_manifest()
        assert m.capabilities == (AdapterCapability.OBSERVE,)
        assert len(m.bindings) == 1
        assert m.bindings[0].capability is AdapterCapability.OBSERVE

    def test_forbidden_capability_pair_rejected_at_manifest(self) -> None:
        """Direct manifest construction with intent_relay + execute fails."""
        with pytest.raises(ValidationError):
            AdapterManifest(
                manifest_id="x",
                adapter_id="x",
                manifest_version="v0",
                manifest_hash="sha256:x",
                signed_by="k",
                signature="s",
                status=AdapterManifestStatus.CANDIDATE,
                capabilities=(
                    AdapterCapability.EXECUTE,
                    AdapterCapability.INTENT_RELAY,
                ),
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


class TestTrust:
    def test_default_band_medium(self) -> None:
        adapter = EchoAdapter.default()
        assert adapter.trust_band() is TrustBand.MEDIUM

    def test_revoked_trust_via_signature_failure(self) -> None:
        trust = build_echo_trust(band=TrustBand.REVOKED)
        adapter = EchoAdapter(
            manifest=build_echo_manifest(),
            trust=trust,
        )
        assert adapter.trust_band() is TrustBand.REVOKED


class TestEmitObservation:
    def test_emits_observation_event(self) -> None:
        adapter = EchoAdapter.default()
        ev = adapter.emit_observation(magnitude_normalized=0.7)
        assert ev.event_type.value == "ObservationEvent"
        assert ev.magnitude_normalized == 0.7
        assert ev.source_adapter_id == adapter.manifest.adapter_id

    def test_counter_advances(self) -> None:
        adapter = EchoAdapter.default()
        a = adapter.emit_observation(magnitude_normalized=0.1)
        b = adapter.emit_observation(magnitude_normalized=0.2)
        assert a.event_id != b.event_id


class TestRedLine:
    def test_neural_seed_direct_emission_rejected(self) -> None:
        adapter = EchoAdapter.default()
        with pytest.raises(InvariantViolation) as exc_info:
            adapter.emit_neural_seed_directly()
        assert exc_info.value.violation_code == "ADAPTER_NEURAL_SEED_EMISSION_DETECTED"
        assert exc_info.value.evidence["adapter_id"] == adapter.manifest.adapter_id
