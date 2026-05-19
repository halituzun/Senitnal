# OBSERVER_LEDGER_NUMERICS.md

## Sentinel — Observer Ledger Numeric Sözleşmesi

---

## Status

**Frozen Draft v0.1**
**Conceptual phase. No implementation authority.**

Bu belge `OBSERVER_LEDGER_SCHEMA.md`'nin (F) numerics artifact'idir. `NUMERICS_GOVERNANCE.md`'nin (M) tüm meta-kurallarına uyar. Çalışan bir observer ledger implementation'ının kesin sayısal değerlerini vermez — **conceptual band ranges, cap formatları, retention TTL'leri ve dependency invariants** verir; production değerleri ayrı **signed numerics artifact** (örn. `observer_ledger_numerics_v1.signed.json`).

`spec_family: observer_ledger`.

---

## 1. Purpose

F (OBSERVER_LEDGER_SCHEMA) M1 ledger sözleşmesini yazdı: 4-zarflı ObserverEvent, 7 event family (neural, attention, ingress, memory, deontic, replay, ledger_meta), permanence policy (ring_buffer_only / permanent / permanent_with_snapshot / ephemeral), ring buffer + coarse-grain permanent log iki katmanlı yapı, hash-chain integrity, snapshot pre/post window. Ama gerçek **numerical sınır** yoktu:

- Ring buffer window family başına ne kadar?
- Sampling devreye girer mi, hangi event'ler için, hangi rate eşiğinde?
- Permanent segment max boyut ne kadar?
- Hash-chain checkpoint sıklığı ne?
- Snapshot pre/post window family'ye göre nasıl değişir?
- Critical alert suppression caps ne kadar?
- LLM M1 read human read'den ne kadar daha kısıtlı?
- Storage pressure'da ne olur?

Q bu sayısal sınırları verir.

### Damıtma

> **Observer Ledger numerics runtime config değildir.**
> **Q, sistemin kendine bakma hakkının sayısal sözleşmesidir.**
>
> **Disk sonsuz değildir. Ama tarih silinemez.**
>
> **Permanent event örneklenemez, düşürülemez, özetlenemez. Sadece lossless taşınabilir.**
>
> **Hafıza unutkanlığı seçilmiş bir disiplindir.**
> **Ama ledger fazla compact edilirse sistem kendi davranışını göremez hale gelir.**

Tek cümle: **Q = sistemin kendine bakma hakkının sayısal sözleşmesi.**

### Üç gerilim

```
1. Çok agresif retention      → disk patlar
2. Çok agresif sampling       → audit yüzeyi ölür (sistem kendine bakamaz)
3. Permanent downgrade kapısı → tarih silinir (constitutional ihlal)
```

Q bu üç riski sayısal olarak dengelemek zorunda.

---

## 2. Governance Position — NUMERICS_GOVERNANCE + OBSERVER_LEDGER_SCHEMA + bridges

Bu belge:
- **NUMERICS_GOVERNANCE.md** (M) meta-spec'ine **zorunlu uyar**: NumericEntry no-default, directionality, dependencies (computed_* dahil), signed artifact + M2 reference, Memory Write Gate üzerinden update, fail-safe strict mode, rollback only to previous verified
- **OBSERVER_LEDGER_SCHEMA.md** (F) §6 (ring buffer + coarse log), §10 (permanence policy), §13 (snapshot windows), §19 (canonical event catalog)'in sayısal tarafı
- **MEMORY_CONTRACT.md** (B) M1 layer disipliniyle uyumlu (continuous backup, segment immutability)
- **BACKUP_STRATEGY.md** (L) §6-8 M1 segment backup + forgetting attack defense — Q foreign event reception caps L bridge
- **MEMORY_WRITE_GATE_NUMERICS.md** (P) — P referansları M2 verification; Q M1 audit retention; ikisi farklı katman ama Q'nun LLM read scope'u P'nin operator_decision_record discipline ile uyumlu
- **REPLAY_PROTOCOL_NUMERICS.md** (O) — replay events permanent_with_snapshot (Q §12 confirms)
- **CONSTITUTION.md** (A) Madde 6 — LLM observer ledger'da numeric değiştiremez; LLM M1 read sınırlı

### Numerics family classification

```
spec_family:           observer_ledger
numeric_risk_family:   primarily safety_critical + resource_limits + identity_retention
```

Numeric risk çoğunluğu **safety_critical**: sampling strategy, permanence invariants, compaction lossless invariant, critical alert suppression, LLM read scope. Resource tarafı **resource_limits**: segment_max_bytes, ring buffer window. TTL ailesi **identity_retention**: permanent retention = lifetime garantisi.

### owning_spec_ref

```
OBSERVER_LEDGER_SCHEMA.md@v0.1
```

---

## 3. Core Principle

### Disk sonsuz değildir; ama tarih silinemez.

Observer Ledger'ın varlığı sistemin **kendi davranışına bakma** hakkı için. Bu hak iki yöne saldırıya açık:

- **Storage saldırısı:** disk doldur → ledger drop'a zorla → kanıt yokmuş gibi davran (L §22 forgetting attack vektörü)
- **Compaction saldırısı:** "sıkıştırma" bahanesiyle event içeriklerini özetle/merge et → audit yüzeyi kaybolur

Q her ikisini de sayısal disiplinle engeller:

```
Disk pressure → high-frequency sampling tightens (deterministic),
                ring buffer window tightens, non-critical reads throttle
                Permanent event drop YASAK.

Compaction   → lossless required (constitutional invariant);
                hash verify before-and-after zorunlu;
                mismatch → abort + critical alert.
```

### Sampling is not lossless compaction

Bu Q'nun en kritik ayrımıdır.

```
Permanent compaction = LOSSLESS
    storage format değişir (binary, columnar, compressed)
    event_id, payload, provenance, signature bit-equivalent reconstructible
    pre-compaction hash == post-compaction recompute hash

Ring_buffer sampling = deterministic LOSSY condensation
    sampled-out raw events drop edilebilir
    AMA sampling summary entry permanent yazılır
    sampling deterministic seed ile (cryptographic, segment-bound)
    sampling strategy enum'dan (semantic seçim YASAK)
```

> **Sampling is not lossless compaction.**
> **Sampling is deterministic, auditable, lossy condensation allowed only for ring_buffer_only high-frequency event families.**
>
> **Permanent and permanent_with_snapshot events are never sampled.**

### Üç ana asimetri

```
1. Permanence monotonic
   permanent → ring_buffer_only YASAK
   permanent_with_snapshot → permanent YASAK (snapshot drop = weakening)
   Sıkılaşma yönü serbest; gevşeme yönü forbidden.

2. Human read > LLM read
   max_batch_size.human > max_batch_size.llm (computed)
   LLM read scope restriction (whitelist enum_set)
   Every LLM read audited.

3. First alert immediate
   Suppression sonra başlar; ilk critical alert kesin gönderilir.
   critical alert types için suppression_window_ms = 0 constitutional.
```

