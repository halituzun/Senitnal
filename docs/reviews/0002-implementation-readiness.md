# 0002 — Implementation Readiness Review

> Belge fazı kapandı. Bu dosya yeni tasarım üretmez.
> Bu dosya 22 frozen draft belgesinin hangi parçalarının implementation'a
> hazır olduğunu sınıflandırır.

---

## Status

**Phase Closure Review (0001) GREEN sonrası implementation readiness denetimi.**

Bu rapor:
- Yeni conceptual/numeric belge değildir.
- Kod yazımına **doğrudan başlangıç** değildir.
- "Şu an ne kodlanabilir?" sorusunun mekanik cevabıdır.

Sonraki dosya: `docs/build/0001-minimum-viable-brain-plan.md`
(yalnız bu review GREEN çıkarsa).

---

## 1. Purpose

22 belge frozen draft v0.1 kapanışından sonra, **MVP (Minimum Viable Brain)**
inşasına geçmeden önce şu sorulara cevap üretmek:

```
- Hangi parça yeterince net ki Pydantic/model olarak yazılabilir?
- Hangi parça stub interface ile başlayabilir?
- Hangi parça synthetic event ile test edilebilir?
- Hangi parça production değer bekliyor ama kavramsal hazır?
- Hangi parça MVP dışına atılmalı?
- Hangi parça ilk sürümde KESİNLİKLE yasak?
- Hangi invariant testleri kod başlamadan yazılmalı?
- 121 open question hangi sınıflara dağılır?
```

Tek cümle: **Bu review "artık neyi inşa edebiliriz?" sorusunun mekanik cevabıdır.**

---

## 2. Scope

### Dahil

- A-U conceptual + numerics belgelerin **implementation-blocking** vs
  **dev-OK** vs **deferred** sınıflandırması
- Constitutional invariant'ların test edilebilirliği
- Numerics artifact'lerin dev fixture ile MVP'de kullanılabilirliği
- 121 open question'ın 5 triage sınıfına yerleştirilmesi
- İlk 10 build phase önerisi

### Hariç

- Production değerler (signed artifact içeriği)
- Yeni tasarım kararı
- Spec değişiklik önerisi
- Kod
- Teknoloji seçimi (Python/Rust/Go vb.) — bu build plan'in kararı

---

## 3. Readiness Labels

Her component aşağıdaki 6 etiketten birini alır:

| Label | Anlam |
|-------|-------|
| `READY_FOR_SCHEMA` | Pydantic/model/event schema yazılabilir; field set ve validation kuralları net |
| `READY_FOR_STUB` | Interface + no-op/stub implementation yazılabilir; sözleşme net |
| `READY_FOR_SIMULATION` | Synthetic event ile test edilebilir; davranış kanıtlanabilir |
| `NEEDS_SIGNED_NUMERIC_VALUES` | Kavram hazır; production değer (signed artifact) bekliyor; dev fixture ile MVP'de simüle edilebilir |
| `DEFERRED_FROM_MVP` | MVP dışında; sonraki sürümler |
| `FORBIDDEN_IN_MVP` | İlk sürümde özellikle yasak (constitutional risk) |

Bir component birden fazla etiket alabilir (örn. SCHEMA + STUB +
NEEDS_SIGNED_VALUES); en sıkı etiket dominant.

---

## 4. MVP Required Components — READY hub

MVP'nin **çıktısı**: synthetic ObservationEvent al → neural_seed üret →
M0'da iz bırak → WORKSPACE_PULSE yay → M1'e audit yaz → en fazla
`WAIT/BLOCK/MONITOR/NEED_RECALL/NO_ACTION` dön. **Hiçbir live action yok.**

Bu hedef için gerekli componentler:

