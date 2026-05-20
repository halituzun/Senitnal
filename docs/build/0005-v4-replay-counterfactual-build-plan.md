# 0005 — V4 Replay / Counterfactual Build Plan

> Successor to `docs/build/0004-v3-financial-m2-memory-recall-build-plan.md`.
>
> V4 adds a sandbox-only replay surface that produces bounded
> evidence proposals from existing M1 / M2 / observation refs.
> Replay CANNOT push events into the live core, CANNOT write M2
> directly, CANNOT generate any action output, and CANNOT confuse
> counterfactual results with real outcome alignment.

---

## 1. Purpose

Give Sentinel the ability to evaluate its past in a bounded sandbox:

```
- Replay session lifecycle with budget caps
- Sandbox isolation (live event count, action count, memory
  write count all HARD-ZERO)
- Counterfactual ablation (single + pairwise; pairwise requires
  causal link; >= 3 forbidden)
- Replay survival score (deterministic; synthetic-only)
- Outcome alignment analysis (requires EXTERNAL recorded outcome
  refs; counterfactual results cannot become outcome refs)
- Effect-channel proposal schemas (sleep synapse, attention
  habituation, ingress calibration, memory verification evidence)
- M1 audit emitters for the four new REPLAY catalog rows
- MWG integration that PROPOSES evidence; the v0.1 Memory Write
  Gate remains the only path that can change verified status
- Financial-memory pipeline that exercises replay over V3
  candidate records
```

---

## 2. Non-goals

```
- No live trading, no execution, no live exchange API
- No real exchange SDK imports (ccxt / binance / btcturk / ...)
- No LLM imports (openai / anthropic / langchain)
- No network library imports (requests / httpx / aiohttp / urllib3 /
  socket / asyncio.subprocess) under sentinel/
- No Gel.Al live bridge
- No production verified memory promotion in V4
- No direct M2 write from replay
- No direct core ingress from replay
- No ApprovedActionIntent generation from replay
- No recursive replay (replay-can-trigger-replay chain depth is
  not a configurable field)
- No production numerics update from replay
- No outcome alignment derived from counterfactual results
- No symbol/venue leakage into replay audit reason strings
- No new SubjectClass value
- No promotion of OBSERVATION_INGESTED / WORKSPACE_PULSE to
  permanent JSONL
```

---

## 3. Safety constraints

All v0.1 + V2 + V3 constitutional red lines remain in force. The
CI grep set is a strict superset of v0.1's. V4 source modules
assert per-module that no exchange / LLM / network library is
imported.

`ReplaySandboxResult` enforces three hard zeros at construction:
`produced_live_event_count == 0`, `produced_action_count == 0`,
`produced_memory_write_count == 0`. The result dataclass refuses
to even exist if any of these is non-zero.

`ReplayFinancialPipelineResult` enforces:
`records_promoted_to_verified == 0`,
`live_event_count == 0`,
`action_count == 0`.

`CounterfactualAblationResult.synthetic_only` is True by
construction.

`OutcomeRef.external` must be True; the model_validator rejects
internal-only outcomes.

`OutcomeRef.payload` cannot contain forbidden execution literals
(BUY / SELL / EXECUTE_REAL / ORDER_SUBMIT) or API-credential /
order-side / account-state keys.

`MemoryRecord` written through `submit_replay_*_evidence` is
NEVER mutated; the wrappers only emit an audit event.

---

## 4. Replay is not re-living

```
Replay does NOT re-emit live ObservationEvent into the core.
Replay does NOT call route_observer_event with a simulated event.
Replay does NOT call ingress compiler as a live path.
Replay does NOT push WorkspacePulseEvent into the live workspace.
Replay does NOT call the deontic gate to evaluate a synthetic
ApprovedActionIntent (none is constructed in V4).
Replay does NOT write M2.
Replay does NOT touch production numerics.
Replay produces only:
    - audit events under REPLAY family
    - proposal schemas (returned to caller; not state mutators)
    - evidence schemas (also returned; the gate may consume them
      in a future release behind an explicit constitutional
      amendment, not in V4)
```

---

## 5. Single replay engine, multiple effect channels

`ReplayPurpose` enumerates the canonical purposes:

```
sleep_synapse_update
attention_habituation
ingress_calibration
memory_verification
outcome_alignment_analysis
counterfactual_ablation
financial_memory_review
```

`ReplayEffectChannel` enumerates the channels a session may
request and apply:

```
sleep_synapse_update
attention_habituation_update
ingress_calibration_update
memory_verification_evidence
outcome_alignment_analysis
audit_only
```

