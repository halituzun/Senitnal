# 0003 — V2 Read-Only Market Adapters Build Plan

> Successor to `docs/build/0001-minimum-viable-brain-plan.md` (the
> v0.1 MVB plan) and `docs/build/0002-read-only-market-observation-plan.md`
> (the V2 readiness contract).
>
> This document defines V2 end-to-end. V2 adds a synthetic / local
> read-only market observation surface on top of v0.1, while
> preserving every v0.1 constitutional red line.

---

## 1. Purpose

Give Sentinel a safe way to receive market-shaped observations
from synthetic adapters or local JSONL fixtures, sanitize them
into v0.1 `ObservationEvent` objects, route them through the
sanctioned router, and drive the existing v0.1 pipeline
(ingress compiler → workspace pulse → outputs).

Output set remains the closed v0.1 set:
`{WAIT, BLOCK, MONITOR, NEED_RECALL, NO_ACTION}`. Market replay
runs produce only `{WAIT, MONITOR, NO_ACTION}` — there is no path
to `BLOCK` or `NEED_RECALL` from market data alone, and no path
to anything outside this five-member set.

---

## 2. Non-goals

```
- No live orders
- No account or balance mutation
- No exchange API keys
- No trading SDK imports (ccxt / binance / btcturk / pybit / okx /
  gate_api / kucoin / huobi / bitfinex / kraken / web3)
- No network library imports (requests / httpx / aiohttp /
  urllib3 / socket / asyncio.subprocess) under sentinel/
- No LLM SDK imports (openai / anthropic / langchain)
- No LLM interpretation of market state
- No direct memory verified-status write
- No production numerics matrix update
- No execution adapter
- No Sentinel -> Gel.Al channel (does not exist; not "unused")
- No real-time WebSocket subscription
- No async tail-follow daemon (V2)
```

---

## 3. Safety constraints

All v0.1 constitutional red lines remain in force unchanged. The
CI grep set is a strict superset of v0.1's — V2 never relaxes it.

```
C-01 SystemOutput membership closed
C-02 No live exchange / venue API integration
C-03 No LLM SDK integration
C-04 No execution-output literals
C-05 No M2 verified-status memory production
C-06 No numerics runtime mutation
C-07 No cross-instance / fork / migration paths
C-08 No replay-driven memory update
C-09 No M0 learning
C-10 No silent action
C-11 No adapter NeuralSeed emission
C-12 No operator override of the deontic gate
C-13 No human/LLM-direct recall push
```

---

## 4. Raw market data boundary

Raw market data — symbol, venue, source_system, best_bid, best_ask,
mid_price, spread_pct, depth, raw_ref, provenance_hash — lives
exclusively on the **observer side** of the V2 boundary. It is
recorded in observer-side audit payloads (which intentionally
accept domain labels per `sentinel/types/observer.py` docstring).
It NEVER enters a core-facing `ObservationEvent`.

The boundary is enforced by three mechanisms:

```
[1] v0.1 ObservationEvent schema (extra='forbid'). Even if the
    sanitizer regressed and tried to pass a symbol field through,
    Pydantic would reject the construction.
[2] V2 sanitize_market_observation_to_event source code: the
    function explicitly constructs an ObservationEvent with the
    closed v0.1 field set only.
[3] V2 tests: tests/adapters/test_market_observation.py::test_14
    asserts no observer-side label appears in the resulting
    ObservationEvent.model_dump().
```

---

## 5. Core-facing ObservationEvent boundary

`ObservationEvent` schema is **unchanged**. V2 produces standard
v0.1 ObservationEvent instances containing only:

```
event_id, event_type=OBSERVATION, occurred_at_ms, ttl_ms,
confidence, source_adapter_id, source_reliability_band (0..5),
magnitude_normalized (0..1), novelty_indicator (0..1),
staleness_ms (>= 0)
```

The sanitizer maps market envelope state into this shape per
the deterministic formula in `sanitize_market_observation_to_event`.

---

## 6. Adapter classes in V2

V2 introduces two observe-only adapter classes plus a routing
helper. No execution adapter is added.

```
SyntheticMarketAdapter     emits MarketObservationEnvelope on demand
                           (counter-based event_id; deterministic).
LocalJsonlMarketAdapter    reads MarketObservationEnvelope JSON lines
                           from a local file. No network. No tail-
                           follow. No async daemon.
```

