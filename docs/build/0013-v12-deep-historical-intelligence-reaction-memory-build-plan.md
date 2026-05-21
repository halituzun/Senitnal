# 0013 — V12 Deep Historical Intelligence + Reaction Memory — Build Plan

**Date:** 2026-05-21  
**Phase:** V12

---

## 1. Purpose

V12 teaches Sentinel how markets have reacted to past technical /
macro / news / social / commodity events.  Reaction memory becomes a
new evidence source feeding V11 fusion and conviction; it does not
itself authorise any action.

## 2. Non-goals

- No production scaling (V13)
- No panel (V14)
- No new exchange execution

## 3. Modules

- `sentinel/intelligence/reaction_taxonomy.py` — closed-set event &
  reaction-window taxonomy.
- `sentinel/intelligence/reaction_memory.py` — frozen Pydantic records
  + in-memory store + selector.
- `sentinel/intelligence/historical_similarity.py` — deterministic
  similarity engine matching current state to ReactionMemory.
- `sentinel/intelligence/historical_backtest.py` — pure helper that
  aggregates historical evidence by event family / regime.
- `services/intelligence_adapters/historical_data_adapter/` —
  manifest + checksum schemas for cross-source archives.

## 4. Reaction taxonomy

- `HistoricalEventFamily` (20-value closed enum)
- `ReactionWindow` (7-value closed enum: 1m, 5m, 15m, 1h, 4h, 1d, 3d)
- `MarketReactionMeasurement` (frozen, bounded, 14 reaction fields)

## 5. Reaction memory

- `ReactionMemoryRecord`, `ReactionPattern`
- `usable_for_live` flag — `True` only when sample_count ≥ threshold
  AND contradiction ≤ threshold AND not stale.

## 6. Historical similarity

- Input: current fusion + macro/news context + memory store.
- Output: `historical_similarity_score`, matched pattern refs,
  expected reaction band, risk warnings.
- Low sample-count patterns clamped to low confidence.

## 7. Backtest helper

- Aggregates historical evidence by event family / regime.
- Returns edge / failure / staleness distributions (evidence only).
- Counterfactual remains synthetic — never live proof.

## 8. Tests

- Taxonomy: 20 event families, 7 reaction windows
- Reaction memory: usable_for_live gating, contradiction shrinks confidence
- Historical similarity: low-sample patterns clamped, mismatch warns
- Backtest aggregator deterministic
- Boundary: no network imports added to `sentinel/intelligence/`

## 9. Deferred

- V13 strategy lifecycle + portfolio
- V14 panel
