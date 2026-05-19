"""Runtime — dry simulation, feature flags, output set.

Per build plan §15 (Phase 10):
    - dry_sim.py:       end-to-end synthetic simulation driver
    - feature_flags.py: centralized MVP flag matrix (build plan §18)
    - output.py:        MVP output enum {WAIT, BLOCK, MONITOR, NEED_RECALL, NO_ACTION}

Constitutional:
    - Forbidden outputs: BUY, SELL, EXECUTE_REAL, ORDER_SUBMIT (CI-enforced)
    - Feature flag matrix cannot be overridden at runtime
"""
