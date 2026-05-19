# 0017 — Observer Ledger Numerics

> Bu dosya `OBSERVER_LEDGER_NUMERICS.md` (v0.1, Q turu) ortaya çıkmadan önce
> yapılan üçlü tasarım konuşmasının (Halit + Claude + ChatGPT) sıkıştırılmış
> özetidir. **Dördüncü numerics artifact'inin** soyağacı.
>
> A-P: 0001-0016

---

## Tarih
2026-05-19 (P → Q geçişi, dördüncü numerics specifikasyonu)

## Bağlam

N (INGRESS_COMPILER), O (REPLAY_PROTOCOL), P (MEMORY_WRITE_GATE) numerics
donmuş. Q F'nin (OBSERVER_LEDGER_SCHEMA) numerics artifact'i; sistemin
kendine bakma hakkı sayısallaşıyor.

Tek cümle: **Q = sistemin kendine bakma hakkının sayısal sözleşmesi.**

Q'nun üç gerilimi:
- Çok agresif retention → disk patlar
- Çok agresif sampling → audit yüzeyi ölür
- Permanent downgrade kapısı → tarih silinir (constitutional ihlal)

---

## Başlangıç pozisyonları

### Ön sorular — yön belirleme

İki ön soru çapa turundan önce:

1. **Sampling kabul mü?** → Evet, ama sadece ring_buffer/high-frequency için.
   Permanent event sampling'e girmez. Sampling deterministic seed ile,
   strategy enum'dan (semantic seçim YASAK).

2. **Permanent gerçekten sonsuz mu?** → Evet anlam olarak. Hayır fiziksel
   format olarak. Lossless compaction allowed; storage layout değişir;
   event content bit-equivalent kalır. Pre/post hash match zorunlu.

Bu iki kabul Q'nun omurgası oldu.

### ChatGPT (Halit'in vekili, açılış)

7 ana çapa + 13 kırmızı çizgi:

1. Ring buffer window (per family, bidirectional_sensitive)
2. Snapshot window + max_event_count (pre/post per event type)
3. Sampling threshold (rate threshold + canonical strategies)
4. Permanence policy storage limits (segment_max_bytes, hash_checkpoint)
5. Human alert thresholds (suppression caps + first-alert discipline)
6. M1 read batch limits (reader identity ayrımı)
7. Compaction numerics (lossless_required, hash verify, segment age)

### Claude (7 çapaya cevap + 3 ek çapa)

7 çapaya hardening önerileri:
- **Çapa 1 ek:** `min_event_lifetime_in_buffer_ms` floor
- **Çapa 2 ek:** sayısal family hierarchy (constitutional ≥ operational ≥ high_frequency)
- **Çapa 3 ek:** sampling default = none (missing entry → full capture);
  sampling activation audit event
- **Çapa 4 ek:** storage tier transition lossless invariant
- **Çapa 5 ek:** `first_alert_immediate = true` constitutional; critical
  types için `suppression_window = 0`
- **Çapa 6 ek:** LLM reads always audited; LLM scope restriction enum_set
- **Çapa 7 ek:** `hash_verify_before_and_after = true` constitutional;
  mismatch → abort + critical

3 ek çapa:
- **Ek 8:** meta-event recursion cap (max=2 default, max=5 constitutional upper)
- **Ek 9:** foreign event reception caps (L forgetting attack bridge)
- **Ek 10:** permanence policy monotonic invariant (downgrade yasak)

### ChatGPT (kabul + 3 kritik düzeltme + "yaz")

3 kritik düzeltme:

**Düzeltme 1 — Sampling lossless compaction DEĞİL**

Claude'un "sampling de bir tür lossless compaction" wording'i tehlikeli.
Ham event drop edildiyse bu lossless değil. Doğru ayrım:
- Permanent compaction = lossless (storage layout değişir, content sabit)
- Ring buffer sampling = deterministic lossy condensation (ham event drop OK
  ama summary entry permanent)

Belge cümlesi: "Sampling is not lossless compaction. Sampling is
deterministic, auditable, lossy condensation allowed only for ring_buffer_only
high-frequency event families."

**Düzeltme 2 — Yeni event tipi YOK**

