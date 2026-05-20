# Gel.Al Borsa ↔ Sentinel — Read-Only / Shadow Bridge Alignment

> **Status: ALIGNMENT DOCUMENT. No code, no live order path,
> no exchange API keys.**
>
> Triggered by `/goal` Phase 4. Companion to
> `docs/build/0002-read-only-market-observation-plan.md`.
>
> Belgelenen ana mesele: Sentinel **trade motoru değildir**.
> Sentinel zihinsel çekirdek, risk / audit / hafıza / deontic
> katmandır. Execution ayrı kalır. Gel.Al Borsa execution
> engine ayrı kalır. Sentinel önce **read-only observer**
> olarak bağlanır.

---

## 1. Current Gel.Al Borsa state

Gel.Al Borsa is, today, **the** execution surface. It is the
system that:

```
- holds (and is responsible for) exchange API credentials
- speaks to one or more exchange / venue HTTP + WS endpoints
- submits, modifies, cancels live orders
- tracks live account balance, position state, fills
- enforces its own risk rails (margin, per-symbol caps,
  daily loss caps) inside its own boundaries
- exposes its own operator interface (Telegram / dashboard)
```

Gel.Al's responsibilities, in this alignment, **do not move
into Sentinel**. Specifically:

```
- Gel.Al keeps the exchange SDK imports.
- Gel.Al keeps the API keys.
- Gel.Al keeps the order placement code.
- Gel.Al keeps the live position state.
- Gel.Al keeps the kill-switch surface (Halit's manual hand
  on the wheel).
```

Sentinel does **not** want any of these. That is the entire
point of the alignment.

---

## 2. Sentinel role

Sentinel, in the first integration mode, is a **shadow
observer**. It receives a stream of sanitized market
observations (and, optionally, sanitized Gel.Al state
observations) and produces only members of the closed v0.1
output set:

```
SystemOutput ∈ { WAIT, BLOCK, MONITOR, NEED_RECALL, NO_ACTION }
```

None of these are execution verbs. None of these can become
order side. None of these are interpreted by Gel.Al as a
"signal to buy / sell". They are status-of-mind outputs from
the brain layer — and the brain in this mode is **read-only
toward the execution surface**.

Specifically, Sentinel's outputs in shadow mode are:

```
WAIT         — default-deny posture; "I have observed; I see
                no condition I am authorized to act on."
                (And it cannot act anyway. There is no path.)
BLOCK        — a deontic violation has been detected; the
                brain expresses disapproval. In shadow mode
                this is recorded to M1 only; Gel.Al is not
                wired to receive it.
MONITOR      — observation magnitude is meaningful but
                inconclusive; brain elects to keep watching.
NEED_RECALL  — composite trigger asks for a memory lookup;
                memory write gate is silent and candidate-
                only; nothing leaks.
NO_ACTION   — explicit "no opinion" status; equivalent to
                WAIT for our purposes but distinguishable in
                the audit trail.
```

None of these route to an order. None of these route to
Gel.Al's order surface. None of these enable, arm, or disarm
Gel.Al's kill-switch.

---

## 3. Gel.Al remains the execution system

This is the durable separation:

```
Gel.Al Borsa                        Sentinel MVB
-----------------                   ------------------
Owns: exchange credentials          Owns: ledger + invariants
Owns: order placement                Owns: deontic gate
Owns: position state                 Owns: memory gate
Owns: PnL tracking                   Owns: recall protocol
Owns: live margin rails              Owns: M1 hash chain
Owns: execution risk rails           Owns: observer router
                                     Owns: dry sim runtime
Sends to Sentinel (read-only):       Sends to Gel.Al:
  - sanitized market observations    - NOTHING
  - sanitized own-state observations
    (account heartbeats, order
     book context — see §6 for the
     allowed field set)
```

The Gel.Al → Sentinel direction is **the only direction**
across the boundary in the first integration mode. Sentinel →
Gel.Al has **no channel**. Not "is unused" — does not exist.
Gel.Al has no consumer wired for Sentinel output, and Sentinel
has no producer wired toward Gel.Al's execution surface.

---

## 4. Sentinel remains observer / brain / risk / audit layer

The four roles that **stay** inside Sentinel:

