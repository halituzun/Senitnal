# 0007 — Memory Write Gate

> Bu dosya `MEMORY_WRITE_GATE.md` (v0.1) ortaya çıkmadan önce yapılan üçlü
> tasarım konuşmasının (Halit + Claude + ChatGPT) sıkıştırılmış özetidir. G
> turunun kararlarının soyağacı.
>
> A: [`0001-neural-core-genesis.md`](./0001-neural-core-genesis.md)
> B: [`0002-attention-workspace.md`](./0002-attention-workspace.md)
> C: [`0003-world-ingress.md`](./0003-world-ingress.md)
> D: [`0004-bootstrap-genome.md`](./0004-bootstrap-genome.md)
> E: [`0005-deontic-gate.md`](./0005-deontic-gate.md)
> F: [`0006-observer-ledger-schema.md`](./0006-observer-ledger-schema.md)

---

## Tarih
2026-05-18 (F → G geçişi)

## Bağlam
A + B + C + D + E + F kapanmış. **Anayasa katmanı + evidence surface** tamamlandı. G operational specification fazının ilk belgesi:

- MEMORY_CONTRACT §9 Memory Write Gate kavramını tanıttı ama detaylandırmadı
- F §5 summarizer'ın gate'e candidate önerdiğini söyledi ama gate kuralları yazılmadı
- DEONTIC_GATE §6 "Memory Write Gate epistemik risktir" dedi ama ne yaptığı eksik

G bu boşluğu doldurur — **gate'in karar kuralları, statü zinciri, evidence matrix, self-deception önleme**.

---

## Başlangıç pozisyonları

### ChatGPT (açılış manifestosu)
> *Memory Write Gate, sistemin kendi hikâyesine inanmasını engelleyen epistemik frendir.*
>
> *Deontic gate: "Bu eylem dünyaya çıkabilir mi?"*
> *Memory Write Gate: "Bu kayıt hafızaya gerçekmiş gibi yazılabilir mi?"*

5 candidate kaynağı, statü makinesi (quarantined dahil), 8 evidence ekseni, 12 kırmızı çizgi, 21 bölümlü iskelet.

### Claude (açılış sertleştirmeleri)
1. **Subject Class × Evidence Axes Matrix** — verification kriterleri tek üniversal AND değil, subject_class'a göre değişken
2. **Self-deception detection mekanik tanım** — `internal_only_refs` vs `external_corroboration_refs`
3. **Gate testleri boolean/sayısal**, yargı yok
4. **Quarantined statü çıkış yolları** (verified / rejected / expired / superseded)

Üç çapa:
- Matrix kabul mü?
- Self-deception mekanizması yeterince mekanik mi?
- Gate kendi kararından candidate üretemez kuralı doğru mu?

---

## Konuşmanın diyalektiği

### İlk tur — ChatGPT yeni katkılar

ChatGPT Claude'un üç çapasının cevabını verdi + sertleştirmeler ekledi:

- **Subject Class × Evidence Matrix kabul** — yeni subject_class eklemesi matrix satırı zorunlu
- **Self-deception detection** — `internal_only_refs` (neural/attention/memory/replay/summarizer/self-field events) vs `external_corroboration_refs` (ObservationEvent, Human direct, OutcomeReceived, verified non-system M2, signed artifact)
- **Gate kendi kararından candidate üretemez** — yoksa self-reinforcement döngüsü
- **Quarantined non-terminal** — bekleme alanı, çıkış yolları var
- **Verified geçişi anlık, retroaktif değil** — "Verification does not rewrite history"
- **Event tipi sertleştirmesi** — `MEMORY_RECORD_STATUS_CHANGED` canonical event (B/C/E/F disiplini), eski PASSED/REJECTED/VERIFIED/QUARANTINED ayrı event tipleri olmaz
- **Human write iki kategori** — auto-verified (bootstrap_reference, signed_admin) vs matrix-required (diğerleri)

### İkinci tur — Claude sertleştirmeler + silent gate

Claude iki sorunun cevabını verdi + bir kritik sertleştirme ekledi:

1. **MEMORY_RECORD_STATUS_CHANGED canonical** kabul. `MEMORY_WRITE_PROPOSED` ayrı kalır (candidate doğumu). F event catalog patch'i gerek.

2. **Human write kategorileri detaylandı**:
   - Auto-verified: bootstrap_reference, signed_administrative_reference, **operator_decision_record**, **incident_human_record**, **deontic_kill_switch_action_record**
   - Matrix-required: structured_fact, procedural, narrative_claim, causal_explanation, source_trust
   
   Ayrım: *"Halit yazdı ≠ Halit doğru söylüyor. Halit yazdı = Halit'in beyanı kayda geçti."* İnsan kendi eylemini kayda geçirir → fact. İnsan dünya hakkında iddia ederse → matrix.

