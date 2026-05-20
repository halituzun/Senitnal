"""Sentinel — Financial AGI core.

Minimum Viable Brain (MVB) v0.1 — shipped.

Conceptual + numerics design phase **closed**:
    22 frozen draft documents (A-U + ATTENTION_WORKSPACE + M) +
    2 reviews (phase closure + implementation readiness) +
    1 build plan (`docs/build/0001-minimum-viable-brain-plan.md`).

Implementation phase **closed**:
    Phases 1-10 (Contracts as Code -> End-to-end Dry Simulation)
    + polish phase (audit wiring, property tests, CLI, public API,
    catalog-consistency guard) — see
    `docs/reviews/0004-mvp-build-closure-review.md` and
    `docs/reviews/0005-mvp-polish-closure-review.md`.

Constitutional MVB invariants (enforced by type boundary + CI
grep + invariant test suite):
    - No live action output. Output set: {WAIT, BLOCK, MONITOR, NEED_RECALL, NO_ACTION}.
    - No live exchange API integration.
    - No LLM integration (intent_relay capability disabled).
    - No M2 verified production (candidate-only writes in MVP).
    - No numerics runtime mutation (signed artifacts only).
    - No cross-instance / fork / migration paths (MVP single-instance).
    - No replay-driven memory update (replay engine disabled in MVP).
    - No silent action (every gate decision audited to M1).

Top-level package re-exports the curated public API (see __all__
below); deeper module paths remain available for explicit imports.

Quick start:
    >>> from sentinel import (
    ...     EchoAdapter, JsonlObserverLedger, run_dry_simulation,
    ... )
    >>> ledger = JsonlObserverLedger(path)
    >>> result = run_dry_simulation(
    ...     ledger=ledger,
    ...     adapter=EchoAdapter.default(),
    ...     observation_magnitude=0.8,
    ... )
    >>> result.output
    <SystemOutput.WAIT: 'WAIT'>
    >>> ledger.verify()
    True
"""

__version__ = "0.1.0"


# ---------------------------------------------------------------------------
# Public API — curated re-exports.
#
# Importing from `sentinel` directly is the supported integration surface
# for downstream callers; deeper paths (e.g. `sentinel.observer.ledger`)
# remain available but may be reorganized in later phases.
# ---------------------------------------------------------------------------

from sentinel.adapters.audit import (
    emit_manifest_status_changed,
    emit_neural_seed_attempt_revoke,
)
from sentinel.adapters.echo import EchoAdapter
from sentinel.adapters.local_jsonl_market import LocalJsonlMarketAdapter
from sentinel.adapters.market_observation import (
    MarketObservationEnvelope,
    SanitizedMarketProvenance,
    build_market_observation_audit_payload,
    sanitize_market_observation_to_event,
)
from sentinel.adapters.synthetic_market import SyntheticMarketAdapter
from sentinel.adapters.trust import (
    AdapterTrustRecord,
    TrustBand,
    compute_trust,
)
from sentinel.constitution.invariants import (
    MVP_REQUIRED_INVARIANTS,
    InvariantCategory,
    InvariantDefinition,
    InvariantSeverity,
    assert_invariant,
    get_invariant,
    list_invariants,
)
from sentinel.constitution.violations import (
    ConstitutionalViolation,
    InvariantViolation,
    ViolationContext,
)
from sentinel.gates.deontic import (
    ApprovedActionIntent,
    BlockClass,
    DeonticDecision,
    DeonticOutcome,
    evaluate_action,
    evaluate_action_with_audit,
)
from sentinel.observer.ledger import JsonlObserverLedger
from sentinel.observer.permanence import EventPermanence
from sentinel.observer.ring_buffer import ObserverRingBuffer
from sentinel.observer.router import RoutingOutcome, route_observer_event
from sentinel.recall.audit import (
    emit_recall_request,
    emit_recall_result_empty,
    emit_recall_trigger_rejected,
)
from sentinel.runtime.dry_sim import DrySimResult, run_dry_simulation
from sentinel.runtime.market_replay import (
    MarketReplayResult,
    run_market_jsonl_file,
    run_market_observations,
)
from sentinel.runtime.output import SystemOutput
from sentinel.types.neural_seed import EventProfile, NeuralSeed, ProvenanceRef
from sentinel.types.observer import EventFamily, ObserverEvent
from sentinel.types.payload import PayloadSeed, PrimerPayload

__all__ = [
    "MVP_REQUIRED_INVARIANTS",
    "AdapterTrustRecord",
    "ApprovedActionIntent",
    "BlockClass",
    "ConstitutionalViolation",
    "DeonticDecision",
    "DeonticOutcome",
    "DrySimResult",
    "EchoAdapter",
    "EventFamily",
    "EventPermanence",
    "EventProfile",
    "InvariantCategory",
    "InvariantDefinition",
    "InvariantSeverity",
    "InvariantViolation",
    "JsonlObserverLedger",
    "LocalJsonlMarketAdapter",
    "MarketObservationEnvelope",
    "MarketReplayResult",
    "NeuralSeed",
    "ObserverEvent",
    "ObserverRingBuffer",
    "PayloadSeed",
    "PrimerPayload",
    "ProvenanceRef",
    "RoutingOutcome",
    "SanitizedMarketProvenance",
    "SyntheticMarketAdapter",
    "SystemOutput",
    "TrustBand",
    "ViolationContext",
    "__version__",
    "assert_invariant",
    "build_market_observation_audit_payload",
    "compute_trust",
    "emit_manifest_status_changed",
    "emit_neural_seed_attempt_revoke",
    "emit_recall_request",
    "emit_recall_result_empty",
    "emit_recall_trigger_rejected",
    "evaluate_action",
    "evaluate_action_with_audit",
    "get_invariant",
    "list_invariants",
    "route_observer_event",
    "run_dry_simulation",
    "run_market_jsonl_file",
    "run_market_observations",
    "sanitize_market_observation_to_event",
]
