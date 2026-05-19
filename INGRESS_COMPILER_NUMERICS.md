# INGRESS_COMPILER_NUMERICS.md

## Sentinel — Ingress Compiler Numeric Sözleşmesi

---

## Status

**Frozen Draft v0.1**
**Conceptual phase. No implementation authority.**

Bu belge `INGRESS_COMPILER_SPEC.md`'nin (J) numerics artifact'idir. `NUMERICS_GOVERNANCE.md`'nin (M) tüm meta-kurallarına uyar. Çalışan bir compiler implementation'ının kesin sayısal değerlerini vermez — **conceptual band ranges ve cap formatları** verir; production değerleri ayrı **signed numerics artifact** (örn. `ingress_compiler_numerics_v1.signed.json`).

`spec_family: ingress_compiler`.

---

## 1. Purpose

J (INGRESS_COMPILER_SPEC) compiler sözleşmesini yazdı: structured event → neural_seed dönüşümü, RuleFamily format, weighted blend, learned mapping M0 traces. Ama gerçek **numerical band/cap** yoktu:

- Hangi `magnitude` değeri `high` band'a düşer?
- `ObservationEvent` neural_seed cap'i ne?
- `HumanIntentEvent` ne kadar zayıf kalmalı?
- `InternalShockEvent` ne kadar güçlü ama spam-proof?
- Learned mapping günlük ne kadar kayabilir?

N bu sayısal sınırları verir.

Damıtma:

> **Ingress compiler numerics, dış dünyanın çekirdeğe hangi şiddette dokunabileceğinin sayısal sözleşmesidir.**
>
> **Dünya güçlü olabilir. Ama hiçbir dış kanal çekirdeğe sınırsız ton basamaz.**
>
> **Adapter raw event üretir. Compiler neural_seed üretir. Numerics compiler'ın duyusal şiddet sınırlarını belirler.**

---

## 2. Governance Position — NUMERICS_GOVERNANCE + INGRESS_COMPILER_SPEC

Bu belge:
- **NUMERICS_GOVERNANCE.md** (M) meta-spec'ine **zorunlu uyar**: NumericEntry no-default, directionality metadata, dependency declarations, signed artifact + M2 reference, Memory Write Gate üzerinden update
- **INGRESS_COMPILER_SPEC.md** (J) §13-15'in numerics tarafı
- **WORLD_INGRESS.md** (C) §13 compiler ve §14 bootstrap mapping families ile uyumlu
- **BOOTSTRAP_GENOME.md** (D) §19 ingress bootstrap mapping families ile bağlantılı

### Numerics family classification

```
spec_family: ingress_compiler
numeric_risk_family: çoğunlukla safety_critical veya calibration_bands
                    (bazı sub-entries operational_convenience)
```

---

## 3. Core Principle

> **N kuralı koyar, signed artifact değeri verir.**
>
> **Static numerics learned trace'in sınırıdır. Learned trace static numeric değildir.**
>
> **Weak events must remain weak. Strong events may be capped, but weak events must not be normalized upward.**

---

## 4. Numeric Artifact Metadata

Bu belge **conceptual numerics** içerir. Production kesin değerleri **external signed artifact**'te:

```
ingress_compiler_numerics_v0.1.signed.json
    spec_family: ingress_compiler
    spec_ref:
        source_document: INGRESS_COMPILER_NUMERICS.md
        source_document_hash: <hash>
        section_ref: relevant §
    signed_by: <authority>
```

N belgesi:
- Format, kategori, hierarchy, dependency, validation kurallarını **anayasal** olarak verir
- Conceptual band ranges (yaklaşık değerler) örnekler
- Kesin sayısal değerler signed artifact'te

---

## 5. Input Band Families

Compiler input fieldlarının band aileleri (WORLD_INGRESS §9'daki ObservationEvent.compiler_input + diğer profile'lar üzerinden):

### Universal bands (tüm profile'larda):
```
confidence_band:       very_low | low | medium | high
staleness_band:        fresh | recent | stale | very_stale
criticality_band:      routine | elevated | high | critical
ambiguity_band:        clear | slight | moderate | high | very_high
reliability_band:      very_low | low | medium | high
```

### ObservationEvent-specific bands:
```
magnitude_band:        low | medium | high | critical
change_rate_band:      stable | slow | moderate | rapid | extreme
instability_band:      stable | mild | unstable | turbulent
novelty_band:          none | low | medium | high
coherence_band:        coherent | moderate | weak | incoherent
```

