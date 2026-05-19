# 0020 — Recall Protocol Numerics

> Bu dosya `RECALL_PROTOCOL_NUMERICS.md` (v0.1, T turu) ortaya çıkmadan
> önce yapılan üçlü tasarım konuşmasının (Halit + Claude + ChatGPT)
> sıkıştırılmış özetidir. **Yedinci numerics artifact'inin** soyağacı.
>
> A-S: 0001-0019

---

## Tarih
2026-05-19 (S → T geçişi, yedinci numerics specifikasyonu)

## Bağlam

N, O, P, Q, R, S numerics donmuş. T H'nin (RECALL_PROTOCOL) numerics
artifact'i; **hatırlama hakkının sayısal omurgası**.

Tek cümle: **T = hatırlama hakkının sayısal sözleşmesidir.**

T'nin üç gerilimi:
- Çok düşük memory_echo threshold → ruminasyon
- Çok yüksek memory_echo threshold → amnezi
- Stale record fresh-feeling → epistemic erosion (self-deception)

---

## Başlangıç pozisyonları

### Üç ana soru — yön belirleme

1. **Core-facing recall top-k mı top-1 mi?** → Top-1 constitutional immutable
2. **memory_echo threshold bidirectional_sensitive mı?** → Evet (iki yön safety_weakening)
3. **P staleness threshold aşılınca suppress mi dampened mi?** → Subject_class'a göre split

### ChatGPT (Halit'in vekili, açılış + kararlı pozisyon)

10 ana çapa açıldı. Üç sorunun cevabı kabul edildi. Çapa turu çift turlu
oldu; ikinci turda Halit "ChatGPT'ye tekrar göndermeye gerek yok, yeterince
net" dedi.

### Claude (cevaplara hardening + 4 ek pozisyon)

**Üç soruya hardening:**

**Ek 1 — Recall economy** (O pattern): `budget_per_cycle + budget_per_24h_window`
çift cap + restore continuity required (forgetting attack defense numerics
yansıması).

**Ek 2 — Recall failure** = audit only, sensory absence değil.
`core_facing_absence_payload_forbidden = true` constitutional.

**Ek 3 — Human-requested recall** hard rule: `bypass_allowed = false`
constitutional; HumanIntentEvent → memory_echo → çekirdek kendi karar verir.

**Ek 4 — Candidate recall O-pattern**: `candidate_cooldown ≥ verified_cooldown × 1.5`
asimetri (real evidence dominance prensibi).

### ChatGPT (kabul + 2 özel uyarı + "yaz")

İki özel uyarı belgeye gömüldü:

**Uyarı 1 — Mechanical ranking, semantic search değil**

Ranking score: `status_weight × provenance_strength × freshness_dampening ×
(1 - contradiction_penalty) × (1 - habituation_penalty) × scope_match_score`.

Yasak inputs: LLM "relevance", semantic plausibility, interestingness,
domain heuristics, importance scores. Madde 6 yansıması.

**Uyarı 2 — Core-originated scope, dış dünya etiketi değil**

Core-facing scope inputs: memory_echo_signature / context_signature /
payload_mix_signature / subject_class_filter / causal_ref_filter.

Yasak inputs: symbol=BTC / market=Binance / strategy=lead_lag / domain
labels. Observer/M2 ham kayıt domain etiketi taşıyabilir; core-facing
RecallRequest taşımaz.

"Yaz" hükmü — ChatGPT'ye tekrar gönderme gerek yok.

### Halit final

> *"Yaz. T = hatırlama hakkının sayısal sözleşmesi. Hafıza çekirdeğe emir
> vermez. İnsan hafızayı zorla konuşturamaz. Çekirdek sadece kendi
> memory_echo gerilimi yeterliyse hatırlatma ister."*

---

## Çekirdek kararlar (16 omurga)

1. T runtime config değildir; signed artifact + M2 reference.
2. T = hatırlama hakkının sayısal sözleşmesidir.
3. Hafıza çekirdeğe emir vermez; hatırlatma gönderir; core-originated RecallRequest zorunlu.
4. Core-facing recall top-1 (constitutional immutable); audit top-k operational.
5. memory_echo_threshold bidirectional_sensitive (iki yön safety_weakening).
6. Sustained tension required (constitutional); spike-based trigger forbidden.
7. Ranking mekanik score; LLM/semantic input forbidden (Madde 6).
8. Core-facing scope çekirdek-içi signature; domain label input forbidden.
9. Cooldown matrix (record/scope/subject_class/global); candidate ≥ verified × 1.5.
10. Recall economy çift cap (cycle + 24h); restore continuity required.
11. Status-based eligibility: quarantined/rejected/expired suppression constitutional.
12. Stale record SUPPRESS (self-deception-prone + active policy) veya DAMPEN (factual + historical).
13. T → P staleness override forbidden (P canonical; T gevşetemez).
14. T → N candidate cap dependency (candidate intensity ≤ N candidate_recall_ratio).
15. human_requested_recall_bypass_allowed = false (constitutional).
16. Recall failure audit-only; core-facing absence payload forbidden.

