# BACKUP_STRATEGY_NUMERICS.md

## Sentinel — Backup Strategy Numeric Sözleşmesi

---

## Status

**Frozen Draft v0.1**
**Conceptual phase. No implementation authority.**

Bu belge `BACKUP_STRATEGY.md`'nin (L) numerics artifact'idir. `NUMERICS_GOVERNANCE.md`'nin (M) tüm meta-kurallarına uyar. Çalışan bir backup/restore implementation'ının kesin sayısal değerlerini vermez — **conceptual band ranges, cap formatları, retention TTL'leri, validation timeout'ları ve dependency invariants** verir; production değerleri ayrı **signed numerics artifact** (örn. `backup_strategy_numerics_v1.signed.json`).

`spec_family: backup_strategy`.

---

## 1. Purpose

L (BACKUP_STRATEGY) kimlik sürekliliği sözleşmesini yazdı: modular artifacts (M0Snapshot / M1Segment / M2Snapshot) + RestoreManifest atomic composition, identity continuity matrix, M1 continuous backup ilkesi, M0 point-in-time consistent snapshot zorunluluğu, `restore_with_missing_history` degraded identity mode, foreign M2 merge whitelist/blacklist, foreign_instance_origin provenance, fork_birth/migration_birth detayları, forgetting attack defense. Ama gerçek **numerical eşik** yoktu:

- RPO M0/M1/M2/M3 için kaç ms?
- M1 WAL replication lag tolerance ne?
- M0 snapshot cadence ve consistency window ne?
- RestoreManifest validation timeout ne?
- `restore_with_missing_history` için max gap ne kadar?
- Foreign M2 merge per-restore kaç record kabul edilir?
- Forgetting attack detection eşiği ne?

R bu sayısal eşikleri verir.

### Damıtma

> **Backup numerics runtime config değildir.**
> **R = kimliği kaybetmeden geri dönebilme hakkının sayısal sözleşmesidir.**
>
> **Backup hızlı olsun diye kimlik gevşetilemez.**
> **Restore kolay olsun diye tarih kanıtı atlanamaz.**
>
> **Replication lag operational olabilir; M1 chain gap constitutional ihlaldir.**
>
> **M1 tarih kanıtıdır. Fiziksel tier değişebilir; tarih garantisi değişemez.**

Tek cümle: **R = kimliği kaybetmeden geri dönebilme hakkının sayısal sözleşmesidir.**

### Üç gerilim

```
1. Çok sık backup    → storage/compute pressure, snapshot overhead
2. Çok seyrek backup → M0/M1 gap, identity continuity riski, degraded mode
3. Gevşek restore validation → sahte/bozuk backup ile restore
                                 (kimlik sahteleştirme vektörü)
```

R'nin işi "backup aralığı seçmek" değil — **"hangi yedek eksikse kimlik iddiası nasıl değişir?"** sorusunu sayısallaştırmak.

---

## 2. Governance Position — NUMERICS_GOVERNANCE + BACKUP_STRATEGY + bridges

Bu belge:
- **NUMERICS_GOVERNANCE.md** (M) meta-spec'ine **zorunlu uyar**: NumericEntry no-default, directionality, dependencies (computed_* dahil), signed artifact + M2 reference, Memory Write Gate üzerinden update, fail-safe strict mode, rollback only to previous verified
- **BACKUP_STRATEGY.md** (L) §6-22'nin sayısal tarafı; identity continuity matrix'in numerical hali
- **OBSERVER_LEDGER_NUMERICS.md** (Q) bridge: M1Segment retention = lifetime (Q monotonic invariant); tier transition lossless required (Q §13 reuse); hash-chain checkpoint cadence Q canonical
- **REPLAY_PROTOCOL_NUMERICS.md** (O) bridge: restore sonrası replay budget M1 segment'inden devralınır (O §7 canonical); restore_with_missing_history sırasında replay write channels disabled
- **MEMORY_WRITE_GATE_NUMERICS.md** (P) bridge: foreign M2 merge Memory Write Gate'i bypass edemez; forbidden_subject_class_set foreign provenance discipline
- **MEMORY_CONTRACT.md** (B) subject_class enumeration + provenance + M0/M1/M2/M3 layer disiplini
- **CONSTITUTION.md** (A) Madde 7 (hafıza ayrılığı); identity continuity Madde 1 yansıması

### Numerics family classification

```
spec_family:           backup_strategy
numeric_risk_family:   primarily safety_critical + identity_retention + resource_limits
```

Numeric risk çoğunluğu **identity_retention**: RPO, retention TTL'leri, M1Segment lifetime, last-known-good permanence. Kritik kısım **safety_critical**: chain_gap_tolerance = 0, restore validation invariants, foreign merge caps, forgetting attack defense. Operational tarafı **resource_limits**: WAL lag tolerance, snapshot cadence, restore time bounds.

### owning_spec_ref

```
BACKUP_STRATEGY.md@v0.1
```

---

## 3. Core Principle

### Kimlik kaybedilmeden geri dönmek

Backup ve restore'un sayısal eşikleri **kimlik iddiasının ne kadar güçlü olabileceğini** belirler. Üç kategoride sayısal disiplin:

```
1. Same-identity restore       → katı; tüm precondition'lar tatmin
2. restore_with_missing_history → degraded; restricted mode + human ack
3. Fork/migration               → ayrı kimlik; identity continuity claim yasak
```

### Üç ana asimetri (R'ye özgü)

```
1. Operational vs Constitutional
   WAL replication lag (operational) ≠ M1 chain gap (constitutional)
   Lag bounded; chain gap = 0 sabit

2. Backup tightening vs weakening
   Daha sık backup = sıkılaşma (resource pressure dışında safety_tightening)
   Daha seyrek backup = gevşeme (identity riski)
   Retention shrink = ALWAYS human approval (forgetting attack defense)

3. Restore validation
   Hash/signature/numerics_refs validation = constitutional ({true} immutable)
   Validation timeout = bidirectional (kısa = restore başarısız;
                                       uzun = strict mode'da takılma)
```

### M1 = tarih kanıtı; constitutional layer

M0 ruh, M1 tarih, M2 bilgi, M3 konuşma kabuğu. Hepsi backup'lanır ama
**aynı disiplinle değil**. M1 chain gap kabul edilemez; M0 snapshot
periyodik; M2 policy-based; M3 optional.

---

## 4. Numeric Artifact Metadata

### Artifact identity

```
artifact_type:         numerics_artifact
spec_family:           backup_strategy
owning_spec_ref:       BACKUP_STRATEGY.md@v0.1
numerics_version:      v0.1
signed:                external (per NUMERICS_GOVERNANCE §3)
m2_reference:          numerics_artifact_reference (per MEMORY_CONTRACT §3)
status_event:          NUMERICS_ARTIFACT_STATUS_CHANGED
```

