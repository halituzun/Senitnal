#!/usr/bin/env python3
"""Full-screen Trading Dashboard v2 — split layout, live log, positions.

Top: Strategy grid + Portfolio + Exchange balances
Bottom: Scrolling trade log with real-time updates
"""

import json, os, shutil, sys, time
from pathlib import Path

SNAPSHOT = Path("panel/api/src/mock/snapshot.json")
PORTFOLIO = Path("data/paper_trades/portfolio.json")
TRADES = Path("data/paper_trades/trades.jsonl")

C = {
    "g": "\033[32m", "r": "\033[31m", "y": "\033[33m",
    "b": "\033[34m", "c": "\033[36m", "m": "\033[35m",
    "w": "\033[37m", "B": "\033[1m", "d": "\033[2m",
    "x": "\033[0m", "clr": "\033[2J\033[H",
    "inv": "\033[7m",
}

def clr(c: str, t: str) -> str: return f"{C.get(c,'')}{t}{C['x']}"
def bar(v: float, w: int = 15, mx: float = 1.0) -> str:
    f = int(min(abs(v), mx) / mx * w)
    color = "g" if v > 0.5 else "y" if v > 0.25 else "r"
    return clr(color, "█" * f + "░" * (w - f))

_last_trade_count = 0

def render():
    global _last_trade_count
    cols, rows = shutil.get_terminal_size((120, 40))
    
    while True:
        try:
            snap = json.loads(SNAPSHOT.read_text()) if SNAPSHOT.exists() else {}
            ls = snap.get("learning_state", {})
            strategies = snap.get("strategies", [])
            events = snap.get("ledger_events", [])
            
            pf = json.loads(PORTFOLIO.read_text()) if PORTFOLIO.exists() else {"balance_try": 10000, "closed_pnl_try": 0, "total_trades": 0, "winning_trades": 0, "positions": {}}
            
            # Read all trades for log
            trade_lines = []
            if TRADES.exists():
                trade_lines = [json.loads(l) for l in open(TRADES).readlines()[-50:] if l.strip()]
            
            age = int(time.time() - SNAPSHOT.stat().st_mtime) if SNAPSHOT.exists() else 999
            cycle = ls.get("cycle", 0)
            alpha = ls.get("adaptive_alpha", 0)
            acc = ls.get("accuracy", 0)
            mem = ls.get("total_memories", 0)
            pnl = pf.get("closed_pnl_try", 0)
            trades = pf.get("total_trades", 0)
            wins = pf.get("winning_trades", 0)
            wr = wins / max(1, trades)
            positions = pf.get("positions", {})
            
            live = "g" if age < 8 else "y" if age < 25 else "r"
            pnl_c = "g" if pnl > 0 else "r" if pnl < 0 else "y"
            
            # Calculate available height for log
            header_h = 8
            strat_h = len(strategies) + 2
            pos_h = min(len(positions) + 3, 8) if positions else 0
            log_h = max(6, rows - header_h - strat_h - pos_h - 2)
            
            sys.stdout.write(C["clr"])
            
            # ═══ HEADER ═══
            w = cols - 2
            print(clr("B", f"╔{'═'*w}╗"))
            print(clr("B", f"║  SENTINEL TRADING v2 {' '*(w-26)}║"))
            print(clr("B", f"╠{'═'*w}╣"))
            print(f"║  Cycle: {cycle:<6} │ α: {alpha:.3f} │ Acc: {acc:.0%} │ Mem: {mem:<5} │ {clr(live, f'LIVE ({age}s)')} {' '*(w-65)}║")
            print(f"║  PnL: {clr(pnl_c, f'{pnl:+.1f} TRY'):<20} │ Trades: {trades:<5} │ WR: {wr:.0%} │ Pos: {len(positions):<3} {' '*(w-60)}║")
            
            # ═══ STRATEGIES ═══
            print(clr("B", f"╠{'═'*w}╣"))
            print(f"║  {'STRATEJİ':<19s} {'EDGE':<17s} {'RISK':<8s} {'QUALITY':<10s} {'STATE':<18s} {'POS':<5s} {'SİNYAL':<8s} {' '*(w-92)}║")
            
            for st in strategies:
                name = st["name"][:17]
                edge = st.get("current_edge_score", 0)
                risk = st.get("current_risk_score", 0)
                q = st.get("strategy_quality", 0)
                state = st.get("lifecycle_state", "?")
                
                rc = "g" if risk < 0.3 else "y" if risk < 0.6 else "r"
                qc = "g" if q > 0.5 else "y" if q > 0.3 else "r"
                sc = "g" if "ACTIVE" in state or "LIMITED" in state else "y" if "PAUSED" in state else "r"
                
                has_pos = "🔒" if any(st["strategy_id"] in k for k in positions) else "  "
                signal = clr("g", "BUY") if edge >= 0.28 else clr("y", "WAIT") if edge >= 0.20 else clr("r", "PASS")
                
                print(f"║  {name:<17s} {bar(edge):<17s} {edge:.2f}  {clr(rc, f'{risk:.2f}'):<20s} {clr(qc, f'{q:.2f}'):<20s} {clr(sc, state):<26s} {has_pos}  {signal:<16s}║")
            
            # ═══ POSITIONS ═══
            if positions:
                print(clr("B", f"╠{'═'*w}╣"))
                print(f"║  AÇIK POZİSYONLAR {' '*(w-20)}║")
                for sid, pd in list(positions.items())[:6]:
                    entry = pd.get("entry_price", 0)
                    amt = pd.get("amount_try", 0)
                    name = sid[:30]
                    print(f"║    {name:<30s} {amt:8.0f} TRY @ {entry:<12.2f} {' '*(w-58)}║")
            
            # ═══ TRADE LOG ═══
            print(clr("B", f"╠{'═'*w}╣"))
            print(f"║  TRADE LOG (son 50) {' '*(w-22)}║")
            
            show_trades = trade_lines[-log_h:]
            for t in show_trades:
                action = t.get("action", "?")
                sid = t.get("strategy_id", "?")[:20]
                if action == "OPEN":
                    msg = f"🟢 ALIM  {sid:<20s} {t.get('amount_try',0):8.0f} TRY @ {t.get('price',0):.2f}"
                elif action == "CLOSE":
                    p = t.get("pnl_try", 0)
                    wl = "WIN " if t.get("win") else "LOSS"
                    msg = f"🔴 SATIŞ {sid:<20s} {p:+8.1f} TRY {wl}"
                else:
                    msg = f"   {action} {sid}"
                print(f"║  {msg:<{w-4}s} ║")
            
            # Fill remaining space
            remaining = log_h - len(show_trades)
            for _ in range(remaining):
                print(f"║  {' '*(w-4)} ║")
            
            # ═══ FOOTER ═══
            print(clr("B", f"╚{'═'*w}╝"))
            print(clr("d", f"  R:2s │ Ctrl+C exit │ {time.strftime('%H:%M:%S')} │ Loop: {'ACTIVE' if age < 20 else 'STOPPED'} │ Trades this session: {trades - _last_trade_count} new"))
            _last_trade_count = trades
            
        except Exception as e:
            print(clr("r", f"Error: {e}"))
        
        time.sleep(2)

if __name__ == "__main__":
    try: render()
    except KeyboardInterrupt: print(clr("g", "\n✓ Closed"))
