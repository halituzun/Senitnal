# 0008 — Recall Protocol

> Bu dosya `RECALL_PROTOCOL.md` (v0.1) ortaya çıkmadan önce yapılan üçlü
> tasarım konuşmasının (Halit + Claude + ChatGPT) sıkıştırılmış özetidir. H
> turunun kararlarının soyağacı.
>
> A: [`0001-neural-core-genesis.md`](./0001-neural-core-genesis.md)
> B: [`0002-attention-workspace.md`](./0002-attention-workspace.md)
> C: [`0003-world-ingress.md`](./0003-world-ingress.md)
> D: [`0004-bootstrap-genome.md`](./0004-bootstrap-genome.md)
> E: [`0005-deontic-gate.md`](./0005-deontic-gate.md)
> F: [`0006-observer-ledger-schema.md`](./0006-observer-ledger-schema.md)
> G: [`0007-memory-write-gate.md`](./0007-memory-write-gate.md)

---

## Tarih
2026-05-18 (G → H geçişi)

## Bağlam
A-G kapanmış. G `MEMORY_WRITE_GATE` M2'ye yazma kapısını tanımladı. H bunun **çift kapısı**: M2'den çekirdeğe okuma yolu.

```
G:  M0 / observer / human / replay → M2 (yazma)
H:  M2 → RecallEvent → World Ingress → neural_seed → core (okuma)
```

MEMORY_CONTRACT §5-6, WORLD_INGRESS §10-11, OBSERVER_LEDGER §16/§19'da dağınık recall kararları vardı; H bunları **tek tutarlı protokol** altında topladı + eksik kalanları doldurdu.

---

## Başlangıç pozisyonları

### ChatGPT (açılış manifestosu)
> *Recall Protocol, M2'deki explicit memory'nin çekirdeğe emir değil, kaynaklı hatırlatma olarak nasıl döndüğünü tanımlar.*

### Claude (açılış sertleştirmeleri)
1. **5 candidate kaynağı, sadece core RecallEvent üretir** — summarizer/replay/human/LLM M2 okuyabilir ama çekirdeğe RecallEvent enjekte edemez
2. **Hybrid scope** — tam free search yanlış (gizli karar modülü), tam context-bound yanlış (confirmation bias), doğru: subject_class + status + context similarity + economy
3. **Multi-record tek event** — top-1 core-facing RecallEvent, alternates observer audit
4. **Quarantined recall yok** (G ile uyumlu)
5. **Recall failure → çekirdeğe payload basmaz**, M1 audit-only

Üç açılış çapası:
- RecallRequest kaynağı core-only mi?
- Scope hybrid mi?
- Multi-record tek event mi?

### ChatGPT ilk turu
ChatGPT üçüne de PASS verdi, beş sertleştirme ekledi:
- "Recall is not retrieval, recall is sensory ingress" anayasal cümle
- Status-based recall tablosu (verified/active/candidate/quarantined/rejected/expired/superseded)
- Recall economy H'nin kalbi (cost/cooldown/habituation + recall_budget)
- Recall failure event olmalı (`RECALL_RESULT_EMPTY`) ama çekirdeğe basmaz
- 15 kırmızı çizgi

İki açık soru bıraktı:
1. Candidate recall tamamen kapalı mı, dar koşulda açık mı?
2. Human-requested recall nasıl çalışır?

---

## Konuşmanın diyalektiği

### İkinci tur — Claude'un iki soruya cevabı

**Candidate recall:** Varsayılan kapalı, dar bir subject_class alt-kümesinde açık.
- ✅ Allowed: `source_trust`, `procedural` (düşük confidence, capped intensity, status_band:candidate explicit)
- ❌ Forbidden: `narrative_claim`, `causal_explanation`, `decision_rationale`, `episodic`, `structured_fact`, `incident` (self-deception riski yüksek; verified olmadan "şu oldu" gibi davranamaz)

Sebep: operational pattern adayları için düşük etkili recall faydalı; anlatı/iddia/gerçeklik için recall self-deception zinciri kurar.

**Human-requested recall:**
- İnsan'ın "şu kaydı hatırlat" talebi → LLM translator → `HumanIntentEvent`
- WORLD_INGRESS §11 deterministic compiler → neural_seed (memory_echo + curiosity-like)
- Çekirdek bu seed'i duyusal uyaran olarak yaşar
- Eğer `memory_echo` yükselirse → kendi RecallRequest'ini doğurur
- Aksi halde "alındı" olarak M1'de kayıtlı kalır ama recall olmaz

