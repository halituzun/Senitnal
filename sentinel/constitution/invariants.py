"""Constitutional invariant catalog and assertion helpers.

Per the build plan §6 (Phase 1 — Contracts as Code) and the closure
of Commit 10 (exception vocabulary): this module pins the MVP
**REQUIRED** invariant catalog as a closed tuple of immutable
`InvariantDefinition` rows, plus a tiny helper surface for runtime
sites to assert against catalog entries.

Design intent (schema-only at this stage):
    - Catalog is data, not behavior. Each entry carries its
      severity, category, source_ref, statement, and an
      `mvp_required` flag (always True for v0.1, kept explicit so
      later phases can add `mvp_required=False` rows without
      destabilizing the v0.1 set)
    - Helpers do not import from `sentinel.types.*`. The catalog is
      a passive registry; concrete schema-level checks live in the
      schemas themselves (Phase 1), and runtime composite checks
      will land in later phases
    - `assert_invariant(condition, code, evidence=...)` raises
      `InvariantViolation` with a `ViolationContext` bound to the
      catalog row, so observer sites get a fully-decorated breach

What this module deliberately does NOT contain:
    - Imports from `sentinel.types.*` (kept fully decoupled)
    - Concrete schema checks (those are in the Pydantic models)
    - Runtime / observer enforcement plumbing (later phases)
    - The full 50+ invariant master set; the v0.1 catalog is the
      curated red-line set required for MVP. Later phases add rows
      without removing or renaming existing codes
"""

from __future__ import annotations

from collections.abc import Mapping  # noqa: TC003 (dataclass field runtime annotation)
from dataclasses import dataclass
from enum import StrEnum

from sentinel.constitution.violations import InvariantViolation, ViolationContext


