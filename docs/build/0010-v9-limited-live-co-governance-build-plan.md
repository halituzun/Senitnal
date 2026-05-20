# 0010 — V9 — Limited Live Co-Governance — Build Plan

> Status: BUILD PLAN. Implementation tracks this document section-by-section.

## 1. Purpose

V9 lets Sentinel participate in Gel.Al's limited live decision chain
as a **bounded, auditable, human-approved, veto-first co-governor**.
Sentinel evaluates a `LiveGovernanceRequest` against the V6 active
policy, V7 paper decision, V8 canary veto decision, V4 replay
evidence, V3 memory state, and a `HumanApprovalRecord`, then
produces a `LiveGovernanceDecision` drawn from the closed v0.1
`SystemOutput` set.

`no_action`, `monitor_only`, `wait_for_human`, `need_recall` are
**not approval**.  Only `block_live_candidate` may carry a
`live_impact_allowed=True` flag, and only as a safety brake (no
order is placed, no Gel.Al state is mutated).

## 2. Non-goals

- No live order placement by Sentinel.
- No trade approval by Sentinel alone.
- No Gel.Al DB / Redis / config / kill-switch write.
- No exchange API integration.
- No LLM integration.
- No full autonomous live mode.
- No live capital scaling.
- No production allocation changes.
- No strategy threshold mutation.
- No Telegram command path.
- No V10 financial AGI v1.

## 3. Safety constraints

- All v0.1–V8 constitutional invariants preserved.
- Output set still `{WAIT, BLOCK, MONITOR, NEED_RECALL, NO_ACTION}`.
- No `BUY` / `SELL` / `EXECUTE_REAL` / `ORDER_SUBMIT` outputs.
- No `ApprovedActionIntent` produced.
- No exchange / network / LLM imports under `sentinel/`.
- `LiveGovernanceDecision` pins `creates_action=False`,
  `writes_external=False`, `approves_trade=False`,
  `no_veto_is_approval=False`, `monitor_is_approval=False`
  via `Literal`.
- `live_impact_allowed=True` permitted only when
  `decision=block_live_candidate` AND
  `system_output=BLOCK`.

## 4. Co-governance is not execution

Sentinel **co-governs** by classifying.  Gel.Al's risk engine
remains final execution authority.  Sentinel never places an
order.

## 5. Veto is not approval

A `block_live_candidate` decision may be honored by Gel.Al as a
safety brake.  It does not authorize the inverse trade.

## 6. No-veto is not approval

`no_action` records that Sentinel saw no block reason.  It does
**not** authorize Gel.Al to act.  The schema pins
`no_veto_is_approval=Literal[False]`.

## 7. Gel.Al remains execution engine

Gel.Al keeps API credentials, exchange SDKs, order placement, kill
switch.  V9 adds no Sentinel→Gel.Al write surface.

## 8. Sentinel governance role

```
Gel.Al live candidate              ─► Sentinel governance evaluator
                                          - block_live_candidate (BLOCK)
                                          - monitor_only         (MONITOR)
                                          - wait_for_human       (WAIT)
                                          - need_recall          (NEED_RECALL)
                                          - no_action            (NO_ACTION)
                                      ─► Gel.Al risk engine reads
                                          advisory via separate
                                          transport (out of scope)
```

## 9. Limited live governance scope

`LimitedLiveGovernanceScope` carries hashed scope refs only.  The
five fail-closed flags
(`fail_closed_on_missing_policy`,
`fail_closed_on_missing_human_approval`,
`fail_closed_on_timeout`,
`fail_closed_on_hash_failure`,
`human_approval_required`)
are pinned `Literal[True]` when `environment=limited_live`.

## 10. Governance request model

`LiveGovernanceRequest` is an observed candidate governance
request from Gel.Al or local fixture.  Raw symbol / venue /
strategy / order / API / account fields are rejected at
construction.

## 11. Governance decision model

`LiveGovernanceDecision`:

| Field | Value |
|---|---|
| `creates_action` | `Literal[False]` |
| `writes_external` | `Literal[False]` |
| `approves_trade` | `Literal[False]` |
| `no_veto_is_approval` | `Literal[False]` |
| `monitor_is_approval` | `Literal[False]` |

There is no `approve` / `allow` / `execute` / `submit` decision
kind.  The closed `GovernanceDecisionKind` set is:
`block_live_candidate`, `monitor_only`, `wait_for_human`,
`need_recall`, `no_action`.

## 12. Human approval model

`HumanApprovalRecord` carries `status ∈ {pending, approved,
rejected, expired, revoked}`, `signed_by` / `signature` /
`provenance_hash` non-empty, `expires_at_ms > created_at_ms`.
Approved records require `approval_reason_hash`.  The schema
contains no trade-command fields.

`is_human_approval_valid` returns True iff the approval record
matches the request_id, is `approved`, not expired, and has a
non-empty signature.

