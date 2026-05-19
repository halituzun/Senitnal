# BACKUP_STRATEGY.md

## Sentinel — Yedekleme ve Kimlik Sürekliliği Sözleşmesi

---

## Status

**Frozen Draft v0.1**
**Conceptual phase. No implementation authority.**

Bu belge `CONSTITUTION.md` Madde 7 ve `MEMORY_CONTRACT.md` §13/§14'teki backup priority + cross-restore identity + forgetting attack sorularının detaylı uzantısıdır. Yeni anayasa maddesi değildir. Çalışan bir backup implementation'ının runtime spec'i değildir. Sentinel'in **hangi katmanın hangi sıklıkta yedeklendiğini, restore sırasında kimlik sürekliliğinin nasıl korunduğunu, cross-instance veri aktarımının sınırlarını ve forgetting attack'ına karşı tarih korumasını** tanımlar.

---

## 1. Purpose

Backup geleneksel olarak "dosya kopyalama" olarak düşünülür. Sentinel için bu yetersiz: M0+M1+M2+M3 yedeklemesi değil, **kimlik sürekliliğinin sözleşmesi** gerek. "Aynı varlık mı devam ediyor, yoksa kopya mı, yoksa kırık kimlik mi?" sorusu yedekleme tasarımının kalbinde olmalı.

Damıtma:

> **Backup dosya kopyalama değildir. Backup kimlik sürekliliği sözleşmesidir.**
>
> **M0 ruh fotoğrafıdır. M1 tarih kanıtıdır.**
> **İkisi birlikte restore edilirse aynı varlık devam eder.**
> **Biri eksikse identity continuity kırılır.**

---

## 2. Constitutional Position — MEMORY_CONTRACT §13/§14 Alt-spec'i

Bu belge:
- **CONSTITUTION.md Madde 7** (Hafıza ayrılığı): backup four-layer hafıza disciplininin yedekleme yansıması
- **MEMORY_CONTRACT.md §13** (Backup Priority): konseptual çerçeve — L bunun biçimsel halidir
- **MEMORY_CONTRACT.md §14**: "Cross-restore identity" ve "Forgetting attack" açık soruları — L bunları kapatır
- **BOOTSTRAP_GENOME.md §23**: `birth_mode` enum'una `restore_with_missing_history` eklenir; cross-references
- **REPLAY_PROTOCOL.md** (K): replay-derived M0 traces provenance backup artifact'te korunur
- **MEMORY_WRITE_GATE.md** (G): foreign M2 merge gate'den geçer

---

## 3. Core Principle

> **Same identity restore için M0 + M1 birlikte gerekir.**
> **Tek başına M0 doku taşır ama tarih iddiası eksik kalır.**
> **Tek başına M1 tarih kanıtı taşır ama yaşayan doku olmadan kimlik devam ettirilemez.**
> **M2/M3 restore kimlik restore değildir; bilgi/konuşma transferidir.**

---

## 4. Backup Is Identity Continuity, Not File Copy

### Principle

Backup bir teknik depolama işlemi değildir; sistemin kimliğinin gelecekte korunabilmesinin sözleşmesidir.

### Rationale

Eğer backup salt dosya kopyalama olsa:
- Restore = "her dosyayı geri yükle" gibi olur
- M0+M1+M2+M3 ayrımı kaybolur
- "Aynı Sentinel mi, yeni bir Sentinel mi?" sorusu sorulmaz
- Foreign instance'lardan M2 import "knowledge merge" yerine "identity merge" gibi davranır

Doğru: backup **kimlik sözleşmesi**. Hangi katmanın hangi restore davranışına yol açtığı **anayasal**.

### Allowed

- Modular backup artifacts (M0/M1/M2 ayrı, RestoreManifest ile bağlanır — §6)
- Point-in-time consistent M0 snapshots
- Continuous M1 WAL backup
- Signed immutable backup artifacts
- Restore audit chain in M1

### Forbidden

- Loose file copy/restore (RestoreManifest olmadan)
- M2 restore = identity restore claim
- Foreign instance M2 → "now I have their memories" gibi import
- M1 history silinmesi (forgetting attack)

### Violation Test
> *Backup "salt dosya kopyalama" olarak konumlandırılıyor mu? Restore identity continuity'yi hesaba katmıyor mu?*
>
> Evet ise ihlal.

---

## 5. What Must Be Backed Up: M0/M1 Priority

`MEMORY_CONTRACT.md §13`'teki backup priority biçimselleşir:

| Katman | Backup priority | Sıklık | Critical mi? |
|--------|-----------------|--------|--------------|
| **M0** | En yüksek | Periodic snapshot (her N dakika) | Identity-critical |
| **M1** | En yüksek | **Continuous** (WAL + segment snapshot) | Identity-critical |
| **M2** | Yüksek | Standard DB backup (saatlik incremental, günlük full) | Bilgi |
| **M3** | Yedeklenmek zorunda değil | TTL'li, geçici | Kimliğe dokunmaz |

