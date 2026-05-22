#!/usr/bin/env python3
"""Gel.Al ↔ Sentinel trade bridge.

Simulates Gel.Al trade signals and passes them through the Sentinel guard.
Shadow mode: no real execution, only approval/block decisions.

Phases:
  shadow  → 0 TRY, only log decisions
  canary  → max 50 TRY/day, limited live
  live    → full portfolio limits
"""

from __future__ import annotations

import json
import random
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

TRADE_LOG = Path("data/trades/gelal_trades.jsonl")
GUARD_LOG = Path("data/trades/guard_decisions.jsonl")

CANARY_DAILY_LIMIT = 50.0  # TRY
LIMITED_LIVE_DAILY_LIMIT = 500.0


@dataclass
class TradeSignal:
    """A Gel.Al trade attempt."""
    signal_id: str
    strategy_id: str
    symbol: str
    side: str  # BUY or SELL
    amount_try: float
    price: float
    edge_score: float
    risk_score: float
    ts_ms: int = field(default_factory=lambda: int(time.time() * 1000))


@dataclass
class GuardDecision:
    """Sentinel guard decision on a trade."""
    signal_id: str
    approved: bool
    reason: str
    guard_level: str  # shadow, canary, limited_live, active_live
    ts_ms: int = field(default_factory=lambda: int(time.time() * 1000))


def generate_test_signals(n: int = 3) -> list[TradeSignal]:
    """Generate test trade signals simulating Gel.Al output."""
    strategies = [
        ("btc-momentum-v3", "BTCUSDT", 350),
        ("eth-mean-reversion", "ETHUSDT", 280),
        ("sol-breakout-alpha", "SOLUSDT", 120),
    ]
    signals = []
    for i in range(n):
        sid, sym, max_entry = random.choice(strategies)
        edge = random.uniform(0.2, 0.8)
        risk = random.uniform(0.1, 0.6)
        signals.append(TradeSignal(
            signal_id=f"gelal-{int(time.time() * 1000)}-{i:03d}",
            strategy_id=sid,
            symbol=sym,
            side=random.choice(["BUY", "SELL"]),
            amount_try=round(random.uniform(10, max_entry), 2),
            price=0.0,
            edge_score=round(edge, 3),
            risk_score=round(risk, 3),
        ))
    return signals


def evaluate_trade(
    signal: TradeSignal,
    phase: str = "shadow",
    daily_total: float = 0.0,
    strategy_quality: float = 0.5,
    kill_switch: bool = False,
) -> GuardDecision:
    """Run a trade signal through the Sentinel guard.

    Returns decision with approval and reason.
    """
    if kill_switch:
        return GuardDecision(signal.signal_id, False, "KILL_SWITCH_ACTIVE", phase)

    if phase == "shadow":
        return GuardDecision(signal.signal_id, False, "SHADOW_MODE — execution disabled", phase)

    # Quality guard
    if strategy_quality < 0.10:
        return GuardDecision(signal.signal_id, False,
            f"LOW_QUALITY ({strategy_quality:.2f} < 0.10)", phase)

    # Risk guard
    if signal.risk_score > 0.80:
        return GuardDecision(signal.signal_id, False,
            f"HIGH_RISK ({signal.risk_score:.2f} > 0.80)", phase)

    # Edge guard
    if signal.edge_score < 0.25:
        return GuardDecision(signal.signal_id, False,
            f"LOW_EDGE ({signal.edge_score:.2f} < 0.25)", phase)

    # Budget limits
    if phase == "canary" and daily_total + signal.amount_try > CANARY_DAILY_LIMIT:
        return GuardDecision(signal.signal_id, False,
            f"CANARY_LIMIT ({daily_total:.1f} + {signal.amount_try:.1f} > {CANARY_DAILY_LIMIT})", phase)

    if phase == "limited_live" and daily_total + signal.amount_try > LIMITED_LIVE_DAILY_LIMIT:
        return GuardDecision(signal.signal_id, False,
            f"LIMITED_LIVE_LIMIT ({daily_total:.1f} + {signal.amount_try:.1f} > {LIMITED_LIVE_DAILY_LIMIT})", phase)

    # Constitution guard: no BUY/SELL in sentinel core output
    # (This is simulated — in production, Gel.Al receives WAIT/APPROVE, not BUY/SELL)

    return GuardDecision(signal.signal_id, True,
        f"APPROVED — edge={signal.edge_score:.2f} risk={signal.risk_score:.2f}", phase)


def run_guard_cycle(
    phase: str = "shadow",
    strategy_qualities: dict[str, float] | None = None,
    kill_switch: bool = False,
) -> list[GuardDecision]:
    """Run one guard cycle with simulated trades."""
    if strategy_qualities is None:
        strategy_qualities = {}

    signals = generate_test_signals(random.randint(1, 4))
    decisions = []
    daily_total = 0.0

    for signal in signals:
        quality = strategy_qualities.get(signal.strategy_id, 0.5)
        decision = evaluate_trade(signal, phase, daily_total, quality, kill_switch)
        decisions.append(decision)

        # Log
        TRADE_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(TRADE_LOG, "a") as f:
            f.write(json.dumps({"signal": signal.__dict__, "decision": decision.__dict__}) + "\n")

        GUARD_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(GUARD_LOG, "a") as f:
            f.write(json.dumps(decision.__dict__) + "\n")

        if decision.approved:
            daily_total += signal.amount_try

    return decisions


def get_guard_stats() -> dict[str, Any]:
    """Get guard statistics from log files."""
    if not GUARD_LOG.exists():
        return {"total": 0, "approved": 0, "blocked": 0, "approval_rate": 0}

    decisions = []
    with open(GUARD_LOG) as f:
        for line in f:
            if line.strip():
                decisions.append(json.loads(line))

    approved = sum(1 for d in decisions if d.get("approved"))
    return {
        "total": len(decisions),
        "approved": approved,
        "blocked": len(decisions) - approved,
        "approval_rate": round(approved / len(decisions), 3) if decisions else 0,
        "last_decision": decisions[-1] if decisions else None,
    }


if __name__ == "__main__":
    print("Gel.Al ↔ Sentinel Guard Bridge")
    print(f"Phase: shadow (0 TRY)")
    print()

    for i in range(3):
        decisions = run_guard_cycle("shadow")
        for d in decisions:
            status = "✅ APPROVED" if d.approved else "❌ BLOCKED"
            print(f"  {status}: {d.reason}")
        time.sleep(1)

    stats = get_guard_stats()
    print(f"\nGuard stats: {stats['total']} total, {stats['approved']} approved, {stats['blocked']} blocked")
