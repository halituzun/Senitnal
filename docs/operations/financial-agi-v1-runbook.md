# Financial AGI v1 — Operations Runbook

**Version:** V10  
**Date:** 2026-05-20  
**Status:** ACTIVE

---

## 1. Overview

Sentinel Financial AGI v1 is a closed-output advisory system.  It
synthesises shadow, paper, canary and limited-live governance signals
into a unified evaluation result.  Sentinel never executes trades,
never writes to Gel.Al, and never generates `ApprovedActionIntent`.

---

## 2. Production activation pre-requisites

All of the following must be GREEN before activating production:

| Requirement | Minimum |
|---|---|
| Shadow observation evidence | 30 days |
| Paper co-pilot evidence | 30 days |
| Canary micro-live veto evidence | 30 days |
| Limited-live governance evidence | **90 days** |
| Incident-free window | **90 days** |
| Hash-chain integrity | 100% |
| Policy stability | Confirmed |

**If any 90-day window is missing → activation BLOCKED
(`RELEASED_BUT_NOT_ACTIVATED`).**

---

## 3. Normal operating cycle

1. Gel.Al shadow event arrives via local JSONL file.
2. `LiveGovernanceRequest` is constructed by operator (no automated
   construction from raw market data).
3. `run_financial_agi_file` is called with:
   - `--input` path to governance request fixture
   - `--ledger` path to persistent JSONL ledger
   - `--now-ms` current epoch milliseconds
4. `FINANCIAL_AGI_V1_EVALUATED` permanent audit event is emitted per
   request.
5. `FINANCIAL_AGI_READINESS_RECORDED` permanent audit event is emitted
   once per batch.
6. CLI exit code:
   - `0` — normal (hash chain valid, no safety flag violations)
   - `1` — load/schema error
   - `2` — hash chain invalid
   - `3` — safety flag violation (NEVER expected; investigate immediately)

---

## 4. Monitoring

- Hash chain: `ledger.verify()` must be `True` after every batch.
- Safety flags: `any_creates_action`, `any_writes_external`,
  `any_approves_trade`, `any_no_veto_is_approval`,
  `any_monitor_is_approval` must all be `False`.
- Readiness report status: target `GREEN` for activated instances.

---

## 5. Dry-run smoke test

```bash
uv run python -m sentinel.runtime.financial_agi \
  --input tests/fixtures/agi/benign_agi.jsonl \
  --ledger /tmp/agi-smoke.jsonl \
  --now-ms 1700000001000
```

Expected:  `exit 0`, `hash_chain_valid=True`,
`readiness_status=RELEASED_NOT_ACTIVATED` (CLI supplies empty evidence gate).

---

## 6. Key invariants (enforced by type system + tests)

1. `direct_execution=Literal[False]` — cannot be overridden.
2. `exchange_imports=Literal[False]` — cannot be overridden.
3. `llm_imports=Literal[False]` — cannot be overridden.
4. `gelal_write_path=Literal[False]` — cannot be overridden.
5. `approved_action_intent_generation=Literal[False]` — cannot be overridden.
6. `allowed_to_influence_live=True` only when `effective_output==BLOCK`.
7. Missing 90-day evidence → `RELEASED_BUT_NOT_ACTIVATED`.
