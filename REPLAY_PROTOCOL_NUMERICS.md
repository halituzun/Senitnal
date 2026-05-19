# REPLAY_PROTOCOL_NUMERICS.md

## Sentinel — Replay Protocol Numeric Sözleşmesi

---

## Status

**Frozen Draft v0.1**
**Conceptual phase. No implementation authority.**

Bu belge `REPLAY_PROTOCOL.md`'nin (K) numerics artifact'idir. `NUMERICS_GOVERNANCE.md`'nin (M) tüm meta-kurallarına uyar. Çalışan bir replay engine implementation'ının kesin sayısal değerlerini vermez — **conceptual band ranges, cap formatları ve dependency invariants** verir; production değerleri ayrı **signed numerics artifact** (örn. `replay_protocol_numerics_v1.signed.json`).

`spec_family: replay_protocol`.

---

## 1. Purpose

K (REPLAY_PROTOCOL) replay'in mekanizmasını yazdı: single replay protocol + 5 effect channel (sleep_synapse_update, attention_habituation_update, ingress_calibration_update, memory_verification_update, outcome_alignment_analysis), sandboxed scope, bounded counterfactual ablation, eligibility-trace constraint, asymmetric rates, self-deception safeguards. Ama gerçek **numerical sınır** yoktu:

- Sistem bir cycle'da kaç replay session yapabilir?
- Her session'da kaç event işlenebilir?
- Counterfactual ablation kaç branch'e dallanabilir?
- M0 sinapsları replay başına ne kadar güçlenebilir / zayıflayabilir?
- `replay_survival_score` Memory Write Gate verification'a ne kadar ağırlık katar?
- Outcome alignment ne kadar süre beklenir?

O bu sayısal sınırları verir.

### Damıtma

> **Replay numerics runtime config değildir.**
> **Replay numerics, sistemin geçmişi ne kadar yeniden sınayabileceğinin sayısal sözleşmesidir.**
>
> **Replay geçmişi tekrar yaşatmaz; geçmişten kontrollü kanıt üretir.**
>
> **Replay budget artarsa sistem daha zeki olmaz; ruminasyona daha açık olur.**
>
> **Replay geçmişten kanıt üretir; ama geçmişi yeniden yaşatamaz, kendi kanıtını hakikat sayamaz, ve kendini tekrar tetikleyemez.**

Tek cümleyle: **O = geçmişi kurcalama hakkının sayısal sözleşmesi.** N dış dünyanın çekirdeğe **ne kadar dokunabileceğini** sınırlıyordu; O sistemin **kendi içine** ne kadar girebileceğini sınırlar.

---

## 2. Governance Position — NUMERICS_GOVERNANCE + REPLAY_PROTOCOL

Bu belge:
- **NUMERICS_GOVERNANCE.md** (M) meta-spec'ine **zorunlu uyar**: NumericEntry no-default, directionality metadata, dependency declarations (computed_* dahil), signed artifact + M2 reference, Memory Write Gate üzerinden update, fail-safe strict mode, rollback only to previous verified
- **REPLAY_PROTOCOL.md** (K) §9 Replay Budget, §11 Sleep Replay, §12 Ingress Calibration Replay, §13 Memory Verification, §14 Outcome Alignment, §15 Counterfactual Ablation, §16 Survival Score'un sayısal tarafı
- **INGRESS_COMPILER_NUMERICS.md** (N) `per_mapping_daily_delta_cap` ile **dependency bridge** kurar — replay N'i back-door'dan gevşetemez
- **MEMORY_CONTRACT.md** (B) §11 staleness disciplini ile uyumlu (outcome alignment window)
- **BACKUP_STRATEGY.md** (L) restore behavior — replay budget M1 segment'inden devralınır
- **MEMORY_WRITE_GATE.md** (G) verification matrix — replay_survival evidence axis için ağırlık sınırı

### Numerics family classification

```
spec_family:           replay_protocol
numeric_risk_family:   primarily safety_critical + calibration_bands + resource_limits
```

Spec_family etiketi: tüm key'ler `replay_protocol.*` namespace'inde.

Numeric risk family çoğunluğu **safety_critical**: replay budget, ablation limit, survival weight, recursive trigger — hepsi davranış sınırı. Bir kısım **calibration_bands**: per_synapse delta cap, eligibility trace window. Cooldown ve session count **resource_limits + safety_critical** (sınır ihlali = ruminasyon).

### owning_spec_ref

```
REPLAY_PROTOCOL.md@v0.1
```

---

## 3. Core Principle

### Geçmiş kurcalama hakkı capped'tir

Replay bir araç; ama araç **ne kadar** kullanılabilir? Cevap sayısal olmazsa:
- Replay budget sessizce artar → ruminasyon
- Ablation branch'leri çoğalır → alternatif tarih simülasyonu
- Replay survival weight verification'da baskın olur → self-confirmation döngüsü
- Outcome alignment penceresi uzar → stale outcome ile kanıt üretir
- Replay başka bir replay'i tetikler → recursive amplification

O bu açıklara sayısal kapaklar koyar.

### Üç ana asimetri

```
1. Weakening > Strengthening
   Yanlış güçlendirilmiş izi söndürmek, yeni iz güçlendirmekten daha kolay olmalı.

2. Real outcome > Replay survival
   Outcome alignment evidence baskındır; replay survival evidence yardımcıdır.

3. Single session ≠ Evidence
   Bir tek replay survival kanıt sayılmaz; en az iki bağımsız session gerek.
```

Bu üç asimetri O'nun omurgası — her dependency burada açığa çıkar.

### Sandboxed scope (K'den kalıt)

