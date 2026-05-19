"""Numerics artifact loader and validator.

Per build plan §8 (Phase 3):
    - loader.py:    NumericsArtifact JSON load + dev_only flag enforcement
    - validator.py: no-default rule (M §9) + dependency validation (M §12)
    - enum_set.py:  enum_set convention (M §8; whitelist vs blacklist semantics)
    - fixtures/:    8 dev fixture artifacts (N/O/P/Q/R/S/T/U)

Production loader rejects `dev_only=true` artifacts.
MVP loader accepts dev fixtures with explicit marker.
"""
