# Financial AGI v1 — Incident Response

**Version:** V10  
**Date:** 2026-05-20

---

## Severity levels

| Level | Examples |
|---|---|
| CRITICAL | Safety flag set to True; hash chain break; CLI exit 3 |
| HIGH | Persistent block pattern; 90-day evidence gap; policy missing |
| MEDIUM | Repeated WAIT / NEED_RECALL; low confidence pattern |
| LOW | Single monitor / no_action anomaly |

---

## CRITICAL — safety flag violation (exit code 3)

**Trigger:** any of `any_creates_action`, `any_writes_external`,
`any_approves_trade`, `any_no_veto_is_approval`,
`any_monitor_is_approval` is `True` in a batch result.

**Immediate actions:**
1. Stop all batch processing immediately.
2. Preserve the ledger JSONL file (do not overwrite).
3. Escalate to security and engineering leads.
4. Do NOT restart without a root-cause analysis and code review.

---

## HIGH — hash chain invalid (exit code 2)

**Trigger:** `ledger.verify()` returns `False` or CLI exits 2.

**Immediate actions:**
1. Stop all batch processing.
2. Preserve the ledger JSONL file.
3. Compare ledger content against last known-good backup.
4. Investigate: file corruption, partial write, replay attack.
5. Replace with clean ledger from last verified snapshot before resuming.

---

## HIGH — persistent block pattern

**Trigger:** block rate > 80% over a 1-hour window.

**Actions:**
1. Check kill_switch_observed flag in context.
2. Review active policy record for over-restrictive thresholds.
3. Check human approval expiry timestamps.
4. Review canary veto decisions for false positives.

---

## MEDIUM — missing active policy

**Trigger:** `MISSING_ACTIVE_POLICY` reason appears.

**Actions:**
1. Confirm a policy candidate has been submitted and activated via V6 path.
2. Check policy record `status = ACTIVE` in the policy store.
3. Verify `effective_at_ms` is not in the future.

---

## Escalation contacts

- All CRITICAL incidents: immediate escalation to engineering.
- V10 safety flags: never treat as recoverable without code review.
