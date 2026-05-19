"""Schema tests for WorkspacePulseEvent.

Constitutional discipline tested here (schema layer only):
    - event_type literal pinned to "WORKSPACE_PULSE"
    - dominant_payload_mix non-empty + duplicate primer payloads rejected
    - All bounded quality scores constrained to [0.0, 1.0] and finite
    - ttl_ms strictly > 0
    - Frozen immutability; extra="forbid"
    - "No pulse type" rule: pulse_type / pulse_category / focus_type /
      semantic_label / domain_label are rejected at the type boundary
"""

from __future__ import annotations

import math

import pytest
from pydantic import ValidationError
from sentinel.types.payload import PayloadSeed, PrimerPayload
from sentinel.types.workspace import WorkspacePulseEvent


def _seed(payload: PrimerPayload, intensity: float = 0.4) -> PayloadSeed:
    return PayloadSeed(payload=payload, intensity=intensity)


def _valid_kwargs() -> dict[str, object]:
    return {
        "pulse_id": "pulse-001",
        "assembly_id": "assembly-001",
        "occurred_at_ms": 1_700_000_000_000,
        "dominant_payload_mix": (
            _seed(PrimerPayload.URGENCY, 0.7),
            _seed(PrimerPayload.CONTRADICTION, 0.3),
        ),
        "activation_mass": 0.6,
        "coherence": 0.55,
        "persistence": 0.4,
        "habituation_penalty": 0.1,
        "fatigue_penalty": 0.05,
        "dissonance_score": 0.25,
        "allocation_share": 0.3,
        "ttl_ms": 750,
        "context_signature_hash": "sha256:abcd",
    }


# ---------------------------------------------------------------------------
# Valid construction
# ---------------------------------------------------------------------------


class TestValid:
    def test_valid_pulse_accepted(self) -> None:
        ev = WorkspacePulseEvent.model_validate(_valid_kwargs())
        assert ev.event_type == "WORKSPACE_PULSE"
        assert ev.pulse_id == "pulse-001"
        assert len(ev.dominant_payload_mix) == 2

    def test_event_type_default(self) -> None:
        ev = WorkspacePulseEvent.model_validate(_valid_kwargs())
        assert ev.event_type == "WORKSPACE_PULSE"

    def test_urgency_plus_contradiction_signature_accepted(self) -> None:
        """Pulse character expressed by mix, not by a pulse_type enum."""
        ev = WorkspacePulseEvent.model_validate(_valid_kwargs())
        payloads = {seed.payload for seed in ev.dominant_payload_mix}
        assert payloads == {PrimerPayload.URGENCY, PrimerPayload.CONTRADICTION}


# ---------------------------------------------------------------------------
# event_type discriminator
# ---------------------------------------------------------------------------


class TestEventType:
    def test_wrong_event_type_rejected(self) -> None:
        kwargs = _valid_kwargs()
        kwargs["event_type"] = "FOCUS_PULSE"
        with pytest.raises(ValidationError):
            WorkspacePulseEvent.model_validate(kwargs)

    def test_contradiction_pulse_type_rejected(self) -> None:
        kwargs = _valid_kwargs()
        kwargs["event_type"] = "CONTRADICTION_PULSE"
        with pytest.raises(ValidationError):
            WorkspacePulseEvent.model_validate(kwargs)


# ---------------------------------------------------------------------------
# dominant_payload_mix
# ---------------------------------------------------------------------------


class TestDominantPayloadMix:
    def test_empty_mix_rejected(self) -> None:
        kwargs = _valid_kwargs()
        kwargs["dominant_payload_mix"] = ()
        with pytest.raises(ValidationError):
            WorkspacePulseEvent.model_validate(kwargs)

    def test_duplicate_payload_in_mix_rejected(self) -> None:
        kwargs = _valid_kwargs()
        kwargs["dominant_payload_mix"] = (
            _seed(PrimerPayload.URGENCY, 0.7),
            _seed(PrimerPayload.URGENCY, 0.2),
        )
        with pytest.raises(ValidationError):
            WorkspacePulseEvent.model_validate(kwargs)


# ---------------------------------------------------------------------------
# Bounded score fields
# ---------------------------------------------------------------------------


