# 0021 — V9 Limited Live Co-Governance — Closure Review

**Date:** 2026-05-20  
**Reviewer:** Automated phase-closure protocol  
**Phase:** V9 — Limited Live Co-Governance  
**Build plan:** `docs/build/0010-v9-limited-live-co-governance-build-plan.md`  
**Final verdict:** **GREEN**

> Filed as `0021-…`; the goal-spec placeholder numbering does not
> match the actual repo (0014-0020 are V2–V8 reviews).

---

## 1. Status

Status: **GREEN**  
Scope: V9 — veto-first, human-approved, bounded co-governance
producing closed `SystemOutput` advisories over Gel.Al-observed
limited-live candidate governance requests.

---

## 2. Version: V9 — Limited Live Co-Governance

Ninth phase added to PR #1.

---

## 3. Scope completed

- `GovernanceEnvironment` (5-value closed enum including `limited_live`)
- `GovernanceScopeKind` (6-value closed enum)
- `LimitedLiveGovernanceScope` (5 `Literal[True]` fail-closed flags;
  28-field forbidden-name denylist)
- `GovernanceRequestKind` (8-value closed enum)
- `LiveGovernanceRequest` (live_impact_possible ↔ requires_human_approval
  invariant; limited_live ↔ human_approval_required invariant)
- `HumanApprovalStatus` (5-value closed enum)
- `HumanApprovalRecord` (decided_at_ms required for approved/rejected/revoked;
  approval_reason_hash required for approved)
- `is_human_approval_valid` helper
- `GovernanceDecisionKind` (5-value closed enum — no approve / execute / order)
- `GovernanceReason` (21-value closed enum)
- `LiveGovernanceDecision` (5 safety flags pinned `Literal[False]`:
  `creates_action`, `writes_external`, `approves_trade`,
  `no_veto_is_approval`, `monitor_is_approval`; `live_impact_allowed=True`
  permitted only when decision=block AND output=BLOCK)
- `GovernanceGuardContext` + `evaluate_governance_guard`
  (13-step deterministic decision order, fail-closed throughout)
- `emit_live_governance_decision_recorded` + new catalog row
  `LIVE_GOVERNANCE_DECISION_RECORDED` (family=deontic, permanent,
  severity=HIGH)
- `LiveGovernanceRequestJsonlAdapter` (read-only)
- `run_live_governance_file` + `python -m sentinel.runtime.live_governance` CLI
- `docs/integrations/gel-al-limited-live-governance-contract.md`
- Public API additions (15 V9 symbols)
- 4 fixtures (3 valid scenarios + 1 invalid)
- 102 V9 tests across 8 test files

---

## 4. Files added

```
sentinel/governance/__init__.py
sentinel/governance/scope.py
sentinel/governance/request.py
sentinel/governance/approval.py
sentinel/governance/decision.py
sentinel/governance/guard.py
sentinel/governance/audit.py
sentinel/governance/jsonl.py
sentinel/runtime/live_governance.py
docs/build/0010-v9-limited-live-co-governance-build-plan.md
docs/integrations/gel-al-limited-live-governance-contract.md
docs/reviews/0021-v9-limited-live-co-governance-review.md
tests/governance/__init__.py
tests/governance/_fixtures.py
tests/governance/test_scope_schema.py
tests/governance/test_request_schema.py
tests/governance/test_approval.py
tests/governance/test_decision_schema.py
tests/governance/test_guard.py
tests/governance/test_audit.py
tests/governance/test_jsonl.py
tests/runtime/test_live_governance_runner.py
tests/fixtures/governance/benign_no_action.jsonl
tests/fixtures/governance/expired_request_block.jsonl
tests/fixtures/governance/high_risk_block.jsonl
tests/fixtures/governance/invalid_order_fields.jsonl
```

Modified (additive only):

```
sentinel/__init__.py               (V9 exports + __all__)
sentinel/observer/catalog.py       (+1 canonical row LIVE_GOVERNANCE_DECISION_RECORDED)
tests/test_public_api.py           (V9_PUBLIC_API_ADDITIONS + test)
```

