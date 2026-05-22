"""Deepseek LLM adapter — AI-powered news sentiment analysis.

Uses Deepseek API to analyze crypto/financial news headlines and produce
structured sentiment scores. Reads DEEPSEEK_API_KEY from environment.

Produces dict with: sentiment (-1 to 1), confidence (0-1),
impact_score (0-1), category, summary
"""

from __future__ import annotations

import json
import os
from typing import Any
from urllib.request import Request, urlopen

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEFAULT_MODEL = "deepseek-chat"

SYSTEM_PROMPT = """You are a crypto financial news analyzer. For each headline, output JSON:
{
  "sentiment": <float -1 to 1, bearish to bullish>,
  "confidence": <float 0 to 1>,
  "impact_score": <float 0 to 1, market impact>,
  "category": "<crypto_positive|crypto_negative|macro_hawkish|macro_dovish|geopolitical_risk|safe_haven|commodity_inflation|liquidity_positive|neutral>",
  "summary": "<one-line analysis in English>"
}
Rules:
- ETF approval, institutional adoption, regulatory clarity → crypto_positive, sentiment > 0
- SEC lawsuit, hack, exchange collapse → crypto_negative, sentiment < 0
- Fed rate hike, high CPI, strong jobs → macro_hawkish, sentiment negative for crypto
- Rate cut, low CPI, liquidity injection → macro_dovish, sentiment positive
- War, sanctions, military conflict → geopolitical_risk, sentiment negative
- Gold rally, safe haven flows → safe_haven, sentiment negative for crypto
- Oil/food price shock → commodity_inflation, sentiment slightly negative
- Dollar weakness, bond yield drop → liquidity_positive, sentiment positive
- Be concise. Output ONLY the JSON array, no markdown, no explanation."""


def analyze_headlines(headlines: list[str]) -> list[dict[str, Any]]:
    """Analyze multiple headlines with Deepseek LLM. Returns list of sentiment dicts."""
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY not set")

    if not headlines:
        return []

    headlines_text = "\n".join(f"{i+1}. {h}" for i, h in enumerate(headlines))
    user_prompt = f"Analyze these crypto/financial headlines:\n\n{headlines_text}"

    body = json.dumps({
        "model": DEFAULT_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 500,
        "response_format": {"type": "json_object"},
    }).encode()

    req = Request(
        DEEPSEEK_API_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    with urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())

    content = data["choices"][0]["message"]["content"]
    try:
        result = json.loads(content)
        if isinstance(result, list):
            return result
        if isinstance(result, dict):
            values = list(result.values())
            if values and isinstance(values[0], list):
                return values[0]
            return [result]
    except json.JSONDecodeError:
        pass

    return [{"sentiment": 0, "confidence": 0, "impact_score": 0,
             "category": "neutral", "summary": "parse error"}]


def compute_aggregate_sentiment(analyses: list[dict[str, Any]]) -> dict[str, float]:
    """Compute aggregate sentiment metrics from analyzed headlines."""
    if not analyses:
        return {
            "avg_sentiment": 0.0,
            "avg_confidence": 0.0,
            "avg_impact": 0.0,
            "risk_score": 0.3,
            "headline_count": 0.0,
        }

    sentiments = [a.get("sentiment", 0) for a in analyses]
    confidences = [a.get("confidence", 0) for a in analyses]
    impacts = [a.get("impact_score", 0) for a in analyses]

    avg_sentiment = sum(sentiments) / len(sentiments)
    avg_confidence = sum(confidences) / len(confidences)
    avg_impact = sum(impacts) / len(impacts)

    categories = [a.get("category", "neutral") for a in analyses]
    risk_cats = sum(1 for c in categories
                    if c in ("crypto_negative", "macro_hawkish", "geopolitical_risk", "safe_haven"))
    positive_cats = sum(1 for c in categories
                        if c in ("crypto_positive", "macro_dovish", "liquidity_positive"))

    risk_score = risk_cats / len(categories) if categories else 0.3
    risk_score = max(0.1, min(0.9, risk_score + (0.2 if avg_sentiment < -0.2 else 0)))

    return {
        "avg_sentiment": round(avg_sentiment, 3),
        "avg_confidence": round(avg_confidence, 3),
        "avg_impact": round(avg_impact, 3),
        "risk_score": round(risk_score, 3),
        "headline_count": float(len(analyses)),
    }


__all__ = [
    "analyze_headlines",
    "compute_aggregate_sentiment",
]
