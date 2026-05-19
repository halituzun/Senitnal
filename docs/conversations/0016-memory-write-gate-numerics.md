# 0016 — Memory Write Gate Numerics

> Bu dosya `MEMORY_WRITE_GATE_NUMERICS.md` (v0.1, P turu) ortaya çıkmadan önce
> yapılan üçlü tasarım konuşmasının (Halit + Claude + ChatGPT) sıkıştırılmış
> özetidir. **Üçüncü numerics artifact'inin** soyağacı.
>
> A-O: 0001-0015

---

## Tarih
2026-05-19 (O → P geçişi, üçüncü numerics specifikasyonu)

## Bağlam

N (INGRESS_COMPILER) ve O (REPLAY_PROTOCOL) numerics donmuş. P doğrudan G'nin
(MEMORY_WRITE_GATE) numerics artifact'i; epistemik fren sayısallaşıyor.

ChatGPT'nin damıtması:

> *"P, hafızaya gerçekmiş gibi yazma hakkının sayısal sözleşmesidir."*

Tek cümle: **P = epistemik fren sözleşmesidir.**

P'nin üç riski sayısal olarak çözmesi gerek:
- Gevşek eşik → self-deception
- Sert eşik → epistemic paralysis (hiçbir şey verified olamaz)
- Tek-yön cap → verified sticky değil, tek karşı kanıtla devrilir

Ayrıca P, O'nun açık bıraktığı **outcome_alignment.max_wait_ms staleness
dependency**'sini canonical bağa dönüştürecek.

---

## Başlangıç pozisyonları

### ChatGPT (Halit'in vekili, açılış)

7 ana çapa:
1. Subject class TTL matrix (candidate_max_age, quarantine_max_age, staleness_threshold, refresh_required, default_expiry_behavior)
2. Evidence minimumları (causal_refs, cross_source, observation_count, outcome_alignment, replay_survival, external_corroboration per subject_class × axis)
3. Contradiction threshold band'leri (clear → mild → moderate → high → critical)
4. Self-deception risk numerics (internal_only_ref_ratio, external_corroboration_min_count, narrative/causal/rationale için sıkı)
5. Replay survival vs outcome alignment (O zaten global'ı kilitledi; P verification matrix'e bağlanacak)
6. Status transition thresholds (candidate↔verified↔quarantined↔superseded↔expired/rejected)
7. Human-write numerics (auto-verified vs matrix-required; world_claim hard invariant)

P'nin canonical staleness kaynağı olma önerisi:
- P = kayıt epistemik olarak taze mi?
- T = recall hangi yoğunlukla, ne sıklıkla döner?

### Claude (7 çapaya cevap + 1 ek çapa + staleness ownership netleştirme)

**Çapa 1 ek:** `quarantine_max_age >= candidate_max_age` invariant +
`refresh_required_window_ms`.

**Çapa 2 ek:** G-bridge (matrix row var ama numeric yok → artifact REJECT);
temporal separation for "independent" observations.

**Çapa 3 ek:** **verified stickiness asimetrisi** — demote eşiği promote
eşiğinden yüksek (DEONTIC §18 epistemic karşılığı).

**Çapa 5 ek:** O-bridge global cap; subject-spesifik replay disable
constitutional immutable (`{min: 0, max: 0}`).

**Çapa 7 ek:** whitelist enum NumericEntry directionality; world_claim
ayrımı hard invariant.

