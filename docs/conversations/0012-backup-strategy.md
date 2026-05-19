# 0012 — Backup Strategy

> Bu dosya `BACKUP_STRATEGY.md` (v0.1) ortaya çıkmadan önce yapılan üçlü
> tasarım konuşmasının (Halit + Claude + ChatGPT) sıkıştırılmış özetidir. L
> turunun kararlarının soyağacı.
>
> A-K: 0001-0011

---

## Tarih
2026-05-18 (K → L geçişi)

## Bağlam

A-K kapanmış. L **conceptual phase'in son büyük kimlik belgesi**. MEMORY_CONTRACT §13'te backup priority kavramsal, §14'te cross-restore identity ve forgetting attack açık sorulardı. L bu boşlukları kapattı.

L için ana zorluk: backup "dosya kopyalama"dan "kimlik sürekliliği sözleşmesi"ne çevirmek. Restore senaryolarının her birinde "aynı varlık mı, kopya mı, kırık kimlik mi?" sorusuna net cevap.

---

## Başlangıç pozisyonları

### Claude (açılış)
10 ana soru ve restore matrix:
- M0+M1 = aynı varlık
- M0 var M1 yok = audit-broken
- M1 var M0 yok = yeni doğum
- M2 = bilgi, kimlik değil
- M3 = konuşma kabuğu

3 ana çapa:
1. M0 restore + M1 kayıp yasak mı, izinli mi?
2. BackupArtifact monolithic mi modular mı?
3. Replay-derived vs observation-derived M0 traces ayrımı

### ChatGPT (5 ana pozisyon + 4 kritik soru)

ChatGPT'nin pozisyonları:
1. Same identity sadece M0+M1 ile — kesin
2. `restore_with_missing_history` ayrı mode olsun, degraded
3. M2 foreign merge knowledge transfer (kimlik değil)
4. Foreign whitelist (bootstrap_ref, structured_fact, procedural, signed_admin) / blacklist (narrative, causal, decision_rationale, episodic)
5. Memory Write Gate foreign merge için zorunlu

4 kritik soru:
1. `restore_with_missing_history` ayrı mı yasak mı?
2. BackupArtifact tek mi modular mı?
3. Replay-derived provenance summary vs per-trace?
4. Foreign M2 merge whitelist + gate?

### Claude (4 sorunun cevabı + ek)

1. **Ayrı mode + degraded:** `birth_mode: restore_with_missing_history`, `identity_continuity: degraded`, `audit_status: broken`, `operational_mode: restricted`, human_ack required
2. **Modular + RestoreManifest:** M0/M1/M2 ayrı artifact'ler, RestoreManifest atomic composition
3. **Hem summary hem per-trace:** Summary mandatory, per-trace recommended
4. **Whitelist/blacklist + Memory Write Gate zorunlu** + iki kat validation (foreign + original subject_class matrix)

Yeni nüans:
- **`foreign_instance_origin` provenance kalıcı taşınır** — imported record native episodic'e dönüşemez
- **fork_birth detayı** (BOOTSTRAP §23 ile bağlantı)

### ChatGPT son tur (final kararlar + canonical events)

ChatGPT 4 cevabı kabul + ek sertleştirmeler:
- **M1 backup continuous, not periodic** (anayasal ilke)
- **M0 snapshot point-in-time consistent** (freeze_point veya copy_on_write)
- **Canonical events:** BACKUP_ARTIFACT_STATUS_CHANGED, RESTORE_OPERATION_STATUS_CHANGED, M2_FOREIGN_MERGE_STATUS_CHANGED, FORGETTING_ATTACK_SUSPECTED, M1_HISTORY_LOST_AT_RESTORE, FORK_FROM_INSTANCE, MIGRATION_FROM_INSTANCE

"Yaz" hükmü.

---

## Çekirdek kararlar (15)

1. Backup dosya kopyalama değildir; kimlik sürekliliği sözleşmesidir.
2. Same identity restore için M0+M1 birlikte gerekir.
3. M0 olmadan aynı varlık restore edilemez.
4. M1 olmadan full continuity claim yapılamaz (`restore_with_missing_history` degraded path).
5. M2 restore bilgi transferi, kimlik değil.
6. M3 restore konuşma kabuğu, kimlik değil.
7. Modular artifacts (M0Snapshot/M1Segment/M2Snapshot) + RestoreManifest atomic.
8. M0 snapshot point-in-time consistent zorunlu.
9. M1 backup continuous (not periodic).
10. Hash chain + signature tamper evidence zorunlu.
11. Replay-derived trace provenance summary mandatory.
12. Foreign M2 merge whitelist'le sınırlı; narrative/causal/decision_rationale yasak.
13. `foreign_instance_origin` provenance kalıcı taşınır.
14. `restore_with_missing_history` degraded identity, restricted operational mode.
15. Forgetting attack: M2 expire M1'i silemez.

---

## Madde 7 + Madde 1 yansıması — kimlik seviyesi

A-K boyunca Madde 1 her seviyede yansıdı. L'de Madde 7 yansıması daha güçlü:
- M0/M1/M2/M3 ayrımı **backup priority'ye** taşınıyor
- M2 restore identity değil (Madde 7 "hafıza çekirdeğe emir vermez" prensibinin restore yansıması)
- Foreign merge "knowledge transfer ≠ identity continuity" (cross-instance epistemic boundary)

