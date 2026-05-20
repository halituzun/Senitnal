"""V9 — Local JSONL governance request adapter (read-only)."""

from __future__ import annotations

from collections.abc import Iterator  # noqa: TC003 (iter runtime)
from dataclasses import dataclass
from pathlib import Path  # noqa: TC003 (dataclass field runtime)

from pydantic import ValidationError

from sentinel.governance.request import LiveGovernanceRequest


@dataclass(frozen=True, slots=True)
class LiveGovernanceRequestJsonlAdapter:
    """Read-only file source of live governance requests."""

    path: Path

    def read_all(self) -> tuple[LiveGovernanceRequest, ...]:
        return tuple(self.iter_requests())

    def iter_requests(self) -> Iterator[LiveGovernanceRequest]:
        if not self.path.exists():
            raise FileNotFoundError(f"governance request jsonl not found: {self.path}")
        with self.path.open("r", encoding="utf-8") as fh:
            for line_no, raw in enumerate(fh, start=1):
                stripped = raw.strip()
                if not stripped:
                    continue
                try:
                    yield LiveGovernanceRequest.model_validate_json(stripped)
                except ValidationError:
                    raise
                except ValueError as exc:
                    raise ValueError(
                        f"malformed JSON on line {line_no} of {self.path}: {exc}"
                    ) from exc


__all__ = ["LiveGovernanceRequestJsonlAdapter"]