class TestBoundedScores:
    @pytest.mark.parametrize(
        "field",
        [
            "activation_mass",
            "coherence",
            "persistence",
            "habituation_penalty",
            "fatigue_penalty",
            "dissonance_score",
            "allocation_share",
        ],
    )
    def test_score_above_one_rejected(self, field: str) -> None:
        kwargs = _valid_kwargs()
        kwargs[field] = 1.01
        with pytest.raises(ValidationError):
            WorkspacePulseEvent.model_validate(kwargs)

    @pytest.mark.parametrize(
        "field",
        [
            "activation_mass",
            "coherence",
            "persistence",
            "habituation_penalty",
            "fatigue_penalty",
            "dissonance_score",
            "allocation_share",
        ],
    )
    def test_score_below_zero_rejected(self, field: str) -> None:
        kwargs = _valid_kwargs()
        kwargs[field] = -0.01
        with pytest.raises(ValidationError):
            WorkspacePulseEvent.model_validate(kwargs)

    def test_nan_score_rejected(self) -> None:
        kwargs = _valid_kwargs()
        kwargs["activation_mass"] = math.nan
        with pytest.raises(ValidationError):
            WorkspacePulseEvent.model_validate(kwargs)

    def test_inf_score_rejected(self) -> None:
        kwargs = _valid_kwargs()
        kwargs["coherence"] = math.inf
        with pytest.raises(ValidationError):
            WorkspacePulseEvent.model_validate(kwargs)


# ---------------------------------------------------------------------------
# ttl_ms / occurred_at_ms
# ---------------------------------------------------------------------------


class TestTimingFields:
    def test_ttl_ms_zero_rejected(self) -> None:
        kwargs = _valid_kwargs()
        kwargs["ttl_ms"] = 0
        with pytest.raises(ValidationError):
            WorkspacePulseEvent.model_validate(kwargs)

    def test_ttl_ms_negative_rejected(self) -> None:
        kwargs = _valid_kwargs()
        kwargs["ttl_ms"] = -1
        with pytest.raises(ValidationError):
            WorkspacePulseEvent.model_validate(kwargs)

    def test_occurred_at_ms_negative_rejected(self) -> None:
        kwargs = _valid_kwargs()
        kwargs["occurred_at_ms"] = -1
        with pytest.raises(ValidationError):
            WorkspacePulseEvent.model_validate(kwargs)


# ---------------------------------------------------------------------------
# Required string fields
# ---------------------------------------------------------------------------


class TestRequiredStringFields:
    @pytest.mark.parametrize(
        "field",
        ["pulse_id", "assembly_id", "context_signature_hash"],
    )
    def test_empty_string_rejected(self, field: str) -> None:
        kwargs = _valid_kwargs()
        kwargs[field] = ""
        with pytest.raises(ValidationError):
            WorkspacePulseEvent.model_validate(kwargs)


# ---------------------------------------------------------------------------
# "No pulse type" constitutional rule
# ---------------------------------------------------------------------------


class TestNoPulseTypeRule:
    """Pulse character lives in dominant_payload_mix, NOT in any enum."""

    @pytest.mark.parametrize(
        "rogue_field",
        [
            "pulse_type",
            "pulse_category",
            "focus_type",
            "semantic_label",
            "domain_label",
        ],
    )
    def test_pulse_typing_field_rejected(self, rogue_field: str) -> None:
        kwargs = _valid_kwargs()
        kwargs[rogue_field] = "focus"
        with pytest.raises(ValidationError):
            WorkspacePulseEvent.model_validate(kwargs)


# ---------------------------------------------------------------------------
# Immutability
# ---------------------------------------------------------------------------


class TestImmutability:
    def test_extra_field_rejected(self) -> None:
        kwargs = _valid_kwargs()
        kwargs["rogue_field"] = "nope"
        with pytest.raises(ValidationError):
            WorkspacePulseEvent.model_validate(kwargs)

    def test_frozen(self) -> None:
        ev = WorkspacePulseEvent.model_validate(_valid_kwargs())
        with pytest.raises(ValidationError):
            setattr(ev, "activation_mass", 0.9)  # noqa: B010
