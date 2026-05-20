# 0018 — V6 Financial Deontic Policy — Closure Review

**Date:** 2026-05-20  
**Reviewer:** Automated phase-closure protocol  
**Phase:** V6 — Financial Deontic Policy  
**Build plan:** `docs/build/0007-v6-financial-deontic-policy-build-plan.md`  
**Final verdict:** **GREEN**

> The V6 review is filed as `0018-…` because doc slots `0014-0017`
> were already taken by V2/V3/V4/V5 reviews; the goal spec's
> placeholder number does not match real numbering in the repository.

---

## 1. Status

Status: **GREEN**  
Scope: V6 — signed financial deontic policy in M2 + shadow-only
evaluation against Gel.Al envelopes.

---

## 2. Version: V6 — Financial Deontic Policy

Sixth phase added to PR #1 on top of v0.1.0-mvb baseline.

---

## 3. Scope completed

- `FinancialPolicyAction` (closed 5-value enum, all `classify_*`)
- `FinancialPolicyOperator` (closed 8-value enum)
- `FinancialPolicySeverity` (closed 5-value enum)
- `FinancialPolicyScope` (hashed-only, no raw symbol/venue/strategy)
- `FinancialHardStopThresholds` (kill-switch / stale / missing-provenance
  hard-stops pinned to True via `Literal`)
- `FinancialPolicyRule` (closed condition-key allowlist; execution-token
  denylist; critical-cannot-be-wait validator)
- `FinancialDeonticPolicyArtifact` (signed artifact with non-empty
  signature / hash / signed_by; effective/expiry ordering; non-empty
  rules; defense-in-depth artifact-key denylist)
- `build_deontic_policy_candidate_record` (CANDIDATE-only DEONTIC_POLICY
  M2 record builder)
- `InMemoryPolicyStore` (CANDIDATE/VERIFIED entry; activation
  requires VERIFIED + human approval; one active per scope;
  emergency revert validates target-precedes-current)
- `submit_financial_policy_candidate` (MWG-integrated candidate write,
  candidate-only, M1 audit emitted)
- `emit_deontic_policy_status_changed`, `emit_policy_emergency_revert`
- `FinancialPolicyInput`, `FinancialPolicyEvaluation` (shadow_only,
  creates_action, writes_external pinned via `Literal`)
- `evaluate_financial_policy` (rejects non-ACTIVE policies; expiry +
  staleness gates; constitutional hard-stops first; output ∈ closed
  v0.1 set)
- `resolve_policy_conflicts` (BLOCK > MONITOR > NEED_RECALL > NO_ACTION
  > WAIT; deterministic tie-break)
- `build_policy_input_from_gelal_shadow`,
  `evaluate_gelal_shadow_with_policy` (Gel.Al integration; raw
  symbol/venue/strategy never propagated)
- `python -m sentinel.runtime.policy_eval` CLI
- Public API additions (15 V6 symbols)
- 4 policy fixtures + 4 Gel.Al policy fixtures
- 89 V6 tests across 7 test files

---

## 4. Files added

```
sentinel/policy/__init__.py
sentinel/policy/financial.py
sentinel/policy/record_builder.py
sentinel/policy/store.py
sentinel/policy/write_path.py
sentinel/policy/audit.py
sentinel/policy/evaluator.py
sentinel/integrations/gelal_policy.py
sentinel/runtime/policy_eval.py
docs/build/0007-v6-financial-deontic-policy-build-plan.md
docs/reviews/0018-v6-financial-deontic-policy-review.md
tests/policy/__init__.py
tests/policy/_fixtures.py
tests/policy/test_financial_policy_schema.py
tests/policy/test_policy_record_builder.py
tests/policy/test_policy_store.py
tests/policy/test_policy_write_path.py
tests/policy/test_policy_audit.py
tests/policy/test_policy_evaluator.py
tests/integrations/test_gelal_policy.py
tests/runtime/test_policy_eval.py
tests/fixtures/policy/conservative_shadow_policy.json
tests/fixtures/policy/invalid_execution_action_policy.json
tests/fixtures/policy/invalid_missing_signature_policy.json
tests/fixtures/policy/expired_policy.json
tests/fixtures/gelal_policy/gelal_opportunity_seen.jsonl
tests/fixtures/gelal_policy/gelal_high_risk_blocked.jsonl
tests/fixtures/gelal_policy/gelal_bad_order_observed.jsonl
tests/fixtures/gelal_policy/gelal_kill_switch_active.jsonl
```

Modified (additive only):

```
sentinel/__init__.py            (V6 exports + __all__)
sentinel/gates/memory_write.py  (+1 whitelist pair: DEONTIC_POLICY+HUMAN_TESTIMONY)
tests/test_public_api.py        (V6_PUBLIC_API_ADDITIONS + test)
```

The MWG whitelist gains a single row:
`(SubjectClass.DEONTIC_POLICY, EvidenceAxis.HUMAN_TESTIMONY)`.
This is constitutionally aligned (signed policy artifacts are
human-attested) and remains candidate-only — verified production is
still gated by `mvp_verified_disabled`.

---

## 5. Tests added

89 new V6 tests across 7 files.  Total suite: **1303 passing**.

| File | Tests |
|---|---|
| `tests/policy/test_financial_policy_schema.py` | 20 |
| `tests/policy/test_policy_record_builder.py` | 3 |
| `tests/policy/test_policy_store.py` | 9 |
| `tests/policy/test_policy_write_path.py` | 4 |
| `tests/policy/test_policy_audit.py` | 4 |
| `tests/policy/test_policy_evaluator.py` | 17 |
| `tests/integrations/test_gelal_policy.py` | 13 |
| `tests/runtime/test_policy_eval.py` | 6 |
| `tests/test_public_api.py` (V6 additions test) | +1 |

