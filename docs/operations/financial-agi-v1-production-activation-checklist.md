# Financial AGI v1 — Production Activation Checklist

**Version:** V10  
**Date:** 2026-05-20

Complete all items before transitioning to `AGI_V1_READY` in production.

---

## Evidence gate (mandatory)

- [ ] `shadow_30d` evidence window present and `satisfied=True`
- [ ] `paper_30d` evidence window present and `satisfied=True`
- [ ] `canary_30d` evidence window present and `satisfied=True`
- [ ] `limited_live_90d` evidence window present and `satisfied=True` (**90-day hard requirement**)
- [ ] `incident_free_90d` evidence window present and `satisfied=True` (**90-day hard requirement**)
- [ ] `hash_chain_integrity` window present and `satisfied=True`
- [ ] `policy_stability` window present and `satisfied=True`
- [ ] `evaluate_evidence_gate` returns `EvidenceGateDecision.PASS_GREEN`

## Governance stack (mandatory)

- [ ] Active policy record present (`status=ACTIVE`)
- [ ] Policy not expired (staleness_ms within threshold)
- [ ] Human approval available for all live-impact requests
- [ ] Kill switch NOT observed
- [ ] Hash chain valid (`ledger.verify() is True`)
- [ ] No canary veto in context

## Capability map verification

- [ ] `direct_execution=False` confirmed
- [ ] `exchange_imports=False` confirmed
- [ ] `llm_imports=False` confirmed
- [ ] `gelal_write_path=False` confirmed
- [ ] `approved_action_intent_generation=False` confirmed

## Safety invariant smoke tests

- [ ] CLI smoke test: `exit 0`, `hash_chain_valid=True`
- [ ] Full test suite: **1641+ passing**
- [ ] `ruff check .`: **0 errors**
- [ ] `pyright`: **0 errors**
- [ ] Forbidden import grep: clean
- [ ] Forbidden output grep: clean

## Readiness report

- [ ] `FinancialAGIReadinessReport.status == "GREEN"`
- [ ] `activation_state == "agi_v1_ready"`
- [ ] `allowed_to_influence_live` matches expected pattern
- [ ] `FINANCIAL_AGI_READINESS_RECORDED` event in permanent ledger

## Final approval

- [ ] Engineering lead sign-off
- [ ] Operator sign-off
- [ ] Incident response plan in place
- [ ] Rollback plan documented and tested
