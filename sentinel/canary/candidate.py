"""V8 — Canary candidate action schemas.

Frozen Pydantic v2 models.  Raw symbol / venue / strategy / order /
account / API-key fields and Gel.Al-side execution payload fields
(redis_stream, orders_pending_payload, order_command, ...) are
rejected at construction.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Final, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CanaryCandidateSource(StrEnum):
    """Closed source enum for canary candidate actions."""

    GELAL_SHADOW = "gelal_shadow"
    GELAL_PAPER = "gelal_paper"
    LOCAL_FIXTURE = "local_fixture"
    SYNTHETIC_MARKET = "synthetic_market"
    MANUAL_FIXTURE = "manual_fixture"


class CanaryEnvironment(StrEnum):
    """Closed observed-environment enum.

    ``micro_live_canary`` is an observed environment label only; it
    grants no execution authority.
    """

    LOCAL = "local"
    SHADOW = "shadow"
    PAPER = "paper"
    MICRO_LIVE_CANARY = "micro_live_canary"


# Documented denylist of forbidden top-level field names.  Pydantic
# ``extra='forbid'`` already blocks unknown attributes; the explicit
# list documents constitutional intent and is referenced by tests.
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
        "order_command",
        "execute_command",
        "redis_stream",
        "orders_pending_payload",
    }
)


class CanaryCandidateAction(BaseModel):
    """Observed Gel.Al-side candidate action.

    This record represents a candidate action *observed by Sentinel*.
    It is NOT a Sentinel-produced action and grants no execution
    authority.  Raw domain labels are forbidden; ``scope_hash`` and
    optional hashed strategy / symbol / venue refs carry only opaque
    identifiers.

    ``notional_ref`` is an opaque reference (e.g. ``"tier:micro"``);
    raw notional amounts must be replaced upstream with a tier label
    so that Sentinel never observes the live sizing scalar.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    candidate_id: str = Field(min_length=1)
    source: CanaryCandidateSource
    environment: CanaryEnvironment
    observed_at_ms: int = Field(ge=0)
    expires_at_ms: int = Field(ge=0)
    source_event_refs: tuple[str, ...]
    provenance_hash: str = Field(min_length=1)
    scope_hash: str = Field(min_length=1)
    strategy_hash: str | None = None
    symbol_hash: str | None = None
    venue_hash: str | None = None
    notional_ref: str = Field(min_length=1)
    risk_score: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    confidence: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    staleness_ms: int = Field(ge=0)
    latency_ms: int = Field(ge=0)
    orderbook_age_ms: int = Field(ge=0)
    spread_pct: float = Field(ge=0.0, allow_inf_nan=False)
    liquidity_score: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    expected_net_edge_pct: float = Field(allow_inf_nan=False)
    expected_slippage_pct: float = Field(ge=0.0, allow_inf_nan=False)
    expected_fee_pct: float = Field(ge=0.0, allow_inf_nan=False)
    gelal_policy_ref: str | None = None
    paper_decision_ref: str | None = None

    @model_validator(mode="after")
    def _validate_candidate(self) -> Self:
        if self.expires_at_ms <= self.observed_at_ms:
            raise ValueError(
                f"expires_at_ms ({self.expires_at_ms}) must be > observed_at_ms "
                f"({self.observed_at_ms})"
            )
        if not self.source_event_refs:
            raise ValueError("source_event_refs must be non-empty")
        return self


__all__ = [
    "CanaryCandidateAction",
    "CanaryCandidateSource",
    "CanaryEnvironment",
]
