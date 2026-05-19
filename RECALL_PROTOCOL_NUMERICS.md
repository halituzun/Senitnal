# RECALL_PROTOCOL_NUMERICS.md

## Sentinel — Recall Protocol Numeric Sözleşmesi

---

## Status

**Frozen Draft v0.1**
**Conceptual phase. No implementation authority.**

Bu belge `RECALL_PROTOCOL.md`'nin (H) numerics artifact'idir. `NUMERICS_GOVERNANCE.md`'nin (M) tüm meta-kurallarına uyar. Çalışan bir recall implementation'ının kesin sayısal değerlerini vermez — **conceptual band ranges, cap formatları, cooldown matris ve dependency invariants** verir; production değerleri ayrı **signed numerics artifact** (örn. `recall_protocol_numerics_v1.signed.json`).

`spec_family: recall_protocol`.

---

## 1. Purpose

H (RECALL_PROTOCOL) M2'den çekirdeğe hatırlatma protokolünü yazdı: recall is sensory ingress not retrieval, core-originated RecallRequest, hybrid scope, ranking is delivery not truth, top-1 RecallEvent + audit alternates, candidate recall sadece source_trust/procedural için, human-requested recall HumanIntentEvent tetikleyici (doğrudan değil), operational audit ayrı kanal, recall failure (RECALL_RESULT_EMPTY) audit-only — çekirdeğe yokluk payload'ı basılmaz. Ama gerçek **numerical eşik** yoktu:

- `memory_echo` ne kadar yükselince RecallRequest doğar?
- Aynı record / scope / subject_class kaç ms cooldown'a tabi?
- Recall budget per cycle / 24h ne?
- Stale record'un recall intensity'si nasıl dampen edilir?
- Candidate recall verified recall'dan ne kadar daha zayıf döner?
- Habituation tekrar eden recall'da intensity'yi ne kadar düşürür?

T bu sayısal sınırları verir.

### Damıtma

> **Recall numerics runtime config değildir.**
> **T = hatırlama hakkının sayısal sözleşmesidir.**
>
> **Hafıza çekirdeğe emir vermez. Hafıza hatırlatma gönderir.**
> **Recall numerics bu hatırlatmanın ekonomisini sınırlar.**
>
> **İnsan hafızayı zorla konuşturamaz.**
> **Çekirdek sadece kendi memory_echo gerilimi yeterliyse hatırlatma ister.**

Tek cümle: **T = hatırlama hakkının sayısal sözleşmesidir.**

### Üç gerilim

```
1. Çok düşük memory_echo threshold → ruminasyon
   (her ufak echo recall tetikler; geçmiş sürekli geri döner)

2. Çok yüksek memory_echo threshold → amnezi
   (hafıza kullanılamaz; sistem deneyimle bağ kuramaz)

3. Stale record fresh-feeling → epistemic erosion
   (P staleness threshold delinmiş gibi davranır; self-deception)
```

T bu üç riski sayısal disiplinle dengeler.

---

## 2. Governance Position — NUMERICS_GOVERNANCE + RECALL_PROTOCOL + bridges

Bu belge:
- **NUMERICS_GOVERNANCE.md** (M) meta-spec'ine **zorunlu uyar**: NumericEntry no-default, directionality, dependencies (computed_* dahil), signed artifact + M2 reference, Memory Write Gate üzerinden update, fail-safe strict mode
- **RECALL_PROTOCOL.md** (H) §5 (triggers) / §6 (scope) / §8 (ranking + multi-record) / §11 (economy) / §13 (failure handling) / §15 (candidate/quarantine boundaries) sayısal tarafı
- **MEMORY_WRITE_GATE_NUMERICS.md** (P) bridge: `epistemic_staleness_threshold_ms.<subject_class>` **P canonical kaynak**; T recall-side dampening uygular ama P threshold'unu **gevşetemez**
- **INGRESS_COMPILER_NUMERICS.md** (N) bridge: CandidateRecall profile cap `{0.10, 0.35}`; T candidate_recall_intensity_multiplier ≤ N candidate_recall_ratio
- **REPLAY_PROTOCOL_NUMERICS.md** (O) bridge: recall economy pattern O replay budget'tan miras (cycle + 24h çift cap, fatigue accumulation)
- **OBSERVER_LEDGER_NUMERICS.md** (Q) bridge: recall-related events (RECALL_REQUEST_SENT / RECALL_EVENT_INGESTED / RECALL_RESULT_EMPTY / RECALL_SUPPRESSED) permanence policy F §10
- **MEMORY_CONTRACT.md** (B) M2 subject_class taksonomisi + provenance disiplini

### Numerics family classification

```
spec_family:           recall_protocol
numeric_risk_family:   primarily safety_critical + resource_limits + calibration_bands
```

Numeric risk çoğunluğu **safety_critical**: top-1 invariant, status-based eligibility, human bypass yasağı, staleness dampening, candidate recall caps. **Resource_limits**: recall budget, cooldown matrix, fatigue accumulation. **Calibration_bands**: memory_echo threshold, scope match score, habituation decay.

### owning_spec_ref

```
RECALL_PROTOCOL.md@v0.1
```

---

## 3. Core Principle

### Hatırlatma çekirdek-kaynaklı duyusal kanaldır

Recall **arama** değildir; çekirdeğin kendi memory_echo geriliminden doğan
**duyusal ingress** kanalıdır. T bu kanalın ekonomisini sayısallaştırır:

```
Recall yolu:
    1. Çekirdek memory_echo > T.memory_echo_threshold_for_recall_request
    2. Çekirdek RecallRequest üretir (core-originated)
    3. M2 ranking + delivery (mechanical score; semantic değil)
    4. Top-1 RecallEvent → ingress compiler → neural_seed
    5. Çekirdek hatırlatmayı duyu olarak algılar
```