```
[1] Observer
    - Receives sanitized envelopes.
    - Routes them through route_observer_event (catalog
      permanence policy).
    - Writes M1 entries via JsonlObserverLedger (hash chain
      preserved).

[2] Brain (Core)
    - Compiles ObservationEvent into NeuralSeed via the
      ingress compiler.
    - Runs M0 tissue + WorkspacePulse.
    - Maintains the silent / candidate-only memory write
      gate.
    - Maintains the composite-AND / top-1 / CORE-only recall
      protocol.

[3] Risk / Deontic
    - Default-deny deontic gate.
    - 11 declaratives; every failure → DEONTIC_BLOCKED audit
      event (permanent).
    - Cannot be overridden by an operator (constitutional
      C-12).
    - Cannot be biased by an LLM (constitutional C-03).

[4] Audit
    - Every gate decision, every adapter registration, every
      recall trigger / rejection, every envelope reception /
      rejection is M1-audited.
    - Hash chain re-verifies on demand.
    - Forbidden output literals do NOT appear in any reason
      field (CI grep enforces).
```

---

## 5. First bridge mode: shadow observation only

The **first** integration mode (and the only one in scope for
this alignment) is shadow observation. Concretely:

```
A. Gel.Al runs as it does today. Live execution unchanged.
   Halit's hand stays on the wheel.

B. Gel.Al adds a side-car export: it writes
   MarketObservationEnvelope-shaped JSON events (per
   docs/build/0002 §5) to a local file / queue. This is
   one-way write from Gel.Al.

C. Sentinel reads those envelopes from a separate process,
   sanitizes them, and runs the v0.1 pipeline.

D. Sentinel produces SystemOutput values (WAIT / MONITOR /
   NEED_RECALL / BLOCK / NO_ACTION) and writes them to its
   own M1 ledger.

E. The Sentinel output is NOT read by Gel.Al. There is no
   subscription, no reader, no auto-action hook.

F. Halit (and only Halit) inspects Sentinel's M1 ledger
   manually. He uses it as a second opinion, like a risk
   officer reading a desk's daily report. The decision to
   act, throttle, or override stays with Halit.
```

The shadow window has a fixed duration (see §10).

---

## 6. Data exported from Gel.Al to Sentinel

Allowed fields (sanitized; observer-side; never propagated
into Core ObservationEvent labels):

```
MarketObservationEnvelope (per docs/build/0002 §5):
  - envelope_id, source_system, source_adapter_id, timestamp,
    provenance_hash
  - venue, symbol            (observer-side only — Core never
                              sees these)
  - raw_bid, raw_ask, spread_pct
  - orderbook_age_ms, latency_ms
  - depth_summary (bid_top_n_qty, ask_top_n_qty,
                   imbalance_ratio)

Optionally, GelAlStateHeartbeat (a NEW observer-side schema,
reserved here, NOT implemented):
  - envelope_id, source_system, source_adapter_id, timestamp,
    provenance_hash
  - account_age_seconds            (how long the account has
                                    been live this session)
  - open_position_count            (integer count, NO symbol
                                    list, NO size, NO PnL)
  - cooldown_active                (bool: is Gel.Al currently
                                    in a self-throttle window?)
  - risk_rail_engaged              (bool: did Gel.Al's own
                                    rails fire recently?)
  - last_heartbeat_seq             (monotonic seq number)

  Explicitly NOT included:
  - position symbol names
  - position sizes
  - PnL
  - balance
  - margin numbers
  - open order IDs / sides / sizes
  - exchange API key IDs / hashes
  - fee schedule
  - strategy names / strategy parameters
```

Even the heartbeat is a coarse-grained opacity signal:
"Gel.Al is alive, not in cooldown, no rail engaged" or
"Gel.Al is alive, in cooldown, one rail engaged in the last
window". Sentinel does NOT learn Gel.Al's strategy. Sentinel
does NOT learn what Gel.Al is doing. Sentinel only learns
Gel.Al's **health posture**, and only to the extent the
heartbeat schema reveals.

---

## 7. Data never exported from Sentinel to execution

This is the durable constraint. Sentinel **does not produce**
any of:

```
- an order
- a side (buy / sell / long / short / open / close)
- a quantity
- a target price
- a stop loss
- a take profit
- a kill-switch arm / disarm command
- a strategy-parameter mutation
- a risk-rail threshold mutation
- an operator override of the deontic gate
- a "trade signal" of any shape
```

Even WAIT / MONITOR / NEED_RECALL / BLOCK / NO_ACTION are
**not** wired into a Gel.Al consumer. If a future revision
wants Sentinel-influenced execution, that revision must
write its own design doc, pass its own readiness review,
introduce its own constitutional amendments (publicly and
explicitly), and survive its own audit. It is not implicitly
allowed by this alignment.

