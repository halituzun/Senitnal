"""Tests for the dry-sim CLI entry point."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003 (fixture annotation)

import pytest  # noqa: TC002 (CaptureFixture runtime annotation)
from sentinel.runtime.__main__ import main


class TestCli:
    def test_runs_and_exit_zero(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        ledger_path = tmp_path / "sim.jsonl"
        rc = main(
            [
                "--ledger",
                str(ledger_path),
                "--magnitude",
                "0.8",
            ]
        )
        assert rc == 0
        assert ledger_path.exists()
        out = capsys.readouterr().out
        assert "output=WAIT" in out
        assert "audit_events=2" in out

    def test_creates_parent_dir(self, tmp_path: Path) -> None:
        ledger_path = tmp_path / "nested" / "subdir" / "sim.jsonl"
        rc = main(["--ledger", str(ledger_path)])
        assert rc == 0
        assert ledger_path.exists()

    def test_appends_across_runs(self, tmp_path: Path) -> None:
        from sentinel.observer.ledger import JsonlObserverLedger

        ledger_path = tmp_path / "sim.jsonl"
        main(["--ledger", str(ledger_path)])
        main(["--ledger", str(ledger_path)])
        events = JsonlObserverLedger(ledger_path).read_all()
        # 2 events per run, 2 runs = 4 events; chain re-verifies
        assert len(events) == 4
        assert JsonlObserverLedger(ledger_path).verify() is True
