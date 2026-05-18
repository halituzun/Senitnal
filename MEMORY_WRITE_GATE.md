# MEMORY_WRITE_GATE.md

## Sentinel — Epistemik Yazma Kapısı

---

## Status

**Frozen Draft v0.1**
**Conceptual phase. No implementation authority.**

Bu belge `CONSTITUTION.md` Madde 7 ve `MEMORY_CONTRACT.md` §9'un detaylı uzantısıdır. Yeni anayasa maddesi değildir. Deontic gate'in alt türü değildir. Çalışan bir epistemic validator'ın spec'i değildir. Sentinel'in M2 explicit memory'sine yazılmak istenen bilgi iddialarının **hangi mekanik testlerden geçtiğini, hangi statüleri aldığını, kimin neyi yazabildiğini ve self-deception riskinin nasıl engellendiğini** tanımlar.

---

## 1. Purpose

Sentinel kendi M2'sini self-deception aracına çevirmemeli. Sistemin kendi anlatısını "gerçek" diye kazıması M2'nin değerini yok eder. Bu belge bu kazımayı engelleyen mekanik freni tanımlar.

Damıtma:

> **Memory Write Gate, sistemin kendi hikâyesine inanmasını engelleyen epistemik frendir.**
>
> **Deontic gate eylem riskini sınırlar.**
> **Memory Write Gate epistemik riski sınırlar.**
>
> **Sistemin kendi açıklaması kanıt değildir. Kayıt olabilir, ama verified fact değildir.**

---

## 2. Constitutional Position — Madde 7 / MEMORY_CONTRACT §9 Alt-spec'i

Bu belge `CONSTITUTION.md` Madde 7'deki hafıza ayrılığının ve `MEMORY_CONTRACT.md` §9'daki Memory Write Gate kavramının **detaylı uzantısıdır**. Yeni şeyler eklemez — Memory Write Gate'in karar kurallarını, statü zincirini, evidence matrix'ini ve audit yüzeyini biçimselleştirir.

MEMORY_CONTRACT zaten ana çizgileri çiziyor:
- M2'ye yazma niyeti Memory Write Gate'e tabi (§9)
- CandidateMemoryRecord statü zinciri (§10)
- Subject_class alt-türleme (§2 M2)
- Observer dual-role: summarizer Memory Write Gate'e candidate önerir (§11, §14)

G bu çerçevenin **biçimsel ve uygulanabilir** halini verir.

---

## 3. Core Principle

> **M2'ye yazılmak isteyen şey önce kanıtlanır. Kanıtlanamayan şey ya candidate kalır, ya quarantine olur, ya reddedilir. Çekirdek kendi hikâyesini M2'ye gerçek diye kazıyamaz.**

Bu cümle belgenin kilididir.

---

## 4. Epistemic Gate, Not Deontic Gate

### Principle
Memory Write Gate deontic gate'in alt türü **değildir**. İki gate farklı risk eksenlerinde çalışır.

### İki gate ayrımı

| Boyut | Deontic Gate | Memory Write Gate |
|-------|--------------|-------------------|
| Risk tipi | Action risk (dünyaya etki) | Epistemic risk (gerçeklik / self-deception) |
| Soru | "Bu eylem dünyaya çıkabilir mi?" | "Bu kayıt hafızaya gerçekmiş gibi yazılabilir mi?" |
| Sınır | Constitutional hard-stop list + operational thresholds | Subject_class × evidence axes matrix |
| Çekirdeğe yansıma | Kritik bloklarda InternalShockEvent | **Yok** (silent gate — bkz. §5) |
| M1 audit | DEONTIC_BLOCKED, DEONTIC_BYPASS_ATTEMPT | MEMORY_WRITE_PROPOSED, MEMORY_RECORD_STATUS_CHANGED |
| Yasaklananı | Tehlikeli eylem | Doğrulanmamış kayıt |

### Forbidden

- Deontic gate ile Memory Write Gate'i tek mekanizmaya birleştirmek
- Memory Write Gate'in action-risk testleri yapması
- Deontic gate'in epistemic validation yapması
- Birinin diğeri yerine geçmesi

### Violation Test
> *Bu öneri Memory Write Gate'i deontic gate'in alt türü olarak konumlandırıyor mu?*
>
> Evet ise ihlal. İki gate farklı risk eksenlerinde, ayrı sözleşmelerle çalışır.

---

## 5. Gate Is Not a Truth Engine

### Principle
Memory Write Gate hakikat **üretmez**. Hakikat iddiasını **statülendirir**.

### Rationale
Eğer gate "şu kayıt mantıklı, verified yapayım" diye yargı yaparsa, gate gizli bir karar modülüne dönüşür — Madde 1'in gate seviyesindeki ihlali. Doğru: gate **deterministic boolean/sayısal testler** uygular, yargı yapmaz.

