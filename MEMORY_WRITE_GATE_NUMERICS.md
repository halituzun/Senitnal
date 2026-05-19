# MEMORY_WRITE_GATE_NUMERICS.md

## Sentinel — Memory Write Gate Numeric Sözleşmesi

---

## Status

**Frozen Draft v0.1**
**Conceptual phase. No implementation authority.**

Bu belge `MEMORY_WRITE_GATE.md`'nin (G) numerics artifact'idir. `NUMERICS_GOVERNANCE.md`'nin (M) tüm meta-kurallarına uyar. Çalışan bir Memory Write Gate implementation'ının kesin sayısal değerlerini vermez — **conceptual band ranges, cap formatları, subject_class × evidence_axis matrix ve dependency invariants** verir; production değerleri ayrı **signed numerics artifact** (örn. `memory_write_gate_numerics_v1.signed.json`).

`spec_family: memory_write_gate`.

---

## 1. Purpose

G (MEMORY_WRITE_GATE) M2'ye yazma için epistemik freni tanımladı: subject_class × evidence_axes verification matrix, statü makinesi (candidate/verified/active/quarantined/superseded/rejected/expired), self-deception detection, silent gate principle, `MEMORY_RECORD_STATUS_CHANGED` canonical event. Ama gerçek **numerical eşik** yoktu:

- Her subject_class için `candidate_max_age` ne?
- `quarantine_max_age` subject'e göre nasıl değişir?
- `min_evidence_count` her axis için kaç?
- `contradiction_threshold` band'ları nerede?
- `internal_only_ref_ratio` cap'i ne?
- Replay survival vs outcome alignment ağırlıkları subject_class başına nasıl dağılır?

P bu sayısal eşikleri verir.

### Damıtma

> **Memory Write Gate numerics runtime config değildir.**
> **P, hafızaya gerçekmiş gibi yazma hakkının sayısal sözleşmesidir.**
>
> **Sistem kendi açıklamasını üretebilir. Ama kendi açıklamasını kanıt sayamaz.**
>
> **Self-explanation is not proof.**
> **Internal-only refs cannot satisfy verification alone.**
>
> **Halit yazdı = Halit'in beyanı kayda geçti.**
> **Halit yazdı ≠ dünya iddiası otomatik doğru.**

Tek cümle: **P = epistemik fren sözleşmesidir.** N dış dünyanın çekirdeğe ne kadar dokunabileceğini sınırlıyordu. O sistemin geçmişi ne kadar kurcalayabileceğini sınırlıyordu. P sistemin hafızaya **ne kadar emin olabileceğini** sınırlar.

### Üç riski sayısal olarak çözmek zorunda

```
1. Gevşek eşik    → sistem kendi anlatısına inanır (self-deception)
2. Sert eşik      → hiçbir şey verified olamaz (epistemic paralysis)
3. Tek-yön cap    → verified status sticky değildir, tek karşı kanıtla devrilir
```

---

## 2. Governance Position — NUMERICS_GOVERNANCE + MEMORY_WRITE_GATE + bridges

Bu belge:
- **NUMERICS_GOVERNANCE.md** (M) meta-spec'ine **zorunlu uyar**: NumericEntry no-default, directionality metadata, dependency declarations (computed_* dahil), signed artifact + M2 reference, Memory Write Gate üzerinden update, fail-safe strict mode, rollback only to previous verified
- **MEMORY_WRITE_GATE.md** (G) §8-§13'ün sayısal tarafı
- **MEMORY_CONTRACT.md** (B) §3-§11 subject_class taksonomisi + provenance + staleness disciplini
- **REPLAY_PROTOCOL_NUMERICS.md** (O) §14, §17 ile **bridge**: O global replay_survival_weight cap; P per-subject dağıtımı (`max over P <= O global cap`)
- **BACKUP_STRATEGY.md** (L) §10 `internal_only_refs` / `external_corroboration_refs` ayrımı numerics'leştirilir
- **INGRESS_COMPILER_NUMERICS.md** (N) — soft-overlap membership reuse (band cutoff disiplini)

### Numerics family classification

```
spec_family:           memory_write_gate
numeric_risk_family:   primarily safety_critical + identity_retention + calibration_bands
```

Spec_family etiketi: tüm key'ler `memory_write.*` namespace'inde.

Numeric risk family çoğunluğu **safety_critical**: verified eşikleri, contradiction caps, self-deception risk threshold'ları, supersede asymmetry — hepsi davranış sınırı. Bir kısım **identity_retention**: TTL'ler (candidate_max_age, quarantine_max_age), refresh windows. Band cutoff'lar **calibration_bands** (contradiction band geçişleri).

### owning_spec_ref

```
MEMORY_WRITE_GATE.md@v0.1
```

---

## 3. Core Principle

### Epistemik fren

Memory Write Gate'in sayısal hali, "ne kadar emin olmamız gerek?" sorusunun **subject_class × evidence_axis pivot tablosu**:

```
verified(<subject_class>, <record>) iff
    for each evidence_axis required by G §8 for <subject_class>:
        record.<axis>.value >= P.min_threshold.<subject_class>.<axis>
    AND
    contradiction_band(<record>) <= P.contradiction_band_max_for_new_verified.<subject_class>
    AND
    self_deception_risk(<record>) below P.max_internal_only_ref_ratio.<subject_class>
    AND
    record.age < P.candidate_max_age_ms.<subject_class>
```

Hiçbir koşul gevşeyemez (silent gate). Her eşik **subject_class spesifik** ve **explicit NumericEntry**.

### Üç ana asimetri (P'ye özgü)

```
1. Verified stickiness
   demote eşiği > promote eşiği
   (verified status'tan düşmek zor; verified'a çıkmak zor)

2. Internal vs external evidence
   internal_only refs verified için tek başına yetmez
   external corroboration zorunlu (subject_class'a bağlı)

3. Real outcome > Replay survival (O bridge)
   per subject_class: outcome_alignment_weight > replay_survival_weight
   global cap: max(replay_survival_weight.*) <= O global cap
```

### G-bridge — verification matrix completeness

Bu P'nin O'nun N-bridge'ine analoğu:

```
G §8 verification matrix discipline:
    Tanımlı her (subject_class, evidence_axis) çifti P'de bir NumericEntry'e karşılık gelmek zorunda.
    Eksik kombinasyon → P artifact validation REJECT.

Numeric threshold olmayan (subject_class, evidence_axis) çifti verified üretmez.
```

Bu G'nin "matrix satırı olmayan subject_class verified olamaz" kuralının numeric tarafı.

---

## 4. Numeric Artifact Metadata

### Artifact identity

```
artifact_type:         numerics_artifact
spec_family:           memory_write_gate
owning_spec_ref:       MEMORY_WRITE_GATE.md@v0.1
numerics_version:      v0.1
signed:                external (per NUMERICS_GOVERNANCE §3)
m2_reference:          numerics_artifact_reference (per MEMORY_CONTRACT §3)
status_event:          NUMERICS_ARTIFACT_STATUS_CHANGED
```

