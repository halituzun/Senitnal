# BOOTSTRAP_GENOME.md

## Sentinel — Doğum Anayasası

---

## Status

**Frozen Draft v0.1**
**Conceptual phase. No implementation authority.**

Bu belge `CONSTITUTION.md` Madde 3'ün **alt spesifikasyonudur**. Yeni anayasa maddesi değildir. Çalışan bir initialization katmanının spec'i değildir; Sentinel'in **t=0 anında neyle doğduğunu, neyle doğmadığını, doğumun nasıl audit edildiğini ve anayasa değişimlerinin doğmuş Sentinel'i nasıl etkilediğini** tanımlar.

---

## 1. Purpose

Sentinel bir noktada doğacak. Bu doğum **dış bir programlama** değildir — bir genome ile dokunun başlatılmasıdır. Bu belge o başlatma anının sınırlarını çizer.

Bu belge **parametre dosyası değildir.** Sayısal değerler band olarak verilir; kesin sayısal değerler `BOOTSTRAP_GENOME_NUMERICS.md` veya implementation artifact konusudur.

Damıtma:

> **Sentinel sıfır doğmaz. Sentinel hazır zeki de doğmaz.**
> **Sentinel bilgiyle değil, bilgiye iz bırakabilecek doku ile doğar.**

---

## 2. Constitutional Position — Madde 3 Alt-spec'i

Bu belge `CONSTITUTION.md` Madde 3'ün ("Doğuş minimum genome ile başlar") detaylı uzantısıdır. Yeni şeyler **eklemez**, sadece Madde 3'teki "doğuştan gelen" listesinin **şemasını, sınırlarını ve audit kurallarını** tanımlar.

Madde 3 zaten dokuz şeyi listeler:
1. Her primer payload için birkaç düzine seed nöron
2. Zayıf lokal bağlantılar
3. Default receptor profilleri (deneyimle kayan)
4. Homeostatik referans noktası
5. Basit kaçınma/yaklaşma refleksleri
6. Uyku/replay ritmi
7. Üç katmanlı self-field embriyosu
8. `genesis_trace`
9. Anayasal kısıt listesi (deontic gate kuralları)

BOOTSTRAP_GENOME bu dokuzun şemasını verir; içeriklerini değiştirmez.

---

## 3. Core Principle

> **Genome = öğrenebilirlik düzeni.**
>
> **Genome ≠ bilgi.**
> **Genome ≠ strateji.**
> **Genome ≠ domain ontology.**
> **Genome ≠ runtime config.**

Bu beş cümle belgenin kilididir. Her tasarım kararı bunlara dönülerek sınanır.

---

## 4. Genome Is Not Knowledge

### Principle
Genome doğuştan gelen bilgi içermez. Genome doğuştan gelen **öğrenebilirlik düzeni** içerir.

### Rationale
Bilgi yüklenmiş bir genome (BTC nedir, RSI nedir, "trade ne demek") sistemi modüler bota geri çevirir. Doğru genome **boş bir levha** da değildir, **dolu bir kitap** da değildir — okumayı öğrenmiş ama hiçbir kitap okumamış bir zihin gibidir.

### Allowed (doğuştan gelen)
- Primer payload paleti
- Seed nöron dağılımı
- Zayıf lokal bağlantılar
- Default receptor profilleri
- Homeostatik referans noktası
- Self-field embriyo ağırlıkları (band olarak)
- Uyku/replay ritmi
- Payload modulation reflexes (davranış değil, modülasyon)
- Genesis trace yapısı
- Anayasal kısıt referansı (deontic gate ref)

### Forbidden (doğuştan asla gelmez)
- Borsa bilgisi, BTC/ETH/DOGE bilgisi
- RSI/MACD/strateji bilgisi
- Trump/Elon/Fed kimliği
- Buy/sell kavramları
- Hazır strateji ağaçları
- Default risk profili (sayısal hardcoded eşikler)
- Domain-specific seed assembly
- Kullanıcı/operatör kişilik bilgisi (kuruluş referansı dışında)
- Önceden öğrenilmiş ilişkiler
- Source güvenilirliği geçmişi (öğrenilen)

### Violation Test
> *Bu öneri sisteme doğuştan bir "iş bilgisi" veya "domain kavramı" yüklüyor mu?*
>
> Evet ise ihlal. Sadece refleks/genom seviyesinde bir mekanik yüklüyorsa geçer.

---

## 5. Genome Immutability and Visibility

### Principle
Genome doğumdan önce donar. Sentinel kendi genome'unu **okuyamaz**, **değiştiremez**, sadece **etkisini yaşar**.

