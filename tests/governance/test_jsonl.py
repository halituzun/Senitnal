"""V9 — Governance JSONL adapter tests."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from pydantic import ValidationError
from sentinel.governance.jsonl import LiveGovernanceRequestJsonlAdapter

_FIX = Path("tests/fixtures/governance")


class TestGovernanceJsonlAdapter:
    def test_reads_valid_file(self) -> None:
        adapter = LiveGovernanceRequestJsonlAdapter(path=_FIX / "benign_no_action.jsonl")
        rs = adapter.read_all()
        assert len(rs) == 1
        assert rs[0].request_id == "gov-req-001"

    def test_missing_file_rejected(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            LiveGovernanceRequestJsonlAdapter(path=tmp_path / "nope.jsonl").read_all()

    def test_invalid_schema_rejected(self) -> None:
        with pytest.raises(ValidationError):
            LiveGovernanceRequestJsonlAdapter(path=_FIX / "invalid_order_fields.jsonl").read_all()

    def test_malformed_rejected_with_line_number(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.jsonl"
        bad.write_text("{not valid json\n", encoding="utf-8")
        with pytest.raises(ValueError, match=re.compile(r"line\s*\d+")):
            LiveGovernanceRequestJsonlAdapter(path=bad).read_all()

    def test_no_write_method(self) -> None:
        adapter = LiveGovernanceRequestJsonlAdapter(path=_FIX / "benign_no_action.jsonl")
        for attr in ("write", "write_line", "append", "publish", "push"):
            assert not hasattr(adapter, attr)
