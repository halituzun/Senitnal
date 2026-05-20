"""Cross-module consistency: every event_type literal is in the catalog.

A regression guard against drift: when a developer adds a new
`event_type="X"` somewhere in `sentinel/` but forgets to add `X` to
the canonical event catalog, this test fails.

Scans every `.py` file under `sentinel/` and `tests/` for
    event_type="..."
literal assignments, then asserts each unique value is either:
    - in CANONICAL_EVENT_CATALOG, or
    - in the explicitly allowed test-only sentinel set below.
"""

from __future__ import annotations

import re
from pathlib import Path

from sentinel.observer.catalog import CANONICAL_EVENT_CATALOG

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SENTINEL_DIR = _REPO_ROOT / "sentinel"
_TESTS_DIR = _REPO_ROOT / "tests"

# Test-only event_type / probe strings deliberately used to exercise
# the "unknown event_type rejected" or "frozen attribute" paths.
# These are NOT real canonical events and SHOULD NOT be in the catalog.
_TEST_ONLY_SENTINELS: frozenset[str] = frozenset(
    {
        "NOT_A_CANONICAL_EVENT",
        "FOCUS_PULSE",  # rejected in workspace pulse type tests
        "CONTRADICTION_PULSE",  # rejected in workspace pulse type tests
        # Frozen-dataclass mutation probes (test_definition_is_frozen
        # in catalog / invariants tests assign these to an event_type
        # attribute on an otherwise frozen object; the assignment is
        # expected to raise).
        "OTHER",
        "X",
    }
)

_EVENT_TYPE_RE = re.compile(r'event_type\s*=\s*"([A-Z_][A-Z0-9_]*)"')


def _collect_event_types(root: Path) -> set[str]:
    found: set[str] = set()
    for path in root.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        for match in _EVENT_TYPE_RE.finditer(text):
            found.add(match.group(1))
    return found


class TestCatalogConsistency:
    def test_every_referenced_event_type_is_canonical_or_sentinel(self) -> None:
        catalog_types = {ev.event_type for ev in CANONICAL_EVENT_CATALOG}
        referenced = _collect_event_types(_SENTINEL_DIR) | _collect_event_types(_TESTS_DIR)
        # Workspace pulse event is the only event_type that isn't appended
        # via the observer ledger flow — it's a Literal value on the
        # WorkspacePulseEvent envelope. The workspace.pulse emitter
        # writes the same string into the ledger so it IS canonical.
        unknown = referenced - catalog_types - _TEST_ONLY_SENTINELS
        assert unknown == set(), (
            "non-canonical event_type literals detected; either add them "
            f"to CANONICAL_EVENT_CATALOG or to _TEST_ONLY_SENTINELS: {sorted(unknown)!r}"
        )

    def test_catalog_event_types_actually_referenced_somewhere(self) -> None:
        """Catch unreachable catalog entries (light coverage check).

        Soft: catalog can carry entries not yet emitted by code. We
        only assert the catalog itself is non-empty and the v0.1
        red-line event_types are present.
        """
        catalog_types = {ev.event_type for ev in CANONICAL_EVENT_CATALOG}
        for must_be_present in (
            "WORKSPACE_PULSE",
            "OBSERVATION_INGESTED",
            "MEMORY_RECORD_STATUS_CHANGED",
            "DEONTIC_BLOCKED",
            "DEONTIC_BYPASS_ATTEMPT",
            "KILL_SWITCH_ACTIVATED",
            "M1_READ_AUDIT_RECORDED",
            "NUMERICS_FAILSAFE_ACTIVATED",
            "ADAPTER_MANIFEST_STATUS_CHANGED",
            "RECALL_REQUEST_EMITTED",
            "RECALL_RESULT_EMPTY",
        ):
            assert must_be_present in catalog_types