### Every NumericEntry carries (M §6 no-default)

```
key                          memory_write.<group>.<subject_class>[.<axis>]
value                        production sayı (signed artifact)
unit                         ms | count | ratio | enum | enum_set | band_name
allowed_range                {min, max} or set/enum constraint
directionality               lower_is_stricter | higher_is_stricter
                            | bidirectional_sensitive | neutral
change_class_if_increased    safety_weakening | safety_tightening
                            | operational_no_behavior_change
                            | forbidden
change_class_if_decreased    (same enum)
requires_human_approval      bool
dependencies                 [NumericDependency...]
numeric_risk_family          safety_critical | identity_retention
                            | calibration_bands | operational_convenience
                            | experimental
spec_family                  memory_write_gate
owning_spec_ref              "MEMORY_WRITE_GATE_NUMERICS.md §X"
```

### enum_set convention (P'de tanıtılır)

`auto_verified_human_subject_classes` gibi key'ler için `unit: enum_set`. Convention:

```
For enum_set NumericEntry:
    increase = set expansion (whitelist genişler)
    decrease = set contraction (whitelist daralır)
    
Directionality: lower_is_stricter (genelde whitelist'in genişlemesi safety_weakening)
allowed_range: subset_of_<canonical_enum>
```

Bu convention M §7 change_class enum'una **ek** değil, **interpretation**.

---

## 5. Subject Class Numeric Matrix

### Matrix scaffolding

Her subject_class için zorunlu numeric setleri:

```
Per subject_class:
├── candidate_max_age_ms                      (§6)
├── quarantine_max_age_ms                     (§7)
├── refresh_required_window_ms                (§8)
├── epistemic_staleness_threshold_ms          (§8, O bridge canonical)
├── evidence axis min_threshold.<axis>        (§9-10)
├── min_evidence_count                        (§10)
├── min_observation_temporal_separation_ms    (§11)
├── min_causal_refs                           (§12)
├── min_cross_source_corroboration            (§13)
├── contradiction_band_max_for_new_verified   (§14)
├── contradiction_band_required_to_demote_verified (§14)
├── duplicate_match_threshold                 (§15)
├── supersede_confidence_delta_min            (§15)
├── max_internal_only_ref_ratio               (§16)
├── external_corroboration_min_count          (§16)
├── replay_survival_weight                    (§17)
├── outcome_alignment_weight                  (§17)
└── human_signature_requirement               (§18)
```

### Subject class enumeration (B §3'ten)

```
M2 subject_class:
    source_trust
    adapter_trust
    procedural
    structured_fact
    incident
    episodic
    narrative_claim
    causal_explanation
    decision_rationale
    deontic_policy
    bootstrap_reference
    signed_administrative_reference
    operator_decision_record
    deontic_kill_switch_action_record
    numerics_artifact_reference (P §20)
```

Her subject için yukarıdaki numeric set'in **tamamı veya G §8 matrix'inde tanımlı subset**'i zorunlu. Eksik → P artifact validation REJECT.

### Provenance metadata — NOT subject_class

```
Provenance metadata (B §10), not subject_class:
    foreign_instance_origin
```

`foreign_instance_origin` **subject_class değil; provenance metadata field**'idir.
Bu yüzden kendi TTL / evidence / contradiction numeric satırını **almaz**.
Import edilen foreign kayıtlar orijinal subject_class'larını korur
(`source_trust`, `structured_fact`, vb.) ve `foreign_instance_origin`'i
provenance olarak taşır. L §10 foreign_instance_origin provenance
permanence kuralı korunur.

### Forbidden

- Default subject_class entry'si (her sınıf explicit)
- "Diğer subject_class'lar için fallback" entry
- Matrix scaffolding'in dışında subject — önce B §3'e eklenmeli

---

## 6. Candidate Max Age by Subject Class

### Per-subject conceptual values (production = signed artifact)

```
candidate_max_age_ms.source_trust:               ~long       (insan veya outcome bekleyebilir)
candidate_max_age_ms.adapter_trust:              ~medium     (manifest re-verify)
candidate_max_age_ms.procedural:                 ~medium
candidate_max_age_ms.structured_fact:            ~medium     (cross-source bekler)
candidate_max_age_ms.incident:                   ~short-medium (outcome ile bağlanır)
candidate_max_age_ms.episodic:                   ~short-medium
candidate_max_age_ms.narrative_claim:            ~short      (self-deception riski)
candidate_max_age_ms.causal_explanation:         ~short      (self-deception riski)
candidate_max_age_ms.decision_rationale:         ~short      (self-deception riski)
candidate_max_age_ms.deontic_policy:             ~very_short (human approval bekler)
candidate_max_age_ms.numerics_artifact_reference: ~very_short (§20)
```

### NumericEntry örneği

```
NumericEntry:
    key: memory_write.candidate_max_age_ms.narrative_claim
    value: <production_short>
    unit: ms
    allowed_range: {min: 60_000, max: 86_400_000}    # 1 dk - 24 saat
    directionality: lower_is_stricter
    change_class_if_increased: safety_weakening
    change_class_if_decreased: safety_tightening
    requires_human_approval: true (for increase beyond 6h)
    dependencies:
        - target_key: memory_write.quarantine_max_age_ms.narrative_claim
          relationship: must_be_greater_than_or_equal
          rationale: "narrative_claim için: candidate quarantine'dan uzun
                      yaşamamalı; self-deception riskli class'ta hızlı karar."
    numeric_risk_family: identity_retention
    spec_family: memory_write_gate
    owning_spec_ref: "MEMORY_WRITE_GATE_NUMERICS.md §6"
```

### Kural

> *Candidate sonsuza kadar yaşayamaz.*

### Forbidden

- `candidate_max_age_ms` entry'si olmayan subject_class
- `allowed_range.max = infinity` (sonsuz candidate)

---

## 7. Quarantine Max Age by Subject Class

### Per-subject conceptual values

```
quarantine_max_age_ms.source_trust:              ~long       (insan reviews)
quarantine_max_age_ms.adapter_trust:             ~medium-long
quarantine_max_age_ms.procedural:                ~medium
quarantine_max_age_ms.structured_fact:           ~medium
quarantine_max_age_ms.incident:                  ~medium
quarantine_max_age_ms.episodic:                  ~medium
quarantine_max_age_ms.narrative_claim:           ~short      (self-deception riski)
quarantine_max_age_ms.causal_explanation:        ~short      (self-deception riski)
quarantine_max_age_ms.decision_rationale:        ~short      (self-deception riski)
quarantine_max_age_ms.deontic_policy:            ~short      (review veya reject hızlı)
```

### Subject-spesifik dependency (global invariant YOK)

Bu kritik: `quarantine_max_age` vs `candidate_max_age` arasındaki ilişki **subject_class'a bağlı**.

