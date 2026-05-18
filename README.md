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
- [x] `MEMORY_CONTRACT.md` v0.1 — M0-M3 hafıza sınır anayasası, Memory Write Gate (epistemic), CandidateMemoryRecord statüleri
- [x] `ATTENTION_WORKSPACE.md` v0.1 — Madde 4 alt-spec'i: homojen WORKSPACE_PULSE, pulse imzası (tip değil), dissonant attention, InternalShockEvent ayrımı

### Sıradaki (tasarım belgeleri)

- [ ] `WORLD_MODEL_INGRESS.md` — dış dünya temsili ve giriş kuralları
- [ ] `RECALL_PROTOCOL.md` — recall şema detayı
- [ ] `OBSERVER_LEDGER_SCHEMA.md` — ledger event tipleri
- [ ] `MEMORY_WRITE_GATE.md` — **epistemik gate** (deontic gate'ten ayrı)
- [ ] `DEONTIC_GATE.md` — kategorik action-risk kısıtlarının biçimsel listesi
- [ ] `BOOTSTRAP_GENOME.md` — sistem doğduğunda elinde ne var
- [ ] `ADAPTER_MANIFEST_SPEC.md` — uzuvların standart kontratı
- [ ] `BACKUP_STRATEGY.md` — M0/M1 yedekleme planı

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
