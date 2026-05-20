"""Tests for the adapter trust composition + hard gates."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sentinel.adapters.trust import (
    AdapterTrustRecord,
    TrustBand,
    compute_trust,
)
from sentinel.constitution.violations import InvariantViolation


def _record(**overrides: object) -> AdapterTrustRecord:
    defaults: dict[str, object] = dict(
        adapter_id="ad-1",
        signature_validity=True,
        manifest_hash_integrity=True,
        neural_seed_emission_count=0,
        channel_binding_compliance=1.0,
        rate_compliance=1.0,
        declaration_drift=1.0,
        reliability_score=1.0,
    )
    defaults.update(overrides)
    return AdapterTrustRecord(**defaults)  # type: ignore[arg-type]


class TestHardGates:
    def test_signature_invalid_revoked(self) -> None:
        rec = _record(signature_validity=False)
        out = compute_trust(rec)
        assert out.hard_gates_passed is False
        assert out.band is TrustBand.REVOKED
        assert out.composite_score == 0.0

    def test_manifest_hash_failed_revoked(self) -> None:
        rec = _record(manifest_hash_integrity=False)
        out = compute_trust(rec)
        assert out.band is TrustBand.REVOKED


class TestNeuralSeedRedLine:
    def test_emission_count_above_zero_raises_at_schema(self) -> None:
        # InvariantViolation is raised before AdapterTrustRecord even
        # constructs (constitutional red line).
        with pytest.raises((InvariantViolation, ValidationError)):
            _record(neural_seed_emission_count=1)


class TestCompositeAndBands:
    def test_all_soft_one_high_band(self) -> None:
        out = compute_trust(_record())
        assert out.band is TrustBand.HIGH
        assert out.composite_score == 1.0

    def test_one_soft_zero_revoked(self) -> None:
        out = compute_trust(_record(channel_binding_compliance=0.0))
        assert out.composite_score == 0.0
        assert out.band is TrustBand.REVOKED

    def test_medium_band(self) -> None:
        # product = 0.9 * 0.9 * 0.9 * 0.9 = 0.6561 → medium [0.5, 0.8)
        rec = _record(
            channel_binding_compliance=0.9,
            rate_compliance=0.9,
            declaration_drift=0.9,
            reliability_score=0.9,
        )
        out = compute_trust(rec)
        assert pytest.approx(out.composite_score, rel=1e-9) == 0.6561
        assert out.band is TrustBand.MEDIUM

    def test_low_band(self) -> None:
        # product = 0.8 * 0.8 * 0.8 * 0.8 = 0.4096 → low [0.3, 0.5)
        rec = _record(
            channel_binding_compliance=0.8,
            rate_compliance=0.8,
            declaration_drift=0.8,
            reliability_score=0.8,
        )
        out = compute_trust(rec)
        assert pytest.approx(out.composite_score, rel=1e-9) == 0.4096
        assert out.band is TrustBand.LOW

    def test_quarantined_band(self) -> None:
        # product 0.7^4 = 0.2401 → quarantined (0.0, 0.3)
        rec = _record(
            channel_binding_compliance=0.7,
            rate_compliance=0.7,
            declaration_drift=0.7,
            reliability_score=0.7,
        )
        out = compute_trust(rec)
        assert pytest.approx(out.composite_score, rel=1e-9) == 0.2401
        assert out.band is TrustBand.QUARANTINED


class TestFieldBounds:
    def test_negative_soft_score_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _record(rate_compliance=-0.1)

    def test_above_one_soft_score_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _record(reliability_score=1.1)
