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
from sentinel.recall.audit import (
    emit_recall_request,
    emit_recall_result_empty,
    emit_recall_trigger_rejected,
)
from sentinel.runtime.dry_sim import DrySimResult, run_dry_simulation
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
    "EventProfile",
    "InvariantCategory",
    "InvariantDefinition",
    "InvariantSeverity",
    "InvariantViolation",
    "JsonlObserverLedger",
    "NeuralSeed",
    "ObserverEvent",
    "PayloadSeed",
    "PrimerPayload",
    "ProvenanceRef",
    "SystemOutput",
    "TrustBand",
    "ViolationContext",
    "__version__",
    "assert_invariant",
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
    "run_dry_simulation",
]
