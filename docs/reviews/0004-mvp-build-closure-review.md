# 0004 — MVP Build Closure Review

> Phase 10 dry simulation pipeline shipped. This document records
> the closure of the Minimum Viable Brain build plan
> (`docs/build/0001-minimum-viable-brain-plan.md`) against the
> done-definition for each phase.

---

## Status

**GREEN.**

All 10 phases of the MVB build plan have closed. The end-to-end
pipeline runs a synthetic ObservationEvent through compile →
workspace pulse → recall-trigger check → deontic-guard-by-default
and produces `SystemOutput.WAIT` with a fully-chained M1 ledger
trail. No execution-output literal is permitted into the ledger,
on disk or in memory.

---

## 1. Done-definition recap

### Phase 1 — Contracts as Code (Commits 1-12)

```
[+] payload, neural_seed, events, observer, memory, numerics,
    adapters, workspace schemas
[+] constitution/violations + constitution/invariants (24-row catalog)
[+] Phase 1 review (0003)
```

### Phase 2 — Observer Ledger (Commits 13-18)

```
[+] catalog (18 + 2 NUMERICS events = 20)
[+] hash_chain (deterministic JSON, sha256:<hex>, link + verify)
[+] ledger (JSONL append-only, family validation, write-authoritative chain)
[+] permanence (decision interpretation + monotonicity invariant)
[+] ring_buffer (capacity + catalog-aware policy guard)
[+] audit_reader (reader_type enum + LLM scope whitelist + audit emit)
```

### Phase 3 — Numerics Loader (Commits 19-21)

```
[+] loader (mode-gated, dev_only enforcement, MissingArtifactError)
[+] dependency_validator (unknown-key + cycle DFS)
[+] 8 v0-dev fixtures (one per SpecFamily) + parametric load tests
```

### Phase 4 — Ingress Compiler (Commits 22-25)

```
[+] profile_caps (N §7 hierarchy + import-time monotonicity assertion)
[+] soft_overlap (FuzzyBand trapezoidal/triangular linear membership)
[+] rules (BootstrapRule schema + 8-rule MVP registry, learning OFF)
[+] compiler (deterministic event-to-NeuralSeed; weighted blend; cap)
```

### Phase 5 — Minimal M0 Tissue (Commits 26-31)

```
[+] neuron (homonymous bias, no specialist invariant)
[+] synapse (weak band, weight<stable threshold, read-only propagate)
[+] self_field (strict hierarchy + sum budget)
[+] proto_resonance (5-layer birth invariant)
[+] assembly + AssemblyCensus (zero-at-birth invariants)
[+] tissue (uniform per-payload birth seed allocation)
```

### Phase 6 — Workspace Pulse (Commit 32)

```
[+] pulse (should_emit_pulse + emit_workspace_pulse;
    single mechanism; pulse character = dominant_payload_mix)
```

### Phase 7 — Gates (Commits 33-35)

```
[+] runtime/feature_flags (22-flag matrix, single source of truth)
[+] deontic (11 declaratives, default-deny, kill-switch precedence,
    schema-enforced BLOCK<->declarative consistency)
[+] memory_write (silent gate, candidate-only, subject x evidence
    whitelist, audit-on-every-resolution)
```

### Phase 8 — Recall Skeleton (Commit 36)

```
[+] protocol (composite-AND trigger, source whitelist {CORE},
    sustained-tension required, no-spike rule)
[+] ranking (multiplicative score, top-1 only, stable tie-break)
[+] candidate (subject whitelist {SOURCE_TRUST, PROCEDURAL} +
    intensity cap)
```

### Phase 9 — EchoAdapter (Commits 37-38)

```
[+] trust (AdapterTrustRecord with hard gates + multiplicative soft
    composition, TrustBand classification, NeuralSeed-emission red
    line raises at schema construction)
[+] echo (signed mock manifest, observe-only, TrustBand.MEDIUM
    default, emit_observation, emit_neural_seed_directly raises
    constitutional red line)
```

### Phase 10 — End-to-end Dry Simulation (Commits 39-40)

```
[+] runtime/output (SystemOutput 5-value enum + forbidden-literal
    substring guard + ForbiddenOutputViolation)
[+] runtime/dry_sim (pipeline driver, WAIT output, chained audit,
    every reason passes the forbidden-literal guard)
[+] tests/integration/test_dry_simulation_e2e.py (16 cases)
[+] tests/integration/test_forbidden_outputs.py (4 cases)
```

---

## 2. Test, lint, type, forbidden-grep status

```
814 tests passing
pyright strict:                       0 errors
ruff:                                 clean
forbidden imports grep:               clean
forbidden output literal grep:        clean
forbidden output substring guard:     active in every reason path
hash chain re-verify after e2e run:   True
```

---

## 3. Constitutional invariants now code-pinned

### Type-boundary rejections

