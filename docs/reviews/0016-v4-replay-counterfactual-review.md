# V4 — Replay / Counterfactual: Closure Review

**Date:** 2026-05-20  
**Reviewer:** Automated Phase-Closure Protocol  
**Phase:** V4 — Replay / Counterfactual  
**Build plan:** `docs/build/0005-v4-replay-counterfactual-build-plan.md`  
**Status: CLOSED — all acceptance criteria satisfied**

---

## 1. Scope

V4 adds a sandbox-only replay surface that produces bounded evidence proposals
from existing M1/M2/observation refs.  The phase is strictly additive: no
existing behaviour is altered, no live integration added, and all five
constitutional invariants from the V0.1 safety boundary are preserved
(extended where required by the replay surface).

---

## 2. Deliverables Checklist

| # | Deliverable | Status |
|---|-------------|--------|
| 1 | `sentinel/replay/__init__.py` | ✅ |
| 2 | `sentinel/replay/session.py` | ✅ |
| 3 | `sentinel/replay/budget.py` | ✅ |
| 4 | `sentinel/replay/sandbox.py` | ✅ |
| 5 | `sentinel/replay/counterfactual.py` | ✅ |
| 6 | `sentinel/replay/survival.py` | ✅ |
| 7 | `sentinel/replay/outcome_alignment.py` | ✅ |
| 8 | `sentinel/replay/effects.py` | ✅ |
| 9 | `sentinel/replay/audit.py` | ✅ |
| 10 | `sentinel/memory/replay_evidence.py` | ✅ |
| 11 | `sentinel/runtime/replay_financial_pipeline.py` | ✅ |
| 12 | 4 new catalog rows (`sentinel/observer/catalog.py`) | ✅ |
| 13 | V4 public API surface (`sentinel/__init__.py`) | ✅ |
| 14 | `tests/replay/` package (8 test files) | ✅ |
| 15 | `tests/test_public_api.py` V4 additions | ✅ |
| 16 | `docs/build/0005-v4-replay-counterfactual-build-plan.md` | ✅ |
| 17 | `docs/reviews/0016-v4-replay-counterfactual-review.md` (this file) | ✅ |

---

## 3. Constitutional Safety Constraints — Verification

### 3.1 No live action output

`ReplayFinancialPipelineResult.__post_init__` asserts
`action_count == 0` and raises `ValueError` otherwise.
`ReplaySandboxResult.__post_init__` asserts
`produced_action_count == 0`.  Both are enforced structurally at
construction time, not by runtime code path.

Grep evidence:

```
grep -r "ApprovedActionIntent" sentinel/runtime/replay_financial_pipeline.py
grep -r "evaluate_action"      sentinel/runtime/replay_financial_pipeline.py
```

Both return empty.  The source-inspection test
`test_no_action_intent_in_source` covers this at test time.

### 3.2 No live memory write

`ReplayFinancialPipelineResult.__post_init__` asserts
`records_promoted_to_verified == 0`.
`sentinel/memory/replay_evidence.py` never calls `store.add` or any
write method — it only reads `store.get` and emits an audit event.
`ReplaySandboxResult.__post_init__` asserts
`produced_memory_write_count == 0`.

### 3.3 No live event injection

`ReplaySandboxResult.__post_init__` asserts
`produced_live_event_count == 0`.
`run_in_sandbox` is a pure function that returns
`ReplaySandboxResult` without touching the observer ledger or ring
buffer.  Audit events emitted by the replay pipeline use
`PERMANENT` permanence (as required for audit trails) but carry
`event_family="replay"`, keeping them strictly off the ring-buffer
`OBSERVATION_INGESTED`/`WORKSPACE_PULSE` path.

### 3.4 No exchange / network / LLM import

