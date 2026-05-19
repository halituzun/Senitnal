"""AdapterManifest schema, capabilities, channel bindings, and status.

Per ADAPTER_TRUST_NUMERICS.md / I §6-7 (channel binding constitution)
and the Phase 1 build plan: this module pins the schema-layer contract
for one adapter manifest — capability set, per-capability channel
binding, manifest identity / signature shape, and lifecycle status.

Constitutional discipline (schema layer only):
    - 5 canonical AdapterCapability values
    - Fixed per-capability channel binding matrix (input channel,
      output channel, required gate ref). One binding per declared
      capability; no missing, no extra
    - Incompatible capability pairs rejected at construction time
    - `execute` requires `observe` (efference / feedback pair)
    - Manifest identity / signature / version / hash are all required
      non-empty strings; signature *verification* is a loader concern
      (Phase 3+)
    - 6 lifecycle statuses; transitions are NOT validated here

What this module deliberately does NOT contain:
    - AdapterTrustRecord and trust scoring (Phase 9 / U)
    - SourceTrust bridge wiring (Phase 9)
    - Manifest lifecycle event logic / state-machine validation
    - Actual signature / hash verification
    - Rate-limit band numerics (U numerics; only `min_length>=1` here)
    - `NeuralSeed` is NEVER a legal adapter output channel
"""

from __future__ import annotations

from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AdapterCapability(StrEnum):
    """The 5 canonical adapter capabilities (I §6)."""

    OBSERVE = "observe"
    EXECUTE = "execute"
    INTENT_RELAY = "intent_relay"
    RECALL_PROVIDER = "recall_provider"
    MEMORY_WRITER = "memory_writer"


class AdapterInputChannel(StrEnum):
    """Closed set of input channels an adapter may consume."""

    EXTERNAL_SOURCE = "external_source"
    APPROVED_ACTION_INTENT = "approved_action_intent"
    HUMAN_NATURAL_LANGUAGE = "human_natural_language"
    RECALL_REQUEST = "recall_request"
    CANDIDATE_MEMORY_RECORD = "candidate_memory_record"


class AdapterOutputChannel(StrEnum):
    """Closed set of output channels (event types) an adapter may emit.

    `NeuralSeed` is intentionally NOT in this set: only the core /
    cortex may produce a NeuralSeed; adapters never do.
    """

    OBSERVATION_EVENT = "ObservationEvent"
    EXECUTION_RESULT_EVENT = "ExecutionResultEvent"
    HUMAN_INTENT_EVENT = "HumanIntentEvent"
    RECALL_EVENT = "RecallEvent"
    MEMORY_RECORD_STATUS_CHANGED = "MEMORY_RECORD_STATUS_CHANGED"


class RequiredGateRef(StrEnum):
    """Which gate must process an adapter binding's output before it
    becomes effective in the system."""

    INGRESS_COMPILER = "ingress_compiler"
    DEONTIC_GATE = "deontic_gate"
    MEMORY_WRITE_GATE = "memory_write_gate"
    NONE = "none"


class AdapterManifestStatus(StrEnum):
    """Adapter manifest lifecycle status (I §9)."""

    CANDIDATE = "candidate"
    REGISTERED = "registered"
    ACTIVE = "active"
    QUARANTINED = "quarantined"
    REVOKED = "revoked"
    SUPERSEDED = "superseded"


_EXPECTED_BINDING_MATRIX: dict[
    AdapterCapability,
    tuple[AdapterInputChannel, AdapterOutputChannel, RequiredGateRef],
] = {
    AdapterCapability.OBSERVE: (
        AdapterInputChannel.EXTERNAL_SOURCE,
        AdapterOutputChannel.OBSERVATION_EVENT,
        RequiredGateRef.INGRESS_COMPILER,
    ),
    AdapterCapability.EXECUTE: (
        AdapterInputChannel.APPROVED_ACTION_INTENT,
        AdapterOutputChannel.EXECUTION_RESULT_EVENT,
        RequiredGateRef.DEONTIC_GATE,
    ),
    AdapterCapability.INTENT_RELAY: (
        AdapterInputChannel.HUMAN_NATURAL_LANGUAGE,
        AdapterOutputChannel.HUMAN_INTENT_EVENT,
        RequiredGateRef.INGRESS_COMPILER,
    ),
    AdapterCapability.RECALL_PROVIDER: (
        AdapterInputChannel.RECALL_REQUEST,
        AdapterOutputChannel.RECALL_EVENT,
        RequiredGateRef.NONE,
    ),
    AdapterCapability.MEMORY_WRITER: (
        AdapterInputChannel.CANDIDATE_MEMORY_RECORD,
        AdapterOutputChannel.MEMORY_RECORD_STATUS_CHANGED,
        RequiredGateRef.MEMORY_WRITE_GATE,
    ),
}