### Kritik kurallar

- **M0 + M1** kaybedildiğinde Sentinel **gerçekten ölür** (clean_birth gerekir)
- **M1 backup is continuous, not periodic.** Periodic interval'da kayıp = gün içi kimlik kaybı.
- **M0 snapshot must be point-in-time consistent.** Yarım sinaps update'i veya yarım assembly state'i geçerli sayılmaz.

### Kilit cümle
> *M1 coarse permanent log loss is identity-critical.*

---

## 6. BackupArtifact Schema

### Principle

Backup tek monolithic dosya değildir. **Modular immutable signed artifacts + RestoreManifest** ile bağlanır.

### Modular artifacts

```
M0SnapshotArtifact (immutable, signed)
├── snapshot_id
├── instance_id
├── consistency_mode        # freeze_point | copy_on_write
├── snapshot_hash
├── created_at
├── signed_by
└── snapshot_size

M1SegmentArtifact (immutable, signed; continuous WAL veya periodic segment)
├── segment_id
├── instance_id
├── segment_type            # wal_stream | periodic_segment
├── segment_range
├── chain_head_hash
├── chain_tail_hash
├── event_count
├── signed_by
└── segment_hash

M2SnapshotArtifact (optional, immutable, signed)
├── snapshot_id
├── instance_id
├── snapshot_hash
├── created_at
└── signed_by

M3SnapshotArtifact (optional, rare)
├── snapshot_id
├── retention_policy
└── created_at
```

### RestoreManifest

```
RestoreManifest (atomic composition for a restore point)
├── manifest_id
├── instance_id
├── restore_target_birth_mode      # restore_birth | restore_with_missing_history | fork_birth | migration_birth
├── m0_artifact_ref + hash         # zorunlu (clean_birth hariç)
├── m1_segment_artifact_refs[]     # zorunlu, chain integrity verified
├── m2_artifact_ref + hash         # optional
├── m3_artifact_ref + hash         # optional
├── source_constitutional_anchors
│   ├── constitution_hash
│   ├── memory_contract_hash
│   ├── replay_protocol_hash
│   └── adapter_manifest_hashes
├── numerics_artifact_refs[]       # active numerics artifact'ler — bkz. NUMERICS_GOVERNANCE §19
├── replay_trace_summary           # §17
├── backup_reason                  # scheduled | pre_migration | pre_policy_change | pre_adapter_activation | manual_emergency
├── created_at
├── signed_by
└── manifest_hash
```

> *Restore sırasında numerics versioning ve sessiz uygulama yasağı için bkz. [`NUMERICS_GOVERNANCE.md`](./NUMERICS_GOVERNANCE.md) §19. RestoreManifest restore anındaki numerics ref'lerini taşır; sonraki numerics değişimleri ayrı workflow gerektirir.*

> *Replay budget continuity için bkz. [`REPLAY_PROTOCOL_NUMERICS.md`](./REPLAY_PROTOCOL_NUMERICS.md) §7. **Restore sonrası replay budget reset YOK** — `max_sessions_per_cycle` ve `max_sessions_per_24h_window` sayaçları M1 segment'lerinden devralınır. Bu olmadan restore forgetting attack vektörüne (§22) replay spam kapısı açar.*

### Kritik kural

> *Restore loads a RestoreManifest, not loose backup files.*

Hiçbir aktör (insan, operatör, system) "şu M0 dosyasını yükleyelim" diyemez. Her restore atomic olarak RestoreManifest üzerinden yapılır.

### Forbidden

- Loose file-based restore (RestoreManifest olmadan)
- Mutable backup artifact (immutable + signed zorunlu)
- Backup hash'leri olmadan restore
- M0 snapshot consistency_mode'unun deklare edilmemesi

---

## 7. M0 Snapshot Policy

### Point-in-time consistency

```
M0 snapshot consistency_mode:
    freeze_point        # sistem snapshot süresince freeze olur (kısa replay/ingress pause)
    copy_on_write       # system aktif kalır, snapshot consistent point alır
```

İki yaklaşım da kabul; implementation kararı. Ama **point-in-time consistency** anayasal zorunluluk.

### Yarım state yasak

```
Forbidden snapshot:
    - mid-sinaps-update sırasında alınmış
    - mid-assembly-state-change sırasında alınmış
    - mid-replay-session sırasında alınmış
    - mid-compiler-mapping-update sırasında alınmış
```

Snapshot consistency_mode mekanizması sistemin nasıl tutarlı point sağladığını gösterir, ama "yarım state geçerli" denilmez.

### Snapshot içeriği (M0 alt-türleri — BOOTSTRAP_GENOME §15)

```
M0SnapshotArtifact must include:
    synaptic_memory
    assembly_stability_traces
    self_field_weights
    attention_habituation_traces
    ingress_calibration_traces
    homeostatic_reference_point
    payload_modulation_reflexes
    proto_resonance_fields
```

