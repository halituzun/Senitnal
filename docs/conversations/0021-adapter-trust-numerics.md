# 0021 — Adapter Trust Numerics

> Bu dosya `ADAPTER_TRUST_NUMERICS.md` (v0.1, U turu) ortaya çıkmadan
> önce yapılan üçlü tasarım konuşmasının (Halit + Claude + ChatGPT)
> sıkıştırılmış özetidir. **Son numerics artifact'inin** soyağacı.
>
> A-T: 0001-0020

---

## Tarih
2026-05-19 (T → U geçişi, **son** numerics specifikasyonu)

## Bağlam

N, O, P, Q, R, S, T numerics donmuş. U I'nın (ADAPTER_MANIFEST_SPEC)
numerics artifact'i; **dış uzva güvenme hakkının sayısal omurgası**.

Tek cümle: **U = dış uzva güvenme hakkının sayısal sözleşmesidir.**
Kilit ayrım: **Adapter powerful olabilir; ama kendi güvenini kendi üretemez.**

U'nun üç gerilimi:
- Çok gevşek adapter trust → silent compromise (bozuk manifest güçlü event basar)
- Çok sert adapter trust → operational paralysis (dış dünya duyulamaz)
- Capability laundering → high trust yeni capability yaratır → Madde 6 ihlali

U **conceptual + numerics phase'in son artifact'idir**.

---

## Başlangıç pozisyonları

### ChatGPT (Halit'in vekili, açılış)

10 ana çapa + 17 kırmızı çizgi:
1. AdapterTrustRecord ≠ SourceTrustRecord
2. Trust band cutoffs (6-band)
3. Capability-specific minimum trust
4. Capability incompatibility numerics değiştirilemez
5. Demotion hızlı, promotion yavaş
6. Manifest validation numerics
7. Channel binding violation thresholds
8. Adapter neural_seed yasağı immediate revoke
9. Rate limit / burst trust effects
10. LLM intent_relay trust ceiling

### Claude (10 çapaya cevap + 7 ek pozisyon)

**Ek 1 — Trust composite signal mekanik.** T mechanical ranking pattern'i
U'da: deterministic multiplicative composition. Hard gates vs soft scores
ayrımı kritik.

**Ek 2 — Double-layer asymmetry.** Rate asymmetry (demote_delta ≥
promote_delta × 2) + threshold asymmetry (demotion < promotion, hysteresis).

**Ek 3 — Execute double-gate.** Trust yeterli olsa bile 8 koşul AND.
U sadece trust tarafını sayısallaştırır.

**Ek 4 — Restore continuity (R bridge).** Same-identity restore'da
adapter_trust devralınır; fork foreign starts quarantined.

**Ek 5 — Source/Adapter dependency tek-yön.** AdapterTrust SourceTrust'a
ÜST TAVAN; SourceTrust AdapterTrust'ı YÜKSELTEMEZ.

**Ek 6 — Neural seed emission terminal.** Clean window/demotion gradient/
recovery YOK. Tek girişim immediate revoke.

**Ek 7 — Capability hierarchy explicit.** execute > memory_writer >
recall_provider > intent_relay/observe (computed_greater_than).

### ChatGPT (kabul + "yaz")

ChatGPT: "U yaz. Son numerics belgesi olduğu için çapa turunu tekrar
ChatGPT'ye göndermeye gerek yok. Mekanik review belge çıktıktan sonra
yapılır."

Korunacak ana kararlar belirtildi:
- AdapterTrust ≠ SourceTrust (ayrı subject_class + one-way bound)
- Trust composite signal — hard gates / soft scores ayrı
- Capability-specific min_band + execute hierarchy
- Capability incompatibility override yok
- Adapter neural_seed = immediate revoke terminal
- Demotion hızlı, promotion yavaş double-layer
- Restore continuity / fork foreign quarantined

Üç cümle sert dursun:
- "Adapter powerful olabilir; ama kendi güvenini kendi üretemez"
- "High trust does not create new capability"
- "LLM intent_relay trust execution'a evrilemez"

### Halit final

> *"Yaz. U dış uzva güvenme hakkının sayısal sözleşmesi. Adapter dünyayı
> taşır, compiler tonu üretir, adapter neural_seed üretemez."*

---

## Çekirdek kararlar (18 omurga)

