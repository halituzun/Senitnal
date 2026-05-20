"""V6 — Policy evaluator tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from sentinel.policy.evaluator import (
    FinancialPolicyEvaluation,
    FinancialPolicyInput,
    evaluate_financial_policy,
    is_policy_expired,
    resolve_policy_conflicts,
)
from sentinel.policy.financial import FinancialPolicySeverity
from sentinel.policy.record_builder import build_deontic_policy_candidate_record
from sentinel.runtime.output import SystemOutput
from sentinel.types.memory import MemoryRecord, MemoryRecordStatus
from sentinel.types.neural_seed import ProvenanceRef

from tests.policy._fixtures import make_artifact


def _active_record(artifact_id: str = "art-1", expires_at_ms: int | None = None) -> MemoryRecord:
    rec = build_deontic_policy_candidate_record(
        artifact=make_artifact(artifact_id=artifact_id, expires_at_ms=expires_at_ms),
        provenance=ProvenanceRef(source_event_id=f"ev-{artifact_id}"),
        created_at_ms=1_000_000,
        evidence_refs=("approval",),
    )
    return rec.model_copy(update={"status": MemoryRecordStatus.ACTIVE})


def _input(
    *,
    risk_score: float = 0.1,
    confidence: float = 0.7,
    staleness_ms: int = 50,
    bad_order: bool = False,
    kill_switch_active: bool = False,
    provenance_missing: bool = False,
) -> FinancialPolicyInput:
    return FinancialPolicyInput(
        event_id="evt-1",
        scope_id="scope-1",
        environment="shadow",
        risk_score=risk_score,
        confidence=confidence,
        staleness_ms=staleness_ms,
        latency_ms=30,
        orderbook_age_ms=10,
        spread_pct=0.05,
        liquidity_score=0.5,
        bad_order=bad_order,
        kill_switch_active=kill_switch_active,
        provenance_missing=provenance_missing,
        unknown_risk_score=0.1,
        source_event_refs=("evt-1",),
    )


class TestEvaluator:
    def test_active_policy_evaluates(self) -> None:
        ev = evaluate_financial_policy(
            policy_record=_active_record(),
            policy_input=_input(),
        )
        assert isinstance(ev, FinancialPolicyEvaluation)
        assert ev.output in {
            SystemOutput.WAIT,
            SystemOutput.MONITOR,
            SystemOutput.NEED_RECALL,
            SystemOutput.NO_ACTION,
            SystemOutput.BLOCK,
        }

    def test_candidate_cannot_evaluate(self) -> None:
        candidate = build_deontic_policy_candidate_record(
            artifact=make_artifact(),
            provenance=ProvenanceRef(source_event_id="ev-1"),
            created_at_ms=1_000_000,
            evidence_refs=("approval",),
        )
        with pytest.raises(ValueError, match="ACTIVE"):
            evaluate_financial_policy(policy_record=candidate, policy_input=_input())

    def test_verified_not_active_cannot_evaluate(self) -> None:
        verified = build_deontic_policy_candidate_record(
            artifact=make_artifact(),
            provenance=ProvenanceRef(source_event_id="ev-1"),
            created_at_ms=1_000_000,
            evidence_refs=("approval",),
        ).model_copy(update={"status": MemoryRecordStatus.VERIFIED})
        with pytest.raises(ValueError, match="ACTIVE"):
            evaluate_financial_policy(policy_record=verified, policy_input=_input())

    def test_kill_switch_active_blocks(self) -> None:
        ev = evaluate_financial_policy(
            policy_record=_active_record(),
            policy_input=_input(kill_switch_active=True),
        )
        assert ev.output is SystemOutput.BLOCK
        assert ev.severity_band is FinancialPolicySeverity.CRITICAL

    def test_provenance_missing_blocks(self) -> None:
        ev = evaluate_financial_policy(
            policy_record=_active_record(),
            policy_input=_input(provenance_missing=True),
        )
        assert ev.output is SystemOutput.BLOCK

    def test_bad_order_blocks(self) -> None:
        ev = evaluate_financial_policy(
            policy_record=_active_record(),
            policy_input=_input(bad_order=True),
        )
        assert ev.output is SystemOutput.BLOCK

    def test_high_risk_score_triggers_rule(self) -> None:
        ev = evaluate_financial_policy(
            policy_record=_active_record(),
            policy_input=_input(risk_score=0.95),
        )
        assert ev.output is SystemOutput.BLOCK
        assert "r-block-high-risk" in ev.triggered_rule_ids

    def test_no_rule_triggered_wait(self) -> None:
        ev = evaluate_financial_policy(
            policy_record=_active_record(),
            policy_input=_input(risk_score=0.1, staleness_ms=10, confidence=0.8),
        )
        assert ev.output is SystemOutput.WAIT
        assert ev.triggered_rule_ids == ()

    def test_shadow_only_pinned(self) -> None:
        ev = evaluate_financial_policy(
            policy_record=_active_record(),
            policy_input=_input(),
        )
        assert ev.shadow_only is True
        assert ev.creates_action is False
        assert ev.writes_external is False

    def test_reason_no_forbidden_literals(self) -> None:
        for input_kwargs in (
            {"kill_switch_active": True},
            {"bad_order": True},
            {"risk_score": 0.95},
            {"staleness_ms": 5000},
        ):
            ev = evaluate_financial_policy(
                policy_record=_active_record(),
                policy_input=_input(**input_kwargs),  # type: ignore[arg-type]
            )
            lowered = ev.reason.lower()
            for needle in ("buy", "sell", "execute", "order", "submit", "_real"):
                assert needle not in lowered, (
                    f"forbidden literal {needle!r} in reason {ev.reason!r}"
                )

    def test_no_approved_action_intent_in_evaluator_source(self) -> None:
        from sentinel.policy import evaluator

        src = Path(evaluator.__file__).read_text(encoding="utf-8")
        assert "ApprovedActionIntent" not in src

    def test_expired_policy_rejected(self) -> None:
        rec = _active_record(artifact_id="exp", expires_at_ms=2_000_000)
        with pytest.raises(ValueError, match="expired"):
            evaluate_financial_policy(policy_record=rec, policy_input=_input(), now_ms=3_000_000)

    def test_is_policy_expired(self) -> None:
        rec = _active_record(artifact_id="x", expires_at_ms=2_000_000)
        assert is_policy_expired(rec, now_ms=1_000_000) is False
        assert is_policy_expired(rec, now_ms=3_000_000) is True


class TestConflictResolution:
    def _ev(
        self,
        output: SystemOutput,
        severity: FinancialPolicySeverity = FinancialPolicySeverity.HIGH,
        policy_id: str = "p1",
        record_id: str = "r1",
        rule_ids: tuple[str, ...] = ("r-1",),
    ) -> FinancialPolicyEvaluation:
        return FinancialPolicyEvaluation(
            input_event_id="evt",
            policy_id=policy_id,
            policy_record_id=record_id,
            triggered_rule_ids=rule_ids,
            output=output,
            severity_band=severity,
            reason=f"policy classification: rules triggered={len(rule_ids)}; shadow {output.value}",
        )

    def test_block_dominates_monitor(self) -> None:
        a = self._ev(SystemOutput.MONITOR, policy_id="p1", record_id="r1")
        b = self._ev(SystemOutput.BLOCK, policy_id="p2", record_id="r2")
        winner = resolve_policy_conflicts((a, b))
        assert winner.output is SystemOutput.BLOCK

    def test_monitor_dominates_wait(self) -> None:
        a = self._ev(SystemOutput.WAIT, policy_id="p1", record_id="r1")
        b = self._ev(SystemOutput.MONITOR, policy_id="p2", record_id="r2")
        winner = resolve_policy_conflicts((a, b))
        assert winner.output is SystemOutput.MONITOR

    def test_deterministic_tie_break(self) -> None:
        a = self._ev(SystemOutput.BLOCK, policy_id="z-policy", record_id="r-a")
        b = self._ev(SystemOutput.BLOCK, policy_id="a-policy", record_id="r-b")
        # Same severity + same output; tie-break by policy_id ascending,
        # and the "max" picks the larger policy_id deterministically.
        winner = resolve_policy_conflicts((a, b))
        assert winner.policy_id == "z-policy"

    def test_empty_rejected(self) -> None:
        with pytest.raises(ValueError, match="at least one"):
            resolve_policy_conflicts(())
