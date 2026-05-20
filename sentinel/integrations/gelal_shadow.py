"""Gel.Al shadow event schemas (V5).

Pydantic v2 schemas for the one-way Gel.Al → Sentinel shadow event
contract.  All envelopes are frozen, ``extra='forbid'`` and strict.
The denylist below blocks API keys, account-mutation commands, and
execution-instruction fields at construction time so a forged
envelope cannot escalate into a Sentinel-side action.

Constitutional boundary:
    - Observer-side only.  These types never cross into a v0.1
      ``ObservationEvent`` directly.  The sanitizer in
      ``sentinel/integrations/gelal_sanitizer.py`` is the bridge.
    - No exchange SDK import.  No network import.  No LLM import.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Final, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

# ---------------------------------------------------------------------------
# Closed event-type enum
# ---------------------------------------------------------------------------


class GelAlShadowEventType(StrEnum):
    """Closed observer-side enum for shadow events Gel.Al may export."""

    MARKET_OBSERVATION = "market_observation"
    OPPORTUNITY_SEEN = "opportunity_seen"
    OPPORTUNITY_BLOCKED = "opportunity_blocked"
    RISK_GATE_DECISION = "risk_gate_decision"
    EXECUTION_ATTEMPT_OBSERVED = "execution_attempt_observed"
    PAPER_RESULT_OBSERVED = "paper_result_observed"
    LIVE_RESULT_OBSERVED = "live_result_observed"
    SYSTEM_HEALTH_OBSERVED = "system_health_observed"
    KILL_SWITCH_OBSERVED = "kill_switch_observed"


# ---------------------------------------------------------------------------
# Forbidden payload keys (defense-in-depth).
#
# Even though every payload model below uses ``extra='forbid'`` for its
# typed-payload subset, the generic ``GelAlShadowEnvelope.payload`` is
# ``dict[str, object]`` (Gel.Al may evolve faster than Sentinel).  We
# scan the dict for known-dangerous keys and reject the envelope.  The
# list mirrors the goal spec verbatim.
# ---------------------------------------------------------------------------

_FORBIDDEN_PAYLOAD_KEYS: Final[frozenset[str]] = frozenset(
    {
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
    }
)


def _assert_no_forbidden_payload_keys(payload: dict[str, object]) -> None:
    bad = sorted(k for k in payload if k in _FORBIDDEN_PAYLOAD_KEYS)
    if bad:
        raise ValueError(
            f"forbidden payload key(s) present in Gel.Al shadow envelope: {bad}; "
            "Sentinel is read-only, command / credential keys cannot cross the boundary"
        )


# ---------------------------------------------------------------------------
# Top-level envelope
# ---------------------------------------------------------------------------


class GelAlShadowEnvelope(BaseModel):
    """One observer-side Gel.Al shadow event.

    ``event_type`` selects which optional payload model is most
    appropriate (see ``GelAlOpportunityPayload`` etc.) but the
    envelope intentionally stores ``payload`` as ``dict[str, object]``
    so unrelated Gel.Al event types can still flow.

    All execution-instruction fields are rejected; see
    ``_FORBIDDEN_PAYLOAD_KEYS``.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    event_id: str = Field(min_length=1)
    event_type: GelAlShadowEventType
    source_system: Literal["gel_al_borsa"] = "gel_al_borsa"
    observed_at_ms: int = Field(ge=0)
    exported_at_ms: int = Field(ge=0)
    source_table: str = Field(min_length=1)
    source_row_id: str = Field(min_length=1)
    source_hash: str = Field(min_length=1)
    environment: Literal["local", "paper", "shadow", "canary", "live"]
    strategy_name: str | None = None
    symbol: str | None = None
    venue: str | None = None
    payload: dict[str, object]

    @model_validator(mode="after")
    def _validate_envelope(self) -> Self:
        if self.exported_at_ms < self.observed_at_ms:
            raise ValueError(
                f"exported_at_ms ({self.exported_at_ms}) must be >= observed_at_ms "
                f"({self.observed_at_ms})"
            )
        if not self.payload:
            raise ValueError("payload must be non-empty")
        _assert_no_forbidden_payload_keys(self.payload)
        return self


# ---------------------------------------------------------------------------
# Typed payload models (optional helpers — not stored inside the envelope)
# ---------------------------------------------------------------------------


class GelAlOpportunityPayload(BaseModel):
    """Typed shape for opportunity_seen / opportunity_blocked payload."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    opportunity_id: str = Field(min_length=1)
    strategy_name: str = Field(min_length=1)
    symbol: str = Field(min_length=1)
    venue: str = Field(min_length=1)
    gross_edge_pct: float = Field(allow_inf_nan=False)
    fee_pct: float = Field(ge=0.0, allow_inf_nan=False)
    slip_pct: float = Field(ge=0.0, allow_inf_nan=False)
    net_edge_pct: float = Field(allow_inf_nan=False)
    confidence: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    block_reason: str | None = None
    order_sent: bool
    bad_order: bool
    depth_age_ms: int = Field(ge=0)
    latency_ms: int = Field(ge=0)
    provenance_hash: str = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_payload(self) -> Self:
        if self.net_edge_pct > self.gross_edge_pct + 1e-9:
            raise ValueError(
                f"net_edge_pct ({self.net_edge_pct}) cannot exceed "
                f"gross_edge_pct ({self.gross_edge_pct})"
            )
        return self


class GelAlRiskDecisionPayload(BaseModel):
    """Typed shape for risk_gate_decision payload."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    decision_id: str = Field(min_length=1)
    strategy_name: str = Field(min_length=1)
    symbol: str = Field(min_length=1)
    venue: str = Field(min_length=1)
    decision: str = Field(min_length=1)
    block_reason: str | None = None
    risk_score: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    confidence: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    order_sent: bool
    bad_order: bool
    provenance_hash: str = Field(min_length=1)


class GelAlHealthPayload(BaseModel):
    """Typed shape for system_health_observed payload."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    component_name: str = Field(min_length=1)
    status: str = Field(min_length=1)
    latency_ms: int = Field(ge=0)
    error_count: int = Field(ge=0)
    stale_count: int = Field(ge=0)
    confidence: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    provenance_hash: str = Field(min_length=1)


class GelAlKillSwitchPayload(BaseModel):
    """Typed shape for kill_switch_observed payload.

    Sentinel may observe Gel.Al's kill switch; it may never set or
    clear it.  The schema is observational only.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    kill_switch_active: bool
    source: str = Field(min_length=1)
    reason: str | None = None
    observed_by: str = Field(min_length=1)
    provenance_hash: str = Field(min_length=1)
