# 0001 — Neural Core Genesis

> Bu dosya `CONSTITUTION.md` (v0.1) ve `MEMORY_CONTRACT.md` (v0.1) ortaya çıkmadan
> önce yapılan üçlü tasarım konuşmasının (Halit + Claude + ChatGPT) sıkıştırılmış
> özetidir. Sadece **kararların özü**; tam döküm için bkz.
> [`2026-05-18-agi-core-design.md`](./2026-05-18-agi-core-design.md).

---

## Tarih
2026-05-18

## Katılımcılar
- **Halit** — proje sahibi, finansal AGI vizyonu, son söz
- **Claude** — mimari tartışma partneri, "iyi tasarlanmış yazılım mimarisi" tarafı
- **ChatGPT** — ikinci görüş, "saf sinir dokusu" tarafı

## Konuşmanın diyalektiği

İki uç pozisyon vardı:

- **Claude'un ilk yaklaşımı:** Kontrat-önce yaklaşım, modül mimarisi, decision governor, adapter manifest. Yazılım mühendisliği.
- **ChatGPT'nin ilk yaklaşımı:** Saf homojen nöral doku. Tek tip nöron, sinaps, charge, decay, plasticity. Anlam emergent.

Halit her ikisini de reddetti:
- Claude'un mimarisi modülerleşmeye geri kaçıyordu.
- ChatGPT'nin saf nöral dokusu hesap verebilirliği yok ediyordu.

**Sentez:** Saf nöral doku + observer + dış katmanlar. Embriyo doğsun, hesap verebilir kalsın.

---

## Çekirdek kararlar

### Nöron / Payload kararı
- **Yol B-** seçildi: homojen denklem + heterojen semantic payload + target-side receptor yorumlama.
- Payload **iş kategorisi** değil **zihinsel renk** olmalı (`suspicion`, `novelty`, `contradiction` — `buy`, `risk` değil).
- Primer payload paleti + sistemin kombinasyonla türettiği karışım payload'lar.
- Default modulation profilleri deneyimle kayar.

### Sinaps kararı
- Sinaps **anlam taşımaz**, akış deseninin hafızasını taşır.
- Saf yol; yorumu hedef nöron yapar.
- **STDP + outcome-gated learning + üç ölçekli eligibility trace** (fast/medium/slow).
- Outcome **skaler değil vektör**.
- **Sleep/replay tabanlı causal pruning** zorunlu — saf STDP correlation/causation karıştırır.
- Doğum: lokal komşuluk + co-firing tabanlı (long-range shortcut).
- Ölüm: decay → dormant → pruned (observer snapshot sonrası).

### Assembly / Akış kararı
- **Bir kez yanan desen gürültüdür. Geri dönebilen ve işe yarayan desen fikirdir.**
- Yerel rekabet (winner-take-most) + global paralellik.
- Aynı temsil alanı + zıt eylem → rekabet.
- Farklı bağlam → paralel kalır.
- **Düşüncede paralellik, niyette rekabet, eylemde tekleşme.**

### Self-field / Deontic gate kararı
- Benlik tek assembly değil; **üç katman**: homeostatik öz + predictive self-model + narrative iz.
- Self-field **soft pressure** — eşik yükseltir, ama yasaklamaz.
- **Deontic gate** ayrı bir katman — kategorik, müzakeresiz, sadece eylem çıkışında durur.
- "Benlik basınç yapar. Anayasa fren tutar."

### LLM Boundary kararı
- **B-kısıtlı** çizgi seçildi.
- LLM çekirdeğin **dış tercümanıdır**, nöral dokunun parçası değildir.
- LLM asla charge/weight/assembly/intent yazamaz.
- **Deterministic Ingress Compiler** — LLM yapısal niyet üretir, payload'a çevirme kuralları çekirdeğin sabit kuralı.
- Translator memory silinse bile çekirdek değişmez.
- Sandbox/replay laboratory'de C seçeneği (LLM nöron tipi) sadece offline.

### Memory Boundary kararı
- "Memory architecture" değil **"Memory Boundary"** — sorun veri yapısı değil sınır çizmek.
- **Dört katman**: M0 (implicit neural), M1 (observer ledger), M2 (explicit recall store), M3 (translator memory).
- **Hafıza çekirdeğe emir vermez. Hafıza çekirdeğe hatırlatma gönderir.**
- M2 → çekirdek sadece `RecallEvent` (duyusal event) ile.
- Çekirdek M2'ye doğrudan yazamaz; **Memory Write Gate** denetler.
- **Memory Write Gate deontic gate'in alt türü değildir** — epistemik risk vs action risk farkı.
- M2'ye sistem kaynaklı yazılan her kayıt önce `candidate`, replay/outcome ile `verified` olur.
- **Silmek ≠ unutmak** — her silme/expire/prune olayı M1'e yazılır.
- Kimlik hiyerarşisi: M0 + M1 = ruh + tarih; M2 = bilgi; M3 = konuşma kabuğu.

---

## Sonuç

Bu konuşmadan iki donmuş taslak doğdu:

- [`CONSTITUTION.md`](../../CONSTITUTION.md) v0.1 — 7 madde
- [`MEMORY_CONTRACT.md`](../../MEMORY_CONTRACT.md) v0.1 — 14 bölüm

## Sıradaki

Hâlâ kod yok. Sırada:

- **B** — `ATTENTION_WORKSPACE.md` (dikkat, global workspace pulse)
- **C** — `WORLD_MODEL_INGRESS.md` (semi-structured event + neural overlay)
- Sonra: `MEMORY_WRITE_GATE.md`, `RECALL_PROTOCOL.md`, `OBSERVER_LEDGER_SCHEMA.md`, `BOOTSTRAP_GENOME.md`, `DEONTIC_GATE.md`

---

## Kilit cümle

> **Senitnal önce düşüncenin anayasasıdır. Kod daha sonra gelir.**
