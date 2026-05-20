"""MVP feature flag matrix.

Per build plan §18: this module is the **single source of truth** for
runtime capability gating. No call site may override these flags;
they are immutable at the type level (frozen mapping) and the matrix
is closed (extra keys rejected at lookup time).

Constitutional discipline:
    - The flag matrix is constant within a process. Tests that need
      a different posture construct their own `FeatureFlagMatrix`
      and pass it explicitly
    - Boolean values only (no degree-of-permission, no enums). This
      matches the build plan §18 verbatim
    - Lookups go through `get_flag(name)` which raises `KeyError` if
      `name` is not a known flag — this prevents typos from silently
      reading `False`

What this module deliberately does NOT contain:
    - Production flag matrix (deferred; see build plan §18 note)
    - Mutable runtime override
    - Per-call-site flag injection (the matrix is global)
"""

from __future__ import annotations

from collections.abc import Mapping  # noqa: TC003 (runtime annotation)
from types import MappingProxyType

_MVP_RAW: dict[str, bool] = {
    # ---- Execute / live action --------------------------------------------
    "mvp_execute_disabled": True,
    "live_exchange_api_enabled": False,
    "real_market_data_enabled": False,
    # ---- Memory production ------------------------------------------------
    "mvp_verified_disabled": True,
    "memory_writer_auto_verify": False,
    # ---- LLM --------------------------------------------------------------
    "llm_intent_relay_enabled": False,
    "llm_translator_loaded": False,
    # ---- Replay -----------------------------------------------------------
    "replay_engine_enabled": False,
    "replay_session_creation": False,
    # ---- Restore / fork / migration --------------------------------------
    "restore_endpoint_enabled": False,
    "fork_birth_enabled": False,
    "migration_birth_enabled": False,
    # ---- Numerics ---------------------------------------------------------
    "production_numerics_required": False,
    "numerics_runtime_mutation": False,
    # ---- Adapters ---------------------------------------------------------
    "production_adapters_enabled": False,
    "echo_adapter_only": True,
    # ---- Operator surface -------------------------------------------------
    "telegram_control_enabled": False,
    "operator_override_enabled": False,
    # ---- Plasticity -------------------------------------------------------
    "learning_enabled": False,
    "sleep_cycle_enabled": False,
    # ---- Kill switch ------------------------------------------------------
    "kill_switch_active": False,
}

MVP_FEATURE_FLAGS: Mapping[str, bool] = MappingProxyType(dict(_MVP_RAW))


def get_flag(name: str, *, flags: Mapping[str, bool] = MVP_FEATURE_FLAGS) -> bool:
    """Return the value of `name` in `flags`. Raises KeyError if unknown.

    This is the only sanctioned way to read a feature flag at runtime.
    A typo in the flag name fails loudly instead of silently returning
    `False`.
    """
    if name not in flags:
        raise KeyError(f"unknown feature flag: {name!r}")
    return flags[name]


def all_flag_names(*, flags: Mapping[str, bool] = MVP_FEATURE_FLAGS) -> frozenset[str]:
    """Return the closed set of flag names known to the matrix."""
    return frozenset(flags.keys())
