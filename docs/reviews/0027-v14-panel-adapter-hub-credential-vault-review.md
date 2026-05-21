# 0027 — V14 Panel, Adapter Hub & Credential Vault — Closure Review

**Date:** 2026-05-21  
**Phase:** V14  
**Verdict:** **ACTIVE_LIVE_PORTFOLIO**

---

## 1. Status

`ACTIVE_LIVE_PORTFOLIO`.  V14 delivers the three components deferred from
V13: a read-only **Panel** for portfolio observability, an **Adapter Hub**
for intelligence adapter health aggregation, and a **Credential Vault**
schema layer for secure credential reference management.
**Sentinel still does not execute**; Gel.Al owns execution.
No web UI was introduced — all outputs are frozen Pydantic models
(JSON-serialisable).

## 2. Panel snapshot (`sentinel/panel/snapshot.py`)

- `PanelStrategyRow` — per-strategy view: lifecycle state, allocated budget,
  edge/risk/confidence scores, enabled flag, quality score.
- `PanelSnapshot` — top-level read-only snapshot: portfolio id,
  captured_at_ms, approved capital, total allocated, active/paused counts,
  strategy rows, linked daily/weekly report ids.
- `build_panel_snapshot()` — pure constructor; enforces count consistency
  via model validator.
- Quality scores clamped to [0.0, 1.0]; missing scores default to 1.0.

## 3. Adapter Hub (`sentinel/panel/adapter_hub.py`)

- `AdapterSignalStatus` — per-adapter view: adapter_id, source_family,
  last_seen_ms, trust_band, is_fresh, is_healthy.
- `AdapterHubStatus` — hub aggregate: hub_id, captured_at_ms, adapters
  tuple, healthy_count, stale_count, degraded flag.
- `build_adapter_hub_status()` — re-evaluates freshness against
  captured_at_ms + freshness_horizon_ms; REVOKED/QUARANTINED trust bands
  always unhealthy; None last_seen → stale.
- `healthy_count + stale_count ≤ len(adapters)` enforced by validator.

## 4. Credential Vault (`sentinel/panel/credential_vault.py`)

- `CredentialKind` — closed enum: api_key, hmac_secret, bearer_token,
  oauth2_client.
- `CredentialReference` — reference only: ref_id, kind, adapter_id, label,
  created_at_ms, expires_at_ms, is_active. No actual secret stored;
  label validator rejects raw secret material.
- `CredentialVaultConfig` — vault_id, rotation_reminder_days,
  `allow_expired: Literal[False]` (always False), credentials tuple with
  duplicate ref_id guard.
- `is_credential_valid(ref, now_ms)` — active + not expired predicate.
- `list_expiring_soon(config, now_ms, horizon_days)` — returns refs
  expiring within horizon, excludes inactive and already-expired.

## 5. Safety invariants

| # | Invariant | Status |
|---|-----------|--------|
| 1 | PanelSnapshot is frozen (no mutation) | GREEN |
| 2 | No actual secrets in CredentialReference | GREEN |
| 3 | allow_expired is always Literal[False] | GREEN |
| 4 | healthy_count + stale_count ≤ len(adapters) | GREEN |
| 5 | build_panel_snapshot has no side-effects | GREEN |
| 6 | creates_action / writes_external / approves_trade absent from panel | GREEN |
| 7 | No exchange / LLM / network import in sentinel/panel/ | GREEN |
| 8 | V1-V13 invariants preserved | GREEN |

## 6. Local sweep

```
ruff check .            All checks passed
pyright                 0 errors / 0 warnings
pytest -q               1789 passed
```

## 7. Deferred to V15

- Deployment config (sentinel.gel.al)
- Panel credential vault backend (actual secret store integration)
- Adapter Hub UI
- Panel live streaming / WebSocket
