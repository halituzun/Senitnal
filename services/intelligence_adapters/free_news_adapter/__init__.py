"""Free news adapters — CoinTelegraph RSS, CoinGecko trending.

No API keys required. Provides crypto news headlines for sentiment analysis.
"""

from __future__ import annotations

import re
import time
from typing import Any
from urllib.request import Request, urlopen


def fetch_cointelegraph_rss(limit: int = 10) -> list[dict[str, str]]:
    """Fetch CoinTelegraph RSS feed headlines."""
    url = "https://cointelegraph.com/rss"
    req = Request(url, headers={"Accept": "application/xml"})
    with urlopen(req, timeout=10) as resp:
        xml = resp.read().decode("utf-8", errors="ignore")

    titles = re.findall(r"<title>(.*?)</title>", xml)
    links = re.findall(r"<link>(.*?)</link>", xml)
    pubs = re.findall(r"<pubDate>(.*?)</pubDate>", xml)

    result: list[dict[str, str]] = []
    for i in range(1, min(limit + 1, len(titles))):
        result.append({
            "title": titles[i] if i < len(titles) else "",
            "link": links[i] if i < len(links) else "",
            "published": pubs[i] if i < len(pubs) else "",
        })
    return result


# Trend analysis keywords
BULLISH_KW = [
    "rally", "surge", "soar", "bullish", "breakout", "record", "milestone",
    "adoption", "partnership", "launch", "approval", "etf", "inflow",
    "accumulation", "upgrade", "growth", "raise", "funding", "breakthrough",
]

BEARISH_KW = [
    "crash", "plunge", "drop", "decline", "bearish", "sell-off", "hack",
    "exploit", "breach", "lawsuit", "sec", "investigation", "fraud",
    "scam", "outage", "halt", "liquidation", "ban", "warning", "risk",
    "concern", "fear", "slump", "wind down", "crumbles",
]


def analyze_headline_sentiment(headlines: list[str]) -> dict[str, float]:
    """Quick keyword-based sentiment from headlines. Returns aggregate scores."""
    if not headlines:
        return {"sentiment": 0.0, "bullish_ratio": 0.0, "headline_count": 0.0}

    bull_count = 0
    bear_count = 0
    for h in headlines:
        t = h.lower()
        if any(kw in t for kw in BULLISH_KW):
            bull_count += 1
        if any(kw in t for kw in BEARISH_KW):
            bear_count += 1

    total = max(1, bull_count + bear_count)
    sentiment = (bull_count - bear_count) / total

    return {
        "sentiment": round(sentiment, 3),
        "bullish_ratio": round(bull_count / max(1, len(headlines)), 3),
        "bearish_ratio": round(bear_count / max(1, len(headlines)), 3),
        "headline_count": float(len(headlines)),
        "fetched_at_ms": int(time.time() * 1000),
    }


def fetch_sentiment() -> dict[str, float]:
    """Fetch CoinTelegraph RSS and compute sentiment."""
    try:
        items = fetch_cointelegraph_rss(15)
        headlines = [item["title"] for item in items if item["title"]]
        return analyze_headline_sentiment(headlines)
    except Exception:
        return {"sentiment": 0.0, "bullish_ratio": 0.0, "headline_count": 0.0}


__all__ = [
    "analyze_headline_sentiment",
    "fetch_cointelegraph_rss",
    "fetch_sentiment",
]
