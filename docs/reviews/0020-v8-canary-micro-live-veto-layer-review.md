# 0020 — V8 Canary Micro-Live Veto Layer — Closure Review

**Date:** 2026-05-20  
**Reviewer:** Automated phase-closure protocol  
**Phase:** V8 — Canary Micro-Live Veto Layer  
**Build plan:** `docs/build/0009-v8-canary-micro-live-veto-layer-build-plan.md`  
**Final verdict:** **GREEN**

> Filed as `0020-…`.  Goal-spec placeholder numbering does not match
> the actual repo (0014-0019 are taken by V2–V7 reviews).

---

## 1. Status

Status: **GREEN**  
Scope: V8 — veto-only canary safety layer producing closed
`SystemOutput` advisories over Gel.Al-observed candidate actions.

---

## 2. Version: V8 — Canary Micro-Live Veto Layer

Eighth phase added to PR #1.

---

## 3. Scope completed

- `CanaryCandidateSource` (5-value closed enum)
- `CanaryEnvironment` (4-value closed enum;
  `micro_live_canary` is an observed label only)
- `CanaryCandidateAction` (28-name forbidden-field denylist; no raw
  symbol / venue / strategy / order / api_key / balance /
  redis_stream / orders_pending_payload)
- `VetoReason` (16-value closed enum)
- `VetoDecisionKind` (3-value closed enum: `veto`, `monitor_only`,
  `no_veto`)
- `VetoRequest` (deadline > requested_at validator)
- `CanaryVetoDecision` (four safety flags pinned `Literal[False]`:
  `creates_action`, `writes_external`, `approves_trade`,
  `no_veto_is_approval`; decision/output mapping invariants;
  `can_affect_canary=True` permitted only when `decision=veto` AND
  environment is `micro_live_canary`)
- `CanaryMicroLiveBounds` (hard-stop flags pinned `Literal[True]`:
  `kill_switch_blocks`, `missing_policy_blocks`,
  `missing_provenance_blocks`, `expired_candidate_blocks`,
  `fail_closed_on_error`)
- `CanaryDecisionWindowState` + `check_canary_bounds` +
  `reset_window_if_due`
- `CanaryVetoContext` + `evaluate_canary_veto` (deterministic rule
  set with constitutional hard-stops first)
- `emit_canary_veto_decision_recorded` + new catalog row
  `CANARY_VETO_DECISION_RECORDED` (family=deontic, permanent)
- `CanaryCandidateJsonlAdapter` (read-only)
- `run_canary_veto_file` + `python -m sentinel.runtime.canary_veto`
  CLI with exit codes 0/1/2/3
- `docs/integrations/gel-al-canary-veto-contract.md`
- Public API additions (13 V8 symbols)
- 5 fixtures (4 valid scenarios + 1 invalid)
- 97 V8 tests across 7 test files

---

## 4. Files added

```
sentinel/canary/__init__.py
sentinel/canary/candidate.py
sentinel/canary/veto.py
sentinel/canary/limits.py
sentinel/canary/evaluator.py
sentinel/canary/audit.py
sentinel/canary/jsonl.py
sentinel/runtime/canary_veto.py
docs/build/0009-v8-canary-micro-live-veto-layer-build-plan.md
docs/integrations/gel-al-canary-veto-contract.md
docs/reviews/0020-v8-canary-micro-live-veto-layer-review.md
tests/canary/__init__.py
tests/canary/_fixtures.py
tests/canary/test_candidate_schema.py
tests/canary/test_veto_schema.py
tests/canary/test_limits.py
tests/canary/test_evaluator.py
tests/canary/test_audit.py
tests/canary/test_jsonl.py
tests/runtime/test_canary_veto_runner.py
tests/fixtures/canary/benign_candidate_no_veto.jsonl
tests/fixtures/canary/expired_candidate_veto.jsonl
tests/fixtures/canary/high_risk_candidate_veto.jsonl
tests/fixtures/canary/negative_edge_candidate_veto.jsonl
tests/fixtures/canary/forbidden_order_fields_invalid.jsonl
```