class InvariantSeverity(StrEnum):
    """Severity tier for a constitutional invariant."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"


class InvariantCategory(StrEnum):
    """Category bucket for a constitutional invariant."""

    CORE_PAYLOAD = "core_payload"
    INGRESS_BOUNDARY = "ingress_boundary"
    OBSERVER_LEDGER = "observer_ledger"
    MEMORY_BOUNDARY = "memory_boundary"
    ADAPTER_BOUNDARY = "adapter_boundary"
    NUMERICS_GOVERNANCE = "numerics_governance"
    WORKSPACE = "workspace"
    MVP_RUNTIME = "mvp_runtime"


@dataclass(frozen=True, slots=True)
class InvariantDefinition:
    """One row in the constitutional invariant catalog.

    Fields:
        code:         closed-set short identifier (UPPER_SNAKE_CASE)
        category:     bucket from `InvariantCategory`
        severity:     `InvariantSeverity` tier
        source_ref:   spec section anchor
                      (e.g. "CONSTITUTION.md §6:Madde-6")
        statement:    human-readable invariant
        mvp_required: always True for the v0.1 set; explicit so the
                      catalog can grow to non-MVP rows in later phases
    """

    code: str
    category: InvariantCategory
    severity: InvariantSeverity
    source_ref: str
    statement: str
    mvp_required: bool = True


MVP_REQUIRED_INVARIANTS: tuple[InvariantDefinition, ...] = (
    # ---- CORE_PAYLOAD ------------------------------------------------------
    InvariantDefinition(
        code="PAYLOAD_CLOSED_PRIMER_PALETTE",
        category=InvariantCategory.CORE_PAYLOAD,
        severity=InvariantSeverity.CRITICAL,
        source_ref="BOOTSTRAP_GENOME.md §4 + INGRESS_COMPILER_SPEC.md §11",
        statement=(
            "Primer payload palette is the closed set of 10 constitutional "
            "values; extra payload kinds are rejected at the type boundary."
        ),
    ),
    InvariantDefinition(
        code="PAYLOAD_REJECTS_TASK_LABELS",
        category=InvariantCategory.CORE_PAYLOAD,
        severity=InvariantSeverity.CRITICAL,
        source_ref="MEMORY_CONTRACT.md §3 + WORLD_INGRESS.md §6",
        statement=(
            "PayloadSeed rejects action / task tokens as payload values "
            "(no execution verbs as payloads)."
        ),
    ),
    InvariantDefinition(
        code="PAYLOAD_REJECTS_DOMAIN_LABELS",
        category=InvariantCategory.CORE_PAYLOAD,
        severity=InvariantSeverity.CRITICAL,
        source_ref="MEMORY_CONTRACT.md §3 + WORLD_INGRESS.md §6",
        statement=(
            "PayloadSeed rejects domain tickers / market labels as payload "
            "values (no symbol- or venue-specific tokens as payloads)."
        ),
    ),
    InvariantDefinition(
        code="NEURAL_SEED_PAYLOADS_UNIQUE",
        category=InvariantCategory.CORE_PAYLOAD,
        severity=InvariantSeverity.HIGH,
        source_ref="INGRESS_COMPILER_SPEC.md §7",
        statement=(
            "A NeuralSeed's payload mix contains no duplicate primer "
            "payloads; each primer color appears at most once."
        ),
    ),
    InvariantDefinition(
        code="NEURAL_SEED_TOTAL_INTENSITY_COMPUTED",
        category=InvariantCategory.CORE_PAYLOAD,
        severity=InvariantSeverity.HIGH,
        source_ref="INGRESS_COMPILER_SPEC.md §7",
        statement=(
            "NeuralSeed.total_intensity is a computed field equal to the "
            "sum of payload intensities; it is never an input."
        ),
    ),
    # ---- INGRESS_BOUNDARY --------------------------------------------------
    InvariantDefinition(
        code="INGRESS_EVENT_TYPE_FIXED",
        category=InvariantCategory.INGRESS_BOUNDARY,
        severity=InvariantSeverity.CRITICAL,
        source_ref="WORLD_INGRESS.md §4 + INGRESS_COMPILER_SPEC.md §3",
        statement=(
            "Each ingress envelope has a Literal event_type discriminator "
            "fixed by class; arbitrary event_type strings are rejected."
        ),
    ),
    InvariantDefinition(
        code="INGRESS_REJECTS_DOMAIN_RAW_FIELDS",
        category=InvariantCategory.INGRESS_BOUNDARY,
        severity=InvariantSeverity.CRITICAL,
        source_ref="WORLD_INGRESS.md §6",
        statement=(
            "Ingress envelopes reject domain-specific raw fields "
            "(symbol / market / venue / price). Provenance lives only "
            "in opaque references."
        ),
    ),
    InvariantDefinition(
        code="HUMAN_INTENT_RAW_TEXT_FORBIDDEN",
        category=InvariantCategory.INGRESS_BOUNDARY,
        severity=InvariantSeverity.HIGH,
        source_ref="WORLD_INGRESS.md §9",
        statement=(
            "HumanIntentEvent carries a normalized intent shape; raw "
            "natural-language text fields are not part of the envelope."
        ),
    ),
    InvariantDefinition(
        code="RECALL_SUBJECT_CLASS_CANONICAL",
        category=InvariantCategory.INGRESS_BOUNDARY,
        severity=InvariantSeverity.HIGH,
        source_ref="RECALL_PROTOCOL.md §5 + MEMORY_CONTRACT.md §3",
        statement=(
            "RecallEvent.subject_class is bound to the canonical "
            "memory SubjectClass taxonomy; free-form strings are rejected."
        ),
    ),
    # ---- OBSERVER_LEDGER ---------------------------------------------------
    InvariantDefinition(
        code="OBSERVER_EVENT_FAMILY_CLOSED",
        category=InvariantCategory.OBSERVER_LEDGER,
        severity=InvariantSeverity.HIGH,
        source_ref="OBSERVER_LEDGER.md §3",
        statement=(
            "ObserverEvent.event_family is one of the 8 canonical families; "
            "unknown families are rejected."
        ),
    ),
    # ---- MEMORY_BOUNDARY ---------------------------------------------------
    InvariantDefinition(
        code="MEMORY_SUBJECT_CLASS_CLOSED",
        category=InvariantCategory.MEMORY_BOUNDARY,
        severity=InvariantSeverity.CRITICAL,
        source_ref="MEMORY_CONTRACT.md §3 + RECALL_PROTOCOL.md §5",
        statement=(
            "MemoryRecord.subject_class is one of the 16 canonical subject "
            "classes; free-form strings are rejected."
        ),
    ),
    InvariantDefinition(
        code="FOREIGN_INSTANCE_ORIGIN_NOT_SUBJECT_CLASS",
        category=InvariantCategory.MEMORY_BOUNDARY,
        severity=InvariantSeverity.CRITICAL,
        source_ref="MEMORY_CONTRACT.md §3 + Patch P §5",
        statement=(
            "`foreign_instance_origin` is NOT a SubjectClass. MVP excludes "
            "cross-instance / fork / migration memory subjects."
        ),
    ),
    InvariantDefinition(
        code="MEMORY_RECORD_STATUS_CLOSED",
        category=InvariantCategory.MEMORY_BOUNDARY,
        severity=InvariantSeverity.HIGH,
        source_ref="MEMORY_CONTRACT.md §6",
        statement=(
            "MemoryRecord.status is one of the canonical statuses; "
            "unknown statuses are rejected at the type boundary."
        ),
    ),
    # ---- NUMERICS_GOVERNANCE ----------------------------------------------
    InvariantDefinition(
        code="NUMERIC_ENTRY_NO_DEFAULT_FIELDS",
        category=InvariantCategory.NUMERICS_GOVERNANCE,
        severity=InvariantSeverity.CRITICAL,
        source_ref="NUMERICS_GOVERNANCE.md §9",
        statement=(
            "NumericEntry exposes no implicit defaults; every field must "
            "be supplied at construction time (M §9 no-default rule)."
        ),
    ),
    InvariantDefinition(
        code="NUMERIC_IMMUTABLE_SINGLE_RANGE_FORBIDDEN_BOTH_DIRECTIONS",
        category=InvariantCategory.NUMERICS_GOVERNANCE,
        severity=InvariantSeverity.CRITICAL,
        source_ref="NUMERICS_GOVERNANCE.md §10",
        statement=(
            "AllowedRangeSingle requires both change_class_if_increased "
            "and change_class_if_decreased == FORBIDDEN; conversely, "
            "both-FORBIDDEN requires AllowedRangeSingle (constitutional "
            "immutable invariant)."
        ),
    ),
    InvariantDefinition(
        code="NUMERICS_ARTIFACT_ENTRY_KEYS_UNIQUE",
        category=InvariantCategory.NUMERICS_GOVERNANCE,
        severity=InvariantSeverity.HIGH,
        source_ref="NUMERICS_GOVERNANCE.md §8",
        statement=(
            "Within a NumericsArtifact, entry keys are unique and every "
            "entry's spec_family equals the artifact's spec_family."
        ),
    ),
    # ---- ADAPTER_BOUNDARY --------------------------------------------------
    InvariantDefinition(
        code="ADAPTER_CANNOT_OUTPUT_NEURAL_SEED",
        category=InvariantCategory.ADAPTER_BOUNDARY,
        severity=InvariantSeverity.CRITICAL,
        source_ref="ADAPTER_MANIFEST_SPEC.md §7",
        statement=(
            "No adapter output channel may emit a NeuralSeed. Only the "
            "core / cortex produces NeuralSeed."
        ),
    ),
    InvariantDefinition(
        code="ADAPTER_CAPABILITY_INCOMPATIBILITY_ENFORCED",
        category=InvariantCategory.ADAPTER_BOUNDARY,
        severity=InvariantSeverity.CRITICAL,
        source_ref="ADAPTER_MANIFEST_SPEC.md §8",
        statement=(
            "An AdapterManifest cannot declare any of the constitutional "
            "incompatible capability pairs (execute+intent_relay, "
            "execute+recall_provider, execute+memory_writer, "
            "recall_provider+memory_writer, intent_relay+memory_writer, "
            "intent_relay+recall_provider)."
        ),
    ),
    InvariantDefinition(
        code="ADAPTER_EXECUTE_REQUIRES_OBSERVE",
        category=InvariantCategory.ADAPTER_BOUNDARY,
        severity=InvariantSeverity.HIGH,
        source_ref="ADAPTER_MANIFEST_SPEC.md §8",
        statement=(
            "An AdapterManifest declaring `execute` must also declare "
            "`observe` (efference / feedback pair)."
        ),
    ),
    # ---- WORKSPACE --------------------------------------------------------
    InvariantDefinition(
        code="WORKSPACE_SINGLE_PULSE_EVENT_TYPE",
        category=InvariantCategory.WORKSPACE,
        severity=InvariantSeverity.CRITICAL,
        source_ref="BOOTSTRAP_GENOME.md §B (attention workspace)",
        statement=(
            "There is exactly one workspace pulse event type, "
            "WORKSPACE_PULSE; other event_type values are rejected."
        ),
    ),
    InvariantDefinition(
        code="WORKSPACE_NO_PULSE_CATEGORY",
        category=InvariantCategory.WORKSPACE,
        severity=InvariantSeverity.CRITICAL,
        source_ref="BOOTSTRAP_GENOME.md §B (attention workspace)",
        statement=(
            "There is no pulse type / pulse_category / focus_type / "
            "semantic_label / domain_label on a pulse. The pulse "
            "signature lives in dominant_payload_mix."
        ),
    ),
    # ---- MVP_RUNTIME ------------------------------------------------------
    InvariantDefinition(
        code="MVP_FORBIDS_LIVE_EXCHANGE_IMPORTS",
        category=InvariantCategory.MVP_RUNTIME,
        severity=InvariantSeverity.CRITICAL,
        source_ref="docs/build/0001-minimum-viable-brain-plan.md",
        statement=(
            "MVP forbids live exchange / market integrations (ccxt, "
            "web3, binance, btcturk) anywhere in the import graph."
        ),
    ),
    InvariantDefinition(
        code="MVP_FORBIDS_LLM_IMPORTS",
        category=InvariantCategory.MVP_RUNTIME,
        severity=InvariantSeverity.CRITICAL,
        source_ref="docs/build/0001-minimum-viable-brain-plan.md",
        statement=(
            "MVP forbids LLM SDK imports (openai, anthropic, langchain) "
            "anywhere in the import graph."
        ),
    ),
    InvariantDefinition(
        code="MVP_FORBIDS_EXECUTION_OUTPUTS",
        category=InvariantCategory.MVP_RUNTIME,
        severity=InvariantSeverity.CRITICAL,
        source_ref="docs/build/0001-minimum-viable-brain-plan.md",
        statement=(
            "MVP output set is restricted; live-execution literals "
            "(action verbs such as the buy / sell / execute_real / "
            "order_submit family) must not appear as system outputs."
        ),
    ),
    # ---- Phase 3-10 runtime-raised invariants (catalog companion to
    # the violation codes raised by the runtime modules). The
    # canonical statement for each is the runtime ViolationContext;
    # this catalog row exists so listing / get_invariant covers them.
    # ---- NUMERICS_GOVERNANCE (loader + dependency validator) ----------
    InvariantDefinition(
        code="NUMERICS_DEV_ONLY_REJECTED_IN_PRODUCTION",
        category=InvariantCategory.NUMERICS_GOVERNANCE,
        severity=InvariantSeverity.CRITICAL,
        source_ref="NUMERICS_GOVERNANCE.md §8 + build plan §8",
        statement=(
            "A `dev_only=True` numerics artifact is rejected by the loader in PRODUCTION mode."
        ),
    ),
    InvariantDefinition(
        code="NUMERICS_DEPENDENCY_UNKNOWN_KEY",
        category=InvariantCategory.NUMERICS_GOVERNANCE,
        severity=InvariantSeverity.HIGH,
        source_ref="NUMERICS_GOVERNANCE.md §12",
        statement=(
            "Every NumericDependency.target_key must reference another "
            "entry in the same artifact; unknown keys are rejected."
        ),
    ),
    InvariantDefinition(
        code="NUMERICS_DEPENDENCY_CYCLE_DETECTED",
        category=InvariantCategory.NUMERICS_GOVERNANCE,
        severity=InvariantSeverity.HIGH,
        source_ref="NUMERICS_GOVERNANCE.md §12",
        statement=(
            "The directed graph of cross-key dependencies within a "
            "NumericsArtifact must be acyclic; cycles (self-loops "
            "included) are rejected."
        ),
    ),
    # ---- INGRESS_BOUNDARY (profile cap input guard) -------------------
    InvariantDefinition(
        code="INGRESS_PROFILE_CAP_INPUT_INVALID",
        category=InvariantCategory.INGRESS_BOUNDARY,
        severity=InvariantSeverity.HIGH,
        source_ref="INGRESS_COMPILER_NUMERICS.md §7",
        statement=(
            "`apply_profile_cap(profile, intensity)` rejects intensity "
            "outside [0.0, 1.0] (raises NumericsGovernanceViolation)."
        ),
    ),
    # ---- OBSERVER_LEDGER (catalog + permanence + ring + LLM scope) ----
    InvariantDefinition(
        code="OBSERVER_EVENT_TYPE_UNKNOWN",
        category=InvariantCategory.OBSERVER_LEDGER,
        severity=InvariantSeverity.HIGH,
        source_ref="OBSERVER_LEDGER_SCHEMA.md §19",
        statement=(
            "An ObserverEvent whose event_type is not in the canonical "
            "catalog is rejected at the writer boundary."
        ),
    ),
    InvariantDefinition(
        code="OBSERVER_EVENT_FAMILY_MATCHES_CATALOG",
        category=InvariantCategory.OBSERVER_LEDGER,
        severity=InvariantSeverity.HIGH,
        source_ref="OBSERVER_LEDGER_SCHEMA.md §19",
        statement=(
            "An ObserverEvent's event_family must match the canonical "
            "catalog row for its event_type; mismatches are rejected."
        ),
    ),
    InvariantDefinition(
        code="OBSERVER_PERMANENCE_DOWNGRADE_FORBIDDEN",
        category=InvariantCategory.OBSERVER_LEDGER,
        severity=InvariantSeverity.CRITICAL,
        source_ref="OBSERVER_LEDGER_NUMERICS.md §10-12",
        statement=(
            "Permanence policy is monotonic; storage pressure cannot "
            "downgrade an event_type's permanence (e.g. permanent ->"
            " ring_buffer_only is forbidden)."
        ),
    ),
    InvariantDefinition(
        code="OBSERVER_RING_BUFFER_POLICY_MISMATCH",
        category=InvariantCategory.OBSERVER_LEDGER,
        severity=InvariantSeverity.HIGH,
        source_ref="OBSERVER_LEDGER_SCHEMA.md §10",
        statement=(
            "Pushing an event whose catalog permanence does not include "
            "ring-buffer participation into the in-memory ring is "
            "rejected."
        ),
    ),
    InvariantDefinition(
        code="OBSERVER_LLM_READ_SCOPE_FORBIDDEN",
        category=InvariantCategory.OBSERVER_LEDGER,
        severity=InvariantSeverity.CRITICAL,
        source_ref="OBSERVER_LEDGER_NUMERICS.md §12-15",
        statement=(
            "An LLM reader explicitly requesting an event_type outside "
            "the LLM_ALLOWED_READ_EVENT_TYPES whitelist is rejected; "
            "no events are returned and no audit is emitted on the "
            "failed call."
        ),
    ),
    # ---- ADAPTER_BOUNDARY (trust + neural-seed red line) --------------
    InvariantDefinition(
        code="ADAPTER_NEURAL_SEED_EMISSION_DETECTED",
        category=InvariantCategory.ADAPTER_BOUNDARY,
        severity=InvariantSeverity.CRITICAL,
        source_ref="ADAPTER_MANIFEST_SPEC.md §7; ADAPTER_TRUST_NUMERICS.md §6",
        statement=(
            "An adapter with neural_seed_emission_count > 0 (or one "
            "attempting direct NeuralSeed emission) is irrevocably "
            "revoked; AdapterTrustRecord rejects this at construction."
        ),
    ),
    InvariantDefinition(
        code="ADAPTER_TRUST_HARD_GATES_REQUIRED",
        category=InvariantCategory.ADAPTER_BOUNDARY,
        severity=InvariantSeverity.CRITICAL,
        source_ref="ADAPTER_TRUST_NUMERICS.md §6",
        statement=(
            "Adapter trust hard gates (signature_validity = True, "
            "manifest_hash_integrity = True, "
            "neural_seed_emission_count == 0) must all pass; any "
            "failure forces composite trust score = 0.0 and band = "
            "REVOKED."
        ),
    ),
    # ---- INGRESS_BOUNDARY (recall protocol invariants) ----------------
    InvariantDefinition(
        code="RECALL_TOP_ONE_INVARIANT",
        category=InvariantCategory.INGRESS_BOUNDARY,
        severity=InvariantSeverity.CRITICAL,
        source_ref="RECALL_PROTOCOL.md §5 + §8",
        statement=(
            "At the core boundary, at most one recall result is "
            "emitted per trigger; multi-result APIs are forbidden."
        ),
    ),
    InvariantDefinition(
        code="RECALL_CORE_TRIGGER_SOURCE_ONLY",
        category=InvariantCategory.INGRESS_BOUNDARY,
        severity=InvariantSeverity.CRITICAL,
        source_ref="RECALL_PROTOCOL.md §19",
        statement=(
            "Only `RecallTriggerSource.CORE` may trigger recall in MVP; "
            "human-direct, LLM, replay, summarizer sources are rejected."
        ),
    ),
    InvariantDefinition(
        code="RECALL_CANDIDATE_SUBJECT_CLASS_FORBIDDEN",
        category=InvariantCategory.INGRESS_BOUNDARY,
        severity=InvariantSeverity.HIGH,
        source_ref="RECALL_PROTOCOL.md §14",
        statement=(
            "A candidate recall is only permitted for subject classes "
            "in {SOURCE_TRUST, PROCEDURAL}; any other subject is "
            "rejected at the protocol boundary."
        ),
    ),
    # ---- MEMORY_BOUNDARY (Memory Write Gate) --------------------------
    InvariantDefinition(
        code="MEMORY_WRITE_GATE_SILENT",
        category=InvariantCategory.MEMORY_BOUNDARY,
        severity=InvariantSeverity.CRITICAL,
        source_ref="MEMORY_WRITE_GATE.md §4",
        statement=(
            "The Memory Write Gate is silent toward the core. The only "
            "core-observable signal of a memory write is the audit "
            "event MEMORY_RECORD_STATUS_CHANGED; the gate returns no "
            "direct signal to the core."
        ),
    ),
    InvariantDefinition(
        code="MEMORY_WRITE_GATE_CANDIDATE_ONLY_IN_MVP",
        category=InvariantCategory.MEMORY_BOUNDARY,
        severity=InvariantSeverity.CRITICAL,
        source_ref="MEMORY_WRITE_GATE.md §8 + build plan §12",
        statement=(
            "While mvp_verified_disabled is True, any VERIFIED-status "
            "write request is downgraded to CANDIDATE; the verified "
            "path is unreachable in MVP."
        ),
    ),
    # ---- WORKSPACE (pulse-coupling guard) -----------------------------
    InvariantDefinition(
        code="WORKSPACE_PULSE_NO_ACTION_COUPLING",
        category=InvariantCategory.WORKSPACE,
        severity=InvariantSeverity.CRITICAL,
        source_ref="BOOTSTRAP_GENOME.md §B; build plan §11",
        statement=(
            "Pulse alone cannot trigger action. The pulse emitter "
            "references no execution / intent constructs; the deontic "
            "gate is the sole action authorizer."
        ),
    ),
    # ---- MVP_RUNTIME (feature flag + output set + dry sim) ------------
    InvariantDefinition(
        code="MVP_FEATURE_FLAG_MATRIX_IMMUTABLE",
        category=InvariantCategory.MVP_RUNTIME,
        severity=InvariantSeverity.HIGH,
        source_ref="build plan §18",
        statement=(
            "The MVP_FEATURE_FLAGS mapping is read-only at runtime; no "
            "code path may override a flag value mid-process. Reads "
            "must go through `get_flag(name)` which raises on unknown "
            "names."
        ),
    ),
    InvariantDefinition(
        code="MVP_OUTPUT_SET_CLOSED",
        category=InvariantCategory.MVP_RUNTIME,
        severity=InvariantSeverity.CRITICAL,
        source_ref="build plan §15",
        statement=(
            "SystemOutput is the closed 5-value set {WAIT, BLOCK, MONITOR, NEED_RECALL, NO_ACTION}."
        ),
    ),
    # ---- M0 birth-time invariants ------------------------------------
    InvariantDefinition(
        code="M0_NEURON_NO_SPECIALIST_AT_BIRTH",
        category=InvariantCategory.CORE_PAYLOAD,
        severity=InvariantSeverity.CRITICAL,
        source_ref="BOOTSTRAP_GENOME_NUMERICS.md §6; agi-core S §8",
        statement=(
            "Every M0 neuron's receptor sensitivities lie in "
            "[1.0 - epsilon, 1.0 + epsilon] for a small epsilon; the "
            "max-min span <= 2*epsilon guarantees no specialist "
            "neuron exists at birth."
        ),
    ),
    InvariantDefinition(
        code="M0_SYNAPSE_WEIGHT_BELOW_STABLE_THRESHOLD",
        category=InvariantCategory.CORE_PAYLOAD,
        severity=InvariantSeverity.CRITICAL,
        source_ref="agi-core S §7",
        statement=(
            "Every M0 synapse's initial weight is in the weak band "
            "and strictly below STABLE_PATH_THRESHOLD; charge "
            "propagation is read-only (learning OFF in MVP)."
        ),
    ),
    InvariantDefinition(
        code="M0_SELF_FIELD_STRICT_HIERARCHY",
        category=InvariantCategory.CORE_PAYLOAD,
        severity=InvariantSeverity.CRITICAL,
        source_ref="agi-core S §11",
        statement=(
            "Embryo self-field weights satisfy "
            "homeostatic_weight > predictive_weight > narrative_weight."
        ),
    ),
    InvariantDefinition(
        code="M0_PROTO_RESONANCE_5_LAYER_BIRTH",
        category=InvariantCategory.CORE_PAYLOAD,
        severity=InvariantSeverity.CRITICAL,
        source_ref="agi-core S §9",
        statement=(
            "At MVP birth every proto-resonance pattern satisfies: "
            "recallability == 0, assembly_id_at_birth is None, "
            "persistence_max_ms < STABLE_ASSEMBLY_MIN_PERSISTENCE_MS, "
            "stability_score_cap < ASSEMBLY_STABILIZATION_THRESHOLD, "
            "memory_write_eligibility is False."
        ),
    ),
    InvariantDefinition(
        code="M0_TISSUE_UNIFORM_BIRTH_ALLOCATION",
        category=InvariantCategory.CORE_PAYLOAD,
        severity=InvariantSeverity.CRITICAL,
        source_ref="BOOTSTRAP_GENOME_NUMERICS.md §8",
        statement=(
            "Tissue birth allocates global_seed_count uniformly across "
            "all 10 primer payloads; per-payload divergence == 0."
        ),
    ),
)


_BY_CODE: dict[str, InvariantDefinition] = {inv.code: inv for inv in MVP_REQUIRED_INVARIANTS}


def list_invariants(
    category: InvariantCategory | None = None,
    *,
    mvp_required: bool | None = None,
) -> tuple[InvariantDefinition, ...]:
    """Return catalog rows, optionally filtered by category / MVP flag."""
    rows: tuple[InvariantDefinition, ...] = MVP_REQUIRED_INVARIANTS
    if category is not None:
        rows = tuple(inv for inv in rows if inv.category is category)
    if mvp_required is not None:
        rows = tuple(inv for inv in rows if inv.mvp_required is mvp_required)
    return rows


def get_invariant(code: str) -> InvariantDefinition:
    """Look up a catalog row by code. Raises `KeyError` if unknown."""
    return _BY_CODE[code]


def assert_invariant(
    condition: bool,
    code: str,
    *,
    evidence: Mapping[str, object] | None = None,
) -> None:
    """Raise `InvariantViolation` if `condition` is falsy.

    The raised exception carries a `ViolationContext` bound to the
    catalog entry's `code` and `source_ref`, with the caller-supplied
    `evidence` (defensively copied + made read-only by
    `ViolationContext.__post_init__`).
    """
    if condition:
        return
    invariant = get_invariant(code)
    raise InvariantViolation(
        invariant.statement,
        ViolationContext(
            violation_code=code,
            source_ref=invariant.source_ref,
            evidence=evidence if evidence is not None else {},
        ),
    )