---

## 8. Allowed Sentinel outputs

Restated for clarity. The closed set:

```
WAIT
MONITOR
NEED_RECALL
BLOCK
NO_ACTION
```

This set is enforced by the `SystemOutput` enum (v0.1
StrEnum) and by `tests/runtime/test_output_guard.py`. Any
attempt to extend the set is a constitutional change and
must be reviewed as such.

---

## 9. Forbidden

The list, exhaustively, of what is forbidden under this
alignment:

```
F-01 live order from Sentinel
F-02 auto approval of any execution by Sentinel
F-03 strategy threshold mutation from Sentinel
F-04 kill-switch mutation by Sentinel
       (without explicit human command — and "explicit
        human command" means a command issued OUTSIDE
        Sentinel, in Gel.Al's own operator surface; not
        a Sentinel-produced verb)
F-05 exchange API keys inside Sentinel repo
F-06 exchange API keys inside Sentinel environment
F-07 exchange SDK import under sentinel/
F-08 LLM SDK import under sentinel/
F-09 forbidden output literal in any M1 reason field
F-10 memory verified-status write driven by market data
F-11 production numerics matrix update driven by market data
F-12 deontic gate override driven by market data
F-13 human-direct recall push driven by market data
F-14 replay-driven memory update driven by market data
F-15 cross-instance / fork / migration path that would let
     a "shadow" instance go live
F-16 silent action of any kind
```

If any of F-01 .. F-16 becomes operationally plausible, the
shadow mode is paused and the alignment is re-reviewed.

---

## 10. 30-day shadow evaluation metrics

Once the bridge (in synthetic-fixture form first, then in
Gel.Al-export form) is wired and Sentinel begins receiving
real-shaped envelopes, a 30-day shadow window is observed.
At the end of the window, the following metrics are read off
the M1 ledger and reported in a follow-up review:

```
Volume metrics
  - total observations received (envelope count)
  - total observations sanitized into Core ObservationEvent
  - total observations rejected (with breakdown per reason
    enum from docs/build/0002 §14:
        schema_violation, stale, latency_breach,
        adapter_untrusted, duplicate_envelope_id)

Output metrics
  - count of SystemOutput.BLOCK emissions
  - count of SystemOutput.WAIT emissions
  - count of SystemOutput.MONITOR emissions
  - count of SystemOutput.NEED_RECALL emissions
  - count of SystemOutput.NO_ACTION emissions
  - histogram of which deontic declarative blocked
    (when BLOCK was emitted)

Quality metrics (annotated by Halit during the window)
  - number of Gel.Al opportunities observed
    (Halit annotates: "Gel.Al saw an opportunity at T;
     did Sentinel emit BLOCK?")
  - number of correct blocks
    (Halit annotates: "in hindsight, the block aligned with
     a bad opportunity")
  - number of false blocks
    (Halit annotates: "the block prevented an opportunity
     that would have been correct")
  - number of correct waits
    (Halit annotates: "Sentinel said WAIT and that was
     right")

Safety metrics (mechanical, no Halit annotation)
  - forbidden output literal count                 must be 0
  - bad order count emitted by Sentinel            must be 0
                                                   (cannot
                                                   be > 0 by
                                                   construction)
  - hash chain re-verification                     must be PASS
  - 877 v0.1 tests still passing on each release
    candidate in the window                        must be PASS
  - new tests added during the window              non-regressing
  - CI green on main throughout the window         must be PASS
  - exchange SDK presence under sentinel/          must be 0
  - LLM SDK presence under sentinel/               must be 0
```

A 30-day shadow review is written at the end of the window:
`docs/reviews/0012-v0.x-shadow-window-review.md` (number
reserved; not created in this commit). That review either
authorizes the next planning step (a Sentinel → Gel.Al
**advisory** read-only signal, still not execution, still
gated by deontic and still subject to its own constitutional
amendment), or it does not. Failure to authorize means the
shadow mode continues unchanged.

---

## 11. Final hüküm

```
Sentinel is the brain.
Gel.Al is the hand.
The brain observes, the hand acts — and in this alignment,
the brain does not speak to the hand. It only writes to
its own journal, which Halit reads.

This is the conservative integration. It can be relaxed
later, but only through a documented constitutional
amendment, never silently. v0.1's red lines are PRESERVED.
```
