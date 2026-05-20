# 0007 — V6 — Financial Deontic Policy — Build Plan

> Status: BUILD PLAN. Implementation tracks this document section-by-section.

## 1. Purpose

V6 introduces a signed, auditable financial **deontic policy** layer
that lives in M2 as `MemoryRecord(subject_class=DEONTIC_POLICY)`.
Policies are evaluated against Gel.Al shadow events to classify each
event into the closed v0.1 `SystemOutput` set
`{WAIT, BLOCK, MONITOR, NEED_RECALL, NO_ACTION}`.

The evaluation is **shadow-only**.  A V6 BLOCK is a Sentinel
classification recorded in M1; it is not a live veto, not an order,
not a Gel.Al config mutation.

## 2. Non-goals

- No live trading or execution.
- No paper co-pilot.
- No canary / live veto layer.
- No Gel.Al DB / Redis / config / kill-switch write.
- No exchange API integration.
- No LLM integration.
- No Telegram control.
- No production policy auto-tuning.
- No policy generated from replay alone.
- No multiple active overlapping policies for the same scope.
- No human / LLM bypass of the activation workflow.

## 3. Safety constraints

- All v0.1 / V2 / V3 / V4 / V5 constitutional invariants preserved.
- Output set still `{WAIT, BLOCK, MONITOR, NEED_RECALL, NO_ACTION}`.
- No `BUY` / `SELL` / `EXECUTE_REAL` / `ORDER_SUBMIT` outputs.
- No `ApprovedActionIntent` produced from policy evaluation.
- No exchange / network / LLM imports under `sentinel/`.
- Memory Write Gate not bypassed.
- Deontic Gate not bypassed.
- `OBSERVATION_INGESTED` / `WORKSPACE_PULSE` remain ring-only.
- A policy artifact carrying an executing action is rejected at schema construction.
- An active policy requires:
  1. signed artifact with non-empty `signed_by` / `signature` / `artifact_hash`
  2. `MemoryRecord.status == VERIFIED`
  3. non-empty `human_approval_ref`
- Emergency revert may target only a previous VERIFIED policy in the same scope.

## 4. Constitutional vs operational policy boundary

| Layer | Where | Mutable | V6? |
|---|---|---|---|
| Constitutional hard-stops | `sentinel/constitution/invariants.py` | NO (constitutional amendment) | unchanged |
| Operational financial policy | `MemoryRecord(DEONTIC_POLICY)` | YES via signed artifact + MWG + human approval | V6 |

V6 operational policy cannot weaken any constitutional hard-stop.

## 5. FinancialDeonticPolicyArtifact

Frozen Pydantic v2 model.  Carries:

- `artifact_id`, `policy_id`, `policy_version`
- `scope: FinancialPolicyScope`
- `thresholds: FinancialHardStopThresholds`
- `rules: tuple[FinancialPolicyRule, ...]` (non-empty)
- `signed_by`, `signature`, `artifact_hash`, `previous_artifact_hash`
- `effective_at_ms`, `expires_at_ms`
- `human_approval_ref`, `rollback_ref`
- `created_at_ms`

Validators reject empty rule tuple, expiry before effective, raw
symbol fields, and any execution-instruction key.

## 6. DeonticPolicyRecord in M2

`build_deontic_policy_candidate_record(artifact, provenance,
created_at_ms, evidence_refs) -> MemoryRecord` with
`subject_class=DEONTIC_POLICY`, `status=CANDIDATE`,
`payload=artifact.model_dump(mode="json")`.

`evidence_refs` populate both `causal_refs` and
`external_corroboration_refs` (human-attested approval is by
construction external).  `internal_only_refs` remain empty.

## 7. Policy lifecycle

```
CANDIDATE  ─► (out-of-band: VERIFIED by integration layer)
            ─► ACTIVE  (requires human_approval_ref)
            ─► SUPERSEDED  (when newer policy activates for same scope)
            ─► REJECTED / QUARANTINED / EXPIRED  (terminal)
```

`MemoryRecordStatus.VERIFIED` is set by the integration layer, not
by the gate (per MEMORY_WRITE_GATE v0.1 — MVP mode is candidate-only).
For V6, the test/dev path constructs verified records directly via
`MemoryRecord(...)` for activation; production verified
production remains constitutionally disabled.

## 8. Policy activation workflow

`InMemoryPolicyStore.activate_verified_policy(record_id,
human_approval_ref, now_ms)`:

1. Record must be present, status `VERIFIED`, subject_class
   `DEONTIC_POLICY`.
2. `human_approval_ref` non-empty.
3. If another active policy exists for the same scope, it is
   superseded (status → SUPERSEDED) with a status-change audit.
4. New record marked active; status-change audit emitted.

## 9. Emergency revert workflow

`emit_policy_emergency_revert(..., to_previous_verified_policy_record_id, ...)`:

- Target must have status `VERIFIED` (or `SUPERSEDED` previously
  active) in the same scope.
