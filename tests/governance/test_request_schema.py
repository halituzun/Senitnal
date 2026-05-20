"""V9 — Governance request schema tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sentinel.governance.request import GovernanceRequestKind, LiveGovernanceRequest

from tests.governance._fixtures import make_request, make_scope


class TestRequestSchema:
    def test_valid_request_accepted(self) -> None:
        req = make_request()
        assert req.requires_human_approval is True

    def test_live_impact_requires_human_approval(self) -> None:
        with pytest.raises(ValidationError):
            LiveGovernanceRequest(
                request_id="x",
                request_kind=GovernanceRequestKind.CANDIDATE_LIVE_ACTION_REVIEW,
                scope=make_scope(),
                candidate_ref="cand-x",
                source_event_refs=("ev-1",),
                observed_at_ms=1_000_000,
                deadline_ms=2_000_000,
                provenance_hash="sha256:p",
                risk_score=0.2,
                confidence=0.7,
                staleness_ms=0,
                latency_ms=0,
                live_impact_possible=True,
                requires_human_approval=False,
            )

    def test_deadline_before_observed_rejected(self) -> None:
        with pytest.raises(ValidationError):
            make_request(observed_at_ms=2_000_000, deadline_ms=1_000_000)

    def test_empty_source_event_refs_rejected(self) -> None:
        with pytest.raises(ValidationError):
            LiveGovernanceRequest(
                request_id="x",
                request_kind=GovernanceRequestKind.CANDIDATE_LIVE_ACTION_REVIEW,
                scope=make_scope(),
                candidate_ref="cand-x",
                source_event_refs=(),
                observed_at_ms=1_000_000,
                deadline_ms=2_000_000,
                provenance_hash="sha256:p",
                risk_score=0.2,
                confidence=0.7,
                staleness_ms=0,
                latency_ms=0,
                live_impact_possible=True,
                requires_human_approval=True,
            )

    @pytest.mark.parametrize("bad_field", ["symbol", "venue", "order_side", "api_key"])
    def test_forbidden_field_rejected(self, bad_field: str) -> None:
        base: dict[str, object] = {
            "request_id": "x",
            "request_kind": GovernanceRequestKind.CANDIDATE_LIVE_ACTION_REVIEW,
            "scope": make_scope(),
            "candidate_ref": "cand-x",
            "source_event_refs": ("ev-1",),
            "observed_at_ms": 1_000_000,
            "deadline_ms": 2_000_000,
            "provenance_hash": "sha256:p",
            "risk_score": 0.2,
            "confidence": 0.7,
            "staleness_ms": 0,
            "latency_ms": 0,
            "live_impact_possible": True,
            "requires_human_approval": True,
        }
        base[bad_field] = "x"
        with pytest.raises(ValidationError):
            LiveGovernanceRequest(**base)  # type: ignore[arg-type]

    def test_frozen_immutable(self) -> None:
        req = make_request()
        with pytest.raises(ValidationError):
            req.request_id = "other"  # type: ignore[misc]
