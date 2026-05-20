"""V6 — Financial deontic policy schema tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sentinel.policy.financial import (
    FinancialDeonticPolicyArtifact,
    FinancialPolicyAction,
    FinancialPolicyOperator,
    FinancialPolicyRule,
    FinancialPolicyScope,
    FinancialPolicySeverity,
)

from tests.policy._fixtures import (
    make_artifact,
    make_block_rule,
    make_monitor_rule,
    make_scope,
    make_thresholds,
)


class TestArtifactSchema:
    def test_valid_artifact_accepted(self) -> None:
        a = make_artifact()
        assert a.policy_id == "policy-1"

    def test_empty_rules_rejected(self) -> None:
        with pytest.raises(ValidationError):
            FinancialDeonticPolicyArtifact(
                artifact_id="x",
                policy_id="x",
                policy_version="v1",
                scope=make_scope(),
                thresholds=make_thresholds(),
                rules=(),
                signed_by="x",
                signature="x",
                artifact_hash="x",
                effective_at_ms=0,
                created_at_ms=0,
            )

    def test_missing_signature_rejected(self) -> None:
        with pytest.raises(ValidationError):
            FinancialDeonticPolicyArtifact(
                artifact_id="x",
                policy_id="x",
                policy_version="v1",
                scope=make_scope(),
                thresholds=make_thresholds(),
                rules=(make_block_rule(),),
                signed_by="x",
                signature="",
                artifact_hash="x",
                effective_at_ms=0,
                created_at_ms=0,
            )

    def test_expiry_before_effective_rejected(self) -> None:
        with pytest.raises(ValidationError):
            make_artifact(effective_at_ms=2000, expires_at_ms=1000)

    def test_artifact_frozen(self) -> None:
        a = make_artifact()
        with pytest.raises(ValidationError):
            a.policy_id = "other"  # type: ignore[misc]


class TestRuleSchema:
    @pytest.mark.parametrize(
        "bad_action",
        [
            "execute_order",
            "approve_trade",
            "submit_order",
            "live_veto",
            "clear_kill_switch",
            "set_kill_switch",
            "mutate_config",
        ],
    )
    def test_execution_ish_action_rejected_by_str_enum(self, bad_action: str) -> None:
        # The action must come from FinancialPolicyAction enum; any
        # value outside the closed set is rejected by Pydantic's
        # strict enum validation.
        with pytest.raises(ValidationError):
            FinancialPolicyRule(
                rule_id="r",
                condition_key="risk_score",
                operator=FinancialPolicyOperator.GTE,
                threshold_ref="0.5",
                output_if_triggered=bad_action,  # type: ignore[arg-type]
                severity_band=FinancialPolicySeverity.HIGH,
                rationale="t",
            )

    def test_critical_severity_cannot_output_wait(self) -> None:
        with pytest.raises(ValidationError):
            FinancialPolicyRule(
                rule_id="r",
                condition_key="risk_score",
                operator=FinancialPolicyOperator.GTE,
                threshold_ref="0.5",
                output_if_triggered=FinancialPolicyAction.CLASSIFY_WAIT,
                severity_band=FinancialPolicySeverity.CRITICAL,
                rationale="t",
            )

    def test_unknown_condition_key_rejected(self) -> None:
        with pytest.raises(ValidationError):
            FinancialPolicyRule(
                rule_id="r",
                condition_key="not_a_known_key",
                operator=FinancialPolicyOperator.GTE,
                threshold_ref="0.5",
                output_if_triggered=FinancialPolicyAction.CLASSIFY_BLOCK,
                severity_band=FinancialPolicySeverity.HIGH,
                rationale="t",
            )

    def test_rule_frozen(self) -> None:
        r = make_block_rule()
        with pytest.raises(ValidationError):
            r.rule_id = "other"  # type: ignore[misc]


class TestScopeSchema:
    def test_symbol_hash_required_when_not_all(self) -> None:
        with pytest.raises(ValidationError):
            FinancialPolicyScope(
                scope_id="s",
                environment="shadow",
                source_system="gel_al_borsa",
                applies_to_all_symbols=False,
                applies_to_all_strategies=True,
            )

    def test_symbol_hash_forbidden_when_all(self) -> None:
        with pytest.raises(ValidationError):
            FinancialPolicyScope(
                scope_id="s",
                environment="shadow",
                source_system="gel_al_borsa",
                symbol_hash="sha256:x",
                applies_to_all_symbols=True,
                applies_to_all_strategies=True,
            )


class TestThresholds:
    def test_hard_stops_pinned_true(self) -> None:
        t = make_thresholds()
        assert t.kill_switch_observed_blocks is True
        assert t.stale_data_blocks is True
        assert t.missing_provenance_blocks is True

    def test_kill_switch_observed_blocks_cannot_be_false(self) -> None:
        from sentinel.policy.financial import FinancialHardStopThresholds

        with pytest.raises(ValidationError):
            FinancialHardStopThresholds(
                max_daily_loss_pct=1.0,
                max_single_observation_risk_score=0.7,
                max_staleness_ms=1000,
                max_latency_ms=500,
                max_orderbook_age_ms=200,
                max_spread_pct=1.0,
                min_confidence=0.3,
                min_liquidity_score=0.1,
                max_bad_order_count=0,
                max_unknown_risk_score=0.5,
                kill_switch_observed_blocks=False,  # type: ignore[arg-type]
                stale_data_blocks=True,  # type: ignore[arg-type]
                bad_order_blocks=True,
                missing_provenance_blocks=True,  # type: ignore[arg-type]
            )


class TestArtifactRejectsForbiddenTopLevelKeys:
    def test_two_monitor_rule_artifact(self) -> None:
        # Building an artifact with two rules just exercises the
        # `dumped`-rescan codepath; no forbidden keys present.
        a = make_artifact(rules=(make_block_rule(), make_monitor_rule()))
        assert len(a.rules) == 2
