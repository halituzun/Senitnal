"""V3 — Financial recall query, ranking, and event builder.

Builds on the v0.1 recall protocol:
    sentinel.recall.protocol       (trigger evaluation)
    sentinel.recall.ranking        (multiplicative score + top-1
                                    tie-break by record_id)
    sentinel.recall.candidate      (subject-class whitelist)
    sentinel.recall.audit          (M1 audit emitters)

V3 adds a financial-domain scope object, a request envelope tied to
CORE-only triggering, a deterministic per-record scorer, and a
RecallEvent builder. None of these widens any v0.1 surface; they
plug into existing primitives.

Constitutional discipline (V3):
    - top-1 only (multi-record API forbidden)
    - candidate recall restricted to source_trust + procedural
      (the v0.1 whitelist, asserted via
       validate_candidate_recall_subject)
    - rejected / quarantined / expired records cannot be recalled
    - human / LLM / replay / summarizer trigger sources rejected
    - no domain-label matching, no semantic search, no LLM scoring
    - no raw symbol / venue in the resulting RecallEvent
"""

from __future__ import annotations

from dataclasses import dataclass

from sentinel.memory.store import InMemoryExplicitMemoryStore  # noqa: TC001 (runtime arg)
from sentinel.recall.candidate import validate_candidate_recall_subject
from sentinel.recall.protocol import RecallTriggerSource
from sentinel.recall.ranking import RankingInputs, compute_recall_score, select_top_one
from sentinel.types.events import IngressEventType, RecallEvent, RecallRecordStatus
from sentinel.types.memory import MemoryRecord, MemoryRecordStatus, SubjectClass


@dataclass(frozen=True, slots=True)
class FinancialRecallScope:
    """Scope description for a financial recall request.

    `subject_classes` narrows the candidate pool. `include_candidates`
    is an opt-in flag for the caller, but it does NOT relax the
    v0.1 candidate-recall whitelist (source_trust + procedural).
    """

    subject_classes: tuple[SubjectClass, ...]
    max_records_considered: int
    include_candidates: bool = True

    def __post_init__(self) -> None:
        if self.max_records_considered <= 0:
            raise ValueError("max_records_considered must be > 0")
        if not self.subject_classes:
            raise ValueError("subject_classes must be non-empty")


@dataclass(frozen=True, slots=True)
class FinancialRecallRequest:
    """A core-originated request for a financial memory recall.

    `source` MUST be RecallTriggerSource.CORE. Any other source
    (HUMAN, LLM, REPLAY, SUMMARIZER) is rejected at construction.
    """

    request_id: str
    source: RecallTriggerSource
    scope: FinancialRecallScope
    created_at_ms: int

    def __post_init__(self) -> None:
        if not self.request_id:
            raise ValueError("request_id must be non-empty")
        if self.source is not RecallTriggerSource.CORE:
            raise ValueError(
                "FinancialRecallRequest.source must be RecallTriggerSource.CORE; "
                f"got {self.source!r}"
            )
        if self.created_at_ms < 0:
            raise ValueError("created_at_ms must be >= 0")


def _status_weight(status: MemoryRecordStatus) -> float:
    """Deterministic v0.1-compatible status weight in [0, 1]."""
    if status is MemoryRecordStatus.VERIFIED:
        return 1.0
    if status is MemoryRecordStatus.ACTIVE:
        return 0.85
    if status is MemoryRecordStatus.CANDIDATE:
        return 0.5
    # REJECTED / EXPIRED / QUARANTINED / SUPERSEDED — should not
    # appear in scored pool; coerced to zero defensively.
    return 0.0


def _provenance_strength(record: MemoryRecord) -> float:
    """External corroboration count, bucketed into [0, 1]."""
    n = len(record.external_corroboration_refs)
    if n >= 3:
        return 1.0
    if n == 2:
        return 0.75
    if n == 1:
        return 0.5
    return 0.25  # internal only / no refs


def _payload_confidence(record: MemoryRecord) -> float:
    """Read the optional confidence field from the dumped payload."""
    value = record.payload.get("confidence")
    if isinstance(value, (int, float)) and 0.0 <= float(value) <= 1.0:
        return float(value)
    return 0.5


