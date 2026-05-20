"""V4 — Replay budget tests."""

from __future__ import annotations

import pytest
from sentinel.replay.budget import (
    ReplayBudget,
    ReplayBudgetState,
    can_start_replay_session,
    record_replay_session_completion,
)


def _budget(**kw: object) -> ReplayBudget:
    defaults: dict[str, object] = {
        "budget_id": "b1",
        "max_sessions_per_cycle": 3,
        "max_sessions_per_24h_window": 10,
        "max_events_per_session": 50,
        "max_counterfactual_branches": 4,
        "max_session_duration_ms": 60_000,
        "replay_cooldown_ms": 1_000,
        "replay_fatigue_accum_rate": 0.1,
        "restore_continuity_required": True,
    }
    defaults.update(kw)
    return ReplayBudget(**defaults)  # type: ignore[arg-type]


class TestBudgetConstruction:
    def test_valid_budget(self) -> None:
        _budget()

    def test_restore_continuity_required_false_rejected(self) -> None:
        with pytest.raises(ValueError, match="restore_continuity_required"):
            _budget(restore_continuity_required=False)

    def test_24h_below_cycle_rejected(self) -> None:
        with pytest.raises(ValueError):
            _budget(max_sessions_per_cycle=5, max_sessions_per_24h_window=2)

    def test_zero_max_per_cycle_rejected(self) -> None:
        with pytest.raises(ValueError):
            _budget(max_sessions_per_cycle=0)

    def test_fatigue_rate_out_of_range_rejected(self) -> None:
        with pytest.raises(ValueError):
            _budget(replay_fatigue_accum_rate=1.5)

    def test_no_recursive_field(self) -> None:
        # ReplayBudget is a frozen dataclass with slots; arbitrary
        # extra fields are not accepted (TypeError at construction).
        with pytest.raises(TypeError):
            ReplayBudget(
                budget_id="b1",
                max_sessions_per_cycle=1,
                max_sessions_per_24h_window=1,
                max_events_per_session=1,
                max_counterfactual_branches=0,
                max_session_duration_ms=1,
                replay_cooldown_ms=0,
                replay_fatigue_accum_rate=0.0,
                restore_continuity_required=True,
                replay_can_trigger_replay_max_chain_depth=2,  # type: ignore[call-arg]
            )


class TestBudgetGuards:
    def test_cycle_cap_blocks(self) -> None:
        b = _budget(max_sessions_per_cycle=2)
        s = ReplayBudgetState(budget=b, sessions_used_this_cycle=2, sessions_used_24h=2)
        assert can_start_replay_session(state=s, now_ms=10_000) is False

    def test_24h_cap_blocks(self) -> None:
        b = _budget(max_sessions_per_cycle=2, max_sessions_per_24h_window=2)
        s = ReplayBudgetState(budget=b, sessions_used_this_cycle=0, sessions_used_24h=2)
        assert can_start_replay_session(state=s, now_ms=10_000) is False

    def test_cooldown_blocks(self) -> None:
        b = _budget(replay_cooldown_ms=5_000)
        s = ReplayBudgetState(budget=b, last_session_completed_at_ms=10_000)
        assert can_start_replay_session(state=s, now_ms=12_000) is False

    def test_cooldown_allows_after_elapsed(self) -> None:
        b = _budget(replay_cooldown_ms=5_000)
        s = ReplayBudgetState(budget=b, last_session_completed_at_ms=10_000)
        assert can_start_replay_session(state=s, now_ms=20_000) is True

    def test_fatigue_blocks(self) -> None:
        b = _budget()
        s = ReplayBudgetState(budget=b, replay_fatigue=0.95)
        assert can_start_replay_session(state=s, now_ms=10_000) is False


class TestCompletion:
    def test_counters_increment(self) -> None:
        b = _budget()
        s = ReplayBudgetState(budget=b)
        s2 = record_replay_session_completion(state=s, completed_at_ms=10_000)
        assert s2.sessions_used_this_cycle == 1
        assert s2.sessions_used_24h == 1
        assert s2.last_session_completed_at_ms == 10_000
        assert s2.replay_fatigue == pytest.approx(0.1)

    def test_fatigue_caps_at_one(self) -> None:
        b = _budget(replay_fatigue_accum_rate=0.6)
        s = ReplayBudgetState(budget=b, replay_fatigue=0.9)
        s2 = record_replay_session_completion(state=s, completed_at_ms=10)
        assert s2.replay_fatigue == 1.0

    def test_24h_window_resets_after_a_day(self) -> None:
        b = _budget()
        s = ReplayBudgetState(budget=b, sessions_used_24h=8, last_session_completed_at_ms=0)
        # completed 25h later -> counter resets to 1
        twenty_five_h = 25 * 60 * 60 * 1000
        s2 = record_replay_session_completion(state=s, completed_at_ms=twenty_five_h)
        assert s2.sessions_used_24h == 1
