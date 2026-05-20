# 0006 — V5 — Gel.Al Shadow Integration — Build Plan

> Status: BUILD PLAN. Implementation tracks this document section-by-section.

## 1. Purpose

V5 wires Sentinel as a **one-way, read-only shadow observer** of the
Gel.Al Borsa execution system.  Gel.Al exports its own market /
opportunity / risk / health / kill-switch events as JSONL records;
Sentinel reads those records, sanitizes them into the v0.1
`ObservationEvent` core surface, runs the existing v0.1 pipeline
(ingress compiler → WorkspacePulseEvent → recall / memory / replay
hooks) and produces a `SystemOutput` value drawn from the closed v0.1
set `{WAIT, BLOCK, MONITOR, NEED_RECALL, NO_ACTION}`.

Gel.Al does not consume Sentinel output in V5.  No Sentinel → Gel.Al
channel exists.

## 2. Non-goals

- No live trading.
- No execution.
- No live exchange connection.
- No write to Gel.Al Redis (`orders.pending`, `kill_switch`, config).
- No write to Gel.Al production DB.
- No exchange API keys inside Sentinel.
- No LLM integration.
- No paper co-pilot.
- No canary live veto.
- No financial deontic activation yet.
- No strategy threshold mutation.
- No direct human Telegram control.
- No Gel.Al state mutation of any kind.

## 3. Safety constraints

- All v0.1 / V2 / V3 / V4 constitutional invariants preserved.
- Output set still `{WAIT, BLOCK, MONITOR, NEED_RECALL, NO_ACTION}`.
- No `BUY` / `SELL` / `EXECUTE_REAL` / `ORDER_SUBMIT` outputs.
- No `ApprovedActionIntent` produced from Gel.Al envelopes.
- No exchange / network / LLM imports under `sentinel/`.
- No mutation of Gel.Al state.
- `OBSERVATION_INGESTED` / `WORKSPACE_PULSE` remain `ring_buffer_only`.
- Memory Write Gate and Recall Protocol not bypassed.
- The Sentinel → Gel.Al action channel **does not exist**: no
  function, no method, no helper writes anywhere outside the
  Sentinel ledger and ring buffer.

## 4. Gel.Al remains the execution system

Gel.Al keeps the API credentials, the exchange SDKs, the order
placement code, the position state, and the kill-switch surface.
Sentinel does not move any of these into its codebase.

## 5. Sentinel remains observer / brain / audit

Sentinel keeps the ledger, deontic gate, memory gate, recall
protocol, M1 hash chain, observer router, and dry-sim runtime.  The
V5 surface adds only new schemas and a sanitizer.

## 6. One-way bridge principle

```
Gel.Al → JSONL file → Sentinel
Sentinel → ⊥   (no channel)
```

Sentinel writes only to its own ledger and ring buffer.  The
Sentinel codebase contains **no** import that targets Gel.Al's DB,
Redis, or HTTP surface.

## 7. Shadow event families

`GelAlShadowEventType` is a closed observer-side enum (9 values):

- `market_observation`
- `opportunity_seen`
- `opportunity_blocked`
- `risk_gate_decision`
- `execution_attempt_observed`
- `paper_result_observed`
- `live_result_observed`
- `system_health_observed`
- `kill_switch_observed`

These are observer-side event types only.  They do not create new
Sentinel ingress event profiles and do not extend the core observer
catalog.

## 8. Local JSONL export contract

Gel.Al writes line-delimited JSON encoding of `GelAlShadowEnvelope`
records to a local file.  Sentinel reads via
`GelAlShadowJsonlAdapter`.  The adapter is read-only with respect
to the filesystem and has no `write` method.

## 9. Read-only fixture / import adapter

`GelAlShadowJsonlAdapter` is a frozen dataclass holding a `Path`.
Methods: `read_all() -> tuple[GelAlShadowEnvelope, ...]` and
`iter_events() -> Iterator[GelAlShadowEnvelope]`.  No daemon, no
network, no DB, no Redis.

## 10. Gel.Al event provenance

The envelope carries:

- `event_id`, `event_type`, `source_system="gel_al_borsa"`
- `source_table`, `source_row_id`, `source_hash`
- `environment ∈ {local, paper, shadow, canary, live}`
- `observed_at_ms`, `exported_at_ms` (exported >= observed)
- optional `strategy_name`, `symbol`, `venue`
- `payload: dict[str, object]` non-empty, forbidden keys blocked

## 11. Core-facing ObservationEvent sanitization

`sanitize_gelal_shadow_to_observation_event(envelope, ...)` produces
a v0.1 `ObservationEvent`.  The function strips all domain labels
(`symbol`, `venue`, `strategy_name`, `opportunity_id`, `order_sent`,
`bad_order`, `decision`, `block_reason`, raw payload).  Only the
following normalized fields cross into core:

