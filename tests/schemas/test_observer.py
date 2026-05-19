"""Schema tests for ObserverEvent (M1 audit ledger envelope).

Constitutional discipline tested here (schema layer only):
    - 8 closed EventFamily values
    - event_id / event_type / event_hash non-empty
    - occurred_at_ms non-negative
    - previous_event_hash may be None (genesis) or string
    - payload non-empty
    - extra="forbid"
    - frozen immutability
    - Observer-vs-Ingress asymmetry: domain labels ALLOWED in
      ObserverEvent.payload (raw audit), REJECTED in core-facing
      ingress envelopes (see test_events.py)
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sentinel.types.neural_seed import ProvenanceRef
from sentinel.types.observer import EventFamily, ObserverEvent


def _ref() -> ProvenanceRef:
    return ProvenanceRef(source_event_id="evt-source", source_spec="test")


def _base_kwargs() -> dict[str, object]:
    return {
        "event_id": "obs-0001",
        "event_family": EventFamily.MEMORY,
        "event_type": "MEMORY_RECORD_STATUS_CHANGED",
        "occurred_at_ms": 1_700_000_000_000,
        "payload": {"new_status": "candidate", "record_id": "rec-1"},
        "provenance": _ref(),
        "previous_event_hash": "sha256:prev",
        "event_hash": "sha256:self",
    }


# ---------------------------------------------------------------------------
# Closed enum
# ---------------------------------------------------------------------------


class TestEventFamily:
    def test_eight_values(self) -> None:
        assert len(EventFamily) == 8

    def test_canonical_names(self) -> None:
        expected = {
            "neural",
            "attention",
            "memory",
            "ingress",
            "bootstrap",
            "deontic",
            "replay",
            "ledger_meta",
        }
        assert {f.value for f in EventFamily} == expected


# ---------------------------------------------------------------------------
# Valid construction
# ---------------------------------------------------------------------------


class TestObserverEventValid:
    def test_minimal_construction(self) -> None:
        evt = ObserverEvent.model_validate(_base_kwargs())
        assert evt.event_family == EventFamily.MEMORY
        assert evt.event_hash == "sha256:self"

    def test_genesis_event_previous_hash_none(self) -> None:
        """First / genesis events may have previous_event_hash=None.

        Chain integrity is Phase 2's job; here schema only requires that
        the field be either None or a string.
        """
        kwargs = _base_kwargs()
        kwargs["previous_event_hash"] = None
        evt = ObserverEvent.model_validate(kwargs)
        assert evt.previous_event_hash is None

    def test_payload_with_domain_fields_allowed(self) -> None:
        """ObserverEvent.payload INTENTIONALLY allows domain/raw fields.

        Ingress envelopes (events.py) reject `symbol`/`venue`/`raw_payload`
        at the type boundary. ObserverEvent — the audit ledger — must
        record what really happened, including raw context, for forensic
        traceability. This test pins that ingress-vs-observer asymmetry.
        """
        kwargs = _base_kwargs()
        kwargs["event_family"] = EventFamily.INGRESS
        kwargs["event_type"] = "OBSERVATION_INGESTED"
        kwargs["payload"] = {
            "symbol": "BTCUSDT",
            "venue": "Binance",
            "raw_payload": "tick {bid:50000, ask:50001}",
        }
        evt = ObserverEvent.model_validate(kwargs)
        assert evt.payload["symbol"] == "BTCUSDT"

    @pytest.mark.parametrize("family", list(EventFamily))
    def test_every_family_accepted(self, family: EventFamily) -> None:
        kwargs = _base_kwargs()
        kwargs["event_family"] = family
        evt = ObserverEvent.model_validate(kwargs)
        assert evt.event_family == family


# ---------------------------------------------------------------------------
# Invalid construction
# ---------------------------------------------------------------------------


class TestObserverEventInvalid:
    def test_empty_event_id_rejected(self) -> None:
        kwargs = _base_kwargs()
        kwargs["event_id"] = ""
        with pytest.raises(ValidationError):
            ObserverEvent.model_validate(kwargs)

    def test_empty_event_type_rejected(self) -> None:
        kwargs = _base_kwargs()
        kwargs["event_type"] = ""
        with pytest.raises(ValidationError):
            ObserverEvent.model_validate(kwargs)

    def test_negative_occurred_at_rejected(self) -> None:
        kwargs = _base_kwargs()
        kwargs["occurred_at_ms"] = -1
        with pytest.raises(ValidationError):
            ObserverEvent.model_validate(kwargs)

    def test_empty_event_hash_rejected(self) -> None:
        kwargs = _base_kwargs()
        kwargs["event_hash"] = ""
        with pytest.raises(ValidationError):
            ObserverEvent.model_validate(kwargs)

    def test_empty_payload_rejected(self) -> None:
        kwargs = _base_kwargs()
        kwargs["payload"] = {}
        with pytest.raises(ValidationError):
            ObserverEvent.model_validate(kwargs)

    def test_invalid_event_family_rejected(self) -> None:
        kwargs = _base_kwargs()
        kwargs["event_family"] = "nonexistent_family"
        with pytest.raises(ValidationError):
            ObserverEvent.model_validate(kwargs)

    def test_extra_field_rejected(self) -> None:
        kwargs = _base_kwargs()
        kwargs["extra_field"] = "nope"
        with pytest.raises(ValidationError):
            ObserverEvent.model_validate(kwargs)

    def test_missing_provenance_rejected(self) -> None:
        kwargs = _base_kwargs()
        del kwargs["provenance"]
        with pytest.raises(ValidationError):
            ObserverEvent.model_validate(kwargs)

    def test_missing_event_hash_rejected(self) -> None:
        kwargs = _base_kwargs()
        del kwargs["event_hash"]
        with pytest.raises(ValidationError):
            ObserverEvent.model_validate(kwargs)


# ---------------------------------------------------------------------------
# Frozen immutability
# ---------------------------------------------------------------------------


class TestObserverEventImmutable:
    def test_event_hash_cannot_be_modified(self) -> None:
        evt = ObserverEvent.model_validate(_base_kwargs())
        with pytest.raises(ValidationError):
            setattr(evt, "event_hash", "sha256:tampered")  # noqa: B010

    def test_event_family_cannot_be_modified(self) -> None:
        evt = ObserverEvent.model_validate(_base_kwargs())
        with pytest.raises(ValidationError):
            setattr(evt, "event_family", EventFamily.DEONTIC)  # noqa: B010

    def test_payload_cannot_be_replaced(self) -> None:
        evt = ObserverEvent.model_validate(_base_kwargs())
        with pytest.raises(ValidationError):
            setattr(evt, "payload", {"tampered": True})  # noqa: B010