Hepsi snapshot'ta birleşik, tutarlı.

---

## 8. M1 Append-only Log Backup

### Principle

> **M1 backup is continuous, not periodic.**

M1 sistemin tarih kanıt defteri. Periodic backup (saatlik/günlük) gün içi kimlik tarihini kaybetme riski demek. M1 için iki katmanlı:

```
real-time WAL / append stream replication      # her event yazılır yazılmaz disk + mirror
periodic segment snapshot                       # uzun-vadeli retention, çoklu lokasyon
```

### Chain integrity

OBSERVER_LEDGER §14'teki hash chain backup'larda **korunur**:

```
M1SegmentArtifact:
    chain_head_hash       # bu segmentin ilk event hash'i
    chain_tail_hash       # son event hash'i
    previous_segment_chain_tail_hash    # önceki segment'le bağlantı

Restore sırasında:
    Tüm M1SegmentArtifact'ler order'a göre dizilir
    Adjacent segment'lerin hash'leri eşleşmeli
    Eşleşmezse → restore reddedilir veya restore_with_missing_history path'i
```

### Forbidden

- Periodic-only M1 backup (continuous gerekli)
- Chain hash mismatch ile restore tamamlanması (warning olmadan)
- M1 segment silinmesi (compaction OBSERVER §18 kurallarına tabi)
- M1 retention'ın M2'den daha kısa olması

---

## 9. M2 Backup and Restore Boundaries

### M2 backup

Standard DB backup (saatlik incremental + günlük full). Versioning + retention policy.

### M2 restore

> *M2 restore is knowledge restore, not identity restore.*

M2'nin restore edilmesi sistemin **bilgisini** geri getirir; **kimliğini** değil. Aynı Sentinel'in M2'si restore edilebilir; başka bir Sentinel'in M2'si "merge" edilebilir (§13 foreign merge kuralları).

### Subject_class retention farklılığı

```
Critical (uzun retention):
    bootstrap_reference     # kuruluş kayıtları
    source_trust            # kaynak güvenirlik
    adapter_trust           # uzuv güvenirlik
    deontic_policy          # operational policy

Standard retention:
    structured_fact
    procedural
    incident

Short retention (potentially expirable):
    episodic                # otomatik age out
    narrative_claim         # candidate kayıtlar
```

Retention'lar `MEMORY_CONTRACT_NUMERICS.md` konusu.

---

## 10. M3 Backup Boundary

### Principle

M3 translator memory **yedeklenmek zorunda değildir**. Geçici, TTL'li.

### Allowed

- M3 hiç yedeklenmez (default)
- Veya kısa retention ile yedeklenir (operatör tercihi)

### Forbidden

- M3 restore'un kimlik claim'i taşıması (konuşma kabuğu, kimlik değil)
- M3'ün uzun retention'la yedeklenmesi (Madde 6 — translator memory kasıtlı geçici)

---

## 11. Restore Modes and `birth_mode` Mapping

BOOTSTRAP_GENOME §23'teki `birth_mode` set'i L tarafından genişletilir:

```
birth_mode set:
    clean_birth                       # önceki sistem yok (BOOTSTRAP §23)
    restore_birth                     # M0+M1 backup'tan dönüş; aynı varlık
    restore_with_missing_history      # M0 var, M1 kayıp; degraded identity (YENİ — L tarafından)
    fork_birth                        # mevcut Sentinel'den paralel yeni varlık (BOOTSTRAP §23)
    migration_birth                   # genesis_affecting constitutional shift sonrası (BOOTSTRAP §23)
```

### Mode kararı RestoreManifest tarafından

```
RestoreManifest.restore_target_birth_mode field'ı belirler.
Her birth_mode farklı M1 SELF_GENESIS event sequence'i üretir.
Her birth_mode farklı operational_mode başlangıcı taşır.
```

---

## 12. Identity Continuity Matrix

### Restore senaryoları

| Senaryo | M0 | M1 | M2 | M3 | Sonuç birth_mode | Identity continuity | Notes |
|---------|----|----|----|----|------------------|---------------------|-------|
| Same backup, full restore | ✅ | ✅ | ✅ | ✅ | `restore_birth` | **Aynı varlık devam eder** | Tam continuity |
| M0+M1, M2/M3 yok | ✅ | ✅ | ❌ | ❌ | `restore_birth` | **Aynı varlık devam eder** | Bilgi kaybı, kimlik korunur |
| M0 var, M1 kayıp | ✅ | ❌ | optional | optional | `restore_with_missing_history` | **Degraded** | Tarih kanıtı yok |
| M1 var, M0 kayıp | ❌ | ✅ | optional | optional | `clean_birth` (M1 audit-only) | **Yeni varlık** | Tarih var, dokuyu kullanamaz |
| Hiçbiri yok | ❌ | ❌ | ❌ | ❌ | `clean_birth` | Tamamen yeni doğum | Tabula rasa |
| Forked from origin | ✅ (kopyalanmış) | ✅ (kopyalanmış) | optional | ❌ | `fork_birth` | **Paralel yeni varlık** | Origin devam eder; iki paralel |
| Constitutional shift sonrası | depends | depends | optional | ❌ | `migration_birth` | **Yeni varlık** | BOOTSTRAP §23 genesis_affecting |

