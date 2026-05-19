# 0003 — Phase 1 Contracts as Code Review

> Phase 1 (Contracts as Code) kod faz kapanış denetimi.
> Bu dosya yeni tasarım üretmez; yalnızca Phase 1 çıktısını kayda alır
> ve Phase 2 — Observer Ledger için başlama hattını çizer.

---

## Status

**GREEN.**

Phase 1 hedefi karşılandı: tüm core schema sözleşmeleri Pydantic v2
modeli olarak, constitutional invariant katalogu ise immutable
dataclass olarak kodda. Tip katmanı 22 frozen draft v0.1 belgesinin
ilgili kısımlarını mekanik şekilde reddediyor; legacy / pre-patch
vocabulary type boundary'de düşüyor.

---

## 1. Completed modules

### Schema layer (`sentinel/types/`)

```
payload.py       PrimerPayload (10) + PayloadSeed
neural_seed.py   NeuralSeed + computed total_intensity + 6 profiles
events.py        ObservationEvent / HumanIntentEvent /
                 InternalShockEvent / RecallEvent (Literal discriminator)
observer.py      ObserverEvent + 8 EventFamily
memory.py        MemoryRecord + 16 SubjectClass
numerics.py      Enums (6) + AllowedRange (3 variant union) +
                 NumericDependency + NumericEntry +
                 CompatibilityClass + NumericsArtifact
adapters.py      5 enums + CapabilityBinding + AdapterManifest
workspace.py     WorkspacePulseEvent (single event type)
```

### Constitution layer (`sentinel/constitution/`)

```
violations.py    ViolationContext (frozen + MappingProxy evidence) +
                 ConstitutionalViolation base + 6 specialized subclasses
invariants.py    InvariantSeverity (3) + InvariantCategory (8) +
                 InvariantDefinition + MVP_REQUIRED_INVARIANTS (24) +
                 list_invariants / get_invariant / assert_invariant
```

---

## 2. Test status

```
417 tests passing
pyright strict: 0 errors
ruff: clean
forbidden imports grep: clean
forbidden output literal grep: clean
```

CI guard'ları (`ccxt`, `openai`, `anthropic`, `langchain`, `web3`,
`binance`, `btcturk` ve `"BUY"` / `"SELL"` / `"EXECUTE_REAL"` /
`"ORDER_SUBMIT"` literal'leri) yeşil.

---

## 3. Constitutional invariants now code-pinned

Phase 1 sonunda schema seviyesinde otomatik reddedilen kurallar:

```
Core payload:
  - Primer palette closed (10 values)
  - PayloadSeed rejects task verbs and domain tickers
  - NeuralSeed payload uniqueness
  - NeuralSeed.total_intensity computed, not input

Ingress:
  - Each envelope has Literal event_type
  - No domain raw fields (symbol/market/venue/price)
  - HumanIntent normalized (no raw natural-language)
  - RecallEvent.subject_class bound to canonical taxonomy

Memory:
  - 16-value SubjectClass closed
  - foreign_instance_origin NOT a SubjectClass
  - MemoryRecord.status closed

Numerics:
  - No-default rule (12 required fields)
  - Immutable invariant: AllowedRangeSingle <=> both FORBIDDEN
  - Artifact entry keys unique + spec_family consistency
  - dev_only <=> fixture_purpose two-way

Adapters:
  - Channel-binding matrix per capability
  - Incompatible capability pairs rejected
  - execute requires observe
  - NeuralSeed not a legal adapter output

Workspace:
  - Single WORKSPACE_PULSE event type
  - No pulse_type / pulse_category / focus_type / semantic_label /
    domain_label (signature lives in dominant_payload_mix)
```

24 invariant katalog satırı `MVP_REQUIRED_INVARIANTS` içinde; her
satır code + source_ref + statement taşıyor.

---

## 4. Commit ledger (Phase 1)

```
Commit 1   project skeleton
Commit 2   payload schema
Commit 3   neural seed schema
Commit 4   ingress event envelopes
Commit 4p  literal discriminator patch
Commit 5   observer event envelope
Commit 6   memory record schema
Commit 6a  recall event subject_class refactor
Commit 7a  numerics governance enums
Commit 7b  numerics ranges + dependencies
Commit 7c  numerics entry
Commit 7d  numerics artifact
Commit 8   adapter manifest
Commit 9   workspace pulse event
Commit 10  constitution violations
Commit 11  constitution invariants catalog
```

Her commit küçük, tek konu odaklı, "Yaz" hükmü ile gated.

---

## 5. Deferred to later phases

Phase 1 deliberately excluded:

```
Observer ledger:
  - canonical event catalog validation
  - permanence policy table
  - hash chain
  - JSONL append-only writer
  - audit reader

Numerics governance runtime:
  - artifact loader / signature verification
  - dependency cycle detection
  - cross-key dependency resolution
  - safety_weakening human-approval workflow

Adapter trust:
  - AdapterTrustRecord + scoring
  - SourceTrust bridge
  - manifest lifecycle state machine

Memory write gate:
  - candidate -> committed transitions
  - canonicalization
  - retention / forgetting policy

Replay protocol:
  - replay-time memory updates
  - habituation math

Compiler:
  - event -> NeuralSeed mapping
  - profile cap enforcement at the boundary

M0 tissue runtime:
  - JSONL pulse loop
  - {WAIT, BLOCK, MONITOR, NEED_RECALL, NO_ACTION} output emission
```

---

## 6. Phase 2 — Observer Ledger entry point

Önerilen commit sırası:

```
Commit 12  this review (docs only)
Commit 13  observer/catalog.py
           canonical event family/type registry +
           permanence policy table
Commit 14  observer/hash_chain.py
           append-only hash chain primitives
Commit 15  observer/ledger.py
           JSONL writer (append-only)
Commit 16  observer/permanence.py
           permanence policy enforcement
Commit 17  observer/audit_reader.py
           replay-only reader
Commit 18  phase 2 integration test
```

Her commit küçük kalacak. Phase 1 ile aynı discipline.

---

## 7. Final hüküm

```
Phase 1 (Contracts as Code) GREEN.
Phase 2 (Observer Ledger) — Commit 13 hattında başlayabilir.
```