```
Per-subject dependency declarations:

source_trust:
    quarantine_max_age_ms >= candidate_max_age_ms
    rationale: "Insan/outcome beklenir; quarantine candidate'dan kısa olamaz."

adapter_trust:
    quarantine_max_age_ms >= candidate_max_age_ms
    rationale: "Manifest re-verify quarantine boyunca yapılır."

procedural:
    quarantine_max_age_ms >= candidate_max_age_ms

structured_fact:
    quarantine_max_age_ms >= candidate_max_age_ms

incident / episodic:
    quarantine_max_age_ms >= candidate_max_age_ms

narrative_claim:
    quarantine_max_age_ms <= candidate_max_age_ms
    rationale: "Self-deception riskli class'ta quarantine purgatory'den kaçınılır.
                Kısa quarantine = hızlı reject veya verified karar."

causal_explanation:
    quarantine_max_age_ms <= candidate_max_age_ms
    rationale: aynı (self-deception riski)

decision_rationale:
    quarantine_max_age_ms <= candidate_max_age_ms
    rationale: aynı (self-deception riski)

deontic_policy:
    quarantine_max_age_ms <= candidate_max_age_ms
    rationale: "Active deontic policy belirsiz kalamaz; reject veya verified."
```

### Hiçbir global invariant tüm subject'lere uygulanmaz

Sebep: TTL ilişkisi sınıfın **risk profiline** göre değişir. Insan-bekleyen (`source_trust`) için quarantine uzun mantıklı; self-deception riskli (`narrative_claim`) için quarantine kısa şart.

### Kural

> *Quarantined sonsuza kadar yaşayamaz.*

### Forbidden

- `quarantine_max_age_ms` entry'si olmayan subject_class
- Global "quarantine >= candidate" invariant uygulanan artifact (subject-specific olmalı)
- `allowed_range.max = infinity` (sonsuz quarantine)

---

## 8. Refresh Windows and Epistemic Staleness

### refresh_required_window_ms

Bazı subject_class'lar TTL'e gelmeden **yeniden kanıt** ister. Pencere geçilirse statu otomatik düşmez ama recall'da staleness flag basılır (T'de elaborate).

```
refresh_required_window_ms.source_trust:        ~medium
refresh_required_window_ms.adapter_trust:       ~short    (signed manifest)
refresh_required_window_ms.deontic_policy:      ~short    (human re-attestation)
refresh_required_window_ms.structured_fact:     subject-spesifik
refresh_required_window_ms.narrative_claim:     ~short    (self-deception riski)
refresh_required_window_ms.episodic:            n/a       (geçmiş olay; refresh anlamsız)
```

### Directionality (düzeltilmiş)

```
NumericEntry: memory_write.refresh_required_window_ms.<subject_class>
    directionality: lower_is_stricter
    change_class_if_increased: safety_weakening
    change_class_if_decreased: safety_tightening
    rationale: "Pencere uzarsa kayıt daha uzun süre yeniden kanıt istemeden
                yaşar (gevşeme). Pencere kısalırsa daha sık refresh ister
                (sıkılaşma)."
```

### epistemic_staleness_threshold_ms — canonical source (O bridge)

P, "verified bir kayıt artık epistemik olarak taze sayılır mı?" sorusunun **canonical kaynağıdır**:

```
NumericEntry: memory_write.epistemic_staleness_threshold_ms.<subject_class>
    unit: ms
    directionality: lower_is_stricter
    change_class_if_increased: safety_weakening
    change_class_if_decreased: safety_tightening
```

### O dependency — canonical bağ (artık conceptual değil)

O §15 outcome_alignment.max_wait_ms için bıraktığı conceptual dependency P'de canonical:

```
Cross-artifact dependency (O → P):
    replay_protocol.outcome_alignment.max_wait_ms
        <= memory_write.epistemic_staleness_threshold_ms.<owning_subject_class>
        (computed_less_than_or_equal)
        rationale: "Outcome'un ait olduğu subject_class'ın staleness
                    threshold'unu aşan outcome alignment'a katkı sağlayamaz."
```

T (RECALL_PROTOCOL_NUMERICS) yazıldığında ayrı recall-side numeric'leri (`recall_staleness_dampening_factor`, `recall_cooldown_ms`) ekleyecek ama **P canonical kaynak kalır**.

### Ownership ayrımı

```
P owns:    epistemic_staleness_threshold_ms (kayıt taze mi)
T owns:    recall_staleness_dampening_factor / recall_cooldown_ms
           (kayıt recall'a nasıl döner)
```

### Forbidden

- refresh_required_window_ms `higher_is_stricter` directionality (yanlış)
- O outcome_alignment.max_wait_ms epistemic_staleness_threshold'u aşan artifact
- epistemic_staleness_threshold_ms entry'si olmayan subject_class

---

## 9. Evidence Axis Numeric Matrix

### G-bridge — matrix completeness

```
Artifact validation rule:
    G §8 verification matrix'inde tanımlı her (subject_class, evidence_axis)
    çiftinin P'de karşılığında bir NumericEntry olmalı.
    Eksik kombinasyon → P artifact validation REJECT.
```

### Evidence axis enumeration (G §8'den)

```
evidence_axis:
    observation_count
    causal_link_strength
    cross_source_corroboration_count
    outcome_alignment_score
    replay_survival_score
    external_corroboration_ref_count
    contradiction_level
    operator_signature
    signed_manifest_validity
    execution_audit_score
```

### Matrix entry format

Her (subject_class, axis) çifti:

```
NumericEntry:
    key: memory_write.min_threshold.<subject_class>.<axis>
    unit: ratio | count | band_name
    allowed_range: subject-axis-specific
    directionality: higher_is_stricter (genelde — yüksek eşik = az verified)
    change_class_if_increased: safety_tightening
    change_class_if_decreased: safety_weakening
    requires_human_approval: true (for decrease)
    numeric_risk_family: safety_critical
    spec_family: memory_write_gate
    owning_spec_ref: "MEMORY_WRITE_GATE_NUMERICS.md §9"
```

### Per-subject required axis sets (G §8'den damıtma)

```
source_trust:
    observation_count, cross_source_corroboration_count,
    external_corroboration_ref_count, outcome_alignment_score

adapter_trust:
    signed_manifest_validity, execution_audit_score,
    operator_signature, contradiction_level

procedural:
    observation_count, outcome_alignment_score, replay_survival_score

structured_fact:
    cross_source_corroboration_count, contradiction_level,
    observation_count

incident:
    observation_count, causal_link_strength, outcome_alignment_score

episodic:
    observation_count, causal_link_strength

narrative_claim:
    external_corroboration_ref_count (>=1), contradiction_level

causal_explanation:
    external_corroboration_ref_count (>=1), causal_link_strength

decision_rationale:
    external_corroboration_ref_count (>=1), outcome_alignment_score

deontic_policy:
    operator_signature, contradiction_level (== clear)

numerics_artifact_reference:
    signed_manifest_validity, operator_signature
```