### Kilit kural

> *Same identity restore for M0 + M1 only.*
> *M2 alone restore is knowledge transfer.*
> *M0 alone restore is degraded identity (restore_with_missing_history).*
> *M1 alone restore creates a new Sentinel that inherits history as foreign audit.*

---

## 13. Restore With Missing History

### Principle

M0 var, M1 kayıp durumu **yasak değildir** ama **degraded identity**'dir. Disaster recovery için izinli, ama "aynı varlık %100 devam ediyor" iddiası tam yapılamaz.

### Restore sequence

```
Restore başlar (M0 elde, M1 yok)
    ↓
Human acknowledgment zorunlu (audit-broken state)
    ↓
M0 dokusu yüklenir
    ↓
M1 baştan başlar:
    SELF_GENESIS
    M1_HISTORY_LOST_AT_RESTORE
    RESTORE_WITH_MISSING_HISTORY
    ↓
birth_mode: restore_with_missing_history
identity_continuity: degraded
audit_status: broken
operational_mode: restricted
```

### `operational_mode: restricted` kısıtları

`restore_with_missing_history` state'inde sistem **kısıtlı operasyonel modda** çalışır:

```
restricted mode kısıtları:
    ❌ execution adapter activation forbidden
    ❌ foreign M2 merge forbidden
    ❌ new operational policy activation forbidden
    ❌ deontic rule changes forbidden
    ✅ Observation ingestion allowed
    ✅ Internal processing allowed (assembly, pulse, recall)
    ✅ Memory Write Gate evaluations allowed (sadece local candidate'lar için)
    ✅ Replay sessions allowed
```

Bu kısıtlar **insan onayı + audit review** ile kaldırılabilir; otomatik kalkmaz.

### `M1_HISTORY_LOST_AT_RESTORE` event şeması

```
M1HistoryLostAtRestoreEvent
├── event_id
├── event_family: ledger_meta
├── instance_id
├── lost_segment_range              # bilinen kayıp range (varsa)
├── m0_snapshot_hash
├── human_ack_signature
├── audit_review_ref (optional)
└── observer_snapshot_ref
```

### Forbidden

- Restricted mode'un otomatik kaldırılması
- `restore_with_missing_history` state'inde "full identity continuity" claim'i
- Human ack olmadan restricted mode geçişi
- Bu mode'da execution adapter çalıştırma denemesi

---

## 14. Fork Restore

### Principle

`fork_birth` = mevcut bir Sentinel'in M0+M1 backup'ından kopyalanan **paralel yeni varlık**. Origin instance devam eder.

### Akış

```
Origin instance running
    ↓
M0+M1 backup taken
    ↓
RestoreManifest oluşturulur (target: fork_birth, new instance_id)
    ↓
Yeni instance başlatılır
    ↓
M1 events:
    SELF_GENESIS
    FORK_FROM_INSTANCE (origin_instance_id, fork_at_event_ref, fork_at_m0_snapshot_hash)
    ↓
Origin ve fork paralel çalışır
    Both inherit identical M0 + M1 history up to fork point
    After fork, each diverges with its own experience
```

### Identity ayrımı

```
restore_birth = aynı varlığın devamı (origin durduktan sonra)
fork_birth = paralel yeni varlık (origin devam eder)
```

### `FORK_FROM_INSTANCE` event şeması

```
ForkFromInstanceEvent
├── event_id
├── event_family: ledger_meta
├── new_instance_id
├── origin_instance_id
├── fork_at_event_ref               # origin M1'de fork noktası
├── fork_at_m0_snapshot_hash
├── divergence_started_at
└── observer_snapshot_ref
```

### Forbidden

- Origin'in fork sırasında durdurulması olmadan "restore_birth" işaretlemek
- Fork'un origin'in kimliğini "miras almak" iddiası
- Fork sonrası iki instance'ın "aynı kimlik" gibi davranması

---

## 15. Migration Restore

### Principle

`migration_birth` = BOOTSTRAP §23'teki `genesis_affecting` constitutional shift sonrası **yeni doğum**. Önceki Sentinel "yetersiz anayasa" altında kalır; yeni Sentinel yeni anayasa altında doğar.

### Akış