---

## Madde yansımaları

### Madde 6 — LLM ranking score üretemez (violation test 9, 37)
Mechanical ranking constitutional; semantic judgment forbidden.

### Madde 7 — hafıza ayrılığı
M2 çekirdeğe bilgi yığamaz; core-originated RecallRequest tek yol. Human
direct push forbidden constitutional.

### Üç T asimetri
- **Core-facing vs operational**: top-1 (core) vs top-k (audit)
- **Verified vs candidate**: cooldown × 1.5, intensity ≤ N candidate_recall_ratio
- **Fresh vs stale**: SUPPRESS / DAMPEN split per subject_class

---

## Önemli sertleştirmeler

### Top-1 constitutional
Core-facing recall tek kayıt. Top-k çekirdeği boğar + alternative-narrative
kapısı açar. M2 çekirdeğe bilgi yığamaz; çekirdek bir hatırlatma alır.

### Mechanical ranking
T'nin en kritik kavramsal disiplini. Ranking score deterministic
multiplicative composition; her input mekanik. LLM judgment, semantic
plausibility, interestingness yasak. Recall "arama motoru" değil.

### Core-originated scope
Scope inputs çekirdek-içi sinyaller. Domain etiketleri (BTC/RSI/symbol)
yasak. Çekirdek "BTC verisi getir" diyemez; "bu memory_echo signature'a
uyan kayıt varsa getir" der.

### Recall economy O pattern
Çift cap (cycle + 24h) + fatigue + restore continuity required. O replay
budget pattern'i T'de ruminasyon koruması olarak yansıdı.

### T → P staleness bridge canonical
P epistemic_staleness_threshold canonical kaynak; T recall-side dampening
uygular ama threshold'u **gevşetemez**. SUPPRESS list vs DAMPEN list
per subject_class.

### T → N candidate bridge
Üçlü zincir: N candidate_cap → T candidate_multiplier → P candidate
subject_class restrictions. Atomic update zorunlu (M §12).

### Recall failure audit-only
Boş sonuç çekirdeğe yokluk payload'ı basmaz. RECALL_RESULT_EMPTY canonical
audit event; budget decrement + fatigue accum (recall yapıldı sayılır)
ama core-facing absence yok.

### Human bypass yok
HumanIntentEvent → memory_echo → core karar verir. Direct push forbidden
constitutional. Operational audit M1_READ_AUDIT_RECORDED kanalı; RecallEvent
değil.

---

## Yan güncellemeler (commit'in parçası)

- `RECALL_PROTOCOL.md` §5 cross-ref to T §5-6 (triggers)
- `RECALL_PROTOCOL.md` §8 cross-ref to T §7-8 (top-1 + mechanical ranking + scope)
- `RECALL_PROTOCOL.md` §13 cross-ref to T §14, §12, §15, §16-17 (candidate/status/staleness)
- `RECALL_PROTOCOL.md` §14 cross-ref to T §9-11, §22 (economy + cooldown matrix + habituation)
- `MEMORY_CONTRACT.md` M2 section cross-ref to T
- `WORLD_INGRESS.md` §10 (RecallEvent Boundary) cross-ref to T §13-17
- `INGRESS_COMPILER_NUMERICS.md` §15 cross-ref to T (N → T candidate bridge)
- `MEMORY_WRITE_GATE_NUMERICS.md` §8 cross-ref to T (P → T staleness bridge)
- `README.md` completed listesine RECALL_PROTOCOL_NUMERICS eklendi
- `docs/conversations/0020-recall-protocol-numerics.md` eklendi

Yeni canonical event gerekmedi: RECALL_REQUEST_SENT,
RECALL_EVENT_INGESTED, RECALL_RESULT_EMPTY, RECALL_SUPPRESSED canonical reuse.

---

## Açık kalanlar (implementation veya sonraki numerics artifact'lere devredildi)

- Exact production values → signed artifact
- Habituation decay curve shape → implementation
- Active recall multiplier band exact value → N §7 koordinasyon
- Trust decay function for source_trust dampening → U (ADAPTER_TRUST_NUMERICS)
- Recall budget cycle boundary tanımı → S §17 sleep/wake transition
- Scope signature axis taxonomy → D §10 koordinasyon
- Multi-signature requirement for T updates → M §13

---

## Sıradaki

A-S + T kapandı. **21 belge.** Conceptual phase + 7 numerics artifact tamam.

Sıradaki NUMERICS belgeleri (kalan tek):
- U: `ADAPTER_TRUST_NUMERICS.md` — trust score band'ları, decay rate, source_trust/adapter_trust numerics, signed manifest validation

---

## Kilit cümleler

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
