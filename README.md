# Sentinel

> *Proje kodadı: **Sentinel**. Repo slug: **Senitnal**.*

> Bir trading bot değil. Sonradan trading yeteneği takılabilecek bir yapay zihinsel çekirdek.

**Status: Frozen Draft v0.1 — Conceptual documentation phase. No code yet.**

Sentinel'in amacı; sermaye korumacı, şüpheci, çelişkiyi taşıyabilen, kanıtsız kesinleşmeyen, kendi kararlarını gerekçelendiren bir AGI çekirdeği inşa etmektir.

Çekirdek **önce var olur**, sonra dış dünya bağlanır. Borsa, Telegram, panel, emir motoru, strateji — hepsi sonradan **adaptör** olarak takılır; hiçbiri çekirdeğin parçası değildir.

---

## Sentinel ne değildir

- LLM-controlled trading bot değildir
- Strateji motoru değildir
- Otomatik sinyal jeneratörü değildir
- "Hızlıca kar üretmek" projesi değildir
- Akademik spiking neural network simülasyonu değildir
- Halüsinasyona izin veren bir sohbet katmanı değildir

## Sentinel nedir

- Üzerine yetenekler monte edilebilen bir **karar zekâsı**
- Düşünen, hatırlayan, şüphe eden, simüle eden, kararını gerekçelendiren bir çekirdek
- **Sermayeyi korumayı** her şeyin önünde tutan bir varlık
- **Audit edilebilir**; her karar observer ledger'da geriye doğru izlenebilir
- **Hesap verebilir**; "neden böyle düşündü?" sorusu cevaplanabilir
- **Plastik**; deneyimle değişir, ama temel anayasası sabittir

---

## Çekirdek özet — beş cümle

1. **Nöron renk taşır.**
2. **Sinaps yol hafızası taşır.**
3. **Assembly anlam taşır.**
4. **Self-field basınç yapar.**
5. **Deontic gate sınır çizer.**

Üstüne iki kontrol cümlesi:

6. **Observer kanıtlar.**
7. **LLM tercüme eder.**

---

## Anayasa — 7 madde

1. Nöron homojen denklem + heterojen payload + receptor yorumlama
2. Sinaps anlam taşımaz, akış deseninin hafızasını taşır
3. Doğuş minimum genome ile — sıfır değil, modül de değil
4. Düşüncede paralellik, niyette rekabet, eylemde tekleşme
5. Self-field soft pressure, deontic gate hard stop
6. LLM dış tercümandır; çekirdeğin parçası değildir
7. Hafıza ayrılığı — M0/M1/M2/M3 birbirine geçmez

Detay: [`CONSTITUTION.md`](./CONSTITUTION.md)

---

## Felsefe

Sentinel iki temel sezgi üzerine kuruludur:

**Sezgi 1 — Anlam akış deseninde doğar.**

Anlam ne tek nöronda yaşar, ne sinapsta, ne global modülde. Anlam **devrenin kendisidir**. Bir fikir, tekrar çağrılabilen, iç tutarlılığı yüksek, replay testinden geçen stabil bir nöral assembly'dir. Bir defa yanan desen gürültüdür; geri dönebilen ve işe yarayan desen fikirdir.

**Sezgi 2 — Zekânın belirtisi durabilmektir.**

Zekânın en açık belirtisi harekete geçmek değil, kendini durdurabilmek. Bu yüzden Sentinel'in en sık verdiği karar `ALLOW` değil, `WAIT` ve `BLOCK` olmalıdır. Sistem şunu sormadan eyleme geçmez:

- Ne biliyorum?
- Neye inanıyorum? Neden inanıyorum?
- Neyi bilmiyorum?
- Yanılırsam ne olur?
- Hiçbir şey yapmazsam ne olur?
- Geçmişte buna benzeyen ne oldu?

Bu soruları sormayan sistem AGI değil, sadece otomasyondur.

---

## Mevcut durum — Conceptual Documentation Phase

**Henüz kod yok ve uzun süre olmayacak.** Proje şu an mimari ve felsefi tasarım aşamasındadır. Düşünmek, konuşmak, belgelemek; sonra inşa etmek. Bütün belgeler **Frozen Draft v0.1 / no implementation authority** statüsündedir — kod bunlardan değil, sonraki implementation belgelerinden türetilecektir.

### Tamamlanmış

