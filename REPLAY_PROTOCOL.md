# REPLAY_PROTOCOL.md

## Sentinel — Replay Sözleşmesi

---

## Status

**Frozen Draft v0.1**
**Conceptual phase. No implementation authority.**

Bu belge `CONSTITUTION.md` Madde 2 ve `MEMORY_CONTRACT.md` §14'teki replay engine kavramının detaylı uzantısıdır. Yeni anayasa maddesi değildir. Çalışan bir replay implementation'ının runtime spec'i değildir. Geçmiş M1 izlerinin ve M0 trace'lerinin **hangi sınırlı müdahalelerle yeniden sınanabileceğini, hangi kanallardan etki üretebileceğini ve audit'inin nasıl tutulacağını** tanımlar.

A-J belgelerinde replay birçok yerde **dağınık** olarak referans edildi:
- Madde 2 — sleep/replay causal pruning (sinaps weight)
- B §19 — attention replay habituation update
- G §8 — `replay_survival` verification matrix'te evidence axis
- J §13-14 — mapping update outcome/replay evidence ister
- MEMORY_CONTRACT §14 — replay engine M0 etkisi (3 kanal: sleep, attention, ingress)

K bu dağınık referansları **tek tutarlı kontrat** altında topladı + replay'in **kendi self-deception kapısını** kapattı.

---

## 1. Purpose

Replay sistemde yaygın bir öğrenme/evidence mekanizmasıdır. Ama yanlış yazılırsa:
- "Kanıt üreten mekanizma" olmaktan çıkar
- "Kendi geçmişinden hakikat uyduran mekanizma"ya dönüşür
- Self-deception zincirinin merkezi haline gelir

K bu riski kapatır: replay'in **ne yapabildiğini, ne yapamadığını, hangi kanallardan ne şiddette etkide bulunabildiğini** biçimselleştirir.

Damıtma:

> **Replay geçmişi tekrar yaşatmaz. Replay geçmişten kontrollü kanıt üretir.**
>
> **Replay decision engine değildir. Replay yeni hakikat yaratmaz.**
>
> **Replay kendi sonucuna inanamaz. Replay sonucu sadece denetlenebilir evidence olarak yaşar.**

---

## 2. Constitutional Position — Madde 2 / MEMORY_CONTRACT §14 Alt-spec'i

Bu belge:
- **Madde 2** (Sinaps anlam taşımaz, akış deseninin hafızasını taşır): sleep/replay causal pruning Madde 2'nin altındadır
- **MEMORY_CONTRACT §14** (Replay engine M0 etkisi): üç kanal şimdi K'da formal olarak biçimselleşti
- **B §19** (Attention Replay Habituation): K'nın bir effect channel'ı
- **G §8** (Memory Write Gate verification matrix): `replay_survival` ve `outcome_alignment` evidence axes — K bunları formalize eder
- **J §13-14** (Compiler mapping update): ingress calibration replay channel — K bunu biçimselleştirir

---

## 3. Core Principle

> **Replay proof değildir.**
> **Replay evidence candidate üretir.**
>
> **Replay sandboxed'tır; live core'a duyusal event basamaz.**
> **Replay output direkt M2 candidate yazamaz, direkt verified evidence olamaz.**

---

## 4. Replay Is Not Re-Living

### Principle

Replay geçmişi **tekrar yaşatmaz**. Geçmiş M1 snapshot'larını veya M0 trace'lerini yeniden açmak, bunları çekirdeğe yeniden duyusal olarak göstermek demek değildir.

### Rationale

Eğer replay live core'a "yeniden duyusal event" basabilse:
- Sistem rumination'a girer (geçmişi sürekli yaşar)
- Geçmiş yeni olaylarla karışır (zamansal kafa karışıklığı)
- Recall ekonomisi anlamsız kalır
- Çekirdek "şimdiyi" yaşayamaz

Doğru: replay **sandboxed sürecte** çalışır, sonuçları M1 audit + bounded M0 trace update olarak yaşar.

### Sandboxing

Replay session sırasında üretilen herhangi bir simulated event:

- ❌ `payload_seed` üretmez (live core'a girmez)
- ❌ `WORKSPACE_PULSE` tetiklemez (B §4 kuralı)
- ❌ Memory Write Gate'e doğrudan candidate önermez
- ❌ Deontic gate evaluation'a girmez
- ❌ Adapter'lara write çağrısı yapmaz

### Sandbox output

Sadece:
- ✅ M1 replay session log (audit)
- ✅ Bounded M0 trace update (channel-specific, §10-14)
- ✅ Gate evidence axis (replay_survival, outcome_alignment — sınırlı)

### Violation Test
> *Replay sırasında simulated event live core'a payload_seed/pulse/RecallEvent olarak basılıyor mu?*
>
> Evet ise ihlal.

---

## 5. Single Replay Mechanism, Multiple Effect Channels

### Principle

> **Replay engine tek.**
> **Replay etkileri kanala göre sınırlı.**

Madde 1'in replay seviyesindeki yansıması: ayrı `SleepReplayEngine`, `AttentionReplayEngine`, `IngressReplayEngine`, `MemoryVerificationEngine` **yok**. Tek replay protokolü, çoklu effect channel.

### Effect channels

```
1. sleep_synapse_update        (Madde 2 — sleep replay causal pruning)
2. attention_habituation_update (B §19 — attention replay)
3. ingress_calibration_update  (J §13-14 — compiler mapping update)
4. memory_verification_update  (G §8 evidence — replay_survival)
5. outcome_alignment_analysis  (G §8 evidence — outcome correlation)
```

### Channel-specific authority matrix

| Channel | M0 etkisi | M2 etkisi | M1 event | Evidence axis |
|---------|-----------|-----------|----------|---------------|
| sleep_synapse_update | Sinaps weight/trace güncellemesi (eligibility içinde) | Yok | `SLEEP_REPLAY_SYNAPSE_UPDATE` | — |
| attention_habituation_update | Habituation trace update | Yok | `ATTENTION_REPLAY_HABITUATION_UPDATE` | — |
| ingress_calibration_update | M0 ingress_calibration_traces | Yok | `COMPILER_MAPPING_UPDATED` | — |
| memory_verification_update | Yok (sadece evidence üretir) | Sadece evidence axis | `REPLAY_SURVIVAL_EVALUATED` | replay_survival_score |
| outcome_alignment_analysis | Yok (sadece evidence üretir) | Sadece evidence axis | `REPLAY_OUTCOME_ALIGNMENT_EVALUATED` | outcome_alignment_score |

### Kritik kural

> *Replay M2'ye doğrudan yazmaz. Replay sadece evidence axis sağlar; M2 yazımı her zaman Memory Write Gate'ten geçer.*

> *Replay-derived M0 trace'lerinin backup artifact'te nasıl provenance ile korunduğu için bkz. [`BACKUP_STRATEGY.md`](./BACKUP_STRATEGY.md) §17.*

---

## 6. Replay Inputs

### Allowed sources

Replay engine sadece şu kaynaklardan input alabilir:

```
M1 permanent event refs
M1 fine-grain ring buffer snapshot_ref
M0 trace snapshot (replay başında alınmış)
Outcome event refs (gerçek dünyadan gelen feedback)
Causal envelope (causal_refs zinciri)
```

### Forbidden sources

```
❌ LLM narrative / interpretation
❌ Human verbal explanation (sadece raw event refs)
❌ M2 raw claim content
❌ Unverified candidate M2 record content
❌ Adapter ham payload (sadece compiled event)
❌ Cross-instance replay (başka Sentinel'in geçmişi)
```

### M2 input kuralı

Eğer replay M2 bilgisini kullanıyorsa:
- Sadece **verified** veya **active** status'ündeki kayıtlar
- Status_band explicit (G §8 ile uyumlu)
- Provenance kayıtlı
- Replay engine M2'yi **gerçek** olarak değil, **kaynaklı evidence** olarak kullanır

---

## 7. Replay Session Schema

```
ReplaySession
├── session_id
├── triggered_by                   # internal_pressure | sleep_rhythm | external_request
├── trigger_pressure
│   ├── eligibility_pool_saturation
│   ├── contradiction_load
│   ├── fatigue_accumulation
│   └── replay_consolidation_pressure
├── replay_budget                  # max iterations, max cost, max ablations
├── replay_scope
│   ├── m1_event_window            # hangi pencere
│   ├── m0_trace_snapshot_ref
│   ├── target_channels            # hangi effect channels açık
│   └── counterfactual_allowed     # bool
├── session_status                 # requested | started | completed | aborted | budget_exhausted | failed
├── started_at
├── completed_at
├── effect_updates                 # her channel için yapılan update'ler
│   ├── sleep_synapse_deltas
│   ├── attention_habituation_deltas
│   ├── ingress_calibration_deltas
│   ├── memory_verifications
│   └── outcome_alignments
├── counterfactual_ablations       # liste
├── m1_audit_event_refs            # session'da üretilen tüm M1 event'ler
└── observer_snapshot_ref
```

---

## 8. Replay Trigger Conditions

### Internal pressure triggers

Replay session çekirdeğin **iç basıncından** doğar (cron-temelli değil — BOOTSTRAP §17 ile uyumlu):

```
eligibility_pool_saturation         # eligibility buffer doluyor
contradiction_load_threshold        # çelişki birikmiş
fatigue_accumulation                # sistem yorgun, consolidation gerek
replay_consolidation_pressure       # outcome'lar geldi, sindirme zamanı
```

### Allowed external triggers

- **Sleep/wake transition** (sistem doğal uyku ritmine girdi — BOOTSTRAP §17)
- **Operational maintenance** (insan onaylı manual replay session)

### Forbidden triggers

- ❌ Cron / time-based schedule (zaman yok — BOOTSTRAP §16/19)
- ❌ LLM "replay önerisi" (Madde 6)
- ❌ Adapter "replay tetikleyici" (Madde 1)
- ❌ Pulse repetition (B §16)

### Audit

Her trigger M1'e `REPLAY_SESSION_STATUS_CHANGED` (new_status: requested) olarak yazılır.

---

## 9. Replay Budget and Cooldown

> *Bu bölümün sayısal değerleri `REPLAY_PROTOCOL_NUMERICS.md` §5-7'de (max_session_duration_ms, max_events_per_session, max_counterfactual_branches, replay_cooldown_ms, fatigue_accum_rate, max_sessions_per_cycle + per_24h_window). Restore sonrası budget reset yok — M1 segment'inden devralınır (NUMERICS §7).*

### Budget components

```
replay_budget:
    max_iterations                  # ne kadar derin replay
    max_cost                         # toplam enerji bütçesi
    max_counterfactual_branches      # bkz. §15
    max_session_duration             # ne kadar süre çalışabilir
    fatigue_impact                   # session sonunda fatigue ne kadar artar
```

### Cooldown

Aynı `replay_scope` peşpeşe yapılamaz. Cooldown:

```
cooldown_active(scope) = (now - last_replay_at[scope]) < refractory_period[scope_type]
```

### Habituation

Aynı scope tekrar tekrar replay edilirse session etkinliği azalır:

```
habituation_factor = decay_function(repeat_count, time_since_first_replay)
effect_intensity *= habituation_factor
```

### Critical kural

> *Replay geçmişi getirir, ama şimdiyi boğamaz.*
> *Replay bedelsiz değildir.*

H §14 recall economy pattern'iyle uyumlu — recall ve replay benzer ekonomik baskı altında.

### Forbidden

- Sınırsız replay
- Cooldown bypass
- Habituation devre dışı bırakma
- Budget sınırsız

---

## 10. Sleep/Synapse Replay Channel

### Principle

Replay session sırasında sinaps weight, eligibility ve success trace güncellemeleri yapılabilir. Ama **çok sınırlı**.

### Allowed if (ALL must hold)

```
- replay session audited (M1'de session_id var)
- causal ablation veya replay test sonucu var
- outcome OR coherence evidence var
- delta rate cap altında
- synapse eligibility trace içinde
```

### Eligibility trace constraint

> *Replay sadece eligibility trace içindeki sinapslara dokunabilir.*

```
synapse_eligible_for_replay_update =
    synapse in fast_eligibility
    OR synapse in medium_eligibility
    OR synapse in slow_eligibility
```

Dormant, expired veya eligibility dışı sinapslar replay tarafından dokunulmaz. Replay rastgele topology editor'a dönüşemez.

### Asymmetric update direction

```
strengthening (positive STDP via replay):
    delta_rate: SLOW
    requires: outcome alignment OR replay survival positive
    cap: per_synapse_strengthening_cap

weakening (decay/prune via replay):
    delta_rate: FASTER
    requires: counterfactual ablation showed unchanged outcome
              OR replay survival negative
    cap: per_synapse_weakening_cap
```

J §14'teki "false-positive dampening > positive strengthening" asymmetry pattern'i sleep replay'de de uygulanır.

### M1 audit

Her sinaps update için `SLEEP_REPLAY_SYNAPSE_UPDATE` event:

```
SleepReplaySynapseUpdateEvent
├── session_id
├── synapse_id
├── update_direction              # strengthen | weaken
├── delta_magnitude
├── eligibility_band              # fast | medium | slow
├── evidence_type                 # outcome | counterfactual | coherence
├── evidence_refs
└── observer_snapshot_ref
```

### Forbidden

- Eligibility dışı sinaps update
- Audit'siz update
- Cap bypass
- Topology change (synapse oluşturma/silme); sadece weight/trace update

---

## 11. Attention Habituation Replay Channel

### Principle

Replay session sırasında `attention_habituation_traces` (M0 alt-tipi) güncellenebilir. Sinaps topolojisine dokunmaz.

### B §19 ile uyumlu

```
habituation_key = assembly_id + context_signature
```

Replay bu habituation key'leri update edebilir:
- Bir assembly belirli context'te tekrar tekrar gereksiz pulse aldıysa → habituation artar
- Beklenmeyen kritik durumda assembly habituate'di → habituation azalır

### Update kuralı

```
Allowed if:
    replay session audited
    AND pulse history evidence var (M1'de WORKSPACE_PULSE event'leri)
    AND counterfactual ablation pulse'un faydalı/zararlı olduğunu test etti
    AND delta rate cap altında
```

### Asymmetric rates (J ile uyumlu)

- Gereksiz tekrarlanan pulse pattern'i için habituation artışı: hızlı
- Yanlış habituate olmuş kritik pattern için habituation düşüşü: yavaş (evidence gerekli)

### M1 audit

`ATTENTION_REPLAY_HABITUATION_UPDATE` event (F event catalog'da zaten var):

```
AttentionReplayHabituationUpdateEvent
├── session_id
├── assembly_id
├── context_signature_hash
├── habituation_delta
├── update_direction
├── evidence_refs
└── observer_snapshot_ref
```

### Forbidden

- Sinaps topolojisi değişimi (B §19 ile uyumlu — attention replay sinaps budamaz)
- Pulse_score formülünün doğrudan modifikasyonu
- Audit'siz update

---

## 12. Ingress Calibration Replay Channel

### Principle

J §13-14'teki learned mapping update mekanizmasının replay altındaki hali. Compiler'ın `M0 ingress_calibration_traces`'i replay session sırasında güncellenir.

### Allowed if

```
replay session audited
AND outcome_alignment_score OR replay_survival_score evidence var
AND per_mapping_daily_delta_cap altında
AND global_compiler_drift_cap altında
AND event_profile learned_mappings için açık
    (Observation: açık, Recall: kısıtlı, HumanIntent: KAPALI, InternalShock: KAPALI)
```

### M1 audit

`COMPILER_MAPPING_UPDATED` event (F + J'de zaten var):

```
CompilerMappingUpdatedEvent (replay context)
├── session_id                     # K replay session
├── trace_id
├── rule_family_id
├── update_direction
├── delta_magnitude
├── evidence_refs
├── replay_origin: true
└── observer_snapshot_ref
```

`replay_origin: true` field ile canlı outcome'lardan farkı görünür.

### Forbidden

- HumanIntent / InternalShock profile için update
- Drift cap bypass
- Audit'siz update
- Bootstrap rule'a (anayasal) update

---

## 13. Memory Verification Replay Channel

### Principle

Replay session sırasında M2 candidate'lar için `replay_survival_score` üretilir. Bu G §8 verification matrix'inde evidence axis olarak kullanılır.

### Allowed

```
- Var olan M2 candidate'ı al
- Counterfactual ablation uygula (§15)
- "Bu kayıt olmasaydı pattern aynı olur muydu?" testi
- Sonuç skoru üret
```

### `REPLAY_SURVIVAL_EVALUATED` event

```
ReplaySurvivalEvaluatedEvent
├── session_id
├── memory_record_id
├── subject_class
├── candidate_status_at_evaluation
├── replay_survival_score          # [0.0, 1.0]
├── ablation_method                # single_variable | pairwise
├── ablation_count
├── evidence_refs
└── observer_snapshot_ref
```

### Memory Write Gate ile bağlantı

G §10 evidence axes'te `replay_survival` zaten var. K bu skoru formalize eder:
- `replay_survival_score > threshold`: candidate verified yönünde evidence
- `replay_survival_score < threshold`: candidate quarantined veya rejected yönünde evidence

### Forbidden

- Replay survival score'un **outcome_alignment_score yerine** kullanılması (§14 ile ayrılmış)
- Score'un Memory Write Gate'i bypass etmesi (gate hâlâ verification matrix uygular)

---

## 14. Outcome Alignment Replay Channel

### Principle

Replay session sırasında geçmiş candidate'ların gerçek outcome'larla uyumu değerlendirilir.

### Allowed

```
- Geçmiş M2 candidate / verified kayıt al
- Pattern X gözlendi → kayıt Y öneriyor sayılır
- Gerçek outcome event Z geldi mi?
- Y'nin tahmin ettiği outcome ile Z uyuşuyor mu?
- outcome_alignment_score üret
```

### `REPLAY_OUTCOME_ALIGNMENT_EVALUATED` event

```
ReplayOutcomeAlignmentEvaluatedEvent
├── session_id
├── memory_record_id (or pattern_id)
├── predicted_outcome_signature
├── actual_outcome_refs            # gerçek outcome event'leri
├── alignment_score                # [0.0, 1.0]
├── time_lag_ms                    # tahmin ile outcome arası
└── observer_snapshot_ref
```

### Critical kural — counterfactual ≠ outcome alignment

> *`replay_survival_score` ≠ `outcome_alignment_score`*

| Concept | Kaynak | Tip |
|---------|--------|-----|
| `replay_survival_score` | Counterfactual ablation | Sentetik replay sonucu |
| `outcome_alignment_score` | Gerçek outcome feedback | Real-world evidence |

**Counterfactual sonucu outcome alignment evidence'i olarak sayılamaz.**

Forbidden:
- "Counterfactual ablation positive sonuç verdi → outcome_alignment positive sayılır"
- Sentetik test gerçek dünya geri bildirimini ikame eder

İki concept Memory Write Gate (G §10) evidence axes'te ayrı sütunlardır.

---

## 15. Counterfactual Ablation Rules

> *Sayısal sınırlar `REPLAY_PROTOCOL_NUMERICS.md` §8-9: higher_order_ablation_max_order = 2 (v0.1 constitutional invariant, `forbidden` change_class), max_single_variable_ablations_per_session, max_pairwise_ablations_per_session ≤ single × 0.5 (computed dependency), pairwise_causal_link_score_min eşiği.*

### Principle

> *Counterfactual replay = bounded ablation over recorded traces.*
> *Not free simulation.*
> *Not generative imagined history.*

### Branch limits

```
single_variable_ablation:
    default, allowed
    "Bu event olmasaydı pattern aynı olur muydu?"

pairwise_ablation:
    only for high-severity (permanent_with_snapshot) events
    "Bu iki event birlikte olmasaydı pattern nasıl olurdu?"

higher_order_ablation (>= 3 variables):
    FORBIDDEN in v0.1
    Kombinatorik patlama + hayali tarih riski
```

### Pairwise causal-link constraint

Pairwise ablation için **causal_refs ile bağlantılı** event çiftleri zorunlu:

```
pairwise_ablation allowed if:
    event_A.causal_refs contains event_B
    OR event_B.causal_refs contains event_A
    OR shared correlation_id within causal envelope
```

OBSERVER §13 "causal_refs 1-hop direct only" kuralıyla uyumlu — pairwise ablation 1-hop kapsamında kalır.

### Ablation method

```
Counterfactual ablation method:
    1. M1 snapshot pencere al
    2. Ablate edilecek event'leri "yok" işaretle
    3. Recorded trace'leri yeniden yürüt
    4. Sonuç pattern'i karşılaştır
    5. replay_survival_score üret
```

**Not:** Bu **deterministic** ablation. Model tahmini yok, LLM yorumu yok, sentetik veri üretimi yok. Sadece "şu kayıtlı event'i yokmuş gibi davran, sonra recorded trace'leri tekrar yürüt."

### `COUNTERFACTUAL_ABLATION_PERFORMED` event

```
CounterfactualAblationPerformedEvent
├── session_id
├── ablation_method                # single | pairwise
├── ablated_event_refs
├── causal_link_verified (pairwise için)
├── original_pattern_signature
├── ablation_pattern_signature
├── replay_survival_score
└── observer_snapshot_ref
```

### Forbidden

- Higher-order (>= 3) ablation
- Causal-link olmadan pairwise
- Generative simulation (LLM-based veya neural-net based hayali tarih)
- Counterfactual outcome alignment iddiası

---

## 16. Replay Survival Score

> *Sayısal eşikler `REPLAY_PROTOCOL_NUMERICS.md` §14, §16-17: min_replay_survival_score_for_evidence, min_replay_survival_sessions ≥ 2, min_session_separation_ms, max_replay_survival_weight_in_verification < outcome_alignment_weight_in_verification (real evidence dominance, computed dependency).*

### Tanım

`replay_survival_score` = counterfactual ablation testinden bir kayıt/pattern'in sağ çıkma derecesi.

### Hesaplama (kavramsal)

```
replay_survival_score = 
    similarity(original_pattern, ablation_pattern)

high score: pattern aynı kaldı (ablate edilen event önemli değildi)
low score:  pattern değişti (ablate edilen event önemliydi)
```

### Memory Write Gate'te kullanım

G §8 verification matrix'inde evidence axis:

```
source_trust verified için:
    ...
    AND replay_survival score above threshold
    ...
```

### Critical kural

> *replay_survival_score truth score değildir.*
> *Memory Write Gate bunu evidence axis olarak kullanır, tek başına verified yapmaz.*

### Forbidden

- Replay survival score'un "hakikat puanı" gibi yorumlanması
- Score'un gate decision'ı atlatmak için kullanılması
- Score'un outcome_alignment olarak işlenmesi

---

## 17. Replay Self-Deception Safeguards

### Principle

Replay self-deception kapısı olabilir. K bu kapıları **explicit kuralla** kapatır.

### Safeguard 1 — Replay direct M2 yazamaz

```
Replay session sonucu doğrudan M2 candidate yaratmaz.
M2'ye gidecekse:
    Replay → M1 audit + bounded M0 trace update
    Summarizer (F §5) → M1 pattern özetinden candidate önerir
    Memory Write Gate (G) → değerlendirir
    M2'ye verified yazılır
```

Direct path yok. Always through Memory Write Gate.

### Safeguard 2 — Replay output verified fact değildir

```
Replay tarafından üretilen tüm trace update'ler ve evidence axes
"replay-derived" olarak işaretlidir.
Memory Write Gate bunlara verified yetkisi vermez.
Sadece evidence axis olarak değerlendirir.
```

### Safeguard 3 — Replay live core'a dönmez (sandboxing)

§4'teki sandboxing kuralı. Replay session sırasında ne olursa olsun çekirdeğe duyusal event basılmaz.

### Safeguard 4 — Replay kendi sonucunu kanıt olarak kullanamaz

```
Replay session A'da üretilen evidence → Memory Write Gate'e gönderilir
Memory Write Gate verification matrix uygular
Replay session B yapılır
Session B session A'nın evidence'ini "kanıt" olarak alamaz (recursive amplification)
```

### Safeguard 5 — Counterfactual ≠ outcome (§14)

Sentetik test gerçek dünyayı ikame edemez.

### Kilit cümle

> *Replay kendi sonucuna inanamaz. Replay sonucu sadece denetlenebilir evidence olarak yaşar.*

### Violation Test
> *Replay direct olarak M2'ye verified record yazıyor mu?*
> *Replay output gate verification'ı bypass ediyor mu?*
> *Replay recursive olarak kendi evidence'ini kanıt yapıyor mu?*
>
> Birine "evet" ise ihlal.

---

## 18. Replay Events and Audit

### Canonical events

```
REPLAY_SESSION_STATUS_CHANGED        # canonical lifecycle (F event type discipline)
SLEEP_REPLAY_SYNAPSE_UPDATE          # zaten F'de var
ATTENTION_REPLAY_HABITUATION_UPDATE  # zaten F'de var
COMPILER_MAPPING_UPDATED             # zaten F/J'de var (replay context)
REPLAY_SURVIVAL_EVALUATED            # YENİ — memory verification channel
REPLAY_OUTCOME_ALIGNMENT_EVALUATED   # YENİ — outcome alignment channel
COUNTERFACTUAL_ABLATION_PERFORMED    # YENİ — counterfactual detail audit
```

### `REPLAY_SESSION_STATUS_CHANGED` canonical event

B/C/E/F/G/I disiplinine uyumlu — tek event tipi, alt durumlar field:

```
ReplaySessionStatusChangedEvent
├── event_id
├── event_type: REPLAY_SESSION_STATUS_CHANGED
├── event_family: ledger_meta            # session lifecycle artifact
├── session_id
├── old_status                            # requested | started | completed | aborted | budget_exhausted | failed
├── new_status
├── triggered_by                          # internal_pressure | sleep_rhythm | external_request
├── trigger_pressure_summary
├── replay_budget
├── replay_scope_summary
├── effect_channels_active
├── session_duration_ms
├── total_updates_count
├── total_ablations_count
└── observer_snapshot_ref
```

### Eski legacy: `REPLAY_SESSION_COMPLETED`

F event catalog'da `REPLAY_SESSION_COMPLETED` vardı. K bunu `REPLAY_SESSION_STATUS_CHANGED` (new_status: completed) altına alır. F event catalog'u patch'lenir.

### Permanence policy

```
(REPLAY_SESSION_STATUS_CHANGED, *)                    → permanent
(REPLAY_SESSION_STATUS_CHANGED, new_status=failed)    → permanent_with_snapshot
(SLEEP_REPLAY_SYNAPSE_UPDATE, *)                      → ring_buffer_only
(ATTENTION_REPLAY_HABITUATION_UPDATE, *)              → ring_buffer_only
(COMPILER_MAPPING_UPDATED, *)                         → permanent (J ile uyumlu)
(REPLAY_SURVIVAL_EVALUATED, *)                        → permanent
(REPLAY_OUTCOME_ALIGNMENT_EVALUATED, *)               → permanent
(COUNTERFACTUAL_ABLATION_PERFORMED, *)                → permanent
```

### Audit zorunluluğu

Sistem sonradan şunları cevaplayabilmeli:

- Hangi session ne zaman tetiklendi?
- Hangi channel'lar aktif çalıştı?
- Hangi M0 trace update'leri yapıldı?
- Hangi counterfactual ablation'lar uygulandı?
- Replay evidence Memory Write Gate'e gitti mi, sonuç ne oldu?

Cevap verilemiyorsa replay auditable değildir — Madde 7 ihlali.

---

## 19. Cross-document Anchors

| Belge | Bağlantı |
|-------|----------|
| `CONSTITUTION.md` Madde 2 | Sleep/replay causal pruning ana mekanizma |
| `CONSTITUTION.md` Madde 7 | Hafıza ayrılığı — replay M0 trace update sınırı |
| `MEMORY_CONTRACT.md` §14 (Open Questions) | Replay engine M0 etkisi — K ile formal |
| `ATTENTION_WORKSPACE.md` §19 | Attention replay habituation channel |
| `INGRESS_COMPILER_SPEC.md` §13-14 | Ingress calibration replay channel |
| `MEMORY_WRITE_GATE.md` §8 | Verification matrix evidence axes (replay_survival, outcome_alignment) |
| `MEMORY_WRITE_GATE.md` §10 | Evidence requirements |
| `OBSERVER_LEDGER_SCHEMA.md` §10 | Permanence policy |
| `OBSERVER_LEDGER_SCHEMA.md` §19 | Event catalog memory family |
| `BOOTSTRAP_GENOME.md` §17 | Sleep/replay rhythm trigger conditions |
| `BOOTSTRAP_GENOME.md` §16 | Plasticity replay_consolidation_state'e bağlı |
| `RECALL_PROTOCOL.md` §14 | Recall economy pattern'i (replay budget benzeri) |

---

## 20. Violation Tests

1. **Replay live core'a sensory event basıyor mu?** (§4)
   - Evet ise ihlal.
2. **Replay M2'ye doğrudan candidate veya verified record yazıyor mu?** (§17)
   - Evet ise ihlal.
3. **Replay sonucu outcome_alignment olarak sayılıyor mu?** (§14)
   - Evet ise ihlal. Counterfactual ≠ outcome.
4. **Counterfactual replay serbest alternatif tarih simülasyonu yapıyor mu?** (§15)
   - Evet ise ihlal. Bounded ablation only.
5. **Pairwise ablation causal-link olmadan yapılıyor mu?** (§15)
   - Evet ise ihlal.
6. **Higher-order ablation (>= 3) yapılıyor mu?** (§15)
   - Evet ise v0.1 ihlali.
7. **Replay eligibility trace dışındaki sinapslara update yapıyor mu?** (§10)
   - Evet ise ihlal.
8. **Replay update M1 audit olmadan M0'a dokunuyor mu?** (§10-12)
   - Evet ise ihlal.
9. **Replay budget/cooldown/fatigue yok mu?** (§9)
   - Evet ise ihlal.
10. **Replay survival score truth score gibi kullanılıyor mu?** (§16)
    - Evet ise ihlal.
11. **Replay HumanIntent veya InternalShock profile için mapping update yapıyor mu?** (§12)
    - Evet ise ihlal.
12. **Replay recursive olarak kendi evidence'ini kanıt yapıyor mu?** (§17 Safeguard 4)
    - Evet ise ihlal.
13. **Replay session ayrı engine'ler olarak mı tasarlanmış?** (§5)
    - Evet ise ihlal. Tek mekanizma, çoklu channel.
14. **Replay LLM/adapter tarafından tetikleniyor mu?** (§8)
    - Evet ise ihlal. Internal pressure veya sleep rhythm.
15. **Replay sinaps topolojisi değişimi (oluşturma/silme) yapıyor mu?** (§10)
    - Evet ise ihlal. Sadece weight/trace update.

---

## 21. Open Questions

K çerçevesi kapanırken cevaplanmamış bırakılan sorular:

- **Kesin sayısal değerler:** `max_iterations`, `refractory_period`, `replay_budget` cap'leri, `delta_rate_caps` → `REPLAY_PROTOCOL_NUMERICS.md` / implementation
- **Replay survival score formülü** — similarity metric ne (cosine, edit distance, pattern signature?)
- **Outcome time lag tolerance** — outcome ne kadar gecikebilir, hangi süreden sonra alignment evidence geçersiz?
- **Cross-channel replay session** — bir session'da birden fazla channel aktif olduğunda evidence ne kadar paylaşılır?
- **Failed replay session retry policy** — failed session ne kadar sonra tekrar denenebilir?
- **Replay snapshot retention** — replay'in kullandığı M1 snapshot'ları ekstra korumalı mı tutulur?
- **Multi-instance replay** — iki Sentinel instance'ı arasında replay evidence paylaşımı mümkün mü (cross-restore identity ile bağlantılı)?

Bu sorular implementation/numerics aşamasında cevaplanır.

---

## Çekirdek özet — 14 karar + 15 violation tests

### 14 karar
1. Replay geçmişi tekrar yaşatmaz; geçmişten kontrollü kanıt üretir.
2. Replay decision engine değildir; yeni hakikat yaratmaz.
3. Replay sandboxed'tır; live core'a duyusal event basamaz.
4. Tek replay mekanizması, çoklu effect channel (sleep_synapse, attention_habituation, ingress_calibration, memory_verification, outcome_alignment).
5. Replay input sadece M1 snapshot, M0 trace, outcome refs (LLM narrative ve unverified M2 yok).
6. Replay M2'ye doğrudan yazmaz; sadece gate'lere evidence axis sağlar.
7. Replay sinaps update sadece eligibility trace içinde, audited, evidence-bound.
8. Asymmetric update rates: dampening > strengthening, ikisi de capped.
9. Counterfactual ablation bounded: single-variable default, pairwise causal-linked, higher-order forbidden.
10. `replay_survival_score` ≠ `outcome_alignment_score`. Counterfactual sentetik, outcome gerçek.
11. Replay budget, cooldown, fatigue zorunlu.
12. Replay kendi sonucunu hakikat saymaz; recursive evidence loop forbidden.
13. Replay HumanIntent / InternalShock için mapping update yapamaz.
14. Tek canonical session event: `REPLAY_SESSION_STATUS_CHANGED` (B/C/E/F/G/I disiplini).

---

## Kilit cümleler

> **Replay geçmişi tekrar yaşatmaz. Replay geçmişten kontrollü kanıt üretir.**
>
> **Replay decision engine değildir. Replay yeni hakikat yaratmaz.**
>
> **Replay sandboxed'tır; live core'a sensory event basamaz.**
>
> **Replay kendi sonucuna inanamaz. Replay sonucu sadece denetlenebilir evidence olarak yaşar.**
>
> **Counterfactual replay = bounded ablation over recorded traces. Not free simulation. Not generative imagined history.**
>
> **`replay_survival_score` ≠ `outcome_alignment_score`. Sentetik test gerçek dünya geri bildirimini ikame edemez.**
>
> **Yanlış güçlenmiş izleri zayıflatmak, yeni güçlendirme yapmaktan hızlı olabilir. Ama hiçbir replay update rate cap ve evidence requirement bypass edemez.**
>
> **Replay engine tek. Replay etkileri kanala göre sınırlı.**

---

## Versiyon

- **v0.1** — 18 Mayıs 2026 — Frozen Draft. Conceptual phase. No implementation authority.
- `CONSTITUTION.md` Madde 2 / `MEMORY_CONTRACT.md` §14 alt-spec'i.
- A-J belgelerinin replay-channel sözleşmesi.
- Konuşma soyağacı: [`docs/conversations/0011-replay-protocol.md`](./docs/conversations/0011-replay-protocol.md)