_INCOMPATIBLE_CAPABILITY_PAIRS: frozenset[frozenset[AdapterCapability]] = frozenset(
    {
        frozenset({AdapterCapability.EXECUTE, AdapterCapability.INTENT_RELAY}),
        frozenset({AdapterCapability.EXECUTE, AdapterCapability.RECALL_PROVIDER}),
        frozenset({AdapterCapability.EXECUTE, AdapterCapability.MEMORY_WRITER}),
        frozenset({AdapterCapability.RECALL_PROVIDER, AdapterCapability.MEMORY_WRITER}),
        frozenset({AdapterCapability.INTENT_RELAY, AdapterCapability.MEMORY_WRITER}),
        frozenset({AdapterCapability.INTENT_RELAY, AdapterCapability.RECALL_PROVIDER}),
    }
)


class CapabilityBinding(BaseModel):
    """One capability bound to its (input, output, gate) channel triple.

    Schema-layer guarantees:
        - (input_channel, output_channel, required_gate_ref) must match
          the constitutional matrix entry for `capability`
        - `rate_limit_band` is a non-empty band name; numeric resolution
          lives in U numerics (Phase 3+)
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    capability: AdapterCapability
    input_channel: AdapterInputChannel
    output_channel: AdapterOutputChannel
    required_gate_ref: RequiredGateRef
    rate_limit_band: str = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_channel_matrix(self) -> Self:
        expected_input, expected_output, expected_gate = _EXPECTED_BINDING_MATRIX[self.capability]
        if self.input_channel is not expected_input:
            raise ValueError(
                f"capability {self.capability.value!r} requires input_channel="
                f"{expected_input.value!r}, got {self.input_channel.value!r}"
            )
        if self.output_channel is not expected_output:
            raise ValueError(
                f"capability {self.capability.value!r} requires output_channel="
                f"{expected_output.value!r}, got {self.output_channel.value!r}"
            )
        if self.required_gate_ref is not expected_gate:
            raise ValueError(
                f"capability {self.capability.value!r} requires required_gate_ref="
                f"{expected_gate.value!r}, got {self.required_gate_ref.value!r}"
            )
        return self


class AdapterManifest(BaseModel):
    """A signed adapter manifest (I §6-9).

    Schema-layer invariants enforced:
        - capabilities non-empty, unique
        - bindings non-empty
        - exactly one binding per declared capability:
            * no binding for an undeclared capability
            * no missing binding for a declared capability
        - No incompatible capability pair coexists
        - `execute` requires `observe` (efference / feedback pair)
        - manifest_id / adapter_id / manifest_version / manifest_hash /
          signed_by / signature are all non-empty strings

    Deliberately NOT enforced here:
        - signature / hash cryptographic verification (loader, Phase 3+)
        - lifecycle status transition validity (Phase 3+ state machine)
        - trust score / source-trust coupling (Phase 9, U numerics)
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    manifest_id: str = Field(min_length=1)
    adapter_id: str = Field(min_length=1)
    manifest_version: str = Field(min_length=1)
    manifest_hash: str = Field(min_length=1)
    signed_by: str = Field(min_length=1)
    signature: str = Field(min_length=1)
    status: AdapterManifestStatus
    capabilities: tuple[AdapterCapability, ...]
    bindings: tuple[CapabilityBinding, ...]

    @model_validator(mode="after")
    def _validate_capabilities_non_empty(self) -> Self:
        if len(self.capabilities) == 0:
            raise ValueError("capabilities must declare at least one capability")
        return self

    @model_validator(mode="after")
    def _validate_capabilities_unique(self) -> Self:
        if len(set(self.capabilities)) != len(self.capabilities):
            raise ValueError("capabilities must be unique")
        return self

    @model_validator(mode="after")
    def _validate_bindings_non_empty(self) -> Self:
        if len(self.bindings) == 0:
            raise ValueError("bindings must contain at least one CapabilityBinding")
        return self

    @model_validator(mode="after")
    def _validate_one_binding_per_capability(self) -> Self:
        declared = set(self.capabilities)
        bound: set[AdapterCapability] = set()
        for binding in self.bindings:
            if binding.capability in bound:
                raise ValueError(f"duplicate binding for capability {binding.capability.value!r}")
            if binding.capability not in declared:
                raise ValueError(f"binding for undeclared capability {binding.capability.value!r}")
            bound.add(binding.capability)
        missing = declared - bound
        if missing:
            missing_names = sorted(c.value for c in missing)
            raise ValueError(f"missing binding(s) for declared capability/-ies: {missing_names!r}")
        return self

    @model_validator(mode="after")
    def _validate_incompatible_capability_pairs(self) -> Self:
        declared = set(self.capabilities)
        for pair in _INCOMPATIBLE_CAPABILITY_PAIRS:
            if pair.issubset(declared):
                a, b = sorted(c.value for c in pair)
                raise ValueError(f"incompatible capability pair: {a!r} + {b!r}")
        return self

    @model_validator(mode="after")
    def _validate_execute_requires_observe(self) -> Self:
        declared = set(self.capabilities)
        if AdapterCapability.EXECUTE in declared and AdapterCapability.OBSERVE not in declared:
            raise ValueError(
                "capability 'execute' requires capability 'observe' (efference / feedback pair)"
            )
        return self
