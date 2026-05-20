# 0002 — V2 Read-Only Market Observation Readiness Plan

> **Status: PLAN ONLY. No code, no exchange SDK, no live data,
> no API keys, no execution surface.**
>
> Follow-up to `docs/build/0001-minimum-viable-brain-plan.md`
> (the v0.1 MVB build plan, now realized as the sealed
> v0.1.0-mvb release — see `docs/reviews/0010` +
> `docs/reviews/0011`).
>
> Triggered by `/goal` Phase 2: design how Sentinel can connect
> to **read-only market observation** without crossing the v0.1
> constitutional red lines. This is the **interface contract**
> document — not an implementation. Any subsequent code work is
> gated on Halit's explicit approval of this plan.

---

## 1. Purpose

Specify the boundary, schemas, and bridge options for letting
Sentinel observe real (or synthetic-real-shaped) market data
**without** importing any exchange SDK into the Sentinel repo,
**without** opening any execution path, **without** introducing
order-side semantics into the Core ObservationEvent, and
**without** mutating any account, position, or order state.

The v0.1 MVB observes, audits, and never acts. V2 read-only
market observation expands the *source* of observations beyond
the v0.1 synthetic dev fixtures — it does **not** expand what
Sentinel is allowed to do with them.

---

## 2. Non-goals

```
- No live orders
- No order placement, cancellation, modification
- No account balance read or mutation
- No position read or mutation
- No exchange API keys inside Sentinel repo
- No exchange API keys inside Sentinel environment variables
- No trading SDK imports (ccxt, binance, btcturk, pybit, okx,
  gate_api, kucoin, huobi, bitfinex, kraken, web3)
- No LLM SDK imports (openai, anthropic, langchain)
- No LLM interpretation of market state
- No memory verified-status writes
- No production numerics replacement
- No execution adapter
- No human/LLM-direct recall push
- No automatic strategy threshold mutation
- No automatic kill-switch arming or disarming
- No symbol/venue/exchange names in Core ObservationEvent
- No order-side, side, intent fields in Core schema
- No PnL or balance fields in Core schema
- No backtest-driven memory update
```

---

## 3. Safety constraints

The v0.1 constitutional red lines remain in force without
modification:

```
C-01 SystemOutput membership is closed:
     {WAIT, BLOCK, MONITOR, NEED_RECALL, NO_ACTION}
C-02 No live exchange / venue API integration
C-03 No LLM SDK integration
C-04 No execution-output literals
     ("BUY", "SELL", "EXECUTE_REAL", "ORDER_SUBMIT")
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

V2 must not relax any of these. The CI grep set must remain
strictly a **superset** of the v0.1 grep set; weakening or
removing any banned token is forbidden.

---

## 4. Adapter boundary

The boundary that matters is the **bridge process / observer
adapter / core**. Visualized:

```
+--------------------------+       +-------------------------+
| External market source   |       | Sentinel Core           |
| (Gel.Al Borsa export,    |       |                         |
|  exchange WS via separate|  raw  | route_observer_event    |
|  bridge process, etc.)   |  event| (catalog permanence)    |
|                          | ----> |                         |
|  - exchange SDK lives    |       | ObservationEvent only   |
|    HERE                  |       | (no symbol/venue/side)  |
|  - API keys live HERE    |       |                         |
|  - venue domain labels   |       | WorkspacePulse          |
|    live HERE             |       |                         |
+--------------------------+       | DeonticGate (default    |
       |                           |   deny)                 |
       v sanitize_to_core          |                         |
+--------------------------+       | MemoryWriteGate (silent,|
| ReadOnlyMarketAdapter    |       |   candidate-only)       |
| (in Sentinel repo,       |       |                         |
|  observe-only manifest,  |       | Recall (composite-AND,  |
|  no network code,        |       |   top-1, CORE only)     |
|  no exchange import)     |       |                         |
+--------------------------+       | SystemOutput in         |
                                   |  {WAIT, BLOCK, MONITOR, |
                                   |   NEED_RECALL,          |
                                   |   NO_ACTION}            |
                                   +-------------------------+
```

Key boundary rules:

```
B-01 The exchange SDK NEVER appears in the sentinel/ package
     import graph. CI grep enforces.
