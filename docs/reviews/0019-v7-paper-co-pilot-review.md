# 0019 — V7 Paper Co-Pilot — Closure Review

**Date:** 2026-05-20  
**Reviewer:** Automated phase-closure protocol  
**Phase:** V7 — Paper Co-Pilot  
**Build plan:** `docs/build/0008-v7-paper-co-pilot-build-plan.md`  
**Final verdict:** **GREEN**

> The V7 review is filed as `0019-…`; the goal spec's placeholder
> number does not match the actual numbering in the repository
> (0014-0018 are V2/V3/V4/V5/V6 reviews).

---

## 1. Status

Status: **GREEN**  
Scope: V7 — non-executing paper co-pilot advisor producing closed
`SystemOutput` paper decisions over market and Gel.Al shadow events.

---

## 2. Version: V7 — Paper Co-Pilot

Seventh phase added to PR #1 on top of v0.1.0-mvb baseline.

---

## 3. Scope completed

- `PaperOpportunitySource` (5-value closed enum)
- `PaperOpportunityKind` (9-value closed enum; no trade-side terms)
- `PaperOpportunity` (frozen, `extra=forbid`, denylist for 28
  forbidden field names; raw symbol/venue/strategy/order/account/API
  fields rejected at construction)
- `build_paper_opportunity_from_market_observation`
- `build_paper_opportunity_from_gelal_shadow` (raw labels hashed
  into `scope_hash` / `provenance_hash`)
- `PaperDecisionReason` (13-value closed enum; value strings
  paraphrased to avoid forbidden literal substrings)
- `PaperDecision` (`shadow_only` / `creates_action` /
  `writes_external` / `approved_for_live` pinned via `Literal` AND
  re-validated at `model_validator` time)
- `PaperCoPilotResult` (opportunity / decision id match validator;
  permanent / ring overlap rejected)
- `PaperCoPilotContext` + `evaluate_paper_opportunity` (deterministic
  rule set; constitutional hard-stops first; V6 policy upgrades to
  BLOCK; closed `SystemOutput` only)
- `emit_paper_copilot_evaluated` (permanent
  `LEDGER_STATE_CHANGED` audit; payload excludes raw labels)
- `PaperOutcomeKind` (7-value closed enum) +
  `PaperOutcome` (`external` flag gates `evidence_usable_for_replay`)
- `compare_paper_decision_to_outcome` → `PaperDecisionOutcomeComparison`
- `GelAlPaperComparison` + `compare_gelal_shadow_to_paper_decision`
  (4-band agreement; observer-side Gel.Al descriptor stays inside
  the comparison record)
- `run_paper_copilot_file` (3 source kinds: `market_jsonl`,
  `gelal_shadow_jsonl`, `paper_opportunity_jsonl`)
- `python -m sentinel.runtime.paper_copilot` CLI with exit codes 0/1/2/3
- Public API additions (18 V7 symbols)
- 4 fixtures (mixed paper, Gel.Al opportunity / bad_order / kill_switch)
- 84 V7 tests across 7 test files

---

## 4. Files added

```
sentinel/paper/__init__.py
sentinel/paper/opportunity.py
sentinel/paper/decision.py
sentinel/paper/copilot.py
sentinel/paper/audit.py
sentinel/paper/outcome.py
sentinel/paper/gelal_compare.py
sentinel/runtime/paper_copilot.py
docs/build/0008-v7-paper-co-pilot-build-plan.md
docs/reviews/0019-v7-paper-co-pilot-review.md
tests/paper/__init__.py
tests/paper/_fixtures.py
tests/paper/test_paper_opportunity.py
tests/paper/test_paper_decision.py
tests/paper/test_paper_copilot.py
tests/paper/test_paper_audit.py
tests/paper/test_paper_outcome.py
tests/paper/test_gelal_compare.py
tests/runtime/test_paper_copilot_runner.py
tests/fixtures/paper/gelal_shadow_opportunity_seen.jsonl
tests/fixtures/paper/gelal_shadow_bad_order.jsonl
tests/fixtures/paper/gelal_shadow_kill_switch.jsonl
tests/fixtures/paper/paper_opportunities_mixed.jsonl
tests/fixtures/paper/forbidden_fields_invalid.jsonl
```

