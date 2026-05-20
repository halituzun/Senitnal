"""Tests for the M1 audit-aware reader."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003 (fixture annotation)

import pytest
from sentinel.constitution.violations import InvariantViolation
from sentinel.observer.audit_reader import (
    LLM_ALLOWED_READ_EVENT_TYPES,
    AuditReader,
    ReaderType,
)
from sentinel.observer.hash_chain import placeholder_event_hash
from sentinel.observer.ledger import JsonlObserverLedger
from sentinel.types.neural_seed import ProvenanceRef
from sentinel.types.observer import EventFamily, ObserverEvent


def _event(
    counter: int,
    *,
    event_type: str = "LEDGER_STATE_CHANGED",
    event_family: EventFamily = EventFamily.LEDGER_META,
) -> ObserverEvent:
    return ObserverEvent(
        event_id=f"evt-{counter}",
        event_family=event_family,
        event_type=event_type,
        occurred_at_ms=counter,
        payload={"reason": "unit_test", "counter": counter},
        provenance=ProvenanceRef(source_event_id=f"src-{counter}"),
        previous_event_hash=None,
        event_hash=placeholder_event_hash(),
    )


@pytest.fixture
def ledger_path(tmp_path: Path) -> Path:
    return tmp_path / "ledger.jsonl"


@pytest.fixture
def ledger(ledger_path: Path) -> JsonlObserverLedger:
    return JsonlObserverLedger(ledger_path)


class TestReaderTypeEnum:
    def test_six_canonical_reader_types(self) -> None:
        expected = {
            "human",
            "llm",
            "replay",
            "summarizer",
            "external_audit",
            "internal",
        }
        assert {r.value for r in ReaderType} == expected


class TestReadAllEmitsAudit:
    def test_human_read_emits_audit_event(self, ledger: JsonlObserverLedger) -> None:
        ledger.append(_event(1))
        reader = AuditReader(ledger)
        returned = reader.read_all(reader_type=ReaderType.HUMAN, now_ms=42)
        # returned includes the event but NOT the audit event (audit
        # was written after the snapshot).
        assert tuple(e.event_id for e in returned) == ("evt-1",)
        # Ledger now contains the original + one audit event.
        on_disk = ledger.read_all()
        assert on_disk[-1].event_type == "M1_READ_AUDIT_RECORDED"
        assert on_disk[-1].payload["reader_type"] == "human"
        assert on_disk[-1].payload["returned_count"] == 1

    def test_audit_event_chains_to_prior_event(self, ledger: JsonlObserverLedger) -> None:
        first = ledger.append(_event(1))
        reader = AuditReader(ledger)
        reader.read_all(reader_type=ReaderType.HUMAN, now_ms=2)
        on_disk = ledger.read_all()
        assert on_disk[-1].previous_event_hash == first.event_hash
        assert ledger.verify() is True


class TestLlmScopeFilter:
    def test_llm_read_all_filters_to_whitelist(self, ledger: JsonlObserverLedger) -> None:
        # One whitelisted (LEDGER_STATE_CHANGED) and one not
        # (MEMORY_RECORD_STATUS_CHANGED).
        ledger.append(_event(1, event_type="LEDGER_STATE_CHANGED"))
        ledger.append(
            _event(
                2,
                event_type="MEMORY_RECORD_STATUS_CHANGED",
                event_family=EventFamily.MEMORY,
            )
        )
        reader = AuditReader(ledger)
        returned = reader.read_all(reader_type=ReaderType.LLM, now_ms=3)
        event_types = {e.event_type for e in returned}
        assert "LEDGER_STATE_CHANGED" in event_types
        assert "MEMORY_RECORD_STATUS_CHANGED" not in event_types

    def test_llm_explicit_forbidden_scope_raises(self, ledger: JsonlObserverLedger) -> None:
        ledger.append(_event(1))
        reader = AuditReader(ledger)
        with pytest.raises(InvariantViolation) as exc_info:
            reader.read_by_event_types(
                reader_type=ReaderType.LLM,
                event_types=("MEMORY_RECORD_STATUS_CHANGED",),
                now_ms=2,
            )
        assert exc_info.value.violation_code == "OBSERVER_LLM_READ_SCOPE_FORBIDDEN"
        assert exc_info.value.evidence["forbidden_event_types"] == ["MEMORY_RECORD_STATUS_CHANGED"]
        # No audit was emitted on the failed call.
        on_disk = ledger.read_all()
        assert all(e.event_type != "M1_READ_AUDIT_RECORDED" for e in on_disk)

    def test_llm_allowed_scope_succeeds(self, ledger: JsonlObserverLedger) -> None:
        ledger.append(_event(1, event_type="LEDGER_STATE_CHANGED"))
        reader = AuditReader(ledger)
        returned = reader.read_by_event_types(
            reader_type=ReaderType.LLM,
            event_types=("LEDGER_STATE_CHANGED",),
            now_ms=2,
        )
        assert tuple(e.event_id for e in returned) == ("evt-1",)
        on_disk = ledger.read_all()
        assert on_disk[-1].event_type == "M1_READ_AUDIT_RECORDED"
        assert on_disk[-1].payload["reader_type"] == "llm"
        assert on_disk[-1].payload["requested_event_types"] == ["LEDGER_STATE_CHANGED"]


class TestNonLlmCanReadAnyScope:
    def test_human_can_read_memory_event_types(self, ledger: JsonlObserverLedger) -> None:
        ledger.append(
            _event(
                1,
                event_type="MEMORY_RECORD_STATUS_CHANGED",
                event_family=EventFamily.MEMORY,
            )
        )
        reader = AuditReader(ledger)
        returned = reader.read_by_event_types(
            reader_type=ReaderType.HUMAN,
            event_types=("MEMORY_RECORD_STATUS_CHANGED",),
            now_ms=2,
        )
        assert tuple(e.event_id for e in returned) == ("evt-1",)


class TestWhitelistShape:
    def test_whitelist_is_frozen(self) -> None:
        assert isinstance(LLM_ALLOWED_READ_EVENT_TYPES, frozenset)

    def test_whitelist_does_not_include_memory_or_deontic(self) -> None:
        # Constitutional: LLM cannot peek at memory writes or deontic
        # detail without a security review expanding the whitelist.
        assert "MEMORY_RECORD_STATUS_CHANGED" not in LLM_ALLOWED_READ_EVENT_TYPES
        assert "MEMORY_WRITE_PROPOSED" not in LLM_ALLOWED_READ_EVENT_TYPES
        assert "DEONTIC_BLOCKED" not in LLM_ALLOWED_READ_EVENT_TYPES
        assert "DEONTIC_BYPASS_ATTEMPT" not in LLM_ALLOWED_READ_EVENT_TYPES
        assert "KILL_SWITCH_ACTIVATED" not in LLM_ALLOWED_READ_EVENT_TYPES