`ReplaySession.effect_channels_applied` MUST be a subset of
`effect_channels_requested` (enforced by model_validator).

---

## 6. Replay session lifecycle

```
pending -> running -> { completed | aborted | budget_exhausted | failed }
```

Terminal statuses require `completed_at_ms` to be set and >=
`started_at_ms` (enforced by model_validator).

Each lifecycle transition is audited via
`REPLAY_SESSION_STATUS_CHANGED` (existing catalog row;
permanence=permanent).

---

## 7. Replay input snapshots

`ReplayInputSnapshot` bundles the refs the session is allowed to
consume:

```
source_m1_event_ids
source_memory_record_ids
source_observation_event_ids
source_outcome_refs
provenance_ref
hash_ref
```

At least one ref-tuple must be non-empty. Every ref string must
be non-empty. No raw symbol / venue is carried directly.

---

## 8. Replay budget

`ReplayBudget` is a frozen dataclass with caps:

```
max_sessions_per_cycle              > 0
max_sessions_per_24h_window         > 0 and >= max_sessions_per_cycle
max_events_per_session              > 0
max_counterfactual_branches         >= 0
max_session_duration_ms             > 0
replay_cooldown_ms                  >= 0
replay_fatigue_accum_rate           in [0, 1]
restore_continuity_required         MUST be True (V4 hardcode)
```

Notably absent: any `replay_can_trigger_replay_max_chain_depth`
field — V4 is non-recursive by construction.

`ReplayBudgetState` carries the runtime counters; mutation is
copy-on-update via `record_replay_session_completion`. Restore
is required to preserve the state (`restore_continuity_required`
is checked at construction).

`can_start_replay_session` returns False on any of:
  - sessions_used_this_cycle >= max_sessions_per_cycle
  - sessions_used_24h >= max_sessions_per_24h_window
  - elapsed since last completion < replay_cooldown_ms
  - replay_fatigue >= 0.9

---

## 9. Counterfactual ablation

`AblationKind`:
  - `single_variable` — removes exactly 1 event
  - `pairwise` — removes exactly 2 events AND requires
    `causal_link_required=True`

Higher-order (>= 3) ablation is rejected at schema layer.

`validate_pairwise_causal_link` accepts a pair iff:
  - A's causal_refs contain B, OR
  - B's causal_refs contain A, OR
  - A and B share at least one common parent in causal_refs

`perform_counterfactual_ablation`:
  - validates pairwise causal link at runtime
  - computes a bounded survival_score = ratio of ablated /
    base pattern intensity, clipped to [0, 1]
  - returns a `CounterfactualAblationResult` with
    `synthetic_only=True`

The result CANNOT become an `OutcomeRef`. Outcome alignment is
external-only by design.

---

## 10. Replay survival score

`compute_replay_survival_score(results)`:
  - empty -> 0.0
  - else confidence-weighted mean of per-ablation survival scores
  - bounded [0, 1]
  - deterministic

`ReplaySurvivalEvidence` requires `synthetic_only=True` and at
least one ablation_id. `min_sessions_satisfied=False` means the
evidence can be constructed but is NOT usable for the gate
wrapper.

---

## 11. Outcome alignment analysis

`OutcomeRef`:
  - `external` MUST be True (internal-only rejected)
  - payload non-empty
  - no forbidden execution literal in payload string values
    (assert_no_forbidden_literal wrapped as ValueError so
    Pydantic emits a ValidationError at the boundary)
  - no api_key / api_secret / balance / position / side /
    order_side / order_id / live_fill_id / account_id key

`OutcomeAlignmentEvidence`:
  - `outcome_refs` non-empty
  - every ref.external must be True
  - `stale=True` means the evidence can be constructed but is
    NOT usable for the gate wrapper

`compute_outcome_alignment_score`:
  - deterministic
  - confidence-weighted average of ref confidence, damped by
    record confidence
  - bounded [0, 1]

---

## 12. Effect channels (M0 / attention / ingress)

```
SleepSynapseUpdateProposal
    bounded delta + capped_delta + eligibility_trace_id +
    evidence_ref. Refuses |capped| > |delta|.

AttentionHabituationUpdate
    bounded habituation_delta + capped_delta. NO synapse_id /
    topology field (extra='forbid' rejects).

IngressCalibrationUpdateProposal
    bounded delta + capped_delta + daily_cap_ref. NO new
    payload_type field. Refuses |capped| > daily_cap_ref or
    |capped| > |delta|.

MemoryVerificationEvidenceProposal
    usable_for_gate flag based on:
        replay_survival   -> min_sessions_satisfied
        outcome_alignment -> external + not stale
    This is NOT a write; the v0.1 MWG remains the only write
    path.
```

