"""V8 — Canary JSONL adapter tests."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from pydantic import ValidationError
from sentinel.canary.jsonl import CanaryCandidateJsonlAdapter

_FIX = Path("tests/fixtures/canary")


class TestCanaryJsonlAdapter:
    def test_reads_valid_file(self) -> None:
        adapter = CanaryCandidateJsonlAdapter(path=_FIX / "benign_candidate_no_veto.jsonl")
        cs = adapter.read_all()
        assert len(cs) == 1
        assert cs[0].candidate_id == "cand-001"

    def test_missing_file_rejected(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            CanaryCandidateJsonlAdapter(path=tmp_path / "nope.jsonl").read_all()

    def test_invalid_schema_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CanaryCandidateJsonlAdapter(
                path=_FIX / "forbidden_order_fields_invalid.jsonl"
            ).read_all()

    def test_malformed_rejected_with_line_number(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.jsonl"
        bad.write_text("{not valid json\n", encoding="utf-8")
        with pytest.raises(ValueError, match=re.compile(r"line\s*\d+")):
            CanaryCandidateJsonlAdapter(path=bad).read_all()

    def test_no_write_method(self) -> None:
        adapter = CanaryCandidateJsonlAdapter(path=_FIX / "benign_candidate_no_veto.jsonl")
        for attr in ("write", "write_line", "append", "publish", "push"):
            assert not hasattr(adapter, attr)
