#!/usr/bin/env python3
"""Quick Scalper — fast Binance signal trading on BTCTürk.

Strategy: Buy dips (-2% 24h), sell rips (+1.5% from entry).
No fusion, no TAAPI, no complex pipeline. Pure price action.
"""

import json, os, time
from pathlib import Path

# Direct imports
import sys; sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from services.intelligence_adapters.binance_adapter import fetch_prices, fetch_24h_tickers
from services.paper_trading import PaperPortfolio
from services.exchange_executor.btcturk import place_market_order as btcturk_order

SYMBOLS = {
    "btc-scalp": "BTCUSDT", "eth-scalp": "ETHUSDT", "sol-scalp": "SOLUSDT",
    "bnb-scalp": "BNBUSDT", "ada-scalp": "ADAUSDT", "doge-scalp": "DOGEUSDT",
    "avax-scalp": "AVAXUSDT", "link-scalp": "LINKUSDT",
}

PORTFOLIO = PaperPortfolio.load()
POSITIONS = PORTFOLIO.positions
LIVE_TRADING = os.environ.get("BINANCE_LIVE_TRADING", "").lower() == "true"
CYCLE = 0

print("╔══════════════════════════════════════╗")
print("║     QUICK SCALPER v1                 ║")
print(f"║     {len(SYMBOLS)} pairs  │  {LIVE_TRADING and 'LIVE BTCTÜRK' or 'PAPER'}       ║")
print("╚══════════════════════════════════════╝")

while True:
    CYCLE += 1
    try:
        prices = fetch_prices()
        tickers = fetch_24h_tickers()
        
        for sid, symbol in SYMBOLS.items():
            price = prices.get(symbol, 0)
            ticker = tickers.get(symbol, {})
            if not price or not ticker: continue
            
            chg = float(ticker.get("priceChangePercent", 0))
            high = float(ticker.get("highPrice", 0))
            low = float(ticker.get("lowPrice", 0))
            
            # ── ENTRY: buy the dip ──
            if sid not in POSITIONS and chg < -2.0:
                amt = min(150, max(50, PORTFOLIO.balance_try * 0.08))
                if LIVE_TRADING:
                    try:
                        bt_symbol = symbol.replace("USDT", "TRY")
                        btcturk_order(bt_symbol, "BUY", quote_amount=amt)
                    except: pass
                POSITIONS[sid] = PORTFOLIO.open_position(sid, symbol, price, amt)
                print(f"  🟢 {CYCLE:04d} BUY  {symbol:<10s} {amt:5.0f} TRY @ {price:.2f}  (Δ24h={chg:+.1f}%)")
            
            # ── EXIT: take profit or cut loss ──
            elif sid in POSITIONS:
                pos = POSITIONS[sid]
                pnl_pct = (price - pos.entry_price) / pos.entry_price if pos.entry_price > 0 else 0
                
                if pnl_pct > 0.015:  # +1.5% profit
                    if LIVE_TRADING:
                        try:
                            bt_symbol = symbol.replace("USDT", "TRY")
                            btcturk_order(bt_symbol, "SELL", quantity=pos.quantity)
                        except: pass
                    result = PORTFOLIO.close_position(sid, price)
                    pnl = result['pnl_try'] if result else 0
                    POSITIONS.pop(sid, None)
                    print(f"  🟢 {CYCLE:04d} SELL {symbol:<10s} {pnl:+6.1f} TRY  WIN +{pnl_pct*100:.1f}%")
                
                elif pnl_pct < -0.015:  # -1.5% stop
                    if LIVE_TRADING:
                        try:
                            bt_symbol = symbol.replace("USDT", "TRY")
                            btcturk_order(bt_symbol, "SELL", quantity=pos.quantity)
                        except: pass
                    result = PORTFOLIO.close_position(sid, price)
                    pnl = result['pnl_try'] if result else 0
                    POSITIONS.pop(sid, None)
                    print(f"  🔴 {CYCLE:04d} SELL {symbol:<10s} {pnl:+6.1f} TRY  LOSS {pnl_pct*100:.1f}%")
        
        PORTFOLIO.save()
        
        # Status line
        pos_list = [f"{s.split('-')[0]}" for s in POSITIONS]
        pnl_str = f"{PORTFOLIO.closed_pnl_try:+.1f}"
        print(f"  [{CYCLE:04d}] PnL={pnl_str} TRY | {PORTFOLIO.total_trades}t | Pos: {len(POSITIONS)} | {' '.join(pos_list) if pos_list else 'none'}")
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    time.sleep(10)  # Check every 10 seconds
