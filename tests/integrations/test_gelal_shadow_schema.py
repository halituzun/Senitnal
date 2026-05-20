"""V5 — Gel.Al shadow envelope schema tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sentinel.integrations.gelal_shadow import (
    GelAlShadowEnvelope,
    GelAlShadowEventType,
)


def _base_kwargs(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "event_id": "gelal-evt-1",
        "event_type": GelAlShadowEventType.MARKET_OBSERVATION,
        "source_system": "gel_al_borsa",
        "observed_at_ms": 1000,
        "exported_at_ms": 1010,
        "source_table": "market_obs",
        "source_row_id": "row-1",
        "source_hash": "sha256:src-1",
        "environment": "paper",
        "strategy_name": "latency-arb",
        "symbol": "BTC-USDT",
        "venue": "binance",
        "payload": {"confidence": 0.7, "stale_count": 1},
    }
    base.update(overrides)
    return base


class TestGelAlShadowEnvelope:
    def test_valid_envelope_accepted(self) -> None:
        env = GelAlShadowEnvelope(**_base_kwargs())  # type: ignore[arg-type]
        assert env.event_id == "gelal-evt-1"
        assert env.event_type is GelAlShadowEventType.MARKET_OBSERVATION

    def test_exported_before_observed_rejected(self) -> None:
        with pytest.raises(ValidationError):
            GelAlShadowEnvelope(**_base_kwargs(observed_at_ms=2000, exported_at_ms=1000))  # type: ignore[arg-type]

    def test_empty_payload_rejected(self) -> None:
        with pytest.raises(ValidationError):
            GelAlShadowEnvelope(**_base_kwargs(payload={}))  # type: ignore[arg-type]

    @pytest.mark.parametrize(
        "bad_key",
        [
            "api_key",
            "api_secret",
            "secret",
            "private_key",
            "withdraw_address",
            "order_command",
            "execute_command",
            "approve_trade",
            "reject_trade",
            "mutate_threshold",
            "set_kill_switch",
            "clear_kill_switch",
            "sentinel_action",
            "direct_order",
            "account_password",
        ],
    )
    def test_forbidden_payload_key_rejected(self, bad_key: str) -> None:
        with pytest.raises(ValidationError):
            GelAlShadowEnvelope(**_base_kwargs(payload={bad_key: "x", "confidence": 0.5}))  # type: ignore[arg-type]

    def test_live_environment_accepted_as_observation(self) -> None:
        env = GelAlShadowEnvelope(**_base_kwargs(environment="live"))  # type: ignore[arg-type]
        assert env.environment == "live"

    def test_order_sent_accepted_as_observed_fact(self) -> None:
        env = GelAlShadowEnvelope(
            **_base_kwargs(
                event_type=GelAlShadowEventType.EXECUTION_ATTEMPT_OBSERVED,
                payload={"order_sent": True, "bad_order": False, "confidence": 0.6},
            )  # type: ignore[arg-type]
        )
        assert env.payload["order_sent"] is True

    def test_bad_order_accepted_as_observed_fact(self) -> None:
        env = GelAlShadowEnvelope(
            **_base_kwargs(payload={"bad_order": True, "confidence": 0.5})  # type: ignore[arg-type]
        )
        assert env.payload["bad_order"] is True

    def test_immutable_frozen(self) -> None:
        env = GelAlShadowEnvelope(**_base_kwargs())  # type: ignore[arg-type]
        with pytest.raises(ValidationError):
            env.event_id = "other"  # type: ignore[misc]

    def test_extra_top_level_field_rejected(self) -> None:
        kw = _base_kwargs()
        kw["sentinel_action"] = "buy"
        with pytest.raises(ValidationError):
            GelAlShadowEnvelope(**kw)  # type: ignore[arg-type]

    def test_event_type_closed_set(self) -> None:
        with pytest.raises(ValidationError):
            GelAlShadowEnvelope(**_base_kwargs(event_type="not_a_real_type"))  # type: ignore[arg-type]

    def test_source_system_pinned(self) -> None:
        with pytest.raises(ValidationError):
            GelAlShadowEnvelope(**_base_kwargs(source_system="something_else"))  # type: ignore[arg-type]
