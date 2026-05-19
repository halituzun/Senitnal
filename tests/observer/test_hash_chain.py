"""Tests for the ObserverEvent append-only hash-chain primitives.

Discipline tested here:
    - canonical_json_bytes deterministic (key order, separators)
    - sha256_digest returns "sha256:" + 64 hex chars
    - compute_observer_event_hash deterministic; excludes event_hash;
      includes previous_event_hash
    - with_computed_event_hash returns a new frozen ObserverEvent
      whose event_hash matches the recomputed digest
    - verify_observer_event_hash true after compute, false if the
      payload is mutated post-hoc
    - link_observer_event sets previous_event_hash and recomputes
      event_hash
    - verify_chain_links accepts a valid chain, rejects broken
      previous-hash links and rejects stale event_hash entries
    - Empty chain is valid
"""

from __future__ import annotations

import re

from sentinel.observer.hash_chain import (
    canonical_json_bytes,
    compute_observer_event_hash,
    link_observer_event,
    placeholder_event_hash,
    sha256_digest,
    verify_chain_links,
    verify_observer_event_hash,
    with_computed_event_hash,
)
from sentinel.types.neural_seed import ProvenanceRef
from sentinel.types.observer import EventFamily, ObserverEvent

_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def _event(
    *,
    event_id: str = "ev-001",
    event_type: str = "WORKSPACE_PULSE",
    event_family: EventFamily = EventFamily.ATTENTION,
    occurred_at_ms: int = 1_700_000_000_000,
    payload: dict[str, object] | None = None,
    previous_event_hash: str | None = None,
    event_hash: str | None = None,
) -> ObserverEvent:
    return ObserverEvent(
        event_id=event_id,
        event_family=event_family,
        event_type=event_type,
        occurred_at_ms=occurred_at_ms,
        payload=payload if payload is not None else {"reason": "test", "counter": 1},
        provenance=ProvenanceRef(source_event_id="src-001"),
        previous_event_hash=previous_event_hash,
        event_hash=event_hash if event_hash is not None else placeholder_event_hash(),
    )


# ---------------------------------------------------------------------------
# canonical_json_bytes
# ---------------------------------------------------------------------------


class TestCanonicalJsonBytes:
    def test_deterministic_for_same_mapping(self) -> None:
        a = canonical_json_bytes({"a": 1, "b": 2})
        b = canonical_json_bytes({"a": 1, "b": 2})
        assert a == b

    def test_key_order_does_not_change_output(self) -> None:
        a = canonical_json_bytes({"a": 1, "b": 2})
        b = canonical_json_bytes({"b": 2, "a": 1})
        assert a == b

    def test_returns_bytes(self) -> None:
        assert isinstance(canonical_json_bytes({"x": 1}), bytes)


# ---------------------------------------------------------------------------
# sha256_digest
# ---------------------------------------------------------------------------


class TestSha256Digest:
    def test_digest_format(self) -> None:
        d = sha256_digest(b"hello")
        assert _SHA256_RE.match(d) is not None

    def test_deterministic(self) -> None:
        assert sha256_digest(b"x") == sha256_digest(b"x")

    def test_different_inputs_different_digests(self) -> None:
        assert sha256_digest(b"x") != sha256_digest(b"y")


# ---------------------------------------------------------------------------
# compute_observer_event_hash
# ---------------------------------------------------------------------------


