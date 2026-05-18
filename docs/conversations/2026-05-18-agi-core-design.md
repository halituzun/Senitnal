# 2026-05-18 — AGI Çekirdeği Tasarım Konuşması

> Bu belge, Senitnal projesinin nöral çekirdek anayasası (CONSTITUTION.md) ve
> hafıza sınır sözleşmesi (MEMORY_CONTRACT.md) ortaya çıkmadan önce yapılan
> üçlü tasarım konuşmasının tam dökümüdür: Halit + Claude + ChatGPT.
>
> Projenin soyağacı. Sonradan biri "bu anayasa nereden geldi?" diye sorarsa
> cevabı bu dosyadadır.

---

## Tarih: 2026-05-18

## Katılımcılar
- **Halit** — proje sahibi, finansal AGI vizyonu
- **Claude** — mimari tartışma partneri
- **ChatGPT** — ikinci görüş, felsefi karşı taraf

## Konuşma

---

**Halit (12:24):**

kanka bu işi projelendirmeliyiz ama amacımız finansal agi pojesinin çekirdeği beyni öyle bir yapacağızki insan beyni gibi sonradan buna uzuvlar bir şablonda bir standartta eklenmesi çok kolay olacak ve beyin bunlar şuan sohbet ediyoruz projelendirmek için

---

**Claude — Architected modular AGI brain with standardized adapter contracts:**

Kanka tamam, belgeyi baştan sona okudum. Mimari zaten kafanda netleşmiş — şimdi mesele bunu "düşünülmüş bir felsefe" olmaktan çıkarıp "monte edilebilir bir iskelet" haline getirmek. Projelendirmek dediğin tam olarak bu, kod yazmak değil.

Bence bu sohbette dört şeyi netleştirmemiz gerekiyor. Sırayla gidelim çünkü hangisinde yamuk başlarsak, ileride bütün uzuvlar eğri takılır.

### 1. Kontrat-önce yaklaşımı (asıl temel bu)

Sen "uzuvlar standart bir şablonda takılsın" dedin ya — projenin gerçek omurgası burada. Kod değil, modül değil, kontrat. Önce şu şemaları yazmalıyız (implementasyon değil, sadece spec olarak):

- **Observation Schema** → adaptörlerden beyne ne formatta veri gelecek
- **Decision Schema** → beyinden adaptöre ne formatta karar/intent çıkacak
- **Adapter Manifest** → bir uzuv kendini beyne nasıl tanıtır: yetenekleri, yasakları, izin seviyesi, audit gereği, risk profili
- **Memory Record Schemas** → her hafıza türünün alanları (episodic, risk, counterfactual ayrı ayrı)
- **Neuron Interface** → bir nöron neyi input alır, output olarak hangi formatta iddia üretir

Bu beşi bittiğinde projenin aslında %60'ı bitmiş olur. Çünkü beyin değişir, nöronlar değişir, adaptörler değişir — ama kontratlar değişmez, sadece versiyonlanır.

### 2. Minimum Viable Brain — ilk teslim edilecek şey

Belgede 11 katman var. Hepsini birden inşa edersek iki ay sonra hiçbir şey çalışmıyor olur ve sen sıkılırsın. Bence ilk milestone şu olmalı:

**Beyin hiçbir aksiyon almıyor ama her input'a gerekçeli BLOCK / WAIT cevabı veriyor.**

Bunun için sadece şunlara ihtiyacımız var:
- Survival Kernel → başlangıçta sadece bir kural listesi
- Sensory Router → tek bir normalize fonksiyonu
- Memory: sadece Episodic + Risk memory
- Decision Governor → verdict + reason çıkartan tek bir karar kapısı
- Echo Adapter → sahte bir uzuv

Önce omurganın "hayır" diyebildiğini kanıtlayalım.

### 3. Teknoloji seçimleri

- **Çekirdek dili:** Python. FastAPI, async event loop, ML/LLM ekosistemi.
- **Persistence:** PostgreSQL daha rahat (JSON, event sourcing, vector extension).
- **Mesaj geçişi:** Başlangıçta in-process asyncio queue.
- **Karar logu:** Append-only event store. Pazarlık dışı.

### 4. Repo iskeleti

```
mindcore/
├── contracts/        # şemalar, spec dosyaları (kod değil)
├── core/             # survival kernel, governor, memory
├── neurons/          # her nöron ayrı dosya, hot-loadable
├── adapters/         # uzuvlar — başta sadece echo
├── runtime/          # event loop, dispatcher
├── decisions/        # append-only karar event store
└── tools/            # debug, replay, audit CLI
```

