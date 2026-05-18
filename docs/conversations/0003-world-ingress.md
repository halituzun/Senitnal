# 0003 — World Ingress

> Bu dosya `WORLD_INGRESS.md` (v0.1) ortaya çıkmadan önce yapılan üçlü tasarım
> konuşmasının (Halit + Claude + ChatGPT) sıkıştırılmış özetidir. C turunun
> kararlarının soyağacı.
>
> A turu: [`0001-neural-core-genesis.md`](./0001-neural-core-genesis.md)
> B turu: [`0002-attention-workspace.md`](./0002-attention-workspace.md)

---

## Tarih
2026-05-18 (B → C geçişi)

## Başlangıç pozisyonları

### ChatGPT (açılış)
> *World model = dış eventlerin çekirdekte oluşturduğu stabil neural overlay + observer tarafından izlenebilir structured provenance.*
>
> Üç katman:
> - **Dışarıda:** structured observation
> - **İçeride:** payload seed + assembly activation + nöral iz
> - **Observer'da:** provenance

5 gerilim masaya yatırıldı:
1. World model çekirdeğin içinde mi, dışında mı?
2. Semi-structured event nerede biter, neural overlay nerede başlar?
3. Ingress compiler sabit kural mı, öğrenen katman mı?
4. Dış dünya etiketi context_signature'a sızmadan nasıl temsil edilir?
5. World facts, RecallEvent ve ObservationEvent arasındaki sınır nedir?

### Claude (açılış soruları)
Gizli tuzak tespiti: **"model" kelimesi tehlikeli**. Belge adı `WORLD_INGRESS.md` olmalı.

Üç çapa:
1. İsim değişikliği mantıklı mı?
2. Learned mappings M0 alt-tipi mi?
3. HumanIntentEvent aynı compiler'dan geçmek Madde 6 ile çelişir mi?

---

## Konuşmanın diyalektiği

İlk turda ChatGPT şu sağlam pozisyonları ekledi:
- **Dosya adı:** WORLD_INGRESS.md (model kelimesi tehlikeli, "WORLD_TRACE soyut, EXTERNAL_INGRESS çok geniş")
- **Hibrit yapı:** statik facts M2'de, anlık akış ObservationEvent
- **Üç ingress profile** farkı (Observation/Recall/HumanIntent için yetki farklı)
- **Provenance üç katmanı**: audit / compilation / inside_core
- **InternalShockEvent C'nin de parçası** — B'de tanımlandı, C'de yerleşir
- **M0 alt-türleme açık tanım** — sinaps / assembly / self-field / attention / ingress calibration

Claude muhalefeti ve sertleştirmeleri:
- **Source identity M0'a girmez** — `source_id` çekirdek hafızasına dönüşmemeli. `source_reliability_band` skaler compiler input olabilir.
- **`criticality_band` tek başına `urgency`'ye map edilmez** — kombinasyon ile yorumlanır
- **`coherence_with_recent` global olmalı, source-spesifik değil** — yoksa Madde 1 sızıntısı
- **event_profile compiler ve observer görür, core görmez** — C'nin kalbi

ChatGPT'nin sertleştirmeleri:
- **SourceTrustRecord M2 alt-tipi** olmalı (yeni katman değil)
- **`volatility_normalized` → `instability_normalized`** (finans kokusu çıktı, ileride genel kullanım)
- **`action_origin_ref` observer-only**; compiler'a sadece soyut etkiler (`has_action_origin`, `expected_feedback_score`, `feedback_delay_ms`)
- **Ortak `IngressEventEnvelope`** yapısı — dört event class aynı temel zarfı paylaşır
- **HumanIntentEvent learned_mappings KAPALI** — LLM dolaylı mapping öğrenmesin
- **InternalShockEvent learned_mappings KAPALI** — gate şoku güçlenmesin

---

## Çekirdek kararlar (14 + 2 özel)

