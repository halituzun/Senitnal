# 0014 — V2 Read-Only Market Adapters Review

> Closes V2 — Read-Only Market Adapters. Companion to
> `docs/build/0003-v2-read-only-market-adapters-build-plan.md`.
>
> Builds directly on V2A (review 0013), promoting the
> schema-and-sanitizer trio into a full adapter family with
> manifests, two read-only adapter classes, a routing helper, a
> replay harness, a CLI, fixtures, and public API additions —
> all preserving every v0.1 constitutional red line.

---

## 1. Status

```
Version                                  V2 — Read-Only Market Adapters
Phase                                    end-to-end CLOSURE
Source code added                        YES (additive only)
CI workflow changed                      NO
Forbidden grep relaxed                   NO  (CI grep unchanged;
                                              V2 module-source tests
                                              additionally assert
                                              requests/httpx/aiohttp)
Exchange SDK / LLM import added          NO
Network library import added             NO
Live execution path                      NONE
NeuralSeed emission from V2 module       NONE
Live API or network I/O                  NONE
Symbol/venue leakage into core-facing
    ObservationEvent                      NONE
Test count                               877 (v0.1) -> 964 (V2)
                                          +86 net (note: 38 V2A
                                          tests already in baseline)
pyright                                  0 errors / 0 warnings /
                                          0 informations
ruff check                               clean
ruff format --check                      clean (136 files)
dry sim                                  SystemOutput.WAIT
                                          (audit=4, permanent=2, ring=0)
market replay CLI smoke                  exit 0, hash_chain_valid=True
hash chain                               re-verifies True
Final verdict                            **GREEN**
```

---

## 2. Scope completed

```
[1]  MarketObservationEnvelope schema           done
[2]  SanitizedMarketProvenance schema           done
[3]  sanitize_market_observation_to_event       done
[4]  build_market_observation_audit_payload     done
[5]  build_synthetic_market_manifest            done
[6]  build_local_jsonl_market_manifest          done
[7]  SyntheticMarketAdapter                     done
[8]  LocalJsonlMarketAdapter                    done
[9]  emit_market_observation_ingested helper    done
[10] MarketReplayResult dataclass               done
[11] run_market_observations                    done
[12] run_market_jsonl_file                      done
[13] market_replay CLI                          done
[14] tests/fixtures/market/ (5 valid + 3 invalid) done
[15] Public API additions                       done
[16] V2 build plan (docs/build/0003)            done
[17] V2 review (this file)                      done
```

22/22 done-definition items in `docs/build/0003` §20 are GREEN.

---

## 3. Files added

```
sentinel/adapters/market_observation.py        (V2A — schema + sanitizer;
                                                 V2 adds SanitizedMarketProvenance +
                                                 source_reliability_band param)
sentinel/adapters/market_manifest.py           (V2)
sentinel/adapters/synthetic_market.py          (V2)
sentinel/adapters/local_jsonl_market.py        (V2)
sentinel/adapters/market_audit.py              (V2)
sentinel/runtime/market_replay.py              (V2; includes __main__ CLI)

tests/adapters/test_market_observation.py      (V2A — 38 tests, unchanged)
tests/adapters/test_market_manifest.py         (V2 — 9 tests)
tests/adapters/test_synthetic_market.py        (V2 — 8 tests)
tests/adapters/test_local_jsonl_market.py      (V2 — 9 tests)
tests/adapters/test_market_audit.py            (V2 — 4 tests)
tests/runtime/test_market_replay.py            (V2 — 14 tests + CLI smoke)
tests/test_public_api.py                       (modified — V2_PUBLIC_API_ADDITIONS
                                                 frozenset + drift test)

tests/fixtures/market/calm_tight_spread.jsonl              (valid)
tests/fixtures/market/wide_spread_valid.jsonl              (valid)
tests/fixtures/market/stale_orderbook.jsonl                (valid)
tests/fixtures/market/high_volatility_imbalance.jsonl      (valid)
tests/fixtures/market/low_confidence_market.jsonl          (valid)
tests/fixtures/market/inconsistent_mid_price_invalid.jsonl (invalid)
tests/fixtures/market/inconsistent_spread_invalid.jsonl    (invalid)
tests/fixtures/market/forbidden_order_fields_invalid.jsonl (invalid)

sentinel/__init__.py                           (modified — V2 exports added
                                                 to imports + __all__)

docs/build/0003-v2-read-only-market-adapters-build-plan.md (V2 — new)
docs/reviews/0014-v2-read-only-market-adapters-review.md   (V2 — this file)
```

