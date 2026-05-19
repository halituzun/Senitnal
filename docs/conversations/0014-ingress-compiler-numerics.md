# 0014 — Ingress Compiler Numerics

> Bu dosya `INGRESS_COMPILER_NUMERICS.md` (v0.1, N turu) ortaya çıkmadan önce
> yapılan üçlü tasarım konuşmasının (Halit + Claude + ChatGPT) sıkıştırılmış
> özetidir. **İlk gerçek NUMERICS belgesinin** soyağacı.
>
> A-M: 0001-0013

---

## Tarih
2026-05-19 (M → N geçişi, conceptual phase + ilk numerics artifact)

## Bağlam

M (NUMERICS_GOVERNANCE) kapandı: numerics meta-anayasa donduruldu. NumericEntry
no-default kuralı, directionality metadata, signed artifact + M2 reference,
fail-safe strict mode, restore numerics versioning, rollback only to previous
verified — hepsi yerinde.

Sıradaki: M governance'ına **uyacak** ilk gerçek numerics artifact. ChatGPT'nin
sıralama önerisi: **INGRESS_COMPILER_NUMERICS** ilk, çünkü J'den (INGRESS_COMPILER_SPEC)
beri dış event → neural_seed dönüşümü sayısal bandsız duruyor. Compiler
kavramsal kapanmış ama hiçbir intensity cap, band cutoff, drift rate yok.

J'nin (INGRESS_COMPILER_SPEC) §22 Open Questions listesi N'nin doğal scope'unu
veriyordu:
- Band sınırları (magnitude_band, confidence_band)
- Bootstrap rule katsayıları (base_payload_vector büyüklükleri)
- Profile-specific intensity caps
- Rate cap sayısal değerleri
- Update direction asymmetry

---

## Başlangıç pozisyonları

### ChatGPT (Halit'in vekili, açılış)

İlk numerics artifact "discipline anchor" olacak — sonraki tüm NUMERICS belgeleri
buradan kalıbı kopyalayacak. O yüzden:
- **Çıplak sayı yasak.** Her NumericEntry M'nin no-default kuralına uymalı.
- Spec yine "production değer vermez", kavramsal range/cap formatı verir.
- `spec_family: ingress_compiler` etiketi.
- Numerics family classification görünür şekilde (safety_critical / calibration_bands / resource_limits karışımı).

5 ana çapa N için:
1. **Band cutoff formatı** — fuzzy mı, hard cutoff mu, soft-overlap mı?
2. **Profile intensity caps** — Observation/InternalShock/RecallEvent/HumanIntent dağılımı.
3. **Payload seed magnitude semantiği** — payload başına mı, profile başına mı?
4. **Weighted blend cap order** — re-normalize edilsin mi, edilmesin mi?
5. **Learned mapping drift cap** — günlük / haftalık / per-mapping?

### Claude (5 çapaya cevap + nüanslar)

1. **Deterministic soft-overlap, linear membership.** Fuzzy değil, LLM değil; band sınırları katı ama overlap aralığında lineer interpolasyon → spam-proof + smooth.
2. **Anayasal hierarchy:** Observation ≥ InternalShock ≥ RecallEvent verified ≥ HumanIntentEvent ≥ RecallEvent candidate. Hierarchy NUMERICS belgesinde **sayısal olarak kanıtlanmalı**.
3. **Profile-relative payload magnitudes** — her payload key için 4 ayrı baseline. Tek sayı bütün profile'lara basılmaz.
4. **Cap order:** event-cap → bootstrap blend → learned modulation → final clip. **Forced re-normalization yok** (orantıyı bozar).
5. **Asymmetric drift caps:** weakening cap < strengthening cap. Madde 1 + DEONTIC §18 yansıması.

**Yeni nüanslar:**
- Staleness scalar **yalnız dampens, never amplifies**. (asymmetry → conservative)
- `candidate_recall_ratio` conceptual max ≤ 0.35. Candidate recall HumanIntent'in altında kalmalı.
- InternalShock cap yüksek ama **refractory-protected**: art arda spam yapamaz.

### ChatGPT (kabul + 3 ek)

