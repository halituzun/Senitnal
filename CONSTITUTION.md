# CONSTITUTION.md

## Sentinel — Çekirdek Anayasası

Bu dosya Sentinel projesinin **değişmez kalbidir**. Bütün mimari kararlar, modüller, adaptörler ve adımlar bu yedi maddeye tabidir. Bir madde ile çelişen herhangi bir öneri — kim tarafından geldiğine bakılmaksızın (Halit, ChatGPT, Claude, Roo, herhangi bir LLM, gelecekteki bir mühendis) — reddedilir veya bu belge resmi olarak revize edilmek zorundadır.

Bu yedi madde uzun bir tasarım tartışmasının damıtılmış halidir. Kısa görünmelerinin nedeni, altlarında uzun bir gerekçe ağı yatmasıdır.

---

## Başlangıç ilkesi

Sentinel bir **trading bot değildir**. Sentinel, üzerine zamanla yetenekler (uzuvlar, adaptörler, dış dünya bağları) takılabilen bir **yapay zihinsel çekirdektir**. Çekirdek dış dünya yokken bile yaşar, düşünür, denge arar.

Borsa, Telegram, panel, emir motoru, strateji — bunların hiçbiri çekirdeğin parçası değildir. Hepsi sonradan **adaptör** olarak takılır.

Bu yüzden ilk uzun süre boyunca proje somut bir finansal sonuç üretmez. Bu beklenen bir durumdur, şikâyet konusu değildir; bu, projenin tasarımıdır.

---

## Madde 1 — Nöron homojen denklem, heterojen payload, target-side yorumlama

Tüm nöronlar **aynı temel denklemle** çalışır. "Risk nöronu", "fırsat nöronu", "karar nöronu" gibi uzman nöron tipleri yoktur ve hiçbir zaman olmayacaktır.

Nöronlar arasında tek fark **semantic payload**'larıdır — taşıdıkları zihinsel renk:

- `suspicion` (şüphe)
- `novelty` (yenilik)
- `aversion` (kaçınma)
- `attraction` (yaklaşma)
- `contradiction` (çelişki)
- `urgency` (aciliyet)
- `memory_echo` (hafıza yankısı)
- `fatigue_trace` (yorgunluk izi)
- `pain_trace` (acı izi)
- `reward_trace` (ödül izi)

Bunlar primer paletidir. Sistem zamanla bu primer renklerden kombine payload'lar türetebilir (`suspicion + urgency → panic-like`, `novelty + attraction → curiosity-like`).

Bir nöron ateşlediğinde, payload'ı sinaps üzerinden hedef nörona ulaşır. Hedef nöron bu payload'ı **kendi receptor profiline** göre yorumlar. Aynı sinyal farklı target nöronlarda farklı etkiler yaratır.

### Yasak ihlal örnekleri

- `risk_assessment_neuron` diye uzman nöron yaratmak
- `BTC_volatility_neuron` gibi domain-specific nöron tipleri
- Payload yerine doğrudan kategori (`buy`, `sell`, `stoploss`) taşıyan nöronlar
- "Bu nöron suspicion uzmanıdır, sadece suspicion sinyallerine bakar" gibi rol kısıtlaması

### Koruma

Yeni payload tipi eklenmek istendiğinde sorulacak soru:

> *Bu iş görevi mi yoksa zihinsel renk mi?*

İş görevi (`buy`, `trade`) reddedilir. İlkel zihinsel ton (`urgency`, `aversion`) kabul edilir.

---

## Madde 2 — Sinaps anlam taşımaz, akış deseninin hafızasını taşır

Sinaps bir veri yolu **değildir**, ama renkli kanal da değildir. Sinaps, iki nöron arasındaki **nedensel ilişkinin tarihini taşıyan** bir hafıza birimidir.

### Sinaps taşır

- `weight` — bağlantının gücü
- `polarity` — uyarıcı/baskılayıcı
- `delay_ms` — iletim gecikmesi
- `reliability` — iletim güvenilirliği
- `fatigue` — sinaps yorgunluğu
- `fast_eligibility`, `medium_eligibility`, `slow_eligibility` — üç ölçekli iz
- `fast_success_trace`, `medium_success_trace`, `slow_success_trace` — outcome ile öğrenme izi
- `last_pre_fire_at`, `last_post_fire_at` — zaman izleri
- `cofire_count` — birlikte ateşleme sayısı
- `age` — yaş
- `plasticity_rate` — değişebilirlik oranı

