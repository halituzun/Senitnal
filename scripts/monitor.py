#!/usr/bin/env python3
"""Terminal Dashboard v3 — clean borders, live trade log, proper alignment."""

import json, os, shutil, sys, time
from pathlib import Path

SNAP = Path("panel/api/src/mock/snapshot.json")
PORT = Path("data/paper_trades/portfolio.json")
TRADE_LOG = Path("data/paper_trades/trades.jsonl")

class C:
    G = "\033[32m"; R = "\033[31m"; Y = "\033[33m"; B = "\033[1m"; D = "\033[2m"
    C = "\033[36m"; W = "\033[37m"; X = "\033[0m"; CL = "\033[2J\033[H"

def g(t): return f"{C.G}{t}{C.X}"
def r(t): return f"{C.R}{t}{C.X}"
def y(t): return f"{C.Y}{t}{C.X}"
def b(t): return f"{C.B}{t}{C.X}"
def c(t): return f"{C.C}{t}{C.X}"
def d(t): return f"{C.D}{t}{C.X}"

def bar(v, w=12):
    f = int(max(0, min(v, 1.0)) * w)
    color = C.G if v > 0.5 else C.Y if v > 0.25 else C.R
    return f"{color}{'█'*f}{C.X}{'░'*(w-f)}"

def render():
    last_trade = 0
    while True:
        try:
            snap = json.loads(SNAP.read_text()) if SNAP.exists() else {}
            ls = snap.get("learning_state", {})
            strats = snap.get("strategies", [])
            
            pf = json.loads(PORT.read_text()) if PORT.exists() else {"balance_try":10000,"closed_pnl_try":0,"total_trades":0,"winning_trades":0,"positions":{}}
            
            trades_raw = []
            if TRADE_LOG.exists():
                for line in open(TRADE_LOG).readlines()[-100:]:
                    if line.strip(): trades_raw.append(json.loads(line))
            
            age = int(time.time() - SNAP.stat().st_mtime) if SNAP.exists() else 999
            cycle = ls.get("cycle", 0)
            alpha = ls.get("adaptive_alpha", 0)
            acc = ls.get("accuracy", 0)
            mem = ls.get("total_memories", 0)
            pnl_val = pf.get("closed_pnl_try", 0)
            total_tr = pf.get("total_trades", 0)
            wins = pf.get("winning_trades", 0)
            wr = wins/max(1,total_tr)
            positions = pf.get("positions", {})
            
            cols, rows = shutil.get_terminal_size((100, 35))
            W = min(cols - 2, 140)
            
            sys.stdout.write(C.CL)
            
            # ═══ HEADER ═══
            status = g("● LIVE") if age < 8 else y("● STALE") if age < 30 else r("● DEAD")
            pnl_str = g(f"{pnl_val:+.1f} TRY") if pnl_val > 0 else r(f"{pnl_val:+.1f} TRY") if pnl_val < 0 else f"{pnl_val:+.1f} TRY"
            
            print("═" * W)
            print(f"  SENTINEL TRADING  │  Cycle {cycle}  │  α={alpha:.3f}  │  Acc={acc:.0%}  │  Mem={mem}  │  {status}  │  {time.strftime('%H:%M:%S')}")
            print("═" * W)
            print(f"  PnL: {pnl_str}  │  {total_tr} trades  │  {g(f'{wr:.0%}')} WR  │  {len(positions)} open  │  New: {total_tr - last_trade}")
            last_trade = total_tr
            print("─" * W)
            
            # ═══ STRATEGIES ═══
            print(f"  {'STRATEGY':<20s} {'EDGE':<14s} {'RISK':<8s} {'Q':<6s} {'STATE':<14s} {'SIGNAL':<10s} POS")
            print("  " + "─" * (W - 4))
            
            for st in strats:
                name = st["name"][:18]
                edge = st.get("current_edge_score", 0)
                risk = st.get("current_risk_score", 0)
                q = st.get("strategy_quality", 0)
                state = st.get("lifecycle_state", "?")
                has_pos = "🔒" if any(st["strategy_id"] in k for k in positions) else "  "
                
                if edge >= 0.28: sig = g("▶ BUY ")
                elif edge >= 0.20: sig = y("▶ WAIT")
                else: sig = r("▶ PASS")
                
                rs = g(f"{risk:.2f}") if risk < 0.3 else y(f"{risk:.2f}") if risk < 0.6 else r(f"{risk:.2f}")
                qs = g(f"{q:.2f}") if q > 0.5 else y(f"{q:.2f}") if q > 0.3 else r(f"{q:.2f}")
                ss = g(state) if "ACTIVE" in state else y(state) if "LIMITED" in state else r(state)
                
                print(f"  {name:<20s} {bar(edge):<14s} {edge:.2f}  {rs:<16s} {qs:<10s} {ss:<22s} {sig:<14s}{has_pos}")
            
            # ═══ POSITIONS ═══
            if positions:
                print("─" * W)
                print(f"  OPEN POSITIONS:")
                for sid, pd in list(positions.items())[:5]:
                    amt = pd.get("amount_try", 0)
                    entry = pd.get("entry_price", 0)
                    print(f"    {sid:<30s} {amt:8.0f} TRY @ {entry:<12.2f}")
            
            # ═══ TRADE LOG ═══
            print("═" * W)
            log_lines = max(6, rows - 18 - len(strats) - (min(len(positions),5)+2 if positions else 0))
            
            show = trades_raw[-log_lines:]
            for t in show:
                a = t.get("action", "?")
                sid = t.get("strategy_id", "?")[:18]
                if a == "OPEN":
                    msg = f"{g('🟢 BUY ')} {sid:<20s} {t.get('amount_try',0):8.0f} TRY @ {t.get('price',0):.0f}"
                elif a == "CLOSE":
                    p = t.get("pnl_try", 0)
                    icon = g("🟢 WIN") if t.get("win") else r("🔴 LOSS")
                    msg = f"{icon} {sid:<20s} {p:+8.1f} TRY"
                else:
                    msg = f"   {a} {sid}"
                print(f"  {msg}")
            
            # Fill
            for _ in range(log_lines - len(show)):
                print()
            
            print("═" * W)
            print(d(f"  R:2s │ Ctrl+C exit │ Loop running" if age < 20 else f"  R:2s │ Ctrl+C exit │ Loop STOPPED ({age}s ago)"))
            
        except Exception as e:
            print(r(f"Error: {e}"))
        
        time.sleep(2)

if __name__ == "__main__":
    try: render()
    except KeyboardInterrupt: print(g("\n✓ Closed"))