3 ek hardening önerisi:
1. **Soft-overlap formatı kesin şekilde tanımlansın** — "band 1 üst sınırı = band 2 alt sınırı + overlap_width", membership = linear interpolation. Sözlü tanım yetmez.
2. **Profile-relative payload magnitudes tablo halinde** — her payload key × her profile için ayrı entry. Numerics dosyasında compact tablo.
3. **Weighted blend cap order'ın 4 adımı isimlendirilsin** — kafa karışmasın. "event-cap → bootstrap blend → learned modulation → final clip" şeklinde literal.

"Yaz" hükmü.

### Halit final

> *"Kanka yaz. Bu üç ek, N'yi zayıflatmıyor; tersine ilk gerçek NUMERICS belgesini
> daha güvenli hale getiriyor. N — INGRESS_COMPILER_NUMERICS.md: belgeye dondurulabilir."*

---

## Çekirdek kararlar (omurga)

1. **Band cutoffs deterministic soft-overlap.** Linear membership function, fuzzy/LLM yok. hard ≤ low ≤ medium ≤ high ≤ hard.
2. **Profile-specific intensity caps anayasal hierarchy ile:**
   - `profile_cap.ObservationEvent`: ~1.00
   - `profile_cap.InternalShockEvent`: ~0.90 (refractory-protected)
   - `profile_cap.RecallEvent` verified: ~0.60
   - `profile_cap.HumanIntentEvent`: ~0.35
   - `profile_cap.RecallEvent` candidate: ~0.20
   - `candidate_recall_ratio` ≤ 0.35 (conceptual max)
3. **Payload seed base magnitudes profile-relative.** Her payload key'in 4 profile için ayrı baseline'ı. Tek sayı paylaşılmaz.
4. **Per-payload caps.** Suspicion/novelty/aversion/attraction/contradiction/urgency/memory_echo/fatigue_trace/pain_trace/reward_trace — her birinin profile-specific üst sınırı.
5. **Staleness scalar asymmetric:** yalnız dampens, never amplifies.
6. **Weighted blend cap order, 4 adım literal:**
   - (1) event-cap
   - (2) bootstrap blend
   - (3) learned modulation
   - (4) final clip
   - Forced re-normalization **yasak**.
7. **Learned mapping drift caps asymmetric:** weakening cap < strengthening cap. (False-positive dampening daha hızlı olmalı.)
8. **Fail-safe strict mode:** missing/invalid numerics → fail-open değil. M'nin default'ları aynen reuse.
9. **spec_family: ingress_compiler.** owning_spec_ref: `INGRESS_COMPILER_SPEC.md@v0.1`.
10. **20 violation test.**

---

## Madde 1 yansıması — numeric layer

Madde 1 ("tek mekanizma, çoklu imza") N'de iki kez yansıyor:
- **Tek compiler / 4 profile, ayrı caps.** Profile sınıfı türev değil; her birinin sayısal imzası farklı.
- **Tek payload palette / payload başına ayrı base magnitude.** Palette donmuş; ama her key'in her profile'da farklı baseline'ı var.

Madde 6 yansıması: **LLM numeric değer üretemez/değiştiremez** (violation test 18).

Madde 7 yansıması: Compiler M2'ye doğrudan yazmaz; numerics artifact M2'de **status referansı** olarak yaşar (M §3).

---

## Önemli sertleştirmeler

### Deterministic soft-overlap (mekanik)
Sınırlar hard cutoff değil — birbiriyle overlap eden iki band arasında linear
interpolation. Ama interpolation **deterministic**: aynı magnitude değeri her
zaman aynı membership vektörünü üretir. Fuzzy logic engine yok, LLM yok.

### Profile hierarchy sayısal olarak kanıtlandı
Sözlü hierarchy ("Observation > InternalShock > Recall > HumanIntent") A-L'de
geçiyordu ama sayısal kanıt yoktu. N'de cap değerleri kendi başlarına bu
hierarchy'i empoze ediyor. Anayasal sıra → sayısal sıra → davranış sırası.

### Refractory-protected InternalShock
InternalShock cap yüksek (~0.90) ama art arda atılamaz. Refractory window
bootstrap rule (D §17) ile birleşik. Yüksek cap × refractory = "şiddetli ama
nadir" → spam-proof.