---

## 13. Memory verification evidence channel

`submit_replay_survival_evidence` and
`submit_outcome_alignment_evidence` (in
`sentinel/memory/replay_evidence.py`):

  - reject rejected / quarantined / expired records
  - reject unusable evidence
  - emit `MEMORY_VERIFICATION_EVIDENCE_PROPOSED` audit ONLY when
    accepted
  - NEVER mutate the record or the store
  - return an `AttachReplayEvidenceResult` for caller inspection
  - do NOT call submit_memory_write — the gate-driven verification
    path is reserved for a future release that explicitly amends
    the MWG matrix

---

## 14. Observer audit events (catalog additions)

Four new canonical event types added to
`sentinel/observer/catalog.py`:

```
SLEEP_REPLAY_SYNAPSE_UPDATE              REPLAY  permanent
ATTENTION_REPLAY_HABITUATION_UPDATE      REPLAY  permanent
INGRESS_CALIBRATION_UPDATED              REPLAY  permanent
MEMORY_VERIFICATION_EVIDENCE_PROPOSED    MEMORY  permanent
```

`REPLAY_SESSION_STATUS_CHANGED` was already in the catalog
(v0.1). The audit emitters in `sentinel/replay/audit.py` write
to the JSONL ledger via `ledger.append(...)`.

---

## 15. Financial memory integration

`sentinel/runtime/replay_financial_pipeline.py` exposes:

```
ReplayFinancialPipelineResult                frozen dataclass
                                              with HARD ZEROs
run_replay_financial_pipeline(...) -> ReplayFinancialPipelineResult
```

Per V3 candidate record:
  - check `can_start_replay_session`
  - emit `REPLAY_SESSION_STATUS_CHANGED(status=running)`
  - construct a `CounterfactualAblation` and run a
    deterministic ablation result
  - compute `ReplaySurvivalEvidence`
    (`min_sessions_satisfied=False` in V4 by default —
    single-session reviews are never sufficient)
  - submit replay-survival evidence (audit only if usable)
  - optionally compute outcome alignment when external refs
    are supplied
  - emit `REPLAY_SESSION_STATUS_CHANGED(status=completed)`
  - update `ReplayBudgetState`

Pipeline does NOT change `MemoryRecord.status`; the v0.1 MWG
remains the only path that can.

---

## 16. Synthetic market integration

V4 inherits V2 synthetic / local-fixture market observation
adapters unchanged. The financial pipeline operates on
already-stored V3 candidates; no live market path is opened.

---

## 17. Restore / budget continuity

`ReplayBudget.restore_continuity_required` is hardcoded True in
V4. Restore must persist `ReplayBudgetState` so caps survive a
process restart; the budget cannot be reset by restore as a way
to dodge the 24h window.

---

## 18. Tests and invariants

```
tests/replay/test_session.py             ReplaySession lifecycle +
                                          snapshot validation
tests/replay/test_budget.py              budget caps + cooldown +
                                          fatigue + restore
                                          continuity + no chain-depth
                                          field
tests/replay/test_sandbox.py             hard zeros + simulated event
                                          validation
tests/replay/test_counterfactual_and_survival.py
                                          single/pairwise/triple +
                                          causal link + bounded
                                          survival + synthetic_only
tests/replay/test_outcome_alignment_and_effects.py
                                          external-only outcomes;
                                          forbidden literals
                                          rejected; effect schemas;
                                          attention without synapse
                                          topology; ingress without
                                          new payload type
tests/replay/test_audit.py               5 audit emitters; forbidden
                                          literal in reason rejected;
                                          family + event_type checks
tests/replay/test_evidence_and_pipeline.py
                                          MWG evidence wrappers +
                                          financial pipeline +
                                          hard zeros + budget
                                          exhaustion + no
                                          ApprovedActionIntent in
                                          source
```

Total V4: 88 new tests. Suite: 1059 (V3) → 1147 (V4 sources +
audit) → 1154 (V4 with audit tests).

---

## 19. Forbidden surfaces (V4 line-item)