## 13. Live-impacting governance guard

`evaluate_governance_guard` produces a `LiveGovernanceDecision`.
Decision order:

1. `hash_chain_valid=False`                  → block / `hash_chain_invalid`
2. request deadline expired                  → block / `governance_timeout`
3. `kill_switch_observed`                    → block / `kill_switch_observed`
4. missing active policy                     → block / `missing_active_policy`
5. `live_impact_possible` + invalid approval → block / `missing_human_approval`
6. canary veto                               → block / `canary_veto`
7. paper BLOCK                               → block / `paper_block`
8. policy BLOCK                              → block / `policy_block`
9. memory conflict                           → need_recall / `memory_conflict`
10. replay uncertain                         → monitor / `replay_uncertain`
11. high risk_score                          → block / `high_risk`
12. low confidence                           → monitor / `low_confidence`
13. otherwise                                → no_action / `no_block_reason_found`

`live_impact_allowed=True` only when
`decision=block_live_candidate` AND `system_output=BLOCK`.

## 14. Policy integration

V6 active policy consulted read-only.  Policy BLOCK upgrades to
governance block.

## 15. Canary integration

V8 `CanaryVetoDecision` reference (optional).  Canary veto
upgrades to governance block.

## 16. Paper integration

V7 `PaperDecision` reference (optional).  Paper BLOCK upgrades to
governance block; paper NEED_RECALL downgrades to need_recall.

## 17. Replay evidence integration

V4 replay-evidence advisory: low replay score downgrades to
monitor.

## 18. Financial memory integration

V3 memory store accepted by API; V9 performs no raw-symbol recall.
Memory conflict signal carried via the request's
`memory_record_refs` field.

## 19. Timeout and fail-closed discipline

Deadline expired → block.  Hash chain invalid → block.  Missing
human approval → block.  Missing active policy → block.  No path
through the guard escalates the decision toward approval on error.

## 20. Observer audit events

V9 adds one new canonical event:

```
LIVE_GOVERNANCE_DECISION_RECORDED  family=deontic
                                    permanence=permanent
                                    severity=HIGH
                                    human_alert_required=False
```

Every guard outcome emits this event.

## 21. Local JSONL governance adapter

`LiveGovernanceRequestJsonlAdapter(path)` reads
`LiveGovernanceRequest` records.  Read-only; no write method; no
network.

## 22. Gel.Al governance contract

`docs/integrations/gel-al-limited-live-governance-contract.md`
documents the one-way advisory channel.  No Python code
implements a Gel.Al write client.

## 23. CLI / local runner

`python -m sentinel.runtime.live_governance --input <path>
--ledger <path>` runs the batch governance evaluator.  Exit codes:

- 0 OK
- 1 load / schema error
- 2 hash chain invalid
- 3 any decision violates safety flags

## 24. Tests and invariants

73 invariants from goal spec §13 covered across 8 test files.

## 25. Forbidden surfaces

| # | Forbidden | Enforcement |
|---|-----------|-------------|
| 1 | approve / execute / order decision kind | closed `GovernanceDecisionKind` |
| 2 | `ApprovedActionIntent` from V9 | source-grep |
| 3 | raw symbol / venue / strategy in request | `extra=forbid` + denylist |
| 4 | `redis_stream` / `orders_pending_payload` | denylist |
| 5 | no-veto → approval | `no_veto_is_approval=Literal[False]` |
| 6 | monitor → approval | `monitor_is_approval=Literal[False]` |
| 7 | trade approval | `approves_trade=Literal[False]` |
| 8 | external write | `writes_external=Literal[False]` |
| 9 | action object | `creates_action=Literal[False]` |
| 10 | Gel.Al Redis / DB / HTTP client | no import in V9 modules |
| 11 | live_impact_allowed without BLOCK | schema validator |

## 26. Done definition

- `LimitedLiveGovernanceScope` schema implemented.
- `LiveGovernanceRequest` schema implemented.
- `HumanApprovalRecord` + `is_human_approval_valid` implemented.
- `LiveGovernanceDecision` schema implemented.
- `evaluate_governance_guard` implemented.
- `emit_live_governance_decision_recorded` + catalog row
  `LIVE_GOVERNANCE_DECISION_RECORDED` added.
- `LiveGovernanceRequestJsonlAdapter` implemented.
- `run_live_governance_file` + CLI implemented.
- 5 fixtures (4 valid + 1 invalid).
- 73+ V9 tests.
- Public API additions.
- Gel.Al limited live governance contract doc.
- Build plan + closure review.
- Full sweep GREEN.

## 27. Deferred V10 items

- V10 Financial AGI v1.
- Full live autonomy.
- Live capital scaling.
- Real Gel.Al API / Redis integration client.
- Telegram commands.
- Exchange adapters.
- LLM-assisted governance authoring.
- Cryptographic signature on governance decisions.
