#!/usr/bin/env python3
"""Terminal Trading Dashboard — mtop-style live monitor.

Reads snapshot.json and displays real-time trading status.
Auto-refreshes every 2 seconds. No external deps needed.
"""

import json
import os
import sys
import time
from pathlib import Path

SNAPSHOT = Path("panel/api/src/mock/snapshot.json")
PORTFOLIO = Path("data/paper_trades/portfolio.json")
TRADES = Path("data/paper_trades/trades.jsonl")

COLORS = {
    "green": "\033[32m", "red": "\033[31m", "yellow": "\033[33m",
    "blue": "\033[34m", "cyan": "\033[36m", "magenta": "\033[35m",
    "white": "\033[37m", "bold": "\033[1m", "dim": "\033[2m",
    "reset": "\033[0m", "clear": "\033[2J\033[H",
}

def c(color: str, text: str) -> str:
    return f"{COLORS.get(color, '')}{text}{COLORS['reset']}"

def bar(value: float, width: int = 20, max_val: float = 1.0) -> str:
    filled = int(min(value, max_val) / max_val * width)
    if value > 0.6: color = "green"
    elif value > 0.3: color = "yellow"
    else: color = "red"
    return c(color, "█" * filled + "░" * (width - filled))

def format_try(v: float) -> str:
    if abs(v) >= 1000: return f"{v:+.0f}"
    return f"{v:+.1f}"

def render():
    while True:
        try:
            # Read snapshot
            if not SNAPSHOT.exists():
                print(c("red", "⏳ Snapshot bekleniyor..."), end="\r")
                time.sleep(2)
                continue

            with open(SNAPSHOT) as f: snap = json.load(f)
            ls = snap.get("learning_state", {})
            strategies = snap.get("strategies", [])
            events = snap.get("ledger_events", [])

            # Portfolio
            pf_data = {"balance_try": 10000, "closed_pnl_try": 0, "total_trades": 0, "winning_trades": 0, "positions": {}}
            if PORTFOLIO.exists():
                with open(PORTFOLIO) as f: pf_data = json.load(f)

            # Recent trades
            recent_trades = []
            if TRADES.exists():
                lines = open(TRADES).readlines()
                for line in lines[-10:]:
                    if line.strip():
                        recent_trades.append(json.loads(line))

            # Clear screen
            sys.stdout.write(COLORS["clear"])
            
            # ═══════════ HEADER ═══════════
            age = int(time.time() - SNAPSHOT.stat().st_mtime)
            status_color = "green" if age < 10 else "yellow" if age < 30 else "red"
            cycle = ls.get("cycle", 0)
            alpha = ls.get("adaptive_alpha", 0)
            acc = ls.get("accuracy", 0)
            
            print(c("bold", "╔══════════════════════════════════════════════════════════╗"))
            print(c("bold", f"║  SENTINEL TRADING DASHBOARD                              ║"))
            print(c("bold", "╠══════════════════════════════════════════════════════════╣"))
            print(f"║  Cycle: {cycle:<6}  │  α: {alpha:.3f}  │  Accuracy: {acc:.0%}  │  {c(status_color, f'Live ({age}s)')}   ║")
            
            # ═══════════ PNL ═══════════
            pnl = pf_data.get("closed_pnl_try", 0)
            trades = pf_data.get("total_trades", 0)
            wins = pf_data.get("winning_trades", 0)
            wr = wins / max(1, trades)
            pos_count = len(pf_data.get("positions", {}))
            
            pnl_color = "green" if pnl > 0 else "red" if pnl < 0 else "yellow"
            print(c("bold", "╠══════════════════════════════════════════════════════════╣"))
            print(f"║  PnL: {c(pnl_color, format_try(pnl)+' TRY'):<30}  Trades: {trades:<5}  WR: {wr:.0%}  Pos: {pos_count}    ║")
            
            # ═══════════ STRATEGIES ═══════════
            print(c("bold", "╠══════════════════════════════════════════════════════════╣"))
            print(f"║  STRATEJİ            Edge      Risk      Quality   Durum ║")
            print(c("bold", "╠══════════════════════════════════════════════════════════╣"))
            
            for st in strategies:
                name = st["name"][:18]
                edge = st.get("current_edge_score", 0)
                risk = st.get("current_risk_score", 0)
                q = st.get("strategy_quality", 0)
                state = st.get("lifecycle_state", "?")
                
                edge_bar = bar(edge, 10)
                risk_str = c("green", f"{risk:.2f}") if risk < 0.3 else c("yellow", f"{risk:.2f}") if risk < 0.6 else c("red", f"{risk:.2f}")
                q_color = "green" if q > 0.5 else "yellow" if q > 0.3 else "red"
                state_color = "green" if "ACTIVE" in state or "LIMITED" in state else "yellow" if "PAUSED" in state else "red"
                
                has_pos = "🔒" if any(st["strategy_id"] in k for k in pf_data.get("positions", {})) else "  "
                print(f"║  {name:<18s}  {edge_bar} {edge:.2f}  {risk_str}  {c(q_color, f'{q:.2f}')}     {c(state_color, state):<18s} {has_pos} ║")
            
            # ═══════════ POSITIONS ═══════════
            positions = pf_data.get("positions", {})
            if positions:
                print(c("bold", "╠══════════════════════════════════════════════════════════╣"))
                print(f"║  AÇIK POZİSYONLAR                                       ║")
                for sid, pd in list(positions.items())[:6]:
                    entry = pd.get("entry_price", 0)
                    amt = pd.get("amount_try", 0)
                    name = sid[:20]
                    print(f"║  {name:<20s}  {amt:6.0f} TRY @ {entry:<10.0f}               ║")
            
            # ═══════════ RECENT EVENTS ═══════════
            trade_events = [e for e in events[-8:] if "TRADE" in e.get("event_type", "") or "EXIT" in e.get("event_type", "")]
            if trade_events:
                print(c("bold", "╠══════════════════════════════════════════════════════════╣"))
                print(f"║  SON İŞLEMLER                                           ║")
                for e in trade_events[-5:]:
                    msg = e.get("message", "")[:55]
                    ev_type = e.get("event_type", "")
                    icon = "🟢" if "ENTRY" in msg or "ALIM" in msg else "🔴" if "EXIT" in msg or "SATI" in msg else "📄"
                    print(f"║  {icon} {msg:<52s} ║")
            
            # ═══════════ FOOTER ═══════════
            print(c("bold", "╚══════════════════════════════════════════════════════════╝"))
            print(c("dim", f"  Refresh: 2s | Ctrl+C to exit | {time.strftime('%H:%M:%S')}"))
            
        except Exception as e:
            print(c("red", f"Render error: {e}"))
        
        time.sleep(2)

if __name__ == "__main__":
    try:
        render()
    except KeyboardInterrupt:
        print(c("green", "\n✓ Dashboard closed"))
