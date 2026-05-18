# MEMORY_CONTRACT.md

## Sentinel — Hafıza Sınır Anayasası

Bu belge `CONSTITUTION.md` Madde 7'nin detaylı uzantısıdır. Sentinel'in dört katmanlı hafıza mimarisini, aralarındaki ilişkileri, recall protokolünü, forgetting kurallarını ve kimlik-hafıza hiyerarşisini tanımlar.

---

## Felsefe

Tartışmanın özünden çıkan damıtma:

> **Çekirdek hatırlar. Observer kanıtlar. Explicit memory hatırlatır. LLM tercüme eder. Hiçbiri diğerinin yerine geçmez.**

Hafıza Sentinel'de bir veri sorununa değil, bir **sınır sorununa** karşılık gelir. Yanlış katmanda yaşayan veri sistemin doğasını bozar. Bu yüzden bu belge depo formatlarını konuşmaz; **kim kime ne yazabilir, kim kime ne soramaz** onu konuşur.

---

## Dört katman

### M0 — Implicit Neural Memory

Çekirdeğin **dokusu**. Sistemin gerçek hafızası.

**Ne saklar:**

- Sinaps ağırlıkları
- Eligibility trace'ler (fast/medium/slow)
- Success trace'ler (fast/medium/slow)
- Assembly stabilite skorları
- Payload alışkanlıkları (hangi payload sık üretiliyor)
- Self-field eğilimleri
- Narrative self tortusu
- Receptor profile kaymaları

**Nasıl saklar:** Doku olarak. Veritabanı tablosu gibi okunmaz; sistem deneyimle bu hafızayı kazanır, deneyimle kaybeder.

**Sorgulanabilir mi:** Doğrudan değil. "Şu sinaps şu ağırlıkta" diye sorgulanmaz. Sistemin **davranışı** bu hafızanın ifadesidir.

**Kim yazar:** Sadece sistemin kendisi (STDP + outcome + eligibility kuralları üzerinden, otomatik).

**Kim okur:** Observer (passive okuyucu). Başka hiç kimse dışarıdan yazamaz.

**Silinirse ne olur:** Sistem kimliğini kaybeder. Yeni doğum. Geri dönüşsüz.

**Persistans:** Sürekli yedeklenmeli (M0 snapshot). Bu yedek sistemin "ruh fotoğrafıdır".

---

### M1 — Observer Ledger

Sistemin **tarihinin kanıt defteri**.

**Ne saklar:** Hangi spike, hangi sinaps güncellemesi, hangi assembly olayı, hangi niyet, hangi gate engelleme, hangi recall, hangi outcome — her önemli iç olay.

**Yapı:** İki katmanlı.

**Fine-grain ring buffer:**

- Son N saniyenin (örn. 60sn) her event'i
- RAM'de döner
- Eski olanlar otomatik tasfiye olur
- "Anlık zihinsel iz" — kısa dönem inceleme için

**Coarse-grain permanent log:**

- Anlamlı eşik geçilen olaylar
- Append-only, **silinemez**
- Diskte, çoklu yedekli
- Sistemin uzun süreli tarihi

**Köprü mekaniği:** Bir olay coarse-grain log'a yazıldığı an, ilgili fine-grain pencere snapshot olarak kalıcılaşır. Yani önemli bir olay olduğunda öncesindeki 60sn'lik beyin akışı da kalıcı arşive geçer.

**Coarse-grain log'a giren tipik event'ler:**

- `SPIKE_BURST` (assembly başladı)
- `ASSEMBLY_CANDIDATE_BORN`
- `ASSEMBLY_STABILIZED`
- `ASSEMBLY_MERGED`
- `ASSEMBLY_SPLIT`
- `ASSEMBLY_SUPPRESSED`
- `ASSEMBLY_RECALLED`
- `ASSEMBLY_PROMOTED_TO_IDEA`
- `ASSEMBLY_DECAYED`
- `ASSEMBLY_PRUNED`
- `CONTRADICTION_PEAK`
- `INTENTION_FORMED`
- `INTENTION_SUPPRESSED`
- `DEONTIC_BLOCKED`
- `DEONTIC_BYPASS_ATTEMPT`
- `RECALL_REQUEST_SENT`
- `RECALL_EVENT_INGESTED`
- `OUTCOME_RECEIVED`
- `WAKE_TO_SLEEP_TRANSITION`
- `SLEEP_TO_WAKE_TRANSITION`
- `REPLAY_SESSION_COMPLETED`
- `SELF_GENESIS` (bir kez, doğumda)

