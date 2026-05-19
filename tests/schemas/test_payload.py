"""Schema tests for PayloadSeed.

Constitutional discipline tested here:
    - Closed 10-value primer payload palette
    - Bounded finite intensity [0.0, 1.0]; NaN/inf rejected
    - extra fields rejected
    - frozen immutability
    - Task/domain payloads (BUY/SELL/TRADE/BTC/BTCUSDT) rejected
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sentinel.types.payload import PayloadSeed, PrimerPayload


class TestPrimerPayload:
    """The closed palette is exactly 10 canonical names."""

    def test_palette_has_ten_values(self) -> None:
        assert len(PrimerPayload) == 10

    def test_canonical_names(self) -> None:
        expected = {
            "suspicion",
            "novelty",
            "aversion",
            "attraction",
            "contradiction",
            "urgency",
            "memory_echo",
            "fatigue_trace",
            "pain_trace",
            "reward_trace",
        }
        assert {p.value for p in PrimerPayload} == expected


class TestPayloadSeedValid:
    """Valid PayloadSeed constructions."""

    @pytest.mark.parametrize("payload", list(PrimerPayload))
    def test_every_primer_payload_accepted(self, payload: PrimerPayload) -> None:
        seed = PayloadSeed(payload=payload, intensity=0.5)
        assert seed.payload == payload

    def test_intensity_zero_accepted(self) -> None:
        seed = PayloadSeed(payload=PrimerPayload.SUSPICION, intensity=0.0)
        assert seed.intensity == 0.0

    def test_intensity_one_accepted(self) -> None:
        seed = PayloadSeed(payload=PrimerPayload.URGENCY, intensity=1.0)
        assert seed.intensity == 1.0


class TestPayloadSeedInvalid:
    """Invalid PayloadSeed constructions must raise ValidationError."""

    def test_intensity_below_zero_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PayloadSeed(payload=PrimerPayload.SUSPICION, intensity=-0.1)

    def test_intensity_above_one_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PayloadSeed(payload=PrimerPayload.SUSPICION, intensity=1.1)

    def test_intensity_nan_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PayloadSeed(payload=PrimerPayload.SUSPICION, intensity=float("nan"))

    def test_intensity_positive_inf_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PayloadSeed(payload=PrimerPayload.SUSPICION, intensity=float("inf"))

    def test_intensity_negative_inf_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PayloadSeed(payload=PrimerPayload.SUSPICION, intensity=float("-inf"))

    def test_extra_field_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PayloadSeed.model_validate(
                {
                    "payload": "suspicion",
                    "intensity": 0.5,
                    "extra_field": "not allowed",
                }
            )

    @pytest.mark.parametrize(
        "forbidden_payload",
        [
            "buy",
            "sell",
            "trade",
            "execute",
            "order",
        ],
    )
    def test_task_payload_rejected(self, forbidden_payload: str) -> None:
        """Task verbs are NOT mental colors; reject at type boundary."""
        with pytest.raises(ValidationError):
            PayloadSeed.model_validate({"payload": forbidden_payload, "intensity": 0.5})

    @pytest.mark.parametrize(
        "forbidden_payload",
        [
            "BTC",
            "BTCUSDT",
            "ETH",
            "binance",
            "btcturk",
            "symbol",
            "market",
        ],
    )
    def test_domain_payload_rejected(self, forbidden_payload: str) -> None:
        """Domain labels are NOT mental colors; reject at type boundary."""
        with pytest.raises(ValidationError):
            PayloadSeed.model_validate({"payload": forbidden_payload, "intensity": 0.5})


class TestPayloadSeedImmutable:
    """frozen=True forbids mutation after construction."""

    def test_intensity_cannot_be_modified(self) -> None:
        seed = PayloadSeed(payload=PrimerPayload.NOVELTY, intensity=0.3)
        with pytest.raises(ValidationError):
            setattr(seed, "intensity", 0.5)  # noqa: B010

    def test_payload_cannot_be_modified(self) -> None:
        seed = PayloadSeed(payload=PrimerPayload.NOVELTY, intensity=0.3)
        with pytest.raises(ValidationError):
            setattr(seed, "payload", PrimerPayload.SUSPICION)  # noqa: B010
