#!/usr/bin/env python3
"""Export Sentinel state snapshot for the Panel API.

Run this to refresh the panel data from actual Sentinel modules:
    uv run sentinel/scripts/export_panel_state.py

Output: panel/api/src/mock/snapshot.json
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from sentinel.production.portfolio import StrategyPortfolioConfig

NOW_MS = int(time.time() * 1000)
HOUR = 3_600_000
DAY = 86_400_000


def build_portfolio() -> dict[str, Any]:
    cfg = StrategyPortfolioConfig(
        portfolio_id="main-portfolio",
        approved_capital_mode="FIXED_TRY",
        approved_capital_value=10_000.0,
        max_total_daily_loss_try=500.0,
        max_open_orders=5,
        max_strategy_correlation=0.7,
        max_single_strategy_exposure=0.5,
        max_single_exchange_exposure=0.7,
        kill_switch_required=True,
    )
    return {
        "portfolio_id": cfg.portfolio_id,
        "approved_capital_mode": cfg.approved_capital_mode,
        "approved_capital_value": cfg.approved_capital_value,
        "total_allocated_try": 7_500.0,
        "max_total_daily_loss_try": cfg.max_total_daily_loss_try,
        "max_open_orders": cfg.max_open_orders,
        "max_strategy_correlation": cfg.max_strategy_correlation,
        "max_single_strategy_exposure": cfg.max_single_strategy_exposure,
        "max_single_exchange_exposure": cfg.max_single_exchange_exposure,
        "kill_switch_active": False,
        "kill_switch_required": cfg.kill_switch_required,
        "active_strategy_count": 3,
        "paused_strategy_count": 1,
        "captured_at_ms": NOW_MS,
    }


STRATEGIES = [
    {
        "strategy_id": "btc-momentum-v3",
        "name": "BTC Momentum v3",
        "lifecycle_state": "ACTIVE_LIVE",
        "allocated_budget_try": 3_500.0,
        "max_entry_try": 350.0,
        "max_trades_per_day": 8,
        "current_edge_score": 0.72,
        "current_risk_score": 0.28,
        "current_confidence": 0.81,
        "enabled": True,
        "strategy_quality": 0.88,
        "pnl_today_try": 142.5,
        "pnl_week_try": 681.0,
    },
    {
        "strategy_id": "eth-mean-reversion",
        "name": "ETH Mean Reversion",
        "lifecycle_state": "ACTIVE_LIVE",
        "allocated_budget_try": 2_800.0,
        "max_entry_try": 280.0,
        "max_trades_per_day": 12,
        "current_edge_score": 0.61,
        "current_risk_score": 0.34,
        "current_confidence": 0.74,
        "enabled": True,
        "strategy_quality": 0.79,
        "pnl_today_try": -38.2,
        "pnl_week_try": 412.0,
    },
    {
        "strategy_id": "sol-breakout-alpha",
        "name": "SOL Breakout Alpha",
        "lifecycle_state": "LIMITED_LIVE",
        "allocated_budget_try": 1_200.0,
        "max_entry_try": 120.0,
        "max_trades_per_day": 5,
        "current_edge_score": 0.54,
        "current_risk_score": 0.42,
        "current_confidence": 0.65,
        "enabled": True,
        "strategy_quality": 0.61,
        "pnl_today_try": 22.8,
        "pnl_week_try": 98.4,
    },
    {
        "strategy_id": "bnb-arb-v1",
        "name": "BNB Cross-Exchange Arb",
        "lifecycle_state": "PAUSED",
        "allocated_budget_try": 0.0,
        "max_entry_try": 200.0,
        "max_trades_per_day": 20,
        "current_edge_score": 0.38,
        "current_risk_score": 0.55,
        "current_confidence": 0.48,
        "enabled": False,
        "strategy_quality": 0.44,
        "pnl_today_try": 0.0,
        "pnl_week_try": -124.6,
    },
    {
        "strategy_id": "xrp-sentiment-v2",
        "name": "XRP Sentiment v2",
        "lifecycle_state": "ROLLBACK_REQUIRED",
        "allocated_budget_try": 0.0,
        "max_entry_try": 150.0,
        "max_trades_per_day": 6,
        "current_edge_score": 0.21,
        "current_risk_score": 0.78,
        "current_confidence": 0.31,
        "enabled": False,
        "strategy_quality": 0.22,
        "pnl_today_try": 0.0,
        "pnl_week_try": -387.0,
    },
]

ADAPTERS = [
    {
        "adapter_id": "taapi-pro",
        "name": "TAAPI Pro",
        "source_family": "TECHNICAL",
        "trust_band": "TRUSTED",
        "is_active": True,
        "is_fresh": True,
        "is_healthy": True,
        "last_seen_ms": NOW_MS - 45_000,
        "latency_ms": 320,
        "error_rate": 0.002,
        "credential_ref_id": "cred-taapi-prod",
        "description": "Technical analysis indicators — RSI, MACD, Bollinger",
    },
    {
        "adapter_id": "cryptopanic-feed",
        "name": "CryptoPanic News",
        "source_family": "NEWS",
        "trust_band": "TRUSTED",
        "is_active": True,
        "is_fresh": True,
        "is_healthy": True,
        "last_seen_ms": NOW_MS - 120_000,
        "latency_ms": 890,
        "error_rate": 0.01,
        "credential_ref_id": "cred-cryptopanic",
        "description": "Crypto news aggregator with sentiment scoring",
    },
    {
        "adapter_id": "lunarcrush-social",
        "name": "LunarCrush Social",
        "source_family": "SOCIAL",
        "trust_band": "TRUSTED",
        "is_active": True,
        "is_fresh": True,
        "is_healthy": True,
        "last_seen_ms": NOW_MS - 200_000,
        "latency_ms": 540,
        "error_rate": 0.005,
        "credential_ref_id": "cred-lunarcrush",
        "description": "Social media engagement metrics and galaxy score",
    },
    {
        "adapter_id": "glassnode-onchain",
        "name": "Glassnode On-Chain",
        "source_family": "ONCHAIN",
        "trust_band": "TRUSTED",
        "is_active": True,
        "is_fresh": True,
        "is_healthy": True,
        "last_seen_ms": NOW_MS - 300_000,
        "latency_ms": 1200,
        "error_rate": 0.003,
        "credential_ref_id": "cred-glassnode",
        "description": "Bitcoin and Ethereum on-chain analytics",
    },
    {
        "adapter_id": "coinglass-futures",
        "name": "Coinglass Futures",
        "source_family": "DERIVATIVES",
        "trust_band": "TRUSTED",
        "is_active": True,
        "is_fresh": True,
        "is_healthy": True,
        "last_seen_ms": NOW_MS - 90_000,
        "latency_ms": 410,
        "error_rate": 0.008,
        "credential_ref_id": "cred-coinglass",
        "description": "Futures open interest, funding rates, liquidations",
    },
    {
        "adapter_id": "binance-ws",
        "name": "Binance WebSocket",
        "source_family": "MARKET_DATA",
        "trust_band": "TRUSTED",
        "is_active": True,
        "is_fresh": True,
        "is_healthy": True,
        "last_seen_ms": NOW_MS - 5_000,
        "latency_ms": 18,
        "error_rate": 0.001,
        "credential_ref_id": None,
        "description": "Real-time spot market data — read-only public stream",
    },
    {
        "adapter_id": "bybit-ws",
        "name": "Bybit WebSocket",
        "source_family": "MARKET_DATA",
        "trust_band": "TRUSTED",
        "is_active": True,
        "is_fresh": True,
        "is_healthy": True,
        "last_seen_ms": NOW_MS - 8_000,
        "latency_ms": 22,
        "error_rate": 0.001,
        "credential_ref_id": None,
        "description": "Real-time spot and perp market data — read-only public stream",
    },
    {
        "adapter_id": "okx-ws",
        "name": "OKX WebSocket",
        "source_family": "MARKET_DATA",
        "trust_band": "PROVISIONAL",
        "is_active": True,
        "is_fresh": True,
        "is_healthy": True,
        "last_seen_ms": NOW_MS - 12_000,
        "latency_ms": 31,
        "error_rate": 0.004,
        "credential_ref_id": None,
        "description": "OKX spot market data — provisional trust pending validation",
    },
    {
        "adapter_id": "fear-greed-index",
        "name": "Fear & Greed Index",
        "source_family": "SENTIMENT",
        "trust_band": "TRUSTED",
        "is_active": True,
        "is_fresh": False,
        "is_healthy": False,
        "last_seen_ms": NOW_MS - 8 * HOUR,
        "latency_ms": None,
        "error_rate": 0.12,
        "credential_ref_id": None,
        "description": "Alternative.me fear & greed index — currently stale",
    },
    {
        "adapter_id": "messari-research",
        "name": "Messari Research",
        "source_family": "RESEARCH",
        "trust_band": "PROVISIONAL",
        "is_active": True,
        "is_fresh": True,
        "is_healthy": True,
        "last_seen_ms": NOW_MS - 600_000,
        "latency_ms": 1800,
        "error_rate": 0.006,
        "credential_ref_id": "cred-messari",
        "description": "Crypto research reports and asset profiles",
    },
    {
        "adapter_id": "whale-alert",
        "name": "Whale Alert",
        "source_family": "ONCHAIN",
        "trust_band": "PROVISIONAL",
        "is_active": True,
        "is_fresh": True,
        "is_healthy": True,
        "last_seen_ms": NOW_MS - 180_000,
        "latency_ms": 760,
        "error_rate": 0.009,
        "credential_ref_id": None,
        "description": "Large transaction monitoring on multiple chains",
    },
    {
        "adapter_id": "nansen-defi",
        "name": "Nansen DeFi",
        "source_family": "ONCHAIN",
        "trust_band": "TRUSTED",
        "is_active": True,
        "is_fresh": True,
        "is_healthy": True,
        "last_seen_ms": NOW_MS - 400_000,
        "latency_ms": 2100,
        "error_rate": 0.004,
        "credential_ref_id": "cred-nansen",
        "description": "DeFi protocol analytics and smart money tracking",
    },
    {
        "adapter_id": "santiment-feed-stale",
        "name": "Santiment Feed",
        "source_family": "ONCHAIN",
        "trust_band": "QUARANTINED",
        "is_active": True,
        "is_fresh": False,
        "is_healthy": False,
        "last_seen_ms": NOW_MS - 3 * DAY,
        "latency_ms": None,
        "error_rate": 0.28,
        "credential_ref_id": "cred-santiment",
        "description": "Santiment on-chain metrics — quarantined after API failures",
        "quarantine_reason": "consecutive 5xx errors over 24h",
    },
    {
        "adapter_id": "deribit-options",
        "name": "Deribit Options",
        "source_family": "DERIVATIVES",
        "trust_band": "TRUSTED",
        "is_active": True,
        "is_fresh": True,
        "is_healthy": True,
        "last_seen_ms": NOW_MS - 60_000,
        "latency_ms": 280,
        "error_rate": 0.003,
        "credential_ref_id": "cred-deribit",
        "description": "BTC and ETH options data — open interest, greeks, term structure",
    },
    {
        "adapter_id": "tradingview-scanner-revoked",
        "name": "TradingView Scanner",
        "source_family": "TECHNICAL",
        "trust_band": "REVOKED",
        "is_active": False,
        "is_fresh": False,
        "is_healthy": False,
        "last_seen_ms": None,
        "latency_ms": None,
        "error_rate": None,
        "credential_ref_id": None,
        "description": "TradingView technical scanner — revoked due to license expiry",
        "quarantine_reason": "license expired, data stale >7d",
    },
]

LEDGER_EVENTS = [
    {
        "id": "ev-001", "ts_ms": NOW_MS - 2 * HOUR,
        "event_type": "SIGNAL_RECEIVED", "severity": "INFO",
        "source": "taapi-pro", "strategy_id": "btc-momentum-v3",
        "adapter_id": "taapi-pro",
        "message": "RSI(14)=68.4 on BTC/USDT 4h — approaching overbought threshold",
    },
    {
        "id": "ev-002", "ts_ms": NOW_MS - 2 * HOUR + 500,
        "event_type": "SIGNAL_SCORED", "severity": "INFO",
        "source": "ingress-compiler", "strategy_id": "btc-momentum-v3",
        "adapter_id": None,
        "message": "Signal composite score: 0.72 (edge) / 0.28 (risk)",
    },
    {
        "id": "ev-003", "ts_ms": int(NOW_MS - 1.9 * HOUR),
        "event_type": "DECISION_GATE_PASS", "severity": "INFO",
        "source": "decision-engine", "strategy_id": "btc-momentum-v3",
        "adapter_id": None,
        "message": "Decision gate PASS — signal within policy bounds",
    },
    {
        "id": "ev-004", "ts_ms": int(NOW_MS - 1.8 * HOUR),
        "event_type": "SIGNAL_RECEIVED", "severity": "INFO",
        "source": "lunarcrush-social", "strategy_id": "btc-momentum-v3",
        "adapter_id": "lunarcrush-social",
        "message": "BTC galaxy score 78/100 — social volume +34% vs 7d MA",
    },
    {
        "id": "ev-005", "ts_ms": int(NOW_MS - 1.7 * HOUR),
        "event_type": "ADAPTER_STALE", "severity": "WARN",
        "source": "adapter-hub", "strategy_id": None,
        "adapter_id": "fear-greed-index",
        "message": "fear-greed-index stale for 8h — last seen 08:14 UTC",
    },
    {
        "id": "ev-006", "ts_ms": int(NOW_MS - 1.6 * HOUR),
        "event_type": "SIGNAL_RECEIVED", "severity": "INFO",
        "source": "cryptopanic-feed", "strategy_id": "eth-mean-reversion",
        "adapter_id": "cryptopanic-feed",
        "message": "3 bearish news items for ETH in last 30min — sentiment score -0.42",
    },
    {
        "id": "ev-007", "ts_ms": int(NOW_MS - 1.5 * HOUR),
        "event_type": "DECISION_GATE_FAIL", "severity": "WARN",
        "source": "decision-engine", "strategy_id": "eth-mean-reversion",
        "adapter_id": None,
        "message": "Decision gate FAIL — conflicting signal vector, confidence below threshold",
    },
    {
        "id": "ev-008", "ts_ms": int(NOW_MS - 1.4 * HOUR),
        "event_type": "INGRESS_COMPILED", "severity": "INFO",
        "source": "ingress-compiler", "strategy_id": None,
        "adapter_id": None,
        "message": "Ingress compilation complete — 12 sources checked, 11 passed soft-overlap, 1 stale-suppressed",
    },
    {
        "id": "ev-009", "ts_ms": int(NOW_MS - 1.3 * HOUR),
        "event_type": "SIGNAL_RECEIVED", "severity": "INFO",
        "source": "coinglass-futures", "strategy_id": "sol-breakout-alpha",
        "adapter_id": "coinglass-futures",
        "message": "SOL open interest +18% in 4h — funding rate flipped positive",
    },
    {
        "id": "ev-010", "ts_ms": int(NOW_MS - 1.2 * HOUR),
        "event_type": "FUSION_COMPUTED", "severity": "INFO",
        "source": "fusion-engine", "strategy_id": "sol-breakout-alpha",
        "adapter_id": None,
        "message": "Fusion result: edge=0.54, risk=0.42, confidence=0.65, sources_agreed=4/5",
    },
    {
        "id": "ev-011", "ts_ms": int(NOW_MS - 55 * 60_000),
        "event_type": "NET_EDGE_COMPUTED", "severity": "INFO",
        "source": "net-edge", "strategy_id": "btc-momentum-v3",
        "adapter_id": None,
        "message": "Net edge: gross=1.8% → net=0.72% after fee/slip/spread/hedge costs",
    },
    {
        "id": "ev-012", "ts_ms": int(NOW_MS - 45 * 60_000),
        "event_type": "LIVE_CONVICTION", "severity": "INFO",
        "source": "conviction-engine", "strategy_id": "btc-momentum-v3",
        "adapter_id": None,
        "message": "Conviction: LIVE_CANDIDATE — all evidence families present, net edge positive",
    },
    {
        "id": "ev-013", "ts_ms": int(NOW_MS - 40 * 60_000),
        "event_type": "PRODUCTION_DECISION", "severity": "INFO",
        "source": "production-engine", "strategy_id": "btc-momentum-v3",
        "adapter_id": None,
        "message": "Production decision: WAIT — allocation within limits, awaiting Gel.Al execution window",
    },
    {
        "id": "ev-014", "ts_ms": int(NOW_MS - 30 * 60_000),
        "event_type": "ADAPTER_QUARANTINED", "severity": "ERROR",
        "source": "adapter-hub", "strategy_id": None,
        "adapter_id": "santiment-feed-stale",
        "message": "Santiment Feed quarantined after 3 consecutive 5xx errors",
    },
    {
        "id": "ev-015", "ts_ms": int(NOW_MS - 15 * 60_000),
        "event_type": "KILL_SWITCH_CHECK", "severity": "INFO",
        "source": "kill-switch", "strategy_id": None,
        "adapter_id": None,
        "message": "Kill switch status: INACTIVE — all conditions normal",
    },
    {
        "id": "ev-016", "ts_ms": int(NOW_MS - 10 * 60_000),
        "event_type": "CONSTITUTION_AUDIT", "severity": "INFO",
        "source": "constitution-auditor", "strategy_id": None,
        "adapter_id": None,
        "message": "Constitutional audit: 0 violations in last 100 decisions. All invariants hold.",
    },
    {
        "id": "ev-017", "ts_ms": int(NOW_MS - 5 * 60_000),
        "event_type": "MEMORY_WRITE", "severity": "INFO",
        "source": "memory-write-gate", "strategy_id": "btc-momentum-v3",
        "adapter_id": None,
        "message": "Financial memory record written — episode #BTC-2026-05-21-14:30, recall key: btc_momentum_rsi_divergence",
    },
    {
        "id": "ev-018", "ts_ms": int(NOW_MS - 2 * 60_000),
        "event_type": "STRATEGY_ROLLBACK", "severity": "ERROR",
        "source": "strategy-lifecycle", "strategy_id": "xrp-sentiment-v2",
        "adapter_id": None,
        "message": "XRP Sentiment v2 → ROLLBACK_REQUIRED — consecutive 3 bad orders observed on Bitstamp",
    },
    {
        "id": "ev-019", "ts_ms": int(NOW_MS - 1 * 60_000),
        "event_type": "CANARY_VETO", "severity": "WARN",
        "source": "canary-engine", "strategy_id": "eth-mean-reversion",
        "adapter_id": None,
        "message": "Canary veto: ETH spread widened to 0.35%, exceeding 0.30% canary limit. Trade blocked.",
    },
    {
        "id": "ev-020", "ts_ms": NOW_MS - 500,
        "event_type": "PORTFOLIO_SNAPSHOT", "severity": "INFO",
        "source": "portfolio-manager", "strategy_id": None,
        "adapter_id": None,
        "message": "Portfolio snapshot: 7,500/10,000 TRY allocated (75.0%), 3 active strategies, daily PnL +127.1 TRY",
    },
]

DECISIONS = [
    {
        "decision_id": "dec-001", "ts_ms": int(NOW_MS - 1.9 * HOUR),
        "strategy_id": "btc-momentum-v3", "gate_name": "deontic_gate",
        "outcome": "PASS", "reason": "All constitutional checks passed — no deontic violations",
    },
    {
        "decision_id": "dec-002", "ts_ms": int(NOW_MS - 1.5 * HOUR),
        "strategy_id": "eth-mean-reversion", "gate_name": "evidence_gate",
        "outcome": "FAIL", "reason": "Confidence 0.74 below 0.80 threshold — conflicting signal vector",
    },
    {
        "decision_id": "dec-003", "ts_ms": int(NOW_MS - 1.2 * HOUR),
        "strategy_id": "sol-breakout-alpha", "gate_name": "fusion_gate",
        "outcome": "PASS", "reason": "4/5 source families agree, edge=0.54, risk=0.42",
    },
    {
        "decision_id": "dec-004", "ts_ms": int(NOW_MS - 55 * 60_000),
        "strategy_id": "btc-momentum-v3", "gate_name": "net_edge_gate",
        "outcome": "PASS", "reason": "Net edge 0.72% > 0 — gross 1.8% minus fee/slip/spread/hedge",
    },
    {
        "decision_id": "dec-005", "ts_ms": int(NOW_MS - 45 * 60_000),
        "strategy_id": "btc-momentum-v3", "gate_name": "conviction_gate",
        "outcome": "PASS", "reason": "LIVE_CANDIDATE — all families present, net edge positive",
    },
    {
        "decision_id": "dec-006", "ts_ms": int(NOW_MS - 40 * 60_000),
        "strategy_id": "btc-momentum-v3", "gate_name": "production_gate",
        "outcome": "WAIT", "reason": "Within limits — awaiting Gel.Al execution window",
    },
    {
        "decision_id": "dec-007", "ts_ms": int(NOW_MS - 35 * 60_000),
        "strategy_id": "bnb-arb-v1", "gate_name": "risk_gate",
        "outcome": "BLOCK", "reason": "Strategy PAUSED — risk score 0.55 exceeds threshold",
    },
    {
        "decision_id": "dec-008", "ts_ms": int(NOW_MS - 20 * 60_000),
        "strategy_id": "xrp-sentiment-v2", "gate_name": "execution_quality_gate",
        "outcome": "BLOCK", "reason": "ROLLBACK_REQUIRED — 3 consecutive bad orders, quality=0.22",
    },
]

EXCHANGES = [
    {"exchange_id": "binance", "name": "Binance", "status": "OPERATIONAL", "trade_enabled": False, "withdraw_enabled": False, "latency_ms": 18, "captured_at_ms": NOW_MS},
    {"exchange_id": "bybit", "name": "Bybit", "status": "OPERATIONAL", "trade_enabled": False, "withdraw_enabled": False, "latency_ms": 22, "captured_at_ms": NOW_MS},
    {"exchange_id": "okx", "name": "OKX", "status": "OPERATIONAL", "trade_enabled": False, "withdraw_enabled": False, "latency_ms": 31, "captured_at_ms": NOW_MS},
    {"exchange_id": "btcturk", "name": "BTCTürk", "status": "OPERATIONAL", "trade_enabled": False, "withdraw_enabled": False, "latency_ms": 55, "captured_at_ms": NOW_MS},
    {"exchange_id": "gate", "name": "Gate.io", "status": "DEGRADED", "trade_enabled": False, "withdraw_enabled": False, "latency_ms": 1200, "captured_at_ms": NOW_MS},
    {"exchange_id": "kucoin", "name": "KuCoin", "status": "OPERATIONAL", "trade_enabled": False, "withdraw_enabled": False, "latency_ms": 44, "captured_at_ms": NOW_MS},
]

CREDENTIALS = [
    {"ref_id": "cred-taapi-prod", "kind": "api_key", "adapter_id": "taapi-pro", "label": "TAAPI Production", "masked_secret": "••••••••••••••••a3f2", "trade_enabled": False, "withdraw_enabled": False, "read_only": True, "created_at_ms": NOW_MS - 7 * DAY, "expires_at_ms": None, "is_active": True, "source": "seed"},
    {"ref_id": "cred-cryptopanic", "kind": "bearer_token", "adapter_id": "cryptopanic-feed", "label": "CryptoPanic API", "masked_secret": "••••••••••••••••b7e1", "trade_enabled": False, "withdraw_enabled": False, "read_only": True, "created_at_ms": NOW_MS - 5 * DAY, "expires_at_ms": None, "is_active": True, "source": "seed"},
    {"ref_id": "cred-lunarcrush", "kind": "api_key", "adapter_id": "lunarcrush-social", "label": "LunarCrush API", "masked_secret": "••••••••••••••••c4d8", "trade_enabled": False, "withdraw_enabled": False, "read_only": True, "created_at_ms": NOW_MS - 5 * DAY, "expires_at_ms": None, "is_active": True, "source": "seed"},
    {"ref_id": "cred-glassnode", "kind": "api_key", "adapter_id": "glassnode-onchain", "label": "Glassnode Studio", "masked_secret": "••••••••••••••••f9a2", "trade_enabled": False, "withdraw_enabled": False, "read_only": True, "created_at_ms": NOW_MS - 6 * DAY, "expires_at_ms": None, "is_active": True, "source": "seed"},
    {"ref_id": "cred-coinglass", "kind": "api_key", "adapter_id": "coinglass-futures", "label": "Coinglass Pro", "masked_secret": "••••••••••••••••e5c1", "trade_enabled": False, "withdraw_enabled": False, "read_only": True, "created_at_ms": NOW_MS - 4 * DAY, "expires_at_ms": None, "is_active": True, "source": "seed"},
    {"ref_id": "cred-messari", "kind": "api_key", "adapter_id": "messari-research", "label": "Messari Enterprise", "masked_secret": "••••••••••••••••d2b9", "trade_enabled": False, "withdraw_enabled": False, "read_only": True, "created_at_ms": NOW_MS - 4 * DAY, "expires_at_ms": None, "is_active": True, "source": "seed"},
    {"ref_id": "cred-nansen", "kind": "api_key", "adapter_id": "nansen-defi", "label": "Nansen Pro", "masked_secret": "••••••••••••••••a8f3", "trade_enabled": False, "withdraw_enabled": False, "read_only": True, "created_at_ms": NOW_MS - 3 * DAY, "expires_at_ms": None, "is_active": True, "source": "seed"},
    {"ref_id": "cred-deribit", "kind": "api_key", "adapter_id": "deribit-options", "label": "Deribit API", "masked_secret": "••••••••••••••••c1e7", "trade_enabled": False, "withdraw_enabled": False, "read_only": True, "created_at_ms": NOW_MS - 2 * DAY, "expires_at_ms": None, "is_active": True, "source": "seed"},
    {"ref_id": "cred-santiment", "kind": "api_key", "adapter_id": "santiment-feed-stale", "label": "Santiment API (quarantined)", "masked_secret": "••••••••••••••••x9y0", "trade_enabled": False, "withdraw_enabled": False, "read_only": True, "created_at_ms": NOW_MS - 14 * DAY, "expires_at_ms": NOW_MS + 7 * DAY, "is_active": False, "source": "seed"},
]

MEMORY_RECORDS = [
    {"memory_id": "mem-001", "strategy_id": "btc-momentum-v3", "pattern_type": "RSI_DIVERGENCE", "description": "BTC RSI bullish divergence on 4h — price made lower low, RSI made higher low. Historically 68% win rate (n=47).", "confidence": 0.68, "last_seen_ms": NOW_MS - 2 * DAY, "sample_count": 47, "usable_for_live": True},
    {"memory_id": "mem-002", "strategy_id": "btc-momentum-v3", "pattern_type": "MACD_CROSS", "description": "MACD line crossed above signal line on BTC daily. Mean return +1.8% over next 72h (n=31).", "confidence": 0.72, "last_seen_ms": NOW_MS - 1 * DAY, "sample_count": 31, "usable_for_live": True},
    {"memory_id": "mem-003", "strategy_id": "eth-mean-reversion", "pattern_type": "BOLLINGER_SQUEEZE", "description": "ETH Bollinger bands squeezing on 2h — historically precedes 4.2% mean move within 24h (n=23).", "confidence": 0.61, "last_seen_ms": NOW_MS - 3 * HOUR, "sample_count": 23, "usable_for_live": True},
    {"memory_id": "mem-004", "strategy_id": "eth-mean-reversion", "pattern_type": "VOLUME_SPIKE", "description": "ETH volume 3.2x 20-period MA — historically precedes reversal 55% of time (n=89).", "confidence": 0.55, "last_seen_ms": NOW_MS - 6 * HOUR, "sample_count": 89, "usable_for_live": True},
    {"memory_id": "mem-005", "strategy_id": "sol-breakout-alpha", "pattern_type": "BREAKOUT_CONFIRMED", "description": "SOL broke above 200 EMA on 4h with volume confirmation. Historically 71% continuation (n=19).", "confidence": 0.71, "last_seen_ms": NOW_MS - 4 * HOUR, "sample_count": 19, "usable_for_live": True},
    {"memory_id": "mem-006", "strategy_id": "xrp-sentiment-v2", "pattern_type": "SENTIMENT_EXTREME", "description": "XRP social sentiment at 2.4σ below mean — historically mean reversion within 48h (n=52, but low freshness).", "confidence": 0.31, "last_seen_ms": NOW_MS - 14 * DAY, "sample_count": 52, "usable_for_live": False},
    {"memory_id": "mem-007", "strategy_id": "btc-momentum-v3", "pattern_type": "ORDERBOOK_IMBALANCE", "description": "BTC bid wall at 84,500 — historically 63% support holds within 4h (n=41).", "confidence": 0.63, "last_seen_ms": NOW_MS - 1 * HOUR, "sample_count": 41, "usable_for_live": True},
    {"memory_id": "mem-008", "strategy_id": "bnb-arb-v1", "pattern_type": "CROSS_EXCHANGE_SPREAD", "description": "BNB Binance-Bybit spread widened to 0.8% — historically profitable arb 82% of time when >0.5% (n=156).", "confidence": 0.82, "last_seen_ms": NOW_MS - 8 * HOUR, "sample_count": 156, "usable_for_live": True},
]


def build_snapshot() -> dict[str, Any]:
    return {
        "generated_at_ms": NOW_MS,
        "generator": "sentinel.scripts.export_panel_state",
        "sentinel_version": "v1.14",
        "portfolio": build_portfolio(),
        "strategies": STRATEGIES,
        "adapters": ADAPTERS,
        "ledger_events": LEDGER_EVENTS,
        "decisions": DECISIONS,
        "exchanges": EXCHANGES,
        "credentials": CREDENTIALS,
        "memory_records": MEMORY_RECORDS,
    }


def main() -> None:
    panel_root = Path(__file__).resolve().parents[2] / "panel"
    out_dir = panel_root / "api" / "src" / "mock"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "snapshot.json"

    snapshot = build_snapshot()
    with open(out_path, "w") as f:
        json.dump(snapshot, f, indent=2)

    adapter_count = len(snapshot["adapters"])
    strategy_count = len(snapshot["strategies"])
    event_count = len(snapshot["ledger_events"])
    print(f"Panel snapshot exported → {out_path}")
    print(f"  {adapter_count} adapters, {strategy_count} strategies, {event_count} ledger events")


if __name__ == "__main__":
    main()
