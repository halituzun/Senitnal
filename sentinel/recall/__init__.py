"""Recall protocol — memory_echo trigger → top-1 RecallEvent.

Per build plan §13 (Phase 8):
    - protocol.py:  composite trigger AND + sustained_tension_required
    - ranking.py:   mechanical multiplicative score (T §8; semantic forbidden)
    - candidate.py: T §14 candidate recall constraints

Constitutional:
    - Core-facing recall is top-1 (T §7; immutable)
    - Human direct recall push forbidden (T §19)
    - Empty result → audit only (T §20; no core-facing absence payload)
"""