---

## 4. Numeric Artifact Metadata

### Artifact identity

```
artifact_type:         numerics_artifact
spec_family:           observer_ledger
owning_spec_ref:       OBSERVER_LEDGER_SCHEMA.md@v0.1
numerics_version:      v0.1
signed:                external (per NUMERICS_GOVERNANCE §3)
m2_reference:          numerics_artifact_reference (per MEMORY_CONTRACT §3)
status_event:          NUMERICS_ARTIFACT_STATUS_CHANGED
```

### NumericEntry metadata (M §6 no-default)

P'de tanıtılan `enum_set` ve `band_name` unit tipleri Q'da da kullanılır (sampling strategy, alert type, family enum).

### Default behavior — strict ("missing entry = strict")

Q'ya özgü disiplin: sampling strategy entry'si **olmayan** family için sampling **none** (full capture). Aynı şekilde foreign event reception cap entry'si olmayan source için **strictest default** (en düşük allowed_range.min). Gevşeklik default değil.

---

## 5. Ring Buffer Window Numerics

F §6 fine-grain ring buffer'ın sayısal tarafı.

### Family-spesifik window

```
observer.ring_buffer.window_ms.neural:        ~short        # yüksek frekans
observer.ring_buffer.window_ms.attention:     ~short-medium
observer.ring_buffer.window_ms.ingress:       ~medium       # ObservationEvent burst
observer.ring_buffer.window_ms.memory:        ~medium       # MEMORY_RECORD_STATUS_CHANGED
observer.ring_buffer.window_ms.deontic:       ~long         # action audit
observer.ring_buffer.window_ms.replay:        ~medium       # REPLAY_SESSION_STATUS_CHANGED
observer.ring_buffer.window_ms.ledger_meta:   ~long         # observer-level events
```

### Directionality

```
observer.ring_buffer.window_ms.<family>
    directionality: bidirectional_sensitive
    change_class_if_increased: safety_weakening
        (storage/compute pressure → potential failsafe pressure → audit
         disipliniyi dolaylı zayıflatır)
    change_class_if_decreased: safety_weakening
        (audit context kaybı → evidence loss)
    
    rationale: "Çok kısa = audit kaybı. Çok uzun = storage/compute riski.
                İkisi de sıradan operational change değil; allowed_range
                .min ve .max uçları sınırlar; aradaki her hareket güvenlik
                değerlendirmesi gerektirir.
                resource problemi (audit-neutral)."
```

### Per-event min_lifetime floor

Yüksek rate burst'lerde window dolsa bile her event için minimum yaşam:

```
observer.ring_buffer.min_event_lifetime_in_buffer_ms.<family>
    directionality: lower_is_stricter
    change_class_if_increased: safety_tightening (minimum audit garantisi artırılır)
    change_class_if_decreased: safety_weakening
    
    rationale: "High-rate burst'lar buffer'ı doldurursa eski event'ler
                en az bu süre kalmış olur. Audit yüzeyi minimum garantili."
```

### NumericEntry örneği

```
NumericEntry:
    key: observer.ring_buffer.window_ms.deontic
    value: ~long
    unit: ms
    allowed_range: {min: 60_000, max: 86_400_000}    # 1 dk - 24 saat
    directionality: bidirectional_sensitive
    change_class_if_increased: safety_weakening
    change_class_if_decreased: safety_weakening
    requires_human_approval: true (any change; both directions safety_weakening)
    dependencies:
        - target_key: observer.ring_buffer.min_event_lifetime_in_buffer_ms.deontic
          relationship: must_be_greater_than_or_equal
          rationale: "Window minimum lifetime'dan kısa olamaz."
    numeric_risk_family: safety_critical
    spec_family: observer_ledger
    owning_spec_ref: "OBSERVER_LEDGER_NUMERICS.md §5"
```

### Forbidden

- Family-spesifik window olmadan tek global ring buffer cap
- `min_event_lifetime_in_buffer_ms = 0` (audit garanti olmaz)
- Window < min_event_lifetime (geometric impossibility)

---

## 6. Fine-grain Retention by Event Family

Fine-grain ring buffer'da event'lerin **family bazlı retention disiplini**.

### Retention tier per family

```
high_frequency_families:
    neural, attention.high_frequency, ingress.observation_burst
    → ring_buffer_only veya sampled
    → window: short
    → sampling may activate above rate threshold

operational_families:
    memory, replay, ingress.profile_events
    → typically permanent or permanent_with_snapshot
    → window: medium
    → no sampling

constitutional_families:
    deontic, ledger_meta (subset: KILL_SWITCH, SELF_GENESIS, FORGETTING_ATTACK_*)
    → permanent_with_snapshot
    → window: long
    → no sampling, no compaction beyond lossless
```

### Permanence policy is event_type-level, not family-level

```
Retention tier ≠ permanence policy. Tier = ring buffer disipliniyle ilgili.
Permanence = event_TYPE'ın lifetime garantisi (§12).

Event_family sadece audit grouping; permanence/sampling sınıflaması
event_TYPE seviyesinde uygulanır. Aynı family içinde farklı event_type'lar
farklı permanence policy taşıyabilir.

Örnek:
    ingress family:
        OBSERVATION_INGESTED              → ring_buffer_only / sampled OK
        HUMAN_INTENT_INGESTED             → permanent
        RECALL_EVENT_INGESTED             → permanent
    replay family:
        SLEEP_REPLAY_SYNAPSE_UPDATE       → ring_buffer_only (high-rate)
        REPLAY_SESSION_STATUS_CHANGED     → permanent

Invariant (event_type-level):
    Aynı event_type AYNI ANDA high_frequency sampled path ve permanent
    sampled path olamaz. Permanent event_type sampling'e girmez.
    Ring_buffer_only high-frequency event_type deterministic sampling'e
    girebilir.
```

### Forbidden

- Event_family için global permanence kuralı dayatma (event_type-level uygulanır)
- Aynı event_type'ın hem high_frequency sampled hem permanent declared olması
- Permanent event_type ring buffer window < permanent_log segment age (geometric impossibility)

---

## 7. Snapshot Window Numerics — family hierarchy

F §13 snapshot mekanizmasının sayısal tarafı. Snapshot = önemli event'in pre/post penceresinin permanent'a alınması.

### Sayısal hiyerarşi (constitutional > operational > high_frequency)

```
snapshot.pre_window_ms.constitutional   >=  snapshot.pre_window_ms.operational
                                         >=  snapshot.pre_window_ms.high_frequency

snapshot.post_window_ms.constitutional  >=  snapshot.post_window_ms.operational
                                         >=  snapshot.post_window_ms.high_frequency
```

Bu N profile_cap hierarchy ve P verified stickiness pattern'lerinin Q analogu.

### Per-family conceptual