Both wear AdapterManifest with `capabilities=(OBSERVE,)`. Neither
imports any banned SDK or network library.

---

## 7. SyntheticMarketAdapter

`sentinel/adapters/synthetic_market.py`. Methods:

```
SyntheticMarketAdapter.default() -> SyntheticMarketAdapter
SyntheticMarketAdapter.emit_market_observation(
    *, symbol="SYNTH/TRY", venue="synthetic", source_system="synthetic-fixture",
    best_bid=100.0, best_ask=100.5, volatility_score=0.3, imbalance_score=0.4,
    confidence=0.7, orderbook_age_ms=50, latency_ms=25,
    bid_depth_10=..., ask_depth_10=..., bid_value_10=..., ask_value_10=...,
) -> MarketObservationEnvelope
```

The adapter computes `mid_price` and `spread_pct` from `(best_bid,
best_ask)`, guaranteeing the envelope's cross-field consistency
validator passes by construction. There is NO
`emit_neural_seed_directly` method — the constitutional red line
ADAPTER_NEURAL_SEED_EMISSION_DETECTED is unreachable from this
class.

---

## 8. LocalJsonlMarketAdapter

`sentinel/adapters/local_jsonl_market.py`. Methods:

```
LocalJsonlMarketAdapter(path: Path, manifest: AdapterManifest | None = None)
LocalJsonlMarketAdapter.read_all() -> tuple[MarketObservationEnvelope, ...]
LocalJsonlMarketAdapter.iter_observations() -> Iterator[MarketObservationEnvelope]
```

Reads one JSON envelope per non-blank line. Surfaces are:

```
- missing file               -> FileNotFoundError
- malformed JSON line        -> ValueError (with 1-indexed line number)
- valid JSON / invalid schema -> ValidationError (Pydantic)
```

No network. No HTTP client. No async subprocess. No exchange SDK.
The file-watch / tail-follow / queue-consumer surface is
DEFERRED to V2.x — V2 itself only does one-shot reads.

---

## 9. Gel.Al one-way export placeholder

V2 ships the **adapter** (LocalJsonlMarketAdapter) that the
eventual Gel.Al → Sentinel one-way export contract will feed.
The export contract itself remains documentation-only in
`docs/integrations/gel-al-borsa-readonly-bridge.md`. The V2
build does NOT implement a Gel.Al-specific reader or any
agreed-upon export format; that lives in a follow-up phase
(V2.1 — Gel.Al one-way local export contract) gated on
explicit alignment with the Gel.Al side.

---

## 10. Adapter manifest and trust posture

`sentinel/adapters/market_manifest.py` exposes:

```
build_synthetic_market_manifest(...)     -> AdapterManifest
build_local_jsonl_market_manifest(...)   -> AdapterManifest
```

Both produce manifests with:

```
capabilities  = (OBSERVE,)        # no EXECUTE, no INTENT_RELAY,
                                   # no MEMORY_WRITER, no
                                   # RECALL_PROVIDER
bindings      = (one binding,)    # external_source -> ObservationEvent
                                   # via ingress_compiler
status        = ACTIVE            # (parameterizable; CANDIDATE allowed)
manifest_hash = "sha256:..."      # dev-signed mock
signature     = "sig-..."         # dev-signed mock
```

`NeuralSeed` is not a legal AdapterOutputChannel by v0.1 schema
(`sentinel/types/adapters.py` module docstring), so the manifest
cannot — even by accident — declare neural-seed output. The V2
manifest test `test_neural_seed_not_a_valid_output_channel` pins
this invariant.

Trust posture: V2 uses the existing v0.1 multiplicative-trust
machinery. New market adapters do NOT bypass `compute_trust`. No
new trust path is introduced.

---

## 11. Observer-side raw provenance

Two helpers in `sentinel/adapters/market_observation.py`:

```
SanitizedMarketProvenance        # typed wrapper for the observer-side
                                  # raw fields (frozen, extra='forbid')
build_market_observation_audit_payload(envelope) -> dict[str, Any]
                                  # constructs a plain dict suitable for
                                  # ObserverEvent.payload — preserves
                                  # symbol, venue, source_system, best_bid,
                                  # best_ask, mid_price, depth, raw_ref,
                                  # provenance_hash.
```

