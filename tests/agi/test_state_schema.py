"""V10 — AGI state schema tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sentinel.agi.state import (
    FinancialAGIActivationState,
    FinancialAGICapabilityMap,
    FinancialAGIPhase,
    FinancialAGIState,
)


class TestFinancialAGICapabilityMap:
    def test_default_is_valid(self) -> None:
        cap = FinancialAGICapabilityMap()
        assert cap.direct_execution is False
        assert cap.exchange_imports is False
        assert cap.llm_imports is False
        assert cap.gelal_write_path is False
        assert cap.approved_action_intent_generation is False

    def test_advisory_capabilities_default_true(self) -> None:
        cap = FinancialAGICapabilityMap()
        assert cap.shadow_observation is True
        assert cap.paper_copilot_advisory is True
        assert cap.canary_veto_advisory is True
        assert cap.live_governance_advisory is True
        assert cap.readiness_reporting is True

    def test_direct_execution_cannot_be_true(self) -> None:
        with pytest.raises(ValidationError):
            FinancialAGICapabilityMap(direct_execution=True)  # type: ignore[arg-type]

    def test_exchange_imports_cannot_be_true(self) -> None:
        with pytest.raises(ValidationError):
            FinancialAGICapabilityMap(exchange_imports=True)  # type: ignore[arg-type]

    def test_llm_imports_cannot_be_true(self) -> None:
        with pytest.raises(ValidationError):
            FinancialAGICapabilityMap(llm_imports=True)  # type: ignore[arg-type]

    def test_gelal_write_path_cannot_be_true(self) -> None:
        with pytest.raises(ValidationError):
            FinancialAGICapabilityMap(gelal_write_path=True)  # type: ignore[arg-type]

    def test_approved_action_intent_generation_cannot_be_true(self) -> None:
        with pytest.raises(ValidationError):
            FinancialAGICapabilityMap(approved_action_intent_generation=True)  # type: ignore[arg-type]

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            FinancialAGICapabilityMap(unknown_flag=True)  # type: ignore[call-arg]


class TestFinancialAGIActivationState:
    def test_all_values_accessible(self) -> None:
        states = list(FinancialAGIActivationState)
        assert len(states) == 9

    def test_not_ready_value(self) -> None:
        assert FinancialAGIActivationState.NOT_READY.value == "not_ready"

    def test_released_not_activated_value(self) -> None:
        assert (
            FinancialAGIActivationState.RELEASED_BUT_NOT_ACTIVATED.value
            == "released_but_not_activated"
        )


class TestFinancialAGIState:
    def test_valid_state(self) -> None:
        state = FinancialAGIState(
            state_id="s-1",
            phase=FinancialAGIPhase.AGI_V1,
            activation_state=FinancialAGIActivationState.AGI_V1_READY,
            created_at_ms=1_700_000_001_000,
            evidence_evaluated_at_ms=1_700_000_000_000,
        )
        assert state.capability_map.direct_execution is False

    def test_evidence_at_ms_after_created_rejected(self) -> None:
        with pytest.raises(ValidationError):
            FinancialAGIState(
                state_id="s-2",
                phase=FinancialAGIPhase.AGI_V1,
                activation_state=FinancialAGIActivationState.NOT_READY,
                created_at_ms=1_000,
                evidence_evaluated_at_ms=2_000,
            )

    def test_frozen(self) -> None:
        state = FinancialAGIState(
            state_id="s-3",
            phase=FinancialAGIPhase.SHADOW,
            activation_state=FinancialAGIActivationState.SHADOW_READY,
            created_at_ms=1_000,
        )
        from pydantic import ValidationError as PydanticValidationError

        with pytest.raises((TypeError, AttributeError, PydanticValidationError)):
            state.phase = FinancialAGIPhase.PAPER  # type: ignore[misc]
