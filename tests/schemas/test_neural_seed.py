"""Schema tests for NeuralSeed.

Constitutional discipline tested here (schema layer only):
    - 6 canonical EventProfile values
    - payload_seed non-empty
    - Duplicate PrimerPayload rejected
    - total_intensity computed (not input)
    - Provenance required
    - Frozen immutability
    - extra="forbid"
    - Profile cap enforcement deliberately NOT here (compiler layer)
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sentinel.types.neural_seed import EventProfile, NeuralSeed, ProvenanceRef
from sentinel.types.payload import PayloadSeed, PrimerPayload


def _ref() -> ProvenanceRef:
    return ProvenanceRef(source_event_id="evt-0001", source_spec="test")


class TestEventProfile:
    """The closed profile enum is exactly 6 canonical names."""

    def test_six_values(self) -> None:
        assert len(EventProfile) == 6

    def test_canonical_names(self) -> None:
        expected = {
            "ObservationEvent",
            "InternalShockEvent",
            "RecallEvent.active",
            "RecallEvent.verified",
            "HumanIntentEvent",
            "CandidateRecall",
        }
        assert {p.value for p in EventProfile} == expected


class TestProvenanceRef:
    """Provenance ref is required and minimal."""

    def test_required_source_event_id(self) -> None:
        ref = ProvenanceRef(source_event_id="evt-0001")
        assert ref.source_event_id == "evt-0001"
        assert ref.source_spec is None

    def test_extra_field_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ProvenanceRef.model_validate({"source_event_id": "evt-0001", "extra": "nope"})


class TestNeuralSeedValid:
    """Valid NeuralSeed constructions."""

    def test_minimal_construction(self) -> None:
        seed = NeuralSeed(
            event_profile=EventProfile.OBSERVATION_EVENT,
            payload_seed=(PayloadSeed(payload=PrimerPayload.NOVELTY, intensity=0.4),),
            provenance=_ref(),
        )
        assert seed.event_profile == EventProfile.OBSERVATION_EVENT
        assert len(seed.payload_seed) == 1

    def test_total_intensity_computed(self) -> None:
        seed = NeuralSeed(
            event_profile=EventProfile.OBSERVATION_EVENT,
            payload_seed=(
                PayloadSeed(payload=PrimerPayload.NOVELTY, intensity=0.4),
                PayloadSeed(payload=PrimerPayload.URGENCY, intensity=0.3),
                PayloadSeed(payload=PrimerPayload.SUSPICION, intensity=0.2),
            ),
            provenance=_ref(),
        )
        assert seed.total_intensity == pytest.approx(0.9)

    def test_candidate_recall_profile_accepted(self) -> None:
        """CandidateRecall is a valid event_profile at the schema layer.

        (Its intensity cap is enforced by the ingress compiler, not here.)
        """
        seed = NeuralSeed(
            event_profile=EventProfile.CANDIDATE_RECALL,
            payload_seed=(PayloadSeed(payload=PrimerPayload.MEMORY_ECHO, intensity=0.1),),
            provenance=_ref(),
        )
        assert seed.event_profile == EventProfile.CANDIDATE_RECALL

    def test_no_profile_cap_at_schema_layer(self) -> None:
        """Schema layer does NOT enforce N profile caps.

        A HumanIntent NeuralSeed with total_intensity = 1.0 is type-valid
        here (cap = ~0.35 lives in N + compiler). This test pins that
        boundary: schema admits; compiler enforces.
        """
        seed = NeuralSeed(
            event_profile=EventProfile.HUMAN_INTENT_EVENT,
            payload_seed=(PayloadSeed(payload=PrimerPayload.URGENCY, intensity=1.0),),
            provenance=_ref(),
        )
        # would exceed conceptual HumanIntent cap (~0.35) but compiler
        # is the one that caps; schema allows.
        assert seed.total_intensity == pytest.approx(1.0)


class TestNeuralSeedInvalid:
    """Invalid NeuralSeed constructions must raise ValidationError."""

    def test_empty_payload_seed_rejected(self) -> None:
        with pytest.raises(ValidationError):
            NeuralSeed(
                event_profile=EventProfile.OBSERVATION_EVENT,
                payload_seed=(),
                provenance=_ref(),
            )

    def test_duplicate_primer_payload_rejected(self) -> None:
        with pytest.raises(ValidationError):
            NeuralSeed(
                event_profile=EventProfile.OBSERVATION_EVENT,
                payload_seed=(
                    PayloadSeed(payload=PrimerPayload.NOVELTY, intensity=0.3),
                    PayloadSeed(payload=PrimerPayload.NOVELTY, intensity=0.4),
                ),
                provenance=_ref(),
            )

    def test_provenance_missing_rejected(self) -> None:
        with pytest.raises(ValidationError):
            NeuralSeed.model_validate(
                {
                    "event_profile": "ObservationEvent",
                    "payload_seed": [
                        {"payload": "novelty", "intensity": 0.3},
                    ],
                }
            )

    def test_invalid_event_profile_rejected(self) -> None:
        with pytest.raises(ValidationError):
            NeuralSeed.model_validate(
                {
                    "event_profile": "BuyOrder",
                    "payload_seed": [
                        {"payload": "novelty", "intensity": 0.3},
                    ],
                    "provenance": {"source_event_id": "evt-0001"},
                }
            )

    def test_extra_field_rejected(self) -> None:
        with pytest.raises(ValidationError):
            NeuralSeed.model_validate(
                {
                    "event_profile": "ObservationEvent",
                    "payload_seed": [
                        {"payload": "novelty", "intensity": 0.3},
                    ],
                    "provenance": {"source_event_id": "evt-0001"},
                    "extra_field": "nope",
                }
            )

    def test_total_intensity_as_input_rejected(self) -> None:
        """total_intensity is a computed property; cannot be supplied."""
        with pytest.raises(ValidationError):
            NeuralSeed.model_validate(
                {
                    "event_profile": "ObservationEvent",
                    "payload_seed": [
                        {"payload": "novelty", "intensity": 0.3},
                    ],
                    "provenance": {"source_event_id": "evt-0001"},
                    "total_intensity": 0.9,
                }
            )


class TestNeuralSeedImmutable:
    """frozen=True forbids mutation after construction."""

    def test_payload_seed_cannot_be_modified(self) -> None:
        seed = NeuralSeed(
            event_profile=EventProfile.OBSERVATION_EVENT,
            payload_seed=(PayloadSeed(payload=PrimerPayload.NOVELTY, intensity=0.3),),
            provenance=_ref(),
        )
        with pytest.raises(ValidationError):
            setattr(  # noqa: B010
                seed,
                "payload_seed",
                (PayloadSeed(payload=PrimerPayload.URGENCY, intensity=0.5),),
            )

    def test_event_profile_cannot_be_modified(self) -> None:
        seed = NeuralSeed(
            event_profile=EventProfile.OBSERVATION_EVENT,
            payload_seed=(PayloadSeed(payload=PrimerPayload.NOVELTY, intensity=0.3),),
            provenance=_ref(),
        )
        with pytest.raises(ValidationError):
            setattr(seed, "event_profile", EventProfile.HUMAN_INTENT_EVENT)  # noqa: B010
