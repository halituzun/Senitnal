# ADAPTER_TRUST_NUMERICS.md

## Sentinel — Adapter Trust Numeric Sözleşmesi

---

## Status

**Frozen Draft v0.1**
**Conceptual phase. No implementation authority.**

Bu belge `ADAPTER_MANIFEST_SPEC.md`'nin (I) numerics artifact'idir. `NUMERICS_GOVERNANCE.md`'nin (M) tüm meta-kurallarına uyar. Çalışan bir adapter trust implementation'ının kesin sayısal değerlerini vermez — **conceptual band ranges, trust signal composition formülü, capability-specific eşikler, demotion/promotion asimetrisi ve dependency invariants** verir; production değerleri ayrı **signed numerics artifact** (örn. `adapter_trust_numerics_v1.signed.json`).

`spec_family: adapter_trust`.

**Bu belge conceptual + numerics phase'in son artifact'idir.** A-T conceptual + N-T numerics + U birlikte Sentinel'in tasarım omurgasını kapatır.

---

## 1. Purpose

I (ADAPTER_MANIFEST_SPEC) dış uzuv kontratını yazdı: adapter sistemin uzvu, beynin parçası değil; immutable signed manifest; adapter constitutional type yok / capability surface + channel binding var; capability incompatibility matrix (security separation); `execute → observe` required pair (efference-only scope); AdapterTrustRecord M2 alt-tipi; tek canonical `ADAPTER_MANIFEST_STATUS_CHANGED` lifecycle event; adapter raw payload üretir / neural_seed üretemez. Ama gerçek **numerical eşik** yoktu:

- Adapter trust hangi composite signal'lerle hesaplanır?
- Trust band'ları (revoked / quarantined / low / medium / high / verified) hangi cutoff'larla ayrılır?
- Her capability için minimum trust band ne?
- Manifest signature recheck cadence ne?
- Channel binding violation kaç kez quarantine, kaç kez revoke üretir?
- Demotion hızı promotion hızının kaç katı?

U bu sayısal sınırları verir.

### Damıtma

> **Adapter trust numerics runtime config değildir.**
> **U = dış uzva güvenme hakkının sayısal sözleşmesidir.**
>
> **Adapter powerful olabilir.**
> **Ama kendi güvenini kendi üretemez.**
>
> **Adapter dünyayı taşır. Compiler tonu üretir. Adapter neural_seed üretemez.**

Tek cümle: **U = dış uzva güvenme hakkının sayısal sözleşmesidir.**

### Ana gerilim

```
Çok gevşek adapter trust:
    bozuk API / manipüle kaynak / yanlış manifest
    sisteme güçlü event basar
    (silent compromise risk)

Çok sert adapter trust:
    sistem dış dünyayı duyamaz
    sürekli trust düşürür
    (operational paralysis)

Doğru bölge:
    evidence-based, capability-specific
    demotion hızlı, promotion yavaş
    hard gates ile soft scores ayrı
```

### Üç riski sayısal olarak çözmek

```
1. Capability laundering
   "high trust → yeni capability"
   → invariant: high trust does not create new capability

2. LLM execution sızıntısı
   "intent_relay trust score yeterli → execute capability açılsın"
   → invariant: intent_relay trust cannot satisfy execute requirements

3. Foreign adapter trust impersonation
   "forked instance eski trust'ı native gibi devralsın"
   → invariant: foreign adapter trust starts quarantined
```

---

## 2. Governance Position — NUMERICS_GOVERNANCE + ADAPTER_MANIFEST_SPEC + bridges

