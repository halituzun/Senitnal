# 0004 — V3 Financial M2 Memory + Recall Build Plan

> Successor to `docs/build/0003-v2-read-only-market-adapters-build-plan.md`.
>
> V3 wires the V2 read-only market observation surface into the v0.1
> M2 explicit memory store via the Memory Write Gate, and adds a
> deterministic financial recall query / RecallEvent builder on top
> of the v0.1 recall protocol. Every v0.1 + V2 constitutional red
> line is preserved.

---

## 1. Purpose

Give Sentinel a safe way to:

```
1. Receive sanitized read-only market observations (V2)
2. Derive financial payloads from those observations
3. Submit candidate memory writes through the v0.1 Memory Write Gate
4. Maintain a local / dev explicit M2 store of accepted candidates
5. Run core-originated financial recall queries with top-1 selection
6. Build a v0.1 RecallEvent for the surfaced record
7. Audit every memory + recall event through M1 (sanctioned router /
   ledger only)
```

V3 does NOT:
  - call exchanges
  - speak to LLMs
  - import network libraries
  - touch live execution
  - produce verified M2 records (v0.1
    `mvp_verified_disabled=True` is unchanged)
  - synthesize ApprovedActionIntent
  - bypass the Memory Write Gate or the recall protocol

---

## 2. Non-goals

```
- No live trading
- No execution / order placement
- No live exchange API (any of ccxt, binance, btcturk, pybit,
  okx, gate_api, kucoin, huobi, bitfinex, kraken, web3)
- No network libraries (requests, httpx, aiohttp, urllib3,
  socket, asyncio.subprocess) under sentinel/
- No API key / API secret / account balance fields
- No LLM (openai, anthropic, langchain)
- No production verified memory production without explicit
  evidence-axis matrix change (out of V3 scope)
- No replay / counterfactual engine
- No Gel.Al live bridge
- No strategy recommendation output
- No direct action triggered by recall
- No new SubjectClass enum value
- No use of foreign_instance_origin as a subject_class
- No narrative_claim / causal_explanation / decision_rationale
  recall path for V3 financial memory
- No candidate recall for any subject_class other than
  source_trust or procedural
- No quarantined / rejected / expired records surfaced via recall
```

---

## 3. Safety constraints

All v0.1 + V2 constitutional red lines remain in force. The CI
grep set is a strict superset of v0.1's. V3 tests assert the
forbidden-import set (including `requests`/`httpx`/`aiohttp`) on
each new module via per-module source-grep tests.

---

## 4. Existing M2 subject_class mapping

V3 introduces five financial payload families mapped to FOUR
existing v0.1 SubjectClass values. No new SubjectClass is added.

```
MarketRegimeObservationPayload     -> STRUCTURED_FACT
SpreadWindowObservationPayload     -> STRUCTURED_FACT
LiquidityConditionPayload          -> STRUCTURED_FACT
LatencyPatternPayload              -> SOURCE_TRUST
ExecutionQualityObservationPayload -> PROCEDURAL
```

This mapping exercises both sides of the Memory Write Gate:

```
SOURCE_TRUST + DIRECT_OBSERVATION  -> accepted by MWG whitelist
                                       -> CANDIDATE write, stored
PROCEDURAL + INTERNAL_INFERENCE     -> accepted by MWG whitelist
                                       -> CANDIDATE write, stored
STRUCTURED_FACT + any axis          -> NOT in MWG whitelist
                                       -> REJECTED, audit emitted,
                                          record NOT stored
```

The three STRUCTURED_FACT payload families are intentionally
unable to land in M2 in V3. This is the constitutional rule from
`sentinel/gates/memory_write.py` — V3 does NOT weaken it.

---

## 5. Financial memory payload families

`sentinel/memory/financial.py` defines 5 Pydantic v2 models, all
with `extra='forbid'`, `frozen=True`, `strict=True`. Every payload:

```
- Carries symbol_hash / venue_hash (observer-side opaque hashes)
  rather than raw symbol/venue strings — domain labels do NOT
  enter M2 payload directly.
- Records source_event_ids tuple (non-empty; each entry
  non-empty); this is the causal anchor for the candidate's
  external corroboration.
- Has a confidence ∈ [0, 1] (where applicable).
- Cross-field consistency (e.g. window_end >= window_start,
  max >= p95 >= avg, min <= avg <= max).
- Rejects forbidden execution / account / order fields via
  extra='forbid' (order_id, live_fill_id, account_id, side,
  order_side, api_key, api_secret, balance, position, leverage,
  take_profit, stop_loss, trade_intent, strategy_action, ...).
```