Claude `OBSERVER_SAMPLING_SUMMARY` ayrı event tipi gibi yazmıştı, sonra
"canonical reuse" diye geçiştirmişti. İkisi aynı anda olamaz. Doğru
çözüm: tek canonical event `LEDGER_STATE_CHANGED` + reason field:
- sampling_activated
- sampling_summary_written
- storage_pressure_failsafe
- compaction_performed / compaction_hash_mismatch
- hash_chain_mismatch
- tier_transition_performed
- llm_m1_read
- meta_event_recursion_blocked
- foreign_event_rejected_unknown_source
- human_alert_batch_summary
- failsafe_activated

Bu canonical event F'ye eklenir (yan güncelleme).

**Düzeltme 3 — Permanence downgrade yasağı çok sert yazılsın**

Storage pressure ile bile permanence downgrade yasak:
```
permanent → ring_buffer_only        YASAK
permanent_with_snapshot → permanent  YASAK
permanent_with_snapshot → ring_buffer_only YASAK
```

Doğru fail-safe: high-frequency sampling tighten + ring_buffer window
shrink + non-critical reader throttle + critical alert. Permanent event
drop YOK. "Permanence policy is monotonic" artifact validation invariant.

"Yaz" hükmü.

### Halit final

> *"Q tarafını ayrı tutuyorum. Ana karar: sampling ve compaction olabilir,
> ama deterministic/auditable kalacak; permanent log'un anlamı asla
> kaybolmayacak."*

---

## Çekirdek kararlar (16 omurga)

1. Q runtime config değildir; signed artifact + M2 reference.
2. Sampling is not lossless compaction; deterministic lossy condensation only for ring_buffer high-frequency families.
3. Permanent events are never sampled.
4. Sampling strategy enum'dan; semantic_importance/llm_selected/observer_selected/random_unseeded forbidden.
5. Sampling default = none (missing entry = full capture).
6. Permanent log lossless invariant constitutional (`{true}` allowed_range).
7. Compaction hash verify before-and-after invariant constitutional; mismatch → abort + critical alert.
8. Permanence policy monotonic; downgrade (weakening direction) forbidden across artifact versions.
9. Permanent = lifetime retention; TTL yok.
10. Storage pressure → high-frequency sampling tighten + critical alert; permanent event drop YASAK.
11. Critical alert types için `suppression_window_ms = 0` constitutional; `first_alert_immediate = true` constitutional.
12. LLM M1 read < human/replay/summarizer read (computed); LLM scope restricted enum_set; every LLM read audited.
13. Foreign event reception capped + trusted_source_whitelist + quarantine window.
14. Meta-event recursion `max = 2` (allowed_range max = 5 constitutional upper).
15. Snapshot pre/post window hierarchy: constitutional ≥ operational ≥ high_frequency.
16. Missing Q numerics → strict audit-safe mode.

---

## Madde yansımaları

### Madde 6 — LLM observer ledger'da
Q §15: LLM M1 read scope restriction (enum_set whitelist), max_batch_size.llm
< human/replay/summarizer (computed), every LLM read audited via
LEDGER_STATE_CHANGED(reason=llm_m1_read). LLM tüm M1'i taramaz; sadece
izinli aileler.

### Madde 7 — hafıza ayrılığı (M1)
Q F'nin numerics artifact'i; M1'in iç tutulma kuralları sayısallaşıyor.

### Üç ana asimetri (Q'ya özgü)
- **Permanence monotonic:** sıkılaşma serbest, gevşeme forbidden
- **Human read > LLM read:** computed dependency + scope restriction
- **First alert immediate:** suppression sonra başlar; ilk alert kesin

---

## Önemli sertleştirmeler

### Sampling ≠ lossless compaction
Q'nun en kritik kavramsal ayrımı. Wording sertleştirildi:
- Permanent compaction = lossless (hash match)
- Ring buffer sampling = deterministic lossy condensation (summary permanent)

### Sampling default = none
Missing entry = full capture. Gevşeklik default değil. Fail-safe yön.

### Permanence monotonic invariant
Artifact validation seviyesinde. Bir event_type permanent veya
permanent_with_snapshot ilan edildiyse, sonraki artifact onu zayıflatamaz.
Storage pressure bile downgrade'e izin vermez.

### lossless_required + hash_verify_before_and_after constitutional
İkisi de `{true}` allowed_range, change_class forbidden. O §19
replay-triggers-replay = 0 pattern'i Q'da iki yerde.

### LEDGER_STATE_CHANGED canonical event
Q yeni operational state change için **tek event** + reason field
discipline. F'ye eklendi (yan güncelleme); 13 reason değeri.
Yeni event tipi inflation yasaklandı.