3. **YENİ — Silent Gate sertleştirmesi**: Memory Write Gate kararları çekirdeğe **geri yansımaz**. Deontic gate kritik bloklarda `InternalShockEvent` üretir; Memory Write Gate'te bu **yoktur**. Sebep:
   - Action-risk = dünyaya etkili, sistem öğrenmeli
   - Epistemic-risk = kendi anlatısı, gate'in işi sessizce filtrelemek
   - Reject çekirdeğe yansısa, gate dolaylı öğretici modüle dönüşür — karar modülü tehlikesinin yeni hali

### Üçüncü tur — ChatGPT "yaz"

ChatGPT son hüküm:
- Silent gate sertleştirmesi G'nin ruhuna tam oturuyor
- 17. kırmızı çizgi olarak eklensin
- F event catalog patch'i ve permanence_policy güncellemesi yan iş

---

## Çekirdek kararlar (13 ana + 17 kırmızı çizgi)

### 13 ana karar
1. Memory Write Gate deontic gate'in alt türü **değildir**.
2. Gate hakikat üretmez; hakikat iddiasını statülendirir.
3. **Gate sessizdir** — kararları çekirdeğe geri yansımaz.
4. Verification matrix subject_class'a göre değişken.
5. Matrix satırı olmayan subject_class verified olamaz.
6. Statü makinesi: candidate → verified → active → superseded; quarantined ve rejected yan yollar; expired terminal.
7. Verified geçişi anlık, retroaktif değil.
8. Pulse/recall repetition evidence değildir.
9. Self-deception detection mekanik (event family + provenance + refs).
10. İnsan eylem kaydı auto-verified; insan dünya iddiası matrix-required.
11. Tek canonical event: MEMORY_RECORD_STATUS_CHANGED.
12. Gate testleri boolean/sayısal; yargı yok.
13. Gate kendi kararından candidate üretemez; pattern öğrenme summarizer üzerinden.

---

## Madde 7 yansıması — M2 yazma kapısı seviyesi

A turunda Madde 7 hafıza ayrılığını kurdu. MEMORY_CONTRACT §9'da Memory Write Gate kavramı geldi. F'de summarizer-as-candidate-proposer rolü tanımlandı. **G turunda gate'in karar kuralları biçimselleşti.**

Bu zincir: hafıza ayrılığı → M2 yazma niyeti → epistemic gate karar kuralları → silent feedback. Madde 7'nin "hafıza çekirdeğe emir vermez" prensibinin yansıması:

- Çekirdek M2'ye doğrudan yazamaz (Madde 7)
- M2 candidate'lar gate'ten geçer (MEMORY_CONTRACT §9)
- Gate sessizdir, çekirdeğe geri yansımaz (G §5)

---

## Önemli sertleştirmeler

### "Silent Gate" — G'nin en büyük katkısı
Bu tur boyunca ortaya çıkan en kritik sertleştirme. Deontic gate kritik bloklarda InternalShockEvent ile çekirdeğe yansır (öğrenme); Memory Write Gate'te bu **yoktur**.

Sebep: epistemic-risk = sistemin kendi anlatısı. Eğer gate "reject" sonucu çekirdeğe payload_seed olarak yansısa, gate dolaylı şekilde sisteme **şu tip iddiada bulunma** dersini verir — karar modülü tehlikesinin başka bir hali. Doğru: sessiz filtreleme + audit.

### Subject Class × Evidence Axes Matrix
ChatGPT'nin "tek üniversal AND" yerine subject_class'a göre değişken matrix kararı. Source_trust outcome misalignment pattern'i ister; episodic causal_refs ister; structured_fact cross-source corroboration ister. Bu farklılık matrix ile yazılır.

Yeni subject_class eklenirse matrix satırı zorunlu — "ileride biri `subject_class = strategy_belief` eklesin ama gate ne yapacağını bilemesin" açığı kapatıldı.

### Self-deception detection mekanik tanım
"Self-explanation is not proof" prensibi `internal_only_refs` vs `external_corroboration_refs` ayrımı ile mekanik test'e dönüştü:

```
self_deception_risk = HIGH when:
    candidate.subject_class IN {narrative_claim, causal_explanation, decision_rationale}
    AND evidence_refs ⊆ internal_only_refs
    AND external_corroboration_refs is empty
```

Gate yargı yapmıyor; sadece event family + provenance + refs boyutlarına bakıyor.

