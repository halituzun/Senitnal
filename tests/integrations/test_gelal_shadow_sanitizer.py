"""V5 — Gel.Al sanitizer + manifest tests."""

from __future__ import annotations

from sentinel.integrations.gelal_manifest import build_gelal_shadow_manifest
from sentinel.integrations.gelal_sanitizer import (
    build_gelal_shadow_audit_payload,
    sanitize_gelal_shadow_to_observation_event,
)
from sentinel.integrations.gelal_shadow import (
    GelAlShadowEnvelope,
    GelAlShadowEventType,
)
from sentinel.types.adapters import AdapterCapability
from sentinel.types.events import ObservationEvent


def _opportunity_env() -> GelAlShadowEnvelope:
    return GelAlShadowEnvelope(
        event_id="evt-1",
        event_type=GelAlShadowEventType.OPPORTUNITY_SEEN,
        source_system="gel_al_borsa",
        observed_at_ms=1000,
        exported_at_ms=1020,
        source_table="opportunities",
        source_row_id="row-1",
        source_hash="sha256:opp-1",
        environment="paper",
        strategy_name="latency-arb",
        symbol="BTC-USDT",
        venue="binance",
        payload={
            "opportunity_id": "opp-1",
            "net_edge_pct": 0.5,
            "confidence": 0.7,
            "depth_age_ms": 5,
            "latency_ms": 25,
            "order_sent": False,
            "bad_order": False,
        },
    )


def _kill_switch_env(active: bool) -> GelAlShadowEnvelope:
    return GelAlShadowEnvelope(
        event_id="kill-1",
        event_type=GelAlShadowEventType.KILL_SWITCH_OBSERVED,
        source_system="gel_al_borsa",
        observed_at_ms=2000,
        exported_at_ms=2002,
        source_table="kill_switch",
        source_row_id="ks-1",
        source_hash="sha256:ks-1",
        environment="live",
        payload={
            "kill_switch_active": active,
            "source": "operator",
            "observed_by": "gel_al_runtime",
        },
    )


class TestSanitizer:
    def test_returns_observation_event(self) -> None:
        obs = sanitize_gelal_shadow_to_observation_event(_opportunity_env())
        assert isinstance(obs, ObservationEvent)
        assert obs.source_adapter_id == "gelal-shadow"

    def test_no_domain_labels_in_observation_event(self) -> None:
        obs = sanitize_gelal_shadow_to_observation_event(_opportunity_env())
        # ObservationEvent extra='forbid' already blocks domain labels;
        # we verify via model_dump that they did not slip in.
        dumped = obs.model_dump()
        for forbidden in (
            "symbol",
            "venue",
            "strategy_name",
            "opportunity_id",
            "order_sent",
            "bad_order",
            "decision",
            "block_reason",
            "payload",
        ):
            assert forbidden not in dumped

    def test_bounded_magnitude_and_novelty(self) -> None:
        obs = sanitize_gelal_shadow_to_observation_event(_opportunity_env())
        assert 0.0 <= obs.magnitude_normalized <= 1.0
        assert 0.0 <= obs.novelty_indicator <= 1.0

    def test_kill_switch_dominates_magnitude(self) -> None:
        obs = sanitize_gelal_shadow_to_observation_event(_kill_switch_env(active=True))
        assert obs.magnitude_normalized == 1.0
        assert obs.novelty_indicator == 1.0

    def test_staleness_computed(self) -> None:
        obs = sanitize_gelal_shadow_to_observation_event(_opportunity_env())
        # export-lag (20ms) + latency (25ms) + depth_age (5ms) = 50
        assert obs.staleness_ms == 50

    def test_deterministic(self) -> None:
        a = sanitize_gelal_shadow_to_observation_event(_opportunity_env())
        b = sanitize_gelal_shadow_to_observation_event(_opportunity_env())
        assert a == b

    def test_audit_payload_preserves_provenance(self) -> None:
        env = _opportunity_env()
        payload = build_gelal_shadow_audit_payload(env)
        assert payload["symbol"] == "BTC-USDT"
        assert payload["venue"] == "binance"
        assert payload["strategy_name"] == "latency-arb"
        assert payload["source_table"] == "opportunities"
        assert payload["source_hash"] == "sha256:opp-1"
        assert payload["event_type"] == "opportunity_seen"

    def test_audit_payload_excludes_secrets_and_commands(self) -> None:
        env = _opportunity_env()
        payload = build_gelal_shadow_audit_payload(env)
        # The summary only includes whitelisted keys; even if envelope
        # had a forbidden key (it cannot, validator blocks it), the
        # audit payload would not echo it.
        for forbidden in (
            "api_key",
            "api_secret",
            "secret",
            "set_kill_switch",
            "approve_trade",
            "direct_order",
            "account_password",
        ):
            assert forbidden not in payload
            assert forbidden not in payload["payload_summary"]  # type: ignore[operator]


class TestManifest:
    def test_observe_only(self) -> None:
        m = build_gelal_shadow_manifest()
        assert m.capabilities == (AdapterCapability.OBSERVE,)

    def test_execute_capability_rejected(self) -> None:
        # AdapterCapability.EXECUTE is not in the manifest the builder produces.
        m = build_gelal_shadow_manifest()
        assert AdapterCapability.EXECUTE not in m.capabilities
        assert AdapterCapability.INTENT_RELAY not in m.capabilities
        assert AdapterCapability.MEMORY_WRITER not in m.capabilities
        assert AdapterCapability.RECALL_PROVIDER not in m.capabilities

    def test_neural_seed_output_impossible(self) -> None:
        from sentinel.types.adapters import AdapterOutputChannel

        # AdapterOutputChannel does not even contain a NeuralSeed variant.
        assert not hasattr(AdapterOutputChannel, "NEURAL_SEED")
