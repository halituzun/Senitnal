"""V6 — Policy evaluator CLI tests."""

from __future__ import annotations

from pathlib import Path

from sentinel.runtime.policy_eval import cli_main

_POLICY_DIR = Path("tests/fixtures/policy")
_GELAL_DIR = Path("tests/fixtures/gelal_policy")


class TestPolicyEvalCli:
    def test_cli_runs_valid_inputs(self, tmp_path: Path) -> None:
        rc = cli_main(
            [
                "--policy",
                str(_POLICY_DIR / "conservative_shadow_policy.json"),
                "--gelal",
                str(_GELAL_DIR / "gelal_opportunity_seen.jsonl"),
                "--ledger",
                str(tmp_path / "l.jsonl"),
                "--now-ms",
                "1700000000500",
            ]
        )
        assert rc == 0

    def test_cli_high_risk_blocks_under_conservative_policy(self, tmp_path: Path) -> None:
        rc = cli_main(
            [
                "--policy",
                str(_POLICY_DIR / "conservative_shadow_policy.json"),
                "--gelal",
                str(_GELAL_DIR / "gelal_high_risk_blocked.jsonl"),
                "--ledger",
                str(tmp_path / "l.jsonl"),
                "--now-ms",
                "1700000010500",
            ]
        )
        assert rc == 0

    def test_cli_bad_order_blocks(self, tmp_path: Path) -> None:
        rc = cli_main(
            [
                "--policy",
                str(_POLICY_DIR / "conservative_shadow_policy.json"),
                "--gelal",
                str(_GELAL_DIR / "gelal_bad_order_observed.jsonl"),
                "--ledger",
                str(tmp_path / "l.jsonl"),
                "--now-ms",
                "1700000020500",
            ]
        )
        assert rc == 0

    def test_cli_kill_switch_blocks(self, tmp_path: Path) -> None:
        rc = cli_main(
            [
                "--policy",
                str(_POLICY_DIR / "conservative_shadow_policy.json"),
                "--gelal",
                str(_GELAL_DIR / "gelal_kill_switch_active.jsonl"),
                "--ledger",
                str(tmp_path / "l.jsonl"),
                "--now-ms",
                "1700000030500",
            ]
        )
        assert rc == 0

    def test_cli_invalid_policy_returns_1(self, tmp_path: Path) -> None:
        rc = cli_main(
            [
                "--policy",
                str(_POLICY_DIR / "invalid_execution_action_policy.json"),
                "--gelal",
                str(_GELAL_DIR / "gelal_opportunity_seen.jsonl"),
                "--ledger",
                str(tmp_path / "l.jsonl"),
            ]
        )
        assert rc == 1

    def test_cli_missing_policy_returns_1(self, tmp_path: Path) -> None:
        rc = cli_main(
            [
                "--policy",
                str(tmp_path / "nope.json"),
                "--gelal",
                str(_GELAL_DIR / "gelal_opportunity_seen.jsonl"),
                "--ledger",
                str(tmp_path / "l.jsonl"),
            ]
        )
        assert rc == 1
