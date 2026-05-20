"""LocalJsonlMarketAdapter — local file-based read-only market source.

Reads sanitized MarketObservationEnvelope records from a local JSONL
file. Each line is one envelope encoded as JSON. The adapter does
NOT open network sockets, does NOT fetch remote URLs, does NOT
import any exchange SDK.

This is the V2 "read-only bridge" surface intended for synthetic
fixture suites and (in future) one-way exports from sibling
processes (e.g. Gel.Al → file → Sentinel). The bridge process
itself is NOT inside Sentinel; only the file reader is. The reader
has no concept of HTTP, WebSocket, or any exchange protocol.
"""

from __future__ import annotations

from collections.abc import Iterator  # noqa: TC003 (runtime annotation on iter return)
from dataclasses import dataclass, field
from pathlib import Path  # noqa: TC003 (Pydantic + dataclass field at runtime)

from pydantic import ValidationError

from sentinel.adapters.market_manifest import build_local_jsonl_market_manifest
from sentinel.adapters.market_observation import MarketObservationEnvelope
from sentinel.types.adapters import AdapterManifest  # noqa: TC001 (dataclass field at runtime)


@dataclass
class LocalJsonlMarketAdapter:
    """Read-only JSONL market observation source.

    Construction:
        LocalJsonlMarketAdapter(path=Path("tests/fixtures/market/calm.jsonl"))

    `path` must exist when read methods are called. The constructor
    does NOT open the file; it stores the path. `read_all` and
    `iter_observations` read on demand.
    """

    path: Path
    manifest: AdapterManifest = field(default_factory=build_local_jsonl_market_manifest)

    def read_all(self) -> tuple[MarketObservationEnvelope, ...]:
        """Read every envelope into a tuple.

        Raises:
            FileNotFoundError: if `self.path` does not exist.
            ValueError: if any non-blank line is not valid JSON;
                        the error message includes the 1-indexed
                        line number.
            ValidationError: if a JSON line is well-formed but the
                             resulting envelope fails schema
                             validation (e.g. inconsistent mid_price,
                             extra=forbid field present).
        """
        return tuple(self.iter_observations())

    def iter_observations(self) -> Iterator[MarketObservationEnvelope]:
        """Lazily yield envelopes one per non-blank line.

        Same raises as `read_all`. The iterator is single-pass.
        """
        if not self.path.exists():
            raise FileNotFoundError(f"market jsonl fixture not found: {self.path}")
        with self.path.open("r", encoding="utf-8") as fh:
            for line_no, raw in enumerate(fh, start=1):
                stripped = raw.strip()
                if not stripped:
                    continue
                try:
                    yield MarketObservationEnvelope.model_validate_json(stripped)
                except ValidationError:
                    # surface validation errors directly so callers can
                    # distinguish schema breach from corrupt JSON
                    raise
                except ValueError as exc:
                    raise ValueError(
                        f"malformed JSON on line {line_no} of {self.path}: {exc}"
                    ) from exc