| Component | Source spec | Label | Notlar |
|---|---|---|---|
| Core domain types (PayloadSeed, NeuralSeed) | B + C + N | READY_FOR_SCHEMA | 10-key primer palette enum; intensity ratio'lar |
| Ingress event envelopes (ObservationEvent / HumanIntentEvent / InternalShockEvent / RecallEvent) | C §6-11 | READY_FOR_SCHEMA | 4 envelope, profile flag |
| ObserverEvent envelope (4-zarf) | F §7 | READY_FOR_SCHEMA | event_id, family, type, payload, provenance, hash chain |
| M1 JSONL ledger + hash-chain | F §6 + Q §11 | READY_FOR_STUB | Append-only file, segment rotation cap; tier transition DEFERRED |
| NumericsArtifact schema + validator | M §6-8 | READY_FOR_SCHEMA | NumericEntry no-default rule, enum_set unit, computed_* deps |
| Ingress compiler skeleton (deterministic mapping) | J §4-12 + N | READY_FOR_STUB + NEEDS_SIGNED_NUMERIC_VALUES | Dev fixture artifact; soft-overlap linear membership; bootstrap rule families |
| Synthetic ObservationEvent → neural_seed pipeline | C + J + N | READY_FOR_SIMULATION | End-to-end dry test |
| Minimal M0 tissue (neuron/synapse/receptor profile) | D §4-12 + S | READY_FOR_STUB + NEEDS_SIGNED_NUMERIC_VALUES | Seed neuron count uniform; initial weights weak |
| Workspace pulse | A §4 + ATTENTION_WORKSPACE | READY_FOR_STUB | Single mechanism; signature not type |
| Deontic gate stub | E §8 + §11 | READY_FOR_STUB | All execution BLOCKED in MVP (default-allow disabled) |
| Memory Write Gate stub | G §8 + §15 + P | READY_FOR_STUB | Silent gate principle; candidate-only writes (no verified production in MVP) |
| Recall request/result skeleton (top-1) | H §6 + §8 + T | READY_FOR_STUB | Synthetic memory_echo trigger; mechanical ranking; failure audit-only |
| EchoAdapter (test-only) | I §15 + U §22 | READY_FOR_STUB + READY_FOR_SIMULATION | Sahte observation source; signed manifest mock; observe-only capability |
| Constitution invariant test suite | A 7 madde | READY_FOR_SCHEMA | Her madde 1+ violation test; bkz. §8 |
| Common forbidden field validators | tüm "Forbidden" listeleri | READY_FOR_SCHEMA | Cross-document harvested |

**Sonuç:** 15 component MVP'ye girer; hepsi en azından SCHEMA + STUB
seviyesinde implementable. 6'sı NEEDS_SIGNED_NUMERIC_VALUES — dev fixture
ile MVP simulation mümkün.

---

## 5. MVP Deferred Components — DEFERRED hub

Kavramsal olarak tamam ama MVP'ye girmiyor:

| Component | Source spec | Reason for deferral |
|---|---|---|
| Full replay engine + 5 effect channels | K + O | Self-deception risk; M0 update + memory verification + outcome alignment kapsamlı; MVP "iz bırak ama replay yapma" |
| Replay-driven M2 verification | G §10-11 + K §13 + O §17 | Verified production MVP'de yok; replay survival weight uygulanamaz |
| Foreign M2 merge | L §18 + R §17 + P §16 | Cross-instance; MVP single-instance |
| Fork / migration restore | L §15 + R §14-15 + S §23 | Multi-instance scenario; MVP fresh-only |
| Backup restore (gerçek) | L + R | RestoreManifest validation pipeline; MVP'de M1 sadece append |
| Real external adapters (exchange APIs vb.) | I + U | Live data + signed manifest enforcement; MVP EchoAdapter only |
| LLM intent_relay (gerçek translator) | A §6 + I §6 | Madde 6 boundary 8-katman test gerek; MVP'de LLM yok |
| Memory writer auto-verification | P §18 | Whitelist enforcement + admin signature workflow; MVP'de sadece candidate |
| Adapter trust promotion | U §17 | Clean window + reverification cycle; MVP trust statik |
| Numerics artifact rollback path | M §15 | Rollback only to previous verified; MVP fresh-load only |
| Telegram / operator control surface | DEONTIC §15 kill-switch detay | Operator audit channel; MVP CLI/file-based |
| Sleep/wake transition (gerçek) | D §17 + BOOTSTRAP §17 + O §6 | Plasticity phase transition; MVP boot_phase only |
| Snapshot windows / tier transitions | Q §13 | Lossless tier migration; MVP single-tier hot storage |
| Forgetting attack detection (gerçek) | L §22 + Q §17 + R §19 | Composite signal; MVP audit-only |

**Sonuç:** 14 component deferred; MVP scope dışı. Kavramsal tamamlık var,
implementation MVP'den sonraki sprint'lere.