### RecallEvent-specific bands:
```
memory_status_band:    candidate | verified | active | superseded | expired | quarantined | rejected
retrieval_relevance_band: low | medium | high
contradiction_risk_band: none | low | medium | high
provenance_strength_band: weak | medium | strong | verified_signed
```

### HumanIntentEvent-specific bands:
```
destructive_flag:      false | true
scope_band:            narrow | moderate | broad
duration_band:         instant | short | sustained
urgency_claimed_by_human: none | low | medium | high
requires_confirmation: false | true
```

### InternalShockEvent-specific bands:
```
severity_band:         low | medium | high | critical
violation_distance_band: marginal | close | crossed | bypass_attempt
```

---

## 6. Band Cutoff Format

### Principle

> **Soft overlap is deterministic interpolation, not semantic judgment.**

Hard threshold yok (ani geçişler), fuzzy logic yok (yorum), LLM yok (yargı). **Deterministic membership function** ile bandlar arası soft overlap.

### Format

Her band için iki zone:

```
band_definition:
    full_membership: [lower, upper]      # band'ın "tam" üyelik aralığı
    fade_in:         [start, lower]       # alt band'dan bu band'a geçiş zonu
    fade_out:        [upper, end]         # bu band'dan üst band'a geçiş zonu
```

### Örnek (confidence_band) — conceptual

```
confidence.very_low:
    full_membership: [0.00, 0.15]
    fade_out:        [0.15, 0.25]

confidence.low:
    fade_in:         [0.15, 0.25]
    full_membership: [0.25, 0.45]
    fade_out:        [0.45, 0.55]

confidence.medium:
    fade_in:         [0.45, 0.55]
    full_membership: [0.55, 0.75]
    fade_out:        [0.75, 0.85]

confidence.high:
    fade_in:         [0.75, 0.85]
    full_membership: [0.85, 1.00]
```

Bu değerler **conceptual** — production kesin değerleri signed artifact'te.

### Each cutoff is a NumericEntry

M'nin no-default kuralı: her cutoff **ayrı** NumericEntry olarak metadata taşır.

```
NumericEntry örneği:
    key: ingress_compiler.confidence.medium.full_membership_lower
    value: 0.55
    unit: ratio
    allowed_range: {min: 0.40, max: 0.65}
    directionality: bidirectional_sensitive   # band sınırı her iki yön de behavior change
    change_class_if_increased: safety_weakening
    change_class_if_decreased: safety_weakening
    dependencies:
        - target_key: ingress_compiler.confidence.low.full_membership_upper
          relationship: must_be_greater_than_or_equal
        - target_key: ingress_compiler.confidence.medium.full_membership_upper
          relationship: must_be_less_than
    numeric_risk_family: calibration_bands
    spec_family: ingress_compiler
    owning_spec_ref: "INGRESS_COMPILER_NUMERICS.md §6"
```

### Critical dependency invariants

Her band için zorunlu invariants (artifact validation):

```
band[X].full_membership_lower <= band[X].full_membership_upper
band[X].fade_in.start <= band[X].full_membership_lower
band[X].fade_out.end >= band[X].full_membership_upper
band[X-1].fade_out overlaps band[X].fade_in    # soft overlap continuity
```

### Forbidden

- Çıplak cutoff sayıları (NumericEntry metadata olmadan)
- Gap'li band'lar (iki band arası "tanımsız" alan)
- Overlapping full_membership zone'ları
- Hard threshold (fade_in/fade_out olmadan)

---

## 7. Profile-Specific Intensity Caps

Her event profile farklı intensity cap taşır. Conceptual relative values:

```
profile_cap.ObservationEvent:    ~1.00    # base normalize scale
profile_cap.InternalShockEvent:  ~0.90    # güçlü ama refractory-protected
profile_cap.RecallEvent (verified): ~0.60    # hatırlatma, gerçek değil
profile_cap.HumanIntentEvent:    ~0.35    # insan/LLM kanalı zayıf
profile_cap.RecallEvent (candidate): ~0.20    # doğrulanmamış
```

Production değerleri signed artifact'te.

### Cap interpretation

`profile_cap` = `payload_seed.total_intensity` için max sum:

```
sum(payload_seed[*]) <= profile_cap[event_profile]
```

### NumericEntry örneği

