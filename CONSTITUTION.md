# CONSTITUTION.md

## Sentinel — Çekirdek Anayasası

---

## Status

**Frozen Draft v0.1**
**Conceptual phase. No implementation authority.**

Bu belge bağlayıcı düşünce sınırıdır, henüz çalışan bir sistemin spesifikasyonu değildir. Kod, runtime davranışı ve API yüzeyleri bu belgeden değil, sonraki implementation belgelerinden türetilecektir. Bu belge sadece **neye izin yok, neye izin var, neyin hangi sınırda olduğunu** söyler.

> *Proje kodadı: Sentinel. Repo slug: Senitnal.*

---

## Giriş

Bu dosya Sentinel projesinin **değişmez kalbidir**. Bütün mimari kararlar, modüller, adaptörler ve adımlar bu yedi maddeye tabidir. Bir madde ile çelişen herhangi bir öneri — kim tarafından geldiğine bakılmaksızın (Halit, ChatGPT, Claude, Roo, herhangi bir LLM, gelecekteki bir mühendis) — reddedilir veya bu belge resmi olarak revize edilmek zorundadır.

Sentinel bir **trading bot değildir**. Sentinel, üzerine zamanla yetenekler (uzuvlar, adaptörler, dış dünya bağları) takılabilen bir **yapay zihinsel çekirdektir**. Çekirdek dış dünya yokken bile yaşar, düşünür, denge arar.

Borsa, Telegram, panel, emir motoru, strateji — bunların hiçbiri çekirdeğin parçası değildir. Hepsi sonradan **adaptör** olarak takılır.

Bu yüzden ilk uzun süre boyunca proje somut bir finansal sonuç üretmez. Bu beklenen bir durumdur, şikâyet konusu değildir; bu, projenin tasarımıdır.

---

## Madde formatı

Her madde aşağıdaki standart şablonda yazılır. Yeni öneriler bu şablonun "İhlal Testi" satırı ile sınanır.

- **Principle** — maddenin tek cümlelik özü
- **Rationale** — neden böyle, niye başka türlü değil
- **Allowed** — bu madde çerçevesinde yapılabilecekler
- **Forbidden** — bu madde çerçevesinde yapılamayacaklar
- **Violation Test** — "öneri bu maddeyi ihlal ediyor mu?" sorusunun mekanik cevaplanma kuralı

---

## Madde 1 — Nöron

### Principle
Tüm nöronlar aynı temel denklemle çalışır. Fark sadece **semantic payload** ve **target-side receptor** yorumlamasındadır.

### Rationale
"Risk nöronu", "fırsat nöronu", "karar nöronu" gibi uzman tipler modülerleşmeyi geri getirir. Anlamı nörona kazımak değil, **nöronlar arası akış desenine** bırakmak gerekir. Aynı tip nöron, farklı renkler, hedefin yorumu — bu insan beynindeki nörotransmitter analojisine de uyar (dopamin/serotonin/GABA aynı nöron iskeleti üzerinde farklı çağrışım yaratır).

### Allowed
- Primer payload paleti: `suspicion`, `novelty`, `aversion`, `attraction`, `contradiction`, `urgency`, `memory_echo`, `fatigue_trace`, `pain_trace`, `reward_trace`
- Sistem zamanla bu primer renklerden **kombine payload** türetebilir (`suspicion + urgency → panic-like`, `novelty + attraction → curiosity-like`)
- Default receptor profilleri (deneyimle kayan)
- Aynı payload'ı farklı target nöronlarda farklı yorumlamak

### Forbidden
- Uzman nöron tipi yaratmak (`risk_assessment_neuron`, `BTC_volatility_neuron`)
- Payload yerine **iş kategorisi** taşıyan nöronlar (`buy`, `sell`, `stoploss`)
- "Bu nöron suspicion uzmanıdır, sadece ona bakar" gibi rol kısıtı
- Nöron seviyesinde domain-specific etiket

### Violation Test
> *Bu öneri belirli bir nörona belirli bir "iş" veya "domain rolü" yüklüyor mu?*
>
> Evet ise ihlal. Hayır ise (sadece zihinsel renk taşıyorsa) geçer.

---

## Madde 2 — Sinaps

### Principle
Sinaps anlam taşımaz; **akış deseninin hafızasını** taşır. Anlam sinapsta değil, sinapslarla örülen devrede doğar.

