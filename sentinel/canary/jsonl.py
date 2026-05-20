"""V8 — Local JSONL canary candidate adapter (read-only)."""

from __future__ import annotations

from collections.abc import Iterator  # noqa: TC003 (iter return runtime)
from dataclasses import dataclass
from pathlib import Path  # noqa: TC003 (dataclass field runtime)

from pydantic import ValidationError

from sentinel.canary.candidate import CanaryCandidateAction


@dataclass(frozen=True, slots=True)
class CanaryCandidateJsonlAdapter:
    """Read-only file source of canary candidate actions."""

    path: Path

    def read_all(self) -> tuple[CanaryCandidateAction, ...]:
        return tuple(self.iter_candidates())

    def iter_candidates(self) -> Iterator[CanaryCandidateAction]:
        if not self.path.exists():
            raise FileNotFoundError(f"canary candidate jsonl not found: {self.path}")
        with self.path.open("r", encoding="utf-8") as fh:
            for line_no, raw in enumerate(fh, start=1):
                stripped = raw.strip()
                if not stripped:
                    continue
                try:
                    yield CanaryCandidateAction.model_validate_json(stripped)
                except ValidationError:
                    raise
                except ValueError as exc:
                    raise ValueError(
                        f"malformed JSON on line {line_no} of {self.path}: {exc}"
                    ) from exc


__all__ = ["CanaryCandidateJsonlAdapter"]
