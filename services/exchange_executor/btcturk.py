"""BTCTürk exchange executor."""
from __future__ import annotations
import base64, hashlib, hmac, json, os, socket, time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

# Force IPv4 for BTCTürk (their whitelist uses IPv4)
_socket_orig = socket.getaddrinfo
def _force_ipv4(host, port, family=0, *args, **kwargs):
    return _socket_orig(host, port, socket.AF_INET, *args, **kwargs)

def _signed_request(endpoint: str, params: dict = None, method: str = "GET") -> dict:
    api_key = os.environ.get("BTCTURK_PUBLIC_KEY", "")
    api_secret_b64 = os.environ.get("BTCTURK_PRIVATE_KEY", "")
    if not api_key or not api_secret_b64:
        raise ValueError("BTCTURK keys not set")
    
    socket.getaddrinfo = _force_ipv4
    try:
        params = params or {}
        nonce = str(int(time.time()) * 1000)
        msg = f"{api_key}{nonce}"
        secret_bytes = base64.b64decode(api_secret_b64)
        sig_bytes = hmac.new(secret_bytes, msg.encode(), hashlib.sha256).digest()
        sig = base64.b64encode(sig_bytes).decode()
        url = f"https://api.btcturk.com{endpoint}"
        headers = {
            "X-PCK": api_key,
            "X-Stamp": nonce,
            "X-Signature": sig,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0",
        }
        if method == "POST":
            body = json.dumps(params).encode() if params else None
        else:
            body = None
            if params:
                url += "?" + urlencode(params)
        req = Request(url, data=body, headers=headers)
        if method == "POST":
            req.method = "POST"
        with urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    finally:
        socket.getaddrinfo = _socket_orig

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