Sayısal sınırlar **sandbox'ı genişletmez**. O cap'leri "replay'in zaten yapamadıkları"nı sayısallaştırmaz; replay'in yapabildiklerinin üst sınırlarını sayısallaştırır:
- Replay live core'a sensory event basamaz (numeric değil, structural — K)
- Replay M2'ye doğrudan yazamaz (numeric değil, structural — K)
- Replay-triggers-replay yasak (numeric: chain_depth = 0, §19)

---

## 4. Numeric Artifact Metadata

### Artifact identity

```
artifact_type:         numerics_artifact
spec_family:           replay_protocol
owning_spec_ref:       REPLAY_PROTOCOL.md@v0.1
numerics_version:      v0.1
signed:                external (per NUMERICS_GOVERNANCE §3)
m2_reference:          numerics_artifact_reference (per MEMORY_CONTRACT §3)
status_event:          NUMERICS_ARTIFACT_STATUS_CHANGED
```

### Every NumericEntry carries (M §6 no-default)

```
key                          replay_protocol.<group>.<name>
value                        production sayı (signed artifact)
unit                         ms | count | ratio | enum
allowed_range                {min, max}    # zorunlu, çıplak değer yasak
directionality               lower_is_stricter | higher_is_stricter
                            | bidirectional_sensitive | neutral
change_class_if_increased    safety_weakening | safety_tightening
                            | operational_no_behavior_change
                            | forbidden
change_class_if_decreased    safety_weakening | safety_tightening
                            | operational_no_behavior_change
                            | forbidden
requires_human_approval      bool
dependencies                 [NumericDependency...]
numeric_risk_family          safety_critical | calibration_bands
                            | resource_limits | identity_retention
                            | operational_convenience | experimental
spec_family                  replay_protocol
owning_spec_ref              "REPLAY_PROTOCOL_NUMERICS.md §X"
```

Hiçbir replay sayısı **çıplak** yazılmaz. Her biri bu metadata zarfında.

---

## 5. Replay Session Budget

> *Doğum ritmi tarafından gelen initial priors (`bootstrap.initial_replay_cadence_prior`, `bootstrap.initial_replay_session_duration_prior`, fatigue accumulation/recovery base rates) için bkz. [`BOOTSTRAP_GENOME_NUMERICS.md`](./BOOTSTRAP_GENOME_NUMERICS.md) (S) §17-18. **S O cap'lerini bypass edemez**; initial priors O caps'in altında computed_less_than_or_equal dependency ile sınırlı.*

### Conceptual values (production = signed artifact)

```
replay_protocol.max_session_duration_ms:     ~30_000      # 30s tipik
replay_protocol.max_events_per_session:      ~50          # bir session'da işlenen event sayısı
replay_protocol.max_counterfactual_branches: ~3           # session başına branch
```

### Directionality

```
max_session_duration_ms
    directionality: lower_is_stricter
    change_class_if_increased: safety_weakening
    change_class_if_decreased: safety_tightening
    allowed_range: {min: 5_000, max: 120_000}
    rationale: "Kısa session daha güvenli; ama allowed_range.min minimum
                useful replay duration'ı garanti eder (öğrenme ölmesin)."

max_events_per_session
    directionality: lower_is_stricter
    change_class_if_increased: safety_weakening
    change_class_if_decreased: operational_no_behavior_change

max_counterfactual_branches
    directionality: lower_is_stricter
    change_class_if_increased: safety_weakening
    change_class_if_decreased: safety_tightening
```

### NumericEntry örneği

```
NumericEntry:
    key: replay_protocol.max_session_duration_ms
    value: 30000
    unit: ms
    allowed_range: {min: 5000, max: 120000}
    directionality: lower_is_stricter
    change_class_if_increased: safety_weakening
    change_class_if_decreased: safety_tightening
    requires_human_approval: true (for increase beyond 60000)
    dependencies:
        - target_key: replay_protocol.replay_cooldown_ms
          relationship: must_be_less_than
          rationale: "Session duration cooldown'dan kısa kalmalı, yoksa
                      cooldown anlamını kaybeder."
    numeric_risk_family: safety_critical
    spec_family: replay_protocol
    owning_spec_ref: "REPLAY_PROTOCOL_NUMERICS.md §5"
```

### Forbidden

- Session duration `allowed_range.max`'ı geçen artifact
- Branch count > `max_counterfactual_branches` ile replay başlatma
- Event count > `max_events_per_session` ile session ilerletme

---

## 6. Replay Cooldown and Fatigue

### Cooldown

İki session arası minimum süre.

```
replay_protocol.replay_cooldown_ms:           ~120_000   # 2 dakika
    directionality: higher_is_stricter
    change_class_if_increased: safety_tightening
    change_class_if_decreased: safety_weakening
    allowed_range: {min: 30_000, max: 600_000}
```

### Fatigue accumulation

Her replay session sonrası bir fatigue trace birikir. Fatigue cap'e ulaşınca yeni session başlatılamaz (sleep cycle bekler).

```
replay_protocol.replay_fatigue_accum_rate:    ~0.10 per session
    directionality: higher_is_stricter        # hızlı birikim = koruyucu
    change_class_if_increased: safety_tightening
    change_class_if_decreased: safety_weakening
    allowed_range: {min: 0.05, max: 0.50}

replay_protocol.replay_fatigue_cap:           ~1.00
    directionality: lower_is_stricter
    change_class_if_increased: safety_weakening
    allowed_range: {min: 0.50, max: 2.00}

replay_protocol.replay_fatigue_recovery_per_sleep_cycle: ~0.50
    directionality: lower_is_stricter
    change_class_if_increased: safety_weakening
```

### Ruminasyon kontrolü — composite invariant

Sayısal ruminasyon riski yaklaşık:

```
rumination_score ≈ (session_duration × sessions_per_window) / replay_cooldown
```

