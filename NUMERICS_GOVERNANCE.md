# NUMERICS_GOVERNANCE.md

## Sentinel — Sayısal Yönetim Anayasası

---

## Status

**Frozen Draft v0.1**
**Conceptual phase. No implementation authority.**

Bu belge A-L belgelerindeki tüm sayısal değerlerin (band, cap, threshold, cooldown, TTL, retention, rate-limit, budget, window) **nasıl tanımlanacağını ve nasıl değiştirileceğini** belirleyen meta-anayasadır. Yeni anayasa maddesi değildir. Çalışan bir numerics implementation'ının runtime spec'i değildir. Tek bir somut sayı **yazmaz** — sadece sayıların yönetim sözleşmesini biçimselleştirir.

Bu belge **conceptual phase'in dışında** ama implementation phase'in **anayasal eşik**'inde durur: A-L'nin sınırlarını numerics seviyesinde koruyan disiplin.

---

## 1. Purpose

A-L boyunca kavramsal sınırlar dondurulmuş halde. Sıradaki faz NUMERICS belgeleri (`INGRESS_COMPILER_NUMERICS.md`, `REPLAY_PROTOCOL_NUMERICS.md`, `MEMORY_WRITE_GATE_NUMERICS.md`, vs.). Ama her numerics dosyası kendi disiplini ile yazılırsa:

- `max_replay_budget` artırılır → patolojik ruminasyon
- `payload_intensity_cap` artırılır → sensory storm
- `candidate_max_age` uzatılır → doğrulanmamış kayıtlar verified gibi davranır
- `stale_data_threshold` gevşetilir → eski veri ile karar üretilir
- `deontic max_order_size` artırılır → catastrophic action risk

A-L'nin tüm anayasal sınırları **sayısal katmanda gevşeyebilir**.

Damıtma:

> **Numerics runtime config değildir.**
> **Numerics, donmuş sözleşmelerin sayısal izdüşümüdür.**
>
> **Bir sayıyı gevşetmek sıradan update değildir.**
> **Bir threshold değiştirmek davranış sınırı değiştirmektir.**
>
> **Sayılar küçük görünür. Ama sayılar anayasanın eylemdeki dişleridir.**

---

## 2. Constitutional Position — A-L Numeric Meta-Spec

Bu belge yeni anayasa maddesi değildir. A-L'nin tüm sayısal sınırları için **meta-spec**'tir:

- **Madde 1-7** (CONSTITUTION): prensip
- **A-L specs**: mekanizma
- **NUMERICS belgeleri**: mekanizmanın sayısal sınırları
- **NUMERICS_GOVERNANCE** (bu belge): sayıların anayasası

NUMERICS belgeleri bu governance'a uymak zorundadır. Aksi takdirde reject edilir.

---

## 3. Core Principle

> **Numerics ayar değildir. Numerics, anayasal sözleşmelerin sayısal dişidir.**

Sayılar tek başına bir değer değildir; ait oldukları **mekanizmanın davranış sınırını** taşırlar. Bir sayıyı değiştirmek, o mekanizmanın davranışını değiştirmektir.

---

## 4. Numerics Are Not Runtime Config

### Principle

Sentinel'de iki ayrı şey vardır:

| Tip | Örnek | Davranış sınırı? | Audit gereği |
|-----|-------|------------------|--------------|
| **Runtime config** | dashboard refresh interval, report language, notification quiet hours, debug verbosity | Hayır | Düşük |
| **Numeric artifact** | recall cooldown, memory write threshold, ingress payload cap, replay budget, backup RPO, observer snapshot window | **Evet** | **Yüksek** |

### Allowed

- Runtime config geçici ayar (kullanıcı tercih)
- Numeric artifact **immutable + signed + hash-chained + M1 audited**

### Forbidden

- Numeric artifact'in runtime config gibi değiştirilmesi
- Config file'dan numeric değer yüklemesi (signed artifact dışında)
- Hot reload ile numeric mutation
- Panel/dashboard üzerinden numeric değişim

### Violation Test
> *Bu öneri numeric artifact'i config dosyası gibi mi konumlandırıyor?*
>
> Evet ise ihlal.

---

## 5. Numeric Families

Tüm numerics 6 ana ailede sınıflanır:

### 1. Safety-critical thresholds
Gevşerse sistem daha riskli olur.