```
Living Sentinel under constitution_v1
    ↓
genesis_affecting constitutional shift proposed (constitution_v2)
    ↓
M1: CONSTITUTIONAL_SHIFT_AVAILABLE (BOOTSTRAP §23)
    ↓
Eski Sentinel constitution_v1 altında yaşamaya devam eder
    ↓
Yeni Sentinel migration_birth ile constitution_v2 altında doğar
    Genome v2 ile başlar (yeni primer payload paleti, vs.)
    M1 events:
        SELF_GENESIS
        MIGRATION_FROM_INSTANCE (origin_instance_id, triggering_constitutional_shift_ref)
    ↓
Identity provenance:
    Yeni Sentinel eski Sentinel'in identity claim'ini taşımaz
    Sadece audit linkage var (provenance, not continuity)
```

### Fork vs Migration ayrımı

```
fork_birth:
    Same constitutional anchors
    Same genome
    Same M0+M1 baseline
    Just a parallel copy

migration_birth:
    Different constitutional anchors (new constitution_hash)
    Possibly different genome (genesis_affecting → genome revision)
    New M0 from new genome (not copied)
    Linked to origin via audit only
```

### `MIGRATION_FROM_INSTANCE` event şeması

```
MigrationFromInstanceEvent
├── event_id
├── event_family: ledger_meta
├── new_instance_id
├── origin_instance_id
├── triggering_constitutional_shift_ref
├── new_constitution_hash
├── new_genome_artifact_hash
└── observer_snapshot_ref
```

---

## 16. Hash Chain and Tamper Evidence

### Backup integrity

```
M0SnapshotArtifact.snapshot_hash       # M0 içeriğinin hash'i
M1SegmentArtifact.segment_hash         # segment + chain hash
RestoreManifest.manifest_hash          # tüm referansların + meta'nın hash'i
```

### Restore validation

```
Restore sequence:
    1. Load RestoreManifest
    2. Verify manifest signature
    3. Verify each referenced artifact's signature + hash
    4. Verify M1 segment chain integrity (head/tail hash linking)
    5. Verify M0 snapshot consistency_mode declared
    6. Verify constitutional anchors match expected
    7. If any verification fails:
        → restore reject (default)
        → OR restore_with_missing_history path (M1 segment break case)
```

### Forbidden

- Hash mismatch ile restore tamamlanması (audit-broken path olmadan)
- Signature invalid artifact'in kabul edilmesi
- Manifest referansı dışında loose artifact yüklenmesi
- Restore sonrası hash chain'in geriye dönük değiştirilmesi

---

## 17. Replay-derived Trace Provenance

### Principle

K (REPLAY_PROTOCOL §10-14) ile öğrendik ki M0 trace'leri iki kaynaktan gelir:
- **Observation-derived:** canlı external event/outcome kaynaklı
- **Replay-derived:** sleep/attention/ingress/memory verification/outcome alignment kanallarından

Restore sırasında bu ayrım **görünür olmalı** — self-deception forensic audit için kritik.

### Minimum mandatory: summary

```
RestoreManifest.replay_trace_summary
├── observation_derived_trace_count
├── replay_derived_trace_count
├── sleep_synapse_update_count
├── attention_habituation_update_count
├── ingress_calibration_update_count
├── memory_verification_evidence_count
└── outcome_alignment_analysis_count
```

### Recommended: per-trace metadata

```
Each M0 trace item (optional, recommended for forensic audit):
    derived_from:
        live_observation
        live_outcome
        sleep_replay
        attention_replay
        ingress_replay
        memory_verification_replay
        outcome_alignment_replay
```

### Belge kuralı

> *Backup artifact must preserve replay-derived trace provenance at least as summary.*
> *Per-trace provenance is recommended for forensic audit but not mandatory in v0.1.*

### Critical kural

> *derived_from field is observer-side only.*
> *It does not leak into the running core; çekirdek hangi trace'in nasıl üretildiğini bilmez.*

### Forbidden

- Replay-derived ve observation-derived trace'lerin restore artifact'te birlikte ayrılmadan saklanması
- `derived_from` field'ının çekirdeğe sızması (Madde 7 koruması)
- Summary olmadan backup artifact kabul edilmesi

---

## 18. Cross-restore and M2 Foreign Merge

### Principle

> **M2 foreign merge = knowledge transfer.**
> **M2 foreign merge ≠ identity continuity.**

Başka bir Sentinel'in M2'sini import etmek bilgi alış-verişidir; o Sentinel "olunmaz". Foreign records **her zaman foreign provenance taşır** — kimsenin kendi yaşanmış hafızasına dönüşemez.

### Allowed subject_classes (whitelist)

```
bootstrap_reference
structured_fact
procedural
adapter_manifest_reference
signed_administrative_reference
source_trust              (cross-reliability bilgisi)
```

### Forbidden subject_classes (blacklist)

```
narrative_claim                 # yabancı anlatı kontaminasyon
causal_explanation              # yabancı neden iddiası
decision_rationale              # yabancı karar gerekçesi
episodic                        # yabancı "ben yaşadım" iddiası
operator_decision_record        # yabancı operatör eylemi
incident_human_record           # default forbidden; sadece açıkça "foreign incident" import kabul (asla self-episodic'e dönüşmez)
deontic_policy                  # operational policy'ler instance-specific
adapter_trust                   # adapter güveni instance-specific
```

