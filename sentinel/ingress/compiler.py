"""Deterministic ingress compiler.

Per INGRESS_COMPILER_SPEC.md §3-9 and the Phase 4 build plan: the
compiler converts an (event_profile, event_attributes, provenance)
triple into a fully-bound `NeuralSeed` by:

    1. Filtering the bootstrap rule registry to rules whose
       `applies_to_profile` matches the event profile
    2. For each matching rule, computing
       `membership(rule.stimulus_band, event_attributes[rule.stimulus_attribute])`
       and multiplying by `rule.base_intensity` to get a per-rule
       contribution
    3. Summing contributions per primer payload (weighted blend, no
       forced normalization per N §9)
    4. Applying the profile cap (N §7) to EACH resulting per-payload
       intensity
    5. Dropping any payload whose final intensity is exactly 0.0
    6. Returning a `NeuralSeed` with the surviving `(payload, intensity)`
       pairs

Constitutional discipline:
    - Deterministic: same inputs → same NeuralSeed bytes
    - No domain labels, no semantic interpretation, no LLM
    - Missing `stimulus_attribute` is silently treated as "no
      contribution from this rule" (the rule simply doesn't fire)
    - `event_attributes` values outside [0.0, 1.0] are REJECTED at the
      boundary (raises NumericsGovernanceViolation via
      `apply_profile_cap`)
    - Adapters CANNOT call this compiler directly with a hand-crafted
      `(profile, attributes)` to forge a NeuralSeed — that path is
      blocked at the adapter trust layer (Phase 9). This module is
      the engine; trust is the gatekeeper.

What this module deliberately does NOT contain:
    - Forced normalization (N §9: weighted blend + cap, no rescale)
    - Cross-payload coupling
    - Learning / rule discovery
    - Adapter-side validation (Phase 9 concern)
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping  # noqa: TC003 (runtime annotations)

from sentinel.ingress.profile_caps import apply_profile_cap
from sentinel.ingress.rules import MVP_BOOTSTRAP_RULES, BootstrapRule
from sentinel.ingress.soft_overlap import membership
from sentinel.types.neural_seed import EventProfile, NeuralSeed, ProvenanceRef
from sentinel.types.payload import PayloadSeed, PrimerPayload


def compile_neural_seed(
    *,
    profile: EventProfile,
    event_attributes: Mapping[str, float],
    provenance: ProvenanceRef,
    rules: Iterable[BootstrapRule] = MVP_BOOTSTRAP_RULES,
) -> NeuralSeed:
    """Compile an ingress event into a NeuralSeed.

    Raises:
        NumericsGovernanceViolation if any attribute value is outside
        [0.0, 1.0] (via apply_profile_cap on the final per-payload
        intensity; rule membership inputs are also bounded checks).
        ValidationError (Pydantic) if no rule fires and the resulting
        NeuralSeed would have an empty payload_seed — caller is
        responsible for providing event_attributes that match at
        least one rule for the profile.
    """
    per_payload: dict[PrimerPayload, float] = {}

    for rule in rules:
        if rule.applies_to_profile is not profile:
            continue
        if rule.stimulus_attribute not in event_attributes:
            continue
        value = event_attributes[rule.stimulus_attribute]
        m = membership(rule.stimulus_band, value)
        if m == 0.0:
            continue
        contribution = m * rule.base_intensity
        per_payload[rule.payload] = per_payload.get(rule.payload, 0.0) + contribution

    seeds: list[PayloadSeed] = []
    for payload, raw_intensity in per_payload.items():
        capped = apply_profile_cap(profile, min(raw_intensity, 1.0))
        if capped > 0.0:
            seeds.append(PayloadSeed(payload=payload, intensity=capped))

    # Stable order by enum declaration order so equality across runs is
    # deterministic regardless of dict insertion order.
    seeds.sort(key=lambda s: list(PrimerPayload).index(s.payload))

    return NeuralSeed(
        event_profile=profile,
        payload_seed=tuple(seeds),
        provenance=provenance,
    )
