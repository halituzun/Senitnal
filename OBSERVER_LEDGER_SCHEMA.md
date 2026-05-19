# OBSERVER_LEDGER_SCHEMA.md

## Sentinel — Kanıt Defteri Şeması

---

## Status

**Frozen Draft v0.1**
**Conceptual phase. No implementation authority.**

Bu belge `CONSTITUTION.md` Madde 7'deki M1 katmanının (Observer Ledger) detaylı şemasıdır. Yeni anayasa maddesi değildir. Çalışan bir audit log implementation'ının spec'i değildir. Sentinel'in **tarihinin nasıl kaydedildiğini, hangi event'lerin nasıl yaşadığını, kimin neyi okuyup yazabildiğini ve audit zincirinin tamper-evidence olarak nasıl korunduğunu** tanımlar.

---

## 1. Purpose

A-E boyunca her belge M1'e event üretti. ~40 event tipi dağınık halde altı belgeye yayılmıştı. F bu event'lerin **ortak zarfını**, **yetki kurallarını**, **kalıcılık politikasını** ve **audit zincirini** tek yerde toplar.

Damıtma:

> **Observer karar vermez. Observer düzeltmez. Observer engellemez. Observer sadece kanıtlar.**
>
> **M1 sistemin hafızası değil, sistemin tarihinin kanıt defteridir.**
>
> **Observer neyin önemli olduğuna karar vermez. Observer sadece önceden tanımlı kanıt kurallarını uygular.**

---

## 2. Constitutional Position — Madde 7 / M1 Detail

Bu belge `CONSTITUTION.md` Madde 7 ("Hafıza ayrılığı") ve `MEMORY_CONTRACT.md` M1 (Observer Ledger) tanımının detaylı uzantısıdır.

M1 zaten tanımlı:
- İki katmanlı: fine-grain ring buffer + coarse-grain permanent log
- Append-only (coarse-grain)
- Observer dinler ve yazar, müdahale etmez

F bu yapının **şemasını, yetki kurallarını ve audit invariant'larını** verir.

---

## 3. Core Principle

> **Observer neyin önemli olduğuna karar vermez. Observer sadece önceden tanımlı kanıt kurallarını uygular.**

Bu cümle belgenin kilididir. Observer'a "yargı yetkisi" verilmez; sadece **mekanik kayıt yetkisi**. Önem kararı belge revizyonu ile yapılır (`permanence_policy`).

---

## 4. Observer Is Not a Controller

### Principle
Observer pasif bir kayıt katmanıdır. Karar üretmez, kararı değiştirmez, akışı engellemez.

### Rationale
Observer'a karar yetkisi verilirse audit'in kendisi karar zincirinin parçası olur — sistem kendi gerçekliğini değiştirebilir hale gelir. Bu Madde 7'nin "hafıza çekirdeğe emir vermez" kuralının observer seviyesindeki yansıması.

### Allowed
- Event kaydetme
- Snapshot oluşturma (önceden tanımlı kurallarla)
- Hash chain üretme
- Compaction (storage organization only)
- M1'den okuma (kayıtlı meta-event üreterek)

### Forbidden
- Event içeriğini değiştirme
- Event'i seçici olarak kaydetmeme ("bu önemsiz" diye atlamak)
- Permanence kararını dinamik yapma
- Snapshot içeriğini filtreleme
- Karar/öneri üretme
- M0'a yazma
- M2'ye doğrudan yazma (summarizer rolü ayrı, §5)
- Deontic gate'e veya self-field'e müdahale

### Violation Test
> *Observer bir hareket karar mekaniği gibi mi davranıyor?*
>
> Evet ise ihlal.

---

## 5. Observer Roles — Recorder vs Summarizer

Observer iki ayrı **görev** taşır. Aynı entity, farklı yetki seviyeleri.

### Recorder

**Görev:** Event'leri M1'e yazmak.

```
Recorder
├── pasif izler
├── permanence_policy tablosuna göre M1'e yazar
├── karar vermez
├── özet çıkarmaz
└── M2'ye yazmaz
```

### Summarizer

**Görev:** M1'i okumak, M2'ye candidate önermek.

```
Summarizer
├── M1'den okur (read audit gerekir — bkz. §16)
├── özet üretir (kuralla, "bence önemli" demez)
├── M2'ye doğrudan yazamaz
├── Memory Write Gate'e CandidateMemoryRecord önerir
└── her özetleme M1'e meta-event olarak yazılır
```

### Summarizer'ın kuralı

> *Summarizer kendi başına "önem" kararı vermez.*
> *Yalnızca önceden tanımlı observer event permanence/severity/snapshot kurallarına göre özet adayı üretir.*

Yani summarizer:
- ❌ "bence bu önemli"
- ✅ "permanence=permanent_with_snapshot + severity=high + event_family=memory/deontic → özet candidate üret"

### MEMORY_CONTRACT §11 / §14 cevabı

Bu rol ayrımı MEMORY_CONTRACT §11'deki ("Observer Relationship") ve §14'teki ("Observer dual-role") açık sorularını yapısal olarak kapatır. Detay implementation (kesin kurallar): `MEMORY_WRITE_GATE.md` ve `OBSERVER_LEDGER_NUMERICS.md` konusu.

### Violation Test
> *Recorder summary üretiyor mu? Summarizer M2'ye doğrudan yazıyor mu?*
>
> Evet ise ihlal.

---

## 6. Ledger Layers — Ring Buffer vs Permanent Log

`MEMORY_CONTRACT.md` M1'i iki katmanlı tanımlıyor. F bu yapıyı sıkılaştırır.

### Fine-grain Ring Buffer