**Ek Çapa 8 (Claude önerisi):** numerics_artifact_reference için en kısa
candidate_max_age (sistem strict mode'dan hızla çıkmalı).

**Staleness ownership:** P canonical source
(`epistemic_staleness_threshold_ms.<sc>`); T sonradan recall-side
numeric'lerini ekler; O dependency P'de kapanır.

### ChatGPT (kabul + 6 düzeltme + "yaz")

**Düzeltme 1:** `refresh_required_window_ms` directionality YANLIŞ — Claude
"higher_is_stricter" yazmıştı ama gerekçe "uzun pencere = az refresh = trust
decay yavaşlar" idi, yani gevşeme. Doğru: **lower_is_stricter**.

**Düzeltme 2:** `quarantine >= candidate` global invariant değil,
**subject-spesifik**. source_trust/adapter_trust için quarantine ≥
candidate; narrative_claim/causal_explanation/decision_rationale için
quarantine ≤ candidate (self-deception riski, hızlı karar).

**Düzeltme 3:** enum_set convention M governance'a eklenmeli:
- increase = set expansion
- decrease = set contraction

**Düzeltme 4:** Contradiction stickiness aynen taşınsın — çok güçlü disiplin.

**Düzeltme 5:** P ↔ O bridge dependency declaration'larda explicit yazılsın:
- per subject: `replay_survival_weight < outcome_alignment_weight`
- global: `max(replay_survival_weight.*) ≤ O.max_replay_survival_weight_in_verification`

**Düzeltme 6:** Staleness ownership ayrımı temiz — P canonical, T recall-side.

"Yaz" hükmü.

### Halit final

> *"Yaz. Bu çapa turu yeterince yakınsamış. P artık belgeye dondurulabilir."*

---

## Çekirdek kararlar (16 omurga)

1. P runtime config değildir; signed artifact + M2 reference.
2. P, Memory Write Gate'in sayısal epistemik frenidir.
3. Her subject_class için ayrı TTL / evidence / contradiction / staleness eşiği vardır.
4. G matrix row'u olan her (subject, axis) çifti P'de NumericEntry'e karşılık gelir (G-bridge).
5. Numeric threshold olmayan (subject, axis) çifti verified üretmez.
6. Candidate sonsuza kadar yaşayamaz; quarantined sonsuza kadar yaşayamaz.
7. TTL ilişkisi subject-spesifik; global "quarantine >= candidate" invariant YOK.
8. `refresh_required_window_ms` lower_is_stricter (uzun pencere = gevşeme).
9. Contradiction band'leri asymmetric: demote_required > promote_max (verified stickiness).
10. `supersede_confidence_delta_min > 0` zorunlu (tek gözlem verified rekoru devirmez).
11. Self-explanation is not proof; internal-only refs verified için tek başına yetmez.
12. `max(replay_survival_weight.*) <= O global cap` (P → O bridge); per subject < outcome_alignment.
13. Constitutional-immutable subject'ler (deontic_policy, incident, adapter_trust, numerics_artifact_reference) için `replay_survival_weight = 0` allowed_range {min:0, max:0}.
14. Human write otomatik dünya hakikati değildir; auto_verified ∪ matrix_required = universe.
15. `numerics_artifact_reference` candidate TTL en kısa olmalı; verified human signature gerek.
16. Missing numerics → strict_no_verified mode (verified üretimi DISABLED, audit-safe).

---

## Madde yansımaları

### Madde 1 — asimetri her yerde (üç yeni asimetri)
N'de "yanlış pozitiften kaçar, yanlış negatife düşer" asimetrisi vardı.
O'da "weakening > strengthening" + "outcome > replay" vardı. P üç yeni
asimetri ekledi:
- **Verified stickiness:** demote eşiği > promote eşiği
- **Internal vs external:** internal_only refs verified için tek başına yetmez
- **False-merge > false-split:** duplicate_match_threshold tightening yönünde
  imzalı (information loss false-merge'den gelir)

### Madde 6 — LLM numeric değiştiremez (violation test 28)
P numerics LLM tarafından üretilemez veya değiştirilemez.

### Madde 7 — hafıza ayrılığı
P doğrudan M2 verification freni. G silent gate principle'ını numeric
seviyede de korur — eşikler "yumuşatılamaz", her gevşeme `safety_weakening`
+ human approval.

---

## Önemli sertleştirmeler

### G-bridge — verification matrix completeness
"G matrix row'u var ama P numeric'i yok" durumu artifact reject. Bu N'de
profile_cap completeness'inin, O'da N drift bridge'inin analogu. Üç
numerics artifact arasında tutarlı disiplin: spec mekanizması ile numeric
artifact arasında **birebir matching zorunlu**.

### Verified stickiness asimetrisi
Yeni disiplin. Verified bir kayıt sticky'dir; tek karşı kanıtla devrilmez.
Bu finansal hafızada **kritik**: sistem bir kaydı verified yaptıysa, ufak
gürültüyle devrilmesi kararsızlık üretir. DEONTIC §18'in epistemic karşılığı.

### Subject-spesifik TTL dependency
Bütün subject'ler için tek invariant yok. Self-deception riskli class'larda
quarantine'ı candidate'tan **kısa** tutmak (hızlı karar) hayati. Insan-bekleyen
class'larda quarantine candidate'tan **uzun** olabilir (review süresi).

### enum_set convention M'ye eklendi
P §18 `auto_verified_human_subject_classes` ihtiyacı M §8 schema'sını
genişletti. Convention: set expansion = increase, contraction = decrease.
Directionality semantiği aynen korunuyor.

### O staleness dependency P'de canonical kapandı
O §15'in "şimdilik conceptual, ilgili artifact yazıldığında canonical" notu
artık `epistemic_staleness_threshold_ms.<subject_class>` ile bağlandı.
O artifact'inde sadece bir line edit (conceptual → computed_less_than_or_equal).
T yazıldığında recall-side staleness numeric'leri eklenir ama P canonical
kaynak kalır.

### L bridge — self-deception sayısallaştı
L §10'da kavramsal olan `internal_only_refs` / `external_corroboration_refs`
ayrımı P §16'da `max_internal_only_ref_ratio.<subject_class>` ve
`external_corroboration_min_count.<subject_class>` olarak sayısal.
Self-deception-prone subject'ler için (narrative/causal/rationale)
`external_corroboration_min_count >= 1` zorunlu.

### Constitutional immutable replay disable
O §19'da `replay_can_trigger_replay_max_chain_depth = 0` allowed_range
{min:0, max:0} pattern'i vardı. P §17'de bu pattern üç subject_class için
replay_survival_weight = 0'da kullanıldı:
- deontic_policy (human approval gerek)
- incident (gerçek outcome gerek)
- adapter_trust (signed manifest + audit gerek)
- numerics_artifact_reference (human signature gerek)

Bu sınıflar için "replay ile verified olunamaz" sayısal olarak kilitli.

### Human-write whitelist enum_set
auto-verified human subject'ler kapalı bir liste. Genişlemesi safety_weakening.
World_claim ayrımı hard invariant: Halit yazdı = beyanı kayda geçti; dünya
iddiası olarak auto-verified yapılmaz.

---

## Yan güncellemeler (commit'in parçası)

- `MEMORY_WRITE_GATE.md` §8 (verification matrix) / §10 (evidence requirements)
  / §13 (self-deception) cross-ref to P
- `REPLAY_PROTOCOL_NUMERICS.md` §15 outcome_alignment.max_wait_ms cross-artifact
  dependency artık canonical (P §8 → epistemic_staleness_threshold_ms);
  §21 dependency matrix güncellendi; §25 open question kapandı
- `NUMERICS_GOVERNANCE.md` §8 NumericEntry schema'sına enum_set / band_name unit
  tipleri ve enum_set convention eklendi (P §18 ihtiyacı)
- `MEMORY_CONTRACT.md` §9 (epistemic test seti) blok-quote'una P cross-ref
- `README.md` completed listesine MEMORY_WRITE_GATE_NUMERICS eklendi
- `docs/conversations/0016-memory-write-gate-numerics.md` eklendi

Yeni canonical event gerekmedi; P `MEMORY_RECORD_STATUS_CHANGED` (G §15) +
M lifecycle event'lerini reuse ediyor, reason field discipline ile.

---

## Açık kalanlar (implementation veya sonraki numerics artifact'lere devredildi)

- Recall-side staleness numerics → T (RECALL_PROTOCOL_NUMERICS)
- Trust decay function shape (linear vs exponential vs step) → implementation
- deontic_policy verified eşikleri için human approval signature schema → DEONTIC numerics veya implementation
- Foreign provenance recovery path → L §17 ile koordine
- numerics_artifact_reference için multi-signature requirement → M §13 open question
- Drift detection threshold (band cutoff "yeterince değişti" eşiği) → implementation
- Subject_class taksonomisinin genişlemesi → B §3 spec revision

Bunlar **P kapsamı dışında**; implementation veya sonraki numerics artifact'lerde
netleşir.

---

## Sıradaki

A-O + P kapandı. **17 belge.** Conceptual phase + 3 numerics artifact tamam.

Sıradaki NUMERICS belgeleri (kalan):
- Q: `OBSERVER_LEDGER_NUMERICS.md` — snapshot windows, sampling thresholds,
  segment sizes, permanence_policy TTL
- R: `BACKUP_STRATEGY_NUMERICS.md` — RPO/RTO, retention windows, restore timeout
- S: `BOOTSTRAP_GENOME_NUMERICS.md` — kesin genome parametreleri, sleep cycle
  matematiği, plasticity state transitions, fatigue recovery (O §6 ile bağ)
- T: `RECALL_PROTOCOL_NUMERICS.md` — top-k candidate set boyutu, recall cooldown,
  recall-side staleness (P canonical kaynak)
- U: `ADAPTER_TRUST_NUMERICS.md` — trust score band'ları, decay rate'leri

---

## Kilit cümleler

> **Memory Write Gate numerics, hafızaya gerçekmiş gibi yazma hakkının sayısal sözleşmesidir.**
>
> **Sistem kendi açıklamasını üretebilir. Ama kendi açıklamasını kanıt sayamaz.**
>
> **Self-explanation is not proof. Internal-only refs cannot satisfy verification alone.**
>
> **Halit yazdı = Halit'in beyanı kayda geçti. Halit yazdı ≠ dünya iddiası otomatik doğru.**
>
> **Verified status sticky'dir. Tek yeni karşı kanıtla devrilmez.**
>
> **O, replay evidence'ın global tavanıdır. P, subject_class bazlı dağılımıdır.**
>
> **Numerics yoksa Memory Write Gate daha serbest değil; verified üretimi tamamen kapalı.**
>
> **N dış dünyanın hakkını sınırlar.**
> **O kendi geçmişine girme hakkını sınırlar.**
> **P hafızaya emin olma hakkını sınırlar.**
