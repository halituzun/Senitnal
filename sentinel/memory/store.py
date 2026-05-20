"""V3 — Local / in-memory explicit M2 store (dev + test only).

NOT a production database. This in-memory store exists to give the
V3 build + tests a place to drop accepted candidate MemoryRecord
instances and query them for recall ranking. A persistent M2 store
(durable, multi-process, replicated) is explicitly out of V3 scope.

The store does NOT bypass the Memory Write Gate. Callers MUST run a
record through `submit_memory_write` (or the V3 wrapper
`submit_financial_memory_candidate`) first; only after the gate
ACCEPTs (or DOWNGRADES) the record may it land in this store.
`store.add` exists for the wrapper to call; it is not itself a gate.
"""

from __future__ import annotations

from sentinel.recall.candidate import ALLOWED_CANDIDATE_RECALL_SUBJECT_CLASSES
from sentinel.types.memory import MemoryRecord, MemoryRecordStatus, SubjectClass

_RECALLABLE_STATUSES: frozenset[MemoryRecordStatus] = frozenset(
    {
        MemoryRecordStatus.VERIFIED,
        MemoryRecordStatus.ACTIVE,
        MemoryRecordStatus.CANDIDATE,
    }
)

_NEVER_RECALLABLE_STATUSES: frozenset[MemoryRecordStatus] = frozenset(
    {
        MemoryRecordStatus.REJECTED,
        MemoryRecordStatus.EXPIRED,
        MemoryRecordStatus.QUARANTINED,
    }
)


class InMemoryExplicitMemoryStore:
    """In-memory M2 record store.

    Records are keyed by `record_id`. Duplicate ids are rejected at
    `add`-time. The store provides simple subject-class queries and
    a `query_recallable` filter that respects the v0.1 candidate-
    recall whitelist (source_trust + procedural only) and never
    surfaces rejected / expired / quarantined records.
    """

    def __init__(self) -> None:
        self._records: dict[str, MemoryRecord] = {}

    def add(self, record: MemoryRecord) -> None:
        if record.record_id in self._records:
            raise ValueError(f"duplicate record_id: {record.record_id!r}")
        self._records[record.record_id] = record

    def get(self, record_id: str) -> MemoryRecord | None:
        return self._records.get(record_id)

    def list_all(self) -> tuple[MemoryRecord, ...]:
        return tuple(self._records.values())

    def query_by_subject_class(self, subject_class: SubjectClass) -> tuple[MemoryRecord, ...]:
        return tuple(r for r in self._records.values() if r.subject_class is subject_class)

    def query_recallable(
        self,
        *,
        subject_classes: tuple[SubjectClass, ...] | None = None,
        include_candidates: bool = True,
        include_superseded: bool = False,
    ) -> tuple[MemoryRecord, ...]:
        """Return records that may be surfaced to recall ranking.

        Exclusions (always):
            rejected, expired, quarantined.
        Exclusions (default):
            superseded (opt in via include_superseded=True).
        Candidate records are included only when both
            (a) include_candidates is True, AND
            (b) subject_class is in {source_trust, procedural}
                (per RECALL_PROTOCOL.md §14 +
                 sentinel/recall/candidate.py whitelist).
        The `subject_classes` filter, if supplied, further narrows
        results to the listed subject_class values.
        """
        out: list[MemoryRecord] = []
        for record in self._records.values():
            if record.status in _NEVER_RECALLABLE_STATUSES:
                continue
            if record.status is MemoryRecordStatus.SUPERSEDED and not include_superseded:
                continue
            if record.status is MemoryRecordStatus.CANDIDATE:
                if not include_candidates:
                    continue
                if record.subject_class not in ALLOWED_CANDIDATE_RECALL_SUBJECT_CLASSES:
                    continue
            if subject_classes is not None and record.subject_class not in subject_classes:
                continue
            out.append(record)
        return tuple(out)

    def __len__(self) -> int:
        return len(self._records)
