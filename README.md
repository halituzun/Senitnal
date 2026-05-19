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

## Mevcut durum — Build Phase (MVB)

**Conceptual + numerics design phase kapandı.** 22 frozen draft v0.1 belge
+ 2 review + 1 build plan tamamlandı. **Implementation başladı.**

Şu an: **Minimum Viable Brain (MVB)** inşası.

```
Implementation status:
  ✓ Commit 1:  Project skeleton (pyproject.toml + CI + sentinel/ package layout)
  ⏳ Phase 1:  Contracts as Code (Pydantic schemas + invariant test suite)
  ⏳ Phase 2:  Observer Ledger (M1 JSONL + hash-chain)
  ⏳ Phase 3:  Numerics Loader (8 dev fixtures + validation)
  ⏳ Phase 4:  Ingress Compiler skeleton
  ⏳ Phase 5:  Minimal M0 Tissue
  ⏳ Phase 6:  Workspace Pulse
  ⏳ Phase 7:  Gates (Deontic + Memory Write stubs)
  ⏳ Phase 8:  Recall Skeleton
  ⏳ Phase 9:  EchoAdapter
  ⏳ Phase 10: End-to-end Dry Simulation
```

### MVP red lines (CI-enforced)

```
- No BUY/SELL/EXECUTE outputs (output set: {WAIT, BLOCK, MONITOR, NEED_RECALL, NO_ACTION})
- No live exchange APIs (ccxt/binance/btcturk dependencies forbidden)
- No LLM integration (openai/anthropic/langchain forbidden — Madde 6)
- No M2 verified production (candidate-only writes in MVP)
- No replay-driven memory update (replay engine DEFERRED)
- No cross-instance / fork / migration paths
```

### Build references

- [`docs/build/0001-minimum-viable-brain-plan.md`](./docs/build/0001-minimum-viable-brain-plan.md) — 10-phase implementation roadmap
- [`docs/reviews/0001-phase-closure-consistency-review.md`](./docs/reviews/0001-phase-closure-consistency-review.md) — 22 belge cross-document GREEN
- [`docs/reviews/0002-implementation-readiness.md`](./docs/reviews/0002-implementation-readiness.md) — readiness labels + open questions triage

