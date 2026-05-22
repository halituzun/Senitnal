"""CoinGecko adapter — free crypto market data.

No API key required for public endpoints.
Provides: price, 24h change, market cap, volume.
"""

from __future__ import annotations

import json
import time
from typing import Any
from urllib.request import Request, urlopen

BASE_URL = "https://api.coingecko.com/api/v3"

COINS = {
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "solana": "SOL",
}


def fetch_prices() -> dict[str, dict[str, float]]:
    """Fetch current prices and 24h changes. Returns {btc: {usd, change_pct}, ...}."""
    ids = ",".join(COINS.keys())
    url = f"{BASE_URL}/simple/price?ids={ids}&vs_currencies=usd&include_24hr_change=true"
    req = Request(url, headers={"Accept": "application/json"})
    with urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())

    result: dict[str, dict[str, float]] = {}
    for coin_id, symbol in COINS.items():
        if coin_id in data:
            result[symbol] = {
                "usd": float(data[coin_id].get("usd", 0)),
                "change_24h_pct": float(data[coin_id].get("usd_24h_change", 0)),
            }
    return result


def fetch_trending() -> list[dict[str, Any]]:
    """Fetch trending coins (top 7 by market cap)."""
    url = f"{BASE_URL}/search/trending"
    req = Request(url, headers={"Accept": "application/json"})
    with urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())

    coins = data.get("coins", [])
    result: list[dict[str, Any]] = []
    for c in coins[:7]:
        item = c.get("item", {})
        result.append({
            "name": item.get("name", ""),
            "symbol": item.get("symbol", ""),
            "market_cap_rank": item.get("market_cap_rank", 0),
            "score": item.get("score", 0),
        })
    return result


def fetch_global_data() -> dict[str, Any]:
    """Fetch global crypto market stats."""
    url = f"{BASE_URL}/global"
    req = Request(url, headers={"Accept": "application/json"})
    with urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read()).get("data", {})

    return {
        "total_market_cap_usd": data.get("total_market_cap", {}).get("usd", 0),
        "total_volume_24h_usd": data.get("total_volume", {}).get("usd", 0),
        "btc_dominance_pct": float(data.get("market_cap_percentage", {}).get("btc", 0)),
        "eth_dominance_pct": float(data.get("market_cap_percentage", {}).get("eth", 0)),
        "active_cryptocurrencies": data.get("active_cryptocurrencies", 0),
        "market_cap_change_24h_pct": float(data.get("market_cap_change_percentage_24h_usd", 0)),
        "fetched_at_ms": int(time.time() * 1000),
    }


def fetch_market_sentiment() -> dict[str, float]:
    """Compute market sentiment from CoinGecko + alternative.me data."""
    try:
        prices = fetch_prices()
        global_data = fetch_global_data()
    except Exception:
        prices = {}
        global_data = {}

    # Fear & Greed from alternative.me (free, no auth)
    fg_value = 50.0
    fg_label = "neutral"
    try:
        import json
        from urllib.request import Request, urlopen
        req = Request("https://api.alternative.me/fng/?limit=1", headers={"Accept": "application/json"})
        with urlopen(req, timeout=5) as resp:
            fng = json.loads(resp.read())
            fg_value = float(fng["data"][0]["value"])
            fg_label = fng["data"][0]["value_classification"]
    except Exception:
        pass

    changes = [v.get("change_24h_pct", 0) for v in prices.values()]
    avg_change = sum(changes) / len(changes) if changes else 0

    btc_dom = global_data.get("btc_dominance_pct", 50)
    mcap_change = global_data.get("market_cap_change_24h_pct", 0)

    return {
        "sentiment_change_pct": round(avg_change, 2),
        "fear_greed_index": round(fg_value / 100, 2),
        "fear_greed_value": fg_value,
        "fear_greed_label": fg_label,
        "btc_dominance": round(btc_dom, 1),
        "market_cap_change_pct": round(mcap_change, 2),
        "fetched_at_ms": int(time.time() * 1000),
    }


__all__ = [
    "fetch_global_data",
    "fetch_market_sentiment",
    "fetch_prices",
    "fetch_trending",
]
