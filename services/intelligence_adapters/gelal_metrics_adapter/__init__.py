"""Gel.Al metrics read adapter.

External limb; read-only access to Gel.Al's metrics tables.  This
service never writes to Gel.Al's DB, never writes to
Redis ``orders.pending``, and never mutates config or kill-switch.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from sentinel.intelligence.schemas import GelAlMetricsObservation

GelAlMetricFamily = Literal[
    "depth_snapshots",
    "opportunity_history",
    "live_trade_attempts",
    "scout_signals",
    "latency_metrics",
]


@dataclass(frozen=True, slots=True)
class GelAlMetricsConfig:
    """Gel.Al metrics adapter configuration (read-only)."""

    enabled: bool
    dsn_env: str = "GELAL_METRICS_DSN"
    read_timeout_ms: int = 5_000


_READ_ONLY_QUERIES: dict[GelAlMetricFamily, str] = {
    "depth_snapshots": (
        "SELECT symbol_hash, venue_hash, sample_count, mean_value, p50_value, p95_value, observed_at_ms "
        "FROM metrics.depth_snapshots WHERE observed_at_ms >= %(since_ms)s"
    ),
    "opportunity_history": (
        "SELECT symbol_hash, venue_hash, sample_count, mean_value, p50_value, p95_value, observed_at_ms "
        "FROM metrics.opportunity_history WHERE observed_at_ms >= %(since_ms)s"
    ),
    "live_trade_attempts": (
        "SELECT symbol_hash, venue_hash, sample_count, mean_value, p50_value, p95_value, observed_at_ms "
        "FROM metrics.live_trade_attempts WHERE observed_at_ms >= %(since_ms)s"
    ),
    "scout_signals": (
        "SELECT symbol_hash, venue_hash, sample_count, mean_value, p50_value, p95_value, observed_at_ms "
        "FROM metrics.btcturk_alt_try_scout_signals WHERE observed_at_ms >= %(since_ms)s"
    ),
    "latency_metrics": (
        "SELECT symbol_hash, venue_hash, sample_count, mean_value, p50_value, p95_value, observed_at_ms "
        "FROM metrics.latency_metrics WHERE observed_at_ms >= %(since_ms)s"
    ),
}


def get_read_query(family: GelAlMetricFamily) -> str:
    """Return the parameterised read-only SQL for a metric family."""
    return _READ_ONLY_QUERIES[family]


def row_to_observation(
    *,
    family: GelAlMetricFamily,
    row: dict[str, object],
    observation_id: str,
    provenance_hash: str,
) -> GelAlMetricsObservation:
    """Convert one read-only DB row into a GelAlMetricsObservation."""
    return GelAlMetricsObservation(
        observation_id=observation_id,
        metric_family=family,
        symbol_hash=str(row["symbol_hash"]),
        venue_hash=str(row["venue_hash"]),
        sample_count=int(row["sample_count"]),
        mean_value=float(row["mean_value"]),
        p50_value=float(row["p50_value"]),
        p95_value=float(row["p95_value"]),
        confidence=0.8,
        observed_at_ms=int(row["observed_at_ms"]),
        provenance_hash=provenance_hash,
    )


__all__ = [
    "GelAlMetricFamily",
    "GelAlMetricsConfig",
    "get_read_query",
    "row_to_observation",
]