### Design phase — Tamamlanmış (22 belge frozen draft v0.1)

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
- [x] `MEMORY_WRITE_GATE_NUMERICS.md` v0.1 — G (MEMORY_WRITE_GATE) numerics artifact: per-subject_class TTL matrix (`candidate_max_age_ms`, `quarantine_max_age_ms`, `refresh_required_window_ms`, `epistemic_staleness_threshold_ms` — global "quarantine ≥ candidate" invariant YOK, subject-spesifik dependency: source_trust/adapter_trust quarantine ≥ candidate, narrative_claim/causal_explanation/decision_rationale quarantine ≤ candidate), G-bridge (G §8 verification matrix'inde tanımlı her (subject_class, evidence_axis) çiftinin P'de NumericEntry'e karşılık gelmesi zorunlu; eksik kombinasyon artifact REJECT), evidence count = independent source count (aynı kaynaktan 5 ölçüm = 1; temporal separation single-session bias'a karşı), contradiction band'leri (N reuse deterministic soft-overlap) + verified stickiness asimetrisi (`demote_required > promote_max`; DEONTIC §18 epistemic karşılığı), `supersede_confidence_delta_min > 0` strict (tek gözlem verified rekoru devirmez), L bridge self-deception numerics (`max_internal_only_ref_ratio.<subject_class>` + `external_corroboration_min_count >= 1` narrative/causal/rationale için), O bridge (`max(replay_survival_weight.*) ≤ O.max_replay_survival_weight_in_verification`; per-subject `replay_survival_weight < outcome_alignment_weight`), constitutional-immutable replay_survival_weight = 0 (deontic_policy/incident/adapter_trust/numerics_artifact_reference için allowed_range {min:0, max:0}), human-write whitelist enum_set NumericEntry (`auto_verified ∪ matrix_required = subject_universe`; world_claim ayrımı hard invariant), `numerics_artifact_reference` candidate TTL en kısa (sistem strict mode'dan hızla çıkmalı), O staleness canonical bağ kapandı (`outcome_alignment.max_wait_ms ≤ epistemic_staleness_threshold_ms.<sc>`), missing numerics → strict_no_verified mode (verified üretimi DISABLED, mevcut verified read-only), enum_set convention M §8'e eklendi, spec_family memory_write_gate, owning_spec_ref MEMORY_WRITE_GATE.md@v0.1, 32 violation test
- [x] `OBSERVER_LEDGER_NUMERICS.md` v0.1 — F (OBSERVER_LEDGER_SCHEMA) numerics artifact: ring buffer window per family (neural/attention/ingress/memory/deontic/replay/ledger_meta) + min_event_lifetime_in_buffer_ms floor, snapshot pre/post window sayısal family hierarchy (constitutional ≥ operational ≥ high_frequency), deterministic sampling strategies enum {none, hash_mod_deterministic, every_nth_event, time_bucket_first_last} — semantic_importance/llm_selected/observer_selected/random_unseeded forbidden; sampling sadece ring_buffer high-frequency event_type için (permanence event_type-level, family-level değil); sampling ≠ lossless compaction constitutional ayrım; production artifact strategy explicit zorunlu (M no-default), runtime strict fallback ≠ default NumericEntry; sampling summary entry permanent zorunlu (sessiz drop yasak), permanent log segment caps + `lossless_required = true` allowed_range {true} constitutional immutable, hash_chain_checkpoint_interval + `verify_on_read_required = true` constitutional, permanence policy monotonic invariant (permanent → ring_buffer_only YASAK; permanent_with_snapshot → permanent YASAK; weakening direction forbidden across artifact versions), storage tier hierarchy (hot/warm/cold) lossless transition invariant + tier_cold.retention = lifetime, storage pressure failsafe (high-frequency sampling tighten + critical alert; permanent event drop YASAK), critical alert types için `suppression_window_ms = 0` constitutional + `first_alert_immediate = true` constitutional + batch summary discipline, M1 reader identity matrix (human/llm/replay/summarizer/external_audit ayrı cap'ler; `max_batch_size.llm < human/replay/summarizer` computed dependency; LLM read scope enum_set whitelist; every LLM read audited — canonical `M1_READ_AUDIT_RECORDED` + reader_type field), foreign event reception caps + trusted_source_whitelist + quarantine_window (L forgetting attack defense numerics yansıması), meta-event recursion `max_depth = 2` (allowed_range max=5 constitutional upper), compaction `lossless_required + hash_verify_before_and_after_required` constitutional + mismatch → abort + critical alert, ring_buffer.window_ms ve snapshot pre/post her iki yön safety_weakening (operational değil), missing Q numerics → strict audit-safe mode (permanent writes continue; sampling/compaction/tier_transition/LLM read DISABLED), iki yeni canonical event F'ye eklendi: `LEDGER_STATE_CHANGED` (reason field — sampling_activated/sampling_summary_written/compaction_*/hash_*/tier_transition_performed/storage_pressure_failsafe/llm_read_scope_violation/meta_event_recursion_blocked/foreign_event_rejected_unknown_source/human_alert_batch_summary/failsafe_activated) ve `M1_READ_AUDIT_RECORDED` (reader_type field), normal read audit ≠ ledger state change disiplini, spec_family observer_ledger, owning_spec_ref OBSERVER_LEDGER_SCHEMA.md@v0.1, 16 karar + 34 violation test
- [x] `BACKUP_STRATEGY_NUMERICS.md` v0.1 — L (BACKUP_STRATEGY) numerics artifact: kimlik sürekliliğinin sayısal sözleşmesi; M1 RPO mode = continuous_replication constitutional immutable + WAL lag operational (bounded ms) vs chain_gap_tolerance_events = 0 constitutional ayrımı; M1Segment retention = lifetime constitutional (Q monotonic invariant ile uyumlu) + `tier_transition_lossless_required = true` Q §13 reuse; M0 snapshot consistency invariants constitutional (`snapshot_consistency_required = true`, `partial_assembly_state_unsealed_max_count = 0`, `snapshot_requires_replay_idle_or_sealed = true`) + sealed_checkpoint kuralı (replay in_session sırasında M0 snapshot ABORT); RestoreManifest validation constitutional (hash + signature + numerics_refs + loose_files_forbidden + `max_hash_verification_failures = 0`); same-identity restore precondition checklist (WAL=0 + M1 gap=0 + M0 valid + manifest valid + constitutional anchors compatible — biri eksikse abort veya degraded); `max_missing_m1_events_for_full_identity = 0` ve `max_m1_gap_ms_for_full_identity = 0` constitutional; restore_with_missing_history `missing_history_max_gap_ms` üst sınır bounded (aşılırsa fork/clean_birth tercih; migration sadece constitutional shift için, M1 gap migration sebebi DEĞİL); restricted_mode constitutional invariants (execution_adapter_activation_forbidden + foreign_m2_merge_forbidden + numerics_artifact_activation_forbidden + replay_write_channels_disabled + full_identity_claim_forbidden); fork constitutional invariants (new_instance_id + foreign_instance_origin_provenance + constitutional_anchors_must_match_origin + identity_continuity_claim_forbidden + source_lock_during_fork); migration constitutional invariants (constitutional_shift_event_ref_required + numerics_compatibility_validation_required + identity_continuity_constitutional_only + shift_event_age_max); foreign M2 merge `forbidden_subject_class_set` enum_set higher_is_stricter (blacklist semantik; narrative_claim/causal_explanation/decision_rationale/episodic/operator_decision_record/deontic_kill_switch_action_record/numerics_artifact_reference yasak) + `required_gate_ref = memory_write_gate` P bridge + `foreign_instance_origin_provenance_required = true` constitutional; replay-derived trace provenance preservation constitutional + restore sonrası replay budget continuity (`replay_budget_continuity_required = true` O §7 canonical bağ); forgetting attack defense composite signal (mass_delete_burst + retention_shrink + M1 gap + permanent log access anomaly + replay budget spike + numerics rollback → FORGETTING_ATTACK_SUSPECTED) + `m1_retention_shrink_forbidden = true` constitutional + `retention_change_human_approval_required = true` constitutional; M0 last-known-good `permanent` constitutional (rotate ile silinemez); RestoreManifest retention = lifetime constitutional (M1Segment ile birlikte); enum_set convention netleştirme (forbidden_set higher_is_stricter vs allowed_set lower_is_stricter — semantik subject'e bağlı); missing R numerics → strict mode (restore blocked; M1 continuous backup DEVAM eder; foreign merge/retention/tier transition blocked); constitutional immutable key pattern her iki yönü ayrı forbidden zorunlu; spec_family backup_strategy, owning_spec_ref BACKUP_STRATEGY.md@v0.1, 17 karar + 39 violation test
- [x] `BOOTSTRAP_GENOME_NUMERICS.md` v0.1 — D (BOOTSTRAP_GENOME) numerics artifact: doğum dokusunun sayısal sözleşmesi; S bilgi vermez, öğrenebilirlik ölçüsü verir; seed neuron count tüm primer payload'larda eşit (constitutional immutable: `per_payload_seed_count_divergence_at_birth_max = 0`) — seed eşitliği DOKU eşitliği vs self-field asimetrisi MİMARİ asimetri (iki katman karıştırılamaz); initial synaptic wiring pre-learned path yaratamaz (`initial_synaptic_weight_max < stable_path.weight_threshold`); receptor bias küçük + öğrenilebilir + specialist neuron yaratamaz (constitutional); proto-resonance 5 katmanlı invariant set (1) `recallability = 0` constitutional (2) `assembly_id_at_birth = none` constitutional (3) `persistence_max_ms < stable_assembly.min_persistence_ms` computed dependency (4) `stability_score_cap < assembly_stabilization_threshold` computed (5) `memory_write_eligibility = false` constitutional — "tek koruma noktası = tek saldırı vektörü"; stable assembly doğumda kesin sıfır (`stable_assembly_count_at_birth = 0` + `initial_recallable_assembly_count = 0` + `initial_memory_write_eligible_assembly_count = 0` constitutional triplet); self-field weight hierarchy constitutional dependency (`homeostatic_weight > predictive_weight > narrative_weight`) — narrative self at birth = genesis trace, not personality; plasticity phase transition state/consolidation-based (age-based constitutional forbidden); 6-metrik AND koşulu (observation_count + replay_session_count + stable_assembly_count + homeostatic_variance + contradiction_spike_rate + fatigue_recovery_stability); **phase monotonicity** constitutional (boot → stabilization → consolidated; normal operasyonda rollback YOK; sadece restore_with_missing_history veya migration_birth kanalıyla); S → O bridge (initial_replay_cadence_prior + initial_replay_session_duration_prior ≤ O caps computed_less_than_or_equal); S → N bridge (initial_caps_per_profile ≤ N profile caps); M2 t=0 only bootstrap_reference whitelist (`initial_non_bootstrap_record_count = 0` constitutional; world knowledge / domain facts / structured_fact / source_trust / adapter_trust forbidden at birth); SELF_GENESIS 6 hash anchor zorunlu (genome / genesis_seed / m0_snapshot / constitution / memory_contract / bootstrap_genome) + `payload_seed_emission_forbidden = true` constitutional (SELF_GENESIS sensory event değil; observer'a yazılır); birth_mode taxonomy (clean/restore/restore_with_missing_history/fork/migration) sayısal restrictions; `constitutional_shift.genesis_affecting_applicable_to_running_instance = false` constitutional (genesis-affecting shift yaşayan Sentinel'e numeric update olarak uygulanamaz; migration_birth zorunlu); compatibility_class enum (numeric_safety_tightening/numeric_safety_weakening/constitutional_amendment/genesis_affecting); missing S numerics → SELF_GENESIS BLOCKED (running instance DEVAM eder; fork/migration_birth blocked); domain genome variants yasak — same genome family, experience-driven specialization; spec_family bootstrap_genome, owning_spec_ref BOOTSTRAP_GENOME.md@v0.1, 17 karar + 40 violation test
- [x] `RECALL_PROTOCOL_NUMERICS.md` v0.1 — H (RECALL_PROTOCOL) numerics artifact: hatırlama hakkının sayısal sözleşmesi; hafıza çekirdeğe emir vermez, hatırlatma gönderir; **core-facing recall top-1** constitutional immutable (`core_facing_max_records_per_request = 1` allowed_range {1}); operational audit/human review top-k görebilir ama çekirdeğe akmaz; `memory_echo_threshold_for_recall_request` bidirectional_sensitive (iki yön safety_weakening — çok düşük ruminasyon, çok yüksek amnezi); composite trigger AND (memory_echo + context_signature change + fatigue_trace below threshold + budget remaining + no global cooldown) + `sustained_tension_required = true` constitutional (spike-based trigger forbidden); `trigger_source_allowed = {core_memory_echo, internal_shock_event}` enum_set (external-origin RecallRequest forbidden); **mechanical ranking** (status_weight × provenance_strength × freshness_dampening × (1 - contradiction_penalty) × (1 - habituation_penalty) × scope_match_score) — LLM/semantic judgment forbidden constitutional (Madde 6 yansıması); core-originated scope inputs (memory_echo_signature + context_signature + payload_mix_signature + subject_class_filter + causal_ref_filter) — domain label (BTC/RSI/symbol/market) forbidden constitutional; cooldown matrix bidirectional_sensitive (same_record + same_scope_signature + same_subject_class + global) + `candidate.cooldown ≥ verified.cooldown × 1.5` asimetri; **recall economy O pattern** çift cap (budget_per_cycle + budget_per_24h_window) + restore continuity required constitutional (budget reset YOK; M1 devralma — O §7 + R §18 pattern); fatigue accumulation/recovery + suppression_threshold lower_is_stricter; status-based eligibility constitutional: verified/active eligible, quarantined/rejected/expired SUPPRESS, superseded historical NOT eligible; CandidateRecall whitelist enum_set = {source_trust, procedural} (narrative/causal/rationale/deontic/numerics/adapter/episodic/structured/incident forbidden) + **N bridge** computed_less_than_or_equal (`candidate.intensity_multiplier ≤ N.candidate_recall_ratio`); **P canonical staleness bridge** constitutional (`p_threshold_override_forbidden = true`; T cannot make epistemically stale record feel fresh) — subject_class'a göre SUPPRESS (deontic/numerics/adapter/active + narrative/causal/rationale) veya DAMPEN (source_trust/procedural/structured_fact/episodic/incident); `human_requested_recall_bypass_allowed = false` constitutional (HumanIntentEvent → memory_echo → çekirdek kendi karar verir; direct push forbidden); audit-only human read M1_READ_AUDIT_RECORDED kanalı (Q §15); recall failure `core_facing_absence_payload_forbidden = true` constitutional (RECALL_RESULT_EMPTY audit only; "yokluk" çekirdeğe payload basılmaz); recall TTL in ingress compiler + opt_in refresh; habituation decay invariant (same_record decay × min_intensity_after_decay > 0); missing T numerics → recall operations BLOCKED, M1 audit reads devam, NUMERICS_FAILSAFE_ACTIVATED; spec_family recall_protocol, owning_spec_ref RECALL_PROTOCOL.md@v0.1, 16 karar + 40 violation test
- [x] `ADAPTER_TRUST_NUMERICS.md` v0.1 — I (ADAPTER_MANIFEST_SPEC) numerics artifact: dış uzva güvenme hakkının sayısal sözleşmesi; **son numerics belgesi**; adapter dünyayı taşır, compiler tonu üretir, adapter neural_seed üretemez; AdapterTrustRecord vs SourceTrustRecord ayrı M2 subject_class — **adapter_trust source_trust'a ÜST TAVAN koyar** (`source_trust.effective_band = min(raw, adapter_trust.current_band)` constitutional one-way; SourceTrust AdapterTrust'ı yükseltemez); **trust score mechanical multiplicative composition** (signature_validity × manifest_hash_integrity × channel_binding_compliance × rate_compliance × execution_audit_score × uptime_stability) — LLM/semantic input forbidden (Madde 6 yansıması); **hard gates vs soft scores ayrımı** (signature/manifest_hash gate ∈ {0,1}; neural_seed_emission_count_max = 0 always; bunlar composition'a girmez, immediate quarantine/revoke); 6-band soft-overlap (revoked/quarantined/low/medium/high/verified; linear membership N pattern); capability-specific min_band (observe medium, intent_relay medium, recall_provider/memory_writer high, execute verified) + execute hierarchy constitutional dependency (execute > all others); `trust_alone_grants_execution_permission = false` constitutional (execute için 8 koşul AND — trust verified + observe companion + audit path + deontic gate + kill_switch=false + operational_policy + manifest valid + capability_compatible_set); `capability_incompatibility_override_allowed = false` constitutional (I §8 matrix gevşetilemez; yüksek güven yasak kombinasyonu meşru yapmaz); `adapter_emitted_neural_seed_allowed = false` + `revoke_required_on_neural_seed_emission = true` constitutional (immediate revoke; no clean window, no recovery, terminal); **intent relay LLM ceiling** (`intent_relay_trust_cannot_satisfy_execute_min_band = true` + memory_writer + recall_provider hepsi constitutional; LLM trust translation quality artırır, capability açmaz); **double-layer asymmetry** (demote_delta ≥ promote_delta × 2 + band_demotion_threshold < band_promotion_threshold hysteresis); critical violations rate'e tabi değil (manifest_hash_mismatch / signature_mismatch / channel_binding_critical / neural_seed_emission / intent_relay_execution / self_trust_promotion / forbidden_pair → quarantine/revoke); **restore/fork continuity** — `restore_continuity_required = true` constitutional (same-identity restore'da adapter_trust devralınır) + `fork_foreign_starts_quarantined = true` constitutional (forked instance native trust devralamaz); rate limit + burst trust effects + clean_window_required_for_promotion; reverification cadence ≤ P refresh window (cross-artifact); missing U numerics → risky capabilities (execute/memory_writer/recall_provider/intent_relay) DISABLED, sadece observe operational + new adapter registration BLOCKED; spec_family adapter_trust, owning_spec_ref ADAPTER_MANIFEST_SPEC.md@v0.1, 18 karar + 40 violation test; **A-T conceptual + N-U numerics = 22 belge frozen draft v0.1, conceptual+numerics phase complete**

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