`ObserverEvent.payload` accepts domain labels by design (the
audit ledger must record what really happened). Core-facing
events do NOT.

---

## 12. Sanitization rules

`sanitize_market_observation_to_event(envelope, *, ttl_ms=1000,
source_reliability_band=3) -> ObservationEvent`.

Mapping (deterministic, pure):

```
magnitude_normalized = clamp(
    0.4 * min(spread_pct / 10.0, 1.0)
  + 0.4 * volatility_score
  + 0.2 * imbalance_score,
    0.0, 1.0)
novelty_indicator    = clamp(
    0.5 * volatility_score + 0.5 * imbalance_score, 0.0, 1.0)
staleness_ms         = orderbook_age_ms + latency_ms
confidence           = envelope.confidence  (pass-through)
source_adapter_id    = envelope.source_adapter_id
source_reliability_band = caller-supplied (default 3, must be in [0,5])
```

Domain fields (symbol, venue, source_system, raw prices, depth,
raw_ref, provenance_hash, volatility_score, imbalance_score)
are NOT present in the resulting ObservationEvent. v0.1
extra='forbid' makes them unreachable anyway.

---

## 13. Ingress compiler integration

V2 calls the existing v0.1 `compile_neural_seed` with
`event_attributes={"magnitude": ..., "confidence": ...}` — the
same shape `dry_sim` uses. No new rule, no new profile, no new
band. If a sanitized observation produces no signal under the
v0.1 rule set, `compile_neural_seed` raises `ValidationError`
(empty payload_seed), and the V2 replay treats it as a rejected
observation and emits `SystemOutput.NO_ACTION` for that envelope.

---

## 14. Workspace pulse integration

When a neural seed compiles, V2 builds a `WorkspacePulseEvent`
using the same deterministic mapping `dry_sim` uses
(`mass = min(seed.total_intensity, 1.0)`, `persistence =
allocation_share = mass / 2.0`, etc.), routes a WORKSPACE_PULSE
ObserverEvent through `route_observer_event`, and emits
`SystemOutput.MONITOR` for that observation.

WORKSPACE_PULSE permanence remains `ring_buffer_only` per
catalog. V2 does not change the catalog.

---

## 15. Observer router / permanence routing

All V2 observer-facing event writes flow through
`sentinel.observer.router.route_observer_event`. The catalog
rows touched by V2:

```
OBSERVATION_INGESTED     (ring_buffer_only, INGRESS family)
WORKSPACE_PULSE          (ring_buffer_only, ATTENTION family)
```

No new catalog row is added in V2. The constitutional rule
"OBSERVATION_INGESTED / WORKSPACE_PULSE remain ring_buffer_only"
holds; V2 cannot promote either to permanent JSONL by any path.

---

## 16. Fixture replay harness

`sentinel/runtime/market_replay.py`. Public surface:

```
MarketReplayResult                    frozen dataclass
run_market_observations(observations, *, ledger, ring_buffer,
                        provenance, coherence=0.4, ttl_ms=1000,
                        source_path=None) -> MarketReplayResult
run_market_jsonl_file(path, *, ledger, ring_buffer, provenance,
                      coherence=0.4, ttl_ms=1000) -> MarketReplayResult
```

The harness consumes either a hand-built iterable of envelopes
or a local JSONL fixture. Per-envelope pipeline:

```
emit_market_observation_ingested  (ring-only via router)
sanitize_market_observation_to_event
try compile_neural_seed:
    ValidationError -> rejected; SystemOutput.NO_ACTION
    ok              -> accepted; build pulse; route pulse;
                       SystemOutput.MONITOR
```

If no envelopes are presented, outputs default to `(WAIT,)`.

`MarketReplayResult` fields include `observations_seen`,
`observations_accepted`, `observations_rejected`,
`neural_seed_count`, `pulse_count`, `outputs`, `audit_event_ids`,
`permanent_event_ids`, `ring_buffer_event_ids`, `hash_chain_valid`,
`reason`. The reason string passes through
`assert_no_forbidden_literal`.

---

## 17. CLI

