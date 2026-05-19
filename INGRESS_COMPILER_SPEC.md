# INGRESS_COMPILER_SPEC.md

## Sentinel — Deterministic Ingress Compiler Sözleşmesi

---

## Status

**Frozen Draft v0.1**
**Conceptual phase. No implementation authority.**

Bu belge `WORLD_INGRESS.md` §13'teki Deterministic Ingress Compiler kavramının detaylı uzantısıdır. Yeni anayasa maddesi değildir. Çalışan bir compiler implementation'ının runtime spec'i değildir. Adapter'lardan gelen structured event'lerin **hangi mekanik kurallarla** çekirdeğin nöral diline (`neural_seed`) çevrildiğini tanımlar.

Bu belge **implementation-adjacent**'tır. A-I belgeleri anayasal/mimari sınırı koydu; J bu sınırın işleyiş biçimini biçimselleştirir. Hâlâ kod yok, ama artık "mapping family", "rate cap", "rule lifecycle", "weighted blend" konuşulur.

---

## 1. Purpose

A-I boyunca compiler tanımı şu kadarla sınırlı kaldı:
- WORLD_INGRESS §13 — iki katmanlı (bootstrap + learned), async, dedup allowed, aggregation forbidden
- WORLD_INGRESS §14 — örnek bootstrap mapping aileleri sözel
- WORLD_INGRESS §15 — learned_mappings M0 ingress_calibration_traces olarak yaşar
- BOOTSTRAP_GENOME §19 — bootstrap mapping aileleri kavramsal
- BOOTSTRAP_GENOME §20 — `ingress_calibration_traces: 0` doğumda

J bu boşluğu doldurur: **structured event → neural_seed dönüşümünün tam biçimsel sözleşmesi**.

Damıtma:

> **Compiler dünyayı anlamaz. Compiler duyusal olayı primer zihinsel tona çevirir.**
>
> **Adapter ham olay üretir. Compiler neural_seed üretir. Çekirdek sadece tonu yaşar.**

---

## 2. Constitutional Position — WORLD_INGRESS §13 Alt-spec'i

Bu belge yeni anayasa maddesi değildir; mevcut maddelerin compiler-level detayıdır:

- **Madde 1** (Nöron homojen, payload heterojen): Compiler primer payload üretir, kategori değil.
- **Madde 3** (Minimum genome): Compiler doğuştan minimum bootstrap rule set ile başlar.
- **Madde 6** (LLM dış tercüman): LLM mapping update yapamaz.
- **Madde 7** (Hafıza ayrılığı): Learned mappings M0'da yaşar, runtime config değil.
- **WORLD_INGRESS §13**: Deterministic ingress compiler ana mekanizma.
- **BOOTSTRAP_GENOME §19**: Bootstrap mapping aileleri doğuştan gelir.

---

## 3. Core Principle

> **Compiler classifier değildir.**
> **Compiler structured event'i deterministic mapping function'ları ile primer payload tonuna çevirir.**
> **Bootstrap mapping anayasaldır; learned mappings M0 dokusudur. İkisi de runtime config değildir.**

---

## 4. Compiler Is Not a Classifier

### Principle

Compiler **kategorize etmez**. "Bu event volatility high", "bu event news flash", "bu event human urgent" gibi semantic etiketler **üretmez**. Sadece compiler_input field'larından primer payload'lara mapping uygular.

### Rationale

Compiler classifier olursa:
- Gizli karar modülüne dönüşür (Madde 1 ihlali)
- Domain ontolojisi çekirdeğe sızabilir (Madde 3 ihlali)
- Semantic interpretation yargı içerir
- LLM-style attention modeline kayma riski

Doğru: deterministic mapping function'ları, boolean/sayısal koşullar, mekanik output.

