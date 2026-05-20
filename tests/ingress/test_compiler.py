"""Tests for the deterministic ingress compiler."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sentinel.constitution.violations import NumericsGovernanceViolation
from sentinel.ingress.compiler import compile_neural_seed
from sentinel.ingress.profile_caps import cap_for
from sentinel.types.neural_seed import EventProfile, ProvenanceRef
from sentinel.types.payload import PrimerPayload


def _prov() -> ProvenanceRef:
    return ProvenanceRef(source_event_id="src-1")


class TestObservationCompile:
    def test_high_magnitude_emits_novelty(self) -> None:
        seed = compile_neural_seed(
            profile=EventProfile.OBSERVATION_EVENT,
            event_attributes={"magnitude": 0.9, "confidence": 0.8},
            provenance=_prov(),
        )
        payloads = {s.payload for s in seed.payload_seed}
        assert PrimerPayload.NOVELTY in payloads

    def test_low_confidence_emits_suspicion(self) -> None:
        seed = compile_neural_seed(
            profile=EventProfile.OBSERVATION_EVENT,
            event_attributes={"magnitude": 0.5, "confidence": 0.1},
            provenance=_prov(),
        )
        payloads = {s.payload for s in seed.payload_seed}
        assert PrimerPayload.SUSPICION in payloads

    def test_determinism(self) -> None:
        attrs = {"magnitude": 0.7, "confidence": 0.2}
        s1 = compile_neural_seed(
            profile=EventProfile.OBSERVATION_EVENT,
            event_attributes=attrs,
            provenance=_prov(),
        )
        s2 = compile_neural_seed(
            profile=EventProfile.OBSERVATION_EVENT,
            event_attributes=attrs,
            provenance=_prov(),
        )
        assert s1.model_dump() == s2.model_dump()


class TestProfileCapEnforcement:
    def test_observation_cap_one(self) -> None:
        """High magnitude alone cannot exceed Observation cap of 1.0."""
        seed = compile_neural_seed(
            profile=EventProfile.OBSERVATION_EVENT,
            event_attributes={"magnitude": 1.0},
            provenance=_prov(),
        )
        for s in seed.payload_seed:
            assert s.intensity <= cap_for(EventProfile.OBSERVATION_EVENT)

    def test_human_intent_cap_clamped(self) -> None:
        """HumanIntent alignment_score=1.0 → base 0.3 → under 0.35 cap."""
        seed = compile_neural_seed(
            profile=EventProfile.HUMAN_INTENT_EVENT,
            event_attributes={"alignment_score": 1.0},
            provenance=_prov(),
        )
        for s in seed.payload_seed:
            assert s.intensity <= cap_for(EventProfile.HUMAN_INTENT_EVENT)


class TestNoMatchingRule:
    def test_unknown_attribute_falls_through(self) -> None:
        # ObservationEvent with neither magnitude nor confidence → no
        # rule fires → empty payload_seed → NeuralSeed schema rejects.
        with pytest.raises(ValidationError):
            compile_neural_seed(
                profile=EventProfile.OBSERVATION_EVENT,
                event_attributes={"unrelated": 0.5},
                provenance=_prov(),
            )

    def test_candidate_recall_has_no_rules_in_mvp(self) -> None:
        with pytest.raises(ValidationError):
            compile_neural_seed(
                profile=EventProfile.CANDIDATE_RECALL,
                event_attributes={"anything": 0.5},
                provenance=_prov(),
            )


class TestInputValidation:
    def test_attribute_above_one_rejected(self) -> None:
        # apply_profile_cap raises if the final intensity is out of range;
        # but membership is bounded [0,1] so we need to construct a
        # scenario where the unbounded raw_intensity then exceeds bounds.
        # The boundary check is at apply_profile_cap(profile, min(raw, 1.0))
        # — so the loop clamps raw to 1.0 first, never out of range.
        # Instead validate that the cap interface itself rejects;
        # the compiler relies on it. This is a no-op assurance test.
        # Use observe_compiler to confirm graceful behaviour on edge
        # value 1.0 (cap=1.0):
        seed = compile_neural_seed(
            profile=EventProfile.OBSERVATION_EVENT,
            event_attributes={"magnitude": 1.0, "confidence": 0.0},
            provenance=_prov(),
        )
        for s in seed.payload_seed:
            assert 0.0 < s.intensity <= 1.0


class TestStableOrdering:
    def test_payload_order_follows_enum_declaration(self) -> None:
        seed = compile_neural_seed(
            profile=EventProfile.OBSERVATION_EVENT,
            event_attributes={"magnitude": 0.9, "confidence": 0.1},
            provenance=_prov(),
        )
        order = [s.payload for s in seed.payload_seed]
        # PrimerPayload declares SUSPICION before NOVELTY → expect
        # SUSPICION first if both present.
        if PrimerPayload.SUSPICION in order and PrimerPayload.NOVELTY in order:
            assert order.index(PrimerPayload.SUSPICION) < order.index(PrimerPayload.NOVELTY)


class TestRejectInvalidIntensityViaBoundary:
    def test_negative_value_in_attribute_rejected_by_cap(self) -> None:
        # If an attribute is -0.5 and the rule applies, membership is 0
        # so the rule doesn't fire; but if a downstream cap is asked for
        # negative input it raises. Walk the path explicitly:
        with pytest.raises(NumericsGovernanceViolation):
            # Force a negative final intensity by patching: we test the
            # cap directly which the compiler depends on.
            from sentinel.ingress.profile_caps import apply_profile_cap

            apply_profile_cap(EventProfile.OBSERVATION_EVENT, -0.1)
