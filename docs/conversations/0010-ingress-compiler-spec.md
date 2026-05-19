# 0010 — Ingress Compiler Spec

> Bu dosya `INGRESS_COMPILER_SPEC.md` (v0.1) ortaya çıkmadan önce yapılan üçlü
> tasarım konuşmasının (Halit + Claude + ChatGPT) sıkıştırılmış özetidir. J
> turunun kararlarının soyağacı.
>
> A: [`0001-neural-core-genesis.md`](./0001-neural-core-genesis.md)
> B: [`0002-attention-workspace.md`](./0002-attention-workspace.md)
> C: [`0003-world-ingress.md`](./0003-world-ingress.md)
> D: [`0004-bootstrap-genome.md`](./0004-bootstrap-genome.md)
> E: [`0005-deontic-gate.md`](./0005-deontic-gate.md)
> F: [`0006-observer-ledger-schema.md`](./0006-observer-ledger-schema.md)
> G: [`0007-memory-write-gate.md`](./0007-memory-write-gate.md)
> H: [`0008-recall-protocol.md`](./0008-recall-protocol.md)
> I: [`0009-adapter-manifest-spec.md`](./0009-adapter-manifest-spec.md)

---

## Tarih
2026-05-18 (I → J geçişi)

## Bağlam

A-I kapanmış. **Conceptual phase'in dış sınırı** I ile kapandı (adapter kontratı). J **implementation-adjacent phase**'in ilk belgesi.

I'da kilitlenen:
- Adapter raw / structured event üretir
- Adapter neural_seed üretemez
- Core-facing neural_seed her zaman WORLD_INGRESS compiler'dan doğar

Bu durumda sıradaki doğal soru: **Structured event → neural_seed dönüşümü nasıl yapılır?**

WORLD_INGRESS §13-15 ana hatları çizmişti ama:
- Mapping function format açık
- Learned mapping update kuralları açık
- Rate limiting / drift control açık
- Conflict resolution açık
- Rule family lifecycle açık

J bu açıkları kapattı.

---

## Başlangıç pozisyonları

### Claude (açılış)
> *Ingress compiler kategori üretmez. Ingress compiler primer payload tonu üretir.*
> *Compiler kuralları deterministic mapping function'larıdır; semantic interpretation değildir.*
> *Bootstrap mapping anayasaldır; learned mappings M0 dokusudur.*

Üç çapa:
1. Mapping function format (boolean rule? lookup table? continuous function?)
2. Learned mapping rate limiting (drift control)
3. Payload seed normalization (sabit toplam vs raw)

### ChatGPT'nin 5 sertleştirmesi + 3 çapa cevabı
- **event_profile compiler bilir, core bilmez** (anayasal)
- **Output tek zarf: neural_seed**
- **Learned_mappings yetki matrisi** (Observation açık / Recall kısıtlı / HumanIntent kapalı / InternalShock kapalı)
- **M0 ingress_calibration_traces** olarak yaşar
- **Mapping weakening daha hızlı, strengthening yavaş** (asymmetric)

Çapa cevapları:
1. **Hybrid format:** condition_band + base_payload_vector + scalar_modifiers + caps
2. **Rate cap'li learned update:** outcome/replay evidence zorunlu, asymmetric rates
3. **Hybrid bounded raw:** raw intensity + profile-specific cap (full normalization yok)

### Claude'un 3 ek netleştirmesi
1. **Conflict resolution = weighted blend** (en spesifik kazanır gibi yargı yok, sadece toplama + cap)
2. **Mapping family deprecation** (active/deprecated/archived lifecycle)
3. **Numerics belgeleri net referans**

### ChatGPT'nin son sertleştirmesi
- **`COMPILER_RULE_FAMILY_STATUS_CHANGED` ayrı canonical event** (mapping update'tan farklı nedensel mekanizma)
- **Deprecated rule family compiler evaluation'a girmez**, sadece migration/audit penceresinde
- "Weighted blend hakikat veya öncelik kararı değildir" — anayasal cümle

Ardından "yaz" hükmü.

---

## Çekirdek kararlar (13)

1. Compiler classifier değildir; deterministic mapping function uygular.
2. Output tek zarftır: `neural_seed`.
3. event_profile compiler tarafından görülür, core'a sızmaz.
4. Authority matrix: Observation açık / Recall kısıtlı / HumanIntent kapalı / InternalShock kapalı.
5. RuleFamily format: condition_band + base_payload_vector + scalar_modifiers + caps.
6. Bootstrap rules anayasal; learned mappings M0 ingress_calibration_traces.
7. Mapping update sadece outcome/replay evidence ile.
8. Rate cap'ler zorunlu; drift audit edilir.
9. Asymmetric rates: false-positive dampening > positive strengthening, ama ikisi de capped.
10. Conflict resolution = weighted blend + cap (semantik winner yok).
11. Payload intensity hybrid bounded raw (raw + profile cap).
12. Rule family lifecycle: active / deprecated / archived; deprecated traces frozen.
13. Dedup allowed, aggregation forbidden.

---

## Madde 1 yansıması — compiler seviyesi

A-I boyunca Madde 1 her seviyede yansıdı. J'de en güçlü yansıması:

**Weighted blend conflict resolution.** "En spesifik rule kazanır" örtük yargı; weighted blend purely additive + cap. Compiler **karar vermez**, sadece **mekanik toplama + cap** uygular.

Bu Madde 1'in implementation-adjacent fazdaki ilk önemli sertleştirmesi: anayasal kavram → mekanik kurala dönüşürken **yargı kaçaklarını** kapatma.

---

## Önemli sertleştirmeler

### Weighted blend, not winner selection
> *Weighted blend hakikat veya öncelik kararı değildir.*
> *Sadece eşleşen rule family katkılarının mekanik toplamıdır.*

"En spesifik rule kazanır" reddedildi çünkü condition_band sayısını ranking olarak kullanmak örtük yargıdır. Weighted blend pure addition + cap — yargı yok.

### Asymmetric update rates
> *False-positive dampening may be faster than positive strengthening, but neither may bypass rate caps or evidence requirements.*

Sebep: yanlış pozitif sensory tone sistemi bozar (panik üretir); düzeltme hızlı olmalı ama yine evidence-bound + capped.

### Rule family lifecycle ayrı event
ChatGPT'nin son katkısı: `COMPILER_RULE_FAMILY_STATUS_CHANGED` ayrı canonical event (mapping update'tan farklı nedensel mekanizma). Bootstrap/manifest benzeri artifact lifecycle.