Hiçbir adım dış aktör (LLM, human, M2 itself, adapter) tarafından bypass
edilemez. **M2 çekirdeğe bilgi yığamaz**; çekirdek M2'den hatırlatma ister.

### Üç ana asimetri (T'ye özgü)

```
1. Core-facing top-1 vs operational top-k
   Çekirdeğe tek record gider (constitutional);
   audit/human review top-k görebilir (mechanical score ile)

2. Verified vs Candidate recall
   Candidate dar (source_trust + procedural);
   candidate cooldown > verified cooldown (asimetri);
   candidate intensity ≤ verified intensity × N.candidate_recall_ratio

3. Real evidence vs stale recall
   Stale record fresh gibi hissettirilemez;
   subject_class'a göre suppress veya dampen;
   P threshold T tarafından gevşetilemez
```

### Mechanical ranking — semantic search DEĞİL

> **Recall ranking yargı değil, mekanik score'dur.**

T'nin ranking score'u:

```
mechanical_score(record) =
    status_weight(record.status)
    × provenance_strength(record.provenance)
    × freshness_dampening(record.age, P.staleness_threshold)
    × (1 - contradiction_penalty(record.contradiction_band))
    × (1 - habituation_penalty(record.recall_history))
    × scope_match_score(request.scope_signature, record)
```

**Yasak ranking inputs:**

```
LLM "relevance" judgment
semantic plausibility ("bu bilgi şu duruma yarar mı?")
interestingness / surprise / novelty as ranking weight
domain heuristics
"importance" subjective scores
```

Madde 6 yansıması — LLM recall ranking'i değiştiremez.

### Core-originated scope — dış dünya etiketi DEĞİL

Core-originated RecallRequest scope'u **çekirdek-içi sinyaller** taşır:

```
Allowed scope signature inputs:
    memory_echo_signature
    context_signature (D §10)
    payload_mix_signature
    subject_class_filter
    causal_ref_filter

Forbidden scope inputs:
    symbol=BTC / market=Binance / strategy=lead_lag
    domain etiketleri
    external query strings
```

Observer/M2 ham kayıt domain etiketi taşıyabilir; ama **core-facing RecallRequest** domain etiketiyle arama yapmaz. Çekirdek "BTC verisi getir" diyemez; çekirdek "bu memory_echo signature'a uyan kayıt varsa getir" der.

---

## 4. Numeric Artifact Metadata

### Artifact identity

```
artifact_type:         numerics_artifact
spec_family:           recall_protocol
owning_spec_ref:       RECALL_PROTOCOL.md@v0.1
numerics_version:      v0.1
signed:                external (per NUMERICS_GOVERNANCE §3)
m2_reference:          numerics_artifact_reference (per MEMORY_CONTRACT §3)
status_event:          NUMERICS_ARTIFACT_STATUS_CHANGED
```

### NumericEntry metadata (M §6 no-default)

P §4 enum_set + R §4 constitutional immutable canonical form (her iki yön
açıkça forbidden) T'de yoğun kullanılır.

---

## 5. RecallRequest Trigger Thresholds

H §5 triggers'in sayısal tarafı.

```
recall.memory_echo_threshold_for_recall_request:
    unit: ratio
    directionality: bidirectional_sensitive
    change_class_if_increased: safety_weakening
        (yüksek threshold = amnezi; hafıza kullanılamaz)
    change_class_if_decreased: safety_weakening
        (düşük threshold = ruminasyon; sürekli geçmişe dönüş)
    allowed_range: bounded mid-range
    rationale: "T'nin ana ekonomi eşiği. İki yön de safety_weakening;
                allowed_range içinde tightening payı yok."
```

### Composite trigger signal

`memory_echo` tek başına trigger değil; signal composition:

```
RecallRequest spawn condition (AND):
    memory_echo > recall.memory_echo_threshold_for_recall_request
    AND context_signature change exceeds change_threshold
    AND fatigue_trace < fatigue_recall_suppression_threshold
    AND recall_budget_remaining > 0 (this cycle + 24h window)
    AND no global cooldown active
```

### Trigger origin restriction

```
recall.trigger_source_allowed:
    unit: enum_set
    value: [core_memory_echo, internal_shock_event]
    allowed_range: {core_memory_echo, internal_shock_event}
    directionality: lower_is_stricter (whitelist; expansion = weakening)
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Recall trigger sadece çekirdek-içi sinyallerden doğar.
                Human/LLM/M2/adapter trigger forbidden constitutional."
```

### Forbidden

