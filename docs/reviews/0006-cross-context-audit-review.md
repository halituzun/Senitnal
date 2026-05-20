# 0006 — Cross-Context Audit + Permanence Routing Closure

> Polish phase closed in review 0005. This document records the
> forensic cross-context audit pass (Commits 53-56) that closed
> three real wiring / semantic gaps and aligned every audit
> emission path with the canonical catalog permanence policy.

---

## Status

**GREEN.**

874 tests passing. pyright strict 0 errors. ruff clean. Forbidden
imports / output literal grep clean. Hash chain re-verifies after
the end-to-end run, and every audit event now lands where the
catalog says it should: PERMANENT/PERMANENT_WITH_SNAPSHOT events
in the JSONL ledger, RING_BUFFER_ONLY events in the RAM ring
buffer (or dropped if no buffer is supplied — no implicit JSONL
promotion).

---

## 1. Audit findings + fixes

A fresh forensic audit (post review 0005) found five real gaps.
Each was closed in a focused commit:

```
Audit finding                                                Closed by
-----------                                                  --------
[blocker] Recall audit helpers unreachable in MVP pipeline   Commit 53
[blocker] Deontic audit helper exported but never called     Commit 53
[blocker] Adapter audit helpers exported but never called    Commit 53
[quality] should_emit_pulse orphan + docstring drift         Commit 53
[quality] Audit docstrings overpromise v0.2 contract         Commit 53
[blocker] Catalog says ring_buffer_only but code writes      Commit 55
          PERMANENT — semantic split between catalog and
          code (OBSERVATION_INGESTED + WORKSPACE_PULSE)
```

---

## 2. New runtime wiring (Commit 53)

```
run_dry_simulation now invokes every catalog-documented audit path:
    1. emit_manifest_status_changed -> ADAPTER_MANIFEST_STATUS_CHANGED
       (CANDIDATE -> ACTIVE) on every canonical run; opt-out via
       emit_adapter_activation=False
    2. _build_observation_ingested -> OBSERVATION_INGESTED (routed)
    3. _build_workspace_pulse_event -> WORKSPACE_PULSE (routed)
    4. emit_recall_trigger_rejected -> RECALL_TRIGGER_REJECTED
       after every recall trigger check (T §5 'exactly one audit
       per evaluation' contract honored)
    5. evaluate_action_with_audit -> DEONTIC_BLOCKED via opt-in
       exercise_deontic_gate=True parameter
```

Docstrings in `recall/audit.py` and `adapters/audit.py` now list
the v0.1 wired callers honestly — no more "every evaluation must"
claims that the codebase itself doesn't honor.

`workspace/pulse.py::should_emit_pulse` docstring explicitly
documents why `dry_sim` doesn't call it (MVP always emits) and
who the intended caller is (future stateful runtime).

---

## 3. Permanence-aware router (Commit 55)

New module: `sentinel/observer/router.py`

    route_observer_event(*, event, ledger, ring_buffer)
        -> RoutingOutcome (permanence, written_to_ledger,
                           pushed_to_ring_buffer, event)

The catalog row for `event.event_type` decides routing:

```
ring_buffer_only         push to ring_buffer; drop if None
permanent                append to JSONL ledger
permanent_with_snapshot  BOTH ledger.append + ring.push
ephemeral                drop
```

Catalog permanence is now **binding**. Two source-of-truth
signals (catalog policy + actual write path) agree.

`run_dry_simulation` rewired through the router; `DrySimResult`
grows two new tuple fields:

```
permanent_event_ids       events in the JSONL chain
ring_buffer_event_ids     events in the ring buffer
audit_event_ids           union (existing field, now derives
                          from the routing outcome)
```

Canonical run (with ring buffer): 2 PERMANENT (adapter activation,
recall rejected) + 2 RING_ONLY (observation, pulse) = 4 total.

CLI prints permanent= and ring= counts.

---

## 4. Public API additions

`from sentinel import ...` now exposes:

```
emit_manifest_status_changed       (adapter audit)
emit_neural_seed_attempt_revoke    (adapter red-line audit)
emit_recall_request                (recall audit)
emit_recall_result_empty           (recall audit)
emit_recall_trigger_rejected       (recall audit)
EventPermanence                    (catalog policy enum)
ObserverRingBuffer                 (ring storage)
route_observer_event               (sanctioned routing)
RoutingOutcome                     (routing result)
```

Brings the public surface to 38 symbols + __version__.

---

## 5. Aggregate state

```
Total commits:               ~ 110 (Phase 1-10 + polish + audit pass)
Tests passing:               874  (+ 13 from review 0005)
pyright strict:              0 errors
ruff:                        clean
Forbidden imports grep:      clean
Forbidden output literals:   clean
Constitutional invariants:   44-row catalog (data + runtime)
Canonical observer events:   23 catalog rows; every event_type
                             literal in code is in the catalog
                             (regression guard from review 0005)
Permanence policy:           BINDING; no code path bypasses the
                             router for routing decisions
Public API symbols:          38 + __version__
CLI:                         python -m sentinel.runtime
Dry sim output:              SystemOutput.WAIT (verified)
M1 ledger:                   re-verifies end-to-end after every run
                             (chain only carries PERMANENT events)
```

---

## 6. Final hüküm

```
Sentinel Minimum Viable Brain v0.1 — GREEN, polished, cross-
context aligned. No audit helper is orphan; no catalog row is
unreachable; no docstring overpromises behaviour the code
doesn't deliver; catalog permanence policy is enforced at the
single sanctioned routing point.

Bağlamlar arası nizam: tamam.
```