B-02 The bridge process is a SEPARATE artifact. It MAY live in
     a separate repository, or in a `bridges/` directory at the
     repo root that is explicitly excluded from CI's import-graph
     grep. (The exclusion is path-scoped; the grep continues to
     enforce that nothing under sentinel/ touches a banned SDK.)
B-03 The bridge process sends ONLY sanitized envelopes to the
     adapter. The adapter accepts ONLY MarketObservationEnvelope
     objects (V2 schema below) — never raw exchange WebSocket
     payloads, never order objects, never private account data.
B-04 The adapter SANITIZES the envelope into a Core-facing
     ObservationEvent (v0.1 schema, unchanged). The sanitization
     strips all market-domain labels.
B-05 The bridge process is read-only by design: it has no write
     capability against any exchange. If a future revision needs
     execution, it lives in a completely separate execution
     engine (Gel.Al Borsa), not in Sentinel.
```

---

## 5. External market event schema (observer-side)

A new Pydantic v2 schema, defined in
`sentinel/adapters/market_observation.py` **when (and only when)
Phase 3 ships**:

```python
class MarketObservationEnvelope(BaseModel):
    """Bridge-to-adapter event. Observer-side only."""
    model_config = ConfigDict(extra="forbid", frozen=True,
                              strict=True)

    # provenance (REQUIRED)
    envelope_id:        UUID            # adapter-assigned
    source_system:      str             # e.g. "gel-al-borsa",
                                        #     "synthetic-fixture",
                                        #     "bridge-binance-readonly"
    source_adapter_id:  str             # canonical adapter id
    timestamp:          datetime        # UTC, tz-aware
    provenance_hash:    str             # hex of canonical
                                        # source payload

    # raw context (observer-side ONLY — never copied into Core)
    venue:              str             # e.g. "binance",
                                        #     "btcturk", "gel-al"
    symbol:             str             # e.g. "BTCUSDT"
                                        # NOT propagated to Core

    # numeric market state (sanitized into Core-facing magnitudes)
    raw_bid:            Decimal
    raw_ask:            Decimal
    spread_pct:         float           # 0.0 <= x
    orderbook_age_ms:   int             # >= 0
    depth_summary:      DepthSummary    # frozen sub-schema
    latency_ms:         int             # bridge -> adapter
```

`DepthSummary` is a small, **opaque** roll-up:

```python
class DepthSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True,
                              strict=True)
    bid_top_n_qty:      Decimal         # sum of top-N bid qty
    ask_top_n_qty:      Decimal         # sum of top-N ask qty
    imbalance_ratio:    float           # in [-1.0, 1.0]
    # NOTE: no per-level order book. Sentinel core does not need
    # the book. The bridge computes the summary; the adapter
    # passes the summary as-is into observer-side raw fields.
```

**No order-side fields.** Bid/ask are price levels, not buy/sell
intents. The schema does not contain a `side`, `intent`,
`signal`, `direction`, or anything that resembles a trade verb.

---

## 6. Observer-side raw provenance

The envelope's market-domain fields (`venue`, `symbol`,
`raw_bid`, `raw_ask`, `depth_summary`, ...) are kept on the
**observer side of the boundary**. They are recorded in the
adapter's audit trail (M1 ledger) under a new
`MARKET_OBSERVATION_ENVELOPE_RECEIVED` event family, with
permanence policy `permanent_with_snapshot` (chain entry
+ full envelope snapshot for forensic re-derivation), exactly
analogous to how `ADAPTER_MANIFEST_STATUS_CHANGED` works today.

The Core side **never sees these fields.** The mapping
function (next section) strips them.

---

## 7. Core-facing ObservationEvent mapping

The Core `ObservationEvent` schema **does not change in V2**.
It remains the v0.1 schema. The V2 adapter implements:

```python
def sanitize_to_observation_event(
    envelope: MarketObservationEnvelope,
) -> ObservationEvent:
    """Observer-side -> Core-facing.

    Strips every market-domain label. Maps numeric state to
    Core-allowed magnitudes only.
    """
```

The mapping rules (no exceptions):

```
envelope.spread_pct        -> magnitude_normalized
                              (clipped to [0.0, 1.0])
envelope.imbalance_ratio   -> directional_pressure_normalized
                              (clipped to [-1.0, 1.0]; this is
                              NOT a buy/sell intent — it is a
                              symmetric numeric pressure
                              magnitude with sign)