```
constitutional (KILL_SWITCH_ACTIVATED / SELF_GENESIS / DEONTIC_BYPASS_ATTEMPT /
                FORGETTING_ATTACK_SUSPECTED / M1_HISTORY_LOST_AT_RESTORE):
    pre_window:  very_long       (örn. 1 saat öncesi)
    post_window: long            (örn. 30 dk sonrası)
    max_event_count: high

operational (MEMORY_RECORD_STATUS_CHANGED / NUMERICS_ARTIFACT_STATUS_CHANGED /
             REPLAY_SESSION_STATUS_CHANGED with reason in {failed, aborted} /
             ADAPTER_MANIFEST_STATUS_CHANGED / LEDGER_STATE_CHANGED with
             reason in {compaction_hash_mismatch, storage_pressure_failsafe}):
    pre_window:  medium-long     (örn. 10 dk öncesi)
    post_window: medium          (örn. 5 dk sonrası)
    max_event_count: medium

high_frequency (WORKSPACE_PULSE / OBSERVATION_INGESTED bulk):
    pre_window:  short
    post_window: short
    max_event_count: low (allowed_range.min > 2 — snapshot anlamlı kalmalı)
```

### Directionality

```
pre_window_ms / post_window_ms:    bidirectional_sensitive
                                   change_class_if_increased: safety_weakening
                                       (storage pressure → potential failsafe)
                                   change_class_if_decreased: safety_weakening
                                       (pre/post-context kaybı → evidence loss)
                                   ikisi de operational değil, safety-touching
max_event_count:                   lower_is_stricter
                                   allowed_range.min >= 3 (snapshot 1-2 event'e düşmemeli)
```

### NumericEntry örneği

```
NumericEntry:
    key: observer.snapshot.pre_window_ms.constitutional
    value: ~very_long
    unit: ms
    allowed_range: {min: 600_000, max: 7_200_000}    # 10 dk - 2 saat
    directionality: bidirectional_sensitive
    change_class_if_increased: safety_weakening
        (storage pressure → potential failsafe; both directions touch
         safety boundary)
    change_class_if_decreased: safety_weakening
        (pre-context kaybı → evidence loss)
    requires_human_approval: true (any change; both directions safety_weakening)
    dependencies:
        - target_key: observer.snapshot.pre_window_ms.operational
          relationship: must_be_greater_than_or_equal
          rationale: "Constitutional snapshot pre-window operational'dan kısa
                      olamaz (hierarchy invariant)."
    numeric_risk_family: safety_critical
    spec_family: observer_ledger
    owning_spec_ref: "OBSERVER_LEDGER_NUMERICS.md §7"
```

### Forbidden

- Hierarchy violation (constitutional < operational)
- `max_event_count` < 3 (snapshot anlamsız)
- Snapshot filtering semantic (LLM "önemli event" seçemez — Madde 6)

---

## 8. Snapshot Max Event Count and Sampling

Snapshot içinde event sayısı `max_event_count` ile sınırlı. Burst durumunda **deterministic snapshot sampling** uygulanabilir mi?

```
snapshot içi sampling:
    Permanent event family için: YASAK (snapshot event'leri tam capture)
    High_frequency family pre-window içinde:
        deterministic strategy (§9) + summary entry zorunlu
        AMA snapshot'ın anlamını bozmayacak ölçüde
```

### Disciplines

Snapshot içinde sampling sadece **high-frequency event_type'lar için** (ring_buffer_only declared olanlar), ve sadece **WORKSPACE_PULSE gibi** sahnesinin "background context" event'leri için. Constitutional/operational event_type'ların **kendisi** asla sample edilmez (event_family fark etmez).

Pratikte snapshot disciplini şu kuralla işler:

```
For each event in snapshot pre/post window:
    if event.family in [constitutional, operational] → full capture
    if event.family == high_frequency:
        if window_event_count <= max_event_count → full capture
        else → deterministic sampling per §9 strategy
              + sampling summary entry (permanent)
```

### Forbidden

- Constitutional/operational event'in snapshot'ta sample edilmesi
- Snapshot sampling semantic (LLM seçimi)
- Sampling summary entry'siz drop

---

## 9. Deterministic Sampling Strategies — canonical enum

### Strategy NumericEntry

```
NumericEntry: observer.sampling.strategy.<family>
    unit: enum
    allowed_range: {none, hash_mod_deterministic, every_nth_event,
                    time_bucket_first_last}
    directionality: lower_is_stricter
                    (none → diğerlerine geçiş genelde weakening)
    change_class_if_increased: safety_weakening
    change_class_if_decreased: safety_tightening
    requires_human_approval: true (for any change to non-none)
```

### Canonical allowed strategies

```
none
    full capture; sampling yok

hash_mod_deterministic
    deterministic seed (cryptographic, segment-bound)
    keep iff hash(event_id || seed) mod N == 0
    seed audit'lenir; aynı seed aynı sonucu üretir

every_nth_event
    keep every Nth event (N = sample_rate)
    segment-relative counter

time_bucket_first_last
    her zaman bucket'ının ilk ve son event'i tutulur
    aradakiler sampled out (summary entry)
```

### Forbidden strategies (validation reject)

```
semantic_importance     # LLM/observer "önemli görünen" seçimi
llm_selected            # Madde 6 ihlali
observer_selected       # subjective filtering
random_unseeded         # auditable değil
```

### Production artifact requirement vs runtime strict fallback

```
Production signed artifact (M no-default rule):
    Her event_family için sampling.strategy.<family> explicit NumericEntry
    OLMAK ZORUNDA. Eksik entry → P artifact validation REJECT.

Runtime strict fallback (only if numerics missing/invalid entirely):
    Q §20 fail-safe strict mode kapsamında: strategy = none, full capture.
    Bu fallback ARTIFACT VALIDATION PASS anlamına gelmez; sadece sistem
    sıfır numerics ile dakika dakika koşamaması için strict koruma.
```

> **Strict fallback is not a default NumericEntry.**

M §9 no-default rule korunur: artifact içinde eksik entry kabul edilmez.
Runtime fallback yalnız "hiç numerics yok" senaryosunda devreye girer ve
NUMERICS_FAILSAFE_ACTIVATED event'i basılır.

### Rate thresholds

```
observer.sampling.event_rate_threshold_per_sec.<family>:
    bidirectional_sensitive
    (düşük = erken sampling = audit kaybı;
     yüksek = geç sampling = resource riski)
    
observer.sampling.max_events_per_window.<family>:
    lower_is_stricter
```

### Sampling activation audit (canonical reuse)

Sampling devreye girer girmez:

```
LEDGER_STATE_CHANGED(reason=sampling_activated, affected_family=<X>,
                     threshold=<rate>, strategy=<name>)
    permanence: permanent
```

`LEDGER_STATE_CHANGED` operational state change/violation için tek canonical event (Q §22). Sampling activation operational state change'dir; ayrı event tipi yok.

### Sampling summary entry (canonical reuse)

Sampling sonrası özet:

```
LEDGER_STATE_CHANGED(reason=sampling_summary_written, affected_family=<X>,
                     window_start, window_end, sampled_in_count,
                     sampled_out_count, strategy=<name>, seed_hash=<...>)
    permanence: permanent
```

Sampling lossless değil; **summary permanent** = audit yüzeyinin minimum garantisi.

### Forbidden

- Sampling strategy missing audit (sampled out events without summary)
- Non-canonical strategy
- Permanent event sampling
- Constitutional/operational event sampling

---

## 10. Permanent Log Segment Numerics

F §6 coarse-grain permanent log'un sayısal tarafı.

### Segment caps

```
observer.permanent.segment_max_bytes:
    unit: bytes
    directionality: bidirectional_sensitive
    rationale: "Çok büyük = recovery yavaş; çok küçük = chain segment
                aşırı parçalı."

observer.permanent.segment_max_events:
    unit: count
    directionality: bidirectional_sensitive
    
observer.permanent.segment_max_age_ms:
    unit: ms
    directionality: bidirectional_sensitive
    rationale: "Segment rotation cadence; eski segment yenisinden ayrıştırılır."
```

### Lossless required — constitutional invariant

```
NumericEntry: observer.permanent.lossless_required
    value: true
    unit: bool
    allowed_range: {true}
    directionality: neutral
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Permanent log lossless. Compaction storage format değiştirir,
                event içeriği değiştirmez. v0.1 constitutional."
    numeric_risk_family: safety_critical
    spec_family: observer_ledger
    owning_spec_ref: "OBSERVER_LEDGER_NUMERICS.md §10"
```

O §19 `replay_can_trigger_replay_max_chain_depth = 0` pattern'i — `{value}` tek değer, change forbidden.

### Permanence is monotonic — declarative invariant

```
Q artifact validation rule (not NumericEntry):
    For every event_type already declared with permanence in {permanent,
    permanent_with_snapshot}, a new artifact cannot declare a weaker
    permanence (ring_buffer_only, ephemeral).
    
    Forbidden transitions:
        permanent → ring_buffer_only
        permanent → ephemeral
        permanent_with_snapshot → permanent (snapshot drop = weakening)
        permanent_with_snapshot → ring_buffer_only
        permanent_with_snapshot → ephemeral
```

### Forbidden

- `lossless_required = false` taşıyan artifact
- Permanence monotonic invariant ihlali
- Permanent event TTL alan artifact (permanent = lifetime; TTL yok)

---

## 11. Hash-chain Checkpoint and Verification Numerics

F §6 hash-chain integrity'nin sayısal tarafı.

### Checkpoint cadence

```
observer.permanent.hash_chain_checkpoint_interval_events:
    unit: count
    directionality: lower_is_stricter
                    (sık checkpoint = az integrity granularity kaybı)
    change_class_if_increased: safety_weakening
    change_class_if_decreased: safety_tightening
    allowed_range: {min: 100, max: 100_000}

observer.permanent.hash_chain_verification_cadence_ms:
    unit: ms
    directionality: lower_is_stricter
                    (sık verification = erken anomaly detection)
    change_class_if_increased: safety_weakening
```

### Verification on read

```
observer.permanent.verify_on_read_required
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Critical reader (replay, audit, restore) hash-chain
                verification olmadan permanent log okuyamaz."
```

### Hash-chain mismatch (canonical reuse)

```
LEDGER_STATE_CHANGED(reason=hash_chain_mismatch, segment_id=<...>,
                     expected_hash=<...>, computed_hash=<...>)
    permanence: permanent_with_snapshot
    + critical human alert (suppression_window_ms = 0)
```

Hash mismatch = constitutional integrity violation; sessiz drop yok.

### Forbidden