`COMPILER_MAPPING_UPDATED`: learned mapping calibration update (eski).
`COMPILER_RULE_FAMILY_STATUS_CHANGED`: rule family status değişimi (yeni).

İki ayrı tip ama event_family farklı: birincisi `ingress`, ikincisi `ledger_meta` (artifact lifecycle).

### Hybrid bounded raw normalization
Tam normalize ile tam raw arasında orta yol: raw intensity korunur, profile-specific cap aşılırsa proportional scaling. Weak/strong event farkı kaybolmaz; storm da olmaz.

### Learned mappings M0'da yaşar
Config kanalı yok. LLM/human/adapter doğrudan write yapamaz. Sadece sistem otomatik öğrenme (outcome + replay + STDP-benzeri) ile kayar. Madde 7 koruması en derin halinde.

---

## Yan güncellemeler (commit'in parçası)

- `WORLD_INGRESS.md` §13 — INGRESS_COMPILER_SPEC cross-ref (RuleFamily format, weighted blend, lifecycle)
- `WORLD_INGRESS.md` §14 — Bootstrap rules ile NUMERICS ayrımı netleştirildi
- `WORLD_INGRESS.md` §15 — Learned mapping update kuralları cross-ref
- `BOOTSTRAP_GENOME.md` §19 — INGRESS_COMPILER_SPEC cross-ref
- `MEMORY_CONTRACT.md` §14 — Replay engine M0 etkisi sorusunun J tarafından kapanan kısmı eklendi (3. kanal: ingress calibration update via COMPILER_MAPPING_UPDATED)
- `OBSERVER_LEDGER_SCHEMA.md` §10 permanence_policy — COMPILER_RULE_FAMILY_STATUS_CHANGED, COMPILER_DRIFT_WARNING, INGRESS_NO_RULE_MATCH eklendi
- `OBSERVER_LEDGER_SCHEMA.md` §19 event catalog — ingress family'ye INGRESS_NO_RULE_MATCH, COMPILER_DRIFT_WARNING; ledger_meta family'ye COMPILER_RULE_FAMILY_STATUS_CHANGED
- `README.md` — INGRESS_COMPILER_SPEC tamamlanmış listesine

---

## Açık kalanlar (implementation/numerics)

- Kesin band sınırları (magnitude_band, confidence_band, vs.)
- Bootstrap rule katsayıları (base_payload_vector büyüklükleri)
- Profile-specific intensity caps sayısal değerleri
- Rate cap sayısal değerleri (per_mapping_daily_delta_cap, vs.)
- Drift detection threshold
- Cleanup window süresi (deprecated → archived)
- Update direction asymmetry ratio
- INGRESS_NO_RULE_MATCH event gerçekten gerekli mi (debug için yararlı, production gürültü olabilir)
- Rule family versioning (yeni version registered olunca eski otomatik deprecated mi?)

Bu sorular `INGRESS_COMPILER_NUMERICS.md` ve implementation belgelerine devredildi.

---

## Sıradaki

A + B + C + D + E + F + G + H + I + J kapandı. **11 belge.** Conceptual + implementation-adjacent compiler katmanı tam.

Sıradaki belgeler (devam):
- `BACKUP_STRATEGY.md` — M0/M1 yedekleme, RPO/RTO, cross-restore identity
- `OBSERVER_LEDGER_NUMERICS.md` — snapshot windows, sampling thresholds
- `BOOTSTRAP_GENOME_NUMERICS.md` — kesin genome parametreleri
- `MEMORY_WRITE_GATE_NUMERICS.md` — gate threshold'ları
- `RECALL_PROTOCOL_NUMERICS.md` — recall threshold'ları
- `ADAPTER_TRUST_NUMERICS.md` — reliability bands
- `INGRESS_COMPILER_NUMERICS.md` — compiler band'ları, rule katsayıları, rate caps
- `REPLAY_PROTOCOL.md` — sleep/attention replay detay

---

## Kilit cümleler

> **Compiler dünyayı anlamaz. Compiler duyusal olayı primer zihinsel tona çevirir.**
>
> **Adapter ham olay üretir. Compiler neural_seed üretir. Çekirdek sadece tonu yaşar.**
>
> **Bootstrap mapping anayasaldır; learned mappings M0 dokusudur. İkisi de runtime config değildir.**
>
> **Weighted blend hakikat veya öncelik kararı değildir. Sadece eşleşen rule family katkılarının mekanik toplamıdır.**
>
> **No event may force unbounded payload intensity. No normalization may erase weak/strong event distinction.**
>
> **False-positive dampening may be faster than positive strengthening, but neither may bypass rate caps or evidence requirements.**
>
> **Deprecated rule family audit'te kalır; sessizce silinmez.**
