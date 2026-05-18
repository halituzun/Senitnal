# 0004 — Bootstrap Genome

> Bu dosya `BOOTSTRAP_GENOME.md` (v0.1) ortaya çıkmadan önce yapılan üçlü
> tasarım konuşmasının (Halit + Claude + ChatGPT) sıkıştırılmış özetidir.
> D turunun kararlarının soyağacı.
>
> A turu: [`0001-neural-core-genesis.md`](./0001-neural-core-genesis.md)
> B turu: [`0002-attention-workspace.md`](./0002-attention-workspace.md)
> C turu: [`0003-world-ingress.md`](./0003-world-ingress.md)

---

## Tarih
2026-05-18 (C → D geçişi)

## Bağlam
A, B, C üçü de kapanmış halde. Üçü de **açık soruları BOOTSTRAP_GENOME'a devretmiş**:

- **A'dan:** genesis_trace formatı, self-field embriyo başlangıç ağırlıkları, doğuştan refleksler
- **B'den:** context_signature başlangıç eksenleri, self_signature_slow başlangıç ağırlıkları, InternalShockEvent payload_seed magnitudes
- **C'den:** bootstrap_rules sayısal parametreleri, InternalShockEvent payload_seed magnitudes (B ile aynı), source_reliability_band başlangıç mantığı

D turu bu açık soruların **birleşim noktası**.

---

## Başlangıç pozisyonları

### ChatGPT (manifesto)
> *Sentinel sıfır doğmaz. Sentinel hazır zeki de doğmaz. Sentinel bilgiyle değil, bilgiye iz bırakabilecek doku ile doğar.*

Ana ayrım:
> *Genome = öğrenebilirlik düzeni. Genome ≠ bilgi.*

### Claude (açılış sertleştirmeleri)
1. BOOTSTRAP_GENOME Madde 3 alt-spec'i (yeni anayasa maddesi değil)
2. İki katmanlı genome: initial_state + developmental_rules
3. Genome immutable artifact, sistem kendi genome'unu göremez
4. Domain-agnostic — tüm Sentinel'ler aynı genome

Üç açılış çapası:
- Plasticity yaşa bağlı mı?
- M2 t=0'da boş mu doğmalı?
- Genome formatı manifesto + band mı, sayısal mı?

---

## Konuşmanın diyalektiği

İlk turda ChatGPT üç çapaya net cevaplar verdi:

1. **Plasticity:** state/consolidation-based, age-based değil. "Sentinel has no biological age. Initial bootstrap phase exists, age identity does not."
2. **M2:** B (Bootstrap Injection) ama sıkı sınırla. `provenance: human | genesis`, `subject_class: bootstrap_reference`. Dünya bilgisi yasak.
3. **Format:** A (Manifesto + band + sınır), sayısal implementation belgesine devir.

