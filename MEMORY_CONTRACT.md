# MEMORY_CONTRACT.md

## Sentinel — Hafıza Sınır Anayasası

---

## Status

**Frozen Draft v0.1**
**Conceptual phase. No implementation authority.**

Bu belge `CONSTITUTION.md` Madde 7'nin detay sözleşmesidir. Çalışan bir veri katmanının spec'i değildir; **kim hangi katmana ne yazabilir, kim kime ne soramaz, hangi katman silinirse ne olur** — onun sınırlarıdır.

---

## 1. Purpose

Sentinel'in hafızası bir veri sorununa değil, **bir sınır sorununa** karşılık gelir. Yanlış katmanda yaşayan veri sistemin doğasını bozar.

Tartışmanın özünden çıkan damıtma:

> **Çekirdek hatırlar. Observer kanıtlar. Explicit memory hatırlatır. LLM tercüme eder. Hiçbiri diğerinin yerine geçmez.**

Bu belge depo formatlarını konuşmaz; **yetkilerin sınırını** konuşur.

---

## 2. Memory Layers

### M0 — Implicit Neural Memory

Çekirdeğin **dokusu**. Sistemin gerçek hafızası.

- **Ne saklar:** Sinaps ağırlıkları, eligibility trace'ler (fast/medium/slow), success trace'ler, assembly stabilite skorları, payload alışkanlıkları, self-field eğilimleri, narrative self tortusu, receptor profile kaymaları.
- **Nasıl saklar:** Doku olarak. Tabloda değil, ağda. Davranışın kendisi M0'ın ifadesidir.
- **Sorgulanabilir mi:** Doğrudan değil. M0 ifade edilir, sorgulanmaz.
- **Yazıcı:** Sadece sistemin kendi öğrenme kuralları (STDP + outcome + eligibility), otomatik.
- **Okuyucu:** Observer (passive).
- **Silinirse:** Tam kimlik kaybı, yeni doğum, geri dönüşsüz.
- **Persistans:** Sürekli yedeklenmeli — sistemin "ruh fotoğrafı".

### M1 — Observer Ledger

Sistemin **tarihinin kanıt defteri**.

İki katmanlı:

**Fine-grain ring buffer**
- Son ~60 saniyenin her event'i, RAM'de döner
- Eski olanlar otomatik tasfiye olur
- "Anlık zihinsel iz" — kısa dönem inceleme için

**Coarse-grain permanent log**
- Anlamlı eşik geçilen olaylar
- Append-only, **silinemez**
- Diskte, çoklu yedekli

**Köprü mekaniği:** Bir olay coarse-grain log'a yazıldığı an, ilgili fine-grain pencere snapshot olarak kalıcılaşır.

**Coarse-grain log'a giren tipik event'ler:**
`SPIKE_BURST`, `ASSEMBLY_CANDIDATE_BORN`, `ASSEMBLY_STABILIZED`, `ASSEMBLY_MERGED`, `ASSEMBLY_SPLIT`, `ASSEMBLY_SUPPRESSED`, `ASSEMBLY_RECALLED`, `ASSEMBLY_PROMOTED_TO_IDEA`, `ASSEMBLY_DECAYED`, `ASSEMBLY_PRUNED`, `CONTRADICTION_PEAK`, `INTENTION_FORMED`, `INTENTION_SUPPRESSED`, `DEONTIC_BLOCKED`, `DEONTIC_BYPASS_ATTEMPT`, `MEMORY_WRITE_PROPOSED`, `MEMORY_WRITE_GATE_PASSED`, `MEMORY_WRITE_GATE_REJECTED`, `RECALL_REQUEST_SENT`, `RECALL_EVENT_INGESTED`, `OUTCOME_RECEIVED`, `WAKE_TO_SLEEP_TRANSITION`, `SLEEP_TO_WAKE_TRANSITION`, `REPLAY_SESSION_COMPLETED`, `SELF_GENESIS` (bir kez, doğumda).

- **Yazıcı:** Sadece sistemin kendisi (observer dinler ve yazar, sormaz, müdahale etmez).
- **Okuyucu:** İnsanlar (audit), LLM tercüman (rapor), explicit memory adapter (özet üretmek için).
- **Silinirse:** Tarih kaybı. **Yapılmaz.** Yedekleme sürekli ve dağıtık.

### M2 — Explicit Recall Store

Dış **hafıza organı**.

