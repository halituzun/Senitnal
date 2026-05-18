# RECALL_PROTOCOL.md

## Sentinel — Hatırlatma Protokolü

---

## Status

**Frozen Draft v0.1**
**Conceptual phase. No implementation authority.**

Bu belge `CONSTITUTION.md` Madde 7 ve `MEMORY_CONTRACT.md` §5'in (Recall Flow) detaylı uzantısıdır. Yeni anayasa maddesi değildir. Çalışan bir recall implementation'ının spec'i değildir. Sentinel'in M2 explicit memory'sindeki kayıtların çekirdeğe **emir değil, kaynaklı hatırlatma** olarak nasıl döndüğünü tanımlar.

---

## 1. Purpose

G `MEMORY_WRITE_GATE` M2'ye yazma kapısını tanımladı. H bunun **çift kapısı**: M2'den çekirdeğe okuma yolu.

```
G (Memory Write Gate):  M0 / observer / human / replay → M2 (yazma)
H (Recall Protocol):    M2 → RecallEvent → World Ingress → neural_seed → core (okuma)
```

Damıtma:

> **RecallEvent gerçek değildir. RecallEvent kaynaklı hatırlatmadır.**
>
> **Recall retrieval değildir. Recall sensory ingress'tir.**
>
> **Hafıza çekirdeğe emir vermez. Hafıza çekirdeğe hatırlatma gönderir.**

---

## 2. Constitutional Position — Madde 7 / MEMORY_CONTRACT §5 Alt-spec'i

Bu belge `CONSTITUTION.md` Madde 7'deki hafıza ayrılığının ve `MEMORY_CONTRACT.md` §5'teki Recall Flow + §6'daki Recall Economy mekaniklerinin detaylı uzantısıdır.

MEMORY_CONTRACT zaten ana çizgileri çiziyor:
- M2 → çekirdek sadece `RecallEvent` üzerinden (§5)
- Recall ekonomisi: enerji bedeli, cooldown, habituation (§6)
- RecallEvent gerçek değil, kaynaklı gözlem (§5)

WORLD_INGRESS de katkıda bulunuyor:
- RecallEvent şeması (§10)
- RecallEvent compiler üzerinden neural_seed'e dönüşür (§10)

MEMORY_WRITE_GATE de etkili:
- Quarantined kayıt RecallEvent üretmez (§9)
- Statü-bazlı recall davranışı

H bu çerçevenin **biçimsel ve uygulanabilir** halini verir.

---

## 3. Core Principle

> **M2 çekirdeğe bilgi vermez. M2 çekirdeğe kaynaklı hatırlatma gönderir.**
> **Hatırlatma bile gerçek değildir. Sadece çekirdekte iz bırakabilecek bir duyusal olaydır.**

Bu cümle belgenin kilididir.

---

## 4. Recall Is Not Retrieval — It Is Sensory Ingress

### Principle
Recall bir **veri çekme** işlemi değildir. Çekirdek M2'yi sorgulamaz, kayıt okumaz. Çekirdek M2'den gelen hatırlatma **olayının nöral etkisini** yaşar.

### Rationale
Eğer recall "veri çekme" olarak modellense, çekirdek M2'yi bilen, sorgulayan, kayıt seçen bir entity olurdu — Madde 7'nin "çekirdek M2'yi bilmez, sadece etkisini yaşar" prensibini ihlal. Doğru: recall, **dış olayla aynı kategoride duyusal ingress** (WORLD_INGRESS §10).

### Allowed

- Çekirdek `memory_echo` gerilimi üretir
- RecallRequest port üzerinden çıkar
- Explicit memory adapter M2'de arar
- Bulunan kayıt RecallEvent olarak geri döner
- Deterministic ingress compiler nöral seed'e çevirir
- Çekirdek bu seed'i duyusal event olarak yaşar

### Forbidden

- Çekirdeğin M2'yi doğrudan sorgulaması
- Çekirdeğe M2 kayıt içeriğinin **ham fact** olarak girmesi
- "Çekirdek hatırlamak istedi" diye tek-adım veri okuma
- Kayıt ID'sinin veya raw content'in çekirdeğe sızması

### Violation Test
> *Bu öneri çekirdeğin M2'yi sorgulayan bir entity gibi davranmasına yol açıyor mu?*
>
> Evet ise ihlal.

---

## 5. Who May Request Recall

### RecallRequest tetikleyici yetkisi

Sadece **core-originated** RecallRequest çekirdeğe RecallEvent döndürebilir. Diğer aktörler M2'yi okuyabilir ama **çekirdeğe RecallEvent enjekte edemez**.