---

## 4. Adapter surfaces

### SyntheticMarketAdapter

```python
from sentinel import SyntheticMarketAdapter
adapter = SyntheticMarketAdapter.default()
envelope = adapter.emit_market_observation(
    symbol="SYNTH/TRY",
    venue="synthetic",
    best_bid=99.5,
    best_ask=100.5,
    volatility_score=0.9,
    imbalance_score=0.9,
    confidence=0.8,
)
# -> MarketObservationEnvelope, frozen, extra='forbid'
```

mid_price and spread_pct are computed from (best_bid, best_ask)
so the cross-field validator passes by construction. The class
has NO `emit_neural_seed_directly` method — the constitutional
red line ADAPTER_NEURAL_SEED_EMISSION_DETECTED is unreachable.

### LocalJsonlMarketAdapter

```python
from pathlib import Path
from sentinel import LocalJsonlMarketAdapter
adapter = LocalJsonlMarketAdapter(path=Path("tests/fixtures/market/calm_tight_spread.jsonl"))
for envelope in adapter.iter_observations():
    ...
```

Read-only file consumer. No network. No tail-follow. No async
daemon. Missing file → FileNotFoundError; malformed JSON →
ValueError (with line number); schema violation → ValidationError.

---

## 5. Pipeline

```
MarketObservationEnvelope
    -> emit_market_observation_ingested (router, ring_buffer_only)
        OBSERVATION_INGESTED stored in ring buffer (or dropped
        if no ring buffer supplied); never promoted to JSONL.
    -> sanitize_market_observation_to_event (pure)
        Core-facing ObservationEvent with only:
            event_id, event_type=OBSERVATION,
            occurred_at_ms, ttl_ms,
            confidence, source_adapter_id,
            source_reliability_band, magnitude_normalized,
            novelty_indicator, staleness_ms
    -> compile_neural_seed (v0.1 ingress compiler, unchanged)
        empty payload_seed -> ValidationError -> rejected;
                              outputs.append(SystemOutput.NO_ACTION)
        non-empty -> seed
    -> _make_pulse_for_seed (deterministic; mass=min(total,1),
                              persistence=allocation=mass/2)
    -> WORKSPACE_PULSE (router, ring_buffer_only)
        ring buffer push only; never promoted to JSONL.
    -> outputs.append(SystemOutput.MONITOR)
```

If `observations_seen == 0`, outputs defaults to `(WAIT,)`.

Outputs are **strictly** in `{WAIT, MONITOR, NO_ACTION}`. There
is no path from market data alone to BLOCK, NEED_RECALL, or
anything outside the v0.1 SystemOutput set.

---

## 6. Replay verification (per fixture)

Smoke-run from a fresh ledger per fixture:

```
calm_tight_spread          seen=1 acc=0 rej=1 pulses=0
                            outputs=(NO_ACTION,) ring=1 perm=0
                            hash_chain_valid=True
wide_spread_valid          seen=2 acc=0 rej=2 pulses=0
                            outputs=(NO_ACTION, NO_ACTION)
                            ring=2 perm=0 hash_chain_valid=True
stale_orderbook            seen=1 acc=0 rej=1 pulses=0
                            outputs=(NO_ACTION,) ring=1 perm=0
                            hash_chain_valid=True
high_volatility_imbalance  seen=2 acc=2 rej=0 pulses=2
                            outputs=(MONITOR, MONITOR)
                            ring=4 perm=0 hash_chain_valid=True
low_confidence_market      seen=1 acc=1 rej=0 pulses=1
                            outputs=(MONITOR,) ring=2 perm=0
                            hash_chain_valid=True
```

**perm=0 in every case.** OBSERVATION_INGESTED and WORKSPACE_PULSE
strictly stayed ring-only. Hash chain re-verifies on each run.

---

## 7. Safety invariants verified

