# Intelligence Adapter Services

External limb adapters.  **Network/API client imports are allowed here.**
Sentinel core under `sentinel/` may not import these modules directly.

Each adapter:
- Reads raw data from its source (TAAPI, exchange archives, Gel.Al metrics,
  macro/news/social/commodity feeds).
- Normalizes raw data into Sentinel-facing snapshots (see
  `sentinel/intelligence/schemas.py`).
- Writes normalized snapshots to a local JSONL spool path under
  `data/intelligence/<adapter>/*.jsonl`.
- Never calls Sentinel core API directly.
- Never emits trade commands.

## Adapters

- `taapi_adapter/` — TAAPI technical indicator fetch
- `exchange_history_adapter/` — exchange historical OHLCV/trade fetch
- `gelal_metrics_adapter/` — Gel.Al metrics read (read-only SQL)
- `macro_adapter/` — macro calendar (CPI/FOMC/NFP/rate decisions)
- `news_adapter/` — news event ingestion
- `social_x_adapter/` — X/Twitter / social platform ingestion
- `commodity_adapter/` — DXY / oil / gold / rates / indices
- `historical_data_adapter/` — V12 cross-source historical loader

## Constitutional discipline

- Secrets (`TAAPI_API_KEY`, exchange API keys) MUST NOT appear in logs.
- Withdrawal permission MUST NEVER be requested.
- Adapter failures are health events; they do not break Sentinel core.
