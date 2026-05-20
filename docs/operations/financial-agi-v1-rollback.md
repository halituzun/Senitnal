# Financial AGI v1 — Rollback Procedures

**Version:** V10  
**Date:** 2026-05-20

---

## When to roll back

- Exit code 3 (safety flag violation) — roll back immediately.
- Exit code 2 (hash chain invalid) — roll back after preserving artifacts.
- Activation state regressed to `PRODUCTION_BLOCKED` without expected cause.
- Governance consensus producing unexpected block floods.

---

## Rollback steps

### 1. Stop batch runner

Stop any running `sentinel.runtime.financial_agi` process.

### 2. Preserve current ledger

```bash
cp /path/to/agi-ledger.jsonl /path/to/agi-ledger.jsonl.$(date +%s).bak
```

### 3. Revert to previous V9 governance runner

```bash
uv run python -m sentinel.runtime.live_governance \
  --input <input.jsonl> \
  --ledger <ledger.jsonl> \
  --now-ms <timestamp>
```

V9 remains intact and unmodified by V10.

### 4. Root-cause analysis

Before re-enabling V10, identify:
- Which safety invariant was violated (if exit 3).
- Which module introduced the regression.
- Whether tests cover the scenario.

### 5. Re-enable after review

Only re-enable V10 after:
- Root cause identified and fixed.
- All 1641+ tests passing.
- ruff + pyright clean.
- Hash chain integrity confirmed.

---

## V10 does not modify V1-V9 code paths

Rollback to V9 (or any earlier version) is always safe because V10
adds only new modules under `sentinel/agi/` and one new CLI.  No
existing V1-V9 module is modified by V10.