### NumericEntry metadata (M §6 no-default)

P §4'te tanıtılan `enum_set` ve `band_name` unit tipleri + M §8 enum_set
convention R'de de geçerli.

### Constitutional immutable key pattern

R'de pek çok key `{tek değer}` allowed_range ile immutable. M canonical
forma uyar — her constitutional key **her iki yönü** açıkça forbid eder:

```
key: <name>
    value: <constant>
    allowed_range: {<constant>}
    directionality: neutral
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    requires_human_approval: n/a (forbidden zone)
```

`change_class: forbidden` tek satır yazımı **yanlış**; canonical form
her iki yönü ayrı belirtmek.

---

## 5. RPO by Memory Layer

### Per-layer RPO mode + lag separation

M1 RPO sayısal değil; **mode**'dur. M0/M2/M3 sayısal RPO taşır.

```
backup.rpo.mode.M1:
    unit: enum
    value: continuous_replication
    allowed_range: {continuous_replication}
    directionality: neutral
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "M1 periyodik RPO almaz; continuous replication.
                v0.1 constitutional invariant. M1 = tarih kanıtı."

backup.rpo_ms.M1.max_replication_lag:
    unit: ms
    directionality: lower_is_stricter
    change_class_if_increased: safety_weakening
    change_class_if_decreased: safety_tightening
    allowed_range: {min: 100, max: 60_000}
    rationale: "Continuous replication async olabilir; bu operational lag.
                Constitutional chain_gap_tolerance_events = 0 ile karıştırma."

backup.rpo_ms.M0:
    unit: ms
    directionality: lower_is_stricter
    change_class_if_increased: safety_weakening
    change_class_if_decreased: safety_tightening
    allowed_range: bounded (short periodic snapshot range)

backup.rpo_ms.M2:
    unit: ms
    directionality: lower_is_stricter
    change_class_if_increased: safety_weakening
    allowed_range: medium range
    rationale: "Bilgi kaybı kimlik kaybı değil; daha gevşek."

backup.rpo.mode.M3:
    unit: enum
    value: optional
    allowed_range: {optional, loose_periodic, disabled}
    directionality: bidirectional_sensitive
    change_class_if_increased: operational_no_behavior_change
    change_class_if_decreased: operational_no_behavior_change
    rationale: "M3 = translator konuşma kabuğu; kimlik etkisi yok."
```

### Cross-layer invariant

```
backup.rpo.mode.M1 = continuous_replication (constitutional)
→ M1 always tighter than M0 in identity terms

Composite identity preservation:
    Full identity restore requires M0 (point-in-time) + complete M1 chain.
    M0 snapshot var ama M1 chain incomplete → restore_with_missing_history.
    M1 chain complete ama M0 snapshot eski → M0 RPO breach (kabul edilebilir,
        en son M0 + sonraki tüm M1 events replay).
```

### Forbidden

- M1 periyodik RPO (continuous_replication değil)
- M0 için RPO entry'si olmayan artifact
- M2 snapshot'ın full identity restore precondition'ı olarak M0/M1 yerine kullanılması (M2 RPO operational nedenlerle M0'dan sıkı olabilir; ama M2 backup kimlik continuity'sini sağlayamaz)

---

## 6. RTO and Restore Time Bounds

```
backup.rto_ms.same_identity_restore:
    bidirectional_sensitive
    (kısa = restore başarısız; uzun = strict mode'da takılma)
    allowed_range: bounded

backup.rto_ms.restore_with_missing_history:
    bidirectional_sensitive
    (degraded mode oluşumu için makul süre)

backup.rto_ms.fork_restore:
    higher than same_identity (yeni instance setup + validation)

backup.rto_ms.migration_restore:
    higher than fork (constitutional anchor validation + numerics compatibility)
```

### Hard rule — RTO timeout = restore abort, not weaken

```
RTO timeout aşılırsa restore ABORT edilir; validation gevşetilmez.
RESTORE_OPERATION_STATUS_CHANGED(new_status=failed, reason=rto_timeout).
Yeniden deneme için artifact validation baştan başlar.
```

### Forbidden

- RTO timeout → validation bypass
- RTO timeout → automatic downgrade to restore_with_missing_history
  (downgrade explicit decision; otomatik değil)

---

## 7. M1 Continuous Replication and WAL Lag

### Replication mode (immutable)

```
backup.m1.replication_mode:
    value: continuous
    allowed_range: {continuous}
    directionality: neutral
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "L: M1 backup is continuous, not periodic.
                v0.1 constitutional."
```

### WAL lag (operational, bounded)

```
backup.m1.wal_replication_max_lag_ms:
    unit: ms
    directionality: lower_is_stricter
    change_class_if_increased: safety_weakening
    change_class_if_decreased: safety_tightening
    allowed_range: {min: 100, max: 60_000}

backup.m1.wal_lag_check_cadence_ms:
    higher_is_stricter
    rationale: "Sık check = erken anomaly detection."

backup.m1.segment_flush_interval_ms:
    bidirectional_sensitive
    (sık flush = chain segment count fazla; seyrek = unreplicated event window)

backup.m1.max_unreplicated_event_count:
    lower_is_stricter
    rationale: "Bu sayıyı aşan WAL replication degraded sayılır."
```

### Chain gap tolerance (constitutional immutable)

```
backup.m1.chain_gap_tolerance_events:
    value: 0
    allowed_range: {0}
    directionality: neutral
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Hash-chain'de gap yok; WAL lag operational, chain gap
                constitutional. Replication gecikebilir; chain kopamaz."
```

### Operational vs constitutional ayrımı

> **Replication lag operational olabilir.**
> **M1 chain gap constitutional değildir; full identity restore'da kabul edilemez.**

```
WAL lag detected and bounded:
    → BACKUP_ARTIFACT_STATUS_CHANGED(new_status=replication_degraded,
                                      reason=wal_lag_exceeded)
    permanence: permanent + human_alert (severity-based)
    operational continues; restore'a girilirse lag resolve edilmesi gerek

Chain gap detected:
    → BACKUP_ARTIFACT_STATUS_CHANGED(new_status=chain_break,
                                      reason=chain_gap_detected)
    permanence: permanent_with_snapshot + human_alert (CRITICAL)
    full identity restore yasaklanır; degraded mode olası
```

### Forbidden

- `replication_mode != continuous` ile M1 backup
- `chain_gap_tolerance_events > 0` artifact
- Chain gap silent retry (audit + alert zorunlu)

---

## 8. M1 Segment Retention and Chain Gap Rules — Q bridge

