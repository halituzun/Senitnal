"""CLI entry point for the MVP dry simulation.

Usage:
    python -m sentinel.runtime --ledger /tmp/sim.jsonl --magnitude 0.8

Runs `run_dry_simulation` once with the supplied arguments and
prints a one-line summary plus the final SystemOutput value. The
M1 ledger file is created (or appended to) at the requested path
and re-verified before exit.

Exit codes:
    0  pipeline ran, ledger chain re-verifies, output was WAIT
    1  pipeline raised an error
    2  ledger chain failed to re-verify (constitutional defect)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sentinel.adapters.echo import EchoAdapter
from sentinel.observer.ledger import JsonlObserverLedger
from sentinel.runtime.dry_sim import run_dry_simulation


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m sentinel.runtime",
        description="Run the Sentinel MVP dry simulation once.",
    )
    p.add_argument(
        "--ledger",
        type=Path,
        required=True,
        help="Path to the JSONL ledger file (created if absent).",
    )
    p.add_argument(
        "--magnitude",
        type=float,
        default=0.8,
        help="Observation magnitude in [0,1] (default 0.8).",
    )
    p.add_argument(
        "--confidence",
        type=float,
        default=0.7,
        help="Observation confidence in [0,1] (default 0.7).",
    )
    p.add_argument(
        "--coherence",
        type=float,
        default=0.4,
        help="Pulse coherence in [0,1] (default 0.4).",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    ledger_path: Path = args.ledger
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger = JsonlObserverLedger(ledger_path)
    adapter = EchoAdapter.default()

    try:
        result = run_dry_simulation(
            ledger=ledger,
            adapter=adapter,
            observation_magnitude=args.magnitude,
            confidence=args.confidence,
            coherence=args.coherence,
        )
    except Exception as exc:
        print(f"sentinel-mvp: pipeline error: {exc}", file=sys.stderr)
        return 1

    if not ledger.verify():
        print(
            "sentinel-mvp: ledger hash chain failed to re-verify!",
            file=sys.stderr,
        )
        return 2

    print(
        f"sentinel-mvp: output={result.output.value} "
        f"audit_events={len(result.audit_event_ids)} "
        f"ledger={ledger_path}"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover — CLI entry
    raise SystemExit(main())