### Allowed

Gate testleri sadece şu formlarda olabilir:

```
evidence_refs.length >= min_evidence_count
contradiction_level < max_contradiction_threshold
staleness_ms < max_staleness_threshold
duplicate_match(existing_records) == false
cross_source_count >= min_corroboration_count
replay_survival_score >= min_replay_survival
outcome_alignment_score >= min_outcome_alignment
provenance_strength_band IN allowed_bands
self_deception_risk != HIGH
external_corroboration_refs is not empty
```

Hepsi boolean veya sayısal. Sonuç deterministic.

### Forbidden

- "Bu kayıt mantıklı görünüyor"
- "LLM tutarlı buldu"
- "Sistem bundan fayda görür"
- "Bu ilginç"
- "Bu anlatı güzel açıklıyor"
- Semantic interpretation veya yargı

### Silent Gate Principle

**Memory Write Gate sessizdir.** Reject, quarantine, verify veya supersede kararları çekirdeğe geri yansımaz. Audit M1'de yaşar, ama çekirdek doğrudan görmez.

```
candidate gelir
    ↓
Memory Write Gate test eder
    ↓
M1'e MEMORY_RECORD_STATUS_CHANGED yazar
    ↓
çekirdeğe shock / pulse / recall / payload_seed DÖNMEZ
```

### Rationale (Silent Gate)

Deontic gate kritik bloklarda `InternalShockEvent` üretir — sistemin tehlikeli action niyetinden öğrenmesi için. Memory Write Gate'te bu yoktur çünkü:

- Action-risk dünyaya dokunur; sistemin **öğrenmesi gerek**
- Epistemic-risk sistemin kendi anlatısıdır; gate'in işi **sessiz filtrelemek**

Eğer Memory Write Gate reject'i çekirdeğe yansısa, gate **dolaylı şekilde sisteme öğreten** bir modül olur — karar modülü tehlikesinin yeni hali. Doğru davranış: sessiz filtreleme.

### Pattern feedback yolu (dolaylı)

Reject pattern'ı önemliyse:

```
gate kararı M1'e yazılır
    ↓
summarizer M1'i okur
    ↓
meta-pattern keşfeder
    ↓
normal candidate olarak önerir
    ↓
Memory Write Gate yine değerlendirir
```

Yani feedback **summarizer döngüsünden** geçer, doğrudan gate'ten değil. Bu anti-self-reinforcement koruması.

### Violation Test
> *Gate reject/quarantine/verify sonucu çekirdeğe payload_seed, pulse, InternalShockEvent veya RecallEvent olarak geri dönüyor mu?*
>
> Evet ise ihlal.

---

## 6. What May Propose a Memory Write

### Beş candidate kaynağı

| Kaynak | Tetik | Self-deception riski | Gate matrix |
|--------|-------|---------------------|-------------|
| **Core** (memory_write_intention) | Çekirdek bir desen stabil olduğunda niyet üretir | **Yüksek** (kendi hikâyesi) | Full matrix + self-deception test |
| **Summarizer** | M1 pattern özetinden candidate | Orta (M1 verisinden gelir) | Full matrix |
| **Replay engine** | Counterfactual veya outcome alignment sonucu | Düşük-orta (replay-validated) | Full matrix |
| **Human** (operator) | Direct write | Düşük (provenance güçlü) | Subject_class'a göre (§14) |
| **System policy update** (SourceTrust, DeonticPolicy) | Sistem-kaynaklı reliability/policy değişimi | Orta (kalibre değişimi) | Full matrix + human approval |

### Kural

> *M2'ye gate'siz sistem-kaynaklı yazı yok.*

Tüm sistem-kaynaklı candidate'lar (core, summarizer, replay, system policy) gate'ten geçer. İnsan direct write farklı profil takip eder ama yine audit zorunlu (§14).

### Forbidden

- Adapter'ın doğrudan M2'ye yazması (gate'siz)
- LLM'in candidate üretmesi (HumanIntentEvent kanalı zaten var, M3'te konuşma kaydı; M2 değil)
- Çekirdeğin M2'ye gate'i atlayarak yazması
- Summarizer'ın gate'i atlayarak doğrudan yazması

---

## 7. CandidateMemoryRecord Schema

### Yapı