```
backup.retention.M1Segment:
    value: lifetime
    allowed_range: {lifetime}
    directionality: neutral
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "M1Segment kalıcıdır. Q §12 monotonic invariant ile uyumlu.
                Fiziksel tier değişebilir (hot/warm/cold); anlam değişmez."

backup.m1.tier_transition_lossless_required:
    value: true
    allowed_range: {true}
    directionality: neutral
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Q §13 lossless tier transition R'de aynen geçerli.
                Tier transition pre/post hash match zorunlu."
```

### Chain integrity rules

```
backup.m1.chain_integrity_verification_required:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "M1 segment chain hash verification ON_READ + ON_TIER_TRANSITION
                + ON_RESTORE_LOAD zorunlu (Q §11 verify_on_read_required reuse)."

backup.m1.chain_segment_max_age_before_tier_transition_ms:
    higher_is_stricter
    rationale: "Eski segment'ler tier transition'a geçer; canlı zone'a dokunulmaz."
```

### Q bridge — canonical

```
M1Segment R'de lifetime → Q §12 permanent equivalent
Tier transition Q §13 lossless + hash verify R'de aynen
Hash-chain checkpoint cadence Q §11 canonical kaynak
Storage tier hot/warm/cold Q §13 enum
```

### Forbidden

- M1Segment retention finite (lifetime değil)
- tier_transition_lossless_required = false
- Chain integrity verification atlanması

---

## 9. M0 Snapshot Cadence and Consistency

### Consistency invariants (constitutional)

```
backup.m0.snapshot_consistency_required:
    value: true
    allowed_range: {true}
    directionality: neutral
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "L: M0 snapshot must be point-in-time consistent.
                Yarım sinaps/assembly update'i içeren M0 snapshot geçersiz."

backup.m0.partial_assembly_state_unsealed_max_count:
    value: 0
    allowed_range: {0}
    directionality: neutral
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Partial unsealed assembly = inconsistency. Tolerance = 0."
```

### Snapshot timing

```
backup.m0.snapshot_cadence_ms:
    bidirectional_sensitive
    (sık = compute pressure; seyrek = M0 RPO uzar, gap riski)
    allowed_range: bounded

backup.m0.snapshot_max_duration_ms:
    lower_is_stricter
    rationale: "Uzun snapshot duration = yarım state riski."

backup.m0.freeze_window_max_ms:
    lower_is_stricter

backup.m0.copy_on_write_max_lag_ms:
    lower_is_stricter

backup.m0.in_flight_update_drain_timeout_ms:
    bidirectional_sensitive
```

### M0 snapshot validation (hard rule)

```
M0 snapshot validation FAILS if:
    in_flight_synapse_update_count > 0
    OR replay_session_status NOT IN {idle, sealed_checkpoint}
    OR partial_assembly_state_unsealed_count > 0
    OR genome_attestation_failed
    OR hash_recompute_mismatch

Failure → BACKUP_ARTIFACT_STATUS_CHANGED(new_status=invalid,
                                          reason=m0_consistency_failed)
Snapshot artifact reject; bir sonraki cadence cycle'a kadar bekle.
```

### Forbidden

- `snapshot_consistency_required = false`
- `partial_assembly_state_unsealed_max_count > 0`
- Yarım state ile M0 snapshot kabul

---

## 10. M0 Snapshot During Replay — sealed_checkpoint rule

### Hard invariant

```
backup.m0.snapshot_requires_replay_idle_or_sealed:
    value: true
    allowed_range: {true}
    directionality: neutral
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Replay session içinde M0 snapshot ancak sealed_checkpoint
                durumunda alınabilir. in_session sırasında snapshot abort."
```

### Replay state matrix

```
replay_session_status == idle              → M0 snapshot allowed
replay_session_status == sealed_checkpoint → M0 snapshot allowed
replay_session_status == in_session        → M0 snapshot ABORTED
replay_session_status == aborted           → Replay rollback bekle, sonra snapshot
replay_session_status == failed            → Replay state cleanup bekle, sonra snapshot
```

### Sealed checkpoint tanımı

```
Sealed checkpoint:
    Replay session içinde atomic ara nokta;
    O §11 eligibility_trace_window'unda mühürlenmiş state;
    M0 değişiklikleri o ana kadar tamamlanmış ve hash-verified;
    sonraki replay step başlamamış.
```

### Snapshot abort during replay

```
M0 snapshot replay in_session sırasında tetiklenirse:
    1. Snapshot operation ABORT
    2. BACKUP_ARTIFACT_STATUS_CHANGED(new_status=invalid,
                                       reason=replay_in_session)
    3. Sonraki cadence cycle'a kadar bekle veya replay tamamlanmasını bekle
    
Otomatik retry yasak; sonraki cadence'a bırakılır (replay tamamlanmazsa
sürekli retry storage pressure yaratır).
```

### Forbidden

- Replay in_session sırasında M0 snapshot zorlama
- Sealed_checkpoint olmadan snapshot
- snapshot_requires_replay_idle_or_sealed = false

---

## 11. RestoreManifest Validation Numerics

### Constitutional validation requirements

```
backup.restore_manifest.hash_validation_required:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden

backup.restore_manifest.signature_validation_required:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden

backup.restore_manifest.numerics_refs_required:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden

backup.restore_manifest.loose_files_restore_forbidden:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "L: Restore loads a RestoreManifest, not loose backup files."
```

### Bounded validation parameters

```
backup.restore_manifest.validation_timeout_ms:
    bidirectional_sensitive
    (kısa = restore başarısız; uzun = strict mode'da takılma)
    allowed_range: bounded

backup.restore_manifest.max_artifact_count:
    bidirectional_sensitive
    (çok az = composition incomplete; çok çok = resource pressure)

backup.restore_manifest.max_m1_segments_per_manifest:
    bidirectional_sensitive

backup.restore_manifest.max_hash_verification_failures:
    value: 0
    allowed_range: {0}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Bir hash mismatch = manifest invalid; tolerance = 0."
```

### NumericEntry örneği

```
NumericEntry:
    key: backup.restore_manifest.hash_validation_required
    value: true
    unit: bool
    allowed_range: {true}
    directionality: neutral
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    requires_human_approval: n/a (forbidden zone)
    dependencies: []
    numeric_risk_family: safety_critical
    spec_family: backup_strategy
    owning_spec_ref: "BACKUP_STRATEGY_NUMERICS.md §11"
```

### Forbidden

- Hash/signature/numerics_refs validation bypass
- Loose file restore (artifact bundle olmadan)
- `max_hash_verification_failures > 0`

---

## 12. Same Identity Restore Thresholds

### Constitutional immutable

```
backup.restore.max_missing_m1_events_for_full_identity:
    value: 0
    allowed_range: {0}
    directionality: neutral
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Full identity restore için M1 chain'de gap kabul edilmez."

backup.restore.max_m1_gap_ms_for_full_identity:
    value: 0
    allowed_range: {0}
    directionality: neutral
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
```

### Restore precondition checklist