---

## 6. Candidate write flow

`sentinel/memory/builder.py` exposes
`build_candidate_financial_memory_record(...)`. Always builds
status=CANDIDATE. No verified path exists in the API.

`sentinel/memory/write_path.py` exposes
`submit_financial_memory_candidate(...)`. It:

```
1. builds the candidate record (always CANDIDATE)
2. constructs a MemoryWriteRequest(requested_status=CANDIDATE)
3. calls submit_memory_write (silent v0.1 gate)
4. if outcome is ACCEPTED_CANDIDATE or DOWNGRADED_TO_CANDIDATE:
     store.add(record)
   else (REJECTED):
     leave store untouched.
```

The gate's M1 audit event (MEMORY_RECORD_STATUS_CHANGED) is
emitted regardless of outcome.

---

## 7. Verification / status discipline

V3 never produces a VERIFIED record. `mvp_verified_disabled` is
True. Requests are always for CANDIDATE. The MWG's verified path
remains gated behind a future evidence-axis matrix change that
V3 does NOT make.

```
ACCEPTED_VERIFIED         never returned in V3
DOWNGRADED_TO_CANDIDATE   never returned in V3 (we never
                          request VERIFIED)
ACCEPTED_CANDIDATE        the only positive resolution V3 uses
REJECTED                  produced when subject/evidence-axis
                          pair is not in the MWG whitelist
                          (e.g. STRUCTURED_FACT payloads)
```

---

## 8. Recall request flow

`sentinel/recall/financial.py` defines:

```
FinancialRecallScope        subject_classes + max_records_considered
                            + include_candidates
                            (include_candidates does NOT override
                             the v0.1 source_trust/procedural
                             whitelist)
FinancialRecallRequest      request_id + source + scope + created_at_ms
                            source MUST be RecallTriggerSource.CORE;
                            HUMAN_DIRECT / LLM / REPLAY / SUMMARIZER
                            rejected at __post_init__
```

---

## 9. Recall ranking / scoring

`score_record_for_request` uses the v0.1
`compute_recall_score` multiplicative formula:

```
score = status_weight
      * provenance_strength
      * freshness_dampening (= payload confidence)
      * (1 - contradiction_penalty)        (= 1, V3)
      * (1 - habituation_penalty)          (= 1, V3)
      * scope_match_score                  (1 if subject_class in
                                            scope, else 0)
```

`status_weight`: VERIFIED=1.0, ACTIVE=0.85, CANDIDATE=0.5,
others=0.

`provenance_strength`: bucketed by external corroboration count
(0 refs -> 0.25, 1 -> 0.5, 2 -> 0.75, 3+ -> 1.0).

`select_financial_recall_top_one`:
  - pulls from `store.query_recallable` (which enforces the
    candidate whitelist + excludes rejected/expired/quarantined)
  - filters by scope.subject_classes
  - truncates to max_records_considered
  - drops zero-score records
  - delegates to v0.1 `select_top_one` (deterministic tie-break
    on smaller record_id)

---

## 10. Candidate recall restrictions

`store.query_recallable` enforces:

```
NEVER recallable:    rejected, expired, quarantined
default excluded:    superseded   (include_superseded=True
                                    opt-in)
candidate recallable only when subject_class in
{source_trust, procedural} (v0.1 whitelist from
sentinel/recall/candidate.py)
```

`build_financial_recall_event` additionally:

```
- raises ValueError for rejected/expired/quarantined records
- raises InvariantViolation (via
  validate_candidate_recall_subject) for any candidate whose
  subject_class is outside the whitelist
- caps candidate-record confidence at 0.5 in the resulting
  RecallEvent
```

---

## 11. Observer audit events

V3 uses ONLY existing canonical event types. No new
ObserverEvent catalog row is added.

```
OBSERVATION_INGESTED                (ring_buffer_only)   V2 path
MEMORY_RECORD_STATUS_CHANGED        (permanent)          MWG
RECALL_REQUEST_EMITTED              (permanent)          recall
RECALL_RESULT_EMPTY                 (permanent)          recall
RECALL_TRIGGER_REJECTED             (permanent)          recall
```

---

## 12. Store abstraction

`sentinel/memory/store.py` ships `InMemoryExplicitMemoryStore`.
Local / dev / test only — NOT a production database. Persistent
M2 (durable, multi-process, replicated) is out of V3 scope.