- Target must precede the current active policy.
- No forward-to-new-policy permitted via the revert path.

## 10. Policy scope model

`FinancialPolicyScope(scope_id, environment, source_system, venue_hash,
symbol_hash, strategy_hash, applies_to_all_symbols,
applies_to_all_strategies)`.  Hashes only — no raw symbol/venue/strategy
names.

Scope `environment="live"` is permitted as an observation label,
not as a Sentinel action permission.

## 11. Financial hard-stop families

`FinancialHardStopThresholds` enforces (at schema layer):

- `kill_switch_observed_blocks` must be True
- `stale_data_blocks` must be True
- `missing_provenance_blocks` must be True
- `bad_order_blocks` defaults to True (allowed False with rationale)
- bounded numeric thresholds

## 12. Gel.Al shadow policy evaluation

`build_policy_input_from_gelal_shadow(envelope)` extracts only
abstract scalars (`risk_score`, `confidence`, `staleness_ms`,
`bad_order`, `kill_switch_active`, `provenance_missing`).  Raw
symbol / venue / strategy are intentionally absent from
`FinancialPolicyInput`.

`evaluate_gelal_shadow_with_policy(envelope, active_policy_record,
ledger, ring_buffer, provenance)`:

1. routes `OBSERVATION_INGESTED` through V5 helper (ring-only).
2. builds policy input.
3. evaluates active policy.
4. returns `FinancialPolicyEvaluation` (`shadow_only=True`,
   `creates_action=False`, `writes_external=False`).

## 13. Observer audit events

V6 uses the existing `MEMORY_RECORD_STATUS_CHANGED` catalog row for
policy status changes (candidate → verified is out-of-band; verified
→ active and active → superseded use status-change audits).  No new
catalog row is added.

## 14. Memory Write Gate integration

V6 adds one row to the MWG MVP whitelist:

```python
(SubjectClass.DEONTIC_POLICY, EvidenceAxis.HUMAN_TESTIMONY)
```

This is constitutionally aligned: deontic policy candidates are
human-attested signed artifacts.  The gate remains candidate-only;
no verified production is enabled.  MWG audit emits as before.

## 15. Policy conflict resolution

`resolve_policy_conflicts(evaluations)` deterministic precedence:

```
BLOCK > MONITOR > NEED_RECALL > NO_ACTION > WAIT
```

Tie-break by `policy_id` ascending, then `rule_id` ascending.
BLOCK never downgraded.  Empty evaluations rejected.

## 16. Policy staleness and expiry

`is_policy_expired(record, now_ms)`: True iff
`artifact.expires_at_ms is not None and expires_at_ms <= now_ms`.

`is_policy_stale(record, now_ms)`: True iff
`now_ms - artifact.effective_at_ms > 30 * 24 * 3600 * 1000`
(default 30-day staleness window).

Expired or stale policies are rejected by `evaluate_financial_policy`;
no silent active expiry.

## 17. Policy provenance and signatures

`signed_by` / `signature` / `artifact_hash` non-empty.  Sentinel
performs schema-level presence validation only; cryptographic
signature verification is out of V6 scope (mock signature accepted
provided the fields are non-empty).  `previous_artifact_hash`
optional but recommended for chain anchoring.

## 18. Tests and invariants

53 invariants from goal spec §14 covered across 8 test files
(see §20 done definition).

## 19. Forbidden surfaces

| # | Forbidden | Enforcement |
|---|---|---|
| 1 | execution actions in policy rules | `FinancialPolicyAction` closed enum + name denylist |
| 2 | API key / account fields in artifact | `extra=forbid` |
| 3 | raw symbol/venue/strategy in policy input | absent from schema |
| 4 | `ApprovedActionIntent` from evaluator | source-grep test |
| 5 | Gel.Al write helper | no module imports Redis/HTTP/DB |
| 6 | active policy without human approval | store validator |
| 7 | multiple active overlapping policies | store validator |
| 8 | emergency revert forward to new policy | revert validator |

## 20. Done definition

- Financial policy schemas + `FinancialPolicyAction` closed enum.
- Signed artifact schema.
- M2 deontic_policy candidate builder.
- Policy store with activation discipline.
- Candidate write path through MWG + V6 wrapper.
- Activation / supersede / revert audit helpers.
- Shadow evaluator with closed output mapping.
- Gel.Al policy integration mapping.
- Conflict resolution + staleness/expiry helpers.
- 9 policy fixtures + 4 Gel.Al policy fixtures.
- 53+ V6 tests.
- Optional CLI `python -m sentinel.runtime.policy_eval`.
- Public API additions.
- Build plan + closure review.
- Full sweep GREEN.

## 21. Deferred V7+ items

- V7 Paper Co-Pilot.
- V8 Canary micro-live veto layer.
- V9 Limited live co-governance.
- Real Gel.Al policy enforcement.
- Live kill-switch control.
- Live strategy threshold mutation.
- Telegram control plane.
- Cryptographic signature verification.
- LLM-assisted policy authoring.