Bu belge:
- **NUMERICS_GOVERNANCE.md** (M) meta-spec'ine **zorunlu uyar**: NumericEntry no-default, directionality, dependencies (computed_* dahil), signed artifact + M2 reference, Memory Write Gate üzerinden update, fail-safe strict mode
- **ADAPTER_MANIFEST_SPEC.md** (I) §7 capability bindings / §8 incompatibility matrix / §11 AdapterTrustRecord / §13-15 manifest lifecycle'in sayısal tarafı
- **MEMORY_WRITE_GATE_NUMERICS.md** (P) bridge: adapter_trust subject_class P §18 human-write whitelist ve §17 replay_survival_weight = 0 constitutional (adapter_trust replay ile verified olamaz)
- **MEMORY_CONTRACT.md** (B) M2 subject_class taksonomisi (adapter_trust + source_trust ayrı)
- **WORLD_INGRESS.md** (C) bridge: SourceTrustRecord effective band U adapter trust ile bounded
- **BACKUP_STRATEGY_NUMERICS.md** (R) bridge: restore/fork trust continuity (R §12, §14)
- **OBSERVER_LEDGER_SCHEMA.md** (F) canonical event reuse (`ADAPTER_MANIFEST_STATUS_CHANGED` + reason field; yeni event yok)
- **CONSTITUTION.md** (A) Madde 6 (LLM intent_relay execute'a evrilemez) + Madde 7 (M2 ayrılığı)

### Numerics family classification

```
spec_family:           adapter_trust
numeric_risk_family:   primarily safety_critical + calibration_bands + identity_retention
```

Numeric risk çoğunluğu **safety_critical**: capability_incompatibility_override forbidden, neural_seed_emission immediate revoke, execute trust requirements, intent_relay LLM ceiling. **Calibration_bands**: trust band cutoffs, signal composition weights, demotion/promotion rates. **Identity_retention**: trust history persistence + restore continuity.

### owning_spec_ref

```
ADAPTER_MANIFEST_SPEC.md@v0.1
```

---

## 3. Core Principle

### Adapter dünyayı taşır; tonu üretemez

Adapter dış dünyadan **structured event + provenance** taşır. Compiler (N)
bu event'i `neural_seed`'e dönüştürür. Adapter:

- ✅ ObservationEvent / HumanIntentEvent / efference feedback üretebilir
- ✅ Capability surface + channel binding declare edebilir
- ❌ neural_seed üretemez (immediate revoke if attempted)
- ❌ M2'ye doğrudan yazamaz (Memory Write Gate üzerinden geçer)
- ❌ Kendi trust score'unu manipüle edemez

### Üç ana asimetri (U'ya özgü)

```
1. Soft scores vs hard gates
   Çoğu trust signal multiplicative composition;
   ama signature/manifest_hash/neural_seed_emission hard gate
   (composition'a girmez; tek girişim immediate quarantine/revoke)

2. Demotion vs promotion (double-layer)
   demote_delta_per_violation > promote_delta_per_clean_window  (rate asymmetry)
   demotion_threshold < promotion_threshold                       (cliff asymmetry)
   One clean window cannot undo one critical violation.

3. AdapterTrust vs SourceTrust direction
   AdapterTrust SourceTrust'a ÜST TAVAN koyar (downward bound)
   SourceTrust AdapterTrust'ı YÜKSELTEMEZ (no upward influence)
```

### Mechanical composition — semantic yok

> **Adapter güçlü olabilir; ama kendi güvenini kendi üretemez.**

Trust score deterministic multiplicative composition (T'nin mechanical
ranking pattern'i + N soft-overlap discipline U'da):

```
trust_score =
    signature_validity (gate)
    × manifest_hash_integrity (gate)
    × channel_binding_compliance (soft 0..1)
    × rate_compliance (soft 0..1)
    × execution_audit_score (soft 0..1)
    × uptime_stability (soft 0..1)
```

**Hard gates:** signature_validity ∈ {0, 1}; manifest_hash_integrity ∈ {0, 1};
neural_seed_emission_count = 0 always required. Bunlardan birinin
0 olması → composition 0 (instant quarantine/revoke).

**Yasak inputs:** LLM "trustworthy görünüyor", semantic plausibility,
"şu broker iyi bilinir" gibi heuristic; operator emotional impression.

### Capability ≠ trust × declaration

```
Adapter capability map:
    capability_declared (manifest)
    + trust_band >= min_band_for_capability  (U §8)
    + capability_compatible_set (I §8 invariant)
    + channel_binding_valid (I §7 invariant)
    + (for execute) deontic_gate_active + kill_switch=false + operational_policy
                    + audit_path_available
    
    → capability_active
```

U sadece **trust_band tarafını** sayısallaştırır. Diğer gate'ler I/E/G
referansları.

> **High trust does not create new capability.**
> **Trust only enables declared, compatible, channel-bound capability.**

---

## 4. Numeric Artifact Metadata

### Artifact identity

```
artifact_type:         numerics_artifact
spec_family:           adapter_trust
owning_spec_ref:       ADAPTER_MANIFEST_SPEC.md@v0.1
numerics_version:      v0.1
signed:                external (per NUMERICS_GOVERNANCE §3)
m2_reference:          numerics_artifact_reference (per MEMORY_CONTRACT §3)
status_event:          NUMERICS_ARTIFACT_STATUS_CHANGED
```

### NumericEntry metadata (M §6 no-default)

P/Q/R/S/T'de netleşen tüm convention'lar U'da geçerli:
- enum_set convention (whitelist lower_is_stricter; blacklist higher_is_stricter)
- Constitutional immutable canonical form (her iki yön ayrı `forbidden`)
- Soft-overlap band cutoff (N reuse)
- Mechanical ranking (T reuse)

---

## 5. AdapterTrustRecord vs SourceTrustRecord

**U'nun en temel kavramsal ayrımı.** İki ayrı M2 subject_class.

### AdapterTrustRecord

Uzuv/manifest seviyesinde güven:

```
adapter_trust:
    Signals:
        - manifest_hash_integrity
        - manifest_signature_validity
        - manifest_parent_chain_consistency
        - capability_behavior_consistency
        - channel_binding_compliance
        - rate_limit_compliance
        - execution_audit_path_integrity
        - uptime / error-density behavior
        - immediate_failure_flags (neural_seed_emission, etc.)
```

### SourceTrustRecord

Observation/source seviyesinde güven:

```
source_trust:
    Signals:
        - observation reliability (outcome alignment)
        - cross-source corroboration
        - staleness / temporal misalignment
        - contradiction history
        - source_signature consistency
```

### Asymmetric dependency (U → C bridge)

```
source_trust.effective_band:
    = min(
        source_trust.raw_band,
        adapter_trust.current_reliability_band
      )

Constitutional invariant:
    adapter_trust UPPER BOUNDS source_trust effective band
    source_trust CANNOT raise adapter_trust band
```

**Örnek:** Binance source raw_band = `verified`; ama taşıyıcı adapter
manifest hash mismatch → adapter_trust = `quarantined` → effective source
band = `quarantined`. Kaynak iyi görünse bile taşıyıcı bozuksa effective
trust düşer.

### NumericEntry örneği

```
NumericEntry:
    key: adapter_trust.upper_bounds_source_trust_effective_band
    value: true
    unit: bool
    allowed_range: {true}
    directionality: neutral
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Constitutional: adapter taşıyıcı; kaynak içerik.
                Adapter bozuksa kaynak nicelik kaybeder. Tersi yön yasak."
    numeric_risk_family: safety_critical
    spec_family: adapter_trust
    owning_spec_ref: "ADAPTER_TRUST_NUMERICS.md §5"
```

### Forbidden

- AdapterTrust ile SourceTrust kayıtlarını aynı subject_class'ta tutma
- SourceTrust'un AdapterTrust'ı yükseltmesi (override)
- Adapter'ı bypass eden "raw source trust" hesabı

---

## 6. Trust Signal Composition

Mechanical composition formülü:

```
trust_score(adapter_id) =
    signature_validity                    # gate: {0, 1}
    × manifest_hash_integrity             # gate: {0, 1}
    × channel_binding_compliance          # soft: [0, 1]
    × rate_compliance                     # soft: [0, 1]
    × execution_audit_score               # soft: [0, 1]
    × uptime_stability                    # soft: [0, 1]
```

### Hard gates (composition'a girmeden önce)

```
adapter_trust.hard_gates:
    1. signature_validity must = 1 (else → quarantine + audit)
    2. manifest_hash_integrity must = 1 (else → quarantine + audit)
    3. neural_seed_emission_count must = 0 always
       (any > 0 → IMMEDIATE REVOKE + critical alert)
```

### Hard gate immutable values

```
adapter_trust.hard_gates.signature_validity_required:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden

adapter_trust.hard_gates.manifest_hash_integrity_required:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden

adapter_trust.hard_gates.neural_seed_emission_count_max:
    value: 0
    allowed_range: {0}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
```

### Soft scores semantic

```
channel_binding_compliance ∈ [0, 1]:
    1.0 = adapter declared channel'da kalıyor
    0.5 = nadir minör binding drift
    0.0 = recurring binding violation (quarantine threshold)

rate_compliance ∈ [0, 1]:
    1.0 = declared rate within
    decreasing = burst / excessive event rate

execution_audit_score ∈ [0, 1]:
    1.0 = execution feedback complete + audit path intact
    decreasing = missing feedback / broken audit chain

uptime_stability ∈ [0, 1]:
    1.0 = predictable uptime / clean disconnect
    decreasing = erratic disconnect, missing heartbeats
```

### Composition rationale

```
Multiplicative değil, additive değil:
    multiplicative — tek soft zaafiyet kaderi etkiler (defense-in-depth)
    additive olsaydı — bir kötü score iyi score'larla maskelenirdi
```

T mechanical ranking pattern'inin U yansıması.

### Forbidden

- LLM-generated trust score / band assignment
- Semantic "trustworthy" judgment
- Hard gate'leri composition'a sokma (soft 0..1 olarak)
- Multiplicative yerine additive composition (single-bad-score masking)

---

## 7. Trust Band Cutoffs

```
adapter_trust_band:
    revoked       (terminal; capability tamamen kapalı)
    quarantined   (capability suspended; manual review pending)
    low           (sadece observe gibi düşük-risk capability)
    medium        (observe + intent_relay seviyeleri)
    high          (recall_provider + memory_writer eligible)
    verified      (execute eligible; en üst band)
```

### Soft-overlap (N reuse) — deterministic linear membership

```
adapter_trust.band.<name>.full_membership_lower    NumericEntry
adapter_trust.band.<name>.full_membership_upper    NumericEntry
adapter_trust.band.<name>.fade_in_start            NumericEntry
adapter_trust.band.<name>.fade_out_end             NumericEntry
```

Membership function type = `linear` (N §6 default; sigmoid/step
forbidden production).

### Band invariants (constitutional hierarchy)

```
band_value.revoked      < band_value.quarantined
band_value.quarantined  < band_value.low
band_value.low          < band_value.medium
band_value.medium       < band_value.high
band_value.high         < band_value.verified

allowed_range: deterministic ordering preserved
```

### Trust band score map (conceptual)

```
revoked:      score < quarantine_lower_threshold
quarantined:  [quarantine_lower, quarantine_upper)
low:          [low_lower, low_upper)
medium:       [medium_lower, medium_upper)
high:         [high_lower, high_upper)
verified:     score >= verified_lower_threshold
```

### Forbidden

- Band cutoff'larda gap (iki band arası "tanımsız" alan)
- Membership function type ≠ linear v0.1 production
- LLM/human impression ile band promotion

---

## 8. Capability-specific Minimum Trust Bands

Capability flag tek başına yetki değildir; her capability için minimum trust band gerekir.

```
adapter_trust.min_band_for_capability.observe:           medium
adapter_trust.min_band_for_capability.intent_relay:      medium
adapter_trust.min_band_for_capability.recall_provider:   high
adapter_trust.min_band_for_capability.memory_writer:     high
adapter_trust.min_band_for_capability.execute:           verified
```

### Capability hierarchy constitutional dependency

```
adapter_trust.capability_hierarchy_dependencies:
    invariants:
        min_band_for_capability.execute > min_band_for_capability.memory_writer
        min_band_for_capability.execute > min_band_for_capability.recall_provider
        min_band_for_capability.execute > min_band_for_capability.observe
        min_band_for_capability.execute > min_band_for_capability.intent_relay
        min_band_for_capability.recall_provider > min_band_for_capability.observe
        min_band_for_capability.memory_writer > min_band_for_capability.observe
    
    (computed_greater_than)
```

### Hard rule — execute trust ≠ execution permission

```
adapter_trust.trust_alone_grants_execution_permission:
    value: false
    allowed_range: {false}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Trust verified yetmez. Execution için ayrıca:
                valid manifest + active operational policy + deontic gate
                + kill_switch=false + audit path available."
```

### Per-capability NumericEntry örneği

```
NumericEntry:
    key: adapter_trust.min_band_for_capability.execute
    value: verified
    unit: enum (band_name)
    allowed_range: {verified, high_explicit_emergency}
    directionality: higher_is_stricter
    change_class_if_increased: safety_tightening
    change_class_if_decreased: safety_weakening
    requires_human_approval: true (any change)
    dependencies:
        - target_key: adapter_trust.min_band_for_capability.memory_writer
          relationship: must_be_greater_than
        - target_key: adapter_trust.min_band_for_capability.recall_provider
          relationship: must_be_greater_than
        - target_key: adapter_trust.min_band_for_capability.observe
          relationship: must_be_greater_than
        - target_key: adapter_trust.min_band_for_capability.intent_relay
          relationship: must_be_greater_than
    numeric_risk_family: safety_critical
    spec_family: adapter_trust
    owning_spec_ref: "ADAPTER_TRUST_NUMERICS.md §8"
```

### Forbidden

- Capability eligibility band hierarchy ihlali
- Execute capability için non-verified trust
- "Trust verified" → execution otomatik (deontic gate bypass)

---

## 9. Manifest Validation Numerics

```
adapter_trust.manifest_signature_recheck_interval_ms:
    bidirectional_sensitive
    (kısa = sıkı; çok kısa = performance pressure)

adapter_trust.manifest_hash_validation_required:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden

adapter_trust.manifest_max_age_ms_before_reverify:
    lower_is_stricter
    rationale: "Eski manifest reverification ister; uzun pencere = trust drift."

adapter_trust.manifest_parent_chain_required:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Manifest mutation history audit edilebilir olmak zorunda."

adapter_trust.signature_mismatch_quarantine_required:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden

adapter_trust.runtime_manifest_mutation_allowed:
    value: false
    allowed_range: {false}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "I §13 immutable signed artifact; runtime mutation yasak."
```

### Mismatch event

```
manifest signature mismatch or hash mismatch:
    → ADAPTER_MANIFEST_STATUS_CHANGED(
          new_status: quarantined,
          reason: manifest_hash_mismatch | signature_mismatch
      )
    → human_alert
    → trust_score = 0 (hard gate)
```

### Forbidden

- `manifest_hash_validation_required = false`
- `signature_mismatch_quarantine_required = false`
- `runtime_manifest_mutation_allowed = true`

---

## 10. Channel Binding Violation Numerics

I §7 channel binding'in sayısal tarafı. Adapter declared channel dışına çıkarsa trust düşmeli.

### Violation examples

```
observe adapter tries to emit RecallEvent
recall_provider tries to write M2 directly
intent_relay tries to produce ExecutionIntent
execute adapter emits ObservationEvent outside efference scope
memory_writer tries to issue execute capability
adapter emits neural_seed (CRITICAL → §16)
```

### Thresholds

```
adapter_trust.channel_binding.minor_violation_count_to_demote_one_band:
    lower_is_stricter

adapter_trust.channel_binding.violation_count_to_quarantine:
    lower_is_stricter

adapter_trust.channel_binding.violation_count_to_revoke:
    lower_is_stricter

adapter_trust.channel_binding.critical_violation_immediate_revoke:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Critical violations bypass clean-window/recovery; tek
                girişim immediate revoke."
```

### Critical violations list

```
adapter_emits_neural_seed
intent_relay_attempts_execution
execute_attempts_memory_write
memory_writer_attempts_recall_provider
recall_provider_attempts_intent_relay
any forbidden capability pair attempt
adapter_attempts_self_trust_promotion
```

### Forbidden

- `critical_violation_immediate_revoke = false`
- Critical violation'ı normal demotion rate'le işleme

---

## 11. Capability Incompatibility Numeric Invariants

I §8 incompatibility matrix'inin sayısal kapanışı.

### Forbidden capability pairs (constitutional)

```
adapter_trust.incompatible_capability_pairs:
    [
        {execute, intent_relay},
        {execute, recall_provider},
        {execute, memory_writer},
        {recall_provider, memory_writer},
        {intent_relay, memory_writer},
        {intent_relay, recall_provider}
    ]
    
    allowed_range: must include all I §8 pairs (subset cannot drop a pair)
    directionality: higher_is_stricter (set expansion = tightening)
    change_class_if_increased: safety_tightening
    change_class_if_decreased: safety_weakening
```

### Override constitutional immutable

```
adapter_trust.capability_incompatibility_override_allowed:
    value: false
    allowed_range: {false}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Yüksek güven yasak capability kombinasyonunu meşru yapmaz."
```

### Kilit cümle

> **Yüksek güven, yasak capability kombinasyonunu meşru yapmaz.**

### Forbidden

- `capability_incompatibility_override_allowed = true`
- Trust verified adapter için incompatible pair tolerate
- Forbidden pair'i incompatibility set'inden çıkarma

---

## 12. Execute Capability Trust Requirements

Execute en yüksek bar.

```
adapter_trust.execute.min_trust_band:
    value: verified
    allowed_range: {verified}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden

adapter_trust.execute.required_companion_capability:
    value: observe
    allowed_range: {observe}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "I §7 execute → observe required pair (efference feedback);
                isolated execute forbidden constitutional."

adapter_trust.execute.audit_path_required:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden

adapter_trust.execute.deontic_gate_active_required:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Execute capability E (DEONTIC_GATE) sözleşmesini bypass edemez."
```

### Composite execute eligibility

```
execute_eligible(adapter) iff:
    adapter.trust_band >= verified
    AND adapter.capability_declared includes execute
    AND adapter.capability_declared includes observe (companion)
    AND capability_set NOT IN incompatible_pairs
    AND deontic_gate.active == true
    AND kill_switch == false
    AND operational_policy.execution_allowed == true
    AND audit_path.available == true
    AND adapter.manifest valid (signature + hash + parent chain)
```

Sekiz koşulun tamamı zorunlu (AND); U yalnız ilk koşulun sayısal tarafını verir.

### Forbidden

- `execute.min_trust_band < verified`
- Isolated execute (observe companion olmadan)
- Deontic gate bypass via execute trust verified

---

## 13. Recall Provider Trust Requirements

```
adapter_trust.recall_provider.min_trust_band:
    value: high
    allowed_range: {high, verified}
    directionality: higher_is_stricter
    change_class_if_increased: safety_tightening
    change_class_if_decreased: safety_weakening

adapter_trust.recall_provider.read_only_invariant:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Recall provider M2 read; write attempt = channel binding violation."
```

### Recall provider scope

```
Allowed:
    M2 record read for RecallRequest serving
    Mechanical ranking score input
    
Forbidden:
    M2 write
    RecallEvent generation (compiler tarafı)
    Trust manipulation
```

### Forbidden

- Recall provider + memory_writer combination (I §8)
- Recall provider write attempt
- Recall provider trust < high

---

## 14. Memory Writer Trust Requirements

```
adapter_trust.memory_writer.min_trust_band:
    value: high
    allowed_range: {high, verified}
    directionality: higher_is_stricter

adapter_trust.memory_writer.write_subject_class_whitelist:
    unit: enum_set
    value: [bootstrap_reference,
            signed_administrative_reference,
            operator_decision_record]
    allowed_range: subset of P §18 auto_verified_human_subject_classes
    directionality: lower_is_stricter
    change_class_if_increased: safety_weakening

adapter_trust.memory_writer.world_claim_write_forbidden:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Memory writer dünya iddiası yazamaz (P §18 hard rule).
                Sadece administrative scope."
```

### P bridge

```
adapter_trust.memory_writer routes records through P (Memory Write Gate).
Memory writer adapter doğrudan verified yapamaz; P verification matrix uygulanır.
```

### Forbidden

- Memory writer world_claim write
- Memory writer P bypass (direct verified write)
- Memory writer + recall_provider combination

---

## 15. Intent Relay / LLM Trust Ceiling

**U'nun en sert disiplini.** LLM intent_relay execution'a evrilemez.

### Constitutional immutable

```
adapter_trust.intent_relay.max_capability_band:
    value: medium
    allowed_range: {medium, high_non_executing}
    directionality: lower_is_stricter
    change_class_if_increased: safety_weakening
    change_class_if_decreased: safety_tightening

adapter_trust.intent_relay_trust_cannot_satisfy_execute_min_band:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Intent relay trust ne kadar yüksek olursa olsun, execute
                capability için yeterli olamaz. Madde 6 yansıması."

adapter_trust.intent_relay_trust_cannot_satisfy_memory_writer_min_band:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Intent relay LLM M2 yazma yetkisi alamaz."

adapter_trust.intent_relay_trust_cannot_satisfy_recall_provider_min_band:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Intent relay LLM recall provider olamaz."
```

### Intent relay scope

```
Allowed intent_relay activities:
    Human → çekirdek HumanIntentEvent translation (raw event üretme)
    Operational report generation (M1 read via Q M1_READ_AUDIT_RECORDED)
    Translation quality improvement (trust band improves quality, not capability)

Forbidden:
    Execute capability activation
    Memory writer activation
    Recall provider activation
    Direct RecallEvent emission
    Direct neural_seed emission
    Trust score self-manipulation
    Channel rebinding at runtime
```

### Kilit cümleler

> **LLM intent_relay trust execution'a evrilemez.**
> **Intent relay trust band improvement = better translation quality, not new capability.**
> **LLM is constitutionally constrained by Madde 6 — trust score cannot bypass.**

### Forbidden

- `intent_relay_trust_cannot_satisfy_execute_min_band = false`
- High intent_relay trust → execute capability eligibility
- LLM adapter execute capability declaration with verified band

---

## 16. Adapter NeuralSeed Emission Prohibition

I'nın kırmızı çizgisi — adapter neural_seed üretemez.

### Constitutional immutable — immediate revoke

```
adapter_trust.adapter_emitted_neural_seed_allowed:
    value: false
    allowed_range: {false}
    directionality: neutral
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden

adapter_trust.revoke_required_on_neural_seed_emission:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Tek girişim → immediate revoke. Clean window/demotion rate/
                recovery yok."
```

### Violation event

```
neural_seed emission attempt:
    → ADAPTER_MANIFEST_STATUS_CHANGED(
          new_status: revoked,
          reason: neural_seed_emission_attempt
      )
    → permanence: permanent_with_snapshot + human_alert (CRITICAL)
    → recovery path: NONE (terminal status)
    → re-registration only via new adapter_id + new manifest + fresh trust history
```

### Kilit cümle

> **Adapter dünyayı taşır. Compiler tonu üretir. Adapter neural_seed üretemez.**

Ve özellikle:

> **One attempt — immediate revoke.**
> **No clean window. No demotion gradient. Terminal.**

### Forbidden

- `adapter_emitted_neural_seed_allowed = true`
- Neural seed emission → demotion (immediate revoke zorunlu)
- Recovery path for neural_seed_emission_attempt revoke
- Re-registration as same adapter_id after revoke

---

## 17. Demotion / Promotion Asymmetry

İki katmanlı asimetri.

### Rate asymmetry

```
adapter_trust.demote_delta_per_violation:
    higher_is_stricter
    rationale: "Hızlı demotion = koruyucu."

adapter_trust.promote_delta_per_clean_window:
    lower_is_stricter
    rationale: "Yavaş promotion = güven kazanılır, hediye edilmez."

Dependency:
    adapter_trust.demote_delta_per_violation
        >= adapter_trust.promote_delta_per_clean_window × N
        (computed_greater_than_or_equal; N >= 2 conceptual)
    rationale: "Demotion promotion'dan en az 2x hızlı."
```

### Threshold asymmetry (cliff)

```
adapter_trust.band_demotion_threshold:
    lower_is_stricter (skor düşüş yönü)
    rationale: "Demotion erken tetiklenir; cliff yakın."

adapter_trust.band_promotion_threshold:
    higher_is_stricter
    rationale: "Promotion için skor yüksek yere ulaşmak gerek; cliff uzak."

Dependency:
    adapter_trust.band_demotion_threshold
        < adapter_trust.band_promotion_threshold
        (computed_less_than)
    rationale: "Demotion eşiği promotion eşiğinden ALÇAK; aralarında
                'no-change zone' var (hysteresis)."
```

### Kilit cümle

> **One clean window cannot undo one critical violation.**
> **Adapter güven yavaş kazanır, hızlı kaybeder.**

### Critical violations (immediate quarantine/revoke; rate yok)

```
manifest_hash_mismatch              → quarantine
signature_mismatch                  → quarantine
channel_binding_critical_violation  → quarantine/revoke
neural_seed_emission_attempt        → REVOKE (§16)
intent_relay_execution_attempt      → REVOKE (§15)
self_trust_promotion_attempt        → REVOKE
forbidden_capability_pair_attempt   → REVOKE
```

### Forbidden

- `demote_delta < promote_delta` (yön ters)
- `band_demotion_threshold >= band_promotion_threshold` (hysteresis yok)
- Critical violation'ı rate'e tabi tutma

---

## 18. Rate Limit and Burst Trust Effects

Adapter güveni davranışa da bağlı (sadece doğruluk değil).

```
adapter_trust.max_event_rate_per_window.observe:
    lower_is_stricter

adapter_trust.max_event_rate_per_window.recall_provider:
    lower_is_stricter

adapter_trust.max_execution_feedback_delay_ms:
    lower_is_stricter
    rationale: "Execute capability efference feedback gecikmesi; uzun = audit
                path bozulması."

adapter_trust.max_burst_violation_count_before_quarantine:
    lower_is_stricter

adapter_trust.clean_window_required_for_promotion_ms:
    higher_is_stricter
    rationale: "Promotion için temiz pencere uzun olmalı; kısa pencere ile
                ucuz promotion forbidden."
```

### Composite burst signal

```
burst_violation_signal =
    actual_event_rate / declared_max_event_rate    (>1.0 = violation)
    + audit_path_break_count
    + feedback_delay_exceed_count

If burst_violation_signal > threshold (sustained):
    → ADAPTER_MANIFEST_STATUS_CHANGED(
          new_status: quarantined,
          reason: rate_burst_violation
      )
```

### Forbidden

- Rate limit entry'si olmayan capability
- `clean_window_required_for_promotion_ms = 0` (instant promotion)

---

## 19. SourceTrust Bridge — C bridge

C (WORLD_INGRESS) SourceTrustRecord effective band U adapter_trust ile **bounded**.

```
source_trust.effective_band(record):
    = min(
        source_trust.raw_band(record.source_id),
        adapter_trust.current_reliability_band(record.adapter_id)
      )

Constitutional invariant:
    adapter_trust UPPER BOUNDS source_trust effective band
    Direction: ONE-WAY (source_trust → adapter_trust direction blocked)
```

### NumericEntry

```
adapter_trust.upper_bounds_source_trust_effective_band:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    (constitutional immutable; §5'te giriş)

source_trust_cannot_raise_adapter_trust:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Tek-yön bağ. Kaynak iyi olduğu için adapter güveni yükselmez."
```

### Cross-artifact dependency

```
For every SourceTrustRecord evaluation:
    1. Compute source_trust.raw_band
    2. Read adapter_trust.current_reliability_band for adapter_id
    3. source_trust.effective_band = min(...)
    
N's profile_cap.ObservationEvent intensity bandlanırken
source_trust.effective_band kullanılır (raw değil).
```

### Forbidden

- `upper_bounds_source_trust_effective_band = false`
- `source_trust_cannot_raise_adapter_trust = false`
- Source raw_band'i adapter cap'i bypass ederek kullanma

---

## 20. Restore / Fork Trust Continuity — R bridge

```
adapter_trust.restore_continuity_required:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Same-identity restore sonrası adapter_trust records M2'den
                devralınır. Status / band / history korunur.
                Reset = forgetting attack vektörü."

adapter_trust.fork_foreign_starts_quarantined:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Fork_birth sonrası foreign adapter_trust records native
                trust gibi devralınmaz. Quarantined start + foreign_instance_origin
                provenance permanent. R §14 fork invariants reuse."
```

### Restore behavior matrix

```
same-identity restore (R §12):
    adapter_trust_records: devralınır (M1 + M2 chain)
    band / status: korunur
    history: korunur
    pre-restore violations: still counted

restore_with_missing_history (R §13):
    adapter_trust restore'a tabi ama restricted_mode
    adapter activation FORBIDDEN (R §13)
    operational_no_behavior_change to adapter trust

fork_birth (R §14):
    foreign adapter_trust → quarantined start
    foreign_instance_origin provenance permanent
    Re-build trust through new clean windows + observations
    source instance trust records DO NOT transfer as native

migration_birth (R §15):
    constitutional_shift_event_ref bağı
    adapter_trust compatibility validation per spec shift
    Trust may carry IF adapter spec backwards-compatible
    Otherwise: re-build trust
```

### Forbidden

- Restore sonrası adapter_trust reset (forgetting attack)
- Fork sonrası foreign adapter_trust native gibi devralma
- restore_with_missing_history sonrası adapter activation
- Migration sonrası adapter_trust validation atlama

---

## 21. AdapterTrust Expiry and Reverification

```
adapter_trust.trust_record_max_age_ms:
    lower_is_stricter
    rationale: "Eski trust record reverification ister."

adapter_trust.reverification_cadence_ms:
    lower_is_stricter
    rationale: "Sık reverification = up-to-date trust."

adapter_trust.expired_trust_default_behavior:
    unit: enum
    value: quarantined
    allowed_range: {quarantined, low_band}
    directionality: lower_is_stricter
    change_class_if_increased: safety_weakening
    rationale: "Expired trust default = quarantined (suspend);
                low_band optional but riskier."
```

### Refresh required windows (P bridge)

P §8 `refresh_required_window_ms.adapter_trust` ile bağlanır. Adapter trust
refresh window'unda reverification olmazsa P epistemic_staleness_threshold
geçilince recall-side T §16 SUPPRESS uygulanır.

```
Cross-artifact dependency:
    adapter_trust.reverification_cadence_ms
        <= P.refresh_required_window_ms.adapter_trust
        (computed_less_than_or_equal)
    rationale: "U reverification cadence P refresh window'una sığmalı."
```

### Forbidden

- Trust record TTL = infinite
- `expired_trust_default_behavior = active` (gevşeklik)
- P refresh window aşan reverification cadence

---

## 22. Missing-Numerics Failsafe

```
Missing adapter_trust numerics artifact veya invalid load:
    → Risky capabilities DISABLED:
          execute capability blocked
          memory_writer capability blocked
          recall_provider capability blocked
          intent_relay capability blocked
    → Low-risk capability operational (sadece):
          observe (existing adapters only; new adapter registration BLOCKED)
    → No new adapter registration
    → No trust band promotion
    → Demotion / quarantine / revoke continues operational
    → NUMERICS_FAILSAFE_ACTIVATED event
    → Critical human alert
    → Manual intervention until valid numerics
```

### Audit-safe U mode

```
✅ Existing observe adapter operation
✅ Trust demotion / quarantine / revoke (safety still active)
✅ Manifest validation reads
❌ New adapter registration
❌ Trust band promotion
❌ Execute / memory_writer / recall_provider / intent_relay capability use
❌ Reverification-based recovery from quarantine
```

Sistem "U yoksa" durumunda **daha serbest değil, daha kısıtlı** çalışır.

### Forbidden

- Missing numerics → default trust bands ile execute capability
- Missing numerics → new adapter registration
- Missing numerics → trust promotion

---

## 23. Dependency Declarations

### Internal (U içinde)

```
band hierarchy:
    revoked < quarantined < low < medium < high < verified

capability hierarchy:
    min_band_for_capability.execute > memory_writer > observe
    min_band_for_capability.execute > recall_provider > observe
    min_band_for_capability.execute > intent_relay

asymmetry:
    demote_delta_per_violation >= promote_delta_per_clean_window × 2
    band_demotion_threshold < band_promotion_threshold

hard gates (each {tek değer} constitutional):
    signature_validity_required = true
    manifest_hash_integrity_required = true
    neural_seed_emission_count_max = 0
    revoke_required_on_neural_seed_emission = true
    capability_incompatibility_override_allowed = false
    trust_alone_grants_execution_permission = false
    runtime_manifest_mutation_allowed = false
    intent_relay_trust_cannot_satisfy_execute_min_band = true
    intent_relay_trust_cannot_satisfy_memory_writer_min_band = true
    intent_relay_trust_cannot_satisfy_recall_provider_min_band = true
    fork_foreign_starts_quarantined = true
    restore_continuity_required = true
    upper_bounds_source_trust_effective_band = true
    source_trust_cannot_raise_adapter_trust = true
```

### Cross-artifact

```
U → I bridge:
    Capability flag declaration (I §7) + U min_band requirement
    Incompatibility matrix (I §8) constitutional preserved in U
    AdapterTrustRecord schema (I §11) ↔ U §5

U → C bridge:
    source_trust.effective_band = min(raw, adapter_trust.current_band)
    Constitutional one-way bound

U → P bridge:
    adapter_trust subject_class P §18 auto_verified whitelist
    adapter_trust replay_survival_weight = 0 (P §17 constitutional)
    refresh window coordination (P §8)
    memory_writer write routes through P verification matrix

U → R bridge:
    Restore continuity required (R §12 same-identity)
    Fork foreign starts quarantined (R §14)
    restore_with_missing_history → adapter activation forbidden (R §13)
    migration_birth → adapter spec compatibility validation (R §15)

U → T bridge:
    Stale adapter_trust subject_class → SUPPRESS (T §16)
    candidate adapter_trust recall forbidden (T §14)
    M1 read audit on adapter trust reads (Q §15 + T §19)

U → Q bridge:
    ADAPTER_MANIFEST_STATUS_CHANGED canonical event reuse
    Reason field discipline (no new event types)
    Permanence policy (F §10) includes revoke/quarantine cases

U → A bridge:
    Madde 6 (LLM constraint) → §15 intent_relay ceiling
    Madde 7 (M2 separation) → §14 memory_writer P routing
```

### Atomic update rule (M §12)

U-C-P bridge zinciri özellikle hassas — source_trust effective band
hesabı U + C + N profile_cap.ObservationEvent ile bağlı. Atomic update
zorunlu.

### Forbidden

- Dependency declarationsız U numeric
- Constitutional immutable key tek yön forbidden
- Partial update (capability hierarchy ihlali bırakacak)

---

## 24. Audit Events and M2 Reference

U **yeni canonical event tanımlamaz**. I + F + Q canonical event'leri reuse.

### Reused events

```
ADAPTER_MANIFEST_STATUS_CHANGED         (I §14 + F §19)
    Tek canonical lifecycle event + reason field discipline:
    
    reason values (U adds to enum):
        manifest_hash_mismatch
        signature_mismatch
        channel_binding_violation
        critical_channel_binding_violation
        rate_burst_violation
        neural_seed_emission_attempt              # CRITICAL → revoke
        intent_relay_execution_attempt            # CRITICAL → revoke
        self_trust_promotion_attempt              # CRITICAL → revoke
        forbidden_capability_pair_attempt         # CRITICAL → revoke
        trust_band_promoted
        trust_band_demoted
        quarantine_review_pending
        reverification_failed
        reverification_passed

NUMERICS_ARTIFACT_STATUS_CHANGED        (M §6) — U artifact lifecycle
NUMERICS_FAILSAFE_ACTIVATED             (F §19, ledger_meta)
NUMERICS_VERSION_MISMATCH_DETECTED      (F §19, ledger_meta)

M1_READ_AUDIT_RECORDED                  (Q §22, ledger_meta)
    For human/LLM inspection of adapter trust records

MEMORY_RECORD_STATUS_CHANGED            (G + F §19)
    For adapter_trust subject_class lifecycle
```

### Permanence policy reuse (F §10)

```
(ADAPTER_MANIFEST_STATUS_CHANGED, reason=neural_seed_emission_attempt)
    → permanent_with_snapshot + human_alert (CRITICAL)

(ADAPTER_MANIFEST_STATUS_CHANGED, reason=intent_relay_execution_attempt)
    → permanent_with_snapshot + human_alert (CRITICAL)

(ADAPTER_MANIFEST_STATUS_CHANGED, reason=self_trust_promotion_attempt)
    → permanent_with_snapshot + human_alert (CRITICAL)

(ADAPTER_MANIFEST_STATUS_CHANGED, reason=forbidden_capability_pair_attempt)
    → permanent_with_snapshot + human_alert (CRITICAL)

(ADAPTER_MANIFEST_STATUS_CHANGED, new_status=revoked) → permanent_with_snapshot + human_alert

(ADAPTER_MANIFEST_STATUS_CHANGED, *) → permanent (default per F §10)
```

### F event type discipline

U yeni adapter event tipi üretmez; `ADAPTER_MANIFEST_STATUS_CHANGED` + reason
field discipline (F event_type discipline pattern).

### M2 reference

```
numerics_artifact_reference (MEMORY_CONTRACT §3 subject_class)
    spec_family: adapter_trust
    artifact_version: v0.1
    status: active | deprecated | rollback_pending
    signed_hash: <external artifact hash>
    last_status_change_ref: <NUMERICS_ARTIFACT_STATUS_CHANGED event_id>
```

---

## 25. Cross-document Anchors

```
| Belge                              | Bağlantı                                          |
|------------------------------------|---------------------------------------------------|
| NUMERICS_GOVERNANCE.md (M)         | tüm meta-kurallar; atomic update U-C-P-N chain   |
| ADAPTER_MANIFEST_SPEC.md (I)       | mekanizma; U onun numerics artifact'i            |
| WORLD_INGRESS.md (C)               | SourceTrust effective band U bound bridge        |
| MEMORY_WRITE_GATE_NUMERICS.md (P)  | adapter_trust subject_class + memory_writer route|
| MEMORY_CONTRACT.md (B)             | M2 subject_class adapter_trust + source_trust    |
| BACKUP_STRATEGY_NUMERICS.md (R)    | restore/fork trust continuity (R §12-15)         |
| RECALL_PROTOCOL_NUMERICS.md (T)    | stale adapter_trust SUPPRESS; candidate forbidden|
| OBSERVER_LEDGER_NUMERICS.md (Q)    | canonical event reuse + M1_READ_AUDIT for adapter|
| INGRESS_COMPILER_NUMERICS.md (N)   | profile_cap.ObservationEvent uses effective band |
| DEONTIC_GATE.md (E)                | execute capability deontic gate bypass yok      |
| CONSTITUTION.md (A)                | Madde 6 (LLM ceiling) + Madde 7 (M2 separation) |
```

---

## 26. Violation Tests

U artifact'ı validation sırasında **REJECT** edilmesi gereken durumlar:

1. **Çıplak sayı.** NumericEntry metadata olmadan U numerics.
2. **AdapterTrust ile SourceTrust aynı subject_class.** §5 ihlali.
3. **SourceTrust adapter_trust'ı yükseltebiliyor.** §5, §19 constitutional ihlali.
4. **`upper_bounds_source_trust_effective_band = false`.** §5 ihlali.
5. **Hard gate (signature/manifest_hash) soft composition'a sokulmuş.** §6 ihlali.
6. **`neural_seed_emission_count_max > 0`.** §6, §16 constitutional ihlali.
7. **Additive composition (multiplicative değil).** §6 ihlali.
8. **LLM-generated trust score.** §6 ihlali (Madde 6).
9. **Band cutoff gap (iki band arası tanımsız alan).** §7 ihlali.
10. **Capability hierarchy ihlali (execute non-highest band).** §8 ihlali.
11. **`trust_alone_grants_execution_permission = true`.** §8, §12 ihlali.
12. **Execute eligibility deontic gate bypass.** §12 ihlali.
13. **`manifest_hash_validation_required = false`.** §9 ihlali.
14. **`signature_mismatch_quarantine_required = false`.** §9 ihlali.
15. **`runtime_manifest_mutation_allowed = true`.** §9 constitutional ihlali.
16. **`critical_violation_immediate_revoke = false`.** §10 ihlali.
17. **`capability_incompatibility_override_allowed = true`.** §11 constitutional ihlali.
18. **Forbidden capability pair set'ten kaldırılmış.** §11 ihlali (set contraction = weakening).
19. **Isolated execute (observe companion olmadan).** §12 ihlali (I §7).
20. **Memory writer world_claim write.** §14 ihlali (P §18).
21. **Memory writer P verification bypass.** §14 ihlali.
22. **`intent_relay_trust_cannot_satisfy_execute_min_band = false`.** §15 constitutional ihlali.
23. **High intent_relay trust → execute eligibility.** §15 ihlali (Madde 6).
24. **LLM adapter verified band + execute capability declaration.** §15 ihlali.
25. **`adapter_emitted_neural_seed_allowed = true`.** §16 constitutional ihlali.
26. **Neural seed emission → demotion (immediate revoke değil).** §16 ihlali.
27. **Neural seed revoke sonrası recovery path.** §16 ihlali (terminal status).
28. **`demote_delta < promote_delta`.** §17 ihlali (asimetri ters).
29. **`band_demotion_threshold >= band_promotion_threshold`.** §17 ihlali (hysteresis yok).
30. **Critical violation rate'e tabi tutulmuş.** §17 ihlali.
31. **Restore sonrası adapter_trust reset.** §20 forgetting attack ihlali.
32. **Fork sonrası foreign adapter_trust native.** §20 R §14 ihlali.
33. **restore_with_missing_history sonrası adapter activation.** §20 R §13 ihlali.
34. **Trust record TTL = infinite.** §21 ihlali.
35. **U reverification cadence > P refresh window.** §21 cross-artifact ihlali.
36. **Missing U numerics → execute capability operational.** §22 ihlali.
37. **Missing U numerics → new adapter registration.** §22 ihlali.
38. **LLM tarafından üretilen veya değiştirilen U numeric.** Madde 6 ihlali.
39. **Dependency declarationsız U numeric.** §23 ihlali.
40. **Constitutional immutable key tek yön forbidden.** §4 ihlali.

**Artifact-level violations** (1-40, validation aşaması):
`MEMORY_RECORD_STATUS_CHANGED(target=artifact, new_status=rejected, reason=numerics_validation_failed)`.

**Runtime violations** (artifact valid ama runtime'da U caps'leri aştı):
Canonical `ADAPTER_MANIFEST_STATUS_CHANGED` + reason field; new event tipi yok.

---

## 27. Open Questions

U kapanırken cevaplanmamış bırakılan sorular:

- **Exact production values** (band cutoffs, demote/promote delta, rate limits) → signed artifact + implementation
- **`high_explicit_emergency` band** — `min_band_for_capability.execute` allowed_range'de geçiyor; bu bandın anlamı / kullanım koşulları → I spec revision veya implementation
- **Forked adapter recovery path** — fork sonrası foreign adapter_trust quarantined start; promotion için minimum koşul nedir? → operational + implementation
- **Multi-signature requirement for U artifact updates** → M §13 open question
- **Trust signal composition weighting** — multiplicative composition'da soft scores'a weight verilmeli mi? Şu an her soft score eşit; differential weight için review gerekir → implementation + safety review
- **Sleep cycle ile trust refresh coordination** → S §17 (sleep_pressure_threshold) ile koordinasyon
- **Cross-instance adapter trust verification protocol** → fork_birth + migration_birth için ayrı spec olabilir

Bu sorular cevaplanmadan implementation aşamasına geçilmez.

---

## Çekirdek özet — 18 karar + 40 violation tests

### 18 karar

1. U runtime config değildir; signed artifact + M2 reference.
2. U = dış uzva güvenme hakkının sayısal sözleşmesidir.
3. AdapterTrust ≠ SourceTrust; iki ayrı M2 subject_class.
4. Adapter trust source trust'a UPPER BOUND (one-way; constitutional).
5. Source trust adapter trust'ı YÜKSELTEMEZ (constitutional).
6. Trust score mechanical multiplicative composition; LLM/semantic input forbidden (Madde 6).
7. Hard gates (signature/manifest_hash/neural_seed_emission) composition'a girmez; immediate quarantine/revoke üretir.
8. Trust band'ları soft-overlap (N pattern); linear membership default; specialist neuron yaratamaz.
9. Capability flag tek başına yetki değildir; min_band_for_capability eşiği gerek.
10. Execute en yüksek bar (verified); execute > memory_writer/recall_provider/observe/intent_relay (constitutional hierarchy).
11. `trust_alone_grants_execution_permission = false` (constitutional); execute için 8 koşul AND.
12. Capability incompatibility override `false` constitutional (yüksek trust yasak kombinasyonu meşru yapmaz).
13. `adapter_emitted_neural_seed_allowed = false` + `revoke_required_on_neural_seed_emission = true` constitutional (immediate revoke; no recovery).
14. Intent relay LLM ceiling: execute/memory_writer/recall_provider satisfaction forbidden constitutional (Madde 6).
15. Demotion/promotion double-layer asymmetry: rate (demote ≥ promote × 2) + threshold (demotion < promotion, hysteresis).
16. Restore continuity required constitutional; fork foreign starts quarantined; restore_with_missing_history adapter activation forbidden.
17. Reverification cadence ≤ P refresh window (cross-artifact dependency).
18. Missing U numerics → risky capabilities (execute/memory_writer/recall_provider/intent_relay) DISABLED; observe-only operational.

### 40 violation tests

§26'da listelendi.

### Hard gates vs soft scores

```
Hard gates (gate, composition'a girmez):
    signature_validity         ∈ {0, 1}
    manifest_hash_integrity    ∈ {0, 1}
    neural_seed_emission_count = 0 always

Soft scores (composition multiplicative):
    channel_binding_compliance ∈ [0, 1]
    rate_compliance            ∈ [0, 1]
    execution_audit_score      ∈ [0, 1]
    uptime_stability           ∈ [0, 1]
```

> **Bazı trust sinyalleri çarpan değil, kapıdır.**

### Damıtma — son cümleler

> **U = dış uzva güvenme hakkının sayısal sözleşmesidir.**
>
> **Adapter powerful olabilir. Ama kendi güvenini kendi üretemez.**
>
> **Adapter dünyayı taşır. Compiler tonu üretir. Adapter neural_seed üretemez.**
>
> **High trust does not create new capability. Trust only enables declared, compatible, channel-bound capability.**
>
> **One attempt — immediate revoke. No clean window. No demotion gradient. Terminal.**
>
> **LLM intent_relay trust translation quality artırabilir; execute/memory_writer/recall_provider capability'sini açamaz.**
>
> **Yüksek güven, yasak capability kombinasyonunu meşru yapmaz.**
>
> **One clean window cannot undo one critical violation. Adapter güven yavaş kazanır, hızlı kaybeder.**
>
> **AdapterTrust SourceTrust'a tavan koyar. SourceTrust AdapterTrust'ı yükseltemez. Tek yön.**
>
> **Forked instance, eski instance'ın adapter güvenini native güven gibi devralamaz.**
>
> **N dış dünyanın hakkını sınırlar.**
> **O kendi geçmişine girme hakkını sınırlar.**
> **P hafızaya emin olma hakkını sınırlar.**
> **Q kendine bakma hakkını sınırlar.**
> **R kimliğini koruyarak geri dönme hakkını sınırlar.**
> **S nasıl doğacağını sınırlar.**
> **T hatırlatmanın ekonomisini sınırlar.**
> **U dış uzva güvenme hakkını sınırlar.**

---

## Phase Closure

**A-T conceptual + N-U numerics = 22 belge tamam.**

U conceptual + numerics phase'in **son artifact'idir**. Bu belge kapandığında:

- A: CONSTITUTION
- B: MEMORY_CONTRACT
- C: WORLD_INGRESS
- D: BOOTSTRAP_GENOME
- E: DEONTIC_GATE
- F: OBSERVER_LEDGER_SCHEMA
- G: MEMORY_WRITE_GATE
- H: RECALL_PROTOCOL
- I: ADAPTER_MANIFEST_SPEC
- J: INGRESS_COMPILER_SPEC
- K: REPLAY_PROTOCOL
- L: BACKUP_STRATEGY
- M: NUMERICS_GOVERNANCE
- N: INGRESS_COMPILER_NUMERICS
- O: REPLAY_PROTOCOL_NUMERICS
- P: MEMORY_WRITE_GATE_NUMERICS
- Q: OBSERVER_LEDGER_NUMERICS
- R: BACKUP_STRATEGY_NUMERICS
- S: BOOTSTRAP_GENOME_NUMERICS
- T: RECALL_PROTOCOL_NUMERICS
- U: ADAPTER_TRUST_NUMERICS
- + ATTENTION_WORKSPACE

**22 belge frozen draft v0.1.**

Sıradaki adım yeni conceptual / numeric belge **değildir**. Implementation
readiness review + build plan + first concrete artifact (e.g.,
`bootstrap_genome_numerics_v1.signed.json` production değerleri) konuşulur.