| Kaynak | M2 okuma | Core'a RecallEvent? |
|--------|----------|---------------------|
| **Core / M0** (memory_echo tension) | RecallRequest üretir | ✅ Evet |
| **Replay engine** | Offline/validation amaçlı query yapabilir | ❌ Live core'a değil |
| **Summarizer** | M1/M2 okuyup candidate/revalidation önerebilir | ❌ Hayır |
| **Human** (operator) | HumanIntentEvent ile recall isteyebilir (dolaylı) | ❌ Doğrudan değil — bkz. §11 |
| **LLM translator** | Rapor için M2 okuyabilir | ❌ Hayır |

### Rationale

Eğer summarizer, replay engine veya LLM çekirdeğe RecallEvent doğrudan basabilse, M2 → çekirdek yolu **emir kanalı**na döner. Madde 7'nin "hafıza emir vermez" prensibi ihlal olur.

### Kritik kurallar

> *Summarizer core'a hatırlatma enjekte edemez.*
> *Replay engine live core'a hatırlatma enjekte edemez.*
> *Human/LLM recall'u doğrudan core'a basamaz.*

### Audit

Diğer aktörlerin M2 okuması zaten OBSERVER_LEDGER §16'da kayıtlı (M1_HUMAN_READ, M1_REPLAY_READ_BATCH, M1_SUMMARY_GENERATED). Bu okumalar **insana raporlanır** veya **candidate önerir**, ama **çekirdeğe ingress üretmez**.

### Violation Test
> *Bir aktör çekirdeğe RecallEvent enjekte edebiliyor mu (core-originated request olmadan)?*
>
> Evet ise ihlal.

---

## 6. RecallRequest Triggers

### Core-originated tetikleyiciler

Çekirdek kendi RecallRequest'ini şu içsel basınçlardan doğurur:

```
memory_echo tension
    + contradiction pressure
    + dissonant attention
    + unresolved intention context
    + recall_load_band (terslik — yüksekse tetik zayıflar)
```

### Kavramsal eşik

```
recall_pressure = f(
    memory_echo,
    contradiction_load,
    dissonance_score,
    unresolved_intention_pressure,
    fatigue_state (inverse),
    recall_load_band (inverse)
)

if recall_pressure > recall_threshold[context]:
    çekirdek RecallRequest doğurur
```

Kesin formül ve eşikler implementation konusu. H sadece **tetikleyici eksenleri** anayasallaştırır.

### Forbidden

- RecallRequest'in çekirdek dışında bir aktör tarafından üretilmesi (§5)
- "Otomatik recall scheduler" — periyodik recall (çekirdek tetiği iç durum, zaman değil)
- Pulse alındı diye otomatik recall (B §16 ile uyumlu — pulse RecallRequest doğurabilir ama tek başına yetmez)

### İnsan tetiği (dolaylı)

Bkz. §11 — İnsan recall talebi `HumanIntentEvent` olarak girer, çekirdek `memory_echo` yükselirse kendi RecallRequest'ini doğurur.

---

## 7. RecallRequest Schema

### Yapı

```
RecallRequest
├── request_id
├── triggered_at
├── trigger_pressure
│   ├── memory_echo_level
│   ├── contradiction_level
│   ├── dissonance_score
│   └── intention_pressure
├── scope
│   ├── allowed_subject_classes        # boş ise tüm matrix'te izinli olanlar
│   ├── allowed_statuses               # default: {verified, active}
│   ├── context_signature_similarity_band
│   ├── contradiction_tolerance
│   ├── staleness_limit
│   └── exclusion_keys                 # cooldown/habituation tarafından dolduruluyor
├── recall_budget                      # max iterations / max cost
└── source_layer: "core"               # her zaman, §5 kuralı
```

### Notlar

- `scope` çekirdeğin iç durumundan türer; dış etiket içermez (context_signature iç durum karakteridir — ATTENTION §11)
- `recall_budget` recall economy ile sınırlı (§14)
- `exclusion_keys` cooldown/habituation aktif kayıtları dışlar

---

## 8. Recall Scope and Search Boundaries

### Principle — Hybrid scoping

Tam free search **yanlış** (tüm M2 sürekli taranır, retrieval motor karar modülüne döner).
Tam context-bound da **yanlış** (sadece mevcut iç duruma benzer kayıtlar gelir, confirmation bias).

**Doğru: hybrid.**

