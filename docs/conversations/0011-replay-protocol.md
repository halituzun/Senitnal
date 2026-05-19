# 0011 — Replay Protocol

> Bu dosya `REPLAY_PROTOCOL.md` (v0.1) ortaya çıkmadan önce yapılan üçlü
> tasarım konuşmasının (Halit + Claude + ChatGPT) sıkıştırılmış özetidir. K
> turunun kararlarının soyağacı.
>
> A-J: 0001-0010

---

## Tarih
2026-05-18 (J → K geçişi)

## Bağlam

A-J kapanmış. **Implementation-adjacent phase**'in ikinci belgesi. Replay A-J boyunca dağınık olarak referans edildi:
- Madde 2 — sleep/replay causal pruning (sinaps)
- B §19 — attention replay habituation
- G §8 — `replay_survival` verification matrix evidence
- J §13-14 — mapping update outcome/replay evidence
- MEMORY_CONTRACT §14 — replay engine M0 etkisi (3 kanal: sleep, attention, ingress)

K bu dağınık kullanımı **tek tutarlı kontrat** altında topladı + self-deception kapısını kapattı.

---

## Başlangıç pozisyonları

### Claude (açılış)
6 ana soru:
1. Sleep replay ile attention replay aynı mekanizma mı?
2. Replay M0'a hangi kanallardan dokunabilir?
3. Replay survival score nasıl üretilir?
4. Counterfactual gerçek mi, model-based mi?
5. Replay outcome evidence sayılır mı?
6. Replay self-deception kapısı mı?

