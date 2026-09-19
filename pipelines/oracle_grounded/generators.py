"""Public facade for deterministic oracle-grounded scenario generators.

Each family implementation remains generator-only: it proposes scenarios,
interventions, and non-authoritative guesses without producing measurements.
"""

from . import generator_common as _common
from . import generator_encoder as _encoder
from . import generator_neuron as _neuron
from . import generator_mesh as _mesh
from . import generator_credit as _credit
from . import generator_memory as _memory

GENERATOR_NAME = _common.GENERATOR_NAME
GENERATOR_VERSION = _common.GENERATOR_VERSION
generator_block = _common.generator_block
SIGNAL_FAMILIES = _encoder.SIGNAL_FAMILIES
PERTURBATIONS = _encoder.PERTURBATIONS
make_signal = _encoder.make_signal
apply_perturbation = _encoder.apply_perturbation
propose_encoder_scenario = _encoder.propose_encoder_scenario
_ENCODER_HUNCH = _encoder._ENCODER_HUNCH
predict_encoder_winner = _encoder.predict_encoder_winner
STIMULI = _neuron.STIMULI
MAX_NEURON_STEPS = _neuron.MAX_NEURON_STEPS
propose_neuron_scenario = _neuron.propose_neuron_scenario
_finite_number = _neuron._finite_number
neuron_sample_count = _neuron.neuron_sample_count
build_current = _neuron.build_current
_NEURON_OPERATIONS = _neuron._NEURON_OPERATIONS
propose_neuron_intervention = _neuron.propose_neuron_intervention
predict_neuron_effect = _neuron.predict_neuron_effect
MESH_INTERVENTIONS = _mesh.MESH_INTERVENTIONS
_MESH_TEMPLATE = _mesh._MESH_TEMPLATE
propose_mesh_scenario = _mesh.propose_mesh_scenario
mesh_events = _mesh.mesh_events
propose_mesh_intervention = _mesh.propose_mesh_intervention
apply_mesh_intervention = _mesh.apply_mesh_intervention
predict_mesh_effect = _mesh.predict_mesh_effect
_shortest_excitatory_path = _mesh._shortest_excitatory_path
SITUATIONS = _credit.SITUATIONS
propose_reward_scenario = _credit.propose_reward_scenario
predict_reward_effect = _credit.predict_reward_effect
propose_memory_scenario = _memory.propose_memory_scenario
predict_memory_response = _memory.predict_memory_response

__all__ = tuple(name for name in globals() if not name.startswith("_"))