---

## 6. FORBIDDEN_IN_MVP — kırmızı hat

İlk sürümde **kesinlikle yasak**:

```
1. Any BUY / SELL / EXECUTE output
   → MVP output set: {WAIT, BLOCK, MONITOR, NEED_RECALL, NO_ACTION}
   → BUY/SELL gibi action verb output yasak (DEONTIC §8 Rule 1+2)

2. Live exchange API calls
   → execute capability disabled by default; deontic gate hard-block

3. Real market data ingestion
   → EchoAdapter only; production data adapter MVP-out

4. LLM API integration
   → intent_relay capability disabled; Madde 6 yansıması

5. M2 verified status production
   → tüm yeni M2 records candidate (P §13); MVP'de verified geçiş yok
     (Memory Write Gate stub her zaman candidate döner)

6. Numerics artifact runtime mutation
   → M §3: signed artifact only; runtime config değil
   → MVP'de hot-reload yok; restart-required

7. Cross-instance import / fork / migration
   → R §14-15; single-instance MVP

8. Adapter capability promotion at runtime
   → I §13: immutable signed manifest; MVP'de yeni adapter yalnız
     restart-time registration

9. Replay-driven memory update
   → O §17: replay_survival_weight = 0 default; MVP'de replay disabled

10. Operator override of constitutional rules
    → A §6 + DEONTIC §8 Rule 10
```

**Bu 10 madde MVP test suite'inde explicit violation test'i olarak yazılır.**

---

## 7. Artifact / Schema Readiness

Aşağıdaki schema'lar **kod başlamadan önce yazılır**. Her biri SCHEMA layer.

### Domain schemas

```
PayloadSeed:
    payload_key: enum (10-key primer palette: suspicion / novelty / aversion /
                       attraction / contradiction / urgency / memory_echo /
                       fatigue_trace / pain_trace / reward_trace)
    intensity: float in [0, 1]
    provenance: ProvenanceRef
    source spec: B + C + N §3
    forbidden: extra payload_key beyond palette (constitutional)

NeuralSeed:
    payload_seed: list[PayloadSeed]
    total_intensity: float ≤ profile_cap (N §7)
    event_profile: enum (ObservationEvent / HumanIntentEvent /
                        InternalShockEvent / RecallEvent.verified /
                        RecallEvent.active / CandidateRecall)
    provenance: ProvenanceRef
    source spec: C + J + N

ProvenanceRef:
    source_id, adapter_id (if applicable), event_id_chain, signed_hash
    foreign_instance_origin: optional, permanent if present
    source spec: B §10 + L §10

ObservationEvent / HumanIntentEvent / InternalShockEvent / RecallEvent:
    structured event envelope per C §6-11
    each carries provenance + magnitude + confidence + timestamp
```

### Ledger schemas

```
ObserverEvent (F §7 — 4-zarf):
    event_id (uuid)
    event_family: enum (neural | attention | memory | ingress | bootstrap |
                       deontic | replay | ledger_meta)
    event_type: enum (canonical event catalog)
    payload: type-specific dict
    provenance: source + audit chain + signed_hash
    timestamp + permanence_policy ref

CanonicalEventCatalog:
    Tüm canonical event tipleri F §19'dan harvested
    Her event_type için: permanence (F §10), allowed reason values,
                         required payload fields
```

### Artifact schemas

```
NumericsArtifact (M §6-7):
    artifact_type: numerics_artifact
    spec_family: enum (ingress_compiler / replay_protocol / memory_write_gate /
                      observer_ledger / backup_strategy / bootstrap_genome /
                      recall_protocol / adapter_trust)
    owning_spec_ref: string
    numerics_version: string
    signed: external (signature + parent_chain)
    entries: list[NumericEntry]

NumericEntry (M §8):
    key: string
    value: any
    unit: enum (count / ms / bytes / ratio / percentage / enum / enum_set /
               band_name / bool)
    allowed_range: {min, max} or {set} or {single}
    directionality: enum (higher_is_stricter / lower_is_stricter /
                         bidirectional_sensitive / neutral)
    change_class_if_increased: enum
    change_class_if_decreased: enum
    requires_human_approval: bool
    dependencies: list[NumericDependency]
    numeric_risk_family: enum
    spec_family: string
    owning_spec_ref: string

NumericDependency (M §12):
    target_key, relationship (8 enum value),
    expression (for computed_*), factor, rationale

MemoryRecord (B §3 + G §15):
    subject_class: enum (16 values)
    record_id
    payload (type-specific)
    status: enum (candidate / verified / active / quarantined / superseded /
                 rejected / expired)
    provenance: ProvenanceRef
    causal_refs / external_corroboration_refs / internal_only_refs
    timestamps (created_at / verified_at / expires_at / refresh_required_at)

AdapterManifest (I §6):
    adapter_id, version
    capabilities: enum_set
    channel_bindings: per-capability dict
    incompatible_with: derived
    signed (signature + parent_chain)
    operator_identity_ref
```