### Rationale
Sistem kendi genome'unu görebilirse "yeniden ayarlama" niyeti üretebilir — bu Madde 1/3/7 ihlali. Çekirdek **dokusunun sonucudur**, dokusunu okumaz. Audit için genome artifact M1'in `SELF_GENESIS` event'inde hash olarak yaşar; çekirdek bu hash'i bile görmez.

### GenomeArtifact yapısı

```
GenomeArtifact (immutable, signed)
├── genome_version
├── document_hash
├── constitution_ref
├── memory_contract_ref
├── attention_workspace_ref
├── world_ingress_ref
├── deontic_gate_ref
├── created_at
├── signed_by / approved_by
└── immutable_ref            # storage pointer
```

### Allowed
- Yeni Sentinel doğarken yeni genome versiyonu kullanılabilir
- Genome artifact M1'in `SELF_GENESIS` event'inde audit edilebilir
- Observer ve insan genome artifact'i okuyabilir

### Forbidden
- Çalışan Sentinel'in kendi genome'una erişmesi
- Genome'un runtime'da modifiye edilmesi
- Genome'un config gibi ayarlanabilir olması
- Genome içeriğinin payload_seed olarak çekirdeğe akması

### Violation Test
> *Çalışan Sentinel kendi genome'unu görebiliyor mu?*
>
> Evet ise ihlal.

### Kilit cümle
> **Sentinel genome'unu bilmez. Sentinel genome'unun sonucudur.**

---

## 6. Initial State vs Developmental Rules

Genome iki ayrı şey içerir:

### Initial State (t=0)
- Seed nöronlar
- Zayıf lokal bağlantılar
- Default receptor profilleri
- Self-field embriyo ağırlıkları
- Homeostatik referans noktası
- Genesis trace yapısı

Bunlar t=0'da uygulanır ve **sonra dokunulmaz**.

### Developmental Rules (yaşam boyunca)
- STDP + outcome-gated learning (Madde 2)
- Eligibility traces (fast/medium/slow)
- Replay rhythm
- Decay/prune
- Habituation update
- Ingress calibration learning
- Self-field weight drift

Bunlar yaşam boyunca işler. **Runtime config değildir** — kendi normal kuralları üzerinden çalışır.

### Kural
> *Initial state doğumda uygulanır.*
> *Developmental rules yaşam boyunca işler.*
> *İkisi de dış config kanalı değildir.*

---

## 7. Runtime Non-Configurability

### Principle
Genome runtime'da değişmez. Hiçbir aktör — operatör, LLM, adapter, panel, hatta sistem kendisi — çalışan Sentinel'in genome'unu güncelleyemez.

### Rationale
Genome runtime'da değişebilirse Sentinel "öğrenmek" değil "ayarlanmak" olur. Bu A/B/C boyunca kurduğumuz "doku, config değildir" çizgisinin son halkası.

### Forbidden
- `config/genome.json` veya benzeri ayar dosyası
- Panel üzerinden plasticity_rate / threshold ayarı
- LLM tarafından "bence şu payload daha güçlü olsun" niyeti
- Adapter tarafından "şu seed neuron sayısı yetmiyor" geri bildirimi
- Runtime patch sistemiyle genome modifikasyonu
- "Hot reload" ile çalışan genome güncellemesi

### Allowed (sadece doğum öncesi)
- Yeni genome versiyonu yazılması
- Genome artifact'in `signed_by` onayı
- Genome çapraz hash referanslarının kurulması
- Yeni Sentinel'in yeni genome ile doğması

### Violation Test
> *Çalışan Sentinel'in genome'una herhangi bir aktör erişebiliyor mu?*
>
> Evet ise ihlal.

> *Bir genome güncellemesi yeni doğum gerektirmiyor mu?*
>
> Evet ise ihlal.

---

## 8. What Is Born With