- `event_id`, `occurred_at_ms`, `ttl_ms`, `confidence`
- `source_adapter_id` (constant `gelal-shadow`)
- `source_reliability_band` (caller default 3)
- `magnitude_normalized` (deterministic function of payload signals)
- `novelty_indicator` (deterministic function of event-type rarity)
- `staleness_ms` (export − observed + payload latency hints)

## 12. Financial memory integration

V3 memory store is consumed read-only by the evaluator when a
relevant trigger occurs.  No write path is added.  V3 candidate
records remain unaffected.

## 13. Replay / counterfactual integration

V4 replay survival / outcome alignment evidence may be consulted
read-only by the evaluator if available.  V5 does not generate new
replay sessions or counterfactual ablations.

## 14. Shadow evaluation result

`GelAlShadowEvaluationResult` is a frozen dataclass with: `event_id`,
`source_event_type`, `sentinel_output`, `reason`, `observation_event_id`,
`neural_seed_total_intensity`, `pulse_created`, `recall_requested`,
`memory_candidate_created`, `replay_evidence_used`, `audit_event_ids`,
`permanent_event_ids`, `ring_buffer_event_ids`, `hash_chain_valid`.

`sentinel_output` must be drawn from the closed v0.1 set.  The
runtime never constructs `ApprovedActionIntent`.

## 15. Observer routing / permanence

`emit_gelal_shadow_observation_ingested` builds an
`OBSERVATION_INGESTED` `ObserverEvent` and dispatches via
`route_observer_event`.  Per catalog policy this lands ring-only and
is dropped if no ring buffer is supplied.  V5 introduces no new
catalog rows.

## 16. CLI / local runner

`python -m sentinel.runtime.gelal_shadow --fixture <path> --ledger <path>`
loads a fixture, evaluates each envelope, and reports the aggregated
result.  Exit codes: 0 (OK), 1 (load/schema error), 2 (hash chain
invalid).

## 17. Tests and invariants

8 test files (schema, JSONL adapter, sanitizer, audit, manifest,
evaluator, runner, safety greps).  All 46 invariants from §11 of the
goal spec covered.

## 18. Forbidden surfaces

| # | Forbidden | Enforcement |
|---|---|---|
| 1 | exchange SDK imports | source grep test |
| 2 | network library imports | source grep test |
| 3 | LLM imports | source grep test |
| 4 | forbidden output literals | `assert_no_forbidden_literal` |
| 5 | API key fields | envelope `extra=forbid` + key denylist |
| 6 | execution command fields | envelope `extra=forbid` + key denylist |
| 7 | symbol/venue/strategy in `ObservationEvent` | v0.1 schema |
| 8 | Sentinel → Gel.Al write | no helper exists in source |

## 19. Done definition

- 9-value `GelAlShadowEventType` enum implemented.
- `GelAlShadowEnvelope` schema with key denylist + cross-validators.
- `GelAlShadowJsonlAdapter` read-only adapter.
- `sanitize_gelal_shadow_to_observation_event` pure function.
- `build_gelal_shadow_audit_payload` pure function preserving
  observer-side provenance.
- `build_gelal_shadow_manifest` observe-only manifest.
- `emit_gelal_shadow_observation_ingested` router-only helper.
- `evaluate_gelal_shadow_event` pipeline producing closed output.
- `run_gelal_shadow_file` batch runner + optional CLI.
- 8 fixtures (6 valid scenarios + 2 invalid).
- Full sweep GREEN (ruff, pyright, pytest, forbidden grep).
- V5 closure review GREEN.

## 20. Deferred V6+ items

- V6: Financial deontic policy activation.
- V7: Paper co-pilot.
- V8: Canary micro-live veto layer.
- Real Gel.Al DB / Redis read adapter.
- Live exchange adapter.
- LLM integration.
- Telegram control plane.

---

## Pipeline diagram

```
GelAlShadowEnvelope (observer-side)
  ─► build_gelal_shadow_audit_payload
       ─► OBSERVATION_INGESTED ObserverEvent
            ─► route_observer_event  (ring_buffer_only)
  ─► sanitize_gelal_shadow_to_observation_event
       ─► ObservationEvent  (no symbol/venue/strategy)
            ─► compile_neural_seed
                 ─► NeuralSeed
                      ─► WorkspacePulseEvent
                           ─► WORKSPACE_PULSE  (ring_buffer_only)
                                ─► SystemOutput ∈ {WAIT, BLOCK, MONITOR, NEED_RECALL, NO_ACTION}
```

No branch of this pipeline ever produces an `ApprovedActionIntent`,
a write to Gel.Al, or a string containing a forbidden output literal.