`python -m sentinel.runtime.market_replay --fixture FIXTURE
--ledger LEDGER [--coherence FLOAT] [--ttl-ms INT]
[--ring-capacity INT]`.

Behavior:
  - Reads JSONL fixture via LocalJsonlMarketAdapter
  - Runs the replay
  - Prints a single result-line with counts, outputs, ring/permanent
    sizes, and hash_chain_valid
  - Exit codes: 0 on success, 1 on fixture-load error
    (FileNotFoundError / ValueError / ValidationError), 2 if
    hash_chain_valid is False.

The existing v0.1 `python -m sentinel.runtime --ledger ...`
canonical run is UNTOUCHED. The market replay CLI is a separate
entry point.

---

## 18. Tests and invariants

Test classes added (all under `tests/`):

```
tests/adapters/test_market_manifest.py
    9 tests:
        observe-only capability (synthetic + local)
        binding matches external_source -> OBSERVATION_EVENT
        no EXECUTE / INTENT_RELAY / MEMORY_WRITER /
            RECALL_PROVIDER
        NeuralSeed not a legal AdapterOutputChannel
        EXECUTE+OBSERVE combo with mismatched bindings rejected
        adapter_id / manifest_id / manifest_hash distinct
        across the two manifests

tests/adapters/test_synthetic_market.py
    8 tests:
        default manifest observe-only
        emit returns MarketObservationEnvelope
        counter advances
        invalid bid/ask rejected
        sanitized ObservationEvent valid
        no emit_neural_seed_directly method
        no network imports / no exchange or LLM imports /
            no forbidden output literals in module source

tests/adapters/test_local_jsonl_market.py
    9 tests:
        reads valid fixture
        preserves order
        missing file raises FileNotFoundError
        malformed JSON raises ValueError with line number
        invalid envelope raises ValidationError
        forbidden-field envelope raises ValidationError
        iter_observations is single-pass
        no network imports / no exchange or LLM imports

tests/adapters/test_market_audit.py
    4 tests:
        OBSERVATION_INGESTED routes to ring buffer (not ledger)
        no JSONL promotion when ring_buffer is None
        payload preserves symbol/venue + source_event_id link
        event_type == "OBSERVATION_INGESTED", family == ingress

tests/runtime/test_market_replay.py
    14 tests:
        each fixture in {calm, wide, stale, hvi, lowc} replay
        OBSERVATION_INGESTED stays ring-only
        WORKSPACE_PULSE stays ring-only
        determinism for same fixture
        no ApprovedActionIntent constructed in replay
        invalid fixture raises ValidationError
        module has no network / exchange / LLM imports
        module has no forbidden output literals
        module does not invoke MemoryWriteGate
        synthetic adapter -> replay produces 3 MONITOR outputs
        CLI runs calm fixture and exits 0
        CLI on missing fixture exits 1
```

Plus the existing V2A 38 tests in `tests/adapters/test_market_observation.py`.

Total V2 net tests added: **86** (was 877 at v0.1 release, now
963 → 964 after the V2 public-API additive test).

---

## 19. Forbidden surfaces (V2 line-item)

```
- No `import ccxt`, `web3`, `binance`, `btcturk`, `pybit`, `okx`,
  `gate_api`, `kucoin`, `huobi`, `bitfinex`, `kraken` under
  `sentinel/`. Asserted by per-module source tests + repo-level
  CI grep.
- No `import openai`, `anthropic`, `langchain` under `sentinel/`.
- No `import requests`, `httpx`, `aiohttp`, `urllib3`, `socket`,
  `asyncio.subprocess` in V2 source modules. Asserted by per-
  module source tests (CI workflow grep is a separate scope —
  see §17 of `docs/reviews/0013` for the optional CI tightening
  follow-up).
- No `"BUY"`, `"SELL"`, `"EXECUTE_REAL"`, `"ORDER_SUBMIT"`
  (or single-quoted variants) in any V2 source module.
- No order side, side, qty, amount, quantity, api_key, api_secret,
  secret, execution_hint, account_id, wallet, withdrawal_address,
  balance, position, leverage, take_profit, stop_loss,
  trade_intent, strategy_action, order_type field on
  MarketObservationEnvelope. extra='forbid' rejects them.
- No live HTTP / WebSocket / IPC connection initiated from
  sentinel/.
- No memory verified-status write from market data.
- No production numerics matrix update from market data.
- No deontic gate bypass from market data.
- No new ObserverEvent catalog row (catalog unchanged in V2).
```