### Schema readiness summary

```
READY_FOR_SCHEMA: 11/11 above types
SCHEMA blockers: 0
Production blockers: 0 (only signed values needed downstream)
```

---

## 8. Invariant Test Readiness

Her constitutional kırmızı çizgi **test edilebilir** olmalı. Code öncesi
test suite yazılır; kod test'leri geçirmek zorundadır.

### Harvested invariants (top 30, full list 100+)

| Invariant | Source | Testable | Type |
|---|---|---|---|
| Adapter cannot emit neural_seed | I §15 + U §16 | YES | property + simulation |
| LLM cannot produce RecallEvent | H §5 + T §5 + A §6 | YES | property |
| LLM cannot execute | E §8 Rule 4 + U §15 | YES | property + integration |
| Core-facing recall top-1 | H §6 + T §7 | YES | property |
| Permanent event cannot be sampled | Q §6 + §9 | YES | property |
| Missing numerics cannot fail-open | M §11 + every Nx §22-23 | YES | integration |
| Human intent cannot bypass core | A §6 + H §5 + T §19 | YES | property + integration |
| Memory Write Gate is silent | G §4 | YES | property (no return signal to core) |
| Deontic Gate acts at action boundary only | E §4 | YES | property |
| Top-k recall cannot reach core | H §6 + T §7 | YES | property |
| Adapter neural_seed = immediate revoke | U §16 | YES | integration + simulation |
| Capability incompatibility cannot be overridden | I §8 + U §11 | YES | property |
| Forked instance cannot claim identity continuity | DEONTIC Rule 12 + R §14 + U §20 | YES | integration |
| restore_with_missing_history cannot claim full identity | DEONTIC Rule 13 + R §13 | YES | integration |
| Phase monotonicity (boot → stab → cons only forward) | S §16 | YES | property |
| M1 chain gap = 0 for full identity | R §12 | YES | integration |
| AdapterTrust upper-bounds SourceTrust | U §5 + §19 | YES | property |
| SourceTrust cannot raise AdapterTrust | U §5 + §19 | YES | property |
| Hard gates not soft scores (signature/manifest_hash/neural_seed_emission) | U §6 | YES | property |
| Permanent log lossless invariant | Q §10 + §18 | YES | property + integration |
| Compaction hash verify before/after required | Q §18 | YES | integration |
| Critical alert cannot be suppressed | Q §14 | YES | property |
| Verified status is sticky (demote > promote threshold) | P §14 | YES | property |
| Foreign provenance permanent | B §10 + L §10 | YES | property |
| Seed equality at birth (per_payload_divergence = 0) | S §6 | YES | property + simulation |
| Stable assembly empty at birth | S §10 | YES | property + simulation |
| Replay cannot trigger replay (chain depth = 0) | O §19 | YES | property + simulation |
| Real outcome > replay survival (per-subject) | O §17 + P §17 | YES | property |
| Replay budget reset forbidden after restore | O §7 + R §18 + T §10 | YES | integration |
| Numerics LLM-untouchable (Madde 6) | M Violation Test 11 | YES | property |

### Test readiness summary

```
READY_FOR_PROPERTY_TEST: ~80 invariants
READY_FOR_INTEGRATION_TEST: ~20 invariants
READY_FOR_SIMULATION: ~15 invariants
MVP REQUIRED: ~50 invariants (core + adapter + gate + LLM)
MVP DEFERRED: ~30 invariants (replay-specific + fork/migration)
NOT_TESTABLE_AT_MVP (needs production deps): ~5 invariants
```