**Asıl soru:** Bu beyin event-driven mi olacak yoksa sürekli düşünen bir döngü mü?

Diğer üç soru:
1. Konuşan beyin mi, dilsiz beyin mi? LLM nereye giriyor?
2. Tek brain mi, çoklu brain mi?
3. Persistence: MSSQL'de ısrar mı, PostgreSQL'e geçiş mi?

---

**Halit:**

bence bu değil... önceki cevap hâlâ modül mimarisine kaçtı. Senin aradığın şey organigram değil, daha ilkel bir sinir dokusu ya da zeka tohumu.

---

**Halit (12:30):**

kanka hayır dur benim istediğim bak chatgbt de katıldı aramıza onunda yorumu aşağıda

---

**Claude — Orchestrated collaborative AGI framework balancing emergence with auditability:**

Kanka tamam, ChatGPT'nin yorumu seni daha yakından temsil ediyor — kabul. Ben hâlâ "iyi tasarlanmış yazılım mimarisi" zihninden bakmışım. O daha derinden konuşuyor: önce zihin değil, zihin doğurabilecek doku.

Yine de bu noktada dürüst arkadaş olarak üç gizli tuzak görüyorum:

**Tuzak 1 — "Hafıza sinaps ağırlığında yaşar" → audit kaybı.** Finansal sistemde "sinaps ağırlıkları öyle dedi" kabul edilebilir cevap değil.

**Tuzak 2 — "Tek tip nöron, uzmanlık emergent çıkar" → bu denenmiş, çıkmadı.** SNN, Liquid State Machines, Hebbian/STDP — 30 yıldır araştırılıyor, dar görevlerde çalışıyor.

**Tuzak 3 — "Modül yok, hepsi emergent" → modüller gizliden geri sızıyor.** "Homeostatik benlik alanı" da bir meta-nöron olur, modül olur.

**Orta yol:**
- Alt katman: ChatGPT'nin dediği gibi. Nöron, sinaps, charge, decay, plastisite, Hebbian.
- Üstte tek bir sessiz katman: **observer**. Karar vermez, müdahale etmez, sadece her nöron ateşlemesini append-only log'a yazar. MRI cihazı gibi.

### Bir yapay nöron nasıl davranmalı?

ChatGPT'nin yedi parametresi (charge, threshold, memory_trace, decay, fatigue, plasticity, links) iyi başlangıç ama bir tane daha eklemeliyiz:

**`semantic_payload` — nöronun ne taşıdığı.**

Bu strict bir kategori değil, bir "yük rengi" gibi: "şüphe", "benzerlik", "tehlike-hatırlatması". Bu etiket nöronun ne olduğunu söylemez, **ne çağrıştırdığını** söyler.

Beyinde de böyle: aynı tip nöron, ama nörotransmitter farklı (dopamin, serotonin, GABA, glutamat).

