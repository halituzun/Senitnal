# 0018 — Backup Strategy Numerics

> Bu dosya `BACKUP_STRATEGY_NUMERICS.md` (v0.1, R turu) ortaya çıkmadan önce
> yapılan üçlü tasarım konuşmasının (Halit + Claude + ChatGPT) sıkıştırılmış
> özetidir. **Beşinci numerics artifact'inin** soyağacı.
>
> A-Q: 0001-0017

---

## Tarih
2026-05-19 (Q → R geçişi, beşinci numerics specifikasyonu)

## Bağlam

N (INGRESS_COMPILER), O (REPLAY_PROTOCOL), P (MEMORY_WRITE_GATE), Q
(OBSERVER_LEDGER) numerics donmuş. R L'nin (BACKUP_STRATEGY) numerics
artifact'i; **kimlik sürekliliğinin sayısal tarafı**.

Tek cümle: **R = kimliği kaybetmeden geri dönebilme hakkının sayısal sözleşmesidir.**

R'nin üç gerilimi:
- Çok sık backup → storage/compute pressure
- Çok seyrek backup → M0/M1 gap, identity continuity riski
- Gevşek restore validation → sahte/bozuk backup ile restore

R'nin işi backup aralığı seçmek değil — **"hangi yedek eksikse kimlik
iddiası nasıl değişir?"** sorusunu sayısallaştırmak.

---

## Başlangıç pozisyonları

### Ön sorular — yön belirleme

Üç ön soru çapa turundan önce:

1. **Full identity için max_missing_m1_events = 0?** → EVET constitutional
2. **M0 snapshot during replay yasak mı sealed mi?** → sealed_checkpoint ile izinli
3. **M1Segment retention lifetime mı tiered mı?** → tiered lifetime (semantik lifetime + fiziksel hot/warm/cold + lossless transition; Q ile uyumlu)

Bu üç kabul R'nin omurgasını kilitledi.

### ChatGPT (Halit'in vekili, açılış)

9 ana çapa + 20 kırmızı çizgi:
1. RPO per layer
2. M1 WAL replication tolerance
3. M0 snapshot consistency window
4. Same identity restore thresholds
5. restore_with_missing_history numerics
6. Backup artifact retention
7. RestoreManifest validation
8. Foreign M2 merge caps
9. Forgetting attack defense numerics

### Claude (9 çapaya cevap + 1 ek çapa)

7 çapaya hardening önerileri + Ek Çapa 10:

**Ek Çapa 10:** Fork ve Migration restore ayrımı — same-identity restore'dan
**sayısal ayrım** kritik. Fork: new_instance_id + foreign_instance_origin +
anchors match origin + identity_continuity_claim forbidden. Migration:
constitutional_shift_event_ref + numerics_compatibility_validation +
identity_continuity_constitutional_only.

Önemli pozisyonlar:
- M1 RPO `continuous_replication` enum (sayı değil); cross-layer invariant
- `chain_gap_tolerance_events = 0` `{0}` allowed_range constitutional
- Üç M0 consistency invariant (consistency, replay_idle_or_sealed, partial_assembly_unsealed_count=0)
- Restore precondition checklist (5 koşul)
- `missing_history_max_gap_ms` allowed_range.max bounded; üstü = fork/migration
- `m0.last_known_good_retention = permanent` constitutional
- Foreign forbidden_set `higher_is_stricter` (Q whitelist'ten ters yön; semantik subject'e bağlı)
- Retention shrink human approval constitutional

### ChatGPT (kabul + 5 düzeltme + "yaz")

5 düzeltme:

**Düzeltme 1 — `change_class: forbidden` yerine canonical iki yön yaz**

M canonical alanlar `change_class_if_increased` ve `change_class_if_decreased`.
`change_class: forbidden` tek satır yanlış; immutable single-value key'lerde
her iki yön ayrı yazılmak zorunda.

**Düzeltme 2 — `backup.rpo.M1` unit karmaşası temizlensin**

`unit: enum + ms (hybrid)` problemli. İki ayrı key:
- `backup.rpo.mode.M1` (enum, value=continuous_replication)
- `backup.rpo_ms.M1.max_replication_lag` (ms, bounded)

M1 backup mode = continuous; M1 operational lag = bounded ms.

