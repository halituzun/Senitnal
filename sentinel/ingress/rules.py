"""Bootstrap ingress rule schema + minimal MVP registry.

Per WORLD_INGRESS.md §D-19 and the Phase 4 build plan: each
bootstrap rule maps a (profile, stimulus_attribute, stimulus_band)
triple to one (primer payload, base_intensity) emission. The
compiler aggregates contributions across all matching rules and
applies the profile cap.

Constitutional discipline (MVP):
    - Learned rule count is 0 (S §20). The MVP set is a closed,
      version-pinned bootstrap registry; new rules require spec
      revision
    - Deterministic: no LLM, no semantic interpretation. The
      compiler asks `membership(rule.stimulus_band, value)` and
      multiplies by `base_intensity`
    - One payload per rule. Aggregate effects (e.g. two rules both
      contributing to `novelty`) sum at the compiler boundary and
      are then capped by the profile cap

What this module deliberately does NOT contain:
    - Learning / rule discovery
    - Cross-payload coupling
    - Rule conflict resolution beyond simple sum-then-cap
"""

from __future__ import annotations

from dataclasses import dataclass

from sentinel.ingress.soft_overlap import FuzzyBand
from sentinel.types.neural_seed import EventProfile
from sentinel.types.payload import PrimerPayload


@dataclass(frozen=True, slots=True)
class BootstrapRule:
    """One bootstrap mapping rule (rule_id is unique within registry)."""

    rule_id: str
    applies_to_profile: EventProfile
    stimulus_attribute: str
    stimulus_band: FuzzyBand
    payload: PrimerPayload
    base_intensity: float
    source_ref: str

    def __post_init__(self) -> None:
        if self.rule_id == "":
            raise ValueError("BootstrapRule.rule_id must be non-empty")
        if self.stimulus_attribute == "":
            raise ValueError("BootstrapRule.stimulus_attribute must be non-empty")
        if not (0.0 <= self.base_intensity <= 1.0):
            raise ValueError(
                f"BootstrapRule.base_intensity must be in [0.0, 1.0]; got {self.base_intensity}"
            )
        if self.source_ref == "":
            raise ValueError("BootstrapRule.source_ref must be non-empty")


# ---------------------------------------------------------------------------
# MVP bootstrap rule registry (v0.1, closed)
# ---------------------------------------------------------------------------


MVP_BOOTSTRAP_RULES: tuple[BootstrapRule, ...] = (
    BootstrapRule(
        rule_id="novelty_from_high_observation_magnitude",
        applies_to_profile=EventProfile.OBSERVATION_EVENT,
        stimulus_attribute="magnitude",
        stimulus_band=FuzzyBand(low=0.4, peak_low=0.8, peak_high=1.0, high=1.0),
        payload=PrimerPayload.NOVELTY,
        base_intensity=0.6,
        source_ref="WORLD_INGRESS.md §D-19; INGRESS_COMPILER_SPEC.md §7",
    ),
    BootstrapRule(
        rule_id="suspicion_from_low_observation_confidence",
        applies_to_profile=EventProfile.OBSERVATION_EVENT,
        stimulus_attribute="confidence",
        stimulus_band=FuzzyBand(low=0.0, peak_low=0.0, peak_high=0.3, high=0.6),
        payload=PrimerPayload.SUSPICION,
        base_intensity=0.5,
        source_ref="WORLD_INGRESS.md §D-19; INGRESS_COMPILER_SPEC.md §7",
    ),
    BootstrapRule(
        rule_id="urgency_from_high_internal_shock",
        applies_to_profile=EventProfile.INTERNAL_SHOCK_EVENT,
        stimulus_attribute="stimulus_strength",
        stimulus_band=FuzzyBand(low=0.5, peak_low=0.8, peak_high=1.0, high=1.0),
        payload=PrimerPayload.URGENCY,
        base_intensity=0.7,
        source_ref="WORLD_INGRESS.md §10; INGRESS_COMPILER_SPEC.md §7",
    ),
    BootstrapRule(
        rule_id="aversion_from_pain_trace_in_shock",
        applies_to_profile=EventProfile.INTERNAL_SHOCK_EVENT,
        stimulus_attribute="pain_amplitude",
        stimulus_band=FuzzyBand(low=0.3, peak_low=0.7, peak_high=1.0, high=1.0),
        payload=PrimerPayload.AVERSION,
        base_intensity=0.6,
        source_ref="INGRESS_COMPILER_SPEC.md §7",
    ),
    BootstrapRule(
        rule_id="attraction_from_human_intent_alignment",
        applies_to_profile=EventProfile.HUMAN_INTENT_EVENT,
        stimulus_attribute="alignment_score",
        stimulus_band=FuzzyBand(low=0.3, peak_low=0.7, peak_high=1.0, high=1.0),
        payload=PrimerPayload.ATTRACTION,
        base_intensity=0.3,
        source_ref="WORLD_INGRESS.md §9; INGRESS_COMPILER_SPEC.md §7",
    ),
    BootstrapRule(
        rule_id="memory_echo_from_recall_active",
        applies_to_profile=EventProfile.RECALL_EVENT_ACTIVE,
        stimulus_attribute="recall_strength",
        stimulus_band=FuzzyBand(low=0.2, peak_low=0.5, peak_high=1.0, high=1.0),
        payload=PrimerPayload.MEMORY_ECHO,
        base_intensity=0.5,
        source_ref="RECALL_PROTOCOL.md §5; INGRESS_COMPILER_SPEC.md §7",
    ),
    BootstrapRule(
        rule_id="memory_echo_from_recall_verified",
        applies_to_profile=EventProfile.RECALL_EVENT_VERIFIED,
        stimulus_attribute="recall_strength",
        stimulus_band=FuzzyBand(low=0.2, peak_low=0.5, peak_high=1.0, high=1.0),
        payload=PrimerPayload.MEMORY_ECHO,
        base_intensity=0.45,
        source_ref="RECALL_PROTOCOL.md §5; INGRESS_COMPILER_SPEC.md §7",
    ),
    BootstrapRule(
        rule_id="contradiction_from_internal_shock_dissonance",
        applies_to_profile=EventProfile.INTERNAL_SHOCK_EVENT,
        stimulus_attribute="dissonance",
        stimulus_band=FuzzyBand(low=0.3, peak_low=0.7, peak_high=1.0, high=1.0),
        payload=PrimerPayload.CONTRADICTION,
        base_intensity=0.5,
        source_ref="INGRESS_COMPILER_SPEC.md §7",
    ),
)


_RULE_IDS: set[str] = {r.rule_id for r in MVP_BOOTSTRAP_RULES}
assert len(_RULE_IDS) == len(MVP_BOOTSTRAP_RULES), "MVP_BOOTSTRAP_RULES has duplicate rule_id"
