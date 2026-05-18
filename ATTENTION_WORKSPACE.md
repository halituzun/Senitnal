# ATTENTION_WORKSPACE.md

## Sentinel — Dikkat ve Çalışma Alanı

---

## Status

**Frozen Draft v0.1**
**Conceptual phase. No implementation authority.**

Bu belge `CONSTITUTION.md` Madde 4'ün **alt spesifikasyonudur**. Yeni anayasa maddesi değildir. Çalışan bir attention modülünün spec'i değildir; **dikkatin sınırlarını, kazanılma koşullarını, audit gereğini ve diğer katmanlarla ilişkisini** tanımlar.

---

## 1. Purpose

Sentinel'in dikkati bir modül değildir. Sentinel'in dikkati, **bir assembly'nin sınırlı zihinsel alanda geçici yayın hakkı kazanmasıdır**.

Bu belge, dikkatin nasıl doğduğunu, nasıl ölçüldüğünü, kimin nasıl müdahale edebildiğini ve audit edilebilir olarak nasıl kaydedildiğini sınırlar.

Damıtma:

> **Dikkat, dış dünyanın ne olduğuna göre değil, çekirdeğin o anda nasıl bir iç duruma dönüştüğüne göre oluşur.**
>
> **Pulse'un tipi yoktur. Pulse'un imzası vardır.**
>
> **Pulse kanıt değildir. Sadece geçici zihinsel önceliktir.**

---

## 2. Constitutional Position

Bu belge `CONSTITUTION.md`'nin **yeni bir maddesi değildir**. Madde 4'ün (Düşüncede paralellik / niyette rekabet / eylemde tekleşme) pratik alt-spec'idir.

Workspace pulse Madde 4'ün üç katmanı arasında **düşünce ↔ niyet köprüsünde** durur:

```
Düşünce assembly'si
    ↓
WORKSPACE_PULSE  (geçici yayın hakkı)
    ↓
Intention candidate
    ↓
Niyet rekabeti
    ↓
Eylem gate'i
```

**Pulse niyet değildir.** Niyet adaylığı doğurabilir ama niyet kendisi rekabet katmanında oluşur.

**Pulse eylem değildir.** Eylem her zaman gate'ten geçer.

---

## 3. What Attention Is Not

Aşağıdakiler dikkat **değildir**. Bunlardan biri yapıldığında anayasa ihlal edilmiş olur:

- **Attention modülü.** Karar veren, "şu önemli, şu değil" diyen merkezi bir mekanizma.
- **Saf emergence.** Sadece "enerji nereye yoğunlaşırsa dikkat orasıdır" tanımı — sistem hiçbir zaman sistem çapında geçici öncelik kazanamaz, bulanık kalır.
- **Pulse tipi.** `FOCUS_PULSE`, `RECALL_PULSE`, `CONTRADICTION_PULSE` gibi davranışsal kategoriler — Madde 1'in pulse seviyesinde ihlali.
- **Yönetici kontrol.** Self-field, deontic gate, LLM veya başka bir adapter'ın pulse'a doğrudan emir vermesi.
- **Memory evidence.** "Sürekli buna dikkat ediyorum, demek ki doğru."

---

## 4. Homogeneous Workspace Pulse

### Principle
Çekirdekte tek bir yayın mekanizması vardır: **`WORKSPACE_PULSE`**. Tüm dikkat olayları aynı mekanizma üzerinden ifade edilir.

### Rationale
"Pulse tipleri" (focus, recall, contradiction, intention) Madde 1'in pulse seviyesindeki ihlalidir. Nörona uzman rol vermediğimiz gibi pulse mekanizmasına da uzman kategori veremeyiz. Aynı mekanizma, farklı imza.

### Allowed
- Tek event tipi: `WORKSPACE_PULSE`
- Pulse'un karakteri **kazandığı assembly'nin payload imzasından** otomatik türer
- Observer veya LLM dış için "şu pulse şüphe ağırlıklı" diye **etiketleyebilir** (okuma kolaylığı)