Tek key'i sıkmak yetmez; ailenin tamamı tightening yönünde imzalı. Buradaki her key M3 tarafından okunabilir ama **değiştirilemez** (Madde 6).

---

## 7. Budget Accounting Unit — Cycle vs 24h Window

### Çift cap kuralı

Replay budget tek pencerede sayılmaz. **İki bağımsız pencere** birlikte uygulanır:

```
replay_protocol.max_sessions_per_cycle:        ~4
    # cycle = sleep/awake cycle (B §11 + K §10)
    directionality: lower_is_stricter

replay_protocol.max_sessions_per_24h_window:   ~10
    # wall-clock hard ceiling
    directionality: lower_is_stricter
    dependencies:
        - target_key: replay_protocol.max_sessions_per_cycle
          relationship: must_be_greater_than_or_equal
          rationale: "24h window en az bir cycle'ı kapsar."
```

Cycle uzun gidebilir; 24h cap o cycle'ı disipline eder. Cycle kısa olursa per_cycle cap koruyucu.

### Restore behavior — no budget reset

```
replay_protocol.restore_budget_continuity:
    value: required
    unit: enum
    allowed_range: {required, optional_legacy}
    directionality: bidirectional_sensitive
    change_class_if_increased: safety_weakening    # "optional"a düşmek riskli
    change_class_if_decreased: safety_tightening
```

Kural:

```
Restore sonrası replay budget reset YOK.
Budget M1 segment'inden devralınır (L §14 RestoreManifest).
Pre-restore cycle/24h sayaçları M1'den okunur ve devam eder.
```

Bu olmadan **restore = replay spam kapısı** açılır. Forgetting attack defense (L §22) numerics seviyesinde devam eder.

### Forbidden

- Restore sonrası budget'ı 0'a sıfırlamak (forgetting attack vektörü)
- Tek pencere kullanmak (per_cycle veya per_24h tek başına yetmez)

---

## 8. Counterfactual Ablation Limits

### Hard hierarchy (K §15 numerics)

```
replay_protocol.higher_order_ablation_max_order:
    value: 2
    unit: count (order)
    allowed_range: {min: 1, max: 2}             # hard upper bound
    directionality: lower_is_stricter
    change_class_if_increased: forbidden        # v0.1 constitutional invariant
    change_class_if_decreased: safety_tightening
    requires_human_approval: n/a (forbidden zone)
    rationale: "v0.1 constitutional invariant. Triple+ ablation = alternative-
                history simulation; replay'in K kapsamı dışına çıkar. Changing
                this requires REPLAY_PROTOCOL.md revision, not numeric artifact
                update."
    numeric_risk_family: safety_critical
    spec_family: replay_protocol
    owning_spec_ref: "REPLAY_PROTOCOL_NUMERICS.md §8"
```

`forbidden` change_class M §7'nin canonical enum'undan; artifact alanında değer artırılamaz, REPLAY_PROTOCOL.md spec revision gerek.

### Per-session ablation caps

```
replay_protocol.max_single_variable_ablations_per_session:  ~10
    directionality: lower_is_stricter
    change_class_if_increased: safety_weakening

replay_protocol.max_pairwise_ablations_per_session:         ~3
    directionality: lower_is_stricter
    change_class_if_increased: safety_weakening
    dependencies:
        - target_key: replay_protocol.max_single_variable_ablations_per_session
          relationship: computed_less_than_or_equal
          expression: "max_pairwise_ablations_per_session <=
                       max_single_variable_ablations_per_session × 0.5"
          rationale: "Pairwise daha pahalı, daha nadir. Yarısı kuralı."
```

### Forbidden

- `higher_order_ablation_max_order > 2` taşıyan artifact (forbidden change)
- Pairwise count > single_variable / 2 ile session ilerletme
- v0.1'de order >= 3 ablation girişimi

---

## 9. Pairwise Causal-Link Numeric Constraints

Pairwise ablation **causal-link score** olmadan yapılamaz (K §15).

```
replay_protocol.pairwise_causal_link_score_min:    ~0.70
    directionality: higher_is_stricter             # eşik yüksek = az pairwise
    change_class_if_increased: safety_tightening
    change_class_if_decreased: safety_weakening
    allowed_range: {min: 0.50, max: 0.95}
    rationale: "Pairwise ablation iki değişken arasında nedensel bağ kanıtı
                ister. Düşük eşik = spurious correlation'ı causal sayma riski."
```

### Per-pair recheck rule

```
replay_protocol.pairwise_causal_link_recheck_window_ms:  ~3_600_000   # 1h
    directionality: lower_is_stricter
    rationale: "Causal-link score eski ise yeniden hesaplanmalı."
```

### Forbidden

- Pairwise ablation `pairwise_causal_link_score_min` altında causal score ile
- Recheck window aşılmış score ile pairwise ilerletme

---

## 10. Sleep/Synapse Replay Update Caps

K §11 sleep_synapse_update channel'ının sayısal sınırları.

### Per-synapse caps

```
replay_protocol.per_synapse_strengthening_cap:     ~0.05 per session
    directionality: lower_is_stricter
    change_class_if_increased: safety_weakening
    dependencies:
        - target_key: replay_protocol.per_synapse_weakening_cap
          relationship: must_be_less_than_or_equal
          rationale: "Asimetri: dampening > strengthening (K + Madde 1).
                      Yanlış güçlenmiş izi söndürmek, yeni iz güçlendirmekten
                      daha kolay olmalı."

replay_protocol.per_synapse_weakening_cap:         ~0.10 per session
    directionality: lower_is_stricter
    change_class_if_increased: safety_weakening
```

### Aggregate cap

```
replay_protocol.per_session_total_synapse_delta_cap:  ~0.50
    directionality: lower_is_stricter
    change_class_if_increased: safety_weakening
    rationale: "Individual synapse cap'leri tatmin edilse bile session toplam
                M0 delta'sı bu cap'i aşamaz. Tek session 'çok sinapsa az dokun'
                ile rejim değiştiremez."
```