Her satır G §8 verification matrix'ine birebir denk.

### Forbidden

- G matrix'inde tanımlı (subject, axis) çiftine karşılık P entry yok
- Subject_class için "evidence_axis = none" entry'si (verified hiçbir kanıt olmadan yapılamaz)

---

## 10. Evidence Count Minimums

### Definition — bağımsız kaynak sayımı

`evidence_count` = bağımsız kaynak sayısı, ölçüm sayısı değil. Aynı kaynaktan 5 ölçüm = 1 evidence.

```
NumericEntry: memory_write.min_evidence_count.<subject_class>.<axis>
    unit: count
    directionality: higher_is_stricter
    change_class_if_increased: safety_tightening
    change_class_if_decreased: safety_weakening
    rationale: "Independent source count; same-source repeats = 1."
```

### Per-subject conceptual values

```
min_evidence_count.source_trust.cross_source_corroboration:  >= 2
min_evidence_count.structured_fact.cross_source:             >= 2
min_evidence_count.narrative_claim.external_corroboration:   >= 1
min_evidence_count.causal_explanation.external_corroboration: >= 1
min_evidence_count.decision_rationale.external_corroboration: >= 1
min_evidence_count.incident.observation_count:               >= 2
min_evidence_count.procedural.observation_count:             >= 3
```

### Forbidden

- Aynı kaynaktan multiple ölçümleri "independent" sayma
- `min_evidence_count = 0` (kanıtsız verified)

---

## 11. Temporal Separation for Independent Evidence

Aynı session'da art arda 3 gözlem = 1; gerçek "bağımsız gözlem" temporal separation ister. Bu O §14'teki `min_session_separation_ms` mantığının M2 verification karşılığı.

```
NumericEntry: memory_write.min_observation_temporal_separation_ms.<subject_class>
    unit: ms
    directionality: higher_is_stricter
    change_class_if_increased: safety_tightening
    change_class_if_decreased: safety_weakening
    allowed_range: {min: 60_000, max: 86_400_000}
```

### Per-subject conceptual values

```
min_observation_temporal_separation_ms.source_trust:       ~long
min_observation_temporal_separation_ms.procedural:         ~medium
min_observation_temporal_separation_ms.incident:           ~short (event-bound)
min_observation_temporal_separation_ms.episodic:           n/a (single event)
min_observation_temporal_separation_ms.structured_fact:    ~medium
```

### Kural

```
Aynı session'dan gelen multiple observation 1 evidence sayılır.
Independent observation = temporal_separation >= min_observation_temporal_separation_ms.
```

### Forbidden

- Aynı session'daki observation'ları "independent" olarak verified evidence sayma
- `min_observation_temporal_separation_ms = 0` (single-session bias kapısı)

---

## 12. Causal Reference Minimums

### NumericEntry pattern

```
NumericEntry: memory_write.min_causal_refs.<subject_class>
    unit: count
    directionality: higher_is_stricter
    change_class_if_increased: safety_tightening
    change_class_if_decreased: safety_weakening
```

### Per-subject conceptual values

```
min_causal_refs.episodic:                  >= 1 (causal chain bilinmeli)
min_causal_refs.causal_explanation:        >= 1 (definition gereği)
min_causal_refs.incident:                  >= 1
min_causal_refs.decision_rationale:        >= 1
min_causal_refs.procedural:                0 (causal chain zorunlu değil)
min_causal_refs.source_trust:              0
min_causal_refs.structured_fact:           0
```

### Forbidden

- causal_refs zorunlu subject_class için min < 1
- Causal ref olmadan causal_explanation verified

---

## 13. Cross-source Corroboration Thresholds

### NumericEntry pattern

```
NumericEntry: memory_write.min_cross_source_corroboration.<subject_class>
    unit: count (distinct sources)
    directionality: higher_is_stricter
    change_class_if_increased: safety_tightening
    change_class_if_decreased: safety_weakening
```

### Per-subject conceptual values

```
min_cross_source_corroboration.source_trust:        >= 2
min_cross_source_corroboration.structured_fact:     >= 2
min_cross_source_corroboration.incident:            >= 1 (single eyewitness ok)
min_cross_source_corroboration.narrative_claim:     >= 1 (en az external one)
min_cross_source_corroboration.causal_explanation:  >= 1
min_cross_source_corroboration.decision_rationale:  >= 1
min_cross_source_corroboration.procedural:          0 (tek operator yeterli)
```

### Source distinctness

```
Two sources are "distinct" iff:
    source_id_1 != source_id_2
    AND no shared upstream_source_chain
```

