"""Schema tests for ingress event envelopes.

Constitutional discipline tested here (schema layer only):
    - 4 closed event types
    - Bounded confidence [0.0, 1.0]; NaN/inf rejected
    - Positive ttl_ms; non-negative occurred_at_ms
    - Domain labels (symbol/venue/market/raw_payload/intent_text) rejected
    - Frozen immutability
    - extra="forbid"
    - All 7 RecallRecordStatus values schema-valid (suppression is Phase 8)
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sentinel.types.events import (
    HumanIntentEvent,
    IngressEventType,
    InternalShockEvent,
    ObservationEvent,
    RecallEvent,
    RecallRecordStatus,
    ShockSeverity,
    ShockSource,
)
from sentinel.types.memory import SubjectClass

# ---------------------------------------------------------------------------
# Closed enum sets
# ---------------------------------------------------------------------------


class TestIngressEventType:
    def test_four_values(self) -> None:
        assert len(IngressEventType) == 4

    def test_canonical_names(self) -> None:
        expected = {
            "ObservationEvent",
            "HumanIntentEvent",
            "InternalShockEvent",
            "RecallEvent",
        }
        assert {e.value for e in IngressEventType} == expected


class TestShockSource:
    def test_four_values(self) -> None:
        assert len(ShockSource) == 4


class TestShockSeverity:
    def test_four_bands(self) -> None:
        assert {s.value for s in ShockSeverity} == {"low", "medium", "high", "critical"}


class TestRecallRecordStatus:
    def test_seven_statuses(self) -> None:
        assert len(RecallRecordStatus) == 7


# ---------------------------------------------------------------------------
# Valid construction
# ---------------------------------------------------------------------------


def _base_kwargs() -> dict[str, object]:
    return {
        "event_id": "evt-0001",
        "occurred_at_ms": 1_700_000_000_000,
        "ttl_ms": 60_000,
        "confidence": 0.7,
    }


class TestObservationEventValid:
    def test_minimal_construction(self) -> None:
        evt = ObservationEvent(
            **_base_kwargs(),  # type: ignore[arg-type]
            source_adapter_id="echo",
            source_reliability_band=3,
            magnitude_normalized=0.4,
            novelty_indicator=0.2,
            staleness_ms=500,
        )
        assert evt.event_type == IngressEventType.OBSERVATION
        assert evt.confidence == pytest.approx(0.7)


class TestHumanIntentEventValid:
    def test_minimal_construction(self) -> None:
        evt = HumanIntentEvent(
            **_base_kwargs(),  # type: ignore[arg-type]
            intent_text_hash="sha256:abc",
            ambiguity_score=0.3,
            human_confirmed=True,
        )
        assert evt.event_type == IngressEventType.HUMAN_INTENT


class TestInternalShockEventValid:
    def test_minimal_construction(self) -> None:
        evt = InternalShockEvent(
            **_base_kwargs(),  # type: ignore[arg-type]
            shock_source=ShockSource.DEONTIC_GATE,
            severity=ShockSeverity.HIGH,
            refractory_key="deontic:bypass_attempt",
        )
        assert evt.event_type == IngressEventType.INTERNAL_SHOCK


class TestRecallEventValid:
    def test_minimal_construction(self) -> None:
        evt = RecallEvent(
            **_base_kwargs(),  # type: ignore[arg-type]
            source_record_id="rec-001",
            record_status=RecallRecordStatus.VERIFIED,
            subject_class=SubjectClass.SOURCE_TRUST,
            age_ms=120_000,
            contradiction_risk=0.05,
        )
        assert evt.event_type == IngressEventType.RECALL
        assert evt.subject_class == SubjectClass.SOURCE_TRUST

    @pytest.mark.parametrize("status", list(RecallRecordStatus))
    def test_all_record_statuses_accepted(self, status: RecallRecordStatus) -> None:
        """All 7 statuses are schema-valid; suppression is Phase 8 (recall)."""
        evt = RecallEvent(
            **_base_kwargs(),  # type: ignore[arg-type]
            source_record_id="rec-002",
            record_status=status,
            subject_class=SubjectClass.PROCEDURAL,
            age_ms=0,
            contradiction_risk=0.0,
        )
        assert evt.record_status == status

    @pytest.mark.parametrize("subject_class", list(SubjectClass))
    def test_every_subject_class_accepted(self, subject_class: SubjectClass) -> None:
        """Every canonical SubjectClass value is type-accepted on RecallEvent.

        (Suppression / candidate restrictions live in Phase 8 / T §14.)
        """
        evt = RecallEvent(
            **_base_kwargs(),  # type: ignore[arg-type]
            source_record_id="rec-003",
            record_status=RecallRecordStatus.VERIFIED,
            subject_class=subject_class,
            age_ms=0,
            contradiction_risk=0.0,
        )
        assert evt.subject_class == subject_class

    def test_foreign_instance_origin_rejected_as_subject_class(self) -> None:
        """foreign_instance_origin is provenance metadata, not a subject_class.

        Bound by `SubjectClass` enum — string passes through model_validate
        but is rejected because it is not a canonical SubjectClass member.
        """
        with pytest.raises(ValidationError):
            RecallEvent.model_validate(
                {
                    "event_id": "evt-0001",
                    "occurred_at_ms": 1,
                    "ttl_ms": 1,
                    "confidence": 0.5,
                    "source_record_id": "rec-001",
                    "record_status": "verified",
                    "subject_class": "foreign_instance_origin",
                    "age_ms": 0,
                    "contradiction_risk": 0.0,
                }
            )

    def test_invalid_subject_class_string_rejected(self) -> None:
        with pytest.raises(ValidationError):
            RecallEvent.model_validate(
                {
                    "event_id": "evt-0001",
                    "occurred_at_ms": 1,
                    "ttl_ms": 1,
                    "confidence": 0.5,
                    "source_record_id": "rec-001",
                    "record_status": "verified",
                    "subject_class": "totally_made_up",
                    "age_ms": 0,
                    "contradiction_risk": 0.0,
                }
            )


# ---------------------------------------------------------------------------
# Common base validation (run via ObservationEvent for brevity)
# ---------------------------------------------------------------------------


class TestCommonBaseValidation:
    def test_confidence_above_one_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ObservationEvent(
                event_id="evt-0001",
                occurred_at_ms=1,
                ttl_ms=1,
                confidence=1.1,
                source_adapter_id="echo",
                source_reliability_band=3,
                magnitude_normalized=0.4,
                novelty_indicator=0.2,
                staleness_ms=0,
            )

    def test_confidence_negative_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ObservationEvent(
                event_id="evt-0001",
                occurred_at_ms=1,
                ttl_ms=1,
                confidence=-0.01,
                source_adapter_id="echo",
                source_reliability_band=3,
                magnitude_normalized=0.4,
                novelty_indicator=0.2,
                staleness_ms=0,
            )

    def test_confidence_nan_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ObservationEvent(
                event_id="evt-0001",
                occurred_at_ms=1,
                ttl_ms=1,
                confidence=float("nan"),
                source_adapter_id="echo",
                source_reliability_band=3,
                magnitude_normalized=0.4,
                novelty_indicator=0.2,
                staleness_ms=0,
            )

    def test_ttl_zero_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ObservationEvent(
                event_id="evt-0001",
                occurred_at_ms=1,
                ttl_ms=0,
                confidence=0.5,
                source_adapter_id="echo",
                source_reliability_band=3,
                magnitude_normalized=0.4,
                novelty_indicator=0.2,
                staleness_ms=0,
            )

    def test_occurred_at_negative_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ObservationEvent(
                event_id="evt-0001",
                occurred_at_ms=-1,
                ttl_ms=1,
                confidence=0.5,
                source_adapter_id="echo",
                source_reliability_band=3,
                magnitude_normalized=0.4,
                novelty_indicator=0.2,
                staleness_ms=0,
            )

    def test_empty_event_id_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ObservationEvent(
                event_id="",
                occurred_at_ms=1,
                ttl_ms=1,
                confidence=0.5,
                source_adapter_id="echo",
                source_reliability_band=3,
                magnitude_normalized=0.4,
                novelty_indicator=0.2,
                staleness_ms=0,
            )


# ---------------------------------------------------------------------------
# Domain label rejection — constitutional discipline
# ---------------------------------------------------------------------------


class TestDomainLabelsRejected:
    """Raw/domain fields are NOT permitted on core-facing ingress envelopes."""

    @pytest.mark.parametrize(
        "domain_field",
        ["symbol", "venue", "market", "raw_payload", "price", "ticker"],
    )
    def test_observation_event_rejects_domain_field(self, domain_field: str) -> None:
        with pytest.raises(ValidationError):
            ObservationEvent.model_validate(
                {
                    "event_id": "evt-0001",
                    "occurred_at_ms": 1,
                    "ttl_ms": 1,
                    "confidence": 0.5,
                    "source_adapter_id": "echo",
                    "source_reliability_band": 3,
                    "magnitude_normalized": 0.4,
                    "novelty_indicator": 0.2,
                    "staleness_ms": 0,
                    domain_field: "BTCUSDT",
                }
            )

    def test_human_intent_event_rejects_raw_intent_text(self) -> None:
        with pytest.raises(ValidationError):
            HumanIntentEvent.model_validate(
                {
                    "event_id": "evt-0001",
                    "occurred_at_ms": 1,
                    "ttl_ms": 1,
                    "confidence": 0.5,
                    "intent_text_hash": "sha256:abc",
                    "ambiguity_score": 0.3,
                    "human_confirmed": True,
                    "intent_text": "Halit said BTC up",
                }
            )

    def test_recall_event_rejects_raw_content(self) -> None:
        with pytest.raises(ValidationError):
            RecallEvent.model_validate(
                {
                    "event_id": "evt-0001",
                    "occurred_at_ms": 1,
                    "ttl_ms": 1,
                    "confidence": 0.5,
                    "source_record_id": "rec-001",
                    "record_status": "verified",
                    "subject_class": "source_trust",
                    "age_ms": 0,
                    "contradiction_risk": 0.0,
                    "raw_content": "BTCUSDT price 50000",
                }
            )


# ---------------------------------------------------------------------------
# Frozen immutability
# ---------------------------------------------------------------------------


class TestImmutable:
    def test_observation_event_frozen(self) -> None:
        evt = ObservationEvent(
            event_id="evt-0001",
            occurred_at_ms=1,
            ttl_ms=1,
            confidence=0.5,
            source_adapter_id="echo",
            source_reliability_band=3,
            magnitude_normalized=0.4,
            novelty_indicator=0.2,
            staleness_ms=0,
        )
        with pytest.raises(ValidationError):
            setattr(evt, "confidence", 0.9)  # noqa: B010

    def test_internal_shock_event_frozen(self) -> None:
        evt = InternalShockEvent(
            event_id="evt-0001",
            occurred_at_ms=1,
            ttl_ms=1,
            confidence=0.5,
            shock_source=ShockSource.KILL_SWITCH,
            severity=ShockSeverity.CRITICAL,
            refractory_key="kill:01",
        )
        with pytest.raises(ValidationError):
            setattr(evt, "severity", ShockSeverity.LOW)  # noqa: B010


# ---------------------------------------------------------------------------
# Discriminator invariant — envelope cannot wear another envelope's event_type
# ---------------------------------------------------------------------------


class TestEventTypeDiscriminatorFixed:
    """Each envelope's event_type is a Literal — wrong values rejected.

    This pins the schema invariant: ObservationEvent cannot pretend to be
    a RecallEvent (and vice versa) by overriding event_type at construction.
    """

    def test_observation_event_rejects_wrong_event_type(self) -> None:
        with pytest.raises(ValidationError):
            ObservationEvent.model_validate(
                {
                    "event_type": "RecallEvent",
                    "event_id": "evt-0001",
                    "occurred_at_ms": 1,
                    "ttl_ms": 1,
                    "confidence": 0.5,
                    "source_adapter_id": "echo",
                    "source_reliability_band": 3,
                    "magnitude_normalized": 0.4,
                    "novelty_indicator": 0.2,
                    "staleness_ms": 0,
                }
            )

    def test_human_intent_event_rejects_wrong_event_type(self) -> None:
        with pytest.raises(ValidationError):
            HumanIntentEvent.model_validate(
                {
                    "event_type": "ObservationEvent",
                    "event_id": "evt-0001",
                    "occurred_at_ms": 1,
                    "ttl_ms": 1,
                    "confidence": 0.5,
                    "intent_text_hash": "sha256:abc",
                    "ambiguity_score": 0.3,
                    "human_confirmed": True,
                }
            )

    def test_internal_shock_event_rejects_wrong_event_type(self) -> None:
        with pytest.raises(ValidationError):
            InternalShockEvent.model_validate(
                {
                    "event_type": "HumanIntentEvent",
                    "event_id": "evt-0001",
                    "occurred_at_ms": 1,
                    "ttl_ms": 1,
                    "confidence": 0.5,
                    "shock_source": "deontic_gate",
                    "severity": "high",
                    "refractory_key": "deontic:bypass_attempt",
                }
            )

    def test_recall_event_rejects_wrong_event_type(self) -> None:
        with pytest.raises(ValidationError):
            RecallEvent.model_validate(
                {
                    "event_type": "InternalShockEvent",
                    "event_id": "evt-0001",
                    "occurred_at_ms": 1,
                    "ttl_ms": 1,
                    "confidence": 0.5,
                    "source_record_id": "rec-001",
                    "record_status": "verified",
                    "subject_class": "source_trust",
                    "age_ms": 0,
                    "contradiction_risk": 0.0,
                }
            )