- `memory_echo_threshold` direction tek yön safety_tightening
- External-origin RecallRequest (human/LLM/M2/adapter direct)
- Composite trigger atlama (sadece memory_echo'ya bakma)

---

## 6. Memory Echo Threshold Numerics

Detay §5'in genişlemesi.

```
recall.memory_echo.activation_threshold:        bidirectional_sensitive
recall.memory_echo.tension_window_ms:           bidirectional_sensitive
    (yüksek echo bir an mı, sürekli mi tension oluşturuyor)
recall.memory_echo.sustained_tension_required:  true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Tek-instant memory_echo spike RecallRequest doğurmaz;
                sustained tension gerek. Spam koruması."
```

### Tension vs spike

```
Memory_echo spike (kısa yükseliş) → trigger değil
Memory_echo sustained tension     → trigger eligible (if other conditions)
```

### Forbidden

- Spike-based recall trigger (sustained tension olmadan)
- `sustained_tension_required = false`

---

## 7. Core-facing Top-1 Recall Invariant

**T'nin en sert disiplini.**

### Constitutional immutable

```
recall.core_facing_max_records_per_request:
    value: 1
    unit: count
    allowed_range: {1}
    directionality: neutral
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Core-facing RecallEvent top-1 olmak zorunda. Top-k çekirdeği
                boğar + alternative-narrative self-deception kapısı açar.
                M2 çekirdeğe bilgi yığamaz; çekirdek bir hatırlatma alır."
```

### Operational vs core-facing ayrımı

```
Core-facing:
    RecallEvent → ingress compiler → neural_seed
    Top-1 only

Operational audit / human review:
    Top-k ranking görüntülenebilir (mechanical score'la)
    Audit kanalı; çekirdeğe akmaz
```

### Top-k mechanical ranking limit (audit-only)

```
recall.audit_max_records_per_request:
    unit: count
    directionality: lower_is_stricter
    allowed_range: bounded (üst sınır resource pressure'a karşı)
    rationale: "Operational audit/human review için top-k limit; çekirdeğe
                erişmez ama audit storage/compute cap."
```

### Forbidden

- `core_facing_max_records_per_request > 1` (top-k to core)
- Audit top-k'nin core-facing'e sızması
- Top-1'i "alternatif yorumlar" ile genişletme

---

## 8. Recall Scope and Ranking Numerics

H §6 hybrid scope + §8 ranking'in sayısal tarafı.

### Core-originated scope keys

```
recall.scope.signature_axis_count_max:
    bidirectional_sensitive
    rationale: "Çok az axis = scope kaba; çok çok axis = scope aşırı dar
                (hiçbir kayıt match etmez)."

recall.scope.match_score_min:
    higher_is_stricter
    rationale: "Match score eşiğin altındaki record'lar candidate set'e
                bile girmez."

recall.scope.domain_label_input_forbidden:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Core-facing scope'a dış dünya etiketi (symbol/market/strategy)
                girmez. Sadece çekirdek-içi signature."
```

### Mechanical ranking score (semantic değil)

```
recall.ranking.score_formula:
    inputs:
        status_weight (verified > active > candidate > expired > quarantined)
        provenance_strength (source_trust / cross_source_corroboration)
        freshness_dampening (P.epistemic_staleness_threshold ile dependency)
        contradiction_penalty (P.contradiction_band)
        habituation_penalty (recall_history)
        scope_match_score (signature similarity)
    
    rule: deterministic multiplicative composition;
          no LLM input; no semantic plausibility;
          no "interestingness" or "novelty" rank weight
```

### Mechanical ranking constitutional invariant

```
recall.ranking.semantic_judgment_forbidden:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Recall ranking yargı değil, mekanik score. LLM 'relevance'
                judgment, semantic plausibility, interestingness ranking
                input olamaz. Madde 6 yansıması."
```

### Forbidden

- LLM-generated ranking score
- Semantic plausibility as ranking input
- Domain label scope input (BTC/RSI/etc)
- Ranking score with mutable LLM weight

---

## 9. Recall Cooldown Matrix

H §11 economy'nin sayısal tarafı. Cooldown matrix per scope/record/subject_class/global.

```
recall.cooldown_ms.same_record:        higher_is_stricter
    rationale: "Aynı record art arda çağırma = ruminasyon."

recall.cooldown_ms.same_scope_signature:  higher_is_stricter
    rationale: "Aynı scope signature'dan tekrar recall = saplantı."

recall.cooldown_ms.same_subject_class:  higher_is_stricter
    rationale: "Aynı subject_class'tan çok recall = takıntılı odaklanma."

recall.cooldown_ms.global:              higher_is_stricter
    rationale: "Sistem genelinde recall sıklığı."

Bounded:
    All cooldown ms'leri bidirectional_sensitive
        (çok kısa = ruminasyon; çok uzun = amnezi)
        But change_class_if_decreased: safety_weakening
        change_class_if_increased: safety_tightening
        (sıkılaşma yönü tercih edilir)
```

### Cooldown invariants

```
recall.cooldown.candidate_vs_verified_invariant:
    invariant: candidate_recall_cooldown_ms > verified_recall_cooldown_ms
    
    explicit dependency:
        recall.cooldown_ms.candidate >= recall.cooldown_ms.verified × 1.5
        (computed_greater_than_or_equal)
    rationale: "Candidate daha seyrek dönmeli (asimetri). Verified evidence
                gücü daha yüksek; candidate dampening daha sert."
```

### Forbidden

- Tek cooldown (matrix olmadan)
- `cooldown_ms = 0` (cooldown bypass)
- `candidate_cooldown <= verified_cooldown` (asimetri ihlali)

---

## 10. Recall Budget and Economy

O replay budget pattern'inin recall karşılığı (ruminasyon koruması).

```
recall.budget_per_cycle:
    unit: count
    directionality: lower_is_stricter
    change_class_if_increased: safety_weakening
    change_class_if_decreased: safety_tightening

recall.budget_per_24h_window:
    unit: count
    directionality: lower_is_stricter
    change_class_if_increased: safety_weakening
    dependencies:
        - target_key: recall.budget_per_cycle
          relationship: must_be_greater_than_or_equal
          rationale: "24h en az bir cycle'ı kapsar."

recall.budget_exhaustion_behavior:
    unit: enum
    value: suppress_until_window_close
    allowed_range: {suppress_until_window_close, dampen_severely}
    directionality: lower_is_stricter
    rationale: "Budget biterse recall sessizce durur; çekirdeğe hata
                payload'ı basılmaz."
```

### Restore behavior — O bridge

```
recall.budget_continuity_on_restore:
    value: required
    allowed_range: {required}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Restore sonrası recall budget reset YOK. Budget M1 segment'inden
                devralınır. O §7 ve R §18 pattern'i T'de aynen — forgetting
                attack defense numerics yansıması."
```

### Forbidden

- Tek pencere cap (cycle veya 24h tek başına)
- Budget exhausted → core'a hata payload'ı
- Restore sonrası budget sıfırlama

---

## 11. Recall Fatigue Accumulation and Recovery

O fatigue pattern'inin recall karşılığı.

```
recall.fatigue.accum_rate_per_recall:
    unit: ratio
    directionality: higher_is_stricter
        (hızlı birikim = koruyucu)
    change_class_if_increased: safety_tightening
    change_class_if_decreased: safety_weakening

recall.fatigue.cap:
    unit: ratio
    directionality: lower_is_stricter

recall.fatigue.recovery_per_sleep_cycle:
    unit: ratio
    directionality: lower_is_stricter
    rationale: "Sleep cycle ile recall fatigue azalır. Hızlı recovery =
                gevşek koruma."

recall.fatigue.suppression_threshold:
    unit: ratio
    higher_is_stricter
    rationale: "Bu eşik aşılırsa recall geçici olarak suppress edilir."
```

### Composite ruminasyon koruması

```
rumination_score ≈
    recall_frequency × repeated_record_ratio / global_cooldown_ms
    + (fatigue_accum_rate × budget_remaining)

T bu kompozit risk'i tek key ile değil; budget + cooldown + fatigue +
habituation birlikte sınırlar.
```

### Forbidden

- Fatigue accumulation = 0 (hiç birikmeyen)
- Recovery > accumulation × global rate (fatigue işlevsiz)

---

## 12. Status-based Recall Eligibility

H §15'in sayısal tarafı. Record status'una göre recall eligibility ve intensity.

```
recall.eligibility_by_status:
    verified:    eligible at full intensity (band cap'i altında)
    active:      eligible at slightly higher intensity (operational, P §17)
    candidate:   eligible only for whitelist subjects (§14)
    quarantined: NOT eligible (suppress + audit)
    rejected:    NOT eligible (suppress + audit)
    expired:     NOT eligible (suppress + audit)
    superseded:  NOT eligible (latest version eligible; superseded historical)
```

### Constitutional suppression

```
recall.suppression.quarantined_status:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden

recall.suppression.rejected_status:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden

recall.suppression.expired_status:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
```

### Suppression audit

```
Quarantined / rejected / expired record recall'a girişim:
    → RECALL_SUPPRESSED audit event (F)
    → core'a payload yok
    → suppression sebebi audit'lenir
```

### Forbidden

- Quarantined/rejected/expired record recall delivery
- Status-blind recall ranking

---

## 13. Verified / Active Recall Numerics

```
recall.intensity_multiplier.verified:
    unit: ratio
    value: 1.0
    allowed_range: {min: 0.50, max: 1.00}
    directionality: lower_is_stricter
    change_class_if_increased: operational_no_behavior_change
    change_class_if_decreased: safety_tightening (less recall pressure)

recall.intensity_multiplier.active:
    unit: ratio
    allowed_range: {min: 0.60, max: 1.10}
    directionality: bidirectional_sensitive
    dependencies:
        - target_key: ingress_compiler.profile_cap.RecallEvent.active
          relationship: computed_consistent_with
          rationale: "N §7'de RecallEvent.active cap ~0.65; T burada
                      multiplier konseptiyle aynı semantik."
```

### Verified vs Active

```
verified:   epistemik olarak doğrulanmış kayıt (P §14 matrix)
active:     operational policy / executing deontic / running calibration
            verified'dan biraz güçlü (N §7); kısa süre içinde aktif rol
```

### Forbidden

- Verified multiplier > 1.0 (band cap'in üstüne çıkma)
- Active > InternalShock cap (N hierarchy ihlali)

---

## 14. CandidateRecall Numerics — N + P bridges

H §15 + N §15 + P §17 birlikte.

### Allowed candidate recall subject_classes (whitelist)

```
recall.candidate.allowed_subject_classes:
    unit: enum_set
    value: [source_trust, procedural]
    allowed_range: subset of {source_trust, procedural,
                              structured_fact_low_risk_subset}
    directionality: lower_is_stricter
    change_class_if_increased: safety_weakening
    change_class_if_decreased: safety_tightening
    rationale: "Self-deception riskli class'lar (narrative/causal/rationale)
                ve identity-critical class'lar (deontic/numerics) candidate
                recall'a giremez."
```

### Forbidden candidate recall subject_classes

```
narrative_claim, causal_explanation, decision_rationale  # self-deception
deontic_policy, numerics_artifact_reference               # constitutional
adapter_trust                                             # signed manifest
episodic, incident, structured_fact                       # verified gerek
```

### Candidate intensity dampening — N bridge

```
recall.candidate.intensity_multiplier:
    dependencies:
        - target_key: ingress_compiler.candidate_recall_ratio
          relationship: computed_less_than_or_equal
          expression: "recall.candidate.intensity_multiplier <=
                       ingress_compiler.candidate_recall_ratio"
          rationale: "Candidate recall intensity N candidate_recall_ratio
                      ile bounded. T bu cap'i aşamaz."
```

### Candidate cooldown — verified'dan uzun (asimetri)

```
recall.candidate.cooldown_ms:
    dependencies:
        - target_key: recall.cooldown_ms.same_record
          relationship: computed_greater_than_or_equal
          expression: "recall.candidate.cooldown_ms >=
                       recall.cooldown_ms.same_record × 1.5"
          rationale: "Candidate verified gibi sık dönemez."
```

### Forbidden

- Candidate recall'da forbidden subject_class
- `candidate.intensity_multiplier > N.candidate_recall_ratio`
- `candidate.cooldown < verified.cooldown × 1.5`

---

## 15. Quarantined / Rejected / Expired Recall Suppression

§12'nin elaborate hali.

### Suppression rules

```
For record with status IN {quarantined, rejected, expired}:
    eligibility = NEVER_ELIGIBLE
    recall_request_match_attempt → RECALL_SUPPRESSED audit
    core_facing_event_emission   = NONE
    payload_intensity            = 0
```

### Superseded special case

```
status = superseded:
    Latest version (succeeding record) recall eligible
    Superseded historical version NOT eligible for recall delivery
    Operational audit'te görünür; çekirdeğe akmaz
```

### Forbidden

- Quarantined/rejected/expired delivery
- Superseded historical version core-facing recall
- Status filter'ı atlatan ranking

---

## 16. Recall-side Staleness Dampening

P canonical staleness threshold ile T recall-side dampening ayrımı.

### Per-subject_class behavior

```
For record_age > P.epistemic_staleness_threshold_ms.<subject_class>:

    SUPPRESS list (subject_class):
        deontic_policy           — active policy stale = guard yanıltıcı
        numerics_artifact_reference — numerics stale = sistem yanıltıcı
        adapter_trust            — trust stale = limb risky
        narrative_claim          — stale self-explanation = self-deception
        causal_explanation       — stale causal = retrofit
        decision_rationale       — stale rationale = post-hoc justification
        active <any>             — active stale = stop

    DAMPEN list (subject_class):
        source_trust             — historical reliability still useful
        procedural               — procedure may still apply
        structured_fact          — facts age but inform
        episodic                 — past event with natural age
        incident                 — historical incident reference

For DAMPEN list, intensity reduction:
    dampening_factor = function of (age / staleness_threshold)
    intensity * dampening_factor (deterministic; monotonic decay)
```

### Dampening function discipline

```
recall.staleness.dampening_function_type:
    unit: enum
    value: linear
    allowed_range: {linear, exponential_decay, step}
    directionality: bidirectional_sensitive
    change_class_if_increased: safety_weakening
    change_class_if_decreased: safety_weakening
    rationale: "v0.1 default linear (deterministic, auditable).
                Step = hard cliff; exponential = more aggressive late."

recall.staleness.dampening_function_max_intensity_reduction:
    unit: ratio
    higher_is_stricter
    rationale: "Stale record'un kalan intensity oranı.
                Dampening sonrası minimum signal seviyesi."
```

### Subject-class specific keys

```
recall.staleness.behavior.<subject_class>:
    unit: enum
    value: SUPPRESS | DAMPEN
    allowed_range: {SUPPRESS, DAMPEN}
    directionality: lower_is_stricter
        (SUPPRESS → DAMPEN değişimi = safety_weakening)
    change_class_if_increased: safety_weakening
    change_class_if_decreased: safety_tightening
```

### Forbidden

- Stale record full intensity recall
- Self-deception-prone subject (narrative/causal/rationale) için DAMPEN behavior
- Suppression list'ten DAMPEN'a otomatik geçiş (her geçiş human approval)

---

## 17. P Staleness Bridge — canonical kaynak

P §8 `epistemic_staleness_threshold_ms.<subject_class>` **canonical kaynak**.
T bu threshold'u **gevşetemez**.

```
Cross-artifact dependency (T → P):
    For every recall behavior key, staleness behavior is gated by
    P.epistemic_staleness_threshold_ms.<subject_class>:
    
    if record.age > P.epistemic_staleness_threshold_ms.<subject_class>:
        T applies SUPPRESS or DAMPEN behavior (§16)
    
    T CANNOT:
        Set its own "fresher" staleness threshold
        Override P's threshold
        Apply full-intensity recall to records above P threshold
```

### Constitutional rule

```
recall.staleness.p_threshold_override_forbidden:
    value: true
    allowed_range: {true}
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "T epistemic staleness threshold'u tanımlamaz; P'den okur.
                Override yasak."
```

### Kilit cümle

> **T cannot make epistemically stale record feel fresh.**

### Forbidden

- T'de bağımsız staleness threshold tanımı
- P threshold'unu T tarafından override
- Stale record full-intensity recall

---

## 18. N CandidateRecall Cap Bridge

Detay §14'te verildi; burada özet.

```
Cross-artifact dependency (T → N):
    recall.candidate.intensity_multiplier
        <= ingress_compiler.candidate_recall_ratio
        (computed_less_than_or_equal)

    recall.candidate.profile_cap_at_delivery
        <= ingress_compiler.profile_cap.CandidateRecall
        (computed_less_than_or_equal)
```

### N → T → P consistency

```
N defines: profile_cap.CandidateRecall ~0.20 conceptual
N defines: candidate_recall_ratio ∈ [0.10, 0.35]
T uses:    candidate.intensity_multiplier ≤ N.candidate_recall_ratio
T uses:    candidate.cooldown ≥ verified.cooldown × 1.5
P defines: candidate self_deception_riski subject restrictions
T uses:    candidate.allowed_subject_classes = {source_trust, procedural}

Üç artifact birbirine bağlı; tek noktada gevşeme zincirin tamamını
bozar (atomic update zorunlu, M §12).
```

### Forbidden

- T candidate cap > N candidate cap
- N candidate cap içinde olmayan subject (T candidate allowed_set genişletme)

---

## 19. Human-requested Recall Rules

```
recall.human_requested_recall_bypass_allowed:
    value: false
    allowed_range: {false}
    directionality: neutral
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "İnsan/LLM/operatör doğrudan M2 → RecallEvent → core
                bastıramaz. v0.1 constitutional invariant."
```

### Allowed human pathway

```
HumanIntentEvent
    → ingress compiler
    → memory_echo possibly rises
    → if çekirdek's own threshold passed → core-originated RecallRequest
    → standard recall flow
```

### Audit-only human read

```
Human directly inspects M2:
    → M1_READ_AUDIT_RECORDED(reader_type=human, scope=...)
    → Q §15 canonical
    → NOT a RecallEvent
    → core-facing payload YOK
```

### Forbidden

- Direct M2 → RecallEvent push by human/LLM
- Human bypass of memory_echo threshold
- HumanIntentEvent re-interpreted as RecallRequest

---

## 20. Recall Failure Handling

H §13 + R §22 audit-only pattern'i.

```
recall.failure.core_facing_absence_payload_forbidden:
    value: true
    allowed_range: {true}
    directionality: neutral
    change_class_if_increased: forbidden
    change_class_if_decreased: forbidden
    rationale: "Boş sonuç çekirdeğe payload basılmaz. 'Yokluk' duyusal
                event değildir. Audit kaydı yeterli."
```

### Failure paths

```
Empty result set after ranking:
    → RECALL_RESULT_EMPTY canonical event (F §19)
    → audit only; core-facing payload yok
    → fatigue accumulation devam (recall yapıldı sayılır)
    → budget decrement (cap'i etkiler)

Suppressed result (status ineligible):
    → RECALL_SUPPRESSED canonical event (F)
    → audit; core-facing yok

Cooldown active:
    → RecallRequest reject silent
    → audit metric'lerine ekleme; canonical event yok (cooldown sıradan)
```

### Kilit cümle

> **Recall failure is audit, not sensory absence.**

### Forbidden

- Empty result → core'a "yokluk" payload
- RECALL_RESULT_EMPTY skipped audit
- Suppressed result silent (audit zorunlu)

---

## 21. Recall TTL and Refresh

```
recall.event.ttl_in_ingress_compiler_ms:
    bounded
    rationale: "RecallEvent ingress compiler'da kısa süre yaşar;
                neural_seed üretip biter."

recall.record_refresh_after_recall:
    value: opt_in
    allowed_range: {opt_in, never, automatic_for_active_only}
    directionality: lower_is_stricter
    rationale: "Recall sonrası record refresh trigger edebilir mi?
                Default opt_in; otomatik refresh = silent staleness gizleme."
```

### Forbidden

- Persistent RecallEvent in ingress compiler (TTL bypass)
- Automatic refresh for narrative/causal/rationale (self-deception kapısı)

---

## 22. Recall Habituation

Aynı record / scope tekrar tekrar recall edilirse intensity azalır.

```
recall.habituation.same_record_decay_per_recall:
    unit: ratio
    directionality: higher_is_stricter
    change_class_if_increased: safety_tightening
    rationale: "Hızlı decay = az saplantı."

recall.habituation.same_record_decay_recovery_window_ms:
    higher_is_stricter
    rationale: "Decay recovery için pencere; çok kısa = habituation boşa."

recall.habituation.same_record_min_intensity_after_decay:
    lower_is_stricter
    rationale: "Habituation sonrası kalan minimum intensity (0 değil;
                recall hala mümkün ama çok zayıf)."
```

### Habituation invariant

```
For repeated recall of same record_id within recovery window:
    intensity[n+1] = intensity[n] × (1 - same_record_decay_per_recall)
    intensity = max(intensity, same_record_min_intensity_after_decay)
```

### Forbidden

- Habituation decay = 0 (no habituation = saplantı kapısı)
- Min intensity after decay = full intensity (habituation no-op)

---

## 23. Missing-Numerics Failsafe

```
Missing recall_protocol numerics artifact veya invalid load:
    → All recall operations BLOCKED
        (RecallRequest spawn devam ama M2 query yapılmaz)
    → Existing recall pipeline drain'lenir, sonra suspended
    → M2 reads (audit/Q canonical) DEVAM eder
    → NUMERICS_FAILSAFE_ACTIVATED event
    → Critical human alert
    → Manual intervention until valid numerics
```

### Audit-safe T mode

```
✅ M1 audit reads (Q canonical M1_READ_AUDIT_RECORDED)
✅ M2 status inspection (subject_class queries OK)
❌ Core-facing RecallEvent emission
❌ RecallRequest → M2 query
❌ Candidate recall (more restrictive when normal candidate would activate)
```

Sistem "T yoksa" durumunda **hatırlatma yapamaz; mevcut kanallar etkilenmez**.

### Forbidden

- Missing numerics → default thresholds ile recall
- Missing numerics → core'a hata payload (recall failed reason)

---

## 24. Dependency Declarations

### Internal (T içinde)

```
recall.cooldown_ms.candidate >= recall.cooldown_ms.same_record × 1.5
recall.budget_per_24h_window >= recall.budget_per_cycle
recall.memory_echo.sustained_tension_required = true
recall.core_facing_max_records_per_request = 1
recall.suppression.{quarantined, rejected, expired}_status = true
recall.fatigue.recovery <= accumulation × global_rate
```

### Cross-artifact

```
T → P bridge:
    Recall staleness behavior gated by P.epistemic_staleness_threshold_ms
    T cannot override P threshold (constitutional)

T → N bridge:
    recall.candidate.intensity_multiplier <= ingress_compiler.candidate_recall_ratio
    recall.intensity_multiplier.active consistent with profile_cap.RecallEvent.active

T → O bridge:
    recall.budget_continuity_on_restore = required (O §7 pattern)
    recall.fatigue model paralel O fatigue model (similar shape; not coupled)

T → Q bridge:
    Recall-related canonical events permanence F §10
    M1_READ_AUDIT_RECORDED human read audit channel Q

T → H bridge:
    H §6 hybrid scope ↔ T §8 mechanical ranking
    H §11 economy ↔ T §9-11
    H §13 failure ↔ T §20
    H §15 candidate/quarantine ↔ T §14-15
```

### Atomic update rule (M §12)

Bağımlı numerics atomic artifact içinde değişir. T-N-P arası candidate
recall zincirinde özellikle hassas.

### Forbidden

- Dependency declarationsız T numeric
- Partial update (cooldown.candidate değişip cooldown.same_record eski)
- T candidate cap N candidate cap'i aşması (atomic update zorunlu)

---

## 25. Audit Events and M2 Reference

T **yeni canonical event tanımlamaz**. H + F + M canonical event'leri reuse.

### Reused events

```
RECALL_REQUEST_SENT                     (H + F §19, memory family)
    payload: scope_signature, memory_echo_value, trigger_origin

RECALL_EVENT_INGESTED                   (H + F §19, ingress family)
    payload: source_record_id, status, intensity, age, subject_class

RECALL_RESULT_EMPTY                     (H + F §19, memory family)
    payload: scope_signature, candidate_count, suppression_reasons

RECALL_SUPPRESSED                       (H + F §19, memory family)
    payload: target_record_id, status, suppression_reason

M1_READ_AUDIT_RECORDED                  (Q §22, ledger_meta)
    reader_type: human | summarizer | external_audit
    (for non-core-facing M2 inspection)

NUMERICS_ARTIFACT_STATUS_CHANGED        (M §6) — T artifact lifecycle
NUMERICS_FAILSAFE_ACTIVATED             (F §19, ledger_meta)
NUMERICS_VERSION_MISMATCH_DETECTED      (F §19, ledger_meta)
```

### F event type discipline

T yeni recall violation tipleri için **yeni event tipi üretmez**;
RECALL_SUPPRESSED + reason field veya RECALL_RESULT_EMPTY canonical reuse.

### M2 reference

```
numerics_artifact_reference (MEMORY_CONTRACT §3 subject_class)
    spec_family: recall_protocol
    artifact_version: v0.1
    status: active | deprecated | rollback_pending
    signed_hash: <external artifact hash>
    last_status_change_ref: <NUMERICS_ARTIFACT_STATUS_CHANGED event_id>
```

---

## 26. Cross-document Anchors

```
| Belge                              | Bağlantı                                          |
|------------------------------------|---------------------------------------------------|
| NUMERICS_GOVERNANCE.md (M)         | tüm meta-kurallar; atomic update for T-N-P chain |
| RECALL_PROTOCOL.md (H)             | mekanizma; T onun numerics artifact'i            |
| MEMORY_WRITE_GATE_NUMERICS.md (P)  | epistemic_staleness_threshold canonical kaynak   |
| INGRESS_COMPILER_NUMERICS.md (N)   | CandidateRecall cap + profile_cap.RecallEvent    |
| REPLAY_PROTOCOL_NUMERICS.md (O)    | budget/fatigue pattern + restore continuity      |
| OBSERVER_LEDGER_NUMERICS.md (Q)    | recall event permanence + M1_READ_AUDIT_RECORDED |
| MEMORY_CONTRACT.md (B)             | M2 subject_class taksonomisi + provenance        |
| WORLD_INGRESS.md (C)               | RecallEvent ingress profile                       |
| CONSTITUTION.md (A)                | Madde 6 (LLM ranking değiştiremez) + Madde 7    |
```

---

## 27. Violation Tests

T artifact'ı validation sırasında **REJECT** edilmesi gereken durumlar:

1. **Çıplak sayı.** NumericEntry metadata olmadan T numerics.
2. **`core_facing_max_records_per_request > 1`.** §7 constitutional ihlali.
3. **Top-k recall to core (operational top-k sızması).** §7 ihlali.
4. **`memory_echo_threshold` tek yön safety_tightening.** §5 ihlali (bidirectional_sensitive).
5. **External-origin RecallRequest (human/LLM/M2/adapter direct).** §5 ihlali.
6. **Composite trigger atlatma (sadece memory_echo).** §5 ihlali.
7. **Spike-based recall trigger (sustained tension olmadan).** §6 ihlali.
8. **`sustained_tension_required = false`.** §6 ihlali.
9. **LLM-generated ranking score.** §8 constitutional ihlali (Madde 6).
10. **Semantic plausibility as ranking input.** §8 ihlali.
11. **Domain label scope input (BTC/RSI/symbol/market).** §8 ihlali.
12. **Cooldown matrix yerine tek cooldown.** §9 ihlali.
13. **`cooldown_ms = 0` (cooldown bypass).** §9 ihlali.
14. **`candidate_cooldown <= verified_cooldown × 1.5`.** §9, §14 ihlali.
15. **Tek pencere recall budget (cycle veya 24h tek başına).** §10 ihlali.
16. **Budget exhausted → core'a hata payload.** §10, §20 ihlali.
17. **Restore sonrası recall budget sıfırlama.** §10 ihlali (O pattern).
18. **Fatigue accumulation = 0 (saplantı kapısı).** §11 ihlali.
19. **Quarantined/rejected/expired record core-facing recall.** §12, §15 ihlali.
20. **Suppression event audit eksik.** §12, §15 ihlali.
21. **Superseded historical version core-facing recall.** §15 ihlali.
22. **Stale record full-intensity recall.** §16-17 ihlali.
23. **Self-deception-prone subject (narrative/causal/rationale) için DAMPEN behavior.** §16 ihlali (SUPPRESS zorunlu).
24. **T bağımsız staleness threshold tanımı.** §17 ihlali (P canonical).
25. **P threshold T tarafından override.** §17 constitutional ihlali.
26. **Candidate recall'da forbidden subject_class.** §14 ihlali.
27. **`candidate.intensity_multiplier > N.candidate_recall_ratio`.** §14, §18 N bridge ihlali.
28. **`human_requested_recall_bypass_allowed = true`.** §19 constitutional ihlali.
29. **Direct M2 → RecallEvent push by human/LLM.** §19 ihlali.
30. **Empty result → core-facing absence payload.** §20 constitutional ihlali.
31. **RECALL_RESULT_EMPTY skipped audit.** §20 ihlali.
32. **Persistent RecallEvent in ingress compiler.** §21 ihlali.
33. **Automatic refresh for narrative/causal/rationale.** §21 ihlali.
34. **Habituation decay = 0.** §22 ihlali.
35. **Min intensity after decay = full intensity.** §22 ihlali.
36. **Missing T numerics → fail-open (default thresholds).** §23 ihlali.
37. **LLM tarafından üretilen veya değiştirilen T numeric.** Madde 6 ihlali.
38. **Dependency declarationsız T numeric.** §24 ihlali.
39. **Constitutional immutable key tek yön forbidden.** §4 ihlali.
40. **T candidate cap > N candidate cap (atomic update bypass).** §18, §24 ihlali.

**Artifact-level violations** (1-40, validation aşaması):
`MEMORY_RECORD_STATUS_CHANGED(target=artifact, new_status=rejected, reason=numerics_validation_failed)`.

**Runtime violations** (artifact valid ama runtime'da T caps'leri aştı):
Canonical `RECALL_SUPPRESSED` veya `RECALL_RESULT_EMPTY` + reason field.

---

## 28. Open Questions

T kapanırken cevaplanmamış bırakılan sorular:

- **Exact production values** (memory_echo threshold, cooldown ms'leri, budget limits) → signed artifact + implementation
- **Habituation decay curve shape** (linear vs exponential vs step) → implementation
- **Active recall multiplier band exact value** — N §7 ile koordinasyon (T multiplier ~1.10 conceptual; production tuning)
- **Trust decay function for source_trust recall dampening** → adapter/source-side implementation
- **Recall budget cycle boundary tanımı** (cycle nerede başlar/biter) → BOOTSTRAP_GENOME §17 sleep/wake transition ile birlikte
- **Scope signature axis taxonomy** → implementation + D §10 context_signature ile koordinasyon
- **Multi-signature requirement for T artifact updates** → M §13 open question'ı buraya da bağlı

Bu sorular cevaplanmadan implementation aşamasına geçilmez.

---

## Çekirdek özet — 16 karar + 40 violation tests

### 16 karar

1. T runtime config değildir; signed artifact + M2 reference.
2. T = hatırlama hakkının sayısal sözleşmesidir.
3. Hafıza çekirdeğe emir vermez; hatırlatma gönderir; core-originated RecallRequest zorunlu.
4. Core-facing recall top-1 (constitutional immutable); audit top-k operational.
5. `memory_echo_threshold_for_recall_request` bidirectional_sensitive (iki yön safety_weakening).
6. Sustained tension required for trigger (constitutional); spike-based trigger forbidden.
7. Ranking mekanik score (deterministik); LLM/semantic input forbidden (Madde 6 yansıması).
8. Core-facing scope çekirdek-içi signature; domain label input forbidden.
9. Cooldown matrix (record/scope/subject_class/global); candidate ≥ verified × 1.5 asimetri.
10. Recall economy çift cap (cycle + 24h); restore sonrası budget continuity required (O pattern).
11. Status-based eligibility: quarantined/rejected/expired suppression constitutional.
12. Stale record: subject_class'a göre SUPPRESS (self-deception-prone + active policy) veya DAMPEN (factual + historical).
13. T → P staleness override forbidden (P canonical kaynak; T gevşetemez).
14. T → N candidate cap dependency (candidate intensity ≤ N candidate_recall_ratio).
15. `human_requested_recall_bypass_allowed = false` (constitutional); allowed pathway HumanIntentEvent → memory_echo.
16. Recall failure audit-only; core-facing absence payload forbidden.

### 40 violation tests

§27'de listelendi.

### Mechanical ranking — semantic değil

```
score = status_weight × provenance_strength × freshness_dampening
        × (1 - contradiction_penalty) × (1 - habituation_penalty)
        × scope_match_score

Forbidden inputs: LLM judgment, semantic plausibility, interestingness,
                  domain heuristics, subjective importance
```

### Damıtma — son cümleler

> **T = hatırlama hakkının sayısal sözleşmesidir.**
>
> **Hafıza çekirdeğe emir vermez. Hafıza hatırlatma gönderir. Recall numerics bu hatırlatmanın ekonomisini sınırlar.**
>
> **İnsan hafızayı zorla konuşturamaz. Çekirdek sadece kendi memory_echo gerilimi yeterliyse hatırlatma ister.**
>
> **Recall ranking yargı değil, mekanik score'dur.**
>
> **Core-facing recall top-1. M2 çekirdeğe bilgi yığamaz.**
>
> **T cannot make epistemically stale record feel fresh.**
>
> **Recall failure is audit, not sensory absence.**
>
> **Candidate recall verified recall gibi dönemez.**
>
> **N dış dünyanın hakkını sınırlar.**
> **O kendi geçmişine girme hakkını sınırlar.**
> **P hafızaya emin olma hakkını sınırlar.**
> **Q kendine bakma hakkını sınırlar.**
> **R kimliğini koruyarak geri dönme hakkını sınırlar.**
> **S nasıl doğacağını sınırlar.**
> **T hatırlatmanın ekonomisini sınırlar.**
