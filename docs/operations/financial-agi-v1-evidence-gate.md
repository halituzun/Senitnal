# Financial AGI v1 — Evidence Gate Reference

**Version:** V10  
**Date:** 2026-05-20

---

## Purpose

The evidence gate validates that all mandatory observation windows
have been satisfied before a production activation state is granted.
It is the primary guard against premature activation.

---

## Mandatory windows

| Window kind | Minimum days | Description |
|---|---|---|
| `shadow_30d` | 30 | Gel.Al shadow observation |
| `paper_30d` | 30 | Paper co-pilot decisions |
| `canary_30d` | 30 | Canary micro-live veto |
| `limited_live_90d` | **90** | Limited-live governance (hard requirement) |
| `incident_free_90d` | **90** | No safety incidents (hard requirement) |
| `hash_chain_integrity` | N/A | Ledger hash chain verified |
| `policy_stability` | N/A | Active policy unchanged |

---

## Decision rules

| Condition | Decision | Activation state |
|---|---|---|
| Any 90-day window missing | `insufficient_evidence` | `RELEASED_BUT_NOT_ACTIVATED` |
| Any mandatory window missing | `insufficient_evidence` | `RELEASED_BUT_NOT_ACTIVATED` |
| Any mandatory window unsatisfied | `blocked` | `PRODUCTION_BLOCKED` |
| All 7 windows satisfied | `pass_green` | `AGI_V1_READY` (if governance also passes) |

---

## Constructing the gate input

```python
from sentinel import EvidenceGateInput, EvidenceWindow, EvidenceWindowKind

gate_input = EvidenceGateInput(
    evaluation_id="my-eval-001",
    windows=(
        EvidenceWindow(kind=EvidenceWindowKind.SHADOW_30D, satisfied=True, days_observed=45),
        EvidenceWindow(kind=EvidenceWindowKind.PAPER_30D, satisfied=True, days_observed=35),
        EvidenceWindow(kind=EvidenceWindowKind.CANARY_30D, satisfied=True, days_observed=32),
        EvidenceWindow(kind=EvidenceWindowKind.LIMITED_LIVE_90D, satisfied=True, days_observed=92),
        EvidenceWindow(kind=EvidenceWindowKind.INCIDENT_FREE_90D, satisfied=True, days_observed=92),
        EvidenceWindow(kind=EvidenceWindowKind.HASH_CHAIN_INTEGRITY, satisfied=True, days_observed=92),
        EvidenceWindow(kind=EvidenceWindowKind.POLICY_STABILITY, satisfied=True, days_observed=92),
    ),
    evaluated_at_ms=1_700_000_000_000,
)
```

---

## Safety invariants

- Gate is read-only; it never mutates state.
- `direct_execution=False` and
  `approved_action_intent_generation=False` are pinned in the result.
- Gate result is immutable (Pydantic `frozen=True`).
