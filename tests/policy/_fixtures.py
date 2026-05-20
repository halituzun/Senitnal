"""Shared in-Python builders for V6 tests."""

from __future__ import annotations

from sentinel.policy.financial import (
    FinancialDeonticPolicyArtifact,
    FinancialHardStopThresholds,
    FinancialPolicyAction,
    FinancialPolicyOperator,
    FinancialPolicyRule,
    FinancialPolicyScope,
    FinancialPolicySeverity,
)


def make_scope(
    *,
    scope_id: str = "scope-1",
    environment: str = "shadow",
    venue_hash: str | None = None,
    symbol_hash: str | None = None,
    strategy_hash: str | None = None,
) -> FinancialPolicyScope:
    return FinancialPolicyScope(
        scope_id=scope_id,
        environment=environment,  # type: ignore[arg-type]
        source_system="gel_al_borsa",
        venue_hash=venue_hash,
        symbol_hash=symbol_hash,
        strategy_hash=strategy_hash,
        applies_to_all_symbols=symbol_hash is None,
        applies_to_all_strategies=strategy_hash is None,
    )


def make_thresholds() -> FinancialHardStopThresholds:
    return FinancialHardStopThresholds(
        max_daily_loss_pct=1.0,
        max_daily_loss_abs_ref=None,
        max_single_observation_risk_score=0.7,
        max_staleness_ms=1000,
        max_latency_ms=500,
        max_orderbook_age_ms=200,
        max_spread_pct=1.0,
        min_confidence=0.3,
        min_liquidity_score=0.1,
        max_bad_order_count=0,
        max_unknown_risk_score=0.5,
        bad_order_blocks=True,
    )


def make_block_rule(rule_id: str = "r-block-high-risk") -> FinancialPolicyRule:
    return FinancialPolicyRule(
        rule_id=rule_id,
        condition_key="risk_score",
        operator=FinancialPolicyOperator.GTE,
        threshold_ref="0.7",
        output_if_triggered=FinancialPolicyAction.CLASSIFY_BLOCK,
        severity_band=FinancialPolicySeverity.HIGH,
        rationale="High risk; shadow-block.",
    )


def make_monitor_rule(rule_id: str = "r-monitor-stale") -> FinancialPolicyRule:
    return FinancialPolicyRule(
        rule_id=rule_id,
        condition_key="staleness_ms",
        operator=FinancialPolicyOperator.GT,
        threshold_ref="1000",
        output_if_triggered=FinancialPolicyAction.CLASSIFY_MONITOR,
        severity_band=FinancialPolicySeverity.MEDIUM,
        rationale="Stale data; shadow-monitor.",
    )


def make_artifact(
    *,
    artifact_id: str = "art-1",
    policy_id: str = "policy-1",
    scope: FinancialPolicyScope | None = None,
    rules: tuple[FinancialPolicyRule, ...] | None = None,
    effective_at_ms: int = 1_000_000,
    expires_at_ms: int | None = None,
    human_approval_ref: str | None = "approval-1",
    previous_artifact_hash: str | None = None,
    created_at_ms: int = 1_000_000,
) -> FinancialDeonticPolicyArtifact:
    return FinancialDeonticPolicyArtifact(
        artifact_id=artifact_id,
        policy_id=policy_id,
        policy_version="v1",
        scope=scope or make_scope(),
        thresholds=make_thresholds(),
        rules=rules or (make_block_rule(), make_monitor_rule()),
        signed_by="sentinel-mock-key",
        signature="sig-mock",
        artifact_hash=f"sha256:{artifact_id}",
        previous_artifact_hash=previous_artifact_hash,
        effective_at_ms=effective_at_ms,
        expires_at_ms=expires_at_ms,
        human_approval_ref=human_approval_ref,
        rollback_ref=None,
        created_at_ms=created_at_ms,
    )
