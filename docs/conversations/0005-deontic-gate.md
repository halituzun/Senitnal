# 0005 — Deontic Gate

> Bu dosya `DEONTIC_GATE.md` (v0.1) ortaya çıkmadan önce yapılan üçlü tasarım
> konuşmasının (Halit + Claude + ChatGPT) sıkıştırılmış özetidir. E turunun
> kararlarının soyağacı.
>
> A turu: [`0001-neural-core-genesis.md`](./0001-neural-core-genesis.md)
> B turu: [`0002-attention-workspace.md`](./0002-attention-workspace.md)
> C turu: [`0003-world-ingress.md`](./0003-world-ingress.md)
> D turu: [`0004-bootstrap-genome.md`](./0004-bootstrap-genome.md)

---

## Tarih
2026-05-18 (D → E geçişi)

## Bağlam
A + B + C + D kapanmış halde. Sentinel'in kavramsal mimarisi ve doğum anayasası dondurulmuş. Önceki dört belge hepsi **deontic gate'e referans veriyor** ama kategorik kuralların kendisi henüz yazılmamış:

- CONSTITUTION Madde 5 deontic gate'i ana hatlarıyla tanımlar
- ATTENTION_WORKSPACE §18 "kritik deontic block" der ama listeyi vermez
- WORLD_INGRESS §12 InternalShockEvent ingress'i tanımlar ama tetikleyici kuralları vermez
- BOOTSTRAP_GENOME §8 "deontic gate ref" der, içeriği vermez

E turu bu **dört belgenin action-side sınırını** çiziyor.

---

## Başlangıç pozisyonları

### ChatGPT (açılış)
> *Deontic gate iki parçaya ayrılmalı: Constitutional hard-stops + Operational hard-stops.*

Constitutional = anayasal yasaklar, belge revizyonu ile değişir.
Operational = pratik güvenlik eşikleri, signed policy artifact ile güncellenebilir.

### Claude (açılış sertleştirmeleri)
1. Operational policy artifact = M2 alt-tipi (DeonticPolicyRecord, subject_class = "deontic_policy")
2. Block classification = routine / safety / constitutional (3 bant)
3. Bypass attempt mekaniği netleştirilmeli — DEONTIC_BYPASS_ATTEMPT formal şema
4. Kill-switch özel statüsü — eylem çıkışı tamamen kapanır, düşünce devam eder

Yapısal soru: Deontic proximity → action_boundary_pressure mekaniği nasıl çalışır?

---

## Konuşmanın diyalektiği

### İlk tur — ChatGPT'nin sertleştirmeleri

ChatGPT Claude'un dört sertleştirmesine PASS verdi, ardından **kendi katkılarını** ekledi:

- **Constitutional vs Operational Rule Authority** ayrı bölüm — bu sertleştirme kritik: M2 alt-tipi sadece operational için, constitutional M2'ye düşmez
- **Block class hard-stop oluşunu değiştirmez, sadece post-block davranışı belirler** — önemli netlik (üçü de eylemi eşit sertlikte durdurur)
- **`SUSPECTED_BYPASS_PATTERN` vs `DEONTIC_BYPASS_ATTEMPT`** ikili ayrım — conservative classification (her başarısız niyet bypass attempt sayılmasın)
- **"Kill-switch is action silence, not cognitive death"** — anayasal cümle
- **Adapter reads kill-switch'te devam, writes durur** — görünürlük korunur
- **Kill-switch activation shock once, sonrası sessiz** — alarm fırtınası engellenir
- **§15 Read/Write Behavior tablosu** — gate state'lere göre sistem davranışı
- **DEONTIC_POLICY_STATUS_CHANGED** tek event (B'nin WORKSPACE_PULSE, C'nin SOURCE_TRUST_STATUS_CHANGED disiplini)

### İkinci tur — Claude üç soruya cevap + 3 sertleştirme

ChatGPT üç açık soru yöneltmişti:
1. Constitutional hard-stop bağlayıcılık seviyesi?
2. Operational policy update workflow kesin mi?
3. Kill-switch deactivation tek-adım mı, graduated mı?

