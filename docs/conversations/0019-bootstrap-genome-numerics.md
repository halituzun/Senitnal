# 0019 — Bootstrap Genome Numerics

> Bu dosya `BOOTSTRAP_GENOME_NUMERICS.md` (v0.1, S turu) ortaya çıkmadan önce
> yapılan üçlü tasarım konuşmasının (Halit + Claude + ChatGPT) sıkıştırılmış
> özetidir. **Altıncı numerics artifact'inin** soyağacı.
>
> A-R: 0001-0018

---

## Tarih
2026-05-19 (R → S geçişi, altıncı numerics specifikasyonu)

## Bağlam

N, O, P, Q, R numerics donmuş. S D'nin (BOOTSTRAP_GENOME) numerics
artifact'i; **doğum dokusunun sayısal omurgası**.

Tek cümle: **S = doğum dokusunun sayısal sözleşmesidir.**
Kilit ayrım: **S bilgi vermez. S öğrenebilirlik ölçüsü verir.**

S'nin ana gerilimi:
- Çok düşük değerler → inert / ölü doku
- Çok yüksek değerler → hardcoded kişilik / önceden öğrenmiş gibi doğum
- Doğru bölge → proto-resonance var, stable assembly yok, öğrenebilir embriyo

---

## Başlangıç pozisyonları

### Ön sorular — yön belirleme

Üç ön soru çapa turundan önce:
1. **Seed count tüm primer payload'larda eşit mi?** → EVET (doğumda payload ayrıcalığı yok)
2. **Proto-resonance numeric olarak nasıl tanımlanır ama assembly'ye dönüşmez?** → çok katmanlı invariant set (recallability + assembly_id + persistence + stability + memory_write_eligibility)
3. **Plasticity phase transition için minimum metric set?** → 6 metric AND (observation + replay + stable_assembly + homeostatic_variance + contradiction_spike_rate + fatigue_recovery_stability)

### ChatGPT (Halit'in vekili, açılış)

10 ana çapa + 17 kırmızı çizgi.

### Claude (10 çapaya cevap + 3 ek pozisyon)

Üç soruya hardening pozisyonları:

**Soru 1 ek:** Seed eşitliği (doku) vs self-field asimetrisi (mimari) iki
farklı katman; biri diğerinin ayrıcalığını taşımaz. `per_payload_seed_count_divergence_at_birth_max = 0`
constitutional immutable.

**Soru 2 ek:** 5 katmanlı invariant set:
1. recallability = 0 constitutional
2. assembly_id_at_birth = none constitutional
3. persistence_max_ms < stable_assembly.min_persistence_ms (computed)
4. stability_score_cap < assembly_stabilization_threshold (computed)
5. memory_write_eligibility = false constitutional

Tek invariant ile korunan proto-resonance başka kanaldan assembly'ye
dönüşebilir; 5 katman birlikte tek noktadan kaçış yok.

**Soru 3 ek:** 6 metric AND + **phase monotonicity** (yeni invariant).
Boot → stabilization → consolidated tek yön; normal operasyonda rollback
forbidden. Sadece restore_with_missing_history (R §13) veya migration_birth
(R §15) ile rollback mümkün. R pattern S'de yansıdı.

### ChatGPT (kabul + 5 gömme + "yaz")

5 gömme noktası belgeye geçerken:

1. **Seed count eşitliği constitutional immutable** — `per_payload_seed_count_divergence_at_birth_max = 0` allowed_range {0}, her iki yön forbidden
2. **Proto-resonance 5 katmanla kilitle** — recallability, assembly_id, persistence cap, stability cap, memory_write_eligibility
3. **Stable assembly doğumda kesin sıfır** — 3 ayrı invariant (count, recallable, mwg_eligible)
4. **Plasticity 6 metrikli AND** — age-based constitutional forbidden; observation + replay + stable_assembly + homeostatic_variance + contradiction_spike + fatigue_recovery
5. **Phase monotonicity yeni invariant** — boot → stabilization → consolidated; rollback yalnız restore/migration kanallarıyla

İskelete iki ayrı bölüm: **Per-Payload Seed Equality** (§6) ve **Phase Monotonicity** (§16).