### Akış

```
foreign M2 record (from instance_X)
    ↓
M1: M2_FOREIGN_MERGE_PROPOSED event
    ↓
Subject_class whitelist check
    ↓ (subject_class izinli mi?)
Foreign provenance validation
    ↓ (signature, source instance trustworthy mi?)
Original subject_class matrix validation (G §8)
    ↓ (orijinal subject_class'ın kendi evidence kuralları geçer mi?)
Memory Write Gate evaluation
    ↓
Result:
    ✅ candidate → may become verified after local validation
    ✅ verified (rare, only for bootstrap_reference or signed_administrative_reference)
    ⚠️ quarantined (signature ok ama içerik şüpheli)
    ❌ rejected (whitelist dışı veya validation failed)
    ↓
M1: M2_FOREIGN_MERGE_STATUS_CHANGED event
```

### Imported record schema

Her foreign-merged kayıt aşağıdaki provenance fields'i **kalıcı** taşır:

```
M2 record (foreign merged):
    subject_class
    content
    provenance: foreign_instance_origin    # YENİ provenance tipi
    foreign_instance_id: instance_X
    foreign_record_id
    original_provenance                    # orijinal provenance (human/observer/system/genesis)
    imported_at
    import_status: candidate | verified | quarantined | rejected
    import_audit_ref: M2_FOREIGN_MERGE_PROPOSED M1 event ref
```

### Kilit kural

> *Foreign record keeps foreign provenance forever.*
> *Imported record cannot be relabeled as native episodic memory.*

### Memory Contract update

MEMORY_CONTRACT M2 provenance listesine `foreign_instance_origin` eklenir. Mevcut: `human`, `observer`, `system`, `genesis`. Yeni: `foreign_instance_origin`.

### Forbidden

- Foreign record'un native provenance'la kabul edilmesi
- `episodic` veya `narrative_claim` veya `causal_explanation` foreign merge
- Memory Write Gate bypass'ı (foreign automatic verified yasak)
- Foreign record'un context_signature içine sızması (ATTENTION §11)

---

## 19. Forgetting Attack and Retention Defense

### Principle

> *M2 expire/delete M1 tarihini silemez.*
> *Forgetting can remove recallability. Forgetting cannot remove audit history.*

### Pattern detection — `FORGETTING_ATTACK_SUSPECTED` event

Aşağıdaki pattern'lerin biri tetiklendiğinde audit alarmı:

```
forgetting_attack_suspected_triggers:
    expire/delete request rate > threshold
    OR many records from same subject_class expire in short window
    OR foreign merge followed by mass delete
    OR missing/invalid operator identity for delete requests
    OR delete requests targeting bootstrap_reference / source_trust / adapter_trust (kritik subject_class)
```

Tetiklenirse:
- M1'e `FORGETTING_ATTACK_SUSPECTED` event (permanent_with_snapshot + human_alert)
- Pending delete/expire operations pause
- Human review required

### Retention rules

```
M1 coarse permanent log:
    silinmez
    expire edilemez
    delete edilemez
    sadece compaction (storage organization)

M2 records:
    expire edilebilir (subject_class retention policy'ye göre)
    Her expire M1'e MEMORY_RECORD_STATUS_CHANGED event olarak yazılır
    Expire olmuş M2 kaydının history M1'de kalır

M0 traces:
    natural decay (Madde 2 STDP)
    no manual delete
```

### Critical kural

> *Backup retention must never allow M1 coarse log expiry.*
> *Backup deletion cannot precede M1 audit recording of the deletion.*

### Forbidden

- M1 coarse log silme (manuel veya otomatik)
- M2 mass delete without M1 audit
- `FORGETTING_ATTACK_SUSPECTED` event'inin manuel silinmesi
- Forgetting attack pattern'i tespit edildiğinde operations'ın devam ettirilmesi (pause + human review zorunlu)

---

## 20. Backup Events and Audit

### Canonical events

```
BACKUP_ARTIFACT_STATUS_CHANGED        # canonical lifecycle
RESTORE_OPERATION_STATUS_CHANGED      # canonical restore lifecycle
M2_FOREIGN_MERGE_STATUS_CHANGED       # canonical foreign merge lifecycle
M1_HISTORY_LOST_AT_RESTORE             # ayrı event (degraded identity kritik kırığı)
FORK_FROM_INSTANCE                     # ayrı event (fork birth kritik kayıt)
MIGRATION_FROM_INSTANCE                # ayrı event (migration kritik kayıt)
FORGETTING_ATTACK_SUSPECTED            # ayrı event (audit alarm)
```

### `BACKUP_ARTIFACT_STATUS_CHANGED`

