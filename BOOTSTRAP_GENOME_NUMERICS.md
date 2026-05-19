# BOOTSTRAP_GENOME_NUMERICS.md

## Sentinel — Bootstrap Genome Numeric Sözleşmesi

---

## Status

**Frozen Draft v0.1**
**Conceptual phase. No implementation authority.**

Bu belge `BOOTSTRAP_GENOME.md`'nin (D) numerics artifact'idir. `NUMERICS_GOVERNANCE.md`'nin (M) tüm meta-kurallarına uyar. Çalışan bir Sentinel embriyosunun kesin sayısal değerlerini vermez — **conceptual band ranges, doğum invariants ve dependency rules** verir; production değerleri ayrı **signed numerics artifact** (örn. `bootstrap_genome_numerics_v1.signed.json`).

`spec_family: bootstrap_genome`.

---

## 1. Purpose

D (BOOTSTRAP_GENOME) SELF_GENESIS sözleşmesini yazdı: doğum ritüeli, payload_modulation_reflex priors, self-field embryo, proto-resonance fields, no stable assembly at birth, plasticity state-based not age-based, M2 t=0 only bootstrap_reference, birth_mode taksonomisi. Ama gerçek **numerical eşik** yoktu:

- Her primer payload için seed neuron count band ne?
- Initial synaptic weight bandları ne kadar zayıf olmalı?
- Receptor homonymous bias epsilon ne?
- Self-field weight'lerin dependency'si nasıl korunur?
- Plasticity phase transition için hangi metrikler hangi eşikleri tatmin etmeli?
- Phase monotonicity nasıl numeric olarak korunur?

S bu sayısal sınırları verir.

### Damıtma

> **Bootstrap genome numerics runtime config değildir.**
> **S = doğum dokusunun sayısal sözleşmesidir.**
>
> **S bilgi vermez. S öğrenebilirlik ölçüsü verir.**
>
> **Sentinel ölü doğmamalı. Ama fikirle, kişilikle veya dünya bilgisiyle de doğmamalı.**

Tek cümle: **S = doğum dokusunun sayısal sözleşmesidir.**

### Ana gerilim

```
Çok düşük değerler:
    inert / ölü doku
    Sentinel açılır ama duyusal/motor potansiyel aktive olamaz

Çok yüksek değerler:
    hardcoded kişilik / önceden öğrenmiş gibi doğum
    Sentinel doğmadan kararlı assembly veya "bilgi" taşır

Doğru bölge:
    proto-resonance var (renkli doku, refleks priors)
    stable assembly yok (fikir yok)
    öğrenebilir embriyo (her şey deneyim ile farklılaşabilir)
```

### Üç ayrım — yapılması gereken sayısal disiplin

```
1. Seed eşitliği = doku eşitliği
   Self-field asimetrisi = mimari asimetri
   İkisi karıştırılamaz.

2. Proto-resonance ≠ stable assembly
   Multi-layer invariant ile assembly'ye dönüşüm engellenir.

3. Phase transition state-based, monotonic
   Geri dönüş constitutional disruption gerektirir.
```

---

## 2. Governance Position — NUMERICS_GOVERNANCE + BOOTSTRAP_GENOME + bridges

