"""Pydantic v2 schemas for Sentinel core types.

Per build plan §6 (Phase 1 — Contracts as Code):
    - payload.py:     PayloadSeed + 10-key primer palette
    - neural_seed.py: NeuralSeed + profile cap enforcement
    - events.py:      ObservationEvent / HumanIntentEvent / InternalShockEvent / RecallEvent
    - observer.py:    ObserverEvent 4-envelope
    - memory.py:      MemoryRecord + 16-class subject taxonomy
    - numerics.py:    NumericsArtifact + NumericEntry + Dependency
    - adapters.py:    AdapterManifest + capability + channel binding
    - workspace.py:   WorkspacePulseEvent (single mechanism)

All schemas enforce forbidden field rejection (Madde 6 LLM-untouchable).
"""
