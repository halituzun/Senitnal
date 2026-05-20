"""Tests for the bootstrap rule schema and MVP registry."""

from __future__ import annotations

import pytest
from sentinel.ingress.rules import MVP_BOOTSTRAP_RULES, BootstrapRule
from sentinel.ingress.soft_overlap import FuzzyBand
from sentinel.types.neural_seed import EventProfile
from sentinel.types.payload import PrimerPayload


def _band() -> FuzzyBand:
    return FuzzyBand(low=0.0, peak_low=0.3, peak_high=0.7, high=1.0)


class TestRuleConstruction:
    def test_valid_rule_accepted(self) -> None:
        r = BootstrapRule(
            rule_id="x",
            applies_to_profile=EventProfile.OBSERVATION_EVENT,
            stimulus_attribute="magnitude",
            stimulus_band=_band(),
            payload=PrimerPayload.NOVELTY,
            base_intensity=0.5,
            source_ref="docs",
        )
        assert r.rule_id == "x"

    def test_empty_rule_id_rejected(self) -> None:
        with pytest.raises(ValueError):
            BootstrapRule(
                rule_id="",
                applies_to_profile=EventProfile.OBSERVATION_EVENT,
                stimulus_attribute="magnitude",
                stimulus_band=_band(),
                payload=PrimerPayload.NOVELTY,
                base_intensity=0.5,
                source_ref="docs",
            )

    def test_empty_attribute_rejected(self) -> None:
        with pytest.raises(ValueError):
            BootstrapRule(
                rule_id="x",
                applies_to_profile=EventProfile.OBSERVATION_EVENT,
                stimulus_attribute="",
                stimulus_band=_band(),
                payload=PrimerPayload.NOVELTY,
                base_intensity=0.5,
                source_ref="docs",
            )

    def test_out_of_range_base_intensity_rejected(self) -> None:
        with pytest.raises(ValueError):
            BootstrapRule(
                rule_id="x",
                applies_to_profile=EventProfile.OBSERVATION_EVENT,
                stimulus_attribute="m",
                stimulus_band=_band(),
                payload=PrimerPayload.NOVELTY,
                base_intensity=1.5,
                source_ref="docs",
            )

    def test_empty_source_ref_rejected(self) -> None:
        with pytest.raises(ValueError):
            BootstrapRule(
                rule_id="x",
                applies_to_profile=EventProfile.OBSERVATION_EVENT,
                stimulus_attribute="m",
                stimulus_band=_band(),
                payload=PrimerPayload.NOVELTY,
                base_intensity=0.5,
                source_ref="",
            )


class TestMvpRegistry:
    def test_registry_non_empty(self) -> None:
        assert len(MVP_BOOTSTRAP_RULES) > 0

    def test_rule_ids_unique(self) -> None:
        ids = [r.rule_id for r in MVP_BOOTSTRAP_RULES]
        assert len(set(ids)) == len(ids)

    def test_all_profiles_covered_by_at_least_one_rule_except_candidate(
        self,
    ) -> None:
        """CandidateRecall is deliberately deferred to later phases."""
        covered = {r.applies_to_profile for r in MVP_BOOTSTRAP_RULES}
        for p in EventProfile:
            if p is EventProfile.CANDIDATE_RECALL:
                continue
            assert p in covered, f"profile {p.value!r} has no MVP rule"

    def test_every_rule_has_source_ref(self) -> None:
        for r in MVP_BOOTSTRAP_RULES:
            assert r.source_ref != ""
