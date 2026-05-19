# ADAPTER_MANIFEST_SPEC.md

## Sentinel — Dış Uzuv Kontratı

---

## Status

**Frozen Draft v0.1**
**Conceptual phase. No implementation authority.**

Bu belge `CONSTITUTION.md` Madde 1/3/5/6/7 ile uyumlu bir alt-spec'tir. Yeni anayasa maddesi değildir. Çalışan bir adapter framework'ünün implementation spec'i değildir. Sentinel'in dış uzuvlarının (adapters) sisteme **hangi kontratla bağlandığını, hangi yetkileri taşıdığını, hangi sınırlarda davrandığını ve nasıl audit edildiğini** tanımlar.

---

## 1. Purpose

A turunda Halit'in başlangıç vizyonu:

> *İnsan beyni gibi sonradan buna uzuvlar bir şablonda bir standartta eklenmesi çok kolay olacak.*

A-H boyunca adapter konsepti her belgede kullanıldı ama tam kontratı yazılmadı:
- WORLD_INGRESS §9 — `adapter_capabilities_snapshot` ObservationEvent'te
- WORLD_INGRESS §16 — `SourceTrustRecord` adapter reliability
- BOOTSTRAP_GENOME §20 — bootstrap M2'de `adapter_manifest_refs`
- DEONTIC_GATE §8 Rule 7 — "no action if execution adapter lacks valid manifest snapshot"
- MEMORY_CONTRACT M2 — subject_class adapter refs

I bu dağınık referansları **tek kontrat** altında toplar + adapter'ın ne yapabildiği/yapamadığını biçimselleştirir.

Damıtma:

> **Adapter sistemin uzvudur. Adapter sistemin beyni değildir.**
>
> **Adapter çekirdeği bilmez. Adapter sadece kendi yeteneklerini deklare eder.**
>
> **Çekirdek adapter'ı bilmez. Çekirdek sadece adapter'dan gelen kaynaklı olayları yaşar.**

---

## 2. Constitutional Position

Bu belge yeni anayasa maddesi değildir; mevcut maddelerin dış uzuv teması için detay sözleşmesidir:

- **Madde 1** (Nöron homojen, payload heterojen): Adapter tipi yok; tek manifest mekanizması, capability imzası.
- **Madde 3** (Minimum genome): Adapter doğuştan gelmez; deneyimle takılır.
- **Madde 5** (Self-field / Deontic gate): Adapter eylem çıkışı deontic gate'e tabi.
- **Madde 6** (LLM dış tercüman): LLM özel bir adapter tipi (translator); execution adapter'a doğrudan yol yok.
- **Madde 7** (Hafıza ayrılığı): Adapter M0'a yazamaz; M1 yazımı observer üzerinden; M2 yazımı Memory Write Gate'ten.

I bu çerçevenin **biçimsel ve uygulanabilir** halini verir.

---

## 3. Core Principle — Adapter Is a Limb, Not a Brain Part

> **Adapter yetenek bildirir. Sistem sınır uygular. Çekirdek sadece kaynaklı olayların nöral etkisini yaşar.**

Bu cümle belgenin kilididir.

---

## 4. Adapter Identity vs Constitutional Type

### Principle

Adapter'ın **adı** olabilir. Adapter'ın **domain'i** olabilir. Ama adapter'ın **anayasal tipi yoktur**.

### Rationale

A-H boyunca her seviyede Madde 1 yansıdı (nöron, pulse, ingress, genome, gate, event family, gate test, recall ranking). Adapter seviyesinde aynı disiplin: tek mekanizma, capability imzası.

### Allowed

```
adapter_identity:
  adapter_name: "binance_spot_v1"
  domain_label: "exchange/binance"        # observer/provenance için
  vendor: "human-readable label"
  version: "v1.2.3"
```

`adapter_name`, `domain_label`, `vendor`, `version` **observer-side** alanlardır. Çekirdeğe **sızmaz**. Sistemin gördüğü şey **capability_surface + channel_bindings + authority_bounds**.

### Forbidden

- Adapter constitutional type kategorisi (`TradeAdapter`, `NewsAdapter`, `ExecutionAdapter`)
- Çekirdeğe adapter ismi sızdırmak
- Adapter'a göre farklı çekirdek davranışı

