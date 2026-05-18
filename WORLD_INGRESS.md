# WORLD_INGRESS.md

## Sentinel — Dış Dünya Giriş Sınırları

---

## Status

**Frozen Draft v0.1**
**Conceptual phase. No implementation authority.**

Bu belge çalışan bir ingress katmanının spec'i değildir. Dış dünyadan gelen kaynaklı olayların çekirdeğe hangi sınırlar altında, hangi yetki matrisi ile, hangi audit gereği ile, ve hangi nöral izlere dönüşerek girebileceğini tanımlar.

---

## 1. Purpose

Sentinel dış dünya ile bir noktada temas edecek. Bu temas **çekirdeği dış ontolojiye sızdırmadan** yapılmak zorundadır. Bu belge o sızdırmayı engelleyen sınırın anayasal halidir.

Damıtma:

> **Dünya çekirdeğe gerçek olarak girmez.**
> **Dünya kaynaklı gözlem olarak gelir.**
> **Çekirdekte sadece nöral iz olarak yaşar.**

---

## 2. Not a World Model

### Sentinel'in world model'i **yoktur**.

"World model" kelimesi yanıltıcıdır — çünkü "dünya hakkındaki bilgiyi tutan bir yapı" çağrışımı yapar. Bizim ihtiyacımız bu değil.

**Sentinel dünyayı içeride saklamaz.** Sentinel dünyanın çekirdeğe nasıl yansıdığını yaşar. Bu belge bir world model belgesi değildir; bir **ingress boundary** belgesidir.

Sentinel dünyanın iki yansımasını yaşar:

