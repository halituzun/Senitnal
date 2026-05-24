#!/usr/bin/env python3
"""Run the learning loop with real Binance + TAAPI market data.

Usage:
    uv run scripts/run_learning_loop.py --once
    uv run scripts/run_learning_loop.py --interval 10

Env vars:
    TAAPI_API_KEY   — (optional) TAAPI.io free API key for indicators
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

# Load .env file if it exists
_env_path = Path(__file__).resolve().parents[1] / ".env"
if _env_path.exists():
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _key, _val = _line.split("=", 1)
                if _key not in os.environ:
                    os.environ[_key] = _val.strip()
from services.intelligence_adapters.binance_adapter import (
    fetch_all_snapshots as fetch_binance,
    fetch_prices,
)
from services.intelligence_adapters.taapi_adapter import (
    TaapiConfig,
    fetch_and_normalize,
    is_enabled,
)
from services.intelligence_adapters.gdelt_adapter import (
    fetch_all_news_with_headlines,
    compute_news_sentiment_summary,
)
from services.intelligence_adapters.deepseek_adapter import (
    analyze_headlines,
    compute_aggregate_sentiment,
)
from sentinel.runtime.learning_loop import (
    DEFAULT_STRATEGIES,
    LearningState,
    StrategyState,
    export_snapshot,
    run_cycle_with_real_data,
)
from scripts.fetch_historical import get_historical_context
from scripts.backtest import run_backtest_pipeline
from services.intelligence_adapters.coingecko_adapter import fetch_market_sentiment as fetch_coingecko_sentiment
from services.intelligence_adapters.free_news_adapter import fetch_sentiment as fetch_cointelegraph_sentiment, fetch_coindesk_sentiment
from services.intelligence_adapters.smart_strategy import compute_indicator_score
from scripts.gelal_bridge import run_guard_cycle, get_guard_stats
from services.alerting import alert_kill_switch, alert_strategy_paused, alert_guard_block
from services.paper_trading import PaperPortfolio, run_paper_trade
from services.exchange_executor import place_market_buy, place_market_sell, get_balances as get_binance_balances
from services.exchange_executor.btcturk import get_balances as get_btcturk_balances, place_market_order as btcturk_order

STATE_FILE = Path("data/learning_state.json")


def save_state(state: LearningState) -> None:
    """Persist learning state to disk for survival across restarts."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "cycle": state.cycle,
        "started_at_ms": state.started_at_ms,
        "total_signals": state.total_signals_processed,
        "total_blocks": state.total_blocks,
        "total_candidates": state.total_candidates,
        "total_live_candidates": state.total_live_candidates,
        "correct_predictions": state.correct_predictions,
        "total_predictions": state.total_predictions,
        "adaptive_alpha": state.adaptive_alpha,
        "kill_switch_active": state.kill_switch_active,
        "blocked_trades": state.blocked_trades,
        "total_trade_attempts": state.total_trade_attempts,
        "strategies": [
            {
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
                "total_decisions": s.total_decisions,
                "total_pass": s.total_pass, "total_block": s.total_block,
            }
            for s in state.strategies.values()
        ],
        "memory_count": len(state.memory_records),
        "last_prices": state.last_prices,
        "market_sentiment": state.market_sentiment,
    }
    with open(STATE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def load_state() -> LearningState | None:
    """Load persisted learning state from disk."""
    if not STATE_FILE.exists():
        return None
    with open(STATE_FILE) as f:
        data = json.load(f)
    state = LearningState()
    state.cycle = data.get("cycle", 0)
    state.total_signals_processed = data.get("total_signals", 0)
    state.total_blocks = data.get("total_blocks", 0)
    state.total_candidates = data.get("total_candidates", 0)
    state.total_live_candidates = data.get("total_live_candidates", 0)
    state.correct_predictions = data.get("correct_predictions", 0)
    state.total_predictions = data.get("total_predictions", 0)
    state.adaptive_alpha = data.get("adaptive_alpha", 0.15)
    state.kill_switch_active = data.get("kill_switch_active", False)
    state.blocked_trades = data.get("blocked_trades", 0)
    state.total_trade_attempts = data.get("total_trade_attempts", 0)
    state.last_prices = data.get("last_prices", {})
    state.market_sentiment = data.get("market_sentiment", {})
    state._event_idx = data.get("cycle", 0) * 10  # Approximate

    for sdata in data.get("strategies", []):
        sid = sdata["strategy_id"]
        if sid in {s.strategy_id for s in DEFAULT_STRATEGIES}:
            s = StrategyState(
                strategy_id=sid, name=sdata["name"],
                lifecycle_state=sdata["lifecycle_state"],
                allocated_budget_try=sdata["allocated_budget_try"],
                max_entry_try=sdata["max_entry_try"],
                max_trades_per_day=sdata["max_trades_per_day"],
                current_edge_score=sdata["current_edge_score"],
                current_risk_score=sdata["current_risk_score"],
                current_confidence=sdata["current_confidence"],
                enabled=sdata["enabled"],
                strategy_quality=sdata["strategy_quality"],
                pnl_today_try=sdata["pnl_today_try"],
                pnl_week_try=sdata["pnl_week_try"],
                total_decisions=sdata.get("total_decisions", 0),
                total_pass=sdata.get("total_pass", 0),
                total_block=sdata.get("total_block", 0),
            )
            state.strategies[sid] = s

    return state

SYMBOL_MAP = {
    "btc-momentum-v3": "BTC/USDT",
    "eth-mean-reversion": "ETH/USDT",
    "sol-breakout-alpha": "SOL/USDT",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--interval", type=int, default=10)
    parser.add_argument("--cycles", type=int, default=0)
    args = parser.parse_args()

    taapi_config = TaapiConfig(enabled=True, symbols=("BTC/USDT", "ETH/USDT", "SOL/USDT"))
    taapi_ok = is_enabled(taapi_config)

    # Load persisted state or start fresh
    state = load_state()
    if state:
        print(f"♺ Resumed from saved state (cycle {state.cycle}, α={state.adaptive_alpha:.3f})")
    else:
        state = LearningState()

    # Merge: loaded strategies override defaults
    defaults = {s.strategy_id: s for s in DEFAULT_STRATEGIES}
    for sid, s in state.strategies.items():
        if sid in defaults:
            # Force PAUSED → LIMITED_LIVE if quality >= 0.10 (stuck prevention)
            if s.lifecycle_state == "PAUSED" and s.strategy_quality >= 0.10:
                s.lifecycle_state = "LIMITED_LIVE"
                s.allocated_budget_try = s.max_entry_try * 3
            if s.lifecycle_state == "ROLLBACK_REQUIRED" and s.strategy_quality >= 0.15:
                s.lifecycle_state = "PAUSED"
            defaults[sid] = s
    state.strategies = defaults

    # Load historical context for informed initial decisions
    hist = get_historical_context()

    # Paper trading portfolio
    portfolio = PaperPortfolio.load()
    print(f"  Paper Portfolio: {portfolio.balance_try:.0f} TRY, {portfolio.total_trades} trades, {portfolio.win_rate():.0%} WR")
    
    # Real exchange balances
    live_trading = os.environ.get("BINANCE_LIVE_TRADING", "").lower() == "true"
    if live_trading:
        try:
            bb = get_binance_balances()
            if isinstance(bb, dict) and 'error' not in str(bb):
                print(f"  Binance: {len(bb)} assets")
        except Exception:
            pass
        try:
            bt = get_btcturk_balances()
            if isinstance(bt, dict) and 'error' not in str(bt):
                total_try = sum(d['total'] for d in bt.values() if isinstance(d, dict) and d.get('asset') == 'TRY')
                print(f"  BTCTürk: {len(bt)} assets, {bt.get('TRY', {}).get('total', 0):.0f} TRY")
        except Exception:
            pass
        print(f"  ⚠️  LIVE TRADING ACTIVE — gerçek emirler gönderilecek")
    print()
    for symbol, data in hist.get("symbols", {}).items():
        daily = data.get("intervals", {}).get("daily", {})
        if daily:
            print(f"  Historical: {symbol} RSI={daily.get('rsi')} MACD={daily.get('macd_histogram')} "
                  f"Δ={daily.get('price_change_pct')}% vol={daily.get('volatility')}%")

    mode = "once" if args.once else f"every {args.interval}s"
    sources = "Binance"
    if taapi_ok:
        sources += " + TAAPI"
    sources += " + GDELT + CoinGecko + CT/CD"
    print(f"♺ Learning loop ({sources}) — {len(state.strategies)} strategies, {mode}")
    print()

    cycle_count = 0
    max_cycles = args.cycles or (1 if args.once else 0)

    try:
        while True:
            micro_snapshots, tech_snapshots = fetch_binance()
            prices = fetch_prices()
            for sym, price in prices.items():
                if sym not in state.last_prices:
                    state.last_prices[sym] = price
                state.last_prices["_current_" + sym] = price

            if taapi_ok:
                for strategy in state.strategies.values():
                    symbol = SYMBOL_MAP.get(strategy.strategy_id)
                    if not symbol:
                        continue
                    taapi_snap = fetch_and_normalize(
                        config=taapi_config, symbol=symbol,
                        symbol_hash=symbol, timeframe="4h",
                    )
                    if taapi_snap and taapi_snap.indicators:
                        tech_snapshots.append(taapi_snap)
                        # Smart strategy analysis from real indicators
                        score = compute_indicator_score(taapi_snap.indicators)
                        # Blend smart score with existing strategy state
                        strategy.current_edge_score = round(strategy.current_edge_score * 0.6 + max(0, score["edge_score"]) * 0.4, 3)
                        strategy.current_risk_score = round(strategy.current_risk_score * 0.6 + score["risk_score"] * 0.4, 3)
                        strategy.current_confidence = round(strategy.current_confidence * 0.6 + score["confidence"] * 0.4, 3)

            # Fetch news sentiment (graceful — skip on failure)
            news_sentiment: dict[str, float] = {}
            try:
                news, headlines = fetch_all_news_with_headlines(["crypto", "macro", "geopolitical"], max_per_category=5)
                news_sentiment = compute_news_sentiment_summary(news)

                # Deepseek AI-enhanced analysis
                if headlines:
                    try:
                        ai = analyze_headlines(headlines[:10])
                        ai_sentiment = compute_aggregate_sentiment(ai)
                        news_sentiment["ai_risk_score"] = ai_sentiment.get("risk_score", 0.3)
                        news_sentiment["ai_confidence"] = ai_sentiment.get("avg_confidence", 0.0)
                        if ai_sentiment.get("risk_score", 0.0) > news_sentiment.get("macro_risk_score", 0.0):
                            news_sentiment["macro_risk_score"] = ai_sentiment["risk_score"]
                    except Exception:
                        pass
            except Exception:
                pass

            # CoinGecko market sentiment
            try:
                cg = fetch_coingecko_sentiment()
                fg = cg.get("fear_greed_index", 50)
                if fg > 70:
                    news_sentiment["market_greed"] = 1.0
                elif fg < 30:
                    news_sentiment["market_fear"] = 1.0
                news_sentiment["fear_greed_index"] = fg / 100
            except Exception:
                pass

            # CoinTelegraph RSS sentiment
            try:
                ct = fetch_cointelegraph_sentiment()
                if ct.get("headline_count", 0) > 0:
                    news_sentiment["ct_sentiment"] = ct.get("sentiment", 0)
                    news_sentiment["ct_bullish"] = ct.get("bullish_ratio", 0)
            except Exception:
                pass

            # CoinDesk RSS sentiment
            try:
                cd = fetch_coindesk_sentiment()
                if cd.get("headline_count", 0) > 0:
                    news_sentiment["cd_sentiment"] = cd.get("sentiment", 0)
            except Exception:
                pass

            state = run_cycle_with_real_data(state, micro_snapshots, tech_snapshots, news_sentiment)
            cycle_count += 1

            # Walk-forward validation: every 50 cycles, score strategies by recent PnL
            if state.cycle % 50 == 0 and state.cycle > 0:
                try:
                    import json as _json
                    trades_log = _json.loads(open("data/paper_trades/trades.jsonl").read() + "\n]") if False else []
                    # Score from portfolio
                    for sid, s in state.strategies.items():
                        # Check recent closed trades for this strategy
                        recent_pnl = 0.0
                        recent_wins = 0
                        recent_total = 0
                        trade_file = "data/paper_trades/trades.jsonl"
                        try:
                            for line in open(trade_file):
                                if not line.strip(): continue
                                t = _json.loads(line)
                                if t.get("strategy_id") == sid and t.get("action") == "CLOSE":
                                    recent_pnl += t.get("pnl_try", 0)
                                    recent_total += 1
                                    if t.get("win"): recent_wins += 1
                        except Exception:
                            pass
                        
                        # Adjust quality based on actual results
                        if recent_total >= 3:
                            wr = recent_wins / recent_total
                            if wr > 0.6 and recent_pnl > 0:
                                s.strategy_quality = min(0.95, s.strategy_quality + 0.10)
                                print(f"  ⬆️  {sid}: WR={wr:.0%} PnL={recent_pnl:+.1f} → Q={s.strategy_quality:.2f}")
                            elif wr < 0.4 or recent_pnl < -10:
                                s.strategy_quality = max(0.05, s.strategy_quality - 0.10)
                                print(f"  ⬇️  {sid}: WR={wr:.0%} PnL={recent_pnl:+.1f} → Q={s.strategy_quality:.2f}")
                except Exception:
                    pass

            # Periodic backtest (every 100 cycles) to re-optimize strategies
            if state.cycle % 100 == 0:
                try:
                    bt = run_backtest_pipeline()
                    for sid, s in state.strategies.items():
                        if sid in bt:
                            optimal = bt[sid].get("optimal_rsi", {}).get("best_params", {})
                            if optimal and hasattr(state, 'ledger_events'):
                                state.ledger_events.append({
                                    "id": f"bt-{state.cycle}", "ts_ms": int(__import__('time').time() * 1000),
                                    "event_type": "BACKTEST_COMPLETED", "severity": "INFO",
                                    "source": "backtest-engine", "strategy_id": sid, "adapter_id": None,
                                    "message": f"Optimal RSI({optimal.get('rsi_period')},{optimal.get('oversold')}) hold={optimal.get('hold_days')}d"
                                })
                except Exception:
                    pass

            strategies = list(state.strategies.values())
            total_pnl = round(sum(s.pnl_today_try for s in strategies), 1)
            active_cnt = sum(1 for s in strategies if s.lifecycle_state in ("ACTIVE_LIVE", "LIMITED_LIVE") and s.enabled)

            print(
                f"  [{state.cycle:04d}] signals={state.total_signals_processed} "
                f"★={state.total_live_candidates} ✗={state.total_blocks} "
                f"active={active_cnt} PnL={total_pnl:+.1f}TRY α={state.adaptive_alpha:.3f} "
                f"acc={state.correct_predictions}/{state.total_predictions} mem={len(state.memory_records)}"
            )

            path = export_snapshot(state)
            # Inject paper portfolio into snapshot for panel
            try:
                prices = fetch_prices()
                pv = portfolio.total_value(prices)
                pnl = portfolio.total_pnl(prices)
                with open(path, "r") as f:
                    snap = json.loads(f.read())
                snap["paper_portfolio"] = {
                    "balance_try": round(portfolio.balance_try, 2),
                    "total_value_try": pv,
                    "total_pnl_try": pnl,
                    "total_trades": portfolio.total_trades,
                    "winning_trades": portfolio.winning_trades,
                    "win_rate": portfolio.win_rate(),
                    "open_positions": len(portfolio.positions),
                }
                with open(path, "w") as f:
                    json.dump(snap, f, indent=2)
            except Exception:
                pass
            if state.cycle % 5 == 0:
                save_state(state)
                # Critical event alerts
                if state.kill_switch_active:
                    alert_kill_switch(f"Kill switch active after {state.cycle} cycles")
                for sid, s in state.strategies.items():
                    if s.lifecycle_state == "PAUSED" and s.strategy_quality < 0.10:
                        alert_strategy_paused(sid, s.strategy_quality)
                # Run Gel.Al guard cycle
                try:
                    qualities = {sid: s.strategy_quality for sid, s in state.strategies.items()}
                    avg_q = sum(qualities.values()) / max(1, len(qualities))
                    phase = "shadow"
                    if avg_q > 0.4 and state.cycle > 100: phase = "canary"
                    if avg_q > 0.6 and state.cycle > 200: phase = "limited_live"
                    if avg_q > 0.8 and state.cycle > 500: phase = "active_live"
                    run_guard_cycle(phase, qualities, state.kill_switch_active)
                except Exception:
                    pass

                # Reactivate paused strategies that have paper positions to unwind
                for sid, s in state.strategies.items():
                    if s.lifecycle_state == "PAUSED" and sid in portfolio.positions:
                        s.lifecycle_state = "LIMITED_LIVE"
                        s.allocated_budget_try = s.max_entry_try * 3

                # Execute trades with indicator-based decisions
                for sid, s in state.strategies.items():
                    if s.lifecycle_state not in ("ACTIVE_LIVE", "LIMITED_LIVE"):
                        continue
                    if s.strategy_quality < 0.10:
                        continue
                    symbol = "BTCUSDT" if "btc" in sid else "ETHUSDT" if "eth" in sid else "SOLUSDT" if "sol" in sid else "BNBUSDT"
                    price = prices.get(symbol, 0)
                    if not price:
                        continue
                    
                    # Ensemble: count how many strategies agree on direction
                    bullish_votes = sum(1 for st in state.strategies.values() 
                                       if st.current_edge_score > 0.25 and st.lifecycle_state in ("ACTIVE_LIVE","LIMITED_LIVE"))
                    bearish_votes = sum(1 for st in state.strategies.values() 
                                       if st.current_edge_score < 0.18 and st.lifecycle_state in ("ACTIVE_LIVE","LIMITED_LIVE"))
                    total_active = sum(1 for st in state.strategies.values() if st.lifecycle_state in ("ACTIVE_LIVE","LIMITED_LIVE"))
                    consensus = bullish_votes / max(1, total_active)
                    
                    # Correlation check: if BTC and ETH both open, reduce new positions
                    open_symbols = set()
                    for psid in portfolio.positions:
                        if "btc" in psid: open_symbols.add("BTC")
                        if "eth" in psid: open_symbols.add("ETH")
                        if "sol" in psid: open_symbols.add("SOL")
                        if "bnb" in psid: open_symbols.add("BNB")
                    
                    # Dynamic entry: stronger when ensemble agrees
                    # Lower threshold in oversold/overbought extremes
                    base_threshold = 0.22
                    if s.current_risk_score < 0.1: base_threshold = 0.15  # Very low risk = easier entry
                    if s.current_confidence > 0.6: base_threshold = 0.12   # High confidence = easier
                    
                    entry_ok = (s.current_edge_score >= base_threshold and s.current_risk_score < 0.65)
                    # Boost entry based on consensus
                    if consensus > 0.6: entry_ok = s.current_edge_score >= max(0.12, base_threshold - 0.05)  # Strong consensus = easier
                    elif consensus < 0.3: entry_ok = s.current_edge_score >= min(0.30, base_threshold + 0.05)  # Weak consensus = strict
                    # Entry: edge >= 0.22, risk < 0.65
                    # Dynamic position sizing
                    if sid not in portfolio.positions and entry_ok:
                        # 1. Base position from Kelly: f = edge * confidence / risk
                        win_prob = s.current_confidence if s.current_confidence > 0 else 0.5
                        risk_adj = max(0.01, s.current_risk_score)
                        kelly = (win_prob * s.current_edge_score - (1 - win_prob) * risk_adj) / max(0.01, s.current_edge_score)
                        kelly = max(0.01, min(kelly, 0.15))
                        
                        # 2. Available balance check
                        total_value = portfolio.total_value(prices)
                        max_position = total_value * kelly
                        
                        # 3. Volatility adjustment
                        vol_adj = 1.0
                        if s.current_risk_score > 0.5: vol_adj = 0.5
                        elif s.current_risk_score < 0.2: vol_adj = 1.5
                        
                        # 4. Exposure limit — max 20% in one position
                        current_exposure = sum(pd.amount_try for pd in portfolio.positions.values()) if portfolio.positions else 0
                        remaining = total_value * 0.20 - current_exposure
                        
                        # 5. Exchange-specific limits
                        if live_trading:
                            max_position = min(max_position, 500)  # Max 500 TRY/order safety
                        
                        amt = min(max_position * vol_adj, remaining, s.max_entry_try, 500)
                        amt = max(amt, 25)  # Min 25 TRY
                        
                        if live_trading:
                            executed = False
                            # Try Binance
                            try:
                                result = place_market_buy(symbol, amt)
                                if result.status not in ("ERROR", "REJECTED", "SIMULATED"):
                                    portfolio.open_position(sid, symbol, price, amt)
                                    executed = True
                                    state.ledger_events.append({
                                        "id": f"live-{state.cycle}", "ts_ms": int(time.time() * 1000),
                                        "event_type": "LIVE_TRADE", "severity": "INFO",
                                        "source": "binance", "strategy_id": sid,
                                        "message": f"ENTRY {symbol} {amt:.0f} TRY @ {price:.0f} edge={s.current_edge_score:.2f}"
                                    })
                                    print(f"  🟢 ALIM  {symbol} {amt:.0f} TRY @ {price:.0f} (edge={s.current_edge_score:.2f})")
                            except Exception:
                                pass
                            
                            # Fallback to BTCTürk
                            if not executed:
                                try:
                                    bt_symbol = symbol.replace("USDT", "TRY")
                                    btcturk_order(bt_symbol, "BUY", quote_amount=amt)
                                    portfolio.open_position(sid, bt_symbol, price, amt)
                                    state.ledger_events.append({
                                        "id": f"live-{state.cycle}", "ts_ms": int(time.time() * 1000),
                                        "event_type": "LIVE_TRADE", "severity": "INFO",
                                        "source": "btcturk", "strategy_id": sid,
                                        "message": f"ENTRY {bt_symbol} {amt:.0f} TRY @ {price:.0f} edge={s.current_edge_score:.2f}"
                                    })
                                    print(f"  🟢 BTCTÜRK {bt_symbol} {amt:.0f} TRY @ {price:.0f} (edge={s.current_edge_score:.2f})")
                                except Exception:
                                    pass
                        
                        if sid not in portfolio.positions:
                            portfolio.open_position(sid, symbol, price, min(amt, portfolio.balance_try * 0.1))
                            print(f"  📄 PAPER {symbol} {min(amt, portfolio.balance_try * 0.1):.0f} TRY @ {price:.0f}")
                    
                    # Smart exit: take-profit, trailing stop, risk guard
                    elif sid in portfolio.positions:
                        pos = portfolio.positions[sid]
                        pnl_pct = (price - pos.entry_price) / pos.entry_price if pos.entry_price > 0 else 0
                        should_exit = False
                        exit_reason = ""
                        
                        # Dynamic exit thresholds based on volatility
                        vol_factor = 1.0 + s.current_risk_score  # 1.0-1.9
                        tp_target = 0.01 * vol_factor  # 1-1.9% take-profit (volatility-adjusted)
                        sl_limit = -0.01 * vol_factor  # 1-1.9% stop-loss
                        
                        # Determine edge trend (improving or deteriorating?)
                        edge_improving = s.current_edge_score > (getattr(s, '_prev_edge', s.current_edge_score) or s.current_edge_score - 0.01)
                        setattr(s, '_prev_edge', s.current_edge_score)  # Track for next cycle
                        
                        # Take-profit: dynamic target based on edge strength
                        if pnl_pct > tp_target:
                            should_exit = True
                            exit_reason = f"TP +{pnl_pct*100:.1f}% (target={tp_target*100:.1f}%)"
                        # Stop-loss: dynamic limit
                        elif pnl_pct < sl_limit:
                            should_exit = True
                            exit_reason = f"SL {pnl_pct*100:.1f}% (limit={sl_limit*100:.1f}%)"
                        # Edge rapidly deteriorating → exit early
                        elif not edge_improving and s.current_edge_score < 0.25 and pnl_pct > 0:
                            should_exit = True
                            exit_reason = f"edge fading ({s.current_edge_score:.2f}) lock +{pnl_pct*100:.1f}%"
                        # Risk guard: high risk → exit
                        elif s.current_risk_score > 0.70:
                            should_exit = True
                            exit_reason = f"high risk ({s.current_risk_score:.2f})"
                        # Force rotation every 15 cycles to prevent stagnation
                        elif state.cycle % 15 == 0:
                            should_exit = True
                            exit_reason = f"scheduled rotation (cycle {state.cycle})"
                        
                        if should_exit:
                            # Execute real sell if position was on exchange
                            if live_trading:
                                try:
                                    place_market_sell(symbol, pos.quantity)
                                except Exception:
                                    pass
                            closed = portfolio.close_position(sid, price)
                            pnl = closed['pnl_try'] if closed else 0
                            # Deduct trading fees (0.15% per trade = 0.3% round-trip)
                            fee = (pos.amount_try + (pos.amount_try + pnl)) * 0.0015
                            pnl -= fee
                            state.ledger_events.append({
                                "id": f"exit-{state.cycle}", "ts_ms": int(time.time() * 1000),
                                "event_type": "SMART_EXIT", "severity": "INFO",
                                "source": "risk-engine", "strategy_id": sid,
                                "message": f"EXIT {symbol}: {exit_reason} | PnL={pnl:+.2f} TRY (fee={fee:.2f})"
                            })
                            print(f"  🔴 SATIŞ {symbol}: {exit_reason} | PnL={pnl:+.2f} TRY")
                
                portfolio.save()
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