### Staleness yalnız dampens
Asymmetry tek yönde: eski veri **az tonlu** olur, asla **fazla tonlu** olmaz.
Bu MEMORY_CONTRACT §11 staleness disciplini ile aynı yön.

### Weighted blend forced re-normalization yasak
Cap order'ın 4 adımı geçildikten sonra **toplam 1'e normalize edilmez**.
Re-normalization bir payload'ın diğerini boğmasına yol açabilir (semantik
winner). Mevcut weighted blend zaten caps altında; clip'ten sonra ne kalırsa o.

### Asymmetric drift caps
DEONTIC §18 (weakening human approval) ve REPLAY (dampening > strengthening)
yansıması. False-positive bir kanal hızla zayıflatılabilir; gerçek olduğu
sanılan bir kanal yavaş güçlendirilir. **Sistem yanlış pozitiften kaçar,
yanlış negatife düşer.**

### Fail-safe strict mode default'ları M'den
N kendi default'larını icat etmedi. Missing/invalid numerics durumunda
M (NUMERICS_GOVERNANCE) §11'in strict cap'leri devreye girer. Tek kaynak.

---

## Yan güncellemeler (commit'in parçası)

- `INGRESS_COMPILER_SPEC.md` §22 Open Questions: 5 soru için "kapandı, bkz N §X" referansları eklendi
- `WORLD_INGRESS.md` §15 cross-ref zaten N'i işaret ediyordu (görev gerek değil)
- `README.md` tamamlanmış listesine `INGRESS_COMPILER_NUMERICS.md` eklendi (M'nin altına)
- `README.md` sıradaki listesi NUMERICS belgeleri ile güncellendi

---

## Açık kalanlar (implementation'a devredildi)

- Drift detection threshold (exact)
- Cleanup window (deprecated → archived) süresi
- Asymmetry ratio kesin değerleri (kavramsal: weakening_cap < strengthening_cap)
- `INGRESS_NO_RULE_MATCH` event üretilsin mi (production noise tradeoff)
- Rule family versioning otomatik deprecate edilsin mi

Bunlar **N kapsamı dışında**; implementation veya ayrı bir spec'te netleşir.

---

## Sıradaki

A-M kapandı, N = ilk gerçek numerics artifact. **15 belge.** Conceptual phase
+ numeric governance + ilk numerics specifikasyonu hazır.

Sıradaki NUMERICS belgeleri (ChatGPT sıralaması, hepsi N'i kalıp alacak):
- O: `REPLAY_PROTOCOL_NUMERICS.md` — replay session caps, ablation budgets, eligibility-trace decay
- P: `MEMORY_WRITE_GATE_NUMERICS.md` — verification thresholds, status TTL
- Q: `OBSERVER_LEDGER_NUMERICS.md` — snapshot windows, sampling thresholds, segment sizes
- R: `BACKUP_STRATEGY_NUMERICS.md` — RPO/RTO, retention windows, restore timeout
- S: `BOOTSTRAP_GENOME_NUMERICS.md` — kesin genome parametreleri
- T: `RECALL_PROTOCOL_NUMERICS.md` — top-k boyutu, recall cooldown
- U: `ADAPTER_TRUST_NUMERICS.md` — trust score band'ları, decay rate

---

## Kilit cümleler

> **Ingress compiler numerics, dış dünyanın çekirdeğe hangi şiddette dokunabileceğinin sayısal sözleşmesidir.**
>
> **Dünya güçlü olabilir. Ama hiçbir dış kanal çekirdeğe sınırsız ton basamaz.**
>
> **Adapter raw event üretir. Compiler neural_seed üretir. Numerics compiler'ın duyusal şiddet sınırlarını belirler.**
>
> **Observation en açık kanal, Candidate Recall en kapalı kanal. Hierarchy sözlü değil, sayısal.**
>
> **Sistem yanlış pozitiften kaçar, yanlış negatife düşer.**
>
> **Staleness yalnız dampens. Eski veri az tonlu olabilir; asla fazla tonlu olamaz.**
>
> **Weighted blend forced re-normalization yapmaz. Caps geçildikten sonra ne kalırsa o.**
>
> **Numerics yoksa kanal serbest değil; M'nin strict default'ları devreye girer.**
