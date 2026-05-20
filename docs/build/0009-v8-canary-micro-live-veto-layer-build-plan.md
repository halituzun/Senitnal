# 0009 — V8 — Canary Micro-Live Veto Layer — Build Plan

> Status: BUILD PLAN. Implementation tracks this document section-by-section.

## 1. Purpose

V8 adds a **veto-only** safety layer that runs against Gel.Al's
micro-live canary candidate actions.  Sentinel may classify a
candidate as `veto` (BLOCK), `monitor_only` (MONITOR), or `no_veto`
(NO_ACTION / MONITOR).  Sentinel does **not** issue orders, sizes,
sides, or approvals.  Gel.Al's risk engine remains the final
execution authority and decides whether to honor a Sentinel veto.

## 2. Non-goals

- No live order placement by Sentinel.
- No trade approval.
- No Gel.Al DB / Redis / config write.
- No kill-switch mutation.
- No exchange API integration.
- No LLM integration.
- No full live mode.
- No live capital scaling.
- No limited live co-governance (V9).
- No strategy threshold mutation.
- No production policy auto-tuning.

## 3. Safety constraints

- All v0.1–V7 constitutional invariants preserved.
- Output set still `{WAIT, BLOCK, MONITOR, NEED_RECALL, NO_ACTION}`.
- No `BUY` / `SELL` / `EXECUTE_REAL` / `ORDER_SUBMIT` outputs.
- No `ApprovedActionIntent` produced.
- No exchange / network / LLM imports under `sentinel/`.
- No `redis` / `psycopg` / `sqlalchemy` / `kafka` / `telegram` import
  under `sentinel/canary/` or `sentinel/runtime/canary_veto.py`.
- `CanaryVetoDecision` pins `creates_action=False`,
  `writes_external=False`, `approves_trade=False`,
  `no_veto_is_approval=False` via `Literal`.
- `can_affect_canary=True` is permitted only when
  `decision=veto` AND environment is `micro_live_canary`.

## 4. Veto is not approval

A `veto` decision **may** be honored by Gel.Al's risk engine.  It
does not place an order or mutate strategy state.  It is an
advisory safety brake.

## 5. No-veto is not approval

`no_veto` means Sentinel saw no additional block reason.  It does
**not** grant trade authorization.  Gel.Al's risk engine continues
normal evaluation regardless of Sentinel's no-veto.

## 6. Gel.Al remains execution engine

Gel.Al owns API credentials, exchange SDKs, order placement, kill
switch.  Sentinel owns ledger, gate audits, deontic policy,
paper/canary advisories.  V8 adds no Sentinel→Gel.Al write surface.

## 7. Sentinel canary role

```
Gel.Al candidate action     ─► Sentinel canary veto layer
                                  - veto       (BLOCK)
                                  - monitor    (MONITOR)
                                  - no_veto    (NO_ACTION / MONITOR)
                              ─► Gel.Al risk engine reads veto
                                  via separate advisory channel
                                  (out of Sentinel scope)
```

## 8. Canary candidate action observation

`CanaryCandidateAction` carries only abstract scalars and hashed
scope refs.  Raw symbol / venue / strategy / order side / API key /
account / balance fields are rejected at construction.

## 9. Veto request model

`VetoRequest` bundles a `CanaryCandidateAction` plus optional
references to the active policy record, paper decision, replay
evidence, memory records, and a deadline.

## 10. Veto decision model

`CanaryVetoDecision`:

- `decision: VetoDecisionKind ∈ {veto, monitor_only, no_veto}`
- `system_output: SystemOutput`
- `reasons: tuple[VetoReason, ...]`
- four safety flags pinned `Literal[False]`:
  `creates_action`, `writes_external`, `approves_trade`,
  `no_veto_is_approval`
- `can_affect_canary: bool` — True only iff
  `decision=veto` AND environment is `micro_live_canary`.

Mapping invariants:

- `veto`  → `system_output=BLOCK`, non-empty reasons.
- `monitor_only` → `system_output=MONITOR`.
- `no_veto` → `system_output ∈ {NO_ACTION, MONITOR}`,
  `can_affect_canary=False`.

## 11. Micro-live bounds

