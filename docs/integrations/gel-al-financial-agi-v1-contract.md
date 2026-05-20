# Gel.Al — Financial AGI v1 Integration Contract

**Version:** V10  
**Date:** 2026-05-20  
**Direction:** Sentinel → Gel.Al (advisory only, one-way)

---

## 1. Overview

V10 extends the V9 advisory contract to include a full
Financial AGI v1 evaluation summary.  The direction remains
**Sentinel → Gel.Al**, advisory only.  Sentinel does not write
to any Gel.Al database, Redis stream, or execution channel.

---

## 2. What Sentinel provides

| Signal | Format | Description |
|---|---|---|
| `FINANCIAL_AGI_V1_EVALUATED` | JSONL (permanent) | Per-request AGI evaluation result |
| `FINANCIAL_AGI_READINESS_RECORDED` | JSONL (permanent) | Per-batch readiness report |
| `allowed_to_influence_live` | bool | True only when output=BLOCK |
| `activation_state` | string | One of 9 closed-enum values |
| `final_output` | string | One of 5 closed-enum output values |

---

## 3. What Sentinel does NOT provide

- Trade approvals of any kind.
- Position sizing, capital allocation.
- Exchange API connectivity.
- Direct write to Gel.Al DB, Redis, or execution stream.
- Telegram commands.
- LLM-generated text.

---

## 4. Output set (closed — unchanged from V9)

`{WAIT, BLOCK, MONITOR, NEED_RECALL, NO_ACTION}`

---

## 5. Advisory discipline

Gel.Al's risk engine, running in a separate process, may interpret
a `BLOCK` signal as a brake.  Sentinel places no obligation on Gel.Al
to act on any advisory.  Sentinel does not track Gel.Al's response.

---

## 6. Evidence gate contract

Before activation, Gel.Al operator must supply a fully populated
`EvidenceGateInput` with all 7 mandatory windows satisfied, including
the two 90-day windows.  Sentinel refuses to report `AGI_V1_READY`
without this evidence.

---

## 7. Human approval contract

For every `live_impact_possible=True` request, a valid
`HumanApprovalRecord` must be injected into the governance context.
Sentinel never auto-approves.

---

## 8. Transport

Transport of Sentinel's advisory output to Gel.Al is the operator's
responsibility.  V10 does not implement a Gel.Al write client.
