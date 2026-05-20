"""Smoke tests for the 8 v0.1 dev fixtures.

Every spec_family ships with a v0-dev JSON fixture under
`sentinel/numerics/fixtures/`. This module loads each, verifies it
through the loader in DEVELOPMENT mode, and walks the dependency
validator over it.

If a new spec_family is added (or an existing one's file is renamed)
this test will fail and force the build plan to be revisited.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from sentinel.numerics.dependency_validator import validate_dependencies
from sentinel.numerics.loader import LoaderMode, load_artifact
from sentinel.types.numerics import SpecFamily

FIXTURES_DIR = Path(__file__).resolve().parents[2] / "sentinel" / "numerics" / "fixtures"

EXPECTED_FIXTURES: dict[SpecFamily, str] = {
    SpecFamily.INGRESS_COMPILER: "ingress_compiler_numerics_v0_dev_fixture.json",
    SpecFamily.REPLAY_PROTOCOL: "replay_protocol_numerics_v0_dev_fixture.json",
    SpecFamily.MEMORY_WRITE_GATE: "memory_write_gate_numerics_v0_dev_fixture.json",
    SpecFamily.OBSERVER_LEDGER: "observer_ledger_numerics_v0_dev_fixture.json",
    SpecFamily.BACKUP_STRATEGY: "backup_strategy_numerics_v0_dev_fixture.json",
    SpecFamily.BOOTSTRAP_GENOME: "bootstrap_genome_numerics_v0_dev_fixture.json",
    SpecFamily.RECALL_PROTOCOL: "recall_protocol_numerics_v0_dev_fixture.json",
    SpecFamily.ADAPTER_TRUST: "adapter_trust_numerics_v0_dev_fixture.json",
}


class TestFixtureCoverage:
    def test_one_fixture_per_spec_family(self) -> None:
        assert set(EXPECTED_FIXTURES.keys()) == set(SpecFamily)


class TestFixtureLoad:
    @pytest.mark.parametrize(
        ("spec_family", "filename"),
        list(EXPECTED_FIXTURES.items()),
    )
    def test_fixture_loads_in_development(self, spec_family: SpecFamily, filename: str) -> None:
        path = FIXTURES_DIR / filename
        artifact = load_artifact(path, mode=LoaderMode.DEVELOPMENT)
        assert artifact.spec_family is spec_family
        assert artifact.dev_only is True
        assert artifact.numerics_version == "v0-dev"
        assert artifact.fixture_purpose is not None
        assert len(artifact.entries) >= 1

    @pytest.mark.parametrize(
        ("spec_family", "filename"),
        list(EXPECTED_FIXTURES.items()),
    )
    def test_fixture_dependencies_validate(self, spec_family: SpecFamily, filename: str) -> None:
        artifact = load_artifact(FIXTURES_DIR / filename, mode=LoaderMode.DEVELOPMENT)
        validate_dependencies(artifact)

    @pytest.mark.parametrize(
        ("spec_family", "filename"),
        list(EXPECTED_FIXTURES.items()),
    )
    def test_fixture_rejected_in_production(self, spec_family: SpecFamily, filename: str) -> None:
        from sentinel.constitution.violations import InvariantViolation

        with pytest.raises(InvariantViolation) as exc_info:
            load_artifact(FIXTURES_DIR / filename, mode=LoaderMode.PRODUCTION)
        assert exc_info.value.violation_code == "NUMERICS_DEV_ONLY_REJECTED_IN_PRODUCTION"