### Rationale
Sinaps "renkli kanal" olursa kombinatorik patlama olur (her nöron çifti × her payload = milyonlarca kanal). Ayrıca payload'ı sinapsa kazımak yine modülerleşmenin gizli kapısıdır. Sinaps sadece **hangi akışların yaşamaya değer olduğunu** öğrenir.

### Allowed
- Sinaps şu alanları taşır: `weight`, `polarity`, `delay_ms`, `reliability`, `fatigue`, `fast_eligibility`, `medium_eligibility`, `slow_eligibility`, `fast_success_trace`, `medium_success_trace`, `slow_success_trace`, `last_pre_fire_at`, `last_post_fire_at`, `cofire_count`, `age`, `plasticity_rate`
- Öğrenme kuralı: `Δw = stdp_delta × outcome_signal_vector × confidence × plasticity_rate − decay_penalty`
- Üç ölçekli paralel eligibility (fast/medium/slow)
- Sleep/replay tabanlı causal pruning
- Lokal komşuluk doğumu + co-firing doğumu (long-range shortcut)
- Üç aşamalı ölüm: decay → dormant → pruned (observer snapshot sonrası)

### Forbidden
- Sinapsa semantic etiket koymak (`this is a suspicion synapse`)
- Saf Hebbian — outcome'suz "beraber ateşleyenler bağlanır"
- Outcome olmadan ağırlık güncellemesi
- Sleep/replay olmadan canlı STDP (correlation/causation karışır)
- Outcome'u skaler tek sayı olarak modellemek (vektör zorunlu)

### Violation Test
> *Bu öneri sinapsın kendisine bir kategori/etiket/yorum ekliyor mu?*
>
> Evet ise ihlal. Hayır ise (sinaps hâlâ saf yol, anlam hedefte yorumlanıyorsa) geçer.

---

## Madde 3 — Doğuş / Minimum Genome

### Principle
Sentinel **embriyo** olarak doğar — sıfırdan değil, modülden değil. Doğuştan minimum genome ile başlar; deneyimle düşünür.

### Rationale
Saf sıfırdan başlamak (tam tabula rasa) pratikte ölü doğmaktır — yıllarca hiçbir şey öğrenemez. Tam kişilikle başlamak (hardcoded davranış ağaçları, hazır strateji) modülerleşmenin geri kapısıdır. Evrim de bu dengeyi seçmiştir: bebek hiçbir şey bilmez ama acı izinden kaçmayı, novelty'ye dikkat etmeyi doğuştan yapar.