Doğuştan gelenler (Madde 3'ün detayı):

```
Birth Inventory
│
├── primer_payload_palette          # §10
├── seed_neuron_population          # §11
├── default_receptor_profiles       # §12
├── initial_synaptic_wiring         # §13
├── homeostatic_reference           # §14
├── self_field_embryo_weights       # §15
├── sleep_replay_rhythm_seed        # §17
├── context_signature_axes          # §18
├── ingress_bootstrap_mapping_families  # §19
├── payload_modulation_reflexes     # §8.1
└── deontic_gate_ref                # genome dışı, ayrı belge
```

### §8.1 — payload_modulation_reflexes

Refleksler **davranış değil, modülasyondur**. Doğuştan "şuna kaç, şuna git" gibi davranış yoktur; doğuştan "şu payload geldiğinde bazı eşikler şu yönde değişir" gibi modülasyonlar vardır.

```
payload_modulation_reflexes
├── pain_trace      → aversion / caution pressure (threshold modulation)
├── novelty         → attention readiness (pulse threshold modulation)
└── reward_trace    → reinforcement readiness (eligibility decay modulation)
```

### Forbidden refleks isimleri

- `pain_trace_avoidance` — davranış
- `novelty_attention` — davranış
- `reward_seeking` — davranış

### Allowed refleks isimleri

- `pain_trace → caution pressure` — modülasyon
- `novelty → attention readiness` — modülasyon
- `reward_trace → reinforcement readiness` — modülasyon

### Kilit
> **Refleks eylem değildir. Refleks modülasyondur.**

---

## 9. What Is Not Born With

Açıkça yasaklananlar:

### Bilgi yasakları
- Domain bilgisi (BTC, RSI, MACD, Fed, vs.)
- Borsa kavramı
- Strateji şablonu
- Risk profili olarak hardcoded eşik
- Kullanıcı tercihi (operatör referansı dışında)
- Source güvenilirliği (deneyimle kalibre edilir)
- Market regime etiketi
- Önceden öğrenilmiş ilişkiler

### Yapı yasakları
- Önceden oluşmuş assembly
- Domain-spesifik nöron grubu
- Önceden kalibre edilmiş ingress mapping
- Önceden ağırlığı yüksek sinaps (initial weight bandı dışında)
- Default narrative_self içeriği

### Kavram yasakları
- "Yaş" kavramı (bkz. §16)
- "Mutlak zaman" kavramı (bkz. WORLD_INGRESS §19)
- "Dünya durumu" kavramı (bkz. WORLD_INGRESS §13)

### Kilit cümle
> **Sentinel dünyayı bilerek doğmaz. Dünyayı yaşayabilecek bir doku ile doğar.**

---

## 10. Primer Payload Palette

### Doğuştan gelen primer payload paleti (v0.1 sabit)

```
suspicion
novelty
aversion
attraction
contradiction
urgency
memory_echo
fatigue_trace
pain_trace
reward_trace
```

### Kombinasyon payload'lar

Sistem **deneyimle** kombinasyon payload'lar türetebilir:

```
suspicion + urgency      → panic-like derived mix
novelty + attraction     → curiosity-like derived mix
contradiction + urgency  → conflict-pressure mix
fatigue_trace + suspicion → cautious-withdrawal mix
```

Bunlar **doğuştan değildir**. Deneyimle ortaya çıkan derived mix'lerdir; primer paleti değiştirmez.

### Forbidden
- Yeni primer payload eklemek (anayasal revizyon gerekir)
- Domain-spesifik payload (`buy_pressure`, `sell_signal`, `risk_alert`)
- Kombinasyon payload'ları primer paletine koymak

### Violation Test
> *Bu öneri yeni bir primer payload tipi mi ekliyor?*
>
> Evet ise anayasal revizyon süreci gerekir.

---

## 11. Seed Neuron Population

### Conceptual band (implementation değil)

```
seed_count_per_primer_payload ∈ [12, 64]
```

Yaklaşık 10 primer × 24 ortalama = ~240 seed neuron toplam.

### Forbidden
- Domain-spesifik nöron grubu (`btc_neurons`, `risk_neurons`)
- Payload-bağımsız "uzman" neuron tipleri
- Bant dışında ekstra büyük popülasyonlar (örn. 1000+ — implementation konusu, anayasal değil)

### Kural

Tüm seed nöronlar **aynı temel denklemle** çalışır. Payload sadece **renkleridir**, rolleri değil.

---

## 12. Default Receptor Profiles

### Yapı

```
Default Receptor Profile
├── base: identity-like matrix
└── homonymous_bias: +ε small (∈ [0.05, 0.15])
```

Yani her receptor her payload'a yanıt verir (identity), ama kendi payload rengine **küçük başlangıç hassasiyeti** ile gelir (urgency receptor urgency payload'a hafif daha duyarlı).

