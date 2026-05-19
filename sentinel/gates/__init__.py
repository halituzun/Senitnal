"""Gates — Deontic (action) and Memory Write (epistemic).

Per build plan §12 (Phase 7):
    - deontic.py:      E §8 hard-stops (13 rules); MVP default-deny mode
    - memory_write.py: G §8 matrix; silent gate (G §4); candidate-only in MVP

Constitutional:
    - Every ApprovedActionIntent → BLOCK in MVP (mvp_execute_disabled = True)
    - Memory Write Gate produces no core-facing signal (silent)
    - All verified writes DEFERRED (MVP: candidate or rejected only)
"""