The store rejects duplicate record_ids at `add`-time. It does
NOT bypass MWG; callers are expected to use
`submit_financial_memory_candidate`, which calls MWG first and
only invokes `store.add` after acceptance.

---

## 13. Synthetic market replay integration

`sentinel/runtime/financial_memory_pipeline.py` exposes the
end-to-end run that V3 closes:

```
run_financial_memory_pipeline(
    *,
    observations,        Iterable[MarketObservationEnvelope]
    store,
    ledger,
    ring_buffer,
    provenance,
    emit_recall_after_writes = True,
    recall_request_id = "fin-recall-pipeline-1",
) -> FinancialMemoryPipelineResult
```

Per envelope: emit OBSERVATION_INGESTED via router (ring-only),
derive a LatencyPatternPayload (SOURCE_TRUST), submit through
MWG, accept as candidate, store. After the loop (optional):
run a core-originated recall request scoped to SOURCE_TRUST +
PROCEDURAL, select top-1, emit RECALL_REQUEST_EMITTED (or
RECALL_RESULT_EMPTY), build a RecallEvent.

The base `run_dry_simulation` is UNTOUCHED. V3 does NOT change
the canonical v0.1 dry-sim output tuple.

---

## 14. Public API decision

Curated V3 public symbols (added to `sentinel.__all__`):

```
ExecutionQualityObservationPayload
FinancialMemoryPipelineResult
FinancialMemoryWriteResult
FinancialRecallRequest
FinancialRecallScope
InMemoryExplicitMemoryStore
LatencyPatternPayload
LiquidityConditionPayload
MarketRegimeObservationPayload
SpreadWindowObservationPayload
build_candidate_financial_memory_record
build_financial_recall_event
run_financial_memory_pipeline
select_financial_recall_top_one
submit_financial_memory_candidate
```

Pinned in `tests/test_public_api.py` via `V3_PUBLIC_API_ADDITIONS`
with a drift test.

Internal helpers (`financial_payload_subject_class`,
`score_record_for_request`) are NOT exported.

---

## 15. Tests and invariants

```
tests/memory/test_financial_payloads.py
    schema validation across all 5 payload families
    + cross-field consistency + extra='forbid' + subject_class
    mapping (asserts no new SubjectClass, mapping uses existing
    enum, never narrative/causal/decision)

tests/memory/test_builder_and_store.py
    builder always-CANDIDATE / payload JSON-roundtrip /
    no verified path
    store add/get/list/query_by_subject_class /
    duplicate rejection / recallable filter
    (rejected/expired/quarantined excluded; candidate gated
    by source_trust+procedural whitelist; structured_fact
    candidate excluded; verified+active included; superseded
    excluded by default)

tests/memory/test_write_path.py
    SOURCE_TRUST + DIRECT_OBSERVATION accepted
    PROCEDURAL + INTERNAL_INFERENCE accepted
    STRUCTURED_FACT rejected (not stored, audit emitted)
    Disallowed evidence axis pair rejected
    No verified path returned in V3

tests/recall/test_financial.py
    FinancialRecallRequest source must be CORE
    (HUMAN_DIRECT / LLM / REPLAY / SUMMARIZER all rejected)
    top-1 selection / deterministic tie-break
    verified beats candidate same-score
    rejected/expired/quarantined excluded
    structured_fact candidate ineligible
    source_trust / procedural candidate eligible
    RecallEvent for verified / active / candidate
    RecallEvent for terminal states rejected
    No raw symbol/venue in RecallEvent

tests/runtime/test_financial_memory_pipeline.py
    valid envelopes -> candidate records written
    recall request emitted after writes
    no observations -> no recall
    MEMORY_RECORD_STATUS_CHANGED emitted
    hash chain verifies
    no ApprovedActionIntent / evaluate_action / DeonticGate
        in source
    no forbidden imports / output literals in source
    OBSERVATION_INGESTED stays ring-only
```

---

## 16. Forbidden surfaces (V3 line-item)

