"""V6 — Financial deontic policy shadow evaluator.

Pure functions only.  Maps a ``FinancialPolicyInput`` against an
ACTIVE deontic-policy ``MemoryRecord`` and returns a
``FinancialPolicyEvaluation`` carrying a closed v0.1 ``SystemOutput``
value.

Constitutional discipline:
    - Evaluation is shadow-only: ``shadow_only=True``,
      ``creates_action=False``, ``writes_external=False`` are pinned
      via ``Literal[True/False]`` defaults.
    - Reason strings pass ``assert_no_forbidden_literal``.
    - No execution intent constructed.  No M2 write.  No Gel.Al write.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal

from pydantic import BaseModel, ConfigDict, Field

from sentinel.policy.financial import (
    FinancialDeonticPolicyArtifact,
    FinancialPolicyAction,
    FinancialPolicyOperator,
    FinancialPolicyRule,
    FinancialPolicySeverity,
)
from sentinel.policy.store import parse_artifact_from_record
from sentinel.runtime.output import SystemOutput, assert_no_forbidden_literal
from sentinel.types.memory import MemoryRecord, MemoryRecordStatus, SubjectClass

_ACTION_TO_OUTPUT: Final[dict[FinancialPolicyAction, SystemOutput]] = {
    FinancialPolicyAction.CLASSIFY_WAIT: SystemOutput.WAIT,
    FinancialPolicyAction.CLASSIFY_MONITOR: SystemOutput.MONITOR,
    FinancialPolicyAction.CLASSIFY_BLOCK: SystemOutput.BLOCK,
    FinancialPolicyAction.CLASSIFY_NEED_RECALL: SystemOutput.NEED_RECALL,
    FinancialPolicyAction.CLASSIFY_NO_ACTION: SystemOutput.NO_ACTION,
}

_SEVERITY_RANK: Final[dict[FinancialPolicySeverity, int]] = {
    FinancialPolicySeverity.ROUTINE: 0,
    FinancialPolicySeverity.LOW: 1,
    FinancialPolicySeverity.MEDIUM: 2,
    FinancialPolicySeverity.HIGH: 3,
    FinancialPolicySeverity.CRITICAL: 4,
}

_OUTPUT_RANK: Final[dict[SystemOutput, int]] = {
    SystemOutput.WAIT: 0,
    SystemOutput.NO_ACTION: 1,
    SystemOutput.NEED_RECALL: 2,
    SystemOutput.MONITOR: 3,
    SystemOutput.BLOCK: 4,
}


# Default staleness window for policy artifacts (30 days).
_DEFAULT_POLICY_STALENESS_MS: Final[int] = 30 * 24 * 3600 * 1000


# ---------------------------------------------------------------------------
# Input / output schemas
# ---------------------------------------------------------------------------


class FinancialPolicyInput(BaseModel):
    """Abstract per-event signals for policy evaluation.

    No raw symbol / venue / strategy / account fields.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    event_id: str = Field(min_length=1)
    scope_id: str = Field(min_length=1)
    environment: Literal["local", "shadow", "paper", "canary", "live"]
    risk_score: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    confidence: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    staleness_ms: int = Field(ge=0)
    latency_ms: int = Field(ge=0)
    orderbook_age_ms: int = Field(ge=0)
    spread_pct: float = Field(ge=0.0, allow_inf_nan=False)
    liquidity_score: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    bad_order: bool
    kill_switch_active: bool
    provenance_missing: bool
    unknown_risk_score: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    source_event_refs: tuple[str, ...]

    def model_post_init(self, __context: object, /) -> None:
        if not self.source_event_refs:
            raise ValueError("source_event_refs must be non-empty")

    def get_value(self, key: str) -> object:
        """Lookup a condition key from the input scalars."""
        return getattr(self, key, None)


@dataclass(frozen=True, slots=True)
class FinancialPolicyEvaluation:
    """Result of one policy evaluation pass.

    ``shadow_only`` / ``creates_action`` / ``writes_external`` are
    pinned via Literal types — any instantiation that flips them is
    a type error.
    """

    input_event_id: str
    policy_id: str
    policy_record_id: str
    triggered_rule_ids: tuple[str, ...]
    output: SystemOutput
    severity_band: FinancialPolicySeverity
    reason: str
    shadow_only: Literal[True] = True
    creates_action: Literal[False] = False
    writes_external: Literal[False] = False

    def __post_init__(self) -> None:
        assert_no_forbidden_literal(self.reason)
        if self.shadow_only is not True:
            raise ValueError("FinancialPolicyEvaluation.shadow_only must be True")
        if self.creates_action is not False:
            raise ValueError("FinancialPolicyEvaluation.creates_action must be False")
        if self.writes_external is not False:
            raise ValueError("FinancialPolicyEvaluation.writes_external must be False")