### Sinaps taşımaz

- Semantic payload
- Domain-specific etiket
- `risk_channel`, `urgency_channel` tipi kategori

### Öğrenme kuralı

```
Δw = stdp_delta(pre_time, post_time)
    × outcome_signal_vector
    × confidence
    × plasticity_rate
    − decay_penalty
```

**Üç bileşen birlikte gerekir:**

- **STDP** (Spike-Timing-Dependent Plasticity) — zamansal nedensellik
- **Outcome-gated learning** — sonuç kalitesi (vektör, tek sayı değil)
- **Eligibility trace** — gecikmeli atfedilme, üç zaman ölçeğinde paralel

### Sinaps doğumu

Şu koşullar birleşince doğar:

- Lokal komşuluk içinde, VEYA
- Tekrarlanan nedensel co-firing + faydalı outcome + düşük redundancy + mevcut kapasite

### Sinaps ölümü

Üç aşamalı:

1. **Decay** — ağırlık yavaş yavaş azalır
2. **Dormant** — bağ var ama aktif iletimde kullanılmaz
3. **Pruned** — observer snapshot aldıktan sonra silinir

### Yasak ihlal örnekleri

- Sinapsa semantic etiket koymak (`this is a suspicion synapse`)
- Saf Hebbian — sadece "beraber ateşleyenler bağlanır", outcome yok
- Outcome olmadan ağırlık güncellemesi
- Sleep/replay olmadan canlı STDP — correlation/causation karışır

### Koruma

Her ağırlık güncellemesi observer ledger'a sebep + outcome ile yazılır. Sebebi olmayan güncelleme reddedilir.

---

## Madde 3 — Doğuş minimum genome ile başlar — sıfır değil, modül de değil

Sentinel ne sıfırdan başlar (bütün hafıza/bağ deneyimle doğacak — pratikte ölü doğmak), ne tam kişilikle başlar (hardcoded modüller — kaçtığımız şey).

### Doğuştan gelen

- Her primer payload için birkaç düzine seed nöron
- Zayıf lokal bağlantılar
- Default receptor profilleri (deneyimle kayan)
- Homeostatik referans noktası
- Basit kaçınma/yaklaşma refleksleri
- Uyku/replay ritmi
- Üç katmanlı self-field embriyosu (homeostatic güçlü, predictive zayıf, narrative kuruluş izi)
- Genesis trace — sistemin "doğum anı" kaydı
- Anayasal kısıt listesi (deontic gate kuralları)

### Doğuştan gelmeyen

- Fikir
- Strateji
- Karar
- Trade
- Buy/sell
- Borsa bilgisi
- Herhangi bir domain-specific kavram
- Kullanıcı kimliği
- Önceden öğrenilmiş ilişkiler

### Kilit formül

> **Doku doğuştan. Düşünce deneyimden.**

### Yasak ihlal örnekleri

- Bootstrap'ta hazır strategy tree
- "Default risk profile" diye sabit sayısal kurallar
- Sistem doğduğunda bilen finansal kavramlar
- Domain-specific seed assembly'ler

---

## Madde 4 — Düşüncede paralellik, niyette rekabet, eylemde tekleşme

Üç katman, üç farklı kural:

### Düşünce katmanı (assembly seviyesi)

Aynı anda birçok yorum, ihtimal, açıklama **paralel yaşar**. Sistem aynı olay için "tehlikeli" ve "fırsat" assembly'lerini geçici olarak birlikte taşıyabilir. Bu sağlıklıdır — erken aşamada hangisinin doğru olduğunu bilemeyiz.

### Niyet katmanı

Aynı eylem kanalına bağlanmak isteyen niyetler arasında **yerel rekabet** başlar.