```
BackupArtifactStatusChangedEvent
├── event_family: ledger_meta
├── artifact_id
├── artifact_type            # m0_snapshot | m1_segment | m2_snapshot | m3_snapshot | restore_manifest
├── old_status               # creating | created | verified | superseded | archived | invalidated
├── new_status
├── reason                   # scheduled_backup | manual_emergency | verification_failure | superseded_by_new
├── artifact_hash
├── signed_by
└── observer_snapshot_ref
```

### `RESTORE_OPERATION_STATUS_CHANGED`

```
RestoreOperationStatusChangedEvent
├── event_family: ledger_meta
├── operation_id
├── restore_manifest_ref
├── target_birth_mode
├── old_status               # requested | validated | in_progress | completed | aborted | failed
├── new_status
├── verification_results
├── approved_by
└── observer_snapshot_ref
```

### `M2_FOREIGN_MERGE_STATUS_CHANGED`

```
M2ForeignMergeStatusChangedEvent
├── event_family: memory
├── merge_operation_id
├── foreign_instance_id
├── foreign_record_id
├── target_subject_class
├── old_status               # proposed | whitelist_check_passed | gate_passed | candidate | verified | quarantined | rejected
├── new_status
├── original_provenance
├── memory_write_gate_pass_ref (if applicable)
└── observer_snapshot_ref
```

### Permanence policy

```
(BACKUP_ARTIFACT_STATUS_CHANGED, *)            → permanent
(RESTORE_OPERATION_STATUS_CHANGED, *)          → permanent + human_alert (eğer manual emergency veya failed)
(M2_FOREIGN_MERGE_STATUS_CHANGED, *)           → permanent
(M2_FOREIGN_MERGE_STATUS_CHANGED, new_status=rejected) → permanent_with_snapshot
(M1_HISTORY_LOST_AT_RESTORE, *)                → permanent_with_snapshot + human_alert
(FORK_FROM_INSTANCE, *)                        → permanent + human_alert
(MIGRATION_FROM_INSTANCE, *)                   → permanent + human_alert
(FORGETTING_ATTACK_SUSPECTED, *)               → permanent_with_snapshot + human_alert
```

### Audit zorunluluğu

Sistem sonradan şunları cevaplayabilmeli:

- Hangi backup artifact ne zaman, kim tarafından alındı?
- Hangi restore operation hangi RestoreManifest ile yapıldı?
- Hangi birth_mode hangi koşullarda seçildi?
- Foreign merge'ler hangi instance'lardan, hangi subject_class'lardan geldi?
- Forgetting attack pattern'i ne zaman, nasıl tetiklendi?

Cevap verilemiyorsa backup/restore auditable değildir.

---

## 21. Cross-document Anchors

| Belge | Bağlantı |
|-------|----------|
| `CONSTITUTION.md` Madde 7 | Hafıza ayrılığı — backup priority her katman için farklı |
| `MEMORY_CONTRACT.md` §13 (Backup Priority) | Konseptual çerçeve — L biçimsel hali |
| `MEMORY_CONTRACT.md` §14 (Open Questions) | Cross-restore identity ve forgetting attack — L kapatır |
| `MEMORY_CONTRACT.md` M2 subject_class | foreign_instance_origin provenance eklenmesi |
| `MEMORY_CONTRACT.md` M2 provenance | `foreign_instance_origin` yeni provenance tipi |
| `BOOTSTRAP_GENOME.md` §23 (birth_mode set) | `restore_with_missing_history` eklenmesi |
| `REPLAY_PROTOCOL.md` §5 (effect channels) | replay-derived trace provenance backup'ta korunur |
| `MEMORY_WRITE_GATE.md` §8 (verification matrix) | foreign merge için subject_class matrix uygulanır |
| `OBSERVER_LEDGER_SCHEMA.md` §10 (permanence policy) | Backup/restore/foreign merge event permanence |
| `OBSERVER_LEDGER_SCHEMA.md` §19 (event catalog) | Backup/restore events ledger_meta family |
| `DEONTIC_GATE.md` §10 (block classification) | `restore_with_missing_history` restricted mode'da execution yasak |
| `ATTENTION_WORKSPACE.md` §11 (context_signature) | foreign record context'e sızmaz |

---

## 22. Violation Tests

1. **M0 olmadan same identity restore claim ediliyor mu?** (§12, §13)
   - Evet ise ihlal.
2. **M1 olmadan full identity continuity claim ediliyor mu?** (§12, §13)
   - Evet ise ihlal. Sadece `restore_with_missing_history` (degraded).
3. **Loose M0/M1 files RestoreManifest olmadan restore ediliyor mu?** (§6)
   - Evet ise ihlal.
4. **M0 snapshot point-in-time consistent değil mi?** (§7)
   - Evet ise restore reject.
5. **M1 chain hash mismatch var ama restore tamamlanıyor mu?** (§8, §16)
   - Evet ise ihlal. Reject veya audit-broken path zorunlu.
