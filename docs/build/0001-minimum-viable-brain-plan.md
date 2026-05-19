# 0001 — Minimum Viable Brain Build Plan

> Bu dosya yeni conceptual/numeric belge değildir.
> Bu dosya 22 frozen draft + 2 review sonucunda Minimum Viable Brain'in
> hangi sırayla inşa edileceğini belirleyen build plan'dır.

---

## Status

**Implementation Readiness Review (0002) GREEN sonrası build plan.**

Bu dosya:
- 22 belge + 2 review'un mekanik devamı
- Teknoloji seçimi yapan ilk belge (Python-first)
- Repository structure + package map + 10 phase milestone'ları + CI shape + test discipline
- **Yeni anayasal karar üretmez**; readiness review §11 implementation order'unun **somut kod planı**

Sonraki dosya: gerçek kod (`sentinel/` package + `tests/` + `pyproject.toml`).

---

## 1. Purpose

22 frozen draft belge → 10 phase build plan dönüşümü:
- Repository structure
- Module map
- Phase-by-phase milestone + done definition
- Technology stack (Python-first)
- Test-first discipline
- CI/CD shape
- Feature flag matrix
- Red lines (MVP'de FORBIDDEN olanlar)

Tek cümle: **Bu plan "ne yazılır, hangi sırayla, hangi araçla" sorusunun cevabıdır.**

---

## 2. Non-goals

```
- Yeni conceptual karar üretmek (yasak; 22 belge donmuş)
- Yeni numerics artifact tasarımı (deferred to production phase)
- Production değer setleri (signed numerics artifact ayrı work)
- Live trading / exchange integration (FORBIDDEN_IN_MVP)
- LLM intent_relay implementation (DEFERRED)
- Replay engine full build (DEFERRED)
- Restore/fork/migration paths (DEFERRED)
- Telegram/operator surface (DEFERRED)
- Performance optimization (premature)
- Microservice architecture (premature)
```

---

## 3. Technology Decision

### Stack — Python-first

```
Language:        Python 3.12+
Schema:          Pydantic v2
Testing:         pytest + Hypothesis (property-based)
Lint:            ruff
Type check:      mypy or pyright (pyright tercih — daha hızlı)
Packaging:       uv
Format:          ruff format
Pre-commit:      pre-commit hooks (ruff, type check, invariant tests)
```

### Storage layer (MVP)

```
M1 Ledger:       JSONL append-only file + hash-chain
                 (gerçek DB DEFERRED; ledger tier transitions DEFERRED)
M0 State:        In-memory (synthetic dry simulation; persistence DEFERRED)
M2:              In-memory candidate-only store; verified production DEFERRED
M3:              not implemented in MVP (LLM DEFERRED)
Numerics:        JSON dev fixtures in `sentinel/numerics/fixtures/`
                 dev_only=true marker enforced
```

### Async

```
MVP Phase 1-8:   Synchronous (deterministic, easier to test)
MVP Phase 9+:    asyncio if EchoAdapter event loop needed
                 (otherwise sync throughout MVP)
```

### Rationale

```
- MVB hedefi correctness; performans değil
- Pydantic v2 schema validation + Hypothesis property-based testing
  invariant suite için ideal
- Rust premature; M0 kernel henüz büyük değil
- Go fazla servis-odaklı; modelleme + numerics validation için Python daha uygun
- uv modern, hızlı, lock-file disciplined
- Pyright tip kontrolünde mypy'dan hızlı; CI'de zaman kazanır
```

### Deferred technology decisions (MVB sonrası)

```
- M0 kernel için Rust port (perf bottleneck olursa)
- M2 için SQLite veya DuckDB (gerçek M2 persistence)
- Async event loop genişlemesi
- gRPC/REST API layer (telegram/operator surface gelirse)
```

### Forbidden dependencies (constitutional)

```
- openai / anthropic / langchain / any LLM client library
  → A §6 (LLM dış adapter; MVB'de bağlanmaz)
- ccxt / web3 / exchange API client
  → DEONTIC §8 Rule 1 (no action output; execute capability disabled)
- celery / dramatiq (queueing — DEFERRED)
- fastapi / flask (web layer — DEFERRED)
```

CI bu paketlerin yokluğunu doğrular (negative dependency check).

---

## 4. Repository Structure

```
Senitnal/
├── docs/                                # frozen drafts + reviews
│   ├── conversations/                   # 0001-0021 tasarım soyağacı
│   ├── reviews/
│   │   ├── 0001-phase-closure-consistency-review.md
│   │   └── 0002-implementation-readiness.md
│   └── build/
│       └── 0001-minimum-viable-brain-plan.md   # bu dosya
├── sentinel/                            # ana paket
│   ├── __init__.py
│   ├── constitution/                    # invariant testlerinin kaynağı
│   │   ├── __init__.py
│   │   ├── invariants.py                # 50+ invariant listesi
│   │   └── violations.py                # violation exception types
│   ├── types/                           # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── payload.py                   # PayloadSeed + 10-key palette enum
│   │   ├── neural_seed.py               # NeuralSeed + profile_cap enforce
│   │   ├── events.py                    # ObservationEvent / HumanIntent / InternalShock / Recall
│   │   ├── observer.py                  # ObserverEvent 4-envelope
│   │   ├── memory.py                    # MemoryRecord + 16 subject_class enum
│   │   ├── numerics.py                  # NumericsArtifact + NumericEntry + Dependency
│   │   ├── adapters.py                  # AdapterManifest + capability + channel binding
│   │   └── workspace.py                 # WorkspacePulseEvent (single mechanism)
│   ├── observer/                        # M1 ledger
│   │   ├── __init__.py
│   │   ├── ledger.py                    # JSONL append-only
│   │   ├── hash_chain.py                # chain integrity verify_on_read
│   │   ├── catalog.py                   # canonical event registry (F §19)
│   │   ├── permanence.py                # F §10 permanence policy table
│   │   └── audit_reader.py              # M1_READ_AUDIT_RECORDED kanalı
│   ├── numerics/                        # numerics artifact subsystem
│   │   ├── __init__.py
│   │   ├── loader.py                    # NumericsArtifact yükleme + validation
│   │   ├── validator.py                 # no-default rule + dependency check
│   │   ├── enum_set.py                  # enum_set convention (M §8)
│   │   └── fixtures/                    # dev_only=true dev fixtures
│   │       ├── ingress_compiler_numerics_v0_dev_fixture.json
│   │       ├── memory_write_gate_numerics_v0_dev_fixture.json
│   │       ├── observer_ledger_numerics_v0_dev_fixture.json
│   │       ├── bootstrap_genome_numerics_v0_dev_fixture.json
│   │       ├── recall_protocol_numerics_v0_dev_fixture.json
│   │       └── adapter_trust_numerics_v0_dev_fixture.json
│   ├── ingress/                         # ingress compiler
│   │   ├── __init__.py
│   │   ├── compiler.py                  # event → neural_seed deterministic mapping
│   │   ├── rules.py                     # bootstrap rule families
│   │   ├── soft_overlap.py              # linear membership function (N §6)
│   │   └── profile_caps.py              # N §7 enforcement
│   ├── m0/                              # M0 tissue (minimal)
│   │   ├── __init__.py
│   │   ├── neuron.py                    # neuron + receptor profile
│   │   ├── synapse.py                   # synapse weight + propagation
│   │   ├── tissue.py                    # seed neuron uniform allocation (S §6)
│   │   ├── assembly.py                  # candidate detection; stable_assembly = 0 at birth
│   │   └── self_field.py                # homeostatic > predictive > narrative
│   ├── workspace/
│   │   ├── __init__.py
│   │   └── pulse.py                     # WORKSPACE_PULSE single mechanism
│   ├── gates/                           # epistemic vs deontic
│   │   ├── __init__.py
│   │   ├── deontic.py                   # E §8 hard-stops; default-deny in MVP
│   │   └── memory_write.py              # G §8 matrix; silent gate principle
│   ├── recall/
│   │   ├── __init__.py
│   │   ├── protocol.py                  # memory_echo trigger; top-1; mechanical ranking
│   │   ├── ranking.py                   # T §8 deterministic multiplicative
│   │   └── candidate.py                 # T §14 candidate recall constraints
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── manifest.py                  # manifest validation + capability check
│   │   ├── trust.py                     # adapter_trust band + composition
│   │   └── echo.py                      # EchoAdapter (test-only)
│   └── runtime/
│       ├── __init__.py
│       ├── dry_sim.py                   # end-to-end dry simulation runner
│       ├── feature_flags.py             # MVP flag matrix
│       └── output.py                    # {WAIT, BLOCK, MONITOR, NEED_RECALL, NO_ACTION}
├── tests/                               # test-first discipline
│   ├── __init__.py
│   ├── conftest.py                      # pytest fixtures
│   ├── invariants/                      # constitutional invariant suite
│   │   ├── test_madde_1_to_7.py         # A §1-7 violation tests
│   │   ├── test_adapter_boundary.py     # I + U invariants
│   │   ├── test_llm_boundary.py         # Madde 6 8-layer hub
│   │   ├── test_recall_top1.py          # T core-facing invariants
│   │   ├── test_memory_write_silent.py  # G silent gate
│   │   ├── test_deontic_hardstops.py    # E §8 13 rules
│   │   ├── test_numerics_no_default.py  # M §9
│   │   ├── test_phase_monotonicity.py   # S §16
│   │   └── test_neural_seed_origin.py   # adapter cannot emit
│   ├── schemas/                         # Pydantic schema validation
│   │   ├── test_payload_seed.py
│   │   ├── test_neural_seed.py
│   │   ├── test_events.py
│   │   ├── test_observer_event.py
│   │   ├── test_numerics_artifact.py
│   │   └── test_adapter_manifest.py
│   ├── observer/                        # ledger tests
│   │   ├── test_hash_chain.py
│   │   ├── test_permanence_policy.py
│   │   └── test_canonical_catalog.py
│   ├── numerics/
│   │   ├── test_loader.py
│   │   ├── test_dependency_validator.py
│   │   └── test_dev_fixture_marker.py
│   ├── ingress/
│   │   ├── test_compiler_determinism.py
│   │   ├── test_profile_caps.py
│   │   └── test_soft_overlap.py
│   ├── m0/
│   │   ├── test_seed_equality.py
│   │   ├── test_proto_resonance.py      # 5-layer invariant
│   │   └── test_no_stable_at_birth.py
│   ├── gates/
│   │   ├── test_deontic_default_deny.py
│   │   └── test_memory_write_silent.py
│   ├── recall/
│   │   ├── test_top1_invariant.py
│   │   └── test_human_bypass_blocked.py
│   ├── adapters/
│   │   ├── test_manifest_validation.py
│   │   ├── test_neural_seed_emission_blocked.py
│   │   └── test_echo_adapter.py
│   └── integration/
│       ├── test_dry_simulation_e2e.py
│       └── test_forbidden_outputs.py    # BUY/SELL/EXECUTE never produced
├── pyproject.toml                       # uv + pydantic + pytest + ruff + pyright
├── .pre-commit-config.yaml
├── .github/
│   └── workflows/
│       └── ci.yml                       # ruff + pyright + pytest invariant suite
└── README.md                            # mevcut
```

---

## 5. Package / Module Map

### Dependency direction (one-way)

```
constitution/  ← invariant tanımları (her şeyin temeli)
        ↑
types/         ← schema sözleşmeleri
        ↑
observer/      ← M1 ledger
numerics/      ← N-U artifact loader
        ↑
ingress/       ← compiler (depends on numerics + types)
m0/            ← tissue (depends on types + numerics)
        ↑
workspace/     ← pulse (depends on m0 + observer)
        ↑
gates/         ← deontic + memory_write (depends on m0 + observer + numerics)
recall/        ← protocol (depends on memory + gates + numerics)
        ↑
adapters/      ← manifest + trust + EchoAdapter (depends on types + numerics)
        ↑
runtime/       ← dry_sim (depends on all)
```

**Constitutional rule:** Higher layer **cannot import from lower layer's parent**. types/ never imports from m0/. runtime/ imports from all; nothing imports from runtime/.

---

## 6. Phase 1 — Contracts as Code (week 1-2)

### Amaç

Markdown sözleşmelerini Python tiplerine çevirmek.

### Tasks

```
[ ] sentinel/types/payload.py: PayloadSeed + 10-key primer palette enum
    Fields: payload_key, intensity (0..1 ratio), provenance
    Validators: forbidden extra payload_key; intensity bounded
    
[ ] sentinel/types/neural_seed.py: NeuralSeed
    Fields: payload_seed list, total_intensity, event_profile enum, provenance
    Validators: total_intensity <= profile_cap from numerics
    
[ ] sentinel/types/events.py: 4 ingress event envelope
    ObservationEvent, HumanIntentEvent, InternalShockEvent, RecallEvent
    Required fields per C §6-11
    
[ ] sentinel/types/observer.py: ObserverEvent 4-envelope
    Fields: event_id (uuid), event_family, event_type, payload, provenance
    
[ ] sentinel/types/memory.py: MemoryRecord
    Fields: subject_class enum (16 values), record_id, payload, status,
            provenance, causal_refs, external_corroboration_refs,
            internal_only_refs, timestamps
    
[ ] sentinel/types/numerics.py: NumericsArtifact + NumericEntry + Dependency
    Per M §6-8 + §12
    
[ ] sentinel/types/adapters.py: AdapterManifest
    Fields: adapter_id, version, capabilities, channel_bindings,
            incompatible_with derived, signed parent_chain
    
[ ] sentinel/types/workspace.py: WorkspacePulseEvent
    Single mechanism (A §4)
    
[ ] sentinel/constitution/invariants.py: invariant catalog (50+ MVP REQUIRED)
[ ] sentinel/constitution/violations.py: violation exception types
[ ] tests/schemas/*.py: schema validation tests
[ ] tests/invariants/*.py: invariant tests (all initially failing)
```

### Done definition

```
✓ All schemas validate against spec field lists (compare to docs/*.md)
✓ Forbidden field rejection tests pass:
    - extra primer_payload key → ValidationError
    - BUY/SELL/EXECUTE in any payload field → ValidationError
    - LLM-untouchable fields cannot be set from external context
✓ ~50 MVP REQUIRED invariant tests compile + fail with NotImplementedError
✓ Pre-commit hooks (ruff + pyright) pass on all new files
```

### Exit criteria

```
- pyproject.toml committed with stack pinned
- pre-commit hooks configured
- CI green on schema + invariant skeleton tests
```

---

## 7. Phase 2 — Observer Ledger (week 2-3)

### Amaç

M1 JSONL append-only ledger + hash-chain.

### Tasks

```
[ ] sentinel/observer/ledger.py:
    Append-only JSONL writer (file lock)
    Segment rotation by event count (Q §10 cap)
    Read API (audit-only)
    
[ ] sentinel/observer/hash_chain.py:
    previous_event_hash + event_hash per ObserverEvent
    verify_on_read_required = true enforcement (Q §11)
    chain mismatch → critical alert
    
[ ] sentinel/observer/catalog.py:
    Canonical event registry (F §19)
    Per event_type: family, allowed reasons, required payload fields
    Forbidden: unknown event_type emission
    
[ ] sentinel/observer/permanence.py:
    F §10 permanence policy table as data
    Read-only enforcement (cannot weaken at runtime)
    permanent → ring_buffer_only downgrade BLOCKED
    
[ ] sentinel/observer/audit_reader.py:
    M1_READ_AUDIT_RECORDED emit on every read
    reader_type: human / llm / replay / summarizer / external_audit / internal
    LLM scope restriction enum_set check (Q §15)
    
[ ] tests/observer/*.py
```

### Done definition

```
✓ Append + read round-trip
✓ Hash chain verify
✓ Permanence policy correctly classifies test events
✓ Permanence downgrade attempt rejected (Q §12 monotonic)
✓ M1 read audit captured for every read
✓ LLM read with forbidden scope rejected
```

---

## 8. Phase 3 — Numerics Loader (week 3-4)

### Amaç

8 dev fixture artifact yüklemek + validate etmek.

### Tasks

```
[ ] sentinel/numerics/loader.py:
    Load JSON file → NumericsArtifact
    dev_only=true flag enforcement
    Mode check: production mode rejects dev_only=true
    
[ ] sentinel/numerics/validator.py:
    No-default rule (M §9): every NumericEntry has all required fields
    Dependency validation (M §12): computed_* expression evaluation
    enum_set convention enforcement
    
[ ] sentinel/numerics/fixtures/*.json:
    8 dev fixture artifact:
    - ingress_compiler_numerics_v0_dev_fixture.json
    - replay_protocol_numerics_v0_dev_fixture.json (load-only, replay disabled)
    - memory_write_gate_numerics_v0_dev_fixture.json
    - observer_ledger_numerics_v0_dev_fixture.json
    - backup_strategy_numerics_v0_dev_fixture.json (load-only, restore disabled)
    - bootstrap_genome_numerics_v0_dev_fixture.json
    - recall_protocol_numerics_v0_dev_fixture.json
    - adapter_trust_numerics_v0_dev_fixture.json
    
[ ] NUMERICS_ARTIFACT_STATUS_CHANGED emit on load/reject
[ ] NUMERICS_FAILSAFE_ACTIVATED emit on missing artifact
[ ] tests/numerics/*.py
```

### Done definition

```
✓ 8 dev fixtures load + validate
✓ Missing field artifact rejected (M §9)
✓ Dependency violation rejected (e.g., chain_gap_tolerance > 0)
✓ dev_only=true rejected in production mode
✓ NUMERICS_FAILSAFE_ACTIVATED on missing artifact
```

### Risk

```
⚠ Dev fixture conceptual values from band ranges; not safety-tested.
   MVP simulation only; production loader rejects dev_only=true.
```

---

## 9. Phase 4 — Ingress Compiler Skeleton (week 4-5)

### Amaç

Synthetic ObservationEvent → neural_seed (deterministic).

### Tasks

```
[ ] sentinel/ingress/compiler.py:
    Event → bootstrap_rules match → base_payload_vector
    Scalar modifiers (J §11)
    Profile cap enforcement (N §7)
    Weighted blend + cap (no forced normalization, N §9)
    
[ ] sentinel/ingress/rules.py:
    Minimal bootstrap rule family set (D §19, MVP subset)
    No learned mappings in MVP (count = 0 constitutional, S §20)
    
[ ] sentinel/ingress/soft_overlap.py:
    Linear membership function (N §6, v0.1 default)
    Deterministic; LLM/semantic forbidden
    
[ ] sentinel/ingress/profile_caps.py:
    N §7 hierarchy: Observation ≥ InternalShock ≥ RecallEvent.active ≥
                    RecallEvent.verified ≥ HumanIntent ≥ CandidateRecall
    Enforcement at compiler output boundary
    
[ ] tests/ingress/*.py
```

### Done definition

```
✓ Synthetic ObservationEvent → valid neural_seed
✓ Profile cap enforced (HumanIntent ≤ 0.35; Observation ≤ 1.00 per dev fixture)
✓ Soft-overlap deterministic (same input → same membership)
✓ Forced normalization absent (sum < cap remains as-is)
✓ Adapter direct neural_seed emit → IMMEDIATE REVOKE
   (covered by adapter trust violation test in Phase 9)
```

---

## 10. Phase 5 — Minimal M0 Tissue (week 5-7)

### Amaç

Neuron / synapse / receptor / charge propagation stub.

### Tasks

```
[ ] sentinel/m0/neuron.py:
    Neuron struct + receptor profile (D §4)
    Homonymous bias epsilon enforcement (S §8)
    No specialist neuron at birth (S §8 constitutional)
    
[ ] sentinel/m0/synapse.py:
    Synapse weight (initial weak band, S §7)
    Charge propagation (read-only at MVP; learning OFF)
    Initial weight < stable_path_threshold (constitutional)
    
[ ] sentinel/m0/tissue.py:
    Birth: global_seed_count sampled once → uniform per primer payload
    per_payload_seed_count_divergence_at_birth_max = 0 enforced
    No domain-specific seed allocation
    
[ ] sentinel/m0/assembly.py:
    Candidate detection stub
    stable_assembly_count_at_birth = 0 enforced
    initial_recallable_assembly_count = 0 enforced
    initial_memory_write_eligible_assembly_count = 0 enforced
    
[ ] sentinel/m0/self_field.py:
    Embryo weight bands (S §11)
    homeostatic_weight > predictive_weight > narrative_weight enforced
    
[ ] sentinel/m0/proto_resonance.py:
    5-layer invariant (S §9):
        recallability = 0
        assembly_id_at_birth = none
        persistence_max_ms < stable_assembly.min_persistence_ms
        stability_score_cap < assembly_stabilization_threshold
        memory_write_eligibility = false
    
[ ] tests/m0/*.py
```

### Done definition

```
✓ Birth produces zero stable_assembly
✓ Per-payload seed count uniform (divergence = 0)
✓ Self-field hierarchy invariant
✓ Proto-resonance 5-layer protection enforced
✓ No assembly stabilization at MVP (learning OFF)
✓ Synthetic neural_seed produces M0 charge propagation trace
```

---

## 11. Phase 6 — Workspace Pulse (week 7-8)

### Amaç

WORKSPACE_PULSE üretmek (single mechanism).

### Tasks

```
[ ] sentinel/workspace/pulse.py:
    Single mechanism (A §4 / ATTENTION_WORKSPACE)
    Pulse signature (activation_mass + coherence + persistence)
    No pulse category / pulse type variants
    Audit emit (WORKSPACE_PULSE canonical event)
    
[ ] tests/workspace/*.py
```

### Done definition

```
✓ Single WORKSPACE_PULSE per coherence threshold cross
✓ No pulse type variants (signature only)
✓ Pulse audit captured in M1
✓ Pulse alone cannot trigger action (gate sees but doesn't act)
```

---

## 12. Phase 7 — Gates (week 8-9)

### Amaç

Deontic gate + Memory Write Gate stub.

### Tasks

```
[ ] sentinel/gates/deontic.py:
    Constitutional hard-stops (E §8, 13 rules)
    Default-deny mode in MVP (feature flag: mvp_execute_disabled = true)
    Every ApprovedActionIntent → BLOCK (MVP)
    Kill-switch check
    Audit emit (DEONTIC_BLOCKED / DEONTIC_BYPASS_ATTEMPT events)
    
[ ] sentinel/gates/memory_write.py:
    Subject_class × evidence_axis matrix (G §8)
    Silent gate principle (G §4): no return signal to core
    Candidate-only writes in MVP (feature flag: mvp_verified_disabled = true)
    No verified production
    MEMORY_RECORD_STATUS_CHANGED emit (new_status = candidate)
    
[ ] tests/gates/*.py
```

### Done definition

```
✓ All action attempts blocked by deontic gate (MVP: zero pass)
✓ All write attempts → candidate or rejected (never verified)
✓ Gate silence verified (no core-facing event from gate)
✓ Kill-switch test (kill_switch_active = true → block all)
✓ Deontic hard-stop coverage: each of 13 rules has a violation test
```

---

## 13. Phase 8 — Recall Skeleton (week 9-10)

### Amaç

memory_echo → top-1 RecallRequest skeleton.

### Tasks

```
[ ] sentinel/recall/protocol.py:
    Composite trigger AND (T §5):
        memory_echo > threshold
        + context_signature change > threshold
        + fatigue_trace < threshold
        + budget remaining
        + no global cooldown
    sustained_tension_required = true enforced
    Core-originated only (trigger_source whitelist)
    
[ ] sentinel/recall/ranking.py:
    Mechanical multiplicative score (T §8):
        status_weight × provenance_strength × freshness_dampening
        × (1 - contradiction_penalty) × (1 - habituation_penalty)
        × scope_match_score
    LLM input forbidden
    Semantic input forbidden
    
[ ] sentinel/recall/candidate.py:
    Whitelist subject_classes (T §14): {source_trust, procedural}
    candidate.intensity_multiplier ≤ N.candidate_recall_ratio
    candidate.cooldown ≥ verified.cooldown × 1.5
    
[ ] Recall failure audit-only (T §20)
    RECALL_RESULT_EMPTY: audit only; no core-facing absence payload
    
[ ] tests/recall/*.py
```

### Done definition

```
✓ Human direct recall push BLOCKED (T §19)
✓ Top-k attempt rejected (only top-1 reaches core)
✓ Empty result → audit, no core payload
✓ Candidate recall on forbidden subject_class → rejected
✓ Spike-based trigger (no sustained tension) → rejected
```

---

## 14. Phase 9 — EchoAdapter (week 10-11)

### Amaç

Sahte dış uzuv; ObservationEvent kaynağı.

### Tasks

```
[ ] sentinel/adapters/manifest.py:
    AdapterManifest validation (I §6)
    Signed manifest mock for EchoAdapter
    Capability surface check
    Incompatibility matrix enforcement (I §8 + U §11)
    
[ ] sentinel/adapters/trust.py:
    AdapterTrustRecord (I §11 + U)
    Trust score composition (U §6, multiplicative)
    Hard gates: signature_validity, manifest_hash_integrity,
               neural_seed_emission_count = 0
    Soft scores: channel_binding_compliance, rate_compliance, etc.
    
[ ] sentinel/adapters/echo.py:
    Synthetic ObservationEvent source
    Observe capability only
    Signed mock manifest
    Trust band: medium (manual fixture)
    Channel binding strict
    
[ ] tests/adapters/*.py
    test_neural_seed_emission_blocked:
        EchoAdapter attempts neural_seed → IMMEDIATE REVOKE
        ADAPTER_MANIFEST_STATUS_CHANGED(reason=neural_seed_emission_attempt)
    test_intent_relay_execution_blocked:
        intent_relay attempts execute → IMMEDIATE REVOKE
    test_forbidden_pair_attempt:
        execute + intent_relay declared → manifest REJECTED
```

### Done definition

```
✓ EchoAdapter registers + verifies trust (medium band)
✓ Adapter neural_seed emission attempt → IMMEDIATE REVOKE
✓ Adapter capability override attempt → REJECT
✓ Adapter outside observe channel → quarantine
✓ Forbidden capability pair declaration → manifest REJECTED
```

---

## 15. Phase 10 — End-to-end Dry Simulation (week 11-12)

### Amaç

Full pipeline runs synthetic event end-to-end.

### Tasks

```
[ ] sentinel/runtime/dry_sim.py:
    Driver:
        EchoAdapter generates ObservationEvent
            ↓
        Ingress compiler → neural_seed
            ↓
        M0 charge propagation (read-only learning OFF)
            ↓
        Assembly candidate (no stabilization in MVP)
            ↓
        WORKSPACE_PULSE
            ↓
        memory_echo signal
            ↓
        RecallRequest (if threshold) → recall delivery (if match)
                                     → RECALL_RESULT_EMPTY (else)
            ↓
        Deontic gate evaluation
            ↓
        Output: WAIT / BLOCK / MONITOR / NEED_RECALL / NO_ACTION
    
    Every step audit'lenir → M1 JSONL
    Hash chain valid at end
    
[ ] sentinel/runtime/feature_flags.py:
    MVP flag matrix (§18)
    
[ ] sentinel/runtime/output.py:
    Output enum: {WAIT, BLOCK, MONITOR, NEED_RECALL, NO_ACTION}
    Forbidden: BUY, SELL, EXECUTE, ORDER, SUBMIT, *_REAL
    
[ ] tests/integration/test_dry_simulation_e2e.py
[ ] tests/integration/test_forbidden_outputs.py
```

### Done definition

```
✓ Full pipeline runs synthetic event end-to-end
✓ All audit events captured in M1 (hash chain valid)
✓ Zero action output (every attempt blocked at gate)
✓ Invariant test suite (~50 MVP REQUIRED) passes
✓ Output ∈ {WAIT, BLOCK, MONITOR, NEED_RECALL, NO_ACTION}
✓ Forbidden output strings (BUY/SELL/EXECUTE) never appear in M1
```

### MVP demonstration scenario

```
Scenario: "EchoAdapter sends a synthetic price observation"
    1. Echo emits ObservationEvent(magnitude=0.8, confidence=0.7, source=test)
    2. Compiler maps to NeuralSeed(novelty=0.4, suspicion=0.2)
    3. M0 produces propagation trace (no stable assembly)
    4. WORKSPACE_PULSE emitted (low coherence)
    5. memory_echo below threshold → no RecallRequest
    6. No ApprovedActionIntent generated (M0 didn't reach action competition)
    7. Deontic gate sees nothing to evaluate; default-deny anyway
    8. Output: WAIT (system observing, not acting)
    9. M1 contains: ObservationEvent → NeuralSeed → M0 trace →
                    WORKSPACE_PULSE → OutputEvent(WAIT)
    10. Hash chain validates from genesis to end
```

---

## 16. Test-first Discipline

### Workflow per phase

```
1. Read spec sections referenced in phase
2. Write invariant tests (failing)
3. Write schema tests (failing)
4. Implement minimal code to pass tests
5. Verify edge cases (Hypothesis property-based)
6. Refactor if needed
7. Commit (pre-commit hooks: ruff + pyright + pytest invariants)
```

### Invariant test categories

```
property:    Hypothesis property-based (input → invariant holds)
unit:        Single function/class
integration: Multi-module flow
simulation:  Synthetic event end-to-end
fixture:     Static data (forbidden state, valid state, edge state)
```

### Critical rules

```
- Invariant suite RUNS on every commit (pre-commit + CI)
- No skip / xfail allowed for MVP REQUIRED invariants
- New code without test → blocked at pre-commit
- Schema change → existing fixtures must update (audit trail)
```

---

## 17. CI/CD Shape

### CI workflow (`.github/workflows/ci.yml`)

```yaml
on: [push, pull_request]

jobs:
  lint:
    - ruff check
    - ruff format --check

  type:
    - pyright --strict

  test:
    - pytest tests/schemas/ -v
    - pytest tests/invariants/ -v --strict
    - pytest tests/observer/ -v
    - pytest tests/numerics/ -v
    - pytest tests/ingress/ -v
    - pytest tests/m0/ -v
    - pytest tests/gates/ -v
    - pytest tests/recall/ -v
    - pytest tests/adapters/ -v
    - pytest tests/integration/ -v

  forbidden_imports:
    - assert "openai" not in dependencies
    - assert "anthropic" not in dependencies
    - assert "langchain" not in dependencies
    - assert "ccxt" not in dependencies
    - assert "web3" not in dependencies

  forbidden_outputs:
    - grep -r "BUY\|SELL\|EXECUTE_REAL\|ORDER_SUBMIT" sentinel/
        → if found, FAIL CI (constitutional violation)
```

### Pre-commit hooks

```yaml
- ruff (lint + format)
- pyright (type check)
- pytest tests/invariants/ -x  (invariant test suite must pass)
- yaml-lint, json-lint (numerics fixture files)
```

---

## 18. Feature Flag Matrix

MVP'de hangi capability açık/kapalı:

```python
# sentinel/runtime/feature_flags.py

MVP_FEATURE_FLAGS = {
    # Execute / live action
    "mvp_execute_disabled":          True,    # deontic gate always BLOCK
    "live_exchange_api_enabled":     False,
    "real_market_data_enabled":      False,
    
    # Memory production
    "mvp_verified_disabled":         True,    # MWG: candidate-only
    "memory_writer_auto_verify":     False,
    
    # LLM
    "llm_intent_relay_enabled":      False,
    "llm_translator_loaded":         False,
    
    # Replay
    "replay_engine_enabled":         False,
    "replay_session_creation":       False,
    
    # Restore / fork / migration
    "restore_endpoint_enabled":      False,
    "fork_birth_enabled":            False,
    "migration_birth_enabled":       False,
    
    # Numerics
    "production_numerics_required":  False,   # MVP allows dev_only=true
    "numerics_runtime_mutation":     False,   # forbidden always
    
    # Adapters
    "production_adapters_enabled":   False,
    "echo_adapter_only":             True,
    
    # Operator surface
    "telegram_control_enabled":      False,
    "operator_override_enabled":     False,
    
    # Plasticity
    "learning_enabled":              False,   # M0 learning OFF in MVP
    "sleep_cycle_enabled":           False,
}
```

**Constitutional rule:** Flag matrix `runtime/feature_flags.py`'da merkezi; başka yerden override yok. Production deployment için ayrı production flag matrix (henüz yok).

---

## 19. Done Definition per Phase

Her phase done sayılır iff:

```
1. Tüm phase task'ları checked
2. Tüm phase test'leri pass (pytest tests/<phase>/ -v)
3. Tüm invariant test'leri pass (regression check)
4. CI green
5. Pre-commit clean
6. Code coverage > 80% for new modules
7. Phase done report yazıldı (docs/build/phase-N-report.md - opsiyonel)
```

---

## 20. MVP Red Lines

Bu satırların altına asla geçilmez:

```
1. No BUY / SELL / EXECUTE output
2. No live exchange API
3. No LLM integration
4. No M2 verified production
5. No numerics runtime mutation
6. No cross-instance / fork / migration
7. No replay-driven memory update
8. No operator constitutional override
9. No silent action (every action audited)
10. No bypass of feature flag matrix at runtime
11. No removal of invariant test from suite
12. No skip / xfail of MVP REQUIRED invariant
```

Bunların hepsi CI'de explicit test ile blocked.

---

## 21. Deferred Components (V2+)

MVB sonrası phase'lerde gelecek:

```
V2 — Production Numerics
    - 8 numerics artifact production signed values
    - Multi-signature workflow (M §13)
    - Drift detection threshold
    - Sleep/wake cycle implementation

V3 — Replay Engine
    - Full 5-channel replay (sleep_synapse / habituation / calibration /
                            verification / outcome_alignment)
    - Counterfactual ablation (single + pairwise)
    - replay_survival_score evidence

V4 — Real Adapters
    - One real exchange adapter (paper trading first)
    - SourceTrustRecord production
    - AdapterTrust band promotion
    - Live data ingestion

V5 — LLM Integration
    - LLM intent_relay (limited; Madde 6 boundary tested)
    - HumanIntentEvent ingestion
    - Operator translator surface (Telegram)
    - M1 read audit for LLM access

V6 — Restore / Fork / Migration
    - Real backup / restore pipeline
    - fork_birth + migration_birth implementations
    - Foreign M2 merge
    - Cross-instance trust verification

V7 — Verified Memory Production
    - Full P verification matrix
    - Replay-driven evidence
    - Outcome alignment evidence
    - source_trust + adapter_trust production records
```

---

## 22. First Code Commit Plan

### Commit 0: Build plan accepted

This document.

### Commit 1: Project skeleton

```
pyproject.toml (Python 3.12, uv, deps: pydantic, pytest, hypothesis,
                ruff, pyright)
.pre-commit-config.yaml
.github/workflows/ci.yml
sentinel/__init__.py
tests/__init__.py
tests/conftest.py
README.md update (build phase section)
```

### Commit 2: Constitution + invariants skeleton

```
sentinel/constitution/__init__.py
sentinel/constitution/invariants.py (50+ invariant catalog)
sentinel/constitution/violations.py (exception types)
tests/invariants/test_madde_1_to_7.py (skeleton; all xfail until impl)
```

### Commit 3+: Phase 1 — Contracts as Code

```
sentinel/types/payload.py
sentinel/types/neural_seed.py
sentinel/types/events.py
sentinel/types/observer.py
sentinel/types/memory.py
sentinel/types/numerics.py
sentinel/types/adapters.py
sentinel/types/workspace.py
tests/schemas/test_*.py (all passing)
```

### ... ve devamı

Her phase için ayrı commit dizisi (TDD discipline).

---

## 23. Final Hüküm

```
═══════════════════════════════════════════
Minimum Viable Brain Build Plan Hükmü
═══════════════════════════════════════════

Status:                          READY FOR IMPLEMENTATION
Technology stack:                Python 3.12+ / Pydantic v2 / pytest /
                                 Hypothesis / ruff / pyright / uv
Repository structure:            Defined (§4)
Module map:                      One-way dependency graph (§5)
Phase order:                     10 phase (§6-15)
Estimated MVB duration:          ~12 weeks single dev
Test-first discipline:           Mandatory
CI shape:                        Defined (§17)
Feature flag matrix:             Centralized (§18)
Red lines:                       12 enforced via CI (§20)
Deferred components:             V2-V7 roadmap (§21)
First commit plan:               Ready (§22)

═══════════════════════════════════════════
Sıradaki:
docs/build/0001 GREEN sonrası gerçek kod.
İlk gerçek commit: Commit 1 (project skeleton).
═══════════════════════════════════════════
```

---

## Notlar

- Bu build plan `Frozen` durumdadır. Implementation phase'de değişiklik
  gerekirse `0002-...` revision olarak kayıtlanır.
- 22 belge + 2 review + 1 build plan = 25 dosya pipeline.
- Build plan accepted → ilk gerçek kod commit ile başlar (`pyproject.toml`,
  project skeleton).
- MVB tamamlandığında V2 (production numerics) için ayrı build plan
  (`docs/build/0002-production-numerics-plan.md`) yazılır.

**Build plan GREEN. Gerçek kod başlayabilir.**

> *Belge fazı kapandı. Plan kapandı. Sıradaki: dokunulabilen ilk dosya — `pyproject.toml`.*