Shared upstream chain (aynı veri kaynağının iki port'undan gelen kayıtlar) = 1 source. Bu L §10 self-corroboration koruması.

### Forbidden

- Aynı upstream'den gelen iki source'u "distinct" sayma
- Cross-source zorunlu subject için < 1 verified

---

## 14. Contradiction Bands and Verified Stickiness

### Contradiction band'leri (N reuse — deterministic soft-overlap)

```
contradiction_band:
    clear     [0.00, 0.10]
    mild      [0.10, 0.30]
    moderate  [0.30, 0.50]
    high      [0.50, 0.75]
    critical  [0.75, 1.00]
```

Her cutoff ayrı NumericEntry (M no-default). Membership function type = linear (N'den miras).

### Asymmetric thresholds — verified stickiness

Bu P'nin en güçlü disiplinlerinden biri. **Verified status sticky'dir**: tek yeni karşı kanıtla devrilmez.

```
NumericEntry: memory_write.contradiction_band_max_for_new_verified.<subject_class>
    unit: band_name
    directionality: lower_is_stricter
    change_class_if_increased: safety_weakening
    
NumericEntry: memory_write.contradiction_band_required_to_demote_verified.<subject_class>
    unit: band_name
    directionality: higher_is_stricter
    change_class_if_increased: safety_tightening
    
Invariant (per subject):
    contradiction_band_required_to_demote_verified
    >
    contradiction_band_max_for_new_verified
    
    rationale: "Verified status sticky'dir. Promote için yüksek bar; demote
                için DAHA yüksek bar. DEONTIC §18 (kolay tighten, zor weaken)
                epistemic karşılığı."
```

### Per-subject conceptual values

```
structured_fact:
    promote_max:       mild
    demote_required:   high
    
source_trust:
    promote_max:       moderate
    demote_required:   high
    
narrative_claim:
    promote_max:       clear
    demote_required:   moderate
    AND external_corroboration_refs > 0
    
deontic_policy:
    promote_max:       clear
    demote_required:   mild
    interpretation:    "mild or higher contradiction demotes / blocks
                        activation; canonical band 'mild' = clear violated
                        for deontic policies (DEONTIC §18 emergency_revert
                        epistemic counterpart)"

causal_explanation:
    promote_max:       clear
    demote_required:   moderate

decision_rationale:
    promote_max:       clear
    demote_required:   moderate

procedural:
    promote_max:       mild
    demote_required:   high

incident:
    promote_max:       mild
    demote_required:   high

episodic:
    promote_max:       mild
    demote_required:   high
```

### Kilit cümle

> **Verified status sticky'dir.**
> **Tek yeni karşı kanıtla devrilmez.**

Finansal hafıza için özellikle kritik: sistem bir kaydı verified yaptıysa, onu düşürmek için daha güçlü karşı kanıt gerekir. Aksi halde verified rejimi her gürültüde dalgalanır.

### Forbidden

- `demote_required <= promote_max` taşıyan artifact (sticky invariant ihlali)
- `high contradiction + verified` status'lu record (validation reject)
- contradiction band cutoff'u olmadan verified karar

---

## 15. Duplicate Detection and Supersede Thresholds

### duplicate_match_threshold

```
NumericEntry: memory_write.duplicate_match_threshold.<subject_class>
    unit: ratio
    directionality: higher_is_stricter
    change_class_if_increased: safety_tightening
                              # different things stay different (false-merge yok)
    change_class_if_decreased: safety_weakening
                              # daha çok merge (false-merge riski)
```

Asymmetric tehlike: **false-merge daha kötü** (information loss); false-split daha az tehlikeli (audit görür). Default sıkı tarafta.

### supersede_confidence_delta_min

Tek yeni gözlem verified rekoru deviremez. Asymmetric — verified stickiness'in supersede tarafı:

```
NumericEntry: memory_write.supersede_confidence_delta_min.<subject_class>
    unit: ratio (evidence_score delta)
    directionality: higher_is_stricter
    change_class_if_increased: safety_tightening
    allowed_range: {min: 0.10, max: 0.50}    # min > 0 zorunlu
    
Rule (verified supersede):
    new_record.evidence_score
        >= existing_verified_record.evidence_score + supersede_confidence_delta_min
```

`min > 0` zorunlu (allowed_range.min strict positive). Sıfır delta = tek yeni gözlemle supersede = sticky kuralının ihlali.

### Retroactive verified geçiş yasağı

```
G §10 hard invariant:
    Verified geçiş retroaktif değildir.
    verified_at öncesi recall'lar eski statüyle kalır.
```

P bunu NumericEntry olarak taşımaz; **declarative kural** olarak referans verir.

### Forbidden

- `supersede_confidence_delta_min = 0` (sticky ihlali)
- `duplicate_match_threshold` entry'si olmayan subject_class
- Retroactive verified geçiş (verified_at öncesi recall'lar promote edilemez)

---

## 16. Self-deception Risk Numerics

### L bridge — internal_only vs external_corroboration

L §10 `internal_only_refs` / `external_corroboration_refs` ayrımı P'de numerics'leşir:

```
internal_only_ref_ratio.<record>
    = internal_only_refs_count / total_refs_count
    
NumericEntry: memory_write.max_internal_only_ref_ratio.<subject_class>
    unit: ratio
    directionality: lower_is_stricter
    change_class_if_increased: safety_weakening
    change_class_if_decreased: safety_tightening
```

### Per-subject conceptual values

```
max_internal_only_ref_ratio.narrative_claim:        ~0.30
max_internal_only_ref_ratio.causal_explanation:     ~0.30
max_internal_only_ref_ratio.decision_rationale:     ~0.20    # en sıkı
max_internal_only_ref_ratio.structured_fact:        ~0.50    # daha gevşek
max_internal_only_ref_ratio.episodic:               ~0.40
max_internal_only_ref_ratio.source_trust:           ~0.30
max_internal_only_ref_ratio.incident:               ~0.40
max_internal_only_ref_ratio.procedural:             ~0.50
```

### external_corroboration_min_count per subject

```
external_corroboration_min_count.narrative_claim:        >= 1
external_corroboration_min_count.causal_explanation:     >= 1
external_corroboration_min_count.decision_rationale:     >= 1 (+ outcome_alignment)
external_corroboration_min_count.source_trust:           >= 1 (cross-source)
external_corroboration_min_count.structured_fact:        >= 1 (cross-source)
external_corroboration_min_count.deontic_policy:         >= 1 (operator signature)
```

### Temporal separation between internal/external refs

```
NumericEntry: memory_write.internal_external_ref_min_temporal_separation_ms.<subject_class>
    unit: ms
    directionality: higher_is_stricter
    rationale: "Internal ref ile external ref AYNI session'da üretilmesin
                (single-session self-confirmation koruması). O §14
                min_session_separation_ms'in M2 verification analogu."
```

### Kilit cümleler (P omurgası)

> **Self-explanation is not proof.**
> **Internal-only refs cannot satisfy verification alone.**
> **Sistem kendi açıklamasını üretebilir; ama kendi açıklamasını kanıt sayamaz.**

### Forbidden

- Tüm referansları internal_only olan narrative/causal/rationale verified
- Aynı session'da üretilen "external" + "internal" ref ile verification
- `external_corroboration_min_count = 0` self-deception-prone subject_class'lar için

---

## 17. Replay Survival vs Outcome Alignment Weights

### O bridge — per subject dağılımı

O global invariant'ı (max_replay_survival_weight_in_verification < outcome_alignment_weight_in_verification) P per-subject seviyesine indirir.

```
NumericEntry: memory_write.replay_survival_weight.<subject_class>
NumericEntry: memory_write.outcome_alignment_weight.<subject_class>

Per-subject dependency:
    replay_survival_weight.<sc> < outcome_alignment_weight.<sc>
    
Global bridge dependency (P → O):
    max over all subject_class (replay_survival_weight.<sc>)
        <= replay_protocol.max_replay_survival_weight_in_verification
        (computed_less_than_or_equal)
    
    rationale: "P herhangi bir subject için O'nun global cap'ini aşamaz.
                O artifact'i P'nin cap'idir. (N → O bridge ile aynı pattern)"
```

### Kilit cümle

> **O, replay evidence'ın global tavanıdır.**
> **P, subject_class bazlı dağılımıdır.**

### Subject-spesifik replay disable (constitutional immutable)

Bazı subject_class'lar **replay survival evidence almaz**. Bunlar `{min: 0, max: 0}` allowed_range ile constitutional immutable (O §19 chain_depth = 0 pattern'i):

```
replay_survival_weight.deontic_policy:
    value: 0
    allowed_range: {min: 0, max: 0}
    directionality: neutral
    change_class_if_increased: forbidden
    rationale: "Deontic policy verified ancak human approval ile;
                replay yetersiz."

replay_survival_weight.incident:
    value: 0
    allowed_range: {min: 0, max: 0}
    rationale: "Incident verified gerçek outcome gerektirir;
                sentetik test yetmez."

replay_survival_weight.adapter_trust:
    value: 0
    allowed_range: {min: 0, max: 0}
    rationale: "Adapter trust signed manifest + execution audit gerektirir;
                replay survival uygulanmaz."

replay_survival_weight.numerics_artifact_reference:
    value: 0
    allowed_range: {min: 0, max: 0}
    rationale: "Numerics artifact verified human signature + validation
                gerektirir; replay yetersiz."
```

### Per-subject conceptual values (replay almayanlar hariç)

```
replay_survival_weight.procedural:              ~0.25
outcome_alignment_weight.procedural:            ~0.60

replay_survival_weight.source_trust:            ~0.20
outcome_alignment_weight.source_trust:          ~0.50

replay_survival_weight.structured_fact:         ~0.15
outcome_alignment_weight.structured_fact:       ~0.40

replay_survival_weight.episodic:                ~0.10
outcome_alignment_weight.episodic:              ~0.30

replay_survival_weight.narrative_claim:         ~0.05
outcome_alignment_weight.narrative_claim:       ~0.30
```

### Forbidden

- `replay_survival_weight >= outcome_alignment_weight` per subject
- `max(replay_survival_weight.*) > O global cap`
- `replay_survival_weight > 0` constitutional-immutable subject için

---

## 18. Human-write Verification Numerics

### auto_verified_human_subject_classes — whitelist enum_set

```
NumericEntry:
    key: memory_write.auto_verified_human_subject_classes
    unit: enum_set
    value: [bootstrap_reference,
            signed_administrative_reference,
            operator_decision_record,
            deontic_kill_switch_action_record]
    allowed_range: subset_of_subject_class_enum
    directionality: lower_is_stricter
    change_class_if_increased: safety_weakening    # whitelist genişlemesi
    change_class_if_decreased: safety_tightening   # whitelist daralması
    requires_human_approval: true (for any change)
    numeric_risk_family: safety_critical
    spec_family: memory_write_gate
    owning_spec_ref: "MEMORY_WRITE_GATE_NUMERICS.md §18"
```

### matrix_required_human_subject_classes — complement set

```
auto_verified ∪ matrix_required = subject_class_universe
Tüm subject_class ya whitelist'te ya matrix-required.
```

### operator_identity_confidence_min

```
NumericEntry: memory_write.operator_identity_confidence_min.<scope>
    unit: ratio (or band_name: low / medium / high / very_high)
    directionality: higher_is_stricter
```

Per-scope conceptual:

```
operator_identity_confidence_min.administrative_writes:    ~high
operator_identity_confidence_min.deontic_actions:          ~very_high
operator_identity_confidence_min.bootstrap_writes:         ~very_high
operator_identity_confidence_min.numerics_artifact_signing: ~very_high
```

### world_claim ayrımı — hard invariant (numeric değil)

```
G §6 fact_subject vs operator_subject:
    Human-write administrative_scope_only;
    world claim olarak auto-verified olamaz.

Auto-verified human writes:
    operator_decision_record       = operator karar verdi (administrative)
    bootstrap_reference            = bootstrap konfigürasyon (administrative)
    signed_administrative_ref      = administrative attestation
    deontic_kill_switch_action     = operatör action audit

NOT auto-verified:
    "Halit dedi ki BTC %10 düşecek" (world claim) → matrix-required structured_fact
```

### Kilit cümle

> **Halit yazdı = Halit'in beyanı kayda geçti.**
> **Halit yazdı ≠ dünya iddiası otomatik doğru.**

### Forbidden

- Whitelist'e world_claim üretebilen subject_class ekleme
- `operator_identity_confidence_min < threshold` ile auto-verified yazma
- Human-write'ı doğrudan structured_fact verified yapma (matrix bypass)

---

## 19. Status Transition Thresholds

### Geçiş matrisi

```
candidate → verified         §9-17 (evidence + contradiction + self-deception caps)
candidate → quarantined      contradiction high veya self-deception risk
candidate → expired          candidate_max_age aşıldı (§6)
candidate → rejected         clear disprove (contradiction critical veya invalid)

quarantined → verified       review + new evidence (matrix)
quarantined → rejected       review reject
quarantined → expired        quarantine_max_age aşıldı (§7)

verified → superseded        new record + supersede_confidence_delta_min (§15)
verified → demoted           contradiction_band_required_to_demote_verified (§14)
verified → expired           epistemic_staleness_threshold + refresh failed (§8)

active → superseded          deontic policy yeniden yazıldı + matrix
```

### Asymmetric thresholds (verified stickiness)

Promote zor; demote daha zor. §14 contradiction asimetrisi + §15 supersede asimetrisi + §16 self-deception eşikleri birlikte:

```
promote_to_verified_requires:
    evidence_axes_min ALL satisfied
    AND contradiction <= promote_max
    AND internal_only_ratio <= max
    AND external_corroboration_min satisfied

demote_from_verified_requires:
    contradiction >= demote_required (> promote_max)
    OR clear disprove evidence
    OR refresh failed beyond grace_window
```

### Forbidden

- Symmetric promote/demote eşikleri (sticky ihlali)
- `verified → expired` geçişi epistemic_staleness_threshold olmadan
- Retroactive supersede

---

## 20. numerics_artifact_reference Special TTLs

`numerics_artifact_reference` subject_class kendi candidate aşamasında uzun süre takılmamalı. Sebep: missing/invalid numerics → fail-safe strict mode (M §11) → operational risk.

```
candidate_max_age_ms.numerics_artifact_reference:    ~very_short
    # numerics artifact register edildikten sonra hızlıca verified veya rejected
    # bekleme = sistem strict mode'da kalır (operational risk)

quarantine_max_age_ms.numerics_artifact_reference:   ~very_short

epistemic_staleness_threshold_ms.numerics_artifact_reference: ~medium
    # active numerics artifact gözden geçirme periyodu

operator_identity_confidence_min.numerics_artifact_signing: ~very_high

replay_survival_weight.numerics_artifact_reference:  0 (constitutional immutable, §17)
```

### Critical dependency

```
candidate_max_age_ms.numerics_artifact_reference
    < candidate_max_age_ms.<any other subject_class>
    (computed_less_than_or_equal — strict <)
    rationale: "Numerics belirsiz kalamaz; sistem strict mode'dan hızla
                çıkmalı veya rejection net olmalı."
```

### Forbidden

- numerics_artifact_reference candidate TTL'i diğer subject'lerden uzun
- Numerics signing düşük operator_identity_confidence ile
- Numerics artifact için replay survival weight > 0

---

## 21. Missing-Numerics Failsafe

M §11 fail-safe strict mode P'ye uygulanır.

### Strict mode behavior

```
Missing memory_write numerics artifact veya invalid load:
    → verified status üretimi DISABLED
    → only candidate / quarantined / rejected / expired status'leri çalışır
    → existing verified records remain readable, but no new verified
      promotion / supersede / active transition is allowed
    → yeni promotion'lar bekletilir (artifact valid olana dek)
    → NUMERICS_FAILSAFE_ACTIVATED event tetiklenir
    → Manual intervention until valid numerics artifact loaded
```

### Audit-safe mode tanımı

```
Audit-safe Memory Write Gate:
    ✅ Mevcut verified kayıtların read access (recall normal çalışır)
    ✅ Yeni candidate yazma (matrix-skipped, status=candidate kalır)
    ✅ Quarantined review (rejected/expired transitions)
    ❌ Candidate → verified promotion
    ❌ Verified status update
    ❌ Supersede / active transitions
```

Sistem "P yoksa" durumunda **daha serbest değil, daha kısıtlı** çalışır (M kuralı).

### NumericEntry

```
NumericEntry: memory_write.failsafe_mode
    value: strict_no_verified
    unit: enum
    allowed_range: {strict_no_verified, strict_full_disable}
    directionality: bidirectional_sensitive
    change_class_if_increased: safety_weakening
    change_class_if_decreased: safety_tightening
```

### Forbidden

- Missing numerics → fail-open (normal verified production)
- Audit-safe mode'da candidate → verified geçiş

---

## 22. Dependency Declarations

P'nin cross-artifact ve internal dependency'lerinin özet matrisi.

### Internal (P içinde, per subject_class)

```
quarantine_max_age_ms vs candidate_max_age_ms       subject-specific (§7)
contradiction_band_required_to_demote_verified
    > contradiction_band_max_for_new_verified       per subject (§14)
supersede_confidence_delta_min > 0                  per subject (§15)
replay_survival_weight < outcome_alignment_weight   per subject (§17)
auto_verified ∪ matrix_required = subject_universe  (§18)
candidate_max_age_ms.numerics_artifact_reference
    < candidate_max_age_ms.<any other subject>      (§20)
```

### Cross-artifact

```
P → O bridge:
    max over P (replay_survival_weight.<sc>)
        <= O.max_replay_survival_weight_in_verification
        (computed_less_than_or_equal)

O → P bridge (O §15 canonical bağ):
    O.outcome_alignment.max_wait_ms
        <= P.epistemic_staleness_threshold_ms.<owning_subject_class>
        (computed_less_than_or_equal)

G → P bridge (matrix completeness):
    Every (subject_class, evidence_axis) in G §8 verification matrix
        → must have a NumericEntry in P
    (artifact validation rule, not single NumericEntry dependency)

L → P bridge (self-deception):
    L §10 internal_only_refs / external_corroboration_refs distinction
        → P §16 max_internal_only_ref_ratio + external_corroboration_min_count

B → P bridge:
    B §3 subject_class enumeration
        → P §5 matrix scaffolding (every subject has a row)
```

### Atomic update rule (M §12)

Bağımlı numerics atomic artifact içinde değişir. Tek key değişikliği bağımlı key'leri eski bırakırsa artifact REJECT.

### Forbidden

- Dependency declarationsız P numeric ekleme
- Partial update (bir key değişip bağımlı key'in eski kalması)
- Dependency violation tolere edilmesi

---

## 23. Audit Events and M2 Reference

P **yeni canonical event tanımlamaz**. M zaten numerics lifecycle event'lerini, G zaten gate lifecycle event'lerini tanımladı; P onları reuse eder.

### Reused events

```
NUMERICS_ARTIFACT_STATUS_CHANGED        (M §6)
    when: memory_write_gate artifact register/deprecate/rollback
    payload: spec_family=memory_write_gate, version, old_status, new_status

NUMERICS_VERSION_MISMATCH_DETECTED      (F §19, ledger_meta)
NUMERICS_FAILSAFE_ACTIVATED             (F §19, ledger_meta)

MEMORY_RECORD_STATUS_CHANGED            (G §15)
    Subject-class spesifik status geçişleri
    Reasons (P'den gelen):
        verified_promotion_threshold_met
        verified_promotion_threshold_failed
        contradiction_band_exceeded
        self_deception_risk_triggered
        candidate_max_age_expired
        quarantine_max_age_expired
        supersede_confidence_delta_met
        verified_demote_threshold_met
        refresh_window_expired
        replay_survival_weight_exceeded_cap   (P → O violation)
        epistemic_staleness_exceeded
```

### F event type discipline

P numerics ihlalleri **yeni event tipi üretmez**; reason field ile canonical event kullanılır:

```
Artifact-level violation:
    MEMORY_RECORD_STATUS_CHANGED(target=artifact, new_status=rejected,
                                 reason=numerics_validation_failed)

Per-record violation:
    MEMORY_RECORD_STATUS_CHANGED(record_id=..., new_status=quarantined,
                                 reason=<specific reason from list above>)
```

### M2 reference

```
numerics_artifact_reference (MEMORY_CONTRACT §3 subject_class)
    spec_family: memory_write_gate
    artifact_version: v0.1
    status: active | deprecated | rollback_pending
    signed_hash: <external artifact hash>
    last_status_change_ref: <NUMERICS_ARTIFACT_STATUS_CHANGED event_id>
```

---

## 24. Cross-document Anchors

```
| Belge                            | Bağlantı                                          |
|----------------------------------|---------------------------------------------------|
| NUMERICS_GOVERNANCE.md (M)       | tüm meta-kurallar; enum_set convention burada     |
| MEMORY_WRITE_GATE.md (G)         | mekanizma; P onun numerics artifact'i             |
| MEMORY_CONTRACT.md (B)           | subject_class enumeration + provenance + staleness|
| REPLAY_PROTOCOL_NUMERICS.md (O)  | replay survival weight cap (global) + outcome wait|
| BACKUP_STRATEGY.md (L)           | internal_only / external_corroboration self-decep|
| INGRESS_COMPILER_NUMERICS.md (N) | soft-overlap membership reuse (contradiction bands)|
| OBSERVER_LEDGER_SCHEMA.md (F)    | canonical event reuse, reason field discipline    |
| RECALL_PROTOCOL.md (H)           | recall-side staleness, T'de elaborate            |
| CONSTITUTION.md (A)              | Madde 6 (LLM numeric değiştiremez) + Madde 7      |
```

---

## 25. Violation Tests

P artifact'ı validation sırasında **REJECT** edilmesi gereken durumlar:

1. **Çıplak sayı.** NumericEntry metadata olmadan P numerics içeren artifact.
2. **G matrix completeness ihlali.** G §8'de tanımlı (subject_class, evidence_axis) çifti için P entry yok.
3. **candidate_max_age_ms entry'si olmayan subject_class.** §6 ihlali.
4. **quarantine_max_age_ms entry'si olmayan subject_class.** §7 ihlali.
5. **Global "quarantine >= candidate" invariant uygulanmış artifact.** Subject-spesifik olmalı (§7).
6. **`refresh_required_window_ms` directionality `higher_is_stricter`.** §8 ihlali (gevşeme yönü ters yazılmış).
7. **O dependency ihlali:** `outcome_alignment.max_wait_ms > epistemic_staleness_threshold_ms.<sc>`. §8 ihlali.
8. **`min_evidence_count = 0` verified-üreten subject.** §10 ihlali.
9. **Aynı session observation'ları "independent" sayılmış.** §11 temporal separation ihlali.
10. **Causal-zorunlu subject (causal_explanation/episodic/incident/decision_rationale) için `min_causal_refs = 0`.** §12 ihlali.
11. **Cross-source-zorunlu subject için `min_cross_source_corroboration = 0`.** §13 ihlali.
12. **Aynı upstream'den iki source "distinct" sayılmış.** §13 ihlali.
13. **`demote_required <= promote_max`.** §14 verified stickiness ihlali.
14. **`high contradiction + verified`.** §14 ihlali (validation reject).
15. **`supersede_confidence_delta_min = 0`.** §15 ihlali.
16. **`max_internal_only_ref_ratio = 1.0`.** §16 self-deception koruması ihlali.
17. **Self-deception-prone subject (narrative_claim/causal_explanation/decision_rationale) için `external_corroboration_min_count = 0`.** §16 ihlali.
18. **Aynı session'da üretilen internal + external ref ile verification.** §16 temporal separation ihlali.
19. **`replay_survival_weight >= outcome_alignment_weight` per subject.** §17 ihlali.
20. **`max(replay_survival_weight.*) > O.max_replay_survival_weight_in_verification`.** P → O bridge ihlali.
21. **Constitutional-immutable subject (deontic_policy/incident/adapter_trust/numerics_artifact_reference) için `replay_survival_weight > 0`.** §17 ihlali.
22. **`auto_verified ∪ matrix_required ≠ subject_class_universe`.** §18 ihlali.
23. **Whitelist'e world_claim üretebilen subject_class eklenmiş.** §18 ihlali.
24. **Numerics_artifact_reference candidate TTL'i diğer subject'lerden uzun.** §20 ihlali.
25. **Missing numerics → fail-open (normal verified production).** §21 fail-safe ihlali.
26. **Audit-safe mode'da candidate → verified geçiş.** §21 ihlali.
27. **Retroactive verified geçiş.** G §10 ihlali.
28. **LLM tarafından üretilen veya değiştirilen P numeric.** Madde 6 ihlali.
29. **Dependency declarationsız P numeric.** §22 ihlali.
30. **Foreign provenance native provenance'a dönüştürülmüş kayıt verified.** B §10 / L ihlali.
31. **`foreign_instance_origin` subject_class gibi numeric matrix row aldı.** §5 ihlali (provenance metadata, subject_class değil).
32. **deontic_policy demote_required non-canonical band değeri (`clear_violated` gibi).** §14 ihlali (canonical set: clear/mild/moderate/high/critical).

**Artifact-level violations** (1-30, validation aşaması):
`MEMORY_RECORD_STATUS_CHANGED(target=artifact, new_status=rejected, reason=numerics_validation_failed)`.

**Per-record violations** (runtime, artifact valid ama record P caps'leri aştı):
`MEMORY_RECORD_STATUS_CHANGED(record_id=..., new_status=quarantined|rejected|expired, reason=<specific>)`.

F event type discipline: yeni canonical event yok, sadece reason field.

---

## 26. Open Questions

P kapanırken cevaplanmamış bırakılan sorular:

- **Recall-side staleness numerics** → T (RECALL_PROTOCOL_NUMERICS): `recall_staleness_dampening_factor`, `recall_cooldown_ms`. P canonical kaynak olarak `epistemic_staleness_threshold_ms` verir; T recall-side davranışı ekler.
- **Trust decay function shape** → adapter_trust ve source_trust için decay matematiği (linear vs exponential vs step) implementation. Refresh window numeric, decay function değil.
- **deontic_policy verified eşikleri için human approval signature schema** → DEONTIC_GATE_NUMERICS veya implementation
- **Foreign provenance recovery path** → L §17 ile koordine, P §22 cross-artifact dependency
- **numerics_artifact_reference için multi-signature requirement** → M §13 (NUMERICS_GOVERNANCE open question'ı buraya da bağlı)
- **Drift detection threshold** (band cutoff'larının "yeterince değişti" sayılma eşiği) → Implementation
- **Subject_class taksonomisinin genişlemesi** → B §3 spec revision; P matrix scaffolding otomatik genişler

Bu sorular cevaplanmadan implementation aşamasına geçilmez.

---

## Çekirdek özet — 16 karar + 32 violation tests

### 16 karar

1. P runtime config değildir; signed artifact + M2 reference.
2. P, Memory Write Gate'in sayısal epistemik frenidir.
3. Her subject_class için ayrı TTL / evidence / contradiction / staleness eşiği vardır.
4. G matrix row'u olan her (subject, axis) çifti P'de NumericEntry'e karşılık gelir (G-bridge).
5. Numeric threshold olmayan (subject, axis) çifti verified üretmez.
6. Candidate sonsuza kadar yaşayamaz; quarantined sonsuza kadar yaşayamaz.
7. TTL ilişkisi subject-spesifik; global "quarantine >= candidate" invariant YOK.
8. `refresh_required_window_ms` lower_is_stricter (uzun pencere = gevşeme).
9. Contradiction band'leri asymmetric: demote_required > promote_max (verified stickiness).
10. `supersede_confidence_delta_min > 0` zorunlu (tek gözlem verified rekoru devirmez).
11. Self-explanation is not proof; internal-only refs verified için tek başına yetmez.
12. `max(replay_survival_weight.*) <= O global cap` (P → O bridge); per subject < outcome_alignment.
13. Constitutional-immutable subject'ler (deontic_policy, incident, adapter_trust, numerics_artifact_reference) için `replay_survival_weight = 0` allowed_range {min:0, max:0}.
14. Human write otomatik dünya hakikati değildir; auto_verified ∪ matrix_required = universe.
15. `numerics_artifact_reference` candidate TTL en kısa olmalı; verified human signature gerek.
16. Missing numerics → strict_no_verified mode (verified üretimi DISABLED, audit-safe).

### 32 violation tests

§25'te listelendi.

### enum_set convention

```
For enum_set NumericEntry (P §4):
    increase = set expansion
    decrease = set contraction
    directionality: lower_is_stricter (genelde — whitelist genişlemesi safety_weakening)
```

### Damıtma — son cümleler

> **Memory Write Gate numerics, hafızaya gerçekmiş gibi yazma hakkının sayısal sözleşmesidir.**
>
> **Sistem kendi açıklamasını üretebilir. Ama kendi açıklamasını kanıt sayamaz.**
>
> **Self-explanation is not proof. Internal-only refs cannot satisfy verification alone.**
>
> **Halit yazdı = Halit'in beyanı kayda geçti. Halit yazdı ≠ dünya iddiası otomatik doğru.**
>
> **Verified status sticky'dir. Tek yeni karşı kanıtla devrilmez.**
>
> **O, replay evidence'ın global tavanıdır. P, subject_class bazlı dağılımıdır.**
>
> **Numerics yoksa Memory Write Gate daha serbest değil; verified üretimi tamamen kapalı.**
>
> **N dış dünyanın hakkını sınırlar. O kendi geçmişine girme hakkını sınırlar. P hafızaya emin olma hakkını sınırlar.**
