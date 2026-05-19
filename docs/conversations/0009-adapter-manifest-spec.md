# 0009 — Adapter Manifest Spec

> Bu dosya `ADAPTER_MANIFEST_SPEC.md` (v0.1) ortaya çıkmadan önce yapılan üçlü
> tasarım konuşmasının (Halit + Claude + ChatGPT) sıkıştırılmış özetidir. I
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

---

## Tarih
2026-05-18 (H → I geçişi)

## Bağlam

A-H kapanmış. Çekirdek mimarisi tam (constitution + memory + attention + ingress + bootstrap + deontic + observer + write gate + recall). Sıradaki gerçek açık **dışarısı** — adapter sistemi.

A turunda Halit'in vizyonu:
> *İnsan beyni gibi sonradan buna uzuvlar bir şablonda bir standartta eklenmesi çok kolay olacak.*

I bu vizyonun biçimsel hali. A-H'de adapter dağınık şekilde referans edildi:
- WORLD_INGRESS §9, §16 — adapter_capabilities_snapshot, SourceTrustRecord
- BOOTSTRAP_GENOME §20 — adapter_manifest_refs opsiyonel
- DEONTIC_GATE §8 Rule 7 — execution adapter valid manifest
- MEMORY_CONTRACT M2 subject_class — adapter references

I tek kontrat altında topladı + ne yapabildiği/yapamadığını biçimselleştirdi.

---

## Başlangıç pozisyonları

### Claude (açılış manifestosu)
> *Adapter sistemin uzuvudur. Adapter sistemin parçası değildir.*
> *Adapter çekirdeği bilmez. Adapter sadece kendi yeteneklerini deklare eder.*
> *Çekirdek adapter'ı bilmez. Çekirdek sadece adapter'dan gelen kaynaklı olayları yaşar.*

Üç çapa:
1. Manifest immutability + versioning
2. Capability flags vs kategori
3. Adapter trust = SourceTrust uzantısı mı, ayrı kayıt mı?

### ChatGPT (6 sertleştirme + 4. çapa)

ChatGPT üç çapanın hepsine PASS verdi ve **6 sertleştirme** ekledi:
1. "Adapter type yok, capability surface var" — adapter_name observer-only
2. **Capability flag + channel binding zorunluluğu** — flag tek başına yetki değil
3. Execution capability özel hard constraints (multi-condition)
4. Adapter lifecycle + `ADAPTER_MANIFEST_STATUS_CHANGED` canonical
5. AdapterTrustRecord ayrı M2 subject_class, SourceTrust ile linked ama farklı
6. Adapter raw payload üretir, **neural_seed üretemez**

Dördüncü çapa: capability authority nasıl channel-bound olacak?

### Claude (4. çapa cevabı + capability incompatibility matrix)

Capability binding şeması verildi (her capability için input_channel, output_channel, required_gate_ref, m1/m2 write scope, kill_switch_respect, rate_limit_band).

