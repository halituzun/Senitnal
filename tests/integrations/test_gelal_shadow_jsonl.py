"""V5 — Gel.Al shadow JSONL adapter tests."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from pydantic import ValidationError
from sentinel.integrations.gelal_jsonl import GelAlShadowJsonlAdapter

_FIXTURE_DIR = Path("tests/fixtures/gelal_shadow")


class TestGelAlShadowJsonlAdapter:
    def test_reads_valid_jsonl(self) -> None:
        adapter = GelAlShadowJsonlAdapter(
            path=_FIXTURE_DIR / "opportunity_seen_positive_edge.jsonl"
        )
        envelopes = adapter.read_all()
        assert len(envelopes) == 1
        assert envelopes[0].event_id == "gelal-evt-001"

    def test_preserves_order(self, tmp_path: Path) -> None:
        path = tmp_path / "ordered.jsonl"
        lines: list[str] = []
        for i in range(3):
            lines.append(
                '{"event_id":"e' + str(i) + '","event_type":"market_observation",'
                '"source_system":"gel_al_borsa","observed_at_ms":' + str(1000 + i) + ","
                '"exported_at_ms":' + str(1010 + i) + ","
                '"source_table":"t","source_row_id":"r","source_hash":"sha256:x",'
                '"environment":"paper","payload":{"confidence":0.5}}'
            )
        path.write_text("\n".join(lines), encoding="utf-8")
        envelopes = GelAlShadowJsonlAdapter(path=path).read_all()
        assert [e.event_id for e in envelopes] == ["e0", "e1", "e2"]

    def test_missing_file_rejected(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            GelAlShadowJsonlAdapter(path=tmp_path / "nope.jsonl").read_all()

    def test_malformed_line_rejected_with_line_number(self) -> None:
        with pytest.raises(ValueError, match=re.compile(r"line\s*\d+")):
            GelAlShadowJsonlAdapter(path=_FIXTURE_DIR / "malformed_invalid.jsonl").read_all()

    def test_invalid_envelope_rejected(self) -> None:
        with pytest.raises(ValidationError):
            GelAlShadowJsonlAdapter(
                path=_FIXTURE_DIR / "forbidden_command_fields_invalid.jsonl"
            ).read_all()

    def test_no_write_method(self) -> None:
        adapter = GelAlShadowJsonlAdapter(
            path=_FIXTURE_DIR / "opportunity_seen_positive_edge.jsonl"
        )
        for attr in ("write", "write_line", "append", "send", "publish", "push"):
            assert not hasattr(adapter, attr), f"adapter should not expose {attr!r}"

    def test_no_network_imports(self) -> None:
        from sentinel.integrations import gelal_jsonl

        src = Path(gelal_jsonl.__file__).read_text(encoding="utf-8")
        for forbidden in ("requests", "httpx", "aiohttp", "urllib3", "ccxt", "websocket"):
            assert f"import {forbidden}" not in src
            assert f"from {forbidden}" not in src
