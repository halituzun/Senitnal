"""Crypto news adapter — cryptocurrency.cv API.

Free, no API key required. Fetches recent crypto news and converts
to sentinel NewsEventSnapshot with severity/sentiment scoring.

Sources: 200+ crypto news outlets
"""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any
from urllib.request import Request, urlopen

from sentinel.intelligence.schemas import NewsEventSnapshot, NewsFamily

BASE_URL = "https://cryptocurrency.cv/api"

# Keyword → NewsFamily mapping for classification
FAMILY_KEYWORDS: dict[str, NewsFamily] = {
    "hack": NewsFamily.HACK,
    "exploit": NewsFamily.HACK,
    "breach": NewsFamily.HACK,
    "sec": NewsFamily.REGULATION,
    "regulation": NewsFamily.REGULATION,
    "lawsuit": NewsFamily.REGULATION,
    "ban": NewsFamily.REGULATION,
    "etf": NewsFamily.ETF,
    "exchange": NewsFamily.EXCHANGE_OUTAGE,
    "outage": NewsFamily.EXCHANGE_OUTAGE,
    "halt": NewsFamily.EXCHANGE_OUTAGE,
    "liquidation": NewsFamily.LIQUIDATION,
    "liquidated": NewsFamily.LIQUIDATION,
    "macro": NewsFamily.MACRO,
    "fed": NewsFamily.MACRO,
    "company": NewsFamily.COMPANY,
    "partnership": NewsFamily.COMPANY,
    "acquisition": NewsFamily.COMPANY,
}

# Negative-sentiment keywords (higher severity)
NEGATIVE_KEYWORDS = [
    "hack", "exploit", "breach", "crash", "ban", "lawsuit", "sec",
    "liquidation", "investigation", "fraud", "scam", "outage", "halt",
    "decline", "drop", "plunge", "crash", "crumbles", "sell-off",
    "bearish", "warning", "risk", "concern", "fear",
]

# Positive-sentiment keywords
POSITIVE_KEYWORDS = [
    "etf", "approval", "adoption", "partnership", "launch", "breakthrough",
    "rally", "surge", "soar", "bullish", "record", "milestone", "upgrade",
    "institutional", "accumulation", "growth", "raise", "funding",
]


def _hash(s: str) -> str:
    return "sha256:" + hashlib.sha256(s.encode()).hexdigest()[:16]


def _classify_family(title: str, content: str = "") -> NewsFamily:
    """Classify news into a NewsFamily based on keywords."""
    text = (title + " " + content).lower()
    for keyword, family in FAMILY_KEYWORDS.items():
        if keyword in text:
            return family
    return NewsFamily.UNKNOWN


def _score_severity(title: str, content: str = "") -> float:
    """Score severity 0-1 based on negative keyword density."""
    text = (title + " " + content).lower()
    neg_count = sum(1 for kw in NEGATIVE_KEYWORDS if kw in text)
    pos_count = sum(1 for kw in POSITIVE_KEYWORDS if kw in text)
    if neg_count == 0 and pos_count == 0:
        return 0.3  # neutral
    total = neg_count + pos_count
    return min(1.0, max(0.1, neg_count / total + 0.1 * neg_count))


def _score_sentiment(title: str, content: str = "") -> float:
    """Score sentiment -1 (bearish) to +1 (bullish)."""
    text = (title + " " + content).lower()
    neg = sum(1 for kw in NEGATIVE_KEYWORDS if kw in text)
    pos = sum(1 for kw in POSITIVE_KEYWORDS if kw in text)
    if neg == 0 and pos == 0:
        return 0.0
    return (pos - neg) / (pos + neg)


def fetch_crypto_news(limit: int = 20) -> list[dict[str, Any]]:
    """Fetch recent crypto news from cryptocurrency.cv."""
    url = f"{BASE_URL}/news?limit={limit}"
    req = Request(url, headers={"Accept": "application/json"})
    with urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("data", data.get("news", data.get("results", [])))
    return []


def fetch_crypto_search(query: str, limit: int = 20) -> list[dict[str, Any]]:
    """Search crypto news by keyword."""
    from urllib.parse import quote

    url = f"{BASE_URL}/search?q={quote(query)}&limit={limit}"
    req = Request(url, headers={"Accept": "application/json"})
    with urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("data", data.get("news", data.get("results", [])))
    return []


def normalize_news_item(item: dict[str, Any]) -> NewsEventSnapshot | None:
    """Convert a crypto news item to a sentinel NewsEventSnapshot."""
    title = str(item.get("title", item.get("headline", "")))
    if not title:
        return None

    content = str(item.get("content", item.get("description", item.get("summary", ""))))
    now_ms = int(time.time() * 1000)

    family = _classify_family(title, content)
    severity = _score_severity(title, content)
    sentiment = _score_sentiment(title, content)

    # Convert sentiment (-1..+1) to contradiction and reliability
    contradiction = abs(sentiment) * 0.5
    source_reliability = 0.6
    novelty = 0.5 + abs(sentiment) * 0.3
    confidence = 0.5 + abs(sentiment) * 0.2

    return NewsEventSnapshot(
        event_id=f"crypto-news-{_hash(title)}",
        news_family=family,
        severity_score=round(severity, 2),
        novelty_score=round(min(1.0, novelty), 2),
        contradiction_score=round(min(1.0, contradiction), 2),
        source_reliability_score=round(source_reliability, 2),
        confidence=round(min(1.0, confidence), 2),
        observed_at_ms=now_ms,
        provenance_hash=_hash(f"cryptocurrency.cv-{title}"),
    )


def fetch_and_normalize_news(limit: int = 20) -> list[NewsEventSnapshot]:
    """Fetch crypto news and return normalized snapshots."""
    try:
        items = fetch_crypto_news(limit)
    except Exception:
        return []

    snapshots: list[NewsEventSnapshot] = []
    for item in items:
        snap = normalize_news_item(item)
        if snap:
            snapshots.append(snap)

    return snapshots


__all__ = [
    "fetch_and_normalize_news",
    "fetch_crypto_news",
    "fetch_crypto_search",
    "normalize_news_item",
]