**Capability incompatibility matrix** önerildi (yeni):
- `execute + intent_relay` kapalı (LLM kanalı + exec aynı yerde olamaz)
- `execute + recall_provider` kapalı (M2 reader + actor self-deception)
- `execute + memory_writer` kapalı (gate bypass riski)
- `recall_provider + memory_writer` kapalı (kendi yazdığını okumak)
- `intent_relay + memory_writer` kapalı (LLM M2'ye yazamaz, Madde 6)

Required pair (positive): `execute → must_have observe` (efference copy).

### ChatGPT (son sertleştirme — execute → observe efference-only)

> *Required pair `execute → observe` is limited to efference/feedback observation.*
> *It does not grant general ObservationEvent authority unless separately declared.*

Yani execute eden adapter'ın observe capability'si **sadece kendi eyleminin sonuçlarını** raporlayabilir; genel market observation için ayrı declaration gerekir.

Ardından "yaz" hükmü.

---

## Çekirdek kararlar (13)

1. Adapter sistemin uzuvudur, beyni değildir.
2. Adapter constitutional type yok; capability surface var (Madde 1 adapter yansıması).
3. Manifest immutable signed artifact.
4. Yeni adapter sürümü = yeni manifest hash'i (no runtime mutation).
5. Capability flag tek başına yetki değil; channel binding zorunlu.
6. Capability incompatibility matrix (security separation).
7. `execute → observe` required, ama sadece efference scope.
8. Execute capability multi-condition hard constraints.
9. LLM/human → execution adapter direct route = yasak.
10. `AdapterTrustRecord` M2 subject_class; SourceTrust ile linked ama farklı granül.
11. Tek canonical lifecycle event: `ADAPTER_MANIFEST_STATUS_CHANGED` (B/C/E/F/G/H disiplini).
12. Adapter raw payload üretir; neural_seed her zaman WORLD_INGRESS compiler'dan.
13. Adapter identity observer-only; çekirdeğe sızmaz.

---

## Madde 1 yansıması — adapter seviyesi

A-H boyunca Madde 1 her seviyede yansıdı:
- Nöron (A): homojen denklem, heterojen payload
- Pulse (B): tek WORKSPACE_PULSE, imza var tip yok
- Ingress (C): tek compiler, ingress profile çekirdek-görünmez
- Genome (D): domain-agnostic, tek genome
- Gate testleri (E, G): boolean/sayısal, yargı yok
- Event family (F): audit grouping, davranış değil
- Recall ranking (H): delivery sıralama, hakikat değil

**Adapter (I): tek manifest mekanizması, capability imzası.** TradeAdapter/NewsAdapter/ExecutionAdapter diye tip yok; capability set'i adapter karakterini belirler.

Bu Madde 1'in en son ve en pratik yansıması — sistemin **dış yüzeyinde** bile aynı disiplin.

---

## Önemli sertleştirmeler

### Capability + channel binding ayrımı
Bu I'nın en önemli kavramı. Capability flag "ne yapabilir" derken yetersiz. Channel binding "nereye değer" diye açık deklarasyon yapar.

> *Capability declares what the adapter can technically do.*
> *Channel binding declares how it is allowed to touch the system.*

### Capability incompatibility matrix
Security separation için zorunlu. Aynı adapter execute + recall_provider olamaz (M2 manipulation + action coupling), execute + intent_relay olamaz (LLM bypass riski), recall_provider + memory_writer olamaz (kendi yazdığını okumak — self-deception).

### Required pair efference-only
`execute → observe` zorunluluğu sadece kendi eyleminin sonuçları için. Genel observation authority ayrı `scope: general` declaration gerektirir. Yoksa execution adapter "genel market observer" olur.

### Adapter neural_seed üretemez
WORLD_INGRESS §13'teki "compiler output sadece neural_seed" kuralının adapter seviyesindeki yansıması. Adapter ham + structured event üretir; compiler ton üretir; çekirdek ton yaşar.

### AdapterTrust ≠ SourceTrust
İki ayrı kavram:
- **AdapterTrust:** uzvun kendisinin güvenirliği (manifest valid mi, error rate ne, stale event rate ne)
- **SourceTrust:** uzvun taşıdığı kaynağın güvenirliği (outcome alignment, prediction accuracy)

Multi-source adapter (news_aggregator: reuters + bloomberg + twitter) durumunda AdapterTrust adapter-level, SourceTrust per-source.

### Execute capability hard constraints
`can_execute = true` tek başına yetersiz. Aşağıdakilerin **hepsi** zorunlu:
- valid_manifest_signature
- active_operational_policy_ref
- deontic_gate_ref
- audit_path_available
- kill_switch_respect = true
- no_direct_llm_route = true
- no_direct_human_route = true (audit kanalı hariç)

Kill-switch aktif iken execution adapter eylem çıkartmaz (defense in depth).

---

## Yan güncellemeler (commit'in parçası)

- `MEMORY_CONTRACT.md` M2 subject_class — `adapter_trust` eklendi
- `WORLD_INGRESS.md` §9 — `adapter_capabilities_snapshot` cross-ref
- `WORLD_INGRESS.md` Open Questions — "Adapter manifest formatı" çözüldü olarak işaretli
- `BOOTSTRAP_GENOME.md` §20 — `adapter_manifest_refs` cross-ref
- `BOOTSTRAP_GENOME.md` Open Questions — "Adapter manifest formatı" çözüldü
- `DEONTIC_GATE.md` §8 Rule 7 — ADAPTER_MANIFEST_SPEC §10 cross-ref
- `OBSERVER_LEDGER_SCHEMA.md` §10 permanence policy — `ADAPTER_MANIFEST_STATUS_CHANGED` eklendi (permanent; revoked/security_incident için permanent_with_snapshot)
- `OBSERVER_LEDGER_SCHEMA.md` §19 event catalog ledger_meta family — `ADAPTER_MANIFEST_STATUS_CHANGED` eklendi
- `README.md` — ADAPTER_MANIFEST_SPEC tamamlanmış listesine
- `README.md` Sıradaki — ADAPTER_MANIFEST_SPEC kaldırıldı

---

## Açık kalanlar (implementation/numerics)

- reliability_band threshold'ları (degraded geçiş)
- rate_limit_band sayısal değerleri
- manifest_signature algorithm + key management
- Cross-adapter trust contamination kuralları
- Capability extension protocol (yeni capability tipi)
- Adapter version migration (M2 records geçişi)
- Sandbox adapter discipline

---

## Sıradaki

A + B + C + D + E + F + G + H + I kapandı. Sentinel'in **çekirdek + evidence + iki M2 kapısı + dış uzuv kontratı** zinciri tamam.

Sıradaki belgeler (operational specification / numerics fazı):
- `INGRESS_COMPILER_SPEC.md` — neural_seed mapping numerics + bootstrap rules detail
- `BACKUP_STRATEGY.md` — M0/M1 yedekleme planı, RPO/RTO
- `OBSERVER_LEDGER_NUMERICS.md` — snapshot windows, sampling thresholds
- `BOOTSTRAP_GENOME_NUMERICS.md` — kesin genome parametreleri
- `MEMORY_WRITE_GATE_NUMERICS.md` — gate threshold'ları
- `RECALL_PROTOCOL_NUMERICS.md` — recall threshold'ları, TTL, cooldown
- `ADAPTER_TRUST_NUMERICS.md` — reliability band threshold'ları
- `REPLAY_PROTOCOL.md` — sleep replay + attention replay detay

Bu noktadan sonra belgeler **implementation-yakın**. Conceptual phase'in en son kapsayıcı kontratı I idi.

---

## Kilit cümleler

> **Adapter sistemin uzuvudur. Adapter sistemin beyni değildir.**
>
> **Adapter yetenek bildirir. Sistem sınır uygular. Çekirdek sadece kaynaklı olayların nöral etkisini yaşar.**
>
> **Capability declares what the adapter can technically do. Channel binding declares how it is allowed to touch the system.**
>
> **Execution capability is never a direct command surface. Only deontic-gate-approved action intents are accepted.**
>
> **Adapter raw payload üretir. Adapter neural_seed üretemez.**
>
> **AdapterTrust = uzvun güvenirliği. SourceTrust = kaynağın güvenirliği. İkisi linked ama aynı değil.**
>
> **Required pair `execute → observe` is limited to efference/feedback observation. It does not grant general ObservationEvent authority.**