```
Core payload:
  - 10-value primer palette closed
  - PayloadSeed rejects task verbs + domain tickers
  - NeuralSeed payload uniqueness
  - NeuralSeed.total_intensity computed (not input)

Ingress:
  - Each envelope has Literal event_type
  - No domain raw fields (symbol/venue/market/price)
  - HumanIntent normalized (no raw NL)
  - RecallEvent.subject_class bound to memory taxonomy

Memory:
  - 16-value SubjectClass closed
  - foreign_instance_origin NOT a SubjectClass
  - MemoryRecord.status closed

Numerics:
  - 12 required fields (no-default rule)
  - AllowedRangeSingle <=> both FORBIDDEN immutable invariant
  - Artifact entry keys unique + spec_family consistency
  - dev_only <=> fixture_purpose two-way

Adapters:
  - Channel-binding matrix per capability
  - Incompatible capability pairs rejected
  - execute requires observe
  - NeuralSeed not a legal adapter output

Workspace:
  - Single WORKSPACE_PULSE event type
  - No pulse_type / pulse_category / focus_type / semantic_label
```

### Runtime-raised invariants (raise InvariantViolation /
NumericsGovernanceViolation / ForbiddenOutputViolation)

```
Numerics:
  - NUMERICS_DEV_ONLY_REJECTED_IN_PRODUCTION
  - NUMERICS_DEPENDENCY_UNKNOWN_KEY
  - NUMERICS_DEPENDENCY_CYCLE_DETECTED

Ingress:
  - INGRESS_PROFILE_CAP_INPUT_INVALID

Observer:
  - OBSERVER_EVENT_TYPE_UNKNOWN
  - OBSERVER_EVENT_FAMILY_MATCHES_CATALOG
  - OBSERVER_PERMANENCE_DOWNGRADE_FORBIDDEN
  - OBSERVER_RING_BUFFER_POLICY_MISMATCH
  - OBSERVER_LLM_READ_SCOPE_FORBIDDEN

Recall:
  - RECALL_CANDIDATE_SUBJECT_CLASS_FORBIDDEN

Adapters:
  - ADAPTER_NEURAL_SEED_EMISSION_DETECTED

Runtime:
  - MVP_FORBIDS_EXECUTION_OUTPUTS  (every output reason path)
```

---

## 4. MVP scenario demonstrated

The `run_dry_simulation` driver, given an `EchoAdapter` and an
observation magnitude, produces a single-line audit trail and the
canonical WAIT output:

```
Echo emits ObservationEvent(magnitude=0.8, confidence=0.7)
    -> M1: OBSERVATION_INGESTED
Compile to NeuralSeed (novelty + suspicion contributions,
    profile-capped)
Build pulse from seed (deterministic mapping;
    dominant_payload_mix = unique payloads)
    -> M1: WORKSPACE_PULSE
Recall trigger: not triggered (sustained tension absent,
    memory_echo below threshold)
No ApprovedActionIntent; deontic gate not invoked
Output: WAIT
M1 chain re-verifies; no forbidden literal present
```

---

## 5. Commit ledger (Phase 2-10)

```
Commit 13  observer canonical event catalog
Commit 14  observer hash-chain primitives
Commit 15  observer JSONL append-only ledger
Commit 16  observer permanence policy helpers
Commit 17  observer bounded ring buffer
Commit 18  observer audit-aware reader + 2 numerics events

Commit 19  numerics artifact loader (dev_only mode guard)
Commit 20  numerics cross-key dependency validator
Commit 21  8 v0.1 dev fixtures + load coverage tests

Commit 22  ingress profile cap hierarchy
Commit 23  ingress trapezoidal soft-overlap membership
Commit 24  ingress bootstrap rule schema + MVP registry
Commit 25  ingress deterministic event-to-NeuralSeed compiler

Commit 26  m0 neuron (homonymous bias, no specialist)
Commit 27  m0 synapse (weak band, read-only propagate)
Commit 28  m0 embryo self-field (strict hierarchy)
Commit 29  m0 proto-resonance (5-layer birth invariant)
Commit 30  m0 assembly + AssemblyCensus zero-at-birth
Commit 31  m0 tissue uniform per-payload allocation

Commit 32  workspace single-mechanism pulse emitter

Commit 33  runtime feature flag matrix (22 flags)
Commit 34  deontic hard-stop gate (11 declaratives)
Commit 35  memory write gate (silent, candidate-only)

Commit 36  recall protocol + ranking + candidate guard

Commit 37  adapter trust composition + hard gates
Commit 38  EchoAdapter (signed mock, observe-only)

Commit 39  SystemOutput enum + forbidden-literal guard
Commit 40  dry simulation pipeline + integration tests
```

40 commits, each small and focused; every commit shipped GREEN
(ruff + pyright + pytest + forbidden grep) and pushed.

---

## 6. Items deliberately deferred beyond MVP

Per build plan §2 (non-goals) and the per-phase "deliberately
NOT" sections:

```
- Live exchange / venue integration (forbidden in MVP)
- LLM SDK integration (forbidden in MVP)
- Replay engine (mvp_replay_enabled=false)
- Backup restore (mvp_restore_enabled=false)
- Cross-instance fork / migration
- Memory verified writes (mvp_verified_disabled=true)
- Operator override paths
- M0 learning (learning_enabled=false)
- Sleep cycle (sleep_cycle_enabled=false)
- Cryptographic signature verification (mock manifests only)
- Production numerics matrix (separate from MVP_FEATURE_FLAGS)
- Telegram / operator surface
```

---

## 7. Final hüküm

```
MVP Build Plan: GREEN.
Sentinel Minimum Viable Brain v0.1 is complete.
Every constitutional red line is code-pinned (type rejection or
runtime invariant). 814 tests verify the contract.
```
