"""V6 — Financial deontic policy schemas.

Pydantic v2, frozen, ``extra='forbid'``, strict.  All schemas are
observer-side and never propagate raw symbol/venue/strategy names —
only hashed references.  Policy actions are constrained to the closed
v0.1 ``SystemOutput`` classification set; any execution-style action
verb is rejected at construction.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Final, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

# ---------------------------------------------------------------------------
# Allowed rule condition keys (closed set).
# ---------------------------------------------------------------------------

_ALLOWED_CONDITION_KEYS: Final[frozenset[str]] = frozenset(
    {
        "risk_score",
        "confidence",
        "staleness_ms",
        "latency_ms",
        "orderbook_age_ms",
        "spread_pct",
        "liquidity_score",
        "bad_order",
        "kill_switch_active",
        "provenance_missing",
        "unknown_risk_score",
    }
)


# Artifact-level forbidden keys (defense-in-depth — payload schemas
# already use ``extra='forbid'`` but the policy artifact may be
# serialised through JSON; reject any key that would route to action).
_FORBIDDEN_ARTIFACT_KEYS: Final[frozenset[str]] = frozenset(
    {
        "api_key",
        "api_secret",
        "secret",
        "private_key",
        "account_id",
        "balance",
        "position",
        "order_command",
        "execute_command",
        "approve_trade",
        "reject_trade",
        "mutate_threshold",
        "set_kill_switch",
        "clear_kill_switch",
        "direct_order",
        "symbol",
        "venue",
        "strategy_name",
    }
)


# Action-value forbidden tokens (case-insensitive).  Any of these in
# the action value text rejects the rule at construction.
_FORBIDDEN_ACTION_TOKENS: Final[tuple[str, ...]] = (
    "execute",
    "approve",
    "submit",
    "_real",
    "live_veto",
    "clear_kill_switch",
    "set_kill_switch",
    "mutate_config",
    "trade",
)


# ---------------------------------------------------------------------------
# Closed enums
# ---------------------------------------------------------------------------


class FinancialPolicyAction(StrEnum):
    """Closed shadow-classification action set.

    Each value maps 1:1 to a closed ``SystemOutput``.  No execution
    verb is permitted.
    """

    CLASSIFY_WAIT = "classify_wait"
    CLASSIFY_MONITOR = "classify_monitor"
    CLASSIFY_BLOCK = "classify_block"
    CLASSIFY_NEED_RECALL = "classify_need_recall"
    CLASSIFY_NO_ACTION = "classify_no_action"


class FinancialPolicyOperator(StrEnum):
    """Closed comparison operator set for rule conditions."""

    LT = "lt"
    LTE = "lte"
    GT = "gt"
    GTE = "gte"
    EQ = "eq"
    NEQ = "neq"
    EXISTS = "exists"
    MISSING = "missing"


class FinancialPolicySeverity(StrEnum):
    """Closed rule severity band."""

    ROUTINE = "routine"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ---------------------------------------------------------------------------
# Scope
# ---------------------------------------------------------------------------


class FinancialPolicyScope(BaseModel):
    """Hashed scope identifier for a policy.

    No raw symbol / venue / strategy names — only hashed references.
    ``environment`` is observational; ``live`` is permitted as a label
    but never grants action permission.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    scope_id: str = Field(min_length=1)
    environment: Literal["local", "shadow", "paper", "canary", "live"]
    source_system: str = Field(min_length=1)
    venue_hash: str | None = None
    symbol_hash: str | None = None
    strategy_hash: str | None = None
    applies_to_all_symbols: bool
    applies_to_all_strategies: bool

    @model_validator(mode="after")
    def _validate_scope(self) -> Self:
        if self.applies_to_all_symbols and self.symbol_hash is not None:
            raise ValueError("symbol_hash must be None when applies_to_all_symbols=True")
        if not self.applies_to_all_symbols and self.symbol_hash is None:
            raise ValueError("symbol_hash required when applies_to_all_symbols=False")
        if self.applies_to_all_strategies and self.strategy_hash is not None:
            raise ValueError("strategy_hash must be None when applies_to_all_strategies=True")
        if not self.applies_to_all_strategies and self.strategy_hash is None:
            raise ValueError("strategy_hash required when applies_to_all_strategies=False")
        return self


# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------