**Critical rule:** invariant test suite **kod öncesi yazılır** ve **her zaman çalışır**.
İlk kod commit'i bu suite'in en az `MVP REQUIRED` subset'ini geçer.

---

## 9. Numerics Artifact Readiness

8 numerics artifact (N-U) için durum:

| Artifact | Schema | Conceptual | Production Values | MVP Use |
|---|---|---|---|---|
| N (Ingress Compiler) | READY | READY | NEEDED for production; dev fixture for MVP | YES (MVP core path) |
| O (Replay Protocol) | READY | READY | NEEDED for production | DEFERRED (replay disabled in MVP) |
| P (Memory Write Gate) | READY | READY | NEEDED; dev fixture for MVP | YES (candidate-only path) |
| Q (Observer Ledger) | READY | READY | NEEDED; dev fixture for MVP | YES (M1 retention + hash-chain) |
| R (Backup Strategy) | READY | READY | NEEDED for production restore | DEFERRED (restore MVP-out) |
| S (Bootstrap Genome) | READY | READY | NEEDED for birth; dev fixture for MVP | YES (SELF_GENESIS path) |
| T (Recall Protocol) | READY | READY | NEEDED; dev fixture for MVP | YES (top-1 recall stub) |
| U (Adapter Trust) | READY | READY | NEEDED; dev fixture for MVP | YES (EchoAdapter trust) |

### Dev fixture artifact naming convention

Production değer setine sahip olmadan MVP'de kullanılacak fixture:

```
naming: <spec_family>_numerics_v0_dev_fixture.json

required fields:
    artifact_type: numerics_artifact
    spec_family: <name>
    numerics_version: v0-dev
    signed: false              # explicit "dev_only_unsigned_fixture" marker
    dev_only: true             # MVP flag
    fixture_purpose: "MVP dry simulation only; NOT for production"
    entries: <conceptual values from spec band ranges>

forbidden:
    used in production runtime (loader rejects dev_only=true if not MVP mode)
    referenced from RestoreManifest (R §11 signature_validation_required)
```

### MVP numerics loader requirements

```
1. Load 5 dev fixture artifacts (N, P, Q, S, T, U)
2. Validate against NumericsArtifact + NumericEntry schemas
3. Enforce no-default rule (every entry has all required fields)
4. Enforce dependency invariants (computed_* expressions evaluated)
5. Refuse load if dev_only=true AND mode=production
6. Refuse load if signed=true AND signature invalid (production path)
7. Emit NUMERICS_ARTIFACT_STATUS_CHANGED event on load/reject
```

---

## 10. Open Questions Triage

121 open question (phase closure review 0001 §L).
5 triage sınıfı:

### BLOCKS_SCHEMA (kod başlamadan önce çözülmeli)

**Sayı:** ~0
**Sebep:** Tüm domain schema'ları conceptual seviyede tam; spec'ler
field set'i veriyor.

### BLOCKS_MVP_SIMULATION (dev fixture ile çözülebilir)

**Sayı:** ~35
**Örnekler:**
- N exact band cutoff values (linear membership intervals)
- P exact `candidate_max_age_ms` per subject_class
- Q exact `ring_buffer.window_ms` per family
- S exact `seed_neurons_per_primer_payload` band
- T exact `memory_echo_threshold_for_recall_request`
- U exact trust band cutoff scores

**Çözüm yolu:** Dev fixture artifact'lerinde conceptual band'lardan
**makul tahmin değerleri** kullan. MVP "ne yaptığını" kanıtlar; "doğru
değerleri" kanıtlamaz.

### BLOCKS_PRODUCTION (signed artifact için karara bağlanmalı)

**Sayı:** ~50
**Örnekler:**
- Production seed count exact value
- Production replay budget caps
- Production storage tier transition cadence
- Multi-signature requirement detayları (M §13)
- Trust decay function shape (linear vs exponential vs step)
- Cross-instance trust verification protocol detayı
- Foreign event trusted source whitelist içeriği

**Çözüm yolu:** MVP sonrası phase'de **safety review + benchmarking + signed
artifact production runs**.

### DOES_NOT_BLOCK_MVP (implementation gözden geçirir)

**Sayı:** ~25
**Örnekler:**
- Drift detection threshold exact ms
- Cleanup window (deprecated → archived)
- Update direction asymmetry ratio exact values
- INGRESS_NO_RULE_MATCH event production noise tradeoff
- Compaction cadence
- High_explicit_emergency band semantik (U §27 patch sonrası clarified)

