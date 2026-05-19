"""M1 Observer Ledger — append-only JSONL with hash-chain.

Per build plan §7 (Phase 2):
    - ledger.py:       append-only JSONL writer
    - hash_chain.py:   chain integrity (verify_on_read_required, Q §11)
    - catalog.py:      canonical event registry (F §19)
    - permanence.py:   F §10 permanence policy table (monotonic invariant)
    - audit_reader.py: M1_READ_AUDIT_RECORDED emission + reader_type tracking
"""
