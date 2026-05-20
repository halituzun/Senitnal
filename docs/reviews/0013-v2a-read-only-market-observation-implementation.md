# 0013 — V2A Read-Only Market Observation Implementation

> Implements **V2A** of the V2 read-only market observation
> readiness plan (`docs/build/0002`). This is the first code-bearing
> phase since v0.1.0-mvb was sealed.
>
> Status: **GREEN.** No live exchange, no LLM, no execution path,
> no NeuralSeed emission, no ledger I/O. The phase added synthetic-
> only schema + pure conversion + pure audit payload builder, and
> 38 boundary tests. v0.1 invariants are unchanged.

---

## Status

```
Scope                                     V2A (planning -> code, schema + sanitizer only)
Files added (sentinel/)                   1  (sentinel/adapters/market_observation.py)
Files added (tests/)                      1  (tests/adapters/test_market_observation.py)
Files added (docs/)                       1  (this file)
Files modified (docs/)                    1  (docs/build/0002 §20 implementation-status appendix)
Source code changed                       YES (additive only, new module + tests)
CI workflow changed                       NO
Forbidden grep relaxed                    NO
Exchange SDK / LLM import added           NO  (forbidden-grep set re-verified clean)
Live execution path                       NONE
NeuralSeed emission                       NONE
Live API or network I/O                   NONE
Test count                                877 -> 915 (+38)
pyright                                   0 errors, 0 warnings, 0 informations
ruff check                                clean
ruff format --check                       126 files clean
dry sim                                   SystemOutput.WAIT (audit=4, permanent=2, ring=0)
hash chain                                re-verifies True
Phase decision                            V2A complete; V2B is the next planning gate
Final verdict                             GREEN
```

---

## 1. Scope of V2A

V2A is the **smallest safe code increment** that converts the V2
read-only market observation plan (`docs/build/0002`) from a
documentation contract into a callable, type-checked, tested
surface. It is **not** V2B (no synthetic fixture replay), **not**
the Gel.Al export contract integration (no IPC, no file watch,
no JSON envelope reader), and **not** any form of live or shadow
exchange access.

V2A is just three things:

```
1. MarketObservationEnvelope            observer-side schema
2. sanitize_market_observation_to_event pure mapping into v0.1
                                        ObservationEvent
3. build_market_observation_audit_payload
                                        pure dict builder for
                                        observer-side audit
                                        payload (no I/O)
```

Plus the boundary tests that prove the discipline.

V2A explicitly does NOT add:
  - an EchoAdapter-style class that emits events on a counter
  - a dry_sim extension (the /goal Golden Rule kept this off
    the table — see §6)
  - an observer audit helper that calls route_observer_event
    (per /goal Step 3, the conservative option was chosen)
  - any reservation of new ObserverEvent catalog rows
    (catalog change would touch tests/observer/
    test_catalog_consistency.py and is V2B territory)

---

## 2. Implementation boundary derived from source docs

Source docs consulted before any code was written:

```
docs/build/0002-read-only-market-observation-plan.md
docs/integrations/gel-al-borsa-readonly-bridge.md
docs/reviews/0011-post-v0.1-hardening-audit.md
docs/releases/v0.1.0-mvb.md
sentinel/types/events.py     (live ObservationEvent schema)
sentinel/types/observer.py   (ObserverEvent schema + payload rule)
sentinel/observer/router.py  (sanctioned routing path)
sentinel/adapters/echo.py    (existing observe-only adapter pattern)
```

The eight source docs the `/goal` Step 1 enumerated includes
some legacy design docs (`ADAPTER_MANIFEST_SPEC.md`,
`WORLD_INGRESS.md`, `INGRESS_COMPILER_SPEC.md`,
`OBSERVER_LEDGER_SCHEMA.md`, `ADAPTER_TRUST_NUMERICS.md`,
`CONSTITUTION.md`) that were part of the pre-build design phase
and are not present in the current MVB repo root. The relevant
content from those design docs is already encoded into:

```
sentinel/types/events.py     (4 closed ingress event types,
                              IngressEventBase with extra=forbid/
                              frozen=True/strict=True, "Domain
                              labels rejected at type boundary")
sentinel/types/observer.py   ("Core-facing ingress envelopes
                              REJECT domain labels.
                              ObserverEvent.payload INTENTIONALLY
                              allows them — audit ledger must
                              record what really happened")
sentinel/observer/router.py  ("Single source of truth: every
                              observer event flowing through the
                              system passes through
                              route_observer_event. No bypass
                              paths")
sentinel/adapters/echo.py    (observe-only manifest,
                              constitutional red line on
                              direct NeuralSeed emission)
```

