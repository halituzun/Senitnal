"""V3 — Financial memory pipeline.

Wires the V2 read-only market observation surface to the V3
financial memory + recall surface, end-to-end:

    MarketObservationEnvelope
      -> emit_market_observation_ingested (V2; router, ring-only)
      -> derive LatencyPatternPayload (per envelope; SOURCE_TRUST)
      -> submit_financial_memory_candidate (MWG; accepted candidate;
                                            M1 audit emitted)
      -> store.add (only when MWG accepts)
      -> [optional] FinancialRecallRequest -> top-1 -> RecallEvent
                                              -> M1 audit emitted

This pipeline is synthetic / dev only. It does NOT touch the base
dry_sim canonical run. It does NOT produce any approved-action
intent, NEVER calls the deontic gate, NEVER produces a verified
MemoryRecord, NEVER emits an execution verb.
"""

from __future__ import annotations

from collections.abc import Iterable  # noqa: TC003 (runtime annotation)
from dataclasses import dataclass

from sentinel.adapters.market_audit import emit_market_observation_ingested
from sentinel.adapters.market_observation import MarketObservationEnvelope  # noqa: TC001 (runtime)
from sentinel.gates.memory_write import EvidenceAxis, MemoryWriteResolution
from sentinel.memory.financial import LatencyPatternPayload
from sentinel.memory.store import InMemoryExplicitMemoryStore  # noqa: TC001 (runtime)
from sentinel.memory.write_path import submit_financial_memory_candidate
from sentinel.observer.ledger import JsonlObserverLedger  # noqa: TC001 (runtime)
from sentinel.observer.ring_buffer import ObserverRingBuffer  # noqa: TC001 (runtime)
from sentinel.recall.audit import (
    emit_recall_request,
    emit_recall_result_empty,
)
from sentinel.recall.financial import (
    FinancialRecallRequest,
    FinancialRecallScope,
    build_financial_recall_event,
    score_record_for_request,
    select_financial_recall_top_one,
)
from sentinel.recall.protocol import RecallTriggerSource
from sentinel.types.events import RecallEvent  # noqa: TC001 (runtime)
from sentinel.types.memory import SubjectClass
from sentinel.types.neural_seed import ProvenanceRef


@dataclass(frozen=True, slots=True)
class FinancialMemoryPipelineResult:
    """Outcome of one V3 pipeline run."""

    observations_seen: int
    candidate_records_written: int
    records_rejected: int
    recall_requests: int
    recall_events_built: int
    audit_event_ids: tuple[str, ...]
    output_summary: str
    hash_chain_valid: bool


def _derive_latency_payload(
    envelope: MarketObservationEnvelope,
) -> LatencyPatternPayload:
    """Derive a per-envelope LatencyPatternPayload.

    Single-sample by construction; p95 == max == avg == latency_ms;
    stale_ratio derived from orderbook_age_ms / (latency_ms +
    orderbook_age_ms) with safe fallback to 0.0.
    """
    latency = float(envelope.latency_ms)
    total = float(envelope.orderbook_age_ms) + latency
    stale_ratio = (float(envelope.orderbook_age_ms) / total) if total > 0 else 0.0
    # venue_hash is a deterministic opaque derivative of the venue
    # string; raw venue label is NOT propagated into the payload.
    return LatencyPatternPayload(
        record_key=f"latency-{envelope.event_id}",
        source_adapter_id=envelope.source_adapter_id,
        venue_hash=f"sha256:venue-{envelope.venue}",
        avg_latency_ms=latency,
        p95_latency_ms=latency,
        max_latency_ms=latency,
        stale_ratio=stale_ratio,
        sample_count=1,
        confidence=envelope.confidence,
        source_event_ids=(envelope.event_id,),
    )