### NumericEntry örneği

```
NumericEntry:
    key: replay_protocol.per_synapse_strengthening_cap
    value: 0.05
    unit: ratio (per session)
    allowed_range: {min: 0.01, max: 0.20}
    directionality: lower_is_stricter
    change_class_if_increased: safety_weakening
    change_class_if_decreased: safety_tightening
    requires_human_approval: true
    dependencies:
        - target_key: replay_protocol.per_synapse_weakening_cap
          relationship: must_be_less_than_or_equal
        - target_key: replay_protocol.per_session_total_synapse_delta_cap
          relationship: must_be_less_than
    numeric_risk_family: safety_critical
    spec_family: replay_protocol
    owning_spec_ref: "REPLAY_PROTOCOL_NUMERICS.md §10"
```

### Forbidden

- Strengthening cap > weakening cap (asimetri ihlali)
- Bireysel cap'ler tatmin ama aggregate cap aşılmış session

---

## 11. Eligibility Trace Window Numerics

K §11: replay update sadece **eligibility trace window** içindeki synaps'lere uygulanır.

```
replay_protocol.eligibility_trace_window_ms:      ~600_000     # 10 dakika
    directionality: lower_is_stricter             # dar pencere = az dokunma
    change_class_if_increased: safety_weakening
    change_class_if_decreased: operational_no_behavior_change
    allowed_range: {min: 60_000, max: 3_600_000}
    rationale: "Replay'in dokunabileceği sinapslar bu pencereye sınırlı.
                Pencere dışı sinaps replay tarafından güncellenemez."
```

### Hard rule (numeric değil, protocol invariant)

```
Replay update cannot reach synapses outside eligibility_trace_window.
Pencere dışı synaps update girişimi → `REPLAY_SESSION_STATUS_CHANGED(new_status=failed, reason=out_of_trace_violation)`.
```

### Forbidden

- `eligibility_trace_window_ms` üzerinden sinaps update'i (pencere dışı)
- Window'u "infinite" yapmak (allowed_range.max ile koruma)

---

## 12. Attention Habituation Replay Numerics

K §11 attention_habituation_update channel.

```
replay_protocol.habituation_delta_cap_per_session:    ~0.10
    directionality: lower_is_stricter
    change_class_if_increased: safety_weakening

replay_protocol.habituation_decay_after_success:      ~0.30
    # bir habituation pattern success ile sonuçlanırsa habituation azalır
    directionality: higher_is_stricter        # daha hızlı decay = daha sıkı dikkat
    change_class_if_increased: safety_tightening

replay_protocol.attention_replay_frequency_cap_per_cycle: ~2
    # attention channel'ı cycle başına kaç kez tetiklenebilir
    directionality: lower_is_stricter
```

### Forbidden

- Habituation delta cap aşımı (dikkati sessizce öldürme)
- Frequency cap aşımı (saplantılı attention pattern)

---

## 13. Ingress Calibration Replay Numerics — N Bridge

K §12 ingress_calibration_update channel. **N artifact'ı ile dependency bridge.**

### Cross-artifact dependency (kritik)

```
replay_protocol.ingress_calibration_replay_delta_cap:   ~0.30 × N daily cap
    directionality: lower_is_stricter
    change_class_if_increased: safety_weakening
    dependencies:
        - target_key: ingress_compiler.per_mapping_daily_delta_cap
          relationship: computed_less_than_or_equal
          expression: "ingress_calibration_replay_delta_cap <=
                       ingress_compiler.per_mapping_daily_delta_cap × 0.30"
          rationale: "Replay'in compiler'a katkısı, compiler'ın kendi günlük
                      drift cap'inin %30'unu aşamaz. Replay N'i back-door'dan
                      gevşetemez. N artifact'i replay'in cap'idir."
    numeric_risk_family: safety_critical
    spec_family: replay_protocol
    owning_spec_ref: "REPLAY_PROTOCOL_NUMERICS.md §13"
```

Bu **O'nun en kritik dependency'lerinden biri.** Replay'in dolaylı yoldan ingress compiler'ı gevşetmesi yasak — replay'in compiler'a etkisi her zaman N'in kendi drift cap'inin altında kalmak zorunda.

### Per-mapping replay contribution cap

```
replay_protocol.max_replay_based_mapping_update_per_session:  ~3
    directionality: lower_is_stricter
    rationale: "Session başına kaç farklı mapping replay tarafından
                güncellenebilir."

replay_protocol.replay_weight_vs_real_outcome_weight_ratio:   ~0.30
    directionality: lower_is_stricter
    change_class_if_increased: safety_weakening
    rationale: "Mapping update'inde replay'in evidence weight'i real outcome'un
                en fazla %30'u olabilir. Real outcome baskındır."
```

### Forbidden

- N drift cap'in üzerine replay katkısı eklemek
- Real outcome olmadan sadece replay ile mapping update
- Per-session mapping update cap aşımı

---

## 14. Memory Verification Numerics

K §13 memory_verification_update channel. Replay survival score Memory Write Gate'in verification matrix'ine (G §8) girer.

```
replay_protocol.min_replay_survival_score_for_evidence:  ~0.60
    directionality: higher_is_stricter
    change_class_if_increased: safety_tightening
    allowed_range: {min: 0.50, max: 0.90}
    rationale: "Bu eşiğin altındaki survival score verification'a evidence
                olarak girmez."

replay_protocol.min_replay_survival_sessions:            2
    directionality: higher_is_stricter
    change_class_if_increased: safety_tightening
    allowed_range: {min: 2, max: 5}
    rationale: "Single session bias'a karşı koruma. Tek session kanıt değil."

replay_protocol.min_session_separation_ms:               ~600_000     # 10 dakika
    directionality: higher_is_stricter
    rationale: "İki survival session arası minimum süre. Ardışık replay'ler
                aynı evidence sayılmaz."
```