No contradictions were found. V2A's design follows the live
schemas exactly.

### Boundary derived

```
B-1 Core-facing ObservationEvent schema is FIXED (v0.1).
    V2A produces standard ObservationEvent instances; it does
    NOT add fields.
B-2 ObservationEvent extra='forbid' is already in force. The
    sanitizer cannot produce a leaky event even if a future
    edit forgot to drop a field — Pydantic would reject it.
B-3 Domain labels (symbol, venue, source_system, raw prices,
    depth) belong on the observer side. ObserverEvent.payload
    is a dict[str, Any] and INTENTIONALLY accepts them.
    build_market_observation_audit_payload produces such a
    dict. The decision to actually persist it via route_
    observer_event is the caller's; V2A does not perform
    the routing.
B-4 No new ObserverEvent catalog row is reserved by V2A.
    Catalog changes touch test_catalog_consistency.py and
    are intentionally a V2B planning concern.
B-5 No adapter manifest is registered by V2A.
    AdapterManifest registration is also V2B / V2C territory;
    V2A is "the data path only".
B-6 No network library imported under sentinel/ (requests,
    httpx, aiohttp, urllib3, socket, asyncio.subprocess).
    V2A test_25 asserts this on the module source.
B-7 No exchange or LLM SDK imported under sentinel/.
    V2A test_26 asserts this on the module source.
B-8 No execution-output literal in module source.
    V2A test_27 asserts this on the module source.
```

---

## 3. Files changed

```
sentinel/adapters/market_observation.py            new   +213
tests/adapters/test_market_observation.py          new   +355
docs/reviews/0013-v2a-read-only-market-observation-implementation.md
                                                   new   (this file)
docs/build/0002-read-only-market-observation-plan.md
                                                   modified (small
                                                   §20 implementation-
                                                   status appendix)
```

No other file is modified. `.github/workflows/ci.yml`, the
deontic gate, the memory write gate, the recall protocol, the
observer router, the catalog, the dry sim runtime, and the
public API surface are all **unchanged**.

---

## 4. Test coverage

38 tests added across 4 classes:

```
TestMarketObservationEnvelopeSchema   12 tests   1-12
TestSanitization                       7 tests  13-19
TestAuditPayload                       4 tests  20-23
TestModuleSourceBoundary               4 tests  24-27
```

Total suite: **877 -> 915 passing.**

