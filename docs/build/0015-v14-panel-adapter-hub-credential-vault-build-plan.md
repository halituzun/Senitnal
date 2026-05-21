# 0015 — V14 Panel, Adapter Hub & Credential Vault — Build Plan

**Date:** 2026-05-21
**Phase:** V14
**Status:** PLANNED

---

## Goal

Implement the three components deferred from V13: a read-only **Panel**
for portfolio observability, an **Adapter Hub** for aggregating intelligence
adapter health, and a **Credential Vault** schema layer for secure reference
management.  Sentinel still does not execute; Gel.Al owns execution.  No web
UI is introduced — all outputs are Pydantic models (JSON-serialisable).

---

## Scope

### 1. Panel snapshot (`sentinel/panel/snapshot.py`)

- `PanelStrategyRow` — per-strategy view: lifecycle state, budget, scores,
  quality, enabled flag.
- `PanelSnapshot` — top-level snapshot: portfolio id, captured_at_ms,
  total allocated, active/paused counts, strategy rows, linked report ids.
- `build_panel_snapshot(snapshot_id, captured_at_ms, portfolio_config,
  allocations, daily_report?, weekly_report?, quality_scores?)` — pure
  constructor; no I/O.

### 2. Adapter Hub (`sentinel/panel/adapter_hub.py`)

- `AdapterSignalStatus` — per-adapter view: adapter_id, source_family,
  last_seen_ms, trust_band, is_fresh (staleness within a configurable
  horizon), is_healthy.
- `AdapterHubStatus` — hub-level aggregate: hub_id, captured_at_ms,
  adapters tuple, healthy_count, stale_count, degraded flag.
- `build_adapter_hub_status(hub_id, captured_at_ms, adapter_statuses,
  freshness_horizon_ms?)` — pure constructor.

### 3. Credential Vault (`sentinel/panel/credential_vault.py`)

- `CredentialKind` — closed enum: api_key, hmac_secret, bearer_token,
  oauth2_client.
- `CredentialReference` — reference only: ref_id, kind, adapter_id, label,
  created_at_ms, expires_at_ms, is_active. **No actual secret stored.**
- `CredentialVaultConfig` — vault_id, rotation_reminder_days, allow_expired
  (Literal[False]), credentials tuple.
- `is_credential_valid(ref, now_ms)` — predicate: active + not expired.
- `list_expiring_soon(config, now_ms, horizon_days)` — returns refs
  expiring within horizon.

### 4. Panel `__init__.py`

Re-exports all public symbols from the three submodules.

---

## Safety invariants

| # | Invariant |
|---|-----------|
| 1 | PanelSnapshot is read-only (frozen Pydantic, no mutation) |
| 2 | No actual secrets in CredentialReference (validator) |
| 3 | allow_expired is always Literal[False] in CredentialVaultConfig |
| 4 | AdapterHubStatus healthy_count + stale_count <= len(adapters) |
| 5 | build_panel_snapshot produces no side-effects |
| 6 | creates_action / writes_external / approves_trade absent from panel |
| 7 | No exchange / LLM / network import in sentinel/panel/ |
| 8 | V1-V13 invariants preserved |

---

## File plan

```
sentinel/panel/__init__.py
sentinel/panel/snapshot.py
sentinel/panel/adapter_hub.py
sentinel/panel/credential_vault.py
tests/panel/__init__.py
tests/panel/test_snapshot.py
tests/panel/test_adapter_hub.py
tests/panel/test_credential_vault.py
docs/build/0015-v14-panel-adapter-hub-credential-vault-build-plan.md
docs/reviews/0027-v14-panel-adapter-hub-credential-vault-review.md
```

---

## Out of scope

- Web UI / HTTP endpoints
- Real secret storage / key management backend
- Panel live streaming / WebSocket
- Deployment config (deferred to V15)