1. U runtime config değildir; signed artifact + M2 reference.
2. U = dış uzva güvenme hakkının sayısal sözleşmesidir.
3. AdapterTrust ≠ SourceTrust; iki ayrı M2 subject_class.
4. Adapter trust source trust'a UPPER BOUND (one-way; constitutional).
5. Source trust adapter trust'ı YÜKSELTEMEZ (constitutional).
6. Trust score mechanical multiplicative composition; LLM/semantic forbidden.
7. Hard gates composition'a girmez (signature/manifest_hash/neural_seed_emission).
8. Trust band'ları soft-overlap (N pattern); linear default.
9. Capability flag tek başına yetki değildir; min_band gerek.
10. Execute en yüksek bar (verified); execute > all others constitutional hierarchy.
11. trust_alone_grants_execution_permission = false; execute 8 koşul AND.
12. capability_incompatibility_override_allowed = false constitutional.
13. adapter_emitted_neural_seed_allowed = false + immediate revoke constitutional; terminal, no recovery.
14. Intent relay LLM ceiling: execute/memory_writer/recall_provider satisfaction forbidden constitutional.
15. Double-layer asymmetry: rate (demote ≥ promote × 2) + threshold hysteresis.
16. Restore continuity + fork foreign starts quarantined; restore_with_missing_history adapter activation forbidden.
17. Reverification cadence ≤ P refresh window (cross-artifact).
18. Missing U numerics → risky capabilities DISABLED; observe-only operational.

---

## Madde yansımaları

### Madde 6 — LLM ceiling
U §15 intent_relay capability ceiling 3 constitutional invariant'la korunuyor:
- cannot satisfy execute min_band
- cannot satisfy memory_writer min_band
- cannot satisfy recall_provider min_band

"LLM trust translation quality artırır; capability açmaz."

### Madde 7 — M2 separation
Memory writer adapter'ı P verification matrix bypass edemez; world_claim
write forbidden constitutional.

### Üç U asimetri
- **Adapter vs Source trust direction**: tek-yön (Adapter → Source upper bound)
- **Hard gates vs soft scores**: gate yok edici (composition 0), soft multiplicative
- **Demotion vs promotion**: rate + threshold double layer

---

## Önemli sertleştirmeler

### One-way trust bound
SourceTrust effective band hesabı `min(raw, adapter_trust)` constitutional.
Kaynak iyi görünse bile taşıyıcı adapter quarantined ise effective trust
düşer. Bu C → U bridge'in canonical kapanışı.

### Hard gates: tek girişim quarantine/revoke
signature_validity ∈ {0,1}, manifest_hash_integrity ∈ {0,1},
neural_seed_emission_count_max = 0. Bunlardan biri yetersiz olduğunda
composition'a girmez; immediate quarantine veya revoke (neural_seed
emission TERMINAL).

### Mechanical composition (T pattern U yansıması)
Multiplicative composition (additive değil) — tek soft zaafiyet kaderi
etkiler (defense-in-depth). Additive olsaydı bir kötü score iyi
score'larla maskelenir.

### Double-layer asymmetry
Sadece demote_delta > promote_delta değil; ayrıca band_demotion_threshold
< band_promotion_threshold (hysteresis zone). DEONTIC §18 emergency_revert
pattern'inin U yansıması.

### Neural seed emission terminal
Clean window/demotion gradient/recovery YOK. Re-registration sadece yeni
adapter_id + yeni manifest + sıfır trust history ile. I'nın "adapter
neural_seed üretemez" kuralının numerics seviyesindeki en sert kapanış.

### Restore/Fork continuity
R §12 same-identity → adapter_trust devralınır (pre-restore violations
still counted). R §14 fork → foreign quarantined start + foreign_instance_origin
provenance permanent. Forgetting attack defense yansıması.

### LLM intent_relay 3 constitutional ceiling
Tek invariant yetmez; üç ayrı capability için ayrı ayrı forbidden
constitutional. LLM trust band ne kadar yüksek olursa olsun 3 yoldan
hiçbiriyle execute/memory_writer/recall_provider'a evrilemez.

### Execute 8-koşul AND
trust verified + observe companion + audit path + deontic gate +
kill_switch=false + operational_policy + manifest valid +
capability_compatible_set. U sadece ilk koşulu sayısallaştırır;
diğerleri I/E/G referansları. "Trust alone grants execution permission =
false."

---

## Yan güncellemeler (commit'in parçası)

- `ADAPTER_MANIFEST_SPEC.md` §7 (capability bindings) cross-ref to U §8, §10, §12
- `ADAPTER_MANIFEST_SPEC.md` §8 (incompatibility matrix) cross-ref to U §11
- `ADAPTER_MANIFEST_SPEC.md` §11 (AdapterTrustRecord) cross-ref to U (full)
- `WORLD_INGRESS.md` §16 (SourceTrustRecord) cross-ref to U §19 (effective band bridge)
- `MEMORY_WRITE_GATE_NUMERICS.md` §17 adapter_trust replay_survival_weight = 0 entry'ye U §6-17 reference eklendi
- `BACKUP_STRATEGY_NUMERICS.md` §12 cross-ref to U §20 (same-identity restore continuity)
- `BACKUP_STRATEGY_NUMERICS.md` §14 cross-ref to U §20 (fork foreign quarantined)
- `MEMORY_CONTRACT.md` M2 subject_class adapter_trust note U reference
- `OBSERVER_LEDGER_SCHEMA.md` §10 ADAPTER_MANIFEST_STATUS_CHANGED permanence policy:
  6 yeni critical reason satırı (neural_seed_emission_attempt /
  intent_relay_execution_attempt / self_trust_promotion_attempt /
  forbidden_capability_pair_attempt / manifest_hash_mismatch /
  signature_mismatch → permanent_with_snapshot + human_alert)
