"""Public registry for the five oracle-grounded dataset families.

Implementation and invariant checks live in one cohesive module per family;
this facade preserves the original import surface used by generators, replay,
and validation.
"""

from . import family_common as _common
from . import sim
from . import family_encoder as _encoder
from . import family_neuron as _neuron
from . import family_mesh as _mesh
from . import family_credit as _credit
from . import family_memory as _memory

ENCODER_FAMILY = _common.ENCODER_FAMILY
NEURON_FAMILY = _common.NEURON_FAMILY
MESH_FAMILY = _common.MESH_FAMILY
CREDIT_FAMILY = _common.CREDIT_FAMILY
MEMORY_FAMILY = _common.MEMORY_FAMILY
FAMILY_NAMES = _common.FAMILY_NAMES
FamilySpec = _common.FamilySpec
ENCODER_UNITS = _encoder.ENCODER_UNITS
_encoder_propose = _encoder._encoder_propose
encoder_request = _encoder.encoder_request
_encoder_oracle = _encoder._encoder_oracle
_encoder_checks = _encoder._encoder_checks
NEURON_UNITS = _neuron.NEURON_UNITS
_neuron_propose = _neuron._neuron_propose
neuron_request = _neuron.neuron_request
_neuron_oracle = _neuron._neuron_oracle
_neuron_checks = _neuron._neuron_checks
MESH_UNITS = _mesh.MESH_UNITS
_mesh_propose = _mesh._mesh_propose
mesh_request = _mesh.mesh_request
_mesh_oracle = _mesh._mesh_oracle
_mesh_checks = _mesh._mesh_checks
CRITIC_UNITS = _credit.CRITIC_UNITS
PLASTICITY_UNITS = _credit.PLASTICITY_UNITS
_credit_propose = _credit._credit_propose
credit_request = _credit.credit_request
_credit_oracle = _credit._credit_oracle
_credit_checks = _credit._credit_checks
MEMORY_UNITS = _memory.MEMORY_UNITS
_memory_propose = _memory._memory_propose
memory_request = _memory.memory_request
_memory_oracle = _memory._memory_oracle
_memory_checks = _memory._memory_checks
ROUNDING_TOL = _neuron.ROUNDING_TOL
TIME_UNITS = _common.TIME_UNITS
ENERGY_UNITS = _common.ENERGY_UNITS
RATE_UNITS = _common.RATE_UNITS
DIMENSIONLESS = _common.DIMENSIONLESS
_measurement_matches = _common._measurement_matches
_trim_encoding = _encoder._trim_encoding
_encoder_reference = _encoder._encoder_reference
_neuron_reference = _neuron._neuron_reference
_intervened_parameters = _neuron._intervened_parameters
_mesh_reference = _mesh._mesh_reference
_critic_reference = _credit._critic_reference
_plasticity_reference = _credit._plasticity_reference
_stage_is_reference = _credit._stage_is_reference
_credit_critic_findings = _credit._credit_critic_findings
_credit_rule_findings = _credit._credit_rule_findings
_credit_update_findings = _credit._credit_update_findings
_credit_behavior_findings = _credit._credit_behavior_findings
DISTRACTOR_SHIFT_MS = _memory.DISTRACTOR_SHIFT_MS
_memory_ablation_changed = _memory._memory_ablation_changed
_shift_distractors = _memory._shift_distractors
_memory_trial_task = _memory._memory_trial_task
_memory_reference = _memory._memory_reference

# --------------------------------------------------------------------------
# Candidate scoring: was the generator's guess right? Never authoritative,
# but it is what makes these records useful as evaluation data.
# --------------------------------------------------------------------------


def _guess(record, key):
    candidate = record.get("candidate_prediction")
    if not isinstance(candidate, dict):
        return None
    return candidate.get(key)


def _score_encoder(record):
    predicted = _guess(record, "predicted_winner")
    return None if predicted is None else predicted == record["result"]["measured"]["winner"]


