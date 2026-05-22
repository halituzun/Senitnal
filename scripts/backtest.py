#!/usr/bin/env python3
"""Backtest engine — validates strategies against historical data.

Runs strategy logic against 90 days of Binance data to:
1. Find optimal parameters (RSI threshold, MACD, Bollinger)
2. Calculate realistic win rates and expectancy
3. Feed results back into learning loop strategy config
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scripts.fetch_historical import get_historical_context

DATA_DIR = Path("data/historical")


def load_historical_klines(symbol: str, interval: str = "daily") -> list[dict[str, Any]]:
    """Load kline data for a symbol from cached historical data."""
    hist = get_historical_context()
    symbol_data = hist.get("symbols", {}).get(symbol, {})
    interval_data = symbol_data.get("intervals", {}).get(interval, {})
    # Raw klines are not stored in the summary — need to fetch fresh
    return []


def compute_rsi_series(closes: list[float], period: int = 14) -> list[float]:
    """Compute RSI time series from closing prices."""
    if len(closes) < period + 1:
        return [50.0] * len(closes)
    rsi_values = [50.0] * period
    for i in range(period, len(closes)):
        gains = 0.0
        losses = 0.0
        for j in range(i - period + 1, i + 1):
            diff = closes[j] - closes[j - 1]
            if diff > 0:
                gains += diff
            else:
                losses -= diff
        avg_gain = gains / period
        avg_loss = losses / period
        if avg_loss == 0:
            rsi_values.append(100.0)
        else:
            rs = avg_gain / avg_loss
            rsi_values.append(100.0 - (100.0 / (1.0 + rs)))
    return rsi_values


def backtest_rsi_strategy(
    closes: list[float],
    rsi_period: int = 14,
    oversold_threshold: float = 30,
    overbought_threshold: float = 70,
    hold_days: int = 3,
) -> dict[str, Any]:
    """Backtest a simple RSI mean-reversion strategy.

    Buy when RSI < oversold_threshold, sell after hold_days.
    """
    if len(closes) < rsi_period + hold_days + 1:
        return {"trades": 0, "win_rate": 0, "total_return_pct": 0, "expectancy": 0}

    rsi = compute_rsi_series(closes, rsi_period)
    trades = []
    in_position = False
    entry_price = 0.0
    entry_idx = 0

    for i in range(rsi_period, len(closes) - hold_days):
        if not in_position and rsi[i] < oversold_threshold:
            entry_price = closes[i]
            entry_idx = i
            in_position = True
        elif in_position and i - entry_idx >= hold_days:
            exit_price = closes[i]
            pnl_pct = (exit_price - entry_price) / entry_price
            trades.append({
                "entry_idx": entry_idx,
                "exit_idx": i,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "pnl_pct": round(pnl_pct * 100, 2),
                "win": pnl_pct > 0,
            })
            in_position = False

    if not trades:
        return {"trades": 0, "win_rate": 0, "total_return_pct": 0, "expectancy": 0, "sharpe": 0}

    wins = sum(1 for t in trades if t["win"])
    win_rate = wins / len(trades)
    total_return = sum(t["pnl_pct"] for t in trades)
    avg_win = sum(t["pnl_pct"] for t in trades if t["win"]) / max(1, wins)
    avg_loss = sum(t["pnl_pct"] for t in trades if not t["win"]) / max(1, len(trades) - wins)
    expectancy = (win_rate * avg_win) + ((1 - win_rate) * avg_loss)

    returns = [t["pnl_pct"] for t in trades]
    mean_ret = sum(returns) / len(returns)
    variance = sum((r - mean_ret) ** 2 for r in returns) / len(returns)
    sharpe = (mean_ret / (variance ** 0.5)) * (252 ** 0.5) if variance > 0 else 0

    return {
        "trades": len(trades),
        "wins": wins,
        "win_rate": round(win_rate, 3),
        "total_return_pct": round(total_return, 2),
        "expectancy": round(expectancy, 2),
        "sharpe": round(sharpe, 2),
        "avg_win_pct": round(avg_win, 2),
        "avg_loss_pct": round(avg_loss, 2),
        "best_params": {
            "rsi_period": rsi_period,
            "oversold": oversold_threshold,
            "hold_days": hold_days,
        },
    }


def optimize_rsi_params(closes: list[float]) -> dict[str, Any]:
    """Find optimal RSI strategy parameters via grid search."""
    best_result = None
    best_score = -999

    periods = [7, 14, 21]
    oversolds = [20, 25, 30, 35, 40]
    holds = [1, 2, 3, 5, 7]

    for period in periods:
        for oversold in oversolds:
            for hold in holds:
                result = backtest_rsi_strategy(closes, period, oversold, 70, hold)
                if result["trades"] < 5:
                    continue
                # Score: prioritize expectancy and win_rate
                score = result["expectancy"] * result["win_rate"] * result["sharpe"]
                if score > best_score:
                    best_score = score
                    best_result = result

    return best_result or backtest_rsi_strategy(closes)


def run_backtest_pipeline() -> dict[str, Any]:
    """Run full backtest pipeline across all symbols and strategies."""
    from services.intelligence_adapters.binance_adapter import fetch_klines

    symbols = {"BTCUSDT": "btc-momentum-v3", "ETHUSDT": "eth-mean-reversion", "SOLUSDT": "sol-breakout-alpha"}
    results: dict[str, Any] = {}

    for symbol, strategy_id in symbols.items():
        try:
            klines = fetch_klines(symbol, "1d", 90)
            closes = [float(k[4]) for k in klines if isinstance(k, list) and len(k) > 4]
        except Exception:
            print(f"  {symbol}: fetch failed, skipping")
            continue

        if len(closes) < 30:
            continue

        rsi_result = backtest_rsi_strategy(closes)
        optimal = optimize_rsi_params(closes)

        results[strategy_id] = {
            "symbol": symbol,
            "candles": len(closes),
            "current_price": closes[-1] if closes else 0,
            "price_change_90d_pct": round((closes[-1] / closes[0] - 1) * 100, 2) if closes and closes[0] > 0 else 0,
            "default_rsi": rsi_result,
            "optimal_rsi": optimal,
        }
        print(f"  {symbol}: {rsi_result['trades']} trades, WR={rsi_result['win_rate']:.0%}, "
              f"expectancy={rsi_result['expectancy']:.1f}%, sharpe={rsi_result['sharpe']:.1f}")

    return results


def save_backtest_results(results: dict[str, Any]) -> Path:
    """Save backtest results to JSON."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / "backtest_results.json"
    with open(path, "w") as f:
        json.dump(results, f, indent=2)
    return path


if __name__ == "__main__":
    print("Running backtest pipeline...")
    results = run_backtest_pipeline()
    path = save_backtest_results(results)
    print(f"\nSaved → {path}")