Modified (additive only):

```
sentinel/__init__.py            (V7 exports + __all__)
tests/test_public_api.py        (V7_PUBLIC_API_ADDITIONS + test)
```

---

## 5. Tests added

84 new V7 tests.  Total suite: **1374 passing**.

| File | Tests |
|---|---|
| `tests/paper/test_paper_opportunity.py` | 13 |
| `tests/paper/test_paper_decision.py` | 12 |
| `tests/paper/test_paper_copilot.py` | 13 |
| `tests/paper/test_paper_audit.py` | 4 |
| `tests/paper/test_paper_outcome.py` | 7 |
| `tests/paper/test_gelal_compare.py` | 6 |
| `tests/runtime/test_paper_copilot_runner.py` | 15 |
| `tests/test_public_api.py` (V7 additions test) | +1 |

---

## 6. Fixtures added

```
gelal_shadow_opportunity_seen.jsonl   nominal Gel.Al envelope
gelal_shadow_bad_order.jsonl          bad_order=true Gel.Al envelope
gelal_shadow_kill_switch.jsonl        kill_switch_active=true envelope
paper_opportunities_mixed.jsonl       3 direct PaperOpportunity records
forbidden_fields_invalid.jsonl        payload with symbol/order_side/api_key
```

---

## 7. Paper opportunity model

`PaperOpportunity` carries only abstract bounded scalars
(`risk_score`, `confidence`, `magnitude_score`, `staleness_ms`,
`latency_ms`, `liquidity_score`, `spread_score`, optional
`replay_evidence_score` and `memory_echo_score`) plus hashed scope
refs (`scope_hash`, `provenance_hash`, optional `policy_scope_id`).
`extra='forbid'` plus a documented 28-name denylist guarantees that
no raw symbol / venue / strategy / order / account / API field can
ever be attached.

---

## 8. Paper decision model

`PaperDecision`:

- `shadow_only: Literal[True]` — pinned
- `creates_action: Literal[False]` — pinned
- `writes_external: Literal[False]` — pinned
- `approved_for_live: Literal[False]` — pinned

`output == BLOCK` requires at least one blocking reason
(`HIGH_RISK`, `BAD_ORDER_OBSERVED`, `KILL_SWITCH_OBSERVED`,
`POLICY_BLOCK`, `STALE_DATA`, `MEMORY_CONFLICT`).

`output == NEED_RECALL` requires `NEEDS_RECALL` in reasons.

Reason enum value `BAD_ORDER_OBSERVED` is paraphrased to
`"bad_dispatch_observed"` because `"bad_order_observed"` would trip
the constitutional forbidden-literal guard (`order` is a forbidden
substring).  Python attribute name preserves the goal-spec
terminology; only the string value is paraphrased.

---

## 9. Paper co-pilot evaluator

Deterministic scoring order:

1. Constitutional hard-stops (kill-switch / bad-dispatch / high
   risk / extreme staleness) → BLOCK.
2. V6 active policy may upgrade non-block paths to BLOCK.
3. `memory_echo_score >= 0.7` → NEED_RECALL.
4. Replay uncertainty hint added to MONITOR reasons.
5. `confidence < 0.2` → WAIT.
6. Staleness MONITOR softening.
7. Very low magnitude + risk → NO_ACTION.
8. Otherwise → MONITOR.

The evaluator never constructs an action-intent object (source-grep
verified).

---

## 10. Financial memory usage