```
CandidateMemoryRecord
├── record_id
├── subject_class                       # source_trust | episodic | structured_fact | ...
├── content_body                        # type-specific
├── proposed_by                         # core | summarizer | replay | human | system_policy
├── proposed_at
├── candidate_provenance
│   ├── source_layer                    # observer | replay | gate-coupled
│   ├── trigger_event_refs              # hangi M1 event'leri tetikledi
│   └── proposed_via                    # memory_write_intention | summarization | replay_outcome | direct_human_write
├── evidence_refs                       # internal_only_refs + external_corroboration_refs
├── status                              # candidate | verified | active | superseded | rejected | expired | quarantined
├── status_history                      # her geçişin M1 event ref'i
├── gate_test_results                   # son evaluation sonuçları (boolean/sayısal)
├── self_deception_risk                 # LOW | MEDIUM | HIGH
├── contradiction_level                 # sayısal
├── candidate_max_age_ref               # subject_class'a göre
├── quarantine_max_age_ref              # quarantined statüde geçerli
└── version
```

### Notlar

- `evidence_refs` iki alt-kategori: `internal_only_refs` (sistemin kendi M1 event'leri) + `external_corroboration_refs` (adapter, human, outcome, signed artifact)
- `self_deception_risk` gate tarafından **mekanik olarak** hesaplanır (bkz. §13)
- `gate_test_results` her testin pass/fail sonucu — audit için ham veri

---

## 8. Subject Class × Evidence Axes Verification Matrix

### Principle

Verified statüsü için gerekli evidence kombinasyonu **subject_class'a göre değişir**. Tek üniversal AND/OR yoktur. Her subject_class kendi matrix satırına tabidir.

### Rationale

`source_trust`, `episodic`, `deontic_policy`, `structured_fact`, `procedural`, `narrative_claim` aynı epistemik doğada değildir. Source trust outcome misalignment pattern'i ister; episodic causal_refs ister; structured_fact cross-source corroboration ister. Bu farklılık matrix ile yazılır.

### Verification matrix (kavramsal)

```
source_trust:
    sustained_outcome_pattern
    AND replay_survival
    AND contradiction_below_threshold
    AND provenance_recorded

episodic:
    causal_refs_minimum
    AND contradiction_below_threshold
    AND staleness_below_threshold
    AND duplicate_check_passed

structured_fact:
    (cross_source_corroboration
        OR (single_source AND high_reliability_band AND strong_provenance))
    AND contradiction_below_threshold

procedural:
    minimum_observation_count
    AND outcome_alignment
    AND replay_survival

deontic_policy:
    epistemic_validation_pass
    AND human_approval
    AND rollback_safe
    AND no_constitutional_conflict

bootstrap_reference:
    provenance IN {human, genesis}
    AND SELF_GENESIS or BOOTSTRAP_M2_INJECTION audit exists

narrative_claim / causal_explanation / decision_rationale:
    external_corroboration_refs is not empty
    AND self_deception_risk != HIGH

incident:
    causal_refs_minimum
    AND (provenance:human OR observer_evidence_strong)
    AND contradiction_below_threshold

incident_human_record (subset of incident):
    provenance:human
    AND human_decision_record_signature
    AND audit_path_intact
```

### Critical kural

> *Yeni subject_class eklenirse, verification_matrix satırı da zorunlu.*
> *Matrix satırı olmayan subject_class M2'ye verified yazılamaz.*

Bu, "ileride biri `subject_class = strategy_belief` eklesin ama gate ne yapacağını bilemesin" açığını kapatır.

### Matrix versioning

- Matrix bu belge ile birlikte revize edilir
- Yeni subject_class ekleme → `safety_tightening` compatibility class (BOOTSTRAP §23)
- Matrix kuralı zayıflatma (eksik evidence ile verified) → **forbidden**
- Matrix kuralı sertleştirme → `safety_tightening`

### Forbidden

- Matrix satırı tanımlanmamış subject_class için verified atamak
- Matrix gereksinimini gate yargısıyla bypass etmek
- Runtime'da matrix güncellemek

---

## 9. Candidate Status Machine

### Statüler

```
candidate
    ↓ (verification kuralları geçti)
verified
    ↓ (active hale getir — opsiyonel adım)
active                ← şu an kullanılan (varsa)
    ↓ (yeni daha güçlü kayıt geldi)
superseded

Yan yollar:
    candidate → rejected     (verification çürüttü)
    candidate → quarantined  (şüpheli ama kayda değer)
    candidate → expired      (candidate_max_age aşıldı)
    quarantined → verified   (yeniden kanıtla)
    quarantined → rejected   (replay/outcome çürüttü)
    quarantined → expired    (quarantine_max_age aşıldı)
    quarantined → superseded (yeni daha güçlü kayıt)
    verified → expired       (verified_max_age aşıldı)
    verified → superseded    (üst kayıt geldi)
```

### Statü özellikleri

| Statü | RecallEvent üretir? | Audit | Açıklama |
|-------|---------------------|-------|----------|
| `candidate` | Düşük confidence ile | M1 var | Henüz doğrulanmadı |
| `verified` | Normal confidence | M1 var | Verification matrix geçti |
| `active` | Normal confidence (varsa) | M1 var | Şu an kullanılan (deontic_policy gibi tek-active tipler için) |
| `superseded` | Üretmez | M1'de kalır | Eski hali, history için |
| `rejected` | Üretmez | M1'de kalır | Çürüdü |
| `expired` | Üretmez | M1'de kalır | Süre doldu |
| `quarantined` | **Üretmez** | M1 var | Şüpheli, bekleme |

### Quarantined statü detayı

> *Quarantined kayıt "şüpheli ama kayda değer"dir. Sistem onu unutmuyor, ama gerçekmiş gibi kullanmıyor.*

- RecallEvent üretmez (verified gibi davranamaz)
- M2'de görünür ama operational truth değildir
- Periyodik re-validation tetiklenebilir (replay engine veya summarizer)
- Maks süre `quarantine_max_age` (subject_class'a göre değişir)
- Süre dolduğunda otomatik `expired`

### Aging

Hiçbir statü sonsuza kadar geçici kalamaz:

```
candidate_max_age[subject_class]      = subject_class'a göre
quarantine_max_age[subject_class]     = subject_class'a göre
verified_max_age[subject_class]       = bazıları için (örn. operational policy)
```

Kesin değerler `MEMORY_WRITE_GATE_NUMERICS.md` veya implementation konusu. G sadece **kuralı** ("kayıt sonsuza kadar bekleyemez") anayasallaştırır.

### Verified geçişi anlık

> *Verification does not rewrite history.*

`verified_at` anlıktır. Eski RecallEvent'ler o sıradaki statüyle kalır (audit). Sonraki RecallEvent'ler verified confidence ile gelir. Geriye dönük gerçeklik üretmez.

### Forbidden

- Statü "sonsuza kadar candidate" kalmak
- Verified statüsünün retroaktif uygulanması
- Quarantined kaydın RecallEvent üretmesi
- Rejected kaydın silinmesi (M1'de history kalır)

---

## 10. Evidence Requirements

Verification için temel evidence eksenleri (matrix'in girdileri):

### Evidence eksenleri

```
evidence_refs                 # bağlantılı M1 event'leri
replay_survival               # replay engine bu pattern'i çürüttü mü
outcome_alignment             # gerçek outcome ile uyumlu mu
contradiction_level           # mevcut state ile çelişki seviyesi
source_provenance_strength    # kaynak güvenirlik bandı
staleness_status              # yaş ne kadar, eski mi
duplicate_check               # zaten benzer kayıt var mı
self_deception_risk           # §13'deki mekanik test
external_corroboration_refs   # sistem-dışı kanıt event'leri
cross_source_count            # kaç farklı source destekliyor
```

### Critical kural — pulse evidence değildir

> *Repeated attention is not evidence.*
> *Repeated recall is not evidence.*
> *Repeated assertion is not evidence.*

Bir assembly'nin sürekli pulse alması (B §17), bir kaydın sürekli recall edilmesi, veya sistemin sürekli aynı şeyi iddia etmesi **verification için yetersizdir**. Pulse + recall + iddia birikimi self-reinforcement döngüsüne kapı açar.

Doğru kanıt:
- **External corroboration** (adapter observation, human direct, outcome, signed artifact)
- **Replay survival** (counterfactual test'ten geçti)
- **Outcome alignment** (gerçek outcome predicted pattern ile uyuştu)

---

## 11. Replay and Outcome Requirements

### Replay survival

Candidate replay engine tarafından test edilir:
- Counterfactual intervention: "Bu kayıt olmasa pattern aynı çıkar mıydı?"
- Replay survival score: kaydın gerekliliği

Replay survival düşükse: kayıt **çürük** — spurious pattern olabilir.

### Outcome alignment

Candidate gerçek outcome'larla karşılaştırılır:
- Pattern X gözlendi → kayıt Y önerildi → sonradan outcome Z geldi
- Y'nin tahmin ettiği outcome Z ile uyuşuyor mu?

Outcome alignment düşükse: kayıt **yanlış prediction** üretiyor demektir.

### Beklenti zamanı

Outcome bazı subject_class'larda hızlı gelir (anlık geri bildirim), bazılarında yavaş (uzun vadeli pattern):

```
fast outcome subject_classes:
    recall_confidence_calibration   # saniyeler
    pulse_evaluation                 # dakikalar

slow outcome subject_classes:
    source_trust                     # haftalar/aylar
    procedural                       # günler
    deontic_policy_effectiveness     # haftalar
```

Bu yüzden candidate `candidate_max_age` ile sonsuza dek beklemez — ama beklemesi gerek. Subject_class kararı.

---

## 12. Provenance and Staleness

### Provenance

Her candidate provenance kayıtlı taşır:

```
candidate_provenance.proposed_via:
    memory_write_intention     # çekirdek niyeti
    summarization              # observer summarizer
    replay_outcome             # replay engine
    direct_human_write         # operator
    system_policy_update       # SourceTrust, DeonticPolicy
```

Gate provenance'a göre farklı testler çalıştırır (§14 ve §15).

### Staleness

Candidate ne kadar eski olursa o kadar zayıf:

```
candidate_age = now - proposed_at

if candidate_age > candidate_max_age[subject_class]:
    status → expired
```

Verified kayıtlar için staleness farklı boyut:

```
staleness_ms = now - last_outcome_alignment_at

if staleness_ms > max_staleness_threshold[subject_class]:
    re-validation tetiklenir
    eğer outcome alignment hâlâ geçerse: stays verified
    eğer geçmezse: quarantined veya rejected
```

### Forbidden

- Provenance'sız candidate
- Eski outcome'lara dayanan kayıt için re-validation atlama
- Staleness threshold'unu runtime'da değiştirme

---

## 13. Self-Deception Detection Mechanism

### Principle

Sistem kendi anlatısını "verified fact" olarak M2'ye kazıyamaz. Self-deception önleme, bu belgenin **kalbidir**.

### Rationale

Sistemin "ben şu kararı şu sebepten verdim" diye M2'ye yazmak istemesi doğal. Ama bu kayıt **kendi M1 izinden gelen kanıtla** doğrulanırsa, sistem kendi hikâyesini kendisi onaylamış olur — recursive self-reinforcement.

Doğru: bu tip kayıtlar **external corroboration** gerektirir.

### Mekanik tanım

```
self_deception_risk = HIGH when:

    candidate.subject_class IN {
        narrative_claim,
        causal_explanation,
        decision_rationale,
        self_assessment
    }

    AND evidence_refs ⊆ internal_only_refs

    AND external_corroboration_refs is empty
```

### `internal_only_refs` (sistem-içi kaynaklar)

```
neural events       (assembly, synapse, contradiction)
attention events    (workspace pulse, replay)
memory events       (recall, write proposals from self)
replay events       (sleep replay, attention replay)
summarizer events   (kendi özetleri)
self-field derived events
system-generated explanation events
```

### `external_corroboration_refs` (sistem-dışı kaynaklar)

```
ObservationEvent (adapter provenance ile)
Human direct record (provenance: human)
OutcomeReceived (dış sonuç)
Verified M2 record (non-system provenance ile)
Signed operational/deontic artifact (insan imzalı)
```

### Gate'in davranışı

```
self_deception_risk = HIGH:
    → verified olamaz
    → değerli kayıtsa: quarantined
    → açıkça yanlışsa: rejected

self_deception_risk = MEDIUM:
    → external corroboration eklenmesi beklenir
    → candidate kalır

self_deception_risk = LOW:
    → matrix'in diğer testlerine geçer
```

### Kilit cümleler

> **Sistemin kendi açıklaması kanıt değildir.**
> **Kayıt olabilir, ama verified fact değildir.**

### Violation Test
> *Self-deception detection mekanik mi (boolean/sayısal), yoksa yargı içeriyor mu?*
>
> Yargı içeriyorsa ihlal. Test deterministic event family + provenance + refs boyutlarına bakar.

---

## 14. Subject Class Specific Rules

Verification matrix (§8) her subject_class için temel kuralı verir. Burada daha derin nüanslar:

### source_trust

- Tek bir yanlış outcome reliability_band düşürmez
- `sustained_outcome_pattern` gerekir (örn. N event'in M'sinde misalignment)
- Replay engine periyodik re-validation tetikler
- Verified statü için human approval **gerekmez** (sistemin kendi kalibrasyonu)

### structured_fact

- Cross-source corroboration tercih edilir
- Tek source kayıt için: high_reliability_band + strong_provenance + outcome_alignment
- Domain ontolojisi sızdırmaz (Madde 1/3)

### procedural (compatibility matrix)

- Pattern başlangıçta candidate
- N tekrar gözlem + outcome alignment → verified
- Replay survival kritik

### deontic_policy

- Memory Write Gate'ten geçer (epistemic risk)
- Ek olarak human approval şart (action risk de potansiyel)
- DEONTIC_GATE §18'deki normal flow ile uyumlu

### bootstrap_reference

- Provenance: human|genesis
- SELF_GENESIS veya BOOTSTRAP_M2_INJECTION audit zinciri
- Otomatik verified (statü doğumda atanır)

### narrative_claim, causal_explanation, decision_rationale

- Self-deception detection mekaniği zorunlu (§13)
- External corroboration olmadan verified olamaz
- Yüksek self_deception_risk → quarantined varsayılan

---

## 15. Human Writes vs System Writes

### İki kategori

İnsan iki tür şey yazabilir:

**Kendi eylemi hakkında olgu** (auto-verified):
```
operator_decision_record           "Halit X saatte kill-switch çekti"
incident_human_record              "Halit X olayı bildirdi"
deontic_kill_switch_action_record  "Halit kill-switch deactive etti"
bootstrap_reference                "kuruluş referansları"
signed_administrative_reference    "imzalı yönetimsel ref"
```

**Dünya hakkında iddia** (matrix-required):
```
structured_fact                    "Şu adapter X özelliklerine sahiptir"
procedural                          "Şu lookup tablosu kullanılsın"
narrative_claim                     "Sistem şu yüzden bunu yaptı"
causal_explanation                  "X nedeni Y sonucudur"
source_trust                        "Şu source güvenilir/güvensiz"
```

### Critical ayrım

> **Halit yazdı ≠ Halit doğru söylüyor.**
> **Halit yazdı = Halit'in beyanı kayda geçti.**

İnsan provenance evidence gücünü artırır, ama her zaman hakikat üretmez. Kendi eyleminin kaydı tartışılmaz olgu (verified); dünya iddiası matrix'e tabi.

### Kural

```
Human-write auto-verified subject_classes:
    Provenance: human kayıtlı.
    Audit path zorunlu.
    Subject_class otomatik verified statü kabul eder.
    M1'e MEMORY_RECORD_STATUS_CHANGED yazılır (provenance: human).

Human-write matrix-required subject_classes:
    Provenance: human kayıtlı, ama verified statüsü matrix'ten geçmek zorunda.
    Outcome / cross_source / replay survival gerekebilir.
    Provenance:human evidence gücünü artırır ama otomatik verified yapmaz.
```

### Forbidden

- İnsan write auto-verified bypass'ı (matrix-required tipler için)
- Audit path'siz insan write
- İnsan tarafından subject_class atlama
- İnsan write'in M1 audit'siz gerçekleşmesi

---

## 16. Observer Summarizer Boundary

`OBSERVER_LEDGER_SCHEMA.md` §5'te tanımlı recorder/summarizer ayrımı. Memory Write Gate açısından kritik nokta:

> *Summarizer M2'ye doğrudan yazamaz. Memory Write Gate'e candidate önerir.*

### Summarizer'ın gate ile ilişkisi

```
Summarizer M1'i okur
    ↓
Pattern özet üretir (mekanik kurala göre — bkz. OBSERVER_LEDGER §5)
    ↓
M2'ye CandidateMemoryRecord önerir
    ↓
Memory Write Gate normal kurallarla değerlendirir
    ↓
Summarizer'ın "bence önemli" demesi kanıt değildir
```

### Summarizer candidate kuralları

- Summarizer kendi başına "önem" kararı veremez
- Sadece önceden tanımlı kurallara göre özet adayı üretir
- Her özetleme M1'e meta-event olarak yazılır (OBSERVER §15)
- Memory Write Gate'in self-deception testi summarizer-kaynaklı candidate'lara da uygulanır

### Critical

> *Summarizer'ın "bence bu önemli" iddiası evidence değildir.*
> *Summarizer'ın matrix-based candidate önerisi gate'ten geçer.*

---

## 17. Gate Decision / Status Events

### Canonical event

```
MEMORY_RECORD_STATUS_CHANGED
```

Statü geçişleri **tek event tipi**. Alt durumlar field olarak gelir (B/C/E/F'deki "tek event, statü field" disiplinine uygun).

### Şema

```
MemoryRecordStatusChangedEvent
├── event_id
├── event_type: MEMORY_RECORD_STATUS_CHANGED
├── event_family: memory
├── record_id
├── subject_class
├── old_status                  # candidate | verified | active | superseded | rejected | expired | quarantined
├── new_status
├── trigger                     # gate_evaluation | replay_validation | outcome_alignment | human_approval | expiration | supersession | quarantine_review
├── gate_test_results           # boolean/sayısal test sonuçları (her test pass/fail)
├── evidence_refs               # internal + external
├── self_deception_risk         # LOW | MEDIUM | HIGH
├── contradiction_level
├── approved_by                 # varsa (insan/sistem)
├── memory_write_gate_pass_ref  # varsa
└── observer_snapshot_ref       # varsa
```

### Ayrı candidate doğum event'i

```
MEMORY_WRITE_PROPOSED
```

Candidate doğumu farklı mekanizma; statü geçişi değil. Bu event ayrı kalır. Şema MEMORY_CONTRACT §9'a uygun.

### Eski event tipleri (kaldırıldı)

Aşağıdaki event tipleri **canonical değildir**, `MEMORY_RECORD_STATUS_CHANGED` altında yaşar:

```
MEMORY_WRITE_GATE_PASSED       # status: candidate → verified
MEMORY_WRITE_GATE_REJECTED     # status: candidate → rejected
MEMORY_WRITE_VERIFIED          # status: candidate → verified
MEMORY_WRITE_QUARANTINED       # status: candidate → quarantined
```

OBSERVER_LEDGER_SCHEMA event catalog buna göre güncellenir (yan patch).

---

## 18. Audit Chain

### Audit zorunluluğu

Sistem sonradan şunları cevaplayabilmeli:

- Hangi candidate hangi statüye geçti?
- Hangi gate testleri uygulandı?
- Test sonuçları neydi (pass/fail her test için)?
- Self-deception risk nasıl hesaplandı?
- Hangi evidence ref'leri kullanıldı?
- İnsan approval'ı kim verdi, ne zaman?
- Quarantined kayıt ne kadar bekledi?

Cevap verilemiyorsa gate auditable değildir — Madde 7 ihlali.

### Audit path zorunluluğu

DEONTIC §8 Rule 8'de "no action if required audit path is unavailable" var. Aynı prensip burada:

> *No memory write if required audit path (M1 write) is unavailable.*
> *Audit edilemeyen kayıt M2'ye giremez.*

---

## 19. Cross-document Anchors

| Belge | Bağlantı |
|-------|----------|
| `CONSTITUTION.md` Madde 7 | Hafıza ayrılığı; bu belge M2 yazma kapısı detayı |
| `MEMORY_CONTRACT.md` §9 (Memory Write Gate) | Ana kavram tanımı |
| `MEMORY_CONTRACT.md` §10 (CandidateMemoryRecord) | Statü zinciri |
| `MEMORY_CONTRACT.md` §11 (Observer Relationship) | Summarizer rolü |
| `MEMORY_CONTRACT.md` M2 subject_class | Subject_class alt-türleme |
| `OBSERVER_LEDGER_SCHEMA.md` §5 | Recorder/summarizer rol ayrımı |
| `OBSERVER_LEDGER_SCHEMA.md` §10 | Permanence policy (MEMORY_RECORD_STATUS_CHANGED için satır) |
| `OBSERVER_LEDGER_SCHEMA.md` §19 | Event catalog (memory family) |
| `DEONTIC_GATE.md` §6 | Action-risk vs epistemic-risk ayrımı |
| `DEONTIC_GATE.md` §7 | DeonticPolicyRecord (deontic_policy subject_class için yan referans) |
| `BOOTSTRAP_GENOME.md` §20 | Bootstrap M2 (bootstrap_reference subject_class auto-verified) |
| `WORLD_INGRESS.md` §16 | SourceTrustRecord (source_trust subject_class) |

---

## 20. Violation Tests

1. **Gate deontic gate'in alt türü olarak konumlanmış mı?** (§4)
   - Evet ise ihlal.
2. **Gate truth engine'e dönüşmüş mü (yargı yapıyor mu)?** (§5)
   - Evet ise ihlal. Sadece deterministic test.
3. **Subject_class matrix satırı olmayan kayıt verified atanmış mı?** (§8)
   - Evet ise ihlal.
4. **Human assertion otomatik hakikat olmuş mu (matrix-required subject_class için)?** (§15)
   - Evet ise ihlal.
5. **Silent gate prensibi bozulmuş mu?** (§5)
   - Memory Write Gate kararı çekirdeğe payload_seed, pulse, InternalShockEvent veya RecallEvent olarak yansıyor mu? Evet ise ihlal.
6. **MEMORY_RECORD_STATUS_CHANGED canonical kullanılıyor mu?** (§17)
   - Hayır ise ihlal. Eski event tipleri (PASSED/REJECTED/VERIFIED/QUARANTINED) ayrı kullanılmamalı.
7. **Quarantined kayıt RecallEvent üretiyor mu?** (§9)
   - Evet ise ihlal.
8. **Self-deception detection mekanik mi?** (§13)
   - Yargı içeriyorsa ihlal. Test event family + provenance + refs üzerinden.
9. **Candidate sonsuza kadar bekleyebiliyor mu?** (§9)
   - Evet ise ihlal. candidate_max_age ile expired olmalı.
10. **Verified retroaktif uygulanıyor mu?** (§9)
    - Evet ise ihlal. verified_at anlık.
11. **Gate kendi kararından candidate üretiyor mu?** (§5)
    - Evet ise ihlal. Meta-pattern summarizer üzerinden gelir.
12. **Pulse/recall repetition evidence sayılıyor mu?** (§10)
    - Evet ise ihlal.
13. **Audit path yoksa M2 yazımı yapılıyor mu?** (§18)
    - Evet ise ihlal.
14. **Verification matrix runtime'da değişebilir mi?** (§8)
    - Evet ise ihlal.
15. **Gate testleri boolean/sayısal mı?** (§5)
    - Yargı veya semantic interpretation içeriyorsa ihlal.
16. **External corroboration olmadan narrative_claim verified yapılıyor mu?** (§13)
    - Evet ise ihlal.
17. **Memory Write Gate çekirdeğe geri yansıma üretiyor mu?** (§5)
    - Evet ise ihlal. Silent gate.

---

## 21. Open Questions

G çerçevesi kapanırken cevaplanmamış bırakılan sorular:

- **Kesin sayısal eşikler:** `min_evidence_count`, `max_contradiction_threshold`, `min_replay_survival`, `min_outcome_alignment`, `candidate_max_age[subject_class]`, `quarantine_max_age[subject_class]` → `MEMORY_WRITE_GATE_NUMERICS.md` veya implementation.
- **Subject_class matrix versioning:** Yeni subject_class eklerken matrix nasıl migrate olur? Eski candidate'ların matrix değişimine etkisi?
- **Replay survival score hesaplaması:** Counterfactual intervention nasıl yapılır, skor nasıl normalize edilir → `REPLAY_PROTOCOL.md` (henüz yazılmadı).
- **Outcome alignment metric:** Predicted vs actual outcome karşılaştırma metodolojisi → Implementation.
- **Cross-source corroboration tanımı:** Kaç "farklı" source gerek? Source ayrımı nasıl yapılır (source_adapter_id farklı yetince mi)? → SourceTrust ile birlikte spec.
- **Quarantine re-validation cadansı:** Quarantined kayıt ne sıklıkta yeniden test edilir? → Implementation.
- **Verified_max_age:** Hangi subject_class'lar için verified süre dolar (örn. operational policy), hangileri için kalıcı (örn. bootstrap_reference)?

Bu sorular cevaplanmadan implementation aşamasına geçilmez.

---

## Çekirdek özet — 13 karar + 17 kırmızı çizgi

### 13 ana karar
1. Memory Write Gate deontic gate'in alt türü değildir.
2. Gate hakikat üretmez; hakikat iddiasını statülendirir.
3. Gate sessizdir — kararları çekirdeğe geri yansımaz.
4. Verification matrix subject_class'a göre değişken (tek üniversal AND yok).
5. Matrix satırı olmayan subject_class verified olamaz.
6. Statü makinesi: candidate → verified → active → superseded; quarantined ve rejected yan yollar; expired terminal.
7. Verified geçişi anlık, retroaktif değil.
8. Pulse/recall repetition evidence değildir.
9. Self-deception detection mekanik (event family + provenance + refs).
10. İnsan yazdı ≠ İnsan doğru söylüyor. İnsan eylem kaydı auto-verified; insan dünya iddiası matrix-required.
11. Tek canonical event: MEMORY_RECORD_STATUS_CHANGED.
12. Gate testleri boolean/sayısal; yargı yok.
13. Gate kendi kararından candidate üretemez; pattern öğrenme summarizer üzerinden.

### 17 kırmızı çizgi
Bkz. §20.

---

## Kilit cümleler

> **Memory Write Gate, sistemin kendi hikâyesine inanmasını engelleyen epistemik frendir.**
>
> **Memory Write Gate hakikat üretmez. Memory Write Gate hafızaya yazılacak hakikat iddiasını statülendirir.**
>
> **Deontic gate eylem riskini sınırlar. Memory Write Gate epistemik riski sınırlar.**
>
> **Sistemin kendi açıklaması kanıt değildir. Kayıt olabilir, ama verified fact değildir.**
>
> **Memory Write Gate is silent: rejections, quarantines, and verifications do not echo into the core.**
>
> **Verification does not rewrite history.**
>
> **Halit yazdı ≠ Halit doğru söylüyor. Halit yazdı = Halit'in beyanı kayda geçti.**
>
> **Repeated attention is not evidence. Repeated recall is not evidence. Repeated assertion is not evidence.**

---

## Versiyon

- **v0.1** — 18 Mayıs 2026 — Frozen Draft. Conceptual phase. No implementation authority.
- `CONSTITUTION.md` Madde 7 / `MEMORY_CONTRACT.md` §9 alt-spec'i.
- A-F belgelerinin M2 yazma kapısı sözleşmesi.
- Konuşma soyağacı: [`docs/conversations/0007-memory-write-gate.md`](./docs/conversations/0007-memory-write-gate.md)
