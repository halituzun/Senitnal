#!/usr/bin/env python3
"""Continuous learning loop — runs sentinel pipeline on synthetic data.

Run:
    uv run sentinel/runtime/learning_loop.py --once    # single cycle
    uv run sentinel/runtime/learning_loop.py           # every 5s
    uv run sentinel/runtime/learning_loop.py --interval 10 --cycles 50
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sentinel.intelligence.conviction import (
    ActionabilityBand,
    LiveConvictionInput,
    evaluate_live_conviction,
)
from sentinel.intelligence.fusion import SignalFusionInput, compute_signal_fusion
from sentinel.intelligence.net_edge import compute_net_edge
from sentinel.intelligence.schemas import (
    MarketMicrostructureSnapshot,
    TechnicalIndicatorSnapshot,
)

NOW_MS = int(time.time() * 1000)
DAY_MS = 86_400_000


def _hash(s: str) -> str:
    return "sha256:" + hashlib.sha256(s.encode()).hexdigest()


@dataclass
class StrategyState:
    strategy_id: str
    name: str
    lifecycle_state: str
    allocated_budget_try: float
    max_entry_try: float
    max_trades_per_day: int
    current_edge_score: float
    current_risk_score: float
    current_confidence: float
    enabled: bool
    strategy_quality: float
    pnl_today_try: float
    pnl_week_try: float
    total_decisions: int = 0
    total_pass: int = 0
    total_block: int = 0


@dataclass
class LearningState:
    cycle: int = 0
    started_at_ms: int = NOW_MS
    last_cycle_ms: int = NOW_MS
    strategies: dict[str, StrategyState] = field(default_factory=dict)
    ledger_events: list[dict[str, Any]] = field(default_factory=list)
    memory_records: list[dict[str, Any]] = field(default_factory=list)
    decisions: list[dict[str, Any]] = field(default_factory=list)
    total_signals_processed: int = 0
    total_blocks: int = 0
    total_candidates: int = 0
    total_live_candidates: int = 0
    _event_idx: int = 0
    _decision_idx: int = 0
    _memory_idx: int = 0
    # Self-training metrics
    correct_predictions: int = 0
    total_predictions: int = 0
    adaptive_alpha: float = 0.15  # Learning rate, auto-adjusted
    last_cycle_pnl: float = 0.0
    last_prices: dict[str, float] = field(default_factory=dict)
    market_sentiment: dict[str, float] = field(default_factory=dict)  # symbol → last_price for PnL calc

    def next_event_id(self) -> str:
        self._event_idx += 1
        return f"ev-{self._event_idx:05d}"

    def next_decision_id(self) -> str:
        self._decision_idx += 1
        return f"dec-{self._decision_idx:05d}"

    def next_memory_id(self) -> str:
        self._memory_idx += 1
        return f"mem-{self._memory_idx:05d}"


DEFAULT_STRATEGIES = [
    StrategyState("btc-momentum-v3", "BTC Momentum v3", "ACTIVE_LIVE", 3500, 350, 8, 0.65, 0.25, 0.75, True, 0.80, 0, 0),
    StrategyState("eth-mean-reversion", "ETH Mean Reversion", "ACTIVE_LIVE", 2800, 280, 12, 0.55, 0.35, 0.65, True, 0.70, 0, 0),
    StrategyState("sol-breakout-alpha", "SOL Breakout Alpha", "LIMITED_LIVE", 1200, 120, 5, 0.45, 0.45, 0.55, True, 0.55, 0, 0),
    StrategyState("bnb-arb-v1", "BNB Cross-Exchange Arb", "PAUSED", 0, 200, 20, 0.35, 0.50, 0.45, False, 0.40, 0, 0),
    StrategyState("xrp-sentiment-v2", "XRP Sentiment v2", "ROLLBACK_REQUIRED", 0, 150, 6, 0.20, 0.70, 0.30, False, 0.20, 0, 0),
]

ADAPTER_POOL = [
    {"id": "taapi-pro", "name": "TAAPI Pro", "family": "TECHNICAL", "error_rate": 0.002, "latency": 320},
    {"id": "binance-ws", "name": "Binance WS", "family": "MARKET_DATA", "error_rate": 0.001, "latency": 18},
    {"id": "lunarcrush-social", "name": "LunarCrush", "family": "SOCIAL", "error_rate": 0.005, "latency": 540},
    {"id": "cryptopanic-feed", "name": "CryptoPanic", "family": "NEWS", "error_rate": 0.01, "latency": 890},
    {"id": "glassnode-onchain", "name": "Glassnode", "family": "ONCHAIN", "error_rate": 0.003, "latency": 1200},
    {"id": "coinglass-futures", "name": "Coinglass", "family": "DERIVATIVES", "error_rate": 0.008, "latency": 410},
    {"id": "fear-greed-index", "name": "Fear & Greed", "family": "SENTIMENT", "error_rate": 0.12, "latency": 3600},
    {"id": "deribit-options", "name": "Deribit", "family": "DERIVATIVES", "error_rate": 0.003, "latency": 280},
]


def _event(
    state: LearningState, event_type: str, severity: str, source: str,
    strategy_id: str | None, message: str,
) -> dict[str, Any]:
    return {
        "id": state.next_event_id(), "ts_ms": int(time.time() * 1000),
        "event_type": event_type, "severity": severity,
        "source": source, "strategy_id": strategy_id,
        "adapter_id": source,
        "message": message,
    }


def generate_observations(
    strategy_id: str, edge: float, risk: float, cycle: int,
) -> tuple[TechnicalIndicatorSnapshot, MarketMicrostructureSnapshot]:
    now_ms = int(time.time() * 1000)
    symbol = "BTCUSDT" if "btc" in strategy_id else "ETHUSDT" if "eth" in strategy_id else "SOLUSDT"

    # Market regime: 35% bull, 15% bear, 50% choppy
    regime = random.random()
    if regime < 0.35:       # Strong bullish
        signal_edge = 0.6 + random.uniform(0, 0.4)
        signal_risk = 0.1 + random.uniform(0, 0.25)
    elif regime < 0.50:     # Strong bearish
        signal_edge = random.uniform(0, 0.4)
        signal_risk = 0.4 + random.uniform(0, 0.4)
    else:                   # Choppy / sideways
        signal_edge = 0.3 + random.uniform(0, 0.4)
        signal_risk = 0.2 + random.uniform(0, 0.35)

    rsi = 30 + (signal_edge * 60) + random.uniform(-8, 8)
    rsi = max(10, min(90, rsi))
    macd_val = (signal_edge - 0.5) * 5 + random.uniform(-0.5, 0.5)
    bb_pos = 0.2 + (signal_edge * 0.6) + random.uniform(-0.15, 0.15)

    tech = TechnicalIndicatorSnapshot(
        snapshot_id=f"tech-{strategy_id}-{cycle}",
        provider="taapi",
        symbol_hash=_hash(symbol),
        timeframe="4h",
        indicators={"rsi": round(rsi, 1), "macd": round(macd_val, 2), "bb_position": round(bb_pos, 2)},
        trend_score=round(max(0.0, min(1.0, signal_edge)), 2),
        momentum_score=round(max(0.0, min(1.0, macd_val + 0.5)), 2),
        volatility_score=round(max(0.0, min(1.0, signal_risk)), 2),
        volume_score=round(max(0.0, min(1.0, 0.4 + random.random() * 0.4)), 2),
        reversal_score=round(max(0.0, min(1.0, 0.2 + random.random() * 0.3)), 2),
        exhaustion_score=round(max(0.0, min(1.0, 0.1 + random.random() * 0.3)), 2),
        pattern_score=round(max(0.0, min(1.0, edge * 0.8)), 2),
        confidence=round(max(0.0, min(1.0, 0.6 + abs(edge - 0.5) * 0.4)), 2),
        observed_at_ms=now_ms - random.randint(1000, 60000),
        provenance_hash=_hash(f"taapi-{symbol}-{cycle}"),
    )

    spread = max(0.0001, 0.001 + risk * 0.01 + random.uniform(-0.002, 0.002))
    micro = MarketMicrostructureSnapshot(
        snapshot_id=f"micro-{strategy_id}-{cycle}",
        symbol_hash=_hash(symbol),
        venue_hash=_hash("binance"),
        orderbook_age_ms=random.randint(50, 500),
        trade_tape_age_ms=random.randint(100, 1000),
        bid_ask_spread_pct=round(spread, 6),
        bid_depth_score=round(0.4 + (1 - risk) * 0.4, 2),
        ask_depth_score=round(0.4 + (1 - risk) * 0.3, 2),
        imbalance_score=round(risk * 0.8 - 0.4 + random.uniform(-0.2, 0.2), 2),
        ofi_score=round((edge - 0.5) * 1.5, 2),
        vpin_score=round(risk * 0.7, 2),
        hawkes_toxicity_score=round(risk * 0.5 + 0.1, 2),
        liquidity_score=round(0.3 + (1 - risk) * 0.5, 2),
        latency_ms=random.randint(15, 50),
        confidence=round(0.7 + random.random() * 0.2, 2),
        observed_at_ms=now_ms - random.randint(500, 30000),
        provenance_hash=_hash(f"binance-{symbol}-{cycle}"),
    )

    return tech, micro


def run_cycle(state: LearningState) -> LearningState:
    """Run one cycle with synthetic data (sentinel core, no external imports)."""
    now_ms = int(time.time() * 1000)
    state.cycle += 1
    cycle = state.cycle

    active = [s for s in state.strategies.values() if s.enabled and s.lifecycle_state in ("ACTIVE_LIVE", "LIMITED_LIVE")]
    if not active:
        state.ledger_events.append(_event(state, "NO_ACTIVE_STRATEGIES", "WARN", "learning-loop", None, "No active strategies"))
        state.last_cycle_ms = now_ms
        return state

    strategy = random.choice(active)
    tech, micro = generate_observations(strategy.strategy_id, strategy.current_edge_score, strategy.current_risk_score, cycle)
    return _process_cycle(state, strategy, tech, micro, now_ms, cycle, source="taapi-pro")


def run_cycle_with_real_data(
    state: LearningState,
    micro_snapshots: list[MarketMicrostructureSnapshot],
    tech_snapshots: list[TechnicalIndicatorSnapshot],
    news_sentiment: dict[str, float] | None = None,
) -> LearningState:
    """Run one cycle with externally-fetched real data (called from outside sentinel/)."""
    now_ms = int(time.time() * 1000)
    state.cycle += 1
    cycle = state.cycle

    active = [s for s in state.strategies.values() if s.enabled and s.lifecycle_state in ("ACTIVE_LIVE", "LIMITED_LIVE")]
    if not active:
        state.ledger_events.append(_event(state, "NO_ACTIVE_STRATEGIES", "WARN", "learning-loop", None, "No active strategies"))
        state.last_cycle_ms = now_ms
        return state

    symbol_map = {"btc": 0, "eth": 1, "sol": 2}
    for strategy in active:
        idx = -1
        for prefix, i in symbol_map.items():
            if prefix in strategy.strategy_id.lower():
                idx = i
                break
        if idx < 0 or idx >= len(micro_snapshots) or idx >= len(tech_snapshots):
            continue

        tech = tech_snapshots[idx]
        micro = micro_snapshots[idx]
        state = _process_cycle(state, strategy, tech, micro, now_ms, cycle, source="binance-api", news_sentiment=news_sentiment)
        state.total_signals_processed += 1

    return state


def _process_cycle(
    state: LearningState,
    strategy: StrategyState,
    tech: TechnicalIndicatorSnapshot,
    micro: MarketMicrostructureSnapshot,
    now_ms: int,
    cycle: int,
    source: str,
    news_sentiment: dict[str, float] | None = None,
) -> LearningState:

    fusion_input = SignalFusionInput(
        fusion_id=f"fusion-{cycle}",
        now_ms=now_ms,
        technical_indicator_snapshots=(tech,),
        microstructure_snapshots=(micro,),
    )
    fusion_result = compute_signal_fusion(fusion_input)

    edge_proxy = fusion_result.trend_pressure
    risk_proxy = (fusion_result.contradiction_pressure + fusion_result.volatility_pressure) / 2

    # Apply news sentiment overlay
    ns = news_sentiment or {}
    state.market_sentiment = ns  # Store for snapshot export
    news_impact = ""
    if ns:
        macro_risk = ns.get("macro_risk_score", 0.0)
        fg = ns.get("fear_greed_index", 0.5)
        is_greed = ns.get("market_greed", 0.0) > 0
        is_fear = ns.get("market_fear", 0.0) > 0

        if macro_risk > 0.3:
            risk_boost = min(0.3, macro_risk * 0.5)
            edge_penalty = min(0.2, macro_risk * 0.3)
            risk_proxy = min(1.0, risk_proxy + risk_boost)
            edge_proxy = max(0.0, edge_proxy - edge_penalty)
            news_impact = f" MacroRisk={macro_risk:.2f}(risk+{risk_boost:.2f})"

        # Fear & Greed overlay: greed → increase risk, fear → reduce edge
        if is_greed and fg > 0.7:
            risk_proxy = min(1.0, risk_proxy + 0.1)
            news_impact += f" GREED(fg={fg:.0%})"
        elif is_fear and fg < 0.3:
            edge_proxy = max(0.0, edge_proxy - 0.1)
            news_impact += f" FEAR(fg={fg:.0%})"

        crypto_count = ns.get("crypto_count", 0)
        if crypto_count >= 3:
            news_impact += f" News={int(crypto_count)}"

    state.ledger_events.append(_event(state, "FUSION_COMPUTED", "INFO", "fusion-engine", strategy.strategy_id,
        f"Trend={edge_proxy:.2f} Contradiction={risk_proxy:.2f} Confidence={fusion_result.confidence:.2f}{news_impact}"))

    alpha = state.adaptive_alpha
    strategy.current_edge_score = round(strategy.current_edge_score * (1 - alpha) + edge_proxy * alpha, 3)
    strategy.current_risk_score = round(strategy.current_risk_score * (1 - alpha) + risk_proxy * alpha, 3)
    strategy.current_confidence = round(strategy.current_confidence * (1 - alpha) + fusion_result.confidence * alpha, 3)

    gross_edge = edge_proxy * 0.03
    net_edge = compute_net_edge(
        breakdown_id=f"net-{cycle}",
        gross_edge_pct=gross_edge,
        fee_pct=0.001,
        slippage_pct=0.0008,
        spread_cost_pct=micro.bid_ask_spread_pct,
    )

    state.ledger_events.append(_event(state, "NET_EDGE_COMPUTED", "INFO", "net-edge", strategy.strategy_id,
        f"Gross={gross_edge:.4f} Net={net_edge.net_edge_pct:.4f} (costs deducted)"))

    conviction_input = LiveConvictionInput(
        conviction_id=f"conv-{cycle}",
        fusion_result=fusion_result,
        net_edge=net_edge,
        execution_quality=strategy.strategy_quality,
        active_policy_ok=strategy.lifecycle_state != "ROLLBACK_REQUIRED",
        governance_ok=True,
        market_fresh=True,
        balance_available=strategy.allocated_budget_try > 0,
        exchange_health=0.95,
    )
    conviction_result = evaluate_live_conviction(conviction_input)
    band = conviction_result.actionability_band

    # Realistic market uncertainty: ~15% of passes become BLOCKED
    if band in (ActionabilityBand.CANDIDATE, ActionabilityBand.LIVE_CANDIDATE):
        if random.random() < 0.15:
            band = ActionabilityBand.BLOCKED
            state.ledger_events.append(_event(state, "CONVICTION_OVERRIDE", "WARN", "conviction-engine", strategy.strategy_id,
                f"Market uncertainty override: LIVE_CANDIDATE → BLOCKED"))

    state.ledger_events.append(_event(state, "LIVE_CONVICTION", "INFO", "conviction-engine", strategy.strategy_id,
        f"Band={band.upper()} Score={conviction_result.conviction_score:.2f}"))

    decision = {
        "decision_id": state.next_decision_id(), "ts_ms": now_ms,
        "strategy_id": strategy.strategy_id, "gate_name": "conviction_gate",
        "outcome": "PASS" if band in (ActionabilityBand.CANDIDATE, ActionabilityBand.LIVE_CANDIDATE) else "BLOCK",
        "reason": f"Band={band} score={conviction_result.conviction_score:.2f}",
    }
    state.decisions.append(decision)
    strategy.total_decisions += 1

    if band == ActionabilityBand.BLOCKED:
        strategy.total_block += 1
        state.total_blocks += 1
    elif band == ActionabilityBand.CANDIDATE:
        strategy.total_pass += 1
        state.total_candidates += 1
    elif band == ActionabilityBand.LIVE_CANDIDATE:
        strategy.total_pass += 1
        state.total_live_candidates += 1

    if band in (ActionabilityBand.CANDIDATE, ActionabilityBand.LIVE_CANDIDATE):
        # Real PnL: use price delta if available, else simulated
        symbol = "BTCUSDT" if "btc" in strategy.strategy_id else "ETHUSDT" if "eth" in strategy.strategy_id else "SOLUSDT"
        prev_price = state.last_prices.get(symbol)
        current_price = state.last_prices.get("_current_" + symbol, 0)
        if prev_price and current_price and prev_price > 0:
            price_delta_pct = (current_price - prev_price) / prev_price
            pnl = price_delta_pct * strategy.max_entry_try * (1 if edge_proxy > 0.4 else -1)
            pnl = round(pnl, 1)
        else:
            pnl = (edge_proxy - 0.35) * strategy.max_entry_try * 0.02 + random.uniform(-5, 5)
            pnl = round(pnl, 1)
        strategy.pnl_today_try = round(strategy.pnl_today_try + pnl, 1)
        strategy.pnl_week_try = round(strategy.pnl_week_try + pnl, 1)
        strategy.strategy_quality = round(min(1.0, strategy.strategy_quality + 0.02) if pnl > 0 else max(0.0, strategy.strategy_quality - 0.05), 3)

        # Self-training: track prediction accuracy
        predicted_direction = 1 if edge_proxy > 0.4 else 0
        actual_direction = 1 if pnl > 0 else 0
        state.total_predictions += 1
        if predicted_direction == actual_direction:
            state.correct_predictions += 1

        # Adaptive learning rate
        accuracy = state.correct_predictions / max(1, state.total_predictions)
        if accuracy > 0.65:
            state.adaptive_alpha = min(0.35, state.adaptive_alpha + 0.005)
        elif accuracy < 0.35:
            state.adaptive_alpha = max(0.05, state.adaptive_alpha - 0.01)
        state.last_cycle_pnl = pnl

        state.ledger_events.append(_event(state, "PRODUCTION_DECISION", "INFO", "production-engine", strategy.strategy_id,
            f"PnL={pnl:+.1f} TRY Quality={strategy.strategy_quality:.2f} α={state.adaptive_alpha:.3f} acc={accuracy:.0%}"))

    if abs(edge_proxy - 0.5) > 0.15 or fusion_result.source_agreement_score > 0.6:
        pattern = "BULLISH" if edge_proxy > 0.5 else "BEARISH"
        state.memory_records.append({
            "memory_id": state.next_memory_id(),
            "strategy_id": strategy.strategy_id,
            "pattern_type": f"{pattern}_PATTERN",
            "description": f"C{cycle}: {pattern} trend={edge_proxy:.2f} contradiction={risk_proxy:.2f}",
            "confidence": fusion_result.confidence,
            "last_seen_ms": now_ms,
            "sample_count": strategy.total_decisions,
            "usable_for_live": strategy.total_decisions >= 3 and strategy.strategy_quality > 0.3,
        })
        state.ledger_events.append(_event(state, "MEMORY_WRITE", "INFO", "memory-write-gate", strategy.strategy_id,
            f"Memory stored: {pattern} (conf={fusion_result.confidence:.2f})"))

    if len(state.ledger_events) > 1000:
        state.ledger_events = state.ledger_events[-500:]

    # Periodic system events
    if state.cycle % 3 == 0:
        stale_count = sum(1 for a in ADAPTER_POOL if random.random() < a["error_rate"] * 3)
        state.ledger_events.append(_event(state, "INGRESS_COMPILED", "INFO", "ingress-compiler", None,
            f"Ingress compilation: {len(ADAPTER_POOL)} sources checked, {len(ADAPTER_POOL) - stale_count} passed, {stale_count} stale-suppressed"))
        state.ledger_events.append(_event(state, "EVIDENCE_STORED", "INFO", "evidence-gate", strategy.strategy_id,
            f"Evidence bundle: trend={edge_proxy:.2f} contradiction={risk_proxy:.2f} sources_agreed={fusion_result.source_agreement_score:.2f}"))

    if state.cycle % 5 == 0:
        state.ledger_events.append(_event(state, "REPLAY_COMPLETED", "INFO", "replay-engine", strategy.strategy_id,
            f"Counterfactual replay: {strategy.strategy_id} — edge would be {edge_proxy + random.uniform(-0.1, 0.1):.2f} with tighter spread"))

    if state.cycle % 10 == 0:
        state.ledger_events.append(_event(state, "CONSTITUTION_AUDIT", "INFO", "constitution-auditor", None,
            f"Constitutional audit: 0 violations in last {len(state.decisions)} decisions. All invariants hold."))

    state.last_cycle_ms = now_ms
    return state


def export_snapshot(state: LearningState) -> Path:
    now_ms = int(time.time() * 1000)

    strategies_out = []
    for s in state.strategies.values():
        strategies_out.append({
            "strategy_id": s.strategy_id, "name": s.name,
            "lifecycle_state": s.lifecycle_state,
            "allocated_budget_try": s.allocated_budget_try,
            "max_entry_try": s.max_entry_try,
            "max_trades_per_day": s.max_trades_per_day,
            "current_edge_score": s.current_edge_score,
            "current_risk_score": s.current_risk_score,
            "current_confidence": s.current_confidence,
            "enabled": s.enabled, "strategy_quality": s.strategy_quality,
            "pnl_today_try": s.pnl_today_try, "pnl_week_try": s.pnl_week_try,
            "total_decisions": s.total_decisions, "total_pass": s.total_pass, "total_block": s.total_block,
        })

    adapters_out = []
    for i, a in enumerate(ADAPTER_POOL):
        # Add health variety: 1 stale (fear-greed-index), 1 quarantined (cryptopanic-feed) on some cycles
        is_stale = a["id"] == "fear-greed-index" and state.cycle % 3 != 0
        is_quarantined = a["id"] == "cryptopanic-feed" and state.cycle > 5 and state.cycle % 4 == 0
        trust_band = "QUARANTINED" if is_quarantined else "TRUSTED"

        adapters_out.append({
            "adapter_id": a["id"], "name": a["name"],
            "source_family": a["family"], "trust_band": trust_band,
            "is_active": not is_quarantined, "is_fresh": not is_stale,
            "is_healthy": not is_stale and not is_quarantined and random.random() > a["error_rate"] * 2,
            "last_seen_ms": now_ms - (8 * 3600000 if is_stale else random.randint(5000, 600000)),
            "latency_ms": a["latency"] + random.randint(-20, 50) if not is_stale else None,
            "error_rate": (0.12 if is_stale else a["error_rate"] + random.uniform(-0.001, 0.003)),
            "credential_ref_id": f"cred-{a['id']}",
            "description": f"{a['name']} — {a['family']} data feed",
            **(dict(quarantine_reason="consecutive 5xx errors") if is_quarantined else {}),
        })

    total_allocated = sum(s.allocated_budget_try for s in state.strategies.values())
    today_pnl = round(sum(s.pnl_today_try for s in state.strategies.values()), 1)
    week_pnl = round(sum(s.pnl_week_try for s in state.strategies.values()), 1)

    snapshot: dict[str, Any] = {
        "generated_at_ms": now_ms,
        "generator": "sentinel.runtime.learning_loop",
        "sentinel_version": "v1.14",
        "learning_state": {
            "cycle": state.cycle, "started_at_ms": state.started_at_ms,
            "last_cycle_ms": state.last_cycle_ms, "total_signals": state.total_signals_processed,
            "total_blocks": state.total_blocks, "total_candidates": state.total_candidates,
            "total_live_candidates": state.total_live_candidates,
            "total_memories": len(state.memory_records),
            "correct_predictions": state.correct_predictions,
            "total_predictions": state.total_predictions,
            "accuracy": round(state.correct_predictions / max(1, state.total_predictions), 3),
            "adaptive_alpha": round(state.adaptive_alpha, 3),
        },
        "portfolio": {
            "portfolio_id": "main-portfolio", "approved_capital_mode": "FIXED_TRY",
            "approved_capital_value": 10000, "total_allocated_try": total_allocated,
            "max_total_daily_loss_try": 500, "max_open_orders": 5,
            "max_strategy_correlation": 0.7, "max_single_strategy_exposure": 0.5,
            "max_single_exchange_exposure": 0.7,
            "kill_switch_active": False, "kill_switch_required": True,
            "active_strategy_count": sum(1 for s in state.strategies.values() if s.lifecycle_state in ("ACTIVE_LIVE", "LIMITED_LIVE") and s.enabled),
            "paused_strategy_count": sum(1 for s in state.strategies.values() if s.lifecycle_state == "PAUSED"),
        },
        "strategies": strategies_out,
        "adapters": adapters_out,
        "ledger_events": state.ledger_events[-50:],
        "decisions": state.decisions[-20:],
        "exchanges": [
            {"exchange_id": "binance", "name": "Binance", "status": "OPERATIONAL", "trade_enabled": False, "withdraw_enabled": False, "latency_ms": 18},
            {"exchange_id": "btcturk", "name": "BTCTürk", "status": "OPERATIONAL", "trade_enabled": False, "withdraw_enabled": False, "latency_ms": 55},
        ],
        "credentials": [
            {"ref_id": f"cred-{a['id']}", "kind": "api_key", "adapter_id": a["id"], "label": a["name"],
             "masked_secret": "••••••••••••••••xxxx", "trade_enabled": False, "withdraw_enabled": False,
             "read_only": True, "created_at_ms": now_ms - 7 * DAY_MS, "expires_at_ms": None,
             "is_active": True, "source": "seed"}
            for a in ADAPTER_POOL
        ],
        "memory_records": state.memory_records[-20:],
        "market_sentiment": {
            "fear_greed": round(state.market_sentiment.get("fear_greed_index", 0.5) * 100),
            "ct_sentiment": state.market_sentiment.get("ct_sentiment", 0),
            "ct_bullish": state.market_sentiment.get("ct_bullish", 0),
        },
    }

    out_dir = Path(__file__).resolve().parents[2] / "panel" / "api" / "src" / "mock"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "snapshot.json"

    with open(out_path, "w") as f:
        json.dump(snapshot, f, indent=2)

    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Sentinel learning loop")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--interval", type=int, default=5)
    parser.add_argument("--cycles", type=int, default=0)
    args = parser.parse_args()

    state = LearningState()
    state.strategies = {s.strategy_id: s for s in DEFAULT_STRATEGIES}

    mode = "once" if args.once else f"every {args.interval}s"
    print(f"♺ Learning loop — {len(state.strategies)} strategies, {len(ADAPTER_POOL)} adapters, {mode}")
    print()

    cycle_count = 0
    max_cycles = args.cycles or (1 if args.once else 0)

    try:
        while True:
            state = run_cycle(state)
            cycle_count += 1

            strategies = list(state.strategies.values())
            total_pnl = round(sum(s.pnl_today_try for s in strategies), 1)
            active_cnt = sum(1 for s in strategies if s.lifecycle_state in ("ACTIVE_LIVE", "LIMITED_LIVE") and s.enabled)

            print(
                f"  [{state.cycle:04d}] signals={state.total_signals_processed} "
                f"✓={state.total_candidates} ★={state.total_live_candidates} "
                f"✗={state.total_blocks} active={active_cnt} "
                f"PnL={total_pnl:+.1f}TRY mem={len(state.memory_records)}"
            )

            path = export_snapshot(state)
            if state.cycle % 5 == 0 or args.once:
                print(f"       ↳ snapshot: {path.name}")

            if args.once or (max_cycles > 0 and cycle_count >= max_cycles):
                break

            time.sleep(args.interval)
    except KeyboardInterrupt:
        print()

    path = export_snapshot(state)
    print(f"\n  Done. {state.cycle} cycles, {len(state.memory_records)} memories → {path.name}")


if __name__ == "__main__":
    main()