The /goal listed tests 28-30 (route integration tests) as
contingent on V2A optionally wiring an observer audit helper.
Per `/goal` Step 3 ("If this becomes too much scope: Do not
write helper") the conservative path was chosen; tests 28-30
are deferred to V2B with the routing helper itself.

### Static boundary tests (24-27) — the constitutional spine

```
test_24_no_neural_seed_emission
    asserts "NeuralSeed" string absent from module source —
    the constitutional red line ADAPTER_NEURAL_SEED_EMISSION_
    DETECTED cannot fire if NeuralSeed cannot be named.

test_25_no_network_imports
    regex on module source matching
        ^\s*(import|from)\s+(requests|httpx|aiohttp|urllib3|
                              socket|asyncio\.subprocess)\b
    Empty match list required.

test_26_no_exchange_or_llm_imports
    regex on module source matching
        ^\s*(import|from)\s+(ccxt|web3|binance|btcturk|pybit|
                              okx|gate_api|kucoin|huobi|
                              bitfinex|kraken|openai|anthropic|
                              langchain)\b
    Empty match list required.

test_27_no_forbidden_output_literals
    "BUY"/"SELL"/"EXECUTE_REAL"/"ORDER_SUBMIT" (both quote
    styles) absent from module source.
```

These four tests are the in-process echo of the CI grep on
`sentinel/`. They live next to the module so a future refactor
breaking the boundary fails the *unit* suite before it fails CI.

---

## 5. Safety invariants verified

```
SAF-01  No exchange SDK imports                          PASS
SAF-02  No LLM SDK imports                               PASS
SAF-03  No network library imports                       PASS
SAF-04  No execution-output literals in sentinel/        PASS
SAF-05  No NeuralSeed emission from V2A module           PASS (test 24)
SAF-06  No live execution path introduced                PASS (no module touches
                                                              exchange or
                                                              network surface)
SAF-07  Domain label (symbol/venue/source_system/raw
        price/depth) leakage into Core ObservationEvent  PASS (test 14)
SAF-08  Observer-side provenance preservation            PASS (tests 20-23)
SAF-09  Cross-field validation enforces internal
        consistency of envelope                          PASS (tests 2-4)
SAF-10  extra='forbid' on the envelope                   PASS (tests 9-11)
SAF-11  Envelope is frozen                               PASS (test 12)
SAF-12  Sanitization is deterministic                    PASS (test 19)
SAF-13  Dry sim canonical output unchanged               PASS (output=WAIT,
                                                              audit=4, perm=2,
                                                              ring=0,
                                                              ledger=/tmp/
                                                              sentinel-v2a-
                                                              smoke.jsonl)
SAF-14  Hash chain re-verifies                           PASS
SAF-15  v0.1 877 tests still passing                     PASS (no regression;
                                                              total 915)
SAF-16  Public API drift guard                           PASS (V2A is internal;
                                                              not re-exported
                                                              from sentinel.__all__)
SAF-17  Deontic gate default-deny preserved              PASS (untouched)
SAF-18  Memory Write Gate silent + candidate-only        PASS (untouched)
SAF-19  Recall top-1 + CORE-only                         PASS (untouched)
SAF-20  route_observer_event remains sanctioned          PASS (V2A does not
                                                              bypass; V2A does
                                                              not call ledger
                                                              at all)
SAF-21  OBSERVATION_INGESTED / WORKSPACE_PULSE remain
        ring_buffer_only per catalog                     PASS (catalog
                                                              untouched)
```

21/21 GREEN.

---

## 6. Why dry_sim was NOT extended

The `/goal` Step 5 marked the dry_sim extension as **optional**
and explicitly stated:

> "Golden rule: Existing v0.1 dry_sim tests must continue
> passing unchanged unless update is explicitly justified and
> still safe."

V2A's value is the schema + sanitizer + audit payload trio. Wiring
the synthetic envelope into `run_dry_simulation` would require:

```
- a new function parameter
  (market_observation: MarketObservationEnvelope | None = None)
- an opt-in code path that calls sanitize_market_observation_to_event
- a routing decision (which OBSERVATION_INGESTED / WORKSPACE_PULSE
  ring write would carry the synthetic envelope's downstream
  effects)
- a new integration test asserting the optional path's output is
  still in {WAIT, MONITOR}
```

None of those changes are unsafe in principle. But two of them
(the parameter and the routing decision) touch `run_dry_simulation`
itself, and any touch of the canonical run is a v0.1 regression
risk: the release note pins `output=WAIT audit_events=4 permanent=2
ring=0` and review 0010 §9 records that exact tuple.

V2A chose the conservative path: do not touch dry_sim. The
synthetic envelope + sanitizer is fully usable from a follow-up
integration test in V2B without any change to the runtime
module. Future V2B planning will explicitly justify or reject
the dry_sim extension.

This is the v0.1 discipline ("kusursuzluk öncelik bitirmek
değildir"), applied to V2A.

---

## 7. Why no live exchange adapter was added

A live adapter would need at least one of:

```
- import ccxt           — FORBIDDEN (constitutional C-02)
- import web3           — FORBIDDEN (constitutional C-02)
- import binance        — FORBIDDEN (constitutional C-02)
- import requests/httpx — FORBIDDEN (V2A pre-flight set adds
                          these to the network-library grep)
- API key field         — FORBIDDEN (no balance/credential
                          surface in V2A schema)
- order side / qty      — FORBIDDEN (rejected by extra='forbid')
- live IPC to a bridge
  process                — out of scope for V2A; would be a
                          V2B feature once the bridge contract
                          is documented and the catalog gains
                          a MARKET_OBSERVATION_ENVELOPE_RECEIVED
                          row.
```

Per `docs/build/0002` §9 the only acceptable real-data path
is Option B (Gel.Al exports JSON files Sentinel reads) or
Option C (external bridge process feeds sanitized envelopes
into Sentinel via IPC). Both of those land in **V2B**, not
**V2A**, by design.

Per `docs/integrations/gel-al-borsa-readonly-bridge.md`:

> "the brain in this mode is **read-only toward the execution
> surface**"
> "Sends to Gel.Al: NOTHING"
> "(reverse channel does NOT exist — not 'is unused')"

V2A does not introduce any channel toward execution. It does
not even introduce a channel toward Gel.Al. It introduces only
a sanitization function that some V2B caller will use.

---

## 8. Why no exchange SDK import was added

Same reason as §7, restated explicitly because the `/goal`
asked for the explicit statement: **the v0.1 constitutional
red line C-02 forbids any live exchange SDK import inside
`sentinel/`.** V2A does not relax this. The pre-flight forbidden
grep was tightened to include `requests`, `httpx`, and
`aiohttp` per the `/goal` Step 0, and the final-sweep forbidden
grep was re-verified clean against the same widened set.

```
$ grep -REn "^\s*(import|from)\s+(ccxt|web3|binance|btcturk|
                                    pybit|okx|gate_api|kucoin|
                                    huobi|bitfinex|kraken|
                                    openai|anthropic|langchain|
                                    requests|httpx|aiohttp)" \
       sentinel/ tests/
EXIT=1  (no match)
```

The CI workflow's permanent forbidden grep was NOT widened in
this commit. Widening CI is a separate change that touches
`.github/workflows/ci.yml` and would be subject to its own
review. V2A respects the rule "tightening CI is welcome,
relaxing CI is forbidden" but defers the actual tightening to
keep this PR's diff strictly additive.

A follow-up micro-commit can promote the `requests|httpx|aiohttp`
addition to the CI workflow once Halit reviews V2A; that
tightening is consistent with the v0.1 constitutional posture.

---

## 9. Implementation-status appendix added to docs/build/0002

A short §20 ("V2A implementation status") was appended to
`docs/build/0002-read-only-market-observation-plan.md` to mark
the plan's V2A portion as implemented. The plan itself is
unchanged in §§1-19; the appendix only records that schema +
sanitizer + audit builder + 38 tests have shipped.

---

## 10. Commits

```
3182603  feat(adapters): add read-only market observation schema (V2A)
0836e33  test(adapters): cover market observation boundary invariants (V2A)
<this>   docs(review): close V2A read-only market observation phase
```

Branch: `claude/add-conversation-main-FvHvl` (PR #1, broadened
from docs-only to docs-only + V2A code).

---

## 11. Final report (per /goal Step 9)

```
V2A Read-Only Market Observation Phase

Status:
- GREEN

Commits:
- 3182603 feat(adapters): add read-only market observation schema (V2A)
- 0836e33 test(adapters): cover market observation boundary invariants (V2A)
- <this>  docs(review): close V2A read-only market observation phase

Files changed:
- sentinel/adapters/market_observation.py             (new)
- tests/adapters/test_market_observation.py           (new)
- docs/reviews/0013-v2a-read-only-market-observation-implementation.md
                                                       (new, this file)
- docs/build/0002-read-only-market-observation-plan.md
                                                       (modified — §20
                                                       implementation-
                                                       status appendix)

Tests:
- total test count       : 915 (was 877; +38)
- new tests count        : 38
- pyright status         : 0 errors / 0 warnings / 0 informations
- ruff status            : clean (126 files formatted)
- forbidden imports      : none (incl. requests/httpx/aiohttp)
- forbidden outputs      : none

Safety:
- exchange imports                          : none
- LLM imports                               : none
- network I/O                               : none
- live execution path                       : none
- ObservationEvent symbol/venue leakage     : none (test 14)
- observer-side provenance preserved        : yes (tests 20-23)
- dry_sim output                            : SystemOutput.WAIT
                                              (audit=4, permanent=2, ring=0)
- hash chain                                : verifies True
- 21/21 SAF invariants                      : GREEN

Decision:
- V2A complete. Next recommended phase: V2B synthetic market
  fixture replay, OR Gel.Al one-way export contract (no live
  data still). V3 / V2 live integration / replay engine / real
  adapter / verified memory production / LLM remain explicitly
  OUT of scope.
```

---

## 12. Constraints honored

```
[+] No new feature beyond the schema + sanitizer + audit
    payload trio
[+] No V2B work
[+] No V3 / V4 work
[+] No real adapter
[+] No live exchange code
[+] No exchange SDK import
[+] No LLM SDK import
[+] No network library import (requests/httpx/aiohttp/urllib3/
    socket/asyncio.subprocess all absent under sentinel/)
[+] No execution verbs in source
[+] No forbidden grep relaxation
[+] No CI workflow change
[+] No deontic gate weakening
[+] No memory write gate weakening
[+] No recall protocol weakening
[+] No bypass of route_observer_event (V2A does not call it
    at all)
[+] No promotion of ring_buffer_only events to JSONL permanent
[+] No new ObserverEvent catalog row added (deferred to V2B)
[+] No public API drift (V2A is internal; not re-exported)
[+] No tag rewrite / release overwrite
[+] No failure hidden in documentation
```
