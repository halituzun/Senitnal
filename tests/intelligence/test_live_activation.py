"""V11 — Live activation tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sentinel.intelligence.live_activation import (
    LiveActivationInput,
    LiveActivationStatus,
    LiveBudgetMode,
    LiveCapitalModel,
    evaluate_live_activation,
)


def _cm(**over: object) -> LiveCapitalModel:
    base: dict[str, object] = {
        "mode": LiveBudgetMode.FIXED_TRY,
        "approved_capital_try": 1_000.0,
        "max_entry_try": 100.0,
        "max_trades_per_day": 10,
        "max_open_orders": 5,
        "max_daily_loss_try": 200.0,
    }
    base.update(over)
    return LiveCapitalModel(**base)  # type: ignore[arg-type]


def _good(**over: object) -> LiveActivationInput:
    base: dict[str, object] = {
        "activation_id": "a1",
        "capital_model": _cm(),
        "halit_approval_present": True,
        "kill_switch_active": False,
        "hash_chain_valid": True,
        "available_balance_try": 10_000.0,
        "qualifying_edge_present": True,
        "last_order_finality_known": True,
        "bad_order_observed": False,
        "stale_data_observed": False,
    }
    base.update(over)
    return LiveActivationInput(**base)  # type: ignore[arg-type]


class TestActivationStatuses:
    def test_no_hardcoded_100_try_cap(self) -> None:
        # Approve 5,000 TRY — must propagate, not be capped to 100.
        cm = _cm(approved_capital_try=5_000.0, max_entry_try=5_000.0)
        r = evaluate_live_activation(_good(capital_model=cm, available_balance_try=10_000.0))
        assert r.status is LiveActivationStatus.CONTROLLED_REAL_LIVE_ACTIVE
        assert r.allowed_capital_try == 5_000.0

    def test_no_approval_yields_waiting_status(self) -> None:
        r = evaluate_live_activation(_good(halit_approval_present=False))
        assert r.status is LiveActivationStatus.READY_FOR_REAL_LIVE_WAITING_APPROVAL

    def test_kill_switch_active_blocks(self) -> None:
        r = evaluate_live_activation(_good(kill_switch_active=True))
        assert r.status is LiveActivationStatus.BLOCKED

    def test_bad_order_triggers_rollback(self) -> None:
        r = evaluate_live_activation(_good(bad_order_observed=True))
        assert r.status is LiveActivationStatus.ROLLBACK_REQUIRED

    def test_stale_data_triggers_rollback(self) -> None:
        r = evaluate_live_activation(_good(stale_data_observed=True))
        assert r.status is LiveActivationStatus.ROLLBACK_REQUIRED

    def test_unknown_finality_triggers_rollback(self) -> None:
        r = evaluate_live_activation(_good(last_order_finality_known=False))
        assert r.status is LiveActivationStatus.ROLLBACK_REQUIRED

    def test_no_edge_yields_waiting_for_edge(self) -> None:
        r = evaluate_live_activation(_good(qualifying_edge_present=False))
        assert r.status is LiveActivationStatus.REAL_LIVE_ACTIVE_WAITING_FOR_EDGE

    def test_first_order_confirmed(self) -> None:
        r = evaluate_live_activation(_good(confirmed_first_real_order=True))
        assert r.status is LiveActivationStatus.FIRST_REAL_LIVE_ORDER_CONFIRMED


class TestActivationCapital:
    def test_percent_mode_sizes_correctly(self) -> None:
        cm = LiveCapitalModel(
            mode=LiveBudgetMode.PERCENT_AVAILABLE,
            approved_capital_percent=25.0,
            max_entry_try=100.0,
            max_trades_per_day=10,
            max_open_orders=5,
            max_daily_loss_try=100.0,
        )
        r = evaluate_live_activation(_good(capital_model=cm, available_balance_try=10_000.0))
        assert r.allowed_capital_try == 2_500.0

    def test_all_available_mode(self) -> None:
        cm = LiveCapitalModel(
            mode=LiveBudgetMode.ALL_AVAILABLE_BALANCE,
            max_entry_try=100.0,
            max_trades_per_day=10,
            max_open_orders=5,
            max_daily_loss_try=100.0,
        )
        r = evaluate_live_activation(_good(capital_model=cm, available_balance_try=12_345.0))
        assert r.allowed_capital_try == 12_345.0

    def test_fixed_try_capped_by_balance(self) -> None:
        cm = _cm(approved_capital_try=5_000.0)
        r = evaluate_live_activation(_good(capital_model=cm, available_balance_try=2_000.0))
        assert r.allowed_capital_try == 2_000.0

    def test_fixed_try_requires_positive_amount(self) -> None:
        with pytest.raises(ValidationError):
            LiveCapitalModel(
                mode=LiveBudgetMode.FIXED_TRY,
                approved_capital_try=0.0,
                max_entry_try=100.0,
                max_trades_per_day=10,
                max_open_orders=5,
                max_daily_loss_try=100.0,
            )