ChatGPT yeni katkılar:
- **GenomeArtifact şeması** (document_hash, signed_by, immutable_ref)
- **SELF_GENESIS şeması** (anayasal belge hash'leri ile)
- **§7 Runtime Non-Configurability** ayrı bölüm (genome config kapısı kapatılır)
- **26 bölümlü iskelet** öneri

Claude ikinci tur — Initial State şeması:
- M0/M1/M2/M3 t=0 detaylı şema
- SELF_GENESIS alanları listesi
- Açık soru: Constitutional Anchors değişirse?

ChatGPT üçüncü tur — Initial State PASS- with 4 sertleştirme:
1. `stable_assembly_state = empty` + `proto_resonance_fields = present` (doku ölü değil)
2. `payload_modulation_reflexes` (davranış değil modülasyon)
3. SELF_GENESIS'e `genesis_random_seed_hash`, `initial_m0_snapshot_hash`, `birth_mode`
4. Constitutional shift policy **C+ with compatibility class** (clarification / safety_tightening / genesis_affecting)

Claude dördüncü tur — küçük nüans:
- `birth_mode` ↔ `compatibility_class` cross-link
- `migration_birth` özel tip: genesis_affecting shift sonrası yeni doğum

ChatGPT son tur: "Yaz. Bir tur daha onaya gerek yok."

---

## Çekirdek kararlar (12 ana + 4 sertleştirme + C+ shift policy)

### Ana kararlar
1. Genome = öğrenebilirlik düzeni; genome ≠ bilgi.
2. Genome doğumdan önce donar; runtime'da değişmez.
3. Sentinel kendi genome'unu okuyamaz, değiştiremez; sadece sonucudur.
4. Initial state ve developmental rules ayrı katmandır.
5. Tüm Sentinel'ler aynı genome ile doğar (domain-agnostic).
6. Primer payload paleti v0.1 sabit (10 payload).
7. M0 t=0: embriyo doku; stable assembly yok ama proto_resonance_fields var.
8. M1 t=0: SELF_GENESIS + bootstrap M2 injection event'leri.
9. M2 t=0: sadece bootstrap_reference kayıtları; dünya bilgisi yasak.
10. M3 t=0: boş.
11. Plasticity yaş-temelli değil, state/consolidation-temelli.
12. Constitutional shift policy: clarification / safety_tightening / genesis_affecting.

### Önemli sertleştirmeler
- **`stable_assembly_state = empty` vs `proto_resonance_fields = present`:** Doğumda fikir yok ama doku ölü değil
- **`payload_modulation_reflexes`:** Refleks eylem değildir, modülasyondur
- **SELF_GENESIS üç hash'i:** genome_artifact_hash + genesis_random_seed_hash + initial_m0_snapshot_hash. "Aynı genome, iki Sentinel, farklı gelişim" sorusuna cevap
- **`birth_mode`:** clean_birth / restore_birth / fork_birth / migration_birth
- **`migration_birth` ↔ `genesis_affecting` shift cross-link:** Anayasa kökten değişirse yeni Sentinel doğar, eski Sentinel'in `SELF_GENESIS`'ine geri referans tutulur

---

## Madde 1 yansıması — genome seviyesi

A turunda Madde 1 nöron seviyesinde, B turunda pulse seviyesinde, C turunda ingress kanalları seviyesinde uygulanmıştı. D turunda **genome seviyesinde**:

- Tek genome (homogeneous), farklı imza (deneyim/adapter ile)
- Genome'da domain etiketi sızmaz (BTC, RSI, vs.)
- Plasticity yaş kategorisi değil, state ölçümü
- Refleksler davranış kategorisi değil, modülasyon ölçümü

Bu Madde 1'in **anayasal mikro-prensip** olarak Sentinel'in her katmanına yansıdığını kanıtlar.

---

## "İki cümle" anayasal eşlik

D turunda ortaya çıkan iki çift cümle, A/B/C boyunca kurulmuş çizgileri tamamlıyor:

> **Sentinel genome'unu bilmez. Sentinel genome'unun sonucudur.**

vs A turundaki:

> **Çekirdek hatırlar. Observer kanıtlar. Explicit memory hatırlatır. LLM tercüme eder. Hiçbiri diğerinin yerine geçmez.**

Bu eşlik: sistem kendi yapısının "üst düzey" parçalarını (genome, hafıza katmanları, anayasa belgeleri) **göremez** — sadece sonuçlarını yaşar. Audit dışarıdan yapılır.

---

## Yan güncellemeler (commit'in parçası)

- `CONSTITUTION.md` Madde 3 — alt-spec referansı satırı (BOOTSTRAP_GENOME §1-26)
- `MEMORY_CONTRACT.md` §13 — restore rule'a `birth_mode` ve constitutional shift policy referansı
- `README.md` — BOOTSTRAP_GENOME tamamlanmış listesine eklendi

---

## Açık kalanlar (sonraki belgelere devredildi)

- **Kesin sayısal genome parametreleri** → `BOOTSTRAP_GENOME_NUMERICS.md` veya signed genome artifact
- **Deontic gate başlangıç kuralları** → `DEONTIC_GATE.md`
- **Ingress mapping katsayıları** → `INGRESS_COMPILER_SPEC.md`
- **Replay rhythm tetikleme eşikleri** → Implementation
- **Adapter manifest formatı** → `ADAPTER_MANIFEST_SPEC.md`
- **`proto_resonance_fields` matematiksel tanım** → Implementation (gevşek anayasal sınır var)
- **`migration_birth` kontinüite sınırı** → MEMORY_CONTRACT §14 cross-restore identity sorusuyla bağlantılı

---

## Sıradaki

A + B + C + D kapandı. Sentinel'in **doğum anayasası** ve **çekirdek mimarisi** tamamen donmuş halde:

- `CONSTITUTION.md` — 7 madde
- `MEMORY_CONTRACT.md` — hafıza sınırı
- `ATTENTION_WORKSPACE.md` — dikkat alt-spec'i (Madde 4)
- `WORLD_INGRESS.md` — dış dünya giriş sınırı
- `BOOTSTRAP_GENOME.md` — doğum anayasası (Madde 3 alt-spec'i)

Sıradaki ana belge: **`DEONTIC_GATE.md`** — kategorik action-risk kısıtlarının biçimsel listesi. Çünkü:
- BOOTSTRAP_GENOME deontic gate ref'ini taşır ama içeriği vermez
- CONSTITUTION Madde 5 deontic gate'i ana hatlarıyla tanımlar ama kategorik kuralları listelemez
- ATTENTION_WORKSPACE InternalShockEvent için "kritik deontic block" der ama hangi block kritik diye söylemez
- WORLD_INGRESS InternalShockEvent ingress yolunu tanımlar ama tetikleyen kuralları vermez

`DEONTIC_GATE.md` bu dört belgenin de **action-side sınırını** çiziyor.

---

## Kilit cümleler

> **Sentinel sıfır doğmaz. Sentinel hazır zeki de doğmaz. Sentinel bilgiyle değil, bilgiye iz bırakabilecek doku ile doğar.**
>
> **Genome = öğrenebilirlik düzeni. Genome ≠ bilgi.**
>
> **Sentinel genome'unu bilmez. Sentinel genome'unun sonucudur.**
>
> **M0 doğar. M1 doğumu kanıtlar. M2 doğum çevresini referanslar. M3 boş kalır.**
>
> **Refleks eylem değildir. Refleks modülasyondur.**
>
> **Sentinel has no biological age. Initial bootstrap phase exists, age identity does not.**
>
> **Yaşayan Sentinel anayasa değişikliğini sessizce kabul etmez. Genesis-affecting değişiklikler yeni doğum gerektirir.**
