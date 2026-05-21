"""TAAPI technical indicator adapter service.

External limb; network allowed.  Reads TAAPI_API_KEY from environment.
Never logs the secret.  Normalizes TAAPI responses into
``TechnicalIndicatorSnapshot`` and spools to local JSONL.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from sentinel.intelligence.schemas import TechnicalIndicatorSnapshot


@dataclass(frozen=True, slots=True)
class TaapiConfig:
    """TAAPI adapter configuration."""

    enabled: bool
    api_key_env: str = "TAAPI_API_KEY"
    symbols: tuple[str, ...] = field(default_factory=tuple)
    timeframes: tuple[str, ...] = field(
        default_factory=lambda: ("1m", "5m", "15m", "1h", "4h", "1d")
    )
    indicators: tuple[str, ...] = field(
        default_factory=lambda: (
            "rsi",
            "macd",
            "adx",
            "atr",
            "bbands",
            "supertrend",
            "vwap",
            "stochrsi",
            "ichimoku",
            "mfi",
            "obv",
        )
    )
    spool_path: Path = Path("data/intelligence/taapi_snapshots")
    base_url: str = "https://api.taapi.io"


def has_api_key(config: TaapiConfig) -> bool:
    """Return True if the API key env var is set and non-empty."""
    value = os.environ.get(config.api_key_env, "")
    return bool(value)


def is_enabled(config: TaapiConfig) -> bool:
    """Adapter is enabled only when config + secret are both present."""
    return config.enabled and has_api_key(config)


def redact_secret(message: str, config: TaapiConfig) -> str:
    """Return message with the API key value redacted if present."""
    value = os.environ.get(config.api_key_env, "")
    if not value:
        return message
    return message.replace(value, "***REDACTED***")


def normalize_response_payload(
    *,
    snapshot_id: str,
    symbol_hash: str,
    timeframe: str,
    payload: dict[str, object],
    now_ms: int,
    provenance_hash: str,
    venue_hash: str | None = None,
) -> TechnicalIndicatorSnapshot:
    """Normalize a TAAPI response payload into a TechnicalIndicatorSnapshot.

    The caller is responsible for fetching the payload over the network
    (this function performs no I/O).  The payload contains indicator
    name -> float pairs only; non-numeric values are dropped.
    """
    indicators: dict[str, float] = {}
    for k, v in payload.items():
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            indicators[str(k)] = float(v)
    return TechnicalIndicatorSnapshot(
        snapshot_id=snapshot_id,
        provider="taapi",
        symbol_hash=symbol_hash,
        venue_hash=venue_hash,
        timeframe=timeframe,
        indicators=indicators,
        confidence=0.7 if indicators else 0.0,
        observed_at_ms=now_ms,
        provenance_hash=provenance_hash,
    )


def write_snapshot_jsonl(
    *,
    config: TaapiConfig,
    snapshot: TechnicalIndicatorSnapshot,
) -> Path:
    """Append a snapshot to the spool path; return the file path."""
    config.spool_path.mkdir(parents=True, exist_ok=True)
    out = config.spool_path / f"{snapshot.snapshot_id}.jsonl"
    out.write_text(snapshot.model_dump_json() + "\n", encoding="utf-8")
    return out


def fetch_indicator(
    *,
    config: TaapiConfig,
    indicator: str,
    symbol: str,
    timeframe: str = "4h",
) -> dict[str, Any]:
    """Fetch one indicator from TAAPI API.

    Returns the raw JSON response.  Raises on HTTP/network errors.
    API key from env var is NOT logged — redact_secret() is available.
    """
    api_key = os.environ.get(config.api_key_env, "")
    if not api_key:
        raise ValueError(f"${config.api_key_env} is not set")

    url = (
        f"{config.base_url}/{indicator}"
        f"?secret={api_key}"
        f"&exchange=binance"
        f"&symbol={symbol}"
        f"&interval={timeframe}"
    )
    req = Request(url, headers={"Accept": "application/json"})
    with urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())  # type: ignore[no-any-return]


def fetch_indicators_batch(
    *,
    config: TaapiConfig,
    symbol: str,
    timeframe: str = "4h",
) -> dict[str, Any]:
    """Fetch the 'bulk' endpoint — multiple indicators in one request.

    TAAPI bulk endpoint: POST /bulk with JSON body of queries.
    Much more efficient than individual calls.
    """
    api_key = os.environ.get(config.api_key_env, "")
    if not api_key:
        raise ValueError(f"${config.api_key_env} is not set")

    queries = [
        {
            "indicator": ind,
            "exchange": "binance",
            "symbol": symbol,
            "interval": timeframe,
        }
        for ind in config.indicators
    ]

    body = json.dumps({"secret": api_key, "construct": {"queries": queries}}).encode()
    req = Request(
        f"{config.base_url}/bulk",
        data=body,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    with urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())  # type: ignore[no-any-return]


def fetch_and_normalize(
    *,
    config: TaapiConfig,
    symbol: str,
    symbol_hash: str,
    timeframe: str = "4h",
) -> TechnicalIndicatorSnapshot | None:
    """Fetch TAAPI indicators and return normalized snapshot. Returns None on failure."""
    if not is_enabled(config):
        return None

    now_ms = int(time.time() * 1000)
    try:
        result = fetch_indicators_batch(
            config=config, symbol=symbol, timeframe=timeframe
        )
    except Exception:
        # Fallback: try individual RSI fetch
        try:
            payload = fetch_indicator(
                config=config, indicator="rsi", symbol=symbol, timeframe=timeframe
            )
            result = {"data": [payload]}
        except Exception:
            return None

    # Extract indicator values from bulk response
    data = result.get("data", [])
    payload: dict[str, object] = {}
    for item in data:
        if isinstance(item, dict):
            for k, v in item.items():
                if k not in ("exchange", "symbol", "interval", "secret", "backtrack", "chart", "period"):
                    payload[k] = v

    if not payload:
        return None

    return normalize_response_payload(
        snapshot_id=f"taapi-{symbol.lower()}-{timeframe}-{now_ms}",
        symbol_hash=symbol_hash,
        timeframe=timeframe,
        payload=payload,
        now_ms=now_ms,
        provenance_hash=f"taapi-bulk-{symbol.lower()}-{now_ms}",
    )


__all__ = [
    "TaapiConfig",
    "has_api_key",
    "is_enabled",
    "normalize_response_payload",
    "redact_secret",
    "write_snapshot_jsonl",
]