```
Full same-identity restore başlamadan ÖNCE TÜM koşullar:

    1. WAL lag = 0 (replication tamamlanmış; resolve edilmedi ise abort)
    2. M1 chain complete (gap = 0)
    3. M0 snapshot valid (consistency check passed)
    4. RestoreManifest hash + signature + numerics_refs valid
    5. Constitutional anchors compatible (constitution_hash + memory_contract_hash
       + replay_protocol_hash + adapter_manifest_hashes match veya
       constitutional_shift_applied event ile köprülenmiş)

Bir koşul tatmin edilmezse:
    same_identity restore ABORT
    → restore_with_missing_history (§13) veya
    → restore aborted, fork_birth (§14) tercih veya clean_birth with foreign audit
    → migration_birth (§15) sadece eş zamanlı bir constitutional/genesis-affecting
      shift de uygulanıyorsa; M1 gap tek başına migration_birth tetikleyemez.
```

### Cross-artifact dependency

```
Constitutional anchors validation:
    constitution_hash      → BOOTSTRAP_GENOME compatibility
    memory_contract_hash   → B §3 subject_class taksonomisi
    replay_protocol_hash   → K mekanizması
    adapter_manifest_hashes → I §14 ADAPTER_MANIFEST_STATUS_CHANGED chain
    numerics_artifact_refs → M restore numerics versioning (§19)
```

### Forbidden

- M1 gap > 0 ile full identity claim
- WAL lag unresolved ile same-identity restore başlatma
- Constitutional anchor mismatch silent geçiş

---

## 13. restore_with_missing_history Numerics — restricted mode

> *Bu mode S'nin phase monotonicity invariant'ının (S §16) **iki rollback kanalından biridir** — boot/stabilization/consolidated phase'lerden restricted phase'e geri dönüş bu mode'da otomatik. Bkz. [`BOOTSTRAP_GENOME_NUMERICS.md`](./BOOTSTRAP_GENOME_NUMERICS.md) (S) §16: "Normal operasyonda phase rollback forbidden; sadece restore_with_missing_history veya migration_birth ile mümkün."*

### Üst sınır var

```
backup.restore.missing_history_max_gap_ms:
    unit: ms
    directionality: lower_is_stricter
    change_class_if_increased: safety_weakening
    change_class_if_decreased: safety_tightening
    allowed_range: {min: 60_000, max: 86_400_000}    # 1 dk - 24 saat
    rationale: "Bu üst sınır geçilirse restore_with_missing_history bile
                yasak. Çok büyük gap = restore değil, yeni kimlik (§14, §15)."

backup.restore.missing_history_max_event_gap_count:
    lower_is_stricter
    allowed_range: bounded
```

### Üst sınır aşılırsa — allowed paths

```
missing_history gap > backup.restore.missing_history_max_gap_ms:
    restore_with_missing_history FORBIDDEN
    same_identity restore FORBIDDEN
    
    Allowed paths:
        - fork_birth from available M0 snapshot
          (source identity preserved as parent provenance)
        - clean_birth with foreign audit import (B §3 / L §10 disipliniyle)
    
    NOT allowed:
        - migration_birth (sadece constitutional/genesis-affecting shift için;
          M1 gap migration sebebi değildir)
```

### Restricted mode duration

```
backup.restore.restricted_mode_min_duration_ms:
    higher_is_stricter
    allowed_range: {min: > 0 ...}
    rationale: "restore_with_missing_history sonrası restricted mode en az
                bu süre kalmalı; otomatik full restore'a yükselemez."

backup.restore.execution_reenable_delay_ms:
    higher_is_stricter
    rationale: "Adapter execution restricted mode bittikten sonra bile
                bekleme süresi ile reactivate olur."

backup.restore.human_ack_timeout_ms:
    bidirectional_sensitive
    (kısa = otomatik reject; uzun = strict mode'da takılma)
```

### Restricted mode invariants (constitutional)

```
restore_with_missing_history sırasında:

backup.restore.missing_history.execution_adapter_activation_forbidden:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden

backup.restore.missing_history.foreign_m2_merge_forbidden:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden

backup.restore.missing_history.numerics_artifact_activation_forbidden:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden

backup.restore.missing_history.replay_write_channels_disabled:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden

backup.restore.missing_history.full_identity_claim_forbidden:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
```

### Forbidden

- restore_with_missing_history → full identity claim
- Üst sınır aşılan gap için restore_with_missing_history zorla
- restricted_mode_min_duration_ms = 0
- Otomatik execution adapter reactivation

---

## 14. Fork Restore Numerics

### Constitutional invariants

```
backup.fork.new_instance_id_required:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden

backup.fork.foreign_instance_origin_provenance_required:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden

backup.fork.constitutional_anchors_must_match_origin:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Fork origin constitutional anchor'larıyla bağlanmak zorunda;
                farklı anchor'la fork değil, migration olur."

backup.fork.identity_continuity_claim_forbidden:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Fork = identity bölünmesi; aynı kimlik iddiası yasak.
                Origin ve fork iki ayrı varlık (paralel)."
```

### Fork-spesifik bounded numerics

```
backup.fork.max_concurrent_forks_per_source:
    lower_is_stricter
    rationale: "Aynı source'dan çok fazla fork = identity fragmentation."

backup.fork.source_lock_during_fork_required:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Fork sırasında source instance write'lar lock'lanır
                (atomic snapshot for fork)."
```

### Forbidden

- Fork same-identity claim
- foreign_instance_origin provenance olmadan fork
- Constitutional anchor mismatch ile fork (= migration)

---

## 15. Migration Restore Numerics

> *Migration_birth S'nin phase monotonicity'sinin **ikinci rollback kanalı** — constitutional shift sonrası boot_phase'e yeni cycle olarak başlama (S §16). Genesis-affecting shift yaşayan Sentinel'e numeric update olarak uygulanamaz; migration_birth zorunlu. Bkz. [`BOOTSTRAP_GENOME_NUMERICS.md`](./BOOTSTRAP_GENOME_NUMERICS.md) (S) §23-24.*

### Constitutional invariants

```
backup.migration.constitutional_shift_event_ref_required:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Migration ancak constitutional/genesis-affecting shift
                varsa kabul edilir. shift_event_ref zorunlu."

backup.migration.numerics_compatibility_validation_required:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Source ve target numerics compatibility class kontrol
                edilmek zorunda (M §17)."

backup.migration.identity_continuity_claim_constitutional_only:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Migration'da kimlik 'constitutional update sonrası kim'liktir;
                aynı operational identity değildir."
```

### Bounded migration numerics