Modified (additive only):

```
sentinel/__init__.py               (V8 exports + __all__)
sentinel/observer/catalog.py       (+1 canonical row CANARY_VETO_DECISION_RECORDED)
tests/test_public_api.py           (V8_PUBLIC_API_ADDITIONS + test)
```

---

## 5. Tests added

97 new V8 tests.  Total suite: **1457 passing**.

| File | Tests |
|---|---|
| `tests/canary/test_candidate_schema.py` | 16 |
| `tests/canary/test_veto_schema.py` | 16 |
| `tests/canary/test_limits.py` | 10 |
| `tests/canary/test_evaluator.py` | 15 |
| `tests/canary/test_audit.py` | 6 |
| `tests/canary/test_jsonl.py` | 5 |
| `tests/runtime/test_canary_veto_runner.py` | 14 |
| `tests/test_public_api.py` (V8 additions test) | +1 |

---

## 6. Fixtures added

```
benign_candidate_no_veto.jsonl         expected no_veto
expired_candidate_veto.jsonl           expected veto / EXPIRED_CANDIDATE
high_risk_candidate_veto.jsonl         expected veto / HIGH_RISK
negative_edge_candidate_veto.jsonl     expected veto / INSUFFICIENT_EDGE
forbidden_order_fields_invalid.jsonl   payload contains order_side / api_key /
                                        direct_order / redis_stream /
                                        orders_pending_payload
```

---

## 7. Veto is not approval

A `veto` decision (`system_output=BLOCK`) records that Sentinel saw
a safety reason to block.  Gel.Al's risk engine, in a separate
process out of Sentinel's repository, may interpret it as a brake.
Sentinel places no order, sizes no position, and constructs no
action-intent object.

## 8. No-veto is not approval

`no_veto` (`system_output ∈ {NO_ACTION, MONITOR}`) means Sentinel
saw no additional block reason this evaluation.  It does **not**
authorize trading.  The schema pins
`no_veto_is_approval=Literal[False]`; any attempt to flip it is a
type error AND a runtime ValueError.

## 9. Canary candidate action model

`CanaryCandidateAction` carries only abstract bounded scalars and
hashed scope / strategy / symbol / venue references.  Raw labels,
order sides, API keys, account fields, and Gel.Al-side execution
payloads (`redis_stream`, `orders_pending_payload`,
`order_command`, `direct_order`) are rejected at construction.

`notional_ref` is opaque (e.g. `"tier:micro"`); raw notional amounts
must be replaced upstream with a tier label.

## 10. Veto decision model

`CanaryVetoDecision`:

| Field | Value |
|---|---|
| `creates_action` | `Literal[False]` |
| `writes_external` | `Literal[False]` |
| `approves_trade` | `Literal[False]` |
| `no_veto_is_approval` | `Literal[False]` |

Mapping:

- `veto`        → `system_output=BLOCK`, non-empty reasons
- `monitor_only`→ `system_output=MONITOR`, `can_affect_canary=False`
- `no_veto`     → `system_output ∈ {NO_ACTION, MONITOR}`,
                  `can_affect_canary=False`

`shadow_only` may be False ONLY when `decision=veto` AND
`environment=micro_live_canary` AND `can_affect_canary=True`.

## 11. Micro-live bounds

`CanaryMicroLiveBounds` caps candidates per hour, vetoes per hour,
unvetoed candidates per hour, staleness, latency, orderbook age,
liquidity floor, confidence floor, risk ceiling.

The five hard-stop flags
(`kill_switch_blocks`, `missing_policy_blocks`,
`missing_provenance_blocks`, `expired_candidate_blocks`,
`fail_closed_on_error`) are pinned `Literal[True]`.

## 12. Fail-closed discipline

