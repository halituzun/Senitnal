"""V4 — Outcome alignment + effect channel proposal tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sentinel.replay.effects import (
    AttentionHabituationUpdate,
    IngressCalibrationUpdateProposal,
    MemoryEvidenceKind,
    MemoryVerificationEvidenceProposal,
    SleepSynapseUpdateProposal,
    SynapseDirection,
)
from sentinel.replay.outcome_alignment import (
    OutcomeAlignmentEvidence,
    OutcomeRef,
    compute_outcome_alignment_score,
)


def _ref(**kw: object) -> OutcomeRef:
    defaults: dict[str, object] = {
        "outcome_ref_id": "or-1",
        "source_event_id": "ev-1",
        "observed_at_ms": 100,
        "confidence": 0.7,
        "external": True,
        "payload": {"signal": "neutral"},
    }
    defaults.update(kw)
    return OutcomeRef(**defaults)  # type: ignore[arg-type]


class TestOutcomeRef:
    def test_valid_external(self) -> None:
        _ref()

    def test_internal_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _ref(external=False)

    def test_empty_payload_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _ref(payload={})

    @pytest.mark.parametrize("literal", ["BUY", "SELL", "EXECUTE_REAL", "ORDER_SUBMIT"])
    def test_forbidden_literal_in_payload_rejected(self, literal: str) -> None:
        with pytest.raises(ValidationError):
            _ref(payload={"signal": literal})

    @pytest.mark.parametrize(
        "bad_key", ["api_key", "api_secret", "balance", "side", "order_id", "account_id"]
    )
    def test_forbidden_key_rejected(self, bad_key: str) -> None:
        with pytest.raises(ValidationError):
            _ref(payload={"signal": "ok", bad_key: "x"})


class TestOutcomeAlignmentEvidence:
    def test_valid(self) -> None:
        OutcomeAlignmentEvidence(
            evidence_id="e1",
            session_id="s1",
            memory_record_id="m1",
            outcome_refs=(_ref(),),
            alignment_score=0.5,
            stale=False,
            created_at_ms=0,
        )

    def test_empty_refs_rejected(self) -> None:
        with pytest.raises(ValidationError):
            OutcomeAlignmentEvidence(
                evidence_id="e1",
                session_id="s1",
                memory_record_id="m1",
                outcome_refs=(),
                alignment_score=0.5,
                stale=False,
                created_at_ms=0,
            )


class TestComputeOutcomeAlignmentScore:
    def test_bounded(self) -> None:
        s = compute_outcome_alignment_score(
            outcome_refs=(_ref(confidence=0.8),), record_confidence=0.7
        )
        assert 0.0 <= s <= 1.0

    def test_deterministic(self) -> None:
        refs = (_ref(confidence=0.8),)
        a = compute_outcome_alignment_score(outcome_refs=refs, record_confidence=0.7)
        b = compute_outcome_alignment_score(outcome_refs=refs, record_confidence=0.7)
        assert a == b

    def test_empty_refs_rejected_at_compute(self) -> None:
        with pytest.raises(ValueError):
            compute_outcome_alignment_score(outcome_refs=(), record_confidence=0.7)


class TestEffectChannels:
    def test_sleep_synapse_valid(self) -> None:
        SleepSynapseUpdateProposal(
            proposal_id="p1",
            session_id="s1",
            synapse_id="syn-1",
            direction=SynapseDirection.STRENGTHENING,
            delta=0.1,
            capped_delta=0.05,
            eligibility_trace_id="trace-1",
            evidence_ref="ev-1",
            created_at_ms=0,
        )

    def test_sleep_synapse_cap_too_large_rejected(self) -> None:
        with pytest.raises(ValidationError):
            SleepSynapseUpdateProposal(
                proposal_id="p1",
                session_id="s1",
                synapse_id="syn-1",
                direction=SynapseDirection.STRENGTHENING,
                delta=0.05,
                capped_delta=0.2,
                eligibility_trace_id="trace-1",
                evidence_ref="ev-1",
                created_at_ms=0,
            )

    def test_attention_no_synapse_topology_field(self) -> None:
        # Attention habituation has NO synapse_id field — extra=forbid
        # rejects any attempt to pass one.
        with pytest.raises(ValidationError):
            AttentionHabituationUpdate(
                update_id="u1",
                session_id="s1",
                assembly_id="asm-1",
                context_signature_hash="sha256:ctx",
                habituation_delta=0.1,
                capped_delta=0.05,
                created_at_ms=0,
                synapse_id="syn-1",  # type: ignore[call-arg]
            )

    def test_attention_cap_too_large_rejected(self) -> None:
        with pytest.raises(ValidationError):
            AttentionHabituationUpdate(
                update_id="u1",
                session_id="s1",
                assembly_id="asm-1",
                context_signature_hash="sha256:ctx",
                habituation_delta=0.05,
                capped_delta=0.2,
                created_at_ms=0,
            )

    def test_ingress_calibration_cap_enforced(self) -> None:
        with pytest.raises(ValidationError):
            IngressCalibrationUpdateProposal(
                proposal_id="p1",
                session_id="s1",
                mapping_id="map-1",
                delta=0.1,
                capped_delta=0.2,
                daily_cap_ref=0.05,
                created_at_ms=0,
            )

    def test_ingress_calibration_no_new_payload_type(self) -> None:
        # The schema has NO payload_type field; extra=forbid rejects.
        with pytest.raises(ValidationError):
            IngressCalibrationUpdateProposal(
                proposal_id="p1",
                session_id="s1",
                mapping_id="map-1",
                delta=0.05,
                capped_delta=0.04,
                daily_cap_ref=0.1,
                created_at_ms=0,
                payload_type="NEW_PAYLOAD_TYPE",  # type: ignore[call-arg]
            )

    def test_memory_evidence_proposal_does_not_mutate(self) -> None:
        proposal = MemoryVerificationEvidenceProposal(
            proposal_id="p1",
            session_id="s1",
            memory_record_id="m1",
            evidence_kind=MemoryEvidenceKind.REPLAY_SURVIVAL,
            evidence_id="e1",
            usable_for_gate=False,
            created_at_ms=0,
        )
        assert proposal.usable_for_gate is False