- **Ne saklar:** Episodic kayıtlar ("Halit 18 Mayıs'ta kill-switch çekti"), structured facts, procedural lookup'lar, incident kayıtları, insan kararlarının izleri, deontic geçmişi, world facts.
- **Yapı:** Standart veri katmanı (PostgreSQL veya MSSQL — sonraki karar). Sorgulanabilir, indekslenebilir, versiyonlanabilir.
- **Yazıcı:** İnsan (direct), observer (snapshot/extract), system (Memory Write Gate'ten geçen `memory_write_intention` üzerinden — bkz. §9).
- **Çekirdek doğrudan yazar mı:** **Hayır.** Sadece niyet üretir.
- **Silinirse:** Bilgi kaybı, kimlik korunur, kısmen yeniden inşa edilebilir.

#### Alt-türleme: `subject_class`

M2 kayıtları `subject_class` alanı ile alt-türlenebilir. Yeni hafıza katmanı doğmaz; M2 içinde farklı **kayıt tipleri** olur. Örnekler:

```
subject_class:
  - episodic         (insan/sistem olay kayıtları)
  - structured_fact  (kalıcı dünya bilgileri)
  - procedural       (lookup tabloları, compatibility matrix)
  - incident         (anlık olaylar, hatalar)
  - source_trust     (kaynak güvenirlik kayıtları — bkz. WORLD_INGRESS §16)
  - deontic_policy   (operasyonel hard-stop eşikleri — bkz. DEONTIC_GATE §7)
  - bootstrap_reference (kuruluş referansları — bkz. BOOTSTRAP_GENOME §20)
```

`SourceTrustRecord` (`subject_class = "source_trust"`) bu mekanizmanın ilk somut örneğidir. Yeni katman değildir; M2'nin bir alt-tipidir. CandidateMemoryRecord statü zinciri (§10) aynen geçerlidir.

### M3 — Translator Memory

LLM'in **konuşma bağlamı**.

- **Ne saklar:** Son konuşmalar, Halit'in ifade biçimi, açıklama tercihleri, dilsel süreklilik, Telegram konuşma geçmişi.
- **Yazıcı:** LLM.
- **Çekirdeğe etkisi:** Hiçbir. M3 silinse bile çekirdek aynıdır.
- **TTL:** Birkaç gün – birkaç hafta sonra otomatik silinir.
- **Silinirse:** Sadece konuşma tarzı sıfırlanır.

---

## 3. Identity Impact

| Katman | Silinirse kimlik durumu | Yedekleme önceliği |
|--------|--------------------------|---------------------|
| M0 | Tam kimlik kaybı, yeni doğum | En yüksek, sürekli, dağıtık |
| M1 | Benlik var ama tarih yok | Çok yüksek, çoklu kopya |
| M2 | Bilgi eksilir, kimlik korunur | Standart DB backup |
| M3 | Konuşma tarzı sıfırlanır, kimlik dokunulmaz | Yedeklenmek zorunda değil |

**M0 + M1 = ruh + tarih.** Restore stratejisi bu ikisi üzerine kurulur. Bir M0+M1 snapshot'undan dönen sistem **aynı varlık** sayılır; sadece M0 boş restore edilirse **yeni doğum** olur.

---

## 4. Read Boundaries

| Okuyucu | M0 | M1 | M2 | M3 |
|---------|----|----|----|-----|
| Çekirdek (kendi) | yaşar ama "okumaz" | hayır | sadece RecallEvent olarak | hayır |
| Observer | passive izleyici | yazar/okur | yardımcı snapshot | hayır |
| Explicit memory adapter | hayır | özet okur | tam okur/yazar | hayır |
| LLM translator | hayır | rapor için okur | hayır (RecallEvent intent üretebilir) | yazar/okur |
| İnsan | hayır (doğrudan) | audit okur | yazar/okur | okur |

**Kritik:** Çekirdek M2'yi "sorgulamaz". Çekirdekte `memory_echo` gerilimi yükselir, RecallRequest çıkar, RecallEvent geri döner ve **duyusal event** olarak içeri girer.

---

## 5. Recall Flow

```
Çekirdekte memory_echo gerilimi yükselir
    ↓
RecallRequest port üzerinden çıkar
    ↓
Explicit memory adapter ilgili hatırlatmayı bulur
    ↓
RecallEvent olarak geri gönderir
    ↓
Deterministic ingress compiler nöral dile çevirir
    ↓
Çekirdek bir duyusal event gibi yorumlar
```

### RecallEvent şeması

```
RecallEvent
├── memory_type: episodic | structured | procedural | incident
├── content: <opaque payload>
├── source: M2 adapter id
├── original_timestamp
├── retrieval_timestamp
├── confidence: 0.0 - 1.0
├── ttl_ms
├── provenance
├── contradiction_risk
└── raw_ref
```

**Önemli kural:** RecallEvent gerçek değildir, **kaynaklı gözlemdir**. Çekirdek otomatik kabul etmez; çelişki/güven testlerine tabi tutar.

---

## 6. Recall Economy

Sınırsız recall = **pathological rumination**. Her recall'un bedeli vardır:

- **Enerji bedeli:** Her `RecallRequest` homeostatic stability'yi geçici düşürür (fatigue birikir).
- **Cooldown:** Aynı `RecallRequest` peşpeşe yapılamaz, her recall tipi için refractory period.
- **Habituation:** Aynı `RecallEvent` 5. kez geldiğinde 1.'ye göre çok düşük payload intensity üretir.

Bu maliyetler self-field tarafından "hissedilir"; sistem kendi kendine recall fırtınasına girmez.

---

## 7. Forgetting Rules

| Katman | Unutma mekanizması | Geri alınabilir? |
|--------|---------------------|--------------------|
| M0 | Doğal sönüm: weight decay, eligibility çürüme, dormant prune | Hayır (dokuya yazılı) |
| M1 | Ring buffer otomatik tasfiye; coarse-grain log **silinmez** | Ring buffer hayır, log dokunulmaz |
| M2 | Retention policy, `expires_at`, `staleness_threshold` | Backup'tan evet |
| M3 | TTL bazlı otomatik silme | Hayır (kasıtlı geçicilik) |

### Forgetting is observable

> **Silmek ≠ unutmak.**

Observer her silme/expire/prune olayını M1'e yazar. M2'den bir kayıt expire olduğunda `M2_RECORD_EXPIRED` event'i M1'de doğar. M0'da bir sinaps prune edildiğinde `SYNAPSE_PRUNED` event'i M1'de doğar.

**Sistem "bunu hiç bilmiyordum" diyemez.** Doğru cevap: "Bu kayıt M2'den şu tarihte expire oldu. Expire olayı M1'de kayıtlı."

---

## 8. Write Boundaries

| Yazıcı | M0 | M1 | M2 | M3 |
|--------|----|----|----|-----|
| Çekirdek (kendi öğrenme kuralları) | evet (auto) | hayır (observer yazar) | hayır (sadece intention) | hayır |
| Observer | hayır | evet | yardımcı (snapshot/extract) | hayır |
| Explicit memory adapter | hayır | event yazar | evet | hayır |
| LLM translator | hayır | hayır | hayır (sadece RecallIntent) | evet |
| İnsan | hayır (doğrudan) | hayır | evet | evet |
| Memory Write Gate (kapı) | hayır | yazma kararını M1'e logla | geçirir/reddeder | hayır |

**Hiç kimse M0'a doğrudan yazamaz.** Sadece sistem kendi öğrenme kurallarıyla yazar.

> *Çekirdek otomatik öğrenme = sistemin kendi iç süreçleri. Bu "dış yazıcı" değildir, M0'ın doğal işleyişidir.*

---

## 9. Memory Write Gate

### Niye ayrı bir kapı?

> **Deontic gate eylem riskini sınırlar.**
> **Memory Write Gate epistemik riski sınırlar.**

İki risk farklıdır:
- **Action risk** (deontic gate): Bir niyet dış dünyaya emir olarak çıkıyor; sermaye, sistem, başkaları etkilenir.
- **Epistemic risk** (Memory Write Gate): Sistem kendi geçmişini, gerekçesini veya bilgisini **explicit kalıcı bilgi** olarak yazıyor; bu kayıt ileride kendisinin ve başkalarının kararlarını etkileyecek.

Birini diğerinin alt türü saymak iki riski karıştırır. **Memory Write Gate deontic gate'in alt türü değildir.** Ayrı bir kapıdır.

### Akış

```
M0 içinde bir desen stabil olur
    ↓
Çekirdek "externalize memory" niyeti üretir
    ↓
Observer ilgili nöral/assembly kanıtlarını paketler
    ↓
Memory Write Gate denetler
    ↓ (geçerse)
M2'ye CandidateMemoryRecord yazılır
    ↓
Sonradan replay/outcome/provenance ile statü değişir
```

### Gate'in karar kuralları

Gate **yargı yapmaz, koşul kontrol eder**. Tamamen sayısal/mekanik kurallar üzerinden çalışır (bir karar modülüne dönüşmemesi için):

- Desen tekrar eşiği geçti mi? (örn. assembly N kez stabilize oldu)
- Observer kanıt seti yeterli mi? (örn. bağlantılı M1 event sayısı eşiğin üstünde)
- Çelişki yükü düşük mü? (`contradiction_field < threshold`)
- Self-field fatigue normal mi? (yorgun sistem M2'ye yazmasın)
- Kayıt zaten benzer içerikle var mı? (duplicate check)

Bu kurallar `MEMORY_WRITE_GATE.md` belgesinde sayısal eşiklerle tanımlanacak. Gate hiçbir koşulda "bu kayıt mantıklı mı?" diye semantik yargı yapmaz.

---

## 10. CandidateMemoryRecord

M2'ye yazılan **sistem kaynaklı** her kayıt önce **candidate** statüsünde doğar. Doğrudan "gerçek" değildir.

### Statü makinesi

```
CandidateMemoryRecord
├── candidate    ← yeni doğdu, henüz doğrulanmadı
├── verified     ← replay/outcome/provenance kontrolünden geçti
├── superseded   ← daha iyi/yeni bir kayıt onun yerini aldı
├── expired      ← retention süresi doldu
└── rejected     ← replay kontrolünde çürüdü
```

### Statü geçişleri

| Geçiş | Kim tetikler | Şart |
|-------|--------------|-------|
| candidate → verified | observer + replay engine | replay kontrolü pozitif outcome ile geçti |
| candidate → rejected | observer | replay çürüttü (counterfactual başarısız) |
| verified → superseded | observer | benzer içerikli daha güçlü kayıt geldi |
| any → expired | retention scheduler | `expires_at` geçti |

### Statü kuralları

- **candidate** statüsündeki bir kayıt RecallEvent üretebilir ama `confidence` düşük gelir
- **verified** statüsündeki kayıt normal confidence ile RecallEvent üretir
- **superseded** ve **rejected** RecallEvent üretmez ama M1'de kalır (history)
- **expired** RecallEvent üretmez; expire olayı M1'e yazılır

> **Çekirdek kendi hikâyesini doğrudan yazamaz. Sadece yazılmasını teklif eder. Observer kanıtlar. Memory Write Gate geçirir. Replay doğrular.**

Bu zincir, self-deception riskini engellemenin asıl mekanizmasıdır. Sistem "ben bu kararı şu sebepten verdim" diye **kendi narrative self'ini şişiremez** — çünkü öyle bir M2 kaydı ancak verified olduktan sonra geri çağrılabilir.

### İnsan kaynaklı kayıtlar

İnsan tarafından (Halit, audit ekibi) doğrudan M2'ye yazılan kayıtlar candidate aşamasından geçmez; başlangıçta **verified** olarak işaretlenir ama `provenance: human` etiketi taşır. Bu kayıtlar da expire olabilir, superseded olabilir, ama rejected statüsüne sadece insan başka bir insan kaydıyla geçirebilir.

---

## 11. Observer Relationship

Observer hem M1 yazıcısıdır, hem M2'ye snapshot paketler. Bu **dual role** dikkatli sınırlandırılmalı:

- Observer hiçbir kararı kendi başına vermez — sadece kaydeder ve paketler.
- Observer Memory Write Gate'in **müşterisi**dir, **gate değildir**.
- Observer'ın paketleme kuralları sayısal/deterministic olmalı (semantik yargı yok).
- Observer'ın kendisi de denetlenebilir olmalı: observer'ın hangi event'i hangi kayda dönüştürdüğü `OBSERVER_PROVENANCE` etiketi ile M1'e yazılır.

> *Açık soru: Observer'ın bu dual-role'ü uzun vadede ikiye bölünmeli mi? (kayıt observer + paketleme observer). Bkz. §14.*

---

## 12. Translator Memory Boundary

M3 çekirdekten **tam ayrık** olmalı:

- **Translator memory silinebilir.** Çekirdek değişmez.
- **LLM değiştirilebilir.** Çekirdek hafıza değişmez.
- M3'teki içerik çekirdek tarafından doğrudan görülmez.
- LLM, M3'teki konuşma bağlamını kullanarak insanın yapısal niyetini **iyileştirebilir**, ama bu iyileştirme `HumanIntentEvent`'a düşer ve oradan deterministic ingress compiler'a gider.

Kritik ayrım:
- M0 silinirse → yeni varlık doğar.
- M3 silinirse → aynı varlık ama "bağlam unutmuş" gibi davranır.

---

## 13. Backup Priority

| Katman | Backup sıklığı | Hedef |
|--------|---------------|-------|
| M0 | Sürekli (her N dakikada bir snapshot + WAL benzeri append) | Dağıtık, çoklu lokasyon |
| M1 | Append-only zaten yedek niteliği; ek olarak günlük tam snapshot | Çoklu lokasyon |
| M2 | Standart DB backup (saatlik incremental + günlük full) | Standart |
| M3 | Yedeklenmez (TTL'li, geçici) | — |

**Restore kuralı:** M0+M1 birlikte restore edilirse aynı varlık. Sadece M0 restore edilirse yeni varlık (M1 yoksa narrative continuity kırılır).

> *Restore senaryolarının `birth_mode` ayrımı (`clean_birth`/`restore_birth`/`fork_birth`/`migration_birth`) ve constitutional shift policy için bkz. [`BOOTSTRAP_GENOME.md`](./BOOTSTRAP_GENOME.md) §23. Constitutional hash değiştiğinde sessiz upgrade yoktur; `genesis_affecting` shift yaşayan Sentinel'e uygulanmaz, `migration_birth` gerektirir.*

---

## 14. Open Questions

Bu belgenin **sonraki sürümlerinde** çözülecek açık sorular:

- **Observer dual-role:** Observer hem kaydedici hem paketleyici. Uzun vadede ayrılmalı mı? Hangi seviyede yetki ayrımı yeterli?
- **Memory Write Gate karar kuralları:** Sayısal eşikler nereden geliyor? Anayasal mı (sabit) yoksa kalibre edilebilir mi (deneyimle ayar)? Kalibre ise kim kalibre ediyor?
- **M2 schema versioning:** M2 explicit store şeması zamanla değişecek. Eski kayıtlar nasıl migrate olur? Migration sırasında provenance nasıl korunur?
- **Replay engine'in M0 üzerindeki etkisi:** *(B tarafından kısmi cevap)* Replay M0'a iki ayrı kanaldan dokunur:
  - **Sleep/replay causal pruning** (Madde 2 altında): sinaps weight, eligibility, success trace değiştirir. Observer event: `SLEEP_REPLAY_SYNAPSE_UPDATE`.
  - **Attention replay** (`ATTENTION_WORKSPACE.md` §19 altında): sadece habituation/attention traces günceller; sinaps topolojisine dokunmaz. Observer event: `ATTENTION_REPLAY_HABITUATION_UPDATE`.
  Açık kalan: "düşledim ve öğrendim" eventinin tam tanımı, iki kanal arasındaki etkileşim, ve replay'in narrative self'i nasıl etkilediği.
- **Cross-restore identity:** Bir sistem M0+M1 backup'tan restore edildi. M2'sini başka bir sistemin M2'siyle birleştirmek istiyoruz (örn. iki Sentinel instance). Bu identity hakkı verir mi yoksa "kontamine" mi sayılır?
- **Forgetting attack:** Düşman bir aktör M2'ye yığınla expire-talebi gönderirse sistemin retention policy'si nasıl davranır? "Cognitive denial-of-service"e karşı sınır ne?

Bu sorular cevaplanmadan implementation aşamasına geçilmez. Cevaplar ileride ayrı belge revizyonları olarak gelir.

---

## İlk yapılacaklar (yine kod değil)

Bu MEMORY_CONTRACT'ın hayata geçirilmesi için ileride yazılacak ama henüz yazılmamış belgeler:

- `RECALL_PROTOCOL.md` — `RecallRequest`/`RecallEvent` şemalarının tam spec'i
- `OBSERVER_LEDGER_SCHEMA.md` — ring buffer + permanent log event tipleri, OBSERVER_PROVENANCE şeması
- `MEMORY_WRITE_GATE.md` — **epistemik gate** (deontic gate'ten ayrı), sayısal eşikler, candidate→verified geçiş kuralları
- `BACKUP_STRATEGY.md` — M0/M1 yedekleme planı, RPO/RTO hedefleri, cross-restore identity kuralları
- `INGRESS_COMPILER_SPEC.md` — RecallEvent ve diğer duyusal eventlerin payload'a çevrilme kuralları

Sıra B (Attention) ve C (World Model) konuşmalarına göre değişebilir.

---

## Versiyon

- **v0.1** — 18 Mayıs 2026 — Frozen Draft. Conceptual phase. No implementation authority.
- `CONSTITUTION.md` Madde 7'nin uzantısı.
