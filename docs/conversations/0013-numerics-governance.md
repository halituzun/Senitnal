# 0013 — Numerics Governance

> Bu dosya `NUMERICS_GOVERNANCE.md` (v0.1) ortaya çıkmadan önce yapılan üçlü
> tasarım konuşmasının (Halit + Claude + ChatGPT) sıkıştırılmış özetidir. M
> turunun kararlarının soyağacı.
>
> A-L: 0001-0012

---

## Tarih
2026-05-19 (L → M geçişi, conceptual phase'in dış sınırı)

## Bağlam

A-L kapanmış. **Conceptual phase tamamen donmuş**. Sıradaki faz NUMERICS belgeleri. Ama her NUMERICS dosyası kendi disiplini ile yazılırsa A-L'nin tüm anayasal sınırları **sayısal katmanda gevşeyebilir**.

Örnek tehlikeler:
- `max_replay_budget` artırılır → patolojik ruminasyon
- `payload_intensity_cap` artırılır → sensory storm
- `candidate_max_age` uzatılır → doğrulanmamış kayıtlar verified gibi
- `stale_data_threshold` gevşetilir → eski veri ile karar
- `deontic max_order_size` artırılır → catastrophic action risk

M = meta-belge. Tek sayı yazmaz; numerics'in **yönetim sözleşmesini** biçimselleştirir.

---

## Başlangıç pozisyonları

### ChatGPT (Halit'in vekili, açılış)

Manifesto:
> *Numerics runtime config değildir.*
> *Numerics, donmuş sözleşmelerin sayısal izdüşümüdür.*
> *Bir sayıyı gevşetmek sıradan update değildir.*

Ayrımlar:
- 6 numeric family (safety_critical, resource_limits, calibration_bands, identity_retention, operational_convenience, experimental)
- tightening vs weakening
- runtime config vs numeric artifact

5 ana çapa:
1. NumericsArtifact nerede yaşar (M2/external/ikisi)?
2. Yeni gate gerekir mi?
3. Learned calibration trace numerics sayılır mı?
4. Directionality her key metadata'sı mı?
5. Restore sırasında version mismatch?

### Claude (5 çapaya cevap + yeni nüans)

1. **External signed artifact + M2 reference** (ADAPTER_MANIFEST pattern)
2. **Yeni gate yok**, G §8 verification matrix'e satır
3. **Static ≠ learned** kesin; static cap, learned trace M0'da yaşar
4. **Directionality her key'de metadata** zorunlu, global rule yok
5. **Restore RestoreManifest numerics ref'leri kullanır**, yeni numerics sessiz uygulanmaz

**Yeni nüans:** Numeric dependency declaration — bağımlı numeric'lerin atomic multi-key update

### ChatGPT (kabul + "yaz")

6 ana karar omurga:
1. NumericsArtifact = external signed + M2 reference
2. Yeni gate yok; Memory Write Gate + numeric validation
3. Static numerics ≠ learned calibration
4. Directionality her NumericEntry metadata'sında zorunlu
5. Restore eski RestoreManifest numerics ref'leriyle başlar
6. Numeric dependency declaration zorunlu

ChatGPT'nin son sertleştirmeleri:
- Permanence policy detayları
- Canonical event seti (NUMERICS_ARTIFACT_STATUS_CHANGED, NUMERICS_VERSION_MISMATCH_DETECTED, NUMERICS_FAILSAFE_ACTIVATED)
- Fail-safe strict mode mantığı
- 12 violation test

"Yaz" hükmü.

---

## Çekirdek kararlar (6 ana)

1. **NumericsArtifact = external signed artifact + M2 reference** (ADAPTER_MANIFEST_SPEC pattern). Artifact dışarıda, M2'de sadece status izlenir.
2. **Yeni gate yok**: Memory Write Gate + numeric-specific verification matrix satırı (G §8).
3. **Static numerics ≠ learned calibration**: static signed artifact, learned M0 traces. Static, learned'ın drift cap'idir.
4. **Directionality her NumericEntry metadata'sında zorunlu**: higher_is_stricter / lower_is_stricter / bidirectional_sensitive / neutral. Global rule yok.
5. **Restore numerics versioning**: RestoreManifest.numerics_artifact_refs[] ile restore başlar. Yeni numerics sessiz uygulanmaz; NUMERICS_VERSION_MISMATCH_DETECTED + human review.
6. **Numeric dependency declaration**: bağımlı numerics atomic multi-key update. Partial update yok; dependency violation = artifact reject.

---

## Madde 1 + Madde 7 yansıması — numeric layer

A-L boyunca Madde 1 her seviyede yansıdı. M'de:
- **Madde 1 yansıması:** Numeric "tip" kategorize edilmez — her key kendi metadata'sını taşır (directionality, allowed_range). Familyye göre davranış değiştirmez; family sadece audit grouping.
- **Madde 7 yansıması:** Numerics_artifact_reference M2'de yaşar — hafıza ayrılığı kuralı, sayısal artifact'lerin yönetimine taşınıyor.
- **Madde 6 yansıması:** LLM numeric value üretemez/değiştiremez (violation test 11).

---

## Önemli sertleştirmeler

### "Numerics ayar değildir; anayasal sözleşmelerin sayısal dişidir"
M'nin omurgası. Sayılar tek başına değer değil; ait oldukları mekanizmanın davranış sınırı.

### Tightening vs Weakening asymmetry
DEONTIC §18 emergency_revert pattern'i numerics'e de uygulanır. Weakening her zaman human approval + audit + rollback path ister. Tightening daha kolay.

### No-default rule
F'deki Observer Ledger no-default permanence policy disiplini numerics seviyesinde de. Her NumericEntry **tüm field'ları explicit** taşır. Çıplak sayı yasak.

### Static ≠ Learned ayrımı
Karıştırılırsa learned mapping static cap gibi davranır (silent drift) veya static numeric learned gibi sürekli değişir. İkisi farklı katmanlar, farklı audit kanalları:
- Static: NUMERICS_ARTIFACT_STATUS_CHANGED
- Learned: COMPILER_MAPPING_UPDATED, SLEEP_REPLAY_SYNAPSE_UPDATE, vs.

### Numeric dependency declaration
Yeni nüans (Claude tarafı). Bağımlı numerics tek bir değişikle bozulamaz; atomic artifact. Bu, "tek değişiklik için iki kat dikkat" disiplinini sağlar.

### Fail-safe strict mode
"Numerics yoksa sistem daha serbest değil, daha kısıtlı çalışır." Fail-open yasak. Eksik numerics = strict cap'ler.

### Restore numerics versioning
BOOTSTRAP §23 constitutional shift policy pattern'inin numerics versiyonu. Restore sırasında sessiz upgrade yok; mismatch detected + human review.

### Rollback only to previous verified
DEONTIC §18 ile uyumlu. Numeric rollback path sadece previous verified artifact'e dönebilir; forward yasak.

---

## Yan güncellemeler (commit'in parçası)

- `MEMORY_CONTRACT.md` M2 subject_class listesine `numerics_artifact_reference` eklendi
- `MEMORY_WRITE_GATE.md` §8 verification matrix'e numerics_artifact_reference satırı + NUMERICS_GOVERNANCE cross-ref
- `BACKUP_STRATEGY.md` RestoreManifest schema'ya `numerics_artifact_refs[]` field eklendi + NUMERICS_GOVERNANCE §19 cross-ref
- `OBSERVER_LEDGER_SCHEMA.md` §10 permanence_policy: 6 yeni numerics event entry (NUMERICS_ARTIFACT_STATUS_CHANGED with conditional permanence + NUMERICS_VERSION_MISMATCH_DETECTED + NUMERICS_FAILSAFE_ACTIVATED)
- `OBSERVER_LEDGER_SCHEMA.md` §19 event catalog ledger_meta family: 3 yeni numerics events eklendi
- `README.md` — NUMERICS_GOVERNANCE tamamlanmış listesine

---

## Açık kalanlar (NUMERICS belgelerine devredildi)

- Default human_approval workflow detayı
- Multi-signature requirement (kritik numerics için)
- Strict mode default values (her family için)
- Compatibility class auto-detection
- Approval timeout süreleri

---

## Sıradaki

A-L kapandı, M = numerics meta-anayasa. **14 belge.** Conceptual phase + numeric governance hazır.

Sıradaki NUMERICS belgeleri (her biri bu governance'a uyacak):
- `INGRESS_COMPILER_NUMERICS.md`
- `REPLAY_PROTOCOL_NUMERICS.md`
- `MEMORY_WRITE_GATE_NUMERICS.md`
- `OBSERVER_LEDGER_NUMERICS.md`
- `BACKUP_STRATEGY_NUMERICS.md`
- `BOOTSTRAP_GENOME_NUMERICS.md`
- `RECALL_PROTOCOL_NUMERICS.md`
- `ADAPTER_TRUST_NUMERICS.md`

Sıralama önerisi: **INGRESS_COMPILER_NUMERICS** ilk (J'den beri dış event → neural_seed dönüşümü sayısal bandsız).

---

## Kilit cümleler

> **Numerics ayar değildir. Numerics, anayasal sözleşmelerin sayısal dişidir.**
>
> **Numerics runtime config değildir. Numerics, donmuş sözleşmelerin sayısal izdüşümüdür.**
>
> **Bir sayıyı gevşetmek sıradan update değildir.**
> **Bir threshold değiştirmek davranış sınırı değiştirmektir.**
>
> **Sayılar küçük görünür. Ama sayılar anayasanın eylemdeki dişleridir.**
>
> **Static numerics learned trace'in sınırıdır. Learned trace static numeric değildir.**
>
> **Numerics yoksa sistem daha serbest değil, daha kısıtlı çalışır.**
>
> **Tightening kolay olabilir; weakening asla kolay olmamalı.**
>
> **Numeric rollback path may only revert to a previously verified artifact, never forward to a new artifact.**