```
SAF-01  No exchange SDK imports under sentinel/             PASS
SAF-02  No LLM SDK imports under sentinel/                  PASS
SAF-03  No network library imports under sentinel/          PASS
        (requests/httpx/aiohttp/urllib3/socket/asyncio.subprocess
         absent from each V2 module; asserted by per-module
         source tests)
SAF-04  No execution-output literals in sentinel/           PASS
SAF-05  No NeuralSeed emission from any V2 module           PASS
        (SyntheticMarketAdapter has no emit_neural_seed_
         directly method; LocalJsonlMarketAdapter is a
         file reader; market_replay never calls a neural-
         seed-emission path)
SAF-06  No live execution path                              PASS
SAF-07  ObservationEvent symbol/venue/source_system /
        raw-price / depth leakage                            PASS
        (v0.1 ObservationEvent extra='forbid' + V2A test_14)
SAF-08  Observer-side raw provenance preserved              PASS
        (build_market_observation_audit_payload includes
         symbol/venue/source_system/raw_bid/raw_ask/.../
         provenance_hash; market_audit attaches it via
         OBSERVATION_INGESTED payload)
SAF-09  OBSERVATION_INGESTED stays ring_buffer_only         PASS
        (replay permanent_event_ids == ()) per all fixtures
SAF-10  WORKSPACE_PULSE stays ring_buffer_only              PASS
        (same; replay permanent_event_ids == ())
SAF-11  No promotion of ring-only events to permanent       PASS
        (router enforces catalog policy; V2 does not
         bypass)
SAF-12  Adapter manifests observe-only                      PASS
        (capabilities == (OBSERVE,); no EXECUTE / INTENT_RELAY
         / MEMORY_WRITER / RECALL_PROVIDER)
SAF-13  SyntheticMarketAdapter cannot execute               PASS
        (no execute method; no AdapterCapability.EXECUTE in
         manifest)
SAF-14  LocalJsonlMarketAdapter cannot fetch network        PASS
        (module source contains zero network-library
         imports; asserted by test)
SAF-15  Market replay outputs in SystemOutput closed set    PASS
        (replay outputs are a tuple of SystemOutput members;
         tests assert subset of {WAIT, MONITOR, NO_ACTION})
SAF-16  Existing v0.1 dry_sim canonical run unchanged       PASS
        (output=WAIT audit_events=4 permanent=2 ring=0)
SAF-17  Full forbidden imports grep clean                   PASS
        (incl. requests/httpx/aiohttp; exit 1)
SAF-18  Full forbidden outputs grep clean                   PASS
SAF-19  Public API drift                                    PASS
        (v0.1 baseline intact; V2 additions exported)
SAF-20  Deontic gate default-deny preserved                 PASS (untouched)
SAF-21  Memory Write Gate silent + candidate-only           PASS (untouched)
SAF-22  Recall top-1 + CORE-only                            PASS (untouched)
SAF-23  route_observer_event sanctioned (no bypass)         PASS
        (every V2 routing call goes through it; market_audit
         does not call ledger.append directly)
SAF-24  No ApprovedActionIntent constructed in replay       PASS
        (asserted by source-grep test in
         test_market_replay.py)
SAF-25  No MemoryWriteGate call in replay                   PASS
        (asserted by source-grep test)
SAF-26  Catalog rows unchanged                              PASS
        (no new ObserverEvent row added in V2)
```

26/26 GREEN.

---

## 8. What is deliberately deferred

```
- Real exchange SDK import        FORBIDDEN — never;
                                    constitutional C-02
- Real network market feed        DEFERRED — V2 has only
                                    file/in-memory adapters
- Gel.Al live bridge              DEFERRED — V2.1 (export
                                    contract) or V5 (full
                                    live shadow integration)
- Account / API key handling      FORBIDDEN — never (C-02)
- V3 Financial M2 Memory          DEFERRED (next planning gate)
- V4 Replay/counterfactual        DEFERRED
- V5 Gel.Al shadow integration    DEFERRED
- Paper / canary / live           FORBIDDEN unless a
                                    constitutional amendment
                                    of C-02 is published and
                                    reviewed
- CI workflow grep tightening
  to include requests / httpx /
  aiohttp at workflow level       DEFERRED (V2.2 micro-PR;
                                    V2 asserts via per-
                                    module source tests
                                    locally)
- New ObserverEvent catalog row
  for MARKET_OBSERVATION_*        DEFERRED (V2 uses
                                    OBSERVATION_INGESTED which
                                    already exists)
```

