# 0006 — Observer Ledger Schema

> Bu dosya `OBSERVER_LEDGER_SCHEMA.md` (v0.1) ortaya çıkmadan önce yapılan üçlü
> tasarım konuşmasının (Halit + Claude + ChatGPT) sıkıştırılmış özetidir. F turunun
> kararlarının soyağacı.
>
> A: [`0001-neural-core-genesis.md`](./0001-neural-core-genesis.md)
> B: [`0002-attention-workspace.md`](./0002-attention-workspace.md)
> C: [`0003-world-ingress.md`](./0003-world-ingress.md)
> D: [`0004-bootstrap-genome.md`](./0004-bootstrap-genome.md)
> E: [`0005-deontic-gate.md`](./0005-deontic-gate.md)

---

## Tarih
2026-05-18 (E → F geçişi)

## Bağlam
A + B + C + D + E kapanmış. Sentinel'in **anayasal aşaması** bitti. F bu noktada başka bir tür belge:

- A-E = "Zihnin anayasası"
- F = "Zihnin kanıt yüzeyi"

F yeni bir kavram tanıtmıyor; A-E boyunca her belgenin **M1'e ürettiği ~40 event'i** ortak bir şema, yetki matrisi ve audit invariant'ı altında topluyor.

ChatGPT'nin sıralama önerisi: F → MEMORY_WRITE_GATE → RECALL_PROTOCOL → ADAPTER_MANIFEST → INGRESS_COMPILER → BACKUP_STRATEGY. Çünkü ledger şeması netleşmeden alt belgeler havada kalır.

---

## Başlangıç pozisyonları

### ChatGPT (açılış manifestosu)
> *Observer karar vermez. Observer düzeltmez. Observer engellemez. Observer sadece kanıtlar.*
>
> *M1 sistemin hafızası değil, sistemin tarihinin kanıt defteridir.*

22 bölümlü iskelet + 10 kırmızı çizgi + ortak event envelope önerisi.

