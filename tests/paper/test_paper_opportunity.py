"""V7 — Paper opportunity schema + conversion tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sentinel.adapters.market_observation import MarketObservationEnvelope
from sentinel.paper.opportunity import (
    PaperOpportunity,
    PaperOpportunityKind,
    PaperOpportunitySource,
    build_paper_opportunity_from_gelal_shadow,
    build_paper_opportunity_from_market_observation,
)

from tests.paper._fixtures import make_gelal_envelope, make_opportunity


class TestPaperOpportunitySchema:
    def test_valid_opportunity_accepted(self) -> None:
        o = make_opportunity()
        assert o.opportunity_id == "po-1"

    @pytest.mark.parametrize(
        "bad_field",
        ["symbol", "venue", "strategy_name", "order_side", "api_key", "set_kill_switch"],
    )
    def test_forbidden_field_rejected(self, bad_field: str) -> None:
        base: dict[str, object] = {
            "opportunity_id": "po-x",
            "source": PaperOpportunitySource.MANUAL_FIXTURE,
            "kind": PaperOpportunityKind.EDGE_CANDIDATE,
            "observed_at_ms": 0,
            "source_event_refs": ("ev-1",),
            "source_adapter_id": "manual",
            "provenance_hash": "sha256:x",
            "scope_hash": "sha256:scope",
            "confidence": 0.5,
            "magnitude_score": 0.3,
            "risk_score": 0.2,
            "staleness_ms": 0,
            "latency_ms": 0,
            "liquidity_score": 0.5,
            "spread_score": 0.05,
        }
        base[bad_field] = "x"
        with pytest.raises(ValidationError):
            PaperOpportunity(**base)  # type: ignore[arg-type]

    def test_empty_source_event_refs_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PaperOpportunity(
                opportunity_id="po-x",
                source=PaperOpportunitySource.MANUAL_FIXTURE,
                kind=PaperOpportunityKind.EDGE_CANDIDATE,
                observed_at_ms=0,
                source_event_refs=(),
                source_adapter_id="manual",
                provenance_hash="sha256:x",
                scope_hash="sha256:scope",
                confidence=0.5,
                magnitude_score=0.3,
                risk_score=0.2,
                staleness_ms=0,
                latency_ms=0,
                liquidity_score=0.5,
                spread_score=0.05,
            )

    def test_immutable_frozen(self) -> None:
        o = make_opportunity()
        with pytest.raises(ValidationError):
            o.opportunity_id = "other"  # type: ignore[misc]


class TestMarketConversion:
    def test_market_envelope_strips_raw_fields(self) -> None:
        env = MarketObservationEnvelope(
            event_id="me-1",
            source_adapter_id="synthetic",
            source_system="synthetic",
            venue="binance",
            symbol="BTC-USDT",
            observed_at_ms=1000,
            best_bid=100.0,
            best_ask=100.2,
            mid_price=100.1,
            spread_pct=(0.2 / 100.1) * 100.0,
            orderbook_age_ms=10,
            latency_ms=20,
            bid_depth_10=1.0,
            ask_depth_10=1.0,
            bid_value_10=100.0,
            ask_value_10=100.0,
            volatility_score=0.3,
            imbalance_score=0.2,
            confidence=0.6,
            provenance_hash="sha256:m-1",
        )
        opp = build_paper_opportunity_from_market_observation(env)
        dumped = opp.model_dump()
        for forbidden in ("symbol", "venue", "exchange", "strategy_name", "side"):
            assert forbidden not in dumped


class TestGelAlConversion:
    def test_gelal_envelope_strips_raw_fields(self) -> None:
        env = make_gelal_envelope()
        opp = build_paper_opportunity_from_gelal_shadow(env)
        dumped = opp.model_dump()
        for forbidden in ("symbol", "venue", "strategy_name", "order_side", "api_key"):
            assert forbidden not in dumped
        # scope_hash must not contain raw labels.
        assert "BTC-USDT" not in opp.scope_hash
        assert "binance" not in opp.scope_hash
        assert "latency-arb" not in opp.scope_hash

    def test_kill_switch_envelope_flips_kind(self) -> None:
        env = make_gelal_envelope(
            event_id="kill",
            event_type=__import__(
                "sentinel.integrations.gelal_shadow", fromlist=["x"]
            ).GelAlShadowEventType.KILL_SWITCH_OBSERVED,
            payload={
                "kill_switch_active": True,
                "source": "operator",
                "observed_by": "gel_al_runtime",
            },
        )
        opp = build_paper_opportunity_from_gelal_shadow(env)
        assert opp.kind is PaperOpportunityKind.KILL_SWITCH_OBSERVATION
        assert opp.risk_score == 1.0

    def test_bad_order_envelope_flips_kind(self) -> None:
        env = make_gelal_envelope(
            event_id="bad",
            payload={"confidence": 0.5, "bad_order": True, "order_sent": True},
        )
        opp = build_paper_opportunity_from_gelal_shadow(env)
        assert opp.kind is PaperOpportunityKind.BAD_ORDER_OBSERVATION
        assert opp.risk_score == 1.0
