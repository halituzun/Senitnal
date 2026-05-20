# 0015 — V3 Financial M2 Memory + Recall Review

> Closes V3 — Financial M2 Memory + Recall. Companion to
> `docs/build/0004-v3-financial-m2-memory-recall-build-plan.md`.
>
> Builds on the V2 read-only market adapter surface (review 0014)
> and the v0.1 MVB memory + recall infrastructure. Every v0.1 + V2
> constitutional red line is preserved.

---

## 1. Status

```
Version                                  V3 — Financial M2 Memory + Recall
Phase                                    end-to-end CLOSURE
Source code added                        YES (6 new modules; additive only)
CI workflow changed                      NO
Forbidden grep relaxed                   NO
Exchange SDK / LLM import added          NO
Network library import added             NO
Live execution path                      NONE
Verified M2 production                   NONE  (mvp_verified_disabled
                                                stays True; V3 wrapper
                                                always requests CANDIDATE)
New SubjectClass enum value              NONE  (5 payloads map to 3
                                                existing values:
                                                STRUCTURED_FACT,
                                                SOURCE_TRUST, PROCEDURAL)
ApprovedActionIntent in V3 modules       NONE  (asserted by source grep)
Candidate recall whitelist relaxation    NONE  (source_trust + procedural
                                                whitelist enforced via
                                                store + recall builder)
Test count                               964 (V2) -> 1059 (V3)
                                          +95 (94 V3 + 1 V3 public-API
                                          drift test)
pyright                                  0 errors / 0 warnings /
                                          0 informations
ruff check                               clean
ruff format --check                      clean (149 files)
dry sim                                  SystemOutput.WAIT
                                          (audit=4, permanent=2, ring=0)
                                          — unchanged
hash chain                               re-verifies True
Final verdict                            **GREEN**
```

---

## 2. Scope completed

```
[1]  Financial memory payload schemas               done
[2]  No new SubjectClass values added               done
[3]  Subject class mapping uses existing enum       done
[4]  Candidate-only builder                         done
[5]  Local InMemoryExplicitMemoryStore              done
[6]  Memory write path wired through MWG            done
[7]  No verified production                         done
[8]  Recall query (FinancialRecallScope/Request)    done
[9]  Recall ranking (top-1, deterministic)          done
[10] Candidate recall restricted source_trust/
     procedural                                     done
[11] rejected/expired/quarantined excluded          done
[12] RecallEvent builder + raw-label-free output    done
[13] V2-to-V3 pipeline (financial_memory_pipeline)  done
[14] Public API additions + drift test              done
[15] V3 build plan (docs/build/0004)                done
[16] V3 review (this file)                          done
```

16/16 done-definition items GREEN.

---

## 3. Files added

```
sentinel/memory/__init__.py                        (new — empty package marker)
sentinel/memory/financial.py                       (new)
sentinel/memory/builder.py                         (new)
sentinel/memory/store.py                           (new)
sentinel/memory/write_path.py                     (new)
sentinel/recall/financial.py                      (new)
sentinel/runtime/financial_memory_pipeline.py     (new)

tests/memory/__init__.py                          (new — empty package marker)
tests/memory/test_financial_payloads.py           (new)
tests/memory/test_builder_and_store.py            (new)
tests/memory/test_write_path.py                   (new)
tests/recall/test_financial.py                    (new)
tests/runtime/test_financial_memory_pipeline.py   (new)

sentinel/__init__.py                              (modified — V3 exports)
tests/test_public_api.py                          (modified — V3 baseline
                                                    + drift test)

docs/build/0004-v3-financial-m2-memory-recall-build-plan.md  (new)
docs/reviews/0015-v3-financial-m2-memory-recall-review.md    (this file)
```

---

## 4. M2 subject_class mapping

Five financial payload families map to **three existing** v0.1
SubjectClass values:

```
MarketRegimeObservationPayload     -> STRUCTURED_FACT
SpreadWindowObservationPayload     -> STRUCTURED_FACT
LiquidityConditionPayload          -> STRUCTURED_FACT
LatencyPatternPayload              -> SOURCE_TRUST
ExecutionQualityObservationPayload -> PROCEDURAL
```

Constitutional implication: STRUCTURED_FACT is NOT in the MWG
MVP-accepted-pair whitelist. Submitting any of the three regime
/ spread / liquidity payloads results in MWG REJECTION with
audit `MEMORY_RECORD_STATUS_CHANGED(new_status=rejected)` —
the record is NOT stored. This is the v0.1 gate rule and V3
respects it without weakening.

LatencyPatternPayload (SOURCE_TRUST + DIRECT_OBSERVATION) and
ExecutionQualityObservationPayload (PROCEDURAL +
INTERNAL_INFERENCE) DO pass the MWG and become stored
candidates.

V3 introduces **zero** new SubjectClass values. The v0.1
16-member enum stands.

---

## 5. Candidate write discipline