```
- import ccxt / binance / btcturk / pybit / okx / gate_api /
  kucoin / huobi / bitfinex / kraken / web3 — FORBIDDEN
- import openai / anthropic / langchain — FORBIDDEN
- import requests / httpx / aiohttp / urllib3 / socket /
  asyncio.subprocess in V4 modules — FORBIDDEN
- API key / API secret field on any V4 schema — FORBIDDEN
- order side / quantity / amount field — FORBIDDEN
- account_id / balance / position / leverage — FORBIDDEN
- BUY / SELL / EXECUTE_REAL / ORDER_SUBMIT literal in source
  or audit payload — FORBIDDEN
- new SubjectClass value — FORBIDDEN
- direct M2 write from replay — FORBIDDEN
- direct core ingress from replay — FORBIDDEN
- ApprovedActionIntent construction in V4 modules — FORBIDDEN
- counterfactual result -> OutcomeRef — FORBIDDEN
- promotion of OBSERVATION_INGESTED / WORKSPACE_PULSE to
  permanent — FORBIDDEN
- replay-can-trigger-replay (recursion) — FORBIDDEN
- production numerics update from replay — FORBIDDEN
- verified MemoryRecord promotion from replay (V4) — FORBIDDEN
```

---

## 20. Done definition

```
[1]  ReplaySession lifecycle schema implemented
[2]  ReplayInputSnapshot schema implemented
[3]  ReplayBudget + ReplayBudgetState + budget guards
[4]  ReplaySandbox + ReplaySandboxResult with HARD ZEROs
[5]  CounterfactualAblation + perform_counterfactual_ablation
[6]  Single + pairwise; triple rejected; pairwise requires
     causal link
[7]  Replay survival score (bounded, deterministic,
     synthetic_only)
[8]  OutcomeRef (external-only) + OutcomeAlignmentEvidence
[9]  Counterfactual result CANNOT become OutcomeRef
[10] Effect channel proposals (sleep / attention / ingress /
     memory evidence) with caps
[11] 4 new catalog rows + 5 audit emitters
[12] MWG evidence wrappers (audit only, never mutate)
[13] run_replay_financial_pipeline with HARD ZEROs
[14] No live event from replay
[15] No action from replay
[16] No exchange / LLM / network imports
[17] Public API additions (16 symbols)
[18] tests/test_public_api drift test for V4
[19] V4 build plan (this file)
[20] V4 review (docs/reviews/0016)
[21] pyright strict 0 errors
[22] ruff check + format clean
[23] forbidden imports + outputs grep clean
[24] dry_sim canonical run unchanged
```

---

## 21. Deferred V5+ items

```
- V5: Gel.Al shadow integration (one-way live bridge)
- V6: Financial deontic policy
- V7+: Paper / canary / live
- Real outcome feed from Gel.Al or other external source
- Production memory verification path (would require MWG
  evidence-axis matrix amendment)
- Production replay scheduler (the V4 implementation is a
  caller-driven pipeline, not a daemon)
- CLI for offline replay (deferred; in-memory tests cover
  the same surface)
- New ObserverEvent catalog rows for additional replay sub-
  flows (V4 ships only the 4 required for the current
  effect channels)
```

None of these are started in V4.

---

## 22. Implementation status (post-build)

```
sentinel/replay/session.py                    SHIPPED
sentinel/replay/budget.py                     SHIPPED
sentinel/replay/sandbox.py                    SHIPPED
sentinel/replay/counterfactual.py             SHIPPED
sentinel/replay/survival.py                   SHIPPED
sentinel/replay/outcome_alignment.py          SHIPPED
sentinel/replay/effects.py                    SHIPPED
sentinel/replay/audit.py                      SHIPPED
sentinel/memory/replay_evidence.py            SHIPPED
sentinel/runtime/replay_financial_pipeline.py SHIPPED
sentinel/observer/catalog.py (4 new rows)     SHIPPED
sentinel/__init__.py (V4 public exports)      SHIPPED
tests/replay/* (5 test files, 88 tests)       SHIPPED
tests/test_public_api.py (V4 drift test)      SHIPPED
docs/build/0005 (this file)                   SHIPPED
docs/reviews/0016 (review)                    SHIPPED

DEFERRED (per §21 above):
    on-disk JSONL fixtures for replay
    CLI for offline replay
    production replay scheduler
    Gel.Al outcome feed integration
    MWG evidence-axis matrix amendment
```

---

## 23. Final hüküm

```
V4 ships replay / counterfactual as a sandbox-only,
proposal-only, audit-only surface. Replay cannot relive the
past. Replay cannot write memory. Replay cannot act. Replay
cannot confuse counterfactual outputs with real outcomes.
Sentinel can evaluate itself; Sentinel still cannot act.
```