**Düzeltme 3 — M1Segment + RestoreManifest retention dependency basitleşsin**

`lifetime` enum comparison zor. Çözüm: **ikisi de lifetime** (immutable).
Bu sayede dependency comparison zorunluluğu çıkmaz; manifest M1'leri
her zaman bulur.

**Düzeltme 4 — restore_with_missing_history üst sınır aşılırsa mode net**

`migration_birth` sadece constitutional/genesis-affecting değişim için.
M1 gap büyük diye migration demek yanlış. Doğru:
- fork_birth (source identity parent provenance)
- clean_birth with foreign audit
- migration_birth ANCAK constitutional shift de aynı anda varsa

**Düzeltme 5 — Foreign M2 merge forbidden set yönü açık yazılsın**

enum_set directionality semantik subject'e bağlı:
- forbidden_subject_class_set (blacklist): higher_is_stricter
- allowed_subject_class_set (whitelist): lower_is_stricter

R'de bu net bir alt kural olarak yazılır.

"Yaz" hükmü.

### Halit final

> *"Yaz. R = kimliği kaybetmeden geri dönebilme hakkının sayısal sözleşmesi.
> Backup hızlı olsun diye kimlik gevşetilemez. Restore kolay olsun diye
> tarih kanıtı atlanamaz."*

---

## Çekirdek kararlar (17 omurga)

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
14. Foreign M2 merge: forbidden_subject_class_set higher_is_stricter; required_gate_ref = memory_write_gate; provenance permanent.
15. Replay budget continuity required (O bridge); replay-derived trace provenance preserved.
16. M1 retention shrink forbidden; retention change human approval required; FORGETTING_ATTACK_SUSPECTED composite signal.
17. Missing R numerics → strict mode (restore blocked; M1 continuous backup DEVAM eder; foreign merge/retention/tier transition blocked).

---

## Madde yansımaları

### Madde 1 — identity continuity asimetrisi
Same-identity / restore_with_missing_history / fork / migration — dört
farklı mod; biri diğerine dönüşemez. Her birinin **constitutional
invariant set'i** ayrı. Madde 1 "tek mekanizma, çoklu imza"nın identity
seviyesindeki yansıması.

### Madde 6 — LLM R numeric değiştiremez (violation test 38)
R numerics LLM tarafından üretilemez veya değiştirilemez.

### Madde 7 — hafıza ayrılığı
R doğrudan kimlik koruma freni. M1 (tarih kanıtı) retention = lifetime
constitutional; M2 (bilgi) retention policy-based; M3 (konuşma kabuğu)
optional. Layer ayrımı sayısal disiplinde de korunur.

### Üç R asimetri
- **Operational vs constitutional:** WAL lag (operational, bounded) ≠ chain gap (constitutional, 0)
- **Backup tightening vs weakening:** retention shrink = ALWAYS human approval
- **Restore validation:** hash/signature/numerics_refs constitutional immutable

---

## Önemli sertleştirmeler

### Constitutional immutable canonical form
`change_class: forbidden` tek satır yanlış; her constitutional key her iki
yön (`change_class_if_increased` ve `change_class_if_decreased`) ayrı
forbidden olmak zorunda. M canonical schema'ya tam uyum.

### M1 RPO mode + lag ayrımı
`backup.rpo.mode.M1 = continuous_replication` (immutable mode)
`backup.rpo_ms.M1.max_replication_lag` (operational ms bound)
İkisi farklı kavramlar; tek hybrid key yanlıştı.

### Lifetime retention basitleştirme
M1Segment + RestoreManifest ikisi de lifetime → dependency comparison
zorunluluğu çıkmaz. Manifest M1'leri her zaman bulur. En güvenli form.

### Fork vs migration sayısal ayrımı
Fork = aynı constitutional anchors + new instance_id + paralel varlık.
Migration = constitutional shift + identity preserved across shift.
M1 gap büyük diye migration olmaz; migration ancak anayasal/genesis-affecting
uyumsuzluk varsa. R bu ayrımı constitutional invariant set'leriyle korur.

### enum_set semantik subject'e bağlı yön
Q §15'te whitelist (LLM scope) lower_is_stricter; R §17'de blacklist
(forbidden_subject_class_set) higher_is_stricter. M §8 enum_set
convention'ın R'deki özel uygulaması; semantik (whitelist mı blacklist mı)
yönü belirler.