```
- import ccxt / binance / btcturk / pybit / okx / gate_api /
  kucoin / huobi / bitfinex / kraken / web3 — FORBIDDEN
- import openai / anthropic / langchain — FORBIDDEN
- import requests / httpx / aiohttp / urllib3 / socket — FORBIDDEN
  in V3 modules
- API key / secret field on any V3 schema — FORBIDDEN
  (extra='forbid' rejects)
- order side / order type / quantity / amount field on V3
  schemas — FORBIDDEN
- account_id / balance / position / leverage / take_profit /
  stop_loss / trade_intent / strategy_action — FORBIDDEN
- BUY / SELL / EXECUTE_REAL / ORDER_SUBMIT literals — FORBIDDEN
- new SubjectClass values — FORBIDDEN
- foreign_instance_origin as subject_class — FORBIDDEN
- narrative_claim / causal_explanation / decision_rationale
  candidate recall — FORBIDDEN
- quarantined / rejected / expired recall — FORBIDDEN
- human / LLM / replay / summarizer recall trigger — FORBIDDEN
- M2 verified write — FORBIDDEN in V3 (gate downgrades)
- ApprovedActionIntent construction in V3 modules — FORBIDDEN
- bypass of route_observer_event — FORBIDDEN
- promotion of OBSERVATION_INGESTED / WORKSPACE_PULSE to
  permanent — FORBIDDEN
- new ObserverEvent catalog row — NOT introduced in V3
```

---

## 17. Done definition

```
[1]  5 financial payload schemas implemented
[2]  No new SubjectClass values added
[3]  Payloads map to existing SubjectClass
[4]  build_candidate_financial_memory_record (CANDIDATE only)
[5]  InMemoryExplicitMemoryStore implemented
[6]  submit_financial_memory_candidate uses MWG
[7]  No verified records produced in V3
[8]  FinancialRecallRequest + FinancialRecallScope implemented
     (CORE-only source)
[9]  select_financial_recall_top_one (top-1, deterministic)
[10] Candidate recall restricted to source_trust/procedural
[11] rejected/quarantined/expired records excluded from recall
[12] build_financial_recall_event with capped candidate
     confidence
[13] No raw symbol/venue leakage into RecallEvent
[14] run_financial_memory_pipeline ties V2 + V3 together
[15] OBSERVATION_INGESTED stays ring-only
[16] Hash chain verifies after pipeline run
[17] All v0.1 tests still passing (877 baseline)
[18] All V2 tests still passing (+87)
[19] All V3 tests passing (+94)
[20] Public API additions exported + pinned in test
[21] docs/build/0004 (this file) + docs/reviews/0015 (review)
     written
[22] pyright strict 0 errors
[23] ruff check + format clean
[24] forbidden imports + outputs grep clean
[25] dry_sim canonical run unchanged
```

---

## 18. Deferred V4+ items

```
- V4: Replay / counterfactual engine
- V5: Gel.Al shadow integration (one-way live bridge)
- V6+: Constitutional amendment for Sentinel -> execution
  surface
- Production verified memory (would require evidence-axis
  matrix change + MWG amendment)
- Persistent durable M2 store (multi-process / replicated)
- Memory subject_class taxonomy extension (would require
  constitutional amendment)
- Memory replay-driven update (would require
  mvp_replay_enabled flag flip)
- LLM-mediated recall (would require constitutional
  amendment)
- Real exchange SDK / network market feed
- New ObserverEvent catalog rows for finance-domain audit
  events
- CI workflow forbidden-grep widening to include
  requests/httpx/aiohttp at workflow level
```

None of these are started in V3.

---

## 19. Implementation status

```
sentinel/memory/financial.py                      SHIPPED
sentinel/memory/builder.py                        SHIPPED
sentinel/memory/store.py                          SHIPPED
sentinel/memory/write_path.py                     SHIPPED
sentinel/recall/financial.py                      SHIPPED
sentinel/runtime/financial_memory_pipeline.py     SHIPPED
sentinel/__init__.py public API additions         SHIPPED
tests/memory/test_financial_payloads.py           SHIPPED
tests/memory/test_builder_and_store.py            SHIPPED
tests/memory/test_write_path.py                   SHIPPED
tests/recall/test_financial.py                    SHIPPED
tests/runtime/test_financial_memory_pipeline.py   SHIPPED
docs/build/0004 (this file)                       SHIPPED
docs/reviews/0015 (review)                        SHIPPED

DEFERRED (per §18 above):
    on-disk JSONL fixture suite for financial memory  (in-memory
        tests already exercise every scenario the proposed
        fixture suite would have)
    new ObserverEvent catalog rows for finance-specific audit
        (V3 reuses existing rows; new rows would be a V4+
        constitutional change)
    persistent / multi-process / durable M2 store
    production-verified memory path
```

---

## 20. Final hüküm

```
V3 ships financial M2 memory + recall as a candidate-only,
audit-disciplined surface. Read-only market observations turn
into candidate memory; candidates pass through the silent
Memory Write Gate; only accepted source_trust + procedural
records become recallable; recall is top-1, core-only,
domain-label-free. Sentinel remembers safely. Sentinel does
NOT act.
```