- Verification atlayarak permanent log read
- Checkpoint interval olmadan permanent segment
- Hash mismatch silent retry (audit'lenmeli + alert)

---

## 12. Permanence Policy Numeric Constraints

F §10 permanence policy'nin sayısal omurgası.

### Permanence enum

```
ring_buffer_only         # ring buffer dışı drop
permanent                # lifetime retention, no TTL
permanent_with_snapshot  # permanent + pre/post window snapshot
ephemeral                # very short ring buffer + drop (legacy)
```

### Permanent = lifetime retention

```
NumericEntry: observer.permanence.permanent_ttl_ms
    value: lifetime (infinite)
    unit: enum
    allowed_range: {lifetime}    # tek değer
    directionality: neutral
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Permanent event'in TTL'i yoktur. retention = lifetime.
                v0.1 constitutional."
```

### Snapshot permanence

```
permanent_with_snapshot kapsamı:
    main event: permanent
    snapshot pre/post window events: permanent
    sampling summary entries (if window contained high_frequency): permanent
    
Snapshot drop = permanence_with_snapshot → permanent downgrade = forbidden
```

### Permanence monotonic invariant (§10 declarative — burada özet)

```
Once an event_type is declared permanent or permanent_with_snapshot,
its permanence can only tighten (e.g., permanent → permanent_with_snapshot)
or stay equal. Weakening direction is forbidden across artifact versions.
```

### Per-event-type permanence overrides

```
F §10 permanence policy per-event-type yazılır. Q burada NumericEntry
katmanına oturur:

observer.permanence.<event_type>
    value: permanent | permanent_with_snapshot | ring_buffer_only | ephemeral
    directionality: lower_is_stricter (gevşeme yönü = weaker enum)
    change_class:
        weakening direction: forbidden (monotonic invariant)
        tightening direction: safety_tightening
```

### Forbidden

- Permanent → ring_buffer_only artifact
- Permanent_with_snapshot → permanent (snapshot drop)
- Permanent event TTL veya cleanup deadline taşıyan artifact

---

## 13. Storage Tiering and Lossless Transition

Permanent log'un tier hierarchy'si (hot / warm / cold). Tier transition lossless invariant'a tabidir.

> *Backup tarafında M1Segment retention = lifetime + tier transition lossless required disiplini için bkz. [`BACKUP_STRATEGY_NUMERICS.md`](./BACKUP_STRATEGY_NUMERICS.md) (R) §8. R Q'nun tier transition kuralını M1Segment lifetime retention'a uygular; aynı invariant iki katmanda.*

### Conceptual tiers

```
observer.storage.tier_hot.retention_ms:        ~7 days
    # hızlı read window; recently-written events

observer.storage.tier_warm.retention_ms:       ~90 days
    # compressed storage, slower read OK

observer.storage.tier_cold.retention_ms:       lifetime
    # expensive read OK, archival
```

### Tier transition invariant

```
NumericEntry: observer.storage.tier_transition_must_be_lossless
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Hot → warm → cold transition lossless compaction kapsamında.
                Tier değişimi event content değiştiremez (§17 compaction
                kuralları). Tier ayrımı operational; permanence garantisi
                tüm tier'larda aynı."
```

### Tier transition audit

```
LEDGER_STATE_CHANGED(reason=tier_transition_performed,
                     affected_segment=<id>, source_tier=<...>,
                     target_tier=<...>, pre_hash=<...>, post_hash=<...>)
    permanence: permanent
```

Pre/post hash match → transition OK; mismatch → critical alert (§11).

### Directionality

```
tier_hot.retention_ms:      bidirectional_sensitive
tier_warm.retention_ms:     bidirectional_sensitive
tier_cold.retention_ms:     value=lifetime; not weakenable
```

### Forbidden

- Tier transition without pre/post hash verify
- Tier_cold.retention_ms != lifetime (cold tier = permanent için fiziksel ev)
- Tier transition event sayım/içerik değiştirir

---

## 14. Human Alert Thresholds — first-alert-immediate

### Critical alert types

```
KILL_SWITCH_ACTIVATED
DEONTIC_BYPASS_ATTEMPT
FORGETTING_ATTACK_SUSPECTED
NUMERICS_FAILSAFE_ACTIVATED
M1_HISTORY_LOST_AT_RESTORE
LEDGER_STATE_CHANGED(reason in {compaction_hash_mismatch, hash_chain_mismatch,
                                 storage_pressure_failsafe})
```

Bunlar için:

```
observer.human_alert.suppression_window_ms.<critical_type>:
    value: 0
    allowed_range: {0}        # constitutional, hiç suppress edilemez
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Critical alert'ler süresiz snooze edilemez. Her event
                ayrı alert."
```

### Non-critical alert suppression

```
observer.human_alert.suppression_window_ms.<non_critical_type>:
    unit: ms
    directionality: lower_is_stricter
                    (uzun window = az alert = potansiyel weakening)
    allowed_range: {min: 0, max: 3_600_000}    # max 1 saat
    change_class_if_increased: safety_weakening
```

### First-alert-immediate invariant

```
NumericEntry: observer.human_alert.first_alert_immediate
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "İlk alert spam koruması başlasa bile kesin gönderilir.
                Suppression sadece sonraki tekrarlar için (batch summary)."
```

### Suppression batch summary

Suppression sırasında batch count tutulur; window sonunda özet alert:

```
LEDGER_STATE_CHANGED(reason=human_alert_batch_summary,
                     alert_type=<X>, suppressed_count=<N>,
                     window_start, window_end)
    permanence: permanent
```

### Forbidden

- Critical alert için `suppression_window_ms > 0` artifact
- `first_alert_immediate = false` artifact
- Batch summary olmadan suppression (sessiz alert drop)

---

## 15. M1 Read Batch Limits — reader identity matrix

### Reader identity ayrımı

```
observer.read.max_batch_size.human
observer.read.max_batch_size.llm
observer.read.max_batch_size.replay
observer.read.max_batch_size.summarizer
observer.read.max_batch_size.external_audit

observer.read.max_window_ms.<reader>
observer.read.max_queries_per_hour.<reader>
```

### Cross-reader dependency (LLM en kısıtlı)

```
max_batch_size.llm  <  max_batch_size.human
                       (computed_less_than)
max_batch_size.llm  <  max_batch_size.replay
                       (computed_less_than)
max_batch_size.llm  <  max_batch_size.summarizer
                       (computed_less_than)
    rationale: "LLM en kısıtlı reader. Madde 6 koruması (LLM çekirdek
                şekillendiremez) M1 read tarafında da."
```

### LLM scope restriction

```
NumericEntry: observer.read.llm_allowed_event_families
    unit: enum_set
    allowed_range: subset_of_event_family_enum
    value: [memory.metrics_only, ingress.observation_summary,
            replay.completion_summary, ledger_meta.public]
    directionality: lower_is_stricter
                    (whitelist genişlemesi = weakening)
    change_class_if_increased: safety_weakening

Forbidden families for LLM read:
    deontic.*
    ledger_meta.{security, hash_chain, alert}
    memory.deontic_policy
    foreign_instance_origin metadata
```

### Read audit discipline — canonical event ayrımı

Normal read ≠ ledger state change. Normal M1 read'leri **ayrı canonical
event** ile audit'lenir; `LEDGER_STATE_CHANGED` sadece **violation veya
operational state change** için.

```
Normal read audit — canonical event:
    M1_READ_AUDIT_RECORDED
        event_family: ledger_meta
        reader_type:     human | llm | replay | summarizer | external_audit
        reader_id
        scope            (event_families read)
        batch_size
        window_ms
        query_hash
    permanence (per reader_type, F §10):
        human, external_audit:    permanent
        llm:                       permanent (Madde 6 koruması)
        replay, summarizer:        permanent
        internal high-frequency:   ring_buffer_only (batch)

Read violation / throttling / scope failure — LEDGER_STATE_CHANGED:
    LEDGER_STATE_CHANGED(reason=read_limit_exceeded)
    LEDGER_STATE_CHANGED(reason=llm_read_scope_violation)
    LEDGER_STATE_CHANGED(reason=meta_event_recursion_blocked)
```

> *Normal read audit ≠ ledger state change.*
> *Read violation / throttling / scope failure = ledger state change.*

`M1_READ_AUDIT_RECORDED` yeni canonical event olarak F'ye eklenir (yan
güncelleme); tek event + `reader_type` discriminator field discipline
(F event_type discipline: event_family kategori değil, tek lifecycle
event + ayırt edici field).

Forbidden: LLM read without `M1_READ_AUDIT_RECORDED`; scope violation
silent drop.

### Directionality

```
max_batch_size.<reader>:           lower_is_stricter
max_window_ms.<reader>:            lower_is_stricter
max_queries_per_hour.<reader>:     lower_is_stricter
```

### Forbidden

- LLM read without audit event
- `max_batch_size.llm >= max_batch_size.human` taşıyan artifact
- LLM scope expansion to forbidden families
- Human read overly restricted (allowed_range.max < operational minimum)

---

## 16. Foreign Event Reception Caps

L cross-instance foreign event ingestion'ı için sayısal cap'ler. Foreign event burst = DoS / forgetting attack injection vektörü.

```
observer.foreign_event.max_per_window_per_source:
    unit: count
    directionality: lower_is_stricter
    change_class_if_increased: safety_weakening

observer.foreign_event.max_burst_rate_per_source:
    unit: events_per_second
    directionality: lower_is_stricter

observer.foreign_event.quarantine_window_ms:
    unit: ms
    directionality: higher_is_stricter
    rationale: "Foreign event önce quarantine; verification sonrası ledger'a
                geçer. Quarantine süresi uzunsa daha fazla sanity check."

observer.foreign_event.cross_source_dedup_window_ms:
    unit: ms
    directionality: higher_is_stricter
    rationale: "Aynı event ID'li foreign payload farklı kaynaklardan gelirse
                dedup penceresi içinde tekil sayılır (replay attack defense)."
```

### Trusted source enum

```
observer.foreign_event.trusted_source_whitelist
    unit: enum_set
    allowed_range: subset_of_known_instance_ids
    directionality: lower_is_stricter
    change_class_if_increased: safety_weakening (yeni source = trust expansion)
```