```
RecallScope
├── subject_class_filter             # matrix-controlled
├── status_filter                    # default: {verified, active}; opsiyonel candidate
├── context_signature_similarity     # iç durum benzerliği (dış etiket değil)
├── contradiction_tolerance
├── staleness_limit
├── recall_budget
└── exclusion_keys (cooldown/habituation)
```

### Critical kural — Scope dış dünya etiketi değildir

> *context_signature dış dünya etiketi değildir (ATTENTION §11).*
> *Recall scope çekirdeğin iç durumuna göre filtrelenir.*

Yanlış:
```
scope.subject_id = "BTCUSDT"
scope.venue = "Binance"
```

Doğru:
```
scope.allowed_subject_classes = { source_trust, episodic }
scope.context_signature_similarity_band = HIGH
scope.staleness_limit = T
```

Dış M2 arama adapter'ı teknik olarak subject_id/venue alanlarını görebilir (M2 raw kaydında var), ama çekirdeğe dönen RecallEvent provenance'ı observer'da kalır, çekirdeğe sızmaz (WORLD_INGRESS §18 provenance boundary).

### Subject_class filtre

Çekirdek "şu subject_class kategorisinde kayıt istiyorum" diye scope koyabilir. Bu sınırlama matrix tarafından kontrollü:
- `source_trust` recall — operational karar için
- `episodic` recall — geçmiş olay hatırlatması için
- `procedural` recall — pattern/lookup için
- `narrative_claim` recall — sadece audit/reflection için

### Status filtre

Default: `{verified, active}`.

Candidate açık ise sadece §13'teki dar kapsamda.
Quarantined, rejected, expired, superseded asla.

### Forbidden

- Tam free search (tüm M2 sürekli scan)
- Tam context-bound search (sadece benzer iç duruma)
- Domain etiketi scope (BTCUSDT, Binance, vs.)
- Statü filtresi olmadan recall (verified ile candidate karışmaz)

---

## 9. Ranking Is Delivery, Not Truth

### Principle

M2 araması birden fazla kayıt bulduğunda **ranking** yapılır. Ama bu ranking **hakikat sıralaması değildir** — sadece **teslim sıralaması**.

### Rationale

Eğer ranking "bu kayıt daha gerçek" anlamına gelirse, search adapter gizli karar modülüne döner. Madde 1 ihlali. Doğru: ranking sadece "hangisi öne geçer" mekanik kararı.

### Allowed ranking criteria

```
record.status_band                        # verified > active > candidate
record.confidence
record.staleness_ms                       # taze > eski
record.context_signature_similarity       # benzer iç durum > uzak
record.contradiction_risk                 # düşük > yüksek
record.provenance_strength_band
```

Hepsi mekanik. Yargı yok.

### Forbidden ranking criteria

- "Bu kayıt daha mantıklı"
- "LLM bu kaydı tercih etti"
- "Sistem bundan fayda görür"
- Semantic interpretation

### Kural

> **Recall ranking truth ranking değildir. Recall ranking delivery ranking'dir.**

---

## 10. Multi-Record Recall Rules

### Principle

Bir `RecallRequest` birden fazla aday kayıt bulabilir. Çekirdeğe **tek RecallEvent** döner; diğerleri observer'da `alternates` olarak kayıtlı kalır.

### Rationale

Eğer çekirdeğe aynı anda 3 farklı RecallEvent dönerse:
- Hangisi gerçek?
- Hangisi daha güvenilir?
- Çekirdek bu üçü arasında "seçim" yapmak zorunda

Bu, M2 arama tarafını gizli dikkat/karar modülüne çevirir. Doğru: tek event, audit alternates.

### Akış

```
RecallRequest
    ↓
M2 search → ranked candidate list (N items)
    ↓
top-1 → core-facing RecallEvent
    ↓
top-2..N → observer alternates (audit only)
```

### `RecallEvent.provenance.alternates`

```
RecallEvent.observer_only.alternates: [
    { memory_record_id, rank, score, status_band, suppression_reason },
    ...
]
```

Bu liste observer'a yazılır, çekirdeğe **sızmaz**.

### İstisna — RECALL_RESULT_EMPTY

Hiç aday bulunamazsa veya hepsi suppress edildiyse: çekirdeğe **hiçbir RecallEvent dönmez**. `RECALL_RESULT_EMPTY` event'i M1'e yazılır (§16).

> *Boş recall çekirdeğe "yokluk payload'ı" basmaz.*

### Critical

> *Top-1 hakikat değildir; sadece "şu an dönen recall budur" demektir.*

---

## 11. RecallEvent Schema

WORLD_INGRESS §10'da temel şema tanımlı. Burada tam form:

```
RecallEvent (IngressEventEnvelope based)
│
├── observer_only
│   ├── event_id
│   ├── event_profile: "recall"
│   ├── memory_record_id
│   ├── subject_class
│   ├── record_status                    # verified | active | candidate
│   ├── status_band                      # explicit field (verified/candidate band)
│   ├── original_timestamp
│   ├── retrieval_timestamp
│   ├── trigger_recall_request_id
│   ├── alternates                       # bkz. §10
│   ├── m2_provenance                    # provenance: human|genesis|system, signed_by, vs.
│   └── raw_ref                          # M2 raw kayıt referansı
│
├── compiler_input                       # WORLD_INGRESS §10 detayı
│   ├── confidence
│   ├── ttl_ms
│   ├── staleness_ms
│   ├── memory_status_band
│   ├── retrieval_relevance
│   ├── contradiction_risk
│   ├── provenance_strength
│   └── criticality_band
│
└── compiler_output                       # WORLD_INGRESS §13 compiler kuralları
    └── neural_seed
        ├── payload_seed (mandatory)
        ├── receptor_bias_seed (optional)
        └── trace_seed (optional)
```

### `status_band` explicit

Çekirdek **status'u doğrudan görmez** ama compiler `status_band`'ı kullanarak intensity'yi modüle eder:

- `verified` → normal intensity
- `active` → normal-high (operational relevance varsa)
- `candidate` → capped intensity (~%30 of verified), sadece §13 izin verdiği subject_class'larda

### M2 raw content sızmıyor

Çekirdeğe sadece **compiler_output.neural_seed** giriyor (WORLD_INGRESS §13). M2 ham içeriği observer'da kalıyor, çekirdek "Halit 18 Mayıs'ta kill-switch çekti" diye bir bilgi olarak yaşamıyor — sadece o hatırlatmanın **tonu** olarak yaşıyor.

---

## 12. Status-Based Recall Behavior

| M2 Status | RecallEvent? | Intensity | Not |
|-----------|--------------|-----------|-----|
| `verified` | ✅ Evet | Normal | Standart recall |
| `active` | ✅ Evet | Normal-high | Operational policy / source_trust active için |
| `candidate` | ⚠️ Sadece §13'teki dar koşulda | Capped (~%30) | Sadece source_trust, procedural |
| `quarantined` | ❌ Hayır | — | G §9 ile uyumlu |
| `rejected` | ❌ Hayır | — | Çürümüş |
| `expired` | ❌ Hayır | — | Süresi dolmuş |
| `superseded` | ❌ Normal recall'da hayır | — | Sadece audit/history query'sinde |

### Critical kural

> *Quarantined / rejected / expired kayıt RecallEvent üretmez.*
> *Superseded kayıt normal recall'da gelmez; sadece audit kanalında erişilir.*

### Status field explicit

RecallEvent.event_body'de `status_band` field'ı **açık**. Compiler bu field'a göre intensity modülasyonu yapar. Çekirdek "candidate vs verified" diye **kategori** olarak değil, **ton yoğunluğu** olarak yaşar — yine Madde 1 koruması.

---

## 13. Candidate Recall Boundary

### Principle

Candidate recall **varsayılan kapalıdır**. Sadece dar bir subject_class alt-kümesinde, sıkı koşullarda açıktır.

### Allowed subject_classes

| Subject class | Candidate recall? | Sebep |
|---------------|-------------------|-------|
| `source_trust` | ✅ düşük confidence | Outcome bekleniyor ama operasyonel kalibrasyon için düşük etkili hatırlatma gerekebilir |
| `procedural` | ✅ düşük confidence | Pattern/lookup adayı kontrollü hatırlatılabilir |
| `narrative_claim` | ❌ kapalı | Self-deception riski |
| `causal_explanation` | ❌ kapalı | Self-deception riski |
| `decision_rationale` | ❌ kapalı | Self-deception riski |
| `episodic` | ❌ kapalı | Verified olmadan "şu oldu" gibi davranamaz |
| `structured_fact` | ❌ kapalı | Verified olmadan fact gibi dönemez |
| `incident` | ❌ kapalı | Olgu iddiası, verified gerekir |
| `deontic_policy` | ❌ kapalı | Active policy zaten verified+active olmalı |
| `bootstrap_reference` | N/A | Doğumda verified |

### Candidate recall koşulları

```
Candidate recall allowed only if:
    subject_class IN {source_trust, procedural}
    AND status_band = candidate (explicit in RecallEvent)
    AND confidence_band = LOW
    AND self_deception_risk != HIGH
    AND neural_seed intensity capped (örn. verified intensity'nin %30'u)
```

