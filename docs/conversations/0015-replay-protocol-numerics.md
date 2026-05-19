# 0015 — Replay Protocol Numerics

> Bu dosya `REPLAY_PROTOCOL_NUMERICS.md` (v0.1, O turu) ortaya çıkmadan önce
> yapılan üçlü tasarım konuşmasının (Halit + Claude + ChatGPT) sıkıştırılmış
> özetidir. **İkinci numerics artifact'i** — O'nun soyağacı.
>
> A-N: 0001-0014

---

## Tarih
2026-05-19 (N → O geçişi, ikinci numerics specifikasyonu)

## Bağlam

N (INGRESS_COMPILER_NUMERICS) kapandı: ilk gerçek numerics artifact dondu.
Patch turu (a71320e) sonrası M dependency enum genişledi, canonical key
naming standardize oldu, per-payload cap unit resolution çözüldü,
`membership_function_type` NumericEntry oldu, staleness wording sertleşti.

Sıradaki: K (REPLAY_PROTOCOL) numerics artifact'i.

ChatGPT'nin damıtması doğru omurgayı verdi:

> *"N dış dünyanın çekirdeğe hangi şiddette dokunacağını sınırlıyordu;
> O ise sistemin kendi geçmişini ne kadar kurcalayabileceğini sınırlayacak.
> Bu yüzden O, N'den daha hassas."*

Tek cümle: **O = geçmişi kurcalama hakkının sayısal sözleşmesi.**

Replay numerics, eğer disipline edilmezse, çok somut tehlikeler taşır:
- `replay_budget` sessizce artar → ruminasyon
- Ablation branch'leri çoğalır → alternatif tarih simülasyonu
- Replay survival weight verification'da baskın olur → self-confirmation döngüsü
- Outcome alignment penceresi uzar → stale outcome ile kanıt
- Replay başka replay'i tetikler → recursive amplification

---

## Başlangıç pozisyonları

### ChatGPT (Halit'in vekili, açılış)

Manifesto:
> *Replay numerics runtime config değildir.*
> *Replay numerics, sistemin geçmişi ne kadar yeniden sınayabileceğinin sayısal sözleşmesidir.*

5 ana çapa:
1. Replay budget directionality (session_duration / events_per_session / counterfactual_branches / cooldown)
2. Counterfactual branch limit (single/pairwise/higher-order)
3. Replay update caps (per_synapse_strengthening, per_synapse_weakening, aggregate, eligibility trace)
4. Replay survival threshold ≠ truth (min_score, min_sessions, max_weight)
5. Outcome alignment window (min_wait, max_wait, lag_window, outcome_ref_count)

12 kırmızı çizgi.

### Claude (5 çapaya cevap + 2 ek çapa)

5 çapaya pozisyon:
1. `max_session_duration_ms` için **bidirectional_sensitive** önerildi (kısa = öğrenme ölür)
2. `higher_order_ablation_max_order > 2` artışı sıradan weakening değil → **yeni change_class veya hard immutable** öneri
3. M0 caps + asimetri dependency + N-bridge (`ingress_calibration_replay_delta_cap ≤ N.per_mapping_daily_delta_cap × 0.30`) eklendi
4. `min_replay_survival_sessions ≥ 2` + `min_session_separation_ms` — ardışık replay'ler self-confirmation
5. `max_wait_ms` staleness threshold ile dependency + external outcome_ref hard rule

İki yeni çapa:
- **Çapa 6:** Çift cap (per_cycle + per_24h_window), restore sonrası budget reset YOK
- **Çapa 7:** `replay_can_trigger_replay_max_chain_depth = 0` constitutional immutable

### ChatGPT (kabul + 4 düzeltme + "yaz")

Mimari kabul. Ama M governance enum/metadata uyumu için 4 düzeltme:

**Düzeltme 1 — max_session_duration_ms directionality**
`bidirectional_sensitive` yerine **lower_is_stricter** + `allowed_range.min`
ile minimum useful duration koruması. Çünkü bidirectional_sensitive iki yönde
de behavior bound demektir; "kısa = öğrenme ölür" sorunu numeric sınır değil,
`allowed_range.min` sorunu.

**Düzeltme 2 — higher_order_ablation forbidden enum**
Claude'un önerdiği `forbidden_in_v0_1` yerine M canonical enum'undaki
**`forbidden`** kullanılsın. Rationale alanı v0.1 constitutional invariant'ı
açıklasın: "Changing this requires REPLAY_PROTOCOL.md revision, not numeric
artifact update."