- `OBSERVER_LEDGER_SCHEMA.md` §19 ADAPTER_MANIFEST_STATUS_CHANGED catalog entry
  U reason enum listesi eklendi
- `README.md` completed list — U eklendi; **conceptual+numerics phase complete** notu
- `docs/conversations/0021-adapter-trust-numerics.md` eklendi

Yeni canonical event gerekmedi: ADAPTER_MANIFEST_STATUS_CHANGED + reason
field discipline yeterli.

---

## Açık kalanlar (implementation veya sonraki phase'e devredildi)

- Exact production values (band cutoffs, demote/promote delta, rate limits) → signed artifact
- `high_explicit_emergency` band semantik → I spec revision veya implementation
- Forked adapter recovery path → operational + implementation
- Multi-signature requirement for U updates → M §13
- Trust signal composition weighting (soft scores eşit mi differential?) → safety review
- Sleep cycle ile trust refresh coordination → S §17
- Cross-instance adapter trust verification protocol → fork_birth + migration_birth

---

## Sıradaki

**A-T conceptual + N-U numerics = 22 belge frozen draft v0.1.**

Conceptual + numerics phase **TAMAM**.

22 belge:
- A-L conceptual (12)
- M numerics governance meta-spec (1)
- N-U numerics artifacts (8)
- + ATTENTION_WORKSPACE (Madde 4 sub-spec, B'den önce hazırlanmış)

Sıradaki adım yeni conceptual / numeric belge **DEĞİL**. Implementation
readiness review + build plan + first concrete signed numerics artifacts
(production değerler) konuşulur.

---

## Kilit cümleler

> **U = dış uzva güvenme hakkının sayısal sözleşmesidir.**
>
> **Adapter powerful olabilir. Ama kendi güvenini kendi üretemez.**
>
> **Adapter dünyayı taşır. Compiler tonu üretir. Adapter neural_seed üretemez.**
>
> **High trust does not create new capability.**
> **Trust only enables declared, compatible, channel-bound capability.**
>
> **One attempt — immediate revoke. No clean window. No demotion gradient. Terminal.**
>
> **LLM intent_relay trust translation quality artırabilir; execute/memory_writer/recall_provider capability'sini açamaz.**
>
> **Yüksek güven, yasak capability kombinasyonunu meşru yapmaz.**
>
> **One clean window cannot undo one critical violation.**
>
> **AdapterTrust SourceTrust'a tavan koyar. Tek yön.**
>
> **Forked instance, eski instance'ın adapter güvenini native güven gibi devralamaz.**
>
> **N dış dünyanın hakkını sınırlar.**
> **O kendi geçmişine girme hakkını sınırlar.**
> **P hafızaya emin olma hakkını sınırlar.**
> **Q kendine bakma hakkını sınırlar.**
> **R kimliğini koruyarak geri dönme hakkını sınırlar.**
> **S nasıl doğacağını sınırlar.**
> **T hatırlatmanın ekonomisini sınırlar.**
> **U dış uzva güvenme hakkını sınırlar.**

---

## Phase Closure — 22 belge complete

```
A: CONSTITUTION
B: MEMORY_CONTRACT
C: WORLD_INGRESS
D: BOOTSTRAP_GENOME
E: DEONTIC_GATE
F: OBSERVER_LEDGER_SCHEMA
G: MEMORY_WRITE_GATE
H: RECALL_PROTOCOL
I: ADAPTER_MANIFEST_SPEC
J: INGRESS_COMPILER_SPEC
K: REPLAY_PROTOCOL
L: BACKUP_STRATEGY
M: NUMERICS_GOVERNANCE
N: INGRESS_COMPILER_NUMERICS
O: REPLAY_PROTOCOL_NUMERICS
P: MEMORY_WRITE_GATE_NUMERICS
Q: OBSERVER_LEDGER_NUMERICS
R: BACKUP_STRATEGY_NUMERICS
S: BOOTSTRAP_GENOME_NUMERICS
T: RECALL_PROTOCOL_NUMERICS
U: ADAPTER_TRUST_NUMERICS
+ ATTENTION_WORKSPACE (Madde 4 sub-spec)
```

**22 belge frozen draft v0.1.**
**Conceptual + numerics phase complete.**