### Human write iki kategori
İnsanın kendi eyleminin kaydı (auto-verified) ile dünya hakkında iddiası (matrix-required) ayrımı. Bu MEMORY_CONTRACT §10'daki "provenance: human" prensibinin alt-sınıflandırması.

> *Halit yazdı ≠ Halit doğru söylüyor.*

### MEMORY_RECORD_STATUS_CHANGED canonical
B/C/E/F disiplinin devamı. `MEMORY_WRITE_PROPOSED` ayrı kalır (candidate doğumu), statü transitions `MEMORY_RECORD_STATUS_CHANGED` altında. F event catalog patch'i alındı.

### Verification anlık, retroaktif değil
> *Verification does not rewrite history.*

Audit invariant'ı korumak için kritik. Eski recall'lar o zamanki statüyle kaldı; sonraki recall'lar verified gücünde gelir.

### Gate testleri boolean/sayısal
Yargı yok, deterministic test. "Bu kayıt mantıklı görünüyor" yasak; `evidence_refs.length >= min_evidence_count` allowed.

---

## Yan güncellemeler (commit'in parçası)

- `MEMORY_CONTRACT.md` §9 — MEMORY_WRITE_GATE cross-ref + "deontic alt-türü değildir" netleştirme
- `OBSERVER_LEDGER_SCHEMA.md` §10 (permanence_policy) — eski MEMORY_WRITE_GATE_PASSED/REJECTED satırları MEMORY_RECORD_STATUS_CHANGED ile değiştirildi; quarantined/HIGH_self_deception için permanent_with_snapshot
- `OBSERVER_LEDGER_SCHEMA.md` §19 (event catalog memory family) — eski event tipleri MEMORY_RECORD_STATUS_CHANGED altına alındı
- `CONSTITUTION.md` Madde 7 — MEMORY_WRITE_GATE cross-ref
- `README.md` — MEMORY_WRITE_GATE tamamlanmış listesine, sıradaki listeden çıkarıldı

---

## Açık kalanlar (sonraki belgelere devredildi)

- Kesin sayısal eşikler → `MEMORY_WRITE_GATE_NUMERICS.md` / implementation
- Subject_class matrix versioning (eski candidate'lar matrix değişimine ne tepki verir)
- Replay survival score hesaplama → `REPLAY_PROTOCOL.md` (henüz yok)
- Outcome alignment metric → Implementation
- Cross-source corroboration tanımı (source ayrımı nasıl yapılır)
- Quarantine re-validation cadansı
- Verified_max_age — hangi subject_class için verified süre dolar?

---

## Sıradaki

A + B + C + D + E + F + G kapandı. **Anayasa + evidence surface + epistemic gate** zinciri tamam.

Sıradaki belgeler (operational specification fazı devamı):
- **`RECALL_PROTOCOL.md`** — RecallRequest/RecallEvent şemalarının tam spec'i
- **`ADAPTER_MANIFEST_SPEC.md`** — uzuvların standart kontratı
- **`INGRESS_COMPILER_SPEC.md`** — neural_seed mapping numerics + bootstrap rules detail
- **`BACKUP_STRATEGY.md`** — M0/M1 yedekleme planı, RPO/RTO
- **`OBSERVER_LEDGER_NUMERICS.md`** — snapshot windows, sampling thresholds, segment sizes
- **`BOOTSTRAP_GENOME_NUMERICS.md`** — kesin genome parametreleri
- **`MEMORY_WRITE_GATE_NUMERICS.md`** — gate threshold'ları, candidate_max_age, quarantine_max_age
- **`REPLAY_PROTOCOL.md`** — sleep replay + attention replay detay

ChatGPT'nin sıralama önerisi: **RECALL_PROTOCOL.md** (M2 → çekirdek yolu, A turundan kalan açık spec).

---

## Kilit cümleler

> **Memory Write Gate, sistemin kendi hikâyesine inanmasını engelleyen epistemik frendir.**
>
> **Memory Write Gate hakikat üretmez. Memory Write Gate hafızaya yazılacak hakikat iddiasını statülendirir.**
>
> **Deontic gate eylem riskini sınırlar. Memory Write Gate epistemik riski sınırlar.**
>
> **Sistemin kendi açıklaması kanıt değildir. Kayıt olabilir, ama verified fact değildir.**
>
> **Memory Write Gate is silent: rejections, quarantines, and verifications do not echo into the core.**
>
> **Verification does not rewrite history.**
>
> **Halit yazdı ≠ Halit doğru söylüyor. Halit yazdı = Halit'in beyanı kayda geçti.**
>
> **Repeated attention is not evidence. Repeated recall is not evidence. Repeated assertion is not evidence.**