envelope.orderbook_age_ms  -> staleness_ms
envelope.latency_ms        -> source_latency_ms
envelope.provenance_hash   -> ProvenanceRef.hash
envelope.source_adapter_id -> source_adapter_id
                              (already an opaque adapter ID,
                              not a venue name)
adapter trust band         -> source_reliability_band
                              (derived from AdapterTrustRecord
                              with multiplicative trust per v0.1)

envelope.venue             -> DROPPED
envelope.symbol            -> DROPPED
envelope.raw_bid           -> DROPPED
envelope.raw_ask           -> DROPPED
envelope.depth_summary.*   -> DROPPED (only imbalance_ratio
                              survives via the mapping above)
```

The sanitizer is **a pure function**. No I/O, no logging, no
network. It is unit-testable with synthetic envelopes.

A property test will assert: for any randomly generated
`MarketObservationEnvelope`, the resulting `ObservationEvent`
contains **none** of the forbidden labels (`venue`, `symbol`,
`raw_bid`, `raw_ask`, exchange names, side keywords).

---

## 8. No exchange SDK in Sentinel repo (rule)

**Rule.** No file under `sentinel/` may `import ccxt`,
`import web3`, `import binance`, `import btcturk`,
`import pybit`, `import okx`, `import gate_api`,
`import kucoin`, `import huobi`, `import bitfinex`,
`import kraken`, `import openai`, `import anthropic`,
`import langchain`. The v0.1 CI grep already enforces this;
V2 does not relax it.

Corollary: the V2 read-only adapter (when written) imports
**zero** network or exchange libraries. Its inputs are
`MarketObservationEnvelope` objects produced by an external
bridge.

---

## 9. Gel.Al Borsa bridge options

```
A. Sentinel standalone synthetic market fixture
   - Sentinel ships a deterministic synthetic generator
     (under tests/fixtures/synthetic_market/) that produces
     MarketObservationEnvelope objects.
   - Used for unit tests + integration tests + dry sim.
   - Zero external dependency.
   - GREEN for development.

B. Gel.Al Borsa exports read-only JSON events
   - Gel.Al's execution engine, which already has authenticated
     market access, writes sanitized JSON files (or pushes to a
     local queue) describing market state.
   - Sentinel reads those files. Sentinel never touches the
     exchange.
   - Gel.Al's surface to Sentinel is read-only by virtue of
     filesystem direction: Gel.Al writes, Sentinel reads.
   - Preferred for the first real-data shadow window.

C. External bridge process reads exchange / Gel.Al and sends
   sanitized events to Sentinel
   - A separate Python process (e.g. `bridges/binance_ro/`
     in a sibling repo) imports ccxt, opens a public market
     WebSocket, and emits MarketObservationEnvelope objects
     over an IPC channel (unix socket / file watch / stdout
     JSONL).
   - The bridge is the ONLY thing that imports ccxt. Sentinel
     itself does not. CI grep continues to enforce.
   - Acceptable if the bridge is in a sibling repo with its
     own constitution; out of scope for Sentinel's v0.1 +
     v2-readonly-plan repo audit.

D. Direct Sentinel exchange SDK import — FORBIDDEN.
   - Not allowed. Period. v0.1 constitutional red line C-02.
```

Preferred sequence: **A → B → C**. Option D is permanently off
the table for the Sentinel repo.

---

## 10. Synthetic fixture strategy

For Phase 3 readiness (if ever taken), Sentinel produces its
own deterministic fixtures under:

```
tests/fixtures/synthetic_market/
    0001-tight-spread-quiescent.json
    0002-wide-spread-stale.json
    0003-large-imbalance-low-confidence.json
    0004-fresh-balanced-medium-pressure.json
    0005-stale-orderbook-veto.json