### Restore precondition checklist
5 koşul tam: WAL=0 + M1 gap=0 + M0 valid + manifest valid + anchors compatible.
Bir koşul tatmin edilmezse same-identity restore ABORT, restore_with_missing_history
veya fork/migration tercih. Gevşeklik yok.

### O → R bridge canonical
O §7 restore_budget_continuity R §18'de `replay_budget_continuity_required = true`
constitutional. Restore sonrası replay budget M1 segment'inden devralınır;
sıfırlama yasak (L forgetting attack defense yansıması).

### Q → R bridge tier lossless
Q §13 storage tier lossless invariant M1Segment lifetime retention'a
uygulanır. Hot/warm/cold transition lossless; anlam değişmez.

### Forgetting attack composite signal
Mass delete + retention shrink + M1 gap + permanent log access anomaly +
replay budget spike + numerics rollback → FORGETTING_ATTACK_SUSPECTED.
R bunu Q + L + O ile birleştirir.

---

## Yan güncellemeler (commit'in parçası)

- `BACKUP_STRATEGY.md` §7 (M0 Snapshot Policy) cross-ref to R §9-10, §21
- `BACKUP_STRATEGY.md` §8 (M1 Append-only) cross-ref to R §7-8, §19
- `BACKUP_STRATEGY.md` §12 (Identity Continuity Matrix) cross-ref to R §12-15
- `BACKUP_STRATEGY.md` §17 (Replay-derived Trace) cross-ref to R §18 + O bridge
- `BACKUP_STRATEGY.md` §18 (Cross-restore + Foreign Merge) cross-ref to R §17
- `REPLAY_PROTOCOL_NUMERICS.md` §21 dependency matrix güncellendi (restore budget
  continuity artık R canonical bağ)
- `OBSERVER_LEDGER_NUMERICS.md` §13 (Storage Tiering) cross-ref to R §8
  (M1Segment lifetime + lossless transition R aynı invariant'ı uygular)
- `MEMORY_WRITE_GATE_NUMERICS.md` §16 (Self-deception) cross-ref to R §17
  foreign merge forbidden_set + Memory Write Gate bypass yasağı
- `README.md` completed listesine BACKUP_STRATEGY_NUMERICS eklendi
- `docs/conversations/0018-backup-strategy-numerics.md` eklendi

Yeni canonical event gerekmedi; L + F + M canonical event'leri reuse:
BACKUP_ARTIFACT_STATUS_CHANGED, RESTORE_OPERATION_STATUS_CHANGED,
M2_FOREIGN_MERGE_STATUS_CHANGED, M1_HISTORY_LOST_AT_RESTORE,
FORK_FROM_INSTANCE, MIGRATION_FROM_INSTANCE, FORGETTING_ATTACK_SUSPECTED.

---

## Açık kalanlar (implementation veya sonraki numerics artifact'lere devredildi)

- Exact production retention values (M2 windows, fork concurrency limits) → signed artifact
- Constitutional shift event taxonomy → BOOTSTRAP_GENOME / CONSTITUTION spec revision
- Tier transition cadence ve cost trade-off'ları → Q ile koordinasyon
- Multi-signature requirement for high-impact numerics changes → M §13 open question
- Cross-instance trust verification protocol → fork_birth + migration_birth için ayrı spec olabilir
- Restore validation timeout ile RTO ilişkisi → benchmark + implementation
- Forgetting attack threshold tuning → operational

Bunlar **R kapsamı dışında**; implementation veya sonraki numerics artifact'lerde
netleşir.

---

## Sıradaki

A-Q + R kapandı. **19 belge.** Conceptual phase + 5 numerics artifact tamam.

Sıradaki NUMERICS belgeleri (kalan):
- S: `BOOTSTRAP_GENOME_NUMERICS.md` — genome parametreleri, sleep cycle
  matematiği, plasticity state transitions, fatigue recovery
- T: `RECALL_PROTOCOL_NUMERICS.md` — top-k boyutu, recall cooldown, recall-side
  staleness (P canonical kaynak)
- U: `ADAPTER_TRUST_NUMERICS.md` — trust score band'ları, decay rate

---

## Kilit cümleler

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