def run_financial_memory_pipeline(
    *,
    observations: Iterable[MarketObservationEnvelope],
    store: InMemoryExplicitMemoryStore,
    ledger: JsonlObserverLedger,
    ring_buffer: ObserverRingBuffer,
    provenance: ProvenanceRef,
    emit_recall_after_writes: bool = True,
    recall_request_id: str = "fin-recall-pipeline-1",
) -> FinancialMemoryPipelineResult:
    """Run the V3 financial memory pipeline against an envelope stream.

    For each envelope:
        1. emit_market_observation_ingested (V2; ring-only via router)
        2. derive LatencyPatternPayload (SOURCE_TRUST)
        3. submit_financial_memory_candidate (MWG accepts;
           record stored as CANDIDATE in `store`)

    After the loop, if `emit_recall_after_writes` is True and the
    store now contains at least one record:
        4. construct FinancialRecallRequest scoped to SOURCE_TRUST +
           PROCEDURAL
        5. select top-1 via select_financial_recall_top_one
        6. on success: emit RECALL_REQUEST_EMITTED + build a
           RecallEvent (purely as a demonstration of the recall
           path; the RecallEvent is NOT routed through the ingress
           compiler in V3 — that integration is left to the caller
           who needs neural-seed compilation).
        7. on empty pool: emit RECALL_RESULT_EMPTY (audit-only).
    """
    audit_ids: list[str] = []
    observations_seen = 0
    candidate_records_written = 0
    records_rejected = 0
    recall_requests = 0
    recall_events_built = 0

    for envelope in observations:
        observations_seen += 1
        ingested = emit_market_observation_ingested(
            envelope=envelope,
            ledger=ledger,
            ring_buffer=ring_buffer,
            provenance=ProvenanceRef(source_event_id=envelope.event_id),
        )
        audit_ids.append(ingested.event.event_id)

        payload = _derive_latency_payload(envelope)
        write_result = submit_financial_memory_candidate(
            store=store,
            ledger=ledger,
            payload=payload,
            provenance=ProvenanceRef(source_event_id=envelope.event_id),
            created_at_ms=envelope.observed_at_ms,
            source_event_ids=(envelope.event_id,),
            evidence_axis=EvidenceAxis.DIRECT_OBSERVATION,
        )
        audit_ids.append(f"mwg-{write_result.record.record_id}")
        if write_result.outcome.resolution in (
            MemoryWriteResolution.ACCEPTED_CANDIDATE,
            MemoryWriteResolution.DOWNGRADED_TO_CANDIDATE,
        ):
            candidate_records_written += 1
        else:
            records_rejected += 1

    if emit_recall_after_writes and observations_seen > 0:
        recall_requests += 1
        request = FinancialRecallRequest(
            request_id=recall_request_id,
            source=RecallTriggerSource.CORE,
            scope=FinancialRecallScope(
                subject_classes=(SubjectClass.SOURCE_TRUST, SubjectClass.PROCEDURAL),
                max_records_considered=64,
                include_candidates=True,
            ),
            created_at_ms=0,
        )
        selected = select_financial_recall_top_one(store=store, request=request)
        if selected is not None:
            score = score_record_for_request(selected, request)
            req_audit = emit_recall_request(
                ledger,
                request_id=recall_request_id,
                selected=selected,
                score=score,
                now_ms=0,
            )
            audit_ids.append(req_audit.event_id)
            recall_event: RecallEvent = build_financial_recall_event(
                record=selected,
                request_id=recall_request_id,
                now_ms=max(1, selected.created_at_ms + 1),
            )
            audit_ids.append(recall_event.event_id)
            recall_events_built += 1
        else:
            empty_audit = emit_recall_result_empty(
                ledger,
                request_id=recall_request_id,
                candidates_considered=len(store),
                now_ms=0,
            )
            audit_ids.append(empty_audit.event_id)

    output_summary = (
        f"V3 financial memory pipeline: observations={observations_seen} "
        f"candidates_written={candidate_records_written} "
        f"rejected={records_rejected} recalls={recall_requests} "
        f"recall_events={recall_events_built}; observe-only, no action"
    )

    return FinancialMemoryPipelineResult(
        observations_seen=observations_seen,
        candidate_records_written=candidate_records_written,
        records_rejected=records_rejected,
        recall_requests=recall_requests,
        recall_events_built=recall_events_built,
        audit_event_ids=tuple(audit_ids),
        output_summary=output_summary,
        hash_chain_valid=ledger.verify(),
    )