# ---------------------------------------------------------------------------
# Staleness / expiry helpers
# ---------------------------------------------------------------------------


def _artifact_of(record: MemoryRecord) -> FinancialDeonticPolicyArtifact:
    return parse_artifact_from_record(record)


def is_policy_expired(record: MemoryRecord, now_ms: int) -> bool:
    """True iff the artifact's expires_at_ms has been reached."""
    artifact = _artifact_of(record)
    if artifact.expires_at_ms is None:
        return False
    return artifact.expires_at_ms <= now_ms


def is_policy_stale(
    record: MemoryRecord,
    now_ms: int,
    *,
    max_age_ms: int = _DEFAULT_POLICY_STALENESS_MS,
) -> bool:
    """True iff the artifact's effective_at_ms is older than max_age_ms."""
    artifact = _artifact_of(record)
    return (now_ms - artifact.effective_at_ms) > max_age_ms


# ---------------------------------------------------------------------------
# Rule firing
# ---------------------------------------------------------------------------


def _operator_matches(
    operator: FinancialPolicyOperator,
    value: object,
    threshold_text: str,
) -> bool:
    if operator is FinancialPolicyOperator.EXISTS:
        return value is not None
    if operator is FinancialPolicyOperator.MISSING:
        return value is None
    if value is None:
        return False
    if isinstance(value, bool):
        # Threshold encoded as "true"/"false" or numeric 1/0.
        rhs_text = threshold_text.strip().lower()
        if rhs_text in {"true", "1"}:
            rhs = True
        elif rhs_text in {"false", "0"}:
            rhs = False
        else:
            return False
        if operator is FinancialPolicyOperator.EQ:
            return value is rhs
        if operator is FinancialPolicyOperator.NEQ:
            return value is not rhs
        return False
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        try:
            rhs_num = float(threshold_text)
        except ValueError:
            return False
        lhs = float(value)
        if operator is FinancialPolicyOperator.LT:
            return lhs < rhs_num
        if operator is FinancialPolicyOperator.LTE:
            return lhs <= rhs_num
        if operator is FinancialPolicyOperator.GT:
            return lhs > rhs_num
        if operator is FinancialPolicyOperator.GTE:
            return lhs >= rhs_num
        if operator is FinancialPolicyOperator.EQ:
            return lhs == rhs_num
        if operator is FinancialPolicyOperator.NEQ:
            return lhs != rhs_num
    return False


def _rule_fires(rule: FinancialPolicyRule, policy_input: FinancialPolicyInput) -> bool:
    value = policy_input.get_value(rule.condition_key)
    return _operator_matches(rule.operator, value, rule.threshold_ref)


# ---------------------------------------------------------------------------
# Evaluator
# ---------------------------------------------------------------------------