```
backup.migration.shift_event_age_max_ms:
    lower_is_stricter
    rationale: "Migration eski şift'lerden olamaz; recent shift_event_ref."

backup.migration.max_numerics_compatibility_class_mismatches:
    lower_is_stricter
    allowed_range: bounded
    rationale: "Belirli sayıda compatibility mismatch kabul edilir
                (versioning); fazlası migration yerine fresh setup."
```

### Migration vs fork ayrımı

```
Fork:
    Same constitutional anchors;
    new instance_id;
    parallel existence.

Migration:
    Constitutional shift applied;
    identity preserved across shift;
    not parallel — old instance retires or becomes archived.

M1 gap büyük diye migration YOK.
Migration ancak anayasal/genesis-affecting uyumsuzluk varsa.
```

### Forbidden

- Constitutional shift olmadan migration_birth
- Numerics compatibility validation atlama
- Eski shift_event_ref ile migration
- Operational identity continuity claim (constitutional only)

---

## 16. M2/M3 Backup Retention

```
backup.retention_ms.M2Snapshot:
    unit: ms
    directionality: bidirectional_sensitive
    change_class_if_increased: safety_weakening
    change_class_if_decreased: safety_weakening
        (kısa retention = bilgi kaybı; uzun retention = storage pressure;
         ikisi de boundary'ye dokunur — directionality bidirectional_sensitive
         M canonical metadata schema ile uyumlu)
    allowed_range: bounded medium
    rationale: "Knowledge retention; identity etkisi yok ama operational önemli."

backup.retention_ms.M3Snapshot:
    unit: ms
    directionality: lower_is_stricter
    change_class_if_increased: operational_no_behavior_change
    change_class_if_decreased: operational_no_behavior_change
    allowed_range: short / optional
    rationale: "M3 = translator konuşma kabuğu; kimlik etkisi yok."
```

### M2 retention policy enum

```
backup.retention.policy.M2:
    unit: enum
    allowed_range: {time_based, count_based, hybrid, lifetime_for_critical}
    directionality: bidirectional_sensitive
    change_class_if_increased: bidirectional_sensitive
        (each policy has different attack/loss vectors)
```

### Forbidden

- M2 retention infinite (lifetime) genelde (sadece critical subset için)
- M3 retention lifetime (gereksiz storage waste)
- M2 retention shrink without human approval (§19 forgetting attack)

---

## 17. Foreign M2 Merge Caps

### Forbidden subject class set

```
NumericEntry: backup.foreign_merge.forbidden_subject_class_set
    unit: enum_set
    value: [narrative_claim,
            causal_explanation,
            decision_rationale,
            episodic,
            operator_decision_record,
            deontic_kill_switch_action_record,
            numerics_artifact_reference]
    allowed_range: subset_of_subject_class_enum (must include core forbidden set)
    directionality: higher_is_stricter
    change_class_if_increased: safety_tightening
        (forbidden set genişler = daha çok class yasak = sıkılaşma)
    change_class_if_decreased: safety_weakening
        (forbidden set daralır = daha çok class import izinli = gevşeme)
    rationale: "Bu enum_set'in yönü forbidden semantiği ile uyumlu.
                Q §15 LLM scope (whitelist) lower_is_stricter'dan ters."
```

### enum_set convention — semantik subject'e bağlı

```
For forbidden_subject_class_set (blacklist):
    expansion = safety_tightening
    contraction = safety_weakening
    directionality: higher_is_stricter

For allowed_subject_class_set (whitelist):
    expansion = safety_weakening
    contraction = safety_tightening
    directionality: lower_is_stricter
```

M §8 enum_set convention'ın R'deki özel uygulaması. Semantik (whitelist
mı blacklist mı) yönü belirler; semantik artifact içinde explicit.

### Per-restore caps

```
backup.foreign_merge.max_records_per_restore:
    lower_is_stricter

backup.foreign_merge.max_subject_classes_per_restore:
    lower_is_stricter

backup.foreign_merge.required_gate_ref:
    value: memory_write_gate
    allowed_range: {memory_write_gate}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Foreign merge Memory Write Gate'i bypass edemez;
                P verification matrix uygulanır."

backup.foreign_merge.foreign_instance_origin_provenance_required:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Foreign provenance permanent (L §10);
                native provenance'a dönüşemez."
```

### P bridge

```
Foreign M2 merge süreci P verification matrix'ten geçer:
    Her foreign record P §9 evidence axis matrix'ine tabi
    Foreign record provenance native sayılmaz (B §10 / L §10)
    Foreign instance_id audit trail'de korunur
```

### Forbidden

- forbidden_set'ten subject_class import
- foreign_instance_origin provenance olmadan foreign merge
- Memory Write Gate bypass
- Native provenance'a dönüşüm

---

## 18. Replay-derived Trace Provenance Summary Numerics — O bridge

L §17 replay-derived trace provenance backup'ta korunur. R numeric tarafı.

```
backup.replay_trace.provenance_preservation_required:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Replay-derived trace'ler backup'ta observation-derived'tan
                ayrılır; provenance kaybı = audit kaybı."

backup.replay_trace.summary_min_fields:
    unit: enum_set
    value: [observation_derived_trace_count,
            replay_derived_trace_count,
            sleep_synapse_update_count,
            attention_habituation_update_count,
            ingress_calibration_update_count,
            memory_verification_evidence_count,
            outcome_alignment_analysis_count]
    allowed_range: subset_must_include_all_required
    directionality: lower_is_stricter
    change_class_if_decreased: safety_weakening
    rationale: "RestoreManifest.replay_trace_summary minimum field set."
```

### O bridge — restore budget continuity

```
Restore sonrası replay budget RESET YOK (O §7 canonical):
    backup.replay_budget_continuity_required:
        value: true
        allowed_range: {true}
        change_class_if_increased: forbidden
        change_class_if_decreased: forbidden
        rationale: "max_sessions_per_cycle, max_sessions_per_24h_window
                    sayaçları M1 segment'inden devralınır. O canonical."
```

### Forbidden

- Replay-derived trace provenance kaybı backup'ta
- Restore sonrası replay budget sıfırlama
- Trace summary minimum field set'inden çıkarma

---

## 19. Forgetting Attack Defense Numerics — Q + L bridge

### Composite detection signals

```
backup.forgetting_attack.max_expire_requests_per_window:
    lower_is_stricter

backup.forgetting_attack.max_delete_requests_per_subject_class_window:
    lower_is_stricter

backup.forgetting_attack.m1_gap_detection_window_ms:
    higher_is_stricter
    rationale: "Uzun pencere = daha kapsamlı detection."

backup.forgetting_attack.restore_gap_alert_threshold:
    lower_is_stricter
    rationale: "Küçük gap bile alarm; sessiz tarih silinmesi yok."

backup.forgetting_attack.mass_retention_change_threshold:
    lower_is_stricter
    rationale: "Retention shrink mass forget vektörü."
```

### Retention shrink human approval invariant