```
[+] requested_status always CANDIDATE
[+] MWG silent (no core-facing return read by caller; only audit)
[+] MWG verified path stays gated by mvp_verified_disabled=True
[+] Accepted -> store.add (which rejects duplicate record_ids)
[+] Rejected -> store untouched; M1 audit emitted
[+] Every MWG decision produces a permanent
    MEMORY_RECORD_STATUS_CHANGED audit event
```

---

## 6. Recall discipline

```
[+] FinancialRecallRequest.source MUST be RecallTriggerSource.CORE
    (HUMAN_DIRECT / LLM / REPLAY / SUMMARIZER rejected at
     construction)
[+] store.query_recallable excludes rejected / expired /
    quarantined unconditionally
[+] store.query_recallable allows candidate only when
    subject_class in {SOURCE_TRUST, PROCEDURAL} (v0.1 whitelist
    enforced via sentinel/recall/candidate.py)
[+] superseded excluded by default
[+] select_financial_recall_top_one delegates to v0.1
    select_top_one (deterministic tie-break by smaller
    record_id)
[+] build_financial_recall_event raises on REJECTED / EXPIRED /
    QUARANTINED
[+] build_financial_recall_event invokes
    validate_candidate_recall_subject for any CANDIDATE source
[+] Candidate-record RecallEvent confidence capped at 0.5
[+] No raw symbol / venue / source_system / raw_ref in the
    RecallEvent (v0.1 RecallEvent extra='forbid' anyway)
```

---

## 7. Pipeline

```
MarketObservationEnvelope
    -> emit_market_observation_ingested  (V2 router; ring-only)
    -> _derive_latency_payload             (SOURCE_TRUST per envelope)
    -> submit_financial_memory_candidate
        -> build_candidate_financial_memory_record (CANDIDATE)
        -> MemoryWriteRequest(requested_status=CANDIDATE)
        -> submit_memory_write
            -> M1 audit MEMORY_RECORD_STATUS_CHANGED (permanent)
            -> ACCEPTED_CANDIDATE for (SOURCE_TRUST, DIRECT_OBSERVATION)
        -> store.add  (only on accept)
    [optional] FinancialRecallRequest (CORE-only, scoped to
                                       SOURCE_TRUST + PROCEDURAL)
        -> select_financial_recall_top_one
            -> store.query_recallable -> v0.1 select_top_one
        -> if selected:
              emit_recall_request -> RECALL_REQUEST_EMITTED audit
              build_financial_recall_event  -> RecallEvent
          else:
              emit_recall_result_empty -> RECALL_RESULT_EMPTY audit
```

End-to-end smoke (3 synthetic envelopes via
SyntheticMarketAdapter):

```
observations_seen          3
candidate_records_written  3   (LatencyPatternPayload -> SOURCE_TRUST
                                accepted by MWG)
records_rejected           0
recall_requests            1
recall_events_built        1
hash_chain_valid           True
store size                 3
output summary             "V3 financial memory pipeline:
                            observations=3 candidates_written=3
                            rejected=0 recalls=1 recall_events=1;
                            observe-only, no action"
```

---

## 8. Safety invariants verified

```
SAF-01  No new SubjectClass enum value                    PASS
SAF-02  foreign_instance_origin NOT used as subject_class PASS
SAF-03  No verified M2 production by default              PASS
SAF-04  Candidate recall restricted to source_trust +
        procedural                                         PASS
SAF-05  Quarantined / rejected / expired recall blocked   PASS
SAF-06  Human / LLM recall bypass blocked                 PASS
        (FinancialRecallRequest source must be CORE;
         HUMAN_DIRECT / LLM / REPLAY / SUMMARIZER rejected
         at __post_init__)
SAF-07  No exchange SDK imports under sentinel/           PASS
SAF-08  No LLM SDK imports under sentinel/                PASS
SAF-09  No network library imports under sentinel/        PASS
SAF-10  No live execution path                            PASS
SAF-11  No raw symbol/venue leakage into RecallEvent /
        NeuralSeed                                         PASS
        (v0.1 RecallEvent extra='forbid' + V3 build
         test_no_raw_symbol_fields)
SAF-12  dry_sim canonical output unchanged                PASS
        (SystemOutput.WAIT, audit=4, permanent=2, ring=0)
SAF-13  Financial recall output is RecallEvent only       PASS
        (no ApprovedActionIntent / no execution verb
         produced; asserted by source-grep test
         test_no_approved_action_intent_in_source +
         test_no_deontic_action_path_invoked)
SAF-14  Hash chain verifies after pipeline                PASS
SAF-15  OBSERVATION_INGESTED stays ring-only              PASS
        (asserted by ledger content grep — never appears
         in JSONL)
SAF-16  WORKSPACE_PULSE not touched by V3                 PASS
        (V3 pipeline does NOT emit WORKSPACE_PULSE; it
         stops at the recall-event boundary and leaves
         compile-to-NeuralSeed / pulse to the caller)
SAF-17  No new ObserverEvent catalog row                  PASS
        (catalog unchanged in V3)
SAF-18  v0.1 877 + V2 87 tests still passing               PASS
SAF-19  Forbidden imports grep clean (incl. network libs) PASS
SAF-20  Forbidden outputs grep clean                       PASS
SAF-21  Public API drift: v0.1 + V2 baseline intact       PASS
        (no v0.1 / V2 symbol removed; V3 additions are
         additive)
```

