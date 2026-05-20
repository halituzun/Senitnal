# Gel.Al ↔ Sentinel — Canary Micro-Live Veto Advisory Contract

> **Status: CONTRACT DOCUMENT (V8).  Read-only.  No live integration
> code, no exchange API key, no Sentinel→Gel.Al write client.**
>
> Companion to `docs/build/0009-v8-canary-micro-live-veto-layer-build-plan.md`
> and `docs/integrations/gel-al-borsa-readonly-bridge.md`.

---

## 1. Purpose

The micro-live canary deployment phase opens a single new direction
in the Gel.Al ↔ Sentinel bridge: a **one-way safety advisory** from
Sentinel back toward Gel.Al's risk engine.

The advisory is a `CanaryVetoDecision` payload.  Gel.Al's risk
engine **may** honor a Sentinel veto.  Sentinel never places, sizes,
or directs an order, and never approves one.

## 2. V8 scope

- Sentinel observes Gel.Al-side candidate actions (read-only via
  fixture or signed export — Sentinel does not pull from Gel.Al).
- Sentinel evaluates each candidate against the V6 active policy,
  V7 paper co-pilot output, V4 replay evidence, V3 memory state,
  and V8 canary bounds.
- Sentinel produces `CanaryVetoDecision` payloads with
  `decision ∈ {veto, monitor_only, no_veto}`.
- Sentinel writes only to its own M1 ledger.  Gel.Al, in a separate
  process not implemented in this repository, may subscribe to that
  ledger or to a sibling export and may interpret the veto as a
  safety brake.

## 3. One allowed Sentinel → Gel.Al surface: veto advisory only

The only direction allowed is `Sentinel.veto_advisory  →  Gel.Al.risk_engine`.
The advisory is read-only on the Gel.Al side; Sentinel has no
network or DB client to push it.  Transport (file, Kafka, Redis)
is **out of V8 scope** and is the operator's responsibility.

## 4. No approval channel

There is **no** Sentinel → Gel.Al `approve_trade` channel.  No
`CanaryVetoDecision.decision` value can be interpreted as approval.
`no_veto` is **not** approval.

## 5. No order channel

There is no Sentinel → Gel.Al order channel.  Sentinel has no
function, method, or symbol that constructs or writes an order
payload.

## 6. No config channel

There is no Sentinel → Gel.Al config-mutation channel.  Sentinel
cannot modify strategy thresholds, capital allocation, or any
Gel.Al runtime configuration.

## 7. No kill-switch mutation channel

There is no Sentinel → Gel.Al kill-switch channel.  Sentinel may
*observe* an active kill switch (V5 + V8) and use it as a veto
reason, but never sets or clears it.

## 8. Candidate action input schema

Gel.Al exports observed candidate actions as JSON records matching
`sentinel.canary.candidate.CanaryCandidateAction`.  Raw symbol /
venue / strategy / order-side / API-key / account / balance fields
must be hashed or excluded before reaching Sentinel.

## 9. Veto decision output schema

Sentinel emits `CanaryVetoDecision` JSON records with the four
safety flags pinned `False` (`creates_action`, `writes_external`,
`approves_trade`, `no_veto_is_approval`).  Decision is one of
`veto`, `monitor_only`, `no_veto`.  `system_output` ∈
`{WAIT, BLOCK, MONITOR, NEED_RECALL, NO_ACTION}`.

## 10. How Gel.Al should interpret

| Sentinel decision | Gel.Al meaning |
|---|---|
| `veto` (system_output=BLOCK) | safety brake observed; Gel.Al's risk engine MAY block the candidate.  Sentinel did not place or cancel an order. |
| `monitor_only` (MONITOR) | observed pulse-worth signal; no operational effect. |
| `no_veto` (NO_ACTION / MONITOR) | Sentinel saw no block reason **this evaluation**.  Gel.Al's own risk pipeline remains authoritative.  This is **not** approval. |

## 11. Timeouts

If Gel.Al does not receive a Sentinel response within
`VetoRequest.deadline_ms`, Gel.Al's canary mode **must** fail
closed (treat as veto).

## 12. Fail-closed behavior

`CanaryMicroLiveBounds.fail_closed_on_error` is pinned `True`.
Sentinel evaluator errors return `veto` with reason `fail_closed`.
Gel.Al must respect this.

## 13. Audit correlation ids

Every veto decision carries:

- `decision_id`
- `request_id`
- `candidate_id`
- `source_event_refs`
- `active_policy_record_ref`
- `paper_decision_ref`
- `replay_evidence_refs`
- `memory_record_refs`
- `scope_hash`

Sentinel's M1 ledger emits `CANARY_VETO_DECISION_RECORDED` for
every outcome.

## 14. 30-day canary metrics

At the end of the first 30-day canary window the operator reviews:

- total candidates seen
- veto rate
- monitor_only rate
- no_veto rate (and explicit reminder: not approval)
- forbidden output literal count (must be 0)
- hash chain re-verification (must PASS)
- any decision with `creates_action`, `writes_external`,
  `approves_trade`, or `no_veto_is_approval` flipped True (must be 0)

## 15. Rollback

If the 30-day metrics are unfavorable, the operator pauses the
canary by revoking the Sentinel veto export.  No Sentinel code
change is required; the Gel.Al risk engine simply stops reading
the advisory channel.

## 16. Deferred V9+ items

- V9 Limited Live Co-Governance.
- Real Sentinel→Gel.Al transport client (network / Redis / DB).
- Cryptographic signature on veto decisions.
- Live capital scaling.
- LLM-assisted veto authoring.
- Cross-instance / fork / migration of veto state.
