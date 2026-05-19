# Sentinel

> *Proje kodadı: **Sentinel**. Repo slug: **Senitnal**.*

> Bir trading bot değil. Sonradan trading yeteneği takılabilecek bir yapay zihinsel çekirdek.

**Status: Frozen Draft v0.1 — Conceptual documentation phase. No code yet.**

Sentinel'in amacı; sermaye korumacı, şüpheci, çelişkiyi taşıyabilen, kanıtsız kesinleşmeyen, kendi kararlarını gerekçelendiren bir AGI çekirdeği inşa etmektir.

Çekirdek **önce var olur**, sonra dış dünya bağlanır. Borsa, Telegram, panel, emir motoru, strateji — hepsi sonradan **adaptör** olarak takılır; hiçbiri çekirdeğin parçası değildir.

---

## Sentinel ne değildir

- LLM-controlled trading bot değildir
- Strateji motoru değildir
- Otomatik sinyal jeneratörü değildir
- "Hızlıca kar üretmek" projesi değildir
- Akademik spiking neural network simülasyonu değildir
- Halüsinasyona izin veren bir sohbet katmanı değildir

## Sentinel nedir

- Üzerine yetenekler monte edilebilen bir **karar zekâsı**
- Düşünen, hatırlayan, şüphe eden, simüle eden, kararını gerekçelendiren bir çekirdek
- **Sermayeyi korumayı** her şeyin önünde tutan bir varlık
- **Audit edilebilir**; her karar observer ledger'da geriye doğru izlenebilir
- **Hesap verebilir**; "neden böyle düşündü?" sorusu cevaplanabilir
- **Plastik**; deneyimle değişir, ama temel anayasası sabittir

---

## Çekirdek özet — beş cümle

1. **Nöron renk taşır.**
2. **Sinaps yol hafızası taşır.**
3. **Assembly anlam taşır.**
4. **Self-field basınç yapar.**
5. **Deontic gate sınır çizer.**

Üstüne iki kontrol cümlesi:

6. **Observer kanıtlar.**
7. **LLM tercüme eder.**

---

## Anayasa — 7 madde

1. Nöron homojen denklem + heterojen payload + receptor yorumlama
2. Sinaps anlam taşımaz, akış deseninin hafızasını taşır
3. Doğuş minimum genome ile — sıfır değil, modül de değil
4. Düşüncede paralellik, niyette rekabet, eylemde tekleşme
5. Self-field soft pressure, deontic gate hard stop
6. LLM dış tercümandır; çekirdeğin parçası değildir
7. Hafıza ayrılığı — M0/M1/M2/M3 birbirine geçmez

Detay: [`CONSTITUTION.md`](./CONSTITUTION.md)

---

## Felsefe

Sentinel iki temel sezgi üzerine kuruludur:

**Sezgi 1 — Anlam akış deseninde doğar.**

Anlam ne tek nöronda yaşar, ne sinapsta, ne global modülde. Anlam **devrenin kendisidir**. Bir fikir, tekrar çağrılabilen, iç tutarlılığı yüksek, replay testinden geçen stabil bir nöral assembly'dir. Bir defa yanan desen gürültüdür; geri dönebilen ve işe yarayan desen fikirdir.

**Sezgi 2 — Zekânın belirtisi durabilmektir.**

Zekânın en açık belirtisi harekete geçmek değil, kendini durdurabilmek. Bu yüzden Sentinel'in en sık verdiği karar `ALLOW` değil, `WAIT` ve `BLOCK` olmalıdır. Sistem şunu sormadan eyleme geçmez:

- Ne biliyorum?
- Neye inanıyorum? Neden inanıyorum?
- Neyi bilmiyorum?
- Yanılırsam ne olur?
- Hiçbir şey yapmazsam ne olur?
- Geçmişte buna benzeyen ne oldu?

Bu soruları sormayan sistem AGI değil, sadece otomasyondur.

---

## Mevcut durum — Conceptual Documentation Phase

