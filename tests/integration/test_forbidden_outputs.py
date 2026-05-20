"""Constitutional: forbidden execution literals never appear in M1.

Per build plan §15, §20 red lines: the entire M1 ledger trail of an
MVP dry-sim run must NEVER contain `BUY`, `SELL`, `EXECUTE_REAL`,
`ORDER_SUBMIT` (or their case variants / substrings).
"""

from __future__ import annotations

import json
from pathlib import Path  # noqa: TC003 (fixture annotation)

import pytest
from sentinel.adapters.echo import EchoAdapter
from sentinel.observer.ledger import JsonlObserverLedger
from sentinel.runtime.dry_sim import run_dry_simulation
from sentinel.runtime.output import (
    FORBIDDEN_OUTPUT_LITERALS,
    SystemOutput,
    assert_no_forbidden_literal,
)


@pytest.fixture
def ledger_path(tmp_path: Path) -> Path:
    return tmp_path / "ledger.jsonl"


@pytest.fixture
def ledger(ledger_path: Path) -> JsonlObserverLedger:
    return JsonlObserverLedger(ledger_path)


class TestForbiddenLiteralsInLedger:
    def test_no_forbidden_literal_in_ledger_payload(
        self, ledger_path: Path, ledger: JsonlObserverLedger
    ) -> None:
        adapter = EchoAdapter.default()
        run_dry_simulation(
            ledger=ledger,
            adapter=adapter,
            observation_magnitude=0.8,
        )
        raw_text = ledger_path.read_text(encoding="utf-8").lower()
        for needle in FORBIDDEN_OUTPUT_LITERALS:
            assert needle not in raw_text, f"forbidden literal {needle!r} leaked into M1 ledger"

    def test_per_line_json_payload_clean(
        self, ledger_path: Path, ledger: JsonlObserverLedger
    ) -> None:
        adapter = EchoAdapter.default()
        run_dry_simulation(
            ledger=ledger,
            adapter=adapter,
            observation_magnitude=0.8,
        )
        with ledger_path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                assert_no_forbidden_literal(json.dumps(obj))


class TestOutputSet:
    def test_dry_sim_output_in_canonical_set(self, ledger: JsonlObserverLedger) -> None:
        adapter = EchoAdapter.default()
        result = run_dry_simulation(
            ledger=ledger,
            adapter=adapter,
            observation_magnitude=0.8,
        )
        assert result.output.value in {
            "WAIT",
            "BLOCK",
            "MONITOR",
            "NEED_RECALL",
            "NO_ACTION",
        }

    def test_canonical_output_set_size(self) -> None:
        # The enum itself must remain exactly 5 values.
        assert len(SystemOutput) == 5