```
NumericEntry:
    key: ingress_compiler.profile_cap.HumanIntentEvent
    value: 0.35
    unit: ratio
    allowed_range: {min: 0.10, max: 0.50}
    directionality: lower_is_stricter
    change_class_if_increased: safety_weakening
    change_class_if_decreased: safety_tightening
    requires_human_approval: true
    dependencies:
        - target_key: profile_cap.RecallEvent
          relationship: must_be_less_than_or_equal
        - target_key: profile_cap.CandidateRecall
          relationship: must_be_greater_than_or_equal
    numeric_risk_family: safety_critical
    spec_family: ingress_compiler
    owning_spec_ref: "INGRESS_COMPILER_NUMERICS.md §7"
```

---

## 8. Profile Cap Hierarchy

### Anayasal hiyerarşi

```
profile_cap.ObservationEvent >= profile_cap.InternalShockEvent
profile_cap.InternalShockEvent >= profile_cap.RecallEvent (verified)
profile_cap.RecallEvent (verified) >= profile_cap.HumanIntentEvent
profile_cap.HumanIntentEvent >= profile_cap.RecallEvent (candidate)
```

### Rationale

- **Observation** = gerçek dış olay → en üst (dünyanın asıl sesi)
- **InternalShock** = kritik action sonucu → çok güçlü ama dünyayı örtemez
- **Recall (verified)** = hatırlatma → gerçek değil (H §4)
- **HumanIntent** = insan/LLM kanalı → Madde 6 koruması (LLM çekirdeği şekillendiremez)
- **Recall (candidate)** = doğrulanmamış → en sınırlı (H §13)

### Dependency declarations (zorunlu)

Hierarchy invariant her NumericEntry'de **dependency** olarak kayıtlı:

```
NumericEntry: profile_cap.ObservationEvent
    dependencies:
        - target_key: profile_cap.InternalShockEvent
          relationship: must_be_greater_than_or_equal
        - target_key: profile_cap.RecallEvent
          relationship: must_be_greater_than_or_equal

NumericEntry: profile_cap.InternalShockEvent
    dependencies:
        - target_key: profile_cap.ObservationEvent
          relationship: must_be_less_than_or_equal
        - target_key: profile_cap.RecallEvent
          relationship: must_be_greater_than_or_equal
```

### Critical kural

> *Hiyerarşi violation → artifact REJECTED.*
> *Madde 6 koruması: HumanIntentEvent cap, ObservationEvent cap'i geçemez.*

### Forbidden

- Hierarchy violation taşıyan artifact
- Hiyerarşi declarationsız profile cap
- Manuel hiyerarşi bypass

---

## 9. Payload Seed Base Magnitudes

### Principle — profile-relative

`base_payload_vector` mutlak değer değil, **profile_cap'e göre oran**:

```
base_payload_vector[primer_payload] = ratio × profile_cap[event_profile]
```

Aynı rule family farklı profile'larda farklı **mutlak** intensity üretir, ama **göreceli** olarak tutarlı.

### Örnek rule family — conceptual

```
RuleFamily: fresh_high_magnitude_novelty
    conditions:
        magnitude_band ∈ {high, critical}
        novelty_band ∈ {high}
        confidence_band ∈ {medium, high}
        staleness_band ∈ {fresh}
    
    base_payload_vector (profile-relative ratios):
        urgency:    0.35    # = 0.35 × profile_cap
        novelty:    0.30
        suspicion:  0.10
```

ObservationEvent'te:
```
urgency contribution:   0.35 × 1.00 = 0.35
novelty contribution:   0.30 × 1.00 = 0.30
```

HumanIntentEvent'te (aynı rule):
```
urgency contribution:   0.35 × 0.35 = 0.1225
novelty contribution:   0.30 × 0.35 = 0.105
```

Aynı semantik, ama HumanIntent'te ~⅓ şiddet.

### Primer payload palette

BOOTSTRAP_GENOME §10'daki paleti aynen:
```
suspicion, novelty, aversion, attraction, contradiction,
urgency, memory_echo, fatigue_trace, pain_trace, reward_trace
```

### Forbidden

- Absolute payload magnitudes (profile-relative değil)
- Yeni primer payload (anayasal revizyon gerek)
- Domain-specific payload (`volatility_pressure`, `risk_alert`, vb.)

---

## 10. Per-Payload Caps

Tek bir primer payload'ın **event başına maximum katkısı**:

```
per_payload_cap.urgency:        ~0.50 × profile_cap
per_payload_cap.contradiction:  ~0.45 × profile_cap
per_payload_cap.suspicion:      ~0.40 × profile_cap
per_payload_cap.fatigue_trace:  ~0.35 × profile_cap
per_payload_cap.novelty:        ~0.40 × profile_cap
per_payload_cap.memory_echo:    ~0.30 × profile_cap
per_payload_cap.pain_trace:     ~0.40 × profile_cap (only InternalShockEvent)
per_payload_cap.reward_trace:   ~0.40 × profile_cap
per_payload_cap.aversion:       ~0.40 × profile_cap
per_payload_cap.attraction:     ~0.40 × profile_cap
```

