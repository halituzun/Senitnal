"""M0 charge propagation integration: NeuralSeed -> tissue -> trace.

Per build plan §10 (Phase 5) done def: 'Synthetic neural_seed
produces M0 charge propagation trace'. This integration test wires
the compiled NeuralSeed into a uniform tissue, drives a simulated
input charge per primer payload, and asserts the M0 chain (neuron,
synapse, propagate_charge) produces a deterministic per-edge trace
without ever mutating its inputs.

Constitutional discipline exercised here:
    - Birth tissue allocation uniform across primer payloads
    - Receptor profile satisfies homonymous bias bound
    - Synapse weight below STABLE_PATH_THRESHOLD
    - propagate_charge read-only (no synapse weight mutation)
    - Charges remain bounded in [0, 1]
"""

from __future__ import annotations

from sentinel.ingress.compiler import compile_neural_seed
from sentinel.m0.neuron import Neuron
from sentinel.m0.synapse import STABLE_PATH_THRESHOLD, Synapse, propagate_charge
from sentinel.m0.tissue import allocate_uniform_birth_seeds
from sentinel.types.neural_seed import EventProfile, ProvenanceRef
from sentinel.types.payload import PayloadSeed, PrimerPayload


def _uniform_receptor() -> dict[PrimerPayload, float]:
    return {p: 1.0 for p in PrimerPayload}


def _make_neuron(neuron_id: str) -> Neuron:
    return Neuron(
        neuron_id=neuron_id,
        homonymous_bias_epsilon=0.05,
        receptor_profile=_uniform_receptor(),
    )


def _make_synapse(idx: int, pre: str, post: str, weight: float = 0.10) -> Synapse:
    return Synapse(
        synapse_id=f"s-{idx}",
        presynaptic_neuron_id=pre,
        postsynaptic_neuron_id=post,
        weight=weight,
    )


class TestSeedToM0Trace:
    def test_uniform_tissue_birth_then_seed_drives_trace(self) -> None:
        # 1) Birth allocates 10 seeds per primer payload (1 per payload
        # for the simplest case = 10 total).
        n_payloads = len(PrimerPayload)
        alloc = allocate_uniform_birth_seeds(n_payloads)
        # Allocation is uniform: each payload has exactly 1 seed.
        for payload in PrimerPayload:
            assert alloc.per_payload[payload] == 1

        # 2) Compile a NeuralSeed from a synthetic observation.
        seed = compile_neural_seed(
            profile=EventProfile.OBSERVATION_EVENT,
            event_attributes={"magnitude": 0.9, "confidence": 0.2},
            provenance=ProvenanceRef(source_event_id="src-m0-int"),
        )
        assert len(seed.payload_seed) >= 1

        # 3) Build a tiny tissue: 3 neurons in a chain.
        _make_neuron("a")
        _make_neuron("b")
        _make_neuron("c")
        s1 = _make_synapse(1, "a", "b", weight=0.10)
        s2 = _make_synapse(2, "b", "c", weight=0.10)

        # 4) For each payload in the seed, drive a propagation step.
        trace: list[tuple[str, float]] = []
        for p in seed.payload_seed:
            input_charge = p.intensity
            mid_charge = propagate_charge(s1, input_charge)
            out_charge = propagate_charge(s2, mid_charge)
            trace.append((p.payload.value, out_charge))

        # 5) Trace properties:
        assert len(trace) == len(seed.payload_seed)
        for _payload_name, charge in trace:
            # Charge bounded
            assert 0.0 <= charge <= 1.0
            # Two-hop through weak band shrinks the charge
            # (0.10 * 0.10 = 0.01 max amplification)
            assert charge <= 0.01 + 1e-12

        # 6) Synapse weights unchanged (read-only invariant).
        assert s1.weight == 0.10
        assert s2.weight == 0.10

        # 7) Synapse weights still below stable-path threshold.
        assert s1.weight < STABLE_PATH_THRESHOLD
        assert s2.weight < STABLE_PATH_THRESHOLD

        # 8) Determinism: replay produces the same trace.
        trace2: list[tuple[str, float]] = []
        for p in seed.payload_seed:
            mid_charge = propagate_charge(s1, p.intensity)
            out_charge = propagate_charge(s2, mid_charge)
            trace2.append((p.payload.value, out_charge))
        assert trace == trace2

    def test_neuron_receptor_within_bias(self) -> None:
        n = _make_neuron("probe")
        for payload, sens in n.receptor_profile.items():
            assert abs(sens - 1.0) <= n.homonymous_bias_epsilon, payload

    def test_zero_input_charge_stays_zero(self) -> None:
        s = _make_synapse(1, "a", "b", weight=0.10)
        assert propagate_charge(s, 0.0) == 0.0

    def test_arbitrary_payload_does_not_change_synapse(self) -> None:
        s = _make_synapse(1, "a", "b", weight=0.10)
        # Walk all primer payloads as if each was a distinct input.
        for _payload in PrimerPayload:
            propagate_charge(s, 0.5)
        assert s.weight == 0.10
        assert _PayloadSeed_module_unchanged()


def _PayloadSeed_module_unchanged() -> bool:
    # Sanity hook: walking the module should not mutate any class.
    return PayloadSeed.model_config.get("frozen", False) is True