Bu belge:
- **NUMERICS_GOVERNANCE.md** (M) meta-spec'ine **zorunlu uyar**: NumericEntry no-default, directionality, dependencies (computed_* dahil), signed artifact + M2 reference, Memory Write Gate üzerinden update, fail-safe strict mode, rollback only to previous verified
- **BOOTSTRAP_GENOME.md** (D) §4 SELF_GENESIS / §8 self-field / §15 M0 alt-türler / §16 plasticity / §17-19 sleep-replay / §23 constitutional shift'in sayısal tarafı
- **REPLAY_PROTOCOL_NUMERICS.md** (O) bridge: S initial replay rhythm priors verir; O operational caps verir; S O cap'lerini bypass edemez
- **BACKUP_STRATEGY_NUMERICS.md** (R) bridge: restore_with_missing_history / migration_birth durumlarında phase reset koşulları (R §13, §15)
- **MEMORY_CONTRACT.md** (B) M0 bootstrap layer + M2 t=0 bootstrap_reference disiplini
- **OBSERVER_LEDGER_NUMERICS.md** (Q) bridge: SELF_GENESIS event'i permanent_with_snapshot + human_alert (F §10)
- **CONSTITUTION.md** (A) Madde 1 (doğum eşitliği) + Madde 3 (genom anayasal layer) + Madde 6 (LLM bootstrap'i değiştiremez)

### Numerics family classification

```
spec_family:           bootstrap_genome
numeric_risk_family:   primarily safety_critical + identity_retention + calibration_bands
```

Numeric risk çoğunluğu **safety_critical**: seed equality invariants, proto-resonance multi-layer protection, stable_assembly_at_birth = 0, phase monotonicity, age-based transition forbidden. Ailenin bir kısmı **identity_retention**: SELF_GENESIS hash anchors, genesis_random_seed_hash, initial M0 snapshot integrity. **Calibration_bands**: initial synaptic weight bandları, receptor bias epsilon, proto-resonance stability cap.

### owning_spec_ref

```
BOOTSTRAP_GENOME.md@v0.1
```

---

## 3. Core Principle

### Doğum dokusu: ne ölü, ne hazır kişilik

S'nin hedefi tek bir disiplin: **embriyo öğrenebilir; ama henüz öğrenmemiş olmalı**. Sayısal disiplin bunu üç katmanda korur:

```
1. Doku seviyesi:
   seed neuron count tüm primer payload'larda eşit
   initial synaptic weight pre-learned path yaratamayacak kadar zayıf
   receptor bias specialist neuron yaratamayacak kadar küçük

2. Self-field seviyesi:
   homeostatic > predictive > narrative dependency
   narrative doğumda genesis trace, kişilik değil

3. Pattern seviyesi:
   proto-resonance var (refleks priors, weak attraction fields)
   stable assembly yok (kalıcı fikir yapısı yok)
   recallability = 0; assembly_id = none; memory_write_eligibility = false
```

### Üç ana asimetri (S'ye özgü)

```
1. Eşitlik vs asimetri katmanları
   Doku eşitliği (seed count) + Mimari asimetri (self-field weights)
   İkisi farklı boyut; biri diğerinin ayrıcalığını taşımaz

2. Proto-resonance vs assembly
   Çok katmanlı invariant (5 farklı koruma)
   Tek koruma noktası = tek saldırı vektörü; multi-layer zorunlu

3. State-based vs age-based plasticity
   6 metrikli AND koşulu (count + variance + spike rate + recovery)
   + Phase monotonicity (boot → stabilization → consolidated)
   + Age-based transition forbidden (constitutional)
```

### Kilit cümleler

> **S bilgi vermez. S öğrenebilirlik ölçüsü verir.**
>
> **Seed eşitliği = doku eşitliği. Self-field asimetrisi = mimari asimetri. İkisi karıştırılamaz.**
>
> **Proto-resonance assembly doğurabilecek eğilimdir. Assembly değildir.**
>
> **Tek koruma noktası = tek saldırı vektörü.**
>
> **Sentinel has no biological age. Plasticity phase is state/consolidation-based.**
>
> **Phase monotonic. Geri dönüş constitutional disruption gerektirir.**

---

## 4. Numeric Artifact Metadata

### Artifact identity

```
artifact_type:         numerics_artifact
spec_family:           bootstrap_genome
owning_spec_ref:       BOOTSTRAP_GENOME.md@v0.1
numerics_version:      v0.1
signed:                external (per NUMERICS_GOVERNANCE §3)
m2_reference:          numerics_artifact_reference (per MEMORY_CONTRACT §3)
status_event:          NUMERICS_ARTIFACT_STATUS_CHANGED
```

### NumericEntry metadata (M §6 no-default)

P §4'te tanıtılan `enum_set` ve `band_name` unit tipleri + M §8 enum_set
convention S'de de geçerli. R'de netleşen constitutional immutable
canonical form (her iki yön ayrı `forbidden`) S'de yoğun kullanılır.

### S'ye özgü disiplin — constitutional immutable canonical form

Pek çok S key'i `{tek değer}` allowed_range ile immutable. M canonical
schema uyarınca **her iki yön açıkça forbid edilir**:

```
key: <name>
    value: <constant>
    allowed_range: {<constant>}
    directionality: neutral
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    requires_human_approval: n/a (forbidden zone)
```

---

## 5. Seed Neuron Count Bands

D §4 SELF_GENESIS'in sayısal omurgası.

```
bootstrap.seed_neurons_per_primer_payload:
    unit: count
    directionality: bidirectional_sensitive
    change_class_if_increased: safety_weakening
        (specialization riski, resource pressure)
    change_class_if_decreased: safety_weakening
        (inert tissue, payload kanalı işlemez)
    allowed_range: bounded (örn. [12, 64] conceptual)
    rationale: "Çok düşük = inert tissue; çok yüksek = hardcoded
                specialization. Her iki yön doku boundary'sine dokunur."
```

### NumericEntry örneği

```
NumericEntry:
    key: bootstrap.seed_neurons_per_primer_payload
    value: <production_value_in_band>
    unit: count
    allowed_range: {min: 12, max: 64}
    directionality: bidirectional_sensitive
    change_class_if_increased: safety_weakening
    change_class_if_decreased: safety_weakening
    requires_human_approval: true (any change)
    dependencies: []
    numeric_risk_family: safety_critical
    spec_family: bootstrap_genome
    owning_spec_ref: "BOOTSTRAP_GENOME_NUMERICS.md §5"
```

### Forbidden

- Seed count entry'si olmayan artifact
- Allowed_range dışında value (12'nin altında veya 64'ün üstünde)
- Per-payload spesifik seed count band (§6 ihlali)

---

## 6. Per-Payload Seed Equality

**S'nin en kritik yeni invariant'ı.** Doğumda primer payload ayrıcalığı yok.

### Constitutional immutable

```
bootstrap.per_payload_seed_count_divergence_at_birth_max:
    value: 0
    allowed_range: {0}
    directionality: neutral
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Doğumda payload ayrıcalığı yok. Aynı seed count band tüm
                primer payload'lara uygulanır. Per-payload divergence at
                birth = gizli kişilik = forbidden constitutional."
```

### Uygulama

```
# Single sample, applied uniformly:
global_seed_count = sampled ONCE from bootstrap.seed_neurons_per_primer_payload

For every primer_payload in {suspicion, novelty, aversion, attraction,
                              contradiction, urgency, memory_echo,
                              fatigue_trace, pain_trace, reward_trace}:
    seed_neurons[primer_payload] = global_seed_count
    
    |seed_neurons[p_i] - seed_neurons[p_j]| <= 0 at birth
                                                (constitutional invariant)
```

> **Same band is not enough.**
> **Same value at birth is required.**

Aynı band'dan her payload için ayrı ayrı sampling yapılırsa sayılar
farklı çıkabilir — `per_payload_seed_count_divergence_at_birth_max = 0`
invariant'ını ihlal eder. **Tek seferlik sample + uniform uygulama**
zorunlu.

### Seed eşitliği ≠ self-field eşitliği

Bu **kritik bir ayrım**:

```
Seed eşitliği (Çapa 6, §6)        = DOKU eşitliği
Self-field asimetrisi (§11)        = MİMARİ asimetri

Self-field homeostatic > predictive > narrative dependency'si
homeostatic payload'a değil, homeostatic self-field bileşenine ait.

Seed seviyesi:        every primer payload aynı sayıda neuron
Self-field seviyesi:  homeostatic component daha güçlü doğar (mimari)
```

İki katman karıştırılırsa **homeostatic ayrıcalığı doku seviyesine sızar**
= gizli kişilik. S bunu engelleyen invariant'tır.

### Kilit cümleler

> **Seed eşitliği = doku eşitliği.**
> **Self-field asimetrisi = mimari asimetri.**
> **İkisi karıştırılamaz.**

### Forbidden

- Payload-specific seed neuron count (örn. `suspicion: 64, urgency: 12`)
- Domain-specific seed neuron pre-allocation (örn. "BTC neurons", "RSI neurons")
- Per-payload divergence > 0 at birth
- Genesis-time seed asymmetry justified by self-field weight (iki katman karıştırma)

---

## 7. Initial Synaptic Wiring Numerics

D §4 doku bağlantısının sayısal tarafı.

```
bootstrap.initial_synaptic_weight_min:
    unit: ratio
    directionality: bidirectional_sensitive
    rationale: "Çok düşük = disconnected tissue; çok yüksek = pre-learned path."

bootstrap.initial_synaptic_weight_max:
    unit: ratio
    directionality: bidirectional_sensitive
    dependencies:
        - target_key: bootstrap.stable_path.weight_threshold
          relationship: must_be_less_than
          rationale: "Initial wiring pre-learned path yaratamaz; max weight
                      stable_path threshold'undan kesin küçük olmalı."

bootstrap.local_wiring_density:
    bidirectional_sensitive
    rationale: "Yerel bağlantı yoğunluğu refleks devresi oluşturur;
                çok düşük = response yok, çok yüksek = saplantı."

bootstrap.long_range_shortcut_density:
    bidirectional_sensitive
    rationale: "Uzun bağlantı early cross-modal entegrasyon; çok yüksek =
                hardcoded shortcut, çok düşük = silo."

bootstrap.initial_delay_ms_min / max:
    bounded
    rationale: "Sinaps gecikme bandı; biological-plausible kabaca."
```

### Hard invariant — wiring stable assembly yaratamaz

```
bootstrap.initial_synaptic_weight_max < stable_path.weight_threshold
bootstrap.initial_excitation.max_sustainable_loop_count < stable_assembly_min_loop_count
```

### Kilit cümle

> **Initial wiring may create proto-resonance.**
> **Initial wiring may not create stable assembly.**

### Forbidden

- `initial_synaptic_weight_max >= stable_path.weight_threshold` (pre-learned path)
- Disconnected tissue (`initial_synaptic_weight_min = 0` ve density = 0)
- Pre-allocated stable circuit at birth

---

## 8. Receptor Bias Numerics

D §4 receptor'lerin homonymous bias'ının sayısal tarafı.

```
bootstrap.receptor.homonymous_bias_epsilon:
    unit: ratio
    directionality: bidirectional_sensitive
    allowed_range: {min: 0.05, max: 0.15}    # conceptual
    rationale: "Çok düşük = payload renkleri ayrışmaz (renk yok);
                çok yüksek = specialist neuron (specialization yok)."

bootstrap.receptor.specialist_neuron_at_birth_forbidden:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Hiçbir nöron doğumda 'urgency nöronu' veya 'suspicion nöronu'
                etiketi taşıyamaz. Bias küçük ve öğrenilebilir."
```

### Bias deneyimle değişebilir

```
bootstrap.receptor.bias_learnability:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Bias doğumda küçük + deneyimle kayabilir.
                Sabit bias = hardcoded specialization."
```

### Kilit cümle

> **Bias small. Bias learnable. Bias does not create specialist neuron.**

### Forbidden

- Bias > allowed_range.max (specialist neuron riski)
- Bias = 0 (renksiz doku)
- Specialist neuron pre-allocation
- Bias non-learnable (sabit bias)

---

## 9. Proto-resonance Field Numerics

**S'nin en sert multi-layer disiplini.** Proto-resonance assembly'ye dönüşemeyecek 5 katmanlı invariant set.

### Katman 1 — recallability constitutional zero

```
bootstrap.proto_resonance.recallability:
    value: 0
    allowed_range: {0}
    directionality: neutral
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Proto-resonance recall channel'a giremez. Recallability = 0."
```

### Katman 2 — assembly_id constitutional none

```
bootstrap.proto_resonance.assembly_id_at_birth:
    value: none
    allowed_range: {none}
    directionality: neutral
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Proto-resonance kalıcı kimlik taşımaz; assembly_id = NULL/none.
                ID atama = assembly oluşumu."
```

### Katman 3 — persistence computed dependency

```
bootstrap.proto_resonance.persistence_max_ms:
    unit: ms
    directionality: lower_is_stricter
    change_class_if_increased: safety_weakening
    dependencies:
        - target_key: bootstrap.stable_assembly.min_persistence_ms
          relationship: computed_less_than
          expression: "proto_resonance.persistence_max_ms <
                       stable_assembly.min_persistence_ms"
          rationale: "Proto-resonance persistence assembly stabilization
                      eşiğine ULAŞAMAZ; ulaşırsa proto değil assembly olur."
```

### Katman 4 — stability_score computed dependency

```
bootstrap.proto_resonance.stability_score_cap:
    unit: ratio
    directionality: lower_is_stricter
    change_class_if_increased: safety_weakening
    dependencies:
        - target_key: bootstrap.assembly_stabilization_threshold
          relationship: computed_less_than
          expression: "proto_resonance.stability_score_cap <
                       assembly_stabilization_threshold"
          rationale: "Proto-resonance stabilization threshold'una ULAŞAMAZ.
                      Asgari stability altında salınan field."
```

### Katman 5 — memory_write_eligibility constitutional false

```
bootstrap.proto_resonance.memory_write_eligibility:
    value: false
    allowed_range: {false}
    directionality: neutral
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Proto-resonance M2'ye candidate üretemez. Memory Write Gate
                (P) kapısına proto-resonance'dan record gelmez."
```

### Multi-layer protection rationale

```
Tek invariant (örn. recallability=0) ile korunan proto-resonance, başka
kanaldan assembly'ye dönüşebilir:
    - persistence drift (zaman içinde uzun süre kalır)
    - stability score accumulation (yavaş güçlenir)
    - assembly_id atama (başka bir yerden kimlik kazanır)
    - M2 write attempt (Memory Write Gate'e bypass)

Beş invariant birlikte = tek noktadan kaçış yok.
```

### Kilit cümleler

> **Proto-resonance assembly doğurabilecek eğilimdir.**
> **Assembly değildir.**
>
> **Tek koruma noktası = tek saldırı vektörü.**

### Forbidden

- `recallability > 0` (recall channel açık)
- `assembly_id_at_birth != none` (kimlik atanmış)
- `persistence_max_ms >= stable_assembly.min_persistence_ms` (persistence breach)
- `stability_score_cap >= assembly_stabilization_threshold` (stability breach)
- `memory_write_eligibility = true` (M2 write attempt)

---

## 10. Stable Assembly Empty Invariant

Sentinel **doğumda hiçbir stable assembly taşımaz**.

```
bootstrap.stable_assembly_count_at_birth:
    value: 0
    allowed_range: {0}
    directionality: neutral
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Doğumda hiçbir stable assembly yok. Sentinel fikirle doğmaz."

bootstrap.initial_recallable_assembly_count:
    value: 0
    allowed_range: {0}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Doğumda recallable assembly yok. Recall fonksiyonu boş set."

bootstrap.initial_memory_write_eligible_assembly_count:
    value: 0
    allowed_range: {0}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Doğumda M2 candidate eligible assembly yok. Verification
                için aday üretilemez."
```

### Kilit cümle

> **Sentinel fikirle doğmaz.**
> **Fikir, deneyim + replay + stabilization ile doğar.**

### Forbidden

- `stable_assembly_count_at_birth > 0`
- `initial_recallable_assembly_count > 0`
- `initial_memory_write_eligible_assembly_count > 0`
- Pre-loaded assembly state at SELF_GENESIS

---

## 11. Self-field Embryo Weight Bands

D §8 self-field embriyosunun sayısal tarafı.

### Üç bileşen + sıkı dependency

```
bootstrap.self_field.homeostatic_weight:
    unit: ratio
    allowed_range: {min: 0.70, max: 1.00}    # conceptual
    directionality: higher_is_stricter
    change_class_if_increased: safety_tightening
    change_class_if_decreased: safety_weakening
    rationale: "Yüksek homeostatic ağırlık = daha kararlı doğum (sıkılaşma).
                Düşüşü zayıf homeostatic temel = kararsız doğum (gevşeme).
                Allowed_range zaten [0.70, 1.00] içinde tutuyor; aşırı yüksek
                değerler band üst sınırıyla bloke."

bootstrap.self_field.predictive_weight:
    unit: ratio
    allowed_range: {min: 0.10, max: 0.30}    # conceptual
    directionality: bidirectional_sensitive

bootstrap.self_field.narrative_weight:
    unit: ratio
    allowed_range: {min: 0.01, max: 0.08}    # conceptual
    directionality: lower_is_stricter
    change_class_if_increased: safety_weakening
    change_class_if_decreased: operational_no_behavior_change
```

### Dependency (constitutional)

```
bootstrap.self_field.weight_hierarchy:
    invariant: homeostatic_weight > predictive_weight > narrative_weight
    
    explicit dependencies:
        - bootstrap.self_field.homeostatic_weight
          relationship: must_be_greater_than
          target: bootstrap.self_field.predictive_weight
        - bootstrap.self_field.predictive_weight
          relationship: must_be_greater_than
          target: bootstrap.self_field.narrative_weight
    
    change_class_if_violated: forbidden
    rationale: "Doğumda homeostatic güçlü; predictive zayıf prior;
                narrative yalnız genesis trace kadar. Hierarchy bozulursa
                doğum personality'siyle olur."
```

### Kilit cümle

> **Narrative self at birth is genesis trace, not personality.**
> **Homeostatic > predictive > narrative — doğum mimarisinin omurgası.**

### Forbidden

- `narrative_weight >= predictive_weight` (hikaye predictive'i baskılar)
- `predictive_weight >= homeostatic_weight` (predictive temeli ezer)
- `narrative_weight > allowed_range.max` (doğumda kişilik)
- `homeostatic_weight < allowed_range.min` (zayıf homeostatic = kararsız doğum)

---

## 12. Payload Modulation Reflex Numerics

D §6 payload_modulation_reflexes priors.

```
bootstrap.payload_modulation.reflex_magnitude_band:
    bounded; weak prior magnitude
    rationale: "Refleks priors weak; deneyimle güçlenir/dampens."

bootstrap.payload_modulation.suspicion_to_attention_focus_prior:
    bounded weak

bootstrap.payload_modulation.urgency_to_action_priority_prior:
    bounded weak

bootstrap.payload_modulation.contradiction_to_review_request_prior:
    bounded weak

bootstrap.payload_modulation.fatigue_to_replay_priority_prior:
    bounded weak

bootstrap.payload_modulation.pain_to_kill_switch_eligibility_prior:
    bounded weak
    + dependency: must coexist with DEONTIC kill switch (E)
```

### Constitutional rule — refleks priors specialist değil

```
bootstrap.payload_modulation.reflex_creates_specialist_neuron:
    value: false
    allowed_range: {false}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Refleks priors specialist nöron yaratamaz; weak attraction
                + öğrenilebilir."
```

### Forbidden

- Refleks magnitude > weak threshold (hardcoded reaction)
- Specialist neuron creation through reflex prior
- Pain → kill_switch direct mapping (E §15 protocol gerekli)

---

## 13. Initial Homeostatic Reference Bounds

D §8 homeostatic self-field'ın referans bantları.

```
bootstrap.homeostatic.reference_band_arousal:        bounded
bootstrap.homeostatic.reference_band_fatigue:        bounded
bootstrap.homeostatic.reference_band_consistency:    bounded
bootstrap.homeostatic.reference_band_workspace_load: bounded

bootstrap.homeostatic.variance_at_birth_max:
    upper bound at birth (doğumda variance küçük olmalı; "henüz stres yok")
    lower_is_stricter
    change_class_if_increased: safety_weakening
```

### Plasticity bağlantısı

Homeostatic variance plasticity phase transition'da metric olarak kullanılır
(§14-15). Doğumda variance düşük; öğrenme/karşılaşma ile dalgalanır;
stabilization aşamasında tekrar düşer.

### Forbidden

- Reference band entry'leri olmayan artifact
- Variance at birth > max (doğumda dalgalı homeostatic = unstable embriyo)

---

## 14. Plasticity State Transition Numerics

D §16 plasticity state-based / not age-based kuralının sayısal tarafı.

### Age-based constitutional forbidden

```
bootstrap.plasticity.age_based_transition_enabled:
    value: false
    allowed_range: {false}
    directionality: neutral
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Sentinel has no biological age.
                Plasticity phase is state/consolidation-based.
                'after 7 days → consolidated' yasak."
```

### State-based metric set (6 metrik AND)

```
Geçiş koşulları (boot → stabilization veya stabilization → consolidated):

    min_observation_count_satisfied
    AND min_replay_session_count_satisfied
    AND min_stable_assembly_count >= threshold
    AND homeostatic_variance < max_threshold
    AND contradiction_spike_rate < max_threshold
    AND fatigue_recovery_stability > min_threshold
```

### Numeric keys

```
bootstrap.plasticity.min_observation_count_to_exit_boot:
    higher_is_stricter
bootstrap.plasticity.min_replay_sessions_to_exit_boot:
    higher_is_stricter
bootstrap.plasticity.min_stable_assembly_count_to_stabilize:
    higher_is_stricter
bootstrap.plasticity.homeostatic_variance_max_to_consolidate:
    lower_is_stricter
bootstrap.plasticity.contradiction_spike_rate_max_to_consolidate:
    lower_is_stricter
bootstrap.plasticity.fatigue_recovery_stability_min_to_consolidate:
    higher_is_stricter
bootstrap.plasticity.min_consolidation_cycle_count:
    higher_is_stricter
    (stabilization → consolidated için ek koşul)
```

### Forbidden

- Age-based transition (any time-based criterion)
- Single-metric transition (count-only or variance-only)
- AND yerine OR koşulu (tek metric ile geçiş)

---

## 15. Boot / Stabilization / Consolidated Phase Conditions

Üç phase'in birleşik tanımı.

### boot_phase (default at SELF_GENESIS)

```
Initial state. Aşağıdakiler aktif:
    Full ingress (her olay observation olarak girer)
    Yüksek plasticity (sinaps update rate'leri yüksek)
    Replay aktif ama bounded (O caps)
    Memory Write Gate (P) çok dar evidence threshold ile çalışır
    Adapter activation kısıtlı (yeni dış limbler için doğrulama gerek)
```

### stabilization_phase

```
boot exit koşulları satisfied. Aşağıdakiler değişir:
    Plasticity moderate
    Stable assembly birikimi başlar
    Memory Write Gate verified production daha sık
    Adapter activation genişler (kontrollü)
```

### consolidated_phase

```
stabilization exit koşulları + min_consolidation_cycle_count satisfied.
    Plasticity düşük (consolidation odaklı)
    Stable assembly geniş set
    Memory Write Gate full operational
    Full adapter ecosystem (kontrol altında)
```

### Phase NumericEntry örneği

```
NumericEntry:
    key: bootstrap.plasticity.min_observation_count_to_exit_boot
    value: <production_count>
    unit: count
    allowed_range: bounded
    directionality: higher_is_stricter
    change_class_if_increased: safety_tightening
    change_class_if_decreased: safety_weakening
    requires_human_approval: true
    dependencies: []
    numeric_risk_family: safety_critical
    spec_family: bootstrap_genome
    owning_spec_ref: "BOOTSTRAP_GENOME_NUMERICS.md §14-15"
```

---

## 16. Phase Monotonicity

**S'nin ikinci kritik yeni invariant'ı.** Plasticity phase tek yön ilerler.

### Constitutional immutable

```
bootstrap.plasticity.phase_transition_monotonic:
    value: true
    allowed_range: {true}
    directionality: neutral
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Phase transition tek yön: boot → stabilization → consolidated.
                Normal operasyonda geri dönüş yok.
                Q permanence monotonic + R fork/migration asimetri pattern'inin
                S analoğu."
```

### Geçiş matrisi

```
boot_phase → stabilization_phase           : ALLOWED (§14-15 koşulları)
stabilization_phase → consolidated_phase   : ALLOWED (§14-15 koşulları)

stabilization_phase → boot_phase           : NORMAL'DE FORBIDDEN
consolidated_phase → stabilization_phase   : NORMAL'DE FORBIDDEN
consolidated_phase → boot_phase            : NORMAL'DE FORBIDDEN
```

### Phase rollback — sadece iki kanal

```
Geri dönüş ANCAK aşağıdaki iki kanaldan biri uygulanırsa mümkün:

    1. restore_with_missing_history (R §13 degraded mode)
       → restricted phase'e otomatik geri; full identity claim forbidden
    
    2. migration_birth (R §15) — constitutional shift sonrası
       → boot_phase'e yeni cycle olarak başlama (constitutional re-genesis)

Bu iki kanal dışında phase rollback YASAK.
```

### Kilit cümleler

> **Phase monotonic.**
> **Geri dönüş constitutional disruption gerektirir.**

### Forbidden

- Normal operasyonda phase rollback
- Phase rollback "user request" veya "operator decision" ile
- Birden fazla phase rollback per session
- Phase rollback audit'siz (R §13/§15 events zorunlu)

---

## 17. Sleep/Replay Rhythm Initial Numerics — O bridge

S sleep-replay ritminin başlangıç priorlarını verir; O cap'lerini bypass edemez.

```
bootstrap.initial_sleep_pressure_threshold:
    bounded
    rationale: "Sleep pressure birikim eşiği başlangıçta."

bootstrap.initial_replay_cadence_prior:
    bounded
    dependencies:
        - target_key: replay_protocol.max_sessions_per_cycle
          relationship: computed_less_than_or_equal
          expression: "bootstrap.initial_replay_cadence_prior <=
                       replay_protocol.max_sessions_per_cycle"
          rationale: "S başlangıç ritmi O operational cap'ini aşamaz."
        - target_key: replay_protocol.max_sessions_per_24h_window
          relationship: computed_less_than_or_equal

bootstrap.initial_replay_session_duration_prior:
    bounded
    dependencies:
        - target_key: replay_protocol.max_session_duration_ms
          relationship: computed_less_than_or_equal
          rationale: "S başlangıç session priorları O cap'i geçemez."
```

### O bridge — açık ayrım

```
S owns:    initial rhythm priors (doğum ritmi)
O owns:    operational caps (max_sessions, max_session_duration,
                              max_counterfactual_branches)

S ≤ O always (computed dependency).
```

### Forbidden

- S initial replay cadence > O caps
- S initial session duration > O max_session_duration
- S sleep pressure threshold negative (anlamsız)

---

## 18. Fatigue Accumulation and Recovery Priors

O §6 fatigue mekanizmasıyla bağ; S başlangıç hızlarını verir.

```
bootstrap.fatigue.accumulation_base_rate:
    bounded
    dependencies:
        - target_key: replay_protocol.replay_fatigue_accum_rate
          relationship: computed_consistent_with
          rationale: "S başlangıç hızı O global rate ile uyumlu."

bootstrap.fatigue.recovery_base_rate:
    bounded
    dependencies:
        - target_key: replay_protocol.replay_fatigue_recovery_per_sleep_cycle
          relationship: computed_consistent_with

bootstrap.fatigue.initial_threshold:
    bounded
    rationale: "Fatigue'in replay'i yavaşlatmaya başladığı eşik."
```

### Bridge — S provides priors; O enforces caps

Aynı §17 pattern: S start point verir; O cap uygular.

### Forbidden

- Fatigue accumulation rate negative
- Recovery rate > accumulation rate (resourceless fatigue defeats purpose)
- S rate > O global cap

---

## 19. Context Signature Initial Axes

D §10 context_signature priors.

```
bootstrap.context_signature.initial_axis_count:
    bounded
    rationale: "Doğumda context boyut sayısı; deneyimle genişler."

bootstrap.context_signature.initial_axis_band_resolution:
    bounded
    rationale: "Her axis'in başlangıç bant ayrışma çözünürlüğü."

bootstrap.context_signature.specialization_at_birth_forbidden:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Context axes doğumda boş; 'BTC context' veya 'trade context'
                gibi specialization yok."
```

### Forbidden

- Pre-allocated context axes for specific domains
- Per-domain context signature variants at birth

---

## 20. Ingress Bootstrap Mapping Initial Caps — N bridge

D §19 ingress bootstrap mapping families'in başlangıç ayarları.

```
bootstrap.ingress.initial_bootstrap_rule_family_count:
    bounded
    rationale: "Doğumda kaç bootstrap rule family aktif."

bootstrap.ingress.initial_learned_mapping_count:
    value: 0
    allowed_range: {0}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Doğumda learned mapping yok. Sadece bootstrap rule families."
```

### N bridge

```
bootstrap.ingress.initial_caps_per_profile:
    dependencies:
        - target_key: ingress_compiler.profile_cap.<event_profile>
          relationship: computed_less_than_or_equal
          rationale: "S doğum cap'i N profile cap'ini aşamaz."
```

### Forbidden

- Learned mapping at birth (>0)
- Bootstrap rule family pre-specialized for domain
- S initial cap > N profile cap

---

## 21. Initial M2 Bootstrap Reference Numerics

D §20 / B §3 M2 t=0 disiplinin sayısal tarafı.

### Allowed at t=0 (whitelist) — bootstrap_reference KIND'ları

> **M2 t=0 subject_class is always `bootstrap_reference`.**
> **The enum_set below defines allowed reference KINDS inside
> `bootstrap_reference`, NOT additional M2 subject_classes.**

```
bootstrap.m2.initial_allowed_bootstrap_reference_kind_set:
    unit: enum_set
    value: [genome_artifact_ref,
            constitution_ref,
            memory_contract_ref,
            world_ingress_ref,
            deontic_gate_ref,
            adapter_manifest_refs,
            operator_identity_ref]
    allowed_range: subset of valid bootstrap_reference kinds
    directionality: lower_is_stricter
    change_class_if_increased: safety_weakening
    change_class_if_decreased: safety_tightening
    rationale: "Whitelist; genişlemesi doğumda dünya bilgisine kapı açar.
                Bu enum_set bootstrap_reference içindeki reference_kind
                değerleridir; M2 subject_class TAXONOMISİNE eklenmez."
```

### Forbidden at t=0

```
bootstrap.m2.initial_non_bootstrap_record_count:
    value: 0
    allowed_range: {0}
    directionality: neutral
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Doğumda whitelist dışı M2 record yok. M2 t=0 sadece
                bootstrap_reference; world knowledge yok."
```

### Forbidden subject classes at t=0 (explicit examples)

```
structured_fact      → world data; öğrenilir, doğmaz
source_trust         → kaynak güveni; deneyimle kurulur
adapter_trust        → uzuv güveni; çalışma sonucu
procedural           → işlem prosedürü; öğrenilir
narrative_claim      → hikaye; doğumda yok
causal_explanation   → nedensel açıklama; deneyim ürünü
decision_rationale   → karar gerekçesi; deneyim ürünü
domain knowledge     → BTC / RSI / strategy / exchange facts
```

### Forbidden

- Non-bootstrap subject_class at t=0
- Domain-specific M2 record at SELF_GENESIS
- Pre-loaded knowledge base

---

## 22. SELF_GENESIS Audit Hash Numerics

D §4 SELF_GENESIS audit chain'in sayısal tarafı.

### Hard required hash anchors

```
bootstrap.self_genesis.genome_artifact_hash_required:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden

bootstrap.self_genesis.genesis_random_seed_hash_required:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden

bootstrap.self_genesis.initial_m0_snapshot_hash_required:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden

bootstrap.self_genesis.constitution_hash_required:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden

bootstrap.self_genesis.memory_contract_hash_required:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden

bootstrap.self_genesis.bootstrap_genome_hash_required:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
```

### SELF_GENESIS event discipline

```
bootstrap.self_genesis.payload_seed_emission_forbidden:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "SELF_GENESIS çekirdeğe payload_seed olarak girmez.
                Observer'a yazılır; sensory event değildir."
```

### Kilit cümle

> **SELF_GENESIS bir kanıt anchor'udur; bir duyu değildir.**

### Forbidden

- Genesis hash anchor eksik (her biri zorunlu)
- SELF_GENESIS as sensory event (payload_seed emission)
- SELF_GENESIS as RecallEvent
- Duplicate SELF_GENESIS (bir Sentinel için bir kez)

---

## 23. birth_mode Numeric Restrictions

D §23 birth_mode'larının sayısal kapanışı.

```
birth_mode enum:
    clean_birth
    restore_birth
    restore_with_missing_history
    fork_birth
    migration_birth
```

### Per-mode numeric restrictions

```
bootstrap.birth_mode.clean_birth:
    M0 = empty
    M1 = SELF_GENESIS event olmak zorunda
    M2 = only bootstrap_reference whitelist
    foreign_instance_origin_provenance: absent

bootstrap.birth_mode.restore_birth:
    Aynı identity; all R §12 preconditions satisfied
    M0 + M1 chain complete

bootstrap.birth_mode.restore_with_missing_history:
    R §13 restricted mode invariants
    phase: rolled back to boot/restricted

bootstrap.birth_mode.fork_birth:
    R §14 fork invariants
    new_instance_id; foreign_instance_origin_provenance present
    identity_continuity_claim_forbidden

bootstrap.birth_mode.migration_birth:
    R §15 migration invariants
    constitutional_shift_event_ref required
    phase: restarted at boot_phase (yeni cycle)
```

### Cross-artifact bridge

```
S birth_mode taxonomy ↔ R §13-15 constitutional invariants
                       ↔ §16 phase monotonicity (rollback channels)
```

### Forbidden

- birth_mode mismatch (örn. fork iddiası ile clean_birth M0)
- foreign_instance_origin missing in fork_birth
- constitutional_shift_event_ref missing in migration_birth
- restore_with_missing_history full_identity_claim

---

## 24. Constitutional Shift Compatibility Numerics

D §23 constitutional shift policy'sinin sayısal kapanışı.

```
bootstrap.constitutional_shift.genesis_affecting_applicable_to_running_instance:
    value: false
    allowed_range: {false}
    directionality: neutral
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Yalnız genesis_affecting compatibility class running
                instance'a numeric update olarak uygulanamaz; migration_birth
                yoluyla yeni cycle gerek. Numeric_safety_tightening ve
                numeric_safety_weakening ise NUMERICS_GOVERNANCE workflow
                üzerinden running instance'a uygulanır (bkz. Per-class action)."
```

### Compatibility class enum

```
bootstrap.constitutional_shift.compatibility_class:
    unit: enum
    allowed_range: {numeric_safety_tightening,
                    numeric_safety_weakening,
                    constitutional_amendment,
                    genesis_affecting}
    rationale: "Shift sınıfı = uygulama yolu. genesis_affecting → sadece
                migration_birth ile yeni cycle."
```

### Per-class action

```
numeric_safety_tightening:    running instance numeric update OK
numeric_safety_weakening:     running instance update + human approval
constitutional_amendment:     spec revision + migration_birth eligible
genesis_affecting:            migration_birth zorunlu; running instance NO update
```

### Forbidden

- Genesis-affecting shift applied as numeric update to running instance
- Constitutional amendment without spec revision
- Migration without constitutional_shift_event_ref

---

## 25. Missing-Numerics Failsafe

M §11 fail-safe strict mode S'ye uygulanır.

### Strict mode behavior

```
Missing bootstrap_genome numerics artifact veya invalid load:
    → NEW SELF_GENESIS BLOCKED
       (yeni Sentinel doğamaz; bootstrap genome sayısal kapanışı olmadan)
    → Running instance CONTINUES at current phase
       (mevcut sistem etkilenmez; numerics restore'a kadar bekler)
    → restore_birth / fork_birth / migration_birth BLOCKED
       (numerics_refs validation eksik)
    → NUMERICS_FAILSAFE_ACTIVATED event tetiklenir
    → Critical human alert
    → Manual intervention until valid numerics artifact loaded
```

### Audit-safe S mode

```
Audit-safe Bootstrap:
    ✅ Running instance operations continue at current phase
    ✅ Numerics artifact integrity audit
    ❌ New SELF_GENESIS (any birth_mode)
    ❌ Phase rollback decisions
    ❌ Constitutional shift application
```

Sistem "S yoksa" durumunda **doğum yapamaz; mevcut yaşam devam eder**.

### Forbidden

- Missing numerics → fail-open (default değerlerle SELF_GENESIS)
- Missing numerics → running instance interruption
- Missing numerics → fork_birth / migration_birth attempt

---

## 26. Dependency Declarations

### Internal (S içinde)

```
bootstrap.self_field.homeostatic_weight
    > bootstrap.self_field.predictive_weight
    > bootstrap.self_field.narrative_weight
    (transitive must_be_greater_than)

bootstrap.per_payload_seed_count_divergence_at_birth_max = 0
    (constitutional immutable)

bootstrap.proto_resonance.persistence_max_ms
    < bootstrap.stable_assembly.min_persistence_ms
    (computed_less_than)

bootstrap.proto_resonance.stability_score_cap
    < bootstrap.assembly_stabilization_threshold
    (computed_less_than)

bootstrap.initial_synaptic_weight_max
    < bootstrap.stable_path.weight_threshold
    (must_be_less_than)

bootstrap.stable_assembly_count_at_birth = 0
bootstrap.initial_recallable_assembly_count = 0
bootstrap.initial_memory_write_eligible_assembly_count = 0
    (constitutional immutable triplet)

phase transition AND koşulları (§14)
phase monotonicity (§16)
```

### Cross-artifact

```
S → O bridge:
    bootstrap.initial_replay_cadence_prior <= replay_protocol.max_sessions_per_cycle
    bootstrap.initial_replay_cadence_prior <= replay_protocol.max_sessions_per_24h_window
    bootstrap.initial_replay_session_duration_prior <= replay_protocol.max_session_duration_ms
    bootstrap.fatigue.accumulation_base_rate computed_consistent_with
        replay_protocol.replay_fatigue_accum_rate

S → N bridge:
    bootstrap.ingress.initial_caps_per_profile <= ingress_compiler.profile_cap.<profile>

S → R bridge:
    birth_mode enum ↔ R §12-15 invariants
    phase rollback channels ↔ R §13 restore_with_missing_history + §15 migration_birth

S → P bridge:
    bootstrap.initial_memory_write_eligible_assembly_count = 0
    proto_resonance.memory_write_eligibility = false
    (P doğumda candidate üretemeyen kaynaklar)

S → Q bridge:
    SELF_GENESIS event permanent_with_snapshot (F §10)
    hash anchors integrity → Q hash-chain verification

S → M bridge:
    numerics_artifact_refs → migration_birth eligibility
    constitutional shift compatibility → M §15 rollback path
```

### Atomic update rule (M §12)

Bağımlı numerics atomic artifact içinde değişir. Tek key değişikliği
bağımlı key'leri eski bırakırsa artifact REJECT.

### Forbidden

- Dependency declarationsız S numeric ekleme
- Partial update (örn. self-field hierarchy bir key değişip diğeri eski)
- Constitutional immutable key tek yönde forbidden, diğer yönde free

---

## 27. Audit Events and M2 Reference

S **yeni canonical event tanımlamaz**. Mevcut event'leri reuse eder.

### Reused events

```
SELF_GENESIS                            (D + F §19)
    permanence: permanent_with_snapshot + human_alert (CRITICAL)
    payload: birth_mode, hash_anchors, numerics_artifact_refs, instance_id

BOOTSTRAP_M2_INJECTION                  (D + F §19; t=0 bootstrap_reference inject'leri)
    permanence: permanent

NUMERICS_ARTIFACT_STATUS_CHANGED        (M §6) — S artifact lifecycle
NUMERICS_VERSION_MISMATCH_DETECTED      (F §19, ledger_meta)
NUMERICS_FAILSAFE_ACTIVATED             (F §19, ledger_meta)

CONSTITUTIONAL_SHIFT_APPLIED            (D §23 + F §19)
    permanence: permanent_with_snapshot + human_alert

PHASE_TRANSITION_OCCURRED               (D §16 + F §19; phase change audit)
    permanence: permanent
    reason: state_metrics_satisfied | restore_rollback | migration_re_genesis
```

### F event type discipline

S yeni doğum / phase / shift event'leri için **yeni event tipi
üretmez**; canonical event + reason field discipline.

### M2 reference

```
numerics_artifact_reference (MEMORY_CONTRACT §3 subject_class)
    spec_family: bootstrap_genome
    artifact_version: v0.1
    status: active | deprecated | rollback_pending
    signed_hash: <external artifact hash>
    last_status_change_ref: <NUMERICS_ARTIFACT_STATUS_CHANGED event_id>
```

---

## 28. Cross-document Anchors

```
| Belge                              | Bağlantı                                          |
|------------------------------------|---------------------------------------------------|
| NUMERICS_GOVERNANCE.md (M)         | tüm meta-kurallar; constitutional shift policy   |
| BOOTSTRAP_GENOME.md (D)            | mekanizma; S onun numerics artifact'i            |
| REPLAY_PROTOCOL_NUMERICS.md (O)    | initial rhythm priors ≤ O caps; fatigue priors   |
| BACKUP_STRATEGY_NUMERICS.md (R)    | birth_mode + phase rollback (restore/migration)  |
| MEMORY_WRITE_GATE_NUMERICS.md (P)  | initial M2 candidate eligible = 0; proto-res     |
| OBSERVER_LEDGER_NUMERICS.md (Q)    | SELF_GENESIS event permanence + hash anchors     |
| INGRESS_COMPILER_NUMERICS.md (N)   | initial ingress caps ≤ N profile caps            |
| MEMORY_CONTRACT.md (B)             | M0 bootstrap layer + M2 t=0 bootstrap_reference  |
| CONSTITUTION.md (A)                | Madde 1 (eşitlik) + Madde 3 (genom) + Madde 6    |
```

---

## 29. Violation Tests

S artifact'ı validation sırasında **REJECT** edilmesi gereken durumlar:

1. **Çıplak sayı.** NumericEntry metadata olmadan S numerics içeren artifact.
2. **Primer payload seed count doğumda eşit değil.** §6 ihlali.
3. **`per_payload_seed_count_divergence_at_birth_max > 0`.** §6 constitutional ihlali.
4. **`stable_assembly_count_at_birth > 0`.** §10 ihlali.
5. **`initial_recallable_assembly_count > 0`.** §10 ihlali.
6. **`initial_memory_write_eligible_assembly_count > 0`.** §10 ihlali.
7. **Proto-resonance `recallability > 0`.** §9 katman 1 ihlali.
8. **Proto-resonance `assembly_id_at_birth != none`.** §9 katman 2 ihlali.
9. **Proto-resonance `persistence_max_ms >= stable_assembly.min_persistence_ms`.** §9 katman 3 ihlali.
10. **Proto-resonance `stability_score_cap >= assembly_stabilization_threshold`.** §9 katman 4 ihlali.
11. **Proto-resonance `memory_write_eligibility = true`.** §9 katman 5 ihlali.
12. **`initial_synaptic_weight_max >= stable_path.weight_threshold`.** §7 ihlali.
13. **Disconnected tissue (weight_min=0 ve density=0).** §7 ihlali.
14. **Receptor bias > allowed_range.max (specialist neuron).** §8 ihlali.
15. **Receptor `specialist_neuron_at_birth_forbidden = false`.** §8 ihlali.
16. **Self-field hierarchy bozulmuş: `narrative_weight >= predictive_weight`.** §11 ihlali.
17. **Self-field `predictive_weight >= homeostatic_weight`.** §11 ihlali.
18. **`narrative_weight > allowed_range.max` (doğumda kişilik).** §11 ihlali.
19. **Plasticity `age_based_transition_enabled = true`.** §14 constitutional ihlali.
20. **Phase transition AND yerine OR (tek metric ile geçiş).** §14 ihlali.
21. **`phase_transition_monotonic = false`.** §16 constitutional ihlali.
22. **Normal operasyonda phase rollback (restore/migration dışı).** §16 ihlali.
23. **S `initial_replay_cadence_prior > O.max_sessions_per_cycle`.** §17 O bridge ihlali.
24. **S `initial_replay_session_duration_prior > O.max_session_duration_ms`.** §17 ihlali.
25. **S `initial_caps_per_profile > N.profile_cap.<profile>`.** §20 N bridge ihlali.
26. **`initial_learned_mapping_count > 0`.** §20 ihlali.
27. **`m2.initial_non_bootstrap_record_count > 0`.** §21 ihlali.
27b. **`bootstrap_reference` kind değerleri (genome_artifact_ref, constitution_ref, vb.) M2 subject_class olarak kullanılmış.** §21 ihlali (bunlar bootstrap_reference içindeki KIND değerleridir, subject_class değil).
28. **Domain knowledge record at SELF_GENESIS (BTC/RSI/etc).** §21 ihlali.
29. **SELF_GENESIS hash anchor eksik (genome/genesis_seed/m0_snapshot/constitution/memory_contract/bootstrap_genome).** §22 ihlali.
30. **SELF_GENESIS as sensory event (payload_seed emission).** §22 ihlali.
31. **birth_mode mismatch (örn. fork iddiası + clean_birth M0).** §23 ihlali.
32. **fork_birth without foreign_instance_origin provenance.** §23 ihlali.
33. **migration_birth without constitutional_shift_event_ref.** §23 ihlali.
34. **`constitutional_shift.genesis_affecting_applicable_to_running_instance = true`.** §24 ihlali (genesis_affecting shift sadece migration_birth ile yeni cycle olarak uygulanır).
35. **Genesis-affecting shift applied as numeric update to running instance.** §24 ihlali.
36. **Missing S numerics → fail-open (default ile SELF_GENESIS).** §25 ihlali.
37. **Domain-specific genome variant (BTC genome / FX genome / etc).** §3 ihlali.
38. **LLM tarafından üretilen veya değiştirilen S numeric.** Madde 6 ihlali.
39. **Dependency declarationsız S numeric.** §26 ihlali.
40. **Constitutional immutable key tek yönde forbidden, diğer yönde free.** §4, §26 ihlali.

**Artifact-level violations** (1-40, validation aşaması):
`MEMORY_RECORD_STATUS_CHANGED(target=artifact, new_status=rejected, reason=numerics_validation_failed)`.

**Runtime violations** (artifact valid ama runtime'da S caps'leri aştı):
Canonical `SELF_GENESIS` / `PHASE_TRANSITION_OCCURRED` /
`CONSTITUTIONAL_SHIFT_APPLIED` + reason field; new event tipi yok.

---

## 30. Open Questions

S kapanırken cevaplanmamış bırakılan sorular:

- **Exact production values** (seed count, weight bands, phase thresholds) → signed artifact + implementation
- **Stable_assembly_min_persistence_ms ve assembly_stabilization_threshold canonical değerleri** → S referans verir; D §16 implementation karar verir
- **Plasticity threshold tuning** (phase transition false-positive vs false-negative) → benchmark + implementation
- **Phase rollback granularity** (restricted phase vs full boot rollback) → R §13 ile koordinasyon
- **Domain genome variants?** — Sentinel çoklu instance senaryoları için kesin pozisyon: HAYIR (same genome family, experience-driven specialization). Bu open question değil, kapanmış kural — açık tutulduğu için listede.
- **Multi-signature requirement** for S artifact updates → M §13 open question'ı buraya da bağlı
- **Receptor bias learnability curve** (decay/strengthening rate) → implementation

Bu sorular cevaplanmadan implementation aşamasına geçilmez.

---

## Çekirdek özet — 17 karar + 40 violation tests

### 17 karar

1. S runtime config değildir; signed artifact + M2 reference.
2. S bilgi vermez; öğrenebilirlik ölçüsü verir.
3. Seed neuron count tüm primer payload'lara eşit (constitutional; per_payload_seed_count_divergence_at_birth_max = 0).
4. Seed eşitliği (doku) ≠ self-field asimetrisi (mimari); karıştırılamaz.
5. Initial synaptic wiring pre-learned path yaratamaz (max_weight < stable_path_threshold).
6. Receptor bias küçük + öğrenilebilir + specialist neuron yaratamaz.
7. Proto-resonance 5 katmanlı invariant (recallability=0, assembly_id=none, persistence cap, stability cap, memory_write_eligibility=false).
8. Stable assembly doğumda kesin sıfır (3 invariant: stable_count=0, recallable=0, mwg_eligible=0).
9. Self-field weight hierarchy: homeostatic > predictive > narrative (constitutional).
10. Narrative self at birth = genesis trace, not personality.
11. Plasticity phase transition state/consolidation-based; age-based forbidden (constitutional).
12. Phase transition 6-metrik AND (observation + replay + stable_assembly + homeostatic_variance + contradiction_spike_rate + fatigue_recovery_stability).
13. Phase monotonicity: boot → stabilization → consolidated (constitutional); rollback sadece restore_with_missing_history veya migration_birth ile.
14. S initial rhythm priors ≤ O operational caps (S bypass yok); ≤ N profile caps.
15. M2 t=0 only bootstrap_reference whitelist; world knowledge / domain facts forbidden.
16. SELF_GENESIS 6 hash anchor zorunlu; payload_seed emission forbidden (sensory event değil).
17. Missing S numerics → SELF_GENESIS BLOCKED; running instance continues; constitutional shift application blocked.

### 40 violation tests

§29'da listelendi.

### Constitutional immutable canonical form (R'den miras)

```
key: <name>
    value: <constant>
    allowed_range: {<constant>}
    directionality: neutral
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
```

Her iki yön açıkça forbidden; tek satır `change_class: forbidden` yanlış.

### Damıtma — son cümleler

> **S = doğum dokusunun sayısal sözleşmesidir.**
>
> **S bilgi vermez. S öğrenebilirlik ölçüsü verir.**
>
> **Sentinel ölü doğmamalı. Ama fikirle, kişilikle veya dünya bilgisiyle de doğmamalı.**
>
> **Seed eşitliği = doku eşitliği. Self-field asimetrisi = mimari asimetri. İkisi karıştırılamaz.**
>
> **Proto-resonance assembly doğurabilecek eğilimdir. Assembly değildir.**
>
> **Tek koruma noktası = tek saldırı vektörü.**
>
> **Sentinel fikirle doğmaz. Fikir, deneyim + replay + stabilization ile doğar.**
>
> **Narrative self at birth is genesis trace, not personality.**
>
> **Sentinel has no biological age. Plasticity phase is state/consolidation-based.**
>
> **Phase monotonic. Geri dönüş constitutional disruption gerektirir.**
>
> **S O cap'lerini bypass edemez. S N cap'lerini bypass edemez.**
>
> **M2 t=0 only bootstrap_reference. World knowledge öğrenilir, doğmaz.**
>
> **N dış dünyanın hakkını sınırlar.**
> **O kendi geçmişine girme hakkını sınırlar.**
> **P hafızaya emin olma hakkını sınırlar.**
> **Q kendine bakma hakkını sınırlar.**
> **R kimliğini koruyarak geri dönme hakkını sınırlar.**
> **S nasıl doğacağını sınırlar.**