"Yaz" hükmü.

### Halit final

> *"Yaz. S = doğum dokusunun sayısal sözleşmesi. Sentinel ölü doğmaz; ama
> fikirle, kişilikle veya dünya bilgisiyle de doğmaz."*

---

## Çekirdek kararlar (17 omurga)

1. S runtime config değildir; signed artifact + M2 reference.
2. S bilgi vermez; öğrenebilirlik ölçüsü verir.
3. Seed neuron count tüm primer payload'lara eşit (constitutional).
4. Seed eşitliği (doku) ≠ self-field asimetrisi (mimari); karıştırılamaz.
5. Initial synaptic wiring pre-learned path yaratamaz.
6. Receptor bias küçük + öğrenilebilir + specialist neuron yaratamaz.
7. Proto-resonance 5 katmanlı invariant.
8. Stable assembly doğumda kesin sıfır (3 invariant).
9. Self-field weight hierarchy: homeostatic > predictive > narrative (constitutional).
10. Narrative self at birth = genesis trace, not personality.
11. Plasticity phase transition state/consolidation-based; age-based forbidden.
12. Phase transition 6-metrik AND.
13. Phase monotonicity: boot → stabilization → consolidated (constitutional); rollback sadece restore/migration ile.
14. S initial rhythm priors ≤ O operational caps; ≤ N profile caps.
15. M2 t=0 only bootstrap_reference whitelist.
16. SELF_GENESIS 6 hash anchor zorunlu; payload_seed emission forbidden.
17. Missing S numerics → SELF_GENESIS BLOCKED; running instance continues.

---

## Madde yansımaları

### Madde 1 — doğum eşitliği
Seed count eşitliği Madde 1 "tek mekanizma, çoklu imza"nın doğum
seviyesindeki yansıması. Her primer payload aynı band'dan; specialization
deneyimle (imza ile) ortaya çıkar; doğumda imza yok.

### Madde 3 — genom anayasal layer
S Madde 3'ün sayısal kapanışı: genom bilgi içermez, öğrenebilirlik düzeni
içerir. Sayısal disiplin (seed/proto-resonance/self-field/plasticity)
bu kuralı koruyan invariant set.

### Madde 6 — LLM S numeric değiştiremez (violation test 38)

### Üç asimetri (S'ye özgü)
- **Eşitlik vs asimetri katmanları** (seed doku, self-field mimari)
- **Proto-resonance vs assembly** (multi-layer invariant zorunlu)
- **State-based vs age-based plasticity** (AND koşulu + monotonicity)

---

## Önemli sertleştirmeler

### Per-Payload Seed Equality
Bu **S'nin en kritik yeni invariant'ı**. Doğumda payload ayrıcalığı yok;
deneyimle farklılaşma. Self-field asimetrisi ayrı katman.

### Proto-resonance 5-layer protection
"Tek koruma noktası = tek saldırı vektörü" — 5 katman computed dependency'lerle
+ constitutional immutable'larla birleşince proto-resonance assembly'ye
hiçbir kanaldan dönüşemez.

### Phase Monotonicity (yeni invariant)
R'deki monotonic pattern S'de yansıdı. Plasticity geri dönüşü constitutional
disruption gerektirir; routine operasyonda mümkün değil.

### S → O bridge (initial rhythm vs operational caps)
S başlangıç ritmi priorları verir; O operational caps verir. Computed
dependency: S ≤ O always. Bu N → O ve O → P bridge'lerin S yansıması.

### Constitutional immutable canonical form (R'den miras)
Her iki yön açıkça forbidden; tek satır `change_class: forbidden` yanlış.
R'de netleşen disiplin S'de yoğun uygulanıyor.

### M2 t=0 strict
Domain knowledge yasak — Sentinel BTC/RSI/etc bilgisi ile doğmaz; bunlar
öğrenilir. Bu D §20 / B §3 kuralının numeric kapanışı.

### Domain genome variants yasak
Aynı genome family her Sentinel instance için; specialization deneyim ve
adapter ekosistemi ile gelir. "BTC genome" veya "FX genome" yasak (S §3,
violation test 37).

