"""Schema tests for AdapterManifest, CapabilityBinding, and the
adapter capability / channel / status enums.

Constitutional discipline tested here (schema layer only):
    - 5 canonical AdapterCapability values
    - 6 canonical AdapterManifestStatus values
    - Fixed per-capability channel-binding matrix
    - Capabilities unique, non-empty
    - Bindings non-empty
    - One binding per declared capability (no missing, no extra)
    - Incompatible capability pairs rejected
    - `execute` requires `observe`
    - Frozen immutability; extra="forbid"
    - NeuralSeed is NOT a legal adapter output channel
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sentinel.types.adapters import (
    AdapterCapability,
    AdapterInputChannel,
    AdapterManifest,
    AdapterManifestStatus,
    AdapterOutputChannel,
    CapabilityBinding,
    RequiredGateRef,
)

# ---------------------------------------------------------------------------
# Binding factories
# ---------------------------------------------------------------------------


def _observe_binding() -> CapabilityBinding:
    return CapabilityBinding(
        capability=AdapterCapability.OBSERVE,
        input_channel=AdapterInputChannel.EXTERNAL_SOURCE,
        output_channel=AdapterOutputChannel.OBSERVATION_EVENT,
        required_gate_ref=RequiredGateRef.INGRESS_COMPILER,
        rate_limit_band="default",
    )


def _execute_binding() -> CapabilityBinding:
    return CapabilityBinding(
        capability=AdapterCapability.EXECUTE,
        input_channel=AdapterInputChannel.APPROVED_ACTION_INTENT,
        output_channel=AdapterOutputChannel.EXECUTION_RESULT_EVENT,
        required_gate_ref=RequiredGateRef.DEONTIC_GATE,
        rate_limit_band="default",
    )


def _intent_relay_binding() -> CapabilityBinding:
    return CapabilityBinding(
        capability=AdapterCapability.INTENT_RELAY,
        input_channel=AdapterInputChannel.HUMAN_NATURAL_LANGUAGE,
        output_channel=AdapterOutputChannel.HUMAN_INTENT_EVENT,
        required_gate_ref=RequiredGateRef.INGRESS_COMPILER,
        rate_limit_band="default",
    )


def _recall_provider_binding() -> CapabilityBinding:
    return CapabilityBinding(
        capability=AdapterCapability.RECALL_PROVIDER,
        input_channel=AdapterInputChannel.RECALL_REQUEST,
        output_channel=AdapterOutputChannel.RECALL_EVENT,
        required_gate_ref=RequiredGateRef.NONE,
        rate_limit_band="default",
    )


def _memory_writer_binding() -> CapabilityBinding:
    return CapabilityBinding(
        capability=AdapterCapability.MEMORY_WRITER,
        input_channel=AdapterInputChannel.CANDIDATE_MEMORY_RECORD,
        output_channel=AdapterOutputChannel.MEMORY_RECORD_STATUS_CHANGED,
        required_gate_ref=RequiredGateRef.MEMORY_WRITE_GATE,
        rate_limit_band="default",
    )


def _valid_observe_manifest_kwargs() -> dict[str, object]:
    return {
        "manifest_id": "manifest-001",
        "adapter_id": "adapter-mock-feed",
        "manifest_version": "v0.1.0",
        "manifest_hash": "sha256:deadbeef",
        "signed_by": "operator-key-1",
        "signature": "sig-deadbeef",
        "status": AdapterManifestStatus.CANDIDATE,
        "capabilities": (AdapterCapability.OBSERVE,),
        "bindings": (_observe_binding(),),
    }


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class TestAdapterCapability:
    def test_five_canonical_values(self) -> None:
        expected = {
            "observe",
            "execute",
            "intent_relay",
            "recall_provider",
            "memory_writer",
        }
        assert {c.value for c in AdapterCapability} == expected

    def test_five_values(self) -> None:
        assert len(AdapterCapability) == 5


class TestAdapterManifestStatus:
    def test_canonical_six_values(self) -> None:
        expected = {
            "candidate",
            "registered",
            "active",
            "quarantined",
            "revoked",
            "superseded",
        }
        assert {s.value for s in AdapterManifestStatus} == expected

    def test_six_values(self) -> None:
        assert len(AdapterManifestStatus) == 6


class TestAdapterOutputChannel:
    def test_neural_seed_not_a_legal_output_channel(self) -> None:
        """Only the core/cortex emits NeuralSeed; adapters never do."""
        values = {c.value for c in AdapterOutputChannel}
        assert "NeuralSeed" not in values
        assert "neural_seed" not in values


# ---------------------------------------------------------------------------
# CapabilityBinding channel-matrix
# ---------------------------------------------------------------------------


class TestCapabilityBindingMatrix:
    def test_observe_binding_valid(self) -> None:
        binding = _observe_binding()
        assert binding.capability is AdapterCapability.OBSERVE

    def test_observe_wrong_input_channel_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CapabilityBinding(
                capability=AdapterCapability.OBSERVE,
                input_channel=AdapterInputChannel.APPROVED_ACTION_INTENT,
                output_channel=AdapterOutputChannel.OBSERVATION_EVENT,
                required_gate_ref=RequiredGateRef.INGRESS_COMPILER,
                rate_limit_band="default",
            )

    def test_observe_wrong_output_channel_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CapabilityBinding(
                capability=AdapterCapability.OBSERVE,
                input_channel=AdapterInputChannel.EXTERNAL_SOURCE,
                output_channel=AdapterOutputChannel.EXECUTION_RESULT_EVENT,
                required_gate_ref=RequiredGateRef.INGRESS_COMPILER,
                rate_limit_band="default",
            )

    def test_execute_wrong_gate_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CapabilityBinding(
                capability=AdapterCapability.EXECUTE,
                input_channel=AdapterInputChannel.APPROVED_ACTION_INTENT,
                output_channel=AdapterOutputChannel.EXECUTION_RESULT_EVENT,
                required_gate_ref=RequiredGateRef.INGRESS_COMPILER,
                rate_limit_band="default",
            )

    def test_empty_rate_limit_band_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CapabilityBinding(
                capability=AdapterCapability.OBSERVE,
                input_channel=AdapterInputChannel.EXTERNAL_SOURCE,
                output_channel=AdapterOutputChannel.OBSERVATION_EVENT,
                required_gate_ref=RequiredGateRef.INGRESS_COMPILER,
                rate_limit_band="",
            )


# ---------------------------------------------------------------------------
# AdapterManifest valid
# ---------------------------------------------------------------------------


class TestAdapterManifestValid:
    def test_valid_observe_only_manifest(self) -> None:
        manifest = AdapterManifest.model_validate(_valid_observe_manifest_kwargs())
        assert manifest.status is AdapterManifestStatus.CANDIDATE
        assert len(manifest.capabilities) == 1
        assert manifest.capabilities[0] is AdapterCapability.OBSERVE

    def test_valid_execute_plus_observe_manifest(self) -> None:
        manifest = AdapterManifest(
            manifest_id="manifest-002",
            adapter_id="adapter-broker-mock",
            manifest_version="v0.1.0",
            manifest_hash="sha256:cafebabe",
            signed_by="operator-key-1",
            signature="sig-cafebabe",
            status=AdapterManifestStatus.REGISTERED,
            capabilities=(AdapterCapability.OBSERVE, AdapterCapability.EXECUTE),
            bindings=(_observe_binding(), _execute_binding()),
        )
        assert set(manifest.capabilities) == {
            AdapterCapability.OBSERVE,
            AdapterCapability.EXECUTE,
        }

    def test_valid_intent_relay_only(self) -> None:
        manifest = AdapterManifest(
            manifest_id="manifest-003",
            adapter_id="adapter-human-cli",
            manifest_version="v0.1.0",
            manifest_hash="sha256:1234",
            signed_by="operator-key-1",
            signature="sig-1234",
            status=AdapterManifestStatus.ACTIVE,
            capabilities=(AdapterCapability.INTENT_RELAY,),
            bindings=(_intent_relay_binding(),),
        )
        assert manifest.capabilities[0] is AdapterCapability.INTENT_RELAY


# ---------------------------------------------------------------------------
# AdapterManifest structural invariants
# ---------------------------------------------------------------------------


class TestAdapterManifestStructural:
    def test_empty_capabilities_rejected(self) -> None:
        kwargs = _valid_observe_manifest_kwargs()
        kwargs["capabilities"] = ()
        kwargs["bindings"] = ()
        with pytest.raises(ValidationError):
            AdapterManifest.model_validate(kwargs)

    def test_empty_bindings_rejected(self) -> None:
        kwargs = _valid_observe_manifest_kwargs()
        kwargs["bindings"] = ()
        with pytest.raises(ValidationError):
            AdapterManifest.model_validate(kwargs)

    def test_duplicate_capability_rejected(self) -> None:
        kwargs = _valid_observe_manifest_kwargs()
        kwargs["capabilities"] = (
            AdapterCapability.OBSERVE,
            AdapterCapability.OBSERVE,
        )
        with pytest.raises(ValidationError):
            AdapterManifest.model_validate(kwargs)

    def test_missing_binding_for_declared_capability_rejected(self) -> None:
        with pytest.raises(ValidationError):
            AdapterManifest(
                manifest_id="manifest-004",
                adapter_id="adapter-x",
                manifest_version="v0.1.0",
                manifest_hash="sha256:x",
                signed_by="operator-key-1",
                signature="sig-x",
                status=AdapterManifestStatus.CANDIDATE,
                capabilities=(
                    AdapterCapability.OBSERVE,
                    AdapterCapability.EXECUTE,
                ),
                bindings=(_observe_binding(),),
            )

    def test_binding_for_undeclared_capability_rejected(self) -> None:
        with pytest.raises(ValidationError):
            AdapterManifest(
                manifest_id="manifest-005",
                adapter_id="adapter-x",
                manifest_version="v0.1.0",
                manifest_hash="sha256:x",
                signed_by="operator-key-1",
                signature="sig-x",
                status=AdapterManifestStatus.CANDIDATE,
                capabilities=(AdapterCapability.OBSERVE,),
                bindings=(_observe_binding(), _intent_relay_binding()),
            )

    def test_duplicate_binding_rejected(self) -> None:
        with pytest.raises(ValidationError):
            AdapterManifest(
                manifest_id="manifest-006",
                adapter_id="adapter-x",
                manifest_version="v0.1.0",
                manifest_hash="sha256:x",
                signed_by="operator-key-1",
                signature="sig-x",
                status=AdapterManifestStatus.CANDIDATE,
                capabilities=(AdapterCapability.OBSERVE,),
                bindings=(_observe_binding(), _observe_binding()),
            )


# ---------------------------------------------------------------------------
# Execute → observe required pair
# ---------------------------------------------------------------------------


class TestExecuteRequiresObserve:
    def test_execute_without_observe_rejected(self) -> None:
        with pytest.raises(ValidationError):
            AdapterManifest(
                manifest_id="manifest-007",
                adapter_id="adapter-broker",
                manifest_version="v0.1.0",
                manifest_hash="sha256:e",
                signed_by="operator-key-1",
                signature="sig-e",
                status=AdapterManifestStatus.CANDIDATE,
                capabilities=(AdapterCapability.EXECUTE,),
                bindings=(_execute_binding(),),
            )


# ---------------------------------------------------------------------------
# Incompatible capability pairs
# ---------------------------------------------------------------------------


class TestIncompatibleCapabilityPairs:
    """Each incompatible pair must be rejected at manifest construction."""

    def test_execute_plus_intent_relay_rejected(self) -> None:
        with pytest.raises(ValidationError):
            AdapterManifest(
                manifest_id="manifest-008",
                adapter_id="adapter-x",
                manifest_version="v0.1.0",
                manifest_hash="sha256:x",
                signed_by="operator-key-1",
                signature="sig-x",
                status=AdapterManifestStatus.CANDIDATE,
                capabilities=(
                    AdapterCapability.OBSERVE,
                    AdapterCapability.EXECUTE,
                    AdapterCapability.INTENT_RELAY,
                ),
                bindings=(
                    _observe_binding(),
                    _execute_binding(),
                    _intent_relay_binding(),
                ),
            )

    def test_execute_plus_recall_provider_rejected(self) -> None:
        with pytest.raises(ValidationError):
            AdapterManifest(
                manifest_id="manifest-009",
                adapter_id="adapter-x",
                manifest_version="v0.1.0",
                manifest_hash="sha256:x",
                signed_by="operator-key-1",
                signature="sig-x",
                status=AdapterManifestStatus.CANDIDATE,
                capabilities=(
                    AdapterCapability.OBSERVE,
                    AdapterCapability.EXECUTE,
                    AdapterCapability.RECALL_PROVIDER,
                ),
                bindings=(
                    _observe_binding(),
                    _execute_binding(),
                    _recall_provider_binding(),
                ),
            )

    def test_execute_plus_memory_writer_rejected(self) -> None:
        with pytest.raises(ValidationError):
            AdapterManifest(
                manifest_id="manifest-010",
                adapter_id="adapter-x",
                manifest_version="v0.1.0",
                manifest_hash="sha256:x",
                signed_by="operator-key-1",
                signature="sig-x",
                status=AdapterManifestStatus.CANDIDATE,
                capabilities=(
                    AdapterCapability.OBSERVE,
                    AdapterCapability.EXECUTE,
                    AdapterCapability.MEMORY_WRITER,
                ),
                bindings=(
                    _observe_binding(),
                    _execute_binding(),
                    _memory_writer_binding(),
                ),
            )

    def test_recall_provider_plus_memory_writer_rejected(self) -> None:
        with pytest.raises(ValidationError):
            AdapterManifest(
                manifest_id="manifest-011",
                adapter_id="adapter-x",
                manifest_version="v0.1.0",
                manifest_hash="sha256:x",
                signed_by="operator-key-1",
                signature="sig-x",
                status=AdapterManifestStatus.CANDIDATE,
                capabilities=(
                    AdapterCapability.RECALL_PROVIDER,
                    AdapterCapability.MEMORY_WRITER,
                ),
                bindings=(
                    _recall_provider_binding(),
                    _memory_writer_binding(),
                ),
            )

    def test_intent_relay_plus_memory_writer_rejected(self) -> None:
        with pytest.raises(ValidationError):
            AdapterManifest(
                manifest_id="manifest-012",
                adapter_id="adapter-x",
                manifest_version="v0.1.0",
                manifest_hash="sha256:x",
                signed_by="operator-key-1",
                signature="sig-x",
                status=AdapterManifestStatus.CANDIDATE,
                capabilities=(
                    AdapterCapability.INTENT_RELAY,
                    AdapterCapability.MEMORY_WRITER,
                ),
                bindings=(
                    _intent_relay_binding(),
                    _memory_writer_binding(),
                ),
            )

    def test_intent_relay_plus_recall_provider_rejected(self) -> None:
        with pytest.raises(ValidationError):
            AdapterManifest(
                manifest_id="manifest-013",
                adapter_id="adapter-x",
                manifest_version="v0.1.0",
                manifest_hash="sha256:x",
                signed_by="operator-key-1",
                signature="sig-x",
                status=AdapterManifestStatus.CANDIDATE,
                capabilities=(
                    AdapterCapability.INTENT_RELAY,
                    AdapterCapability.RECALL_PROVIDER,
                ),
                bindings=(
                    _intent_relay_binding(),
                    _recall_provider_binding(),
                ),
            )


# ---------------------------------------------------------------------------
# Required string fields / immutability
# ---------------------------------------------------------------------------


class TestRequiredStringFields:
    @pytest.mark.parametrize(
        "field",
        [
            "manifest_id",
            "adapter_id",
            "manifest_version",
            "manifest_hash",
            "signed_by",
            "signature",
        ],
    )
    def test_empty_string_field_rejected(self, field: str) -> None:
        kwargs = _valid_observe_manifest_kwargs()
        kwargs[field] = ""
        with pytest.raises(ValidationError):
            AdapterManifest.model_validate(kwargs)


class TestImmutability:
    def test_extra_field_rejected(self) -> None:
        kwargs = _valid_observe_manifest_kwargs()
        kwargs["rogue_field"] = "nope"
        with pytest.raises(ValidationError):
            AdapterManifest.model_validate(kwargs)

    def test_frozen(self) -> None:
        manifest = AdapterManifest.model_validate(_valid_observe_manifest_kwargs())
        with pytest.raises(ValidationError):
            setattr(manifest, "status", AdapterManifestStatus.ACTIVE)  # noqa: B010

    def test_binding_frozen(self) -> None:
        binding = _observe_binding()
        with pytest.raises(ValidationError):
            setattr(binding, "rate_limit_band", "another")  # noqa: B010