- Son N saniyenin (kavramsal band ~60s) **tüm** event'leri
- RAM'de döner
- Eski olanlar otomatik tasfiye olur
- Kısa dönem inceleme + snapshot kaynağı
- Compaction event'i M1 coarse-grain'e yazılır

### Coarse-grain Permanent Log

- `permanence_policy`'ye göre seçilen event'ler
- Append-only, **silinemez**
- Diskte, çoklu yedekli
- Hash chain ile tamper-evidence (§14)

### Köprü mekaniği

Bir event coarse-grain'e yazıldığında, ilgili `pre/post_window` fine-grain snapshot olarak kalıcılaşır (§11). Ring buffer'daki ilgili pencere artık permanent log'un parçası.

---

## 7. Common ObserverEvent Envelope

Tüm event tipleri aynı dört envelope'u taşır:

```
ObserverEvent
│
├── audit_envelope                       # kim/ne zaman/hangi katman
│   ├── event_id                         # unique
│   ├── event_type                       # OBSERVATION_INGESTED, WORKSPACE_PULSE, ...
│   ├── event_family                     # neural | attention | memory | ingress | bootstrap | deontic | ledger_meta
│   ├── occurred_at                      # event gerçek anı
│   ├── observed_at                      # observer kaydetme anı
│   ├── source_layer                     # M0 | adapter | gate | summarizer | ...
│   ├── severity_band                    # routine | safety | critical | constitutional
│   └── human_alert_required             # bool, orthogonal
│
├── causal_envelope                      # nedensel bağlantı
│   ├── causal_refs                      # direct causes only (1-hop)
│   ├── subject_refs                     # event'in dokunduğu nesne ID'leri
│   └── correlation_id                   # multi-event causal session
│
├── event_body                           # type-specific içerik
│   └── <fields by event_type>
│
└── integrity_envelope                   # tamper evidence
    ├── permanence                       # ring_buffer_only | permanent | permanent_with_snapshot
    ├── snapshot_ref                     # varsa
    ├── previous_event_hash              # önceki permanent event (coarse-grain için)
    ├── event_hash                       # bu event'in kendi hash'i
    └── provenance                       # observer_self | replay | human_audit | ...
```

### Kritik notlar

- `event_body` adı **kasten farklı** — `payload_seed` ile karışmasın. `payload_seed` çekirdeğe giren nöral tohum; `event_body` observer kaydının içeriği.
- Dört envelope **sabit yapı**. Type-specific complexity sadece `event_body`'de.
- Audit yapan biri `audit_envelope` + `integrity_envelope`'a bakar, type'ı bilmek zorunda kalmaz.

### Kilit ayrım
> *`payload_seed` = çekirdeğe giren nöral tohum.*
> *`event_body` = observer kaydının içeriği.*

---

## 8. Event Type Discipline — Type vs Field

### Principle (anayasal)

> *Ayrı event tipi sadece farklı nedensel mekanizma varsa.*
> *Aynı mekanizmanın statü/değer değişimi field olarak yazılır.*
> *Statü field'ı olan event tipi tektir; alt durumlar `old_status` / `new_status` olarak gelir.*

### Rationale
A-E boyunca bu disiplin emerge etti: B'de `WORKSPACE_PULSE` + dissonance field, C'de `SOURCE_TRUST_STATUS_CHANGED` tek event, E'de `DEONTIC_POLICY_STATUS_CHANGED` tek event. F bu disiplini **anayasal mikro-prensip** olarak yazar.

### Allowed