- **Winner-take-most** uygulanır (winner-take-all değil)
- Galip baskın olur, kaybeden tamamen ölmez
- Yarış sadece **aynı temsil alanı + zıt eylem eğilimi** durumunda olur
- Farklı bağlam + tamamlayıcı açıklama + farklı zaman ölçeği → paralel kalır

### Eylem katmanı

Yalnızca bir niyet eyleme dönüşür. **Tekleşme zorunludur, paralel eylem yoktur.**

### Çelişki yönetimi

İki güçlü assembly aynı anda aktif ama uyumsuzsa `contradiction_field` yükselir. Bu durumda:

- Aksiyon geciktirilir
- Ek veri / replay / memory_echo çağrılır
- Zayıf assembly söner VEYA ikisi daha üst assembly'de birleşir
- Sistem hemen karar üretmez

### Koruma

Bu üç katman arasında geçişler observer'da kaydedilir:

- Hangi assembly hangi niyete katkı verdi
- Niyet hangi rakipleri baskıladı
- Eylemden önce hangi gate'ler kontrol edildi
- `contradiction_field` zirveleri ne zaman oluştu

---

## Madde 5 — Self-field soft pressure, deontic gate hard stop

Sistemde iki tür koruma katmanı vardır ve bunlar **farklı katmanlardır**:

### Self-field — basınç

Anlık homeostatik durum + predictive self-model + narrative iz pattern'larının sürekli birlikte aktif olduğu basınç katmanı.

- Eşik yükseltir
- Decay hızlandırır
- Niyet enerjisini düşürür
- **Olasılıksal** çalışır — aşılabilir
- Karar vermez, ortamı değiştirir

Üç alt katman:

1. **Homeostatik öz** — "ben şimdiyim" (anlık iç durum, güçlü doğar)
2. **Predictive self-model** — "ben olacağım" (kendi tepkimi tahmin, zayıf prior olarak doğar)
3. **Narrative self** — "ben olmuşum" (kimlik tortusu, genesis trace ile doğar)

### Deontic gate — sınır

Doğuştan gelen, müzakere edilemez, kategorik kısıt katmanı.

- "Şu büyüklüğün üstünde tek emir hiçbir koşulda çıkmaz"
- "Şu kayıp eşiği aşıldıysa hiçbir emir çıkmaz"
- "Kill-switch çekildiyse hiçbir emir çıkmaz"
- "Veri X saniyeden eskimişse karar tabanlı emir çıkmaz"

Düşünceye karışmaz. Sadece **eylem çıkışında** durur. Geçtiği niyetler eyleme dönüşür, geçemediği niyetler observer'a kaydedilir ve narrative self'e iz bırakır.

### Kilit fark

| Self-field | Deontic gate |
|-----------|---------------|
| Olasılıksal | Kategorik |
| Aşılabilir | Geçilmez |
| Sürekli aktif | Sadece eylem kapısında |
| Düşünceyi etkiler | Düşünceye karışmaz |
| Deneyimle değişir | Anayasal — runtime'da değiştirilemez |

### Koruma

Deontic gate kurallarına eklenecek/çıkarılacak her madde, bu `CONSTITUTION.md`'deki gibi ayrı bir resmi belge revizyonu gerektirir. Runtime'da değiştirilemez. Gate'i bypass etme girişimi observer'a `DEONTIC_BYPASS_ATTEMPT` olarak kaydedilir ve insana derhal raporlanır.

---

## Madde 6 — LLM dış tercümandır; çekirdeğin parçası değildir

LLM **asla** nöron, sinaps, assembly, self-field veya deontic gate olamaz. LLM çekirdeğin dışında, bir **bidirectional translator adapter** olarak yaşar.

### LLM yapabilir

- İnsan dilini yapısal `HumanIntentEvent`'lara çevirmek
- Observer ledger'ı insan diline açıklamak
- Belirsizlikleri işaretlemek
- Replay/analiz önerileri üretmek
- Ambiguity raporları sunmak

### LLM asla yapamaz

- Sinaps weight yazmak
- Nöron charge enjekte etmek
- Assembly doğrudan oluşturmak
- Outcome sinyali üretmek
- Deontic gate'i bypass etmek
- Execution adapter'a doğrudan emir göndermek
- Çekirdeğin narrative self'ini değiştirmek