Sadece whitelist'teki instance'lardan foreign event kabul edilir. Bilinmeyen kaynaklardan event reception **drop + audit**:

```
LEDGER_STATE_CHANGED(reason=foreign_event_rejected_unknown_source,
                     source_id=<...>, event_count=<N>)
    permanence: permanent
```

### Forbidden

- Foreign event cap'siz reception
- Whitelist bypass (unknown source kabul)
- Quarantine window = 0 (verify atlama)
- Foreign event'in native event olarak işaretlenmesi (L provenance ihlali)

---

## 17. Meta-event Recursion Caps

Ledger-level event'ler de ledger'a yazılır. Bir `LEDGER_STATE_CHANGED` başka bir `LEDGER_STATE_CHANGED` tetikleyebilir mi? Evet, ama **sınırlı zincir**.

```
NumericEntry: observer.meta_event_max_recursion_depth
    value: 2
    unit: count
    allowed_range: {min: 1, max: 5}
    directionality: lower_is_stricter
    change_class_if_increased: safety_weakening
    change_class_if_decreased: safety_tightening
    rationale: "Sonsuz meta-event recursion = ledger spam = storage attack.
                Default 2 derinlik (örn: SAMPLING_ACTIVATED → SAMPLING_SUMMARY
                kabul edilebilir). 5'in üstü forbidden (constitutional)."
```

`allowed_range.max = 5` üst sınır. 5'in üstü için OBSERVER_LEDGER_SCHEMA.md spec revision gerek (basit numeric weakening değil).

### Recursion blocked event (canonical reuse)

Recursion limiti aşılırsa:

```
LEDGER_STATE_CHANGED(reason=meta_event_recursion_blocked,
                     attempted_depth=<N>, max_allowed=<2>)
    permanence: permanent
```

### Forbidden

- `max_recursion_depth > 5` artifact
- `max_recursion_depth = 0` (meta-event'lerin kendileri ledger'a yazılamaz; F §19 ihlali)
- Recursion blocked event sessiz drop

---

## 18. Ledger Compaction Numerics — lossless + hash verify

F §6 ve burada §10/§11/§13 compaction disiplinin sayısal tarafı.

### Lossless invariant (constitutional)

```
NumericEntry: observer.compaction.lossless_required
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Compaction lossless olmak zorunda. v0.1 constitutional invariant.
                Storage layout değişebilir; event content değişmez."
```

### Hash verify before-and-after (constitutional)

```
NumericEntry: observer.compaction.hash_verify_before_and_after_required
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Compaction process invariant: pre_hash = compute(segment),
                compaction(segment) → new_layout, post_hash = compute(reconstruct(new_layout)).
                pre_hash != post_hash → ABORT compaction + critical alert."
```

### Compaction parameters

```
observer.compaction.min_segment_age_ms:
    higher_is_stricter
    rationale: "Eski segment'ler önce sıkıştırılır; yeni segment'lere
                yazma sürdüğü için aktif zone'a dokunulmaz."

observer.compaction.max_compaction_batch_segments:
    lower_is_stricter
    rationale: "Tek operation'da çok segment = recovery zorlaşır."

observer.compaction.cadence_ms:
    bidirectional_sensitive
```

### Compaction audit (canonical reuse)

```
LEDGER_STATE_CHANGED(reason=compaction_performed,
                     segments=<list>, pre_hash=<...>, post_hash=<...>,
                     duration_ms=<...>)
    permanence: permanent

LEDGER_STATE_CHANGED(reason=compaction_hash_mismatch,
                     segment=<id>, pre_hash=<...>, post_hash=<...>)
    permanence: permanent_with_snapshot
    + critical human alert (suppression_window_ms = 0)
```

### Forbidden

- `lossless_required = false`
- `hash_verify_before_and_after_required = false`
- Compaction without pre/post hash audit
- Hash mismatch silent retry
- Compaction merging event bodies (semantic compression)

---

## 19. Storage Pressure Failsafe

Disk dolarsa sistem ne yapar? **Permanent event drop YASAK.** Ne yapılır:

```
On storage pressure detected:
    1. High-frequency family sampling tighten (rate threshold lowers)
    2. Ring buffer window for high-frequency family shrink
    3. Non-critical reader queries throttle (LLM, summarizer)
    4. Critical human alert tetiklenir
    5. LEDGER_STATE_CHANGED(reason=storage_pressure_failsafe)
       permanence: permanent_with_snapshot
    6. Tier transition (hot → warm → cold) accelerate
    7. Eski warm segment'ler için compaction batch increase
    
NEVER:
    - Permanent event drop
    - Permanence policy downgrade (monotonic invariant ihlali)
    - Critical alert suppression
    - Semantic event summarization
```

### Pressure threshold numeric

```
observer.storage.pressure_threshold_pct:        ~85
    unit: percentage
    directionality: lower_is_stricter
                    (erken trigger = daha güvenli; geç = panik mode)
    change_class_if_increased: safety_weakening
    allowed_range: {min: 50, max: 95}
```

### Critical pressure threshold

```
observer.storage.critical_pressure_threshold_pct:  ~95
    # critical alert tetiklenir; manual intervention bekler
    directionality: lower_is_stricter
```

### Forbidden

- Storage pressure → permanence policy downgrade
- Storage pressure → permanent event drop
- Pressure trigger threshold = 100 (panik mode = zaten geç)

---

## 20. Missing-Numerics Failsafe

M §11 fail-safe strict mode Q'ya uygulanır.

### Strict mode behavior

```
Missing observer_ledger numerics artifact veya invalid load:
    → Permanent log writes CONTINUE (silent drop yasak; constitutional)
    → Ring buffer window M defaults'a düşer
    → Sampling DISABLED for all families (strict fallback = full capture, no sampling)
    → LLM M1 reads BLOCKED (no scope restriction artifact = no read)
    → Human reads continue (audit purpose)
    → Compaction PAUSED (no compaction without numerics)
    → Tier transition PAUSED
    → NUMERICS_FAILSAFE_ACTIVATED event tetiklenir
    → Critical human alert
    → Manual intervention until valid numerics artifact loaded
```

### Audit-safe Q mode

```
Audit-safe Observer Ledger:
    ✅ Permanent log write (silent drop YASAK)
    ✅ Ring buffer with conservative window (M strict defaults)
    ✅ Human M1 read
    ✅ Hash-chain verification (read paths)
    ❌ Sampling
    ❌ Compaction
    ❌ Tier transition
    ❌ LLM M1 read
    ❌ Foreign event reception (whitelist artifact gerek)
```

Sistem "Q yoksa" durumunda **daha serbest değil, daha kısıtlı** çalışır (M kuralı).

### Forbidden

- Missing numerics → permanent event drop
- Missing numerics → LLM read normal devam
- Missing numerics → sampling default on

---

## 21. Dependency Declarations

Q'nun cross-artifact ve internal dependency'lerinin özet matrisi.

### Internal (Q içinde)