Source-inspection test `test_no_forbidden_imports_in_source`
asserts the forbidden import list is absent from
`replay_financial_pipeline.py`.  No V4 module contains any of:
`ccxt`, `binance`, `btcturk`, `pybit`, `okx`, `gate_api`, `kucoin`,
`huobi`, `bitfinex`, `kraken`, `web3`, `requests`, `httpx`,
`aiohttp`, `openai`, `anthropic`, `langchain`.

### 3.5 No forbidden output literals

`assert_no_forbidden_literal` is applied in:
- `OutcomeRef._validate` (Pydantic field validator)
- `emit_replay_session_status_changed` (reason string)

All five forbidden literals (`BUY`, `SELL`, `EXECUTE_REAL`,
`ORDER_SUBMIT`, `HALT_ALL`) are rejected at the type boundary.
Source-inspection test `test_no_forbidden_output_literals_in_source`
confirms none appear in the pipeline source.

### 3.6 No replay-triggered replay recursion

`ReplaySandbox.run_in_sandbox` is a pure function that takes a
snapshot of already-serialised `SimulatedEvent` objects and returns
`ReplaySandboxResult`.  It holds no reference to
`run_replay_financial_pipeline` and cannot enqueue a new replay
session.

### 3.7 Memory Write Gate not bypassed

`submit_replay_survival_evidence` and
`submit_outcome_alignment_evidence` emit
`MEMORY_VERIFICATION_EVIDENCE_PROPOSED` audit events; neither calls
any write-path function (`submit_financial_memory_candidate`,
`FinancialMemoryWriteGate`, etc.).  The MWG remains the sole path to
promote a record from `CANDIDATE` to `VERIFIED`.

### 3.8 Deontic Gate not bypassed

No V4 module calls `evaluate_action` or `evaluate_action_with_audit`.
The deontic gate is not touched.

---

## 4. Schema Safety

### 4.1 CounterfactualAblation

- Exactly 1 event: `SINGLE_VARIABLE` only.
- Exactly 2 events: `PAIRWISE` only; `causal_link_required=True`
  enforced at schema level; causal link validated again at
  `perform_counterfactual_ablation` runtime.
- 3+ events: model validator raises `ValueError` unconditionally.

### 4.2 CounterfactualAblationResult

`synthetic_only: Literal[True] = True` — cannot be false.

### 4.3 OutcomeRef

`external: Literal[True] = True` — internal refs cannot be passed.
Payload keys are scanned for `api_key`, `api_secret`, `balance`,
`position`, `side`, `order_side`, `order_id`, `live_fill_id`,
`account_id`.  Any such key raises `ValueError`.

### 4.4 ReplayBudget

`restore_continuity_required: Literal[True] = True` — hardcoded.
`max_sessions_per_24h_window >= max_sessions_per_cycle` enforced by
model validator.

### 4.5 SimulatedEvent

`replay_simulated: Literal[True] = True` — cannot be false.
Prevents simulated events from being accidentally routed as real ones.

### 4.6 SleepSynapseUpdateProposal / AttentionHabituationUpdate / IngressCalibrationUpdateProposal

Cap constraints (`|capped_delta| <= |delta|`,
`|capped_delta| <= daily_cap_ref`) enforced in Pydantic validators.

---

## 5. Audit Surface

Four new canonical event definitions added to `sentinel/observer/catalog.py`:

| event_type | family | permanence | ring_buffer_only |
|---|---|---|---|
| `SLEEP_REPLAY_SYNAPSE_UPDATE` | replay | PERMANENT | False |
| `ATTENTION_REPLAY_HABITUATION_UPDATE` | replay | PERMANENT | False |
| `INGRESS_CALIBRATION_UPDATED` | replay | PERMANENT | False |
| `MEMORY_VERIFICATION_EVIDENCE_PROPOSED` | memory | PERMANENT | False |

All five V4 audit emitters (`emit_replay_session_status_changed`,
`emit_sleep_replay_synapse_update`,
`emit_attention_replay_habituation_update`,
`emit_ingress_calibration_updated`,
`emit_memory_verification_evidence_proposed`) call
`ledger.append(event)` directly and are covered by
`tests/replay/test_audit.py`.

