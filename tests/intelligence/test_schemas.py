"""V11 — Multi-source schema invariants."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sentinel.intelligence.schemas import (
    CommodityMacroSnapshot,
    GelAlMetricsObservation,
    MacroEventKind,
    MacroEventSnapshot,
    MarketMicrostructureSnapshot,
    MultiSourceObservation,
    NewsEventSnapshot,
    NewsFamily,
    SocialPlatform,
    SocialSignalSnapshot,
    SourceFamily,
    TechnicalIndicatorSnapshot,
)


class TestMultiSourceObservation:
    def _kwargs(self, **over: object) -> dict[str, object]:
        base: dict[str, object] = {
            "observation_id": "o1",
            "source_family": SourceFamily.TECHNICAL_INDICATOR,
            "source_id": "ti-1",
            "observed_at_ms": 1_000,
            "exported_at_ms": 1_001,
            "confidence": 0.7,
            "freshness_ms": 100,
            "provenance_hash": "sha:1",
            "source_event_refs": ("ev-1",),
        }
        base.update(over)
        return base

    def test_minimum_valid(self) -> None:
        obs = MultiSourceObservation(**self._kwargs())  # type: ignore[arg-type]
        assert obs.source_family is SourceFamily.TECHNICAL_INDICATOR

    def test_forbidden_field_in_features(self) -> None:
        with pytest.raises(ValidationError):
            MultiSourceObservation(**self._kwargs(normalized_features={"order_side": "x"}))  # type: ignore[arg-type]

    def test_api_secret_field_rejected(self) -> None:
        with pytest.raises(ValidationError):
            MultiSourceObservation(**self._kwargs(normalized_features={"api_secret": "x"}))  # type: ignore[arg-type]

    def test_empty_source_event_refs_rejected(self) -> None:
        with pytest.raises(ValidationError):
            MultiSourceObservation(**self._kwargs(source_event_refs=()))  # type: ignore[arg-type]

    def test_confidence_bounded(self) -> None:
        with pytest.raises(ValidationError):
            MultiSourceObservation(**self._kwargs(confidence=1.5))  # type: ignore[arg-type]


class TestTechnicalIndicatorSnapshot:
    def test_minimum_valid(self) -> None:
        snap = TechnicalIndicatorSnapshot(
            snapshot_id="t1",
            symbol_hash="sha:btc",
            timeframe="1h",
            indicators={"rsi": 55.0, "macd": 0.5},
            confidence=0.6,
            observed_at_ms=1_000,
            provenance_hash="sha:p",
        )
        assert snap.indicators["rsi"] == 55.0

    def test_forbidden_indicator_name(self) -> None:
        with pytest.raises(ValidationError):
            TechnicalIndicatorSnapshot(
                snapshot_id="t2",
                symbol_hash="sha:btc",
                timeframe="1h",
                indicators={"order_side": 1.0},
                confidence=0.6,
                observed_at_ms=1_000,
                provenance_hash="sha:p",
            )

    def test_scores_bounded(self) -> None:
        with pytest.raises(ValidationError):
            TechnicalIndicatorSnapshot(
                snapshot_id="t3",
                symbol_hash="sha:btc",
                timeframe="1h",
                indicators={},
                trend_score=1.5,
                confidence=0.6,
                observed_at_ms=1_000,
                provenance_hash="sha:p",
            )


class TestMicrostructure:
    def test_minimum_valid(self) -> None:
        ms = MarketMicrostructureSnapshot(
            snapshot_id="m1",
            symbol_hash="sha:btc",
            venue_hash="sha:venue",
            orderbook_age_ms=20,
            trade_tape_age_ms=10,
            bid_ask_spread_pct=0.0005,
            bid_depth_score=0.7,
            ask_depth_score=0.6,
            imbalance_score=0.1,
            ofi_score=0.0,
            vpin_score=0.3,
            hawkes_toxicity_score=0.2,
            liquidity_score=0.7,
            latency_ms=20,
            confidence=0.8,
            observed_at_ms=1_000,
            provenance_hash="sha:p",
        )
        assert ms.liquidity_score == 0.7

    def test_imbalance_bounded_negative(self) -> None:
        with pytest.raises(ValidationError):
            MarketMicrostructureSnapshot(
                snapshot_id="m2",
                symbol_hash="sha:btc",
                venue_hash="sha:venue",
                orderbook_age_ms=20,
                trade_tape_age_ms=10,
                bid_ask_spread_pct=0.0005,
                bid_depth_score=0.7,
                ask_depth_score=0.6,
                imbalance_score=-2.0,
                ofi_score=0.0,
                vpin_score=0.3,
                hawkes_toxicity_score=0.2,
                liquidity_score=0.7,
                latency_ms=20,
                confidence=0.8,
                observed_at_ms=1_000,
                provenance_hash="sha:p",
            )


class TestMacroNewsSocialCommodity:
    def test_macro_snapshot(self) -> None:
        s = MacroEventSnapshot(
            event_id="cpi-1",
            event_type=MacroEventKind.CPI,
            country_or_region="US",
            observed_at_ms=1_000,
            severity_score=0.6,
            surprise_score=0.4,
            risk_off_score=0.5,
            confidence=0.8,
            provenance_hash="sha:p",
        )
        assert s.event_type is MacroEventKind.CPI

    def test_news_snapshot(self) -> None:
        s = NewsEventSnapshot(
            event_id="war-1",
            news_family=NewsFamily.WAR,
            severity_score=0.9,
            novelty_score=0.7,
            contradiction_score=0.1,
            source_reliability_score=0.8,
            confidence=0.7,
            observed_at_ms=1_000,
            provenance_hash="sha:p",
        )
        assert s.news_family is NewsFamily.WAR

    def test_social_snapshot(self) -> None:
        s = SocialSignalSnapshot(
            signal_id="x-1",
            platform=SocialPlatform.X_TWITTER,
            crowd_panic_score=0.6,
            crowd_euphoria_score=0.1,
            bot_noise_score=0.2,
            influencer_concentration_score=0.3,
            contradiction_score=0.2,
            confidence=0.5,
            observed_at_ms=1_000,
            provenance_hash="sha:p",
        )
        assert s.platform is SocialPlatform.X_TWITTER

    def test_commodity_snapshot(self) -> None:
        s = CommodityMacroSnapshot(
            snapshot_id="cm-1",
            dxy_score=0.5,
            oil_score=0.4,
            gold_score=0.6,
            rates_score=0.5,
            nasdaq_risk_score=0.6,
            vix_score=0.5,
            global_risk_off_score=0.55,
            confidence=0.7,
            observed_at_ms=1_000,
            provenance_hash="sha:p",
        )
        assert s.global_risk_off_score == 0.55


class TestGelAlMetricsObservation:
    def test_minimum_valid(self) -> None:
        m = GelAlMetricsObservation(
            observation_id="g1",
            metric_family="depth_snapshots",
            symbol_hash="sha:btc",
            venue_hash="sha:venue",
            sample_count=100,
            mean_value=1.5,
            p50_value=1.4,
            p95_value=2.0,
            confidence=0.8,
            observed_at_ms=1_000,
            provenance_hash="sha:p",
        )
        assert m.sample_count == 100
