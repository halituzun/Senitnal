"""Tests for the deontic gate."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from pydantic import ValidationError
from sentinel.gates.deontic import (
    DEONTIC_DECLARATIVES,
    ApprovedActionIntent,
    BlockClass,
    DeonticDecision,
    DeonticDeclarative,
    DeonticOutcome,
    evaluate_action,
    get_declarative,
)


def _intent(intent_id: str = "i1") -> ApprovedActionIntent:
    return ApprovedActionIntent(
        intent_id=intent_id,
        intent_type="observe_only",
        rationale="test",
        requested_at_ms=42,
    )


class TestDeclaratives:
    def test_eleven_declaratives(self) -> None:
        assert len(DEONTIC_DECLARATIVES) == 11

    def test_codes_unique(self) -> None:
        codes = [d.code for d in DEONTIC_DECLARATIVES]
        assert len(set(codes)) == len(codes)

    def test_kill_switch_present(self) -> None:
        d = get_declarative("KILL_SWITCH_ACTIVE_BLOCKS_ALL_ACTION")
        assert d.block_class is BlockClass.CONSTITUTIONAL

    def test_mvp_execute_disabled_present(self) -> None:
        d = get_declarative("MVP_EXECUTE_DISABLED_BLOCKS_ALL_ACTION")
        assert d.block_class is BlockClass.CONSTITUTIONAL

    def test_unknown_code_raises(self) -> None:
        with pytest.raises(KeyError):
            get_declarative("NOPE")

    def test_every_declarative_has_source_ref_and_statement(self) -> None:
        for d in DEONTIC_DECLARATIVES:
            assert d.source_ref != ""
            assert d.statement != ""


class TestEvaluateActionMvp:
    def test_mvp_default_blocks_every_intent(self) -> None:
        out = evaluate_action(_intent())
        assert out.decision is DeonticDecision.BLOCK
        assert out.triggered_declarative_code == ("MVP_EXECUTE_DISABLED_BLOCKS_ALL_ACTION")
        assert out.block_class is BlockClass.CONSTITUTIONAL

    def test_kill_switch_takes_precedence(self) -> None:
        def _flag_stub(name: str) -> bool:
            return name == "kill_switch_active"

        with patch("sentinel.gates.deontic.get_flag", side_effect=_flag_stub):
            out = evaluate_action(_intent())
        assert out.decision is DeonticDecision.BLOCK
        assert out.triggered_declarative_code == ("KILL_SWITCH_ACTIVE_BLOCKS_ALL_ACTION")

    def test_defense_in_depth_blocks_when_both_flags_off(self) -> None:
        with patch("sentinel.gates.deontic.get_flag", return_value=False):
            out = evaluate_action(_intent())
        assert out.decision is DeonticDecision.BLOCK
        assert out.triggered_declarative_code == "NO_LIVE_EXCHANGE_EXECUTION"


class TestOutcomeSchema:
    def test_block_without_block_class_rejected(self) -> None:
        with pytest.raises(ValidationError):
            DeonticOutcome(
                intent_id="i",
                decision=DeonticDecision.BLOCK,
                block_class=None,
                triggered_declarative_code="X",
                reason="r",
            )

    def test_block_without_declarative_rejected(self) -> None:
        with pytest.raises(ValidationError):
            DeonticOutcome(
                intent_id="i",
                decision=DeonticDecision.BLOCK,
                block_class=BlockClass.SAFETY,
                triggered_declarative_code=None,
                reason="r",
            )

    def test_allow_with_block_class_rejected(self) -> None:
        with pytest.raises(ValidationError):
            DeonticOutcome(
                intent_id="i",
                decision=DeonticDecision.ALLOW,
                block_class=BlockClass.SAFETY,
                triggered_declarative_code=None,
                reason="r",
            )

    def test_allow_with_declarative_rejected(self) -> None:
        with pytest.raises(ValidationError):
            DeonticOutcome(
                intent_id="i",
                decision=DeonticDecision.ALLOW,
                block_class=None,
                triggered_declarative_code="X",
                reason="r",
            )

    def test_valid_allow_accepted(self) -> None:
        DeonticOutcome(
            intent_id="i",
            decision=DeonticDecision.ALLOW,
            block_class=None,
            triggered_declarative_code=None,
            reason="non-MVP",
        )


class TestNoSoftPath:
    def test_no_warning_decision_exists(self) -> None:
        # The enum is closed; only BLOCK and ALLOW exist.
        assert {d.value for d in DeonticDecision} == {"block", "allow"}


class TestDeclarativeCoverage:
    """Each declarative produces a constructible BLOCK outcome.

    Per build plan §12 done def, every constitutional rule should
    have a violation test. The MVP gate currently routes through
    the first two declaratives (kill switch + mvp_execute_disabled);
    the remaining declaratives are defense-in-depth wiring for
    future phases. This sweep guarantees every declarative row is
    well-formed and constructible into a valid DeonticOutcome.
    """

    @pytest.mark.parametrize(
        "declarative",
        list(DEONTIC_DECLARATIVES),
    )
    def test_declarative_outcome_schema_accepts(
        self, declarative: DeonticDeclarative
    ) -> None:
        outcome = DeonticOutcome(
            intent_id="probe",
            decision=DeonticDecision.BLOCK,
            block_class=declarative.block_class,
            triggered_declarative_code=declarative.code,
            reason=declarative.statement,
        )
        assert outcome.triggered_declarative_code == declarative.code
        assert outcome.block_class is declarative.block_class