`bounds.fail_closed_on_error=True` is `Literal[True]`.  Any
unhandled exception in the evaluator falls through to a
veto with `reason=fail_closed`.

## 13. Policy / Paper / Replay integration

- V6 active policy is consulted read-only; policy BLOCK upgrades
  the canary decision to `veto / POLICY_BLOCK`.
- V7 paper decision `BLOCK` upgrades to veto; paper
  `NEED_RECALL` downgrades to `monitor_only / MEMORY_CONFLICT`.
- V4 replay evidence advisory: `replay_evidence_score < 0.3`
  downgrades to `monitor_only / REPLAY_UNCERTAIN`.
- V3 memory store is accepted by API but no raw-symbol recall is
  performed.

## 14. Gel.Al canary contract

`docs/integrations/gel-al-canary-veto-contract.md` documents the
**one-way advisory** Sentinel → Gel.Al direction.  No Python code
implements a Gel.Al write client.  Transport is the operator's
responsibility.

## 15. Runtime batch runner

`run_canary_veto_file` loads `CanaryCandidateAction` records from
local JSONL, evaluates each, emits a permanent
`CANARY_VETO_DECISION_RECORDED` audit per result.  CLI exit codes:

- 0 OK
- 1 load / schema error
- 2 hash chain invalid
- 3 any decision violated `creates_action` / `writes_external` /
  `approves_trade` / `no_veto_is_approval` invariant

## 16. Observer audit

V8 adds exactly one catalog row:
`CANARY_VETO_DECISION_RECORDED` (family=deontic, permanent,
severity=HIGH, human_alert_required=False).  No other catalog
changes; no inflation of event types.

---

## 17. Safety invariants

| # | Invariant | Status |
|---|-----------|--------|
| 1 | no live order generation | GREEN |
| 2 | no trade approval | GREEN (`approves_trade=Literal[False]`) |
| 3 | no Gel.Al DB write | GREEN |
| 4 | no Redis `orders.pending` write | GREEN (string grep) |
| 5 | no config/kill mutation | GREEN |
| 6 | no exchange imports | GREEN |
| 7 | no network imports | GREEN |
| 8 | no LLM imports | GREEN |
| 9 | no forbidden output literals | GREEN |
| 10 | no `ApprovedActionIntent` generated | GREEN (source-grep) |
| 11 | no no-veto-as-approval | GREEN (`Literal[False]`) |
| 12 | no paper-to-live promotion | GREEN |
| 13 | veto output BLOCK only | GREEN (schema validator) |
| 14 | output ⊆ closed `SystemOutput` | GREEN |
| 15 | observer audit present | GREEN |
| 16 | hash chain verifies | GREEN |
| 17 | dry_sim canonical output unchanged | GREEN (WAIT, 4/2/0) |

---

## 18. What is deliberately deferred

- V9 Limited Live Co-Governance.
- Actual Gel.Al API / Redis integration.
- Live veto enforcement in production.
- Capital scaling.
- Telegram commands.
- Exchange adapters.
- LLM-assisted veto authoring.
- Cross-instance / fork / migration of veto state.
- Cryptographic signature on veto decisions.

---

## 19. Next recommended version

**V9 — Limited Live Co-Governance.**

V8 grants no implicit permission for V9 to:

- flip any of the four safety flags
- write back to Gel.Al
- approve trades

V9 must arrive with its own design doc and closure review.

---

## Local sweep at HEAD (V8)

```
uv sync                          Resolved 17 packages
uv run ruff check .              All checks passed
uv run ruff format --check .     235 files clean
uv run pyright                   0 errors / 0 warnings / 0 informations
uv run pytest -q                 1457 passed
forbidden imports grep           clean
forbidden outputs grep           clean
orders.pending grep              clean (source-only)
dry sim canonical                WAIT (audit=4, perm=2, ring=0)
canary-veto CLI smoke            high_risk fixture → veto=1
                                 hash_chain_valid=True
```

V8 phase is **CLOSED**.