Kilit: çekirdek autonomous kalır, insan **tetikleyici** ama **doğrudan değil**.

Ayrıca: insan operasyonel audit (kill-switch geçmişini göster gibi) RecallEvent değil, M1 read kanalıdır (`M1_HUMAN_READ`).

### Üçüncü tur — ChatGPT "yaz"

ChatGPT iki cevabı kabul + 15 → 17 kırmızı çizgiye çıkardı:
- 16: Candidate recall sınırı
- 17: Human recall talebi doğrudan recall değildir

Recall failure event önerisi `RECALL_NOT_FOUND` yerine `RECALL_RESULT_EMPTY` (daha esnek, status/economy/scope nedenlerini kapsar). Reasons:
- no_matching_record
- all_matches_quarantined
- all_matches_expired
- recall_budget_exhausted
- cooldown_active
- scope_too_narrow

---

## Çekirdek kararlar (13 ana + 17 kırmızı çizgi)

### 13 ana karar
1. Recall retrieval değildir; sensory ingress'tir.
2. Çekirdek M2'yi doğrudan sorgulamaz.
3. RecallRequest sadece core-originated (memory_echo tension).
4. Summarizer/replay/human/LLM core'a RecallEvent enjekte edemez.
5. Recall scope hybrid (subject_class + status + context similarity + economy).
6. Scope dış dünya etiketi taşımaz.
7. Ranking delivery'dir, hakikat değil.
8. Multi-record sonuçta core'a top-1; alternates observer'da audit.
9. Quarantined/rejected/expired RecallEvent üretmez.
10. Candidate recall sadece source_trust ve procedural için, capped intensity.
11. İnsan recall talebi HumanIntentEvent → çekirdek kendi RecallRequest'i.
12. Operasyonel audit ayrı kanal (M1 human read), recall değil.
13. Recall failure M1'e yazılır; çekirdeğe yokluk payload'ı dönmez.

---

## Madde 7 yansıması — okuma yolu

A turunda Madde 7 hafıza ayrılığını kurdu. MEMORY_CONTRACT §5-6 recall flow + economy'yi tanımladı. WORLD_INGRESS §10 RecallEvent şemasını verdi. G `MEMORY_WRITE_GATE` yazma kapısını biçimselleştirdi. **H okuma kapısını biçimselleştirdi.**

İki gate çifti:
- **G (Memory Write Gate):** Epistemik fren — M2'ye ne yazılabilir?
- **H (Recall Protocol):** Sensory ingress — M2'den ne, nasıl, ne yoğunlukta gelir?

İkisi birlikte M2'nin tam yetki haritası.

---

## Önemli sertleştirmeler

### "Recall is not retrieval, recall is sensory ingress"
Bu anayasal cümle H'nin kalbi. Çekirdek M2'yi bilen/sorgulayan entity değil; M2'den gelen olayı **dış olay gibi** yaşıyor. Madde 7 koruması en üst seviyede.

### Sadece core-originated RecallRequest core-facing RecallEvent üretir
Summarizer, replay, human, LLM hepsi M2 okuyabilir ama çekirdeğe enjekte edemez. Yoksa M2 → çekirdek yolu **emir kanalı**na döner.

### Ranking is delivery, not truth
M2 search top-1 dönerse bu "en gerçek kayıt" değildir; "en alakalı teslim adayı"dır. Yargı yapılmıyor.

### Top-1 core, alternates observer
Multi-record sonuçta çekirdeğe **tek RecallEvent** dönüyor. Alternates observer'da kayıtlı (audit). Yoksa çekirdek "hangisi gerçek" diye seçim yapmak zorunda kalırdı — gizli karar modülü.

### Candidate recall dar kapı
Operational (source_trust, procedural) açık; narrative/causal/episodic/structured_fact **kapalı**. Self-deception zincirini engelleyen kritik sınır.

### Human-requested recall — tetikleyici, doğrudan değil
İnsan recall talebi HumanIntentEvent olarak girer, çekirdek **kendi memory_echo geriliminden** kendi RecallRequest'ini doğurur. Bu autonomy + transparency dengesi:
- Çekirdek "istemiyorum" diyebilir
- Sistem hangi sebeple istemediği görünür kalır (M1 audit)
- İnsan zorla recall bastıramaz (economy bypass yok)