---

## 20. Done definition

V2 is complete iff ALL of the following are true:

```
[1]  MarketObservationEnvelope schema implemented
[2]  SanitizedMarketProvenance schema implemented
[3]  sanitize_market_observation_to_event implemented
[4]  build_market_observation_audit_payload implemented
[5]  build_synthetic_market_manifest + build_local_jsonl_market_manifest
     implemented; manifests observe-only
[6]  SyntheticMarketAdapter implemented
[7]  LocalJsonlMarketAdapter implemented; no network
[8]  emit_market_observation_ingested (audit helper) routes via
     route_observer_event
[9]  market_replay.run_market_observations implemented; outputs
     restricted to {WAIT, MONITOR, NO_ACTION}
[10] market_replay.run_market_jsonl_file implemented
[11] market_replay CLI implemented
[12] tests/fixtures/market/ has at least 5 valid + 3 invalid fixtures
[13] All v0.1 tests still passing (877 baseline)
[14] All new V2 tests passing (≥80 added)
[15] pyright strict 0 errors
[16] ruff check + format clean
[17] forbidden imports grep (incl. requests/httpx/aiohttp) clean
[18] forbidden outputs grep clean
[19] dry_sim canonical output unchanged: SystemOutput.WAIT
     (audit=4, permanent=2, ring=0)
[20] market replay CLI smoke run on calm fixture exits 0 with
     hash_chain_valid=True
[21] public API additions exported from sentinel.__all__ and
     pinned in tests/test_public_api.py via V2_PUBLIC_API_ADDITIONS
[22] docs/build/0003 (this file) + docs/reviews/0014 (review)
     written
```

---

## 21. Deferred V3+ items

```
- V2.1: Gel.Al one-way local export contract (the export
        format itself; LocalJsonlMarketAdapter is the
        consumer)
- V2.2: optional CI workflow forbidden-grep tightening to
        include requests / httpx / aiohttp at the workflow
        level (currently asserted as per-module source tests)
- V3:   Financial M2 Memory + Recall (memory subjects shaped
        for market context; explicit memory write paths
        beyond v0.1's silent + candidate-only)
- V4:   Replay / counterfactual engine
- V5:   Gel.Al shadow integration (one-way Gel.Al -> Sentinel
        actually wired through a real bridge process)
- V6+:  Constitutional amendment for any path that would
        produce Sentinel -> execution-surface output
- V7+:  Real LLM intent_relay (would require constitutional
        amendment of C-03)
- V8:   Paper / canary / live (would require constitutional
        amendments of C-02 and several other red lines)
```

None of these are started in V2.

---

## 22. Implementation status (post-build)

```
Schema + sanitizer + audit payload builder        SHIPPED  (V2A → V2)
SanitizedMarketProvenance                          SHIPPED  (V2)
SyntheticMarketAdapter                             SHIPPED  (V2)
LocalJsonlMarketAdapter                            SHIPPED  (V2)
build_synthetic_market_manifest                    SHIPPED  (V2)
build_local_jsonl_market_manifest                  SHIPPED  (V2)
emit_market_observation_ingested                   SHIPPED  (V2)
run_market_observations                            SHIPPED  (V2)
run_market_jsonl_file                              SHIPPED  (V2)
market_replay CLI                                  SHIPPED  (V2)
tests/fixtures/market/ (5 valid + 3 invalid)       SHIPPED  (V2)
Public API additions                               SHIPPED  (V2)
Build plan (this doc)                              SHIPPED  (V2)
Review doc (docs/reviews/0014)                     SHIPPED  (V2)

Not shipped (deferred per §21 above):              DEFERRED
    Gel.Al export contract
    CI workflow grep tightening (requests/httpx/aiohttp)
    V3 / V4 / V5 / V6+ work
```

---

## 23. Final hüküm

```
V2 ships read-only market observation as a safe, synthetic /
local-fixture surface. Raw market data stays observer-side.
Core-facing ObservationEvent still carries only normalized
magnitudes. Sentinel remains non-executing. All v0.1
constitutional red lines are preserved. No live integration
exists, by design.
```