def score_record_for_request(
    record: MemoryRecord,
    request: FinancialRecallRequest,
) -> float:
    """Deterministic score in [0, 1] for one (record, request) pair.

    Inputs come from record metadata + scope match. No LLM input,
    no semantic similarity, no raw-label matching.
    """
    scope_match = 1.0 if record.subject_class in request.scope.subject_classes else 0.0
    inputs = RankingInputs(
        status_weight=_status_weight(record.status),
        provenance_strength=_provenance_strength(record),
        freshness_dampening=_payload_confidence(record),
        contradiction_penalty=0.0,
        habituation_penalty=0.0,
        scope_match_score=scope_match,
    )
    return compute_recall_score(inputs)


def select_financial_recall_top_one(
    *,
    store: InMemoryExplicitMemoryStore,
    request: FinancialRecallRequest,
) -> MemoryRecord | None:
    """Return the single top-1 record (or None) for a financial recall request.

    Pulls candidates from `store.query_recallable`, restricted by
    the scope's subject_classes, scores each via
    `score_record_for_request`, applies the v0.1 top-1 selector
    (`select_top_one`), and returns the winner — or None if the
    candidate pool is empty after filtering / no record has a
    positive score.
    """
    pool = store.query_recallable(
        subject_classes=request.scope.subject_classes,
        include_candidates=request.scope.include_candidates,
        include_superseded=False,
    )
    if not pool:
        return None
    truncated = pool[: request.scope.max_records_considered]
    scored: list[tuple[MemoryRecord, float]] = []
    for record in truncated:
        score = score_record_for_request(record, request)
        if score > 0.0:
            scored.append((record, score))
    if not scored:
        return None
    return select_top_one(scored)


_CANDIDATE_RECALL_CONFIDENCE_CAP: float = 0.5


def build_financial_recall_event(
    *,
    record: MemoryRecord,
    request_id: str,
    now_ms: int,
    ttl_ms: int = 1000,
) -> RecallEvent:
    """Build a v0.1 RecallEvent for `record`.

    Rules:
        - rejected / expired / quarantined records cannot produce
          a RecallEvent (ValueError raised).
        - candidate records' subject_class must be in the v0.1
          recall whitelist (source_trust / procedural); enforced
          via validate_candidate_recall_subject.
        - candidate-record confidence is capped at
          _CANDIDATE_RECALL_CONFIDENCE_CAP (= 0.5).
        - verified / active records inherit the payload confidence,
          falling back to 0.7 when absent.
        - `age_ms = max(0, now_ms - record.created_at_ms)`.
        - `contradiction_risk` defaults to 0.1 for verified/active,
          0.3 for candidate.
        - No raw symbol / venue / source_system carried in the
          RecallEvent (the v0.1 RecallEvent schema already excludes
          such fields by extra='forbid').
    """
    if record.status in (
        MemoryRecordStatus.REJECTED,
        MemoryRecordStatus.EXPIRED,
        MemoryRecordStatus.QUARANTINED,
    ):
        raise ValueError(f"cannot build RecallEvent for record at status {record.status.value!r}")

    if ttl_ms <= 0:
        raise ValueError("ttl_ms must be > 0")
    if now_ms < 0:
        raise ValueError("now_ms must be >= 0")

    if record.status is MemoryRecordStatus.CANDIDATE:
        validate_candidate_recall_subject(record.subject_class)
        confidence = min(_payload_confidence(record), _CANDIDATE_RECALL_CONFIDENCE_CAP)
        contradiction_risk = 0.3
    elif record.status in (MemoryRecordStatus.VERIFIED, MemoryRecordStatus.ACTIVE):
        confidence = _payload_confidence(record) if "confidence" in record.payload else 0.7
        contradiction_risk = 0.1
    else:
        # SUPERSEDED — not normally recalled; treat conservatively.
        confidence = min(_payload_confidence(record), _CANDIDATE_RECALL_CONFIDENCE_CAP)
        contradiction_risk = 0.3

    age_ms = max(0, now_ms - record.created_at_ms)

    return RecallEvent(
        event_id=f"recall-event-{record.record_id}-{request_id}",
        event_type=IngressEventType.RECALL,
        occurred_at_ms=now_ms,
        ttl_ms=ttl_ms,
        confidence=confidence,
        source_record_id=record.record_id,
        record_status=RecallRecordStatus(record.status.value),
        subject_class=record.subject_class,
        age_ms=age_ms,
        contradiction_risk=contradiction_risk,
    )