### Claude (açılış sertleştirmeleri)
1. ObserverEventEnvelope **dört katmanlı** (audit / causal / event_body / integrity) — `payload` kafa karıştırır (payload_seed ile)
2. Event type vs field **anayasal disiplin** (B/C/E pattern'i tek kurala)
3. **Event families** kategorizasyon (runtime behavior class değil)
4. **Recorder / Summarizer ayrımı** — MEMORY_CONTRACT §11 açık sorusunu kapatıyor

Üç çapa:
- Dört envelope yapısı kabul mü?
- Observer dual-role çözümü yeterli mi (non-recursive meta-events ile)?
- Read permission matrix operasyonel mi (her okuma kaydı patlatır mı)?

---

## Konuşmanın diyalektiği

### İlk tur — ChatGPT yeni katkılar

ChatGPT Claude'un sertleştirmelerini kabul + kendi katkılarını ekledi:

- **Meta-event recording first-order only** (infinite recursion engellenir)
- **High-frequency internal read'ler batch meta-event** (M1_REPLAY_READ_BATCH)
- **Replay scope = purpose-scoped + causal-ref bounded** (domain-limited değil, daha esnek)
- **Sampling deterministic-only**, semantic importance sampling **yasak**
- **Compaction limits** — storage organization, içerik dokunulmaz, `LEDGER_COMPACTION_PERFORMED` event

### İkinci tur — Permanence Policy + Snapshot Window iki konusu

Claude iki son karar gerekli dedi:
1. **Permanence Policy 2D table + no-default + immutable** — observer karar vermez, kuralı uygular
2. **Snapshot Window Policy** — pre/post bands + full snapshot + rate-limited sampling

ChatGPT iki kararı da kabul + sertleştirme:
- **No event type may exist without an explicit permanence policy** (default yasak)
- **Persistence weakening is not a routine update** (permanent → ring_buffer_only yasak)
- **A permanent event may not outlive its required snapshot** (snapshot kaybı yasak)
- **Sampling risk açık tehlike olarak işaretlenmeli** (information loss şeffaf)
- `SnapshotRef` şemasına `trigger_event_id` ve `window_policy_ref` eklendi
- Replay scope hem domain hem causal-ref bounded (attention replay deontic blocked okuyabilir, kendi pulse'una bağlıysa)

### Üçüncü tur — ChatGPT "yaz"

ChatGPT son hüküm: **F belgeye dondurulabilir**. Üç sert kuralı koru:
1. Observer permanence seçmez; permanence_policy uygular
2. Snapshot filtrelemez; pencereyi korur
3. Sampling varsa deterministik ve açıkça kayıplı

---

## Çekirdek kararlar (14 ana + 6 family)

### 14 ana karar
1. Observer karar veremez; sadece kanıt kuralları uygular.
2. Observer M0'a yazamaz.
3. Observer deontic gate veya self-field gibi davranmaz.
4. Observer memory write approve edemez.
5. Recorder ve Summarizer yetkileri ayrıdır.
6. Summarizer M2'ye doğrudan yazamaz; Memory Write Gate'e candidate önerir.
7. Event type inflation yasak; statü değişimleri field'dır.
8. Permanent log append-only ve tamper-evident.
9. Permanence policy 2D table, no-default, immutable.
10. Snapshot pencereyi olduğu gibi alır; filtreleme yasak.
11. Sampling deterministic-only ve açıkça kayıplı.
12. Causal refs 1-hop direct only.
13. Meta-events first-order, non-recursive.
14. Compaction storage organization only; içerik korunur.

### 6 event family
- `neural`, `attention`, `memory`, `ingress`, `bootstrap`, `deontic`
- **Audit grouping**, runtime behavior class **değil**

---

## Madde 7 yansıması — kanıt yüzeyi seviyesi

A turunda Madde 7 hafıza ayrılığını kurdu (M0/M1/M2/M3). B/C/D/E her biri M1'e event üretti. F bu event'leri **tek tutarlı çerçeveye** oturttu.

Madde 7'nin "hafıza çekirdeğe emir vermez" kuralı F'de **"observer karar vermez"** olarak yansıyor. Audit katmanı kararı içermez — sadece kararı kayıt eder.

---

## Önemli sertleştirmeler

### "event_body" naming
ChatGPT ile birlikte karar: `payload` adı çekirdek tarafındaki `payload_seed` ile karışıyordu. `event_body` daha net.

> *`payload_seed` = çekirdeğe giren nöral tohum.*
> *`event_body` = observer kaydının içeriği.*

### Event type vs field anayasal kural
B'nin WORKSPACE_PULSE + dissonance field, C'nin SOURCE_TRUST_STATUS_CHANGED, E'nin DEONTIC_POLICY_STATUS_CHANGED disiplini F'de **anayasal mikro-prensip** oldu:

> *Ayrı event tipi sadece farklı nedensel mekanizma. Aynı mekanizmanın statü/değer değişimi field.*

### Recorder/Summarizer ayrımı MEMORY_CONTRACT §14 açık sorusunu kapatıyor
MEMORY_CONTRACT §14'teki "Observer dual-role" açık sorusu F'de **yapısal cevap** aldı:
- Recorder = M1 writer (passive, permanence_policy uygular)
- Summarizer = M1 reader + M2 candidate proposer (Memory Write Gate'ten geçer)
- Her summarizer hareketi M1'e meta-event olarak kayıtlı
- Meta-events first-order (non-recursive)

Detay implementation kuralları `MEMORY_WRITE_GATE.md` ve `OBSERVER_LEDGER_NUMERICS.md` konusu.

### No-default permanence
> *No event type may exist without an explicit permanence policy.*

Yeni event tipi eklenirken permanence policy de revize edilmek zorunda. Default yok — yanlışlıkla kritik event ring buffer'da kaybolmasın diye.

### Sampling: kayıplı + şeffaf
Rate-limited deterministic sampling **emergency storage tool**, **default değil**. Her sampled snapshot kayıp oranını kayıt eder. Semantic importance sampling **yasak**.

### Replay scope: purpose + causal-ref bounded
ChatGPT'nin gevşetmesi doğru. Attention replay sadece attention events okuyamaz — kendi pulse'una neden olan deontic block veya outcome event'lere de bakabilir. Ama keyfi full-ledger access yok.

---

## Yan güncellemeler (commit'in parçası)

- `CONSTITUTION.md` Madde 7 — OBSERVER_LEDGER_SCHEMA cross-ref
- `MEMORY_CONTRACT.md` M1 bölümü — OBSERVER_LEDGER_SCHEMA cross-ref
- `MEMORY_CONTRACT.md` §14 — "Observer dual-role" açık sorusu yapısal cevap aldı (F tarafından)
- `README.md` — OBSERVER_LEDGER_SCHEMA tamamlanmış listesine

---

## Açık kalanlar (sonraki belgelere devredildi)

- **Kesin window süreleri ve sampling threshold'ları** → `OBSERVER_LEDGER_NUMERICS.md` / implementation
- **Hash algoritması ve segment boyutu** → Implementation
- **Backup ve restore davranışı** → `BACKUP_STRATEGY.md`
- **Multi-instance ledger merge** → Cross-instance identity (MEMORY_CONTRACT §14)
- **Permanent log storage tier movement** → Implementation
- **Summarizer kuralları (hangi event kombinasyonları candidate üretir)** → `MEMORY_WRITE_GATE.md`

---

## Sıradaki

A + B + C + D + E + F kapandı. Sentinel'in **conceptual constitution + ledger schema** fazı bitti.

Sıradaki belgeler (operational specification fazı):
- **`MEMORY_WRITE_GATE.md`** — epistemic gate sayısal eşikler, summarizer candidate → verified kuralları
- **`RECALL_PROTOCOL.md`** — RecallRequest/RecallEvent şemalarının tam spec'i
- **`ADAPTER_MANIFEST_SPEC.md`** — uzuvların standart kontratı
- **`INGRESS_COMPILER_SPEC.md`** — bootstrap mapping detayı + sayısal katsayılar
- **`BACKUP_STRATEGY.md`** — M0/M1 yedekleme planı, RPO/RTO
- **`BOOTSTRAP_GENOME_NUMERICS.md`** — kesin genome parametreleri

ChatGPT'nin önerdiği sonraki sıra: **MEMORY_WRITE_GATE** (çünkü F'de summarizer ona candidate önerir, ama gate kuralı henüz yazılı değil).

---

## Kilit cümleler

> **Observer karar vermez. Observer düzeltmez. Observer engellemez. Observer sadece kanıtlar.**
>
> **M1 sistemin hafızası değil, sistemin tarihinin kanıt defteridir.**
>
> **Observer neyin önemli olduğuna karar vermez. Observer sadece önceden tanımlı kanıt kurallarını uygular.**
>
> **No event type may exist without an explicit permanence policy.**
>
> **Persistence weakening is not a routine update.**
>
> **A permanent event may not outlive its required snapshot.**
>
> **Compaction sadece storage organization'dır. Bilgi kaybı yapamaz.**
>
> **Observer lokal nedenselliği kaydeder. Replay uzak nedenselliği araştırır.**