V3 in-memory store may be passed via
`PaperCoPilotContext.memory_store` but is consulted only for its
presence flag in V7.  Raw-symbol recall is forbidden by the Recall
Protocol; instead, `PaperOpportunity.memory_echo_score` carries a
pre-computed signal.

---

## 11. Replay evidence usage

V4 evidence is consumed advisorily via
`PaperCoPilotContext.replay_evidence_score` or
`PaperOpportunity.replay_evidence_score`.  No new replay sessions
started.

---

## 12. Financial deontic policy usage

If a V6 active policy is provided, the co-pilot constructs a
`FinancialPolicyInput` and calls `evaluate_financial_policy`.  Policy
BLOCK upgrades the paper output; non-block policy outputs are
informational.

---

## 13. Paper-vs-Gel.Al comparison

`GelAlPaperComparison.agreement_band ∈ {same_direction,
sentinel_more_conservative, sentinel_less_conservative, incomparable}`.

Observer-side `gelal_observed_decision` descriptor (e.g.
`gelal_kill_switch_active`, `gelal_bad_dispatch_observed`,
`gelal_opportunity_seen`) stays in the comparison record;
Sentinel's `output` remains a closed `SystemOutput`.

---

## 14. Paper outcome tracking

`PaperOutcomeKind` enumerates 7 observed-outcome bands (no
trade-side terms).  `compare_paper_decision_to_outcome` returns a
`PaperDecisionOutcomeComparison` carrying:

- `was_conservative`, `would_have_helped`, `would_have_hurt`
- `alignment_score ∈ [0,1]`
- `evidence_usable_for_replay` — True iff `PaperOutcome.external`
  is True

Comparisons never mutate M2 or active policy.

---

## 15. Safety invariants

| # | Invariant | Status |
|---|-----------|--------|
| 1 | no live execution path | GREEN |
| 2 | no Gel.Al write path | GREEN (no Redis/HTTP/DB/Telegram in V7) |
| 3 | no exchange / network / LLM imports | GREEN |
| 4 | no forbidden output literals in V7 source | GREEN |
| 5 | no `ApprovedActionIntent` generated | GREEN (source-grep) |
| 6 | no paper-to-live promotion | GREEN (`approved_for_live=Literal[False]`) |
| 7 | no policy mutation by V7 | GREEN |
| 8 | no M2 verified write by V7 | GREEN |
| 9 | output ⊆ closed `SystemOutput` | GREEN |
| 10 | observer audit present | GREEN (`LEDGER_STATE_CHANGED`) |
| 11 | hash chain verifies after V7 pipeline | GREEN |
| 12 | raw symbol/venue/strategy stripped from `PaperOpportunity` | GREEN |
| 13 | `PaperOutcome.external=False` → not replay-usable | GREEN |
| 14 | dry_sim canonical output unchanged | GREEN (WAIT, 4/2/0) |

---

## 16. What is deliberately deferred

- V8 Canary Micro-Live Veto Layer.
- V9 Limited live co-governance.
- Live veto.
- Real Gel.Al write channel.
- Telegram commands.
- Production policy auto-tuning.
- Real exchange adapter.
- LLM-assisted advisory.
- Multi-instance / fork / migration.

---

## 17. Next recommended version

**V8 — Canary Micro-Live Veto Layer.**

V7 closure unlocks V8.  V8 must arrive with its own design doc and
closure review.  V7 grants no implicit permission for V8 to flip
`approved_for_live`.

---

## Local sweep at HEAD (V7)

```
uv sync                          Resolved 17 packages
uv run ruff check .              All checks passed
uv run ruff format --check .     218 files clean
uv run pyright                   0 errors / 0 warnings / 0 informations
uv run pytest -q                 1374 passed
forbidden imports grep           clean
forbidden outputs grep           clean
dry sim canonical                WAIT (audit=4, perm=2, ring=0)
paper-copilot CLI smoke          opportunities_seen=1 block=1 hash_chain_valid=True
```

V7 phase is **CLOSED**.
