"""Deterministic reference simulators used as stand-in oracles.

None of the runtimes named in issue #77 (`axon-encoder`, `neuromod`,
`synaptic-mesh`, `limbic-critic`, `plasticity-lab`, a validated recurrent SNN)
are installed in this environment, and the repository's own notes already
record that the crates.io packages are unavailable. Rather than fake their
output, this package supplies small, fully specified, stdlib-only simulators
that occupy the same position in the pipeline.

They are labelled `implementation: "reference"` in every record they produce.
A reference measurement is a real measurement of a real (if small) model; it
is *not* a measurement from the named runtime, and `record.py` refuses to mark
such records publishable.

Every function is pure and deterministic: same inputs, same floats. The
implementations live in one module per simulator family — ``sim_core``,
``sim_encoder``, ``sim_neuron``, ``sim_mesh``, ``sim_credit``,
``sim_memory`` — and this module re-exports the whole surface.
"""

from .sim_core import ENERGY_PJ_PER_SPIKE, clamp, optional_delta, pearson, rmse
from .sim_credit import (
    CRITIC_DEFAULTS,
    PLASTICITY_DEFAULTS,
    WEIGHT_UPDATE_EPS,
    critic_config,
    eligibility_traces,
    plasticity_circuit,
    plasticity_config,
    run_critic,
    run_plasticity,
)
from .sim_encoder import (
    ENCODER_DEFAULTS,
    ENCODINGS,
    compare_encodings,
    decode_delta,
    decode_latency,
    decode_rate,
    decode_temporal,
    encode_delta,
    encode_latency,
    encode_rate,
    encode_temporal,
    encoder_config,
    run_encoder,
)
from .sim_memory import (
    MEMORY_DEFAULTS,
    memory_config,
    memory_events,
    memory_network,
    memory_response_from_counts,
    run_memory_task,
)
from .sim_mesh import (
    MESH_NODE_DEFAULTS,
    MeshLimits,
    MeshNetwork,
    mesh_causal_delta,
    mesh_causal_summary,
    mesh_node,
    simulate_mesh,
)
from .sim_neuron import (
    INTERVENTION_TARGETS,
    NEURON_DEFAULTS,
    compare_neuron_states,
    neuron_config,
    simulate_neuron,
)

__all__ = [
    "CRITIC_DEFAULTS",
    "ENCODER_DEFAULTS",
    "ENCODINGS",
    "ENERGY_PJ_PER_SPIKE",
    "INTERVENTION_TARGETS",
    "MEMORY_DEFAULTS",
    "MESH_NODE_DEFAULTS",
    "MeshLimits",
    "MeshNetwork",
    "NEURON_DEFAULTS",
    "PLASTICITY_DEFAULTS",
    "WEIGHT_UPDATE_EPS",
    "clamp",
    "compare_encodings",
    "compare_neuron_states",
    "critic_config",
    "decode_delta",
    "decode_latency",
    "decode_rate",
    "decode_temporal",
    "eligibility_traces",
    "encode_delta",
    "encode_latency",
    "encode_rate",
    "encode_temporal",
    "encoder_config",
    "memory_config",
    "memory_events",
    "memory_network",
    "memory_response_from_counts",
    "mesh_causal_delta",
    "mesh_causal_summary",
    "mesh_node",
    "neuron_config",
    "optional_delta",
    "pearson",
    "plasticity_circuit",
    "plasticity_config",
    "rmse",
    "run_critic",
    "run_encoder",
    "run_memory_task",
    "run_plasticity",
    "simulate_mesh",
    "simulate_neuron",
]
