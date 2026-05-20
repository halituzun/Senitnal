"""Adapter manifest / trust audit emission helpers.

Per ADAPTER_MANIFEST_SPEC.md §9 and ADAPTER_TRUST_NUMERICS.md §6,
two ledger events live in this module's domain:

    ADAPTER_MANIFEST_STATUS_CHANGED — every transition of an
        adapter manifest's status (e.g. ACTIVE -> REVOKED) must be
        audited; the reason is recorded with the constitutional
        red-line code when applicable.

The functions here are pure: they take an adapter id + a reason +
a target status and append exactly one observer event. Callers are
responsible for actually changing internal state (the audit is the
authoritative record).

Constitutional discipline:
    - REVOKED status with reason='neural_seed_emission_attempt' is
      the canonical record of a Phase 9 red-line breach
    - All reason strings pass through `assert_no_forbidden_literal`
      so execution verbs cannot leak from a justification text
"""

from __future__ import annotations

from sentinel.observer.hash_chain import placeholder_event_hash
from sentinel.observer.ledger import JsonlObserverLedger  # noqa: TC001 (runtime)
from sentinel.runtime.output import assert_no_forbidden_literal
from sentinel.types.adapters import AdapterManifestStatus
from sentinel.types.neural_seed import ProvenanceRef
from sentinel.types.observer import EventFamily, ObserverEvent


def emit_manifest_status_changed(
    ledger: JsonlObserverLedger,
    *,
    adapter_id: str,
    manifest_id: str,
    previous_status: AdapterManifestStatus,
    new_status: AdapterManifestStatus,
    reason: str,
    now_ms: int,
) -> ObserverEvent:
    """Audit one AdapterManifest status transition.

    Raises `ForbiddenOutputViolation` if `reason` contains any
    forbidden execution literal.
    """
    assert_no_forbidden_literal(reason)
    return ledger.append(
        ObserverEvent(
            event_id=f"adapter-status-{manifest_id}-{new_status.value}",
            event_family=EventFamily.LEDGER_META,
            event_type="ADAPTER_MANIFEST_STATUS_CHANGED",
            occurred_at_ms=now_ms,
            payload={
                "adapter_id": adapter_id,
                "manifest_id": manifest_id,
                "previous_status": previous_status.value,
                "new_status": new_status.value,
                "reason": reason,
            },
            provenance=ProvenanceRef(source_event_id=manifest_id),
            previous_event_hash=None,
            event_hash=placeholder_event_hash(),
        )
    )


def emit_neural_seed_attempt_revoke(
    ledger: JsonlObserverLedger,
    *,
    adapter_id: str,
    manifest_id: str,
    previous_status: AdapterManifestStatus,
    now_ms: int,
) -> ObserverEvent:
    """Audit the constitutional red line: adapter attempted NeuralSeed.

    Records ADAPTER_MANIFEST_STATUS_CHANGED with the canonical
    reason string `neural_seed_emission_attempt`. The new status is
    REVOKED — once an adapter attempts this, trust is irrevocably
    lost.
    """
    return emit_manifest_status_changed(
        ledger,
        adapter_id=adapter_id,
        manifest_id=manifest_id,
        previous_status=previous_status,
        new_status=AdapterManifestStatus.REVOKED,
        reason="neural_seed_emission_attempt",
        now_ms=now_ms,
    )
