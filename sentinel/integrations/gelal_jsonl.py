"""Read-only local JSONL adapter for Gel.Al shadow envelopes (V5).

The adapter reads a local file containing one
``GelAlShadowEnvelope`` per line.  It performs **no** network I/O,
**no** database access, **no** Redis access, and exposes **no**
write methods.  Gel.Al writes the file from its own process; Sentinel
reads it.
"""

from __future__ import annotations

from collections.abc import Iterator  # noqa: TC003 (runtime iter return)
from dataclasses import dataclass
from pathlib import Path  # noqa: TC003 (dataclass field at runtime)

from pydantic import ValidationError

from sentinel.integrations.gelal_shadow import GelAlShadowEnvelope


@dataclass(frozen=True, slots=True)
class GelAlShadowJsonlAdapter:
    """Read-only file-backed source of Gel.Al shadow envelopes.

    Construction does **not** open the file; ``read_all`` and
    ``iter_events`` open on demand.  The adapter is single-pass per
    call.
    """

    path: Path

    def read_all(self) -> tuple[GelAlShadowEnvelope, ...]:
        """Read every envelope into a tuple, preserving file order.

        Raises:
            FileNotFoundError: ``self.path`` does not exist.
            ValueError: a non-blank line is not valid JSON; the
                message includes the 1-indexed line number.
            ValidationError: a well-formed JSON line failed schema
                validation (forbidden payload key, missing field).
        """
        return tuple(self.iter_events())

    def iter_events(self) -> Iterator[GelAlShadowEnvelope]:
        """Lazily yield envelopes one per non-blank line."""
        if not self.path.exists():
            raise FileNotFoundError(f"gel.al shadow jsonl not found: {self.path}")
        with self.path.open("r", encoding="utf-8") as fh:
            for line_no, raw in enumerate(fh, start=1):
                stripped = raw.strip()
                if not stripped:
                    continue
                try:
                    yield GelAlShadowEnvelope.model_validate_json(stripped)
                except ValidationError:
                    raise
                except ValueError as exc:
                    raise ValueError(
                        f"malformed JSON on line {line_no} of {self.path}: {exc}"
                    ) from exc