---

## 5. Tests added

102 new V9 tests.  Total suite: **1544 passing**.

| File | Tests |
|---|---|
| `tests/governance/test_scope_schema.py` | 12 |
| `tests/governance/test_request_schema.py` | 9 |
| `tests/governance/test_approval.py` | 10 |
| `tests/governance/test_decision_schema.py` | 15 |
| `tests/governance/test_guard.py` | 17 |
| `tests/governance/test_audit.py` | 6 |
| `tests/governance/test_jsonl.py` | 5 |
| `tests/runtime/test_live_governance_runner.py` | 12 |
| `tests/test_public_api.py` (V9 additions test) | +1 |

---

## 6. Fixtures added

```
benign_no_action.jsonl          benign request, requires_human_approval=True
expired_request_block.jsonl     deadline < now_ms → governance_timeout
high_risk_block.jsonl           risk_score=0.95 → policy_block / high_risk
invalid_order_fields.jsonl      payload contains order_side / api_key /
                                  direct_order → ValidationError
```

---

## 7. Co-governance is not execution

A `block_live_candidate` decision records a Sentinel safety brake.
Gel.Al's risk engine, in a separate process out of Sentinel's
repository, may interpret it as a brake.  Sentinel places no order,
constructs no action-intent object, and writes nothing to Gel.Al.

## 8. No-veto is not approval

`no_action` records that Sentinel saw no block reason.  The schema
pins `no_veto_is_approval=Literal[False]`; any attempt to flip it
is a type error and a runtime ValueError.

## 9. Monitor is not approval

`monitor_only` is advisory.  The schema pins
`monitor_is_approval=Literal[False]`.

## 10. Human approval discipline

For `scope.environment=limited_live`, requests must satisfy
`requires_human_approval=True`.  The guard demands a valid
`HumanApprovalRecord` (`status=approved`, not expired, matching
`request_id`, non-empty `signature`) before any non-block path.
Missing / invalid approval → block.

## 11. Governance request model

`LiveGovernanceRequest` carries only abstract bounded scalars
(`risk_score`, `confidence`, `staleness_ms`, `latency_ms`,
`live_impact_possible`, `requires_human_approval`) plus hashed
scope refs and reference IDs.  Raw labels, order sides, API keys,
and account fields are rejected at construction by the scope's
`extra='forbid'` plus a 28-name denylist.

## 12. Governance decision model

| Field | Value |
|---|---|
| `creates_action` | `Literal[False]` |
| `writes_external` | `Literal[False]` |
| `approves_trade` | `Literal[False]` |
| `no_veto_is_approval` | `Literal[False]` |
| `monitor_is_approval` | `Literal[False]` |

Closed `GovernanceDecisionKind`:
- `block_live_candidate` → BLOCK
- `monitor_only`         → MONITOR
- `wait_for_human`       → WAIT
- `need_recall`          → NEED_RECALL
- `no_action`            → NO_ACTION

`live_impact_allowed=True` permitted only when
`decision=block_live_candidate` AND `system_output=BLOCK`.

## 13. Governance guard

`evaluate_governance_guard` is deterministic.  13-step decision
order with fail-closed at every gate:

1. `hash_chain_valid=False`                  → block / `hash_chain_invalid`
2. deadline expired                          → block / `governance_timeout`
3. `kill_switch_observed`                    → block / `kill_switch_observed`
4. missing active policy                     → block / `missing_active_policy`
5. `live_impact_possible` + invalid approval → block / `missing_human_approval`
6. canary veto                               → block / `canary_veto`
7. paper BLOCK                               → block / `paper_block`
8. policy BLOCK                              → block / `policy_block`
9. memory conflict (refs + risk ≥ 0.5)      → need_recall / `memory_conflict`
10. replay uncertain (score < 0.3)          → monitor / `replay_uncertain`
11. high risk_score (≥ 0.85)                → block / `high_risk`
12. low confidence (< 0.3)                  → monitor / wait / `low_confidence`
13. otherwise                                → no_action / `no_block_reason_found`