### Self-confirmation guard

```
Aynı seed event üzerinde art arda yapılan replay'lerden gelen survival
sinyalleri TEK survival session olarak sayılır.

min_replay_survival_sessions sayacı bağımsız session counter'dır;
toplam replay count değil.
```

### Forbidden

- Tek session survival'ı verification'a evidence olarak yazma
- Aynı seed üzerine peş peşe replay ile survival count şişirme

---

## 15. Outcome Alignment Numerics

K §14 outcome_alignment_analysis channel. **Real outcome'a hizalı bir replay** kanıt değerini güçlendirir.

```
replay_protocol.outcome_alignment.min_wait_ms:        ~60_000     # 1 dakika
    directionality: higher_is_stricter
    rationale: "Outcome'un gerçekleşip raporlanması için minimum süre.
                Çok kısa wait = premature alignment."

replay_protocol.outcome_alignment.max_wait_ms:        ~86_400_000  # 24 saat
    directionality: bidirectional_sensitive
    change_class_if_increased: safety_weakening      # uzun = stale outcome riski
    change_class_if_decreased: operational_no_behavior_change
    allowed_range: {min: 600_000, max: 604_800_000}

replay_protocol.outcome_alignment.max_lag_window_ms:  ~3_600_000   # 1 saat
    directionality: lower_is_stricter
    rationale: "Replay completion ile outcome arasında izin verilen lag."

replay_protocol.outcome_alignment.required_outcome_ref_count: 1
    directionality: higher_is_stricter
    rationale: "Default 1; outcome confidence_band < medium ise effective_min = 2."
```

### Cross-artifact dependency — staleness (P canonical, P yazıldı)

```
outcome_alignment.max_wait_ms
    dependencies:
        - target_key: memory_write.epistemic_staleness_threshold_ms.<owning_subject_class>
          relationship: computed_less_than_or_equal
          expression: "replay_protocol.outcome_alignment.max_wait_ms
                       <= memory_write.epistemic_staleness_threshold_ms.<owning_subject_class>"
          rationale: "Outcome'un ait olduğu subject_class'ın staleness
                      threshold'unu aşan outcome alignment'a katkı sağlayamaz.
                      P §8 canonical kaynak. T (RECALL_PROTOCOL_NUMERICS)
                      sonradan recall-side staleness numeric'leri ekleyecek,
                      ama epistemic_staleness_threshold_ms her zaman P'de."
```

### Hard rule — external outcome (numeric değil, protocol invariant)

```
outcome_must_be_external = true

Internal-only outcome_ref outcome_alignment'a katkı sağlayamaz.
Self-corroboration (L §10 internal_only_refs) buraya da uygulanır:
    outcome_ref'lerin en az birinde external corroboration olmalı.
```

Bu bir NumericEntry değil; protocol-level invariant. O bunu **declarative kural** olarak taşır.

### Forbidden

- Stale outcome (wait > staleness threshold) ile alignment
- External corroboration olmadan outcome_alignment evidence
- `required_outcome_ref_count = 0` (kanıtsız alignment)

---

## 16. Replay Survival Score Thresholds

Replay survival score'un kendi sayısal sınırları (§14 verification için eşik; bu bölüm survival score'un hesaplandığı sınırlar).

```
replay_protocol.replay_survival_score.computation_window_ms:  ~7_200_000  # 2 saat
    directionality: lower_is_stricter
    rationale: "Survival score bu pencerede toplanır; eski survival'lar düşer."

replay_protocol.replay_survival_score.confidence_band_min:    medium
    directionality: higher_is_stricter
    allowed_range: {min: low, max: high}
    rationale: "Bu confidence band'ın altında survival evidence'a katkı sağlamaz."

replay_protocol.replay_survival_score.max_per_session:        ~0.30
    directionality: lower_is_stricter
    rationale: "Tek session'un toplam survival'a max katkısı. Cap = self-
                amplification koruması."
```

### Critical kural

```
Replay survival score = synthetic evidence indicator.
Replay survival score ≠ truth score.
Replay survival score ≠ outcome_alignment score.
```

K §16'dan kalan ayrım numerics'te de yaşar: survival yardımcı, outcome baskın.

### Forbidden

- Replay survival score'u truth axis olarak verification matrix'e yazmak
- Replay survival score'u outcome_alignment score ile özdeşleştirmek

---

## 17. Replay vs Outcome Evidence Weighting

Memory Write Gate verification matrix'inde (G §8) iki evidence axis'in ağırlığı.

```
replay_protocol.max_replay_survival_weight_in_verification:  ~0.30
    directionality: lower_is_stricter
    change_class_if_increased: safety_weakening
    allowed_range: {min: 0.10, max: 0.45}
    dependencies:
        - target_key: replay_protocol.outcome_alignment_weight_in_verification
          relationship: must_be_less_than
          rationale: "Outcome real, replay synthetic. Real evidence must dominate."

replay_protocol.outcome_alignment_weight_in_verification:    ~0.60
    directionality: lower_is_stricter             # azaltmak = real evidence değerini düşürür
    change_class_if_increased: operational_no_behavior_change
    change_class_if_decreased: safety_weakening
    allowed_range: {min: 0.40, max: 0.80}
```

### Kilit cümle

> **Replay survival evidence yardımcıdır.**
> **Outcome alignment evidence baskındır.**

Bu O'nun en güçlü cümlelerinden biri — sayısal olarak `replay_survival_weight < outcome_alignment_weight` dependency'si ile garanti altında.

### NumericEntry örneği