def _score_neuron(record):
    predicted = _guess(record, "predicted_direction")
    if predicted is None:
        return None
    return predicted == record["result"]["measured"]["delta"]["direction"]


def _score_mesh(record):
    predicted = _guess(record, "predicted_sink_reached")
    if predicted is None:
        return None
    return predicted == record["result"]["measured"]["after"]["sink_reached"]


def _score_credit(record):
    """Scored on which synapse moves most, not on valence or net direction.

    Valence is the sign of received minus expected, which is exactly how the
    critic defines it, and the net weight direction follows that sign whenever
    causal pre-post pairs dominate — both would be near-tautological. Which
    synapse gains the most depends on spike timing relative to the readout,
    which the generator does not simulate.
    """
    predicted = _guess(record, "predicted_strongest_synapse")
    if predicted is None:
        return None
    deltas = record["result"]["measured"]["plasticity"]["weight_deltas"]
    if not deltas or all(abs(delta) <= sim.WEIGHT_UPDATE_EPS for delta in deltas):
        return None
    strongest = max(range(len(deltas)), key=lambda index: (abs(deltas[index]), -index))
    return predicted == strongest


def _score_memory(record):
    predicted = _guess(record, "predicted_response")
    if predicted is None:
        return None
    return predicted == record["result"]["measured"]["baseline"]["response"]


SPECS = {
    ENCODER_FAMILY: FamilySpec(
        name=ENCODER_FAMILY,
        runtimes=("axon-encoder",),
        oracle_type="spike-encoder",
        units=ENCODER_UNITS,
        propose=_encoder_propose,
        build_request=encoder_request,
        build_oracle=_encoder_oracle,
        checks=_encoder_checks,
        score=_score_encoder,
    ),
    NEURON_FAMILY: FamilySpec(
        name=NEURON_FAMILY,
        runtimes=("neuromod",),
        oracle_type="neuron-simulation",
        units=NEURON_UNITS,
        propose=_neuron_propose,
        build_request=neuron_request,
        build_oracle=_neuron_oracle,
        checks=_neuron_checks,
        score=_score_neuron,
    ),
    MESH_FAMILY: FamilySpec(
        name=MESH_FAMILY,
        runtimes=("synaptic-mesh",),
        oracle_type="network-simulation",
        units=MESH_UNITS,
        propose=_mesh_propose,
        build_request=mesh_request,
        build_oracle=_mesh_oracle,
        checks=_mesh_checks,
        score=_score_mesh,
    ),
    CREDIT_FAMILY: FamilySpec(
        name=CREDIT_FAMILY,
        runtimes=("limbic-critic", "plasticity-lab"),
        oracle_type="critic-plasticity-chain",
        units={"critic": CRITIC_UNITS, "plasticity": PLASTICITY_UNITS},
        propose=_credit_propose,
        build_request=credit_request,
        build_oracle=_credit_oracle,
        checks=_credit_checks,
        score=_score_credit,
    ),
    MEMORY_FAMILY: FamilySpec(
        name=MEMORY_FAMILY,
        runtimes=("recurrent-snn",),
        oracle_type="recurrent-snn",
        units=MEMORY_UNITS,
        propose=_memory_propose,
        build_request=memory_request,
        build_oracle=_memory_oracle,
        checks=_memory_checks,
        score=_score_memory,
    ),
}

ALL_RUNTIMES = tuple(dict.fromkeys(runtime for spec in SPECS.values() for runtime in spec.runtimes))


def spec_for(family):
    if family not in SPECS:
        raise KeyError(f"unknown dataset family: {family}")
    return SPECS[family]


def spec_for_profile(family, profile=None):
    if profile is None:
        return spec_for(family)
    from . import native_profiles
    return native_profiles.spec_for(family, profile)


def spec_for_record(record):
    return spec_for_profile(record['family'], record['scenario'].get('profile'))
