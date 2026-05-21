"""V13 — Strategy lifecycle tests."""

from __future__ import annotations

import pytest
from sentinel.production.strategy_lifecycle import (
    StrategyLifecycleState,
    transition_state,
)


class TestForward:
    def test_research_to_paper_skip_rejected(self) -> None:
        with pytest.raises(ValueError):
            transition_state(
                current=StrategyLifecycleState.RESEARCH,
                target=StrategyLifecycleState.PAPER,
            )

    def test_research_to_active_live_skip_rejected(self) -> None:
        with pytest.raises(ValueError):
            transition_state(
                current=StrategyLifecycleState.RESEARCH,
                target=StrategyLifecycleState.ACTIVE_LIVE,
            )

    def test_canary_to_limited_live(self) -> None:
        s = transition_state(
            current=StrategyLifecycleState.CANARY,
            target=StrategyLifecycleState.LIMITED_LIVE,
        )
        assert s is StrategyLifecycleState.LIMITED_LIVE

    def test_limited_live_to_active_live(self) -> None:
        s = transition_state(
            current=StrategyLifecycleState.LIMITED_LIVE,
            target=StrategyLifecycleState.ACTIVE_LIVE,
        )
        assert s is StrategyLifecycleState.ACTIVE_LIVE

    def test_retired_is_terminal(self) -> None:
        with pytest.raises(ValueError):
            transition_state(
                current=StrategyLifecycleState.RETIRED,
                target=StrategyLifecycleState.PAUSED,
            )


class TestForcedRollback:
    def test_bad_order_forces_rollback(self) -> None:
        s = transition_state(
            current=StrategyLifecycleState.ACTIVE_LIVE,
            target=StrategyLifecycleState.PAUSED,
            bad_order_observed=True,
        )
        assert s is StrategyLifecycleState.ROLLBACK_REQUIRED

    def test_stale_data_forces_rollback(self) -> None:
        s = transition_state(
            current=StrategyLifecycleState.ACTIVE_LIVE,
            target=StrategyLifecycleState.PAUSED,
            stale_data_observed=True,
        )
        assert s is StrategyLifecycleState.ROLLBACK_REQUIRED

    def test_unknown_finality_forces_rollback(self) -> None:
        s = transition_state(
            current=StrategyLifecycleState.LIMITED_LIVE,
            target=StrategyLifecycleState.ACTIVE_LIVE,
            finality_known=False,
        )
        assert s is StrategyLifecycleState.ROLLBACK_REQUIRED

    def test_rollback_can_go_to_retired_or_paused(self) -> None:
        s = transition_state(
            current=StrategyLifecycleState.ROLLBACK_REQUIRED,
            target=StrategyLifecycleState.RETIRED,
        )
        assert s is StrategyLifecycleState.RETIRED


class TestPauseResume:
    def test_paused_can_resume_active_live(self) -> None:
        s = transition_state(
            current=StrategyLifecycleState.PAUSED,
            target=StrategyLifecycleState.ACTIVE_LIVE,
        )
        assert s is StrategyLifecycleState.ACTIVE_LIVE

    def test_self_transition_allowed(self) -> None:
        s = transition_state(
            current=StrategyLifecycleState.ACTIVE_LIVE,
            target=StrategyLifecycleState.ACTIVE_LIVE,
        )
        assert s is StrategyLifecycleState.ACTIVE_LIVE