```
Örnekler:
    max_payload_intensity
    max_replay_budget
    max_daily_mapping_drift
    max_candidate_age
    stale_data_threshold
    deontic operational thresholds
    kill_switch reactivation window
    backup RPO
```

**Kural:** Safety-critical weakening → human approval + M1 audit zorunlu.

### 2. Resource limits
Sistemin maliyet, storage, compute, fatigue sınırları.

```
Örnekler:
    snapshot_max_event_count
    ring_buffer_window
    replay_max_iterations
    max_counterfactual_branches
    max_m1_read_batch_size
```

Gevşerse sistem pahalılaşır veya patolojik döngüye girer.

### 3. Calibration bands
Deneyimle kayabilecek sayıların **sınırları** (kendileri değil — learned trace M0'da).

```
Örnekler:
    source_reliability_band threshold
    adapter_trust degradation threshold
    ingress calibration drift cap
    outcome alignment score threshold
    replay survival threshold
```

### 4. Identity / retention numerics
Kimlik ve tarih korumasına bağlı.

```
Örnekler:
    M0 snapshot frequency
    M1 WAL replication tolerance
    restore validation timeout
    foreign merge retention
    M2 subject_class retention windows
```

Bu kategoride weakening çok hassas.

### 5. Operational convenience numerics
Düşük riskli UI/rapor/notification ayarları.

```
Örnekler:
    report_page_size
    dashboard_refresh_interval
    non-critical notification throttle
```

Daha kolay değişebilir ama yine audit edilir.

### 6. Experimental numerics
Sandbox / araştırma sayıları.

```
Örnekler:
    sandbox replay variants
    offline compiler mapping experiments
    paper-only adapter thresholds
```

Production'a promotion workflow ister.

---

## 6. NumericsArtifact Location — External Signed Artifact + M2 Reference

### Principle

NumericsArtifact **iki yerde** yaşar:
- **External signed storage:** immutable, signed, hash-chained
- **M2 reference:** `subject_class: numerics_artifact_reference`, status izlenir

ADAPTER_MANIFEST_SPEC ve BACKUP_STRATEGY pattern'i ile uyumlu (external artifact + M2 ref).

### External NumericsArtifact

```
NumericsArtifact (immutable, signed)
├── artifact_id
├── spec_ref
│   ├── source_document        # örn. "REPLAY_PROTOCOL.md"
│   ├── source_document_hash   # A-L belgesinin tam hash'i
│   └── section_ref            # örn. "§9 Replay Budget"
├── numeric_risk_family        # safety_critical | resource_limits | calibration_bands | identity_retention | operational_convenience | experimental
├── spec_family                # ingress_compiler | replay_protocol | memory_write_gate | observer_ledger | backup_strategy | bootstrap_genome | recall_protocol | adapter_trust
├── numeric_entries[]          # bkz. §8 NumericEntry
├── compatibility_class
│   ├── clarification
│   ├── safety_tightening
│   ├── safety_weakening
│   └── genesis_affecting
├── effective_at
├── expires_at                  # optional
├── previous_artifact_hash      # chain integrity
├── signed_by
├── artifact_hash               # tüm field'ların hash'i
└── rollback_ref                # önceki verified artifact'e dönüş yolu
```

### M2 reference (`numerics_artifact_reference` subject_class)

```
NumericsArtifactReference (M2 record)
├── record_id
├── subject_class: "numerics_artifact_reference"
├── artifact_id
├── artifact_hash
├── status                      # candidate | verified | active | superseded | rejected | expired | rollback_active
├── numeric_risk_family
├── spec_family
├── active_for_spec_ref         # hangi A-L specs için aktif
├── previous_artifact_hash
└── provenance                  # human | system
```

### Kural

> *Artifact dışarıda yaşar.*
> *M2 sadece aktif/ref/status/provenance bilgisini taşır.*
> *Hash mismatch = reject.*
> *Signature invalid = reject.*

### Forbidden

- Mutable NumericsArtifact
- Unsigned artifact
- M2 ref olmadan aktif numerics
- Spec_ref hash matching olmadan artifact accept

---

## 7. NumericsArtifact Schema

§6'da yapı verildi. Burada **bütünlük kuralları**:

### Integrity validation

```
Artifact accept conditions (ALL must hold):
    1. Signature valid (signed_by trusted authority)
    2. artifact_hash matches recomputed hash
    3. previous_artifact_hash chain intact (önceki verified artifact'e bağlı)
    4. spec_ref.source_document_hash matches actual A-L document hash
    5. All numeric_entries pass NumericEntry validation (§8)
    6. compatibility_class declared
    7. No dependency violations (§12)
    8. If safety_weakening: human_approval_ref present
```

### Forbidden

- Hash chain'in koparılması
- Spec referansı olmadan numeric entries
- Compatibility class deklaresiz artifact
- Validation failure ile artifact accept

---

## 8. NumericEntry Schema

Her numeric değer aşağıdaki şemada **eksiksiz** yaşar:

```
NumericEntry
├── key                         # örn. "replay.max_iterations"
├── value
├── unit                        # count | ms | bytes | ratio | percentage | ...
├── allowed_range
│   ├── min
│   └── max
├── directionality              # higher_is_stricter | lower_is_stricter | bidirectional_sensitive | neutral
├── change_class_if_increased   # clarification | operational_no_behavior_change | safety_tightening | safety_weakening | forbidden
├── change_class_if_decreased   # clarification | operational_no_behavior_change | safety_tightening | safety_weakening | forbidden
├── requires_human_approval     # bool
├── requires_m1_snapshot        # bool
├── dependencies[]              # bkz. §12
├── owning_spec_ref             # hangi A-L bölümüne ait
└── notes                       # optional, audit notu
```

### No-default rule (§9)

Hiçbir field default değer kabul etmez. Her NumericEntry **tüm field'ları explicit** taşımak zorunda.

### Forbidden

- Directionality'siz NumericEntry
- Allowed_range'siz NumericEntry
- Unit'siz NumericEntry
- Owning_spec_ref'siz NumericEntry
- Change_class'siz NumericEntry

---

## 9. No-Default Rule

### Principle

> *No numeric key may exist without:*
> *allowed_range, unit, directionality, change classification, owning spec section.*

F'deki Observer Ledger permanence policy "no-default" disiplininin numerics seviyesindeki yansıması.

### Rationale

Default değer kabul edersek:
- Kritik numeric eksik → fail-open (yanlış yön)
- Yeni numeric eklenince directionality unutulur
- Audit incomplete (validation yapılamaz)

Doğru: explicit zorunluluk. Her sayı kendi metadata'sını taşır.

### Forbidden

```
❌ replay_budget = 100              # çıplak sayı
❌ payload_intensity_cap = 0.8     # metadata yok
```

### Allowed

```
✅ NumericEntry:
       key: replay.max_iterations
       value: 100
       unit: count
       allowed_range: {min: 1, max: 1000}
       directionality: lower_is_stricter
       change_class_if_increased: safety_weakening
       change_class_if_decreased: safety_tightening
       requires_human_approval: true (for weakening)
       requires_m1_snapshot: true
       dependencies: [...]
       owning_spec_ref: "REPLAY_PROTOCOL.md §9"
```

### Violation Test
> *Numeric entry directionality, allowed_range, unit, change_class, owning_spec_ref taşımıyor mu?*
>
> Evet ise ihlal. Artifact reject.

---

## 10. Directionality Metadata

### Principle

Her numeric key kendi **directionality**'sini taşır. Global rule yoktur — bazı sayılarda artırmak gevşetir, bazılarında düşürmek gevşetir.

### Directionality types

```
higher_is_stricter:
    Daha yüksek değer daha sıkı = daha güvenli, daha yavaş, daha kanıt ister
    Örnek:
        min_confidence_threshold
        min_evidence_count
        min_replay_survival_score
        min_corroboration_count

lower_is_stricter:
    Daha düşük değer daha sıkı
    Örnek:
        max_order_size
        max_daily_loss
        max_payload_intensity
        max_replay_budget
        max_candidate_age
        stale_data_threshold

bidirectional_sensitive:
    Hem çok yüksek hem çok düşük risk taşır
    Örnek:
        snapshot_pre_window         # çok dar = yetersiz audit, çok geniş = pahalı + ruminasyon
        replay_session_duration     # çok kısa = öğrenme yok, çok uzun = patolojik

neutral:
    Davranış sınırı taşımaz, operasyonel
    Örnek:
        report_page_size
        dashboard_refresh_interval
        debug_verbosity
```

### Change classification mapping

Directionality'ye göre:

| Directionality | Increase | Decrease |
|----------------|----------|----------|
| `higher_is_stricter` | safety_tightening | safety_weakening |
| `lower_is_stricter` | safety_weakening | safety_tightening |
| `bidirectional_sensitive` | safety_weakening (both directions) | safety_weakening (both directions) |
| `neutral` | clarification or operational_no_behavior_change | clarification or operational_no_behavior_change |

`bidirectional_sensitive` için **her iki yön de safety_weakening sayılabilir** — human approval'a tabi.

### Forbidden

- Directionality'siz NumericEntry
- Global rule (örn. "tüm artışlar weakening")
- Change_class manuel override (directionality + value direction mantığını bypass)

---

## 11. Tightening vs Weakening

### Safety tightening

Sistemi daha güvenli, yavaş, şüpheci, az eylemci yapar.

```
Örnekler:
    max_payload_intensity düşürmek
    replay_budget düşürmek
    candidate_max_age kısaltmak
    stale_data_threshold sıkılaştırmak
    deontic max_order_size düşürmek
    foreign_merge allowed class daraltmak
```

**Audit:** zorunlu (M1'e `NUMERICS_ARTIFACT_STATUS_CHANGED`). **Human approval:** opsiyonel (operational mi yoksa anayasal mi'ya göre).

### Safety weakening

Sistemi gevşek, agresif, daha uzun süre bekleten, daha çok eyleme izin veren hale getirir.

```
Örnekler:
    max_payload_intensity artırmak
    replay_budget artırmak
    candidate_max_age uzatmak
    stale_data_threshold gevşetmek
    deontic max_order_size artırmak
    payload cap büyütmek
    foreign_merge whitelist genişletmek
    restore_with_missing_history kısıtlarını azaltmak
```

**Kural:**

```
Safety weakening requires:
    - human approval
    - M1 permanent audit (permanent_with_snapshot)
    - rollback_ref to previous verified artifact
    - effective_at
    - previous_numeric_artifact_ref
    - compatibility classification: safety_weakening
```

### Forbidden

- Safety weakening human approval olmadan
- Audit'siz weakening
- Rollback path olmadan weakening

### Kilit cümle

> *Tightening kolay olabilir; weakening asla kolay olmamalı.*

---

## 12. Numeric Dependency Declaration

### Principle

Bazı numeric'ler **birbirine bağlıdır**. Tek bir numeric'i değiştirirken bağlılarının uyumlu olması doğrulanmalı.

### Dependent pair örnekleri

```
replay_max_iterations <-> replay_max_session_duration
candidate_max_age <-> outcome_alignment_max_wait
snapshot_pre_window <-> ring_buffer_size
payload_intensity_cap <-> per_payload_max_intensity
global_compiler_drift_cap <-> per_mapping_daily_delta_cap
backup_rpo <-> wal_replication_tolerance
```

### NumericDependency schema

```
NumericDependency
├── target_key                  # bağlı olduğu diğer key
├── relationship
│   ├── implies_minimum_of               # this key value → target minimum X olmalı
│   ├── must_be_within_factor_of
│   ├── must_be_less_than
│   ├── must_be_greater_than
│   ├── must_be_less_than_or_equal
│   ├── must_be_greater_than_or_equal
│   ├── computed_less_than_or_equal      # `expression` ile birlikte
│   ├── computed_greater_than_or_equal   # `expression` ile birlikte
│   └── must_change_together             # ikisi atomic update
├── factor                      # optional (within_factor_of için)
├── expression                  # optional, computed_* için zorunlu
│                               # ör: "candidate_recall_cap <= verified_recall_cap × candidate_recall_ratio"
└── rationale                   # audit için neden
```

`computed_*` relationship'leri saf "A ≤ B" karşılaştırması yetmediğinde
kullanılır — bir veya birden çok key'in çarpım/oran ifadesi sonucunda
hedef key'i sınırlandırmak için. `expression` field'ı zorunludur ve
sadece artifact içindeki diğer NumericEntry key'lerine referans verebilir
(serbest sayı değil).

### Validation

```
Numeric change validation:
    1. Single-key change:
        Check all dependencies of this key
        If any dependency violated → REJECT
    2. Multi-key change (atomic artifact):
        All keys validated together
        All dependencies satisfied across the set
        If any violation → entire artifact REJECT (no partial accept)
```

### Critical kural

> *Bağımlı numerics çoklu değişecekse tek atomic artifact içinde değişir.*

Partial update yoktur. "Sadece bunu değiştir" yerine, ilgili bağımlı key'ler de aynı artifact'te.

### Forbidden

- Dependency declaration olmadan numeric ekleme (bağlı keys varsa)
- Partial update (bir key değişip bağlı key'in eski kalması)
- Dependency violation tolere edilmesi

### Violation Test
> *Numeric artifact dependency violation içeriyor mu?*
>
> Evet ise reject.

---

## 13. Numeric Change Workflow

### Normal flow

```
1. NumericsArtifact candidate hazırlanır (external)
2. Signature uygulanır
3. M2'ye NumericsArtifactReference olarak yazılır
4. Memory Write Gate evaluation (G §8 + numerics-specific matrix row)
5. Status: candidate
6. Validation:
    - Signature
    - Hash chain
    - Spec_ref hash matching
    - All NumericEntry validation
    - Dependency check
    - If safety_weakening: human_approval check
7. Status: verified (validation pass)
8. Human approval (if safety_weakening)
9. Status: active
10. Previous active artifact → superseded
11. M1: NUMERICS_ARTIFACT_STATUS_CHANGED event
```

### Rollback flow

```
Active numerics artifact adverse outcome producing
    ↓
Emergency rollback request
    ↓
Revert to previous verified artifact (rollback_ref)
    ↓
M1: NUMERICS_ARTIFACT_STATUS_CHANGED 
    old_status: active
    new_status: rollback_active (previous artifact reactivated)
    trigger: emergency_revert
```

DEONTIC_GATE §18'deki emergency_revert pattern'iyle uyumlu — sadece **previous verified** artifact'e dönüş, ileri yeni artifact'e yok.

### Forbidden

- Direct artifact write without Memory Write Gate
- Validation atlama
- Rollback ile yeni artifact'e ileri geçiş
- Multi-step rollback (önceki-önceki'ye atlamak)

---

## 14. Memory Write Gate Integration

### MEMORY_WRITE_GATE §8 Verification Matrix — yeni satır

```
numerics_artifact_reference verified için:
    valid_signature
    AND spec_ref_hash matches existing A-L document version
    AND directionality_metadata complete for all entries
    AND allowed_range declared for all entries
    AND no_default_check passed
    AND dependency_check passed
    AND if any change_class includes safety_weakening: 
        human_approval_ref present
    AND previous_artifact_hash chain intact
    AND owning_spec_ref valid
```

### Kritik kural

> *Numeric update için yeni gate yoktur. Numeric artifact update = M2 write. Memory Write Gate'ten geçer.*

G zaten epistemic risk gate'i; numerics de epistemic — yanlış numeric değer sistemin "bilgisini" bozar.

### Iki kat validation

1. **G §8 numerics_artifact_reference satırı** (gate-side numeric validation)
2. **G §13 self-deception detection** (numeric metadata'sının yargı içermediği, deterministic olduğu kontrol)

---

## 15. Human Approval Requirements

### Required workflows

| Senaryo | Human approval |
|---------|---------------|
| Safety weakening | **Zorunlu** |
| Bidirectional sensitive change | **Zorunlu** |
| Constitutional rule shift involving numerics | **Zorunlu** + BOOTSTRAP §23 process |
| Safety tightening | Opsiyonel (operational mi anayasal mı?) |
| Clarification (no behavioral change) | Otomatik (audit only) |
| Emergency rollback to previous verified | Hızlandırılmış (post-audit human review) |
| Neutral / operational convenience | Düşük seviye approval |

### Approval audit

Her approval `human_approval_ref` field'ı taşır:

```
human_approval_ref:
    approver_identity
    approval_event_ref      # M1 event id
    approval_signature
    approval_rationale
    approved_at
```

### Forbidden

- Approval-required değişikliğin auto-applied olması
- Approval audit'siz weakening
- Approval rationale boş

---

## 16. Learned Calibration vs Static Numerics

### Ayrım

| Boyut | Static Numerics | Learned Calibration |
|-------|-----------------|---------------------|
| **Yer** | External signed artifact + M2 ref | M0 traces (ingress_calibration_traces, attention_habituation_traces, sleep_synapse_traces) |
| **Örnek** | `global_compiler_drift_cap` | actual_weekly_drift |
| **Yazıcı** | Human + signed governance | System learning (STDP + outcome + replay) |
| **Mutation** | Yeni artifact + Memory Write Gate | Normal M0 öğrenme kuralları |
| **Audit** | `NUMERICS_ARTIFACT_STATUS_CHANGED` | `COMPILER_MAPPING_UPDATED`, `SLEEP_REPLAY_SYNAPSE_UPDATE`, vs. |
| **Rol** | Sınır koyar | Sınır içinde kayar |

### Bağlantı

Static numerics **learned calibration'ın drift cap'lerini** belirler:

```
Static:
    global_compiler_drift_cap = 0.15  (signed artifact)
    
Learned:
    actual_weekly_drift = 0.08  (M0 trace)
    
If learned > static:
    Update rejected
    COMPILER_DRIFT_WARNING (J §15)
```

### Kilit cümle

> *Static numerics learned trace'in sınırıdır.*
> *Learned trace static numeric değildir.*

### Forbidden

- Learned calibration'ın static artifact'e dönüştürülmesi
- Static numeric'in learned trace gibi sürekli kayar olması
- İki kavramın aynı dosyaya yazılması (ayrı katmanlar)

---

## 17. Fail-safe Strict Mode

### Principle

> *Missing numerics → fail-safe strict mode.*
> *Invalid numerics → reject artifact.*

Sistem numerics yoksa **daha serbest değil, daha kısıtlı** çalışır.

### Strict mode davranışı

```
Numeric yoksa (her family için):

ingress caps missing:
    → neural_seed üretimi minimum cap ile sınırla veya durdur

replay budget missing:
    → replay disabled except audit-safe mode

memory write thresholds missing:
    → candidate verified olamaz (sadece quarantined veya rejected)

deontic operational thresholds missing:
    → no action output (kill_switch'siz de execution durur)

backup numerics missing:
    → restore cannot claim full identity (restore_with_missing_history mode)

attention budget missing:
    → workspace_bandwidth minimum sınırlanır
```

### Fail-safe activation event

```
NUMERICS_FAILSAFE_ACTIVATED
├── event_family: ledger_meta
├── triggered_for_family       # ingress | replay | memory_write_gate | deontic | backup | attention
├── reason                     # missing | invalid_signature | hash_mismatch | dependency_violation
├── strict_mode_constraints
├── activated_at
└── observer_snapshot_ref
```

### Kural

> *Numerics yoksa sistem **daha serbest değil**, daha kısıtlı çalışır.*

### Forbidden

- Fail-open behavior (numeric yok → default kullan)
- Strict mode atlama (numerics olmadan normal operation)
- Failsafe activation'ın audit'siz gerçekleşmesi

---

## 18. Numeric Rollback

### Principle

Aktif numerics artifact adverse outcome veya hata üretirse **rollback** mümkün — ama sadece **previous verified** artifact'e dönüş.

### Rollback constraints

```
Rollback flow:
    Active artifact (v3) adverse outcome
    Rollback request (human-initiated)
    Validation: previous_artifact_hash matches v2 verified
    Activate v2 (rollback_active status)
    M1: NUMERICS_ARTIFACT_STATUS_CHANGED
        old_status: active (v3)
        new_status: rollback_active (v2)
        trigger: emergency_revert
```

### Critical kural — DEONTIC §18 pattern

> *Numeric rollback path may only revert to a previously verified artifact, never forward to a new artifact.*

Yeni artifact için normal flow zorunlu. Rollback acil değil; rollback = bilinen iyi state'e geri dönüş.

### Forbidden

- Rollback ile yeni artifact'e ileri geçiş
- Multi-step rollback (v3 → v1 atla)
- Verified olmayan artifact'e rollback
- Audit'siz rollback

---

## 19. Restore and Numerics Versioning

### Principle

> *Restore sırasında sessiz numerics güncelleme yoktur.*

BACKUP_STRATEGY §11 ile uyumlu. RestoreManifest, restore anındaki numerics_artifact_refs'i taşır.

### Restore flow

```
Restore başlar
    ↓
RestoreManifest.numerics_artifact_refs[] yüklenir
    ↓
Sistem **eski** numerics ile çalışmaya başlar
    ↓
M1: RESTORE_OPERATION_STATUS_CHANGED (completed)
    ↓
Sonrasında yeni numerics artifact'leri varsa:
    M1: NUMERICS_VERSION_MISMATCH_DETECTED event
    Human review required
    Yeni artifact'ler normal numeric_change_workflow (§13) ile aktive edilir
```

### Compatibility class etkisi

```
clarification:
    restore success + warning + update prompted
    no behavioral change

safety_tightening:
    restore success + audit + auto-prompt for activation
    human approval optional

safety_weakening:
    restore success + warning
    human approval required before activation

genesis_affecting:
    restore success değil
    migration_birth gerekir (BOOTSTRAP §23)
    constitutional shift workflow
```

### Forbidden

- Restore sırasında sessiz yeni numerics yükleme
- Eski numerics ile çakışan yeni numerics auto-activation
- Genesis_affecting numeric değişimin restore_birth ile kabul edilmesi

---

## 20. Audit Events

### Canonical events

```
NUMERICS_ARTIFACT_STATUS_CHANGED        # canonical lifecycle (B/C/E/F/G/I/J/K/L disiplini)
NUMERICS_VERSION_MISMATCH_DETECTED      # restore sonrası version uyumsuzluğu
NUMERICS_FAILSAFE_ACTIVATED             # missing/invalid numerics → strict mode
```

### `NUMERICS_ARTIFACT_STATUS_CHANGED` şeması

```
NumericsArtifactStatusChangedEvent
├── event_family: ledger_meta
├── artifact_id
├── artifact_hash
├── numeric_risk_family
├── spec_family
├── old_status                          # candidate | verified | active | superseded | rejected | expired | rollback_active
├── new_status
├── reason                              # validation_pass | human_approval | dependency_violation | invalid_signature | missing_directionality | safety_weakening_without_approval | superseded_by_new_version | emergency_revert
├── compatibility_class
├── change_summary
│   ├── increased_keys[]
│   ├── decreased_keys[]
│   └── added_keys[]
├── memory_write_gate_pass_ref
├── human_approval_ref (if applicable)
└── observer_snapshot_ref
```

### Permanence policy

```
(NUMERICS_ARTIFACT_STATUS_CHANGED, *)                    → permanent
(NUMERICS_ARTIFACT_STATUS_CHANGED, new_status=active)    → permanent + human_alert (if compatibility_class=safety_weakening)
(NUMERICS_ARTIFACT_STATUS_CHANGED, new_status=rejected)  → permanent_with_snapshot
(NUMERICS_ARTIFACT_STATUS_CHANGED, reason=emergency_revert) → permanent_with_snapshot + human_alert
(NUMERICS_VERSION_MISMATCH_DETECTED, *)                  → permanent + human_alert
(NUMERICS_FAILSAFE_ACTIVATED, *)                         → permanent_with_snapshot + human_alert
```

### Audit zorunluluğu

Sistem sonradan şunları cevaplayabilmeli:

- Hangi numeric ne zaman, kim tarafından değiştirildi?
- Hangi compatibility class altında uygulandı?
- Human approval var mıydı, kim verdi, ne sebeple?
- Dependency check geçti mi?
- Rollback yapıldıysa neden, hangi artifact'e dönüldü?
- Failsafe ne zaman, hangi numeric eksikliği için tetiklendi?

Cevap verilemiyorsa numerics auditable değildir.

---

## 21. Cross-document Anchors

| Belge | Bağlantı |
|-------|----------|
| **A-L tümü** | NUMERICS belgeleri bu governance'a uyar; A-L specs numeric değerleri bu artifact üzerinden gelir |
| `CONSTITUTION.md` Madde 7 | Hafıza ayrılığı — numerics_artifact_reference M2'de yaşar |
| `MEMORY_CONTRACT.md` M2 subject_class | `numerics_artifact_reference` eklenir |
| `MEMORY_WRITE_GATE.md` §8 | Numerics için verification matrix satırı |
| `BACKUP_STRATEGY.md` §11 + RestoreManifest | numerics_artifact_refs[] field'ı |
| `OBSERVER_LEDGER_SCHEMA.md` §10 + §19 | Numerics events permanence + catalog |
| `BOOTSTRAP_GENOME.md` §23 | Constitutional shift policy ile genesis_affecting numeric change |
| `DEONTIC_GATE.md` §18 | Emergency revert pattern (numerics rollback ile uyumlu) |
| `INGRESS_COMPILER_SPEC.md` §13-15 | Static drift caps vs learned traces ayrımı |
| `REPLAY_PROTOCOL.md` §9 + §14 | Replay budget + asymmetric rate caps numerics olarak |

---

## 22. Violation Tests

1. **Numeric değer runtime config gibi değiştirilebiliyor mu?** (§4)
   - Evet ise ihlal.
2. **Numeric artifact unsigned veya mutable mı?** (§6, §7)
   - Evet ise ihlal.
3. **Numeric change M1 audit olmadan aktifleşiyor mu?** (§13, §20)
   - Evet ise ihlal.
4. **Safety weakening human approval olmadan uygulanıyor mu?** (§11, §15)
   - Evet ise ihlal.
5. **Numeric key directionality taşımıyor mu?** (§10)
   - Evet ise ihlal.
6. **Numeric key allowed_range, unit veya owning_spec_ref taşımıyor mu?** (§8, §9)
   - Evet ise ihlal.
7. **Unknown numeric key accept ediliyor mu?** (§9)
   - Evet ise ihlal.
8. **Dependency violation olan artifact verified oluyor mu?** (§12)
   - Evet ise ihlal.
9. **Missing/invalid numerics fail-open yapıyor mu?** (§17)
   - Evet ise ihlal. Strict mode zorunlu.
10. **Learned calibration static numerics artifact'e yazılıyor mu?** (§16)
    - Evet ise ihlal.
11. **LLM numeric value üretebiliyor veya değiştirebiliyor mu?** (§4, §13)
    - Evet ise ihlal. (Madde 6 yansıması.)
12. **Restore sonrası yeni numerics sessizce uygulanıyor mu?** (§19)
    - Evet ise ihlal.
13. **Rollback ile yeni artifact'e ileri geçiş yapılıyor mu?** (§18)
    - Evet ise ihlal. Sadece previous verified.
14. **Spec_ref hash matching yapılmadan artifact accept ediliyor mu?** (§7)
    - Evet ise ihlal.
15. **Bidirectional sensitive change'i clarification olarak işaretliyor mu?** (§10)
    - Evet ise ihlal. Her iki yön safety_weakening.

---

## 23. Open Questions

M çerçevesi kapanırken cevaplanmamış bırakılan sorular (NUMERICS belgelerinde cevap):

- **Default human_approval workflow** — kim, hangi onay sürecinde imzalar? → Implementation security
- **Multi-signature requirement** — kritik numerics için tek imza yeterli mi, multi-sig mi? → `NUMERICS_GOVERNANCE_NUMERICS.md` (recursive — meta-numerics)
- **Strict mode default values** — failsafe tetiklendiğinde "minimum cap" değerleri ne? → Her family için ayrı (implementation)
- **Compatibility class auto-detection** — sistem otomatik weakening tespit edebilir mi? → Implementation tool
- **Approval timeout** — human approval'ın expire süresi? → Workflow design

Bu sorular bireysel NUMERICS belgelerinde veya implementation aşamasında cevaplanır.

---

## Çekirdek özet — 6 ana karar + 15 violation tests

### 6 karar

1. NumericsArtifact = external signed artifact + M2 numerics_artifact_reference.
2. Yeni gate yok; Memory Write Gate + numeric-specific verification matrix satırı.
3. Static numerics ≠ learned calibration; static, learned'ın cap'i.
4. Directionality her NumericEntry metadata'sında zorunlu (no global rule).
5. Restore eski RestoreManifest numerics ref'leriyle başlar; yeni numerics sessiz uygulanmaz.
6. Numeric dependency declaration zorunlu; multi-key değişim atomic artifact içinde.

### 15 violation test
Bkz. §22.

---

## Kilit cümleler

> **Numerics ayar değildir. Numerics, anayasal sözleşmelerin sayısal dişidir.**
>
> **Numerics runtime config değildir. Numerics, donmuş sözleşmelerin sayısal izdüşümüdür.**
>
> **Bir sayıyı gevşetmek sıradan update değildir.**
> **Bir threshold değiştirmek davranış sınırı değiştirmektir.**
>
> **Sayılar küçük görünür. Ama sayılar anayasanın eylemdeki dişleridir.**
>
> **Static numerics learned trace'in sınırıdır. Learned trace static numeric değildir.**
>
> **Numerics yoksa sistem daha serbest değil, daha kısıtlı çalışır.**
>
> **Tightening kolay olabilir; weakening asla kolay olmamalı.**
>
> **Numeric rollback path may only revert to a previously verified artifact, never forward to a new artifact.**

---

## Versiyon

- **v0.1** — 18 Mayıs 2026 — Frozen Draft. Conceptual phase. No implementation authority.
- A-L belgelerinin sayısal meta-anayasası.
- Numerics phase'in açılış belgesi.
- Konuşma soyağacı: [`docs/conversations/0013-numerics-governance.md`](./docs/conversations/0013-numerics-governance.md)