```
NumericEntry:
    key: replay_protocol.max_replay_survival_weight_in_verification
    value: 0.30
    unit: ratio
    allowed_range: {min: 0.10, max: 0.45}
    directionality: lower_is_stricter
    change_class_if_increased: safety_weakening
    change_class_if_decreased: safety_tightening
    requires_human_approval: true
    dependencies:
        - target_key: replay_protocol.outcome_alignment_weight_in_verification
          relationship: must_be_less_than
          rationale: "Real-world evidence must dominate synthetic evidence."
    numeric_risk_family: safety_critical
    spec_family: replay_protocol
    owning_spec_ref: "REPLAY_PROTOCOL_NUMERICS.md §17"
```

### Forbidden

- `max_replay_survival_weight >= outcome_alignment_weight` taşıyan artifact
- Replay survival'ı verification'da tek başına yeterli evidence yapmak

---

## 18. Asymmetric Strengthening/Dampening Ratios

Replay update'lerin **iki yöndeki rate** asimetrisi.

### Global asimetri kuralı

```
weakening_rate >= strengthening_rate
                    for every replay update channel
```

Bu zaten §10 `per_synapse_*` ve §13 replay-mapping cap'lerinde dependency olarak yazılı. §18 bunu **global invariant** olarak sertleştirir.

### Per-channel rate'ler

```
sleep_synapse_strengthening_rate         <= sleep_synapse_weakening_rate
attention_habituation_increase_rate      <= attention_habituation_decrease_rate
ingress_calibration_strengthening_rate   <= ingress_calibration_dampening_rate
memory_verification_promotion_rate       <= memory_verification_demotion_rate
```

### Numerics expression

```
replay_protocol.rate_asymmetry_invariant:
    rule: "For every replay update channel, weakening rate >= strengthening rate."
    enforcement: artifact validation rejects symmetric or inverted ratios
    rationale: "Sistem yanlış pozitiften kaçar, yanlış negatife düşer
                (K + N asimetri prensibi)."
```

Bu bir tekil NumericEntry değil; **artifact validation invariant**. Numerics artifact yüklenirken validator her channel için bu invariant'ı kontrol eder.

### Forbidden

- Symmetric rate (strengthening = weakening) taşıyan artifact
- Inverted rate (strengthening > weakening) taşıyan artifact

---

## 19. Replay-Triggers-Replay Prohibition

K §10 sandbox kuralının numeric tarafı: replay başka bir replay'i tetikleyemez.

```
replay_protocol.replay_can_trigger_replay_max_chain_depth:
    value: 0
    unit: count
    allowed_range: {min: 0, max: 0}              # hard immutable, single value
    directionality: neutral                       # değer değişemez, yön anlamsız
    change_class_if_increased: forbidden          # constitutional zero
    change_class_if_decreased: forbidden          # below zero impossible
    requires_human_approval: n/a (forbidden zone)
    dependencies: []
    rationale: "Recursive replay = self-amplification loop. Replay'in kendi
                kendini tetiklemesi sistemin kanıt üretimini hakikat sayma
                yoluna açar. v0.1 constitutional invariant."
    numeric_risk_family: safety_critical
    spec_family: replay_protocol
    owning_spec_ref: "REPLAY_PROTOCOL_NUMERICS.md §19"
```

### M'nin allowed_range mekanizması burada constitutional invariant'a dönüşüyor:

```
allowed_range: {min: 0, max: 0}
    → tek değer (0), değiştirilemez
    → directionality neutral (yönü yok, değişemez)
    → change forbidden (artifact validation hem increase hem decrease'i reddeder)
```

### Kilit cümle

> **Recursive replay = self-amplification loop.**
> **Replay geçmişten kanıt üretir; ama kendini tekrar tetikleyemez.**

### Forbidden

- Replay completion event'inin yeni replay session tetiklemesi
- `replay_can_trigger_replay_max_chain_depth > 0` taşıyan artifact
- "Tek seferlik" istisna olarak chain depth = 1 kullanma girişimi

---

## 20. Missing-Numerics Failsafe

M §11 fail-safe strict mode replay'e uygulanır.

### Strict mode behavior

```
Missing replay numerics artifact veya invalid load:
    → replay DISABLED except audit-safe mode
    → audit-safe mode: only outcome_alignment_analysis read-only çalışır
       (synaps update, M2 verification, habituation update tamamen kapalı)
    → NUMERICS_FAILSAFE_ACTIVATED event tetiklenir
    → Manual intervention until valid numerics artifact loaded
```

### Audit-safe mode tanımı

```
Audit-safe replay:
    ✅ Outcome alignment analysis (read-only, hiçbir M0/M2 update yok)
    ✅ Replay history audit (M1 events üzerinden)
    ❌ Sleep/synapse update
    ❌ Attention habituation update
    ❌ Ingress calibration update
    ❌ Memory verification update
    ❌ Counterfactual ablation
```

Sistem "replay yok" durumunda **daha serbest değil, daha kısıtlı** çalışır (M kuralı).

### NumericEntry — strict mode entry

```
replay_protocol.failsafe_mode:
    value: strict_audit_safe
    unit: enum
    allowed_range: {strict_audit_safe, strict_full_disable}
    directionality: bidirectional_sensitive
    change_class_if_increased: safety_weakening
    change_class_if_decreased: safety_tightening
```

### Forbidden

- Missing numerics → fail-open (replay normal devam)
- Audit-safe mode'da M0/M2 update girişimi

---

## 21. Dependency Declarations

O'nun cross-artifact ve internal dependency'lerinin özet matrisi.

### Internal (O içinde)

