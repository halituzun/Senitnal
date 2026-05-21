# 0014 — V13 Production Live Scaling + Strategy Portfolio — Build Plan

**Date:** 2026-05-21  
**Phase:** V13

---

## 1. Purpose

V13 lifts the system from single-opportunity live waiting to a
production strategy portfolio with explicit lifecycle, allocation,
execution-quality feedback, and daily/weekly review automation.
**Sentinel still does not execute** — Gel.Al executes.

## 2. Non-goals

- No panel (V14)
- No exchange order placement from Sentinel core
- No autonomous capital expansion beyond Halit-approved config

## 3. Modules

```
sentinel/production/
    __init__.py
    strategy_lifecycle.py
    portfolio.py
    execution_quality.py
    review.py
```

## 4. Strategy lifecycle

- `StrategyLifecycleState` (10-value closed enum):
  `research`, `historical_validated`, `paper`, `shadow`, `canary`,
  `limited_live`, `active_live`, `paused`, `retired`, `rollback_required`.
- `transition(current, target)` enforces directed-graph rules.  Bad
  transitions raise `ValueError`.
- `bad_order → rollback_required`, `stale/finality_unknown →
  rollback_required`.
- `research → active_live` cannot skip phases.

## 5. Portfolio

- `StrategyPortfolioConfig` — Halit-approved budgets, max correlation,
  max strategy exposure, max venue exposure, kill_switch_required.
- `StrategyAllocation` — per-strategy budget, max entry, max trades,
  current edge / risk / confidence, enabled flag.
- Validators reject negative budgets, missing kill-switch flag, and
  state below `limited_live` with non-zero allocation.

## 6. Production conviction

- `LiveProductionDecisionInput` aggregates: V11 fusion + V12 reaction
  memory similarity + lifecycle state + allocation + execution
  quality + market regime + exchange health + net edge.
- `LiveProductionDecision` returns `system_output ∈ closed SystemOutput`,
  `actionability_band`, `edge_score`, `risk_score`, `allowed_budget_ref`,
  `block_reasons`.

## 7. Execution quality feedback

- `ExecutionQualityRecord` tracks expected vs realized edge, fee,
  slippage, latency, partial fill, cancel success, finality, rejects,
  bad orders, venue & strategy quality scores.
- `update_strategy_quality_from_record` produces a new quality score
  for the strategy (deterministic).

## 8. Review automation

- `DailyProductionReport` and `WeeklyProductionReport` Pydantic models.
- `build_daily_report` and `build_weekly_report` aggregate strategy
  metrics. No panel — reports are JSON / docs / logs.

## 9. Gel.Al integration

- Read-only.  No hidden Redis or DB write.
- Strategy state changes are local to Sentinel and emitted as audit
  events (existing observer ledger path).

## 10. Done definition

- V13 review doc
- All V11 + V12 invariants preserved
- 1720 + ~50 new tests passing
- ruff / pyright / pytest GREEN
- No panel code

## 11. Deferred to V14

- Panel, Adapter Hub UI, sentinel.gel.al deployment, credential vault