def evaluate_financial_policy(
    *,
    policy_record: MemoryRecord,
    policy_input: FinancialPolicyInput,
    now_ms: int | None = None,
) -> FinancialPolicyEvaluation:
    """Evaluate ``policy_input`` against an ACTIVE policy record.

    Constitutional hard-stops apply first (kill_switch_active,
    provenance_missing).  Then per-rule triggers are evaluated.  The
    final output is the highest-ranked SystemOutput across triggered
    rules.
    """
    if policy_record.subject_class is not SubjectClass.DEONTIC_POLICY:
        raise ValueError(
            f"policy_record must be DEONTIC_POLICY; got {policy_record.subject_class.value!r}"
        )
    if policy_record.status is not MemoryRecordStatus.ACTIVE:
        raise ValueError(
            f"policy_record must be ACTIVE to evaluate; got {policy_record.status.value!r}"
        )

    artifact = _artifact_of(policy_record)
    if now_ms is not None:
        if artifact.expires_at_ms is not None and artifact.expires_at_ms <= now_ms:
            raise ValueError(
                f"policy {artifact.policy_id!r} is expired (expires_at_ms="
                f"{artifact.expires_at_ms}, now_ms={now_ms})"
            )
        if (now_ms - artifact.effective_at_ms) > _DEFAULT_POLICY_STALENESS_MS:
            raise ValueError(
                f"policy {artifact.policy_id!r} is stale; effective_at_ms="
                f"{artifact.effective_at_ms}, now_ms={now_ms}, max age "
                f"{_DEFAULT_POLICY_STALENESS_MS}ms"
            )

    triggered: list[FinancialPolicyRule] = []

    # Constitutional hard-stops first.  Always emit a synthetic
    # "constitutional" rule reference for audit clarity.
    if policy_input.kill_switch_active and artifact.thresholds.kill_switch_observed_blocks:
        return FinancialPolicyEvaluation(
            input_event_id=policy_input.event_id,
            policy_id=artifact.policy_id,
            policy_record_id=policy_record.record_id,
            triggered_rule_ids=("constitutional:kill_switch_active",),
            output=SystemOutput.BLOCK,
            severity_band=FinancialPolicySeverity.CRITICAL,
            reason="policy hard-stop: kill-switch active observed; shadow BLOCK",
        )
    if policy_input.provenance_missing and artifact.thresholds.missing_provenance_blocks:
        return FinancialPolicyEvaluation(
            input_event_id=policy_input.event_id,
            policy_id=artifact.policy_id,
            policy_record_id=policy_record.record_id,
            triggered_rule_ids=("constitutional:provenance_missing",),
            output=SystemOutput.BLOCK,
            severity_band=FinancialPolicySeverity.CRITICAL,
            reason="policy hard-stop: missing provenance; shadow BLOCK",
        )
    if policy_input.bad_order and artifact.thresholds.bad_order_blocks:
        return FinancialPolicyEvaluation(
            input_event_id=policy_input.event_id,
            policy_id=artifact.policy_id,
            policy_record_id=policy_record.record_id,
            triggered_rule_ids=("constitutional:bad_dispatch",),
            output=SystemOutput.BLOCK,
            severity_band=FinancialPolicySeverity.CRITICAL,
            reason="policy hard-stop: venue actuation flagged bad; shadow BLOCK",
        )

    for rule in artifact.rules:
        if _rule_fires(rule, policy_input):
            triggered.append(rule)

    if not triggered:
        return FinancialPolicyEvaluation(
            input_event_id=policy_input.event_id,
            policy_id=artifact.policy_id,
            policy_record_id=policy_record.record_id,
            triggered_rule_ids=(),
            output=SystemOutput.WAIT,
            severity_band=FinancialPolicySeverity.ROUTINE,
            reason="policy nominal: no rule triggered; shadow WAIT",
        )

    # Pick the highest-ranked (output, severity) tuple.
    def _key(rule: FinancialPolicyRule) -> tuple[int, int, str]:
        out = _ACTION_TO_OUTPUT[rule.output_if_triggered]
        return (_OUTPUT_RANK[out], _SEVERITY_RANK[rule.severity_band], rule.rule_id)

    winner = max(triggered, key=_key)
    winner_output = _ACTION_TO_OUTPUT[winner.output_if_triggered]
    return FinancialPolicyEvaluation(
        input_event_id=policy_input.event_id,
        policy_id=artifact.policy_id,
        policy_record_id=policy_record.record_id,
        triggered_rule_ids=tuple(r.rule_id for r in triggered),
        output=winner_output,
        severity_band=winner.severity_band,
        reason=f"policy classification: rules triggered={len(triggered)}; shadow {winner_output.value}",
    )


# ---------------------------------------------------------------------------
# Conflict resolution
# ---------------------------------------------------------------------------


def resolve_policy_conflicts(
    evaluations: tuple[FinancialPolicyEvaluation, ...],
) -> FinancialPolicyEvaluation:
    """Return the winning evaluation under deterministic precedence.

    Precedence: BLOCK > MONITOR > NEED_RECALL > NO_ACTION > WAIT.
    Ties broken by ``policy_id`` ascending, then by triggered rule
    count ascending, then by ``policy_record_id`` ascending.
    """
    if not evaluations:
        raise ValueError("resolve_policy_conflicts requires at least one evaluation")

    def _key(e: FinancialPolicyEvaluation) -> tuple[int, int, str, int, str]:
        return (
            _OUTPUT_RANK[e.output],
            _SEVERITY_RANK[e.severity_band],
            e.policy_id,
            len(e.triggered_rule_ids),
            e.policy_record_id,
        )

    return max(evaluations, key=_key)
