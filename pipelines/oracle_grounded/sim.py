"""Public facade for deterministic reference simulators.

Implementations are split by physical model while this module keeps the
established import surface used by family wiring and tests.
"""

from . import sim_common as _common
from . import sim_encoder as _encoder
from . import sim_neuron as _neuron
from . import sim_mesh as _mesh
from . import sim_credit as _credit
from . import sim_memory as _memory

ENERGY_PJ_PER_SPIKE = _common.ENERGY_PJ_PER_SPIKE
ENCODINGS = _common.ENCODINGS
WEIGHT_UPDATE_EPS = _common.WEIGHT_UPDATE_EPS
clamp = _common.clamp
pearson = _common.pearson
rmse = _common.rmse
ENCODER_DEFAULTS = _encoder.ENCODER_DEFAULTS
encoder_config = _encoder.encoder_config
encode_rate = _encoder.encode_rate
decode_rate = _encoder.decode_rate
encode_latency = _encoder.encode_latency
decode_latency = _encoder.decode_latency
encode_delta = _encoder.encode_delta
decode_delta = _encoder.decode_delta
encode_temporal = _encoder.encode_temporal
decode_temporal = _encoder.decode_temporal
_ENCODERS = _encoder._ENCODERS
run_encoder = _encoder.run_encoder
compare_encodings = _encoder.compare_encodings
NEURON_DEFAULTS = _neuron.NEURON_DEFAULTS
INTERVENTION_TARGETS = _neuron.INTERVENTION_TARGETS
neuron_config = _neuron.neuron_config
simulate_neuron = _neuron.simulate_neuron
_neuron_summary = _neuron._neuron_summary
compare_neuron_states = _neuron.compare_neuron_states
_optional_delta = _neuron._optional_delta
MESH_NODE_DEFAULTS = _mesh.MESH_NODE_DEFAULTS
mesh_node = _mesh.mesh_node
MAX_MESH_STEPS = _mesh.MAX_MESH_STEPS
_require_positive_mesh_number = _mesh._require_positive_mesh_number
mesh_step_count = _mesh.mesh_step_count
MeshBounds = _mesh.MeshBounds
simulate_mesh = _mesh.simulate_mesh
mesh_causal_summary = _mesh.mesh_causal_summary
mesh_causal_delta = _mesh.mesh_causal_delta
CRITIC_DEFAULTS = _credit.CRITIC_DEFAULTS
critic_config = _credit.critic_config
run_critic = _credit.run_critic
PLASTICITY_DEFAULTS = _credit.PLASTICITY_DEFAULTS
plasticity_config = _credit.plasticity_config
_plasticity_circuit = _credit._plasticity_circuit
eligibility_traces = _credit.eligibility_traces
run_plasticity = _credit.run_plasticity
MEMORY_DEFAULTS = _memory.MEMORY_DEFAULTS
memory_config = _memory.memory_config
memory_network = _memory.memory_network
memory_events = _memory.memory_events
memory_response_from_counts = _memory.memory_response_from_counts
run_memory_task = _memory.run_memory_task
_latch_alive = _memory._latch_alive

__all__ = tuple(name for name in globals() if not name.startswith("_"))