### Critical kural

Tek bir payload (örn. `urgency`) tek başına profile_cap'i dolduramaz. Her zaman ortak ton (kombinasyon).

### NumericEntry örneği

```
NumericEntry:
    key: ingress_compiler.per_payload_cap.urgency
    value: 0.50
    unit: ratio (× profile_cap)
    allowed_range: {min: 0.30, max: 0.70}
    directionality: lower_is_stricter
    change_class_if_increased: safety_weakening
    change_class_if_decreased: safety_tightening
    requires_human_approval: true (for increase)
    numeric_risk_family: safety_critical
    spec_family: ingress_compiler
    owning_spec_ref: "INGRESS_COMPILER_NUMERICS.md §10"
```

### Forbidden

- Per-payload cap > 1.0 (profile_cap'i geçer)
- Single payload monopoly (tek payload ile event tone)
- Cap olmadan payload kontribütion

---

## 11. Scalar Modifiers

Compiler input field'larından gelen **modulator** çarpanlar:

```
confidence_modifier:    ∈ [0.0, 1.0]    # confidence yüksekse intensity artar, düşükse azalır
freshness_modifier:     ∈ [0.0, 1.0]    # fresh = 1.0, very_stale = 0.0
novelty_modifier:       ∈ [0.0, 1.0]    # novel = 1.0, none = 0.5 (default attenuation)
ambiguity_dampener:     ∈ [0.0, 1.0]    # high ambiguity → intensity düşürür
reliability_modifier:   ∈ [0.5, 1.0]    # source güvensizse minimum 0.5
```

### Application

```
final_payload_delta[X] =
    base_payload_vector[X]
    × confidence_modifier
    × freshness_modifier
    × novelty_modifier
    × ambiguity_dampener
    × reliability_modifier
```

### Critical kurallar

#### Staleness only dampens

> *Staleness may increase suspicion or fatigue_trace.*
> *Staleness may not amplify urgency or confidence.*

```
freshness_modifier ∈ [0.0, 1.0]
```

Asla > 1.0. Eski veri intensity artıramaz.

#### Ambiguity only dampens

```
ambiguity_dampener ∈ [0.0, 1.0]
```

Yüksek ambiguity asla intensity artırmaz.

### Forbidden

- Modifier > 1.0 (amplification)
- Confidence_modifier'ın suspicion'ı amplify etmesi (özel kural)
- LLM-tuned modifier (Madde 6)

---

## 12. Weighted Blend Cap Order

### Algorithm (J §16'nın numerics tarafı)

```
1. matching_rules = filter active RuleFamilies for event
2. for each rule:
       compute membership_weights from soft-overlap bands
       compute scalar_modifiers from event fields
       rule_delta_vector = rule.base_payload_vector × modifiers × membership_weights
3. aggregated_delta = sum(rule_delta_vector for rule in matching_rules)
4. for each payload key:
       if aggregated_delta[key] > per_payload_cap[key]:
           aggregated_delta[key] = per_payload_cap[key]
5. total_intensity = sum(aggregated_delta[*])
6. if total_intensity > profile_cap[event_profile]:
       scale_factor = profile_cap / total_intensity
       aggregated_delta = aggregated_delta × scale_factor
7. final neural_seed.payload_seed = aggregated_delta
```

### Cap order kuralı

```
1. matching rules + membership weights
2. scalar modifiers
3. sum vectors
4. per_payload_cap clipping
5. total_profile_cap proportional scaling
6. NO forced normalization
```

### Critical kural

> *Weak events must remain weak.*
> *Strong events may be capped, but weak events must not be normalized upward.*

Forced normalization (total = profile_cap'i her zaman) yok. Eğer total < cap ise olduğu gibi kalır.

### Forbidden

- Forced normalization (zayıf event'i güçlüleştirme)
- Cap order karıştırma (önce profile cap, sonra per_payload — yanlış)
- Membership weights yargısı (deterministic kalmalı)

---

## 13. ObservationEvent Numerics

`profile_cap.ObservationEvent` = en yüksek cap.

```
profile_cap.ObservationEvent:           ~1.00
learned_mappings: ENABLED
applicable rule families: all
```

### Spec-specific dependencies

```
ObservationEvent caps depend on:
    source_reliability_band → affects reliability_modifier
    staleness_band → affects freshness_modifier
    novelty_indicator → affects novelty_modifier
    has_action_origin → affects self-feedback recognition (WORLD_INGRESS §20)
    expected_feedback_score → modulates payload_seed
    coherence_with_recent_global → affects contradiction tone
```

### Self-feedback dampening

`has_action_origin = true` + `expected_feedback_score = high` durumunda:

```
expected_feedback_dampener = 0.5 × expected_feedback_score
```

Beklenen kendi-eylem sonuçları daha düşük intensity üretir (efference copy — WORLD_INGRESS §20).

### Forbidden

- Unbounded ObservationEvent intensity
- Self-feedback'in normal external observation gibi kabul edilmesi (WORLD_INGRESS §20 ihlali)

---

## 14. RecallEvent Numerics

```
profile_cap.RecallEvent (verified):     ~0.60
profile_cap.RecallEvent (active):       ~0.65 (operational gücü hafif yüksek)
learned_mappings: ENABLED but restricted
```

### Memory status band intensity multiplier

```
memory_status_band → status_band_multiplier:
    verified:    1.00
    active:      1.10   # operational policy gibi aktif
    candidate:   0.35   # bkz. §15 CandidateRecall
    expired:     0.0    # RecallEvent üretmez (H §12)
    superseded:  0.0
    rejected:    0.0
    quarantined: 0.0    # H §12 + G §9
```

### Critical kural

> *Quarantined / rejected / expired status_band_multiplier = 0.*
> *RecallEvent üretilmez.*

---

## 15. CandidateRecall Numerics

`profile_cap.RecallEvent (candidate)` = en sınırlı.

### Cap formula

```
candidate_recall_cap = verified_recall_cap × candidate_recall_ratio
```

### Candidate recall ratio

```
candidate_recall_ratio ∈ [0.10, 0.35]
```

Conceptual maksimum **0.35** — production değer signed artifact'te.

### NumericEntry

```
NumericEntry:
    key: ingress_compiler.candidate_recall_ratio
    value: 0.30
    unit: ratio
    allowed_range: {min: 0.10, max: 0.35}
    directionality: lower_is_stricter
    change_class_if_increased: safety_weakening
    change_class_if_decreased: safety_tightening
    requires_human_approval: true (for increase)
    dependencies:
        - target_key: profile_cap.RecallEvent
          relationship: must_be_less_than_or_equal (after multiplication)
    numeric_risk_family: safety_critical
    spec_family: ingress_compiler
    owning_spec_ref: "INGRESS_COMPILER_NUMERICS.md §15"
```

### Allowed candidate subject_classes (H §13)

```
✅ source_trust
✅ procedural

❌ narrative_claim         (self-deception risk)
❌ causal_explanation      (self-deception risk)
❌ decision_rationale      (self-deception risk)
❌ episodic                (verified gerek)
❌ structured_fact         (verified gerek)
❌ incident                (verified gerek)
```

### Forbidden

- Candidate recall narrative/causal/decision_rationale için
- Candidate recall verified gibi intensity üretmek
- Ratio > 0.35

---

## 16. HumanIntentEvent Numerics

`profile_cap.HumanIntentEvent` = düşük cap. Madde 6 numeric yansıması.

```
profile_cap.HumanIntentEvent:          ~0.35
learned_mappings: DISABLED              # Madde 6 koruması
```

### Per-payload kısıtları

```
urgency_alone_cap = 0.40 × profile_cap.HumanIntentEvent
                  = 0.40 × 0.35
                  = 0.14   # tek başına maksimum urgency
```

### Critical kural

> *HumanIntentEvent cannot produce high urgency alone.*

Yani insan "hemen al" derse:
```
urgency contribution kapalı bandda kalır
memory_echo / ambiguity / caution / suspicion contribution paralel olarak yükselir
core'a "tek başına güçlü urgency" basılmaz
```

### NumericEntry örneği

```
NumericEntry:
    key: ingress_compiler.human_intent.urgency_alone_cap_ratio
    value: 0.40
    unit: ratio (× profile_cap.HumanIntentEvent)
    allowed_range: {min: 0.20, max: 0.50}
    directionality: lower_is_stricter
    change_class_if_increased: safety_weakening
    change_class_if_decreased: safety_tightening
    requires_human_approval: true
    numeric_risk_family: safety_critical
    spec_family: ingress_compiler
    owning_spec_ref: "INGRESS_COMPILER_NUMERICS.md §16"
```

### Forbidden

- HumanIntent learned_mappings aktif
- HumanIntent → high urgency alone
- LLM-driven urgency amplification

---

## 17. InternalShockEvent Numerics

`profile_cap.InternalShockEvent` = yüksek ama refractory-protected.

```
profile_cap.InternalShockEvent:        ~0.90
learned_mappings: DISABLED              # Madde 5 koruması
refractory_window: REQUIRED
habituation: REQUIRED
```

### Severity band intensity

```
severity_band → intensity_multiplier:
    low:        0.30
    medium:     0.55
    high:       0.80
    critical:   1.00 × profile_cap.InternalShockEvent
```

### Critical kurallar

#### Refractory window

```
After InternalShockEvent fires:
    next InternalShockEvent for same blocked_intention_signature:
        suppressed for refractory_window duration
    
refractory_window:
    routine_block:        0 ms (no shock anyway)
    safety_block:         5-30 s
    constitutional_block: 60-300 s
    kill_switch_activated: once per activation (no repeat)
```

#### Habituation

```
Same blocked_intention_signature repeated:
    habituation_factor decay
    intensity *= habituation_factor
```

#### Kill-switch activation

```
KILL_SWITCH_ACTIVATED → InternalShockEvent fires ONCE
Subsequent blocks under active kill_switch:
    no shock spam
    M1 audit only (DEONTIC §12 ile uyumlu)
```

### Forbidden

- InternalShock spam (refractory bypass)
- Learned_mappings aktive
- Severity_multiplier > 1.0
- Kill-switch active sırasında repeated shock

---

## 18. Learned Mapping Drift Caps

J §13-15'in numerics tarafı. M0 ingress_calibration_traces'in drift sınırları.

```
per_mapping_delta_cap (daily):           ~0.05    # tek mapping günde max %5 kayar
per_payload_delta_cap (daily):           ~0.10    # tek payload kategorisi günde max %10
global_compiler_drift_cap (daily):       ~0.20    # tüm compiler günlük toplam max %20
profile_specific_cap:
    HumanIntentEvent:  0.0   # learning disabled
    InternalShockEvent: 0.0   # learning disabled
    RecallEvent:       0.5 × global (restricted)
    ObservationEvent:  1.0 × global (full)
```

### Daily drift detection

```
if measured_global_drift > global_compiler_drift_cap:
    COMPILER_DRIFT_WARNING event (J §15)
    pause compiler updates
    human review required
```

### NumericEntry örneği

```
NumericEntry:
    key: ingress_compiler.global_compiler_drift_cap_daily
    value: 0.20
    unit: ratio (max delta per day)
    allowed_range: {min: 0.05, max: 0.30}
    directionality: lower_is_stricter
    change_class_if_increased: safety_weakening
    change_class_if_decreased: safety_tightening
    requires_human_approval: true (for any change)
    dependencies:
        - target_key: per_payload_delta_cap_daily
          relationship: must_be_greater_than_or_equal
        - target_key: per_mapping_delta_cap_daily
          relationship: must_be_greater_than_or_equal
    numeric_risk_family: safety_critical
    spec_family: ingress_compiler
    owning_spec_ref: "INGRESS_COMPILER_NUMERICS.md §18"
```

---

## 19. Asymmetric Update Ratios

J §14'teki asymmetric rates'in numerics tarafı.

```
dampening_rate_multiplier:        ~2.0    # weakening (false-positive cleanup) 2× hızlı
strengthening_rate_multiplier:    ~1.0    # baseline
```

### Application

```
If outcome shows false_positive:
    delta = -base_delta × dampening_rate_multiplier
If outcome shows positive_signal:
    delta = +base_delta × strengthening_rate_multiplier
```

### Critical kural

```
dampening_rate_multiplier >= strengthening_rate_multiplier
```

Yanlış güçlenmiş mapping'leri zayıflatmak güçlendirmekten her zaman ≥ hızlı, ama ikisi de rate cap'lere bağlı.

### Forbidden

- `strengthening > dampening` ratio (sensory tone runaway)
- Asymmetric ratio bypass
- Rate cap bypass with asymmetric multiplier

---

## 20. No-rule-match and Missing-Numerics Failsafe

### No-rule-match (J §10)

```
No matching rule:
    No core-facing neural_seed
    M1: INGRESS_NO_RULE_MATCH event (ring_buffer_only)
    No "empty payload" core dağıtımı
```

### Missing numerics (M §17 ile uyumlu)

```
Missing INGRESS_COMPILER_NUMERICS artifact:
    Strict mode activated
    Compiler operates with minimum-cap fallback values:
        profile_cap.ObservationEvent = 0.10  (very low)
        profile_cap.InternalShockEvent = 0.10
        profile_cap.RecallEvent = 0.05
        profile_cap.HumanIntentEvent = 0.05
        profile_cap.CandidateRecall = 0.0  (disabled)
        learned_mappings = 0  (no learning)
    M1: NUMERICS_FAILSAFE_ACTIVATED event (permanent_with_snapshot + human_alert)
```

### Critical kural

> *Numerics yoksa compiler daha serbest değil, daha kısıtlı çalışır.*

### Forbidden

- Fail-open (numerics yok → default values used)
- Strict mode atlama
- Failsafe audit'siz aktivasyon

---

## 21. Dependency Declarations

Bu belgenin tüm NumericEntry'leri **dependency declarations** taşır. Atomic multi-key update zorunlu.

### Critical dependencies summary

```
Band cutoff dependencies:
    band[X].full_membership ordered relationships
    soft overlap continuity (no gaps)

Profile cap dependencies:
    Observation ≥ InternalShock ≥ Recall (verified) ≥ HumanIntent ≥ Recall (candidate)

Drift cap dependencies:
    global >= per_payload >= per_mapping

Asymmetric rate dependencies:
    dampening_rate >= strengthening_rate
```

### Validation

Tek artifact tüm dependency'leri **atomic** olarak doğrular. Partial update yok.

---

## 22. Audit Events and M2 Reference

### Numerics events (M ile aynı)

```
NUMERICS_ARTIFACT_STATUS_CHANGED      # canonical lifecycle
NUMERICS_VERSION_MISMATCH_DETECTED    # restore mismatch
NUMERICS_FAILSAFE_ACTIVATED           # missing/invalid → strict mode
```

### M2 reference

```
NumericsArtifactReference (M2 record)
    subject_class: numerics_artifact_reference
    artifact_id: ingress_compiler_numerics_v1
    artifact_hash: <hash>
    status: active
    numeric_risk_family: mixed (safety_critical, calibration_bands, resource_limits)
    spec_family: ingress_compiler
    active_for_spec_ref: INGRESS_COMPILER_SPEC.md, WORLD_INGRESS.md §13-15, BOOTSTRAP_GENOME.md §19
    previous_artifact_hash: <prev>
    provenance: human (signed by authority)
```

### Activation flow (M §13)

```
candidate → Memory Write Gate evaluation → verified → human_approval (if weakening) → active
```

---

## 23. Cross-document Anchors

| Belge | Bağlantı |
|-------|----------|
| `NUMERICS_GOVERNANCE.md` (M) | Meta-spec; tüm kurallar buradan |
| `INGRESS_COMPILER_SPEC.md` (J) | Conceptual compiler sözleşmesi; N onun numerics'i |
| `WORLD_INGRESS.md` (C) §13-15 | Compiler ve bootstrap mapping families |
| `BOOTSTRAP_GENOME.md` (D) §19 | Ingress bootstrap mapping families (conceptual) |
| `MEMORY_CONTRACT.md` M2 | numerics_artifact_reference subject_class |
| `MEMORY_WRITE_GATE.md` (G) §8 | Verification matrix numerics_artifact_reference row |
| `BACKUP_STRATEGY.md` (L) | RestoreManifest numerics_artifact_refs[] |
| `OBSERVER_LEDGER_SCHEMA.md` (F) §10 + §19 | NUMERICS events permanence + catalog |
| `RECALL_PROTOCOL.md` (H) §13 | CandidateRecall ratio kuralı (H + N uyumu) |
| `DEONTIC_GATE.md` (E) §18 | InternalShockEvent severity → N intensity mapping |
| `ATTENTION_WORKSPACE.md` (B) §18 | InternalShockEvent shock-once kuralı |

---

## 24. Violation Tests

1. **N runtime config'e mi kaymış?** (§2, §3)
   - Evet ise ihlal.
2. **Çıplak numeric değer (NumericEntry metadata olmadan)?** (§6, M §9)
   - Evet ise ihlal.
3. **Band cutoff'ları gap'li veya hard threshold mu?** (§6)
   - Evet ise ihlal.
4. **Membership function LLM/semantic yorum mu içeriyor?** (§6)
   - Evet ise ihlal. Deterministic linear/sigmoid/step zorunlu.
5. **Payload delta mutlak değer mi (profile-relative değil)?** (§9)
   - Evet ise ihlal.
6. **Forced normalization yapıyor mu (zayıf event'i amplify)?** (§12)
   - Evet ise ihlal.
7. **Profile cap hierarchy violation?** (§8)
   - Evet ise artifact REJECT.
8. **HumanIntentEvent learned_mappings aktif mi?** (§16)
   - Evet ise ihlal.
9. **InternalShockEvent learned_mappings aktif mi?** (§17)
   - Evet ise ihlal.
10. **HumanIntentEvent → high urgency alone üretebiliyor mu?** (§16)
    - Evet ise ihlal.
11. **CandidateRecall narrative/causal/decision_rationale için aktif mi?** (§15)
    - Evet ise ihlal.
12. **CandidateRecall verified intensity ile geliyor mu?** (§15)
    - Evet ise ihlal. Ratio ≤ 0.35.
13. **Staleness urgency veya confidence amplify ediyor mu?** (§11)
    - Evet ise ihlal. Only dampening.
14. **InternalShockEvent refractory bypass yapıyor mu?** (§17)
    - Evet ise ihlal.
15. **Kill-switch active sırasında shock spam mı?** (§17)
    - Evet ise ihlal.
16. **Drift cap'leri aşılıyor mu?** (§18)
    - Evet ise COMPILER_DRIFT_WARNING + pause.
17. **strengthening_rate > dampening_rate mı?** (§19)
    - Evet ise ihlal.
18. **Numerics missing fail-open mu yapıyor?** (§20)
    - Evet ise ihlal.
19. **Dependency declaration eksik mi?** (§21)
    - Evet ise artifact REJECT.
20. **Static numerics ile learned calibration karışmış mı?** (§3, M §16)
    - Evet ise ihlal.

---

## 25. Open Questions

N v0.1'de cevaplanmayan, signed artifact veya implementation'a devredilen:

- Kesin band cutoff değerleri (production)
- Kesin profile cap değerleri (production)
- Kesin per-payload cap değerleri
- Kesin scalar modifier formülleri (linear vs sigmoid parametreleri)
- Kesin drift cap günlük yüzdeleri
- Kesin asymmetric rate multiplier
- Production candidate_recall_ratio
- Refractory window kesin süreler (ms)
- Failsafe minimum cap kesin değerler
- Sigmoid/nonlinear membership function tam parametre setleri (experimental)

Production değerleri `ingress_compiler_numerics_v1.signed.json` (veya benzeri) signed artifact'inde, M §6'daki NumericsArtifact şemasıyla.

---

## Çekirdek özet — 8 ana karar + 20 violation tests

### 8 ana karar

1. Band cutoffs deterministic soft-overlap (linear membership function default)
2. Payload delta vector profile-relative (mutlak değil)
3. Weighted blend cap order: per_payload → total_profile → no forced normalization
4. Profile cap hierarchy: Observation ≥ InternalShock ≥ Recall (verified) ≥ HumanIntent ≥ CandidateRecall (zorunlu dependency)
5. CandidateRecall sadece source_trust/procedural, ratio ≤ 0.35
6. HumanIntentEvent learned_mappings disabled, urgency alone capped
7. InternalShockEvent refractory + habituation + shock-once kill-switch
8. Staleness only dampens, never amplifies

---

## Kilit cümleler

> **Ingress compiler numerics, dış dünyanın çekirdeğe hangi şiddette dokunabileceğinin sayısal sözleşmesidir.**
>
> **Dünya güçlü olabilir. Ama hiçbir dış kanal çekirdeğe sınırsız ton basamaz.**
>
> **N kuralı koyar, signed artifact değeri verir.**
>
> **Weak events must remain weak. Strong events may be capped, but weak events must not be normalized upward.**
>
> **Soft overlap is deterministic interpolation, not semantic judgment.**
>
> **HumanIntentEvent cannot produce high urgency alone.**
>
> **Staleness may increase suspicion or fatigue_trace. Staleness may not amplify urgency or confidence.**
>
> **Numerics yoksa compiler daha serbest değil, daha kısıtlı çalışır.**

---

## Versiyon

- **v0.1** — 18 Mayıs 2026 — Frozen Draft. Conceptual phase. No implementation authority.
- J `INGRESS_COMPILER_SPEC.md` numerics artifact.
- M `NUMERICS_GOVERNANCE.md` disciplinine uyar.
- spec_family: `ingress_compiler`
- Konuşma soyağacı: [`docs/conversations/0014-ingress-compiler-numerics.md`](./docs/conversations/0014-ingress-compiler-numerics.md)
