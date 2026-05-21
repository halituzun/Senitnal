"""V12 — Historical similarity tests."""

from __future__ import annotations

from sentinel.intelligence.historical_similarity import (
    HistoricalSimilarityInput,
    evaluate_historical_similarity,
)
from sentinel.intelligence.reaction_memory import (
    InMemoryReactionMemoryStore,
    ReactionMemoryRecord,
)
from sentinel.intelligence.reaction_taxonomy import (
    HistoricalEventFamily,
    MarketReactionMeasurement,
    ReactionWindow,
)

_NOW = 1_700_000_000_000


def _measurement(btc_return: float = 0.01) -> MarketReactionMeasurement:
    return MarketReactionMeasurement(
        measurement_id="m",
        event_family=HistoricalEventFamily.MACRO_CPI,
        window=ReactionWindow.W_1H,
        btc_return=btc_return,
        eth_return=btc_return,
        alt_index_return=btc_return,
        volatility_jump=0.05,
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
    event_sig: str,
    regime_sig: str,
    btc_return: float = 0.01,
    sample_count: int = 20,
    usable: bool = True,
) -> ReactionMemoryRecord:
    return ReactionMemoryRecord(
        record_id=record_id,
        event_family=HistoricalEventFamily.MACRO_CPI,
        event_signature_hash=event_sig,
        regime_signature_hash=regime_sig,
        reaction_window=ReactionWindow.W_1H,
        market_reaction=_measurement(btc_return=btc_return),
        source_refs=("hist",),
        sample_count=sample_count,
        confidence=0.8,
        contradiction_count=1,
        last_seen_ms=_NOW,
        provenance_hash="sha:p",
        usable_for_live=usable,
    )


def _store(records: list[ReactionMemoryRecord]) -> InMemoryReactionMemoryStore:
    s = InMemoryReactionMemoryStore()
    for r in records:
        s.insert(r)
    return s


class TestSimilarity:
    def test_no_matching_pattern(self) -> None:
        r = evaluate_historical_similarity(
            HistoricalSimilarityInput(
                query_id="q",
                now_ms=_NOW,
                event_family=HistoricalEventFamily.MACRO_CPI,
                reaction_window=ReactionWindow.W_1H,
                event_signature_hash="sha:e",
                regime_signature_hash="sha:r",
                memory_store=InMemoryReactionMemoryStore(),
            )
        )
        assert r.historical_similarity_score == 0.0
        assert "no_matching_pattern_for_event_family_and_window" in r.risk_warnings

    def test_exact_match_high_similarity(self) -> None:
        store = _store([_record(record_id="r1", event_sig="sha:e", regime_sig="sha:r")])
        r = evaluate_historical_similarity(
            HistoricalSimilarityInput(
                query_id="q",
                now_ms=_NOW,
                event_family=HistoricalEventFamily.MACRO_CPI,
                reaction_window=ReactionWindow.W_1H,
                event_signature_hash="sha:e",
                regime_signature_hash="sha:r",
                memory_store=store,
            )
        )
        assert r.historical_similarity_score > 0.5
        assert "r1" in r.matching_pattern_refs

    def test_low_sample_count_clamped(self) -> None:
        store = _store(
            [_record(record_id="r-low", event_sig="sha:e", regime_sig="sha:r", sample_count=5)]
        )
        r = evaluate_historical_similarity(
            HistoricalSimilarityInput(
                query_id="q",
                now_ms=_NOW,
                event_family=HistoricalEventFamily.MACRO_CPI,
                reaction_window=ReactionWindow.W_1H,
                event_signature_hash="sha:e",
                regime_signature_hash="sha:r",
                memory_store=store,
            )
        )
        assert "low_sample_count_clamp" in r.risk_warnings

    def test_expected_band_within_bounds(self) -> None:
        store = _store(
            [_record(record_id="r1", event_sig="sha:e", regime_sig="sha:r", btc_return=0.02)]
        )
        r = evaluate_historical_similarity(
            HistoricalSimilarityInput(
                query_id="q",
                now_ms=_NOW,
                event_family=HistoricalEventFamily.MACRO_CPI,
                reaction_window=ReactionWindow.W_1H,
                event_signature_hash="sha:e",
                regime_signature_hash="sha:r",
                memory_store=store,
            )
        )
        assert -1.0 <= r.expected_reaction_band <= 1.0

    def test_unusable_records_filtered_when_required(self) -> None:
        store = _store(
            [_record(record_id="r1", event_sig="sha:e", regime_sig="sha:r", usable=False)]
        )
        r = evaluate_historical_similarity(
            HistoricalSimilarityInput(
                query_id="q",
                now_ms=_NOW,
                event_family=HistoricalEventFamily.MACRO_CPI,
                reaction_window=ReactionWindow.W_1H,
                event_signature_hash="sha:e",
                regime_signature_hash="sha:r",
                memory_store=store,
                require_usable_for_live=True,
            )
        )
        assert r.historical_similarity_score == 0.0