- [x] `CONSTITUTION.md` v0.1 — 7 maddelik temel anayasa (Principle / Rationale / Allowed / Forbidden / Violation Test formatında)
- [x] `MEMORY_CONTRACT.md` v0.1 — M0-M3 hafıza sınır anayasası, Memory Write Gate (epistemic), CandidateMemoryRecord statüleri, M2 `subject_class` alt-türleme
- [x] `ATTENTION_WORKSPACE.md` v0.1 — Madde 4 alt-spec'i: homojen WORKSPACE_PULSE, pulse imzası (tip değil), dissonant attention, InternalShockEvent ayrımı
- [x] `WORLD_INGRESS.md` v0.1 — Dış dünya giriş sınırları: 4 ingress profile (Observation/Recall/HumanIntent/InternalShock), IngressEventEnvelope, deterministic compiler, SourceTrustRecord M2 alt-tipi
- [x] `BOOTSTRAP_GENOME.md` v0.1 — Madde 3 alt-spec'i: doğum anayasası, initial M0/M1/M2/M3 state, SELF_GENESIS şeması, payload modulation reflexes, plasticity yaş-değil-state-based, constitutional shift policy (3 compatibility class)
- [x] `DEONTIC_GATE.md` v0.1 — Madde 5 alt-spec'i: anayasal eylem çıkış sınırı, 11 constitutional declarative, DeonticPolicyRecord (M2 alt-tipi), block classification (routine/safety/constitutional), bypass attempt iki-seviyeli audit, kill-switch graduated deactivation
- [x] `OBSERVER_LEDGER_SCHEMA.md` v0.1 — M1 detayı: ObserverEvent envelope (audit/causal/body/integrity), recorder/summarizer rol ayrımı, event type vs field disiplini, deterministic permanence policy table (no-default), snapshot window policy + deterministic sampling, hash chain, read/write permission matrix, 7 event family (ledger_meta dahil)
- [x] `MEMORY_WRITE_GATE.md` v0.1 — Madde 7 / MEMORY_CONTRACT §9 alt-spec'i: epistemik fren (deontic gate ≠), subject_class × evidence axes verification matrix, self-deception detection mekaniği, statü makinesi (candidate/verified/active/quarantined/superseded/rejected/expired), human writes vs system writes ayrımı (auto-verified vs matrix-required), silent gate (çekirdeğe geri yansıma yok), `MEMORY_RECORD_STATUS_CHANGED` canonical event
- [x] `RECALL_PROTOCOL.md` v0.1 — Madde 7 / MEMORY_CONTRACT §5-6 alt-spec'i: M2'den çekirdeğe hatırlatma protokolü (Memory Write Gate'in çift kapısı), recall is sensory ingress not retrieval, core-originated RecallRequest, hybrid scope, ranking is delivery not truth, top-1 RecallEvent + audit alternates, candidate recall sadece source_trust/procedural için capped intensity, human-requested recall HumanIntentEvent tetikleyici (doğrudan değil), operational audit ayrı kanal, recall failure (RECALL_RESULT_EMPTY) audit-only — çekirdeğe yokluk payload'ı basılmaz
- [x] `ADAPTER_MANIFEST_SPEC.md` v0.1 — Dış uzuv kontratı: immutable signed manifest, adapter type yok / capability surface var, capability flags + channel bindings (explicit yetki haritası), capability incompatibility matrix (security separation), `execute → observe` required pair (efference-only scope), execution capability hard constraints, `AdapterTrustRecord` M2 alt-tipi (SourceTrust ile linked ama farklı), tek canonical `ADAPTER_MANIFEST_STATUS_CHANGED` lifecycle event, adapter raw payload üretir / neural_seed üretemez

### Sıradaki (operasyonel specification belgeleri)
- [ ] `INGRESS_COMPILER_SPEC.md` — neural_seed mapping numerics + bootstrap rules detail
- [ ] `BACKUP_STRATEGY.md` — M0/M1 yedekleme planı, RPO/RTO
- [ ] `OBSERVER_LEDGER_NUMERICS.md` — snapshot windows, sampling thresholds, segment sizes
- [ ] `BOOTSTRAP_GENOME_NUMERICS.md` — kesin genome parametreleri

Sıralama tasarım sohbetinin akışına göre değişebilir.

### Uzak hedef (kod aşaması)

- [ ] Minimum Viable Brain — hiçbir aksiyon almayan ama her input'a gerekçeli BLOCK/WAIT cevabı veren çekirdek
- [ ] Echo Adapter — sahte uzuv, sadece test için
- [ ] İlk gerçek adaptörler

Kod aşamasına geçmeden önce yukarıdaki tasarım belgelerinin tamamlanması beklenir.

---

## Repo yapısı

```
Senitnal/
├── README.md              # Bu dosya
├── CONSTITUTION.md         # 7 maddelik anayasa
├── MEMORY_CONTRACT.md      # M0-M3 hafıza sınırları
├── LICENSE                # Apache 2.0
├── .gitignore
└── docs/                  # Detay belgeleri (yazılacak)
    └── conversations/     # Tasarım konuşmalarının arşivi
```

---

## Katkı politikası

Bu proje şu an sadece belgeleme aşamasındadır. Herhangi bir pull request veya issue için:

- Önerinin `CONSTITUTION.md`'deki 7 maddeyi ihlal etmemesi gerekir
- İhlal eden öneriler ya reddedilir ya da resmi revizyon süreciyle anayasa güncellenir
- Revizyon süreci tartışma → gerekçe → yeni metin → versiyon artırımı → tarih notu sırasını takip eder

Anayasa, dokunulmaz olduğu için değil, dokunulmazlığı korumak için ciddiye alındığı için çalışır.

---

## Lisans

Apache 2.0 — bkz. [`LICENSE`](./LICENSE)