```

Each is a `MarketObservationEnvelope` JSON serialization. They
exercise:

```
- magnitude near zero (quiescent)
- magnitude high (wide spread)
- imbalance sign positive / negative / zero
- staleness within bounds / above bound (triggers recall
  trigger rejection by core's existing rules)
- latency within bounds / above bound
- provenance hash consistency
```

Output expectation across the synthetic suite:
**SystemOutput.WAIT or SystemOutput.MONITOR only.** Never any
member of the execution set, because the deontic gate remains
default-deny and no `ApprovedActionIntent` is ever produced
from market data alone.

---

## 11. Read-only adapter manifest

The V2 adapter, when written, registers a manifest:

```python
ADAPTER_MANIFEST = AdapterManifest(
    adapter_id="market-observation-readonly-v2",
    output_channels=frozenset({"OBSERVE"}),
    # NeuralSeed channel ABSENT — emission would trigger
    # ADAPTER_MANIFEST_STATUS_CHANGED reason=
    # neural_seed_emission_attempt and InvariantViolation
    # (covered by v0.1 invariant catalog row).
    trust_band=TrustBand.LOW,           # bootstrap
    multiplicative_trust=Decimal("0.0"),# starts at zero,
                                        # not configurable
                                        # by the adapter
                                        # itself.
    signature=...                       # signed mock (v0.1
                                        # signing model;
                                        # real crypto is
                                        # explicitly deferred
                                        # per v0.1 release
                                        # note "Deferred V2+
                                        # items").
)
```

The manifest is OBSERVE-only. The constitutional invariant
that adapters cannot emit NeuralSeed (S-02 in audit 0011) is
re-asserted at adapter registration time.

---

## 12. SourceTrust / AdapterTrust bootstrap

V2 inherits the v0.1 multiplicative-trust model from
`sentinel/adapters/trust.py`:

```
- New market-observation adapter starts at multiplicative
  trust 0.0 (no influence).
- Trust adjusts only via the existing v0.1 trust update
  mechanism (no new path, no LLM-driven trust, no human-
  direct trust write).
- Trust is multiplicative: source_reliability_band is
  multiplied into the magnitude before workspace pulse,
  meaning a brand-new adapter's signals are effectively
  invisible to the system until trust accrues.
- Trust accrual procedure for V2 is deliberately NOT
  specified in this plan. It is a V2-implementation
  concern, not a V2-readiness concern. The plan does NOT
  promise an accrual mechanism beyond the v0.1 default.
```

---

## 13. Ingress compiler mapping impact

`sentinel/ingress/compiler.py` operates over a fixed set of
profile caps + soft overlap + rules + compiled output.
V2 read-only market envelopes feed into the compiler via the
sanitized `ObservationEvent`, which is **the same v0.1 schema
the compiler already accepts.**

Therefore the ingress compiler **does not change in V2**.

If a future profile cap needs adjustment to reflect typical
market-observation magnitudes, that adjustment will be a
v0.1-style numerics change (signed dev_only fixture →
production matrix review), gated by the dev_only guard in
`sentinel/numerics/loader.py`. Out of scope for this plan.

---

## 14. M1 audit events

Two new ObserverEvent rows are reserved in the catalog (NOT
added in this plan — reservation only):

```
MARKET_OBSERVATION_ENVELOPE_RECEIVED
    permanence: permanent_with_snapshot
    Family: observer
    Reason field: observer-side reception confirmation
    Payload: hash of envelope + envelope_id + source_system

MARKET_OBSERVATION_ENVELOPE_REJECTED
    permanence: permanent
    Family: observer
    Reason: schema_violation | stale | latency_breach |
            adapter_untrusted | duplicate_envelope_id
```

Both events are written via `route_observer_event` and respect
the existing permanence-aware router. No silent rejection.

(The `ObservationEvent` row in the existing catalog —
`OBSERVATION_INGESTED`, permanence `ring_buffer_only` —
remains as-is. The sanitized core-facing event flows through
that row, unchanged from v0.1.)

---

## 15. Dry-run evaluation metrics

For the readiness sign-off (before any code lands), the
synthetic fixture suite must produce:

```
- 100% canonical-run reproducibility
- SystemOutput ∈ {WAIT, MONITOR} for every fixture
- Zero forbidden-output literals in any ledger entry
- Hash chain re-verifies on every run
- All MARKET_OBSERVATION_ENVELOPE_RECEIVED events have
  permanence_with_snapshot, fully serializable, deterministic
  payload hash
- All envelopes that fail sanitation produce
  MARKET_OBSERVATION_ENVELOPE_REJECTED with a reason from the
  fixed enum above
- No symbol / venue / exchange string survives into any
  Core-facing ObservationEvent — property test asserts
- No order-side / intent / direction string appears in any
  Core-facing ObservationEvent — property test asserts
```

The dry-run is the gate. If any of the above misses, V2 work
stops and the failure is documented honestly.

---

## 16. Forbidden surfaces

```
- No `import ccxt` (or any of the banned SDKs) under sentinel/
- No `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, exchange API keys
  in any sentinel/ module
- No live HTTP / WebSocket connection initiated from sentinel/
- No `requests` / `httpx` / `aiohttp` call targeting an
  exchange domain from sentinel/
- No `BUY`, `SELL`, `EXECUTE_REAL`, `ORDER_SUBMIT` string
  anywhere in sentinel/
- No order-side enum in any Core-facing schema
- No PnL field in any Core-facing schema
- No account / balance / position field in any Core-facing
  schema
- No memory verified-status write driven by market data
- No production numerics matrix update driven by market data
- No replay write driven by market data
- No deontic gate bypass for "the market says so"
- No human-direct recall push from market data
- No LLM interpretation of market state
```

---

## 17. Done definition

V2 read-only market observation **planning** is "done" when
this document is approved by Halit and the companion
integration alignment doc
(`docs/integrations/gel-al-borsa-readonly-bridge.md`) is
approved.

V2 read-only market observation **implementation** (Phase 3,
not part of this PR) is "done" when:

```
- A `MarketObservationEnvelope` Pydantic schema lives under
  sentinel/adapters/market_observation.py
- A pure `sanitize_to_observation_event` function exists in
  the same module
- A synthetic fixture suite under tests/fixtures/
  synthetic_market/ exists
- All v0.1 invariants still hold (12/12 in audit 0011)
- Two new ObserverEvent rows are added to the catalog
- The CI grep set is UNCHANGED (still a strict superset of
  v0.1's)
- No network code lives under sentinel/
- A property test asserts no banned label propagates into
  Core ObservationEvent
- All 877+N tests pass (the +N is the new market-observation
  tests; the 877 v0.1 tests do not regress)
- Pyright strict: 0 errors
- Ruff: clean
- A new release readiness review (e.g. 0012) is written and
  approved before any tag move
```

Implementation is **explicitly out of scope** for this plan.

---

## 18. V2 implementation sequence

Strictly sequential — each step gated on the previous.

```
S-1. Halit approves this plan + integrations alignment doc.
     -> No code yet.

S-2. Catalog rows reserved (two new ObserverEvent kinds added
     to sentinel/observer/catalog.py with documented
     permanence). Tests in tests/observer/
     test_catalog_consistency.py extended.
     -> Pure data addition. No adapter code, no schema yet.

S-3. MarketObservationEnvelope + DepthSummary schemas land in
     sentinel/adapters/market_observation.py with extra=forbid,
     frozen, strict. Unit tests cover field validation.
     -> Pure schema. Zero behavior.

S-4. sanitize_to_observation_event lands as a pure function in
     the same module. Unit tests + property test cover
     sanitization invariants.
     -> Pure function. No I/O.

S-5. Synthetic fixture suite under tests/fixtures/
     synthetic_market/ lands. Integration test drives
     fixtures through the pipeline. Outputs asserted
     ∈ {WAIT, MONITOR}.

S-6. ReadOnlyMarketAdapter (observe-only manifest) lands in
     sentinel/adapters/market_observation.py. Adapter
     registration emits ADAPTER_MANIFEST_STATUS_CHANGED.
     Adapter does not import any banned SDK; this is grep-
     enforced.

S-7. End-to-end dry simulation extended (optional
     synthetic-envelope mode in runtime/dry_sim.py).
     Outputs strictly ∈ {WAIT, MONITOR}.

S-8. V2 release readiness review (docs/reviews/0012-...)
     written. No tag move without it.
```

If at any step a constitutional red line would be touched,
the sequence stops. The release does not move forward by
silently relaxing a check; the check holds.

---

## 19. Final hüküm

```
Plan only. Zero code in this commit.
v0.1 constitutional red lines are PRESERVED unchanged.
Phase 3 (V2 schema/stub code) is DEFERRED — per /goal:
    "Eğer bu küçük stub bile fazla scope büyütüyorsa:
     Kod yazma. Sadece plan + review ile dur."
The plan is intentionally complete enough to be approved or
rejected on its own merits, without partial implementation
clouding the decision.
```
