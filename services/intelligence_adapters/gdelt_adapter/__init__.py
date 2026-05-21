"""GDELT global news adapter — multi-category news/sentiment.

Fetches from GDELT Project API (free, no auth) across multiple categories:
- crypto: Bitcoin, Ethereum, crypto regulation
- macro: Fed, interest rates, inflation, CPI
- geopolitical: war, sanctions, military conflict
- commodity: oil, gold, energy

Produces NewsEventSnapshot objects with keyword-based classification
and severity scoring for sentinel fusion engine.
"""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any
from urllib.parse import quote
from urllib.request import Request, urlopen

from sentinel.intelligence.schemas import NewsEventSnapshot, NewsFamily

BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

CATEGORY_QUERIES: dict[str, str] = {
    "crypto": "bitcoin OR ethereum OR crypto",
    "macro": "Federal Reserve OR interest rates OR inflation",
    "geopolitical": "war OR sanctions OR military conflict OR geopolitical",
    "commodity": "crude oil OR gold OR silver OR natural gas",
    "regulation": "SEC OR CFTC OR crypto regulation OR ETF bitcoin",
}

FAMILY_KEYWORDS: dict[str, NewsFamily] = {
    "hack": NewsFamily.HACK, "exploit": NewsFamily.HACK, "breach": NewsFamily.HACK,
    "sec": NewsFamily.REGULATION, "regulation": NewsFamily.REGULATION,
    "cftc": NewsFamily.REGULATION, "lawsuit": NewsFamily.REGULATION,
    "ban": NewsFamily.REGULATION, "etf": NewsFamily.ETF,
    "exchange": NewsFamily.EXCHANGE_OUTAGE, "outage": NewsFamily.EXCHANGE_OUTAGE,
    "halt": NewsFamily.EXCHANGE_OUTAGE, "suspended": NewsFamily.EXCHANGE_OUTAGE,
    "liquidation": NewsFamily.LIQUIDATION, "liquidated": NewsFamily.LIQUIDATION,
    "macro": NewsFamily.MACRO, "fed": NewsFamily.MACRO, "inflation": NewsFamily.MACRO,
    "interest rate": NewsFamily.MACRO, "recession": NewsFamily.MACRO,
    "company": NewsFamily.COMPANY, "partnership": NewsFamily.COMPANY,
    "war": NewsFamily.WAR, "sanctions": NewsFamily.WAR, "conflict": NewsFamily.WAR,
}

NEGATIVE_KW = [
    "hack", "exploit", "breach", "crash", "ban", "lawsuit", "investigation",
    "fraud", "scam", "outage", "halt", "decline", "drop", "plunge", "crash",
    "sell-off", "bearish", "warning", "risk", "concern", "fear", "sanctions",
    "war", "conflict", "recession", "inflation", "crisis", "default",
    "liquidation", "collapse", "downturn", "volatility",
]

POSITIVE_KW = [
    "etf", "approval", "adoption", "partnership", "launch", "breakthrough",
    "rally", "surge", "soar", "bullish", "record", "milestone", "upgrade",
    "institutional", "accumulation", "growth", "funding", "innovation",
    "adopt", "ceasefire", "peace", "recovery", "expansion",
]


def _hash(s: str) -> str:
    return "sha256:" + hashlib.sha256(s.encode()).hexdigest()[:16]


def _classify(title: str) -> NewsFamily:
    text = title.lower()
    for kw, family in FAMILY_KEYWORDS.items():
        if kw in text:
            return family
    return NewsFamily.UNKNOWN


def _score_severity(text: str) -> float:
    t = text.lower()
    neg = sum(1 for kw in NEGATIVE_KW if kw in t)
    pos = sum(1 for kw in POSITIVE_KW if kw in t)
    if neg == 0:
        return 0.2
    return min(1.0, max(0.3, neg / max(1, neg + pos) + neg * 0.05))


def _score_sentiment(text: str) -> float:
    t = text.lower()
    neg = sum(1 for kw in NEGATIVE_KW if kw in t)
    pos = sum(1 for kw in POSITIVE_KW if kw in t)
    total = neg + pos
    if total == 0:
        return 0.0
    return round((pos - neg) / total, 2)


def fetch_category(query: str, max_records: int = 20) -> list[dict[str, Any]]:
    """Fetch articles from GDELT for a query string."""
    q = quote(query, safe="")
    url = (
        f"{BASE_URL}?query={q}&mode=artlist&format=json"
        f"&timespan=24h&sort=datedesc&maxrecords={max_records}"
    )
    req = Request(url, headers={"Accept": "application/json"})
    with urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
    if isinstance(data, dict):
        return data.get("articles", [])
    return []


def normalize_article(article: dict[str, Any], category: str = "") -> NewsEventSnapshot | None:
    """Convert GDELT article to NewsEventSnapshot."""
    title = str(article.get("title", ""))
    if not title:
        return None

    now_ms = int(time.time() * 1000)
    family = _classify(title)
    severity = _score_severity(title)
    sentiment = _score_sentiment(title)

    return NewsEventSnapshot(
        event_id=f"gdelt-{_hash(title)}",
        news_family=family,
        severity_score=round(severity, 2),
        novelty_score=0.5,
        contradiction_score=round(abs(sentiment) * 0.7, 2),
        source_reliability_score=0.7,
        confidence=round(0.4 + abs(sentiment) * 0.3, 2),
        observed_at_ms=now_ms,
        provenance_hash=_hash(f"gdelt-{category}-{title[:40]}"),
    )


def fetch_all_news(
    categories: list[str] | None = None, max_per_category: int = 10,
) -> dict[str, list[NewsEventSnapshot]]:
    """Fetch news across categories. Returns {category: [snapshots]}."""
    if categories is None:
        categories = ["crypto", "macro", "geopolitical"]

    result: dict[str, list[NewsEventSnapshot]] = {}
    for cat in categories:
        query = CATEGORY_QUERIES.get(cat)
        if not query:
            continue
        try:
            articles = fetch_category(query, max_per_category)
        except Exception:
            continue

        snaps: list[NewsEventSnapshot] = []
        for article in articles:
            snap = normalize_article(article, cat)
            if snap:
                snaps.append(snap)

        if snaps:
            result[cat] = snaps

    return result


def compute_news_sentiment_summary(
    news: dict[str, list[NewsEventSnapshot]],
) -> dict[str, float]:
    """Compute aggregate sentiment scores per category.

    Returns dict like:
        {"crypto_sentiment": 0.23, "macro_risk": 0.45, "geopolitical_risk": 0.12}
    """
    summary: dict[str, float] = {}

    for cat, snaps in news.items():
        if not snaps:
            continue
        avg_severity = sum(s.severity_score for s in snaps) / len(snaps)
        summary[f"{cat}_avg_severity"] = round(avg_severity, 3)
        summary[f"{cat}_count"] = float(len(snaps))

    # Compute macro_risk from macro + geopolitical
    macro_sev = summary.get("macro_avg_severity", 0.3)
    geo_sev = summary.get("geopolitical_avg_severity", 0.3)
    summary["macro_risk_score"] = round(max(macro_sev, geo_sev) * 0.9, 3)

    return summary


__all__ = [
    "CATEGORY_QUERIES",
    "compute_news_sentiment_summary",
    "fetch_all_news",
    "fetch_category",
    "normalize_article",
]