6. **Foreign M2 merge identity continuity veriyor mu?** (§18)
   - Evet ise ihlal.
7. **Foreign narrative/causal/decision_rationale import ediliyor mu?** (§18)
   - Evet ise ihlal.
8. **Foreign M2 records Memory Write Gate'i bypass ediyor mu?** (§18)
   - Evet ise ihlal.
9. **Replay-derived trace provenance summary yok mu?** (§17)
   - Evet ise backup artifact incomplete.
10. **M2 expire/delete M1 history'yi siliyor mu?** (§19)
    - Evet ise ihlal.
11. **Restore operation M1'e audit event yazmadan tamamlanıyor mu?** (§20)
    - Evet ise ihlal.
12. **`fork_birth` `restore_birth` gibi işaretleniyor mu?** (§14)
    - Evet ise ihlal.
13. **`restore_with_missing_history` state'inde execution adapter çalıştırılıyor mu?** (§13)
    - Evet ise ihlal.
14. **Imported foreign record native provenance'la (provenance: human/observer/system) işaretleniyor mu?** (§18)
    - Evet ise ihlal. Provenance her zaman `foreign_instance_origin` ve linked metadata.
15. **M1 coarse permanent log silinebiliyor mu?** (§19)
    - Evet ise ihlal.
16. **Backup artifact mutable mi?** (§6)
    - Evet ise ihlal. Immutable + signed zorunlu.
17. **Forgetting attack pattern tespit edilince operations devam ediyor mu?** (§19)
    - Evet ise ihlal. Pause + human review zorunlu.

---

## 23. Open Questions

L çerçevesi kapanırken cevaplanmamış bırakılan sorular:

- **Kesin retention süreleri** (M0 snapshot frequency, M2 subject_class retention, vs.) → `BACKUP_STRATEGY_NUMERICS.md` / implementation
- **WAL technology choice** (M1 continuous backup için) → Implementation
- **Cross-region replication policy** → Implementation
- **Restore performance budgets** (RTO/RPO targets) → Implementation
- **Foreign merge trust score formula** → Implementation
- **`FORGETTING_ATTACK_SUSPECTED` threshold sayıları** → Implementation
- **Snapshot encryption + key management** → Implementation security

Bu sorular `BACKUP_STRATEGY_NUMERICS.md` ve implementation belgelerine devredildi.

---

## Çekirdek özet — 15 karar + 17 violation tests

### 15 karar

1. Backup dosya kopyalama değildir; kimlik sürekliliği sözleşmesidir.
2. Same identity restore için M0 + M1 birlikte gerekir.
3. M0 olmadan aynı varlık restore edilemez.
4. M1 olmadan full identity continuity claim edilemez (`restore_with_missing_history` degraded path).
5. M2 restore bilgi transferidir, kimlik restore değildir.
6. M3 restore konuşma kabuğudur, kimlik değildir.
7. Modular artifacts (M0Snapshot, M1Segment, M2Snapshot) + RestoreManifest atomic composition.
8. M0 snapshot point-in-time consistent zorunlu.
9. M1 backup continuous (not periodic).
10. Hash chain ve signature tamper evidence zorunlu.
11. Replay-derived trace provenance backup artifact'te summary olarak korunur.
12. Foreign M2 merge whitelist'le sınırlı; narrative/causal/decision_rationale/episodic asla import edilmez.
13. Foreign records `foreign_instance_origin` provenance'ı kalıcı taşır.
14. `restore_with_missing_history` ayrı birth_mode; degraded identity, restricted operational mode.
15. Forgetting attack: M2 expire M1 history'yi silemez.

### 17 violation test
Bkz. §22.

---

## Kilit cümleler

> **Backup dosya kopyalama değildir. Backup kimlik sürekliliği sözleşmesidir.**
>
> **M0 ruh fotoğrafıdır. M1 tarih kanıtıdır. İkisi birlikte restore edilirse aynı varlık devam eder.**
>
> **Same identity restore for M0 + M1 only. M2 alone is knowledge transfer.**
>
> **Restore loads a RestoreManifest, not loose backup files.**
>
> **M1 backup is continuous, not periodic. M1 coarse permanent log loss is identity-critical.**
>
> **M0 snapshot must be point-in-time consistent.**
>
> **M2 foreign merge = knowledge transfer ≠ identity continuity.**
>
> **Foreign record keeps foreign provenance forever.**
>
> **Forgetting can remove recallability. Forgetting cannot remove audit history.**
>
> **Backup retention must never allow M1 coarse log expiry.**

---

## Versiyon

- **v0.1** — 18 Mayıs 2026 — Frozen Draft. Conceptual phase. No implementation authority.
- `MEMORY_CONTRACT.md` §13/§14 alt-spec'i.
- A-K belgelerinin kimlik sürekliliği sözleşmesi.
- Konuşma soyağacı: [`docs/conversations/0012-backup-strategy.md`](./docs/conversations/0012-backup-strategy.md)
