"""V3 — Financial memory payload schema tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sentinel.memory.financial import (
    ExecutionQualityObservationPayload,
    LatencyPatternPayload,
    LiquidityConditionPayload,
    MarketRegimeObservationPayload,
    SpreadWindowObservationPayload,
    financial_payload_subject_class,
)
from sentinel.types.memory import SubjectClass

# ---- MarketRegimeObservationPayload ----


def _valid_regime() -> dict[str, object]:
    return {
        "record_key": "regime-001",
        "symbol_hash": "sha256:sym",
        "venue_hash": "sha256:venue",
        "regime_label": "calm",
        "observed_window_ms": 60_000,
        "volatility_score": 0.2,
        "spread_score": 0.1,
        "liquidity_score": 0.8,
        "staleness_score": 0.1,
        "confidence": 0.8,
        "observation_count": 12,
        "source_event_ids": ("ev-1", "ev-2"),
    }


class TestMarketRegimeObservationPayload:
    def test_valid_accepted(self) -> None:
        MarketRegimeObservationPayload(**_valid_regime())  # type: ignore[arg-type]

    def test_negative_window_rejected(self) -> None:
        kw = _valid_regime()
        kw["observed_window_ms"] = 0
        with pytest.raises(ValidationError):
            MarketRegimeObservationPayload(**kw)  # type: ignore[arg-type]

    def test_confidence_out_of_range_rejected(self) -> None:
        kw = _valid_regime()
        kw["confidence"] = 1.5
        with pytest.raises(ValidationError):
            MarketRegimeObservationPayload(**kw)  # type: ignore[arg-type]

    def test_empty_source_event_ids_rejected(self) -> None:
        kw = _valid_regime()
        kw["source_event_ids"] = ()
        with pytest.raises(ValidationError):
            MarketRegimeObservationPayload(**kw)  # type: ignore[arg-type]

    def test_empty_source_event_id_string_rejected(self) -> None:
        kw = _valid_regime()
        kw["source_event_ids"] = ("ev-1", "")
        with pytest.raises(ValidationError):
            MarketRegimeObservationPayload(**kw)  # type: ignore[arg-type]

    @pytest.mark.parametrize("bad_field", ["symbol", "venue", "side", "api_key", "balance"])
    def test_forbidden_extra_field_rejected(self, bad_field: str) -> None:
        kw = _valid_regime()
        kw[bad_field] = "x"
        with pytest.raises(ValidationError):
            MarketRegimeObservationPayload(**kw)  # type: ignore[arg-type]


# ---- SpreadWindowObservationPayload ----


def _valid_spread() -> dict[str, object]:
    return {
        "record_key": "spread-001",
        "symbol_hash": "sha256:sym",
        "venue_hash": "sha256:venue",
        "window_start_ms": 1000,
        "window_end_ms": 5000,
        "min_spread_pct": 0.1,
        "max_spread_pct": 0.5,
        "avg_spread_pct": 0.3,
        "sample_count": 10,
        "confidence": 0.85,
        "source_event_ids": ("ev-1",),
    }


class TestSpreadWindowObservationPayload:
    def test_valid_accepted(self) -> None:
        SpreadWindowObservationPayload(**_valid_spread())  # type: ignore[arg-type]

    def test_inverted_window_rejected(self) -> None:
        kw = _valid_spread()
        kw["window_end_ms"] = 500
        with pytest.raises(ValidationError):
            SpreadWindowObservationPayload(**kw)  # type: ignore[arg-type]

    def test_max_below_min_rejected(self) -> None:
        kw = _valid_spread()
        kw["max_spread_pct"] = 0.05
        with pytest.raises(ValidationError):
            SpreadWindowObservationPayload(**kw)  # type: ignore[arg-type]

    def test_avg_out_of_range_rejected(self) -> None:
        kw = _valid_spread()
        kw["avg_spread_pct"] = 0.99
        with pytest.raises(ValidationError):
            SpreadWindowObservationPayload(**kw)  # type: ignore[arg-type]


# ---- LiquidityConditionPayload ----


def _valid_liquidity() -> dict[str, object]:
    return {
        "record_key": "liq-001",
        "symbol_hash": "sha256:sym",
        "venue_hash": "sha256:venue",
        "bid_depth_score": 0.6,
        "ask_depth_score": 0.6,
        "imbalance_score": 0.1,
        "liquidity_score": 0.7,
        "confidence": 0.8,
        "source_event_ids": ("ev-1",),
    }


class TestLiquidityConditionPayload:
    def test_valid_accepted(self) -> None:
        LiquidityConditionPayload(**_valid_liquidity())  # type: ignore[arg-type]

    def test_out_of_range_score_rejected(self) -> None:
        kw = _valid_liquidity()
        kw["bid_depth_score"] = 1.5
        with pytest.raises(ValidationError):
            LiquidityConditionPayload(**kw)  # type: ignore[arg-type]


# ---- LatencyPatternPayload ----


def _valid_latency() -> dict[str, object]:
    return {
        "record_key": "lat-001",
        "source_adapter_id": "synthetic-market-adapter",
        "venue_hash": "sha256:venue",
        "avg_latency_ms": 10.0,
        "p95_latency_ms": 50.0,
        "max_latency_ms": 200.0,
        "stale_ratio": 0.05,
        "sample_count": 100,
        "confidence": 0.9,
        "source_event_ids": ("ev-1",),
    }


class TestLatencyPatternPayload:
    def test_valid_accepted(self) -> None:
        LatencyPatternPayload(**_valid_latency())  # type: ignore[arg-type]

    def test_order_violation_rejected(self) -> None:
        kw = _valid_latency()
        kw["max_latency_ms"] = 1.0
        with pytest.raises(ValidationError):
            LatencyPatternPayload(**kw)  # type: ignore[arg-type]

    def test_stale_ratio_out_of_range_rejected(self) -> None:
        kw = _valid_latency()
        kw["stale_ratio"] = 1.5
        with pytest.raises(ValidationError):
            LatencyPatternPayload(**kw)  # type: ignore[arg-type]


# ---- ExecutionQualityObservationPayload ----


def _valid_exec_quality() -> dict[str, object]:
    return {
        "record_key": "exq-001",
        "simulation_id": "sim-001",
        "expected_fill_quality": 0.8,
        "estimated_slippage_pct": 0.05,
        "estimated_fee_pct": 0.02,
        "estimated_net_edge_pct": 0.1,
        "sample_count": 50,
        "confidence": 0.75,
        "source_event_ids": ("ev-1",),
    }


class TestExecutionQualityObservationPayload:
    def test_valid_accepted(self) -> None:
        ExecutionQualityObservationPayload(**_valid_exec_quality())  # type: ignore[arg-type]

    @pytest.mark.parametrize(
        "forbidden_field",
        ["order_id", "live_fill_id", "account_id", "order_side", "side", "symbol", "venue"],
    )
    def test_forbidden_execution_field_rejected(self, forbidden_field: str) -> None:
        kw = _valid_exec_quality()
        kw[forbidden_field] = "x"
        with pytest.raises(ValidationError):
            ExecutionQualityObservationPayload(**kw)  # type: ignore[arg-type]


# ---- Subject class mapping ----


class TestFinancialPayloadSubjectClass:
    def test_market_regime_maps_to_structured_fact(self) -> None:
        payload = MarketRegimeObservationPayload(**_valid_regime())  # type: ignore[arg-type]
        assert financial_payload_subject_class(payload) is SubjectClass.STRUCTURED_FACT

    def test_spread_maps_to_structured_fact(self) -> None:
        payload = SpreadWindowObservationPayload(**_valid_spread())  # type: ignore[arg-type]
        assert financial_payload_subject_class(payload) is SubjectClass.STRUCTURED_FACT

    def test_liquidity_maps_to_structured_fact(self) -> None:
        payload = LiquidityConditionPayload(**_valid_liquidity())  # type: ignore[arg-type]
        assert financial_payload_subject_class(payload) is SubjectClass.STRUCTURED_FACT

    def test_latency_maps_to_source_trust(self) -> None:
        payload = LatencyPatternPayload(**_valid_latency())  # type: ignore[arg-type]
        assert financial_payload_subject_class(payload) is SubjectClass.SOURCE_TRUST

    def test_exec_quality_maps_to_procedural(self) -> None:
        payload = ExecutionQualityObservationPayload(**_valid_exec_quality())  # type: ignore[arg-type]
        assert financial_payload_subject_class(payload) is SubjectClass.PROCEDURAL

    def test_all_mappings_use_existing_subject_class(self) -> None:
        # Constitutional: V3 must NOT introduce new SubjectClass values.
        # All mappings must land in the 16-member v0.1 enum.
        for payload_obj in [
            MarketRegimeObservationPayload(**_valid_regime()),  # type: ignore[arg-type]
            SpreadWindowObservationPayload(**_valid_spread()),  # type: ignore[arg-type]
            LiquidityConditionPayload(**_valid_liquidity()),  # type: ignore[arg-type]
            LatencyPatternPayload(**_valid_latency()),  # type: ignore[arg-type]
            ExecutionQualityObservationPayload(**_valid_exec_quality()),  # type: ignore[arg-type]
        ]:
            mapped = financial_payload_subject_class(payload_obj)
            assert mapped in SubjectClass
            # Defensive: must never be in the forbidden-for-financial set
            assert mapped not in {
                SubjectClass.NARRATIVE_CLAIM,
                SubjectClass.CAUSAL_EXPLANATION,
                SubjectClass.DECISION_RATIONALE,
            }
