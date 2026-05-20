"""V9 — Limited live governance scope schema."""

from __future__ import annotations

from enum import StrEnum
from typing import Final, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class GovernanceEnvironment(StrEnum):
    """Closed observed governance environment enum."""

    LOCAL = "local"
    SHADOW = "shadow"
    PAPER = "paper"
    MICRO_LIVE_CANARY = "micro_live_canary"
    LIMITED_LIVE = "limited_live"


class GovernanceScopeKind(StrEnum):
    """Closed scope-kind enum for a governance scope."""

    SYMBOL_SCOPE = "symbol_scope"
    STRATEGY_SCOPE = "strategy_scope"
    VENUE_SCOPE = "venue_scope"
    GLOBAL_MICRO_SCOPE = "global_micro_scope"
    INCIDENT_SCOPE = "incident_scope"
    EMERGENCY_SCOPE = "emergency_scope"


_FORBIDDEN_FIELD_NAMES: Final[frozenset[str]] = frozenset(
    {
        "symbol",
        "venue",
        "exchange",
        "strategy_name",
        "side",
        "order_side",
        "order_type",
        "amount",
        "quantity",
        "qty",
        "api_key",
        "api_secret",
        "secret",
        "balance",
        "position",
        "leverage",
        "take_profit",
        "stop_loss",
        "trade_intent",
        "strategy_action",
        "execution_hint",
        "account_id",
        "wallet",
        "direct_order",
        "approve_trade",
        "reject_trade",
        "set_kill_switch",
        "clear_kill_switch",
        "orders_pending_payload",
    }
)


class LimitedLiveGovernanceScope(BaseModel):
    """Hashed scope for a limited-live governance evaluation.

    For ``environment=limited_live`` the five fail-closed flags are
    pinned ``Literal[True]``.  Raw symbol / venue / strategy names
    are rejected at construction.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    scope_id: str = Field(min_length=1)
    environment: GovernanceEnvironment
    scope_kind: GovernanceScopeKind
    source_system: Literal["gel_al_borsa"] = "gel_al_borsa"
    symbol_hash: str | None = None
    venue_hash: str | None = None
    strategy_hash: str | None = None
    applies_to_all_symbols: bool
    applies_to_all_strategies: bool
    max_candidates_per_hour: int = Field(ge=0, le=10000)
    max_live_impacting_blocks_per_hour: int = Field(ge=0, le=10000)
    max_governance_latency_ms: int = Field(ge=0)
    fail_closed_on_missing_policy: Literal[True] = True
    fail_closed_on_missing_human_approval: Literal[True] = True
    fail_closed_on_timeout: Literal[True] = True
    fail_closed_on_hash_failure: Literal[True] = True
    human_approval_required: Literal[True] = True
    created_at_ms: int = Field(ge=0)
    expires_at_ms: int | None = None

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
        if self.expires_at_ms is not None and self.expires_at_ms <= self.created_at_ms:
            raise ValueError(
                f"expires_at_ms ({self.expires_at_ms}) must be > created_at_ms "
                f"({self.created_at_ms})"
            )
        return self


__all__ = [
    "GovernanceEnvironment",
    "GovernanceScopeKind",
    "LimitedLiveGovernanceScope",
]