**Henüz kod yok ve uzun süre olmayacak.** Proje şu an mimari ve felsefi tasarım aşamasındadır. Düşünmek, konuşmak, belgelemek; sonra inşa etmek. Bütün belgeler **Frozen Draft v0.1 / no implementation authority** statüsündedir — kod bunlardan değil, sonraki implementation belgelerinden türetilecektir.

### Tamamlanmış

- [x] `CONSTITUTION.md` v0.1 — 7 maddelik temel anayasa (Principle / Rationale / Allowed / Forbidden / Violation Test formatında)
- [x] `MEMORY_CONTRACT.md` v0.1 — M0-M3 hafıza sınır anayasası, Memory Write Gate (epistemic), CandidateMemoryRecord statüleri, M2 `subject_class` alt-türleme
- [x] `ATTENTION_WORKSPACE.md` v0.1 — Madde 4 alt-spec'i: homojen WORKSPACE_PULSE, pulse imzası (tip değil), dissonant attention, InternalShockEvent ayrımı
- [x] `WORLD_INGRESS.md` v0.1 — Dış dünya giriş sınırları: 4 ingress profile (Observation/Recall/HumanIntent/InternalShock), IngressEventEnvelope, deterministic compiler, SourceTrustRecord M2 alt-tipi
- [x] `BOOTSTRAP_GENOME.md` v0.1 — Madde 3 alt-spec'i: doğum anayasası, initial M0/M1/M2/M3 state, SELF_GENESIS şeması, payload modulation reflexes, plasticity yaş-değil-state-based, constitutional shift policy (3 compatibility class)
- [x] `DEONTIC_GATE.md` v0.1 — Madde 5 alt-spec'i: anayasal eylem çıkış sınırı, 11 constitutional declarative, DeonticPolicyRecord (M2 alt-tipi), block classification (routine/safety/constitutional), bypass attempt iki-seviyeli audit, kill-switch graduated deactivation
- [x] `OBSERVER_LEDGER_SCHEMA.md` v0.1 — M1 detayı: ObserverEvent envelope (audit/causal/body/integrity), recorder/summarizer rol ayrımı, event type vs field disiplini, deterministic permanence policy table (no-default), snapshot window policy + deterministic sampling, hash chain, read/write permission matrix, 7 event family (ledger_meta dahil)
- [x] `MEMORY_WRITE_GATE.md` v0.1 — Madde 7 / MEMORY_CONTRACT §9 alt-spec'i: epistemik fren (deontic gate ≠), subject_class × evidence axes verification matrix, self-deception detection mekaniği, statü makinesi (candidate/verified/active/quarantined/superseded/rejected/expired), human writes vs system writes ayrımı (auto-verified vs matrix-required), silent gate (çekirdeğe geri yansıma yok), `MEMORY_RECORD_STATUS_CHANGED` canonical event
- [x] `RECALL_PROTOCOL.md` v0.1 — Madde 7 / MEMORY_CONTRACT §5-6 alt-spec'i: M2'den çekirdeğe hatırlatma protokolü (Memory Write Gate'in çift kapısı), recall is sensory ingress not retrieval, core-originated RecallRequest, hybrid scope, ranking is delivery not truth, top-1 RecallEvent + audit alternates, candidate recall sadece source_trust/procedural için capped intensity, human-requested recall HumanIntentEvent tetikleyici (doğrudan değil), operational audit ayrı kanal, recall failure (RECALL_RESULT_EMPTY) audit-only — çekirdeğe yokluk payload'ı basılmaz
- [x] `ADAPTER_MANIFEST_SPEC.md` v0.1 — Dış uzuv kontratı: immutable signed manifest, adapter type yok / capability surface var, capability flags + channel bindings (explicit yetki haritası), capability incompatibility matrix (security separation), `execute → observe` required pair (efference-only scope), execution capability hard constraints, `AdapterTrustRecord` M2 alt-tipi (SourceTrust ile linked ama farklı), tek canonical `ADAPTER_MANIFEST_STATUS_CHANGED` lifecycle event, adapter raw payload üretir / neural_seed üretemez
- [x] `INGRESS_COMPILER_SPEC.md` v0.1 — WORLD_INGRESS §13 alt-spec'i: structured event → neural_seed deterministic mapping, RuleFamily format (condition bands + base_payload_vector + scalar_modifiers + caps), authority matrix (Observation açık / Recall kısıtlı / HumanIntent kapalı / InternalShock kapalı), learned mappings M0 ingress_calibration_traces, mapping update sadece outcome/replay evidence ile, asymmetric rates (false-positive dampening > strengthening), conflict resolution = weighted blend + cap (semantik winner yok), hybrid bounded raw normalization, rule family lifecycle (active/deprecated/archived), `COMPILER_RULE_FAMILY_STATUS_CHANGED` ayrı canonical event
- [x] `REPLAY_PROTOCOL.md` v0.1 — Madde 2 / MEMORY_CONTRACT §14 alt-spec'i: replay geçmişten kontrollü kanıt üretir (re-living değil, decision engine değil), tek replay mekanizması / 5 effect channel (sleep_synapse + attention_habituation + ingress_calibration + memory_verification + outcome_alignment), sandboxed (live core'a sensory event basamaz), bounded counterfactual ablation (single-variable default, pairwise causal-linked, higher-order yasak), `replay_survival_score` ≠ `outcome_alignment_score` (sentetik vs gerçek), eligibility-trace constraint sinaps updates için, asymmetric rates (dampening > strengthening, ikisi de capped), self-deception safeguards (M2'ye doğrudan yazamaz, recursive evidence yasak), `REPLAY_SESSION_STATUS_CHANGED` canonical lifecycle event
- [x] `BACKUP_STRATEGY.md` v0.1 — MEMORY_CONTRACT §13/§14 alt-spec'i: backup kimlik sürekliliği sözleşmesidir (dosya kopyalama değil), modular artifacts (M0Snapshot/M1Segment/M2Snapshot) + RestoreManifest atomic composition, identity continuity matrix (same identity için M0+M1 birlikte gerek), M1 continuous backup ilkesi, M0 point-in-time consistent snapshot zorunlu, `restore_with_missing_history` degraded identity mode (M0 var M1 yok, operational_mode restricted), replay-derived trace provenance backup'ta korunur, foreign M2 merge whitelist+blacklist (narrative/causal/decision_rationale yasak; bootstrap_reference/structured_fact/procedural izinli), `foreign_instance_origin` provenance kalıcı taşınır, fork_birth/migration_birth detayları, forgetting attack defense (`FORGETTING_ATTACK_SUSPECTED` event, M1 silinemez), 7 canonical events (BACKUP_ARTIFACT/RESTORE_OPERATION/M2_FOREIGN_MERGE_STATUS_CHANGED + M1_HISTORY_LOST_AT_RESTORE + FORK_FROM_INSTANCE + MIGRATION_FROM_INSTANCE + FORGETTING_ATTACK_SUSPECTED)
- [x] `NUMERICS_GOVERNANCE.md` v0.1 — A-L numeric meta-spec: numerics runtime config değil signed artifact + M2 reference (ADAPTER_MANIFEST pattern), NumericEntry no-default kuralı (allowed_range + unit + directionality + change_class + owning_spec_ref zorunlu), 6 numeric family (safety_critical/resource_limits/calibration_bands/identity_retention/operational_convenience/experimental), directionality her key'de metadata (higher_is_stricter/lower_is_stricter/bidirectional_sensitive/neutral), tightening vs weakening sınıflandırma (weakening human approval zorunlu), numeric dependency declaration + atomic multi-key update, static numerics ≠ learned calibration (static, learned'ın cap'i), Memory Write Gate integration (yeni gate yok, G §8 matrix satırı), fail-safe strict mode (missing/invalid → fail-open değil), restore numerics versioning (sessiz uygulama yok), rollback sadece previous verified (forward yasak), `NUMERICS_ARTIFACT_STATUS_CHANGED` canonical + `NUMERICS_VERSION_MISMATCH_DETECTED` + `NUMERICS_FAILSAFE_ACTIVATED` events
- [x] `INGRESS_COMPILER_NUMERICS.md` v0.1 — J (INGRESS_COMPILER_SPEC) numerics artifact: deterministic soft-overlap band cutoffs (linear membership, hard ≤ low ≤ medium ≤ high ≤ hard; fuzzy/LLM yok), profile-specific intensity caps anayasal hierarchy ile (Observation ~1.00 ≥ InternalShock ~0.90 refractory-protected ≥ RecallEvent verified ~0.60 ≥ HumanIntentEvent ~0.35 ≥ RecallEvent candidate ~0.20), profile-relative payload seed base magnitudes (her payload key'in 4 profile için ayrı baseline'ı), payload-specific per-key caps, staleness scalar yalnız dampens never amplifies, weighted blend cap order (event-cap → bootstrap blend → learned modulation → final clip; forced re-normalization yok), candidate_recall_ratio ≤ 0.35 conceptual max, learned mapping drift caps asymmetric (false-positive dampening > strengthening; weakening cap < strengthening cap), missing/invalid numerics → strict mode (fail-open yasak; M defaults reuse), spec_family ingress_compiler, owning_spec_ref INGRESS_COMPILER_SPEC.md@v0.1, 20 violation test
- [x] `REPLAY_PROTOCOL_NUMERICS.md` v0.1 — K (REPLAY_PROTOCOL) numerics artifact: replay budget runtime config değil signed sayısal sözleşme (max_session_duration_ms / max_events_per_session / max_counterfactual_branches / replay_cooldown_ms / replay_fatigue_accum_rate, hepsi lower_is_stricter veya higher_is_stricter), çift cap (max_sessions_per_cycle + max_sessions_per_24h_window), restore sonrası budget reset YOK (M1 segment'inden devralma, L forgetting attack defense numerics yansıması), higher_order_ablation_max_order=2 v0.1 constitutional invariant (change_class_if_increased: forbidden; artifact alanında geçilemez, REPLAY_PROTOCOL.md spec revision gerek), pairwise ablation causal_link_score_min eşiği + max_pairwise ≤ max_single × 0.5 (computed_less_than_or_equal), M0 update asimetri (per_synapse_strengthening_cap ≤ per_synapse_weakening_cap; weakening daha hızlı), eligibility_trace_window dışı sinaps update yasak, N bridge (`ingress_calibration_replay_delta_cap ≤ N.per_mapping_daily_delta_cap × 0.30` — replay N drift cap'lerini back-door'dan gevşetemez), replay survival ≠ truth (min 2 bağımsız session, min_session_separation_ms, self-confirmation guard), `max_replay_survival_weight_in_verification < outcome_alignment_weight_in_verification` (real evidence dominance), outcome_alignment external outcome_ref zorunlu (internal-only ref sayılmaz; L self-corroboration koruması), `replay_can_trigger_replay_max_chain_depth = 0` allowed_range {min: 0, max: 0} constitutional immutable, missing numerics → strict audit-safe mode (sleep_synapse/habituation/calibration/verification update kapalı, sadece outcome_alignment read-only), spec_family replay_protocol, owning_spec_ref REPLAY_PROTOCOL.md@v0.1, 22 violation test
- [x] `MEMORY_WRITE_GATE_NUMERICS.md` v0.1 — G (MEMORY_WRITE_GATE) numerics artifact: per-subject_class TTL matrix (`candidate_max_age_ms`, `quarantine_max_age_ms`, `refresh_required_window_ms`, `epistemic_staleness_threshold_ms` — global "quarantine ≥ candidate" invariant YOK, subject-spesifik dependency: source_trust/adapter_trust quarantine ≥ candidate, narrative_claim/causal_explanation/decision_rationale quarantine ≤ candidate), G-bridge (G §8 verification matrix'inde tanımlı her (subject_class, evidence_axis) çiftinin P'de NumericEntry'e karşılık gelmesi zorunlu; eksik kombinasyon artifact REJECT), evidence count = independent source count (aynı kaynaktan 5 ölçüm = 1; temporal separation single-session bias'a karşı), contradiction band'leri (N reuse deterministic soft-overlap) + verified stickiness asimetrisi (`demote_required > promote_max`; DEONTIC §18 epistemic karşılığı), `supersede_confidence_delta_min > 0` strict (tek gözlem verified rekoru devirmez), L bridge self-deception numerics (`max_internal_only_ref_ratio.<subject_class>` + `external_corroboration_min_count >= 1` narrative/causal/rationale için), O bridge (`max(replay_survival_weight.*) ≤ O.max_replay_survival_weight_in_verification`; per-subject `replay_survival_weight < outcome_alignment_weight`), constitutional-immutable replay_survival_weight = 0 (deontic_policy/incident/adapter_trust/numerics_artifact_reference için allowed_range {min:0, max:0}), human-write whitelist enum_set NumericEntry (`auto_verified ∪ matrix_required = subject_universe`; world_claim ayrımı hard invariant), `numerics_artifact_reference` candidate TTL en kısa (sistem strict mode'dan hızla çıkmalı), O staleness canonical bağ kapandı (`outcome_alignment.max_wait_ms ≤ epistemic_staleness_threshold_ms.<sc>`), missing numerics → strict_no_verified mode (verified üretimi DISABLED, mevcut verified read-only), enum_set convention M §8'e eklendi, spec_family memory_write_gate, owning_spec_ref MEMORY_WRITE_GATE.md@v0.1, 30 violation test

### Sıradaki (operasyonel specification belgeleri)
- [ ] `OBSERVER_LEDGER_NUMERICS.md` — snapshot windows, sampling thresholds, segment sizes
- [ ] `BACKUP_STRATEGY_NUMERICS.md` — RPO/RTO, retention windows, restore timeout
- [ ] `BOOTSTRAP_GENOME_NUMERICS.md` — kesin genome parametreleri
- [ ] `RECALL_PROTOCOL_NUMERICS.md` — top-k candidate set boyutu, recall cooldown'lar
- [ ] `ADAPTER_TRUST_NUMERICS.md` — trust score band'ları, decay rate'leri

Sıralama tasarım sohbetinin akışına göre değişebilir.

### Uzak hedef (kod aşaması)

- [ ] Minimum Viable Brain — hiçbir aksiyon almayan ama her input'a gerekçeli BLOCK/WAIT cevabı veren çekirdek
- [ ] Echo Adapter — sahte uzuv, sadece test için
- [ ] İlk gerçek adaptörler

Kod aşamasına geçmeden önce yukarıdaki tasarım belgelerinin tamamlanması beklenir.

---

## Repo yapısı

```
Senitnal/
├── README.md              # Bu dosya
├── CONSTITUTION.md         # 7 maddelik anayasa
├── MEMORY_CONTRACT.md      # M0-M3 hafıza sınırları
├── LICENSE                # Apache 2.0
├── .gitignore
└── docs/                  # Detay belgeleri (yazılacak)
    └── conversations/     # Tasarım konuşmalarının arşivi
```

---

## Katkı politikası

Bu proje şu an sadece belgeleme aşamasındadır. Herhangi bir pull request veya issue için:

- Önerinin `CONSTITUTION.md`'deki 7 maddeyi ihlal etmemesi gerekir
- İhlal eden öneriler ya reddedilir ya da resmi revizyon süreciyle anayasa güncellenir
- Revizyon süreci tartışma → gerekçe → yeni metin → versiyon artırımı → tarih notu sırasını takip eder

Anayasa, dokunulmaz olduğu için değil, dokunulmazlığı korumak için ciddiye alındığı için çalışır.

---

## Lisans

Apache 2.0 — bkz. [`LICENSE`](./LICENSE)