21/21 GREEN.

---

## 9. What is deliberately deferred

```
- V4: Replay / counterfactual engine
- V5: Gel.Al shadow integration (live one-way bridge)
- V6+: Constitutional amendment for Sentinel -> execution
- Production verified memory (requires MWG matrix change)
- Persistent durable M2 store (multi-process / replicated)
- Memory subject_class taxonomy extension
- LLM-mediated recall
- Real exchange SDK / network market feed
- New ObserverEvent catalog rows for finance audit
- CI workflow grep tightening for requests/httpx/aiohttp at
  workflow level (V3 asserts per-module via source tests)
```

None of these are started in V3.

---

## 10. Final report (per /goal Step 17)

```
V3 — Financial M2 Memory + Recall

Status:
- GREEN

Commits:
- (see git log on branch claude/add-conversation-main-FvHvl)

Files changed (V3 portion):
- sentinel/memory/__init__.py                  (new)
- sentinel/memory/financial.py                 (new)
- sentinel/memory/builder.py                   (new)
- sentinel/memory/store.py                     (new)
- sentinel/memory/write_path.py                (new)
- sentinel/recall/financial.py                 (new)
- sentinel/runtime/financial_memory_pipeline.py (new)
- sentinel/__init__.py                          (modified)
- tests/memory/__init__.py                     (new)
- tests/memory/test_financial_payloads.py      (new)
- tests/memory/test_builder_and_store.py       (new)
- tests/memory/test_write_path.py              (new)
- tests/recall/test_financial.py               (new)
- tests/runtime/test_financial_memory_pipeline.py (new)
- tests/test_public_api.py                     (modified)
- docs/build/0004-v3-financial-m2-memory-recall-build-plan.md (new)
- docs/reviews/0015-v3-financial-m2-memory-recall-review.md   (this file)

New modules:
- sentinel/memory/financial.py
- sentinel/memory/builder.py
- sentinel/memory/store.py
- sentinel/memory/write_path.py
- sentinel/recall/financial.py
- sentinel/runtime/financial_memory_pipeline.py

Fixtures:
- (deferred — in-memory tests cover every scenario the proposed
   on-disk JSONL fixture suite would have)

Tests:
- total test count     : 1059 (was 964; +95)
- new tests count      : 94 V3 + 1 V3 public-API drift test
- pyright status       : 0 errors / 0 warnings / 0 informations
- ruff status          : clean (149 files formatted)
- forbidden imports    : clean (incl. requests/httpx/aiohttp)
- forbidden outputs    : clean

Safety:
- new subject_class                          : none
- foreign_instance_origin misuse             : none
- verified production                        : none
- candidate recall restriction               : enforced
- quarantined/rejected/expired recall        : blocked
- human/LLM recall bypass                    : blocked
- exchange imports                           : none
- network I/O                                : none
- LLM imports                                : none
- live execution path                        : none
- raw symbol/venue leakage into RecallEvent  : none
- dry_sim output                             : closed set
                                                (WAIT canonical
                                                 unchanged)
- financial recall output                    : RecallEvent only
- hash chain                                 : verifies

Version decision:
- V3 complete. Next version: V4 — Replay / Counterfactual.
```

---

## 11. Constraints honored

```
[+] No live trading
[+] No execution path
[+] No real exchange adapter
[+] No exchange SDK import
[+] No LLM SDK import
[+] No network library import under sentinel/
[+] No execution verbs in source
[+] No forbidden grep relaxation
[+] No CI workflow change
[+] No deontic gate weakening
[+] No Memory Write Gate weakening
[+] No recall protocol weakening
[+] No bypass of route_observer_event
[+] No promotion of ring_buffer_only events
[+] No new ObserverEvent catalog row
[+] No new SubjectClass value
[+] No verified memory production by default
[+] No tag rewrite / release overwrite
[+] No failure hidden in documentation
[+] No claim of production memory / live financial memory
    / trade recommendation
```

---

## 12. Final hüküm

```
V3 — Financial M2 Memory + Recall is complete.
Sentinel can take read-only market observations, derive
financial payloads, submit them through the silent Memory
Write Gate, accept SOURCE_TRUST + PROCEDURAL candidates into
the local M2 store, and surface a single top-1 record via
core-originated recall as a v0.1 RecallEvent — capped to
candidate intensity for candidate records, free of any raw
symbol / venue / order-side field.

Sentinel remembers safely.
Sentinel does NOT act.
```
