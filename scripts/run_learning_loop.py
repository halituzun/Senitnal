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
import time
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
    export_snapshot,
    run_cycle_with_real_data,
)
from scripts.fetch_historical import get_historical_context
from services.intelligence_adapters.coingecko_adapter import fetch_market_sentiment as fetch_coingecko_sentiment

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

    state = LearningState()
    state.strategies = {s.strategy_id: s for s in DEFAULT_STRATEGIES}

    # Load historical context for informed initial decisions
    hist = get_historical_context()
    for symbol, data in hist.get("symbols", {}).items():
        daily = data.get("intervals", {}).get("daily", {})
        if daily:
            print(f"  Historical: {symbol} RSI={daily.get('rsi')} MACD={daily.get('macd_histogram')} "
                  f"Δ={daily.get('price_change_pct')}% vol={daily.get('volatility')}%")

    mode = "once" if args.once else f"every {args.interval}s"
    sources = "Binance"
    if taapi_ok:
        sources += " + TAAPI"
    sources += " + GDELT + CoinGecko"
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
                    if taapi_snap:
                        tech_snapshots.append(taapi_snap)

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

            state = run_cycle_with_real_data(state, micro_snapshots, tech_snapshots, news_sentiment)
            cycle_count += 1

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