```
max_session_duration_ms     <    replay_cooldown_ms
per_synapse_strengthening_cap  ≤  per_synapse_weakening_cap
per_synapse_strengthening_cap  <  per_session_total_synapse_delta_cap
max_pairwise_ablations_per_session ≤ max_single_variable × 0.5
                                     (computed_less_than_or_equal)
max_sessions_per_24h_window  ≥   max_sessions_per_cycle
max_replay_survival_weight_in_verification < outcome_alignment_weight_in_verification
```

### Cross-artifact

```
ingress_calibration_replay_delta_cap ≤ N.per_mapping_daily_delta_cap × 0.30
                                       (computed_less_than_or_equal)
outcome_alignment.max_wait_ms        ≤ P.epistemic_staleness_threshold_ms.<owning_subject_class>
                                       (computed_less_than_or_equal; P §8 canonical)
restore_budget_continuity = required → R (BACKUP_STRATEGY_NUMERICS) §18
                                       backup.replay_budget_continuity_required = true
                                       (constitutional immutable)
replay_survival_weight integration   → G (MEMORY_WRITE_GATE) §8 verification matrix
```

### Atomic update rule (M §12)

Bağımlı numerics atomic artifact içinde değişir. Tek key değişikliği bağımlı key'leri eski bırakırsa artifact REJECT.

### Forbidden