### Kilit kural

> *Candidate recall sadece operational pattern adayları içindir.*
> *Anlatı, neden iddiası, karar gerekçesi, episodic olay ve structured fact candidate iken RecallEvent üretemez.*
>
> *Candidate recall verified recall gibi hissedilemez.*

### Rationale

`source_trust` candidate'lar henüz doğrulanmamış ama operasyonel karar etkileyebilir (örn. "şu source güvensiz görünüyor, ama henüz outcome alignment yetmedi" → sistem bu sinyali çok düşük yoğunlukta yaşayabilir). `procedural` candidate'lar pattern adayları — düşük yoğunlukta "şu pattern de var" hatırlatması bilgi getirir.

Narrative/causal/episodic/structured_fact için candidate recall **kapalı** çünkü bunların düşük confidence ile bile içeri girmesi self-deception zinciri kurar (sistem kendi anlatısını "var ama belirsiz" diye yaşar).

### Forbidden

- Candidate recall'un verified intensity ile sızması
- Yasak subject_class'lar için candidate recall
- `status_band` field'ının RecallEvent'ten gizlenmesi

---

## 14. Recall Economy — Cost, Cooldown, Habituation

MEMORY_CONTRACT §6'daki kavramların biçimsel hali:

### Enerji bedeli

Her `RecallRequest` `homeostatic_stability`'yi geçici düşürür. `fatigue_state` birikir. Çok recall = sistem yorulur.

```
recall_cost = base_cost
            × subject_class_complexity
            × search_scope_breadth
            × current_fatigue_modifier
```

### Cooldown

Aynı `RecallRequest` peşpeşe yapılamaz:

```
cooldown_active(request_key) = (now - last_request_at[key]) < refractory_period[subject_class]
```

`request_key` request'in **iç imzası** (subject_class + context_signature_similarity_hash). Aynı imza tekrarlanamaz.

### Habituation

Aynı `RecallEvent` 5. kez geldiğinde 1.'ye göre çok düşük intensity üretir:

```
habituation_factor = decay_function(repeat_count, time_since_first_recall)
neural_seed intensity = base_intensity × habituation_factor
```

Habituation `record_id + context_signature_key` üzerinde tutulur (ATTENTION §19 habituation_key pattern'i ile uyumlu).

### Recall budget

Her `RecallRequest`'in `recall_budget` field'ı vardır:
- max iterations (M2 search ne kadar derin)
- max cost (toplam enerji bütçesi)
- max alternates (kaç aday değerlendirilir)

### Kilit kural

> **Recall geçmişi getirir, ama şimdiyi boğamaz.**
> **Recall bedelsiz değildir.**

### Forbidden

- Sınırsız recall
- Cooldown bypass
- Habituation devre dışı bırakma
- Recall budget sınırsız

---

## 15. Recall TTL and Refresh

### RecallEvent TTL

RecallEvent çekirdeğe geldikten sonra **geçicidir**. `ttl_ms` ile sınırlı:

```
ttl_ms = base_ttl
       × subject_class_persistence
       × confidence_modifier
```

Süresi dolan RecallEvent'in nöral etkisi (varsa hâlâ aktif assembly'lerde) doğal olarak söner. Yeni RecallEvent gerek olursa çekirdek yine kendi `memory_echo`'sunu yükseltir.

### Refresh

`RecallRequest` aynı record için tekrar tetiklenebilir:
- Cooldown geçtiyse
- Habituation factor toparlandıysa
- `memory_echo` yeniden yükseldiyse

Refresh **otomatik değil** — çekirdeğin iç basıncına bağlı.

### Forbidden

- Sınırsız TTL (kayıt sonsuz aktif kalmamalı)
- Otomatik refresh (cron-bazlı recall)
- Çekirdek dışı entity tarafından refresh tetikleme

---

## 16. Recall Failure Handling

### `RECALL_RESULT_EMPTY` event

Hiç kayıt bulunamazsa veya hepsi suppress edildiyse:

```
RecallResultEmptyEvent
├── recall_request_id
├── reason
│   ├── no_matching_record           # M2'de uygun kayıt yok
│   ├── all_matches_quarantined      # var ama hepsi quarantined
│   ├── all_matches_expired          # var ama hepsi süresi dolmuş
│   ├── recall_budget_exhausted      # bütçe bitti
│   ├── cooldown_active              # cooldown aktif
│   └── scope_too_narrow             # scope kayıt bulamadı
├── candidate_count                  # değerlendirilen aday sayısı
├── suppressed_count                 # suppress edilen sayı
└── observer_snapshot_ref
```

