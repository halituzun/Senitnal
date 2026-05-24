"""Smart strategy engine — uses ALL TAAPI indicators for real decisions.

Analyzes market conditions and adapts strategy in real-time:
- Trending up: momentum strategies
- Trending down: mean reversion or short
- Ranging: scalp small moves
- High volatility: reduce position size
- Low volatility: increase position size
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MarketRegime:
    """Market condition detected from indicators."""
    trend: str = "neutral"  # bull, bear, neutral
    momentum: str = "neutral"  # strong, weak, neutral
    volatility: str = "normal"  # high, normal, low
    volume_signal: str = "normal"  # high, normal, low
    rsi_zone: str = "neutral"  # oversold, overbought, neutral
    action: str = "hold"  # buy, sell, hold
    confidence: float = 0.0


def analyze_market(indicators: dict[str, float]) -> MarketRegime:
    """Analyze ALL indicators and determine market regime."""
    regime = MarketRegime()

    # RSI analysis
    rsi = indicators.get("rsi", 50)
    if rsi < 30:
        regime.rsi_zone = "oversold"
    elif rsi > 70:
        regime.rsi_zone = "overbought"

    # MACD analysis
    macd = indicators.get("macd", 0)
    macd_signal = indicators.get("macd_signal", 0)
    if macd > macd_signal and macd > 0:
        regime.trend = "bull"
        regime.momentum = "strong" if macd > 2 else "weak"
    elif macd < macd_signal and macd < 0:
        regime.trend = "bear"
        regime.momentum = "strong" if macd < -2 else "weak"

    # ADX — trend strength
    adx = indicators.get("adx", 20)
    if adx > 25:
        regime.momentum = "strong"
    elif adx < 20:
        regime.momentum = "weak"

    # Bollinger Bands — volatility
    bb_width = indicators.get("bb_width", 5)
    if bb_width > 10:
        regime.volatility = "high"
    elif bb_width < 3:
        regime.volatility = "low"

    # ATR — volatility confirmation
    atr_pct = indicators.get("atr_pct", 2)
    if atr_pct > 5:
        regime.volatility = "high"

    # Volume analysis
    obv_trend = indicators.get("obv_trend", 0)
    volume_ratio = indicators.get("volume_ratio", 1)
    if volume_ratio > 1.5 and obv_trend > 0:
        regime.volume_signal = "high"
    elif volume_ratio < 0.5:
        regime.volume_signal = "low"

    # Stochastic RSI
    stoch_k = indicators.get("stoch_k", 50)
    stoch_d = indicators.get("stoch_d", 50)
    if stoch_k < 20 and stoch_d < 20:
        regime.rsi_zone = "oversold"
    elif stoch_k > 80 and stoch_d > 80:
        regime.rsi_zone = "overbought"

    # CCI
    cci = indicators.get("cci", 0)
    if cci > 100:
        regime.momentum = "strong"
        regime.trend = "bull" if regime.trend == "neutral" else regime.trend
    elif cci < -100:
        regime.momentum = "strong"
        regime.trend = "bear" if regime.trend == "neutral" else regime.trend

    # MFI — Money Flow Index
    mfi = indicators.get("mfi", 50)
    if mfi > 80:
        regime.rsi_zone = "overbought"
    elif mfi < 20:
        regime.rsi_zone = "oversold"

    # Determine action based on regime — MARKET ADAPTIVE
    action = "hold"
    confidence = 0.0
    
    # Scenario 1: OVERSOLD — buy the dip (mean reversion)
    if regime.rsi_zone == "oversold" and stoch_k < 30:
        if cci < -100 or stoch_k > stoch_d:  # Bullish divergence or stoch turn
            action = "buy"
            confidence = 0.7 + (0.3 if stoch_k > stoch_d else 0)
    # Scenario 2: OVERBOUGHT — take profit / sell
    elif regime.rsi_zone == "overbought" and stoch_k > 70:
        if cci > 100 or stoch_k < stoch_d:  # Bearish divergence
            action = "sell"
            confidence = 0.7
    # Scenario 3: STRONG TREND — follow it
    elif regime.momentum == "strong":
        if regime.trend == "bull" and adx > 25:
            action = "buy"
            confidence = 0.6
        elif regime.trend == "bear" and adx > 25:
            action = "sell"
            confidence = 0.6
    # Scenario 4: RANGING — scalp the edges
    elif regime.momentum == "weak" and regime.volatility == "normal":
        if rsi < 35 and stoch_k < 25:
            action = "buy"
            confidence = 0.5
        elif rsi > 65 and stoch_k > 75:
            action = "sell"
            confidence = 0.5
    # Scenario 5: HIGH VOLUME BREAKOUT
    elif regime.volume_signal == "high" and adx > 20:
        if regime.trend == "bull":
            action = "buy"
            confidence = 0.55
        elif regime.trend == "bear":
            action = "sell"
            confidence = 0.55

    regime.action = action
    regime.confidence = confidence
    return regime


def compute_indicator_score(indicators: dict[str, float]) -> dict[str, Any]:
    """Compute comprehensive indicator-based trading score."""
    regime = analyze_market(indicators)

    # Position size multiplier based on market conditions
    size_mult = 1.0
    if regime.volatility == "high":
        size_mult = 0.5  # Reduce position in high volatility
    elif regime.volatility == "low":
        size_mult = 1.5  # Increase in low volatility

    if regime.confidence < 0.5:
        size_mult *= 0.5  # Low confidence → smaller position

    # Edge score: combine multiple indicator signals
    rsi = indicators.get("rsi", 50)
    macd = indicators.get("macd", 0)
    stoch_k = indicators.get("stoch_k", 50)
    cci = indicators.get("cci", 0)
    mfi = indicators.get("mfi", 50)
    adx = indicators.get("adx", 20)

    # Composite edge: average of normalized indicator signals
    edge_signals = [
        (70 - rsi) / 40 if rsi > 50 else (rsi - 30) / 40,  # RSI: distance from extremes
        macd / 10,  # MACD normalized
        (stoch_k - 30) / 50 if stoch_k > 30 else (30 - stoch_k) / 30,  # Stoch
        cci / 200,  # CCI
        (50 - mfi) / 50 if mfi > 50 else (mfi - 50) / 50,  # MFI
        (adx - 20) / 30,  # ADX trend strength
    ]
    edge_score = sum(edge_signals) / len(edge_signals)
    edge_score = max(-1.0, min(1.0, edge_score))

    # Risk score: from volatility and uncertainty
    risk_score = (regime.volatility == "high") * 0.4 + (1 - regime.confidence) * 0.3

    return {
        "edge_score": round(edge_score, 3),
        "risk_score": round(min(0.9, max(0.1, risk_score)), 3),
        "confidence": round(regime.confidence, 3),
        "action": regime.action,
        "trend": regime.trend,
        "momentum": regime.momentum,
        "volatility": regime.volatility,
        "size_multiplier": round(size_mult, 2),
        "rsi": rsi,
        "macd": macd,
        "stoch_k": stoch_k,
        "cci": cci,
        "mfi": mfi,
        "adx": adx,
    }


__all__ = ["MarketRegime", "analyze_market", "compute_indicator_score"]
