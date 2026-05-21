"""V11 — Adapter service smoke + boundary tests."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import TYPE_CHECKING

from services.intelligence_adapters.gelal_metrics_adapter import (
    GelAlMetricsConfig,
    get_read_query,
    row_to_observation,
)
from services.intelligence_adapters.taapi_adapter import (
    TaapiConfig,
    has_api_key,
    is_enabled,
    normalize_response_payload,
    redact_secret,
    write_snapshot_jsonl,
)

if TYPE_CHECKING:
    import pytest


class TestTaapiAdapter:
    def test_disabled_without_key(self) -> None:
        cfg = TaapiConfig(enabled=True)
        os.environ.pop("TAAPI_API_KEY", None)
        assert has_api_key(cfg) is False
        assert is_enabled(cfg) is False

    def test_enabled_with_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TAAPI_API_KEY", "secret-token-xyz")
        cfg = TaapiConfig(enabled=True)
        assert has_api_key(cfg) is True
        assert is_enabled(cfg) is True

    def test_secret_redacted(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TAAPI_API_KEY", "abc123secret")
        cfg = TaapiConfig(enabled=True)
        msg = "calling https://api.taapi.io with key=abc123secret"
        red = redact_secret(msg, cfg)
        assert "abc123secret" not in red
        assert "***REDACTED***" in red

    def test_normalize_filters_non_numeric(self) -> None:
        snap = normalize_response_payload(
            snapshot_id="t1",
            symbol_hash="sha:btc",
            timeframe="1h",
            payload={"rsi": 55.0, "macd": 0.5, "label": "trend_up"},
            now_ms=1_000,
            provenance_hash="sha:p",
        )
        assert "rsi" in snap.indicators
        assert "label" not in snap.indicators

    def test_write_snapshot_jsonl(self, tmp_path: Path) -> None:
        cfg = TaapiConfig(enabled=True, spool_path=tmp_path / "spool")
        snap = normalize_response_payload(
            snapshot_id="t-write",
            symbol_hash="sha:btc",
            timeframe="1h",
            payload={"rsi": 50.0},
            now_ms=1_000,
            provenance_hash="sha:p",
        )
        out = write_snapshot_jsonl(config=cfg, snapshot=snap)
        assert out.exists()
        assert out.read_text(encoding="utf-8").strip().startswith("{")


class TestGelAlMetricsAdapter:
    def test_query_is_select_only(self) -> None:
        for family in (
            "depth_snapshots",
            "opportunity_history",
            "live_trade_attempts",
            "scout_signals",
            "latency_metrics",
        ):
            q = get_read_query(family)  # type: ignore[arg-type]
            assert q.strip().upper().startswith("SELECT")
            # no write keywords
            assert not re.search(r"\b(INSERT|UPDATE|DELETE|DROP|ALTER)\b", q, re.IGNORECASE)

    def test_row_to_observation(self) -> None:
        obs = row_to_observation(
            family="depth_snapshots",
            row={
                "symbol_hash": "sha:btc",
                "venue_hash": "sha:venue",
                "sample_count": 50,
                "mean_value": 1.5,
                "p50_value": 1.4,
                "p95_value": 2.0,
                "observed_at_ms": 1_000,
            },
            observation_id="g-1",
            provenance_hash="sha:p",
        )
        assert obs.metric_family == "depth_snapshots"

    def test_config_dataclass(self) -> None:
        cfg = GelAlMetricsConfig(enabled=True)
        assert cfg.enabled is True


class TestCoreBoundary:
    """Sentinel core MUST NOT import services.intelligence_adapters."""

    def test_sentinel_does_not_import_adapter_services(self) -> None:
        for root, _dirs, files in os.walk("sentinel"):
            for f in files:
                if not f.endswith(".py"):
                    continue
                path = Path(root) / f
                src = path.read_text(encoding="utf-8")
                assert "from services.intelligence_adapters" not in src, str(path)
                assert "import services.intelligence_adapters" not in src, str(path)

    def test_intelligence_module_has_no_network_imports(self) -> None:
        pattern = re.compile(
            r"^\s*(import|from)\s+("
            r"ccxt|web3|binance|btcturk|pybit|okx|gate_api|kucoin|huobi|"
            r"bitfinex|kraken|openai|anthropic|langchain|requests|httpx|aiohttp"
            r")\b",
            re.MULTILINE,
        )
        for p in Path("sentinel/intelligence").rglob("*.py"):
            src = p.read_text(encoding="utf-8")
            assert pattern.findall(src) == [], f"forbidden import in {p}"
