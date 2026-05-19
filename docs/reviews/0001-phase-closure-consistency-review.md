# 0001 — Phase Closure Consistency Review

> 22 belge frozen draft v0.1 tamamlandıktan sonra cross-document mekanik
> denetim raporu. **Yeni tasarım belgesi değildir** — kapanış denetimidir.
> Bu rapor temiz çıkarsa Sentinel "implementation readiness review" fazına
> geçer.

---

## Tarih
2026-05-19 (U patches sonrası, faz kapanış denetimi)

## Kapsam

22 belge:

```
Conceptual (12):  A B C D E F G H I J K L
Governance (1):   M (NUMERICS_GOVERNANCE)
Numerics (8):     N O P Q R S T U
Sub-spec (1):     ATTENTION_WORKSPACE (Madde 4 yansıması)
```

12 kategori mekanik denetim:

```
A. Canonical Event Catalog
B. M2 Subject_class Registry
C. Constitutional Immutable Keys (canonical form)
D. Cross-artifact Dependencies
E. Gate / Gateway Boundaries
F. Adapter / Core Boundaries
G. LLM Boundaries (Madde 6)
H. Restore / Fork / Identity Paths
I. Staleness / Cooldown Ownership
J. Budget / Cooldown Continuity
K. Missing-Numerics Failsafe
L. Open Questions Inventory
```

---

## Yöntem

4 paralel Explore agent ile 12 kategori cross-document tarandı. Bulgular
derlendi; **kritik (FAIL)** ve **küçük (PASS-)** olarak ayrıldı; patch
hedefleri belirlendi; bu rapor öncesi 5 patch uygulandı.

Bu rapor **patches uygulandıktan sonraki** denetim hükmünü taşır.

---

## Bulgular ve Uygulanan Patches

### A — Canonical Event Catalog: PASS

**Bulundu (uygulandı):**
- `MEMORY_WRITE_GATE.md` line 816 "OBSERVER_LEDGER_SCHEMA event catalog buna göre güncellenir (yan patch)" notası kalıntıydı (F zaten güncel). Notas net hale getirildi: "F §19 ve §10 bu canonical değişikliğe göre güncellenmiş durumda; eski isimler F'de listede yok."
- `REPLAY_PROTOCOL.md` line 763 `REPLAY_SESSION_COMPLETED` migration narrative pending notası kalıntıydı. Sertleştirildi: "F v0.1 §19 canonical: REPLAY_SESSION_COMPLETED artık valid değil; REPLAY_SESSION_STATUS_CHANGED + new_status: completed field discipline."

**Sonuç:** Tüm canonical event isimleri (`MEMORY_RECORD_STATUS_CHANGED`,
`REPLAY_SESSION_STATUS_CHANGED`, `LEDGER_STATE_CHANGED`, `M1_READ_AUDIT_RECORDED`,
`PHASE_TRANSITION_OCCURRED`, `ADAPTER_MANIFEST_STATUS_CHANGED`,
`BACKUP_ARTIFACT_STATUS_CHANGED`, `NUMERICS_ARTIFACT_STATUS_CHANGED` etc.)
F catalog'da kayıtlı; permanence policy table'da satırı var; reason field
discipline tutarlı.

### B — M2 Subject_class Registry: PASS

**Bulundu (false-positive):**
- Agent rapor etti: `incident_human_record` README'de phantom — kontrol
  edildi, README'de yok, MEMORY_CONTRACT.md §3'te canonical kayıtlı (line 104).
  False-positive.
- `bootstrap_reference` KIND values (genome_artifact_ref vs.) subject_class
  ile karıştırılmış mı? S §21 patch zaten clarification eklemişti
  (`initial_allowed_bootstrap_reference_kind_set` + violation test 27b).
  Kontrol pass.
- `foreign_instance_origin` provenance metadata olduğu P §5 patch ile
  zaten netleştirilmişti. Kontrol pass.

**Sonuç:** M2 subject_class enum (16 değer) B §3 canonical; cross-document
tutarlı.

### C — Constitutional Immutable Keys: PASS (patch uygulandı)

**KRİTİK bulundu (uygulandı):**