### Operational audit ≠ recall
"Kill-switch geçmişini göster" gibi audit isteği `M1_HUMAN_READ` meta-event'idir, RecallEvent değildir. İki kanal karışmamalı.

### Recall failure çekirdeğe payload basmaz
Hiç kayıt bulunamazsa `RECALL_RESULT_EMPTY` M1'e yazılır, çekirdeğe "yokluk payload'ı" basılmaz. Eğer yokluk basıncı gerekirse dolaylı olarak self-field / contradiction tarafında doğal yaşanır (unresolved intention pressure).

---

## Yan güncellemeler (commit'in parçası)

- `MEMORY_CONTRACT.md` §5 (Recall Flow) — RECALL_PROTOCOL cross-ref
- `MEMORY_CONTRACT.md` §6 (Recall Economy) — RECALL_PROTOCOL §14 cross-ref
- `WORLD_INGRESS.md` §10 (RecallEvent Boundary) — RECALL_PROTOCOL cross-ref
- `OBSERVER_LEDGER_SCHEMA.md` §10 permanence_policy — `RECALL_RESULT_EMPTY` (permanent), `RECALL_SUPPRESSED` (ring_buffer_only) eklendi
- `OBSERVER_LEDGER_SCHEMA.md` §19 event catalog memory family — `RECALL_EVENT_INGESTED`, `RECALL_RESULT_EMPTY`, `RECALL_SUPPRESSED` eklendi
- `CONSTITUTION.md` Madde 7 — RECALL_PROTOCOL cross-ref
- `README.md` — RECALL_PROTOCOL tamamlanmış listesine, sıradakiden çıkarıldı

---

## Açık kalanlar (implementation'a devredildi)

- Kesin recall_threshold ve recall_pressure formülü
- base_ttl, refractory_period, cooldown sayısal değerleri
- M2 search engine (vector similarity, sql, hybrid)
- context_signature_similarity_band hesaplama
- alternates sayısı limiti
- subject_class_complexity recall_cost'a nasıl yansır
- RecallEvent sonrası outcome alignment tracking
- Concurrent RecallRequest handling
- Refresh policy — repeat habituation mı, "kritik sinyal" mi?

---

## Sıradaki

A + B + C + D + E + F + G + H kapandı. **Anayasa + evidence surface + M2 yazma kapısı + M2 okuma kapısı** zinciri tamam.

Sıradaki belgeler (operational specification fazı devamı):
- **`ADAPTER_MANIFEST_SPEC.md`** — uzuvların standart kontratı
- **`INGRESS_COMPILER_SPEC.md`** — neural_seed mapping numerics + bootstrap rules detail
- **`BACKUP_STRATEGY.md`** — M0/M1 yedekleme planı, RPO/RTO
- **`OBSERVER_LEDGER_NUMERICS.md`** — snapshot windows, sampling thresholds, segment sizes
- **`BOOTSTRAP_GENOME_NUMERICS.md`** — kesin genome parametreleri
- **`MEMORY_WRITE_GATE_NUMERICS.md`** — gate threshold'ları
- **`RECALL_PROTOCOL_NUMERICS.md`** — recall threshold'ları, TTL, cooldown periyotları
- **`REPLAY_PROTOCOL.md`** — sleep replay + attention replay detay

---

## Kilit cümleler

> **RecallEvent gerçek değildir. RecallEvent kaynaklı hatırlatmadır.**
>
> **Recall is not retrieval. Recall is sensory ingress.**
>
> **Hafıza çekirdeğe emir vermez. Hafıza çekirdeğe hatırlatma gönderir.**
>
> **Recall ranking truth ranking değildir. Recall ranking delivery ranking'dir.**
>
> **Recall geçmişi getirir, ama şimdiyi boğamaz.**
>
> **İnsan recall talebi tetikleyicidir, doğrudan recall değildir.**
>
> **Hatırlatma = core-facing RecallEvent. Audit okuma = human-facing M1 read. İkisi karışmamalı.**
>
> **Recall failure audit edilir. Çekirdeğe yokluk payload'ı basılmaz.**