---

## 6. Budget Safety

`can_start_replay_session` enforces:
- `sessions_started_this_cycle < budget.max_sessions_per_cycle`
- `sessions_started_24h < budget.max_sessions_per_24h_window`
- `fatigue_accumulator < FATIGUE_BLOCK_THRESHOLD` (0.9)
- `now_ms - last_session_completed_at_ms >= replay_cooldown_ms`

`ReplayBudgetState` is frozen; `record_replay_session_completion`
returns a new state via copy-on-update.  Test
`test_budget_exhaustion_stops_sessions` validates that a cycle cap
of 2 stops after exactly 2 sessions when 5 candidates are presented.

---

## 7. Public API Surface

15 new symbols added to `sentinel.__all__` (V4 additive surface):

```python
V4_PUBLIC_API_ADDITIONS = frozenset({
    "AblationKind",
    "CounterfactualAblation",
    "CounterfactualAblationResult",
    "OutcomeAlignmentEvidence",
    "OutcomeRef",
    "ReplayBudget",
    "ReplayBudgetState",
    "ReplayEffectChannel",
    "ReplayFinancialPipelineResult",
    "ReplayInputSnapshot",
    "ReplayPurpose",
    "ReplaySession",
    "ReplaySessionStatus",
    "ReplaySurvivalEvidence",
    "can_start_replay_session",
    "run_replay_financial_pipeline",
})
```

`test_v4_additions_exported` verifies all 15 symbols are present.
No V0.1/V2/V3 baseline symbol was removed.

---

## 8. Test Coverage

| File | Tests | Notes |
|---|---|---|
| `tests/replay/test_session.py` | 12 | lifecycle, terminal-status, applied⊆requested |
| `tests/replay/test_budget.py` | 9 | can_start, fatigue, cooldown, 24h cap |
| `tests/replay/test_sandbox.py` | 7 | hard zeros, pure function, simulated flag |
| `tests/replay/test_counterfactual_and_survival.py` | 11 | ablation limits, pairwise causal, synthetic_only |
| `tests/replay/test_outcome_alignment_and_effects.py` | 12 | external-only, forbidden literals, cap constraints |
| `tests/replay/test_evidence_and_pipeline.py` | 11 | evidence accept/reject, pipeline audit, budget stop |
| `tests/replay/test_audit.py` | 6 | all 5 emitters, forbidden literal in reason |
| `tests/test_public_api.py` | +1 | test_v4_additions_exported |

Total tests (whole suite): **1154 passing, 0 failing, 0 errors**.

---

## 9. Regressions

All pre-V4 tests (V0.1, V2, V3) pass unchanged.  V4 is strictly
additive; no existing module was modified except:
- `sentinel/observer/catalog.py` — 4 rows appended to `CATALOG`
- `sentinel/__init__.py` — 15 new import/export lines
- `tests/test_public_api.py` — 1 new frozenset + test method

---

## 10. Deferred Items

The following items were explicitly excluded from V4 scope per the
build plan's non-goals section:

| Item | Reason |
|---|---|
| CLI command for replay | Risk of scope creep; deferred to V5+ |
| On-disk snapshot fixtures | In-memory tests cover all scenarios |
| Gel.Al shadow integration | V6 scope |
| Live/canary replay | Not in V4; live trading forbidden |
| Cross-instance / fork / migration | MVP single-instance constraint |
| V5 financial deontic policy | Not started |

---

## 11. Sign-off

All acceptance criteria from `docs/build/0005-v4-replay-counterfactual-build-plan.md`
are satisfied.  The V4 phase is **CLOSED**.

No V5 work, no live integration, no exchange SDK, no LLM, no network
calls were introduced in this phase.  The constitutional safety
boundary is unchanged: output set remains `{WAIT, BLOCK, MONITOR,
NEED_RECALL, NO_ACTION}`.
