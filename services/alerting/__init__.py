"""Alerting service — critical event notifications.

Logs to JSONL file. Optional Telegram/Discord if tokens configured.
Critical events: KILL_SWITCH, large PnL changes, guard blocks, strategy pauses.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

ALERT_LOG = Path("data/alerts/events.jsonl")


def send_alert(
    level: str,  # INFO, WARN, CRITICAL
    component: str,
    message: str,
    data: dict[str, Any] | None = None,
) -> None:
    """Log alert to file and optionally send to Telegram."""
    ALERT_LOG.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "ts_ms": int(time.time() * 1000),
        "level": level,
        "component": component,
        "message": message,
        "data": data or {},
    }
    with open(ALERT_LOG, "a") as f:
        f.write(json.dumps(event) + "\n")

    # Telegram notification for CRITICAL events
    if level == "CRITICAL":
        _notify_telegram(f"[{level}] {component}: {message}")


def _notify_telegram(text: str) -> None:
    """Send Telegram message if configured."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        return
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        body = json.dumps({"chat_id": chat_id, "text": text[:500], "parse_mode": "HTML"}).encode()
        req = Request(url, data=body, headers={"Content-Type": "application/json"})
        urlopen(req, timeout=5)
    except Exception:
        pass


def alert_kill_switch(reason: str) -> None:
    send_alert("CRITICAL", "kill-switch", reason)


def alert_guard_block(strategy_id: str, reason: str) -> None:
    send_alert("WARN", "execution-guard", f"{strategy_id}: {reason}", {"strategy_id": strategy_id})


def alert_strategy_paused(strategy_id: str, quality: float) -> None:
    send_alert("WARN", "auto-trainer", f"{strategy_id} paused (quality={quality:.2f})",
                {"strategy_id": strategy_id, "quality": quality})


def alert_large_pnl(strategy_id: str, pnl: float) -> None:
    level = "CRITICAL" if abs(pnl) > 50 else "WARN"
    send_alert(level, "pnl", f"{strategy_id}: PnL={pnl:+.1f} TRY",
                {"strategy_id": strategy_id, "pnl": pnl})


__all__ = [
    "alert_guard_block",
    "alert_kill_switch",
    "alert_large_pnl",
    "alert_strategy_paused",
    "send_alert",
]