---

## 9. Final report (per /goal Step 17)

```
V2 — Read-Only Market Adapters

Status:
- GREEN

Commits:
- (see git log on branch claude/add-conversation-main-FvHvl;
   8 commits across V2A + V2 closure)

Files changed:
- sentinel/adapters/market_observation.py        (V2 extends V2A)
- sentinel/adapters/market_manifest.py           (new)
- sentinel/adapters/synthetic_market.py          (new)
- sentinel/adapters/local_jsonl_market.py        (new)
- sentinel/adapters/market_audit.py              (new)
- sentinel/runtime/market_replay.py              (new — includes CLI)
- sentinel/__init__.py                           (modified — V2 exports)
- tests/adapters/test_market_observation.py     (V2A baseline)
- tests/adapters/test_market_manifest.py         (new)
- tests/adapters/test_synthetic_market.py        (new)
- tests/adapters/test_local_jsonl_market.py      (new)
- tests/adapters/test_market_audit.py            (new)
- tests/runtime/test_market_replay.py            (new)
- tests/test_public_api.py                       (modified — V2 baseline)
- tests/fixtures/market/*                        (8 new JSONL fixtures)
- docs/build/0003-v2-read-only-market-adapters-build-plan.md  (new)
- docs/reviews/0014-v2-read-only-market-adapters-review.md    (this file)

New modules:
- sentinel/adapters/market_manifest.py
- sentinel/adapters/synthetic_market.py
- sentinel/adapters/local_jsonl_market.py
- sentinel/adapters/market_audit.py
- sentinel/runtime/market_replay.py

Fixtures:
- 5 valid (calm_tight_spread, wide_spread_valid, stale_orderbook,
            high_volatility_imbalance, low_confidence_market)
- 3 invalid (inconsistent_mid_price_invalid,
              inconsistent_spread_invalid,
              forbidden_order_fields_invalid)

Tests:
- total test count       : 964 (was 877 at v0.1)
- new tests count        : 87 (38 V2A + 49 V2 + 1 V2-baseline
                                 additions assertion)
- pyright status         : 0 errors / 0 warnings / 0 informations
- ruff status            : clean (136 files formatted)
- forbidden imports      : clean (incl. requests/httpx/aiohttp
                                  via per-module assertions)
- forbidden outputs      : clean

Safety:
- exchange imports                          : none
- network I/O                               : none
- LLM imports                               : none
- live execution path                       : none
- ObservationEvent symbol/venue leakage     : none
- observer-side provenance preserved        : yes
- ring-only permanence                      : respected (perm=0
                                              on every market
                                              replay)
- dry_sim output                            : closed set
                                              (canonical WAIT)
- market replay output                      : closed set
                                              (subset of
                                              {WAIT, MONITOR,
                                              NO_ACTION})
- hash chain                                : verifies True

Version decision:
- V2 complete. Next version: V3 — Financial M2 Memory + Recall.
  Alternative if more read-only integration work is preferred:
  V2.1 — Gel.Al one-way local export contract.
```

---

## 10. Constraints honored

```
[+] No new feature beyond the V2 surface
[+] No V2.x / V3 / V4 / V5+ work
[+] No real adapter
[+] No live exchange code
[+] No exchange SDK import
[+] No LLM SDK import
[+] No network library import under sentinel/
[+] No execution verbs in source
[+] No forbidden grep relaxation
[+] No CI workflow change
[+] No deontic gate weakening
[+] No memory write gate weakening
[+] No recall protocol weakening
[+] No bypass of route_observer_event
[+] No promotion of ring_buffer_only events to JSONL permanent
[+] No new ObserverEvent catalog row
[+] No tag rewrite / release overwrite
[+] No failure hidden in documentation
[+] No claim that live market is connected
[+] No claim that Gel.Al integration exists beyond the
    documented local-file consumer
```

---

## 11. Final hüküm

```
V2 — Read-Only Market Adapters is complete.
Sentinel can safely observe synthetic and local market data
as normalized sensory input. Raw market facts stay observer-
side. Core-facing ObservationEvent receives only normalized
magnitudes. Sentinel remains non-executing. v0.1's
constitutional red lines are preserved unchanged.
```
