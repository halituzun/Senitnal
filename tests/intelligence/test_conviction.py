"""V11 — Live conviction tests."""

from __future__ import annotations

import pytest
from sentinel.intelligence.conviction import (
    ActionabilityBand,
    LiveConvictionInput,
    LiveConvictionResult,
    evaluate_live_conviction,
)
from sentinel.intelligence.fusion import SignalFusionInput, compute_signal_fusion
from sentinel.intelligence.net_edge import compute_net_edge
from sentinel.intelligence.schemas import (
    MacroEventKind,
    MacroEventSnapshot,
    MarketMicrostructureSnapshot,
    NewsEventSnapshot,
    NewsFamily,
    TechnicalIndicatorSnapshot,
)

_NOW = 1_700_000_001_000


def _fusion(*, agreement: int = 4):
    ti = TechnicalIndicatorSnapshot(
        snapshot_id="t",
        symbol_hash="sha:btc",
        timeframe="1h",
        indicators={"rsi": 60.0},
        trend_score=0.7,
        momentum_score=0.6,
        volatility_score=0.4,
        reversal_score=0.2,
        confidence=0.8,
        observed_at_ms=_NOW,
        provenance_hash="sha:p",
    )
    ms = MarketMicrostructureSnapshot(
        snapshot_id="m",
        symbol_hash="sha:btc",
        venue_hash="sha:venue",
        orderbook_age_ms=20,
        trade_tape_age_ms=10,
        bid_ask_spread_pct=0.0005,
        bid_depth_score=0.7,
        ask_depth_score=0.7,
        imbalance_score=0.1,
        ofi_score=0.0,
        vpin_score=0.2,
        hawkes_toxicity_score=0.1,
        liquidity_score=0.75,
        latency_ms=20,
        confidence=0.8,
        observed_at_ms=_NOW,
        provenance_hash="sha:p",
    )
    macro = MacroEventSnapshot(
        event_id="m1",
        event_type=MacroEventKind.CPI,
        country_or_region="US",
        observed_at_ms=_NOW,
        severity_score=0.5,
        surprise_score=0.4,
        risk_off_score=0.4,
        confidence=0.7,
        provenance_hash="sha:p",
    )
    news = NewsEventSnapshot(
        event_id="n1",
        news_family=NewsFamily.ETF,
        severity_score=0.5,
        novelty_score=0.5,
        contradiction_score=0.1,
        source_reliability_score=0.8,
        confidence=0.7,
        observed_at_ms=_NOW,
        provenance_hash="sha:p",
    )
    inp = SignalFusionInput(
        fusion_id="f",
        now_ms=_NOW,
        technical_indicator_snapshots=(ti,) if agreement >= 1 else (),
        microstructure_snapshots=(ms,) if agreement >= 2 else (),
        macro_snapshots=(macro,) if agreement >= 3 else (),
        news_snapshots=(news,) if agreement >= 4 else (),
    )
    return compute_signal_fusion(inp)


def _good_input(**over: object) -> LiveConvictionInput:
    base: dict[str, object] = {
        "conviction_id": "c1",
        "fusion_result": _fusion(agreement=4),
        "net_edge": compute_net_edge(breakdown_id="b", gross_edge_pct=0.01, fee_pct=0.001),
        "execution_quality": 0.8,
        "active_policy_ok": True,
        "governance_ok": True,
        "market_fresh": True,
        "balance_available": True,
        "exchange_health": 0.9,
    }
    base.update(over)
    return LiveConvictionInput(**base)  # type: ignore[arg-type]


class TestConvictionGates:
    def test_negative_net_edge_blocks(self) -> None:
        inp = _good_input(
            net_edge=compute_net_edge(breakdown_id="b", gross_edge_pct=0.001, fee_pct=0.01),
        )
        r = evaluate_live_conviction(inp)
        assert r.actionability_band is ActionabilityBand.BLOCKED
        assert "net_edge_not_positive" in r.block_reasons

    def test_stale_market_blocks(self) -> None:
        r = evaluate_live_conviction(_good_input(market_fresh=False))
        assert r.actionability_band is ActionabilityBand.BLOCKED

    def test_policy_off_blocks(self) -> None:
        r = evaluate_live_conviction(_good_input(active_policy_ok=False))
        assert r.actionability_band is ActionabilityBand.BLOCKED

    def test_governance_off_blocks(self) -> None:
        r = evaluate_live_conviction(_good_input(governance_ok=False))
        assert r.actionability_band is ActionabilityBand.BLOCKED

    def test_exchange_unhealthy_blocks(self) -> None:
        r = evaluate_live_conviction(_good_input(exchange_health=0.1))
        assert r.actionability_band is ActionabilityBand.BLOCKED

    def test_no_balance_blocks(self) -> None:
        r = evaluate_live_conviction(_good_input(balance_available=False))
        assert r.actionability_band is ActionabilityBand.BLOCKED


class TestConvictionPositive:
    def test_full_agreement_live_candidate_or_candidate(self) -> None:
        r = evaluate_live_conviction(_good_input())
        assert r.actionability_band in (
            ActionabilityBand.LIVE_CANDIDATE,
            ActionabilityBand.CANDIDATE,
        )

    def test_single_family_not_live_candidate(self) -> None:
        inp = _good_input(fusion_result=_fusion(agreement=1))
        r = evaluate_live_conviction(inp)
        assert r.actionability_band is not ActionabilityBand.LIVE_CANDIDATE


class TestConvictionSafetyFlags:
    def test_safety_flags_pinned(self) -> None:
        r = evaluate_live_conviction(_good_input())
        assert r.creates_action is False
        assert r.approves_trade is False

    def test_invalid_safety_flag_rejected(self) -> None:
        from pydantic import ValidationError as PVE

        with pytest.raises(PVE):
            LiveConvictionResult(
                conviction_id="x",
                conviction_score=0.5,
                actionability_band=ActionabilityBand.WATCH,
                confidence=0.5,
                creates_action=True,  # type: ignore[arg-type]
            )