### Allowed
- Bootstrap rule family pattern matching (condition band'lara göre)
- Learned mapping pattern matching (M0 ingress_calibration_traces)
- Scalar modulators (confidence, staleness, magnitude)
- Weighted blend across matching rules
- Cap'leme

### Forbidden
- "Bu event news flash" gibi semantic etiketleme
- Neural network classifier
- LLM-assisted interpretation
- Domain etiketi → payload mapping
- "Bu mantıklı" yargısı

### Violation Test
> *Compiler bir event'i semantic kategori olarak etiketliyor mu?*
>
> Evet ise ihlal.

---

## 5. Input Envelope and Allowed Fields

Compiler input olarak **`IngressEventEnvelope.compiler_input`** alır (WORLD_INGRESS §8). Şu field'lar allowed:

```
compiler_input common fields:
    confidence              # [0.0, 1.0]
    ttl_ms
    staleness_ms
    reliability_band
    ambiguity_or_uncertainty
    criticality_band
    profile_specific_scalars
```

Profile-specific allowed fields (her event class için ayrı):

```
ObservationEvent compiler_input:
    confidence, ttl_ms, staleness_ms,
    source_reliability_band,
    magnitude_normalized,
    change_rate_normalized,
    instability_normalized,
    coherence_with_recent_global,
    novelty_indicator,
    has_action_origin,
    expected_feedback_score,
    feedback_delay_ms

RecallEvent compiler_input:
    confidence, ttl_ms, staleness_ms,
    memory_status_band,
    retrieval_relevance,
    contradiction_risk,
    provenance_strength,
    criticality_band

HumanIntentEvent compiler_input:
    confidence, ambiguity_score,
    destructive_flag,
    scope_band, duration_band,
    urgency_claimed_by_human,
    requires_confirmation,
    ttl_ms, criticality_band

InternalShockEvent compiler_input:
    severity_band,
    violation_distance_band,
    blocked_intention_payload_signature,
    criticality_band,
    ttl_ms
```

### Forbidden inputs

- `observer_only` field'ları (event_id, source_adapter_id, subject_id, venue, raw_payload_ref, vs.)
- Domain etiketleri ("BTCUSDT", "Binance", "Fed")
- Adapter identity (name, domain_label)
- M2 raw content (RecallEvent için)
- LLM raw output (HumanIntentEvent için sadece parsed scalar fields)

### Kritik kural

> *Compiler observer_only field'larını okuyamaz. Compiler sadece compiler_input field'larından çalışır.*

---

## 6. Profile Visibility and Authority Matrix

### Profile visibility

```
event_profile compiler tarafından görülür (kural seçimi için).
event_profile core-facing neural_seed'e flag olarak GİREMEZ.
```

Yani compiler "bu HumanIntentEvent" diye kural seçer ama neural_seed içeriğine "human-origin" flag'i koymaz. Çekirdek hangi profile'dan geldiğini bilmez, sadece tonu yaşar.

### Authority matrix (WORLD_INGRESS §7'den taşınan)

| Event profile | bootstrap_rules | learned_mappings | outcome feedback |
|---------------|-----------------|-------------------|------------------|
| `ObservationEvent` | ✅ | ✅ açık | ✅ tam |
| `RecallEvent` | ✅ | ✅ kısıtlı | ✅ kısıtlı |
| `HumanIntentEvent` | ✅ | ❌ **kapalı** | ❌ |
| `InternalShockEvent` | ✅ | ❌ **kapalı, deterministik** | ❌ |

### Kritik kurallar

- **HumanIntentEvent learned_mappings KAPALI:** LLM zamanla compiler tonunu şekillendirmemeli (Madde 6)
- **InternalShockEvent learned_mappings KAPALI:** Deontic shock kendi şiddetini öğrenerek kaymasın (Madde 5)
- **RecallEvent learned_mappings KISITLI:** staleness/provenance ağırlığı sert, candidate recall capped (H §13)

### Forbidden

- Profile visibility'nin core'a sızması
- Authority matrix runtime'da değişmesi (belge revizyonu zorunlu)
- HumanIntent veya InternalShock için learned_mappings update

---

## 7. Output: neural_seed Only

### Principle

Compiler çıkışı tek zarftır:

```
compiler_output
└── neural_seed
    ├── payload_seed          # mandatory — primer palette üzerinde dağılım
    ├── receptor_bias_seed    # optional, bounded
    └── trace_seed            # optional, bounded
```

### compiler_output YAPMAZ

- Assembly oluşturmak
- Pulse oluşturmak
- Intent oluşturmak
- Memory write candidate önermek
- Gate kararı vermek
- Core-facing flag/etiket eklemek

Sadece **nöral uyarı tohumu** üretir. Sonrası normal nöral akış (Madde 4).

### Output normalization

`neural_seed.payload_seed` toplam intensity profile-specific cap ile sınırlı (bkz. §12).

### Violation Test
> *Compiler `neural_seed` dışında core-facing output üretiyor mu?*
>
> Evet ise ihlal.

---

## 8. Bootstrap Rule Family Format

### RuleFamily yapısı

```
RuleFamily
├── rule_family_id
├── rule_family_name              # human-readable, audit için
├── applies_to_profiles           # [observation, recall, ...] subset
├── condition_band                # bkz. §9
├── base_payload_vector           # primer palette delta'ları
├── scalar_modifiers              # confidence, staleness, vb. çarpanlar
├── caps                          # per-payload + total intensity cap
├── status                        # active | deprecated | archived (§17)
└── version
```

### Örnek RuleFamily (sözel, kavramsal)

```
rule_family_id: fresh_high_magnitude_novelty
rule_family_name: "fresh strong novelty surge"
applies_to_profiles: [ObservationEvent]

conditions:
    magnitude_band ∈ {high, critical}
    novelty_band ∈ {high}
    confidence_band ∈ {medium, high}
    staleness_band ∈ {fresh}

base_payload_vector:
    novelty: +medium
    urgency: +low_to_medium
    suspicion: +low

scalar_modifiers:
    urgency *= confidence_modifier
    fatigue_trace *= staleness_modifier  # ters etki: fresh ise düşük

caps:
    per_payload_max: profile_cap
    total_intensity_max: profile_total_cap
```

### Kritik notlar

- Bu format **kavramsal**; kesin sayısal değerler `INGRESS_COMPILER_NUMERICS.md` veya implementation
- `base_payload_vector` primer paleti dışına çıkamaz (`urgency`, `suspicion`, `novelty`, vs.; yeni payload tipi yok)
- `scalar_modifiers` sadece compiler_input field'larına bağlı
- `caps` payload intensity sınırı

### Forbidden

- Rule family'de domain etiketi (`btc_volatility`, `fed_event`)
- Yeni primer payload tipi
- Semantic etiket çıkışı
- Hardcoded sayısal değer (NUMERICS belgesine devir)

---

## 9. Condition Bands and Scalar Modifiers

### Condition band'lar

Her compiler_input field'ı **band'lara** ayrılır:

```
magnitude_band:    {low, medium, high, critical}
confidence_band:   {very_low, low, medium, high}
staleness_band:    {fresh, recent, stale, very_stale}
novelty_band:      {none, low, medium, high}
reliability_band:  {very_low, low, medium, high}
criticality_band:  {routine, elevated, high, critical}
ambiguity_band:    {clear, slight, moderate, high, very_high}
```

Band sınırları `INGRESS_COMPILER_NUMERICS.md` konusu.

### Rule conditions

Rule conditions band membership'le ifade edilir:

```
conditions:
    magnitude_band ∈ {high, critical}
    confidence_band ∈ {medium, high}
    staleness_band ∈ {fresh}
```

Tüm conditions **AND** ile bağlıdır. Bir rule eşleşirse, payload_vector katkı verir.

### Scalar modifiers

Compiler_input field'ları **çarpan** olarak da kullanılabilir:

```
urgency *= (confidence × novelty_factor)
fatigue_trace *= (1 - freshness_factor)
suspicion *= staleness_modifier
```

Modifier formüllerinin kesin hali NUMERICS konusu. Burada sadece **kuralın yapısı** anayasal.

### Forbidden

- Continuous threshold yargısı ("magnitude > 0.83 ise...")
- Non-band conditions
- Semantic conditions ("event tipi news ise...")
- Cross-event conditions ("önceki event şuysa...")

---

## 10. Payload Seed Composition

### Compose mekaniği

```
1. Find all matching RuleFamilies (active status) for event_profile
2. For each matching rule:
   delta_i = rule.base_payload_vector × rule.scalar_modifiers(event)
3. Aggregate: total_delta = sum(delta_i for i in matching rules)
4. Apply per-payload cap: clipped_delta = min(total_delta, per_payload_cap)
5. Apply total intensity cap: 
   if total intensity > profile_total_cap:
       scale down proportionally
6. neural_seed.payload_seed = clipped_delta
```

### Critical kural — weighted blend, semantic winner değil

> *Weighted blend hakikat veya öncelik kararı değildir.*
> *Sadece eşleşen rule family katkılarının mekanik toplamıdır.*

Bkz. §16 detay.

### Empty matching set

Hiç rule eşleşmezse:
- **Core-facing `neural_seed` üretilmez.**
- Çekirdeğe boş veya sıfır-tonlu duyusal event basılmaz.
- M1'e `INGRESS_NO_RULE_MATCH` event yazılır (audit).
- Event observer/provenance tarafında görünür kalır.
- Bu durum **debug/audit sinyalidir**, core stimulus değildir.

H §16'daki `RECALL_RESULT_EMPTY` pattern'iyle tutarlı: failure audit edilir, çekirdeğe "yokluk payload'ı" basılmaz. Eğer yokluk basıncı gerekirse (örn. uzun süre input gelmiyor), bu dolaylı olarak self-field / contradiction / unresolved_intention tarafında doğal yaşanır — ingress üzerinden değil.

### Forbidden

- Empty match için default payload (örn. "her event en az suspicion 0.1") — yargı
- Match seçim sırasında semantic yorum
- Implicit payload (kuralın deklare etmediği primer'a katkı)

---

## 11. Receptor Bias Seed and Trace Seed

`neural_seed.receptor_bias_seed` ve `neural_seed.trace_seed` opsiyonel bileşenler:

### `receptor_bias_seed`

Hedef nöronların receptor profile'ına geçici bias verir. Bazı assembly'lerin payload'a karşı duyarlılığını anlık modüle eder.

```
receptor_bias_seed:
    target_assemblies: [optional list]  # genelde tüm receptor'lar
    bias_vector: {payload: delta}
    duration_ms                          # ne kadar sürer
```

### `trace_seed`

Eligibility trace başlangıç durumunu modüle eder. Replay engine için marker.

```
trace_seed:
    eligibility_modifier
    target_trace_scope: {fast, medium, slow}
    boost_factor
```

### Kritik

- İkisi de **optional**, bootstrap rule'da deklare edilmiş olmalı
- Implicit olarak üretilmezler
- `payload_seed` ile aynı cap'lere tabi
- Bootstrap rule'ların çoğu sadece `payload_seed` üretir; `receptor_bias_seed` ve `trace_seed` özel durumlar için

### Forbidden

- `receptor_bias_seed` veya `trace_seed`'in `payload_seed` olmadan tek başına üretilmesi
- Bunların gate kararına etki etmesi
- Duration_ms sınırsız

---

## 12. Payload Intensity Caps and Normalization

### Principle

> *Hybrid bounded raw.*
> *No event may force unbounded payload intensity.*
> *No normalization may erase weak/strong event distinction.*

### Cap mekaniği

```
profile_intensity_cap[event_profile]:
    ObservationEvent: variable cap (typical, magnitude-dependent)
    RecallEvent: lower cap (verified) / capped intensity (candidate ~30%)
    HumanIntentEvent: capped medium-low
    InternalShockEvent: deterministic critical cap (high but bounded, no spam)
```

### Normalization

```
if sum(payload_seed values) > profile_intensity_cap:
    scale_factor = profile_intensity_cap / sum(payload_seed values)
    payload_seed = payload_seed × scale_factor
```

Yani:
- Zayıf event zayıf gelir (raw intensity korunur)
- Kritik event yüksek gelir ama profile cap aşılamaz
- Cap aşılırsa proportional scaling — relative balance korunur

### Cross-document tutarlılık

- **RecallEvent candidate** intensity ~%30 (H §13)
- **InternalShockEvent** payload_seed primer palette üzerinde sınırlı karışım (C §12)
- **HumanIntentEvent** capped medium-low (Madde 6 koruması)

### Forbidden

- Unbounded payload_seed
- Tam normalization (her event aynı total → weak/strong erezi)
- Relative balance bozan asymmetric clipping
- Cap'in runtime'da değişmesi

---

## 13. Learned Mappings as M0 Ingress Calibration

### Principle

Learned mappings **M0 ingress_calibration_traces** olarak yaşar (WORLD_INGRESS §15, BOOTSTRAP_GENOME §20). Runtime config, M2 record veya adapter manifest **değildir**.

### Yapı

```
IngressCalibrationTrace
├── trace_id
├── linked_rule_family_id           # hangi bootstrap rule'a bağlı
├── event_profile
├── input_signature_band            # condition band'ları içeriyor
├── payload_delta_vector            # bootstrap rule'a göre delta
├── eligibility_trace
├── outcome_alignment_score
├── replay_survival_score
├── false_positive_count
├── false_negative_count
├── last_updated_at
├── update_rate_cap_ref
└── status                          # active | frozen | archived (rule lifecycle ile bağlı)
```

### M0 alt-tipi

M0'da yaşayan alt-türlerden biri (BOOTSTRAP_GENOME §15):

```
M0:
├── synaptic_memory
├── assembly_stability_traces
├── self_field_weights
├── attention_habituation_traces
└── ingress_calibration_traces   ← burada
```

### Kim yazar/okur

- **Sistem otomatik öğrenme** (STDP-benzeri + outcome + replay): writer
- **Compiler runtime evaluation**: reader (rule family + linked trace ile blend yapar)
- **Observer**: indirect (her update için meta-event yazar)
- **Çekirdek doğrudan**: hayır (sadece etkisini yaşar)
- **İnsan, LLM, adapter**: hayır (Madde 1/3/6/7 koruması)

### Forbidden

- Config dosyasından runtime trace update
- Panel/LLM/adapter direct write
- Trace'in M0 dışında yaşaması
- "Mapping hot reload"

---

## 14. Mapping Update Requirements

### Update tetikleyicileri

Learned mapping update **sadece** şu koşullarda yapılabilir:

```
update_allowed if:
    outcome_alignment exists                      # gerçek outcome geldi
    OR replay_survival exists                      # counterfactual test geçti

update_forbidden if:
    only "LLM bu yorumla aktif" sinyali var
    only human "böyle olsun" diyor
    only adapter "böyle gönderiyorum" diyor
    only pulse repetition
    only recall repetition
```

### Update direction

```
positive strengthening:
    pattern X → payload_seed Y mapping doğru çıktı
    → payload_delta_vector güçlenir
    → rate: slow

false-positive dampening:
    pattern X → payload_seed Y mapping false alarm üretiyor
    → payload_delta_vector zayıflar
    → rate: faster than strengthening
```

### Critical kural — asymmetric rates

> *False-positive dampening may be faster than positive strengthening, but neither may bypass rate caps or replay/outcome evidence.*

Sebep: yanlış pozitif sensory tone sistemi bozar (örn. her yüksek magnitude → urgency mapping fazla güçlenirse panik yaratır). Düzeltme hızlı olmalı; ama her update yine de **evidence-bound** ve **rate-capped**.

### Audit

Her update M1'e `COMPILER_MAPPING_UPDATED` event:

```
CompilerMappingUpdatedEvent
├── event_id
├── trace_id
├── rule_family_id
├── update_direction       # strengthening | dampening
├── delta_magnitude
├── evidence_refs          # outcome/replay event refs
├── update_reason
├── new_payload_delta_vector
└── observer_snapshot_ref
```

### Forbidden

- Evidence'sız update
- Cap bypass
- LLM/human/adapter direct update
- Audit'siz update

> *Ingress calibration update'in replay session içindeki yeri (ingress_calibration_update channel), counterfactual ablation kuralları ve audit zinciri için bkz. [`REPLAY_PROTOCOL.md`](./REPLAY_PROTOCOL.md) §12.*

---

## 15. Rate Limiting and Drift Control

### Rate caps (kavramsal)

```
per_mapping_daily_delta_cap:
    Bir trace_id günde maks N delta birimi alabilir

per_payload_delta_cap:
    Bir payload kategorisi için günde maks M delta birimi

global_compiler_drift_cap:
    Tüm compiler için günlük toplam delta sınırı

profile_specific_cap:
    Her event_profile için ayrı cap
    HumanIntent / InternalShock için cap = 0 (öğrenme yok)
```

### Drift detection

Sistem `global_compiler_drift_cap`'i aşan toplam aktivite gözlerse:
- Pause compiler updates
- M1'e `COMPILER_DRIFT_WARNING` event (yeni — gerekirse eklenir)
- Human review için işaretlenir

### Drift audit zorunluluğu

> *Compiler drift audit edilir.*

Sistem sonradan şunları cevaplayabilmeli:
- Hangi rule family için hangi yönde drift oldu?
- Hangi outcome/replay event'leri drift'i tetikledi?
- Drift hız limiti aşıldı mı?
- Hangi update'lar reject edildi?

Cevap verilemiyorsa compiler auditable değildir.

### Forbidden

- Cap bypass
- Drift cap'inin runtime'da değişmesi
- Pause sırasında silent update

---

## 16. Conflict Resolution: Weighted Blend

### Principle

Birden fazla rule family aynı event'e uyarsa **weighted blend** uygulanır. **Semantic winner seçimi yapılmaz.**

### Mekanik

```
matching_rules = [r for r in (bootstrap_rules + learned_mappings)
                  if r.status == active 
                  AND r.conditions_match(event)
                  AND event.event_profile IN r.applies_to_profiles]

aggregated_delta = sum(
    rule.base_payload_vector × rule.scalar_modifiers(event)
    for rule in matching_rules
)

neural_seed.payload_seed = apply_caps(aggregated_delta, profile_caps[event_profile])
```

### Kritik kural

> *Weighted blend hakikat veya öncelik kararı değildir.*
> *Sadece eşleşen rule family katkılarının mekanik toplamıdır.*

### Forbidden alternatives

```
❌ "En spesifik rule kazanır" (condition_band sayısı en yüksek)
   → örtük öncelik kararı, yargı içerir

❌ "En son tetiklenmiş rule"
   → temporal yargı

❌ "En güvenilir rule"
   → semantic yargı

❌ "LLM hangisini önerirse o"
   → Madde 6 ihlali
```

### Allowed

- Mekanik aggregation + cap
- Audit log her matching rule'u kaydeder

### Violation Test
> *Conflict resolution "hangi rule daha mantıklı / daha spesifik / daha güvenilir" diye semantik seçim yapıyor mu?*
>
> Evet ise ihlal.

---

## 17. Rule Family Lifecycle

### Statüler

```
active        # compiler değerlendirmesine girer
    ↓ (belge revizyonu ile)
deprecated    # compiler değerlendirmesine girmez
    ↓ (cleanup)
archived      # sadece audit için
```

### Statü özellikleri

| Statü | Compiler evaluation | Linked traces | Audit |
|-------|---------------------|---------------|-------|
| `active` | ✅ değerlendirilir | normal update alır | M1 var |
| `deprecated` | ❌ değerlendirmeye girmez | **frozen** (yeni update yok) | M1 var, history kalır |
| `archived` | ❌ | dondurulmuş, salt-okunur | sadece audit history |

### Geçişler

```
active → deprecated: belge revizyonu (BOOTSTRAP §23 safety_tightening)
deprecated → archived: cleanup window sonrası
active → active (version): yeni rule_family_id ile yeni version
```

### Frozen traces

`deprecated` rule family'sine bağlı `IngressCalibrationTrace`'lar:
- Yeni update **almazlar**
- Compiler evaluation'a **girmezler**
- M0'da kalır (audit), ama aktif değildir
- Migration için gerekirse manuel read-only erişim

### Kritik kural

> *Deprecated rule family compiler evaluation'a girmez; sadece migration/audit penceresinde görünür.*
>
> *Deprecated/archived rule family audit'te kalır; sessizce silinmez.*

### Canonical event

```
COMPILER_RULE_FAMILY_STATUS_CHANGED
```

Şema:

```
CompilerRuleFamilyStatusChangedEvent
├── event_id
├── rule_family_id
├── old_status            # active | deprecated | archived
├── new_status
├── reason                # document_revision | cleanup | superseded
├── superseding_rule_family_id (optional)
├── approved_by
├── linked_traces_count
└── observer_snapshot_ref
```

Bu event `COMPILER_MAPPING_UPDATED`'tan **ayrı** (farklı nedensel mekanizma):
- `COMPILER_MAPPING_UPDATED`: learned mapping delta / calibration trace update
- `COMPILER_RULE_FAMILY_STATUS_CHANGED`: rule family lifecycle statü değişimi

Event type vs field disiplini uyumlu (F).

### Open Question

Cleanup window süresi (deprecated → archived geçişi için)? — Implementation konusu.

---

## 18. Dedup Allowed, Aggregation Forbidden

WORLD_INGRESS §13'teki kuralın compiler-level netleşmesi:

### Allowed

```
Deduplication:
    same observation_id_hash
    same raw payload
    network retry
    → biri elenir, biri compile edilir
```

### Forbidden

```
Aggregation:
    Binance + BTCTurk + news → "market_state = flash_crash"
    multi-source pre-merge → "doğru dünya budur"
    semantic aggregation
    cross-source reconciliation
```

### Akış

```
3 ObservationEvent aynı anda gelir
    ↓
3 ayrı compiler invocation
    ↓
3 ayrı neural_seed
    ↓
çekirdeğe ardışık olarak akar
    ↓
çelişki (varsa) çekirdek içinde yaşanır
```

Bkz. WORLD_INGRESS §21 Multi-Source Conflict.

### Forbidden

- Pre-ingress aggregator
- Batch compilation (her event ayrı)
- Source uzlaştırma

---

## 19. Compiler Events

### Canonical event'ler

```
COMPILER_MAPPING_UPDATED                    # learned mapping delta / calibration update
COMPILER_RULE_FAMILY_STATUS_CHANGED         # rule family lifecycle
COMPILER_DRIFT_WARNING                      # global drift cap aşıldı (opsiyonel)
INGRESS_NO_RULE_MATCH                       # hiç matching rule yok (opsiyonel audit)
```

### Permanence policy

```
(COMPILER_MAPPING_UPDATED, *)                              → permanent
(COMPILER_RULE_FAMILY_STATUS_CHANGED, *)                   → permanent
(COMPILER_RULE_FAMILY_STATUS_CHANGED, new_status=archived) → permanent_with_snapshot
(COMPILER_DRIFT_WARNING, *)                                → permanent + human_alert
(INGRESS_NO_RULE_MATCH, *)                                 → ring_buffer_only
```

OBSERVER_LEDGER §10 permanence policy buna göre güncellenir.

### Family

```
COMPILER_MAPPING_UPDATED                    → ingress family
COMPILER_RULE_FAMILY_STATUS_CHANGED         → ledger_meta family (artifact lifecycle)
COMPILER_DRIFT_WARNING                      → ingress family
INGRESS_NO_RULE_MATCH                       → ingress family
```

---

## 20. Cross-document Anchors

| Belge | Bağlantı |
|-------|----------|
| `WORLD_INGRESS.md` §13 (Deterministic Ingress Compiler) | Ana mekanizma tanımı |
| `WORLD_INGRESS.md` §14 (Bootstrap Rules) | Bootstrap mapping aileleri kavramsal |
| `WORLD_INGRESS.md` §15 (Learned Mappings) | M0 ingress_calibration_traces |
| `WORLD_INGRESS.md` §8 (IngressEventEnvelope) | compiler_input field'ları |
| `BOOTSTRAP_GENOME.md` §19 (Ingress Bootstrap Mapping Families) | Doğuştan rule familyleri |
| `BOOTSTRAP_GENOME.md` §20 (Initial Memory State M0) | `ingress_calibration_traces: 0` doğumda |
| `BOOTSTRAP_GENOME.md` §15 (M0 alt-türleri) | Ingress calibration trace M0 içinde |
| `MEMORY_CONTRACT.md` §14 (Replay engine M0 etkisi) | Replay-based mapping update |
| `OBSERVER_LEDGER_SCHEMA.md` §10 (Permanence Policy) | Compiler event permanence |
| `OBSERVER_LEDGER_SCHEMA.md` §19 (Event Catalog) | Ingress + ledger_meta families |
| `ADAPTER_MANIFEST_SPEC.md` §15 (Raw Payload vs Neural Seed) | Adapter neural_seed üretemez |
| `RECALL_PROTOCOL.md` §11 (RecallEvent Schema) | RecallEvent compiler_input |
| `ATTENTION_WORKSPACE.md` §11 (Context Signature) | İç durum imzası — compiler dış etiketi sızdırmaz |

---

## 21. Violation Tests

1. **Compiler classifier davranıyor mu?** (§4)
   - Evet ise ihlal.
2. **Compiler semantic category üretiyor mu?** (§4, §10)
   - Evet ise ihlal.
3. **Compiler `neural_seed` dışında core-facing output üretiyor mu?** (§7)
   - Evet ise ihlal.
4. **event_profile core'a sızıyor mu?** (§6)
   - Evet ise ihlal.
5. **Adapter neural_seed üretiyor mu?** (ADAPTER_MANIFEST §15)
   - Evet ise ihlal.
6. **LLM mapping update yapabiliyor mu?** (§13, §14)
   - Evet ise ihlal.
7. **Human mapping update yapabiliyor mu?** (§13, §14)
   - Evet ise ihlal.
8. **HumanIntentEvent learned_mappings kullanıyor mu?** (§6)
   - Evet ise ihlal.
9. **InternalShockEvent learned_mappings kullanıyor mu?** (§6)
   - Evet ise ihlal.
10. **Mapping update outcome/replay evidence olmadan yapılabilir mi?** (§14)
    - Evet ise ihlal.
11. **Pulse/attention mapping evidence sayılıyor mu?** (§14)
    - Evet ise ihlal.
12. **Learned mapping M0 dışında bir yerde yaşıyor mu?** (§13)
    - Evet ise ihlal. Sadece M0 ingress_calibration_traces.
13. **Compiler drift rate cap'siz mi?** (§15)
    - Evet ise ihlal.
14. **Conflict resolution semantic winner seçimi yapıyor mu?** (§16)
    - Evet ise ihlal. Weighted blend + cap.
15. **Payload intensity unbounded mu?** (§12)
    - Evet ise ihlal.
16. **Domain etiketi core-facing rule veya output olarak görünüyor mu?** (§4, §8)
    - Evet ise ihlal.
17. **Deprecated/archived rule family sessizce siliniyor mu?** (§17)
    - Evet ise ihlal. Audit'te kalır.
18. **Aggregation yapılıyor mu (multi-source pre-merge)?** (§18)
    - Evet ise ihlal. Dedup serbest, aggregation yasak.
19. **No-rule-match durumunda çekirdeğe empty/zero payload event gönderiliyor mu?** (§10)
    - Evet ise ihlal. Audit M1'de kalır; core'a yokluk/boş ton basılmaz.

---

## 22. Open Questions

J çerçevesi kapanırken cevaplanmamış bırakılan sorular:

- **Kesin band sınırları** (magnitude_band, confidence_band, vs.) → `INGRESS_COMPILER_NUMERICS.md`
- **Bootstrap rule katsayıları** (base_payload_vector büyüklükleri) → `INGRESS_COMPILER_NUMERICS.md`
- **Profile-specific intensity caps sayısal değerleri** → `INGRESS_COMPILER_NUMERICS.md`
- **Rate cap sayısal değerleri** (per_mapping_daily_delta_cap, vs.) → `INGRESS_COMPILER_NUMERICS.md`
- **Drift detection threshold** → Implementation
- **Cleanup window süresi** (deprecated → archived) → Implementation
- **Update direction asymmetry ratio** (false-positive dampening / strengthening rate oranı) → Implementation
- **`INGRESS_NO_RULE_MATCH` event'inin gerçekten gerekli olup olmadığı** — debug için yararlı ama production'da gürültü olabilir
- **Rule family versioning** — yeni version registered olduğunda eski active kalır mı, otomatik deprecated mi?

Bu sorular cevaplanmadan implementation aşamasına geçilmez.

---

## Çekirdek özet — 13 karar + 18 violation tests

### 13 karar
1. Compiler classifier değildir; deterministic mapping function uygular.
2. Output tek zarftır: `neural_seed`.
3. event_profile compiler tarafından görülür, core'a sızmaz.
4. Authority matrix: Observation açık / Recall kısıtlı / HumanIntent kapalı / InternalShock kapalı.
5. RuleFamily format: condition_band + base_payload_vector + scalar_modifiers + caps.
6. Bootstrap rules anayasal; learned mappings M0 ingress_calibration_traces.
7. Mapping update sadece outcome/replay evidence ile.
8. Rate cap'ler zorunlu; drift audit edilir.
9. Asymmetric rates: false-positive dampening > positive strengthening, ama ikisi de capped.
10. Conflict resolution = weighted blend + cap (semantik winner yok).
11. Payload intensity hybrid bounded raw (raw + profile cap).
12. Rule family lifecycle: active / deprecated / archived; deprecated traces frozen.
13. Dedup allowed, aggregation forbidden.

---

## Kilit cümleler

> **Compiler dünyayı anlamaz. Compiler duyusal olayı primer zihinsel tona çevirir.**
>
> **Adapter ham olay üretir. Compiler neural_seed üretir. Çekirdek sadece tonu yaşar.**
>
> **Compiler classifier değildir. Compiler structured event'i deterministic mapping function'ları ile primer payload tonuna çevirir.**
>
> **Bootstrap mapping anayasaldır; learned mappings M0 dokusudur.**
>
> **Weighted blend hakikat veya öncelik kararı değildir. Sadece eşleşen rule family katkılarının mekanik toplamıdır.**
>
> **No event may force unbounded payload intensity. No normalization may erase weak/strong event distinction.**
>
> **False-positive dampening may be faster than positive strengthening, but neither may bypass rate caps or evidence requirements.**
>
> **Deprecated rule family audit'te kalır; sessizce silinmez.**

---

## Versiyon

- **v0.1** — 18 Mayıs 2026 — Frozen Draft. Conceptual phase. No implementation authority.
- `WORLD_INGRESS.md` §13 alt-spec'i.
- A-I belgelerinin compiler-level sözleşmesi.
- Konuşma soyağacı: [`docs/conversations/0010-ingress-compiler-spec.md`](./docs/conversations/0010-ingress-compiler-spec.md)