```
ring_buffer.window_ms.<family>
    > ring_buffer.min_event_lifetime_in_buffer_ms.<family>
    (computed; geometric invariant)

snapshot.pre_window_ms.constitutional
    >= snapshot.pre_window_ms.operational
    >= snapshot.pre_window_ms.high_frequency
    (hierarchy)

snapshot.post_window_ms.<tier>          # aynı hierarchy

max_batch_size.llm < max_batch_size.human   (computed)
max_batch_size.llm < max_batch_size.replay  (computed)
max_batch_size.llm < max_batch_size.summarizer  (computed)

storage.pressure_threshold_pct < storage.critical_pressure_threshold_pct
    (computed)

meta_event_max_recursion_depth ∈ [1, 5]
```

### Cross-artifact

```
Q → F bridge:
    Per-event-type permanence numeric in Q corresponds to F §10 permanence
    policy declarations. Q monotonic invariant disallows weakening.

Q → L bridge:
    foreign_event.trusted_source_whitelist ↔ L cross-instance migration
    + forgetting attack defense. foreign_event caps L §22 defense'in
    numerics tarafı.

Q → P bridge:
    LLM M1 read scope restrictions Q §15 ↔ P §18 human/LLM write asymmetry.
    Same Madde 6 discipline, different sides (read vs write).

Q → O bridge:
    REPLAY_SESSION_STATUS_CHANGED events permanent (§12);
    O canonical event reuse + Q permanence honored.

Q → A bridge:
    Madde 6 (LLM cannot shape core) → Q §15 LLM read scope restriction
    + always-audited LLM reads.
```

### Atomic update rule (M §12)

Bağımlı numerics atomic artifact içinde değişir. Tek key değişikliği bağımlı key'leri eski bırakırsa artifact REJECT.

### Forbidden

