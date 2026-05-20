"""Hypothesis property-based tests for cross-cutting invariants.

Per build plan §16 (Test-first Discipline) — property-based coverage
for the invariants that must hold for *every* well-formed input,
not just the hand-picked unit cases.

Properties covered:
    - apply_profile_cap: output always in [0, cap] for any input in [0,1]
    - membership(band, value): output always in [0.0, 1.0]
    - compute_recall_score: output always in [0.0, 1.0]
    - compute_trust composite_score: in [0.0, 1.0] when hard gates pass
    - canonical_json_bytes: deterministic for the same logical mapping
    - sha256_digest: deterministic
    - placeholder_event_hash: always parses to a sha256 sentinel
"""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st
from sentinel.adapters.trust import AdapterTrustRecord, compute_trust
from sentinel.ingress.profile_caps import PROFILE_RANK, apply_profile_cap, cap_for
from sentinel.ingress.soft_overlap import FuzzyBand, membership
from sentinel.observer.hash_chain import (
    canonical_json_bytes,
    placeholder_event_hash,
    sha256_digest,
)
from sentinel.recall.ranking import RankingInputs, compute_recall_score
from sentinel.runtime.output import FORBIDDEN_OUTPUT_LITERALS, SystemOutput
from sentinel.types.neural_seed import EventProfile

bounded_unit = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)


class TestProfileCapProperty:
    @given(intensity=bounded_unit, profile=st.sampled_from(list(EventProfile)))
    def test_output_within_profile_cap(self, intensity: float, profile: EventProfile) -> None:
        out = apply_profile_cap(profile, intensity)
        assert 0.0 <= out <= cap_for(profile)
        assert out <= intensity + 1e-12  # cap can only reduce, never amplify

    def test_rank_monotone_in_caps(self) -> None:
        from itertools import pairwise

        # Constants check: enforced by import-time assert, restate.
        for higher, lower in pairwise(PROFILE_RANK):
            assert cap_for(higher) >= cap_for(lower)


class TestSoftOverlapProperty:
    @given(
        low=st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False),
        delta1=st.floats(min_value=0.0, max_value=50.0, allow_nan=False, allow_infinity=False),
        delta2=st.floats(min_value=0.0, max_value=50.0, allow_nan=False, allow_infinity=False),
        delta3=st.floats(min_value=0.0, max_value=50.0, allow_nan=False, allow_infinity=False),
        value=st.floats(min_value=-200.0, max_value=200.0, allow_nan=False, allow_infinity=False),
    )
    def test_membership_in_unit_interval(
        self,
        low: float,
        delta1: float,
        delta2: float,
        delta3: float,
        value: float,
    ) -> None:
        # Build a monotone band: low <= peak_low <= peak_high <= high
        peak_low = low + delta1
        peak_high = peak_low + delta2
        high = peak_high + delta3
        band = FuzzyBand(low=low, peak_low=peak_low, peak_high=peak_high, high=high)
        m = membership(band, value)
        assert 0.0 <= m <= 1.0


class TestRecallScoreProperty:
    @given(
        status=bounded_unit,
        prov=bounded_unit,
        fresh=bounded_unit,
        contra=bounded_unit,
        habit=bounded_unit,
        scope=bounded_unit,
    )
    def test_score_in_unit_interval(
        self,
        status: float,
        prov: float,
        fresh: float,
        contra: float,
        habit: float,
        scope: float,
    ) -> None:
        inputs = RankingInputs(
            status_weight=status,
            provenance_strength=prov,
            freshness_dampening=fresh,
            contradiction_penalty=contra,
            habituation_penalty=habit,
            scope_match_score=scope,
        )
        s = compute_recall_score(inputs)
        assert 0.0 <= s <= 1.0


class TestTrustCompositionProperty:
    @given(
        channel=bounded_unit,
        rate=bounded_unit,
        drift=bounded_unit,
        reliability=bounded_unit,
    )
    def test_composite_in_unit_interval_when_hard_gates_pass(
        self,
        channel: float,
        rate: float,
        drift: float,
        reliability: float,
    ) -> None:
        rec = AdapterTrustRecord(
            adapter_id="probe",
            signature_validity=True,
            manifest_hash_integrity=True,
            neural_seed_emission_count=0,
            channel_binding_compliance=channel,
            rate_compliance=rate,
            declaration_drift=drift,
            reliability_score=reliability,
        )
        c = compute_trust(rec)
        assert c.hard_gates_passed is True
        assert 0.0 <= c.composite_score <= 1.0

    @given(
        channel=bounded_unit,
        rate=bounded_unit,
        drift=bounded_unit,
        reliability=bounded_unit,
    )
    def test_signature_invalid_forces_revoked(
        self,
        channel: float,
        rate: float,
        drift: float,
        reliability: float,
    ) -> None:
        rec = AdapterTrustRecord(
            adapter_id="probe",
            signature_validity=False,
            manifest_hash_integrity=True,
            neural_seed_emission_count=0,
            channel_binding_compliance=channel,
            rate_compliance=rate,
            declaration_drift=drift,
            reliability_score=reliability,
        )
        c = compute_trust(rec)
        assert c.composite_score == 0.0


class TestCanonicalJsonProperty:
    @given(
        st.dictionaries(
            keys=st.text(min_size=1, max_size=20),
            values=st.integers(min_value=-1000, max_value=1000),
            max_size=10,
        )
    )
    def test_deterministic_for_same_mapping(self, payload: dict[str, int]) -> None:
        a = canonical_json_bytes(payload)
        b = canonical_json_bytes(payload)
        assert a == b

    @given(st.binary(min_size=0, max_size=1024))
    def test_sha256_digest_format(self, data: bytes) -> None:
        d = sha256_digest(data)
        assert d.startswith("sha256:")
        assert len(d) == len("sha256:") + 64
        hex_part = d.removeprefix("sha256:")
        int(hex_part, 16)  # raises if not valid hex


class TestPlaceholderHashProperty:
    def test_placeholder_is_sha256_format(self) -> None:
        ph = placeholder_event_hash()
        assert ph.startswith("sha256:")
        assert len(ph) == 71


class TestSystemOutputProperty:
    def test_no_output_value_contains_forbidden_literal(self) -> None:
        for o in SystemOutput:
            for needle in FORBIDDEN_OUTPUT_LITERALS:
                assert needle not in o.value.lower()