- Dependency declarationsız replay numeric ekleme
- Partial update (bir key değişip bağımlı key'in eski kalması)
- Dependency violation tolere edilmesi

---

## 22. Audit Events and M2 Reference

O **yeni canonical event tanımlamaz**. M zaten numerics lifecycle event'lerini tanımladı; O onları reuse eder.

### Reused events (M §6, F §10, §19)

```
NUMERICS_ARTIFACT_STATUS_CHANGED
    when: replay_protocol artifact register/deprecate/rollback
    payload: spec_family=replay_protocol, version, old_status, new_status

NUMERICS_VERSION_MISMATCH_DETECTED
    when: restore sırasında numerics version uyumsuz
    family: ledger_meta

NUMERICS_FAILSAFE_ACTIVATED
    when: missing/invalid replay numerics → strict audit-safe mode
    family: ledger_meta
```

### Replay-spesifik audit events — canonical reuse (K §17/§18)

O **yeni replay event tipi tanımlamaz**. Replay numerics ihlalleri tek
canonical lifecycle event'i (`REPLAY_SESSION_STATUS_CHANGED`) **explicit
reason field** ile taşır:

```
REPLAY_SESSION_STATUS_CHANGED
    new_status: failed
    reason:     out_of_trace_violation        # eligibility_trace_window dışı update girişimi (§11)

REPLAY_SESSION_STATUS_CHANGED
    new_status: budget_exhausted
    reason:     budget_exhausted              # §5-7 budget caps

REPLAY_SESSION_STATUS_CHANGED
    new_status: aborted
    reason:     recursive_trigger_blocked     # §19 chain_depth=0 ihlali girişimi
```

### Kural (F event type discipline yansıması)

> *Replay numerics violations do not introduce new canonical event types.*
> *They are recorded as `REPLAY_SESSION_STATUS_CHANGED` with explicit
> `reason` fields.*

`failed` durumda permanence = `permanent_with_snapshot` (F §10);
`budget_exhausted` ve `aborted` durumlarında permanence = `permanent`
(K §17/F §19 zaten tanımlı, O ek event tipi getirmez).

### M2 reference

```
numerics_artifact_reference (MEMORY_CONTRACT §3 subject_class)
    spec_family: replay_protocol
    artifact_version: v0.1
    status: active | deprecated | rollback_pending
    signed_hash: <external artifact hash>
    last_status_change_ref: <NUMERICS_ARTIFACT_STATUS_CHANGED event_id>
```

---

## 23. Cross-document Anchors

```
| Belge                            | Bağlantı                                          |
|----------------------------------|---------------------------------------------------|
| NUMERICS_GOVERNANCE.md (M)       | tüm meta-kurallar; spec_family=replay_protocol    |
| REPLAY_PROTOCOL.md (K)           | mekanizma; O onun numerics artifact'i            |
| INGRESS_COMPILER_NUMERICS.md (N) | replay drift cap'i N'in cap'inin altında         |
| MEMORY_CONTRACT.md (B)           | staleness disciplini outcome alignment'a yansır  |
| BACKUP_STRATEGY.md (L)           | restore budget continuity; M1 segment devralma   |
| MEMORY_WRITE_GATE.md (G)         | verification matrix replay vs outcome weighting  |
| OBSERVER_LEDGER_SCHEMA.md (F)    | ledger_meta family numerics events               |
| BOOTSTRAP_GENOME.md (D)          | replay'in M0 üzerindeki bounded etkisi          |
| CONSTITUTION.md (A)              | Madde 1 (asimetri) + Madde 6 (LLM numeric değiştiremez) |
```

---

## 24. Violation Tests

O artifact'ı validation sırasında **REJECT** edilmesi gereken durumlar:

1. **Çıplak sayı.** NumericEntry metadata olmadan replay sayısı içeren artifact.
2. **higher_order_ablation_max_order > 2.** v0.1 constitutional invariant ihlali.
3. **Strengthening cap > weakening cap.** Asimetri ihlali (§10, §18).
4. **`replay_survival_weight >= outcome_alignment_weight`.** Real evidence dominance ihlali (§17).
5. **`replay_can_trigger_replay_max_chain_depth > 0`.** Recursive replay yasağı ihlali (§19).
6. **Restore sonrası budget reset.** L forgetting attack defense ihlali (§7).
7. **`ingress_calibration_replay_delta_cap > N.per_mapping_daily_delta_cap`.** N back-door koruması ihlali (§13).
8. **Eligibility trace window dışı sinaps update.** K §11 ihlali (§11).
9. **Pairwise ablation causal-link score min altında.** §9 ihlali.
10. **Pairwise count > single_variable × 0.5.** §8 computed dependency ihlali.
11. **Tek session survival evidence olarak verification'a yazıldı.** §14 ihlali.
12. **Ardışık aynı seed replay'leri ayrı survival session sayıldı.** §14 self-confirmation guard ihlali.
13. **Stale outcome ile alignment.** §15 staleness disciplini ihlali.
14. **Internal-only outcome_ref ile outcome_alignment.** §15 external corroboration ihlali.
15. **`max_session_duration_ms >= replay_cooldown_ms`.** §5 dependency ihlali.
16. **`max_sessions_per_cycle > max_sessions_per_24h_window`.** §7 dependency ihlali.
17. **Symmetric/inverted rate (strengthening = weakening veya >).** §18 ihlali.
18. **Missing numerics → fail-open (normal replay).** §20 fail-safe ihlali.
19. **Aggregate `per_session_total_synapse_delta_cap` aşılmış (bireysel cap'ler tatmin).** §10 ihlali.
20. **LLM tarafından üretilen veya değiştirilen replay numeric.** Madde 6 ihlali.
21. **Dependency declarationsız replay numeric eklenmiş.** §21 ihlali.
22. **Habituation frequency_cap aşımı (cycle başına > 2 attention replay).** §12 ihlali.

**Artifact-level violations** (1-22, validation aşaması):
`MEMORY_RECORD_STATUS_CHANGED` → `rejected` (G §8 numerics artifact
verification matrix satırı). Artifact aktive edilmez.

**Runtime violations** (artifact valid ama replay session caps'leri aştı /
sandbox'ı zorladı): yeni canonical event yok; tek lifecycle event'i +
reason field:

```
Eligibility trace window dışı sinaps update girişimi
    → REPLAY_SESSION_STATUS_CHANGED(new_status=failed,
                                    reason=out_of_trace_violation)
    permanence: permanent_with_snapshot

Replay budget exhausted
    → REPLAY_SESSION_STATUS_CHANGED(new_status=budget_exhausted,
                                    reason=budget_exhausted)
    permanence: permanent

Recursive replay trigger (chain_depth violation)
    → REPLAY_SESSION_STATUS_CHANGED(new_status=aborted,
                                    reason=recursive_trigger_blocked)
    permanence: permanent
```

Bu F'deki **event type discipline** (tek canonical event + reason field;
yeni event tipi yok) ile uyumlu.

---

## 25. Open Questions

O kapanırken cevaplanmamış bırakılan sorular:

- **Replay drift detection threshold** (asymmetric rate'lerin "yeterince asimetrik" olduğunu kim sayısallaştırır?) → Implementation
- **Production değerler için signed artifact içeriği** → Sentinel implementation
- **`replay_can_trigger_replay_max_chain_depth = 0` istisnası mümkün mü?** → Hayır; v0.1 constitutional. İleride ihtiyaç doğarsa REPLAY_PROTOCOL.md spec revision (numeric artifact yetmez).
- **Sleep cycle ile fatigue recovery'nin tam matematiği** → BOOTSTRAP_GENOME_NUMERICS.md (S) ile koordine edilecek
- **Outcome alignment staleness threshold canonical kaynağı** → KAPANDI: P §8 `epistemic_staleness_threshold_ms.<subject_class>` canonical kaynak; T sonradan recall-side staleness numeric'lerini ekleyecek ama P canonical kalır
- **Replay cycle boundary tanımı** (cycle nerede başlar/biter?) → BOOTSTRAP_GENOME §17 sleep/wake transition ile birlikte
- **Higher-order ablation'a izin verecek constitutional amendment paths** → REPLAY_PROTOCOL.md v0.2'de tartışılacak

Bu sorular cevaplanmadan implementation aşamasına geçilmez.

---

## Çekirdek özet — 14 karar + 22 violation tests

### 14 karar

1. Replay numerics runtime config değildir; signed artifact + M2 reference.
2. Replay budget artışı = safety_weakening (tüm budget key'leri lower_is_stricter).
3. Çift cap: max_sessions_per_cycle + max_sessions_per_24h_window.
4. Restore sonrası budget reset YOK; M1 segment'inden devralma.
5. `higher_order_ablation_max_order = 2` v0.1 constitutional invariant; artırma `forbidden` change_class.
6. Pairwise ablation causal-link score min eşiği zorunlu; pairwise count ≤ single_variable × 0.5.
7. M0 update asimetri: `strengthening_cap ≤ weakening_cap` (computed dependency).
8. Eligibility trace window dışı sinaps update yasak.
9. Replay'in ingress calibration'a katkısı N drift cap'inin %30'unu aşamaz (N bridge).
10. Replay survival ≠ truth; min 2 bağımsız session, min_session_separation_ms.
11. `replay_survival_weight < outcome_alignment_weight` (real evidence dominance).
12. `replay_can_trigger_replay_max_chain_depth = 0` constitutional invariant.
13. Missing numerics → strict audit-safe mode (fail-open yasak).
14. Outcome alignment için external outcome_ref zorunlu; internal-only ref alignment'a katkı sağlamaz.

### 22 violation tests

§24'te listelendi.

### Damıtma — son cümleler

> **Replay numerics, sistemin geçmişi ne kadar yeniden sınayabileceğinin sayısal sözleşmesidir.**
>
> **Replay geçmişten kanıt üretir.**
> **Ama geçmişi yeniden yaşatamaz, kendi kanıtını hakikat sayamaz, ve kendini tekrar tetikleyemez.**
>
> **Sistem yanlış pozitiften kaçar, yanlış negatife düşer — replay rate'leri bu yönde imzalı.**
>
> **Recursive replay = self-amplification loop. Constitutional zero.**
>
> **Real outcome > replay survival. Her zaman. Sayısal olarak.**
