# Financial AGI v1 — Human Approval Reference

**Version:** V10  
**Date:** 2026-05-20

---

## Purpose

Human approval is mandatory for any governance request where
`live_impact_possible=True`.  This is enforced by the V9 governance
guard (step 5 of the 13-step decision order) and carried through to
V10 evaluation.

---

## Approval lifecycle

1. Operator constructs a `HumanApprovalRecord` with:
   - `status = approved`
   - `decided_at_ms` populated
   - `approval_reason_hash` populated
   - `signature` non-empty
   - `expires_at_ms` in the future relative to `now_ms`

2. The approval is injected into `GovernanceGuardContext.human_approval`.

3. The guard validates:
   - `status == approved`
   - `now_ms <= expires_at_ms`
   - `approval.request_id == request.request_id`
   - `signature` non-empty

4. Any validation failure → `MISSING_HUMAN_APPROVAL` block.

---

## Discipline

- Approval is per-request, per-window.  One approval does not cover
  multiple requests or sessions.
- An expired approval is treated as a block (`HUMAN_APPROVAL_EXPIRED`).
- A rejected approval is treated as a block (`HUMAN_REJECTED`).
- Sentinel never auto-approves any request.
- `no_veto_is_approval=False` and `monitor_is_approval=False` are
  permanently pinned.

---

## Audit trail

Every governance decision that passes or fails the approval gate is
recorded in a permanent `LIVE_GOVERNANCE_DECISION_RECORDED` event with:
- `human_approval_ref` populated if approval was valid.
- `reasons` containing the failure reason if approval was missing/invalid.
