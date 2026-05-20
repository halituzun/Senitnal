"""Event-profile cap hierarchy enforcement (N §7).

Per INGRESS_COMPILER_NUMERICS.md §7 and the Phase 4 build plan: every
ingress channel has a maximum allowed payload intensity. The hierarchy
is constitutional and monotone:

    Observation >= InternalShock >= RecallEvent.active
                 >= RecallEvent.verified >= HumanIntent
                 >= CandidateRecall

Hard caps in the v0.1 dev fixture (band centers, not safety-tested):
    ObservationEvent       1.00
    InternalShockEvent     0.90
    RecallEvent.active     0.70
    RecallEvent.verified   0.60
    HumanIntentEvent       0.35
    CandidateRecall        0.20

This module is the boundary enforcer: callers ask
`apply_profile_cap(profile, intensity)` and either get back the
clamped value or a `NumericsGovernanceViolation` if the hierarchy
itself is asked about a value it doesn't recognize. The hierarchy
order is exposed as `PROFILE_RANK` so test code can assert the
monotonicity invariant.

Constitutional invariant (also asserted at import time):
    For every adjacent pair in PROFILE_RANK,
    PROFILE_CAPS[higher_rank] >= PROFILE_CAPS[lower_rank].
"""

from __future__ import annotations

from sentinel.constitution.violations import (
    NumericsGovernanceViolation,
    ViolationContext,
)
from sentinel.types.neural_seed import EventProfile

# Strictly decreasing rank (higher rank = higher allowed cap).
PROFILE_RANK: tuple[EventProfile, ...] = (
    EventProfile.OBSERVATION_EVENT,
    EventProfile.INTERNAL_SHOCK_EVENT,
    EventProfile.RECALL_EVENT_ACTIVE,
    EventProfile.RECALL_EVENT_VERIFIED,
    EventProfile.HUMAN_INTENT_EVENT,
    EventProfile.CANDIDATE_RECALL,
)

PROFILE_CAPS: dict[EventProfile, float] = {
    EventProfile.OBSERVATION_EVENT: 1.00,
    EventProfile.INTERNAL_SHOCK_EVENT: 0.90,
    EventProfile.RECALL_EVENT_ACTIVE: 0.70,
    EventProfile.RECALL_EVENT_VERIFIED: 0.60,
    EventProfile.HUMAN_INTENT_EVENT: 0.35,
    EventProfile.CANDIDATE_RECALL: 0.20,
}

# Self-check at import time: catches a future bad edit immediately.
_ranks = [PROFILE_CAPS[p] for p in PROFILE_RANK]
assert _ranks == sorted(_ranks, reverse=True), (
    f"PROFILE_CAPS violates hierarchy monotonicity (N §7); got {_ranks}"
)


def cap_for(profile: EventProfile) -> float:
    """Return the constitutional cap for `profile`."""
    return PROFILE_CAPS[profile]


def apply_profile_cap(profile: EventProfile, intensity: float) -> float:
    """Clamp `intensity` to the profile cap; raise on out-of-range input.

    `intensity` must be a finite value in [0.0, 1.0]; otherwise raises
    NumericsGovernanceViolation (INGRESS_PROFILE_CAP_INPUT_INVALID).
    The cap itself is enforced by clamping (min); the cap clamp is
    NOT an error — it is the policy.
    """
    if not (0.0 <= intensity <= 1.0):
        raise NumericsGovernanceViolation(
            f"intensity {intensity!r} out of [0.0, 1.0]",
            ViolationContext(
                violation_code="INGRESS_PROFILE_CAP_INPUT_INVALID",
                source_ref="INGRESS_COMPILER_NUMERICS.md §7",
                evidence={
                    "profile": profile.value,
                    "intensity": intensity,
                },
            ),
        )
    cap = PROFILE_CAPS[profile]
    return min(intensity, cap)