Madde 1 yansıması: birth_mode set'i tip yaratımı değil, **state classification**. clean/restore/fork/migration/restore_with_missing_history — bunlar kategori değil **konfigürasyon**.

---

## Önemli sertleştirmeler

### "Backup is identity continuity, not file copy"
Belgenin omurgası. Restore'un "her dosyayı geri yükle" değil, "aynı varlık mı devam ediyor?" sorusunu cevaplaması zorunlu.

### M1 continuous backup
Periodic backup (saatlik/günlük) M1 için yetersiz. M1 tarih kanıtı, kayıp = identity-critical. İki katman: real-time WAL + periodic segment snapshot.

### `restore_with_missing_history` degraded mode
M0 var M1 yok durumu disaster recovery için izinli ama tam identity claim'i yok. `operational_mode: restricted` — execution adapter activation, foreign merge, policy activation yasak. Human ack zorunlu.

### Modular artifacts + RestoreManifest
Tek monolithic artifact yerine M0/M1/M2 ayrı, RestoreManifest atomic composition. M1 continuous WAL, M0 periodic snapshot, M2 standard DB backup — farklı ritimler.

### "Restore loads a RestoreManifest, not loose backup files"
Hiçbir aktör tek tek dosya restore edemez. Restore atomic, manifest üzerinden, signature/hash verified.

### Foreign M2 merge: knowledge ≠ identity
Whitelist (bootstrap_ref, structured_fact, procedural, adapter_manifest_ref, signed_admin, source_trust) izinli. Blacklist (narrative_claim, causal_explanation, decision_rationale, episodic, operator_decision_record) yasak. Foreign records `foreign_instance_origin` provenance'ı kalıcı taşır.

### "Foreign record keeps foreign provenance forever"
İmported kayıt asla "ben yaşadım" episodic memory'ye dönüşemez. Provenance kalıcı.

### "Forgetting can remove recallability. Forgetting cannot remove audit history."
M2 expire/delete normal lifecycle. M1 coarse log silinemez. `FORGETTING_ATTACK_SUSPECTED` event pattern-based alarm.

### Replay-derived trace provenance backup'ta
K ile öğrendik replay 5 effect channel'dan M0'a dokunur. Restore artifact'inde bu trace'lerin provenance summary'si zorunlu (per-trace recommended). Self-deception forensic audit için kritik.

---

## Yan güncellemeler (commit'in parçası)

- `MEMORY_CONTRACT.md` §13 — BACKUP_STRATEGY cross-ref, `restore_with_missing_history` eklenir
- `MEMORY_CONTRACT.md` §14 — Cross-restore identity ve forgetting attack soruları L tarafından kapatıldı olarak işaretle
- `BOOTSTRAP_GENOME.md` §23 — birth_mode set'ine `restore_with_missing_history` eklenir, BACKUP_STRATEGY cross-ref
- `OBSERVER_LEDGER_SCHEMA.md` §10 permanence_policy — 7 yeni event eklendi (BACKUP/RESTORE/M2_FOREIGN_MERGE_STATUS_CHANGED + M1_HISTORY_LOST_AT_RESTORE + FORK_FROM_INSTANCE + MIGRATION_FROM_INSTANCE + FORGETTING_ATTACK_SUSPECTED)
- `OBSERVER_LEDGER_SCHEMA.md` §19 event catalog — memory family'ye M2_FOREIGN_MERGE_STATUS_CHANGED, ledger_meta family'ye 6 yeni event
- `REPLAY_PROTOCOL.md` §5 — replay-derived trace provenance backup cross-ref
- `README.md` — BACKUP_STRATEGY tamamlanmış listesine

---

## Açık kalanlar (implementation/numerics)

- Kesin retention süreleri ve sıklıklar
- WAL technology choice
- Cross-region replication policy
- RTO/RPO targets
- Foreign merge trust score formülü
- FORGETTING_ATTACK_SUSPECTED threshold sayıları
- Snapshot encryption + key management

Tümü `BACKUP_STRATEGY_NUMERICS.md` ve implementation belgelerine devredildi.

---

## Sıradaki

A-L kapandı. **13 belge.** Conceptual phase + tüm kapsayıcı sözleşmeler tam:
- Anayasa (A-E)
- Evidence surface (F)
- M2 read/write gates (G/H)
- External limb contract (I)
- Compiler mapping (J)
- Replay mechanism (K)
- Identity continuity (L)

Bundan sonra NUMERICS artifact'ları ve implementation belgeleri gelir:
- `BACKUP_STRATEGY_NUMERICS.md`
- `INGRESS_COMPILER_NUMERICS.md`
- `BOOTSTRAP_GENOME_NUMERICS.md`
- `MEMORY_WRITE_GATE_NUMERICS.md`
- `RECALL_PROTOCOL_NUMERICS.md`
- `OBSERVER_LEDGER_NUMERICS.md`
- `REPLAY_PROTOCOL_NUMERICS.md`
- `ADAPTER_TRUST_NUMERICS.md`

Bunlar **sayısal değerleri** verir; conceptual sınırlar zaten kapalı.

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
