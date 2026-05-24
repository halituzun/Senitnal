"""BinanceTR exchange executor — same as Binance but api.binance.tr"""
from __future__ import annotations
import hashlib, hmac, json, os, time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = "https://api.binance.tr"

def _signed(endpoint: str, params: dict = None, method: str = "GET") -> dict:
    key = os.environ.get("BINANCETR_API_KEY", os.environ.get("BINANCE_API_KEY", ""))
    secret = os.environ.get("BINANCETR_API_SECRET", os.environ.get("BINANCE_API_SECRET", ""))
    if not key or not secret: raise ValueError("BinanceTR keys not set")
    params = params or {}
    params["timestamp"] = int(time.time() * 1000)
    query = urlencode(params)
    sig = hmac.new(secret.encode(), query.encode(), hashlib.sha256).hexdigest()
    url = f"{BASE}{endpoint}?{query}&signature={sig}"
    req = Request(url, headers={"X-MBX-APIKEY": key, "Accept": "application/json"})
    if method == "POST": req.method = "POST"
    with urlopen(req, timeout=15) as r: return json.loads(r.read())

def get_balances() -> dict:
    try:
        data = _signed("/open/v1/account/spot")
        result = {}
        for b in data.get("balances", []):
            free = float(b.get("free", 0))
            locked = float(b.get("locked", 0))
            if free > 0 or locked > 0:
                result[b["asset"]] = {"free": free, "locked": locked, "total": free + locked}
        return result
    except Exception as e:
        return {"error": str(e)}

def place_order(symbol: str, side: str, quote_amount: float = 0, quantity: float = 0) -> dict:
    params = {"symbol": symbol, "side": side.upper(), "type": "MARKET"}
    if quote_amount > 0: params["quoteOrderQty"] = str(round(quote_amount, 2))
    if quantity > 0: params["quantity"] = str(round(quantity, 6))
    try:
        return _signed("/open/v1/orders", params, "POST")
    except Exception as e:
        return {"error": str(e)}

__all__ = ["get_balances", "place_order"]