class FinancialHardStopThresholds(BaseModel):
    """Per-policy hard-stop threshold table.

    Constitutional hard-stops (``kill_switch_observed_blocks``,
    ``stale_data_blocks``, ``missing_provenance_blocks``) must remain
    True at the policy artifact layer.  A V6 policy cannot weaken
    them.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    max_daily_loss_pct: float = Field(ge=0.0, allow_inf_nan=False)
    max_daily_loss_abs_ref: str | None = None
    max_single_observation_risk_score: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    max_staleness_ms: int = Field(ge=0)
    max_latency_ms: int = Field(ge=0)
    max_orderbook_age_ms: int = Field(ge=0)
    max_spread_pct: float = Field(ge=0.0, allow_inf_nan=False)
    min_confidence: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    min_liquidity_score: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    max_bad_order_count: int = Field(ge=0)
    max_unknown_risk_score: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    kill_switch_observed_blocks: Literal[True] = True
    stale_data_blocks: Literal[True] = True
    bad_order_blocks: bool = True
    missing_provenance_blocks: Literal[True] = True


# ---------------------------------------------------------------------------
# Rule
# ---------------------------------------------------------------------------


def _assert_action_token_safe(value: str) -> None:
    lowered = value.lower()
    for token in _FORBIDDEN_ACTION_TOKENS:
        if token in lowered:
            raise ValueError(
                f"policy action {value!r} contains forbidden token {token!r}; "
                "policies cannot express execution"
            )


class FinancialPolicyRule(BaseModel):
    """One rule in a financial policy artifact."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    rule_id: str = Field(min_length=1)
    condition_key: str = Field(min_length=1)
    operator: FinancialPolicyOperator
    threshold_ref: str = Field(min_length=1)
    output_if_triggered: FinancialPolicyAction
    severity_band: FinancialPolicySeverity
    rationale: str = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_rule(self) -> Self:
        if self.condition_key not in _ALLOWED_CONDITION_KEYS:
            raise ValueError(
                f"condition_key {self.condition_key!r} not in allowed set; "
                f"allowed: {sorted(_ALLOWED_CONDITION_KEYS)}"
            )
        _assert_action_token_safe(self.output_if_triggered.value)
        if (
            self.severity_band is FinancialPolicySeverity.CRITICAL
            and self.output_if_triggered is FinancialPolicyAction.CLASSIFY_WAIT
        ):
            raise ValueError("critical severity rule cannot output classify_wait")
        return self


# ---------------------------------------------------------------------------
# Artifact
# ---------------------------------------------------------------------------


def _assert_no_forbidden_artifact_keys(payload: dict[str, object]) -> None:
    bad = sorted(k for k in payload if k in _FORBIDDEN_ARTIFACT_KEYS)
    if bad:
        raise ValueError(
            f"forbidden policy artifact key(s) present: {bad}; "
            "policies cannot carry credentials, account state, or execution instructions"
        )


class FinancialDeonticPolicyArtifact(BaseModel):
    """Signed financial deontic policy artifact.

    Activation requires (out-of-band):
        - status promoted to VERIFIED via integration layer
        - human_approval_ref populated
        - activated through ``InMemoryPolicyStore.activate_verified_policy``
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    artifact_id: str = Field(min_length=1)
    policy_id: str = Field(min_length=1)
    policy_version: str = Field(min_length=1)
    scope: FinancialPolicyScope
    thresholds: FinancialHardStopThresholds
    rules: tuple[FinancialPolicyRule, ...]
    signed_by: str = Field(min_length=1)
    signature: str = Field(min_length=1)
    artifact_hash: str = Field(min_length=1)
    previous_artifact_hash: str | None = None
    effective_at_ms: int = Field(ge=0)
    expires_at_ms: int | None = None
    human_approval_ref: str | None = None
    rollback_ref: str | None = None
    created_at_ms: int = Field(ge=0)

    @model_validator(mode="after")
    def _validate_artifact(self) -> Self:
        if not self.rules:
            raise ValueError("policy artifact must contain at least one rule")
        if self.expires_at_ms is not None and self.expires_at_ms <= self.effective_at_ms:
            raise ValueError(
                f"expires_at_ms ({self.expires_at_ms}) must be > effective_at_ms "
                f"({self.effective_at_ms})"
            )
        # Defense-in-depth: dump and rescan top-level keys.
        dumped = self.model_dump(mode="python")
        _assert_no_forbidden_artifact_keys(dumped)
        return self
