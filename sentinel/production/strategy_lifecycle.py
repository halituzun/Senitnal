"""V13 — Strategy lifecycle state machine.

Closed 10-state set with explicit allowed transitions.  Bad orders,
stale data, and unknown finality force ``rollback_required``.
"""

from __future__ import annotations

from enum import StrEnum


class StrategyLifecycleState(StrEnum):
    """Closed set of strategy lifecycle states."""

    RESEARCH = "research"
    HISTORICAL_VALIDATED = "historical_validated"
    PAPER = "paper"
    SHADOW = "shadow"
    CANARY = "canary"
    LIMITED_LIVE = "limited_live"
    ACTIVE_LIVE = "active_live"
    PAUSED = "paused"
    RETIRED = "retired"
    ROLLBACK_REQUIRED = "rollback_required"


_FORWARD_PATH: dict[StrategyLifecycleState, set[StrategyLifecycleState]] = {
    StrategyLifecycleState.RESEARCH: {
        StrategyLifecycleState.HISTORICAL_VALIDATED,
        StrategyLifecycleState.RETIRED,
        StrategyLifecycleState.ROLLBACK_REQUIRED,
    },
    StrategyLifecycleState.HISTORICAL_VALIDATED: {
        StrategyLifecycleState.PAPER,
        StrategyLifecycleState.RETIRED,
        StrategyLifecycleState.ROLLBACK_REQUIRED,
    },
    StrategyLifecycleState.PAPER: {
        StrategyLifecycleState.SHADOW,
        StrategyLifecycleState.PAUSED,
        StrategyLifecycleState.RETIRED,
        StrategyLifecycleState.ROLLBACK_REQUIRED,
    },
    StrategyLifecycleState.SHADOW: {
        StrategyLifecycleState.CANARY,
        StrategyLifecycleState.PAUSED,
        StrategyLifecycleState.RETIRED,
        StrategyLifecycleState.ROLLBACK_REQUIRED,
    },
    StrategyLifecycleState.CANARY: {
        StrategyLifecycleState.LIMITED_LIVE,
        StrategyLifecycleState.PAUSED,
        StrategyLifecycleState.RETIRED,
        StrategyLifecycleState.ROLLBACK_REQUIRED,
    },
    StrategyLifecycleState.LIMITED_LIVE: {
        StrategyLifecycleState.ACTIVE_LIVE,
        StrategyLifecycleState.PAUSED,
        StrategyLifecycleState.RETIRED,
        StrategyLifecycleState.ROLLBACK_REQUIRED,
    },
    StrategyLifecycleState.ACTIVE_LIVE: {
        StrategyLifecycleState.PAUSED,
        StrategyLifecycleState.RETIRED,
        StrategyLifecycleState.ROLLBACK_REQUIRED,
    },
    StrategyLifecycleState.PAUSED: {
        StrategyLifecycleState.LIMITED_LIVE,
        StrategyLifecycleState.ACTIVE_LIVE,
        StrategyLifecycleState.RETIRED,
        StrategyLifecycleState.ROLLBACK_REQUIRED,
    },
    StrategyLifecycleState.RETIRED: set(),
    StrategyLifecycleState.ROLLBACK_REQUIRED: {
        StrategyLifecycleState.RETIRED,
        StrategyLifecycleState.PAUSED,
    },
}


def transition_state(
    *,
    current: StrategyLifecycleState,
    target: StrategyLifecycleState,
    bad_order_observed: bool = False,
    stale_data_observed: bool = False,
    finality_known: bool = True,
) -> StrategyLifecycleState:
    """Return the validated next state.

    Hard rules:
      - ``bad_order_observed`` forces ``ROLLBACK_REQUIRED``
      - ``stale_data_observed`` forces ``ROLLBACK_REQUIRED``
      - ``finality_known is False`` forces ``ROLLBACK_REQUIRED``
      - Otherwise ``target`` must be in the allowed forward set
        from ``current``.
    """
    if bad_order_observed or stale_data_observed or not finality_known:
        return StrategyLifecycleState.ROLLBACK_REQUIRED

    if target == current:
        return current

    allowed = _FORWARD_PATH.get(current, set())
    if target not in allowed:
        raise ValueError(f"illegal lifecycle transition: {current.value} -> {target.value}")
    return target


__all__ = ["StrategyLifecycleState", "transition_state"]
