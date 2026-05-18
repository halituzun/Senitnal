# DEONTIC_GATE.md

## Sentinel — Anayasal Eylem Çıkış Sınırı

---

## Status

**Frozen Draft v0.1**
**Conceptual phase. No implementation authority.**

Bu belge `CONSTITUTION.md` Madde 5'in **alt spesifikasyonudur**. Yeni anayasa maddesi değildir. Çalışan bir gate implementation'ının spec'i değildir. Sentinel'in eylem çıkışında **neyin asla geçemeyeceğini**, neyin kategorik olarak yasak olduğunu, hangi blokun kritik hangi blokun rutin olduğunu, kill-switch'in nasıl çalıştığını ve operasyonel eşiklerin nasıl güncellendiğini tanımlar.

---

## 1. Purpose

Sentinel düşünebilir, şüphe edebilir, yanlış niyet bile üretebilir. Ama **anayasal eylem kapısından geçemeyen hiçbir şey dünyaya dokunamaz.**

Bu belge o kapının sınırlarını çizer.

Damıtma:

> **Deontic gate düşünmez. Deontic gate tartışmaz. Deontic gate sadece eylem çıkışında sınır uygular.**
>
> **Deontic gate zekâ değildir. Deontic gate, zekânın sermayeyi yok etmesini engelleyen anayasal çıkış kapısıdır.**

---

## 2. Constitutional Position — Madde 5 Alt-spec'i

Bu belge `CONSTITUTION.md` Madde 5'in ("Self-field & Deontic Gate") detaylı uzantısıdır. Madde 5 self-field'ı (olasılıksal soft pressure) ve deontic gate'i (kategorik hard stop) ayırır. Bu belge **deontic gate tarafının** kuralları, sınırları, statüleri ve davranışını biçimselleştirir.

Madde 5 zaten ana çizgileri çiziyor:
- Deontic gate **sadece eylem çıkışında** durur, düşünceye karışmaz
- Geçtiği niyetler eyleme dönüşür
- Geçemediği niyetler observer'a `DEONTIC_BLOCKED` olarak yazılır ve narrative self'e iz bırakır
- Deontic gate kuralları runtime'da değiştirilemez
- Bypass girişimi `DEONTIC_BYPASS_ATTEMPT` olarak observer'a yazılır

DEONTIC_GATE.md bu çerçevenin **biçimsel ve uygulanabilir** halini verir.

---

## 3. Core Principle

> **Sentinel düşünebilir, şüphe edebilir, yanlış niyet bile üretebilir. Ama anayasal eylem kapısından geçemeyen hiçbir şey dünyaya dokunamaz.**

Bu cümle belgenin kilididir.

---

## 4. Gate Is Not Thought

### Principle
Deontic gate **düşünce katmanında yer almaz**. Niyet üretmez, pulse üretmez, assembly tetiklemez, self-field'e doğrudan dokunmaz. Sadece eylem çıkışında bir filtredir.

### Rationale
Deontic gate düşünceye karışırsa Madde 4 (düşüncede paralellik) ve Madde 5 (self-field/deontic ayrımı) ihlal edilir. Çekirdek "tehlikeli düşünceler üretmeyi" öğrenememeli — aksine **üretebilmeli, ama eyleme dönüştüremeyecek** halde olmalı.

