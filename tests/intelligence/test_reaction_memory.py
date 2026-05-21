"""V12 — Reaction memory tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sentinel.intelligence.reaction_memory import (
    InMemoryReactionMemoryStore,
    ReactionMemoryRecord,
    is_record_usable_for_live,
)
from sentinel.intelligence.reaction_taxonomy import (
    HistoricalEventFamily,
    MarketReactionMeasurement,
    ReactionWindow,
)

_NOW = 1_700_000_000_000


def _measurement(**over: object) -> MarketReactionMeasurement:
    base: dict[str, object] = {
        "measurement_id": "m1",
        "event_family": HistoricalEventFamily.MACRO_CPI,
        "window": ReactionWindow.W_1H,
        "btc_return": 0.01,
        "eth_return": 0.012,
        "alt_index_return": 0.015,
        "volatility_jump": 0.05,
        "spread_change": 0.0,
        "orderbook_imbalance_change": 0.0,
        "liquidation_change": 0.0,
        "funding_change": 0.0,
        "dxy_change": 0.0,
        "gold_change": 0.0,
        "oil_change": 0.0,
        "nasdaq_change": 0.0,
        "confidence": 0.7,
        "observed_at_ms": _NOW,
        "provenance_hash": "sha:p",
    }
    base.update(over)
    return MarketReactionMeasurement(**base)  # type: ignore[arg-type]


def _record(**over: object) -> ReactionMemoryRecord:
    base: dict[str, object] = {
        "record_id": "r1",
        "event_family": HistoricalEventFamily.MACRO_CPI,
        "event_signature_hash": "sha:event",
        "regime_signature_hash": "sha:regime",
        "reaction_window": ReactionWindow.W_1H,
        "market_reaction": _measurement(),
        "source_refs": ("hist-1",),
        "sample_count": 10,
        "confidence": 0.7,
        "contradiction_count": 1,
        "last_seen_ms": _NOW,
        "provenance_hash": "sha:p",
        "usable_for_live": False,
    }
    base.update(over)
    return ReactionMemoryRecord(**base)  # type: ignore[arg-type]


class TestReactionMemoryRecord:
    def test_low_sample_count_cannot_be_usable_for_live(self) -> None:
        with pytest.raises(ValidationError):
            _record(sample_count=2, usable_for_live=True)

    def test_high_contradiction_cannot_be_usable_for_live(self) -> None:
        with pytest.raises(ValidationError):
            _record(sample_count=10, contradiction_count=6, usable_for_live=True)

    def test_valid_usable_record(self) -> None:
        r = _record(sample_count=20, contradiction_count=2, usable_for_live=True)
        assert r.usable_for_live is True

    def test_default_usable_for_live_false(self) -> None:
        assert _record().usable_for_live is False

    def test_empty_source_refs_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _record(source_refs=())


class TestStore:
    def test_by_family_filter(self) -> None:
        store = InMemoryReactionMemoryStore()
        store.insert(_record(record_id="r-cpi", event_family=HistoricalEventFamily.MACRO_CPI))
        store.insert(
            _record(
                record_id="r-war",
                event_family=HistoricalEventFamily.WAR_HEADLINE,
                market_reaction=_measurement(event_family=HistoricalEventFamily.WAR_HEADLINE),
            )
        )
        cpi = store.by_family(HistoricalEventFamily.MACRO_CPI)
        assert len(cpi) == 1

    def test_usable_records_filters_stale(self) -> None:
        store = InMemoryReactionMemoryStore()
        store.insert(
            _record(
                record_id="r-fresh",
                sample_count=20,
                contradiction_count=2,
                usable_for_live=True,
                last_seen_ms=_NOW,
            )
        )
        store.insert(
            _record(
                record_id="r-stale",
                sample_count=20,
                contradiction_count=2,
                usable_for_live=True,
                last_seen_ms=_NOW - 60 * 24 * 60 * 60 * 1000,
            )
        )
        usable = store.usable_records(now_ms=_NOW)
        ids = {r.record_id for r in usable}
        assert "r-fresh" in ids
        assert "r-stale" not in ids


class TestUsabilityGating:
    def test_helper_consistent_with_validator(self) -> None:
        rec = _record(sample_count=20, contradiction_count=2, usable_for_live=True)
        assert is_record_usable_for_live(rec, now_ms=_NOW) is True

    def test_helper_rejects_stale(self) -> None:
        rec = _record(
            sample_count=20,
            contradiction_count=2,
            usable_for_live=True,
            last_seen_ms=_NOW - 60 * 24 * 60 * 60 * 1000,
        )
        assert is_record_usable_for_live(rec, now_ms=_NOW) is False