`CanaryMicroLiveBounds` enforces tiny per-hour candidate / veto /
unvetoed caps plus per-event thresholds (staleness, latency,
liquidity, risk, confidence).  Fail-closed: any missing required
flag rejects the artifact.

## 12. Fail-closed discipline

`bounds.fail_closed_on_error=True` is a `Literal[True]` field.
Any unexpected error in the evaluator returns a veto with
`reason=fail_closed`.

## 13. Policy integration

V6 active policy is consulted read-only.  If absent and
`bounds.missing_policy_blocks=True`, the candidate is vetoed with
`reason=no_active_policy`.  If active policy outputs BLOCK, the
candidate is vetoed with `reason=policy_block`.

## 14. Paper co-pilot integration

V7 `PaperDecision` reference (optional) may upgrade the decision:

- `paper_decision.output=BLOCK` → veto.
- `paper_decision.output=NEED_RECALL` → monitor_only.
- `paper_decision.output=MONITOR` → continue (monitor is not approval).

## 15. Replay evidence integration

V4 replay-evidence advisory: low survival / uncertain alignment
adds `replay_uncertain` reason and downgrades to `monitor_only`.

## 16. Memory recall integration

V3 memory store is accepted read-only.  V8 performs no raw-symbol
recall.  `memory_record_refs` in the request are passed through to
audit but do not trigger evaluator mutation.

## 17. Observer audit events

V8 adds one new catalog row:

```
CANARY_VETO_DECISION_RECORDED  family=deontic  PERMANENT
```

Severity HIGH; human alert required only when
`decision=veto` AND severity_band CRITICAL.  Audit emitted for
every evaluator outcome.

## 18. Local JSONL canary adapter

`CanaryCandidateJsonlAdapter(path)` reads `CanaryCandidateAction`
records.  Read-only; no write method; no network.

## 19. Optional external Gel.Al contract (docs only)

`docs/integrations/gel-al-canary-veto-contract.md` documents the
one-way advisory channel.  No Python code implements a Gel.Al
write client in V8.

## 20. CLI / local runner

`python -m sentinel.runtime.canary_veto --input <path> --ledger <path>`
runs the batch evaluator.  Exit codes:

- 0 OK
- 1 load / schema error
- 2 hash chain invalid
- 3 any decision violates the four safety flags

## 21. Tests and invariants

63 invariants from goal spec §12 covered across 7 test files.

## 22. Forbidden surfaces

| # | Forbidden | Enforcement |
|---|-----------|-------------|
| 1 | execution verb in any output | closed `SystemOutput` |
| 2 | `ApprovedActionIntent` from V8 | source-grep |
| 3 | raw symbol / venue / strategy in candidate | `extra=forbid` + denylist |
| 4 | `redis_stream` / `orders_pending_payload` / similar | denylist |
| 5 | no-veto becoming approval | `no_veto_is_approval=Literal[False]` |
| 6 | trade approval | `approves_trade=Literal[False]` |
| 7 | external write | `writes_external=Literal[False]` |
| 8 | action object creation | `creates_action=Literal[False]` |
| 9 | Gel.Al Redis / DB / HTTP client | no import in V8 modules |

## 23. Done definition

- `CanaryCandidateAction` schema implemented.
- `CanaryVetoDecision` + `VetoRequest` + `VetoReason` +
  `VetoDecisionKind` implemented.
- `CanaryMicroLiveBounds` + `CanaryDecisionWindowState` +
  `check_canary_bounds` implemented.
- `CanaryVetoContext` + `evaluate_canary_veto` implemented.
- `emit_canary_veto_decision_recorded` + catalog row
  `CANARY_VETO_DECISION_RECORDED` added.
- `CanaryCandidateJsonlAdapter` implemented.
- `run_canary_veto_file` + CLI implemented.
- 12 fixtures (11 valid scenarios + 1 invalid).
- 63+ V8 tests.
- Public API additions.
- Gel.Al canary veto contract doc.
- Build plan + closure review.
- Full sweep GREEN.

## 24. Deferred V9+ items

- V9 Limited Live Co-Governance.
- Live veto enforcement in production.
- Capital scaling.
- Real Gel.Al Redis / DB / HTTP write client.
- Telegram commands.
- Real exchange adapter.
- LLM-assisted veto authoring.
- Cryptographic signature verification on policy artifacts.
