"""Ingress compiler — deterministic event → neural_seed mapping.

Per build plan §9 (Phase 4):
    - compiler.py:     event → bootstrap_rule match → base_payload_vector
    - rules.py:        minimal bootstrap rule families (D §19 MVP subset)
    - soft_overlap.py: linear membership function (N §6 v0.1 default)
    - profile_caps.py: N §7 hierarchy enforcement

Constitutional: no LLM input, no semantic judgment, no adapter direct neural_seed.
"""