### Violation Test
> *Bu öneri adapter'ın anayasal tipini, çekirdek seviyesinde davranış sınıfı yapıyor mu?*
>
> Evet ise ihlal.

---

## 5. Manifest Schema

### Yapı

```
AdapterManifest (immutable, signed artifact)
│
├── identity
│   ├── manifest_id
│   ├── adapter_name                      # human-readable
│   ├── domain_label                      # observer/provenance için
│   ├── vendor
│   ├── version
│   ├── signed_by
│   └── signature
│
├── capability_surface
│   ├── observe                           # bool
│   ├── execute                           # bool
│   ├── recall_provider                   # bool
│   ├── memory_writer                     # bool
│   ├── intent_relay                      # bool (LLM translator için)
│   └── ...                               # genişletilebilir, ama belge revizyonu gerekir
│
├── capability_bindings
│   └── { per-capability channel binding } # §7 detayı
│
├── compatibility_constraints
│   ├── incompatible_with                 # §8
│   └── required_pairs                    # §9
│
├── trust_profile
│   └── initial_reliability_band          # AdapterTrustRecord başlangıç (§11)
│
└── manifest_hash                         # tüm field'ların hash'i
```

### Notlar

- `manifest_id` unique
- `signed_by` insan veya signed administrative reference
- `manifest_hash` bütün manifest'in tek hash imzası — runtime integrity için

---

## 6. Manifest Immutability and Versioning

### Principle

**Manifest immutable signed artifact'tir.** Runtime'da mutate edilemez. Yeni adapter sürümü = yeni manifest hash'i.

### Rationale

Manifest mutate edilebilirse, adapter capability'lerini "kayar" — yaptığı şey değişir ama sistem bunu bilmez. Madde 7 (audit) ihlali. Doğru: immutable + versioning + status transition.

### Allowed

```
Adapter v1.0 active
    ↓ (yeni sürüm gelir)
Adapter v1.0 → "superseded"
Adapter v1.1 → "registered" → "verified" → "active"
    ↓
M1: ADAPTER_MANIFEST_STATUS_CHANGED (v1.0 active → superseded)
M1: ADAPTER_MANIFEST_STATUS_CHANGED (v1.1 registered → verified)
M1: ADAPTER_MANIFEST_STATUS_CHANGED (v1.1 verified → active)
```

### Forbidden

