# 0008 — V7 — Paper Co-Pilot — Build Plan

> Status: BUILD PLAN. Implementation tracks this document section-by-section.

## 1. Purpose

V7 introduces a non-executing **paper co-pilot** layer.  Given a
read-only / shadow market observation or Gel.Al shadow envelope,
Sentinel produces a `PaperDecision` carrying a closed v0.1
`SystemOutput` value, using the active financial deontic policy (V6),
financial memory (V3), and replay evidence (V4) as evidence — all
shadow / read-only.

The output is **advisory**.  `BLOCK` is a paper classification, not a
live veto.  `MONITOR` is a paper classification, not trade approval.

## 2. Non-goals

- No live trading or execution.
- No live veto.
- No exchange API integration.
- No Gel.Al DB / Redis / config write.
- No Telegram command.
- No LLM.
- No production memory verification.
- No automatic policy mutation.
- No canary / live veto layer.
- No paper-decision-promoted-to-live action.

## 3. Safety constraints

- All v0.1 / V2 / V3 / V4 / V5 / V6 constitutional invariants preserved.
- Output set still `{WAIT, BLOCK, MONITOR, NEED_RECALL, NO_ACTION}`.
- No `BUY` / `SELL` / `EXECUTE_REAL` / `ORDER_SUBMIT` outputs.
- No `ApprovedActionIntent` produced.
- No exchange / network / LLM imports under `sentinel/`.
- `PaperDecision` pins `shadow_only=True`, `creates_action=False`,
  `writes_external=False`, `approved_for_live=False` via `Literal`.
- `PaperOpportunity` strips raw symbol / venue / strategy / order /
  account / API key fields at the type boundary.
- `OBSERVATION_INGESTED` / `WORKSPACE_PULSE` remain ring-only.
- Memory Write Gate, Deontic Gate, Recall Protocol not bypassed.

## 4. Paper co-pilot is not execution

| Output | Live meaning | Paper meaning |
|---|---|---|
| WAIT | n/a (no live) | "advisor sees no condition to act on" |
| BLOCK | n/a (no live) | "advisor recommends not acting" |
| MONITOR | n/a (no live) | "advisor recommends continued watching" |
| NEED_RECALL | n/a (no live) | "advisor wants a memory lookup" |
| NO_ACTION | n/a (no live) | "advisor has no opinion" |

`PaperDecision.approved_for_live` is always `False`.  No code path
flips it.

## 5. Paper opportunity model

`PaperOpportunity` is a frozen Pydantic model carrying only abstract
bounded scalars (`risk_score`, `confidence`, `staleness_ms`,
`magnitude_score`, `liquidity_score`, …) plus hashed scope refs.

Raw symbol / venue / strategy / order side / API key fields are
rejected at construction via `extra='forbid'` and an explicit
denylist for any forbidden field name that might slip through a
typed adapter.

## 6. Paper decision model

`PaperDecision` carries:

- `output: SystemOutput`
- `reasons: tuple[PaperDecisionReason, ...]` (closed enum)
- `shadow_only: Literal[True]`
- `creates_action: Literal[False]`
- `writes_external: Literal[False]`
- `approved_for_live: Literal[False]`

If `output == NEED_RECALL`, reasons must include `needs_recall`.
If `output == BLOCK`, reasons must include at least one blocking
reason (`high_risk`, `bad_order_observed`, `kill_switch_observed`,
`policy_block`, `stale_data`, `memory_conflict`).

## 7. Gel.Al shadow → paper opportunity mapping

`build_paper_opportunity_from_gelal_shadow(envelope)` converts a
V5 `GelAlShadowEnvelope` into a `PaperOpportunity`.  Raw symbol /
venue / strategy hashed into `scope_hash` and `provenance_hash`.
Observed `bad_order` / `kill_switch_active` flags drive `kind` and
`risk_score`, never an order side.

## 8. Market observation → paper opportunity mapping

`build_paper_opportunity_from_market_observation(envelope)` converts
a V2 `MarketObservationEnvelope` into a `PaperOpportunity`.  Same
discipline.

## 9. Financial memory usage

V3 in-memory store may be consulted **read-only**.  V7 does not
write to the store and does not promote candidate records to
verified.

## 10. Replay / counterfactual usage

V4 replay evidence (`ReplaySurvivalEvidence`, `OutcomeAlignmentEvidence`)
may be consulted as advisory signals.  V7 does not start new replay
sessions.

## 11. Financial deontic policy usage

If an active V6 policy is provided, the co-pilot constructs a
`FinancialPolicyInput` and calls `evaluate_financial_policy`.  Policy
BLOCK overrides any non-block paper output.

## 12. Paper scoring model

Deterministic scoring with conservative defaults:

```
risk_score ≥ 0.85           -> BLOCK (high_risk)
kind = bad_order_observation -> BLOCK (bad_order_observed)
kind = kill_switch_observation -> BLOCK (kill_switch_observed)
staleness_ms > 5_000         -> BLOCK (stale_data)  if extreme
                              -> MONITOR otherwise
active policy BLOCK          -> BLOCK (policy_block)
memory_echo_score ≥ 0.7     -> NEED_RECALL (needs_recall)
confidence < 0.2             -> WAIT (insufficient_confidence) or NO_ACTION
replay_evidence_score < 0.3 -> MONITOR (replay_uncertain) or WAIT
otherwise                    -> MONITOR (monitor_only) or WAIT
```

## 13. Paper output mapping

The scoring rules above produce a `SystemOutput` from the closed
v0.1 set.  No execution verb is permitted.

## 14. Paper-vs-Gel.Al comparison

`compare_gelal_shadow_to_paper_decision` produces a
`GelAlPaperComparison` carrying:

- `agreement_band ∈ {same_direction, sentinel_more_conservative, sentinel_less_conservative, incomparable}`
- `safety_note` passing `assert_no_forbidden_literal`

No write back to Gel.Al.  Raw Gel.Al decision string stays in the
observer-side comparison record.

## 15. Paper outcome tracking

`PaperOutcome` records what was observed *after* a paper decision.
`compare_paper_decision_to_outcome` produces a
`PaperDecisionOutcomeComparison` carrying:

- `was_conservative: bool`
- `would_have_helped: bool`
- `would_have_hurt: bool`
- `alignment_score: float [0,1]`
- `evidence_usable_for_replay: bool` (True iff
  `PaperOutcome.external == True`)

Comparison is evidence-candidate only; cannot write M2 directly,
cannot mutate active policy.

## 16. Observer audit events

V7 reuses the existing catalog row `LEDGER_STATE_CHANGED` for paper
co-pilot evaluation audit (permanent).  No new catalog row added.
The audit payload carries:

- `opportunity_id`, `decision_id`, `output`, `reasons`
- `shadow_only=True`, `creates_action=False`, `writes_external=False`,
  `approved_for_live=False`
- `policy_record_ref`, `memory_record_refs`, `replay_evidence_refs`
- no raw symbol / venue / strategy / order / API key
- no forbidden output literal

## 17. Local JSONL runner

`run_paper_copilot_file(path, source_kind, ledger, ring_buffer,
provenance, context)` supports three source kinds:

- `market_jsonl`: V2 market envelopes via `LocalJsonlMarketAdapter`
- `gelal_shadow_jsonl`: V5 Gel.Al envelopes via `GelAlShadowJsonlAdapter`
- `paper_opportunity_jsonl`: direct `PaperOpportunity` records

## 18. CLI plan

`python -m sentinel.runtime.paper_copilot --source-kind <kind>
--input <path> --ledger <path>`.  Exit codes:

- 0 — success
- 1 — load / schema error
- 2 — hash chain invalid
- 3 — any result `creates_action` / `writes_external` /
  `approved_for_live` flagged True (defensive)

## 19. Tests and invariants

53 invariants from goal spec §11 covered across 7 test files (see
§21 done definition).

## 20. Forbidden surfaces

| # | Forbidden | Enforcement |
|---|-----------|-------------|
| 1 | execution verb in paper output | closed `SystemOutput` |
| 2 | `ApprovedActionIntent` from V7 | source-grep |
| 3 | raw symbol / venue / strategy in `PaperOpportunity` | `extra=forbid` + denylist |
| 4 | Gel.Al write helper in V7 | no Redis/HTTP/DB/Telegram import |
| 5 | `approved_for_live` ever True | `Literal[False]` |
| 6 | paper outcome internal claimed as replay evidence | `external=True` required |

## 21. Done definition

- `PaperOpportunity` / `PaperOpportunityKind` / `PaperOpportunitySource` implemented.
- `PaperDecision` / `PaperDecisionReason` implemented.
- `PaperCoPilotResult` implemented.
- `PaperCoPilotContext` + `evaluate_paper_opportunity` implemented.
- `emit_paper_copilot_evaluated` audit helper using
  `LEDGER_STATE_CHANGED`.
- `run_paper_copilot_file` + `python -m sentinel.runtime.paper_copilot`.
- `PaperOutcome` + `compare_paper_decision_to_outcome`.
- `GelAlPaperComparison` + `compare_gelal_shadow_to_paper_decision`.
- 10 fixtures (6 valid + market + Gel.Al + invalid).
- 53+ V7 tests.
- Public API additions.
- Build plan + closure review.
- Full sweep GREEN.

## 22. Deferred V8+ items

- V8 Canary micro-live veto layer.
- V9 Limited live co-governance.
- Live veto.
- Real Gel.Al write channel.
- Telegram commands.
- Production policy auto-tuning.
- Real exchange adapter.
- LLM-assisted advisory.