Claude cevapları:
1. **Constitutional = declaratives, Operational = scalars.** 11 declarative önerisi (kapalı liste).
2. **Workflow kesin** + **emergency_revert flow** ekledi (verified active policy adverse outcome ürettiğinde önceki verified policy'ye dönüş).
3. **Graduated deactivation:** REQUESTED → review_window → audit → CONFIRMED → DEACTIVATED → gradual reactivation. "Kill-switch kolay açılır, zor kapanır."

Yeni constitutional rule: **"Emergency revert path may only revert to a previously verified policy, never forward to a new policy."** (Rule 11)

### Üçüncü tur — ChatGPT'nin final onayı

ChatGPT "Yaz" dedi. Üç önemli onay:
1. Constitutional hard-stops M2'ye indirgenemez (Madde 5 koruması)
2. Operational policy workflow kesin
3. Kill-switch graduated deactivation + "action silence, not cognitive death"

Ek vurgu: **"Bypass attempt yasak düşünce değildir. Yasak olan bypass'ın eyleme dönüşmesidir."** Sistem tehlikeli niyet üretebilmeli, hatta öğrenmek için üretmeli; ama eyleme dönüşemez.

---

## Çekirdek kararlar (13 ana + 11 constitutional declarative)

### 13 ana karar
1. Deontic gate Madde 5'in alt-spec'i, yeni anayasa maddesi değil.
2. Gate düşünmez, tartışmaz; sadece eylem çıkışında hard-stop uygular.
3. İki katmanlı yapı: constitutional (declaratives) + operational (scalars).
4. Constitutional hard-stops M2'ye indirgenemez.
5. Operational hard-stops M2 DeonticPolicyRecord olarak yaşar.
6. Tek anda tek active operational policy.
7. Block class hard-stop oluşunu değiştirmez, sadece post-block davranışı belirler.
8. Three block classes: routine / safety / constitutional.
9. Bypass attempt yasak düşünce değildir; yasak olan eyleme dönüşmesidir.
10. SUSPECTED_BYPASS_PATTERN + DEONTIC_BYPASS_ATTEMPT ikili audit.
11. Kill-switch: action silence, not cognitive death. Activation immediate, deactivation graduated.
12. Deontic proximity gate kararı değil, predictive self-field basıncıdır.
13. Emergency revert sadece previous verified policy'ye dönebilir, ileri geçemez.

### 11 constitutional declarative
Bkz. DEONTIC_GATE.md §8 — kapalı liste, belge revizyonu olmadan değişmez.

---

## Madde 5 yansıması — eylem-çıkışı seviyesi

A turunda Madde 5 self-field/deontic ayrımını kurdu. B turunda InternalShockEvent ile deontic gate'in çekirdeğe yansıma yolu çizildi. C turunda InternalShockEvent ingress yolu tanımlandı. D turunda genome deontic_gate_ref taşıdı. **E turunda gate'in kategorik kurallarının kendisi biçimselleşti.**

Bu, A→B→C→D→E zincirini tamamlıyor:
- Anayasa kurar
- Hafıza sınır çizer
- Dikkat akışı kurar
- Dünya girişi sınırlar
- Doğum başlatır
- **Eylem çıkışı kapatır** ← E

---

## Önemli sertleştirmeler

### Block class hard-stop ayrımı
> *Block class gate'in hard-stop oluşunu değiştirmez. Sadece post-block davranışı belirler.*

Routine de hard-stop, constitutional da hard-stop. Fark sadece audit seviyesi, InternalShockEvent tetikleme, insan bildirimi.

### "Warning-only" yok
Deontic gate'te soft kategori yoktur. Soft pressure self-field'in işidir (`action_boundary_pressure` üzerinden). Gate hard-stop only.

> *Self-field basınç yapar. Deontic gate hard-stop yapar.*

### Kill-switch alarm spam yok
Activation shock once. Sonrasında kill-switch altında her niyet çıkışında InternalShockEvent üretmek sistemi traumatize eder. Doğru davranış: activation kritik, sonrası sessiz.

### Emergency revert yeni policy değil
Emergency revert **yeni karar üretmez**, **bilinen iyi state'e döner**. Yeni policy oluşturma her zaman normal flow gerektirir. Constitutional Rule 11.

### Deontic proximity self-field'da
> *Self-field predicts. Gate enforces.*

Gate düşünceye girmez. Predictive self-field "yakın" hissini verir; gate sadece niyet kapıya gelince gerçek kontrolü yapar.

---

## Yan güncellemeler (commit'in parçası)

- `CONSTITUTION.md` Madde 5 — alt-spec referansı satırı (DEONTIC_GATE.md)
- `MEMORY_CONTRACT.md` M2 subject_class listesi — `deontic_policy` ve `bootstrap_reference` eklendi
- `ATTENTION_WORKSPACE.md` §18 — DEONTIC_GATE §10-14 cross-ref (block classification, kill-switch, bypass)
- `WORLD_INGRESS.md` §12 — DEONTIC_GATE §12-14 cross-ref (InternalShockEvent tetikleme kuralları)
- `README.md` — DEONTIC_GATE tamamlanmış listesine

---

## Açık kalanlar (sonraki belgelere devredildi)

- **Operational threshold sayısal değerleri** → `INITIAL_DEONTIC_POLICY.md` veya implementation
- **`max_consecutive_blocks_before_pause` davranışı** → Pause mode tanımı, implementation
- **`SUSPECTED_BYPASS_PATTERN` → `DEONTIC_BYPASS_ATTEMPT` upgrade kuralı** → Implementation/numerics
- **`mandatory_review_window` süresi** → Kill-switch implementation spec
- **Constitutional rule shift mekaniği** → BOOTSTRAP §23 ile bağlantılı
- **Policy versioning ve rollback derinliği** → Implementation

---

## Sıradaki

A + B + C + D + E kapandı. Sentinel'in **anayasal mimarisi** tamamen donmuş:

- `CONSTITUTION.md` — 7 madde
- `MEMORY_CONTRACT.md` — hafıza sınırı (Madde 7)
- `ATTENTION_WORKSPACE.md` — dikkat alt-spec (Madde 4)
- `WORLD_INGRESS.md` — dış dünya girişi (Madde 1/3/5/6/7)
- `BOOTSTRAP_GENOME.md` — doğum anayasası (Madde 3)
- `DEONTIC_GATE.md` — eylem çıkış sınırı (Madde 5)

Sıradaki belgeler:
- **`OBSERVER_LEDGER_SCHEMA.md`** — M1 event tipleri tam şeması, audit yapısı
- **`RECALL_PROTOCOL.md`** — RecallRequest/RecallEvent şemalarının tam spec'i
- **`MEMORY_WRITE_GATE.md`** — epistemic gate sayısal eşikler
- **`ADAPTER_MANIFEST_SPEC.md`** — uzuvların standart kontratı
- **`INGRESS_COMPILER_SPEC.md`** — bootstrap mapping detayı + sayısal katsayılar
- **`BACKUP_STRATEGY.md`** — M0/M1 yedekleme planı, RPO/RTO

Bunlar **implementation-yakın** belgeler. Anayasal aşama A-E kapandı, sıradaki aşama **operational specification**.

---

## Kilit cümleler

> **Sentinel düşünebilir, şüphe edebilir, yanlış niyet bile üretebilir. Ama anayasal eylem kapısından geçemeyen hiçbir şey dünyaya dokunamaz.**
>
> **Deontic gate düşünmez. Deontic gate tartışmaz. Deontic gate sadece eylem çıkışında sınır uygular.**
>
> **Deontic gate zekâ değildir. Deontic gate, zekânın sermayeyi yok etmesini engelleyen anayasal çıkış kapısıdır.**
>
> **Constitutional hard-stops = declaratives. Operational hard-stops = scalars.**
>
> **Self-field predicts. Gate enforces.**
>
> **Bypass attempt yasak düşünce değildir. Yasak olan bypass'ın eyleme dönüşmesidir.**
>
> **Kill-switch is action silence, not cognitive death.**