Üç çapa:
1. Tek mekanizma + multi-channel
2. Bounded counterfactual ablation
3. Self-deception engelleme (M2'ye direkt yazamaz)

### ChatGPT (5 sertleştirme + iki kritik soru)

ChatGPT 3 çapayı kabul + 5 sertleştirme:
1. Replay source sadece M1 snapshot / M0 trace (LLM/M2 raw yasak)
2. Replay live core'a sensory event basamaz (sandboxed)
3. Replay budget zorunlu
4. Replay survival score truth değil
5. Counterfactual outcome-before yapamaz

Iki kritik soru:
- Sleep/synapse replay sinaps update yapabilir mi? → Evet ama çok sınırlı (audit + evidence + cap + eligibility)
- Counterfactual branch sayısı? → single default, pairwise high-severity, higher-order yasak

### Claude (iki kritik soruya cevap + ek)

**Soru 1 ek:** 
- Asymmetric rates (dampening > strengthening, J ile uyumlu)
- Eligibility trace constraint (replay sadece eligibility içindeki sinapslara dokunur)

**Soru 2 ek:** Pairwise ablation **causal-link constraint** — random combinatorial yok

**Yeni nüans:** `replay_survival_score` ≠ `outcome_alignment_score` (sentetik vs gerçek)

### ChatGPT son tur
"Yaz" hükmü + küçük event düzeltmesi: `REPLAY_SESSION_STARTED/COMPLETED` ayrı event yerine `REPLAY_SESSION_STATUS_CHANGED` canonical (B/C/E/F/G/I disiplini). F'deki `REPLAY_SESSION_COMPLETED` legacy → status_changed altına.

---

## Çekirdek kararlar (14)

1. Replay geçmişi tekrar yaşatmaz; geçmişten kontrollü kanıt üretir.
2. Replay decision engine değildir.
3. Replay sandboxed (live core'a sensory event basamaz).
4. Tek mekanizma + 5 effect channel (sleep_synapse, attention_habituation, ingress_calibration, memory_verification, outcome_alignment).
5. Input: M1 snapshot, M0 trace, outcome refs only (LLM/M2 raw yasak).
6. Replay M2'ye doğrudan yazmaz; sadece evidence axis.
7. Sleep replay sinaps update eligibility içinde, audited, evidence-bound.
8. Asymmetric rates (dampening > strengthening, capped).
9. Counterfactual bounded: single-variable default, pairwise causal-linked, higher-order yasak.
10. `replay_survival_score` ≠ `outcome_alignment_score`.
11. Replay budget + cooldown + fatigue.
12. Recursive evidence loop yasak (self-deception safeguard).
13. HumanIntent/InternalShock mapping update yapamaz.
14. Tek canonical: `REPLAY_SESSION_STATUS_CHANGED`.

---

## Madde 1/2/7 yansıması — replay seviyesi

A-J boyunca Madde 1 her seviyede yansıdı. K'da:
- **Madde 1 yansıması:** Tek replay engine, çoklu channel — ayrı engine yaratımı yasak
- **Madde 2 yansıması:** Sleep replay Madde 2'nin altında, ama sinaps update eligibility + evidence + cap'le çok sınırlı
- **Madde 7 yansıması:** Replay M2'ye doğrudan yazamaz; sadece gate'e evidence

---

## Önemli sertleştirmeler

### Counterfactual ≠ outcome alignment
En kritik sertleştirme. Counterfactual replay sentetik test; outcome gerçek dünya feedback. Memory Write Gate verification matrix'inde ikisi **ayrı evidence axes**. Sentetik gerçeği ikame edemez.

> *`replay_survival_score` ≠ `outcome_alignment_score`.*

### Eligibility trace constraint
Sleep replay rastgele topology editor değil. Sadece **eligibility trace içindeki sinapslar** update alabilir. Dormant/expired sinapslar dokunulmaz. Madde 2'deki "üç ölçekli eligibility" disiplini replay seviyesinde de.

### Pairwise causal-link constraint
Pairwise ablation random event çiftleri için değil; sadece **causal_refs ile bağlantılı** event'ler. Combinatorial explosion + hayali tarih riski engellenir.

### Self-deception safeguards (5 katman)
1. M2'ye direkt yazamaz (her zaman Memory Write Gate)
2. Output "replay-derived" işaretli
3. Sandboxing (live core'a değmez)
4. Recursive evidence loop yasak
5. Counterfactual ≠ outcome

### Sandboxing zorunluluğu
Replay session simulated event üretebilir ama bu event'ler:
- payload_seed üretmez
- WORKSPACE_PULSE tetiklemez  
- Memory Write Gate'e doğrudan candidate önermez
- Deontic gate evaluation'a girmez

Sadece M1 audit + bounded M0 trace update.

### Asymmetric rates (J ile uyumlu)
Yanlış güçlenmiş sinaps/mapping'leri zayıflatmak hızlı; yeni güçlendirme yavaş. Ama ikisi de evidence-bound + rate-capped. Sensory tone runaway engellenir.

---

## Yan güncellemeler (commit'in parçası)

- `CONSTITUTION.md` Madde 2 — alt-spec referansı (sleep_synapse_update channel)
- `MEMORY_CONTRACT.md` §14 — replay engine M0 etkisi sorusu K ile formal cevap (5 kanal, sandboxing, counterfactual sınırı)
- `ATTENTION_WORKSPACE.md` §19 — attention_habituation_update channel cross-ref
- `INGRESS_COMPILER_SPEC.md` §14 — ingress_calibration_update channel cross-ref
- `MEMORY_WRITE_GATE.md` §11 — replay/outcome evidence ayrımı cross-ref
- `OBSERVER_LEDGER_SCHEMA.md` §10 permanence_policy: REPLAY_SESSION_STATUS_CHANGED, REPLAY_SURVIVAL_EVALUATED, REPLAY_OUTCOME_ALIGNMENT_EVALUATED, COUNTERFACTUAL_ABLATION_PERFORMED eklendi
- `OBSERVER_LEDGER_SCHEMA.md` §19 event catalog: REPLAY_SESSION_COMPLETED legacy → REPLAY_SESSION_STATUS_CHANGED canonical; 3 yeni event eklendi
- `README.md` — REPLAY_PROTOCOL tamamlanmış listesine

---

## Açık kalanlar (NUMERICS / implementation)

- Kesin sayısal değerler (replay_budget, refractory_period, rate caps)
- Replay survival score formülü (similarity metric)
- Outcome time lag tolerance
- Cross-channel evidence paylaşımı
- Failed replay session retry policy
- Replay snapshot retention
- Multi-instance replay (cross-restore identity)

---

## Sıradaki

A-K kapandı. **12 belge.** Replay artık tek tutarlı protokol altında.

Sıradaki:
- `BACKUP_STRATEGY.md` — M0/M1 yedekleme, RPO/RTO, cross-restore identity
- NUMERICS belgeleri (INGRESS_COMPILER_NUMERICS, BOOTSTRAP_GENOME_NUMERICS, vb.)

---

## Kilit cümleler

> **Replay geçmişi tekrar yaşatmaz. Replay geçmişten kontrollü kanıt üretir.**
>
> **Replay decision engine değildir. Replay yeni hakikat yaratmaz.**
>
> **Replay kendi sonucuna inanamaz. Replay sonucu sadece denetlenebilir evidence olarak yaşar.**
>
> **Counterfactual replay = bounded ablation over recorded traces. Not free simulation. Not generative imagined history.**
>
> **`replay_survival_score` ≠ `outcome_alignment_score`. Sentetik test gerçek dünya geri bildirimini ikame edemez.**
>
> **Replay engine tek. Replay etkileri kanala göre sınırlı.**