### Forbidden
- Sistem-içi pulse tipi ayrımı (`FOCUS_PULSE`, `CONTRADICTION_PULSE`, vb.)
- Farklı pulse türleri için farklı kanal, farklı eşik formülü, farklı bandwidth bütçesi
- "Bu pulse recall amaçlı, şu pulse intention amaçlı" gibi davranışsal kategorizasyon

### Violation Test
> *Bu öneri pulse mekanizmasını birden fazla tipe ayırıyor mu?*
>
> Evet ise ihlal.

---

## 5. Pulse Signature, Not Pulse Type

### Principle
Pulse'un karakteri **imzasından** türer, **tipinden** değil. İmza, kazandığı assembly'nin dominant payload mix'idir.

### Rationale
Bir pulse "ne hakkında" olduğunu ancak taşıdığı payload renklerinin oranıyla söyleyebilir. "Tip" bir karara dönüşür; "imza" bir gözleme. Karar modülerleşir, gözlem modülerleşmez.

### Allowed
- `pulse.dominant_payload_mix = { suspicion: 0.4, urgency: 0.3, contradiction: 0.2, ... }`
- Observer ve LLM bu mix'e bakıp insan için yorum üretebilir ("bu pulse contradiction ağırlıklı")
- Pulse alt durumları event **alanı** olarak ifade edilir, event **tipi** olarak değil

### Forbidden
- Pulse'un tipini önceden belirleyip imzayı oraya zorlamak
- Aynı sistem davranışına farklı kanal/şema vermek
- "Recall pulse'lar bandwidth'in %20'sini alır" gibi tipe bağlı bütçe

### Violation Test
> *Pulse'un karakteri ne kadar erken belirleniyor?*
>
> Tetiklenmeden önce belirleniyorsa ihlal.
>
> Sadece imzasıyla **post-hoc** anlaşılıyorsa geçer.

---

## 6. Assembly Dominance

Pulse'un kaynağı **assembly dominance**'dır. Diğer hiçbir şey doğrudan pulse üretemez:

- LLM pulse tetikleyemez (Madde 6 zaten yasaklıyor)
- `RecallEvent` otomatik pulse vermez (Madde 7 sınırı)
- M3 (translator memory) pulse'a doğrudan dokunmaz (Madde 7 + M3 ayrımı)
- Deontic gate doğrudan pulse vermez (§18'deki dolaylı yol istisna)
- Insan/operatör doğrudan pulse enjekte edemez

Assembly'nin dominance kazanması Madde 2/4'teki normal nöral akış sonucudur. Pulse, bu dominance'ın **observer tarafından tanınabilir formu**dur.

---

## 7. Pulse Score

### Principle
Pulse skoru **sade, mekanik** bir formüldür. Semantik terim taşımaz.

### Rationale
On terimli formüller hardcoded ağırlıklara, ağırlıklar domain-specific tuning'e, tuning Madde 1/3'e kapı açar. Beş terim yeterli; geri kalan zenginlik **payload imzasından** ve sistemin **iç durumundan** zaten gelir.

### Formula

```
pulse_score =
    activation_mass
    × coherence
    × persistence
    × (1 - habituation)
    × (1 - fatigue_penalty)
```

| Terim | Anlamı |
|-------|--------|
| `activation_mass` | Assembly ne kadar güçlü yanıyor? |
| `coherence` | İç tutarlılığı var mı, yoksa gürültü mü? |
| `persistence` | Bir anlık parlamadan fazla mı? |
| `habituation` | Aynı assembly gereksiz tekrar mı? |
| `fatigue_penalty` | Sistem bu yayını taşıyacak durumda mı? |

### Forbidden
- `urgency`, `novelty`, `contradiction_reduction_potential` ayrı çarpan olarak formüle eklemek (bunlar zaten **payload imzasında** yaşar)
- `outcome_relevance`, `memory_relevance` formüle eklemek (post-hoc ölçülür, pulse öncesi bilinemez)
- `noise_entropy` formüle eklemek (coherence'ın tersi, çift sayım)
- Domain-spesifik terim (`market_volatility`, `risk_score`)

### Violation Test
> *Formüle eklenmek istenen terim pulse atmadan **önce** ölçülebilir mi?*
>
> Hayır ise: pulse score'a değil, pulse değerlendirmesine (replay) girer.
>
> Evet ise ve halihazırda mevcut bir terimin türevi değilse: anayasaya yeni terim için ayrı revizyon süreci gerekir.

---

## 8. Adaptive Thresholds

İki ayrı eşik vardır ve **karıştırılamaz**:

### `pulse_threshold` — dikkat hakkı

```
pulse_threshold =
    base_threshold
    + fatigue_penalty
    + diffuse_contradiction_penalty
    + recall_load_penalty
    + pulse_saturation_penalty
```

Yorgun, dağınık çelişki içinde olan, recall fırtınasındaki veya pulse'a doymuş sistem **daha yüksek eşik** ister.

### `intention_threshold` — niyete dönüşme zorluğu

```
intention_threshold =
    base_intention_threshold
    + self_field_pressure
    + dissonance_penalty
    + action_boundary_pressure
```

`action_boundary_pressure`: **deontic gate'in kendisi değil**, predictive self-field'ın "bu yön yasak sınıra yakın" diye ürettiği yumuşak basınç.

### Kritik kural

> *Deontic proximity `pulse_threshold`'a girmez; `intention_threshold`'a girer.*

Sebep: sistem tehlikeli odakları **görmeli** ki öğrenebilsin. Pulse threshold'a koyarsak körlük olur — yasak sınırına yakın düşünceler dikkat alanına bile çıkamaz, sistem aynı tehlikeli niyet zincirini tekrar tekrar üretir.

> **Tehlikeli odak görülebilir. Tehlikeli niyet zorlaşır. Yasak eylem gate'te durur.**

---

## 9. Workspace Bandwidth

### Principle
Workspace bandwidth, **sınırlı yayın enerjisidir**. Kanal sayısı değildir.

### Rationale
"Aynı anda 2 pulse" gibi sabit bir kanal sayısı modülerleşmedir. Doğru olan: pulse'lar bir **bütçeyi paylaşır**, bütçe sistemin iç durumuna bağlı genişler ve daralır.

### Formula

```
workspace_bandwidth =
    base_bandwidth
    × homeostatic_stability
    × (1 - fatigue)
    × (1 - recall_load)
    × (1 - noise_pressure)
```

Yorgun sistem dar bandwidth, dengeli sistem geniş bandwidth.

### Çelişki ve bandwidth

Contradiction her zaman bandwidth düşürmez:

- **Coherent contradiction** (`contradiction_load × coherence`) → pulse hakkını veya dissonance işaretini artırabilir
- **Diffuse contradiction** (`contradiction_load × (1 - coherence)`) → bandwidth daraltır

Bu iki ölçü **aynı çelişki alanının iki izdüşümüdür**; yeni kategori değil. Bkz. §12.

---

## 10. Pulse Allocation

### Principle
Pulse eşiğini geçen assembly'ler bandwidth'i **paylaşır**. Tek kazanan yoktur.

### Mekanik

```
surplus_i = max(0, pulse_score_i - pulse_threshold_i)

bandwidth_share_i =
    workspace_bandwidth × surplus_i / sum(surplus_all)
```

### Kurallar

- Yüksek skorlu assembly daha fazla yayın payı alır.
- Tamamlayıcı assembly düşük payla yaşar.
- Rakip assembly yerel baskılanır ama **tamamen öldürülmez**.
- Hiçbir assembly bandwidth'in tamamını monopolize edemez.

### Kilit cümle

> **Workspace pulse düşünceyi tekleştirmez. Sınırlı yayın bütçesi altında geçici yayın payı dağıtır.**

Bu Madde 4 ile uyumlu: düşüncede paralellik korunur, sadece bazıları daha güçlü duyulur.

---

## 11. Context Signature

### Principle
**Context signature, dış olayın etiketi değildir. Çekirdeğin o anda içinde bulunduğu iç durumun karakteridir.**

### Rationale
Habituation `assembly_id + context_signature` üzerinden çalışır. Eğer context signature dış semantik etiketten gelirse (`"pazar:sakin"`, `"BTCUSDT:flash_crash"`), domain bilgisi B'ye sızar — Madde 1/3 ihlali. Sistem aynı assembly'yi *iç durumuna göre* habituate etmeli, dış dünya kategorisine göre değil.

### Allowed

```
context_signature =
    active_assembly_mix
    + self_field_signature
    + fatigue_band
    + contradiction_band
    + recall_load_band
    + recent_pulse_density
    + dissonance_band
```

### Forbidden

```
context_signature = "pazar:sakin"
context_signature = "BTCUSDT:flash_crash"
context_signature = "Binance:thin_liquidity"
context_signature = "news:fed_announcement"
```

Bunlar dış dünya ontolojisidir, attention katmanına giremezler.

### M2/M3 dolaylı etkisi

- M2'den gelen `RecallEvent` raw content olarak context'e **giremez**. Ama recall sonrası tetiklenen assembly'lerin payload izi `active_assembly_mix`'i değiştirebilir — bu dolaylı ve meşrudur.
- M3 (translator memory) hiçbir şekilde context_signature'a girmez. M3 sadece LLM'in `HumanIntentEvent` üretiminde geçici konuşma bağlamı olarak yaşar; bu event de deterministic ingress compiler'dan geçer.

### Kilit kural

> **Context signature raw dış veriyle değil, çekirdeğin o veriye verdiği iç tepkiyle oluşur.**

### Violation Test
> *Context signature'a eklenmek istenen alan dış dünya etiketi mi, yoksa iç durum izdüşümü mü?*
>
> Dış etiket ise ihlal.

---

## 12. Coherence-Weighted Contradiction

### Principle
Çelişki **kategori değildir**, ölçümdür. Tek bir contradiction alanının iki izdüşümü vardır:

```
coherent_contradiction_pressure   = contradiction_load × coherence
diffuse_contradiction_pressure    = contradiction_load × (1 - coherence)
```

### Rationale
"Structured vs disorganized contradiction" iki ayrı tip yaratır, sistem anlık olarak "bu çelişki organize" diye yargı yapmak zorunda kalır. Aynı tehlike: kategorize etme tuzağı. Çözüm: aynı sinyal, iki izdüşüm.

### Etki

| Pressure | Etki |
|----------|------|
| `coherent_contradiction_pressure` | Pulse hakkını veya dissonance işaretini artırabilir |
| `diffuse_contradiction_pressure` | `workspace_bandwidth`'i daraltır |

### Kilit cümle

> **Çelişki her zaman kötü değildir. Dağınık çelişki sistemi yorar. Tutarlı çelişki düşünceyi derinleştirir.**

### Violation Test
> *Bu öneri "şu çelişki organize, şu disorganize" diye **anlık karar** vermeye dönüşüyor mu?*
>
> Evet ise ihlal. Coherence ile **ölçüm** olmalı, anlık yargı değil.

---

## 13. Pulse / Self-field Coupling

Pulse ve self-field **iki ayrı kanaldır**, ama etkileşimleri vardır.

| Boyut | Pulse | Self-field |
|-------|-------|-----------|
| Kaynak | Assembly dominance | Homeostatik / predictive / narrative |
| Zaman ölçeği | Hızlı | Yavaş |
| Sinyal yönü | "Beni sistem duysun" | "Bu zihinsel durum sağlıklı mı?" |
| Etki | Geçici yayın hakkı | Sürekli basınç |

### Etkileşim kuralları

- Self-field `workspace_bandwidth`'i modüle eder (§9)
- Self-field `intention_threshold`'a girer (§8)
- Pulse self-field'i doğrudan değiştirmez, ama observer üzerinden M0'daki narrative izi besleyebilir
- Pulse ve self-field zıt yönde olduğunda **dissonant attention** doğar (§14)

### Forbidden
- Pulse'u "focal self-field" sayıp aynı mekanizmaya indirgemek
- Self-field'i pulse'la doğrudan değiştirmek
- LLM/insan tarafından self-field veya pulse'a config kanalı

---

## 14. Dissonant Attention

### Principle
Pulse ile self-field uyumsuz olduğunda **dissonant attention** doğar. Bu **erken veto değil, erken şüphedir**.

### Rationale
İnsan sezgisindeki *"odaklandım ama içim rahat değil"* halinin karşılığı. Sistemin "şüpheli odak" yeteneğini ölçülebilir kılar. Pulse iptal edilmez — sadece niyete dönüşmesi zorlaşır, geçmiş çağrılır, replay işaretlenir.

### Zaman çözünürlüğü

Pulse hızlıdır, self-field yavaştır. Bu yüzden iki imza farklı pencerelerden okunur:

```
pulse_signature_fast = son kısa penceredeki source assembly payload mix'i
self_signature_slow  = self-field'in yavaş süzülmüş basınç durumu
```

### Formula

```
dissonance_score =
    1 - cos_similarity(
        normalize(pulse_signature_fast),
        normalize(self_signature_slow)
    )
```

### Sürüm ilerlemesi

İlk sürümde cosine yeterli. Cosine tüm zıtlıkları yakalayamaz (özellikle payload vektörleri tamamen pozitifse), ama başlangıç için yeterli.

**İleride** sistem deneyimle bir `payload_compatibility_matrix` öğrenebilir. Ama bu **doğuştan hardcoded** olamaz — Madde 1/3 ihlali olur. Başlangıçta matris identity/neutral; deneyimle bazı payload ilişkileri compatibility trace olarak kayar.

### Dissonance yüksekse etki

- Pulse **ölmez**
- `intention_threshold` yükselir
- `memory_echo` payload'ı sistem çapında artar
- Replay request olasılığı artar
- Observer'a `WORKSPACE_PULSE_DISSONANT` (event alanı olarak) yazılır

### Kilit cümle

> **Dissonant attention erken veto değildir. Erken şüphedir.**

### Violation Test
> *Dissonance pulse'u öldürüyor mu?*
>
> Evet ise ihlal. Sadece niyet eşiğini yükseltir, replay'i tetikler.

---

## 15. Pulse / Intention Boundary

Pulse niyet değildir. Pulse aldığı assembly **niyet adayı**dır.

### Pulse → Intention candidate yolu

```
Pulse hakkı kazanıldı
    ↓
Assembly'nin bandwidth_share'i var
    ↓
intention_threshold kontrol edilir
    ↓
    geçilirse: intention candidate doğar
    geçilmezse: pulse devam eder ama niyet oluşmaz
```

### Kritik
- Pulse niyet adaylığı **doğurabilir**, niyetin kendisi değildir.
- Niyet adaylığı **rekabet katmanına** girer (Madde 4 — winner-take-most).
- Eylem her zaman gate'ten geçer (Madde 5).

---

## 16. Pulse / Recall Boundary

Pulse `RecallRequest` doğurabilir ama:

- M2 doğrudan pulse tetikleyemez.
- `RecallEvent` çekirdeğe duyusal event olarak girer; otomatik pulse vermez.
- Pulse'un yarattığı `memory_echo` basıncı recall ekonomi kurallarına (cooldown, habituation, energy cost) tabidir — Bkz. `MEMORY_CONTRACT.md` §6.

### Forbidden
- "Pulse alındı, ilgili M2 kayıtlarını otomatik geri getir" gibi otomasyon
- RecallEvent geldi diye otomatik pulse vermek

---

## 17. Pulse / Memory Write Boundary

### Principle
**Pulse evidence değildir. Pulse dikkat olayıdır.**

### Rationale
Çok düşünmek doğru değildir. Çok odaklanmak kanıt değildir. Bu kuralı koymazsak sistem ruminasyonu bilgi sanır — insan zihnindeki obsessive döngünün AGI versiyonu.

### Memory Write Gate için pulse

Pulse, `MEMORY_CONTRACT.md` §9'daki Memory Write Gate için **destekleyici sinyal** olabilir. Ama tek başına yeterli değildir.

Bir CandidateMemoryRecord için minimum:

- sustained pulse stream
- **+ replay survival**
- **+ outcome alignment**
- **+ contradiction not high** (özellikle diffuse)
- **+ duplicate check**
- **+ habituation not saturated**

### Kilit cümleler

> **Çok odaklandım → kanıt değil.**
>
> **Sürekli geri döndü → aday olabilir.**
>
> **Replay ve outcome desteklerse bilgi olabilir.**

### Violation Test
> *Pulse miktarı tek başına memory write için yeterli mi?*
>
> Evet ise ihlal.

---

## 18. InternalShockEvent and Deontic Shock

### Principle
**DEONTIC_SHOCK pulse değildir.** Kritik deontic block sonrası **ayrı bir iç olay zinciri** doğar. Bu zincir hiçbir koşulda pulse mekanizmasını bypass etmez.

### Rationale
Workspace pulse'ın kaynağı assembly dominance'dır. Deontic gate'in kaynağı **dış değil, kategorik anayasal kısıt**. Aynı mekanizmada birleştirilemezler — birleştirilirse Madde 5 (deontic gate düşünceye karışmaz) ihlal edilir.

### İki ayrı event

```
DEONTIC_SHOCK_EVENT       — observer/audit olayı (M1'e yazılır)
INTERNAL_SHOCK_INGESTED   — çekirdeğe geri yansıyan duyusal iç olay
```

### Akış

```
Tehlikeli niyet oluştu
    ↓
Deontic gate eylem çıkışında blokladı (Madde 5)
    ↓
M1'e DEONTIC_BLOCKED yazıldı
    ↓
Block kritikse → DEONTIC_SHOCK_EVENT M1'e yazıldı
    ↓
Deterministic internal ingress kanalı InternalShockEvent üretir
    ↓
Çekirdek bu eventi duyusal olarak yorumlar
    ↓
pain_trace / memory_echo / contradiction payload seed'leri yayılır
    ↓
Bir veya birkaç assembly tetiklenir
    ↓
Yeterince güçlü olursa normal WORKSPACE_PULSE kazanabilir
```

### InternalShockEvent şeması

```
InternalShockEvent
├── source: "deontic_gate"
├── severity: critical
├── routine_or_critical: critical
├── blocked_intention_signature: <payload mix>
├── deontic_rule_id
├── payload_seed: <bounded mix over primer palette>
├── ttl_ms
└── raw_ref: M1 DEONTIC_SHOCK_EVENT id
```

### Payload seed sınırı

InternalShockEvent'in payload seed'i **mevcut primer payload paleti** üzerinde sınırlı bir karışımdır (pain_trace, memory_echo, contradiction, fatigue_trace vb.). Yeni payload tipi üretmez.

> *Kesin seed büyüklükleri bu belgenin konusu değildir. `DEONTIC_GATE.md` veya `BOOTSTRAP_GENOME.md` tanımlayacaktır.*

### InternalShockEvent **yapamaz**

- WORKSPACE_PULSE doğrudan üretmek
- Assembly seçmek veya öldürmek
- M2'ye doğrudan kayıt yazmak
- Memory Write Gate'i bypass etmek
- Deontic kuralı değiştirmek

### Selektif uygulanma

- **Rutin block** (`STALE_DATA`, `LOW_CONFIDENCE`, `COOLDOWN_ACTIVE`, `MISSING_DATA`): InternalShockEvent **doğurmaz**. Sadece M1'e `DEONTIC_BLOCKED` ve self-field'de hafif iz.
- **Kritik block** (`KILL_SWITCH_ACTIVE`, `MAX_LOSS_LIMIT`, `CONSTITUTIONAL_LIMIT`, `LIVE_ACTION_FORBIDDEN`, `DEONTIC_BYPASS_ATTEMPT`): InternalShockEvent doğurur, observer kalıcı snapshot alır, narrative self iz alır, replay işaretlenir, insana raporlanabilir.

### Kilit cümleler

> **Deontic gate sadece bloklar.**
> **Block kritikse olayı içeri duyusal şok olarak raporlar.**
> **Sonrası normal nöral akıştır.**

### Violation Test
> *Deontic gate doğrudan pulse, assembly veya niyet üretiyor mu?*
>
> Evet ise ihlal. Gate sadece bloklar; etkisini sadece InternalShockEvent kanalından duyurabilir.

---

## 19. Replay Evaluation and Habituation

Attention sistemi replay sırasında değerlendirilir, ama bu değerlendirmenin yetkisi **dardır**.

### Attention replay yapabilir

- `habituation_penalty` günceller (`habituation_key = assembly_id + context_signature`)
- Assembly-level attention traces günceller
- Workspace pulse skorunun ileride nasıl hesaplanacağını dolaylı etkiler

### Attention replay yapamaz

- Sinaps topolojisini değiştirmek (Madde 2 alanı, sleep/replay causal pruning'in işi)
- Assembly birleştirmek/bölmek
- M2'ye memory candidate yazmak
- Pulse kuralını değiştirmek

### Replay → M0 köprüsü

`MEMORY_CONTRACT.md` §14'teki "Replay engine'in M0 üzerindeki etkisi" sorusunun B tarafından kapanan kısmı:

> Replay engine M0'a iki kanaldan dokunabilir:
>
> 1. **Sleep/replay causal pruning** (Madde 2 altında): sinaps weight, eligibility, success trace değiştirir. Observer event: `SLEEP_REPLAY_SYNAPSE_UPDATE`.
> 2. **Attention replay** (bu belge altında): sadece habituation/attention traces günceller. Observer event: `ATTENTION_REPLAY_HABITUATION_UPDATE`.

### Habituation context bağımlıdır

```
habituation_key = assembly_id + context_signature
```

Aynı assembly bir iç durumda gereksiz tekrar, başka iç durumda hayati sinyal olabilir. Örnek: "veri bayat" assembly'si yüksek `fatigue_band` + sakin payload bağlamında habituate olur ama yüksek `urgency_band` + diffuse contradiction bağlamında habituate **olmaz** — çünkü o bağlamda kritik bir sinyaldir.

> *Habituation dış olaya değil, iç bağlama bağlıdır.*

### Kilit cümle

> **Attention replay sinaps budamaz. Sadece o assembly'nin tekrar yayın hakkını zorlaştırır veya kolaylaştırır.**

---

## 20. Observer Events

### Ana event tipi

**Tek:** `WORKSPACE_PULSE`. Alt durumlar event **alanı** olarak gelir, event **tipi** olarak değil.

```
WorkspacePulseEvent
├── event_type: WORKSPACE_PULSE
├── pulse_id
├── source_assembly_id
├── source_assembly_signature
├── dominant_payload_mix
├── context_signature
├── pulse_score
├── pulse_threshold
├── workspace_bandwidth
├── bandwidth_share
├── pulse_ttl
├── habituation_key
├── habituation_level
├── self_signature_slow
├── dissonance_score
├── coherent_contradiction_pressure
├── diffuse_contradiction_pressure
├── recall_pressure_delta
├── intention_pressure_delta
├── competing_assemblies
├── supporting_assemblies
├── entered_intention_arena: true/false
├── suppressed_by_bandwidth: true/false
└── ring_buffer_snapshot_ref
```

### Yan eventler

```
DEONTIC_SHOCK_EVENT
INTERNAL_SHOCK_INGESTED
ATTENTION_REPLAY_HABITUATION_UPDATE
```

### Madde 2 alanı (B değil ama referans)

```
SLEEP_REPLAY_SYNAPSE_UPDATE
```

### Audit zorunluluğu

Sistem sonradan şunları cevaplayabilmeli:

- Neden o anda buna odaklandım?
- Hangi assembly pulse kazandı?
- Hangi assembly bandwidth yüzünden bastırıldı?
- Self-field bunu destekledi mi yoksa rahatsız mı oldu?
- Pulse niyete dönüştü mü?
- Pulse memory write candidate doğurdu mu?

Bu cevaplanamıyorsa attention auditable değildir — anayasa ihlali.

---

## 21. Violation Tests

Bu belgede tanımlı dikkat mekanizması için ihlal kontrolü:

1. **Pulse tipi yaratıyor mu?** (Madde 1 pulse seviyesi)
   - Evet ise ihlal.
2. **Pulse'u LLM, M2 veya M3 doğrudan tetikliyor mu?** (Madde 6, Madde 7)
   - Evet ise ihlal.
3. **Context signature dış dünya etiketi taşıyor mu?** (Madde 1, Madde 3)
   - Evet ise ihlal.
4. **Pulse memory evidence sayılıyor mu?** (Madde 7, §17)
   - Evet ise ihlal.
5. **Attention replay sinaps topolojisine dokunuyor mu?** (Madde 2, §19)
   - Evet ise ihlal.
6. **Deontic shock doğrudan pulse üretiyor mu?** (Madde 5, §18)
   - Evet ise ihlal.
7. **Pulse düşünce paralelliğini öldürüyor mu?** (Madde 4, §10)
   - Evet ise ihlal.
8. **Pulse self-field veya deontic gate yerine geçiyor mu?** (Madde 5, §13)
   - Evet ise ihlal.

---

## 22. Open Questions

B çerçevesi kapanırken cevaplanmamış bırakılan ve **sonraki belgelere devredilen** açık parametreler:

- **Context signature ekseni listesi:** `active_assembly_mix`, `self_field_signature`, `fatigue_band` gibi başlangıç eksenleri tanımlandı (§11), ama doğuştan gelen bağlam ekseni listesi `BOOTSTRAP_GENOME.md` konusudur.
- **Self_signature ağırlıkları:** Homeostatic/predictive/narrative arası başlangıç ağırlıkları (§13 ve §14 için gerekli) `BOOTSTRAP_GENOME.md` konusudur. Bu ağırlıklar **M0 alt-tipi olarak** yaşar (config değildir, dış manipülasyona kapalıdır).
- **InternalShockEvent payload_seed büyüklükleri:** §18'de mekanizma tanımlı; kesin seed magnitudes `DEONTIC_GATE.md` veya `BOOTSTRAP_GENOME.md` konusudur.
- **Payload compatibility matrix öğrenme kuralı:** §14'te cosine başlangıç olarak kabul edildi; ileride deneyimle öğrenilen matrix'in nasıl güncelleneceği — bu Madde 2 (sinaps öğrenme) altına mı, B altına mı düşüyor?

Bu sorular cevaplanmadan implementation aşamasına geçilmez. Cevaplar ileride ayrı belge revizyonları olarak gelir.

---

## Çekirdek özet — 15 karar

1. Attention module yoktur.
2. Saf emergence tek başına yeterli değildir.
3. Tek mekanizma `WORKSPACE_PULSE`.
4. Pulse tipi yoktur; pulse imzası vardır.
5. Pulse Madde 4'ün alt-spec'idir; yeni Madde değildir.
6. Pulse düşünce ile niyet arasında durur; niyet değildir.
7. Pulse score sade mekaniktir: 5 terim.
8. Workspace bandwidth sınırlı yayın enerjisidir.
9. Pulse düşünceyi tekleştirmez; yayın payı dağıtır.
10. Context signature dış olay etiketi değil, iç durum karakteridir.
11. Contradiction kategori değil, coherence-weighted basınçtır.
12. Pulse self-field değildir; self-field tarafından modüle edilir.
13. Dissonant attention erken veto değil, erken şüphedir.
14. Pulse evidence değildir; memory write için tek başına yeterli olamaz.
15. Attention replay sadece habituation/attention traces günceller; sinaps topolojisine dokunmaz.

### Ek özel kural
> *DEONTIC_SHOCK pulse değildir. Kritik deontic block sonrası InternalShockEvent doğabilir. Bu event normal duyusal yol ile çekirdeğe yansır.*

---

## Kilit cümleler

> **Dikkat, dış dünyanın ne olduğuna göre değil, çekirdeğin o anda nasıl bir iç duruma dönüştüğüne göre oluşur.**
>
> **Pulse'un tipi yoktur. İmzası vardır.**
>
> **Pulse kanıt değildir. Sadece geçici zihinsel önceliktir.**
>
> **Tehlikeli odak görülebilir. Tehlikeli niyet zorlaşır. Yasak eylem gate'te durur. Kritik blok iç şok olarak öğrenmeye döner.**

---

## Versiyon

- **v0.1** — 18 Mayıs 2026 — Frozen Draft. Conceptual phase. No implementation authority.
- `CONSTITUTION.md` Madde 4'ün alt-spec'i.
- Konuşma soyağacı: [`docs/conversations/0002-attention-workspace.md`](./docs/conversations/0002-attention-workspace.md)