The guard never constructs an action-intent object (source-grep
verified).

## 14. Policy / Paper / Canary / Replay / Memory integration

- V6 active policy: read-only; policy BLOCK upgrades to governance block.
- V7 paper decision: optional; BLOCK upgrades; NEED_RECALL signal honored.
- V8 canary veto decision: optional; veto upgrades to block.
- V4 replay evidence: advisory score `< 0.3` downgrades to monitor.
- V3 memory store: API hook present; no raw-symbol recall.

## 15. Gel.Al governance contract

`docs/integrations/gel-al-limited-live-governance-contract.md`
documents the one-way Sentinel → Gel.Al advisory direction.  No
Python code in V9 implements a Gel.Al write client; transport is
the operator's responsibility.

## 16. Runtime batch runner

`run_live_governance_file` loads `LiveGovernanceRequest` records,
evaluates each, emits a permanent
`LIVE_GOVERNANCE_DECISION_RECORDED` audit per result.  CLI exit
codes:

- 0 OK
- 1 load / schema error
- 2 hash chain invalid
- 3 any decision violated the five safety flags

## 17. Observer audit

V9 adds one canonical event:
`LIVE_GOVERNANCE_DECISION_RECORDED` (family=deontic, permanent,
severity=HIGH).  No other catalog change.

---

## 18. Safety invariants

| # | Invariant | Status |
|---|-----------|--------|
| 1 | no live order generation | GREEN |
| 2 | no trade approval by Sentinel alone | GREEN (`approves_trade=Literal[False]`) |
| 3 | no Gel.Al DB write | GREEN |
| 4 | no Redis `orders.pending` write | GREEN (source-grep) |
| 5 | no config / kill mutation | GREEN (source-grep) |
| 6 | no exchange imports | GREEN |
| 7 | no network imports | GREEN |
| 8 | no LLM imports | GREEN |
| 9 | no forbidden output literals | GREEN |
| 10 | no `ApprovedActionIntent` generated | GREEN (source-grep) |
| 11 | no no-veto-as-approval | GREEN (`no_veto_is_approval=Literal[False]`) |
| 12 | no monitor-as-approval | GREEN (`monitor_is_approval=Literal[False]`) |
| 13 | no human approval bypass | GREEN (guard validator) |
| 14 | output ⊆ closed `SystemOutput` | GREEN |
| 15 | observer audit present | GREEN |
| 16 | hash chain verifies | GREEN |
| 17 | dry_sim canonical output unchanged | GREEN (WAIT, 4/2/0) |
| 18 | `LimitedLiveGovernanceScope` fail-closed flags pinned `Literal[True]` | GREEN |

---

## 19. What is deliberately deferred

- V10 Financial AGI v1.
- Full live autonomy.
- Live capital scaling.
- Real Gel.Al API / Redis integration client.
- Telegram commands.
- Exchange adapters.
- LLM-assisted governance authoring.
- Cryptographic signature verification on governance decisions.
- Cross-instance / fork / migration of governance state.

---

## 20. Next recommended version

**V10 — Financial AGI v1.**

V9 grants no implicit permission for V10 to:

- flip any of the five safety flags
- write back to Gel.Al
- approve trades
- bypass human approval
- treat monitor / no_action / wait / need_recall as authorization

V10 must arrive with its own design doc and closure review.

---

## Local sweep at HEAD (V9)

```
uv sync                          Resolved 17 packages
uv run ruff check .              All checks passed
uv run ruff format --check .     254 files clean
uv run pyright                   0 errors / 0 warnings / 0 informations
uv run pytest -q                 1544 passed
forbidden imports grep           clean
forbidden outputs grep           clean
runtime forbidden write grep     clean (denylist strings in schema only)
dry sim canonical                WAIT (audit=4, perm=2, ring=0)
live-governance CLI smoke        benign fixture → block=1 (fail-closed
                                  with no policy context)
                                  hash_chain_valid=True
```

V9 phase is **CLOSED**.
