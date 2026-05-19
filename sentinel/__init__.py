"""Sentinel — Financial AGI core.

Minimum Viable Brain (MVB) implementation phase.

Conceptual + numerics design phase is **closed**:
    22 frozen draft documents (A-U + ATTENTION_WORKSPACE + M) +
    2 reviews (phase closure + implementation readiness) +
    1 build plan (`docs/build/0001-minimum-viable-brain-plan.md`).

Constitutional MVB invariants (enforced by CI + invariant test suite):
    - No live action output. Output set: {WAIT, BLOCK, MONITOR, NEED_RECALL, NO_ACTION}.
    - No live exchange API integration.
    - No LLM integration (intent_relay capability disabled).
    - No M2 verified production (candidate-only writes in MVP).
    - No numerics runtime mutation (signed artifacts only).
    - No cross-instance / fork / migration paths (MVP single-instance).
    - No replay-driven memory update (replay engine disabled in MVP).
    - No silent action (every gate decision audited to M1).

See `docs/build/0001-minimum-viable-brain-plan.md` for the implementation roadmap
and `docs/reviews/0001-phase-closure-consistency-review.md` for the
cross-document consistency baseline.
"""

__version__ = "0.1.0"
