"""Adapter manifest, trust, and EchoAdapter (test-only).

Per build plan §14 (Phase 9):
    - manifest.py: AdapterManifest validation (I §6)
    - trust.py:    AdapterTrustRecord composition (U §6) + band cutoffs
    - echo.py:     EchoAdapter — synthetic ObservationEvent source

Constitutional:
    - Adapter cannot emit neural_seed (U §16; immediate revoke, terminal)
    - Capability incompatibility cannot be overridden (U §11)
    - intent_relay cannot satisfy execute/memory_writer/recall_provider (U §15)
"""