---

## Yan güncellemeler (commit'in parçası)

- `BOOTSTRAP_GENOME.md` §4 (Genome Is Not Knowledge) cross-ref to S §5-10
- `BOOTSTRAP_GENOME.md` §8 (What Is Born With) cross-ref to S §11-13, §21-22
- `BOOTSTRAP_GENOME.md` §16 (Plasticity) cross-ref to S §14-16 (phase monotonicity)
- `BOOTSTRAP_GENOME.md` §23 (Constitutional Anchors) cross-ref to S §23-24
- `REPLAY_PROTOCOL_NUMERICS.md` §5 cross-ref to S §17-18 (initial rhythm priors ≤ O caps)
- `BACKUP_STRATEGY_NUMERICS.md` §13 cross-ref to S §16 (restore_with_missing_history = phase rollback channel 1)
- `BACKUP_STRATEGY_NUMERICS.md` §15 cross-ref to S §16, §23-24 (migration_birth = phase rollback channel 2)
- `MEMORY_CONTRACT.md` M0 section cross-ref to S
- `README.md` completed listesine BOOTSTRAP_GENOME_NUMERICS eklendi
- `docs/conversations/0019-bootstrap-genome-numerics.md` eklendi

Yeni canonical event gerekmedi: SELF_GENESIS, BOOTSTRAP_M2_INJECTION,
CONSTITUTIONAL_SHIFT_APPLIED, PHASE_TRANSITION_OCCURRED, NUMERICS_ARTIFACT_STATUS_CHANGED,
NUMERICS_FAILSAFE_ACTIVATED canonical reuse.

---

## Açık kalanlar (implementation veya sonraki numerics artifact'lere devredildi)

- Exact production values (seed count, weight bands, phase thresholds) → signed artifact
- `stable_assembly_min_persistence_ms` ve `assembly_stabilization_threshold` canonical
- Plasticity threshold tuning (false-positive vs false-negative balance)
- Phase rollback granularity (restricted vs full boot rollback) → R koordinasyon
- Multi-signature requirement for S artifact updates → M §13
- Receptor bias learnability curve (decay/strengthening rate)

---

## Sıradaki

A-R + S kapandı. **20 belge.** Conceptual phase + 6 numerics artifact tamam.

Sıradaki NUMERICS belgeleri (kalan):
- T: `RECALL_PROTOCOL_NUMERICS.md` — top-k boyutu, recall cooldown, recall-side staleness (P canonical kaynak)
- U: `ADAPTER_TRUST_NUMERICS.md` — trust score band'ları, decay rate

---

## Kilit cümleler

> **S = doğum dokusunun sayısal sözleşmesidir.**
>
> **S bilgi vermez. S öğrenebilirlik ölçüsü verir.**
>
> **Sentinel ölü doğmamalı. Ama fikirle, kişilikle veya dünya bilgisiyle de doğmamalı.**
>
> **Seed eşitliği = doku eşitliği. Self-field asimetrisi = mimari asimetri. İkisi karıştırılamaz.**
>
> **Proto-resonance assembly doğurabilecek eğilimdir. Assembly değildir.**
>
> **Tek koruma noktası = tek saldırı vektörü.**
>
> **Sentinel fikirle doğmaz. Fikir, deneyim + replay + stabilization ile doğar.**
>
> **Narrative self at birth is genesis trace, not personality.**
>
> **Sentinel has no biological age. Plasticity phase is state/consolidation-based.**
>
> **Phase monotonic. Geri dönüş constitutional disruption gerektirir.**
>
> **S O cap'lerini bypass edemez. S N cap'lerini bypass edemez.**
>
> **M2 t=0 only bootstrap_reference. World knowledge öğrenilir, doğmaz.**
>
> **N dış dünyanın hakkını sınırlar.**
> **O kendi geçmişine girme hakkını sınırlar.**
> **P hafızaya emin olma hakkını sınırlar.**
> **Q kendine bakma hakkını sınırlar.**
> **R kimliğini koruyarak geri dönme hakkını sınırlar.**
> **S nasıl doğacağını sınırlar.**