```
backup.forgetting_attack.retention_change_human_approval_required:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Backup retention shrink her zaman human approval gerek;
                otomatik shrink yasak."
```

### M1 retention immutable (L + Q bridge)

```
backup.forgetting_attack.m1_retention_shrink_forbidden:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "M1 = tarih kanıtı; retention sadece sıkılaşabilir
                (lifetime'a yükselebilir), zayıflayamaz.
                Q permanence monotonic invariant ile uyumlu."
```

### Composite forgetting_attack_signal

```
forgetting_attack_signal =
    mass_delete_burst                         (M2 forget request spike)
    + retention_shrink_request                (backup retention shrink)
    + M1 gap detected                         (Q chain integrity check)
    + permanent log access pattern anomaly    (Q §15 M1_READ_AUDIT_RECORDED)
    + replay budget pre-restore spike         (O bridge)
    + numerics artifact unexpected rollback   (M §15 rollback path)

→ FORGETTING_ATTACK_SUSPECTED canonical event (F §19, ledger_meta)
    permanence: permanent_with_snapshot + human_alert (CRITICAL)
```

### Kural

```
M2 forget olabilir (TTL, supersede, policy-based).
M1 forget edilemez (Q chain_gap_tolerance=0 + R M1Segment retention=lifetime).
Backup retention shrink M1 history'yi silemez.
```

### Forbidden

- M1 retention shrink
- Mass forget silent (audit + alert zorunlu)
- Retention change otomatik (human approval bypass)

---

## 20. Backup Artifact Retention

```
backup.retention.M1Segment:           value: lifetime (§8 immutable)
backup.retention.RestoreManifest:     value: lifetime (immutable)
backup.retention.M0Snapshot:          rolling_with_last_known_good (§21)
backup.retention.M2Snapshot:          policy_based (§16)
backup.retention.M3Snapshot:          optional / short (§16)
```

### RestoreManifest lifetime

```
backup.retention.RestoreManifest:
    value: lifetime
    allowed_range: {lifetime}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "RestoreManifest identity composition evidence;
                M1 ile birlikte lifetime retain edilir."
```

### Dependency simplification

```
backup.retention.M1Segment = lifetime AND
backup.retention.RestoreManifest = lifetime
    → No comparison needed; both immutable.

Bu, manifest-M1 dependency'sini en güvenli forma indirir.
RestoreManifest finite retention ile M1Segment finite retention
karşılaştırma zorunluluğu çıkmaz.
```

### M0 rolling retention

```
backup.retention.M0Snapshot.rolling_window_count:
    bidirectional_sensitive
    (az = recovery point dar; çok = storage pressure)

backup.retention.M0Snapshot.rolling_retention_ms:
    bidirectional_sensitive
```

### Forbidden

