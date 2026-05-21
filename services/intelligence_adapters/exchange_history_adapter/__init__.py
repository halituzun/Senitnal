"""V11 — exchange_history_adapter (skeleton).

External limb; network allowed.  Normalizes raw data into Sentinel-facing
snapshots.  Concrete network client implementation is deferred; the
interface and config types are present so the boundary is verifiable.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AdapterConfig:
    """Generic adapter configuration."""

    enabled: bool
    api_key_env: str = ""
    spool_subdir: str = "exchange_history_adapter"


def is_configured(config: AdapterConfig) -> bool:
    """Return True iff the adapter is enabled and (if needed) keyed."""
    if not config.enabled:
        return False
    if config.api_key_env:
        import os

        return bool(os.environ.get(config.api_key_env, ""))
    return True


__all__ = ["AdapterConfig", "is_configured"]
