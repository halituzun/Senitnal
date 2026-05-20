"""V4 — Replay budget.

Bounded session quota. The budget caps how many replay sessions
can run in a cycle / 24h window, sets per-session limits, and
accumulates a fatigue scalar that further suppresses replay when
recent activity has been high.

V4 explicitly does NOT introduce a "replay-can-trigger-replay
chain depth" field — replay is non-recursive by construction.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

# 24h window in milliseconds.
_TWENTY_FOUR_HOURS_MS: int = 24 * 60 * 60 * 1000


@dataclass(frozen=True, slots=True)
class ReplayBudget:
    """Per-instance replay budget config."""

    budget_id: str
    max_sessions_per_cycle: int
    max_sessions_per_24h_window: int
    max_events_per_session: int
    max_counterfactual_branches: int
    max_session_duration_ms: int
    replay_cooldown_ms: int
    replay_fatigue_accum_rate: float
    restore_continuity_required: bool

    def __post_init__(self) -> None:
        if not self.budget_id:
            raise ValueError("budget_id must be non-empty")
        if self.max_sessions_per_cycle <= 0:
            raise ValueError("max_sessions_per_cycle must be > 0")
        if self.max_sessions_per_24h_window <= 0:
            raise ValueError("max_sessions_per_24h_window must be > 0")
        if self.max_sessions_per_24h_window < self.max_sessions_per_cycle:
            raise ValueError("max_sessions_per_24h_window must be >= max_sessions_per_cycle")
        if self.max_events_per_session <= 0:
            raise ValueError("max_events_per_session must be > 0")
        if self.max_counterfactual_branches < 0:
            raise ValueError("max_counterfactual_branches must be >= 0")
        if self.max_session_duration_ms <= 0:
            raise ValueError("max_session_duration_ms must be > 0")
        if self.replay_cooldown_ms < 0:
            raise ValueError("replay_cooldown_ms must be >= 0")
        if not (0.0 <= self.replay_fatigue_accum_rate <= 1.0):
            raise ValueError("replay_fatigue_accum_rate must be in [0.0, 1.0]")
        if self.restore_continuity_required is not True:
            raise ValueError(
                "V4 requires restore_continuity_required=True; "
                "replay budget must persist across restore"
            )


_FATIGUE_BLOCK_THRESHOLD: float = 0.9


@dataclass(frozen=True, slots=True)
class ReplayBudgetState:
    """Mutable-by-copy budget state.

    `record_replay_session_completion` returns a NEW state with
    updated counters and accumulated fatigue.
    """

    budget: ReplayBudget
    sessions_used_this_cycle: int = 0
    sessions_used_24h: int = 0
    last_session_completed_at_ms: int | None = None
    replay_fatigue: float = 0.0

    def __post_init__(self) -> None:
        if self.sessions_used_this_cycle < 0:
            raise ValueError("sessions_used_this_cycle must be >= 0")
        if self.sessions_used_24h < 0:
            raise ValueError("sessions_used_24h must be >= 0")
        if not (0.0 <= self.replay_fatigue <= 1.0):
            raise ValueError("replay_fatigue must be in [0.0, 1.0]")


def can_start_replay_session(
    *,
    state: ReplayBudgetState,
    now_ms: int,
) -> bool:
    """Return True iff a new replay session may start at `now_ms`."""
    if now_ms < 0:
        raise ValueError("now_ms must be >= 0")
    if state.sessions_used_this_cycle >= state.budget.max_sessions_per_cycle:
        return False
    if state.sessions_used_24h >= state.budget.max_sessions_per_24h_window:
        return False
    if state.last_session_completed_at_ms is not None:
        elapsed = now_ms - state.last_session_completed_at_ms
        if elapsed < state.budget.replay_cooldown_ms:
            return False
    return not state.replay_fatigue >= _FATIGUE_BLOCK_THRESHOLD


def record_replay_session_completion(
    *,
    state: ReplayBudgetState,
    completed_at_ms: int,
) -> ReplayBudgetState:
    """Return a new state with counters and fatigue updated."""
    if completed_at_ms < 0:
        raise ValueError("completed_at_ms must be >= 0")
    new_fatigue = min(1.0, state.replay_fatigue + state.budget.replay_fatigue_accum_rate)
    # 24h-window counter: reset if the previous completion was more
    # than 24h ago; otherwise increment.
    sessions_used_24h = state.sessions_used_24h + 1
    if (
        state.last_session_completed_at_ms is not None
        and completed_at_ms - state.last_session_completed_at_ms > _TWENTY_FOUR_HOURS_MS
    ):
        sessions_used_24h = 1
    return replace(
        state,
        sessions_used_this_cycle=state.sessions_used_this_cycle + 1,
        sessions_used_24h=sessions_used_24h,
        last_session_completed_at_ms=completed_at_ms,
        replay_fatigue=new_fatigue,
    )