### Critical kural — çekirdeğe "yokluk payload'ı" basmaz

> *Recall failure audit edilir.*
> *Core'a "yokluk payload'ı" basılmaz.*

Eğer çekirdeğe "boş recall" duyusal event olarak girerse, sistem **yokluğu hissetmeye** başlar — bu kendi başına bir karar modülü tehlikesidir (gate "boş hatırlatma" diye sistemi pasifize edebilir).

Doğru davranış: failure observer'a kayıtlı, çekirdeğe doğrudan dönüş yok. Eğer yokluk basıncı gerekirse, **dolaylı** olarak self-field / contradiction tarafında doğal yaşanır (örn. çekirdek hatırlatma bekliyordu, gelmedi → unresolved intention pressure birikir → bu çekirdeğin kendi içsel sürecidir).

### Forbidden

- Çekirdeğe boş RecallEvent basmak
- "Yokluk payload'ı" üretmek
- Failure'ı sessizce geçmek (M1 audit zorunlu)

---

## 17. Human-Requested Recall

### Principle

İnsan recall talebi **doğrudan RecallEvent üretmez**. `HumanIntentEvent` olarak girer; çekirdek kendi `memory_echo` gerilimi yükselirse kendi RecallRequest'ini doğurur.

### Akış

```
İnsan: "Bana 2025-12-15'teki kill-switch olayını hatırlat"
    ↓
LLM translator (M3 bağlamlı)
    ↓
HumanIntentEvent { profile: recall_request }
    ↓
WORLD_INGRESS §11 — deterministic compiler
    ↓
neural_seed (memory_echo + curiosity-like + uncertainty seed)
    ↓
çekirdek bu seed'i duyusal uyaran olarak yaşar
    ↓
memory_echo tension yükselirse + recall economy uygunsa
    ↓
çekirdek kendi RecallRequest'ini üretir
    ↓
M2 search
    ↓
RecallEvent
    ↓
WORLD_INGRESS compiler → neural_seed
    ↓
core
```

### Kilit kural

> **İnsan recall talebi tetikleyicidir, doğrudan recall değildir.**

### Önemli özellikler

- Çekirdek autonomous kalır — kendi içsel durumuna göre yanıt verir
- İnsan isteği hiç ignore edilmez — HumanIntentEvent M1'de kayıtlı
- Madde 7 korunur — hafıza emir vermez, hatırlatma gönderir
- Madde 6 korunur — LLM payload yazmaz, deterministic compiler tonu belirler
- Recall economy bypass edilemez — insan sürekli zorlayamaz, fatigue/cost devreye girer

### Forbidden

- İnsan'ın doğrudan M2'den RecallEvent bastırması
- LLM'in çekirdeğe recall payload yazması
- Recall economy'yi insan isteğiyle bypass etme
- Çekirdeğin "istemiyorum" deme hakkının elinden alınması

---

## 18. Operational Audit — Ayrı Kanal

### Principle

İnsan **kill-switch geçmişini göster** veya **dünkü gate kararlarını listele** gibi operasyonel sorgular yaparsa, bu **RecallEvent değildir**. M1 audit okumasıdır.

### Akış

```
Human audit request (operatör)
    ↓
M1 read (OBSERVER_LEDGER §16 read permission matrix)
    ↓
M1_HUMAN_READ meta-event (audit-of-audit)
    ↓
sonuç insana gider (UI / rapor / Telegram)
    ↓
çekirdeğe gitmez
```

### Critical ayrım

| Kanal | Yön | Çekirdeğe etki |
|-------|-----|---------------|
| **Recall** | M2 → core (sensory ingress) | Evet (neural_seed) |
| **Operational audit** | M1 → human (UI/report) | Hayır |

Bu iki kanal **karışmamalı**. İnsan audit isteği "ben görmek istiyorum" demektir; recall talebi "sistem hatırlatsın" demektir.

### Forbidden

- Audit okuma sonucunun çekirdeğe payload_seed olarak girmesi
- Recall sonucunun insan UI'ına raporlanması (RecallEvent çekirdek-içi, audit insan-içi)
- İki kanalın tek event tipinde birleştirilmesi

---

## 19. Observer Recall Events

OBSERVER_LEDGER §19'daki memory family event'leri:

```
RECALL_REQUEST_SENT              # çekirdek RecallRequest çıkardı
RECALL_EVENT_INGESTED            # M2'den RecallEvent çekirdeğe girdi
RECALL_RESULT_EMPTY              # failure (§16)
RECALL_SUPPRESSED                # bireysel kayıt suppress edildi (cooldown/habituation/status)
```

### RECALL_REQUEST_SENT şeması

```
RecallRequestSentEvent
├── event_id
├── request_id
├── trigger_pressure_summary
├── scope_summary
├── recall_budget
└── observer_snapshot_ref
```

### RECALL_EVENT_INGESTED şeması

```
RecallEventIngestedEvent
├── event_id
├── recall_event_id
├── memory_record_id
├── subject_class
├── status_band
├── retrieval_relevance
├── neural_seed_intensity
├── alternates_count
└── observer_snapshot_ref
```

### Permanence policy

```
(RECALL_REQUEST_SENT, *)         → ring_buffer_only  (yüksek frekans)
(RECALL_EVENT_INGESTED, *)       → ring_buffer_only
(RECALL_RESULT_EMPTY, *)         → permanent          (failure audit kritik)
(RECALL_SUPPRESSED, *)           → ring_buffer_only
```

Bu OBSERVER_LEDGER §10 permanence policy'sine eklenir (yan patch).

---

## 20. Cross-document Anchors

| Belge | Bağlantı |
|-------|----------|
| `CONSTITUTION.md` Madde 7 | Hafıza ayrılığı; bu belge M2 okuma yolu detayı |
| `MEMORY_CONTRACT.md` §5 (Recall Flow) | Ana flow tanımı |
| `MEMORY_CONTRACT.md` §6 (Recall Economy) | Cost/cooldown/habituation kavramları |
| `WORLD_INGRESS.md` §10 (RecallEvent Boundary) | RecallEvent şeması, compiler kuralı |
| `WORLD_INGRESS.md` §11 (HumanIntentEvent Boundary) | İnsan recall talebi ingress'i (§17) |
| `WORLD_INGRESS.md` §16 (SourceTrustRecord) | source_trust subject_class recall davranışı |
| `OBSERVER_LEDGER_SCHEMA.md` §16 (Read Permission Matrix) | İnsan/LLM/replay M2 read yetkisi |
| `OBSERVER_LEDGER_SCHEMA.md` §19 (Event Catalog) | RECALL_* event tipleri |
| `MEMORY_WRITE_GATE.md` §9 (Status Machine) | Quarantined recall üretmez |
| `MEMORY_WRITE_GATE.md` §17 (Status Events) | Status değişimleri recall davranışını etkiler |
| `ATTENTION_WORKSPACE.md` §11 (Context Signature) | Context iç durum karakteri (scope için) |
| `ATTENTION_WORKSPACE.md` §16 (Pulse/Recall Boundary) | Pulse recall doğurabilir ama tek başına yetmez |

---

## 21. Violation Tests

1. **Recall retrieval gibi mi konumlandırılmış?** (§4)
   - Evet ise ihlal. Recall sensory ingress'tir.
2. **Çekirdek M2'yi doğrudan sorguluyor mu?** (§4, §5)
   - Evet ise ihlal.
3. **Summarizer / replay / human / LLM core'a doğrudan RecallEvent enjekte edebiliyor mu?** (§5)
   - Evet ise ihlal.
4. **Quarantined / rejected / expired kayıt RecallEvent üretiyor mu?** (§12)
   - Evet ise ihlal.
5. **Candidate kayıt verified intensity ile mi dönüyor?** (§12, §13)
   - Evet ise ihlal. Capped intensity.
6. **Candidate recall narrative/causal/episodic/structured_fact için açık mı?** (§13)
   - Evet ise ihlal. Sadece source_trust ve procedural.
7. **Ranking hakikat sıralaması olarak mı konumlandırılmış?** (§9)
   - Evet ise ihlal.
8. **Multi-record çekirdeğe çoklu RecallEvent dönüyor mu?** (§10)
   - Evet ise ihlal. Top-1 core, alternates observer.
9. **Recall economy bypass edilebiliyor mu?** (§14)
   - Evet ise ihlal.
10. **Recall failure çekirdeğe payload_seed olarak basılıyor mu?** (§16)
    - Evet ise ihlal. Audit M1'de, çekirdeğe yokluk basılmaz.
11. **İnsan recall talebi doğrudan RecallEvent üretiyor mu?** (§17)
    - Evet ise ihlal. HumanIntentEvent tetikleyici, çekirdek kendi recall'ını doğurur.
12. **Operasyonel audit RecallEvent kanalıyla mı yapılıyor?** (§18)
    - Evet ise ihlal. Audit M1 human read; recall ayrı kanal.