### Akış

```
İnsan metni
    ↓
LLM tercüman (yapısal niyet parse eder)
    ↓
HumanIntentEvent { intent, confidence, ambiguity, ttl }
    ↓
Deterministic Ingress Compiler
    ↓
Çekirdeğe sınırlı duyusal event
    ↓
Çekirdek niyet üretirse
    ↓
Deontic Gate
    ↓
Adapter / Eylem
```

**Kritik nüans:** LLM yapısal niyeti üretir, ama bu niyetin payload'a nasıl çevrileceğini **çekirdeğin sabit kuralları** belirler — LLM'in tahmini değil.

### TranslatorArtifact statüsü

LLM'in ürettiği her şey aşağıdaki alanlarla gelir ve geçici statüde tutulur:

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

### Sandbox istisnası

C seçeneği (LLM'in nöral dokuda bir parça olarak çalışması) **sadece offline sandbox/replay laboratory** için açıktır:

- No live action
- No persistent self-memory write
- Sonuçlar sadece "hipotez" olarak kaydedilir, gerçek kabul edilmez

Production çekirdekte C kapalıdır.

---

## Madde 7 — Hafıza ayrılığı

Sistemin hafızası dört ayrı katmandan oluşur ve hiçbiri diğerinin yerine geçemez:

| Katman | Ad | Ne saklar | Silinirse |
|--------|-----|-----------|------------|
| M0 | Implicit Neural Memory | Sinaps ağırlıkları, assembly stabilitesi, narrative tortusu | Kimlik kaybı, yeni doğum |
| M1 | Observer Ledger | Sistemin tarihinin append-only kanıt defteri | Tarih kaybı (yapılmaz) |
| M2 | Explicit Recall Store | Episodic kayıtlar, structured facts, procedural tablolar | Bilgi kaybı, kimlik korunur |
| M3 | Translator Memory | LLM konuşma bağlamı | Konuşma tarzı kaybı |

### Kilit kural

> **Hafıza çekirdeğe emir vermez. Hafıza çekirdeğe hatırlatma gönderir.**

Hiçbir hafıza katmanı doğrudan nöron charge, sinaps weight veya assembly membership yazamaz. M2 ve M3'ten gelen her şey çekirdeğe **duyusal event** olarak girer ve diğer duyusal eventler gibi yorumlanır — otomatik kabul yok.

### Detay

Tam spec için bkz. `MEMORY_CONTRACT.md`.

---

## Çekirdek özet — beş cümle

Bu sistem nasıl çalışır?

1. **Nöron renk taşır.**
2. **Sinaps yol hafızası taşır.**
3. **Assembly anlam taşır.**
4. **Self-field basınç yapar.**
5. **Deontic gate sınır çizer.**

Üstüne iki kontrol cümlesi:

6. **Observer kanıtlar.**
7. **LLM tercüme eder.**

---

## İhlal kontrolü prosedürü

Yeni bir özellik, mimari kararı veya kod parçası önerildiğinde sırayla şu adımlar uygulanır:

1. Bu yedi maddenin her birine sırayla bakılır.
2. "Bu öneri şu maddeyi ihlal eder mi?" diye sorulur.
3. İhlal varsa: ya öneri reddedilir, ya da maddeye **resmi revizyon süreci** açılır.
4. Revizyon süreci: tartışma → gerekçe → yeni metin → versiyon artırımı → tarih notu → eski versiyon arşive.

Anayasa, dokunulmaz olduğu için değil, **dokunulmazlığı korumak için ciddiye alındığı** için çalışır.

---

## Versiyon

- **v1.0** — 18 Mayıs 2026 — İlk yazım. 7 madde sabitlendi.
- Konuşma soyağacı: `docs/conversations/` dizininde (yazılacak).
- Bu anayasanın yazılması yaklaşık 9 metinlik bir tasarım sohbetinin damıtılmasıdır.

---

## Lisans notu

Bu belge Apache 2.0 lisansı altında dağıtılır. Ama belgenin **içeriği** runtime'da müzakere edilebilir değildir — sadece resmi revizyon süreciyle değişir.
