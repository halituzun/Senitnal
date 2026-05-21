# 0025 — V12 Deep Historical Intelligence + Reaction Memory — Closure Review

**Date:** 2026-05-21  
**Phase:** V12  
**Verdict:** **GREEN**

---

## 1. Status

`GREEN` — V12 introduces the historical reaction-memory layer.
Reaction memory is evidence only; it never authorises an action.

## 2. Data sources

- `services/intelligence_adapters/historical_data_adapter/` defines
  `HistoricalDataSource` enum (9 sources), `HistoricalDatasetManifest`
  (with sha256 checksum), `HistoricalEventRecord`,
  `HistoricalMarketReactionRecord`.
- Concrete loaders are deferred; the manifest interface is in place
  so cross-source archives can be registered.

## 3. Event taxonomy

- `HistoricalEventFamily` — 20-value closed enum (macro CPI/FOMC/NFP,
  rate decisions, DXY/oil/gold shocks, war/regulatory/exchange-outage/
  ETF/hack/whale/liquidation, social panic/euphoria, funding
  dislocation, stablecoin depeg, unknown).
- `ReactionWindow` — 7-value closed enum (1m, 5m, 15m, 1h, 4h, 1d, 3d).
- `MarketReactionMeasurement` — 14 reaction fields + confidence.

## 4. Reaction memory

- `ReactionMemoryRecord` frozen Pydantic record.
- `usable_for_live=True` requires:
  - `sample_count >= 5`
  - `contradiction_count / sample_count <= 0.4`
  - record fresh (not stale beyond 30 days)
- Validator rejects violating combinations at construction time.
- `InMemoryReactionMemoryStore` provides `by_family` and
  `usable_records(now_ms=...)` accessors.

## 5. Historical similarity

- `evaluate_historical_similarity` deterministic, scored against
  event + regime signature hashes.
- Low-sample-count patterns clamped to half similarity score.
- Missing matches return zero score + warning.

## 6. Backtest / replay integration

- `aggregate_records` returns evidence summary per event family:
  sample count, mean BTC return, failure rate (bounded), stale rate,
  mean volatility, mean confidence.
- Pure helper; no execution path.

## 7. Live usage discipline

- Reaction memory is evidence, never action.
- Low-sample / high-contradiction / stale records cannot raise live
  conviction.
- V11 fusion result still has `historical_similarity_score` field
  (default 0.0); operators can populate it from the V12 similarity
  engine before passing to conviction.

## 8. Safety invariants

| # | Invariant | Status |
|---|-----------|--------|
| 1 | usable_for_live requires sample threshold | GREEN |
| 2 | usable_for_live requires low contradiction | GREEN |
| 3 | stale records filtered from usable set | GREEN |
| 4 | reaction memory is evidence, not command | GREEN |
| 5 | no execution fields on reaction records | GREEN |
| 6 | low-sample patterns clamped in similarity | GREEN |
| 7 | no network imports in V12 sentinel modules | GREEN |
| 8 | V11 invariants preserved | GREEN |

## 9. Local sweep

```
ruff check .            All checks passed
pyright                 0 errors / 0 warnings
pytest -q               1720 passed
```

## 10. Deferred to V13

- Strategy lifecycle state machine
- Portfolio allocation
- Execution quality feedback
- Daily/weekly review automation

## 11. Deferred to V14

- Panel
- Adapter Hub UI
- sentinel.gel.al deployment