13. **Recall scope dış dünya etiketi içeriyor mu (BTCUSDT, vs.)?** (§8)
    - Evet ise ihlal.
14. **Recall repetition evidence sayılıyor mu?** (§14)
    - Evet ise ihlal. Repeated recall is not evidence.
15. **RecallEvent Memory Write Gate'i bypass edebiliyor mu (verified gibi davranıp)?** 
    - Evet ise ihlal.
16. **Status_band field RecallEvent'te explicit mi?** (§11, §12)
    - Hayır ise ihlal. Compiler intensity modülasyonu için zorunlu.
17. **Çekirdek M2 raw content olarak fact almıyor değil mi?** (§11)
    - Alıyorsa ihlal. Sadece neural_seed.

---

## 22. Open Questions

H çerçevesi kapanırken cevaplanmamış bırakılan sorular:

- **Kesin recall_threshold ve recall_pressure formülü** → Implementation
- **base_ttl, refractory_period, cooldown sayısal değerleri** → Implementation
- **M2 search engine implementation** (vector similarity, sql, hybrid) → Implementation
- **context_signature_similarity_band hesaplama** → Implementation + ATTENTION §11 ile uyum
- **alternates sayısı limiti** (kaç aday observer'a kayıtlı, eski olanlar nasıl tasfiye) → Implementation
- **subject_class_complexity recall_cost'a nasıl yansır** → Sayısal tuning
- **RecallEvent'ten sonra outcome alignment nasıl tracking edilir** (recall'ın faydalı olup olmadığı) → MEMORY_WRITE_GATE_NUMERICS + replay ile bağlantılı
- **Concurrent RecallRequest'ler** — aynı anda iki RecallRequest doğarsa nasıl handle edilir → Implementation
- **Refresh policy** — çekirdek aynı record'u N kere recall etti, bu pattern habituation üretir mi yoksa "bu record kritik" sinyali mi? → Tuning

Bu sorular cevaplanmadan implementation aşamasına geçilmez.

---

## Çekirdek özet — 13 karar + 17 kırmızı çizgi

### 13 ana karar
1. Recall retrieval değildir; sensory ingress'tir.
2. Çekirdek M2'yi doğrudan sorgulamaz.
3. RecallRequest sadece core-originated (memory_echo tension).
4. Summarizer/replay/human/LLM core'a RecallEvent enjekte edemez.
5. Recall scope hybrid (subject_class + status + context similarity + economy).
6. Scope dış dünya etiketi taşımaz.
7. Ranking delivery'dir, hakikat değil.
8. Multi-record sonuçta core'a top-1 RecallEvent; alternates observer'da.
9. Quarantined/rejected/expired RecallEvent üretmez.
10. Candidate recall sadece source_trust ve procedural için, capped intensity.
11. İnsan recall talebi HumanIntentEvent → çekirdek kendi RecallRequest'i.
12. Operasyonel audit ayrı kanal (M1 human read), recall değil.
13. Recall failure M1'e yazılır; çekirdeğe yokluk payload'ı dönmez.

### 17 kırmızı çizgi
Bkz. §21.

---

## Kilit cümleler

> **RecallEvent gerçek değildir. RecallEvent kaynaklı hatırlatmadır.**
>
> **Recall is not retrieval. Recall is sensory ingress.**
>
> **Hafıza çekirdeğe emir vermez. Hafıza çekirdeğe hatırlatma gönderir.**
>
> **Recall ranking truth ranking değildir. Recall ranking delivery ranking'dir.**
>
> **Recall geçmişi getirir, ama şimdiyi boğamaz.**
>
> **Recall bedelsiz değildir.**
>
> **İnsan recall talebi tetikleyicidir, doğrudan recall değildir.**
>
> **Hatırlatma = core-facing RecallEvent. Audit okuma = human-facing M1 read. İkisi karışmamalı.**
>
> **Repeated recall is not evidence.**
>
> **Recall failure audit edilir. Çekirdeğe yokluk payload'ı basılmaz.**

---

## Versiyon

- **v0.1** — 18 Mayıs 2026 — Frozen Draft. Conceptual phase. No implementation authority.
- `CONSTITUTION.md` Madde 7 / `MEMORY_CONTRACT.md` §5-6 alt-spec'i.
- G `MEMORY_WRITE_GATE`'in çift kapısı (M2 okuma yolu).
- Konuşma soyağacı: [`docs/conversations/0008-recall-protocol.md`](./docs/conversations/0008-recall-protocol.md)