`OBSERVER_LEDGER_NUMERICS.md` (Q) 7 yerde `change_class: forbidden` tek
satır canonical form ihlali:
- §10 `permanent.lossless_required`
- §10 `verify_on_read_required`
- §12 `permanence.permanent_ttl_ms`
- §14 `human_alert.suppression_window_ms.<critical_type>`
- §14 `human_alert.first_alert_immediate`
- §18 `compaction.lossless_required`
- §18 `compaction.hash_verify_before_and_after_required`

**Uygulanan patch:** Tüm 7 occurrence `replace_all` ile canonical iki-satır
forma çevrildi:

```diff
- change_class: forbidden
+ change_class_if_increased: forbidden
+ change_class_if_decreased: forbidden
```

**Sonuç:** Q artık M canonical schema'ya tam uyumlu. Diğer numerics
artifact'lerde (N, O, P, R, S, T, U) bu form zaten doğru kullanılıyor.

### D — Cross-artifact Dependencies: PASS

**Bulundu:** 10 kritik bridge sağlam:

| Bridge | Yön | Durum |
|--------|-----|-------|
| N → O | `ingress_calibration_replay_delta_cap ≤ N.per_mapping_daily_delta_cap × 0.30` | ✓ |
| O → P | `max(P.replay_survival_weight.*) ≤ O global cap` | ✓ |
| O → P (staleness) | `outcome_alignment.max_wait_ms ≤ P.epistemic_staleness_threshold` | ✓ canonical |
| P → T | `p_threshold_override_forbidden = true` constitutional | ✓ |
| T → N (candidate) | `candidate.intensity_multiplier ≤ N.candidate_recall_ratio` | ✓ |
| U → C (source) | `source_trust.effective_band = min(raw, adapter_trust)` | ✓ one-way |
| R → O (replay budget) | `replay_budget_continuity_required = true` | ✓ canonical |
| R → U (adapter trust) | same-identity devralma + fork foreign quarantined | ✓ |
| S → O / S → N | initial rhythm/caps ≤ operational caps | ✓ |
| U → I (incompatible pairs) | I §8 + U §11 senkron (intent_relay + recall_provider extension) | ✓ |

**Sonuç:** Tüm bridge'ler her iki belgede karşılıklı kayıtlı; computed_*
dependency form'u doğru kullanılmış.

### E — Gate / Gateway Boundaries: PASS

**Bulundu:**
- Memory Write Gate ≠ Deontic Gate ayrımı `MEMORY_WRITE_GATE.md` §4'te
  explicit (violation test ile)
- Two-Layer Deontic Structure (DEONTIC §4-6) net
- Execute capability 8-koşul AND (U §12) doğru
- Self-field Coupling: "Deontic proximity gate kararı değildir" (E §15) ✓

**Sonuç:** Epistemik vs action risk ekseni karışmıyor.

### F — Adapter / Core Boundaries: PASS

**Bulundu:**
- Adapter neural_seed üretemez (`ADAPTER_MANIFEST_SPEC.md` §15 +
  `INGRESS_COMPILER_SPEC.md` §4 + U §16 immediate revoke)
- Compiler deterministic mapping (J §4)
- Adapter raw payload → compiler → neural_seed akış tutarlı
- Execution akış: core → gate → ApprovedActionIntent → adapter (I §10)

**Sonuç:** Adapter "uzuv, beyin değil" çizgisi 4 belgede tutarlı.

### G — LLM Boundaries (Madde 6): PASS (patch uygulandı)

**Bulundu:** LLM yetkisi tarifi 8 katmana dağılmış; teknik uyum var ama
**single source of truth eksikti**.

**Uygulanan patch:** CONSTITUTION.md Madde 6 "Alt-spec referansları" bölümü
genişletildi; **8 katmanlı yansıma tablosu** eklendi:

| Katman | Belge | Madde 6 Yansıması |
|--------|-------|---|
| Ingress | C §11 + J §6 + N §16 | HumanIntentEvent zayıf cap; learned_mappings KAPALI |
| Adapter contract | I §4 + I §8 | constitutional adapter type değil |
| Adapter trust | U §15 | 3 constitutional invariant (execute/memory_writer/recall_provider satisfaction forbidden) |
| Memory write | G §6, §15 + P §18 | M2 candidate üretemez; world_claim auto-verified yasak |
| Recall | H §5 + T §8 | RecallEvent üretemez; ranking semantic_judgment forbidden |
| Observer ledger | Q §15 | M1 read scope restricted + audit zorunlu |
| Deontic | E §8 Rule 4 | execution adapter'a doğrudan yol yok |
| Numerics | M Violation Test 11 | LLM numeric üretemez |

**Anayasal kural eklendi:** "Herhangi bir katmandaki LLM sınırı gevşeyecekse
Madde 6'nın Forbidden listesinin sayısal yansımasını ihlal etmiş olur —
safety_weakening veya forbidden change_class gerektirir; sessiz patch
yapılamaz."

**Sonuç:** LLM yetkisi artık tek hub'dan (CONSTITUTION Madde 6) tüm
katmanlara izlenebilir.

### H — Restore / Fork / Identity Paths: PASS (2 patch uygulandı)

**KRİTİK 2 delik bulundu (uygulandı):**

**Delik H1 — Fork `identity_continuity_claim_forbidden` DEONTIC §8 hard-stops'ta değildi.**

Sadece BACKUP_STRATEGY §14'te enforcement detail olarak yazılıydı; ama
"constitutional invariant" denmişti — Hard-Stops listesinde olması gerek.

**Uygulanan patch:** DEONTIC_GATE.md §8 Constitutional Hard-stops listesine
2 yeni rule eklendi:

```
12. Forked instance may never claim identity continuity with its
    source instance. Fork = parallel new entity; foreign_instance_origin
    provenance is permanent and cannot be converted to native.
    (BACKUP_STRATEGY §14, R §14, U §20)

13. restore_with_missing_history mode may never claim full identity
    continuity. Restricted mode invariants apply for the duration of
    restricted_mode_min_duration_ms.
    (BACKUP_STRATEGY §13, R §13)
```

**Delik H2 — Phase monotonicity + restore_birth davranışı belirsizdi.**

S §16 "rollback yalnız restore_with_missing_history + migration_birth ile"
diyordu; ama same-identity `restore_birth`'in phase davranışı (M0 +
complete M1 → phase state yüklenir) belirtilmemişti. "Rollback mı?"
sorusu açık kalmıştı.

**Uygulanan patch:** S §16'ya "restore_birth phase davranışı — rollback
DEĞİL, state continuation" alt-bölümü eklendi:

```
restore_birth path:
    M0 + M1 fully restored (R §12 preconditions satisfied)
    → phase state M0 snapshot'tan okunur ve resume edilir
    → bu bir "rollback" değil, "interrupted continuation"
    → monotonicity invariant ihlal edilmez

5 birth_mode için phase davranışı tablosu eklendi.
```

**Sonuç:** Identity path matrix tüm 5 birth_mode için net (clean / restore /
restore_with_missing_history / fork / migration); DEONTIC anayasal hard-stops
listesinde kayıtlı; S phase monotonicity invariant'ı netleştirilmiş.

### I — Staleness / Cooldown Ownership: PASS

**Bulundu:**
- P §8 `epistemic_staleness_threshold_ms.<subject_class>` canonical kaynak
- N §15 `candidate_recall_ratio` canonical
- O §5-6 replay budget caps canonical
- T §17 `p_threshold_override_forbidden = true` constitutional guard

**Sonuç:** Hiçbir spec başka bir spec'in canonical kaynağını override edemez.

### J — Budget / Cooldown Continuity: PASS

**Bulundu:**
- O §7 replay_budget_continuity_required
- R §18 canonical bağ (restore continuity)
- T §10 recall_budget_continuity (aynı pattern)
- U §20 adapter_trust restore_continuity_required

Tüm budget tipleri forgetting attack defense (L §22) ile bağlı; restore
sonrası reset YASAK kuralı 4 belgede tutarlı.

### K — Missing-Numerics Failsafe: PASS

**Bulundu:** 8 numerics artifact (N/O/P/Q/R/S/T/U) "missing → strict mode"
pattern'i M §11 ile uyumlu uyguluyor. Hiçbiri fail-open değil.

