#!/usr/bin/env python3
"""Historical data pipeline — fetch, compute, and store market history.

Fetches from Binance public API (no key needed):
- Daily klines (90 days)
- 4h klines (30 days) for RSI/MACD calculation

Stores as JSON in data/historical/ for persistence across sessions.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
DATA_DIR = Path("data/historical")

INTERVALS = {
    "1d": {"limit": 90, "label": "daily"},
    "4h": {"limit": 180, "label": "4hourly"},
}


def _fetch_klines(symbol: str, interval: str, limit: int) -> list[dict[str, Any]]:
    """Fetch klines from Binance and return normalized dicts."""
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    req = Request(url, headers={"Accept": "application/json"})
    with urlopen(req, timeout=15) as resp:
        raw = json.loads(resp.read())

    result: list[dict[str, Any]] = []
    for k in raw:
        if not isinstance(k, list) or len(k) < 6:
            continue
        result.append({
            "ts": int(k[0]),
            "open": float(k[1]),
            "high": float(k[2]),
            "low": float(k[3]),
            "close": float(k[4]),
            "volume": float(k[5]),
        })
    return result


def compute_rsi(closes: list[float], period: int = 14) -> float:
    """Compute RSI for the latest candle."""
    if len(closes) < period + 1:
        return 50.0
    gains = sum(max(0, closes[i] - closes[i - 1]) for i in range(len(closes) - period, len(closes)))
    losses = sum(max(0, closes[i - 1] - closes[i]) for i in range(len(closes) - period, len(closes)))
    avg_gain = gains / period
    avg_loss = losses / period
    if avg_loss == 0:
        return 100.0
    return 100.0 - (100.0 / (1.0 + avg_gain / avg_loss))


def compute_macd(closes: list[float]) -> tuple[float, float, float]:
    """Compute MACD line, signal, histogram."""
    if len(closes) < 26:
        return 0.0, 0.0, 0.0

    def ema(data: list[float], period: int) -> float:
        k = 2.0 / (period + 1)
        ema_val = sum(data[:period]) / period
        for price in data[period:]:
            ema_val = price * k + ema_val * (1 - k)
        return ema_val

    ema12 = ema(closes, 12)
    ema26 = ema(closes, 26)
    macd_line = ema12 - ema26

    # Signal line (9-period EMA of MACD) — simplified to last value
    signal_line = macd_line * 0.8
    histogram = macd_line - signal_line

    return round(macd_line, 6), round(signal_line, 6), round(histogram, 6)


def compute_bollinger(closes: list[float], period: int = 20) -> dict[str, float]:
    """Compute Bollinger Bands."""
    if len(closes) < period:
        return {"bb_upper": 0, "bb_middle": 0, "bb_lower": 0, "bb_width": 0}

    recent = closes[-period:]
    sma = sum(recent) / period
    variance = sum((x - sma) ** 2 for x in recent) / period
    std = variance ** 0.5

    return {
        "bb_upper": round(sma + 2 * std, 2),
        "bb_middle": round(sma, 2),
        "bb_lower": round(sma - 2 * std, 2),
        "bb_width": round((4 * std / sma) * 100, 2) if sma > 0 else 0,
    }


def fetch_and_compute(symbols: tuple[str, ...] = SYMBOLS) -> dict[str, Any]:
    """Fetch historical data and compute indicators for all symbols."""
    result: dict[str, Any] = {
        "fetched_at_ms": int(time.time() * 1000),
        "symbols": {},
    }

    for symbol in symbols:
        symbol_data: dict[str, Any] = {"intervals": {}}

        for interval, cfg in INTERVALS.items():
            try:
                klines = _fetch_klines(symbol, interval, cfg["limit"])
            except Exception as e:
                print(f"  {symbol} {interval}: fetch failed ({e})")
                continue

            closes = [k["close"] for k in klines]
            rsi = compute_rsi(closes)
            macd_line, macd_signal, macd_hist = compute_macd(closes)
            bb = compute_bollinger(closes)

            # Price stats
            prices = closes
            high = max(k["high"] for k in klines)
            low = min(k["low"] for k in klines)

            symbol_data["intervals"][cfg["label"]] = {
                "candles": len(klines),
                "first_ts": klines[0]["ts"] if klines else 0,
                "last_ts": klines[-1]["ts"] if klines else 0,
                "last_close": closes[-1] if closes else 0,
                "high": round(high, 2),
                "low": round(low, 2),
                "price_change_pct": round((closes[-1] / closes[0] - 1) * 100, 2) if closes and closes[0] > 0 else 0,
                "rsi": round(rsi, 1),
                "macd_line": macd_line,
                "macd_signal": macd_signal,
                "macd_histogram": macd_hist,
                **bb,
                "volatility": round((high - low) / closes[-1] * 100, 2) if closes and closes[-1] > 0 else 0,
            }

        result["symbols"][symbol] = symbol_data
        daily = symbol_data["intervals"].get("daily", {})
        print(f"  {symbol}: {daily.get('candles', 0)} daily candles, RSI={daily.get('rsi', '?')}, Δ={daily.get('price_change_pct', '?')}%")

    return result


def save_historical(data: dict[str, Any]) -> Path:
    """Save historical data to JSON file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / "market_history.json"
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    return path


def load_historical() -> dict[str, Any] | None:
    """Load previously saved historical data."""
    path = DATA_DIR / "market_history.json"
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)  # type: ignore[no-any-return]


def get_historical_context(symbols: tuple[str, ...] = SYMBOLS) -> dict[str, Any]:
    """Get historical context — loads cached if fresh, else fetches."""
    cached = load_historical()
    if cached:
        age_ms = int(time.time() * 1000) - cached.get("fetched_at_ms", 0)
        if age_ms < 3_600_000:  # Cache for 1 hour
            return cached

    data = fetch_and_compute(symbols)
    save_historical(data)
    return data


if __name__ == "__main__":
    print("Fetching historical market data...")
    data = fetch_and_compute()
    path = save_historical(data)
    print(f"\nSaved → {path}")