**Çözüm yolu:** Implementation phase'de benchmark + tuning; MVP'de default
makul değer + audit'le iz bırakma.

### DEFERRED_RESEARCH (MVP + production sonrası araştırma)

**Sayı:** ~11
**Örnekler:**
- Sigmoid/nonlinear membership function tam parametre setleri
- Constitutional shift event taxonomy genişletme
- Higher-order ablation (>=3) için constitutional amendment path
- Multi-instance trust verification protocol formal spec
- Sleep cycle ile fatigue recovery'nin tam matematiği

**Çözüm yolu:** Sentinel V2+ phases; MVP scope dışı.

### Triage summary

```
BLOCKS_SCHEMA:               0
BLOCKS_MVP_SIMULATION:      ~35  (dev fixture'larla çözülür)
BLOCKS_PRODUCTION:          ~50  (signed artifact production)
DOES_NOT_BLOCK_MVP:         ~25  (default value + audit)
DEFERRED_RESEARCH:          ~11  (V2+)

TOTAL:                     ~121
```

**Sonuç:** Hiçbir open question MVP schema/simulation katmanını bloke
etmiyor. ~85'i dev fixture + makul default ile MVP'de çalıştırılabilir.
~50'si production-ready için signed value gerekir. ~11 araştırma.

---

## 11. Implementation Order Recommendation

10 phase, sıralı. Her phase önce **test yazılır**, sonra implementation.

### Phase 1 — Contracts as Code

```
- Pydantic / dataclass / typed dict (dil-bağımsız sözleşmeler)
- Domain schemas (§7): PayloadSeed, NeuralSeed, ObservationEvent,
                       HumanIntentEvent, InternalShockEvent, RecallEvent,
                       ObserverEvent, NumericsArtifact, NumericEntry,
                       MemoryRecord, AdapterManifest, WorkspacePulseEvent
- Enum registries: primer_payload (10), subject_class (16), event_family (8),
                  capability (5), trust_band (6), permanence_policy (4)
- Forbidden field validators (Madde 6 — LLM-untouchable fields)
- Invariant test suite skeleton (~50 MVP REQUIRED tests, all failing initially)

Exit criteria:
    All schemas validate against spec field lists
    Invariant tests compile and fail with NotImplementedError
    Forbidden field rejection works
```

### Phase 2 — Observer Ledger

```
- JSONL append-only ledger writer
- Hash-chain segmentation (Q §11)
- Permanence policy table (F §10) — read-only enforcement
- Event family routing
- Canonical event catalog (F §19) registry
- M1 read API (audit-only; reader_type discriminator per Q §15)
- M1_READ_AUDIT_RECORDED + LEDGER_STATE_CHANGED emit

Exit criteria:
    Append/read tests pass
    Hash chain verify pass
    Permanence policy correctly classifies test events
    M1 read audit captured for every read
```

### Phase 3 — Numerics Loader + Validator

```
- NumericsArtifact + NumericEntry schemas (M §8) implemented
- No-default rule enforcer (any missing field → reject)
- Dependency validator (computed_* expressions evaluated)
- 8 dev fixture artifacts (N, O, P, Q, R, S, T, U) prepared with conceptual
  band-derived values
- dev_only=true flag enforcement
- NUMERICS_ARTIFACT_STATUS_CHANGED emit on load/reject

Exit criteria:
    8 dev fixtures load and validate
    Missing-field artifact rejected
    Dependency violation rejected (e.g., M1 gap > 0 test, asimetri ihlali)
    NUMERICS_FAILSAFE_ACTIVATED triggers on missing artifact
```

### Phase 4 — Ingress Compiler Skeleton

```
- Deterministic event → neural_seed mapping (J §4-12)
- 4 ingress profile pipeline (Observation / HumanIntent / Recall / Shock)
- N numerics fixture'ı yüklü; profile caps + soft-overlap bands enforced
- Bootstrap rule family stub (D §19 minimal rule set)
- Mechanical ranking (T §8) shadow-implementation (recall path için)
- Adapter neural_seed forbidden — every emit rejected + audit

Exit criteria:
    Synthetic ObservationEvent → valid neural_seed
    Profile cap enforced
    Soft-overlap membership deterministic
    Adapter direct neural_seed emit blocked (U §16 immediate revoke triggered)
```