| Artifact | Missing davranışı |
|----------|-------------------|
| N | strict mode (min-cap fallback) |
| O | audit-safe (replay disabled except outcome_alignment RO) |
| P | strict_no_verified (verified üretimi DISABLED) |
| Q | audit-safe (permanent writes CONTINUE; sampling/LLM read DISABLED) |
| R | restore BLOCKED; M1 backup CONTINUES |
| S | SELF_GENESIS BLOCKED; running instance CONTINUES |
| T | recall operations BLOCKED; M1 audit reads continue |
| U | risky capabilities DISABLED; observe-only |

### L — Open Questions Inventory

**Toplam:** ~121 open question 9 numerics + governance belgesinde.

**Recurring themes (3+ belgede tekrarlanan):**

1. **Exact production values** (14 yerde) — seed count, weight bands,
   budget limits, retention windows, threshold ms'leri
2. **Multi-signature requirement** (7 belgede) — M §13 inheritance
3. **Sleep cycle coordination** (4 belgede) — S, O, U, BOOTSTRAP
4. **Trust/decay function shape** (5 belgede) — S, U, T, linearity vs
   exponential
5. **Cross-instance verification** (3 belgede) — R, U, L

**Kapanmış (canonical kaynak bulunmuş):**
- O §25 "outcome alignment staleness threshold canonical kaynağı" → P §8
  ile kapandı (durumda "KAPANDI" yazılı olarak işaretli).

**Yapılması gereken (implementation readiness review fazına devr):**
- 121 open question tek dosyada toplanmalı (`docs/reviews/0002-open-questions-inventory.md` gibi)
- Implementation MVP vs deferred ayrımı yapılmalı
- Production değer setlerinin priority'si belirlenmeli

---

## FINAL HÜKÜM

```
A: PASS
B: PASS
C: PASS (1 patch: Q'da 7 occurrence canonical form)
D: PASS
E: PASS
F: PASS
G: PASS (1 patch: Madde 6 hub tablosu CONSTITUTION'a eklendi)
H: PASS (2 patch: DEONTIC §8 Rules 12-13 + S §16 restore_birth clarification)
I: PASS
J: PASS
K: PASS
L: PASS (open questions toplanmış; implementation phase'e geçişe hazır)
```

**Toplam:** 12 kategori PASS. 5 patch uygulandı (C tekil bulk, G CONSTITUTION
hub, H1 DEONTIC, H2 S, A MEMORY_WRITE_GATE + REPLAY_PROTOCOL wording).

```
A + B + C + D + E + F + G + H + I + J + K + L = PASS

PHASE CLOSURE CONFIRMED
22 belge frozen draft v0.1 — cross-document consistency review GREEN
```

---

## Sıradaki adım — implementation readiness review

Bu rapor PASS olduğu için Sentinel artık conceptual+numerics phase'inden
çıktı. **Yeni conceptual/numeric belge yazılmaz.**

Sıradaki üç iş kalemi sırasıyla:

```
1. Implementation readiness review
   → docs/reviews/0002-implementation-readiness.md
   → MVP için gerekli vs deferred ayrımı
   → 121 open question tek yerde + priority etiketleri

2. Minimum Viable Brain build plan
   → docs/build/0001-minimum-viable-brain-plan.md
   → Repository structure
   → Schema → ledger → compiler → M0 → workspace pulse → gates → MVP
   → İlk hedef: ObservationEvent → neural_seed → M1 audit → BLOCK/WAIT/MONITOR

3. First concrete signed numerics artifacts
   → ingress_compiler_numerics_v1.signed.json (production values)
   → diğer 7 numerics artifact production değerleri
   → MVP'nin numerics yükleyebilmesi için
```

---

## Notlar

- Bu rapor `Frozen` durumdadır; cross-document consistency review tekrar
  yapılırsa yeni numaralı dosya (`0003-...`) olarak kayıt edilir.
- Open questions inventory ayrı dosyaya çıkarılacak (`0002`).
- Build plan kod yazımına geçişin kapısıdır; bu rapor onun ön-koşuludur.

**Faz kapanışı doğrulandı.**

> *Sentinel artık tasarım belgeleri ile değil, ne kadar dikkatli inşa
> edileceği ile yarışıyor.*
