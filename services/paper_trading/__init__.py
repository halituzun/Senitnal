"""Paper trading engine — simulated trading with real Binance prices.

Tracks virtual portfolio, executes paper trades based on guard decisions.
Uses Binance live prices for realistic entry/exit. Constitutional:
runs in services/, not sentinel core.

Portfolio starts with 10,000 TRY virtual balance.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

TRADE_LOG = Path("data/paper_trades/trades.jsonl")
STATE_FILE = Path("data/paper_trades/portfolio.json")


@dataclass
class Position:
    strategy_id: str
    symbol: str
    entry_price: float
    amount_try: float
    quantity: float
    entry_ms: int = field(default_factory=lambda: int(time.time() * 1000))


@dataclass
class PaperPortfolio:
    balance_try: float = 10_000.0
    initial_balance: float = 10_000.0
    positions: dict[str, Position] = field(default_factory=dict)
    closed_pnl_try: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0

    def open_position(self, strategy_id: str, symbol: str, price: float, amount_try: float) -> Position | None:
        """Open a new position. Returns None if insufficient balance."""
        if amount_try > self.balance_try or amount_try <= 0:
            return None
        self.balance_try -= amount_try
        quantity = amount_try / price if price > 0 else 0
        pos = Position(strategy_id, symbol, price, amount_try, quantity)
        self.positions[strategy_id] = pos
        self._log_trade("OPEN", strategy_id, symbol, price, amount_try, quantity)
        return pos

    def close_position(self, strategy_id: str, current_price: float) -> dict[str, Any] | None:
        """Close a position and return PnL. Returns None if no position."""
        if strategy_id not in self.positions:
            return None
        pos = self.positions.pop(strategy_id)
        exit_value = pos.quantity * current_price
        pnl = exit_value - pos.amount_try
        self.balance_try += exit_value
        self.closed_pnl_try += pnl
        self.total_trades += 1
        if pnl > 0:
            self.winning_trades += 1

        result = {
            "strategy_id": strategy_id,
            "symbol": pos.symbol,
            "entry_price": pos.entry_price,
            "exit_price": current_price,
            "amount_try": pos.amount_try,
            "pnl_try": round(pnl, 2),
            "pnl_pct": round(pnl / pos.amount_try * 100, 2) if pos.amount_try > 0 else 0,
            "held_ms": int(time.time() * 1000) - pos.entry_ms,
            "win": pnl > 0,
        }
        self._log_trade("CLOSE", strategy_id, pos.symbol, current_price, pos.amount_try, pos.quantity, result)
        return result

    def total_value(self, prices: dict[str, float]) -> float:
        """Current total portfolio value (balance + open positions)."""
        value = self.balance_try
        for pos in self.positions.values():
            sym = pos.symbol
            if sym in prices:
                value += pos.quantity * prices[sym]
        return round(value, 2)

    def total_pnl(self, prices: dict[str, float]) -> float:
        """Total PnL since start."""
        return round(self.total_value(prices) - self.initial_balance, 2)

    def win_rate(self) -> float:
        return round(self.winning_trades / max(1, self.total_trades), 3)

    def _log_trade(self, action: str, strategy_id: str, symbol: str, price: float, amount: float, qty: float, extra: dict[str, Any] | None = None) -> None:
        TRADE_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "ts_ms": int(time.time() * 1000),
            "action": action,
            "strategy_id": strategy_id,
            "symbol": symbol,
            "price": price,
            "amount_try": amount,
            "quantity": qty,
            "balance_try": self.balance_try,
        }
        if extra:
            entry.update(extra)
        with open(TRADE_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def save(self) -> None:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "balance_try": self.balance_try,
            "initial_balance": self.initial_balance,
            "closed_pnl_try": self.closed_pnl_try,
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "positions": {k: {"strategy_id": v.strategy_id, "symbol": v.symbol, "entry_price": v.entry_price, "amount_try": v.amount_try, "quantity": v.quantity, "entry_ms": v.entry_ms} for k, v in self.positions.items()},
        }
        with open(STATE_FILE, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls) -> PaperPortfolio:
        if not STATE_FILE.exists():
            return cls()
        with open(STATE_FILE) as f:
            data = json.load(f)
        p = cls(
            balance_try=data["balance_try"],
            initial_balance=data["initial_balance"],
            closed_pnl_try=data["closed_pnl_try"],
            total_trades=data["total_trades"],
            winning_trades=data["winning_trades"],
        )
        for sid, pd in data.get("positions", {}).items():
            p.positions[sid] = Position(pd["strategy_id"], pd["symbol"], pd["entry_price"], pd["amount_try"], pd["quantity"], pd["entry_ms"])
        return p


def run_paper_trade(
    portfolio: PaperPortfolio,
    signal: dict[str, Any],
    current_prices: dict[str, float],
) -> dict[str, Any] | None:
    """Execute a paper trade based on a guard-approved signal.

    Signal format: {strategy_id, symbol, side, amount_try, edge_score}
    Returns trade result or None if not executed.
    """
    sid = signal.get("strategy_id", "")
    symbol = signal.get("symbol", "")
    side = signal.get("side", "BUY")
    amount = signal.get("amount_try", 0)
    price = current_prices.get(symbol, 0)

    if not price or not amount:
        return None

    if side == "BUY":
        result = portfolio.open_position(sid, symbol, price, amount)
        if result:
            return {"action": "BUY", "strategy_id": sid, "price": price, "amount": amount}
    elif side == "SELL":
        result = portfolio.close_position(sid, price)
        return result

    return None


__all__ = ["PaperPortfolio", "Position", "run_paper_trade"]
