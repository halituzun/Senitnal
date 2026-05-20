# 0005 — MVP Polish Closure Review

> Phase 1-10 MVB build closed in review 0004. This document records
> the polish phase (Commits 43-51) that wired the catalog-documented
> ledger audits, added Hypothesis property tests, surfaced a CLI,
> exposed the curated public API, and added a catalog-consistency
> regression guard.

---

## Status

**GREEN.**

861 tests passing. pyright strict 0 errors. ruff clean. Forbidden
imports / output literal grep clean. The on-disk M1 ledger
re-verifies after every end-to-end run. The Sentinel MVP package
exposes a curated public API and is installable + runnable from the
command line.

---

## 1. Polish phase commits (43-51)

```
Commit 43  deontic ledger audit + per-declarative coverage tests
Commit 44  recall audit emission + 3 new catalog events
           (RECALL_REQUEST_EMITTED, RECALL_RESULT_EMPTY,
            RECALL_TRIGGER_REJECTED)
Commit 45  adapter manifest + neural-seed-attempt audit
Commit 46  CLI entry point (python -m sentinel.runtime)
Commit 47  README updated to reflect MVB v0.1 shipped state
Commit 48  Hypothesis property tests for cross-cutting invariants
Commit 49  M0 charge propagation integration test
           (closes build plan §10 Phase 5 done-def line:
            'Synthetic neural_seed produces M0 charge propagation
             trace')
Commit 50  top-level sentinel public API exports
Commit 51  catalog consistency regression guard
```

---

## 2. New runtime audit wiring

Three Phase 7-9 ledger audits were catalog-documented but not yet
emitted by code; the polish phase closed those gaps:

```
Deontic gate:
    evaluate_action_with_audit -> DEONTIC_BLOCKED on every BLOCK
    decision (payload carries intent_id / intent_type / block_class /
    triggered_declarative_code / rationale / reason).

Recall protocol:
    emit_recall_trigger_rejected -> RECALL_TRIGGER_REJECTED on a
    trigger that did NOT fire (reason guarded through
    assert_no_forbidden_literal).
    emit_recall_request -> RECALL_REQUEST_EMITTED on a fired
    trigger that surfaced a top-1 record (record_id + subject_class
    + score in payload).
    emit_recall_result_empty -> RECALL_RESULT_EMPTY on a fired
    trigger producing no candidate (T §20 audit-only; the core
    never sees an absence payload).

Adapter trust:
    emit_manifest_status_changed -> ADAPTER_MANIFEST_STATUS_CHANGED
    on any AdapterManifest status transition.
    emit_neural_seed_attempt_revoke -> canonical
    new_status=REVOKED + reason='neural_seed_emission_attempt'
    audit (matching the build plan §14 test specification).
```

All audit payload reason fields flow through
`assert_no_forbidden_literal` so an execution verb cannot leak into
the M1 ledger from a justification string.

---

## 3. Hypothesis property-based coverage

Phase 1-10 unit tests covered hand-picked cases; the polish phase
added Hypothesis-driven property tests for the invariants that
must hold for **every** well-formed input:

```
- apply_profile_cap output in [0, cap] for arbitrary intensity
- PROFILE_RANK monotone non-increasing in cap_for
- membership(band, value) in [0.0, 1.0] for arbitrary monotone band
- compute_recall_score in [0.0, 1.0] for arbitrary [0,1]^6 inputs
- compute_trust composite in [0.0, 1.0] when hard gates pass
- compute_trust composite = 0.0 when signature_validity = False
- canonical_json_bytes deterministic for same mapping
- sha256_digest format sha256:<64-hex> for arbitrary bytes
- placeholder_event_hash format stable
- No SystemOutput value contains a forbidden literal
```

---

## 4. M0 integration test

Phase 5 done definition required a charge propagation trace from a
synthetic NeuralSeed. The polish phase added an integration test
that wires:

```
allocate_uniform_birth_seeds(N) -> BirthSeedAllocation
   (uniform per-payload divergence = 0)
                              ↓
compile_neural_seed(...)   -> NeuralSeed (>= 1 PayloadSeed)
                              ↓
3-neuron tissue (a -> b -> c via 2 weak synapses)
                              ↓
propagate_charge per PayloadSeed
                              ↓
Per-edge trace asserting:
    - charges bounded in [0, 1]
    - 2-hop weak-band attenuation (<= 0.01)
    - synapse weights unchanged (read-only invariant)
    - synapse weights still < STABLE_PATH_THRESHOLD
    - determinism: replay produces identical trace
    - homonymous bias bound respected on every neuron
```

---

## 5. Distribution surface

The MVP is now consumable as a Python package and as a CLI:

```python
# Library use
from sentinel import EchoAdapter, JsonlObserverLedger, run_dry_simulation

ledger = JsonlObserverLedger(path)
result = run_dry_simulation(
    ledger=ledger,
    adapter=EchoAdapter.default(),
    observation_magnitude=0.8,
)
print(result.output.value)  # WAIT
assert ledger.verify()
```

```bash
# CLI use
uv run python -m sentinel.runtime --ledger /tmp/sentinel.jsonl
# -> sentinel-mvp: output=WAIT audit_events=2 ledger=/tmp/sentinel.jsonl
```

The top-level `sentinel` package exposes 28 curated public symbols
(adapters, constitution, gates, observer, types, runtime). Deeper
paths remain stable.

---

## 6. Regression guards

```
tests/observer/test_catalog_consistency.py:
    Scans every .py file under sentinel/ + tests/ for
    event_type="..." literals; any value not in the canonical
    catalog (or in the explicit test-only sentinel set) fails the
    suite. Prevents drift between code and catalog.

tests/runtime/test_cli.py:
    Confirms the CLI returns exit code 0, creates parent
    directories, and appends across runs while preserving the
    hash chain.

tests/property/test_invariants_property.py:
    10 Hypothesis-driven property classes exercising the
    cross-cutting [0,1] / determinism / format invariants.
```

---

## 7. Final aggregate state

```
Total commits:               ~ 102 (40 phase + 5 reviews/expansion +
                              9 polish; see git log --oneline)
Tests passing:               861
pyright strict:              0 errors
ruff:                        clean
Forbidden imports grep:      clean
Forbidden output literals:   clean
Constitutional invariants:   44-row catalog + type-boundary
                             rejections + runtime InvariantViolation
                             paths
Public API symbols:          28 + __version__
CLI:                         python -m sentinel.runtime
Dry sim output:              SystemOutput.WAIT (verified)
M1 ledger:                   re-verifies end-to-end after every run
```

---

## 8. Final hüküm

```
Sentinel Minimum Viable Brain v0.1 — GREEN, polished, shipped.
Build plan §15 done-def + Phase 5 trace gap + Phase 7-9 audit gaps
+ developer ergonomics (CLI, public API, property tests, drift
guard) all closed.

Sonraki tasarım faz işi MVB sonrasıdır ve bu repoda değildir.
```