### LLM M1 read always audited
Madde 6 koruması M1 read tarafında: her LLM query LEDGER_STATE_CHANGED'a
yazılır; scope enum_set whitelist; subject_class deontic.* forbidden;
ledger_meta security/alert forbidden.

### Storage pressure failsafe
Disk dolsa bile permanent event drop YASAK. High-frequency sampling
tighten, ring buffer shrink, non-critical reader throttle, critical alert,
tier transition accelerate — ama anlam asla kaybolmaz.

### Meta-event recursion cap
Sonsuz ledger spam koruması. default=2 (sampling_activated →
sampling_summary kabul edilebilir); max=5 constitutional upper. Üstü
spec revision gerektirir.

### Foreign event reception caps (L bridge)
Cross-instance event burst = DoS / forgetting attack injection vektörü.
trusted_source_whitelist + quarantine_window + cross_source_dedup_window
ile L §22 forgetting attack defense observer ledger tarafına yansıdı.

---

## Yan güncellemeler (commit'in parçası)

- `OBSERVER_LEDGER_SCHEMA.md` §6 cross-ref to Q; §10 permanence policy table'ına
  LEDGER_STATE_CHANGED satırları (storage_pressure_failsafe, compaction_hash_mismatch,
  hash_chain_mismatch, failsafe_activated, foreign_event_rejected_unknown_source,
  meta_event_recursion_blocked, *); §19 canonical event catalog'a LEDGER_STATE_CHANGED
  eklendi (reason field discipline ile)
- `BACKUP_STRATEGY.md` §8 cross-ref to Q (M1 iç tutulma + foreign event L bridge)
- `MEMORY_CONTRACT.md` M1 bölümü cross-ref to Q
- `README.md` completed listesine OBSERVER_LEDGER_NUMERICS eklendi
- `docs/conversations/0017-observer-ledger-numerics.md` eklendi

NUMERICS_GOVERNANCE.md'de spec_family `observer_ledger` zaten implicit
(spec_family enum dökümante edilen liste değil; her yeni spec'ten doğan
spec_family otomatik valid).

---

## Açık kalanlar (implementation veya sonraki numerics artifact'lere devredildi)

- Exact production retention values (segment_max_bytes, tier sınırları) → signed artifact + implementation
- LLM scope whitelist'in ilk içeriği → implementation + güvenlik review
- Foreign event trusted source whitelist içeriği → operational
- Tier transition cadence ve cost trade-off'ları → implementation
- Meta-event recursion max=2 yeterli mi → ileride spec revision
- Storage pressure'da LLM read tamamen disable mi throttle mi → implementation
- Hash-chain checkpoint cadence performance impact → benchmark + implementation

Bunlar **Q kapsamı dışında**; implementation veya sonraki numerics artifact'lerde
netleşir.

---

## Sıradaki

A-P + Q kapandı. **18 belge.** Conceptual phase + 4 numerics artifact tamam.

Sıradaki NUMERICS belgeleri (kalan):
- R: `BACKUP_STRATEGY_NUMERICS.md` — RPO/RTO, retention windows, restore timeout
- S: `BOOTSTRAP_GENOME_NUMERICS.md` — genome parametreleri, sleep cycle matematiği,
  plasticity state transitions, fatigue recovery
- T: `RECALL_PROTOCOL_NUMERICS.md` — top-k boyutu, recall cooldown, recall-side
  staleness (P canonical kaynak)
- U: `ADAPTER_TRUST_NUMERICS.md` — trust score band'ları, decay rate

---

## Kilit cümleler

> **Observer Ledger numerics, sistemin kendine bakma hakkının sayısal sözleşmesidir.**
>
> **Disk sonsuz değildir. Ama tarih silinemez.**
>
> **Permanent event örneklenemez, düşürülemez, özetlenemez. Sadece lossless taşınabilir.**
>
> **Sampling deterministic, auditable, lossy condensation; sadece ring_buffer high-frequency için.**
>
> **Compaction storage layout değiştirir, event anlamını değiştirmez.**
>
> **LLM M1'i okuyabilir ama her okuması audit'lenir, kapsamı sınırlıdır.**
>
> **Critical alert'ler süresiz snooze edilemez. İlk alert her zaman gönderilir.**
>
> **Storage pressure'da sistem high-frequency tightens; permanent event asla drop edilmez.**
>
> **N dış dünyanın hakkını sınırlar.**
> **O kendi geçmişine girme hakkını sınırlar.**
> **P hafızaya emin olma hakkını sınırlar.**
> **Q kendine bakma hakkını sınırlar.**
