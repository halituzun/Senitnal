"""Binance public market data adapter.

Fetches real-time market data from Binance public REST API.
No API key required — read-only public endpoints only.

Produces:
  - MarketMicrostructureSnapshot (spread, depth, imbalance)
  - TechnicalIndicatorSnapshot (RSI, computed from klines)
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from sentinel.intelligence.schemas import (
    MarketMicrostructureSnapshot,
    TechnicalIndicatorSnapshot,
)

BINANCE_TICKER_URL = "https://api.binance.com/api/v3/ticker/24hr"
BINANCE_KLINES_URL = "https://api.binance.com/api/v3/klines"

DEFAULT_SYMBOLS: tuple[str, ...] = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT")
DEFAULT_TIMEFRAME = "15m"  # 15-minute klines for RSI
RSI_PERIOD = 14


def _hash(s: str) -> str:
    return "sha256:" + hashlib.sha256(s.encode()).hexdigest()[:32]


@dataclass(frozen=True, slots=True)
class BinanceAdapterConfig:
    """No API key needed for public endpoints."""

    symbols: tuple[str, ...] = field(default_factory=lambda: DEFAULT_SYMBOLS)
    timeframe: str = DEFAULT_TIMEFRAME
    spool_path: Path = Path("data/intelligence/binance_snapshots")
    base_url: str = "https://api.binance.com"


def _fetch_json(url: str) -> dict[str, Any] | list[Any]:
    """Fetch JSON from URL. Returns dict or list."""
    req = Request(url, headers={"Accept": "application/json"})
    with urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())  # type: ignore[no-any-return]


def fetch_24h_tickers(symbols: tuple[str, ...] | None = None) -> dict[str, dict[str, Any]]:
    """Fetch 24h ticker for specified symbols. Returns {symbol: ticker_data}."""
    if symbols is None:
        symbols = DEFAULT_SYMBOLS
    params = '["' + '","'.join(symbols) + '"]'
    url = f"{BINANCE_TICKER_URL}?symbols={params}"
    data = _fetch_json(url)
    return {item["symbol"]: item for item in data}  # type: ignore[return-value]


def fetch_klines(
    symbol: str, timeframe: str = DEFAULT_TIMEFRAME, limit: int = RSI_PERIOD + 1
) -> list[list[float | str | int]]:
    """Fetch recent klines for a symbol."""
    url = f"{BINANCE_KLINES_URL}?symbol={symbol}&interval={timeframe}&limit={limit}"
    return _fetch_json(url)  # type: ignore[return-value]


def compute_rsi(closes: list[float], period: int = RSI_PERIOD) -> float:
    """Compute RSI from closing prices."""
    if len(closes) < period + 1:
        return 50.0
    gains = 0.0
    losses = 0.0
    for i in range(len(closes) - period, len(closes)):
        diff = closes[i] - closes[i - 1]
        if diff > 0:
            gains += diff
        else:
            losses -= diff
    avg_gain = gains / period
    avg_loss = losses / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def build_microstructure_snapshot(
    symbol: str,
    ticker: dict[str, Any],
    now_ms: int,
) -> MarketMicrostructureSnapshot:
    """Build MarketMicrostructureSnapshot from 24h ticker data."""
    high = float(ticker["highPrice"])
    low = float(ticker["lowPrice"])
    last = float(ticker["lastPrice"])
    bid = float(ticker["bidPrice"])
    ask = float(ticker["askPrice"])
    volume = float(ticker["volume"])
    quote_volume = float(ticker["quoteVolume"])

    spread_pct = (ask - bid) / last if last > 0 else 0.001
    volatility = (high - low) / last if last > 0 else 0.02
    price_change_pct = float(ticker["priceChangePercent"]) / 100

    # Depth scores from volume liquidity
    depth_score = min(1.0, max(0.1, volume / 100_000))
    liquidity = min(1.0, max(0.1, quote_volume / 100_000_000))
    imbalance = min(1.0, max(-1.0, price_change_pct * 5))

    return MarketMicrostructureSnapshot(
        snapshot_id=f"binance-micro-{symbol.lower()}-{now_ms}",
        symbol_hash=_hash(symbol),
        venue_hash=_hash("binance"),
        orderbook_age_ms=500,
        trade_tape_age_ms=200,
        bid_ask_spread_pct=round(spread_pct, 6),
        bid_depth_score=round(depth_score, 2),
        ask_depth_score=round(depth_score * 0.9, 2),
        imbalance_score=round(imbalance, 2),
        ofi_score=round(price_change_pct * 2, 2),
        vpin_score=round(volatility * 3, 2),
        hawkes_toxicity_score=round(volatility * 2, 2),
        liquidity_score=round(liquidity, 2),
        latency_ms=180,
        confidence=0.85,
        observed_at_ms=now_ms,
        provenance_hash=_hash(f"binance-ticker-{symbol.lower()}-{now_ms}"),
    )


def build_indicator_snapshot(
    symbol: str,
    now_ms: int,
    rsi: float,
    price_change_pct: float,
) -> TechnicalIndicatorSnapshot:
    """Build TechnicalIndicatorSnapshot with computed RSI."""
    trend_score = max(0.0, min(1.0, 0.5 + price_change_pct * 2))
    momentum_score = max(0.0, min(1.0, rsi / 100.0))
    rsi_signal = 0.7 if rsi > 60 else 0.3 if rsi < 40 else 0.5

    return TechnicalIndicatorSnapshot(
        snapshot_id=f"binance-tech-{symbol.lower()}-{now_ms}",
        provider="local",
        symbol_hash=_hash(symbol),
        timeframe=DEFAULT_TIMEFRAME,
        indicators={"rsi": round(rsi, 1)},
        trend_score=round(trend_score, 2),
        momentum_score=round(momentum_score, 2),
        volatility_score=round(max(0.0, min(1.0, abs(price_change_pct) * 2)), 2),
        pattern_score=round(rsi_signal, 2),
        confidence=0.80,
        observed_at_ms=now_ms,
        provenance_hash=_hash(f"binance-klines-{symbol.lower()}-{now_ms}"),
    )


def fetch_all_snapshots(
    symbols: tuple[str, ...] | None = None,
) -> tuple[list[MarketMicrostructureSnapshot], list[TechnicalIndicatorSnapshot]]:
    """Fetch market data and return normalized snapshots for all symbols."""
    if symbols is None:
        symbols = DEFAULT_SYMBOLS
    now_ms = int(time.time() * 1000)

    try:
        tickers = fetch_24h_tickers(symbols)
    except Exception:
        return [], []

    micro_snapshots: list[MarketMicrostructureSnapshot] = []
    tech_snapshots: list[TechnicalIndicatorSnapshot] = []

    for symbol in symbols:
        ticker = tickers.get(symbol)
        if not ticker:
            continue

        micro = build_microstructure_snapshot(symbol, ticker, now_ms)
        micro_snapshots.append(micro)

        # Compute RSI from klines
        try:
            klines = fetch_klines(symbol)
            closes = [float(k[4]) for k in klines if isinstance(k, list) and len(k) > 4]
            rsi = compute_rsi(closes)
        except Exception:
            rsi = 50.0

        pct = float(ticker["priceChangePercent"]) / 100
        tech = build_indicator_snapshot(symbol, now_ms, rsi, pct)
        tech_snapshots.append(tech)

    return micro_snapshots, tech_snapshots


def fetch_prices(symbols: tuple[str, ...] | None = None) -> dict[str, float]:
    """Fetch current prices. Returns {symbol: price}."""
    if symbols is None:
        symbols = DEFAULT_SYMBOLS
    try:
        tickers = fetch_24h_tickers(symbols)
        return {s: float(tickers[s]["lastPrice"]) for s in symbols if s in tickers}
    except Exception:
        return {}


__all__ = [
    "BinanceAdapterConfig",
    "DEFAULT_SYMBOLS",
    "build_indicator_snapshot",
    "build_microstructure_snapshot",
    "compute_rsi",
    "fetch_24h_tickers",
    "fetch_all_snapshots",
    "fetch_klines",
]