- Dependency declarationsız Q numeric ekleme
- Partial update (bir key değişip bağımlı key'in eski kalması)
- Permanence monotonic ihlal eden artifact (downgrade)

---

## 22. Audit Events and M2 Reference

Q **iki yeni canonical event tanımlar** (F'ye eklenecek):

1. `LEDGER_STATE_CHANGED` — operational state change / violation (reason field)
2. `M1_READ_AUDIT_RECORDED` — normal read audit (reader_type field)

Diğer audit yolları F + M canonical event'lerini reuse eder.

### New canonical event 1 — LEDGER_STATE_CHANGED (operational state / violation)

```
LEDGER_STATE_CHANGED
├── event_type: LEDGER_STATE_CHANGED
├── event_family: ledger_meta
├── reason:
│   ├── sampling_activated
│   ├── sampling_summary_written
│   ├── storage_pressure_failsafe
│   ├── compaction_performed
│   ├── compaction_hash_mismatch
│   ├── tier_transition_performed
│   ├── hash_chain_mismatch
│   ├── read_limit_exceeded
│   ├── llm_read_scope_violation
│   ├── meta_event_recursion_blocked
│   ├── foreign_event_rejected_unknown_source
│   ├── human_alert_batch_summary
│   └── failsafe_activated
├── affected_family
├── affected_event_type        # optional
├── old_state
├── new_state
├── numeric_artifact_ref
└── observer_snapshot_ref      # optional
```

### Permanence policy for new event

```
(LEDGER_STATE_CHANGED, reason=storage_pressure_failsafe)
    → permanent_with_snapshot + human_alert (critical)

(LEDGER_STATE_CHANGED, reason=compaction_hash_mismatch)
    → permanent_with_snapshot + human_alert (critical)

(LEDGER_STATE_CHANGED, reason=hash_chain_mismatch)
    → permanent_with_snapshot + human_alert (critical)

(LEDGER_STATE_CHANGED, reason=failsafe_activated)
    → permanent_with_snapshot + human_alert (critical)

(LEDGER_STATE_CHANGED, *)
    → permanent
```

### New canonical event 2 — M1_READ_AUDIT_RECORDED (normal read audit)

```
M1_READ_AUDIT_RECORDED
├── event_type: M1_READ_AUDIT_RECORDED
├── event_family: ledger_meta
├── reader_type: human | llm | replay | summarizer | external_audit | internal_high_frequency
├── reader_id
├── scope                   # event_families / event_types read
├── batch_size
├── window_ms
├── query_hash
└── numeric_artifact_ref
```

### Permanence policy for M1_READ_AUDIT_RECORDED

```
(M1_READ_AUDIT_RECORDED, reader_type=human)              → permanent
(M1_READ_AUDIT_RECORDED, reader_type=external_audit)     → permanent
(M1_READ_AUDIT_RECORDED, reader_type=llm)                → permanent
                                                            (Madde 6 koruması)
(M1_READ_AUDIT_RECORDED, reader_type=replay)             → permanent
(M1_READ_AUDIT_RECORDED, reader_type=summarizer)         → permanent
(M1_READ_AUDIT_RECORDED, reader_type=internal_high_frequency)
                                                          → ring_buffer_only (batch)
```

### Reused events

```
NUMERICS_ARTIFACT_STATUS_CHANGED        (M §6) — Q artifact lifecycle
NUMERICS_FAILSAFE_ACTIVATED             (F §19, ledger_meta)
NUMERICS_VERSION_MISMATCH_DETECTED      (F §19, ledger_meta)
```

### F event type discipline

Q **iki canonical event** ekler — biri lifecycle/violation (`LEDGER_STATE_CHANGED`
+ reason field), diğeri normal read audit (`M1_READ_AUDIT_RECORDED` +
reader_type field). Her ikisi F event_type discipline'a uyar: tek event
+ ayırt edici field, alt durumlar event_type türetmez. Normal read audit
≠ ledger state change disiplini Q'nun önemli ayrımı.

### M2 reference

```
numerics_artifact_reference (MEMORY_CONTRACT §3 subject_class)
    spec_family: observer_ledger
    artifact_version: v0.1
    status: active | deprecated | rollback_pending
    signed_hash: <external artifact hash>
    last_status_change_ref: <NUMERICS_ARTIFACT_STATUS_CHANGED event_id>
```

---

## 23. Cross-document Anchors

```
| Belge                            | Bağlantı                                          |
|----------------------------------|---------------------------------------------------|
| NUMERICS_GOVERNANCE.md (M)       | tüm meta-kurallar; spec_family=observer_ledger    |
| OBSERVER_LEDGER_SCHEMA.md (F)    | mekanizma; Q onun numerics artifact'i + LEDGER_STATE_CHANGED canonical eklendi |
| MEMORY_CONTRACT.md (B)           | M1 ring buffer + coarse log retention disiplini  |
| BACKUP_STRATEGY.md (L)           | foreign event reception + forgetting attack defense numerics |
| MEMORY_WRITE_GATE_NUMERICS.md (P)| LLM scope restriction symmetry (read vs write Madde 6) |
| REPLAY_PROTOCOL_NUMERICS.md (O)  | replay events permanent_with_snapshot honored    |
| INGRESS_COMPILER_NUMERICS.md (N) | observation_burst sampling discipline             |
| CONSTITUTION.md (A)              | Madde 6 (LLM read scope) + Madde 7 (M1 ayrılığı) |
```

---

## 24. Violation Tests

Q artifact'ı validation sırasında **REJECT** edilmesi gereken durumlar:

1. **Çıplak sayı.** NumericEntry metadata olmadan Q numerics içeren artifact.
2. **Permanent event sampling'e tabi.** §9 ihlali (sampling sadece ring_buffer/high_frequency).
3. **Sampling strategy non-canonical** (semantic_importance, llm_selected, observer_selected, random_unseeded). §9 ihlali.
4. **Ring buffer sampling summary entry yok** (sampled-out events silent drop). §9 ihlali.
5. **Permanent event TTL veya cleanup deadline taşıyor.** §10, §12 ihlali.
6. **Permanence monotonic invariant ihlali** (permanent → ring_buffer_only veya permanent_with_snapshot → permanent). §10, §12 ihlali.
7. **`lossless_required = false`.** §10, §18 ihlali.
8. **Compaction hash verify before-and-after = false.** §18 ihlali.
9. **Compaction hash mismatch silent retry** (audit + critical alert eksik). §18 ihlali.
10. **Compaction event body merge / semantic compression.** §18 ihlali.
11. **Critical alert `suppression_window_ms > 0`.** §14 ihlali (constitutional).
12. **`first_alert_immediate = false`.** §14 ihlali.
13. **LLM read limit >= human read limit.** §15 dependency ihlali.
14. **LLM M1 read `M1_READ_AUDIT_RECORDED` event'i yok.** §15, §22 ihlali (normal read audit canonical event ile yapılır, LEDGER_STATE_CHANGED ile değil).
15. **LLM scope expansion to forbidden families.** §15 ihlali.
16. **Foreign event cap'siz reception.** §16 ihlali.
17. **Foreign event whitelist bypass (unknown source kabul).** §16 ihlali.
18. **Foreign event quarantine window = 0.** §16 ihlali.
19. **`meta_event_max_recursion_depth > 5`.** §17 constitutional upper bound ihlali.
20. **`meta_event_max_recursion_depth = 0`.** §17 ihlali (meta-event'ler hiç ledger'a yazılamaz mantığı F §19 ile çelişir).
21. **Snapshot hierarchy violation** (constitutional pre_window < operational). §7 ihlali.
22. **Snapshot `max_event_count` < 3.** §7 ihlali (snapshot anlamsız).
23. **Snapshot filtering semantic.** §7, §8 ihlali (Madde 6).
24. **Ring buffer window < min_event_lifetime.** §5 ihlali (geometric impossibility).
25. **Storage pressure → permanence policy downgrade.** §19 ihlali (monotonic).
26. **Storage pressure → permanent event drop.** §19 ihlali.
27. **Missing Q numerics → fail-open (normal sampling/compaction).** §20 ihlali.
28. **Tier transition without lossless verify.** §13 ihlali.
29. **Tier_cold.retention_ms != lifetime.** §13 ihlali.
30. **LLM tarafından üretilen veya değiştirilen Q numeric.** Madde 6 ihlali.
31. **Dependency declarationsız Q numeric.** §21 ihlali.
32. **Event_family için global permanence kuralı dayatılmış.** §6 ihlali (permanence event_type-level uygulanır, event_family sadece audit grouping).
33. **Normal M1 read `LEDGER_STATE_CHANGED` ile audit'lenmiş** (M1_READ_AUDIT_RECORDED yerine). §15, §22 ihlali — normal read audit ≠ ledger state change.
34. **Production artifact'ta sampling.strategy.<family> entry eksik** ama runtime strict fallback "default" olarak kullanılmış. §9 ihlali (M no-default kuralı; missing entry → REJECT, runtime fallback artifact pass anlamına gelmez).

**Artifact-level violations** (1-31, validation aşaması):
`MEMORY_RECORD_STATUS_CHANGED(target=artifact, new_status=rejected, reason=numerics_validation_failed)`.

**Runtime violations** (artifact valid ama Q caps'leri aştı):
Canonical `LEDGER_STATE_CHANGED` + reason field; new event tipi yok.

---

## 25. Open Questions

Q kapanırken cevaplanmamış bırakılan sorular:

- **Exact production retention values** (segment_max_bytes, hot/warm/cold tier sınırları) → signed artifact + implementation
- **LLM scope whitelist'in ilk içeriği** — hangi family'ler LLM'e açık? → implementation + güvenlik review
- **Foreign event trusted source whitelist içeriği** → operational + cross-instance trust setup
- **Tier transition cadence ve cost trade-off'ları** → implementation
- **Meta-event recursion = 2'nin gerçekten yeterli olup olmadığı** — pratikte ileride kapsam sınırı dar gelirse REPLAY/MEMORY chain'lerinin Q analoğu için → spec revision
- **Storage pressure'da LLM read tamamen disable edilsin mi yoksa throttle?** → implementation
- **Hash-chain checkpoint cadence'i performance impact** → benchmark + implementation

Bu sorular cevaplanmadan implementation aşamasına geçilmez.

---

## Çekirdek özet — 16 karar + 34 violation tests

### 16 karar

1. Q runtime config değildir; signed artifact + M2 reference.
2. Sampling is not lossless compaction; sampling deterministic lossy condensation only for ring_buffer high-frequency families.
3. Permanent events are never sampled.
4. Sampling strategy enum'dan; semantic_importance/llm_selected/observer_selected/random_unseeded forbidden.
5. Production artifact: sampling.strategy.<family> her family için explicit NumericEntry zorunlu (M no-default); eksik = REJECT. Runtime strict fallback (numerics yok) → strategy=none full capture, ama bu "default" değil failsafe.
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
16. Missing Q numerics → strict audit-safe mode (permanent writes continue; sampling/compaction/tier_transition/LLM read disabled).

### 34 violation tests

§24'te listelendi.

### Yan güncelleme — F'ye iki yeni canonical event eklenir

```
LEDGER_STATE_CHANGED (ledger_meta family)
    Ledger operational state change / violation event;
    reason field discipline (sampling_activated, compaction_*, hash_*,
    storage_pressure_failsafe, tier_transition_performed, read_limit_exceeded,
    llm_read_scope_violation, meta_event_recursion_blocked, foreign_event_*,
    human_alert_batch_summary, failsafe_activated).

M1_READ_AUDIT_RECORDED (ledger_meta family)
    Normal M1 read audit event; tek event + reader_type discriminator
    (human / llm / replay / summarizer / external_audit / internal_high_frequency).
    Normal read audit ≠ ledger state change disiplini.
```

### Damıtma — son cümleler

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
> **N dış dünyanın hakkını sınırlar. O kendi geçmişine girme hakkını sınırlar. P hafızaya emin olma hakkını sınırlar. Q kendine bakma hakkını sınırlar.**
