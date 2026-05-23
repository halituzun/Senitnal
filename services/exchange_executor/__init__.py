"""Binance real exchange executor — spot market orders.

⚠️  REAL MONEY — use with extreme caution.

Reads BINANCE_API_KEY + BINANCE_API_SECRET from env.
Only executes if BINANCE_LIVE_TRADING=true.

Constitutional: lives in services/, sentinel core never imports this.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ORDER_LOG = Path("data/trades/live_orders.jsonl")

# Safety limits — REMOVED per user request. Use portfolio allocation instead.
MAX_ORDER_TRY = float("inf")  # No hard limit
MAX_DAILY_VOLUME_TRY = float("inf")  # no hard limit


@dataclass
class OrderResult:
    symbol: str
    side: str
    order_id: str | int
    price: float
    quantity: float
    executed_qty: float
    status: str
    error: str = ""


def _signed_request(endpoint: str, params: dict[str, Any], method: str = "GET") -> dict[str, Any]:
    """Make a signed Binance API request."""
    api_key = os.environ.get("BINANCE_API_KEY", "")
    api_secret = os.environ.get("BINANCE_API_SECRET", "")
    if not api_key or not api_secret:
        raise ValueError("BINANCE_API_KEY and BINANCE_API_SECRET must be set")

    params["timestamp"] = int(time.time() * 1000)
    query = urlencode(params)
    signature = hmac.new(api_secret.encode(), query.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com{endpoint}?{query}&signature={signature}"

    req = Request(url, headers={"X-MBX-APIKEY": api_key, "Accept": "application/json"})
    if method == "POST":
        req.method = "POST"

    with urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())  # type: ignore[no-any-return]


def get_balances() -> dict[str, dict[str, float]]:
    """Get account balances for USDT, BTC, ETH, SOL."""
    try:
        data = _signed_request("/api/v3/account", {})
        balances = {}
        for b in data.get("balances", []):
            asset = b["asset"]
            free = float(b["free"])
            locked = float(b["locked"])
            if asset in ("USDT", "BTC", "ETH", "SOL") and (free > 0 or locked > 0):
                balances[asset] = {"free": free, "locked": locked, "total": free + locked}
        return balances
    except Exception as e:
        return {"error": str(e)}


def get_current_price(symbol: str) -> float:
    """Get current price for a symbol."""
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    req = Request(url, headers={"Accept": "application/json"})
    with urlopen(req, timeout=5) as resp:
        data = json.loads(resp.read())
    return float(data["price"])


def place_market_buy(symbol: str, quote_order_qty: float) -> OrderResult:
    """Place a market buy order (buy with quote currency amount)."""
    if not _is_live():
        return OrderResult(symbol, "BUY", "simulated", 0, 0, 0, "SIMULATED",
                          "BINANCE_LIVE_TRADING not set to true")

    if quote_order_qty > MAX_ORDER_TRY:
        return OrderResult(symbol, "BUY", "", 0, 0, 0, "REJECTED",
                          f"Order {quote_order_qty:.0f} TRY exceeds max {MAX_ORDER_TRY} TRY")

    try:
        price = get_current_price(symbol)
        result = _signed_request("/api/v3/order", {
            "symbol": symbol,
            "side": "BUY",
            "type": "MARKET",
            "quoteOrderQty": round(quote_order_qty, 2),
        }, method="POST")

        order_id = result.get("orderId", 0)
        executed_qty = float(result.get("executedQty", 0))
        status = result.get("status", "UNKNOWN")

        _log_order("BUY", symbol, price, quote_order_qty, executed_qty, order_id, status)
        return OrderResult(symbol, "BUY", order_id, price, quote_order_qty, executed_qty, status)
    except Exception as e:
        _log_order("BUY", symbol, 0, quote_order_qty, 0, "", f"ERROR: {e}")
        return OrderResult(symbol, "BUY", "", 0, 0, 0, "ERROR", str(e))


def place_market_sell(symbol: str, quantity: float) -> OrderResult:
    """Place a market sell order."""
    if not _is_live():
        return OrderResult(symbol, "SELL", "simulated", 0, quantity, 0, "SIMULATED",
                          "BINANCE_LIVE_TRADING not set to true")

    try:
        price = get_current_price(symbol)
        result = _signed_request("/api/v3/order", {
            "symbol": symbol,
            "side": "SELL",
            "type": "MARKET",
            "quantity": round(quantity, 6),
        }, method="POST")

        order_id = result.get("orderId", 0)
        executed_qty = float(result.get("executedQty", 0))
        status = result.get("status", "UNKNOWN")

        _log_order("SELL", symbol, price, quantity, executed_qty, order_id, status)
        return OrderResult(symbol, "SELL", order_id, price, quantity, executed_qty, status)
    except Exception as e:
        _log_order("SELL", symbol, 0, quantity, 0, "", f"ERROR: {e}")
        return OrderResult(symbol, "SELL", "", 0, quantity, 0, "ERROR", str(e))


def _is_live() -> bool:
    return os.environ.get("BINANCE_LIVE_TRADING", "").lower() == "true"


def _log_order(side: str, symbol: str, price: float, amount: float, qty: float, order_id: str | int, status: str) -> None:
    ORDER_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts_ms": int(time.time() * 1000),
        "side": side,
        "symbol": symbol,
        "price": price,
        "amount": amount,
        "quantity": qty,
        "order_id": str(order_id),
        "status": status,
        "live": _is_live(),
    }
    with open(ORDER_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")


__all__ = [
    "OrderResult",
    "get_balances",
    "get_current_price",
    "place_market_buy",
    "place_market_sell",
]