### Allowed (doğuştan gelen)
- Her primer payload için birkaç düzine seed nöron
- Zayıf lokal bağlantılar
- Default receptor profilleri (deneyimle kayan)
- Homeostatik referans noktası
- Basit kaçınma/yaklaşma refleksleri
- Uyku/replay ritmi
- Üç katmanlı self-field embriyosu (homeostatic güçlü, predictive zayıf, narrative kuruluş izi)
- `genesis_trace` — sistemin "doğum anı" kaydı (M1'e sabit, silinemez)
- Anayasal kısıt listesi (deontic gate kuralları)

### Forbidden (doğuştan gelmeyen)
- Hazır strateji ağaçları
- Default risk profili (sayısal hardcoded eşikler)
- Doğduğunda bilinen finansal kavram
- Domain-specific seed assembly
- Önceden öğrenilmiş ilişkiler
- Kullanıcı kimliği
- Trade/buy/sell/borsa bilgisi

### Kilit formül
> **Doku doğuştan. Düşünce deneyimden.**

### Violation Test
> *Bu öneri sisteme doğuştan bir "iş bilgisi" veya "domain kavramı" yüklüyor mu?*
>
> Evet ise ihlal. Sadece refleks/genom seviyesinde bir mekanik yüklüyorsa geçer.

### Alt-spec referansı
Initial state şeması, developmental rules, genome immutability, constitutional shift policy ve birth_mode için bkz. [`BOOTSTRAP_GENOME.md`](./BOOTSTRAP_GENOME.md) — Madde 3'ün alt-spec'i, yeni anayasa maddesi değildir.

---

## Madde 4 — Akış / Paralellik–Rekabet–Teklik

### Principle
Düşüncede paralellik. Niyette rekabet. Eylemde tekleşme.

### Rationale
Sistem aynı olay için **birden fazla yorum** aynı anda taşıyabilmeli (epistemic genişlik). Ama aynı eylem kanalına bağlanmak isteyen iki zıt niyet çatıştığında **biri kazanmalı**; yoksa felç olur. Eyleme bir kez varıldığında **tek karar** çıkar; yarım eylem, paralel eylem yoktur.

### Allowed
- **Düşünce katmanı:** çok yorum, çok hipotez paralel yaşar. Sistem aynı olay için "tehlikeli" ve "fırsat" assembly'lerini geçici olarak birlikte taşıyabilir.
- **Niyet katmanı:** yerel rekabet, **winner-take-most** (galip baskın olur, kaybeden tamamen ölmez)
- Aynı temsil alanı + zıt eylem eğilimi → rekabet
- Farklı bağlam + tamamlayıcı açıklama + farklı zaman ölçeği → paralel kalır
- Çelişki yükselince aksiyon ertelenir, ek veri/replay çağrılır
- İki assembly daha üst bir assembly'de **birleşebilir** (sentez)

### Forbidden
- Düşünce katmanında "tek yorum dayatma" (premature collapse)
- Niyet katmanında saf winner-take-all (kaybedeni tamamen yok eden)
- Eylem katmanında paralel/yarım eylem
- Çelişki yüksekken zorla karar üretmek
- Aynı eylem kanalına iki zıt niyetin birlikte gitmesi

### Violation Test
> *Bu öneri hangi katmanda çalışıyor?*
>
> - Düşünce katmanında paralelliği daraltıyorsa ihlal.
> - Niyet katmanında rekabeti atlıyorsa veya saf winner-take-all yapıyorsa ihlal.
> - Eylem katmanında tekleşmeyi bozuyorsa ihlal.

### Alt-spec referansı
Düşünce ↔ niyet köprüsündeki yayın hakkı (workspace pulse, dikkat, audit) için bkz. [`ATTENTION_WORKSPACE.md`](./ATTENTION_WORKSPACE.md) — Madde 4'ün alt-spec'i, yeni anayasa maddesi değildir.

---

## Madde 5 — Self-field & Deontic Gate

### Principle
Sistemde iki tür koruma vardır: **self-field soft pressure** ve **deontic gate hard stop**. İkisi farklı katmandır, birinin yerine diğeri konulamaz.

### Rationale
Saf "soft pressure" %95 senaryoda yeterli ama catastrophic anlarda (flash crash, panic assembly) urgency payload yükseltilmiş eşiği bile aşar. Kalan %5 hesabı sıfırlayabilir. Bu yüzden basıncın altında müzakere edilemez kategorik bir sigorta gerekir. Tersine: deontic gate her şeyi yasaklarsa sistem düşünemez, sadece refleks olur. İkisi farklı görev için.

### Allowed — Self-field (basınç)
- Üç alt katman: **homeostatik öz** (anlık), **predictive self-model** (kendi tepkimi tahmin), **narrative self** (kimlik tortusu)
- Niyet enerjisini düşürme, eşik yükseltme, decay hızlandırma
- Olasılıksal — aşılabilir
- Deneyimle değişir
- Sürekli aktif

### Allowed — Deontic gate (sınır)
- Doğuştan gelen, kategorik kısıtlar listesi
- Sadece **eylem çıkışında** durur, düşünceye karışmaz
- Geçtiği niyetler eyleme dönüşür
- Geçemediği niyetler observer'a `DEONTIC_BLOCKED` olarak yazılır ve narrative self'e iz bırakır
- Örnek kurallar: max emir büyüklüğü, kayıp eşiği, kill-switch durumu, veri tazeliği

### Forbidden
- Deontic gate'in runtime'da değişmesi
- Self-field'in "hayır" diyebilmesi (basınçtır, yasak değil)
- Deontic gate'in düşünce katmanına müdahale etmesi
- LLM veya başka bir adapter'ın deontic gate'i bypass etmesi
- "Soft pressure yeter" diyerek deontic gate'i kaldırmak
- "Sadece deontic gate yeter" diyerek self-field'i kaldırmak

### Kilit fark

| Self-field | Deontic gate |
|-----------|---------------|
| Olasılıksal | Kategorik |
| Aşılabilir | Geçilmez |
| Sürekli aktif | Sadece eylem kapısında |
| Düşünceyi etkiler | Düşünceye karışmaz |
| Deneyimle değişir | Anayasal — runtime'da değiştirilemez |

### Koruma
Deontic gate kurallarına eklenecek/çıkarılacak her madde, bu `CONSTITUTION.md`'deki gibi ayrı bir resmi belge revizyonu gerektirir. Bypass girişimi `DEONTIC_BYPASS_ATTEMPT` olarak observer'a yazılır ve insana derhal raporlanır.

### Violation Test
> *Bu öneri bir engellemeyi sert (kategorik) yapıyorsa: deontic gate'te mi tanımlı?*
>
> *Bu öneri bir engellemeyi yumuşak (olasılıksal) yapıyorsa: self-field'de mi?*
>
> İkisini karıştırıyorsa veya hangisinde olduğu belirsizse ihlal.

### Alt-spec referansı
Deontic gate'in constitutional vs operational hard-stop ayrımı, 11 anayasal declarative, block classification, bypass attempt handling, kill-switch protokolü ve operational policy update workflow için bkz. [`DEONTIC_GATE.md`](./DEONTIC_GATE.md) — Madde 5'in alt-spec'i, yeni anayasa maddesi değildir.

---

## Madde 6 — LLM Boundary

### Principle
LLM çekirdeğin **dış tercümanıdır**; nöron, sinaps, assembly veya niyetin parçası değildir. Çekirdek hafıza silinmeden LLM değiştirilebilir; LLM hafıza silinse bile çekirdek değişmez.

### Rationale
LLM halüsinasyona açıktır ve karar dokusuna karışırsa hesap verebilirliği yok eder. Aynı zamanda LLM'in dil zekâsı çok değerli — onu tamamen dışlamak da israftır. Çözüm: LLM dışarıda, **deterministic ingress compiler** üzerinden çekirdeğe yapısal niyet sunar. Çekirdek niyetin payload'a nasıl çevrileceğini LLM'in tahmininden değil, kendi sabit kuralından alır.

### Allowed
- İnsan dilini yapısal `HumanIntentEvent`'a çevirmek
- Observer ledger'ı insan diline açıklamak
- Belirsizlikleri işaretlemek (`ambiguity_score`)
- Replay/analiz önerileri sunmak
- Halit'in konuşma tarzını M3'te tutmak
- Sandbox/replay laboratory'de "LLM nöron tipi" denemeleri (sadece offline, hiçbir live action yok, sonuçlar "hipotez" olarak işaretli)

### Forbidden
- Sinaps weight yazmak
- Nöron charge enjekte etmek
- Assembly doğrudan oluşturmak
- Outcome sinyali üretmek
- Deontic gate'i bypass etmek
- Execution adapter'a doğrudan emir göndermek
- Çekirdeğin narrative self'ini değiştirmek
- M0, M1 veya M2'ye doğrudan yazmak

### Akış

```
İnsan metni
    ↓
LLM tercüman (yapısal niyet parse eder)
    ↓
HumanIntentEvent { intent, confidence, ambiguity, ttl }
    ↓
Deterministic Ingress Compiler   ← çekirdeğin sabit kuralları
    ↓
Çekirdeğe sınırlı duyusal event
    ↓
Çekirdek niyet üretirse
    ↓
Deontic Gate
    ↓
Adapter / Eylem
```

### TranslatorArtifact

LLM'in ürettiği her yapısal niyet aşağıdaki alanlarla gelir ve **geçici statüde** tutulur:

```
TranslatorArtifact
├── source: "llm_translator"
├── model_id
├── prompt_hash
├── confidence
├── ambiguity_score
├── hallucination_risk_score
├── proposed_structured_event
├── requires_human_confirmation
├── ttl_ms
└── raw_output_ref
```

LLM yorumu **kalıcı inanç değildir**. Observer kaydı kalıcıdır.

### Kilit kural
> **LLM konuşur. Çekirdek düşünür. Deontic gate sınır çizer. Observer kanıtlar.**

### Violation Test
> *Bu öneri LLM çıktısına çekirdek seviyesinde otomatik güven veriyor mu?*
>
> *LLM değişirse çekirdeğin kimliği değişir mi?*
>
> Birine "evet" ise ihlal.

### Alt-spec referansı
`HumanIntentEvent`'in çekirdeğe ingress sınırı için bkz. [`WORLD_INGRESS.md`](./WORLD_INGRESS.md) §11.

---

## Madde 7 — Hafıza Sınırı

### Principle
Sistemin hafızası dört ayrı katmandan oluşur (M0, M1, M2, M3) ve hiçbiri diğerinin yerine geçemez. **Hafıza çekirdeğe emir vermez. Hafıza çekirdeğe hatırlatma gönderir.**

### Rationale
Tek tip hafıza modeli iki uçtan birine düşer: ya her şey sinapsta yaşar (audit imkânsız), ya her şey explicit tabloda yaşar (modüler bota geri dönüş). Dört katman: çekirdeğin gerçek dokusu (M0), tarihinin kanıtı (M1), dış bilgi organı (M2), konuşma kabuğu (M3). Her birinin yazıcısı, okuyucusu, silinme kuralı, kimlik etkisi farklıdır.

### Allowed

| Katman | Ad | Ne saklar | Silinirse |
|--------|-----|-----------|------------|
| M0 | Implicit Neural Memory | Sinaps ağırlıkları, assembly stabilitesi, narrative tortusu | Kimlik kaybı, yeni doğum |
| M1 | Observer Ledger | Append-only kanıt defteri | Tarih kaybı (yapılmaz) |
| M2 | Explicit Recall Store | Episodic kayıtlar, structured facts, procedural tablolar | Bilgi kaybı, kimlik korunur |
| M3 | Translator Memory | LLM konuşma bağlamı | Konuşma tarzı kaybı |

- M2'den gelen her şey çekirdeğe **`RecallEvent` duyusal eventi** olarak girer ve diğer duyusal eventler gibi yorumlanır
- M3 çekirdeğe doğrudan girmez; yalnızca LLM translator'ın `HumanIntentEvent` üretiminde geçici konuşma bağlamı olarak kullanılır (bu event de Madde 6'daki Deterministic Ingress Compiler'dan geçer)
- Çekirdeğin M2'ye yazma niyeti **Memory Write Gate**'e tabidir (deontic gate **değildir** — bkz. ayrım)
- M0 sadece sistemin kendi öğrenme kuralları üzerinden değişir
- M1 append-only, coarse-grain log silinmez

### Forbidden
- M2'nin doğrudan nöron charge, sinaps weight veya assembly membership yazması
- Dış hafıza adapter'ının çekirdeğe "emir" olarak görünmesi
- M0'a herhangi bir dış yazıcı (insan, LLM, adapter)
- M1'in coarse-grain log'unun silinmesi
- Çekirdeğin kendi M2 kayıtlarını doğrudan, gate'siz yazması (self-deception riski)

### Detay
Tam spec: [`MEMORY_CONTRACT.md`](./MEMORY_CONTRACT.md). M2'den `RecallEvent` ingress sınırı için bkz. [`WORLD_INGRESS.md`](./WORLD_INGRESS.md) §10.

### Violation Test
> *Bu öneri herhangi bir hafıza katmanını başka bir katmana doğrudan emir verir hale getiriyor mu?*
>
> *Bu öneri M0'a dış yazıcı koyuyor mu?*
>
> Birine "evet" ise ihlal.

---

## Çekirdek özet — yedi cümle

1. **Nöron renk taşır.**
2. **Sinaps yol hafızası taşır.**
3. **Assembly anlam taşır.**
4. **Self-field basınç yapar.**
5. **Deontic gate sınır çizer.**
6. **Observer kanıtlar.**
7. **LLM tercüme eder.**

---

## İhlal kontrolü prosedürü

Yeni bir özellik, mimari kararı veya kod parçası önerildiğinde:

1. Bu yedi maddenin her birine sırayla bakılır.
2. Her maddenin **Violation Test** satırı uygulanır.
3. İhlal varsa: ya öneri reddedilir, ya da maddeye **resmi revizyon süreci** açılır.
4. Revizyon süreci: tartışma → gerekçe → yeni metin → versiyon artırımı → tarih notu → eski versiyon arşive.

Anayasa, dokunulmaz olduğu için değil, **dokunulmazlığı korumak için ciddiye alındığı** için çalışır.

---

## Versiyon

- **v0.1** — 18 Mayıs 2026 — Frozen Draft. Conceptual phase. No implementation authority.
- Konuşma soyağacı: [`docs/conversations/`](./docs/conversations/)

---

## Lisans notu

Bu belge Apache 2.0 lisansı altında dağıtılır. Ama belgenin **içeriği** runtime'da müzakere edilebilir değildir — sadece resmi revizyon süreciyle değişir.