- **Anlık yansıma:** `ObservationEvent` (dış adapter'dan)
- **Kalıcı hatırlatma:** `RecallEvent` via M2 (kalıcı facts'tan)

İkisi de aynı sınırdan geçer. İkisi de payload_seed olarak içeri girer. Çekirdek hiçbirinde **doğrudan** dünyayla karşılaşmaz.

---

## 3. Constitutional Position

Bu belge yeni anayasa maddesi **değildir**. Mevcut maddelerin dış dünya teması için detay sözleşmesidir:

- **Madde 1** (Nöron homojen, payload heterojen): Çekirdeğe giren her şey primer payload paleti üzerinde dağılır; yeni payload tipi üretilmez.
- **Madde 3** (Minimum genome): Doğuştan domain-specific kavram yok; ingress de domain bilgisi sızdırmaz.
- **Madde 6** (LLM dış tercüman): `HumanIntentEvent` bu sınırın bir profilidir; LLM yine deterministic compiler'dan geçer.
- **Madde 7** (Hafıza ayrılığı): `RecallEvent` M2'den içeri sızar, `ObservationEvent` M2'ye işlenmek için aday üretebilir.
- **Madde 5** (Self-field / Deontic gate): `InternalShockEvent` deontic gate'in çekirdeğe yansıma yoludur.
- **ATTENTION_WORKSPACE.md** (B): ingress'ten gelen payload_seed'ler context_signature'a iç durum izi olarak yansır, dış etiket olarak değil.

---

## 4. Core Principle

> **World ingress dış dünyayı modellemez. Dış dünyadan gelen kaynaklı olayların çekirdekte hangi nöral izlere dönüşebileceğini sınırlar.**

Bu cümle belgenin kilididir. Her tasarım kararı buna geri dönülerek sınanır.

---

## 5. Ingress Boundary

Sentinel'in dış dünya ile teması **tek bir sınırdan** geçer: **Deterministic Ingress Compiler**.

```
[Dış kaynak]
    ↓
IngressEventEnvelope (4 profile)
    ↓
[Deterministic Ingress Compiler]   ← sınır burada
    ↓
[Çekirdek içi: payload_seed]
```

Sınırın **dışı** structured event'ler (audit'lenebilir, izlenebilir, çürütülebilir). Sınırın **içi** sadece nöral uyaran (payload seed). Compiler **kategori** üretmez, sadece **ton** üretir.

---

## 6. Ingress Profile Visibility

### Principle
Event profile observer ve compiler tarafından bilinir. **Çekirdek tarafından bilinmez.**

### Rationale
Eğer çekirdek "bu Observation", "bu Recall", "bu Human" diye ayrımı yaşarsa, ingress kanalları çekirdek için **kategori** olur — gizli ontoloji sızar. Doğru sınır: event_profile compiler'da kural seçimi için kullanılır, payload_seed'e flag olarak yansımaz.

| Aktör | event_profile görür? | Nasıl kullanır? |
|-------|---------------------|-----------------|
| Observer | ✅ | Provenance / audit kaydı için |
| Compiler | ✅ | Yetki matrisi (learned_mappings açık/kapalı) seçimi için |
| Core | ❌ | Sadece payload_seed yaşar |

### Forbidden
- Payload_seed içinde `human_originated: true` benzeri flag
- Çekirdekte event class'a göre farklı işleyiş
- "Bu Recall'dan geldi" diye assembly etiketi

### Violation Test
> *Çekirdek event profile'ı duyabiliyor mu?*
>
> Evet ise ihlal.

---

## 7. Ingress Profile Authority Matrix

C'nin **anayasal yetki tablosu**:

| Event profile | bootstrap_rules | learned_mappings | outcome feedback | Not |
|---------------|-----------------|-------------------|------------------|-----|
| `ObservationEvent` | ✅ | ✅ açık | ✅ tam | Gerçek dış akış |
| `RecallEvent` | ✅ | ✅ kısıtlı | ✅ kısıtlı | Staleness/provenance sert |
| `HumanIntentEvent` | ✅ | ❌ **kapalı** | ❌ | LLM dolaylı mapping öğrenemez |
| `InternalShockEvent` | ✅ | ❌ **kapalı, deterministik** | ❌ | Gate şoku güçlenemez |

### Kritik kurallar

- `HumanIntentEvent` için learned_mappings **kapalı**. Sebep: LLM zamanla compiler mapping'ini şekillendirip payload tonu üzerinde dolaylı kontrol kazanmamalı. Madde 6 koruması.
- `InternalShockEvent` için learned_mappings **kapalı**. Sebep: deontic gate kendi shock'unu deneyimle güçlendirip düşünceye etki etmemeli. Madde 5 koruması.

---

## 8. Common IngressEventEnvelope

Dört event class'ı aynı temel zarfı paylaşır:

```
IngressEventEnvelope
│
├── observer_only        # audit'e gider, çekirdeğe sızmaz
│   ├── event_id
│   ├── event_profile
│   ├── raw_ref
│   ├── provenance_ref
│   ├── received_at
│   ├── emitted_at
│   ├── correlation_id
│   └── hash_or_dedup_key
│
├── compiler_input       # sayısal/skalar, ham etiket yok
│   ├── confidence
│   ├── ttl_ms
│   ├── staleness_ms
│   ├── reliability_band
│   ├── ambiguity_or_uncertainty
│   ├── criticality_band
│   └── profile_specific_scalars
│
└── compiler_output      # çekirdeğe giren tek şey
    └── neural_seed
        ├── payload_seed         # mandatory — primer palette üzerinde dağılım
        ├── receptor_bias_seed   # optional, bounded
        └── trace_seed           # optional, bounded
```

### compiler_output **yapmaz**

- Assembly yaratmaz
- Niyet yaratmaz
- Pulse yaratmaz
- Memory write başlatmaz
- M0 sinapslarını doğrudan değiştirmez

Sadece **nöral uyarı tohumu** üretir. Sonrası normal nöral akış.

> **Core-facing output tek bir `neural_seed`'dir.**
> **`neural_seed` kategori, fact, world state, niyet, pulse veya assembly değildir.**
> **Sadece bounded nöral uyarı tohumu taşır.**

---

## 9. ObservationEvent

Dış adapter'dan gelen anlık akış.

```
ObservationEvent
│
├── observer_only
│   ├── event_id
│   ├── event_profile: "observation"
│   ├── source_adapter_id
│   ├── source_class
│   ├── subject_id
│   ├── venue
│   ├── raw_payload_ref
│   ├── observation_id_hash
│   ├── adapter_capabilities_snapshot
│   ├── received_at
│   └── event_time
│
├── compiler_input
│   ├── confidence
│   ├── ttl_ms
│   ├── staleness_ms
│   ├── source_reliability_band
│   ├── magnitude_normalized
│   ├── change_rate_normalized
│   ├── instability_normalized
│   ├── coherence_with_recent_global
│   ├── novelty_indicator
│   ├── has_action_origin
│   ├── expected_feedback_score
│   └── feedback_delay_ms
│
└── compiler_output
    └── neural_seed       # payload_seed mandatory; receptor_bias_seed / trace_seed optional
```

### Kritik notlar

- `subject_id`, `venue`, `source_adapter_id` **observer_only**. Çekirdeğe sızmaz.
- `action_origin_ref` observer'a yazılır ama compiler_input'a girmez; compiler sadece soyut etkisini görür (`has_action_origin`, `expected_feedback_score`, `feedback_delay_ms`).
- `coherence_with_recent_global` — son N saniyedeki **tüm ingress akışı** ile uyum. Source-spesifik değil. Aksi durumda source bilgisi compiler'a sızar.
- Ham feature vector **yoktur**. Adapter domain feature'ları kaynak-göreceli skalarlara (magnitude, change rate, instability) damıtır.

### Adapter sorumluluğu

**Adapter dünyayı tanır, çekirdek tanımaz.** Adapter'ın görevi: ham veriden kaynak-bağımsız skalar özetler üretmek. "BTC son 24h üzerinden 2.3σ" → `magnitude_normalized=2.3`. Domain etiketi (`BTCUSDT`, `volatility`, vs.) sadece observer'da yaşar.

---

## 10. RecallEvent Boundary

M2 Explicit Recall Store'dan çağrılan kalıcı hatırlatma.

```
RecallEvent
│
├── observer_only
│   ├── event_id
│   ├── event_profile: "recall"
│   ├── memory_record_id
│   ├── memory_type
│   ├── record_status     # candidate | verified | superseded | expired | rejected
│   ├── subject_class     # source_trust | episodic | structured | procedural | ...
│   ├── original_timestamp
│   ├── retrieval_timestamp
│   ├── provenance
│   ├── raw_ref
│   └── trigger_recall_request_id
│
├── compiler_input
│   ├── confidence
│   ├── ttl_ms
│   ├── staleness_ms          # original_timestamp - retrieval_timestamp
│   ├── memory_status_band    # candidate/verified bandı (içerik değil)
│   ├── retrieval_relevance
│   ├── contradiction_risk
│   ├── provenance_strength
│   └── criticality_band
│
└── compiler_output
    └── neural_seed       # payload_seed mandatory; receptor_bias_seed / trace_seed optional
```

### Kritik kurallar

- M2 raw content **çekirdeğe fact olarak giremez**. Sadece status band'ı ve risk skalarları compiler'a girer.
- Çekirdek "Halit 18 Mayıs'ta kill-switch çekti" bilgisini **bilmez**. Sadece "yüksek-criticality, verified, kısmen stale, çelişki riski düşük bir hatırlatma" tonunu yaşar.
- `record_status` band olarak compiler'a gelir, ham status string olarak değil.
- M2'den `RecallEvent` üretilmesi `MEMORY_CONTRACT.md` §5'teki recall flow + §6'daki recall ekonomisine tabidir.

### Kural
> *RecallEvent gerçek değildir. RecallEvent kaynaklı hatırlatmadır.*

> *RecallRequest tetikleyicileri, scope/ranking/multi-record kuralları, status-based recall davranışı, candidate recall sınırı (sadece source_trust + procedural), human-requested recall (HumanIntentEvent tetikleyici, doğrudan değil) ve recall failure handling için bkz. [`RECALL_PROTOCOL.md`](./RECALL_PROTOCOL.md).*

---

## 11. HumanIntentEvent Boundary

LLM translator'dan gelen yapısal insan niyeti.

```
HumanIntentEvent
│
├── observer_only
│   ├── event_id
│   ├── event_profile: "human_intent"
│   ├── translator_artifact_id
│   ├── raw_text_ref
│   ├── model_id
│   ├── prompt_hash
│   ├── conversation_ref     # M3 reference
│   ├── parsed_intent_family
│   ├── hallucination_risk_score
│   └── requires_confirmation
│
├── compiler_input
│   ├── confidence
│   ├── ambiguity_score
│   ├── destructive_flag
│   ├── scope_band
│   ├── duration_band
│   ├── urgency_claimed_by_human
│   ├── requires_confirmation
│   ├── ttl_ms
│   └── criticality_band
│
└── compiler_output
    └── neural_seed       # payload_seed mandatory; receptor_bias_seed / trace_seed optional
```

### Kritik kurallar

- `parsed_intent_family` (`monitor_only_request`, `pause_request`, `inquiry`) observer'a gider, compiler kuralı seçer, **çekirdeğe etiket olarak girmez**.
- learned_mappings **kapalı** — LLM dolaylı mapping öğrenemez.
- M3 (translator memory) `HumanIntentEvent` üretimini bağlamsal olarak iyileştirebilir ama M3 raw content compiler_input'a sızmaz.
- `urgency_claimed_by_human` ham olarak `urgency` payload'ına map edilmez — diğer skalarlarla **kombinasyonla** yorumlanır (criticality_band ile aynı kural).

### LLM yapamaz
- Payload_seed doğrudan üretmek
- Çekirdeğe `urgency: 1.0` enjekte etmek
- Çekirdeğe assembly tetiklemek
- M0 mapping'ini deneyimle şekillendirmek

> **LLM niyet ailesi söyler. Compiler tonu belirler. Core sadece tonu yaşar.**

---

## 12. InternalShockEvent Boundary

Kritik deontic block sonrası çekirdeğe yansıyan iç şok eventi. Bkz. `ATTENTION_WORKSPACE.md` §18 — burası onun ingress yoludur.

```
InternalShockEvent
│
├── observer_only
│   ├── event_id
│   ├── event_profile: "internal_shock"
│   ├── source: "deontic_gate"
│   ├── deontic_rule_id
│   ├── blocked_intention_id
│   ├── blocked_intention_signature_ref
│   ├── gate_snapshot_ref
│   ├── severity
│   ├── routine_or_critical
│   └── raw_ref
│
├── compiler_input
│   ├── severity_band
│   ├── violation_distance_band
│   ├── blocked_intention_payload_signature
│   ├── criticality_band
│   └── ttl_ms
│
└── compiler_output
    └── neural_seed       # bounded, deterministic over primer palette
```

> *Diğer event class'larındaki gibi, payload_seed mandatory; receptor_bias_seed ve trace_seed optional. InternalShockEvent için tüm seed bileşenleri **deterministic** ve **bounded**.*

### Kritik kurallar

- learned_mappings **kapalı**. Deterministic. Anayasal.
- Sadece **kritik** deontic block tetikler (rutin block sessiz kalır — bkz. ATTENTION_WORKSPACE §18 ve DEONTIC_GATE §12).
- Payload_seed primer palette üzerinde **sınırlı** karışım (örn. `pain_trace`, `memory_echo`, `contradiction`, `fatigue_trace`). Yeni payload tipi üretmez.
- Kesin seed magnitudes bu belgenin konusu değil — `DEONTIC_GATE.md` veya `BOOTSTRAP_GENOME.md` konusu.

> *InternalShockEvent tetikleme kuralları (routine vs safety vs constitutional block), kill-switch özel statüsü ve bypass attempt InternalShockEvent davranışı için bkz. [`DEONTIC_GATE.md`](./DEONTIC_GATE.md) §12-14.*

### InternalShockEvent **yapamaz**
- WORKSPACE_PULSE doğrudan üretmek
- Assembly seçmek
- Memory write başlatmak
- Deontic kuralı değiştirmek
- M2'ye doğrudan kayıt yazmak

---

## 13. Deterministic Ingress Compiler

Sınırın kendisi. İki katmanlı:

```
IngressCompiler =
    bootstrap_rules     (sabit, anayasal)
  + learned_mappings    (M0 alt-tipi, deneyimle kayan)
```

### Davranış

- **Asenkron, event-driven.** Her event geldiğinde anında compile edilir. Batch yok.
- **Tek event, tek output.** İki event aynı anda gelirse iki ayrı compile.
- **Profile-gated.** Yetki matrisi (Section 7) event_profile'a göre uygulanır.
- **Dedup allowed.** Aynı `hash_or_dedup_key`'li network retry'lar elenir. Bu uzlaştırma değil, tekrar engelleme.

### Aggregation yasak

```
Allowed:  same observation_id_hash → deduplication
Forbidden: Binance + BTCTurk + news → "market_state = flash_crash" aggregation
```

Çoklu source pre-merge edilmez. Her event ayrı compile edilir, payload_seed olarak ayrı akar, **çelişki çekirdeğin içinde yaşanır** (Madde 4'le uyumlu).

---

## 14. Bootstrap Rules

Compiler'ın sabit, anayasal katmanı. Doğuştan gelir; runtime'da değişmez.

### Örnek bootstrap mapping'leri (sözel)

```
high_magnitude + high_novelty + high_confidence + low_staleness
    → urgency + novelty

high_change_rate + low_coherence_with_recent_global
    → contradiction + suspicion

fresh unexpected self-feedback (has_action_origin + low expected_feedback)
    → contradiction + memory_echo

high_staleness + low_confidence
    → suspicion + fatigue_trace

candidate recall + high_contradiction_risk
    → memory_echo + suspicion (kısıtlı yoğunluk)

human monitor_only + low_ambiguity
    → caution-tone suspicion + reduced intention pressure

critical internal shock (severity_band high)
    → bounded pain_trace + memory_echo + contradiction
```

### Kritik kural — `criticality_band` kombinasyon

`criticality_band` tek başına `urgency`'ye map edilmez. Diğer skalalarla birlikte ton üretir:

```
critical + low_confidence + high_ambiguity   → suspicion + caution
critical + high_confidence + low_staleness   → urgency + caution
critical + high_contradiction_risk           → contradiction + memory_echo
```

Sebep: tek-terim mapping sistemi "her kritik şey panik" zihniyetine sokar. Doğru olan: criticality bir **modülasyon**, çıkış değil.

### Bootstrap kuralları nerede yaşar

`BOOTSTRAP_GENOME.md` ve `INGRESS_COMPILER_SPEC.md` (ileride yazılacak). Bu belge sadece mekanizmayı tanımlar, sayısal parametreleri değil.

---

## 15. Learned Mappings as M0 Ingress Calibration

### Principle
Compiler'ın öğrenen katmanı **M0 alt-tipidir**. Yeni katman değil, yeni kanal değil. Mevcut M0 öğrenme kuralları altında yaşar.

### M0 alt-türleri (tam liste)

```
M0
├── synaptic memory
├── assembly stability traces
├── self-field weights (homeostatic / predictive / narrative)
├── attention habituation traces
└── ingress calibration traces
```

### Yetki

`ingress_calibration_traces` **config değildir**. İnsan, LLM, panel, adapter doğrudan yazamaz. Sadece:

- STDP (Madde 2)
- Outcome alignment (Madde 2)
- Eligibility trace (Madde 2)
- Sleep/replay (Madde 2)

ile kayar. Yani compiler mapping de doku, config değil.

### Hangi event class'lar kalibrasyon üretir

- `ObservationEvent` → tam kalibrasyon yetkisi
- `RecallEvent` → kısıtlı (staleness/provenance ağırlığı sert)
- `HumanIntentEvent` → **kalibrasyon üretmez**
- `InternalShockEvent` → **kalibrasyon üretmez**

### Kural
> *Ingress mapping config değildir. Ingress mapping dokudur.*

---

## 16. SourceTrustRecord as M2 Subtype

### Principle
Source güvenirlik geçmişi **M2 alt-tipi** olarak yaşar. Yeni hafıza katmanı değildir.

### Yapı

M2 kayıtları artık `subject_class` ile alt-türlenir:

```
SourceTrustRecord (M2 record, subject_class = "source_trust")
├── source_adapter_id
├── source_class
├── current_reliability_band
├── candidate_reliability_change
├── evidence_refs            # observer M1 event'leri
├── status                   # candidate | verified | superseded | rejected | expired
├── provenance               # human | observer | system
└── updated_at
```

### Yetki ve sınır

- `MEMORY_CONTRACT.md` §10'daki CandidateMemoryRecord statü zinciri aynen kullanılır.
- Sistem kaynaklı reliability değişimleri **Memory Write Gate**'ten geçer (epistemik risk var: yanlış kalibrasyon sistemi etkiler).
- İnsan elle reliability değiştirebilir (Halit "şu adapter güvensiz" diyebilir) ama o da provenance:human olarak işaretli M2 kaydı doğurur.

### Çekirdeğe etki

SourceTrustRecord çekirdeğe **RecallEvent olarak ham dönmez**. Compiler sadece `source_reliability_band` skaler değerini görür (ObservationEvent'in compiler_input'unda).

> **Kaynak kimliği dış kanıttır.**
> **Güven bandı compiler girdisidir.**
> **Kaynak adı çekirdek hafızasına dönüşmez.**

### Forbidden
- `source_id` çekirdek M0'a yazmak
- `Binance` gibi etiketi çekirdek hafızasında tutmak
- SourceTrustRecord'u yeni bir memory layer olarak ele almak

---

## 17. Payload Seed, Not Category

### Principle
Compiler'ın çekirdeğe verdiği tek şey **payload_seed**'dir. Kategori, etiket, structured event veya domain durumu değildir.

### Doğru output

```
payload_seed = {
    urgency: 0.42,
    novelty: 0.28,
    suspicion: 0.16,
    memory_echo: 0.08
}
```

### Yanlış output

```
payload_seed = {
    volatility_high: true,
    btc_premium: 0.7,
    flash_crash_state: true,
    market_regime: "trending"
}
```

### Kural
> *Compiler kategori üretmez. Compiler zihinsel renk tohumu üretir.*

Çekirdek "BTCUSDT volatility high" diye bir kavramı **bilmez**. Sadece o gözlemden doğan urgency + novelty + suspicion tonunu yaşar.

---

## 18. Provenance Boundary

Provenance üç katmana ayrılır:

| Katman | Nerede yaşar | Çekirdeğe etkisi |
|--------|--------------|------------------|
| `provenance_for_audit` | Observer (M1) | Yok (sadece audit) |
| `provenance_for_compilation` | Compiler input | Skalar etki (confidence, staleness, ttl, reliability_band) |
| `provenance_inside_core` | **Yok** | Çekirdeğe ham giremez |

### Compiler kullanabileceği provenance

```
confidence
ttl_ms
staleness_ms
source_reliability_band
ambiguity_or_uncertainty
criticality_band
has_action_origin
expected_feedback_score
feedback_delay_ms
```

Hepsi **sayısal/skaler**. İsim/etiket değil.

### Çekirdeğe sızmayan provenance

- `source_adapter_id`, `subject_id`, `venue`, `memory_record_id`, `model_id`
- Adapter capability snapshot
- Raw payload reference

### Kural
> *Provenance observer'da isim olarak yaşar. Çekirdekte sadece güven, tazelik ve sürpriz etkisi olarak yaşar.*

---

## 19. Time, Staleness, and Delay

Çekirdek **saat bilmez.** Çekirdek **zaman etkisi yaşar.**

### Compiler input'a giren zaman skalarları

```
staleness_ms             # event_time - now
ttl_ms                   # event'in geçerlilik süresi
feedback_delay_ms        # action_origin'den feedback'e kadar süre
```

### Payload etkisi (örnek)

```
staleness_ms high + confidence low
    → suspicion + fatigue_trace seed

fresh + high_novelty
    → urgency + novelty seed

unexpected delayed self-feedback
    → contradiction + memory_echo seed
```

### Forbidden

- Çekirdeğe ham timestamp girmesi (`2026-05-18T14:32:00Z`)
- "Saat 14'te" gibi mutlak zaman referansı
- Domain-spesifik zaman katmanları (`market_open`, `news_window`)

### Kural
> *Çekirdek saat kaç olduğunu bilmez. Zamanın bedensel etkisini yaşar.*

---

## 20. Action-Origin Feedback / Efference Copy

Sistem bir eylem yaptı (örn. adapter üzerinden bir komut çıktı). Eylem dünyaya etki etti. Dünyadan dönen `ObservationEvent` sistemin **kendi yaptığının** sonucu olabilir.

İnsan beyninde "efference copy" — beyin kendi hareketinin duyusal sonuçlarını "kendisinin yaptığını" işaretler. Yoksa kendi nefesini "rüzgar" diye yorumlar.

### Mekanik

```
ObservationEvent.observer_only.action_origin_ref = <last_action_id or null>

Compiler bunu görmez (observer_only).
Compiler sadece soyut etkisini görür:

ObservationEvent.compiler_input:
    has_action_origin: bool
    expected_feedback_score: [0.0, 1.0]   # ne kadar beklenen?
    feedback_delay_ms
```

### Payload etkisi

```
has_action_origin=true + high expected_feedback_score
    → low novelty + low suspicion (kendi eyleminden beklenen sonuç)

has_action_origin=true + low expected_feedback_score
    → contradiction + memory_echo + replay-mark seed
    (kendi eyleminden beklenmeyen sonuç — sürpriz)
```

### Kural
> *Eylem geri bildirimi, dünyaya ait ham gerçek olarak değil, beklentiyle karşılaştırılmış duyusal sonuç olarak içeri girer.*

Çekirdek `order_id`'sini bilmez. Sadece "kendi eyleminden beklenmedik feedback" tonunu yaşar.

---

## 21. Multi-Source Conflict

Aynı anda Binance + BTCTurk + news → üç farklı ObservationEvent.

### Doğru davranış

```
Üç ObservationEvent ayrı ayrı compile edilir
    ↓
Üç ayrı payload_seed çekirdeğe akar
    ↓
Çelişki çekirdeğin içinde yaşanır
    ↓
contradiction_load doğal yükselir
    ↓
contradiction payload aktivasyonu yükselir
    ↓
ATTENTION_WORKSPACE §12'deki coherence-weighted contradiction çalışır
```

### Yasak

```
Pre-ingress aggregator karar verir:
    "market_state = flash_crash"
    ↓
Tek "uzlaşılmış" event çekirdeğe girer
```

Bu **gizli world model** doğurur. Çekirdek dünyayı dışarıdan-uzlaştırılmış halde alır, gerçekliği bozulur.

### Dedup vs aggregation farkı

```
Dedup (allowed):
    Aynı observation_id_hash, aynı raw payload, network retry
    → biri elenir, biri compile edilir

Aggregation (forbidden):
    Farklı kaynaklar, farklı gözlemler
    → "doğru dünya bu" diye uzlaştırma
```

### Kural
> *Ingress öncesi dünya uzlaştırılmaz. Çelişki çekirdeğin içinde yaşanır.*

---

## 22. Observer Events

### Ana event tipleri

```
OBSERVATION_INGESTED
RECALL_INGESTED
HUMAN_INTENT_INGESTED
INTERNAL_SHOCK_INGESTED
INGRESS_DEDUP_REJECTED
INGRESS_TTL_EXPIRED
COMPILER_MAPPING_UPDATED              # learned_mappings güncellendiğinde
SOURCE_TRUST_STATUS_CHANGED
```

### SourceTrustStatusChangedEvent şeması

```
SourceTrustStatusChangedEvent
├── event_type: SOURCE_TRUST_STATUS_CHANGED
├── source_trust_record_id
├── old_status
├── new_status            # candidate | verified | superseded | rejected | expired
├── evidence_refs
├── current_reliability_band
├── candidate_reliability_change
├── provenance            # human | observer | system
└── observer_snapshot_ref
```

`candidate / verified / superseded / rejected / expired` ayrı event tipleri **değildir** — `MEMORY_CONTRACT.md` §10'daki CandidateMemoryRecord statü makinesinin durumlarıdır. Bu yüzden tek event tipi, alt durumlar `old_status` / `new_status` field'leri olarak gelir. Bu, B'deki `WORKSPACE_PULSE` "tek event tipi, alt durum field" disiplininin C seviyesindeki yansımasıdır.

### Audit zorunluluğu

Sistem sonradan şunları cevaplayabilmeli:

- Hangi event hangi adapter'dan, hangi confidence ile geldi?
- Compiler bu event'i hangi kurallarla payload_seed'e çevirdi?
- O an hangi M0 mapping kalibrasyonu aktifti?
- Çoklu kaynaktan gelen çelişkili event'ler nasıl ayrı compile edildi?
- Source reliability'si ne zaman, hangi kanıtla değişti?

Cevap verilemiyorsa ingress auditable değildir — anayasa ihlali.

---

## 23. Violation Tests

1. **Çekirdeğe dış dünya etiketi giriyor mu?** (Madde 1, §17, §18)
   - Evet ise ihlal.
2. **Compiler kategori üretiyor mu (boolean flag, domain state)?** (§17)
   - Evet ise ihlal.
3. **Source identity M0'a giriyor mu?** (§16)
   - Evet ise ihlal.
4. **HumanIntentEvent learned_mappings kullanıyor mu?** (§7, §11)
   - Evet ise ihlal.
5. **InternalShockEvent learned_mappings kullanıyor mu?** (§7, §12)
   - Evet ise ihlal.
6. **SourceTrustRecord yeni memory layer olarak mı yazılmış?** (§16)
   - Evet ise ihlal. M2 alt-tipi olmalı.
7. **Aggregation ile dedup karışmış mı?** (§13, §21)
   - Aggregation yasak, dedup serbest.
8. **`action_origin_ref` compiler_input'a ham giriyor mu?** (§20)
   - Evet ise ihlal.
9. **Çekirdek event_profile'ı yaşıyor mu?** (§6)
   - Evet ise ihlal.
10. **Pre-ingress aggregator "doğru dünya budur" diye uzlaştırma yapıyor mu?** (§13, §21)
    - Evet ise ihlal.
11. **Çekirdeğe ham timestamp veya mutlak zaman giriyor mu?** (§19)
    - Evet ise ihlal.
12. **`criticality_band` tek başına `urgency`'ye map ediliyor mu?** (§14)
    - Evet ise ihlal.

---

## 24. Open Questions

C kapanırken cevaplanmamış bırakılan ve sonraki belgelere devredilen sorular:

- **Bootstrap mapping sayısal parametreleri:** Compiler'ın bootstrap_rules'unda hangi `magnitude × confidence × staleness` ağırlıkları hangi payload yoğunluğunu üretiyor? → `BOOTSTRAP_GENOME.md` ve `INGRESS_COMPILER_SPEC.md` konusu.
- **Adapter manifest formatı:** Her adapter `adapter_capabilities_snapshot` üretiyor. Bu manifest'in tam şeması, capability listesi, yetki sınırları nasıl tanımlanır? → `ADAPTER_MANIFEST_SPEC.md` konusu.
- **InternalShockEvent payload_seed büyüklükleri:** Severity bandına göre seed magnitudes nasıl ayarlanır? → `DEONTIC_GATE.md` veya `BOOTSTRAP_GENOME.md` konusu.
- **Multi-source conflict resolution time scale:** Çekirdekte çelişki ne kadar süre yaşamalı? Otomatik replay tetikleyici eşik nedir? → `ATTENTION_WORKSPACE.md` §22'deki açık sorularla bağlantılı.
- **SourceTrustRecord migration:** M2 schema versioning (MEMORY_CONTRACT §14) — yeni `subject_class` field'i eski kayıtlara nasıl migrate olur? Provenance nasıl korunur?
- **Learned mapping rate limiting:** Ingress calibration ne kadar hızlı kayabilir? Çok hızlı kayma sistemde "input layer instability" yaratır. Rate limit kuralları nereye düşer?

Bu sorular cevaplanmadan implementation aşamasına geçilmez.

---

## Çekirdek özet — 14 karar

1. Sentinel'in world model'i yoktur; world ingress yolu vardır.
2. Dünya çekirdeğe gerçek olarak girmez; kaynaklı gözlem olarak girer.
3. Dış dünyayı içeride structured fact olarak saklamayız.
4. Kalıcı facts M2'de yaşar; çekirdeğe `RecallEvent` olarak döner.
5. Anlık akış `ObservationEvent` olarak gelir.
6. İnsan niyeti `HumanIntentEvent` olarak gelir (Madde 6'ya tabi).
7. Kritik deontic blok `InternalShockEvent` olarak gelir (Madde 5'ten).
8. Tüm ingress event'leri deterministic ingress boundary'den geçer.
9. Event profile observer ve compiler tarafından bilinir; **çekirdek tarafından bilinmez**.
10. Compiler output kategori değil, **payload_seed**.
11. `ObservationEvent` ve `RecallEvent` learned_mappings kullanabilir; `HumanIntentEvent` ve `InternalShockEvent` kullanamaz.
12. Provenance observer'da isim olarak yaşar; çekirdekte güven/tazelik/sürpriz etkisi olarak yaşar.
13. `learned_mappings` M0 ingress calibration trace olarak yaşar; config değildir.
14. Çoklu source pre-merge edilmez; ayrı ayrı compile edilir, çelişki çekirdekte yaşanır.

### Ek özel kurallar
- **`SourceTrustRecord` M2 alt-tipidir** (subject_class = "source_trust"), yeni katman değildir.
- **Dedup allowed, aggregation forbidden.**

---

## Kilit cümleler

> **Dünya çekirdeğe gerçek olarak girmez. Dünya kaynaklı gözlem olarak gelir. Çekirdekte sadece nöral iz olarak yaşar.**
>
> **Compiler kategori üretmez. Compiler zihinsel renk tohumu üretir.**
>
> **Provenance observer'da isim olarak yaşar. Çekirdekte sadece güven, tazelik ve sürpriz etkisi olarak yaşar.**
>
> **LLM niyet ailesi söyler. Compiler tonu belirler. Core sadece tonu yaşar.**
>
> **Ingress mapping config değildir. Ingress mapping dokudur.**

---

## Versiyon

- **v0.1** — 18 Mayıs 2026 — Frozen Draft. Conceptual phase. No implementation authority.
- `CONSTITUTION.md` Madde 1, 3, 5, 6, 7'nin ortak ingress sözleşmesi.
- Konuşma soyağacı: [`docs/conversations/0003-world-ingress.md`](./docs/conversations/0003-world-ingress.md)
