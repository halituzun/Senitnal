"""Tests for the workspace pulse emitter."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003 (fixture annotation)

import pytest
from sentinel.observer.ledger import JsonlObserverLedger
from sentinel.types.neural_seed import ProvenanceRef
from sentinel.types.payload import PayloadSeed, PrimerPayload
from sentinel.types.workspace import WorkspacePulseEvent
from sentinel.workspace.pulse import emit_workspace_pulse, should_emit_pulse


def _pulse(
    *,
    pulse_id: str = "pulse-1",
    coherence: float = 0.5,
) -> WorkspacePulseEvent:
    return WorkspacePulseEvent(
        pulse_id=pulse_id,
        assembly_id="assembly-1",
        occurred_at_ms=42,
        dominant_payload_mix=(
            PayloadSeed(payload=PrimerPayload.URGENCY, intensity=0.7),
            PayloadSeed(payload=PrimerPayload.CONTRADICTION, intensity=0.3),
        ),
        activation_mass=0.6,
        coherence=coherence,
        persistence=0.4,
        habituation_penalty=0.1,
        fatigue_penalty=0.05,
        dissonance_score=0.25,
        allocation_share=0.3,
        ttl_ms=750,
        context_signature_hash="sha256:abc",
    )


@pytest.fixture
def ledger_path(tmp_path: Path) -> Path:
    return tmp_path / "ledger.jsonl"


@pytest.fixture
def ledger(ledger_path: Path) -> JsonlObserverLedger:
    return JsonlObserverLedger(ledger_path)


class TestShouldEmit:
    def test_above_threshold_true(self) -> None:
        assert should_emit_pulse(_pulse(coherence=0.8), coherence_threshold=0.5) is True

    def test_equal_threshold_true(self) -> None:
        assert should_emit_pulse(_pulse(coherence=0.5), coherence_threshold=0.5) is True

    def test_below_threshold_false(self) -> None:
        assert should_emit_pulse(_pulse(coherence=0.2), coherence_threshold=0.5) is False

    def test_invalid_threshold_raises(self) -> None:
        with pytest.raises(ValueError):
            should_emit_pulse(_pulse(coherence=0.5), coherence_threshold=1.5)
        with pytest.raises(ValueError):
            should_emit_pulse(_pulse(coherence=0.5), coherence_threshold=-0.1)


class TestEmit:
    def test_emit_appends_to_ledger(self, ledger: JsonlObserverLedger) -> None:
        prov = ProvenanceRef(source_event_id="src-1")
        ev = emit_workspace_pulse(ledger, _pulse(), provenance=prov)
        assert ev.event_type == "WORKSPACE_PULSE"
        assert ev.event_family.value == "attention"
        assert ev.payload["pulse_id"] == "pulse-1"
        on_disk = ledger.read_all()
        assert len(on_disk) == 1

    def test_chain_continues_after_pulse(self, ledger: JsonlObserverLedger) -> None:
        prov = ProvenanceRef(source_event_id="src-1")
        emit_workspace_pulse(ledger, _pulse(pulse_id="p1"), provenance=prov)
        emit_workspace_pulse(ledger, _pulse(pulse_id="p2"), provenance=prov)
        on_disk = ledger.read_all()
        assert len(on_disk) == 2
        assert on_disk[1].previous_event_hash == on_disk[0].event_hash
        assert ledger.verify() is True

    def test_payload_carries_dominant_mix(self, ledger: JsonlObserverLedger) -> None:
        from typing import cast

        prov = ProvenanceRef(source_event_id="src-1")
        ev = emit_workspace_pulse(ledger, _pulse(), provenance=prov)
        mix = cast("list[dict[str, object]]", ev.payload["dominant_payload_mix"])
        assert isinstance(mix, list)
        payloads = {str(seed["payload"]) for seed in mix}
        assert "urgency" in payloads
        assert "contradiction" in payloads


class TestNoActionCoupling:
    def test_emit_does_not_imply_action_intent(self) -> None:
        """The emitter has no path that constructs any action / intent."""
        import inspect

        from sentinel.workspace import pulse as mod

        src = inspect.getsource(mod)
        # Sanity: pulse module never references action/execution constructs.
        for forbidden in ("ApprovedActionIntent", "execute", "BUY", "SELL"):
            assert forbidden not in src, f"workspace.pulse must not couple to {forbidden!r}"
