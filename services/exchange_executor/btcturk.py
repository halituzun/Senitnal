"""BTCTürk exchange executor."""
from __future__ import annotations
import hashlib, hmac, json, os, time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

def _signed_request(endpoint: str, params: dict = None, method: str = "GET") -> dict:
    api_key = os.environ.get("BTCTURK_PUBLIC_KEY", "")
    api_secret = os.environ.get("BTCTURK_PRIVATE_KEY", "")
    if not api_key or not api_secret:
        raise ValueError("BTCTURK keys not set")
    params = params or {}
    params["nonce"] = int(time.time() * 1000)
    body = urlencode(params)
    msg = f"{api_key}{params['nonce']}"
    sig = hmac.new(api_secret.encode(), msg.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.btcturk.com{endpoint}?{body}" if method == "GET" else f"https://api.btcturk.com{endpoint}"
    headers = {"X-PCK": api_key, "X-Stamp": str(params["nonce"]), "X-Signature": sig, "Accept": "application/json"}
    if method == "POST": headers["Content-Type"] = "application/x-www-form-urlencoded"
    req = Request(url, data=body.encode() if method == "POST" else None, headers=headers)
    if method == "POST": req.method = "POST"
    with urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())

def get_balances() -> dict:
    try:
        data = _signed_request("/api/v1/users/balances")
        result = {}
        for b in data.get("data", []):
            asset = b["asset"]
            free = float(b["free"])
            locked = float(b["locked"])
            if free > 0 or locked > 0:
                result[asset] = {"free": free, "locked": locked, "total": free + locked}
        return result
    except Exception as e:
        return {"error": str(e)}

def place_market_order(symbol: str, side: str, quantity: float = 0, quote_amount: float = 0) -> dict:
    params = {"symbol": symbol, "side": side.upper(), "orderMethod": "market"}
    if quote_amount > 0: params["quoteAmount"] = str(round(quote_amount, 2))
    if quantity > 0: params["quantity"] = str(round(quantity, 8))
    try:
        return _signed_request("/api/v1/order", params, "POST")
    except Exception as e:
        return {"error": str(e)}

__all__ = ["get_balances", "place_market_order"]
