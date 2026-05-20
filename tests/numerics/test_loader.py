"""Tests for the numerics artifact loader."""

from __future__ import annotations

import json
from pathlib import Path  # noqa: TC003 (fixture annotation)

import pytest
from sentinel.constitution.violations import InvariantViolation
from sentinel.numerics.loader import LoaderMode, MissingArtifactError, load_artifact


def _valid_dev_artifact_json() -> dict[str, object]:
    return {
        "spec_family": "ingress_compiler",
        "owning_spec_ref": "INGRESS_COMPILER_NUMERICS.md@v0.1",
        "numerics_version": "v0-dev",
        "compatibility_class": "clarification",
        "signed": False,
        "dev_only": True,
        "fixture_purpose": "MVP dry simulation only",
        "entries": [
            {
                "key": "ingress_compiler.max_session_duration_ms",
                "value": 30000,
                "unit": "ms",
                "allowed_range": {"kind": "min_max", "min": 5000, "max": 120000},
                "directionality": "lower_is_stricter",
                "change_class_if_increased": "safety_weakening",
                "change_class_if_decreased": "safety_tightening",
                "requires_human_approval": True,
                "dependencies": [],
                "numeric_risk_family": "safety_critical",
                "spec_family": "ingress_compiler",
                "owning_spec_ref": "INGRESS_COMPILER_NUMERICS.md §5",
            }
        ],
    }


def _valid_production_artifact_json() -> dict[str, object]:
    data = _valid_dev_artifact_json()
    data["numerics_version"] = "v0.1.0"
    data["dev_only"] = False
    data["fixture_purpose"] = None
    data["signed"] = True
    return data


class TestMissingArtifact:
    def test_missing_file_raises_missing_artifact_error(self, tmp_path: Path) -> None:
        with pytest.raises(MissingArtifactError):
            load_artifact(tmp_path / "nope.json", mode=LoaderMode.DEVELOPMENT)


class TestLoadDevelopmentMode:
    def test_dev_artifact_accepted_in_development(self, tmp_path: Path) -> None:
        p = tmp_path / "ingress.json"
        p.write_text(json.dumps(_valid_dev_artifact_json()), encoding="utf-8")
        art = load_artifact(p, mode=LoaderMode.DEVELOPMENT)
        assert art.dev_only is True
        assert art.numerics_version == "v0-dev"
        assert len(art.entries) == 1

    def test_production_artifact_accepted_in_development(self, tmp_path: Path) -> None:
        p = tmp_path / "prod.json"
        p.write_text(json.dumps(_valid_production_artifact_json()), encoding="utf-8")
        art = load_artifact(p, mode=LoaderMode.DEVELOPMENT)
        assert art.dev_only is False


class TestLoadProductionMode:
    def test_dev_artifact_rejected_in_production(self, tmp_path: Path) -> None:
        p = tmp_path / "dev.json"
        p.write_text(json.dumps(_valid_dev_artifact_json()), encoding="utf-8")
        with pytest.raises(InvariantViolation) as exc_info:
            load_artifact(p, mode=LoaderMode.PRODUCTION)
        assert exc_info.value.violation_code == "NUMERICS_DEV_ONLY_REJECTED_IN_PRODUCTION"
        assert exc_info.value.evidence["spec_family"] == "ingress_compiler"

    def test_production_artifact_accepted_in_production(self, tmp_path: Path) -> None:
        p = tmp_path / "prod.json"
        p.write_text(json.dumps(_valid_production_artifact_json()), encoding="utf-8")
        art = load_artifact(p, mode=LoaderMode.PRODUCTION)
        assert art.dev_only is False


class TestMalformed:
    def test_malformed_json_raises_value_error(self, tmp_path: Path) -> None:
        p = tmp_path / "bad.json"
        p.write_text("not-json", encoding="utf-8")
        with pytest.raises(ValueError):
            load_artifact(p, mode=LoaderMode.DEVELOPMENT)

    def test_missing_required_field_raises_validation_error(self, tmp_path: Path) -> None:
        data = _valid_dev_artifact_json()
        # Remove a required entry field → schema-level no-default rejection.
        entries = data["entries"]
        assert isinstance(entries, list)
        del entries[0]["requires_human_approval"]
        p = tmp_path / "bad.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        with pytest.raises(Exception):  # noqa: B017 — Pydantic ValidationError
            load_artifact(p, mode=LoaderMode.DEVELOPMENT)


class TestLoaderModeEnum:
    def test_two_values(self) -> None:
        assert {m.value for m in LoaderMode} == {"development", "production"}