**Düzeltme 3 — outcome_alignment.max_wait_ms cross-artifact dep**
Henüz `memory_contract.staleness_threshold_ms` canonical key olarak
yazılmadığı için doğrudan dependency erken; **conceptual dependency** olarak
yaz, canonical bağ RECALL_PROTOCOL_NUMERICS veya MEMORY_WRITE_GATE_NUMERICS
yazıldığında kurulsun.

**Düzeltme 4 — outcome_must_be_external NumericEntry değil**
Numeric değil, **protocol invariant** olarak yaz. Hard rule, deklaratif kural.

"Yaz" hükmü.

### Halit final

> *"Kanka, O'yu yaz. Bu çapa turu yeterince yakınsamış. O artık belgeye
> dondurulabilir. Özellikle şu cümle doğru omurga: O = geçmişi kurcalama
> hakkının sayısal sözleşmesi."*

---

## Çekirdek kararlar (14 omurga)

1. Replay numerics runtime config değildir; signed artifact + M2 reference.
2. Replay budget artışı = safety_weakening (tüm budget key'leri lower_is_stricter).
3. `max_session_duration_ms` lower_is_stricter; allowed_range.min ile minimum useful duration.
4. Çift cap: `max_sessions_per_cycle` + `max_sessions_per_24h_window` (computed dependency).
5. Restore sonrası budget reset YOK; M1 segment'inden devralma (L forgetting attack defense numerics yansıması).
6. `higher_order_ablation_max_order = 2` v0.1 constitutional invariant; `change_class_if_increased: forbidden` (M canonical enum).
7. Pairwise ablation `causal_link_score_min` eşiği + `max_pairwise ≤ max_single × 0.5` (computed_less_than_or_equal).
8. M0 update asimetri: `per_synapse_strengthening_cap ≤ per_synapse_weakening_cap` (computed dependency); aggregate session cap.
9. Eligibility trace window dışı sinaps update yasak.
10. N bridge: `ingress_calibration_replay_delta_cap ≤ N.per_mapping_daily_delta_cap × 0.30` (back-door koruması).
11. Replay survival ≠ truth: min 2 bağımsız session, min_session_separation_ms, self-confirmation guard.
12. `max_replay_survival_weight_in_verification < outcome_alignment_weight_in_verification` (real evidence dominance).
13. `replay_can_trigger_replay_max_chain_depth = 0` allowed_range {min: 0, max: 0} constitutional immutable.
14. Missing numerics → strict audit-safe mode (fail-open yasak; sadece outcome_alignment read-only çalışır).

---

## Madde yansımaları

### Madde 1 — asimetri her yerde
N'nin "sistem yanlış pozitiften kaçar, yanlış negatife düşer" asimetrisi
O'da üç kez yansıyor:
- `per_synapse_strengthening_cap ≤ per_synapse_weakening_cap`
- `max_replay_survival_weight < outcome_alignment_weight`
- Per-channel rate invariant (§18): her replay update channel'da
  weakening_rate ≥ strengthening_rate

### Madde 6 — LLM numeric değiştiremez (violation test 20)
Replay numerics LLM tarafından üretilemez veya değiştirilemez.

### Madde 7 — hafıza ayrılığı
Replay M2'ye doğrudan yazamaz; replay survival weight M2 verification
matrix'inde **sınırlı ağırlıkta** ve outcome'tan **kesinlikle zayıf**.

---

## Önemli sertleştirmeler

### Çift cap + restore continuity
Forgetting attack defense (L §22) numerics seviyesinde devam ediyor.
Restore sonrası "tertemiz budget" ile replay spam kapısı kapanıyor.
`max_sessions_per_cycle` + `max_sessions_per_24h_window` sayaçları M1
segment'inden okunup devam ediyor.

### Constitutional immutable: chain_depth = 0
M'nin `allowed_range` mekanizması `{min: 0, max: 0}` ile constitutional
invariant'a dönüşüyor. Tek değer, değiştirilemez, hem increase hem decrease
`forbidden`. Recursive replay = self-amplification loop.

### Higher-order ablation forbidden change_class
ChatGPT'nin düzeltmesiyle M canonical enum'undaki `forbidden` kullanılıyor.
v0.1'de `higher_order_ablation_max_order > 2` artışı tek artifact + human
approval ile geçilemez; REPLAY_PROTOCOL.md spec revision gerek (constitutional
amendment). Bu çok kritik bir disiplin — replay'in K kapsamı dışına çıkma yolu
kapatıldı.

### N bridge — replay N'i back-door'dan gevşetemez
`ingress_calibration_replay_delta_cap ≤ N.per_mapping_daily_delta_cap × 0.30`
computed dependency. Replay'in compiler'a etkisi her zaman N'in kendi günlük
drift cap'inin altında. Bu O'nun en kritik dependency'lerinden biri — iki
numerics artifact arası anayasal köprü.

### Real evidence dominance numeric
`max_replay_survival_weight_in_verification < outcome_alignment_weight_in_verification`
sadece kural değil, dependency. Replay survival evidence yardımcı,
outcome alignment evidence baskın.

### External outcome zorunluluğu
`outcome_must_be_external = true` hard rule. Internal-only outcome_ref
alignment'a katkı sağlamaz. L §10 internal_only_refs / external_corroboration_refs
disiplini buraya da uygulanıyor.

### Fail-safe strict audit-safe mode
M'nin fail-open yasağı O'da somut bir mod tanımı: replay disabled except
audit-safe (sadece outcome_alignment_analysis read-only). Sleep/synapse,
habituation, calibration, verification update tamamen kapalı.

---

## Yan güncellemeler (commit'in parçası)

- `REPLAY_PROTOCOL.md` §9 (Replay Budget) / §15 (Counterfactual Ablation) /
  §16 (Survival Score) için O cross-ref eklendi
- `BACKUP_STRATEGY.md` RestoreManifest bölümüne replay budget continuity
  cross-ref (restore sonrası reset YOK)
- `INGRESS_COMPILER_NUMERICS.md` §18 (Learned Mapping Drift Caps) back-reference
  to O §13 (replay N drift cap'in 0.30'unu aşamaz)
- `MEMORY_WRITE_GATE.md` §11 (replay/outcome evidence axis) için O §14, §17
  cross-ref (weight dependency)
- `README.md` completed listesine REPLAY_PROTOCOL_NUMERICS eklendi;
  sıradaki listesi güncellendi
- `docs/conversations/0015-replay-protocol-numerics.md` eklendi

Yeni canonical event gerekmedi; M zaten numerics lifecycle eventlerini
tanımladı, O onları reuse ediyor.

---

## Açık kalanlar (implementation veya sonraki numerics artifact'lere devredildi)

- Replay drift detection threshold (exact)
- Production değerler için signed artifact içeriği
- Sleep cycle ile fatigue recovery'nin tam matematiği → S (BOOTSTRAP_GENOME_NUMERICS)
- Outcome alignment staleness threshold canonical kaynağı → P veya T
- Replay cycle boundary tanımı (cycle nerede başlar/biter) → S
- Higher-order ablation'a izin verecek constitutional amendment paths → REPLAY_PROTOCOL.md v0.2

Bunlar **O kapsamı dışında**; implementation veya sonraki numerics artifact'lerde
netleşir.

---

## Sıradaki

A-N + O kapandı. **16 belge.** Conceptual phase + 2 numerics artifact tamam.

Sıradaki NUMERICS belgeleri (ChatGPT sıralaması, N + O kalıbını alacak):
- P: `MEMORY_WRITE_GATE_NUMERICS.md` — verification thresholds, status TTL'ler,
  candidate_max_age per subject_class, quarantine_max_age, evidence count
  minimums, contradiction threshold; outcome alignment staleness threshold
  canonical key burada netleşebilir
- Q: `OBSERVER_LEDGER_NUMERICS.md` — snapshot windows, sampling thresholds,
  segment sizes, permanence_policy TTL
- R: `BACKUP_STRATEGY_NUMERICS.md` — RPO/RTO, retention windows, restore timeout
- S: `BOOTSTRAP_GENOME_NUMERICS.md` — kesin genome parametreleri, sleep cycle
  matematiği, plasticity state transitions
- T: `RECALL_PROTOCOL_NUMERICS.md` — top-k candidate set boyutu, recall cooldown
- U: `ADAPTER_TRUST_NUMERICS.md` — trust score band'ları, decay rate'leri

---

## Kilit cümleler

> **Replay numerics, sistemin geçmişi ne kadar yeniden sınayabileceğinin sayısal sözleşmesidir.**
>
> **Replay geçmişten kanıt üretir.**
> **Ama geçmişi yeniden yaşatamaz, kendi kanıtını hakikat sayamaz, ve kendini tekrar tetikleyemez.**
>
> **Replay budget artarsa sistem daha zeki olmaz; ruminasyona daha açık olur.**
>
> **Recursive replay = self-amplification loop. Constitutional zero.**
>
> **Real outcome > replay survival. Her zaman. Sayısal olarak.**
>
> **Replay survival evidence yardımcıdır. Outcome alignment evidence baskındır.**
>
> **Numerics yoksa replay daha serbest değil; audit-safe mode'a düşer.**
>
> **N dış dünyanın hakkını sınırlar. O kendi içine girme hakkını sınırlar.**
>
> **Tightening kolay olabilir; weakening asla kolay olmamalı — replay rate'leri bu yönde imzalı.**
