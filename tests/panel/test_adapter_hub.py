"""V14 — Adapter Hub tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sentinel.adapters.trust import TrustBand
from sentinel.intelligence.schemas import SourceFamily
from sentinel.panel.adapter_hub import (
    AdapterHubStatus,
    AdapterSignalStatus,
    build_adapter_hub_status,
)


def _status(
    aid: str,
    family: SourceFamily = SourceFamily.TECHNICAL_INDICATOR,
    trust: TrustBand = TrustBand.HIGH,
    last_seen_ms: int | None = 1_000,
) -> AdapterSignalStatus:
    fresh = last_seen_ms is not None
    healthy = trust not in {TrustBand.REVOKED, TrustBand.QUARANTINED} and fresh
    return AdapterSignalStatus(
        adapter_id=aid,
        source_family=family,
        last_seen_ms=last_seen_ms,
        trust_band=trust,
        is_fresh=fresh,
        is_healthy=healthy,
    )


NOW_MS = 5_000
HORIZON_MS = 10_000  # 10 seconds for tests


class TestBuildAdapterHubStatus:
    def test_all_healthy(self) -> None:
        statuses = [
            _status("a1", last_seen_ms=NOW_MS - 1_000),
            _status("a2", family=SourceFamily.NEWS, last_seen_ms=NOW_MS - 2_000),
        ]
        hub = build_adapter_hub_status(
            hub_id="hub-1",
            captured_at_ms=NOW_MS,
            adapter_statuses=statuses,
            freshness_horizon_ms=HORIZON_MS,
        )
        assert hub.healthy_count == 2
        assert hub.stale_count == 0
        assert not hub.degraded

    def test_stale_adapter_detected(self) -> None:
        statuses = [
            _status("a1", last_seen_ms=NOW_MS - 1_000),
            _status("a2", last_seen_ms=NOW_MS - 20_000),  # stale beyond horizon
        ]
        hub = build_adapter_hub_status(
            hub_id="hub-stale",
            captured_at_ms=NOW_MS,
            adapter_statuses=statuses,
            freshness_horizon_ms=HORIZON_MS,
        )
        assert hub.stale_count == 1
        assert hub.healthy_count == 1
        assert hub.degraded

    def test_revoked_adapter_not_healthy(self) -> None:
        statuses = [
            _status("a1", trust=TrustBand.REVOKED, last_seen_ms=NOW_MS - 100),
        ]
        hub = build_adapter_hub_status(
            hub_id="hub-rev",
            captured_at_ms=NOW_MS,
            adapter_statuses=statuses,
            freshness_horizon_ms=HORIZON_MS,
        )
        assert hub.healthy_count == 0
        assert hub.degraded

    def test_quarantined_adapter_not_healthy(self) -> None:
        statuses = [
            _status("a1", trust=TrustBand.QUARANTINED, last_seen_ms=NOW_MS - 100),
        ]
        hub = build_adapter_hub_status(
            hub_id="hub-quar",
            captured_at_ms=NOW_MS,
            adapter_statuses=statuses,
            freshness_horizon_ms=HORIZON_MS,
        )
        assert hub.healthy_count == 0

    def test_none_last_seen_is_stale(self) -> None:
        statuses = [_status("a1", last_seen_ms=None)]
        hub = build_adapter_hub_status(
            hub_id="hub-none",
            captured_at_ms=NOW_MS,
            adapter_statuses=statuses,
            freshness_horizon_ms=HORIZON_MS,
        )
        assert hub.stale_count == 1
        assert hub.healthy_count == 0

    def test_empty_hub(self) -> None:
        hub = build_adapter_hub_status(
            hub_id="hub-empty",
            captured_at_ms=NOW_MS,
            adapter_statuses=[],
        )
        assert hub.healthy_count == 0
        assert hub.stale_count == 0
        assert not hub.degraded

    def test_counts_bounded_validator(self) -> None:
        with pytest.raises(ValidationError):
            AdapterHubStatus(
                hub_id="bad",
                captured_at_ms=0,
                adapters=(),
                healthy_count=5,
                stale_count=5,
                degraded=False,
            )

    def test_default_freshness_horizon(self) -> None:
        statuses = [_status("a1", last_seen_ms=NOW_MS - 100)]
        hub = build_adapter_hub_status(
            hub_id="hub-def",
            captured_at_ms=NOW_MS,
            adapter_statuses=statuses,
        )
        assert hub.healthy_count == 1