**İki yol:**
- **Yol A** — Saf homojen nöron (ChatGPT'nin saf hali): tek tip, anlam yok, sadece elektrik.
- **Yol B** — Etiketli nöron: hâlâ tek tip, hâlâ aynı denklemler, ama her biri küçük bir yük rengi taşıyor.

---

**Halit:**

Metni, ham sinir dokusu fikrini reddetmek değil; onu hesap verebilir ve mühendislikte taşınabilir hale getirme uyarısı olarak okuyorum. Saf nöral doku fikrim felsefi olarak güzel ama fazla romantik kalıyor. **Yol B kazanıyor** ama saf hali değil.

---

**Claude (12:46) — Synthesized intellectual compromise on neural payload semantics:**

Tamam kanka. "Yol B-" formülü doğru, kilitliyoruz. En kritik ayrım şu cümlede saklı:

> payload = nöronun ne yaptığı değil, taşıdığı renk.

"risk", "trade", "buy" payload'larına çekilirsek modül sistemine geri düşeriz; **"suspicion", "novelty", "contradiction"** gibi ilkel zihinsel renklerde kalırsak nöral kalır.

### ChatGPT'nin atladığı üç boşluk

**Boşluk 1: Payload listesi statik mi, dinamik mi?**
Primer set + kombinasyon. 6-8 tane ilkel payload (suspicion, novelty, aversion, attraction, contradiction, urgency, memory_echo, fatigue_trace) çekirdekte sabit. Sistem bunları kombine ederek karışım payload'lar türetebilir.

**Boşluk 2: Payload nasıl etki ediyor, kim yorumluyor?**
Her primer payload için bir default modulation profili. Sistem doğduğunda bu profillerle gelir (refleksler gibi). Ama bu profiller zamanla deneyimle ayar kayar.

**Boşluk 3: Observer'ın çözünürlüğü ne?**
İki katmanlı observer:
- **Fine grain ring buffer:** son 60 sn'nin her ateşlemesi RAM'de, eski olanlar otomatik silinir.
- **Coarse grain permanent log:** anlamlı eşiklerin geçildiği anlar kalıcı olarak yazılır.

### Çekirdek ilkesi:

> Homojen denklem + primer payload paleti (kombinasyona açık) + default modulation profilleri (deneyimle kayan) + iki katmanlı müdahalesiz observer + append-only kalıcı iz + zamanla kendiliğinden oluşan zihin.

### Sıradaki büyük soru: sinaps

a. **Sinaps ağırlığı nasıl güncelleniyor?** STDP (Spike-Timing-Dependent Plasticity) tarafındayım.

b. **Sinaps payload taşır mı, yoksa hedef nöron mu yorumlar?** Hedef nöron yorumlar. Sinaps sade kalıyor.

c. **Sinaps doğuşu ve ölümü nasıl?** Lokal komşuluk + co-firing tabanlı doğum, ikisi birden.

---

**Halit:**

Sinaps renkli kanal olmamalı. Sinaps saf yol olmalı. Yorumu hedef nöron yapmalı. Ama "saf yol" derken şunu kastetmiyorum...

---

**Claude (12:55) — Identified critical gaps in synaptic learning framework:**

Kanka bu cevap çok sağlam, sinaps tarafının %85'i kilitlendi. Özellikle:

> "Anlam sinapsta değil, akış deseninde doğar. Sinaps sadece hangi akışların yaşamaya değer olduğunu öğrenir."

Bu cümle çekirdeğin **ikinci anayasa maddesi**.

### Dört kritik boşluk

**Boşluk 1: Outcome signal nereden geliyor?**
Hibrit: doğuştan içsel (prediction error, contradiction reduction), deneyimle dışsal (adaptörden gelen kar/zarar, kullanıcı feedback) eklenir.

**Boşluk 2: Eligibility trace ne kadar geriye/ileriye uzanıyor?**
Çoklu temporal scale. Her sinapsta üç paralel iz:
- `fast_trace`: yarı ömrü saniyeler
- `medium_trace`: yarı ömrü dakikalar
- `slow_trace`: yarı ömrü saatler

**Boşluk 3: STDP'nin gizli zaafı — correlation vs causation.**
Sistem periyodik **sleep / replay** moduna girmeli. Spurious bağlantılar bu replay'de zayıflar, gerçek nedensel bağlantılar güçlenir.

**Boşluk 4: Bootstrap — ilk çalıştığında ne var?**
"Doğan bebek": minimum genome ile başlar.
- Birkaç düzine seed nöron, her primer payload için
- Lokal komşuluk bağlantıları
- Default receptor profilleri
- Bir "varlığını sürdür" homeostatik referans noktası
- Birkaç doğuştan refleks

### Çekirdek anayasası (3 madde):
1. Nöron homojen denklem + heterojen payload + receptor yorumlama.
2. Sinaps payload taşımaz; akış deseninin hafızasını taşır.
3. Doğuş minimum genome ile başlar — sıfır değil, modül de değil; bir embriyo.

### Sıradaki soru: Nöron toplulukları nasıl oluşuyor?

1. Topluluklar kendiliğinden mi oluşuyor yoksa minimum seed topology mi koyuyoruz?
2. Bir topluluk ne zaman "bir fikir" oluyor, ne zaman sadece gürültü?
3. Topluluklar arasında rekabet var mı (winner-take-all) yoksa paralel mi?

---

**Halit:**

Topluluklar tamamen sıfırdan kendiliğinden oluşmamalı. Ama tam scripted de değil...

---

**Claude (13:43) — Identified critical gaps before advancing self-model discussion:**

Üç anayasa maddesi artık net:
1. **Doku doğuştan. Düşünce deneyimden.**
2. **Bir kez yanan desen gürültüdür. Geri dönebilen ve işe yarayan desen fikirdir.**
3. **Yerel rekabet. Global paralellik. Winner-take-most.**

### Dört boşluk

**Boşluk 1: Time/tick modeli — event-driven mi clocked mi?**
Event-driven. asyncio event loop + priority queue.

**Boşluk 2: Wake/Sleep ritmi nasıl tetikleniyor?**
İçsel basınç bazlı: eligibility trace pool dolunca, contradiction load eşiği geçince, fatigue accumulate olunca.

**Boşluk 3: Counterfactual replay nasıl çalışacak?**
İki yöntem birden, farklı zamanlarda. Model-based (ucuz, anlık) + Causal intervention (pahalı, derin uyku).

**Boşluk 4: Assembly identity continuity — Ship of Theseus.**
Assembly identity = kalıcı nöron çekirdek + observer tarafından atanan id. %60'tan fazlası değişirse → yeni id.

### Benlik konusu

ChatGPT diyor ki benlik = "sürekli aktif olan en derin homeostatik assembly". Doğru ama eksik. Benlik üç ayrı şeyden örülür:

- **Katman 1 — Body schema / homeostatik öz:** "Şu an enerjim X, contradiction yüküm Y."
- **Katman 2 — Predictive self-model:** "Ben buna nasıl tepki vereceğim?"
- **Katman 3 — Narrative self / kimlik izi:** "Ben şüpheci davranan bir sistemim..."

> Katman 1 "ben şimdiyim" + Katman 2 "ben olacağım" + Katman 3 "ben olmuşum"

Üçü aynı anda aktif olmazsa benlik kırılır.

### Çekirdek anayasaya eklenecek madde:

> Benlik tek bir assembly değil; anlık homeostatik öz + predictive self-model + narrative iz pattern'larının sürekli birlikte aktif kalması.

---

**Halit:**

Cümleyi düzeltme: "Sistem aynı olay için iki rakip açıklama tutabilir, ama eyleme dökerken tek bir yorum kazanır."

> Düşüncede paralellik serbest.
> Niyette rekabet başlar.
> Eylemde tekleşme zorunlu.

---

**Claude (14:01) — Synthesized multi-layered defense architecture:**

Cümle düzeltmesi çok yerinde — anayasaya **dördüncü madde**.

Üç katmanlı bootstrap kabul: omurga + tahmin tohumu + genesis izi. "Tam kişilik değil, kişilik doğuracak self-genome."

### Self-field'in son sorusu

ChatGPT'nin cevabı (soft pressure, doğrudan veto yok) çoğunlukla doğru. Karl Friston'un active inference'inde de var — beyin "engellemiyor", precision'ı düşürüyor.

Ama bir senaryoda kırılan yer var: **catastrophic moments.**

Piyasa flash crash'i, sistem panic-like assembly üretiyor. Self-field "yavaşla" diyor ama urgency payload'ı o kadar yüksek ki eşiği yine aşıyor. Bot kötü zamanda emir gönderiyor.

Self-field'in **altında** (üstünde değil) bir katman daha lazım:

### Deontic gate / anayasal kısıt

Bu modül değil. Karar vermiyor. Sadece sistemin doğum sertifikasına kazınmış birkaç dokunulmaz "negative permission":
- "Şu büyüklüğün üstünde tek emir hiçbir koşulda çıkmaz."
- "Şu kayıp eşiği aşıldıysa hiçbir emir çıkmaz."
- "Halit kill-switch çekmişse hiçbir emir çıkmaz."
- "Veri X saniyeden eskimişse karar tabanlı emir çıkmaz."

**Self-field vs Deontic gate:**
- Self-field **olasılıksal** — eşik yükseltir, ama aşılabilir.
- Deontic gate **kategorik** — geçilmez, müzakere yok.

### Anayasaya beşinci madde:

> Self-field soft pressure ile çalışır; niyetin enerjisini düşürür, eşiğini yükseltir, ama yasaklamaz. Yasaklama ayrı bir katmanın işidir: deontic gate.

Daha kısa:
> Benlik basınç yapar. Anayasa fren tutar. İkisi farklı katmandır.

### Çekirdek anayasası 5 maddeye ulaştı:
1. Nöron homojen denklem + heterojen payload + receptor yorumlama.
2. Sinaps anlam taşımaz, akış deseninin hafızasını taşır.
3. Doğuş minimum genome ile — sıfır değil, modül de değil.
4. Düşüncede paralellik, niyette rekabet, eylemde tekleşme.
5. Self-field soft pressure, deontic gate hard stop.

### Sıradaki soru: LLM'in yeri ne?

- **A.** LLM yok. Çekirdek saf nöral.
- **B.** LLM tercüman adaptör. Çekirdek dışında.
- **C.** LLM nöral dokunun parçası.

Ben (B)'den yanayım.

---

**Halit:**

Burada benim kararım net: **B seçilmeli. Ama düz B değil: B-kısıtlı.**

- LLM çekirdeğin dışında kalır.
- LLM tercüman olur.
- LLM asla nöral dokunun parçası olmaz.
- LLM asla doğrudan charge, sinaps, weight, assembly veya niyet yazamaz.

---

**Claude (14:10) — Architected core framework and identified remaining design gaps:**

Madde 6 net ve B-kısıtlı ayrımı kritik — özellikle **"deterministic ingress compiler"** fikri güzel. LLM "monitor_only_request, confidence: 0.84" diye yapısal niyet üretsin, payload'a çeviren çekirdeğin kendi sabit kuralları olsun.

> İki hafıza ayrılmalı. Translator memory silinse bile çekirdek değişmemeli. Çekirdek hafıza silinmeden LLM değiştirilebilmeli.

### Çekirdek anayasası, son hali (6 madde):
1. Nöron homojen denklem + heterojen payload + receptor yorumlama.
2. Sinaps anlam taşımaz, akış deseninin hafızasını taşır.
3. Doğuş minimum genome ile — sıfır değil, modül de değil.
4. Düşüncede paralellik, niyette rekabet, eylemde tekleşme.
5. Self-field soft pressure, deontic gate hard stop.
6. LLM dış tercümandır; çekirdeğin parçası değildir.

### Üç temel konu havada

- **Boşluk A — Memory architecture (implicit vs explicit).**
- **Boşluk B — Attention mekaniği.**
- **Boşluk C — World model / dış dünya temsili.**

Öncelik A → B → C. Memory mimarisi netleşmeden attention konuşulmaz.

---

**Halit:**

Sırayı A → B → C yapardım. Ama A'nın adını sadece "Memory architecture" koymazdım. Bence gerçek başlık şu:

**A — Memory Boundary / Hafıza Sınır Anayasası**

Çünkü sorun "hafıza nerede tutulur?" değil. Asıl sorun:
- Hangi hafıza çekirdeğe dokunabilir?
- Hangi hafıza sadece gözlem olarak içeri girebilir?
- Hangi hafıza silinse çekirdek değişmemelidir?
- Hangi hafıza değişirse benlik bozulur?

### Madde 7 — Hafıza ayrılığı

- Çekirdeğin hafızası, explicit store hafızası, observer ledger ve translator memory birbirinden ayrıdır.
- Translator memory silinse bile çekirdek değişmez.
- LLM değişse bile çekirdek değişmez.
- Explicit memory değişse bile sinapslar doğrudan değişmez.
- Observer ledger geçmişi kaydeder ama düşünceye müdahale etmez.
- Dış hafızadan gelen her şey çekirdeğe sadece "hatırlatma olayı" olarak girer.
- Hiçbir hafıza deposu doğrudan nöron charge, sinaps weight veya assembly membership yazamaz.

Daha kısa:
> Hafıza çekirdeğe emir vermez.
> Hafıza çekirdeğe hatırlatma gönderir.

### Dört hafıza katmanı

- **M0 — Implicit Neural Memory:** Sinaps ağırlıkları, eligibility trace, assembly stabilitesi. Çekirdeğin gerçek kişiliği.
- **M1 — Observer Ledger:** Kanıt defteri. Ne oldu, hangi assembly doğdu, hangi gate engelledi.
- **M2 — Explicit Recall Store:** Episodic kayıtlar, structured facts, procedural lookup tabloları. Dış organ.
- **M3 — Translator Memory:** LLM'in konuşma hafızası. Tamamen ayrı.

> Çekirdek hatırlar.
> Observer kanıtlar.
> Explicit memory hatırlatır.
> LLM tercüme eder.
> Hiçbiri diğerinin yerine geçmez.

---

**Claude (14:40) — Synthesized memory architecture with four-layer framework:**

A → B → C sırasını ve bu kez "Memory Boundary" ismini doğru buluyorum.

> Hafıza çekirdeğe emir vermez. Hafıza çekirdeğe hatırlatma gönderir.

### Dört nüans

**Nüans 1 — Unutma her katmanda farklı çalışır.**
- M0: doğal sönüm
- M1: append-only, silinemez (compaction yapılabilir ama coarse-grain dokunulmaz)
- M2: retention policy, expires_at
- M3: TTL ile silinir

**Kritik kural:** silmek = unutmak değildir. Observer her silme olayını log'lar.

**Nüans 2 — Kimlik-hafıza hiyerarşisi.**

| Katman | Silinirse ne olur? |
|--------|-------------------|
| M0 | Tam kimlik kaybı, yeni doğum, geri dönüşsüz |
| M1 | Benlik var ama tarih yok, audit kaybı |
| M2 | Bilgi kaybı, kimlik etkilenmez |
| M3 | Sadece konuşma tarzı sıfırlanır |

**Nüans 3 — Recall ekonomisi.**
- Enerji bedeli
- Cooldown
- Habituation

Bu maliyetler olmazsa sistem patolojik ruminasyon yapar.

**Nüans 4 — M0 → M2 ters yön.**
Çekirdek doğrudan M2'ye yazamaz. Niyet üretir, observer kanıtlar, **Memory Write Gate** denetler. Self-deception riskini engelliyor.

---

**Halit:**

Şimdi yaz. Ama "proje başlatma" gibi değil. Düşüncenin kristalleşmesi olarak yap.

Üç sınırla:
1. Kod yok.
2. Implementation detayı yok.
3. Her madde ihlal testiyle yazılacak.

### M2'ye yazmak için ayrı **Memory Write Gate**

Deontic gate eylem riski içindir. M2'ye yazmak farklı bir risk: **epistemik risk**. Sistem kendi geçmişini manipüle edebilir.

Akış:
```
M0 içinde bir desen stabil olur
↓
çekirdek "externalize memory" niyeti üretir
↓
observer ilgili kanıtları paketler
↓
Memory Write Gate denetler
↓
M2'ye CandidateMemoryRecord yazılır
↓
replay/outcome/provenance ile kalıcılaşır veya expire olur
```

M2'ye yazılan ilk anda **kesin gerçek olmamalı**. Statüler:
- candidate
- verified
- superseded
- expired
- rejected

> Çekirdek kendi hikâyesini doğrudan yazamaz.
> Sadece yazılmasını teklif eder.
> Observer kanıtlar.
> Memory Write Gate geçirir.

### CONSTITUTION.md formatı

Her madde: Principle / Rationale / Allowed / Forbidden / Violation Test.

### MEMORY_CONTRACT.md yapısı

1. Purpose
2. Memory Layers
3. Identity Impact
4. Read Boundaries
5. Recall Flow
6. Recall Economy
7. Forgetting Rules
8. Write Boundaries
9. Memory Write Gate
10. Observer Relationship
11. Translator Memory Boundary
12. Backup Priority
13. Violations
14. Open Questions

---

**Halit:**

https://github.com/halituzun/Senitnal yeni açtım buna yapacağız

---

**Claude — Teşhis edilen isim ve branch sorunları düzeltiliyor:**

Repo'yu gördüm. İki ufak not:

1. **Repo adı tipo gibi duruyor** — `Senitnal` yerine muhtemelen `Sentinel` (nöbetçi, gözcü) istemiştin.
2. **Branch adı `fiyatgor`** — standart `main` daha sade olurdu.

Üç dokümanı yazdım: CONSTITUTION.md, MEMORY_CONTRACT.md, README.md.

---

## Sonuç

Bu konuşmadan üç dosya doğdu:
- `CONSTITUTION.md` (Frozen Draft v0.1) — 7 anayasa maddesi
- `MEMORY_CONTRACT.md` (Frozen Draft v0.1) — 14 bölümlük hafıza sınır sözleşmesi
- `README.md` — vizyon ve yol haritası

> Senitnal önce düşüncenin anayasasıdır.
> Kod daha sonra gelir.

### Sıradaki adımlar
- B — `ATTENTION_WORKSPACE.md` (Global Workspace pulse, attention_score)
- C — `WORLD_MODEL_INGRESS.md` (semi-structured event + neural overlay)
- Yan: `MEMORY_WRITE_GATE.md`, `RECALL_PROTOCOL.md`, `OBSERVER_LEDGER_SCHEMA.md`
