"""V11 — Signal fusion tests."""

from __future__ import annotations

from sentinel.intelligence.fusion import SignalFusionInput, compute_signal_fusion
from sentinel.intelligence.schemas import (
    MacroEventKind,
    MacroEventSnapshot,
    MarketMicrostructureSnapshot,
    NewsEventSnapshot,
    NewsFamily,
    SocialPlatform,
    SocialSignalSnapshot,
    TechnicalIndicatorSnapshot,
)

_NOW = 1_700_000_001_000


def _ti(**over: object) -> TechnicalIndicatorSnapshot:
    base: dict[str, object] = {
        "snapshot_id": "t1",
        "symbol_hash": "sha:btc",
        "timeframe": "1h",
        "indicators": {"rsi": 55.0},
        "trend_score": 0.6,
        "momentum_score": 0.5,
        "volatility_score": 0.4,
        "reversal_score": 0.2,
        "confidence": 0.8,
        "observed_at_ms": _NOW - 1_000,
        "provenance_hash": "sha:p",
    }
    base.update(over)
    return TechnicalIndicatorSnapshot(**base)  # type: ignore[arg-type]


def _ms(**over: object) -> MarketMicrostructureSnapshot:
    base: dict[str, object] = {
        "snapshot_id": "m1",
        "symbol_hash": "sha:btc",
        "venue_hash": "sha:venue",
        "orderbook_age_ms": 20,
        "trade_tape_age_ms": 10,
        "bid_ask_spread_pct": 0.0005,
        "bid_depth_score": 0.7,
        "ask_depth_score": 0.7,
        "imbalance_score": 0.1,
        "ofi_score": 0.0,
        "vpin_score": 0.3,
        "hawkes_toxicity_score": 0.2,
        "liquidity_score": 0.7,
        "latency_ms": 20,
        "confidence": 0.8,
        "observed_at_ms": _NOW - 1_000,
        "provenance_hash": "sha:p",
    }
    base.update(over)
    return MarketMicrostructureSnapshot(**base)  # type: ignore[arg-type]


class TestFusionBasics:
    def test_no_inputs_zero_confidence(self) -> None:
        r = compute_signal_fusion(SignalFusionInput(fusion_id="f1", now_ms=_NOW))
        assert r.confidence == 0.0
        assert "no source inputs" in " ".join(r.reasons)

    def test_deterministic(self) -> None:
        inp = SignalFusionInput(
            fusion_id="f2",
            now_ms=_NOW,
            technical_indicator_snapshots=(_ti(),),
            microstructure_snapshots=(_ms(),),
        )
        r1 = compute_signal_fusion(inp)
        r2 = compute_signal_fusion(inp)
        assert r1 == r2

    def test_scores_bounded(self) -> None:
        inp = SignalFusionInput(
            fusion_id="f3",
            now_ms=_NOW,
            technical_indicator_snapshots=(_ti(trend_score=1.0, momentum_score=1.0),),
            microstructure_snapshots=(_ms(liquidity_score=1.0),),
        )
        r = compute_signal_fusion(inp)
        for v in (
            r.trend_pressure,
            r.reversal_suspicion,
            r.volatility_pressure,
            r.liquidity_confidence,
            r.toxic_flow_suspicion,
            r.macro_shock_pressure,
            r.social_noise_pressure,
            r.contradiction_pressure,
            r.source_agreement_score,
            r.confidence,
        ):
            assert 0.0 <= v <= 1.0


class TestFusionStaleness:
    def test_stale_indicator_dampened(self) -> None:
        fresh = compute_signal_fusion(
            SignalFusionInput(
                fusion_id="fr",
                now_ms=_NOW,
                technical_indicator_snapshots=(_ti(),),
            )
        )
        stale = compute_signal_fusion(
            SignalFusionInput(
                fusion_id="fs",
                now_ms=_NOW,
                technical_indicator_snapshots=(_ti(observed_at_ms=_NOW - 600_000),),
            )
        )
        assert stale.trend_pressure < fresh.trend_pressure


class TestFusionSourceAgreement:
    def test_single_family_low_agreement(self) -> None:
        inp = SignalFusionInput(
            fusion_id="f-sa1",
            now_ms=_NOW,
            technical_indicator_snapshots=(_ti(),),
        )
        r = compute_signal_fusion(inp)
        # only one family populated -> agreement < 0.5
        assert r.source_agreement_score < 0.5

    def test_multiple_families_higher_agreement(self) -> None:
        macro = MacroEventSnapshot(
            event_id="cpi",
            event_type=MacroEventKind.CPI,
            country_or_region="US",
            observed_at_ms=_NOW,
            severity_score=0.6,
            surprise_score=0.5,
            risk_off_score=0.5,
            confidence=0.8,
            provenance_hash="sha:p",
        )
        news = NewsEventSnapshot(
            event_id="n",
            news_family=NewsFamily.ETF,
            severity_score=0.5,
            novelty_score=0.4,
            contradiction_score=0.1,
            source_reliability_score=0.8,
            confidence=0.7,
            observed_at_ms=_NOW,
            provenance_hash="sha:p",
        )
        inp = SignalFusionInput(
            fusion_id="f-sa2",
            now_ms=_NOW,
            technical_indicator_snapshots=(_ti(),),
            microstructure_snapshots=(_ms(),),
            macro_snapshots=(macro,),
            news_snapshots=(news,),
        )
        r = compute_signal_fusion(inp)
        assert r.source_agreement_score >= 0.6


class TestFusionContradiction:
    def test_social_panic_alone_does_not_dominate(self) -> None:
        social = SocialSignalSnapshot(
            signal_id="x1",
            platform=SocialPlatform.X_TWITTER,
            crowd_panic_score=0.9,
            crowd_euphoria_score=0.0,
            bot_noise_score=0.7,
            influencer_concentration_score=0.5,
            contradiction_score=0.7,
            confidence=0.6,
            observed_at_ms=_NOW,
            provenance_hash="sha:p",
        )
        inp = SignalFusionInput(
            fusion_id="f-sp",
            now_ms=_NOW,
            social_snapshots=(social,),
        )
        r = compute_signal_fusion(inp)
        # high contradiction + single family -> low overall confidence
        assert r.confidence < 0.3
        assert r.social_noise_pressure > 0.5
