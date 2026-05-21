# 0012 — V11 Real Live + Multi-Source Intelligence — Build Plan

**Date:** 2026-05-21  
**Phase:** V11

---

## 1. Purpose

V11 lifts Sentinel from closed-output advisory to a multi-source
financial intelligence frame.  Sentinel core remains a closed-output
advisory system; live execution still goes through Gel.Al only.
V11 adds:

- Multi-source observation schemas (technical / microstructure / macro
  / news / social / commodity).
- SignalFusion engine that aggregates non-execution evidence.
- LiveConvictionScore with NetEdgeGate.
- Halit-approved live capital model (no hardcoded TRY cap).
- TAAPI technical indicator adapter (external limb).
- Gel.Al metrics read adapter (external limb).
- Macro/news/social/commodity adapter skeletons (external limbs).

## 2. Non-goals

- No panel.
- No Node/Vue UI.
- No AG Grid.
- No `sentinel.gel.al` deployment.
- No exchange order generation.
- No LLM imports inside `sentinel/`.

## 3. Boundary

- `sentinel/`              — pure core, **no network/SDK imports allowed**
- `sentinel/intelligence/` — core-adjacent: pure schemas / fusion / conviction
- `services/intelligence_adapters/` — external limbs: network allowed,
   normalize raw data into Sentinel-facing snapshots

## 4. Schemas (sentinel/intelligence/schemas.py)

- `SourceFamily` closed enum
- `MultiSourceObservation` (frozen, strict, no execution fields)
- `TechnicalIndicatorSnapshot`
- `MarketMicrostructureSnapshot`
- `MacroEventSnapshot`
- `NewsEventSnapshot`
- `SocialSignalSnapshot`
- `CommodityMacroSnapshot`
- `GelAlMetricsObservation`

All schemas: `extra='forbid'`, `frozen=True`, scores bounded `[0,1]`,
no API secrets, no order/execution fields, raw symbol only as
provenance hash.

## 5. Fusion engine (sentinel/intelligence/fusion.py)

- `SignalFusionInput` (collection of snapshots)
- `SignalFusionResult` (10 pressure/confidence scores + reasons)
- `compute_signal_fusion` deterministic, source-agreement weighted,
  stale dampened, contradiction-aware.

## 6. Conviction (sentinel/intelligence/conviction.py)

- `LiveConvictionInput`
- `LiveConvictionResult` with actionability band
  (`blocked | watch | candidate | live_candidate`)
- `evaluate_live_conviction` — fail-closed.

## 7. NetEdgeGate (sentinel/intelligence/net_edge.py)

- `NetEdgeBreakdown` (gross, fee, slip, spread, latency_decay,
  partial_fill_risk, hedge_risk, net)
- `compute_net_edge` enforces `net = gross - sum(costs)` and rejects
  consistency violations.

## 8. Live activation (sentinel/intelligence/live_activation.py)

- `LiveBudgetMode` enum
- `LiveCapitalModel` config (FIXED_TRY | PERCENT_AVAILABLE | ALL_AVAILABLE_BALANCE)
- `LiveActivationStatus` enum
- `evaluate_live_activation` returns one of the documented statuses;
  removes 100 TRY hardcoded cap.

## 9. Adapters (services/intelligence_adapters/*)

- `taapi_adapter/` — config-driven; secret never logged
- `gelal_metrics_adapter/` — read-only metrics queries
- `macro_adapter/`, `news_adapter/`, `social_x_adapter/`,
  `commodity_adapter/` — skeleton stubs documenting interface;
  network imports allowed.

## 10. Tests

- All schemas reject execution / API-secret / order fields
- Fusion bounded, deterministic, contradiction-aware
- Conviction blocked on negative net edge / stale / unhealthy
- NetEdgeGate rejects gross >= net
- Live activation honors approved capital config
- Forbidden import grep: clean across `sentinel/`

## 11. Done definition

- V11 review doc written
- Public API extended additively
- All 1641 prior tests still pass
- ruff / pyright / pytest GREEN

## 12. Deferred

- V12 historical reaction memory
- V13 production scaling
- V14 panel