- Runtime mutation (var olan manifest field'larını değiştirme)
- Capability flag'in dinamik açılması/kapanması
- `manifest_hash` değişimi olmadan capability değişimi
- "Hot reload" ile manifest güncellemesi
- Versioning yapmadan adapter yenileme

### Versioning kural

Yeni manifest sürümünde:
- Yeni `manifest_id`
- Yeni `manifest_hash`
- Önceki manifest'e `parent_manifest_id` referansı (opsiyonel, audit için)
- Önceki manifest "superseded" statüsüne geçer (M1 audit)

### Violation Test
> *Çalışan adapter'ın manifest'i runtime'da değişebiliyor mu?*
>
> Evet ise ihlal.

---

## 7. Capability Flags + Channel Bindings

### Principle

> **Capability declares what the adapter can technically do.**
> **Channel binding declares how it is allowed to touch the system.**

Capability flag tek başına yetki **değildir**. Her capability bir **channel binding** ile gelir.

### Capability flag yapısı

```
capability_surface:
  observe:               true | false
  execute:               true | false
  recall_provider:       true | false
  memory_writer:         true | false
  intent_relay:          true | false
```

### Channel binding şeması

Her capability için:

```
capability_bindings:
  
  observe:
    input_channel: external_source
    output_channel: ObservationEvent
    required_gate_ref: ingress_compiler
    m1_write_scope: none
    m2_write_scope: none
    m2_read_scope: none
    rate_limit_band: <band>
  
  execute:
    input_channel: ApprovedActionIntent      # core → deontic gate'ten geçmiş
    output_channel: ExecutionResultEvent
    required_gate_ref: deontic_gate
                     + active_operational_policy
    m1_write_scope: none
    m2_write_scope: none
    kill_switch_respect: true
    no_direct_llm_route: true
    no_direct_human_route: true
    rate_limit_band: <band>
  
  recall_provider:
    input_channel: RecallRequest             # sadece core-originated
    output_channel: RecallEvent
    required_gate_ref: none (read-only)
    m1_write_scope: none
    m2_write_scope: none
    m2_read_scope: subject_class_filtered
    rate_limit_band: bounded_by_recall_economy
  
  memory_writer:
    input_channel: CandidateMemoryRecord
    output_channel: MEMORY_RECORD_STATUS_CHANGED audit
    required_gate_ref: memory_write_gate
    m1_write_scope: own_decisions_audit_only
    m2_write_scope: gated_subject_classes
    rate_limit_band: <band>
  
  intent_relay:                              # LLM translator için
    input_channel: human_natural_language
    output_channel: HumanIntentEvent
    required_gate_ref: ingress_compiler
    m1_write_scope: none
    m2_write_scope: none
    m3_write_scope: own_translator_memory    # Madde 6 / M3 ayrık
    rate_limit_band: <band>
```

### Kritik kurallar

- Her capability **explicit channel binding** taşır
- Implicit yetki **yok** — her şey deklare edilmiş olmalı
- `required_gate_ref` adapter'ın hangi gate'ten geçmiş input kabul ettiğini söyler
- `m1_write_scope` / `m2_write_scope` adapter'ın hafıza erişim yetkisi
- `rate_limit_band` rate limiting band'ı (kesin sayı implementation)

### Forbidden

- Channel binding olmadan capability flag
- Implicit yetki (capability "ne yapar" tanımsız)
- Capability'nin manifest'te declared olmayan channel'a yazması

---

## 8. Capability Incompatibility Matrix

### Principle

Bazı capability'ler **aynı adapter'da olamaz** — security separation gereği. Çakışan capability set'i = invalid manifest = registered olamaz.

### Incompatible pairs

```
execute + intent_relay:
    LLM kanalı (intent_relay) ile execution kanalı aynı entity'de olamaz.
    Yoksa LLM dolaylı olarak execution adapter'a yol bulabilir.
    Madde 6 + DEONTIC §8 Rule 4 koruması.

execute + recall_provider:
    M2 reader olan adapter ayrıca eyleme geçemez.
    M2 manipulation + action coupling self-deception kapısı.

execute + memory_writer:
    Action + M2 write aynı yerde olmaz.
    Gate bypass riski (adapter kendi kararını M2'ye verified olarak yazıp
    sonra ona dayanarak action çıkartabilir).

recall_provider + memory_writer:
    M2 read + M2 write aynı adapter'da olmaz.
    Kendi yazdığını okumak gibi (self-deception, infinite reinforcement).

intent_relay + memory_writer:
    LLM'in M2'ye yazma kanalı olmamalı (Madde 6).
    LLM zaten payload yazamaz; M2 yazımı için ayrı kanal gerek.
```

### Validity check

Manifest registered olabilmesi için:

```
for (cap_a, cap_b) in incompatible_pairs:
    if capability_surface[cap_a] AND capability_surface[cap_b]:
        manifest is INVALID
        registration fails
```

### Rationale

Bu matrix **belge revizyonu ile** genişletilir/daraltılır; runtime'da değişmez. Yeni incompatible pair eklemek = `safety_tightening` compatibility class (BOOTSTRAP §23).

### Forbidden

- Incompatible pair taşıyan manifest'in register edilmesi
- Runtime'da matrix'in değişmesi
- Capability "yorumla bypass" — "ben execute değilim, ben sadece order verim"

### Violation Test
> *Manifest incompatible capability pair'i içeriyor mu?*
>
> Evet ise registration reject.

---

## 9. Required Capability Pairs

### Principle

Bazı capability'ler **birbirini gerektirir** — fonksiyonel zorunluluk.

### Tek required pair (şimdilik)

```
execute → must_have observe (feedback-only)
```

### Kritik kısıt — efference observation only

> *`execute → observe` zorunluluğu, adapter'ın genel observation provider olması anlamına gelmez.*
> *Required pair `execute → observe` is limited to efference/feedback observation. It does not grant general ObservationEvent authority unless separately declared.*

Yani execute eden adapter'ın observe capability'si **sadece kendi eyleminin sonuçlarını** raporlayabilir:

```
allowed efference observation:
    execution_result
    fill_status
    latency
    reject_reason
    order_status_change
    post_action_market_snapshot (sadece kendi eyleminin sonucu)

forbidden general observation:
    raw market data (genel)
    news feeds
    other adapters' subjects
    cross-domain observation
```

Genel observation authority için **observe capability ayrı deklare edilmek zorunda** ve channel binding'inde `scope: general` veya `scope: efference_only` field'ı olmalı.

### Manifest field

```
capability_bindings:
  observe:
    scope: "efference_only" | "general"
    ...
```

`scope: efference_only` adapter sadece kendi eyleminin sonuçlarını yayınlar; `scope: general` adapter ortam observation'ları yayınlar.

### Forbidden

- Execute capability'sinin otomatik genel observation kazanması
- Efference observation ile genel observation'ın aynı capability binding'de karıştırılması
- Scope tanımlanmamış observe capability

### Violation Test
> *Execute capability'si genel observation authority'sini implicit alıyor mu?*
>
> Evet ise ihlal. Genel observation explicit declared olmalı.

---

## 10. Execution Capability — Special Hard Constraints

### Principle

`can_execute = true` **tek başına yetki değildir**. Birden fazla hard constraint zorunlu.

### Zorunlu şartlar

```
can_execute = true requires ALL OF:
  - valid_manifest_signature
  - active_operational_policy_ref (DEONTIC §7)
  - deontic_gate_ref
  - audit_path_available
  - adapter_write_scope explicitly declared
  - kill_switch_respect = true
  - no_direct_llm_route = true
  - no_direct_human_route = true (audit kanalı hariç)
  - rate_limit_band declared
  - efference_observation declared (Required Pair §9)
```

### Doğru execution akış

```
core intention
    ↓
deontic gate (DEONTIC §11)
    ↓ (geçerse)
ApprovedActionIntent envelope
    ↓
execution adapter
    ↓
external action
    ↓
ExecutionResultEvent (efference observation)
    ↓
WORLD_INGRESS deterministic compiler
    ↓
neural_seed (kendi eyleminin sonucu — WORLD_INGRESS §20)
    ↓
core
```

### Forbidden execution paths

```
❌ LLM → execution adapter         (Madde 6, DEONTIC §8 Rule 4)
❌ Human → execution adapter        (audit kanalı hariç direct route yok)
❌ Core → execution adapter         (gate'siz)
❌ Adapter → adapter direct call    (cross-adapter bypass)
❌ Summarizer → execution adapter
```

### Kilit kural

> *Execution capability hiçbir zaman direct command surface değildir.*
> *Sadece deontic gate'ten geçmiş ApprovedActionIntent'i kabul eder.*

### Kill-switch sırasında

Kill-switch aktif iken:
- Execution adapter `kill_switch_active = true` durumunu okumalı
- Hiçbir koşulda eylem çıkarmamalı
- ApprovedActionIntent gelse bile reject etmeli (gate normalde göndermez ama defense in depth)
- DEONTIC §16'daki Read/Write Behavior tablosuyla uyumlu

### Violation Test
> *Execute capability declaration'ı yukarıdaki tüm hard constraint'leri taşıyor mu?*
>
> Hayır ise manifest invalid.

---

## 11. AdapterTrustRecord (M2 subject_class)

### Principle

Adapter güvenirliği `AdapterTrustRecord` olarak M2'de yaşar — `subject_class = "adapter_trust"`. Yeni hafıza katmanı değil, M2'nin alt-tipi (SourceTrustRecord pattern'i ile aynı).

### Yapı

```
AdapterTrustRecord (M2, subject_class = "adapter_trust")
├── adapter_manifest_id
├── current_reliability_band
├── health_evidence_refs               # M1 event refs
├── stale_event_rate
├── error_rate
├── schema_violation_count
├── latency_band
├── manifest_signature_valid           # signature check sonucu
├── linked_source_trust_records[]      # bu adapter hangi source'ları taşıyor
├── status                              # candidate | verified | active | superseded | rejected | expired | quarantined
├── provenance                          # human | observer | system
└── updated_at
```

### Yetki

- `MEMORY_CONTRACT.md` §10 CandidateMemoryRecord statü zinciri aynen geçerli
- Sistem-kaynaklı reliability değişimleri Memory Write Gate'ten geçer (G §7)
- İnsan elle reliability değiştirebilir (`provenance: human`)

### Verification matrix (G §8)

```
adapter_trust verified için:
    sustained_health_pattern
    AND manifest_signature_valid
    AND schema_violation_count below threshold
    AND replay_survival
    AND provenance_recorded
```

---

## 12. SourceTrust vs AdapterTrust — Cross-link

### İki kavramın farkı

```
AdapterTrustRecord:
    Uzvun kendisinin güvenirliği.
    "binance_adapter_v3 son 24 saatte stale event üretiyor mu?"
    "Bu adapter manifest'i hâlâ valid mi?"
    "Bu adapter'ın error_rate'i nasıl?"

SourceTrustRecord:
    Uzvun TAŞIDIĞI kaynağın güvenirliği.
    "Binance orderbook observation'ları outcome ile ne kadar uyumlu?"
    "Bu source son 100 prediction'da kaç kez tutarsız çıktı?"
```

### Multi-source adapter

Bir adapter birden fazla source taşıyabilir:

```
adapter = news_aggregator_v1
sources = [reuters, bloomberg, twitter, official_fed]

AdapterTrustRecord:
    adapter_manifest_id: news_aggregator_v1
    linked_source_trust_records: [
        source_trust:reuters,
        source_trust:bloomberg,
        source_trust:twitter,
        source_trust:official_fed
    ]
```

Her source'un ayrı SourceTrustRecord'u; adapter'ın kendi AdapterTrustRecord'u onları link eder.

### Cross-link kuralları

- Adapter degraded olursa, taşıdığı tüm source'lar etkilenebilir (reliability_band düşer)
- Bir source corrupt olursa, adapter health bilinmez (sadece o source etkilenir)
- Adapter manifest_signature_invalid → tüm linked source'lar otomatik quarantined

### Forbidden

- AdapterTrust ile SourceTrust'ı tek subject_class'a indirgemek
- Cross-link olmadan adapter trust değişimi yapmak

---

## 13. Adapter Lifecycle

### Statüler

```
registered
    ↓ (verification)
verified
    ↓ (activation)
active
    ↓
degraded     (health pattern bozuldu)
    ↓
suspended    (geçici pause)
    ↓
deactivated  (insan tarafından devre dışı)
    ↓
superseded   (yeni manifest geldi)
    ↓
revoked      (security/incident sonucu kalıcı yasak)
```

### Statü geçişleri

| Geçiş | Trigger | Gate |
|-------|---------|------|
| registered → verified | manifest signature + capability validation | sistem otomatik |
| verified → active | human approval (DEONTIC §18'deki normal flow) | insan onayı |
| active → degraded | AdapterTrust reliability düştü | sistem otomatik |
| degraded → suspended | reliability eşiği altına indi | sistem otomatik |
| suspended → active | manuel re-validation | insan onayı |
| active → deactivated | insan kararı | insan |
| deactivated → revoked | security incident, calabasification | insan + DEONTIC review |
| active → superseded | yeni manifest verified → active oldu | sistem otomatik |

### Statü özellikleri

| Statü | Capability aktif? | Ne yapabilir? |
|-------|-------------------|---------------|
| `registered` | Hayır | Bekleme |
| `verified` | Hayır | Aktive edilmeyi bekler |
| `active` | Evet | Tam capability |
| `degraded` | Kısmen | Read-only veya rate-limited (subject_class'a göre) |
| `suspended` | Hayır | Pause |
| `deactivated` | Hayır | Devre dışı |
| `superseded` | Hayır | Eski sürüm, audit history |
| `revoked` | Hayır | Kalıcı yasak |

### Forbidden

- Lifecycle statüsünün direkt mutation'la atlanması
- `revoked` adapter'ın re-register edilmesi (yeni manifest_id zorunlu)
- Statü değişimi M1'e audit yazılmadan

---

## 14. ADAPTER_MANIFEST_STATUS_CHANGED Canonical Event

### Principle

Tek canonical event tipi (B/C/E/F/G/H disiplini). Alt durumlar `old_status` / `new_status` field'larıyla.

### Şema

```
AdapterManifestStatusChangedEvent
├── event_id
├── event_type: ADAPTER_MANIFEST_STATUS_CHANGED
├── event_family: ledger_meta             # adapter lifecycle audit-meta
├── adapter_manifest_id
├── manifest_hash
├── parent_manifest_id                    # opsiyonel (versioning için)
├── old_status                            # registered|verified|active|degraded|...
├── new_status
├── reason
│   ├── manual_human_decision
│   ├── verification_passed
│   ├── verification_failed
│   ├── reliability_degradation
│   ├── security_incident
│   ├── superseded_by_new_version
│   ├── kill_switch_event
│   └── audit_violation
├── evidence_refs                          # M1 event refs (health metrics, vs.)
├── approved_by                            # insan ise
├── linked_adapter_trust_record_ref
└── observer_snapshot_ref
```

### Eski event tipleri (kaldırıldı)

Aşağıdaki ayrı event tipleri **canonical değildir**:

```
ADAPTER_REGISTERED          → use status_change (registered)
ADAPTER_VERIFIED            → use status_change (verified)
ADAPTER_ACTIVATED           → use status_change (active)
ADAPTER_DEACTIVATED         → use status_change (deactivated)
ADAPTER_REVOKED             → use status_change (revoked)
```

OBSERVER_LEDGER §19 event catalog buna göre güncellenir (yan patch).

### Permanence policy

```
(ADAPTER_MANIFEST_STATUS_CHANGED, *)                    → permanent
(ADAPTER_MANIFEST_STATUS_CHANGED, new_status=revoked)   → permanent_with_snapshot + human_alert
(ADAPTER_MANIFEST_STATUS_CHANGED, reason=security_incident) → permanent_with_snapshot + human_alert
(ADAPTER_MANIFEST_STATUS_CHANGED, reason=kill_switch_event) → permanent_with_snapshot + human_alert
```

---

## 15. Adapter Raw Payload vs Core-Facing Neural Seed

### Principle

> *Adapter raw payload üretir.*
> *Adapter core-facing neural_seed üretmez.*
> *Core-facing neural_seed her zaman WORLD_INGRESS compiler'dan doğar.*

### Doğru akış

```
Adapter raw input (örn. binance websocket data)
    ↓
Adapter normalizes to structured event:
    - confidence
    - ttl_ms
    - magnitude_normalized
    - subject_id (observer-only)
    - raw_payload_ref (observer-only)
    ...
    ↓
WORLD_INGRESS deterministic compiler
    ↓
neural_seed (payload_seed + receptor_bias_seed + trace_seed)
    ↓
core
```

### Adapter ÜRETEMEZ

- `payload_seed = { urgency: 1.0, ... }`
- `neural_seed = ...`
- Assembly directly
- Pulse directly
- Intent (HumanIntent kanalı hariç translator için)
- Memory write content (memory_writer capability ile CandidateMemoryRecord önerir, ama gate yazar)

### Forbidden

- Adapter'ın çekirdeğe doğrudan payload basması
- Compiler'ı bypass etmek
- Adapter'ın "ben volatility high diyorum, urgency seed = 0.8" semantic mapping yapması

---

## 16. Provenance Boundary

### Adapter provenance — observer-only

```
Adapter identity:
  adapter_name      → observer
  domain_label      → observer
  vendor            → observer
  version           → observer
  manifest_id       → observer
  manifest_hash     → observer
```

Tümü **observer-side**. Çekirdek **bilmez**. Sadece compiler'a sayısal/soyut etkileri girer (`source_reliability_band`, `adapter_health_band` gibi).

### Cross-document

WORLD_INGRESS §18 (Provenance Boundary) zaten kuralı koymuştu:

> *Provenance observer'da isim olarak yaşar. Çekirdekte sadece güven, tazelik ve sürpriz etkisi olarak yaşar.*

I bu kuralın adapter seviyesindeki yansıması.

### Forbidden

- `adapter_name` çekirdeğe sızdırmak
- `domain_label` payload_seed'e flag olarak girmek
- Adapter ID'sinin assembly/pulse'a etiket olarak yapışması

---

## 17. Audit Chain

### Manifest yaşam döngüsü audit

```
Manifest registration → M1: ADAPTER_MANIFEST_STATUS_CHANGED (registered)
Verification          → M1: ADAPTER_MANIFEST_STATUS_CHANGED (verified)
Activation            → M1: ADAPTER_MANIFEST_STATUS_CHANGED (active)
Health degradation    → M1: ADAPTER_MANIFEST_STATUS_CHANGED (degraded) + AdapterTrustRecord update
Suspension            → M1: ADAPTER_MANIFEST_STATUS_CHANGED (suspended)
Revocation            → M1: ADAPTER_MANIFEST_STATUS_CHANGED (revoked) + permanent_with_snapshot
```

### Audit gereksinimi

Sistem sonradan şunları cevaplayabilmeli:
- Hangi adapter ne zaman registered oldu?
- Hangi insan verified/active onayını verdi?
- Adapter manifest hash'i hangi sürümlerden geçti?
- Hangi reliability event'leri degradation'a yol açtı?
- Hangi security incident revocation'a yol açtı?
- Adapter'ın taşıdığı source'lar bağlantılı olarak nasıl etkilendi?

Cevap verilemiyorsa adapter auditable değildir — anayasa ihlali (DEONTIC §8 Rule 8'in adapter seviyesindeki yansıması).

---

## 18. Cross-document Anchors

| Belge | Bağlantı |
|-------|----------|
| `CONSTITUTION.md` Madde 1 | Adapter type yok, capability surface var |
| `CONSTITUTION.md` Madde 3 | Adapter doğuştan değil, deneyimle |
| `CONSTITUTION.md` Madde 5 | Execution adapter deontic gate'e tabi |
| `CONSTITUTION.md` Madde 6 | LLM = special adapter (intent_relay), execution'a direct route yok |
| `CONSTITUTION.md` Madde 7 | Adapter M0/M1/M2 yetki sınırları |
| `MEMORY_CONTRACT.md` M2 subject_class | `adapter_trust` alt-tipi |
| `MEMORY_CONTRACT.md` §9 (Memory Write Gate) | memory_writer capability gate'e bağlı |
| `MEMORY_WRITE_GATE.md` §6 | Adapter candidate öneri kaynağı |
| `WORLD_INGRESS.md` §9 | `adapter_capabilities_snapshot` ObservationEvent'te |
| `WORLD_INGRESS.md` §13 (Compiler) | Adapter raw event → compiler → neural_seed |
| `WORLD_INGRESS.md` §16 (SourceTrustRecord) | Adapter cross-link |
| `WORLD_INGRESS.md` §18 (Provenance Boundary) | Adapter identity observer-only |
| `WORLD_INGRESS.md` §20 (Action-Origin Feedback) | Execution adapter efference observation |
| `OBSERVER_LEDGER_SCHEMA.md` §10 (Permanence Policy) | ADAPTER_MANIFEST_STATUS_CHANGED permanent |
| `OBSERVER_LEDGER_SCHEMA.md` §19 (Event Catalog) | ledger_meta family |
| `DEONTIC_GATE.md` §8 Rule 7 | Execution adapter valid manifest snapshot zorunlu |
| `DEONTIC_GATE.md` §11 (Block Detection) | Adapter signature check |
| `BOOTSTRAP_GENOME.md` §20 (M2 t=0) | `adapter_manifest_refs` opsiyonel bootstrap |
| `RECALL_PROTOCOL.md` §5 | recall_provider adapter scope |

---

## 19. Violation Tests

1. **Manifest runtime'da mutate edilebiliyor mu?** (§6)
   - Evet ise ihlal.
2. **Adapter constitutional type kategorisi var mı (TradeAdapter, vs.)?** (§4)
   - Evet ise ihlal.
3. **Capability flag channel binding olmadan kullanılıyor mu?** (§7)
   - Evet ise ihlal.
4. **Incompatible capability pair taşıyan manifest registered olabiliyor mu?** (§8)
   - Evet ise ihlal.
5. **Execute capability genel observation authority'sini implicit alıyor mu?** (§9)
   - Evet ise ihlal. Required pair sadece efference observation.
6. **Execute capability hard constraint'leri (manifest signature + active policy + gate + audit + kill_switch) eksik mi?** (§10)
   - Eksik ise manifest invalid.
7. **LLM/human → execution adapter direct route var mı?** (§10)
   - Evet ise ihlal.
8. **Adapter çekirdeğe payload_seed / neural_seed bastırıyor mu?** (§15)
   - Evet ise ihlal.
9. **Adapter compiler'ı bypass edebiliyor mu?** (§15)
   - Evet ise ihlal.
10. **Adapter identity (name, domain_label, vendor) çekirdeğe sızıyor mu?** (§16)
    - Evet ise ihlal.
11. **Eski event tipleri (ADAPTER_REGISTERED, vs.) canonical olarak kullanılıyor mu?** (§14)
    - Evet ise ihlal. `ADAPTER_MANIFEST_STATUS_CHANGED` tek canonical.
12. **AdapterTrust ve SourceTrust tek subject_class olarak birleştirilmiş mi?** (§11, §12)
    - Evet ise ihlal.
13. **Kill-switch aktif iken execution adapter eylem çıkartabiliyor mu?** (§10)
    - Evet ise ihlal.
14. **Manifest signature olmadan adapter active olabiliyor mu?** (§10, §14)
    - Evet ise ihlal.
15. **M2 read + M2 write yetkisi aynı adapter'da birleşmiş mi?** (§8)
    - Evet ise ihlal.
16. **Lifecycle statü değişimi M1 audit'siz yapılıyor mu?** (§17)
    - Evet ise ihlal.

---

## 20. Open Questions

I çerçevesi kapanırken cevaplanmamış bırakılan sorular:

- **Kesin reliability_band threshold'ları** (degraded geçiş) → `ADAPTER_TRUST_NUMERICS.md` / implementation
- **rate_limit_band sayısal değerleri** → Implementation
- **manifest_signature algorithm** (hangi imza şeması, key management) → Implementation security
- **Cross-adapter trust contamination** — bir adapter degraded olunca bağlantılı SourceTrust'lar nasıl etkilenir → Detail spec
- **Capability extension protocol** — yeni capability tipi eklemek için süreç (constitutional revision)
- **Adapter version migration** — eski manifest'ten yeni manifest'e geçişte M2 records (örn. adapter_trust history) nasıl migrate olur?
- **Sandbox adapters** — test/staging adapter'ları production manifest discipline'ından muaf mı, yoksa kendi ayrı statü dünyasında mı?

Bu sorular cevaplanmadan implementation aşamasına geçilmez.

---

## Çekirdek özet — 13 karar + 16 violation tests

### 13 karar
1. Adapter sistemin uzvudur, beyni değildir.
2. Adapter constitutional type yok; capability surface var.
3. Manifest immutable signed artifact.
4. Yeni adapter sürümü = yeni manifest hash'i.
5. Capability flag tek başına yetki değil; channel binding zorunlu.
6. Capability incompatibility matrix (security separation).
7. `execute → observe` zorunlu, ama sadece efference scope.
8. Execute capability multi-condition hard constraints.
9. LLM/human direct route to execution = yasak.
10. `AdapterTrustRecord` M2 subject_class; SourceTrust ile linked ama farklı.
11. Tek canonical lifecycle event: `ADAPTER_MANIFEST_STATUS_CHANGED`.
12. Adapter raw payload üretir; neural_seed compiler'dan doğar.
13. Adapter identity observer-only; çekirdeğe sızmaz.

---

## Kilit cümleler

> **Adapter sistemin uzvudur. Adapter sistemin beyni değildir.**
>
> **Adapter yetenek bildirir. Sistem sınır uygular. Çekirdek sadece kaynaklı olayların nöral etkisini yaşar.**
>
> **Capability declares what the adapter can technically do. Channel binding declares how it is allowed to touch the system.**
>
> **Execution capability is never a direct command surface. Only deontic-gate-approved action intents are accepted.**
>
> **Adapter raw payload üretir. Adapter neural_seed üretemez. Core-facing neural seed her zaman WORLD_INGRESS compiler'dan doğar.**
>
> **AdapterTrust = uzvun güvenirliği. SourceTrust = uzvun taşıdığı kaynağın güvenirliği. İkisi linked ama aynı değil.**
>
> **Required pair `execute → observe` is limited to efference/feedback observation. It does not grant general ObservationEvent authority.**

---

## Versiyon

- **v0.1** — 18 Mayıs 2026 — Frozen Draft. Conceptual phase. No implementation authority.
- A-H belgelerinin dış uzuv kontratı.
- Konuşma soyağacı: [`docs/conversations/0009-adapter-manifest-spec.md`](./docs/conversations/0009-adapter-manifest-spec.md)