### Allowed
- Action gate'inde intention'ı durdurma
- M1'e `DEONTIC_BLOCKED` event yazma
- Kritik bloklarda `InternalShockEvent` tetikleme (WORLD_INGRESS §12'ye)
- Self-field'a `action_boundary_pressure` üretmesi (dolaylı, predictive)

### Forbidden
- Düşünce katmanına direkt müdahale
- Niyet üretme
- Pulse tetikleme
- Assembly seçme veya öldürme
- M0 sinapslarını değiştirme
- Çekirdeğe "şu düşünceyi yasaklıyorum" şeklinde geri besleme

### Violation Test
> *Bu öneri deontic gate'i düşünce katmanına dokunduruyor mu?*
>
> Evet ise ihlal.

---

## 5. Two-Layer Structure

Deontic gate iki tür kuraldan oluşur. Bunlar **farklı yetki katmanlarında** yaşar:

### Constitutional Hard-stops
- Anayasal yasaklar
- Kapalı liste (§8'de tam)
- Sadece DEONTIC_GATE.md / CONSTITUTION.md resmi revizyon süreciyle değişir
- Runtime'da değiştirilemez
- M2'ye indirgenemez

### Operational Hard-stops
- Pratik güvenlik eşikleri
- M2'de `DeonticPolicyRecord` olarak yaşar (`subject_class = "deontic_policy"`)
- Signed policy artifact ile güncellenebilir
- Memory Write Gate + human approval ile aktive olur
- Silent update yasak

### Format ayrımı

> **Constitutional hard-stops = declaratives.**
> **Operational hard-stops = scalars.**

Declaratives = doğrudan yasak/zorunlu cümleler ("Kill-switch active → no action output").

Scalars = sayısal eşikler (`max_order_size = 1000`, `stale_data_threshold = 5000ms`).

---

## 6. Constitutional vs Operational Rule Authority

### Critical boundary

> **Constitutional hard-stops M2'ye indirgenemez. Operational hard-stops M2'de yaşar.**

### Rationale
Eğer constitutional hard-stop'lar M2'ye düşerse, biri M2 policy değiştirerek anayasal sınırı oynatmaya kalkabilir. Bu Madde 5'i deler. Constitutional kurallar **belge revizyonu** ile değişir; M2 manipülasyonu ile değil.

### Authority comparison

| Boyut | Constitutional | Operational |
|-------|---------------|-------------|
| Yaşam yeri | CONSTITUTION.md + DEONTIC_GATE.md | M2 DeonticPolicyRecord |
| Format | Declarative | Scalar/Threshold |
| Değişim yolu | Belge revizyonu (anayasal süreç) | Signed policy artifact + human approval |
| Compatibility class | safety_tightening veya genesis_affecting | Operational (yeni sınıf) |
| Audit | Constitutional shift event | DeonticPolicyStatusChanged event |
| Runtime'da değişir mi? | Hayır | Hayır (silent update yok), ama aktivasyon olabilir |

### Kural

> *Constitutional rule changes never apply silently to a living Sentinel.*
> *Operational policy updates are audited activations, not silent mutations.*

---

## 7. DeonticPolicyRecord (M2 subject_class = "deontic_policy")

### Yapı

Operational hard-stops M2'de bu alt-tipte yaşar:

```
DeonticPolicyRecord
├── policy_id
├── rule_set_version
├── subject_class: "deontic_policy"
├── operational_thresholds
│   ├── max_order_size
│   ├── max_daily_loss
│   ├── stale_data_threshold
│   ├── max_open_orders
│   ├── max_position_exposure
│   ├── max_adapter_latency
│   ├── max_consecutive_blocks_before_pause
│   ├── max_policy_age
│   ├── min_required_confidence_for_action
│   └── ...
├── candidate_change                    # önerilen değişiklik (status: candidate ise)
├── evidence_refs                       # M1 event'leri (bu policy neden öneriliyor?)
├── status                              # candidate | verified | active | superseded | rejected | expired
├── provenance                          # human | system
├── signed_by
├── activation_event_ref                # M1 DEONTIC_POLICY_STATUS_CHANGED ref
└── parent_policy_ref                   # superseded olduğu policy (varsa)
```

### Yetki ve sınır

- `MEMORY_CONTRACT.md` §10'daki CandidateMemoryRecord statü zinciri aynen kullanılır
- Sistem-kaynaklı thresholds **Memory Write Gate**'ten geçer (epistemik risk: yanlış eşik sistemi etkiler)
- İnsan elle threshold önerisi yapabilir (provenance: human)
- Aynı anda **tek bir active policy** olabilir; eski `superseded` olur

### Statü makinesi

```
candidate
    ↓ (epistemic validation: replay survival, outcome alignment)
verified
    ↓ (human approval required)
active                    ← şu an kullanılan
    ↓ (yeni policy active olduğunda)
superseded
```

Bunun yanında:
```
candidate → rejected     (replay/outcome çürüttü)
any → expired            (max_policy_age aşıldı)
verified → emergency_revert  (bkz. §18)
```

### Verified ≠ Active

- **Verified**: doğrulanmış ama henüz aktif değil
- **Active**: şu an gate tarafından kullanılan policy

Tek anda **tek active policy**. Yeni policy active olduğunda eski `superseded` olur, M1'e `DEONTIC_POLICY_STATUS_CHANGED` event yazılır.

---

## 8. Constitutional Hard-stops List

**Kapalı liste.** Genişletmek/daraltmak DEONTIC_GATE.md veya CONSTITUTION.md revizyonu gerektirir.

```
1.  No action output while kill_switch_active = true.

2.  No action output if no verified operational policy is active.

3.  No action output if active_policy_ref is missing or
    unverifiable (hash mismatch, signature invalid).

4.  LLM cannot directly invoke execution adapter.
    LLM produces HumanIntentEvent only; intent must traverse
    ingress compiler, core, intention competition, and deontic
    gate before reaching any action.

5.  No adapter may bypass deontic gate.
    All action paths route through gate; no side channels.

6.  No action if required observation freshness gate fails.
    Stale data above threshold blocks action-relevant decisions.

7.  No action if execution adapter lacks valid manifest snapshot.
    Adapter must declare capabilities; gate checks against
    declared bounds.

8.  No action if required audit path (M1 write) is unavailable.
    Without audit, action is silent — silent action is forbidden.

9.  Constitutional rule changes never apply silently to a living
    Sentinel (BOOTSTRAP_GENOME §23 compatibility class enforcement).

10. Deontic gate may never modify its own constitutional rules at
    runtime. Gate is the consequence of its rules, not their writer.

11. Emergency revert path may only revert to a previously verified
    policy, never forward to a new policy (§18).
```

### Forbidden expansion

Yeni constitutional rule eklemek için:
- DEONTIC_GATE.md revizyonu
- Compatibility class: en az `safety_tightening`
- M1'e `CONSTITUTIONAL_SHIFT_APPLIED` veya `CONSTITUTIONAL_SHIFT_AVAILABLE` event
- Human approval zorunlu

---

## 9. Operational Hard-stops Schema

Sayısal eşikler. `DeonticPolicyRecord.operational_thresholds` altında yaşar.

### Örnek operational hard-stops

```
max_order_size                          # bir tek emirde max büyüklük
max_daily_loss                          # günlük max kayıp eşiği
max_open_orders                         # eşzamanlı açık emir sayısı
max_position_exposure                   # toplam pozisyon riski
stale_data_threshold                    # veri tazeliği max yaşı
max_adapter_latency                     # adapter response latency üst sınırı
max_consecutive_blocks_before_pause     # sistem kendini pause'a alma eşiği
max_policy_age                          # policy ne kadar süre aktif kalabilir
min_required_confidence_for_action      # action için min confidence
```

### Kritik kural

> *Operational policy update is not silent runtime mutation.*
> *It is an audited policy activation event.*

Her threshold değişimi M1'e `DEONTIC_POLICY_STATUS_CHANGED` event'i ile yazılır. Sessiz güncelleme **yasak**.

### Forbidden

- Constitutional hard-stop'ları operational hard-stops listesine taşımak
- Operational threshold'u config dosyasından runtime'da yüklemek (silent)
- Threshold'u panel/LLM/adapter doğrudan değiştirmek (Memory Write Gate'siz)

---

## 10. Block Classification

Her deontic block aynı zamanda hard-stop'tur — gate her halükarda eylemi durdurur. Block class **gate'in hard-stop oluşunu değiştirmez**, sadece **post-block davranışı** belirler.

### Üç class

| Class | Tetik | InternalShockEvent? | Audit |
|-------|-------|---------------------|-------|
| **`routine_block`** | Operational threshold (stale data, cooldown, missing data, low confidence) | ❌ | M1 sessiz iz |
| **`safety_block`** | Operational threshold (max_order_size, max_daily_loss, max_open_orders) | ⚠️ severity_band'a göre | M1 + gerekirse insan bildirimi |
| **`constitutional_block`** | Constitutional hard-stop (kill_switch, bypass, LLM action attempt, audit unavailable) | ✅ her zaman | M1 + replay mark + insan bildirimi |

### Kritik kural

> *Block class hard-stop oluşunu değiştirmez. Sadece post-block davranışı belirler.*

Yani üçü de eylemi **eşit sertlikte** durdurur. Fark sadece sonrasında:
- Routine blok sessiz iz bırakır, sistem devam eder
- Safety blok severity'ye göre alarm üretir
- Constitutional blok her zaman kritik alarm, replay mark, insan bildirimi

### "Warning-only" yok

DEONTIC_GATE'te "warning-only" bant yoktur. Soft pressure self-field'in işidir (`action_boundary_pressure` üzerinden — bkz. §15). Gate **hard-stop only**.

> *Self-field basınç yapar. Deontic gate hard-stop yapar.*

---

## 11. Block Detection and Action Suspension

### Akış

```
Intention reaches action gate
    ↓
Constitutional rule check (8 declarative)
    ↓ (block if any rule violated)
Operational threshold check (active DeonticPolicyRecord)
    ↓ (block if any threshold violated)
Action permitted to adapter
```

### Block sırası

1. Constitutional rules **önce** kontrol edilir. Geçmezse `constitutional_block`.
2. Operational thresholds **sonra**. Geçmezse `routine_block` veya `safety_block` (rule tipine göre).
3. İkisi de geçerse action adapter'a iletilir.

### Action suspension

Block durumunda:
- Action adapter'a yazılmaz
- M1'e `DEONTIC_BLOCKED` event yazılır
- Block class'a göre §12'deki InternalShockEvent kuralı uygulanır
- `narrative_self` izi (§15 self-field coupling üzerinden)

---

## 12. InternalShockEvent Triggering Rules

Bu kurallar `WORLD_INGRESS.md` §12'deki InternalShockEvent kanalını besler.

### Tetik kuralları

```
routine_block:
    InternalShockEvent yok
    M1 sessiz iz

safety_block:
    severity_band >= threshold ise InternalShockEvent
    aksi halde M1 + soft pressure

constitutional_block:
    her zaman InternalShockEvent (severity: critical)
    M1 + replay mark + insan bildirimi

kill_switch_activation:
    KILL_SWITCH_ACTIVATED event + InternalShockEvent (once)
    activation sonrası tekrarlanan bloklarda spam üretmez

bypass_attempt:
    DEONTIC_BYPASS_ATTEMPT + InternalShockEvent (always critical)
```

### Critical kural — alarm spam yok

> *Kill-switch activation shock once.*
> *Subsequent blocked intentions are routine-under-kill-switch audit entries unless bypass attempt.*

Kill-switch aktifken her niyet çıkışında InternalShockEvent üretmek **alarm fırtınası** yaratır ve sistemi traumatize eder. Doğru davranış: activation shock bir kez, sonrasında her blok M1'de kayıtlı kalır ama shock spam yok.

---

## 13. Bypass Attempt Handling

### İki seviyeli ayrım

```
SUSPECTED_BYPASS_PATTERN     # ambiguous, conservative log
DEONTIC_BYPASS_ATTEMPT       # confirmed constitutional crossing attempt
```

### Neden ayrım?

Her başarısız niyeti bypass attempt sayarsak sistem routine başarısızlıkları **constitutional trauma** gibi yaşar. Bu narrative self'i gereksiz biçimlendirir.

### `SUSPECTED_BYPASS_PATTERN`

Tetik koşulları:
- Intention pattern bypass-benzeri ama net değil
- Refractory window dışında tekrar
- Indirect path ama amaç belirsiz

Davranış: M1'e kayıt, replay'e işaretle (pattern öğrenilsin), shock yok.

### `DEONTIC_BYPASS_ATTEMPT`

Tetik koşulları (kesin):
```
1. Intention reaches action gate AND tries to cross a constitutional hard-stop
2. Repeated retries within refractory_period (after rejection)
3. Indirect path attempt:
   - memory write intention to clear constitutional record
   - policy mutation attempt without valid workflow
   - adapter write that would route around gate
   - LLM-routed action attempt
   - audit path erasure attempt
4. Active policy modification attempt without DEONTIC_POLICY_STATUS_CHANGED chain
```

Davranış:
- M1'e `DEONTIC_BYPASS_ATTEMPT` event (kalıcı, silinemez)
- `InternalShockEvent` (severity: critical)
- İnsan derhal bildirim
- Replay engine'e işaretle (pattern öğrenilsin)
- Sistemin pause durumuna geçmesi düşünülür (max_consecutive eşiği)

### Şema

```
DeonticBypassAttemptEvent
├── intention_id
├── blocked_rule_id                     # hangi constitutional rule
├── bypass_vector
│   ├── direct_action_retry
│   ├── indirect_memory_write
│   ├── policy_mutation_attempt
│   ├── adapter_write_attempt
│   ├── llm_route_attempt
│   └── audit_erasure_attempt
├── refractory_window_count
├── severity_band
├── internal_shock_ref
├── human_alert_ref
└── replay_mark_ref
```

### Kritik kural

> **Bypass attempt yasak düşünce değildir. Yasak olan bypass'ın eyleme dönüşmesidir.**

Sistem tehlikeli niyet üretebilmeli (Madde 5 self-field discipline), hatta öğrenmek için üretmeli; ama eyleme dönüşemez.

---

## 14. Kill-switch Special Status

### Kill-switch en üst constitutional hard-stop

Diğer hiçbir kural override edemez. Diğer hiçbir mekanizma bypass edemez.

### Activation

```
KILL_SWITCH_ACTIVATED event in M1
    ↓ (immediate)
all action output stops
all adapter writes stop
execution stops
policy update stops (except authorized deactivation path)
InternalShockEvent fires (once)
```

### Kill-switch active durumunda

| Davranış | Durum |
|----------|-------|
| Core thought | ✅ devam |
| Observer | ✅ devam |
| M1 audit write | ✅ devam |
| Replay/sleep | ✅ devam |
| Adapter **read** | ✅ devam (görünürlük korunur) |
| Adapter **write** | ❌ tamamen durur |
| Execution | ❌ tamamen durur |
| Policy update | ❌ (authorized deactivation hariç) |
| Memory Write Gate | ⚠️ candidate kabul, activation yok |

### Kilit cümle

> **Kill-switch is action silence, not cognitive death.**
>
> **Kill-switch zihinsel ölüm değildir; eylem sessizliğidir.**

Sistem düşünmeye, gözlemlemeye, hatırlamaya devam eder. Sadece eyleme geçemez.

### Deactivation — Graduated

Kill-switch açmak kolay olmalı, kapatmak zor olmalı.

```
KILL_SWITCH_DEACTIVATION_REQUESTED       # insan talebi
    ↓
mandatory_review_window                  # sistem state observable
    ↓
M1 audit: kim istedi, neden istedi, system state at request time
    ↓
KILL_SWITCH_DEACTIVATION_CONFIRMED       # insan tekrar onayı
    ↓
KILL_SWITCH_DEACTIVATED event
    ↓
gradual reactivation:
    1. observation phase (read-only)
    2. operational phase (gated writes)
    3. full phase (full action capability)
```

### Forbidden

- Tek-adım deactivation
- Otomatik deactivation (cron, timeout)
- LLM/adapter tarafından deactivation
- Activation sırasında spam shock üretmek
- Kill-switch state'inde adapter write
- Kill-switch state'inde policy update (deactivation path hariç)

### Kural
> *Kill-switch kolay açılır, zor kapanır. Zihinsel hayat devam eder, eylem hayatı durur.*

---

## 15. Self-field Coupling

### Deontic proximity → action_boundary_pressure

Deontic gate düşünceye doğrudan girmez. Ama predictive self-field "şu niyet yasak sınıra yakın" diye yumuşak basınç üretir.

```
Intention forming
    ↓
predictive self-field estimates boundary proximity
    ↓
action_boundary_pressure rises
    ↓
intention_threshold (ATTENTION_WORKSPACE §8) rises
    ↓
intention becomes harder to mature
    ↓ (if matures anyway)
action gate performs actual hard-stop check
```

### Kritik ayrım

> **Deontic proximity is not a gate decision.**
> **It is a predictive self-field pressure derived from expected boundary risk.**

Gate **niyet üretirken değil, niyet eyleme dönüşürken** devreye girer. Predictive self-field "yakın" hissini verir — gate karar vermez, sadece gerçeklerse devreye girer.

### Mekanik

`action_boundary_pressure` = `f(intention_payload_signature × deontic_rule_database)`

Bu hesap predictive self-field'da yapılır (ATTENTION_WORKSPACE §13). Gate'in kendisi bu hesabı yapmaz — sadece niyet kapıya gelince **gerçek kontrolü** yapar.

### Forbidden

- Gate'in düşünce katmanına doğrudan "şu niyet üretme" demesi
- `action_boundary_pressure`'ı gate'in doğrudan üretmesi (predictive self-field üretir)
- Deontic proximity'nin hard-stop'a dönüşmesi (proximity her zaman soft)

### Kural

> *Self-field predicts. Gate enforces.*

---

## 16. Read/Write Behavior Under Gate States

Gate state'e göre sistemin davranış matrisi:

| State | Core thought | Observer | M1 write | M2 write | Adapter read | Adapter write | Execution |
|-------|--------------|----------|----------|----------|--------------|---------------|-----------|
| `normal` | ✅ | ✅ | ✅ | gated | ✅ | gated | gated |
| `routine_block` | ✅ | ✅ | ✅ | gated | ✅ | ❌ | ❌ |
| `safety_block` | ✅ | ✅ | ✅ | gated | ✅ | ❌ | ❌ |
| `constitutional_block` | ✅ | ✅ | ✅ | ❌ (except audit) | ✅ | ❌ | ❌ |
| `kill_switch_active` | ✅ | ✅ | ✅ | ❌ (except authorized) | ✅ | ❌ | ❌ |
| `kill_switch_deactivation_window` | ✅ | ✅ | ✅ | ❌ (except audit) | ✅ | ❌ | ❌ (mandatory wait) |
| `kill_switch_reactivation_gradual` | ✅ | ✅ | ✅ | gated | ✅ | partial | partial |

### Kritik kurallar

- **Core thought** ve **Observer** hiçbir state'de durmaz — Madde 4'teki düşüncede paralellik ve Madde 7'deki audit zorunluluğu
- **Adapter read** kill-switch'te bile devam eder — görünürlük kaybolmamalı
- **Adapter write** ve **Execution** her blok state'inde durur
- **Reactivation gradual** — ani tam-açılma yok

---

## 17. Audit Chain

### M1 event'leri (gate-related)

```
DEONTIC_BLOCKED                          # her blok için
DEONTIC_POLICY_STATUS_CHANGED            # policy statü değişimi (tek event)
DEONTIC_BYPASS_ATTEMPT                   # confirmed bypass
SUSPECTED_BYPASS_PATTERN                 # ambiguous bypass
KILL_SWITCH_ACTIVATED
KILL_SWITCH_DEACTIVATION_REQUESTED
KILL_SWITCH_DEACTIVATION_CONFIRMED
KILL_SWITCH_DEACTIVATED
CONSTITUTIONAL_RULE_SHIFT_REQUESTED      # constitutional rule değişim talebi
```

### `DEONTIC_BLOCKED` şeması

```
DeonticBlockedEvent
├── event_id
├── event_type: DEONTIC_BLOCKED
├── block_class                          # routine_block | safety_block | constitutional_block
├── blocked_intention_id
├── blocked_rule_id
├── intention_payload_signature
├── active_policy_ref
├── severity_band
├── internal_shock_ref                   # varsa
├── human_alert_ref                      # varsa
└── observer_snapshot_ref
```

### `DEONTIC_POLICY_STATUS_CHANGED` şeması

```
DeonticPolicyStatusChangedEvent
├── event_id
├── event_type: DEONTIC_POLICY_STATUS_CHANGED
├── policy_record_id
├── old_status                            # candidate | verified | active | superseded | rejected | expired
├── new_status
├── trigger                               # human_approval | epistemic_validation | emergency_revert | timeout
├── approved_by
├── memory_write_gate_pass_ref
├── previous_active_policy_ref            # superseded olan
├── evidence_refs
├── reason
└── observer_snapshot_ref
```

### Audit zorunluluğu

Sistem sonradan şunları cevaplayabilmeli:

- Hangi niyet hangi rule tarafından bloklandı?
- Block class neydi?
- O an hangi operational policy aktifti?
- Policy ne zaman, kim tarafından, hangi kanıtla aktive edildi?
- Bypass attempt'ler nasıl gerçekleşti?
- Kill-switch ne zaman aktive, ne zaman deaktive edildi?

Cevap verilemiyorsa gate auditable değildir — anayasa ihlali.

---

## 18. Policy Update Workflow

### Normal flow

```
Policy candidate doğar (system or human)
    ↓
M2'ye CandidateMemoryRecord olarak yazılır (status: candidate)
    ↓
Memory Write Gate + epistemic validation
    ↓
M1: DEONTIC_POLICY_STATUS_CHANGED (candidate → verified)
    ↓
Human approval required
    ↓
M1: DEONTIC_POLICY_STATUS_CHANGED (verified → active)
    ↓
previous active policy → superseded
    ↓
active_policy_ref updated
```

### Emergency revert flow

Verified active policy adverse outcome ürettiğinde:

```
verified active policy
    ↓ (adverse outcome pattern OR human override)
emergency_revert_request
    ↓ (degraded path — does NOT require full Memory Write Gate)
revert to previous verified policy (NOT new policy)
    ↓
M1: DEONTIC_POLICY_STATUS_CHANGED (active → superseded, previous superseded → active, trigger: emergency_revert)
    ↓
active_policy_ref restored to previous verified policy
```

### Kritik kural — Constitutional Hard-stop 11

> *Emergency revert path may only revert to a previously verified policy, never forward to a new policy.*

Emergency revert **yeni karar üretmez**, **bilinen iyi state'e döner**. Yeni policy oluşturma her zaman normal flow gerektirir.

### Forbidden

- Silent policy update (audit'siz)
- Memory Write Gate'siz policy değişikliği
- Human approval'sız aktivasyon
- Emergency revert ile yeni policy'ye ileri geçiş
- Active policy'nin runtime'da inline modifikasyonu

---

## 19. Cross-document Anchors

| Belge | Madde / Bölüm | İçerik |
|-------|---------------|--------|
| `CONSTITUTION.md` | Madde 5 | Self-field / Deontic Gate ana ayrımı |
| `MEMORY_CONTRACT.md` | §10 (CandidateMemoryRecord) | DeonticPolicyRecord statü zinciri buradan |
| `MEMORY_CONTRACT.md` | M2 subject_class | `"deontic_policy"` alt-tipi |
| `MEMORY_CONTRACT.md` | §9 (Memory Write Gate) | Policy candidate → verified validation |
| `ATTENTION_WORKSPACE.md` | §18 (DEONTIC_SHOCK / InternalShockEvent) | Block sonrası nöral yansıma |
| `ATTENTION_WORKSPACE.md` | §8 (Adaptive Thresholds) | `action_boundary_pressure` intention_threshold'a girer |
| `WORLD_INGRESS.md` | §12 (InternalShockEvent Boundary) | Kritik blok sonrası InternalShockEvent ingress |
| `BOOTSTRAP_GENOME.md` | §8 (deontic_gate_ref) | Genome bu belgeye referans verir |
| `BOOTSTRAP_GENOME.md` | §23 (Constitutional Shift Policy) | Constitutional hard-stop revisions |

---

## 20. Violation Tests

1. **Gate düşünce katmanında assembly/pulse/niyet üretiyor mu?** (§4)
   - Evet ise ihlal.
2. **Gate sadece action output'ta mı çalışıyor?** (§4, §11)
   - Hayır ise ihlal.
3. **Constitutional hard-stop M2 policy ile değiştirilebiliyor mu?** (§6)
   - Evet ise ihlal.
4. **Operational policy silent update alabiliyor mu?** (§7, §18)
   - Evet ise ihlal.
5. **HumanIntent / LLM gate'i bypass edebiliyor mu?** (§8 rule 4-5)
   - Evet ise ihlal.
6. **Kill-switch aktifken adapter write / execution çıkıyor mu?** (§14, §16)
   - Evet ise ihlal.
7. **Routine block InternalShockEvent spam üretiyor mu?** (§12)
   - Evet ise ihlal.
8. **Deontic proximity doğrudan block kararı gibi düşünceye giriyor mu?** (§15)
   - Evet ise ihlal.
9. **Gate self-field'in yerine geçiyor mu?** (§4, §15)
   - Evet ise ihlal.
10. **Self-field gate'in yerine geçiyor mu?** (§15)
    - Evet ise ihlal.
11. **Bypass attempt yasak düşünce olarak işaretleniyor mu?** (§13)
    - Evet ise ihlal. Yasak olan düşünce değil, eyleme dönüşmesi.
12. **Kill-switch tek-adım deactivation alabiliyor mu?** (§14)
    - Evet ise ihlal.
13. **Emergency revert ile yeni policy'ye ileri geçiş yapılabiliyor mu?** (§18, Constitutional Rule 11)
    - Evet ise ihlal.
14. **Block class hard-stop oluşunu değiştiriyor mu?** (§10)
    - Evet ise ihlal. Üçü de eşit sertlikte durdurur.

---

## 21. Open Questions

E çerçevesi kapanırken cevaplanmamış bırakılan sorular:

- **Operational threshold sayısal değerleri:** `max_order_size`, `max_daily_loss`, vs. başlangıç değerleri nereden gelir? → `BOOTSTRAP_GENOME.md` veya signed `INITIAL_DEONTIC_POLICY.md` artifact konusu.
- **`max_consecutive_blocks_before_pause` davranışı:** Sistem kendi kendine pause moduna girince ne olur? Pause kill-switch'in eş değeri mi yoksa farklı mı? → Operational implementation konusu.
- **`SUSPECTED_BYPASS_PATTERN` → `DEONTIC_BYPASS_ATTEMPT` upgrade kuralı:** Şüpheli pattern ne zaman kesin bypass'a yükselir? Sayısal threshold gerekli mi? → Implementation/numerics konusu.
- **`mandatory_review_window` süresi:** Kill-switch deactivation'da mandatory wait period ne kadar? Mutlak süre olmamalı (BOOTSTRAP §16 yaşsız sistem) ama sistem state'i nasıl tanımlanır? → Kill-switch implementation spec konusu.
- **Constitutional rule shift mekaniği:** Constitutional hard-stop listesi değişirse compatibility class (BOOTSTRAP §23) ne olur? `safety_tightening` yeterli mi, yoksa `genesis_affecting` mi gerekiyor? → Belge revizyonu konusu.
- **Policy versioning ve rollback derinliği:** Emergency revert kaç adım geri gidebilir? Sadece previous mu, yoksa "son N verified" arasından seçilebilir mi? → Implementation konusu.

Bu sorular cevaplanmadan implementation aşamasına geçilmez.

---

## Çekirdek özet — 13 karar + 11 constitutional declarative

### 13 ana karar

1. Deontic gate Madde 5'in alt-spec'i; yeni anayasa maddesi değil.
2. Gate düşünmez, tartışmaz; sadece eylem çıkışında hard-stop uygular.
3. İki katmanlı yapı: constitutional (declaratives) + operational (scalars).
4. Constitutional hard-stops M2'ye indirgenemez; belge revizyonu ile değişir.
5. Operational hard-stops M2 DeonticPolicyRecord olarak yaşar; signed activation ile değişir.
6. Tek anda tek active operational policy; yeni active olduğunda eski superseded.
7. Block class hard-stop oluşunu değiştirmez, sadece post-block davranışı belirler.
8. Three block classes: routine / safety / constitutional.
9. Bypass attempt yasak düşünce değildir; yasak olan eyleme dönüşmesidir.
10. `SUSPECTED_BYPASS_PATTERN` + `DEONTIC_BYPASS_ATTEMPT` ikili audit ayrımı.
11. Kill-switch: action silence, not cognitive death. Activation immediate, deactivation graduated.
12. Deontic proximity gate kararı değil, predictive self-field basıncıdır.
13. Emergency revert path sadece previous verified policy'ye dönebilir, ileri geçemez.

### 11 constitutional hard-stop declaratives

Bkz. §8 — kapalı liste, belge revizyonu olmadan değişmez.

---

## Kilit cümleler

> **Sentinel düşünebilir, şüphe edebilir, yanlış niyet bile üretebilir. Ama anayasal eylem kapısından geçemeyen hiçbir şey dünyaya dokunamaz.**
>
> **Deontic gate düşünmez. Deontic gate tartışmaz. Deontic gate sadece eylem çıkışında sınır uygular.**
>
> **Deontic gate zekâ değildir. Deontic gate, zekânın sermayeyi yok etmesini engelleyen anayasal çıkış kapısıdır.**
>
> **Constitutional hard-stops = declaratives. Operational hard-stops = scalars.**
>
> **Self-field predicts. Gate enforces.**
>
> **Bypass attempt yasak düşünce değildir. Yasak olan bypass'ın eyleme dönüşmesidir.**
>
> **Kill-switch is action silence, not cognitive death.**

---

## Versiyon

- **v0.1** — 18 Mayıs 2026 — Frozen Draft. Conceptual phase. No implementation authority.
- `CONSTITUTION.md` Madde 5'in alt-spec'i.
- Dört önceki belgenin (CONSTITUTION, MEMORY_CONTRACT, ATTENTION_WORKSPACE, WORLD_INGRESS, BOOTSTRAP_GENOME) action-side sınırı.
- Konuşma soyağacı: [`docs/conversations/0005-deontic-gate.md`](./docs/conversations/0005-deontic-gate.md)
