"""V12 — Historical backtest aggregator tests."""

from __future__ import annotations

from sentinel.intelligence.historical_backtest import aggregate_records
from sentinel.intelligence.reaction_memory import ReactionMemoryRecord
from sentinel.intelligence.reaction_taxonomy import (
    HistoricalEventFamily,
    MarketReactionMeasurement,
    ReactionWindow,
)

_NOW = 1_700_000_000_000


def _measurement(btc_return: float, vol_jump: float = 0.05) -> MarketReactionMeasurement:
    return MarketReactionMeasurement(
        measurement_id="m",
        event_family=HistoricalEventFamily.MACRO_CPI,
        window=ReactionWindow.W_1H,
        btc_return=btc_return,
        eth_return=btc_return,
        alt_index_return=btc_return,
        volatility_jump=vol_jump,
        spread_change=0.0,
        orderbook_imbalance_change=0.0,
        liquidation_change=0.0,
        funding_change=0.0,
        dxy_change=0.0,
        gold_change=0.0,
        oil_change=0.0,
        nasdaq_change=0.0,
        confidence=0.8,
        observed_at_ms=_NOW,
        provenance_hash="sha:p",
    )


def _record(
    *,
    record_id: str,
    family: HistoricalEventFamily,
    btc_return: float,
    contradiction: int = 1,
    last_seen_ms: int = _NOW,
) -> ReactionMemoryRecord:
    return ReactionMemoryRecord(
        record_id=record_id,
        event_family=family,
        event_signature_hash="sha:e",
        regime_signature_hash="sha:r",
        reaction_window=ReactionWindow.W_1H,
        market_reaction=_measurement(btc_return).model_copy(update={"event_family": family}),
        source_refs=("hist",),
        sample_count=10,
        confidence=0.7,
        contradiction_count=contradiction,
        last_seen_ms=last_seen_ms,
        provenance_hash="sha:p",
    )


class TestAggregate:
    def test_empty_returns_zero(self) -> None:
        agg = aggregate_records(
            aggregate_id="a1",
            event_family=HistoricalEventFamily.MACRO_CPI,
            records=[],
            now_ms=_NOW,
        )
        assert agg.sample_count == 0

    def test_mean_btc_return(self) -> None:
        recs = [
            _record(record_id="r1", family=HistoricalEventFamily.MACRO_CPI, btc_return=0.01),
            _record(record_id="r2", family=HistoricalEventFamily.MACRO_CPI, btc_return=0.03),
        ]
        agg = aggregate_records(
            aggregate_id="a1",
            event_family=HistoricalEventFamily.MACRO_CPI,
            records=recs,
            now_ms=_NOW,
        )
        assert agg.sample_count == 2
        assert agg.mean_btc_return == 0.02

    def test_filter_by_family(self) -> None:
        recs = [
            _record(record_id="r1", family=HistoricalEventFamily.MACRO_CPI, btc_return=0.01),
            _record(record_id="r2", family=HistoricalEventFamily.WAR_HEADLINE, btc_return=-0.03),
        ]
        agg = aggregate_records(
            aggregate_id="a1",
            event_family=HistoricalEventFamily.MACRO_CPI,
            records=recs,
            now_ms=_NOW,
        )
        assert agg.sample_count == 1
        assert agg.mean_btc_return == 0.01

    def test_stale_rate(self) -> None:
        recs = [
            _record(record_id="r1", family=HistoricalEventFamily.MACRO_CPI, btc_return=0.01),
            _record(
                record_id="r2",
                family=HistoricalEventFamily.MACRO_CPI,
                btc_return=0.02,
                last_seen_ms=_NOW - 60 * 24 * 60 * 60 * 1000,
            ),
        ]
        agg = aggregate_records(
            aggregate_id="a1",
            event_family=HistoricalEventFamily.MACRO_CPI,
            records=recs,
            now_ms=_NOW,
        )
        assert agg.stale_rate == 0.5

    def test_failure_rate_bounded(self) -> None:
        recs = [
            _record(
                record_id="r1",
                family=HistoricalEventFamily.MACRO_CPI,
                btc_return=0.01,
                contradiction=20,
            ),
        ]
        agg = aggregate_records(
            aggregate_id="a1",
            event_family=HistoricalEventFamily.MACRO_CPI,
            records=recs,
            now_ms=_NOW,
        )
        assert 0.0 <= agg.failure_rate <= 1.0