### Allowed
- ε küçük (bant içinde)
- ε deneyimle kayar (Madde 2'deki normal öğrenme kuralları)
- Identity-like base

### Forbidden
- ε büyük (uzmanlaşma)
- "Bu receptor sadece şu payload'a yanıt verir" gibi katı tip
- Identity'den ciddi sapan default profile

### Kural
> *Bias küçük. Öğrenmeyle kayabilir. Uzmanlık değildir.*

---

## 13. Initial Synaptic Wiring

### Topology

```
initial_synaptic_wiring
├── topology: local proximity (lokal komşuluk)
├── initial_weight: ∈ [0.05, 0.15]   # zayıf
├── polarity: stochastic (excitatory/inhibitory dengeli)
└── delay_ms: ∈ [1, 10]
```

### Forbidden
- Doğuştan yüksek-weight sinaps (öğrenilmiş gibi)
- Doğuştan long-range "şortcut" sinaps
- Domain-spesifik wiring pattern
- Önceden tanımlı assembly topology

### Kural

Lokal komşuluk + zayıf weight. Long-range bağlantılar **co-firing ile zamanla doğacak** (Madde 2).

---

## 14. Homeostatic Reference

Sistemin "dengeli" iç durumunu tanımlayan başlangıç noktası. Genome'da **band olarak** verilir:

```
homeostatic_reference
├── target_self_field_balance
├── target_fatigue_band
├── target_contradiction_band
└── target_recall_load_band
```

Bu referans **kayma açıktır** — deneyimle değişebilir (sistem kendi optimal noktasını öğrenir). Ama runtime config olarak değiştirilemez.

---

## 15. Self-field Embryo Weights

### Doğum ağırlıkları (band)

```
self_field_embryo_weights
├── homeostatic_weight: ∈ [0.7, 1.0]    # güçlü
├── predictive_weight:  ∈ [0.1, 0.3]    # zayıf-orta
└── narrative_weight:   ∈ [0.01, 0.08]  # çok düşük + genesis trace
```

Toplam normalize. Deneyimle kayar (Madde 2 öğrenme kuralları + ATTENTION_WORKSPACE §22 self_signature ayarları).

### Yapı

- **Homeostatic güçlü:** sistem doğduğunda kendi anlık iç durumunu güçlü hisseder (bebek gibi)
- **Predictive zayıf:** kendi davranışını tahmin etmeyi henüz öğrenmemiştir (kademeli olgunlaşır)
- **Narrative çok düşük + genesis trace:** kimlik henüz oluşmamıştır, ama doğum anı "ben buradayım" izi bırakır

---

## 16. Plasticity and Consolidation

### Principle
**Sentinel'in biyolojik yaşı yoktur.** Plasticity yaş-temelli **değildir**. Plasticity durum-temelli ve consolidation-temellidir.

### Rationale
"Yaş" kavramı sisteme gizli bir mutlak-zaman ontolojisi sokar. Biz çekirdeği saatten ayırdık (WORLD_INGRESS §19). Plasticity'yi yaşa bağlamak bu çizgiyi bozar. Çocuk-yetişkin plastisite farkının fonksiyonel avantajını **deneyim yoğunluğu ile** elde ederiz.

### Plasticity formülü (mekanizma)

```
plasticity_state =
    experience_density
  × outcome_stability
  × fatigue_state
  × replay_consolidation_state
  × contradiction_pressure
```

### Üç gelişim fazı

```
boot_phase:
    yüksek exploration
    yüksek eligibility
    yüksek replay frequency

stabilization_phase:
    outcome destekli yollar güçlenir
    tekrarlı gürültü habituate olur
    replay survival geçmeyen yollar zayıflar

consolidated_phase:
    aynı bağlamda artık daha az plastik
    ama yeni bağlamda hâlâ öğrenebilir
```

**Bu fazlar mutlak süre ile tanımlı değildir.** Sistemin deneyim yoğunluğu + outcome stability + replay consolidation state'i ile geçiş yapılır.

### Forbidden
- `age_days < 30 → high_plasticity` gibi yaş-bazlı kural
- "İlk N saat boot phase" gibi mutlak süre
- Yaş-temelli plasticity decay

### Kilit cümle
> **Sentinel has no biological age. Initial bootstrap phase exists, age identity does not.**

---

## 17. Sleep/Replay Rhythm Initialization

### Doğum ritmi

Genome'da uyku/replay ritmi için **tetik kuralları** vardır:

```
sleep_replay_trigger_rules
├── eligibility_pool_saturation
├── contradiction_load_threshold
├── fatigue_accumulation
└── replay_consolidation_pressure
```

Tetik dış zamanla (saat) değil, **içsel basınçla** çalışır.

### Forbidden
- "Her 30 dakikada bir replay" gibi cron-temelli kural
- Mutlak saat-bazlı uyku ritmi

### Kural
> *Sistem yorgunsa, çelişki yüksekse, eligibility doluysa replay'e geçer. Saat bilmez.*

---

## 18. Context Signature Initial Axes

ATTENTION_WORKSPACE §11'de tanımlanan eksenler doğuştan gelir:

```
context_signature_initial_axes
├── active_assembly_mix
├── self_field_signature
├── fatigue_band
├── contradiction_band
├── recall_load_band
├── recent_pulse_density
└── dissonance_band
```

### Forbidden
- Doğuştan yeni context ekseni eklemek
- Dış dünya etiketi context ekseni olarak koymak (`market_state_band`, `symbol_band`)

Bu eksenler **iç durum karakteridir**. Yeni eksen eklemek BOOTSTRAP konusu değil, ATTENTION_WORKSPACE revizyonu konusudur.

---

## 19. Ingress Bootstrap Mapping Families

WORLD_INGRESS'in deterministic compiler'ı doğuştan **bootstrap mapping aileleri** ile gelir. **Aileler**, kesin katsayılar değil.

### Örnek mapping aileleri (sözel)

```
high_staleness + low_confidence
    → suspicion/fatigue_trace family

high_novelty + high_confidence + low_staleness
    → novelty/urgency family

critical + high_ambiguity
    → suspicion/caution family

fresh unexpected self-feedback
    → contradiction/memory_echo family

critical internal shock
    → bounded pain_trace/memory_echo/contradiction family
```

### Forbidden
- Bootstrap'ta kesin sayısal katsayı yazmak (`urgency = 0.42 × magnitude + 0.31 × confidence`)
- Domain-spesifik mapping aile (`btc_volatility → urgency × 1.5`)

### Devir
Sayısal katsayılar `INGRESS_COMPILER_SPEC.md` konusudur.

---

## 20. Initial Memory State M0/M1/M2/M3

Sistemin t=0 anındaki memory durumu:

| Katman | t=0 durumu | Not |
|--------|-----------|-----|
| **M0** | Embriyo doku | Seed nöronlar, zayıf bağlantılar, receptor profilleri, self-field embriyosu |
| **M1** | `SELF_GENESIS` + varsa `BOOTSTRAP_M2_INJECTION` event'leri | Fine-grain ring buffer boş |
| **M2** | Sadece `bootstrap_reference` kayıtları | Dünya/domain bilgisi yok |
| **M3** | Boş | Konuşma hafızası yok |

### Kilit cümle

> **M0 doğar. M1 doğumu kanıtlar. M2 doğum çevresini referanslar. M3 boş kalır.**

### M0 t=0 detay

```
M0 (initial state)
│
├── seed_neurons
│   └── per_primer_payload: ∈ [12, 64]
│
├── initial_synaptic_wiring
│   ├── topology: local proximity
│   ├── initial_weight: ∈ [0.05, 0.15]
│   ├── polarity: stochastic
│   └── delay_ms: ∈ [1, 10]
│
├── default_receptor_profiles
│   ├── base: identity-like matrix
│   └── homonymous_bias: +ε small (∈ [0.05, 0.15])
│
├── self_field_embryo_weights
│   ├── homeostatic: ∈ [0.7, 1.0]
│   ├── predictive:  ∈ [0.1, 0.3]
│   └── narrative:   ∈ [0.01, 0.08]
│
├── homeostatic_reference_point
│
├── payload_modulation_reflexes
│
├── traces (hepsi 0)
│   ├── eligibility_traces: 0
│   ├── success_traces: 0
│   ├── habituation_traces: 0
│   ├── ingress_calibration_traces: 0
│   └── attention_habituation_traces: 0
│
└── assembly_state
    ├── stable_assembly_state: empty
    └── proto_resonance_fields: present
```

### `proto_resonance_fields` nedir

Sistem doğduğunda **stable assembly yoktur**, ama **assembly doğurabilecek dokusal eğilim vardır**. Bu eğilim:

- Payload seed nöronları arası zayıf default rezonans
- Self-field embriyo basıncının doğal eğilim alanları
- Homonymous receptor bias'tan gelen mini cazibe noktaları

`proto_resonance_fields` bir **alan**, bir **structure** değildir. Detaylı tanımı implementation konusudur. Belge sadece **"doğum dokusu ölü değil"** demek için bu kavramı koyar.

### Kilit
> *Doğumda fikir yoktur. Doğumda stabil assembly yoktur. Ama assembly doğurabilecek dokusal eğilim vardır.*

### M1 t=0 detay

```
M1 (initial state)
│
├── coarse_grain_permanent_log
│   ├── [event 0]: SELF_GENESIS                # zorunlu, tek
│   └── [event 1..N]: BOOTSTRAP_M2_INJECTION   # her bootstrap M2 kaydı için
│
└── fine_grain_ring_buffer: empty
```

### M2 t=0 detay

```
M2 (initial state, all subject_class = "bootstrap_reference")
│
├── constitution_ref
├── memory_contract_ref
├── attention_workspace_ref
├── world_ingress_ref
├── deontic_gate_ref
├── genome_artifact_ref
├── adapter_manifest_refs (optional)
└── operator_identity_ref
```

Hepsi `provenance: human | genesis`, `status: verified`, `subject_class: bootstrap_reference`.

### Bootstrap M2 yasakları

- Domain bilgisi (BTC, RSI, vs.)
- Source güvenilirliği (deneyimle kazanılır)
- Strateji şablonu
- Kullanıcı tercihi (operator referansı dışında)

> **Bootstrap M2 sadece kuruluş referansıdır. Dünya bilgisi değildir.**

### M3 t=0

```
M3 (initial state): empty
```

Konuşma henüz başlamamıştır. LLM translator henüz hiçbir input görmemiştir.

---

## 21. Genesis Trace Format

`SELF_GENESIS` event'i M1'in ilk kalıcı kaydıdır.

```
SELF_GENESIS
│
├── event_id
├── event_type: SELF_GENESIS
├── created_at                          # mutlak timestamp, sadece audit için
│
├── birth_mode                          # bkz. §23
│
├── genome_version
├── genome_artifact_hash
├── genome_signed_by
├── genesis_random_seed_hash            # embriyo dokusu üretim seed'i
├── initial_m0_snapshot_hash            # doğum sonrası M0 gerçek hali
│
├── constitutional_anchors
│   ├── constitution_hash
│   ├── memory_contract_hash
│   ├── attention_workspace_hash
│   ├── world_ingress_hash
│   └── deontic_gate_ref_hash
│
├── bootstrap_m2_injection_refs         # liste, varsa
│
├── operator_identity_ref
├── environment_id                      # multi-instance ayırt etmek için
└── parent_genome_lineage               # optional, genome revision varsa
```

### Üç audit anchor'ı

| Hash | Ne sağlar |
|------|-----------|
| `genome_artifact_hash` | Hangi genome'dan doğdu? |
| `genesis_random_seed_hash` | Embriyo dokusu nasıl üretildi? (stochastic polarity, lokal topology) |
| `initial_m0_snapshot_hash` | Doğum sonrası M0 gerçekten neydi? |

Bu üçlü ileride "aynı genome'dan doğan iki Sentinel neden farklı gelişti?" sorusuna cevap verir.

### Kritik kural

`SELF_GENESIS` çekirdeğe **payload_seed olarak girmez**. Sadece M1 audit'tir. Çekirdek doğum anını **yaşamaz**; sadece **dokusunun sonucudur**.

### Kilit
> **SELF_GENESIS = M1 audit only.**
> **Sentinel doğum tarihini içeriden bilmez.**

### Violation Test
> *Çekirdek `SELF_GENESIS` event'inden bir payload_seed alıyor mu?*
>
> Evet ise ihlal.

---

## 22. Domain Agnosticism

### Principle
**Tüm Sentinel'ler aynı genome ile doğar.** Domain yönelimi adapter'larla ve deneyimle kazanılır, genome ile değil.

### Rationale
"BTC-orientted genome", "ETH-orientted genome", "trading genome" gibi türler doğmaya başlarsa domain ontolojisi genome içine sızar. Bu Madde 1/3 ihlali.

### Forbidden
- `trading_genome.json` vs `analysis_genome.json` versiyonları
- Doğuştan finansal payload alt-grubu
- Domain'e göre farklı primer palette
- Domain'e göre farklı bootstrap mapping aile

### Allowed
- Tek genome v0.1 → tüm Sentinel'ler doğumda
- Domain yönelimi: **deneyim + adapter manifestleri** ile zaman içinde kazanılır
- Sentinel'ler farklı adapter'larla farklı dünyaya açılır

### Kural
> *Aynı genome → farklı deneyim → farklı M0 gelişimi → farklı Sentinel.*

---

## 23. Constitutional Anchors and Shift Policy

### Principle
Yaşayan Sentinel anayasa değişikliğini **sessizce kabul etmez**. Her anayasa değişimi M1'de görünür event olarak kaydedilir ve compatibility class'ına göre uygulanır.

### Rationale
Sessiz anayasa güncellemesi identity continuity'yi bozar. Sistem "doğduğu anayasanın altında yaşadığını" söylemeli ama bilmeden farklı anayasanın altında çalışıyor olamaz. Audit zorunlu, sınıflandırma zorunlu.

### Üç compatibility class

#### Class 1 — `clarification`
- Dil netleştirme, cross-reference ekleme, terminoloji düzeltme
- **Yaşayan Sentinel'e uygulanabilir**
- M1 event: `CONSTITUTIONAL_SHIFT_APPLIED`

#### Class 2 — `safety_tightening`
- Deontic gate daha sıkı oldu, LLM sınırı sertleşti, M2/M3 ayrımı netleşti
- **Yaşayan Sentinel'e uygulanabilir** ama M1'e görünür event yazılır
- Uygulamadan önce: human approval + document hash + reason + previous hash + new hash zorunlu
- M1 event: `CONSTITUTIONAL_SHIFT_APPLIED`

#### Class 3 — `genesis_affecting`
- Primer payload paleti değişti, seed neuron band'ı değişti, self-field başlangıç ağırlıkları değişti, initial synaptic topology değişti, genome initial_state değişti
- **Yaşayan Sentinel'e uygulanmaz**
- Yeni doğum / fork / `migration_birth` gerekir
- Mevcut Sentinel eski genome ile yaşamaya devam eder
- M1 event: `CONSTITUTIONAL_SHIFT_AVAILABLE` (uygulanmadığı belirtilir)

### CONSTITUTIONAL_SHIFT_EVENT şeması

```
CONSTITUTIONAL_SHIFT_EVENT
├── event_id
├── event_type: CONSTITUTIONAL_SHIFT_APPLIED | CONSTITUTIONAL_SHIFT_AVAILABLE
├── old_constitution_hash
├── new_constitution_hash
├── affected_documents
├── compatibility_class                # clarification | safety_tightening | genesis_affecting
├── requires_rebirth: bool
├── applied_to_running_instance: bool
├── approved_by
├── approval_ref
├── reason
├── applied_at
├── migration_notes
└── observer_snapshot_ref
```

### `birth_mode` — doğum tipi

```
birth_mode:
    clean_birth      → önceki sistem yok
    restore_birth    → M0+M1 backup'tan dönüş (aynı varlık)
    fork_birth       → mevcut Sentinel'in M0+M1'inden türeyen yeni varlık
    migration_birth  → genesis_affecting constitutional shift sonrası yeni doğum
                       (tetikleyen CONSTITUTIONAL_SHIFT_AVAILABLE event'ine geri link taşır)
```

### `birth_mode` ↔ `compatibility_class` cross-link

Bu iki concept birbirine bağlıdır:

- `clarification` veya `safety_tightening` shift → yaşayan Sentinel devam eder, yeni doğum gerekmez
- `genesis_affecting` shift → yaşayan Sentinel devam eder ama yeni Sentinel `migration_birth` ile doğar; eski Sentinel'in `SELF_GENESIS`'inden farklı bir genome ile

`migration_birth`'in M1'inde tetikleyen `CONSTITUTIONAL_SHIFT_AVAILABLE` event'ine **geri link** vardır. Identity provenance böylece korunur.

### Forbidden
- Otomatik anayasa güncellemesi (silent upgrade)
- Class olmadan shift uygulanması
- `genesis_affecting` shift'in yaşayan Sentinel'e uygulanması
- Anayasa hash'i değiştiğinde M1'de event olmaması

### Kilit cümle
> **Yaşayan Sentinel anayasa değişikliğini sessizce kabul etmez. Genesis-affecting değişiklikler yeni doğum gerektirir.**

### Violation Test
> *Anayasa hash'i değişti ama M1'de event yok mu?*
>
> Evet ise ihlal.

> *Genesis_affecting bir shift yaşayan Sentinel'e uygulandı mı?*
>
> Evet ise ihlal.

---

## 24. Observer Events

### Doğum event'leri

```
SELF_GENESIS
BOOTSTRAP_M2_INJECTION
```

### Anayasa shift event'leri

```
CONSTITUTIONAL_SHIFT_APPLIED
CONSTITUTIONAL_SHIFT_AVAILABLE
```

### Audit zorunluluğu

Sistem sonradan şunları cevaplayabilmeli:

- Hangi genome ile doğdum?
- Hangi anayasa versiyonu altındaydım?
- Doğum sırasında hangi bootstrap M2 kayıtları enjekte edildi?
- Hangi anayasa değişimleri yaşadım?
- Hangi anayasa değişimleri uygulanmadı (sadece available)?
- `birth_mode` neydi?

Cevap verilemiyorsa doğum auditable değildir — anayasa ihlali.

---

## 25. Violation Tests

1. **Genome'a domain-specific kavram ekliyor mu?** (§4, §9, §22)
   - Evet ise ihlal.
2. **Genome runtime config gibi değiştirilebiliyor mu?** (§5, §7)
   - Evet ise ihlal.
3. **Genome içinde strateji / buy / sell / risk rule var mı?** (§4, §9)
   - Evet ise ihlal.
4. **M2 bootstrap kaydı dünya bilgisi taşıyor mu?** (§20)
   - Evet ise ihlal.
5. **Plasticity mutlak zaman / yaşla mı çalışıyor?** (§16)
   - Evet ise ihlal.
6. **Primer payload ekliyor mu (doğuştan)?** (§10)
   - Evet ise anayasal revizyon gerekir.
7. **Deontic gate kurallarını burada sayısallaştırıyor mu?** (§9)
   - Evet ise yanlış belge; `DEONTIC_GATE.md`'ye gider.
8. **Ingress mapping tam sayısal implementation spec'e dönüşmüş mü?** (§19)
   - Evet ise yanlış belge; `INGRESS_COMPILER_SPEC.md`'ye gider.
9. **Refleks "davranış" olarak isimlendiriliyor mu (eylem)?** (§8.1)
   - Evet ise ihlal. Refleks modülasyondur, davranış değildir.
10. **`SELF_GENESIS` çekirdeğe payload_seed olarak girip giriyor mu?** (§21)
    - Evet ise ihlal. Sadece M1 audit'tir.
11. **Çalışan Sentinel kendi genome'unu görebiliyor mu?** (§5)
    - Evet ise ihlal.
12. **Anayasa shift yapıldı ama M1'de event yazılmadı mı?** (§23)
    - Evet ise ihlal.
13. **`genesis_affecting` shift yaşayan Sentinel'e otomatik uygulandı mı?** (§23)
    - Evet ise ihlal.
14. **`stable_assembly_state` t=0'da boş değil mi?** (§20)
    - Boş değilse ihlal.

---

## 26. Open Questions

D çerçevesi kapanırken cevaplanmamış bırakılan ve sonraki belgelere devredilen sorular:

- **Kesin sayısal genome parametreleri:** Seed neuron sayısı, initial weight, homonymous bias, self-field weight, plasticity rate gibi kesin sayılar — implementation/numerics belgesi konusu (`BOOTSTRAP_GENOME_NUMERICS.md` veya signed genome artifact).
- **Deontic gate başlangıç kuralları:** Hangi kategorik kısıtlar doğuştan vardır? → `DEONTIC_GATE.md` konusu.
- **Ingress mapping katsayıları:** Sayısal mapping formülleri → `INGRESS_COMPILER_SPEC.md` konusu.
- **Replay rhythm tetikleme eşikleri:** `eligibility_pool_saturation`, `contradiction_load_threshold`, `fatigue_accumulation` hangi sayısal seviyelerde tetiklenir? → Implementation konusu.
- **Adapter manifest formatı:** Bootstrap M2'de `adapter_manifest_refs` neyi içerir? → `ADAPTER_MANIFEST_SPEC.md` konusu.
- **`proto_resonance_fields` detay:** Dokusal eğilim alanları nasıl matematiksel olarak tanımlanır? Implementation konusu, ama çok sıkı belirsiz bırakılırsa interpretation farkı yaratabilir.
- **`migration_birth` kontinüite sınırı:** `migration_birth` ile doğan Sentinel'in M0'ı tamamen sıfır mı, yoksa eski Sentinel'in M0'ından migration yapılabilir mi (kısıtlı/seçici)? Bu MEMORY_CONTRACT §14'teki "cross-restore identity" sorusuyla bağlantılı.

Bu sorular cevaplanmadan implementation aşamasına geçilmez.

---

## Çekirdek özet — 12 karar

1. Genome = öğrenebilirlik düzeni; genome ≠ bilgi.
2. Genome doğumdan önce donar; runtime'da değişmez.
3. Sentinel kendi genome'unu okuyamaz, değiştiremez; sadece sonucudur.
4. Initial state ve developmental rules ayrı katmandır.
5. Tüm Sentinel'ler aynı genome ile doğar (domain-agnostic).
6. Primer payload paleti v0.1 sabit (10 payload); yeni primer için anayasal revizyon gerekir.
7. M0 t=0: embriyo doku; stable assembly yok ama proto_resonance_fields var.
8. M1 t=0: `SELF_GENESIS` + bootstrap M2 injection event'leri.
9. M2 t=0: sadece `bootstrap_reference` kayıtları; dünya bilgisi yasak.
10. M3 t=0: boş.
11. Plasticity yaş-temelli değil, state/consolidation-temelli.
12. Constitutional shift policy: clarification / safety_tightening / genesis_affecting. Genesis-affecting yaşayan Sentinel'e uygulanmaz; `migration_birth` gerekir.

---

## Kilit cümleler

> **Sentinel sıfır doğmaz. Sentinel hazır zeki de doğmaz. Sentinel bilgiyle değil, bilgiye iz bırakabilecek doku ile doğar.**
>
> **Genome = öğrenebilirlik düzeni. Genome ≠ bilgi. Genome ≠ strateji. Genome ≠ domain ontology. Genome ≠ runtime config.**
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

---

## Versiyon

- **v0.1** — 18 Mayıs 2026 — Frozen Draft. Conceptual phase. No implementation authority.
- `CONSTITUTION.md` Madde 3'ün alt-spec'i.
- A, B, C belgelerinin açık sorularının birleşim noktası.
- Konuşma soyağacı: [`docs/conversations/0004-bootstrap-genome.md`](./docs/conversations/0004-bootstrap-genome.md)