---

## 6. Fixtures added

```
conservative_shadow_policy.json           valid 3-rule shadow policy
invalid_execution_action_policy.json      action verbs rejected
invalid_missing_signature_policy.json     empty signature rejected
expired_policy.json                       expiry-window test policy
gelal_opportunity_seen.jsonl              nominal opportunity envelope
gelal_high_risk_blocked.jsonl             risk_score=0.95 envelope
gelal_bad_order_observed.jsonl            bad_order=true envelope
gelal_kill_switch_active.jsonl            kill_switch_active=true envelope
```

---

## 7. Financial policy lifecycle

```
CANDIDATE → VERIFIED (integration-layer, out of band) →
ACTIVE (requires human_approval_ref) → SUPERSEDED (on new active)

Emergency revert: target must be a previously verified policy in
the same scope; cannot forward to a newer policy.
```

---

## 8. M2 deontic_policy mapping

- `subject_class = DEONTIC_POLICY`
- `payload = FinancialDeonticPolicyArtifact.model_dump(mode="json")`
- `causal_refs = external_corroboration_refs = evidence_refs`
- `internal_only_refs = ()`
- `record_id = "policy-{artifact_id}"`

---

## 9. Memory Write Gate discipline

V6 candidates flow through the existing silent MWG.  The only
addition to MWG is the constitutional pair
`(DEONTIC_POLICY, HUMAN_TESTIMONY)`; MWG is not weakened, and
verified production remains gated by `mvp_verified_disabled`.
Every write attempt emits `MEMORY_RECORD_STATUS_CHANGED` to M1.

---

## 10. Human approval discipline

`InMemoryPolicyStore.activate_verified_policy` raises if
`human_approval_ref` is empty.  Tests cover the rejection path.

---

## 11. Emergency revert discipline

`InMemoryPolicyStore.revert_to_previous_verified` validates:

- source record is currently ACTIVE
- target was previously VERIFIED (or active-then-superseded) in the
  same scope
- target precedes source (by `created_at_ms`)

The "forward to newer policy" path is rejected with
`"target must precede the current active policy"`.

---

## 12. Shadow evaluation behavior

`FinancialPolicyEvaluation` pins `shadow_only=True`,
`creates_action=False`, `writes_external=False` via `Literal`
typing.  Any attempt to flip them at instantiation is a type error
and also rejected at `__post_init__`.

Constitutional hard-stops apply first:
- `kill_switch_active=True` → BLOCK (severity CRITICAL)
- `provenance_missing=True` → BLOCK (severity CRITICAL)
- `bad_order=True` → BLOCK (severity CRITICAL)

Then rule firing.  Final output is drawn from
`{WAIT, BLOCK, MONITOR, NEED_RECALL, NO_ACTION}`.

---

## 13. Gel.Al shadow integration

`build_policy_input_from_gelal_shadow(envelope)` strips raw symbol /
venue / strategy.  `scope_id` carries only hashed references.

`evaluate_gelal_shadow_with_policy` routes the V5 `OBSERVATION_INGESTED`
ring-only audit and then evaluates the active policy.  No write
back to Gel.Al; the V6 module imports no Redis / DB / HTTP / Telegram
client.

---

## 14. Safety invariants

| # | Invariant | Status |
|---|-----------|--------|
| 1 | no live execution path | GREEN |
| 2 | no Gel.Al write path | GREEN |
| 3 | no exchange / network / LLM imports | GREEN |
| 4 | no forbidden output literals | GREEN |
| 5 | no active policy without human approval | GREEN (store validator) |
| 6 | no policy execution action | GREEN (schema rejects) |
| 7 | no `ApprovedActionIntent` from V6 source | GREEN (source-grep) |
| 8 | no multiple active overlapping policies | GREEN (store supersede) |
| 9 | emergency revert forward-to-new rejected | GREEN |
| 10 | policy output ⊆ closed `SystemOutput` | GREEN |
| 11 | observer audit emitted on every status change | GREEN |
| 12 | hash chain verifies after V6 pipeline | GREEN |
| 13 | dry_sim canonical output unchanged | GREEN (WAIT, 4/2/0) |
| 14 | MWG remains candidate-only (mvp_verified_disabled) | GREEN |

---

## 15. What is deliberately deferred

- V7 Paper Co-Pilot
- V8 Canary micro-live veto layer
- V9 Limited live co-governance
- Real Gel.Al policy enforcement (live veto)
- Live kill-switch control by Sentinel
- Live strategy threshold mutation by Sentinel
- Telegram control plane
- Cryptographic signature verification (V6 validates schema-level
  presence only; cryptographic verification is V8+)
- LLM-assisted policy authoring

---

## 16. Next recommended version

**V7 — Paper Co-Pilot.**

Per the goal spec, V6 closure unlocks V7.  V7 must arrive with its
own design doc and closure review.  V6 grants no implicit permission
for V7 to write back to Gel.Al.

---

## Local sweep at HEAD (V6)

```
uv sync                          Resolved 17 packages
uv run ruff check .              All checks passed
uv run ruff format --check .     201 files clean
uv run pyright                   0 errors / 0 warnings / 0 informations
uv run pytest -q                 1303 passed
forbidden imports grep           clean
forbidden outputs grep           clean
dry sim canonical                WAIT (audit=4, perm=2, ring=0)
policy-eval CLI                  events_seen=1 block=1 hash_chain_valid=True
```

V6 phase is **CLOSED**.
