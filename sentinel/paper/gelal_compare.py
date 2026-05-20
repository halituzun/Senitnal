"""V7 — Sentinel paper decision vs Gel.Al shadow comparison."""

from __future__ import annotations

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sentinel.integrations.gelal_shadow import (
    GelAlShadowEnvelope,
    GelAlShadowEventType,
)
from sentinel.paper.decision import PaperDecision  # noqa: TC001
from sentinel.runtime.output import SystemOutput, assert_no_forbidden_literal

_AgreementBand = Literal[
    "same_direction",
    "sentinel_more_conservative",
    "sentinel_less_conservative",
    "incomparable",
]


class GelAlPaperComparison(BaseModel):
    """Comparison record: observed Gel.Al shadow vs Sentinel paper decision."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    comparison_id: str = Field(min_length=1)
    gelal_event_id: str = Field(min_length=1)
    paper_decision_id: str = Field(min_length=1)
    gelal_observed_decision: str = Field(min_length=1)
    sentinel_output: SystemOutput
    agreement_band: _AgreementBand
    safety_note: str = Field(min_length=1)
    created_at_ms: int = Field(ge=0)

    @model_validator(mode="after")
    def _validate_comparison(self) -> Self:
        assert_no_forbidden_literal(self.safety_note)
        return self


def _gelal_decision_descriptor(envelope: GelAlShadowEnvelope) -> str:
    """Stringify the Gel.Al-side observed decision label.

    Observer-side: may contain Gel.Al's own block_reason text and
    event-type label.  Stays inside the comparison record; never
    propagates into the Sentinel core.
    """
    payload = envelope.payload
    bad_order = isinstance(payload.get("bad_order"), bool) and bool(payload["bad_order"])
    kill_active = (
        envelope.event_type is GelAlShadowEventType.KILL_SWITCH_OBSERVED
        and isinstance(payload.get("kill_switch_active"), bool)
        and bool(payload["kill_switch_active"])
    )
    if kill_active:
        return "gelal_kill_switch_active"
    if bad_order:
        return "gelal_bad_dispatch_observed"
    if envelope.event_type is GelAlShadowEventType.OPPORTUNITY_BLOCKED:
        return "gelal_opportunity_blocked"
    if envelope.event_type is GelAlShadowEventType.OPPORTUNITY_SEEN:
        return "gelal_opportunity_seen"
    if envelope.event_type is GelAlShadowEventType.RISK_GATE_DECISION:
        return "gelal_risk_gate_decision"
    return f"gelal_{envelope.event_type.value}"


def compare_gelal_shadow_to_paper_decision(
    *,
    envelope: GelAlShadowEnvelope,
    paper_decision: PaperDecision,
    now_ms: int,
) -> GelAlPaperComparison:
    """Compare a Gel.Al shadow observation with a Sentinel paper decision."""
    sentinel_output = paper_decision.output
    descriptor = _gelal_decision_descriptor(envelope)

    band: _AgreementBand
    if descriptor in ("gelal_kill_switch_active", "gelal_bad_dispatch_observed"):
        # Gel.Al observed risk; same-direction iff Sentinel BLOCK.
        if sentinel_output is SystemOutput.BLOCK:
            band = "same_direction"
        elif sentinel_output is SystemOutput.MONITOR:
            band = "sentinel_less_conservative"
        else:
            band = "incomparable"
    elif descriptor == "gelal_opportunity_blocked":
        if sentinel_output is SystemOutput.BLOCK:
            band = "same_direction"
        elif sentinel_output is SystemOutput.MONITOR:
            band = "sentinel_less_conservative"
        else:
            band = "incomparable"
    elif descriptor == "gelal_opportunity_seen":
        if sentinel_output is SystemOutput.MONITOR:
            band = "same_direction"
        elif sentinel_output is SystemOutput.BLOCK:
            band = "sentinel_more_conservative"
        else:
            band = "incomparable"
    elif descriptor == "gelal_risk_gate_decision":
        if sentinel_output is SystemOutput.BLOCK:
            band = "same_direction"
        elif sentinel_output is SystemOutput.MONITOR:
            band = "sentinel_less_conservative"
        else:
            band = "incomparable"
    else:
        band = "incomparable"

    safety_note = (
        f"paper advisory: sentinel={sentinel_output.value}; "
        f"gelal_descriptor={descriptor}; agreement={band}"
    )
    assert_no_forbidden_literal(safety_note)
    return GelAlPaperComparison(
        comparison_id=f"paper-gelal-cmp-{envelope.event_id}-{paper_decision.decision_id}",
        gelal_event_id=envelope.event_id,
        paper_decision_id=paper_decision.decision_id,
        gelal_observed_decision=descriptor,
        sentinel_output=sentinel_output,
        agreement_band=band,
        safety_note=safety_note,
        created_at_ms=now_ms,
    )