### Phase 5 — Minimal M0 Tissue

```
- Neuron + synapse + receptor profile structs (D §4)
- Seed neuron count per primer payload (S §5-6 invariant)
- Initial synaptic weight bands (S §7)
- Charge propagation (read-only at MVP; learning DEFERRED)
- Assembly candidate detection stub (no stable_assembly at birth)
- proto-resonance field stub (S §9 — 5-layer protection enforced)

Exit criteria:
    Birth produces zero stable_assembly (S §10 invariant)
    Per-payload seed count divergence = 0 verified
    Proto-resonance recallability=0, assembly_id=none enforced
    No assembly stabilization at MVP boundary (learning OFF)
```

### Phase 6 — Workspace Pulse

```
- WORKSPACE_PULSE event signature (A §4 + ATTENTION_WORKSPACE)
- Single mechanism; pulse type forbidden
- Activation mass + coherence + persistence scoring
- Pulse emission audit

Exit criteria:
    Single WORKSPACE_PULSE per coherence threshold cross
    No pulse type variants (signature only)
    Pulse audit captured in M1
```

### Phase 7 — Gates (stubs)

```
- Deontic gate (E §11):
    Constitutional hard-stops (§8) all enforced
    Default-deny mode in MVP (all ApprovedActionIntent → BLOCK)
    Kill-switch check
    Audit emit for every gate decision

- Memory Write Gate (G §8 + P):
    Subject_class × evidence_axis matrix structured
    Candidate-only writes in MVP (verified path DEFERRED)
    Silent gate (no return signal to core)
    MEMORY_RECORD_STATUS_CHANGED emit

Exit criteria:
    All action attempts blocked by deontic gate (MVP: zero pass)
    All write attempts result in candidate or rejected (never verified)
    Gate silence verified (no core-facing event from gate)
```

### Phase 8 — Recall Skeleton

```
- memory_echo trigger composite signal (T §5)
- core-originated RecallRequest (no external bypass)
- Mechanical ranking (T §8)
- Top-1 RecallEvent emission only (core-facing)
- Recall failure audit-only (RECALL_RESULT_EMPTY)
- Status-based suppression (quarantined/rejected/expired)

Exit criteria:
    Human direct recall push blocked (T §19 invariant)
    Top-k attempt rejected (only top-1 reaches core)
    Empty result → audit, no core payload
```

### Phase 9 — EchoAdapter

```
- Sahte ObservationEvent source
- Signed manifest mock (U §9 validation passes)
- observe capability only (intent_relay/execute/memory_writer/recall_provider
  declared incompatible → manifest rejected if declared)
- Trust band: medium (manual fixture)
- Rate limit + clean window simulation
- Channel binding violation test

Exit criteria:
    EchoAdapter registers + verifies trust
    Adapter neural_seed emission attempt → IMMEDIATE REVOKE
    Adapter capability override attempt → REJECT
    Adapter outside observe channel → quarantine
```

### Phase 10 — End-to-end Dry Simulation

```
EchoAdapter → ObservationEvent
            → ingress compiler → neural_seed
            → M0 charge propagation
            → assembly candidate (no stabilization in MVP)
            → WORKSPACE_PULSE
            → memory_echo signal
            → RecallRequest (if threshold)
            → recall delivery (if match) or RECALL_RESULT_EMPTY
            → deontic gate evaluation
            → output: BLOCK / WAIT / MONITOR / NEED_RECALL / NO_ACTION

Exit criteria:
    Full pipeline runs synthetic event end-to-end
    All audit events captured in M1
    Hash chain valid
    Zero action output (every attempt blocked at gate)
    Invariant test suite (~50 MVP REQUIRED) passes
```

### Implementation order summary

```
Phase 1: Contracts as Code           (week 1-2)
Phase 2: Observer Ledger             (week 2-3)
Phase 3: Numerics Loader             (week 3-4)
Phase 4: Ingress Compiler Skeleton   (week 4-5)
Phase 5: Minimal M0 Tissue           (week 5-7)
Phase 6: Workspace Pulse             (week 7-8)
Phase 7: Gates                       (week 8-9)
Phase 8: Recall Skeleton             (week 9-10)
Phase 9: EchoAdapter                 (week 10-11)
Phase 10: End-to-end Dry             (week 11-12)
```