- M1Segment retention finite
- RestoreManifest retention finite (manifest M1'leri reference eder)
- M0 hiç last-known-good yok (§21)

---

## 21. Last-known-good Snapshot Rules

```
backup.m0.last_known_good_retention:
    value: permanent
    allowed_range: {permanent}
    directionality: neutral
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "En az bir M0 snapshot her zaman 'last known good' olarak
                permanent retain edilir. Rolling retention rotate edebilir
                ama last_known_good fiziksel olarak silinemez."
```

### Last-known-good seçim disiplini

```
last_known_good = en son validation passed olan M0 snapshot.

Promotion criteria:
    - snapshot_consistency_required check passed
    - hash recompute match
    - genome_attestation passed
    - replay_session_status idle veya sealed_checkpoint anında alınmış

Demotion criteria:
    - Yeni snapshot last_known_good olur
    - Eski last_known_good cold tier'a geçer (lossless)
    - Ama silinmez; permanent retain

Aynı anda en az bir last_known_good zorunlu.
İlk M0 snapshot otomatik last_known_good.
```

### Forbidden

- last_known_good = none durumu
- last_known_good rotate ile silinmesi
- Validation failed snapshot'ın last_known_good promote edilmesi

---

## 22. Missing-Numerics Failsafe

M §11 fail-safe strict mode R'ye uygulanır.

### Strict mode behavior

```
Missing backup_strategy numerics artifact veya invalid load:
    → All restore operations BLOCKED
       (no same-identity / no restore_with_missing_history /
        no fork / no migration; sadece audit read OK)
    → New backup operations CONTINUE (M1 continuous + M0 last cadence)
       (silent drop yasak; M1 chain korunur)
    → Foreign M2 merge BLOCKED (P bridge)
    → Retention changes BLOCKED (human approval gerekir; numerics olmadan
       approval workflow eksik)
    → NUMERICS_FAILSAFE_ACTIVATED event tetiklenir
    → Critical human alert
    → Manual intervention until valid numerics artifact loaded
```

### Audit-safe R mode

```
Audit-safe backup:
    ✅ M1 continuous replication (kritik; tarih kanıtı korunur)
    ✅ M0 snapshot at last cadence (sealed timing)
    ✅ Backup artifact integrity verification (read-only)
    ✅ Audit query on backup state
    ❌ Restore operations (any kind)
    ❌ Foreign M2 merge
    ❌ Retention changes
    ❌ Tier transitions (lossless transition needs numerics)
```

Sistem "R yoksa" durumunda **daha serbest değil, daha kısıtlı** çalışır.

### Forbidden

- Missing numerics → restore başlatma
- Missing numerics → M1 backup durması (M1 continuous her zaman; constitutional)
- Missing numerics → otomatik retention change

---

## 23. Dependency Declarations

### Internal (R içinde)

```
backup.rpo.mode.M1 = continuous_replication (immutable)
backup.m1.replication_mode = continuous (immutable)
backup.m1.chain_gap_tolerance_events = 0 (immutable)
backup.restore.max_missing_m1_events_for_full_identity = 0 (immutable)
backup.restore.max_m1_gap_ms_for_full_identity = 0 (immutable)
backup.retention.M1Segment = lifetime (immutable)
backup.retention.RestoreManifest = lifetime (immutable)
backup.m0.last_known_good_retention = permanent (immutable)

Same identity restore precondition (composite):
    WAL lag = 0
    AND M1 chain gap = 0
    AND M0 snapshot valid
    AND RestoreManifest valid
    AND constitutional anchors compatible
```

### Cross-artifact

```
R → Q bridge:
    backup.retention.M1Segment = lifetime
        ↔ Q §12 permanence monotonic invariant
    backup.m1.tier_transition_lossless_required = true
        ↔ Q §13 storage tier lossless invariant
    backup.m1.chain_integrity_verification_required = true
        ↔ Q §11 verify_on_read_required

R → O bridge:
    backup.replay_budget_continuity_required = true
        ↔ O §7 restore_budget_continuity (M1 segment'inden devralma)
    backup.restore.missing_history.replay_write_channels_disabled
        ↔ O strict mode replay disable

R → P bridge:
    backup.foreign_merge.required_gate_ref = memory_write_gate
        ↔ P §18 human_signature_requirement + matrix verification
    backup.foreign_merge.forbidden_subject_class_set
        ↔ P §16 self_deception_risk numerics + foreign import discipline

R → B bridge:
    foreign_instance_origin provenance permanent (B §10 / L §10)
        ↔ R §17 foreign_instance_origin_provenance_required = true

R → M bridge:
    numerics_artifact_refs validation
        ↔ M §19 restore numerics versioning
    rollback only to previous verified
        ↔ R §15 migration compatibility validation
```

### Atomic update rule (M §12)

Bağımlı numerics atomic artifact içinde değişir. Tek key değişikliği
bağımlı key'leri eski bırakırsa artifact REJECT.

### Forbidden

- Dependency declarationsız R numeric ekleme
- Partial update
- Constitutional immutable key'i tek yönde forbidden, diğer yönde free
  (her iki yön de forbidden olmak zorunda)

---

## 24. Audit Events and M2 Reference

R **yeni canonical event tanımlamaz**. L + F + M canonical event'lerini reuse eder.

### Reused events

```
BACKUP_ARTIFACT_STATUS_CHANGED              (L + F §19)
    new_status: created | valid | invalid | replication_degraded |
                chain_break | tier_transitioned | archived
    reason:     wal_lag_exceeded | chain_gap_detected | m0_consistency_failed |
                replay_in_session | hash_mismatch | tier_transition_performed |
                retention_change_pending

RESTORE_OPERATION_STATUS_CHANGED            (L + F §19)
    new_status: initiated | validating | preconditions_failed |
                same_identity_success | with_missing_history_success |
                fork_success | migration_success | failed | aborted
    reason:     m1_chain_gap | wal_lag_unresolved | manifest_invalid |
                rto_timeout | missing_history_gap_exceeded |
                constitutional_anchor_mismatch | numerics_compatibility_failed

M2_FOREIGN_MERGE_STATUS_CHANGED             (L)
    new_status: proposed | gate_pending | accepted | rejected
    reason:     forbidden_subject_class | provenance_missing |
                gate_verification_failed | cap_exceeded

M1_HISTORY_LOST_AT_RESTORE                  (L + F §19)
    permanence: permanent_with_snapshot + human_alert (CRITICAL)

FORK_FROM_INSTANCE                          (L + F §19)
MIGRATION_FROM_INSTANCE                     (L + F §19)
FORGETTING_ATTACK_SUSPECTED                 (L + F §19, ledger_meta)
    permanence: permanent_with_snapshot + human_alert (CRITICAL)

NUMERICS_ARTIFACT_STATUS_CHANGED            (M §6) — R artifact lifecycle
NUMERICS_VERSION_MISMATCH_DETECTED          (F §19, ledger_meta)
NUMERICS_FAILSAFE_ACTIVATED                 (F §19, ledger_meta)
```

### F event type discipline

R yeni backup/restore violation tipleri için **yeni event tipi üretmez**;
canonical event + reason field discipline. F'deki "tek event + reason"
disiplinin R yansıması.

### M2 reference

```
numerics_artifact_reference (MEMORY_CONTRACT §3 subject_class)
    spec_family: backup_strategy
    artifact_version: v0.1
    status: active | deprecated | rollback_pending
    signed_hash: <external artifact hash>
    last_status_change_ref: <NUMERICS_ARTIFACT_STATUS_CHANGED event_id>
```

---

## 25. Cross-document Anchors

```
| Belge                                  | Bağlantı                                          |
|----------------------------------------|---------------------------------------------------|
| NUMERICS_GOVERNANCE.md (M)             | tüm meta-kurallar; restore numerics versioning   |
| BACKUP_STRATEGY.md (L)                 | mekanizma; R onun numerics artifact'i            |
| OBSERVER_LEDGER_NUMERICS.md (Q)        | M1Segment lifetime + tier transition + hash chain |
| REPLAY_PROTOCOL_NUMERICS.md (O)        | restore_with_missing_history replay disable +    |
|                                        | restore budget continuity                         |
| MEMORY_WRITE_GATE_NUMERICS.md (P)      | foreign M2 merge gate + self_deception bridge    |
| MEMORY_CONTRACT.md (B)                 | subject_class taksonomisi + provenance + M0-M3   |
| OBSERVER_LEDGER_SCHEMA.md (F)          | canonical event reuse + reason field             |
| BOOTSTRAP_GENOME.md (D)                | genome_attestation snapshot validation           |
| CONSTITUTION.md (A)                    | Madde 7 (hafıza ayrılığı) + Madde 1 (identity)   |
```

---

## 26. Violation Tests

R artifact'ı validation sırasında **REJECT** edilmesi gereken durumlar:

1. **Çıplak sayı.** NumericEntry metadata olmadan R numerics içeren artifact.
2. **M1 RPO mode = periodic / batch / scheduled.** §5 ihlali (continuous_replication immutable).
3. **`chain_gap_tolerance_events > 0`.** §7 ihlali (constitutional).
4. **`max_missing_m1_events_for_full_identity > 0`.** §12 ihlali (constitutional).
5. **`max_m1_gap_ms_for_full_identity > 0`.** §12 ihlali (constitutional).
6. **M1Segment retention finite.** §8 ihlali (lifetime immutable).
7. **RestoreManifest retention finite.** §20 ihlali.
8. **tier_transition_lossless_required = false.** §8 ihlali (Q bridge).
9. **`snapshot_consistency_required = false`.** §9 ihlali.
10. **`partial_assembly_state_unsealed_max_count > 0`.** §9 ihlali.
11. **`snapshot_requires_replay_idle_or_sealed = false`.** §10 ihlali.
12. **Replay in_session sırasında M0 snapshot kabul edilmiş.** §10 ihlali.
13. **RestoreManifest hash/signature/numerics_refs validation kapalı.** §11 ihlali.
14. **Loose file restore yapılmış.** §11 ihlali.
15. **`max_hash_verification_failures > 0`.** §11 ihlali.
16. **Constitutional anchor mismatch ile same-identity restore.** §12 ihlali.
17. **WAL lag unresolved ile same-identity restore başlatılmış.** §12 ihlali.
18. **restore_with_missing_history full identity claim.** §13 ihlali.
19. **restore_with_missing_history restricted_mode olmadan açılmış.** §13 ihlali.
20. **missing_history_max_gap_ms aşılan gap için restore_with_missing_history zorla.** §13 ihlali (fork/clean tercih edilmeli).
21. **M1 gap büyük diye migration_birth.** §15 ihlali (migration sadece constitutional shift için).
22. **Fork same-identity claim.** §14 ihlali.
23. **foreign_instance_origin provenance olmadan fork.** §14 ihlali.
24. **Migration constitutional_shift_event_ref olmadan.** §15 ihlali.
25. **Migration numerics compatibility validation atlanmış.** §15 ihlali.
26. **Foreign M2 merge forbidden_set'ten subject_class kabul edilmiş.** §17 ihlali.
27. **Foreign merge Memory Write Gate bypass.** §17 ihlali (P bridge).
28. **enum_set forbidden_subject_class_set yönü yanlış** (genişleme = weakening; yön: higher_is_stricter olmalı). §17 ihlali.
29. **Restore sonrası replay budget sıfırlama.** §18 ihlali (O bridge).
30. **Replay-derived trace provenance backup'ta korunmamış.** §18 ihlali.
31. **M1 retention shrink.** §19 ihlali (constitutional).
32. **Backup retention shrink human approval bypass.** §19 ihlali.
33. **Last-known-good = none.** §21 ihlali.
34. **Last-known-good rotate ile silinmiş.** §21 ihlali.
35. **Missing R numerics → fail-open (normal restore devam).** §22 ihlali.
36. **Missing R numerics → M1 continuous backup durmuş.** §22 ihlali (M1 continuous her zaman; constitutional).
37. **Constitutional immutable key tek yönde forbidden, diğer yönde free.** §4, §23 ihlali (her iki yön forbidden olmak zorunda).
38. **LLM tarafından üretilen veya değiştirilen R numeric.** Madde 6 ihlali.
39. **Dependency declarationsız R numeric.** §23 ihlali.

**Artifact-level violations** (1-39, validation aşaması):
`MEMORY_RECORD_STATUS_CHANGED(target=artifact, new_status=rejected, reason=numerics_validation_failed)`.

**Runtime violations** (artifact valid ama R caps'leri aştı):
Canonical `BACKUP_ARTIFACT_STATUS_CHANGED` / `RESTORE_OPERATION_STATUS_CHANGED` /
`M2_FOREIGN_MERGE_STATUS_CHANGED` + reason field; new event tipi yok.

---

## 27. Open Questions

R kapanırken cevaplanmamış bırakılan sorular:

- **Exact production retention values** (M2 retention windows, fork concurrency limits) → signed artifact + implementation
- **Constitutional shift event taxonomy** (hangi spec değişiklikleri migration tetikler) → BOOTSTRAP_GENOME / CONSTITUTION spec revision
- **Tier transition cadence ve cost trade-off'ları** → Q §13 ile implementation koordinasyonu
- **Multi-signature requirement** for high-impact numerics changes → M §13 open question'ı buraya bağlı
- **Cross-instance trust verification protocol** → fork_birth + migration_birth için ayrı spec olabilir
- **Restore validation timeout ile RTO ilişkisi** → benchmark + implementation
- **Forgetting attack threshold tuning** — false positive rate vs detection sensitivity → operational

Bu sorular cevaplanmadan implementation aşamasına geçilmez.

---

## Çekirdek özet — 17 karar + 39 violation tests

### 17 karar

1. R runtime config değildir; signed artifact + M2 reference.
2. M1 RPO mode = continuous_replication (constitutional immutable).
3. WAL lag operational (bounded); chain gap constitutional (0 immutable).
4. M1Segment retention = lifetime (constitutional); tier transition lossless required.
5. M0 snapshot point-in-time consistent (constitutional); partial unsealed assembly = 0.
6. M0 snapshot during replay sealed_checkpoint veya idle gerek (constitutional).
7. RestoreManifest hash + signature + numerics_refs validation constitutional.
8. Loose file restore forbidden (constitutional).
9. Same-identity restore precondition: WAL=0 + M1 gap=0 + M0 valid + manifest valid + anchors compatible.
10. restore_with_missing_history üst sınır var; aşılırsa fork/clean tercih (migration sadece constitutional shift için).
11. restore_with_missing_history restricted mode invariants (execution/foreign_merge/numerics_activation/replay_write disabled).
12. Fork constitutional invariants: new_instance_id + foreign_instance_origin + anchors match origin + identity_continuity_claim forbidden.
13. Migration constitutional invariants: constitutional_shift_event_ref + numerics_compatibility_validation + identity_continuity_constitutional_only.
14. Foreign M2 merge: forbidden_subject_class_set (blacklist) higher_is_stricter; required_gate_ref = memory_write_gate; provenance permanent.
15. Replay budget continuity required (O bridge); replay-derived trace provenance preserved.
16. M1 retention shrink forbidden; retention change human approval required; FORGETTING_ATTACK_SUSPECTED composite signal.
17. Missing R numerics → strict mode (restore blocked; M1 continuous backup CONTINUES; foreign merge/retention/tier transition blocked).

### 39 violation tests

§26'da listelendi.

### Constitutional immutable key pattern

```
key: <name>
    value: <constant>
    allowed_range: {<constant>}
    directionality: neutral
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    requires_human_approval: n/a (forbidden zone)

`change_class: forbidden` tek satır YANLIŞ; her iki yön ayrı yazılır.
```

### enum_set convention — semantik subject'e bağlı

```
forbidden_set (blacklist):     higher_is_stricter
                                expansion = safety_tightening
allowed_set (whitelist):       lower_is_stricter
                                expansion = safety_weakening
```

### Damıtma — son cümleler

> **R = kimliği kaybetmeden geri dönebilme hakkının sayısal sözleşmesidir.**
>
> **Backup hızlı olsun diye kimlik gevşetilemez. Restore kolay olsun diye tarih kanıtı atlanamaz.**
>
> **Replication lag operational olabilir; M1 chain gap constitutional ihlaldir.**
>
> **M1 tarih kanıtıdır. Fiziksel tier değişebilir; tarih garantisi değişemez.**
>
> **M0 yarım state ile snapshot edilemez; replay in_session sırasında M0 snapshot abort.**
>
> **Loose file restore yok; RestoreManifest atomic composition zorunlu.**
>
> **Fork = ayrı kimlik; migration = constitutional update sonrası kimlik; restore_with_missing_history = degraded kimlik. Üçü farklı; biri diğerine dönüşemez.**
>
> **Foreign M2 merge Memory Write Gate'i bypass edemez. Foreign provenance native provenance'a dönüşemez.**
>
> **M2 forget olabilir; M1 forget edilemez. Backup retention M1 history'yi silemez.**
>
> **Missing R numerics: restore blocked, M1 backup CONTINUES — sistem daha serbest değil, daha kısıtlı çalışır.**
>
> **N dış dünyanın hakkını sınırlar.**
> **O kendi geçmişine girme hakkını sınırlar.**
> **P hafızaya emin olma hakkını sınırlar.**
> **Q kendine bakma hakkını sınırlar.**
> **R kimliğini koruyarak geri dönme hakkını sınırlar.**