- `WORKSPACE_PULSE` (tek tip, `dissonance_score`, `bandwidth_share`, vb. field)
- `SOURCE_TRUST_STATUS_CHANGED` (tek tip, `old_status`/`new_status` field)
- `DEONTIC_POLICY_STATUS_CHANGED` (tek tip, statü transition'lar field)
- `DEONTIC_BLOCKED` (tek tip, `block_class` field — routine/safety/constitutional)

### Forbidden

- `WORKSPACE_PULSE_DISSONANT` tipi (dissonance bir field, tip değil)
- `SOURCE_TRUST_VERIFIED` / `SOURCE_TRUST_REJECTED` (statü değişimi field olmalı)
- `DEONTIC_BLOCKED_ROUTINE` / `DEONTIC_BLOCKED_CRITICAL` (block_class field)
- `WORKSPACE_PULSE_HIGH_FATIGUE` (fatigue_level field)

### Violation Test
> *Yeni event tipi öneriliyor mu?*
>
> Aynı mekanizma + statü farkı ise: field olmalı.
>
> Farklı nedensel mekanizma ise: yeni tip kabul.

---

## 9. Event Families

Audit kategorizasyonu için 7 family:

```
event_family:
├── neural         (synapse update, assembly birth/merge/split/decay, contradiction peak)
├── attention      (workspace pulse, replay habituation update, dissonant attention)
├── memory         (recall request/event, memory write candidate status change, replay)
├── ingress        (observation/recall/human_intent/internal_shock ingested, dedup, ttl)
├── bootstrap      (self genesis, bootstrap m2 injection, constitutional shift)
├── deontic        (block, policy status change, bypass, kill-switch)
└── ledger_meta    (audit-of-audit: read events, summarization events, compaction)
```

### Kritik kural

> **Event family is an audit grouping, not a runtime behavior class.**

Family **tip değil, kategorizasyon**. Sistem davranışını etkilemez, sadece UI/audit/filter için.

### Forbidden

- "Neural family event'ler daha hızlı işlensin" (runtime behavior)
- "Deontic family otomatik permanent olsun" (permanence_policy o işi yapar, family değil)
- "Family'ye göre farklı retention" (retention permanence'a bağlı, family'ye değil)

### Allowed

- "Deontic family event'lerini raporda ayrı section'a yaz"
- "Attention family event'lerini filtrele"

---

## 10. Permanence Policy as Deterministic Rule Table

### Principle

Observer permanence kararını **vermez**. Önceden tanımlı `permanence_policy` tablosunu **uygular**.

### Rationale
Observer "bence bu önemli" diyebilirse karar mekaniği olur — Madde 7 ihlali. Doğru: belge revizyonu ile tanımlanmış deterministic tablo.

### Format (2D)

```
permanence_policy:
    (event_type, severity_band) → permanence_value
    (event_type, severity_band) → human_alert_required
```

İki boyutlu çünkü `safety_block` low severity'de `permanent`, yüksek severity'de `permanent_with_snapshot` olabilir.

### No-default rule

> *No event type may exist without an explicit permanence policy.*

Default permanence yok. Her event_type tabloda **açıkça** yer almak zorunda. Yeni event tipi eklenirken permanence policy de revize edilir.

Sebep:
- Default `ring_buffer_only` olursa: kritik event yanlışlıkla kaybolur
- Default `permanent` olursa: storage patlar
- En güvenli: explicit zorunluluk

### Immutability

Permanence policy **runtime'da değişmez**. Observer, summarizer, LLM, adapter — hiçbiri değiştiremez. Sadece belge revizyonu.

Change classification (BOOTSTRAP §23 ile uyumlu):

| Geçiş | Compatibility Class |
|-------|---------------------|
| `ring_buffer_only` → `permanent` | safety_tightening |
| `permanent` → `permanent_with_snapshot` | safety_tightening |
| `permanent` → `ring_buffer_only` | **forbidden** (kayıt zayıflama) |
| `permanent_with_snapshot` → `permanent` | **forbidden normally** (snapshot kaybı) |
| Yeni event_type ekleme + permanent | safety_tightening |
| Severity-bazlı policy değişimi | safety_tightening |

> *Persistence weakening is not a routine update.*

### Örnek policy table (sözel, kavramsal)

```
(SELF_GENESIS, *)                            → permanent
(BOOTSTRAP_M2_INJECTION, *)                  → permanent
(CONSTITUTIONAL_SHIFT_APPLIED, *)            → permanent
(CONSTITUTIONAL_SHIFT_AVAILABLE, *)          → permanent
(WORKSPACE_PULSE, *)                         → permanent
(DEONTIC_BLOCKED, routine_block)             → permanent
(DEONTIC_BLOCKED, safety_block low)          → permanent
(DEONTIC_BLOCKED, safety_block high)         → permanent_with_snapshot
(DEONTIC_BLOCKED, constitutional_block)      → permanent_with_snapshot + human_alert
(DEONTIC_POLICY_STATUS_CHANGED, active change) → permanent + human_alert
(DEONTIC_POLICY_STATUS_CHANGED, *)           → permanent
(DEONTIC_BYPASS_ATTEMPT, *)                  → permanent_with_snapshot + human_alert
(SUSPECTED_BYPASS_PATTERN, *)                → permanent
(KILL_SWITCH_ACTIVATED, *)                   → permanent_with_snapshot + human_alert
(KILL_SWITCH_DEACTIVATED, *)                 → permanent + human_alert
(SOURCE_TRUST_STATUS_CHANGED, *)             → permanent
(ASSEMBLY_PROMOTED_TO_IDEA, *)               → permanent
(ASSEMBLY_DECAYED, *)                        → ring_buffer_only
(ASSEMBLY_PRUNED, *)                         → permanent
(ASSEMBLY_RECALLED, *)                       → permanent
(CONTRADICTION_PEAK, *)                      → permanent
(INTENTION_FORMED, *)                        → permanent
(INTENTION_SUPPRESSED, *)                    → ring_buffer_only
(MEMORY_WRITE_PROPOSED, *)                   → permanent
(MEMORY_RECORD_STATUS_CHANGED, *)            → permanent
(MEMORY_RECORD_STATUS_CHANGED, new_status=quarantined OR self_deception_risk=HIGH) → permanent_with_snapshot
(RECALL_REQUEST_SENT, *)                     → ring_buffer_only
(RECALL_EVENT_INGESTED, *)                   → ring_buffer_only
(RECALL_RESULT_EMPTY, *)                     → permanent              # failure audit
(RECALL_SUPPRESSED, *)                       → ring_buffer_only
(OBSERVATION_INGESTED, *)                    → ring_buffer_only
(HUMAN_INTENT_INGESTED, *)                   → permanent
(INTERNAL_SHOCK_INGESTED, *)                 → permanent_with_snapshot + human_alert
(INGRESS_DEDUP_REJECTED, *)                  → ring_buffer_only
(INGRESS_TTL_EXPIRED, *)                     → ring_buffer_only
(COMPILER_MAPPING_UPDATED, *)                → permanent
(COMPILER_RULE_FAMILY_STATUS_CHANGED, *)     → permanent
(COMPILER_RULE_FAMILY_STATUS_CHANGED, new_status=archived) → permanent_with_snapshot
(COMPILER_DRIFT_WARNING, *)                  → permanent + human_alert
(INGRESS_NO_RULE_MATCH, *)                   → ring_buffer_only
(SLEEP_REPLAY_SYNAPSE_UPDATE, *)             → ring_buffer_only
(ATTENTION_REPLAY_HABITUATION_UPDATE, *)     → ring_buffer_only
(REPLAY_SESSION_STATUS_CHANGED, *)           → permanent
(REPLAY_SESSION_STATUS_CHANGED, new_status=failed) → permanent_with_snapshot
(REPLAY_SURVIVAL_EVALUATED, *)               → permanent
(REPLAY_OUTCOME_ALIGNMENT_EVALUATED, *)      → permanent
(COUNTERFACTUAL_ABLATION_PERFORMED, *)       → permanent
(BACKUP_ARTIFACT_STATUS_CHANGED, *)          → permanent
(RESTORE_OPERATION_STATUS_CHANGED, *)        → permanent
(RESTORE_OPERATION_STATUS_CHANGED, reason=manual_emergency OR new_status=failed) → permanent + human_alert
(M2_FOREIGN_MERGE_STATUS_CHANGED, *)         → permanent
(M2_FOREIGN_MERGE_STATUS_CHANGED, new_status=rejected) → permanent_with_snapshot
(M1_HISTORY_LOST_AT_RESTORE, *)              → permanent_with_snapshot + human_alert
(FORK_FROM_INSTANCE, *)                      → permanent + human_alert
(MIGRATION_FROM_INSTANCE, *)                 → permanent + human_alert
(FORGETTING_ATTACK_SUSPECTED, *)             → permanent_with_snapshot + human_alert
(NUMERICS_ARTIFACT_STATUS_CHANGED, *)        → permanent
(NUMERICS_ARTIFACT_STATUS_CHANGED, new_status=active AND compatibility_class=safety_weakening) → permanent + human_alert
(NUMERICS_ARTIFACT_STATUS_CHANGED, new_status=rejected) → permanent_with_snapshot
(NUMERICS_ARTIFACT_STATUS_CHANGED, trigger=emergency_revert) → permanent_with_snapshot + human_alert
(NUMERICS_VERSION_MISMATCH_DETECTED, *)      → permanent + human_alert
(NUMERICS_FAILSAFE_ACTIVATED, *)             → permanent_with_snapshot + human_alert
(WAKE_TO_SLEEP_TRANSITION, *)                → permanent
(SLEEP_TO_WAKE_TRANSITION, *)                → permanent
(LEDGER_COMPACTION_PERFORMED, *)             → permanent
(ADAPTER_MANIFEST_STATUS_CHANGED, *)         → permanent
(ADAPTER_MANIFEST_STATUS_CHANGED, new_status=revoked OR reason=security_incident OR reason=kill_switch_event) → permanent_with_snapshot + human_alert
(meta-events for human/LLM read, *)          → permanent
(meta-events for internal high-frequency read, *) → ring_buffer_only (batch)
```

> *Kesin değerler implementation. F sadece policy yapısını ve örnekleri anayasallaştırır.*

---

## 11. Snapshot Window Policy

### Principle
`permanent_with_snapshot` event'leri tetiklendiğinde, observer **önceden tanımlı pre/post window** kadar fine-grain ring buffer'ı snapshot olarak alır.

### Window bands (kavramsal)

```
(WORKSPACE_PULSE, *)                  pre ∈ [5s, 30s],     post ∈ [1s, 5s]
(DEONTIC_BLOCKED safety high, *)      pre ∈ [30s, 120s],   post ∈ [5s, 15s]
(DEONTIC_BLOCKED constitutional, *)   pre ∈ [60s, 300s],   post ∈ [10s, 60s]
(DEONTIC_BYPASS_ATTEMPT, *)           pre ∈ [120s, 600s],  post ∈ [30s, 120s]
(KILL_SWITCH_ACTIVATED, *)            pre ∈ [300s, 1800s], post ∈ [60s, 300s]
(INTERNAL_SHOCK_INGESTED, *)          pre ∈ [60s, 300s],   post ∈ [10s, 60s]
(SELF_GENESIS, *)                     no snapshot (t=0 audit only)
(BOOTSTRAP_M2_INJECTION, *)           no snapshot
```

Kesin değerler implementation. F sadece **band**'ları anayasallaştırır.

> **Snapshot window entries apply only when `permanence_policy` marks the event as `permanent_with_snapshot`.** Default `permanence_policy` `WORKSPACE_PULSE` için `permanent` (snapshot yok); pencere bandı yalnızca ileride açık policy revizyonuyla (örn. yüksek dissonance veya kritik attention varyantı) yükseltilirse kullanılır. Window band burada **gelecekte aktive olabilecek** policy için tanımlıdır.

### Snapshot içeriği: ham ve filtresiz

> *Observer does not decide what inside the window matters. It only preserves the window.*

Snapshot:
- ❌ Filtrelenmez
- ❌ Özetlenmez
- ❌ "Önemli event seçimi" yapılmaz
- ✅ Ring buffer penceresini olduğu gibi alır

Filtreleme observer'a karar rolü yükler — yasak.

### Sampling Risk

Yorgun veya yoğun bir sistemde 60sn'lik pencerede çok event olabilir. Sınırsız snapshot storage'ı patlatır. Bu yüzden sınırlı durumlarda **rate-limited deterministic sampling** kabul edilir — ama açık tehlike işaretiyle.

```
Default: full snapshot
If max_event_count exceeded:
    rate_limited_deterministic sampling allowed

Allowed deterministic strategies:
    - every-N event (deterministic ordering)
    - hash-based deterministic selection

Forbidden strategies:
    - semantic importance sampling
    - charge-magnitude sampling
    - "interesting to LLM" sampling
    - any non-deterministic selection
```

### Sampling açık tehlike

> *Rate-limited deterministic sampling is an emergency storage-preservation tool.*
> *It introduces information loss.*
> *Every sampled snapshot must record event_count_in_window, event_count_in_snapshot, sampling_strategy, sampling_ratio, and snapshot_hash.*

Sampling **kayıplı**. Bu kayıp her snapshot'ta açıkça kaydedilir. Audit gerektiğinde "ne kadar bilgi kayboldu, nasıl seçildi" sorulabilir.

### Violation Test
> *Snapshot semantic filtering yapıyor mu?*
> *Sampling "önemli olanları" seçiyor mu?*
>
> Birine "evet" ise ihlal.

---

## 12. SnapshotRef Schema and Sampling Rules

### `SnapshotRef` şeması

```
SnapshotRef
├── trigger_event_id                  # snapshot hangi event yüzünden alındı
├── window_policy_ref                 # hangi window policy uygulandı
├── ring_buffer_segment_id
├── pre_window_start_at
├── post_window_end_at
├── event_count_in_window             # pencerede toplam event sayısı
├── event_count_in_snapshot           # snapshot'a giren event sayısı
├── sampling_strategy                 # full | rate_limited_deterministic
├── sampling_ratio                    # rate_limited ise (örn. 1:10)
└── snapshot_hash                     # snapshot segment hash'i
```

### Integrity bağlantısı

Parent event'in `integrity_envelope` içinde `snapshot_ref` linki bulunur. Snapshot kendisi M1'in **ayrı segment**i:

```
ObserverEvent.integrity_envelope.snapshot_ref → SnapshotRef → snapshot segment
                                                                ↓
                                                          snapshot_hash
```

Parent event hash'i `snapshot_ref`'i hash'ler; snapshot'ın kendi segment hash'i ayrıca saklanır. Tamper-evidence iki katmanlı.

### Snapshot saklama

> *A permanent event may not outlive its required snapshot.*

`permanent_with_snapshot` event varsa, snapshot kaybolamaz. Compaction storage organization yapabilir ama içerik silmez.

---

## 13. Causal Reference Depth Rule

### Principle

> *`causal_refs` direct causes only — 1-hop.*

### Rationale

Sınırsız causal_refs storage patlatır. Sıfır causal_refs "neden oldu?" sorusunu cevapsız bırakır. 1-hop direkt nedensellik kayıt, uzak nedensellik **replay engine** üzerinden rekonstrükte edilir.

### Allowed

- Event B doğrudan event A tarafından tetiklendiyse: `B.causal_refs = [A.event_id]`
- A da event Z'den tetiklendiyse: Z `A.causal_refs`'inde — replay zinciri takip edebilir
- Multiple direct causes: `B.causal_refs = [A1.event_id, A2.event_id]`

### Forbidden

- Indirect causes listesi (A'nın A'nın A'sı)
- "Tüm causal history" — replay'in işi
- Causal ref hash'leme — sadece event_id

### Kural
> **Observer lokal nedenselliği kaydeder. Replay uzak nedenselliği araştırır.**

---

## 14. Hash Chain and Tamper Evidence

### Permanent log: hash chain

Coarse-grain permanent log her event için:

```
event_hash = hash(audit_envelope || causal_envelope || event_body || previous_event_hash)
```

`previous_event_hash` zinciri herhangi bir event'in geriye dönük izlenmesini sağlar. Tek event'in değiştirilmesi sonraki tüm hash'leri bozar — tamper detection.

### Ring buffer: hash chain yok

Fine-grain ring buffer için hash chain maliyeti pratik değil (saniyede yüzlerce event). Ring buffer kendisi sınırlı süre yaşar; tamper-evidence permanent log'a yapışıyor.

**İstisna:** snapshot olarak permanent log'a yazılan ring buffer pencereleri `snapshot_hash` taşır.

### Ledger Segment Hash

Periyodik olarak (her N event veya her T süre — implementation kararı) ledger segment hash'lenir:

```
LedgerSegment
├── segment_id
├── first_event_id
├── last_event_id
├── event_count
├── segment_hash
└── previous_segment_hash
```

Segment hash chain'i, daha uzun retention için yedek tamper-evidence.

### Forbidden

- Permanent log event'inin hash'siz yazılması
- `previous_event_hash` koparılması (compaction'da bile)
- Hash algoritmasının runtime'da değişmesi

---

## 15. Meta-events and Non-recursion

### Principle

> **Meta-event recording is first-order only.**
> **Meta-events do not recursively audit their own audit writes.**

### Rationale

Her okumayı yeni event olarak yazarsak infinite recursion doğar. Çözüm: meta-event'ler **birinci derece** kayıtlıdır, kendi yazımları meta-meta-event üretmez.

### Meta-event örnekleri

```
M1_HUMAN_READ                          # insan operatör M1 okudu
M1_LLM_REPORT_GENERATED                # LLM rapor üretti
M1_SUMMARY_GENERATED                   # summarizer özet üretti
M1_REPLAY_READ                         # replay engine okudu (tekil)
M1_REPLAY_READ_BATCH                   # replay engine okudu (batch)
OBSERVER_SUMMARIZATION_EVENT           # summarizer hareketi
LEDGER_COMPACTION_PERFORMED            # ledger compaction yapıldı
```

### Non-recursion kuralı

```
M1_READ → meta-event yazılır
meta-event'in yazılması → meta-meta-event YAZILMAZ
```

Bu rekursif patlamayı engeller.

### Read batching

High-frequency internal read'ler (replay engine, summarizer) **batch meta-event** olarak yazılır:

```
M1_REPLAY_READ_BATCH
├── reader_id
├── purpose                          # attention_replay | sleep_replay
├── event_family_filter              # neural | attention | ...
├── causal_scope_filter              # purpose-scoped + causal-ref bounded
├── event_count
├── time_window
├── batch_started_at
└── batch_ended_at
```

External read'ler (insan, LLM) **tekil meta-event** olarak yazılır (daha az sıklıkta, daha yüksek detay).

---

## 16. Read Permission Matrix

### Yetki tablosu

| Reader | Read scope | Audit type |
|--------|-----------|------------|
| **İnsan (operatör)** | Tam M1 (audit için) | Tekil `M1_HUMAN_READ` |
| **LLM translator** | Tam M1 (rapor için) | Tekil `M1_LLM_REPORT_GENERATED` |
| **Summarizer** | Tam M1 (özet için) | Tekil `OBSERVER_SUMMARIZATION_EVENT` |
| **Replay engine (attention)** | Attention events + causal-ref bounded ilgili event'ler | Batch `M1_REPLAY_READ_BATCH` |
| **Replay engine (sleep)** | Neural events + causal-ref bounded outcome/deontic event'leri | Batch `M1_REPLAY_READ_BATCH` |
| **Explicit memory adapter** | M1'den özet alır (summarizer üzerinden) | Indirect via summarizer |
| **Çekirdek** | **Hayır** (çekirdek M1'i bilmez, sadece dokusunda etkisi vardır) | — |
| **Diğer adapter** (ingress, execution) | **Hayır** | — |

### Replay scope rule

> *Replay read scope is purpose-scoped and causal-ref bounded. Not arbitrary full-ledger access.*

Attention replay attention event'lerinin yanı sıra **causal-ref bounded** ilgili event'leri okuyabilir (örn. pulse'a bağlı deontic block, outcome). Ama keyfi full-ledger access yok.

### Forbidden

- Çekirdeğin M1'i okuması
- Adapter'ların (ingress/execution) M1'i okuması
- Replay engine'in kendi domain'i dışında, causal-ref bağlantısız event okuması
- Read'lerin meta-event olmadan yapılması

---

## 17. Write Permission Matrix

### Yetki tablosu

| Writer | Scope | Path |
|--------|-------|------|
| **Recorder (observer)** | Tüm M1 event'leri | Direct (permanence_policy uygulanır) |
| **Summarizer (observer)** | M2 candidate önerisi | Memory Write Gate üzerinden, M1'e meta-event |
| **Çekirdek** | M0 (kendi öğrenme kuralları) | Direct, observer kaydeder |
| **Adapter (ingress)** | Hiçbiri (M1'e doğrudan yazamaz; observer event üretir) | Indirect (observer recorder) |
| **Deontic gate** | Hiçbiri | Indirect (observer block event kaydeder) |
| **LLM translator** | Hiçbiri | Indirect (HumanIntentEvent ingress üzerinden) |
| **İnsan operatör** | M2 (direct, provenance: human), M1 audit-only | M2 directly, M1 indirectly (observer record) |
| **Replay engine** | M0 traces (own domain), M1 meta-event | Direct M0 traces, indirect M1 (observer record) |

### Çekirdek M1'e doğrudan yazamaz

Çekirdek M0'da yaşar. M0'daki olaylar (assembly birth, pulse, vb.) **observer tarafından gözlemlenip M1'e yazılır**. Çekirdek "şunu M1'e yaz" demez — observer pasif izleyicidir.

### Forbidden

- M1'e doğrudan event yazımı observer-recorder dışındaki bir entity tarafından
- Meta-event'in birden fazla aktör tarafından üretilmesi
- M1 event'inin retroaktif değişimi

---

## 18. Retention and Compaction

### Ring Buffer Retention

- Sınırlı süre (~60s kavramsal band)
- Eski olanlar otomatik tasfiye
- Tasfiye event olarak M1'e yazılmaz (otomatik rotation)
- Snapshot alınmışsa o kısım permanent log'a geçer

### Permanent Log Retention

- **Silinmez.** Append-only.
- Compaction yapılabilir ama içerik korunur.
- Snapshot'lar parent event'in yaşam süresince yaşar.

### Compaction Rules

```
Allowed:
- Storage segment organization (segmentleri farklı tier'lara taşı)
- Index optimization
- Compression (lossless only)
- Older segments to colder storage

Forbidden:
- Event content değişimi
- Event'lerin merge edilmesi
- Event'lerin "özet"e indirgenmesi
- Hash chain'in koparılması
- Snapshot içeriğinin filtrelenmesi/azaltılması
```

### `LEDGER_COMPACTION_PERFORMED` event

```
LedgerCompactionPerformedEvent
├── segment_ids
├── old_segment_hashes
├── new_segment_hash
├── event_count
├── compaction_reason                  # storage_tier_move | reindex | compression
├── performed_by
└── verification_hash_chain_intact     # bool
```

> *Compaction sadece storage organization'dır. Bilgi kaybı yapamaz.*

---

## 19. Event Catalog

Mevcut event tiplerinin tam listesi (A-E + F'den):

### Neural family
```
ASSEMBLY_CANDIDATE_BORN
ASSEMBLY_STABILIZED
ASSEMBLY_MERGED
ASSEMBLY_SPLIT
ASSEMBLY_SUPPRESSED
ASSEMBLY_PROMOTED_TO_IDEA
ASSEMBLY_DECAYED
ASSEMBLY_PRUNED
ASSEMBLY_RECALLED
CONTRADICTION_PEAK
INTENTION_FORMED
INTENTION_SUPPRESSED
SPIKE_BURST
SLEEP_REPLAY_SYNAPSE_UPDATE
WAKE_TO_SLEEP_TRANSITION
SLEEP_TO_WAKE_TRANSITION
```

### Attention family
```
WORKSPACE_PULSE
ATTENTION_REPLAY_HABITUATION_UPDATE
```

### Memory family
```
MEMORY_WRITE_PROPOSED
MEMORY_RECORD_STATUS_CHANGED       # canonical for status transitions
                                    # (replaces MEMORY_WRITE_GATE_PASSED/REJECTED/VERIFIED/QUARANTINED;
                                    #  old_status/new_status as fields — see MEMORY_WRITE_GATE.md §17)
M2_FOREIGN_MERGE_STATUS_CHANGED    # foreign instance M2 import lifecycle (BACKUP_STRATEGY.md §18)
RECALL_REQUEST_SENT
RECALL_RESULT_EMPTY                # failure audit (RECALL_PROTOCOL.md §16)
RECALL_SUPPRESSED                  # individual record suppressed (cooldown/habituation/status)
REPLAY_SURVIVAL_EVALUATED          # M2 verification evidence axis (REPLAY_PROTOCOL.md §13)
REPLAY_OUTCOME_ALIGNMENT_EVALUATED # outcome alignment evidence axis (REPLAY_PROTOCOL.md §14)
OUTCOME_RECEIVED
```

(`RECALL_EVENT_INGESTED` ingress family altındadır — recall'ın çekirdeğe duyusal giriş anı `*_INGESTED` ailesinin parçasıdır.)

### Ingress family
```
OBSERVATION_INGESTED
RECALL_EVENT_INGESTED              # canonical; M2 → core sensory ingress (RECALL_PROTOCOL.md §11)
HUMAN_INTENT_INGESTED
INTERNAL_SHOCK_INGESTED
INGRESS_DEDUP_REJECTED
INGRESS_TTL_EXPIRED
INGRESS_NO_RULE_MATCH              # compiler: hiç matching rule yok (INGRESS_COMPILER_SPEC.md §10)
COMPILER_MAPPING_UPDATED           # learned mapping delta / calibration update (INGRESS_COMPILER_SPEC.md §14)
COMPILER_DRIFT_WARNING             # global drift cap aşıldı (INGRESS_COMPILER_SPEC.md §15)
SOURCE_TRUST_STATUS_CHANGED
```

### Bootstrap family
```
SELF_GENESIS
BOOTSTRAP_M2_INJECTION
CONSTITUTIONAL_SHIFT_APPLIED
CONSTITUTIONAL_SHIFT_AVAILABLE
```

### Deontic family
```
DEONTIC_BLOCKED
DEONTIC_POLICY_STATUS_CHANGED
DEONTIC_BYPASS_ATTEMPT
SUSPECTED_BYPASS_PATTERN
KILL_SWITCH_ACTIVATED
KILL_SWITCH_DEACTIVATION_REQUESTED
KILL_SWITCH_DEACTIVATION_CONFIRMED
KILL_SWITCH_DEACTIVATED
CONSTITUTIONAL_RULE_SHIFT_REQUESTED
```

### Ledger meta family (audit-of-audit)
```
M1_HUMAN_READ
M1_LLM_REPORT_GENERATED
M1_SUMMARY_GENERATED (= OBSERVER_SUMMARIZATION_EVENT)
M1_REPLAY_READ_BATCH
LEDGER_COMPACTION_PERFORMED
ADAPTER_MANIFEST_STATUS_CHANGED       # adapter lifecycle canonical event
                                       # (ADAPTER_REGISTERED/VERIFIED/ACTIVE/REVOKED ayrı tip değil;
                                       #  old_status/new_status field — bkz. ADAPTER_MANIFEST_SPEC.md §14)
COMPILER_RULE_FAMILY_STATUS_CHANGED   # bootstrap rule family lifecycle (active/deprecated/archived)
                                       # bkz. INGRESS_COMPILER_SPEC.md §17
REPLAY_SESSION_STATUS_CHANGED         # replay session lifecycle canonical event
                                       # (replaces REPLAY_SESSION_COMPLETED; old_status/new_status as fields)
                                       # bkz. REPLAY_PROTOCOL.md §18
COUNTERFACTUAL_ABLATION_PERFORMED     # counterfactual ablation audit detail (audit-of-replay artifact)
                                       # bkz. REPLAY_PROTOCOL.md §15
BACKUP_ARTIFACT_STATUS_CHANGED        # backup artifact lifecycle (BACKUP_STRATEGY.md §20)
RESTORE_OPERATION_STATUS_CHANGED      # restore operation lifecycle
M1_HISTORY_LOST_AT_RESTORE            # degraded identity critical event (restore_with_missing_history)
FORK_FROM_INSTANCE                    # fork_birth audit event
MIGRATION_FROM_INSTANCE               # migration_birth audit event (constitutional shift sonrası)
FORGETTING_ATTACK_SUSPECTED           # forgetting attack pattern alarm
NUMERICS_ARTIFACT_STATUS_CHANGED      # numerics artifact lifecycle (NUMERICS_GOVERNANCE.md §20)
NUMERICS_VERSION_MISMATCH_DETECTED    # restore sonrası version uyumsuzluğu
NUMERICS_FAILSAFE_ACTIVATED           # missing/invalid numerics → strict mode
```

### Yeni event ekleme

Yeni event tipi eklemek isteyen:
1. Bu belgeyi revize eder
2. Permanence policy table'ına yeni satır ekler (no-default)
3. Event family belirler
4. Compatibility class: en az `safety_tightening`

---

## 20. Cross-document Anchors

| Belge | Bağlantı |
|-------|----------|
| `CONSTITUTION.md` Madde 7 | M1 = observer ledger; bu belge detayı |
| `MEMORY_CONTRACT.md` M1 bölümü | İki katmanlı yapı (ring buffer + permanent) |
| `MEMORY_CONTRACT.md` §11 | Observer dual-role (recorder vs summarizer) |
| `MEMORY_CONTRACT.md` §14 | Observer dual-role açık sorusu — bu belgede çözüldü |
| `MEMORY_CONTRACT.md` §9 | Memory Write Gate (summarizer M2 candidate üretir) |
| `ATTENTION_WORKSPACE.md` §20 | WorkspacePulseEvent şeması |
| `WORLD_INGRESS.md` §22 | Ingress event tipleri |
| `BOOTSTRAP_GENOME.md` §21 | SELF_GENESIS şeması |
| `BOOTSTRAP_GENOME.md` §23 | Constitutional shift event |
| `DEONTIC_GATE.md` §17 | DEONTIC_BLOCKED, DEONTIC_POLICY_STATUS_CHANGED şemaları |

---

## 21. Violation Tests

1. **Observer karar veriyor mu?** (§4)
   - Evet ise ihlal.
2. **Observer M0'a yazıyor mu?** (§17)
   - Evet ise ihlal.
3. **Observer deontic gate veya self-field gibi davranıyor mu?** (§4)
   - Evet ise ihlal.
4. **Observer memory write approve ediyor mu?** (§5, §17)
   - Evet ise ihlal. Summarizer Memory Write Gate'e candidate önerir, doğrudan yazmaz.
5. **Observer event'i çekirdeğe otomatik RecallEvent olarak dönüyor mu?** (§17)
   - Evet ise ihlal.
6. **Recorder ve Summarizer yetkileri karışmış mı?** (§5)
   - Evet ise ihlal.
7. **Summarizer M2'ye doğrudan yazıyor mu?** (§5, §17)
   - Evet ise ihlal.
8. **Event type inflation var mı?** (§8)
   - Aynı mekanizmanın statü farkları ayrı event tipi mi? Evet ise ihlal.
9. **Permanence policy default kullanıyor mu?** (§10)
   - Evet ise ihlal. No-default kural.
10. **Permanent log append-only ve tamper-evident mi?** (§14)
    - Hayır ise ihlal.
11. **Fine-grain buffer compaction/tasfiye politikası görünür mü?** (§18)
    - Hayır ise ihlal.
12. **Meta-event recording rekürsif mi?** (§15)
    - Evet ise ihlal. First-order only.
13. **Ledger compaction event içeriğine dokunuyor mu?** (§18)
    - Evet ise ihlal.
14. **Snapshot semantic filtering yapıyor mu?** (§11)
    - Evet ise ihlal.
15. **Sampling "önemli olanları" seçiyor mu?** (§11)
    - Evet ise ihlal. Sadece deterministic.
16. **Audit path yoksa action gerçekleşiyor mu?** (DEONTIC §8 Rule 8)
    - Evet ise ihlal. Audit edilemeyen action yasaktır.
17. **Çekirdek M1'i okuyabiliyor mu?** (§16)
    - Evet ise ihlal.
18. **Replay engine kendi domain'i dışında, causal-ref bağlantısız event okuyor mu?** (§16)
    - Evet ise ihlal.

---

## 22. Open Questions

F çerçevesi kapanırken cevaplanmamış bırakılan sorular:

- **Kesin window süreleri ve sampling threshold'ları:** Pre/post window'ların kesin saniye değerleri, `max_event_count` aşımının kesin değeri → `OBSERVER_LEDGER_NUMERICS.md` veya implementation.
- **Hash algoritması ve segment boyutu:** Hangi hash fonksiyonu, segment ne kadar büyür → Implementation.
- **Backup ve restore davranışı:** Snapshot ile birlikte mi yedeklenir, ayrı mı → `BACKUP_STRATEGY.md` konusu.
- **Multi-instance ledger merge:** İki Sentinel'in M1'i birleştirilebilir mi (cross-restore identity, MEMORY_CONTRACT §14)? → Cross-instance kararı.
- **Permanent log storage tier movement:** Hot → warm → cold storage tier'larına geçiş kuralları → Implementation.
- **Summarizer kuralları:** Summarizer hangi event kombinasyonlarını candidate üretmek için kullanır → `MEMORY_WRITE_GATE.md` konusu.

Bu sorular cevaplanmadan implementation aşamasına geçilmez.

---

## Çekirdek özet — 14 karar + 6 family

### 14 karar

1. Observer karar veremez; sadece kanıt kuralları uygular.
2. Observer M0'a yazamaz.
3. Observer deontic gate veya self-field gibi davranmaz.
4. Observer memory write approve edemez.
5. Recorder ve Summarizer yetkileri ayrıdır.
6. Summarizer M2'ye doğrudan yazamaz; Memory Write Gate'e candidate önerir.
7. Event type inflation yasak; statü değişimleri field'dır.
8. Permanent log append-only ve tamper-evident.
9. Permanence policy 2D table, no-default, immutable.
10. Snapshot pencereyi olduğu gibi alır; filtreleme yasak.
11. Sampling deterministic-only ve açıkça kayıplı.
12. Causal refs 1-hop direct only.
13. Meta-events first-order, non-recursive.
14. Compaction storage organization only; içerik korunur.

### 7 event family

- `neural`, `attention`, `memory`, `ingress`, `bootstrap`, `deontic`, `ledger_meta`
- Family **audit grouping**, runtime behavior class **değil**.

---

## Kilit cümleler

> **Observer karar vermez. Observer düzeltmez. Observer engellemez. Observer sadece kanıtlar.**
>
> **M1 sistemin hafızası değil, sistemin tarihinin kanıt defteridir.**
>
> **Observer neyin önemli olduğuna karar vermez. Observer sadece önceden tanımlı kanıt kurallarını uygular.**
>
> **Observer lokal nedenselliği kaydeder. Replay uzak nedenselliği araştırır.**
>
> **Observer does not decide what inside the window matters. It only preserves the window.**
>
> **Persistence weakening is not a routine update.**
>
> **A permanent event may not outlive its required snapshot.**
>
> **Compaction sadece storage organization'dır. Bilgi kaybı yapamaz.**

---

## Versiyon

- **v0.1** — 18 Mayıs 2026 — Frozen Draft. Conceptual phase. No implementation authority.
- `CONSTITUTION.md` Madde 7 / `MEMORY_CONTRACT.md` M1 detayı.
- A, B, C, D, E belgelerinin ortak audit yüzeyi.
- Konuşma soyağacı: [`docs/conversations/0006-observer-ledger-schema.md`](./docs/conversations/0006-observer-ledger-schema.md)