class TestComputeObserverEventHash:
    def test_deterministic(self) -> None:
        ev = _event()
        assert compute_observer_event_hash(ev) == compute_observer_event_hash(ev)

    def test_excludes_self_event_hash_field(self) -> None:
        """Hash must not depend on the (placeholder) event_hash value."""
        ev_a = _event(event_hash=placeholder_event_hash())
        ev_b = _event(event_hash="sha256:" + ("f" * 64))
        assert compute_observer_event_hash(ev_a) == compute_observer_event_hash(ev_b)

    def test_payload_change_changes_hash(self) -> None:
        ev_a = _event(payload={"reason": "a"})
        ev_b = _event(payload={"reason": "b"})
        assert compute_observer_event_hash(ev_a) != compute_observer_event_hash(ev_b)

    def test_previous_event_hash_change_changes_hash(self) -> None:
        ev_a = _event(previous_event_hash=None)
        ev_b = _event(previous_event_hash="sha256:" + ("a" * 64))
        assert compute_observer_event_hash(ev_a) != compute_observer_event_hash(ev_b)

    def test_format_is_sha256_hex(self) -> None:
        ev = _event()
        assert _SHA256_RE.match(compute_observer_event_hash(ev)) is not None


# ---------------------------------------------------------------------------
# with_computed_event_hash / verify_observer_event_hash
# ---------------------------------------------------------------------------


class TestWithComputedEventHash:
    def test_returns_new_event_with_real_hash(self) -> None:
        ev = _event()
        linked = with_computed_event_hash(ev)
        assert linked is not ev
        assert _SHA256_RE.match(linked.event_hash) is not None
        assert linked.event_hash == compute_observer_event_hash(linked)

    def test_verify_true_after_compute(self) -> None:
        ev = with_computed_event_hash(_event())
        assert verify_observer_event_hash(ev) is True

    def test_verify_false_when_payload_is_mutated_via_model_copy(self) -> None:
        ev = with_computed_event_hash(_event(payload={"a": 1}))
        tampered = ev.model_copy(update={"payload": {"a": 2}})
        assert verify_observer_event_hash(tampered) is False


# ---------------------------------------------------------------------------
# link_observer_event
# ---------------------------------------------------------------------------


class TestLinkObserverEvent:
    def test_sets_previous_event_hash_and_computes_event_hash(self) -> None:
        genesis = with_computed_event_hash(_event(event_id="ev-genesis"))
        linked = link_observer_event(
            _event(event_id="ev-002"),
            previous_event_hash=genesis.event_hash,
        )
        assert linked.previous_event_hash == genesis.event_hash
        assert verify_observer_event_hash(linked)

    def test_genesis_can_have_none_previous_hash(self) -> None:
        genesis = link_observer_event(_event(event_id="ev-0"), previous_event_hash=None)
        assert genesis.previous_event_hash is None
        assert verify_observer_event_hash(genesis)


# ---------------------------------------------------------------------------
# verify_chain_links
# ---------------------------------------------------------------------------


class TestVerifyChainLinks:
    def test_empty_chain_is_valid(self) -> None:
        assert verify_chain_links(()) is True

    def test_single_genesis_event_valid(self) -> None:
        g = link_observer_event(_event(event_id="ev-0"), previous_event_hash=None)
        assert verify_chain_links((g,)) is True

    def test_three_event_chain_valid(self) -> None:
        e0 = link_observer_event(_event(event_id="ev-0"), previous_event_hash=None)
        e1 = link_observer_event(
            _event(event_id="ev-1"), previous_event_hash=e0.event_hash
        )
        e2 = link_observer_event(
            _event(event_id="ev-2"), previous_event_hash=e1.event_hash
        )
        assert verify_chain_links((e0, e1, e2)) is True

    def test_broken_previous_hash_rejected(self) -> None:
        e0 = link_observer_event(_event(event_id="ev-0"), previous_event_hash=None)
        e1_bad = link_observer_event(
            _event(event_id="ev-1"),
            previous_event_hash="sha256:" + ("0" * 64),
        )
        assert verify_chain_links((e0, e1_bad)) is False

    def test_stale_event_hash_rejected(self) -> None:
        e0 = link_observer_event(_event(event_id="ev-0"), previous_event_hash=None)
        e1 = link_observer_event(
            _event(event_id="ev-1"), previous_event_hash=e0.event_hash
        )
        # Tamper with e1's payload AFTER it was linked → stale event_hash
        e1_stale = e1.model_copy(update={"payload": {"reason": "tampered"}})
        assert verify_chain_links((e0, e1_stale)) is False
