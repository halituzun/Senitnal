"""Tests for the MVP feature flag matrix."""

from __future__ import annotations

import pytest
from sentinel.runtime.feature_flags import (
    MVP_FEATURE_FLAGS,
    all_flag_names,
    get_flag,
)


class TestMatrixShape:
    def test_matrix_is_mapping(self) -> None:
        from collections.abc import Mapping

        assert isinstance(MVP_FEATURE_FLAGS, Mapping)

    def test_matrix_is_read_only(self) -> None:
        with pytest.raises(TypeError):
            MVP_FEATURE_FLAGS["mvp_execute_disabled"] = False  # type: ignore[index]

    def test_all_values_are_bool(self) -> None:
        for v in MVP_FEATURE_FLAGS.values():
            assert isinstance(v, bool)


class TestMvpRedLines:
    @pytest.mark.parametrize(
        "name",
        [
            "mvp_execute_disabled",
            "mvp_verified_disabled",
            "echo_adapter_only",
        ],
    )
    def test_mvp_safety_flags_on(self, name: str) -> None:
        assert get_flag(name) is True

    @pytest.mark.parametrize(
        "name",
        [
            "live_exchange_api_enabled",
            "real_market_data_enabled",
            "memory_writer_auto_verify",
            "llm_intent_relay_enabled",
            "llm_translator_loaded",
            "replay_engine_enabled",
            "replay_session_creation",
            "restore_endpoint_enabled",
            "fork_birth_enabled",
            "migration_birth_enabled",
            "production_numerics_required",
            "numerics_runtime_mutation",
            "production_adapters_enabled",
            "telegram_control_enabled",
            "operator_override_enabled",
            "learning_enabled",
            "sleep_cycle_enabled",
            "kill_switch_active",
        ],
    )
    def test_mvp_dangerous_flags_off(self, name: str) -> None:
        assert get_flag(name) is False


class TestGetFlag:
    def test_known_flag_returns_value(self) -> None:
        assert get_flag("mvp_execute_disabled") is True

    def test_unknown_flag_raises_keyerror(self) -> None:
        with pytest.raises(KeyError):
            get_flag("nonexistent_flag")

    def test_custom_flags_override(self) -> None:
        custom = {"my_flag": True}
        assert get_flag("my_flag", flags=custom) is True

    def test_custom_unknown_flag_raises(self) -> None:
        custom = {"my_flag": True}
        with pytest.raises(KeyError):
            get_flag("other_flag", flags=custom)


class TestAllFlagNames:
    def test_all_flag_names_is_frozenset(self) -> None:
        assert isinstance(all_flag_names(), frozenset)

    def test_kill_switch_in_names(self) -> None:
        assert "kill_switch_active" in all_flag_names()
