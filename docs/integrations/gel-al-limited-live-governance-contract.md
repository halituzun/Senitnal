# Gel.Al ↔ Sentinel — Limited Live Co-Governance Contract

> **Status: CONTRACT DOCUMENT (V9).  Read-only.  No live integration
> code, no exchange API key, no Sentinel→Gel.Al write client.**
>
> Companion to
> `docs/build/0010-v9-limited-live-co-governance-build-plan.md`,
> `docs/integrations/gel-al-canary-veto-contract.md`, and
> `docs/integrations/gel-al-borsa-readonly-bridge.md`.

---

## 1. Purpose

V9 expands the Gel.Al ↔ Sentinel bridge to support **limited live
co-governance**.  Sentinel evaluates each
`LiveGovernanceRequest` against the V6 active policy, V7 paper
decision, V8 canary veto decision, V4 replay evidence, V3 memory
state, and a `HumanApprovalRecord`, then emits a
`LiveGovernanceDecision` payload.

Gel.Al's risk engine **may** consult the decision as a safety
brake.  Sentinel never places, sizes, or directs an order, and
never approves one.

## 2. V9 scope

- Sentinel observes Gel.Al-side live candidate governance requests
  (read-only via signed export — Sentinel does not pull from Gel.Al).
- Sentinel synthesizes V6 / V7 / V8 / V4 / V3 inputs and the
  human-approval record into a single decision.
- Sentinel produces `LiveGovernanceDecision` payloads with
  `decision ∈ {block_live_candidate, monitor_only, wait_for_human,
  need_recall, no_action}`.
- Sentinel writes only to its own M1 ledger.

## 3. Gel.Al remains execution system

Gel.Al keeps API credentials, exchange SDKs, order placement, kill
switch.  Sentinel has no Python client to write to Gel.Al.

## 4. Sentinel remains governance / risk / audit layer

Sentinel owns ledger, gate audits, deontic policy, paper / canary /
governance advisories, M1 hash chain.

## 5. Allowed input: live governance request

`LiveGovernanceRequest` JSON records matching
`sentinel.governance.request.LiveGovernanceRequest`.  Raw symbol /
venue / strategy / order / api_key / account / balance fields must
be hashed or excluded before reaching Sentinel.

## 6. Allowed output: governance decision

`LiveGovernanceDecision` JSON records with five safety flags pinned
`False`: `creates_action`, `writes_external`, `approves_trade`,
`no_veto_is_approval`, `monitor_is_approval`.

## 7. No approval channel

There is **no** Sentinel → Gel.Al `approve_trade` channel.  No
governance decision value can be interpreted as approval —
including `no_action`, `monitor_only`, `wait_for_human`,
`need_recall`.

## 8. No order channel

There is no Sentinel → Gel.Al order channel.  No V9 function,
method, or symbol constructs or writes an order payload.

## 9. No config channel

There is no Sentinel → Gel.Al config-mutation channel.

## 10. No kill-switch mutation channel

Sentinel may *observe* an active kill switch as a block reason
but never sets or clears it.

## 11. Human approval requirement

For `scope.environment == limited_live`, Sentinel requires a valid
`HumanApprovalRecord` (`status=approved`, non-expired, matching
`request_id`, non-empty `signature`).  Missing / invalid approval
fails closed (block).

## 12. Timeout / fail-closed behavior

`LimitedLiveGovernanceScope` pins five fail-closed flags as
`Literal[True]`:

- `fail_closed_on_missing_policy`
- `fail_closed_on_missing_human_approval`
- `fail_closed_on_timeout`
- `fail_closed_on_hash_failure`
- `human_approval_required`

Any guard exception or missing input returns block.

## 13. How Gel.Al should interpret

| Sentinel decision | Gel.Al meaning |
|---|---|
| `block_live_candidate` (BLOCK) | safety brake; Gel.Al's risk engine MAY block.  Sentinel placed no order. |
| `monitor_only` (MONITOR) | observed pulse-worth signal; **not approval**. |
| `wait_for_human` (WAIT) | governance held pending human input; **not approval**. |
| `need_recall` (NEED_RECALL) | governance wants a memory lookup; **not approval**. |
| `no_action` (NO_ACTION) | Sentinel saw no block reason this evaluation; **not approval**.  Gel.Al's own risk pipeline remains authoritative. |

## 14. Correlation IDs

Every governance decision carries:

- `decision_id`, `request_id`, `candidate_ref`,
- `human_approval_ref`, `policy_record_ref`,
- `canary_decision_ref`, `paper_decision_ref`,
- `replay_evidence_refs`, `memory_record_refs`,
- `source_event_refs`, `scope_id`, `environment`.

Sentinel's M1 ledger emits `LIVE_GOVERNANCE_DECISION_RECORDED` for
every outcome.

## 15. Audit requirements

- Permanent M1 audit event per decision.
- Hash chain verification mandatory.
- `no_veto_is_approval=False` and `monitor_is_approval=False`
  audit-visible.

## 16. Incident procedure

If Sentinel's response is missing past `deadline_ms`, Gel.Al's
canary / limited-live mode **must** fail closed (treat as block).
No Sentinel response means no approval.

## 17. Rollback

The operator may revoke the Sentinel governance export at any time.
No Sentinel code change is required; the Gel.Al risk engine stops
reading the advisory channel.

## 18. Deferred V10 items

- V10 Financial AGI v1.
- Full live autonomy.
- Live capital scaling.
- Real Sentinel → Gel.Al transport client.
- Cryptographic signature verification on governance decisions.
- LLM-assisted governance authoring.
- Cross-instance / fork / migration of governance state.
