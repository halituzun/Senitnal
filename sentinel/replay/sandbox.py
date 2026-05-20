"""V4 — Replay sandbox.

A sandbox isolates simulated events from the live core. Every
event constructed inside a sandbox is tagged `replay_simulated=True`
and CANNOT be routed through `route_observer_event` as a live
event. The sandbox result enforces three hard zeros:

    produced_live_event_count    == 0
    produced_action_count        == 0
    produced_memory_write_count  == 0

A nonzero on any of these is a constitutional violation; the
sandbox result construction raises before the value leaves.
"""

from __future__ import annotations

from collections.abc import Mapping  # noqa: TC003 (runtime annotation)
from dataclasses import dataclass, field

from sentinel.replay.session import ReplaySession  # noqa: TC001 (runtime arg)


@dataclass(frozen=True, slots=True)
class SimulatedEvent:
    """An event constructed inside a sandbox.

    NEVER an ObserverEvent. Caller wraps these in a real
    ObserverEvent via the V4 audit emitter (which encodes the
    proposal as REPLAY_SESSION_STATUS_CHANGED or one of the new
    REPLAY effect-channel events) before any router contact.
    """

    simulated_event_id: str
    kind: str
    payload: Mapping[str, object]
    replay_simulated: bool = True

    def __post_init__(self) -> None:
        if not self.simulated_event_id:
            raise ValueError("simulated_event_id must be non-empty")
        if not self.kind:
            raise ValueError("kind must be non-empty")
        if self.replay_simulated is not True:
            raise ValueError("SimulatedEvent.replay_simulated must be True")


@dataclass(frozen=True, slots=True)
class ReplaySandbox:
    """Isolated namespace for one replay session's simulation."""

    sandbox_id: str
    session_id: str
    source_snapshot_hash: str
    simulated_events: tuple[SimulatedEvent, ...] = field(default_factory=tuple)
    notes: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.sandbox_id:
            raise ValueError("sandbox_id must be non-empty")
        if not self.session_id:
            raise ValueError("session_id must be non-empty")
        if not self.source_snapshot_hash:
            raise ValueError("source_snapshot_hash must be non-empty")


@dataclass(frozen=True, slots=True)
class ReplaySandboxResult:
    """Outcome of one sandbox run.

    Hard zeros: produced_live_event_count, produced_action_count,
    produced_memory_write_count MUST all be 0. Any nonzero value
    raises in `__post_init__` — there is no path through which the
    sandbox can emit a live event, an action, or a memory write.
    """

    sandbox_id: str
    session_id: str
    simulated_event_count: int
    produced_live_event_count: int
    produced_action_count: int
    produced_memory_write_count: int
    score_artifacts: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.simulated_event_count < 0:
            raise ValueError("simulated_event_count must be >= 0")
        if self.produced_live_event_count != 0:
            raise ValueError(
                "ReplaySandboxResult.produced_live_event_count must be 0 "
                "(sandbox MUST NOT emit live events)"
            )
        if self.produced_action_count != 0:
            raise ValueError(
                "ReplaySandboxResult.produced_action_count must be 0 "
                "(sandbox MUST NOT produce action output)"
            )
        if self.produced_memory_write_count != 0:
            raise ValueError(
                "ReplaySandboxResult.produced_memory_write_count must be 0 "
                "(sandbox MUST NOT write M2 directly; MWG is the only path)"
            )


def run_in_sandbox(
    *,
    session: ReplaySession,
    sandbox: ReplaySandbox,
    score_artifacts: tuple[str, ...] = (),
) -> ReplaySandboxResult:
    """Wrap a sandbox's pre-built simulated events as a result.

    Pure: does not call any router, ledger, or core entry point.
    The simulated events live ONLY in the sandbox object; this
    helper just summarises them into a result. Counts that would
    indicate constitutional violation (live / action / memory
    write) are HARD-ZERO and validated by the result dataclass.
    """
    return ReplaySandboxResult(
        sandbox_id=sandbox.sandbox_id,
        session_id=session.session_id,
        simulated_event_count=len(sandbox.simulated_events),
        produced_live_event_count=0,
        produced_action_count=0,
        produced_memory_write_count=0,
        score_artifacts=score_artifacts,
    )
