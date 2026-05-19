"""Tests for the canonical observer event catalog.

Discipline tested here (catalog layer only):
    - Catalog is non-empty and event_type values are unique
    - Every row has a non-empty source_ref
    - Helpers (get/list/is/expected_family_for/permanence_for) behave
    - validate_event_family accepts matching pairs and raises
      InvariantViolation on mismatch / unknown event
    - Critical events require a human alert
    - permanent_with_snapshot rows include the constitutional anchors
    - WORKSPACE_PULSE and OBSERVATION_INGESTED are ring_buffer_only
"""

from __future__ import annotations

import pytest
from sentinel.constitution.violations import InvariantViolation
from sentinel.observer.catalog import (
    CANONICAL_EVENT_CATALOG,
    CanonicalEventDefinition,
    EventPermanence,
    SeverityBand,
    expected_family_for,
    get_event_definition,
    is_canonical_event_type,
    list_event_definitions,
    permanence_for,
    validate_event_family,
)
from sentinel.types.observer import EventFamily


class TestCatalogShape:
    def test_catalog_non_empty(self) -> None:
        assert len(CANONICAL_EVENT_CATALOG) > 0

    def test_event_types_unique(self) -> None:
        types = [ev.event_type for ev in CANONICAL_EVENT_CATALOG]
        assert len(set(types)) == len(types)

    def test_every_row_has_source_ref(self) -> None:
        for ev in CANONICAL_EVENT_CATALOG:
            assert ev.source_ref.strip() != ""

    def test_definition_is_frozen(self) -> None:
        from dataclasses import FrozenInstanceError

        ev = CANONICAL_EVENT_CATALOG[0]
        with pytest.raises(FrozenInstanceError):
            ev.event_type = "OTHER"  # type: ignore[misc]


class TestHelpers:
    def test_list_event_definitions_returns_full_catalog(self) -> None:
        assert list_event_definitions() == CANONICAL_EVENT_CATALOG

    def test_get_event_definition_known(self) -> None:
        ev = get_event_definition("WORKSPACE_PULSE")
        assert isinstance(ev, CanonicalEventDefinition)
        assert ev.event_family is EventFamily.ATTENTION

    def test_get_event_definition_unknown_raises_keyerror(self) -> None:
        with pytest.raises(KeyError):
            get_event_definition("NOT_AN_EVENT")

    def test_is_canonical_event_type_true(self) -> None:
        assert is_canonical_event_type("KILL_SWITCH_ACTIVATED") is True

    def test_is_canonical_event_type_false(self) -> None:
        assert is_canonical_event_type("NOT_AN_EVENT") is False

    def test_expected_family_for(self) -> None:
        assert expected_family_for("DEONTIC_BLOCKED") is EventFamily.DEONTIC

    def test_permanence_for(self) -> None:
        assert permanence_for("WORKSPACE_PULSE") is EventPermanence.RING_BUFFER_ONLY


class TestValidateEventFamily:
    def test_matching_pair_passes(self) -> None:
        validate_event_family("DEONTIC_BLOCKED", EventFamily.DEONTIC)

    def test_mismatched_family_rejected(self) -> None:
        with pytest.raises(InvariantViolation) as exc_info:
            validate_event_family("DEONTIC_BLOCKED", EventFamily.MEMORY)
        assert exc_info.value.violation_code == "OBSERVER_EVENT_FAMILY_MATCHES_CATALOG"
        assert exc_info.value.evidence["event_type"] == "DEONTIC_BLOCKED"
        assert exc_info.value.evidence["expected_family"] == "deontic"
        assert exc_info.value.evidence["actual_family"] == "memory"

    def test_unknown_event_rejected(self) -> None:
        with pytest.raises(InvariantViolation) as exc_info:
            validate_event_family("NOT_AN_EVENT", EventFamily.LEDGER_META)
        assert exc_info.value.violation_code == "OBSERVER_EVENT_TYPE_UNKNOWN"


class TestHumanAlertCriticalEvents:
    @pytest.mark.parametrize(
        "event_type",
        [
            "DEONTIC_BYPASS_ATTEMPT",
            "KILL_SWITCH_ACTIVATED",
            "INTERNAL_SHOCK_INGESTED",
        ],
    )
    def test_critical_event_requires_human_alert(self, event_type: str) -> None:
        assert get_event_definition(event_type).human_alert_required is True


class TestPermanencePolicy:
    @pytest.mark.parametrize(
        "event_type",
        [
            "KILL_SWITCH_ACTIVATED",
            "DEONTIC_BYPASS_ATTEMPT",
            "INTERNAL_SHOCK_INGESTED",
            "SELF_GENESIS",
        ],
    )
    def test_permanent_with_snapshot_anchors(self, event_type: str) -> None:
        assert permanence_for(event_type) is EventPermanence.PERMANENT_WITH_SNAPSHOT

    @pytest.mark.parametrize(
        "event_type",
        ["WORKSPACE_PULSE", "OBSERVATION_INGESTED", "RECALL_EVENT_INGESTED"],
    )
    def test_ring_buffer_only_high_volume_events(self, event_type: str) -> None:
        assert permanence_for(event_type) is EventPermanence.RING_BUFFER_ONLY


class TestSeverityBands:
    def test_kill_switch_is_critical(self) -> None:
        assert get_event_definition("KILL_SWITCH_ACTIVATED").severity_band is SeverityBand.CRITICAL

    def test_workspace_pulse_is_routine(self) -> None:
        assert get_event_definition("WORKSPACE_PULSE").severity_band is SeverityBand.ROUTINE