1. **Sentinel'in world model'i yoktur**; world ingress yolu vardır.
2. Dünya çekirdeğe gerçek olarak girmez; kaynaklı gözlem olarak girer.
3. Dış dünyayı içeride structured fact olarak saklamayız.
4. Kalıcı facts M2'de yaşar; çekirdeğe `RecallEvent` olarak döner.
5. Anlık akış `ObservationEvent` olarak gelir.
6. İnsan niyeti `HumanIntentEvent` olarak gelir (Madde 6'ya tabi).
7. Kritik deontic blok `InternalShockEvent` olarak gelir (Madde 5'ten).
8. Tüm ingress event'leri deterministic ingress boundary'den geçer.
9. **Event profile observer + compiler tarafından bilinir; çekirdek tarafından bilinmez.** ← C'nin kalbi
10. Compiler output kategori değil, **payload_seed**.
11. ObservationEvent + RecallEvent learned_mappings kullanabilir; HumanIntentEvent + InternalShockEvent kullanamaz.
12. Provenance observer'da isim olarak yaşar; çekirdekte sadece güven/tazelik/sürpriz etkisi olarak yaşar.
13. `learned_mappings` M0 ingress calibration trace olarak yaşar; config değildir.
14. Çoklu source pre-merge edilmez; ayrı compile edilir, çelişki çekirdekte yaşanır.

### Ek özel kurallar
- **`SourceTrustRecord` M2 alt-tipi** (subject_class = "source_trust"), yeni katman değildir.
- **Dedup allowed, aggregation forbidden.**

---

## Önemli sertleştirmeler

### "World model" → "World ingress" isim değişikliği
"Model" kelimesi "dünya içeride tutuluyor" çağrışımı yapıyor. Doğru olan: **dünya dışarıda kalır, sistem sadece yansımalarını yaşar**. Belge adı `WORLD_INGRESS.md`, içerikte sertçe "world model yok" cümlesi.

### Madde 1 yansıması — ingress seviyesi
A turunda Madde 1 nöron seviyesinde, B turunda pulse seviyesinde uygulandı. C'de **ingress kanalları seviyesinde**:
- Tek mekanizma (deterministic compiler), farklı imza (event_profile yetki matrisi)
- Çekirdeğe domain etiketi sızmaz (subject_id, source_id, venue → observer_only)
- Compiler kategori üretmez, payload_seed üretir

### Action_origin observer'a tam, compiler'a soyut
İnsan beyninde "efference copy" — sistem kendi eyleminin sonuçlarını bilmeli. Ama `order_id` çekirdeğe sızmamalı. Çözüm: `action_origin_ref` observer'da, compiler'a `has_action_origin` + `expected_feedback_score` + `feedback_delay_ms` soyut etkileri.

> *Çekirdek `order_id`'sini bilmez. Sadece "kendi eyleminden beklenmedik feedback" tonunu yaşar.*

### SourceTrustRecord epistemik gate'e bağlı
Sistem kaynaklı reliability değişimleri **Memory Write Gate**'e tabi (epistemic risk). MEMORY_CONTRACT §10'daki CandidateMemoryRecord statü zinciri aynen kullanılır.

> *Kaynak kimliği dış kanıttır. Güven bandı compiler girdisidir. Kaynak adı çekirdek hafızasına dönüşmez.*

---

## Yan güncellemeler (commit'in parçası)

- `CONSTITUTION.md` Madde 6 — `HumanIntentEvent` ingress için WORLD_INGRESS §11 cross-ref
- `CONSTITUTION.md` Madde 7 — `RecallEvent` ingress için WORLD_INGRESS §10 cross-ref
- `MEMORY_CONTRACT.md` M2 — `subject_class` alt-türleme, SourceTrustRecord örneği
- `README.md` — Tamamlanmış'a WORLD_INGRESS eklendi, sıradaki listeden çıktı

---

## Açık kalanlar (sonraki belgelere devredildi)

- Bootstrap mapping sayısal parametreleri → `BOOTSTRAP_GENOME.md`, `INGRESS_COMPILER_SPEC.md`
- Adapter manifest formatı → `ADAPTER_MANIFEST_SPEC.md`
- InternalShockEvent payload_seed magnitudes → `DEONTIC_GATE.md`, `BOOTSTRAP_GENOME.md`
- Multi-source conflict resolution time scale → ATTENTION_WORKSPACE §22 açık sorularla bağlantılı
- SourceTrustRecord migration → MEMORY_CONTRACT §14 schema versioning
- Learned mapping rate limiting → input layer stability sorusu

---

## Sıradaki

A + B + C kapandı. Sentinel'in **kavramsal çekirdeği** dondurulmuş üç anayasa belgesinde yaşıyor:
- `CONSTITUTION.md` — 7 madde
- `MEMORY_CONTRACT.md` — hafıza sınırı
- `ATTENTION_WORKSPACE.md` — dikkat alt-spec'i
- `WORLD_INGRESS.md` — dış dünya giriş sınırı

Sıradaki ana belgeler (henüz açılmadı):
- `BOOTSTRAP_GENOME.md` — sistem doğduğunda elinde ne var? (üç belgenin de gönderdiği açık sorular burada birleşiyor)
- `DEONTIC_GATE.md` — kategorik action-risk kısıtlarının biçimsel listesi
- `RECALL_PROTOCOL.md` — recall şema detayı
- `OBSERVER_LEDGER_SCHEMA.md` — ledger event tipleri
- `MEMORY_WRITE_GATE.md` — epistemic gate sayısal eşikler
- `ADAPTER_MANIFEST_SPEC.md` — uzuvların standart kontratı
- `INGRESS_COMPILER_SPEC.md` — bootstrap mapping detayı
- `BACKUP_STRATEGY.md` — M0/M1 yedekleme planı

---

## Kilit cümleler

> **Dünya çekirdeğe gerçek olarak girmez. Dünya kaynaklı gözlem olarak gelir. Çekirdekte sadece nöral iz olarak yaşar.**
>
> **Compiler kategori üretmez. Compiler zihinsel renk tohumu üretir.**
>
> **LLM niyet ailesi söyler. Compiler tonu belirler. Core sadece tonu yaşar.**
>
> **Ingress mapping config değildir. Ingress mapping dokudur.**
>
> **Event profile observer ve compiler tarafından bilinir, core tarafından bilinmez.**