**Kim yazar:** Sadece sistemin kendisi. Observer **dinler ve yazar**, sormaz, müdahale etmez.

**Kim okur:** İnsanlar (audit için), LLM tercüman (rapor için), explicit memory adapter (özet üretmek için).

**Silinirse ne olur:** Tarih kaybı. Sistem yaşar ama denetim ölür. **Yapılmaz.** Yedekleme sürekli ve dağıtık olmalı.

---

### M2 — Explicit Recall Store

Dış **hafıza organı**.

**Ne saklar:**

- Episodic kayıtlar — "Halit 18 Mayıs'ta kill-switch çekti"
- Structured facts — "şu eşik şu tarihte değişti"
- Procedural lookup'lar — "şu adapter şu yeteneklere sahip"
- Incident kayıtları
- İnsan kararlarının izleri
- Deontic geçmişi
- World facts (market sembolleri, kategoriler vs.)

**Yapı:** Standart bir veri katmanı (PostgreSQL veya MSSQL — daha sonra karar). Sorgulanabilir, indekslenebilir, versiyonlanabilir.

**Kim yazar:**

- **İnsan** (direct write — örn. "şu rule'u ekle")
- **Observer** (snapshot/extract üretip yazar — yarı otomatik)
- **System** (gate'ten geçen `memory_write_intention` üzerinden — dolaylı, denetimli)

**Çekirdek doğrudan M2'ye yazar mı:** **Hayır.** Çekirdek sadece "şu örüntüyü pekiştir" gibi bir niyet üretebilir. Bu niyet `memory_write_gate`'e tabidir, geçerse observer aracılığıyla M2'ye işlenir.

#### Recall akışı (M2 → çekirdek)

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

#### RecallEvent şeması

```
RecallEvent
├── memory_type: episodic | structured | procedural | incident
├── content: <opaque payload, çekirdeğin nasıl payload'a çevireceği ingress compiler kuralında>
├── source: M2 adapter id
├── original_timestamp: kayıt anı
├── retrieval_timestamp: hatırlatma anı
├── confidence: 0.0 - 1.0
├── ttl_ms: bu hatırlatmanın geçerlilik süresi
├── provenance: kayıt kim/ne tarafından oluşturuldu
├── contradiction_risk: bu hatırlatma mevcut state ile çelişebilir mi?
└── raw_ref: M2'deki orijinal kaydın id'si
```

**Önemli kural:** RecallEvent gerçek değildir, kaynaklı gözlemdir. Çekirdek bunu otomatik kabul etmez; diğer duyusal eventler gibi yorumlar, çelişki/güven testlerine tabi tutar.

**Silinirse ne olur:** Belirli bilgiler kaybedilir. Kimlik etkilenmez. Çekirdek yine düşünür, sadece o spesifik kayıtları hatırlamaz.

---

### M3 — Translator Memory

LLM'in **konuşma bağlamı**.

**Ne saklar:**

- Son konuşmalar
- Halit'in ifade biçimi
- Açıklama tercihleri
- Dilsel süreklilik
- Telegram konuşma geçmişi

**Kim yazar:** LLM (her konuşmada).

**Çekirdeğe etkisi:** **Hiçbir.** M3 silinse bile çekirdek aynıdır. M3 dolu olsa bile çekirdek bu içeriği doğrudan göremez.

**TTL:** Her kayıt birkaç gün – birkaç hafta sonra otomatik silinir.

**Silinirse ne olur:** Sadece konuşma tarzı sıfırlanır. Çekirdeğin karakteri dokunulmaz.

---

## Unutma fizyonu

Her katmanın kendi forgetting mekaniği vardır:

| Katman | Unutma mekanizması | Geri alınabilir? |
|--------|---------------------|--------------------|
| M0 | Doğal sönüm: weight decay, eligibility çürüme, dormant prune | Hayır (dokuya yazılı) |
| M1 | Ring buffer otomatik tasfiye; coarse-grain log **silinmez** | Ring buffer hayır, log dokunulmaz |
| M2 | Retention policy, `expires_at`, `staleness_threshold` | Backup'tan evet |
| M3 | TTL bazlı otomatik silme | Hayır (kasıtlı geçicilik) |

### Kritik kural

> **Silmek ≠ unutmak.**

Observer her silme olayını kendisi kayda alır. "Şu memory kaydı şu tarihte expire oldu" diye M1'de bir iz kalır. Sistemin tarihinde **unutmanın kendisi de hatırlanır**.

---

## Kimlik-hafıza hiyerarşisi

| Katman | Silinirse kimlik durumu | Yedekleme önceliği |
|--------|--------------------------|---------------------|
| M0 | Tam kimlik kaybı, yeni doğum | En yüksek, sürekli, dağıtık |
| M1 | Benlik var ama tarih yok | Çok yüksek, çoklu kopya |
| M2 | Bilgi eksilir, kimlik korunur | Standart DB backup |
| M3 | Konuşma tarzı sıfırlanır, kimlik dokunulmaz | Yedeklenmek zorunda değil |

---

## Recall ekonomisi

Sınırsız recall yapılırsa sistem **pathological rumination**'a girer — geçmişe boğulur, şimdiyi yaşayamaz. Bu yüzden her recall'un bir maliyeti vardır.

### Enerji bedeli

Her `RecallRequest` homeostatic stability'yi geçici olarak düşürür. Çok recall = sistem yoruluyor (fatigue accumulation).

### Cooldown

Aynı `RecallRequest` peşpeşe yapılamaz; her recall tipi için bir refractory period vardır.

### Habituation

Aynı hatırlatma tekrar tekrar gelirse etkisi azalır. Aynı `RecallEvent` 5. kez geldiğinde 1.'ye göre çok daha düşük payload intensity üretir.

Bu maliyetler self-field tarafından "hissedilir"; sistem kendi kendine recall fırtınasına girmez.

---

## M0 → M2 ters yön (memory write intention)

Çekirdek kendi sinaps deseninden öğrendiği bir şeyi explicit memory'ye yazdırmak isteyebilir: "bu örüntü artık kalıcı bilgi olsun." Bu niyet doğrudur ama doğrudan write yetkisi verilemez.

### Akış

```
Çekirdek bir memory_write intention üretir
    ↓
memory_write_gate (deontic gate'in alt-türü) kontrol eder
    ↓
Gate geçerse observer aracılığıyla M2'ye yazılır
    ↓
Yazma olayı M1'e de kaydedilir (audit trail)
```

Bu sayede çekirdek kendi narrative self'ini manipüle ederek **self-deception** yapamaz. Denetim katmanı her zaman arada.

---

## Yetki matrisi

Kim hangi katmana ne yapabilir?

|  | M0 | M1 | M2 | M3 |
|---|----|----|----|-----|
| Çekirdek (kendi) | evet (auto) | evet (auto write) | hayır (sadece intention) | hayır |
| Observer | hayır | evet (yazıcı) | yardımcı (snapshot/extract) | hayır |
| Explicit memory adapter | hayır | evet (kendi events) | evet | hayır |
| LLM translator | hayır | hayır | hayır (sadece intent olarak) | evet |
| İnsan | hayır (doğrudan) | hayır | evet | evet |

**Hiç kimse M0'a doğrudan yazamaz.** Sadece sistem kendi öğrenme kurallarıyla yazar.

---

## İlk yapılacaklar (yine kod değil)

Bu MEMORY_CONTRACT'ın hayata geçirilmesi için ileride yazılacak ama henüz yazılmamış belgeler:

- `RECALL_PROTOCOL.md` — `RecallRequest`/`RecallEvent` şemalarının tam spec'i
- `OBSERVER_LEDGER_SCHEMA.md` — ring buffer + permanent log event tipleri
- `MEMORY_WRITE_GATE.md` — deontic gate'in memory-yazma alt-türü
- `BACKUP_STRATEGY.md` — M0/M1 yedekleme planı, RPO/RTO hedefleri
- `INGRESS_COMPILER_SPEC.md` — duyusal eventlerin payload'a çevrilme kuralları

Bu listenin sırası B (Attention) ve C (World Model) konuşmalarına göre değişebilir.

---

## Versiyon

- **v1.0** — 18 Mayıs 2026 — İlk yazım. M0-M3 sabitlendi.
- Bu belgenin yazılması `CONSTITUTION.md` Madde 7'nin uzantısıdır.
