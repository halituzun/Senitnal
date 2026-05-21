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
)
from services.intelligence_adapters.taapi_adapter import (
    TaapiConfig,
    fetch_and_normalize,
    is_enabled,
)
from services.intelligence_adapters.gdelt_adapter import (
    fetch_all_news,
    compute_news_sentiment_summary,
)
from sentinel.runtime.learning_loop import (
    DEFAULT_STRATEGIES,
    LearningState,
    export_snapshot,
    run_cycle_with_real_data,
)

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

    mode = "once" if args.once else f"every {args.interval}s"
    sources = "Binance"
    if taapi_ok:
        sources += " + TAAPI"
    sources += " + GDELT"
    print(f"♺ Learning loop ({sources}) — {len(state.strategies)} strategies, {mode}")
    print()

    cycle_count = 0
    max_cycles = args.cycles or (1 if args.once else 0)

    try:
        while True:
            micro_snapshots, tech_snapshots = fetch_binance()

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
            news_sentiment = {}
            try:
                news = fetch_all_news(["crypto", "macro", "geopolitical"], max_per_category=5)
                news_sentiment = compute_news_sentiment_summary(news)
            except Exception:
                pass

            state = run_cycle_with_real_data(state, micro_snapshots, tech_snapshots)
            cycle_count += 1

            strategies = list(state.strategies.values())
            total_pnl = round(sum(s.pnl_today_try for s in strategies), 1)
            active_cnt = sum(1 for s in strategies if s.lifecycle_state in ("ACTIVE_LIVE", "LIMITED_LIVE") and s.enabled)

            print(
                f"  [{state.cycle:04d}] signals={state.total_signals_processed} "
                f"★={state.total_live_candidates} ✗={state.total_blocks} "
                f"active={active_cnt} PnL={total_pnl:+.1f}TRY mem={len(state.memory_records)}"
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