Tahmini MVP: ~12 hafta (single dev; parallel work daha hızlı).

---

## 12. Risk Register for First Code

İlk kod commit'i başlamadan önce farkındalık:

| Risk | Source | Mitigation |
|---|---|---|
| Schema'da Madde 6 ihlali (LLM-touchable field unutulur) | A §6 | Forbidden field validator + invariant test 28 (Madde 6 LLM-untouchable) |
| Permanent event accidentally drop edilir | Q §10 monotonic | Permanence policy enforced at write boundary; test 6 (permanent event TTL forbidden) |
| Adapter neural_seed emit eder | U §16 | Compiler input boundary check + invariant test (immediate revoke); integration test mandatory |
| Memory Write Gate verified production yapar (MVP'de yasak) | G §8 | MVP feature flag: `mvp_verified_disabled = true`; tüm verified geçişi candidate'a düşürür |
| Numerics dev fixture production'a sızar | M §11 | Loader `dev_only=true` flag enforcement; production mode'da reject |
| Restore/fork path MVP'de açık kalır | R §13-15 | MVP'de restore endpoint disabled; LOGS fork detection |
| Replay code accidentally execute eder | O §19 | replay engine compile out of MVP build OR feature flag off |
| Sınırı belirsiz "MVP feature flag" tarafı kaçırır | — | Feature flag matrix `docs/build/0001-` planında documented |
| LLM library accidentally imported | A §6 | Build manifest excludes LLM dependencies; CI test |
| Constitutional immutable runtime mutation | M §3 | Numerics artifact loader read-only; no in-process update path |

---

## 13. Final Hüküm

```
Implementation Readiness Hükmü
─────────────────────────────────────────

Schema layer:                  READY
Observer ledger MVP:           READY
Numerics validation MVP:       READY_WITH_DEV_FIXTURES
Ingress compiler skeleton:     READY
Minimal M0 simulation:         READY_FOR_STUB
Workspace pulse:               READY_FOR_STUB
Deontic gate:                  READY_FOR_STUB
Memory Write Gate:             READY_FOR_STUB
Recall protocol:               READY_FOR_STUB
EchoAdapter:                   READY_FOR_STUB
End-to-end dry simulation:     READY_FOR_SIMULATION

Real adapters:                 DEFERRED
Live execution:                FORBIDDEN_IN_MVP
LLM integration:               DEFERRED
Verified memory production:    DEFERRED (MVP: candidate-only)
Replay engine:                 DEFERRED
Restore/fork/migration:        DEFERRED
Production signed numerics:    REQUIRED_BEFORE_PRODUCTION
Telegram/operator control:     DEFERRED

Invariant test suite (MVP):    ~50 tests; READY_FOR_PROPERTY_TEST
Open questions blocking MVP:   0 (~35 dev fixture, ~50 production,
                                  ~25 default + audit, ~11 research)

Risk register:                 10 identified, all mitigated by design

═══════════════════════════════════════════
MVB build plan can be written.
═══════════════════════════════════════════
```

---

## Sıradaki adım

Bu review GREEN. Sıradaki dosya:

```
docs/build/0001-minimum-viable-brain-plan.md
```

Bu artık review değil, **build plan**:
- Repository structure
- Technology stack decision (Python? Rust? Go? — phase 1 contracts katmanı için)
- 10 phase'in haftalık milestone'ları
- Test-first discipline (her phase önce test, sonra implementation)
- CI/CD shape
- Feature flag matrix (MVP'de off olanlar)
- Done definition per phase

Build plan tamamlandıktan sonra **gerçek kod** başlar.

---

## Notlar

- Bu rapor `Frozen` durumdadır. Implementation phase'de değişiklik
  gerekirse `0003-...` yeni rapor olarak kayıtlanır.
- 22 belge + 2 review = 24 dosya phase closure pipeline'da.
- Build plan teknoloji seçimi yapacak; bu review teknoloji-agnostik.

**Implementation readiness denetimi GREEN.**

> *Sentinel'in dokusu artık belge değil; kod olmaya hazır.*
> *Ama önce build plan, sonra kod. Belge fazı kapandı; disiplin değil.*
