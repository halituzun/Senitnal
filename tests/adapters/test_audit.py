"""Tests for the adapter manifest / trust audit emission helpers."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003 (fixture annotation)

import pytest
from sentinel.adapters.audit import (
    emit_manifest_status_changed,
    emit_neural_seed_attempt_revoke,
)
from sentinel.observer.ledger import JsonlObserverLedger
from sentinel.runtime.output import ForbiddenOutputViolation
from sentinel.types.adapters import AdapterManifestStatus


@pytest.fixture
def ledger_path(tmp_path: Path) -> Path:
    return tmp_path / "ledger.jsonl"


@pytest.fixture
def ledger(ledger_path: Path) -> JsonlObserverLedger:
    return JsonlObserverLedger(ledger_path)


class TestStatusChanged:
    def test_active_to_quarantined(self, ledger: JsonlObserverLedger) -> None:
        ev = emit_manifest_status_changed(
            ledger,
            adapter_id="ad-1",
            manifest_id="man-1",
            previous_status=AdapterManifestStatus.ACTIVE,
            new_status=AdapterManifestStatus.QUARANTINED,
            reason="rate violation",
            now_ms=1,
        )
        assert ev.event_type == "ADAPTER_MANIFEST_STATUS_CHANGED"
        assert ev.event_family.value == "ledger_meta"
        assert ev.payload["adapter_id"] == "ad-1"
        assert ev.payload["previous_status"] == "active"
        assert ev.payload["new_status"] == "quarantined"
        assert ev.payload["reason"] == "rate violation"

    def test_forbidden_reason_rejected(self, ledger: JsonlObserverLedger) -> None:
        with pytest.raises(ForbiddenOutputViolation):
            emit_manifest_status_changed(
                ledger,
                adapter_id="ad-1",
                manifest_id="man-1",
                previous_status=AdapterManifestStatus.ACTIVE,
                new_status=AdapterManifestStatus.REVOKED,
                reason="attempted to buy via execute_real",
                now_ms=1,
            )

    def test_chain_continues(self, ledger: JsonlObserverLedger) -> None:
        emit_manifest_status_changed(
            ledger,
            adapter_id="ad-1",
            manifest_id="man-1",
            previous_status=AdapterManifestStatus.CANDIDATE,
            new_status=AdapterManifestStatus.REGISTERED,
            reason="initial registration",
            now_ms=1,
        )
        emit_manifest_status_changed(
            ledger,
            adapter_id="ad-1",
            manifest_id="man-1",
            previous_status=AdapterManifestStatus.REGISTERED,
            new_status=AdapterManifestStatus.ACTIVE,
            reason="trust check passed",
            now_ms=2,
        )
        assert ledger.verify() is True


class TestNeuralSeedAttemptRevoke:
    def test_emits_canonical_red_line_audit(self, ledger: JsonlObserverLedger) -> None:
        ev = emit_neural_seed_attempt_revoke(
            ledger,
            adapter_id="ad-1",
            manifest_id="man-1",
            previous_status=AdapterManifestStatus.ACTIVE,
            now_ms=1,
        )
        assert ev.event_type == "ADAPTER_MANIFEST_STATUS_CHANGED"
        assert ev.payload["new_status"] == "revoked"
        assert ev.payload["reason"] == "neural_seed_emission_attempt"
        assert ev.payload["previous_status"] == "active"
