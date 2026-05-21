"""V11 — Real live activation path.

Halit-approved capital model.  100 TRY hardcoded cap is removed;
capital is fully config-driven.  Sentinel does NOT execute; this
module produces a closed activation status that Gel.Al's engine
can read.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class LiveBudgetMode(StrEnum):
    """Closed set of approved capital modes."""

    FIXED_TRY = "FIXED_TRY"
    PERCENT_AVAILABLE = "PERCENT_AVAILABLE"
    ALL_AVAILABLE_BALANCE = "ALL_AVAILABLE_BALANCE"


class LiveActivationStatus(StrEnum):
    """Closed set of live activation statuses."""

    READY_FOR_REAL_LIVE_WAITING_APPROVAL = "READY_FOR_REAL_LIVE_WAITING_APPROVAL"
    CONTROLLED_REAL_LIVE_ACTIVE = "CONTROLLED_REAL_LIVE_ACTIVE"
    REAL_LIVE_ACTIVE_WAITING_FOR_EDGE = "REAL_LIVE_ACTIVE_WAITING_FOR_EDGE"
    FIRST_REAL_LIVE_ORDER_CONFIRMED = "FIRST_REAL_LIVE_ORDER_CONFIRMED"
    ROLLBACK_REQUIRED = "ROLLBACK_REQUIRED"
    BLOCKED = "BLOCKED"


class LiveCapitalModel(BaseModel, frozen=True, extra="forbid"):
    """Halit-approved capital model."""

    mode: LiveBudgetMode
    approved_capital_try: float = Field(ge=0.0, default=0.0)
    approved_capital_percent: float = Field(ge=0.0, le=100.0, default=0.0)
    max_entry_try: float = Field(ge=0.0)
    max_trades_per_day: int = Field(ge=0)
    max_open_orders: int = Field(ge=0)
    max_daily_loss_try: float = Field(ge=0.0)

    @model_validator(mode="after")
    def _mode_requires_value(self) -> LiveCapitalModel:
        if self.mode is LiveBudgetMode.FIXED_TRY and self.approved_capital_try <= 0:
            raise ValueError("FIXED_TRY mode requires approved_capital_try > 0")
        if self.mode is LiveBudgetMode.PERCENT_AVAILABLE and self.approved_capital_percent <= 0:
            raise ValueError("PERCENT_AVAILABLE mode requires approved_capital_percent > 0")
        return self


class LiveActivationInput(BaseModel, frozen=True, extra="forbid"):
    """Inputs to the live activation decision."""

    activation_id: str = Field(min_length=1)
    capital_model: LiveCapitalModel
    halit_approval_present: bool
    kill_switch_active: bool
    hash_chain_valid: bool
    available_balance_try: float = Field(ge=0.0)
    qualifying_edge_present: bool
    last_order_finality_known: bool
    bad_order_observed: bool
    stale_data_observed: bool
    confirmed_first_real_order: bool = False


class LiveActivationResult(BaseModel, frozen=True, extra="forbid"):
    """Closed-status activation result."""

    activation_id: str
    status: LiveActivationStatus
    allowed_capital_try: float = Field(ge=0.0)
    block_reasons: tuple[str, ...] = Field(default_factory=tuple)


def evaluate_live_activation(inp: LiveActivationInput) -> LiveActivationResult:
    """Determine the live activation status.

    Hardcoded 100 TRY cap is intentionally absent; capital is
    `capital_model`-driven.
    """
    reasons: list[str] = []

    # Hard blockers.
    if inp.bad_order_observed:
        reasons.append("bad_order_observed")
    if inp.stale_data_observed:
        reasons.append("stale_data_observed")
    if not inp.last_order_finality_known:
        reasons.append("unknown_finality")
    if inp.kill_switch_active:
        reasons.append("kill_switch_active")
    if not inp.hash_chain_valid:
        reasons.append("hash_chain_invalid")

    if inp.bad_order_observed or inp.stale_data_observed or not inp.last_order_finality_known:
        return LiveActivationResult(
            activation_id=inp.activation_id,
            status=LiveActivationStatus.ROLLBACK_REQUIRED,
            allowed_capital_try=0.0,
            block_reasons=tuple(reasons),
        )

    if reasons:
        return LiveActivationResult(
            activation_id=inp.activation_id,
            status=LiveActivationStatus.BLOCKED,
            allowed_capital_try=0.0,
            block_reasons=tuple(reasons),
        )

    if not inp.halit_approval_present:
        return LiveActivationResult(
            activation_id=inp.activation_id,
            status=LiveActivationStatus.READY_FOR_REAL_LIVE_WAITING_APPROVAL,
            allowed_capital_try=0.0,
            block_reasons=("awaiting_halit_approval",),
        )

    # Capital sizing.
    cm = inp.capital_model
    if cm.mode is LiveBudgetMode.FIXED_TRY:
        allowed = min(cm.approved_capital_try, inp.available_balance_try)
    elif cm.mode is LiveBudgetMode.PERCENT_AVAILABLE:
        allowed = inp.available_balance_try * (cm.approved_capital_percent / 100.0)
    else:  # ALL_AVAILABLE_BALANCE
        allowed = inp.available_balance_try

    allowed = max(0.0, min(allowed, inp.available_balance_try))

    if inp.confirmed_first_real_order:
        status = LiveActivationStatus.FIRST_REAL_LIVE_ORDER_CONFIRMED
    elif not inp.qualifying_edge_present:
        status = LiveActivationStatus.REAL_LIVE_ACTIVE_WAITING_FOR_EDGE
    else:
        status = LiveActivationStatus.CONTROLLED_REAL_LIVE_ACTIVE

    return LiveActivationResult(
        activation_id=inp.activation_id,
        status=status,
        allowed_capital_try=allowed,
        block_reasons=(),
    )


__all__ = [
    "LiveActivationInput",
    "LiveActivationResult",
    "LiveActivationStatus",
    "LiveBudgetMode",
    "LiveCapitalModel",
    "evaluate_live_activation",
]
