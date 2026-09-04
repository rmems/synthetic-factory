"""Generator side: scenarios, interventions, and non-authoritative guesses.

Everything in this module is what a generator (GPT-5.6-Sol, Fable, Grok, or
the deterministic stand-in used for fixtures) is allowed to author. None of it
is a measurement. The candidate predictions are cheap structural heuristics
deliberately kept separate from the simulators in ``sim.py``, so that scoring a
candidate against the oracle is a real test and not a tautology.

If a hosted model replaces these functions, the contract it must satisfy is
unchanged: emit ``scenario``, ``intervention``, and ``candidate_prediction``,
and never emit anything under ``result``.

One sibling module per family carries the proposers; this facade re-exports
the whole generator surface and stamps the provenance block.
"""

from .gen_credit import SITUATIONS, predict_reward_effect, propose_reward_scenario
from .gen_encoder import predict_encoder_winner, propose_encoder_scenario
from .gen_memory import predict_memory_response, propose_memory_scenario
from .gen_mesh import (
    MESH_INTERVENTIONS,
    apply_mesh_intervention,
    mesh_events,
    predict_mesh_effect,
    propose_mesh_intervention,
    propose_mesh_scenario,
)
from .gen_neuron import (
    MAX_NEURON_STEPS,
    STIMULI,
    build_current,
    neuron_sample_count,
    predict_neuron_effect,
    propose_neuron_intervention,
    propose_neuron_scenario,
)
from .gen_signals import PERTURBATIONS, SIGNAL_FAMILIES, apply_perturbation, make_signal

GENERATOR_NAME = "deterministic-scenario-generator"
GENERATOR_VERSION = "1.0.0"

__all__ = [
    "GENERATOR_NAME",
    "GENERATOR_VERSION",
    "MAX_NEURON_STEPS",
    "MESH_INTERVENTIONS",
    "PERTURBATIONS",
    "SIGNAL_FAMILIES",
    "SITUATIONS",
    "STIMULI",
    "apply_mesh_intervention",
    "apply_perturbation",
    "build_current",
    "generator_block",
    "make_signal",
    "mesh_events",
    "neuron_sample_count",
    "predict_encoder_winner",
    "predict_memory_response",
    "predict_mesh_effect",
    "predict_neuron_effect",
    "predict_reward_effect",
    "propose_encoder_scenario",
    "propose_memory_scenario",
    "propose_mesh_intervention",
    "propose_mesh_scenario",
    "propose_neuron_intervention",
    "propose_neuron_scenario",
    "propose_reward_scenario",
]


def generator_block(seed, label, model=None):
    """The provenance block for whoever proposed the scenario."""
    return {
        "name": model or GENERATOR_NAME,
        "version": GENERATOR_VERSION,
        "role": "proposes scenarios, interventions, and non-authoritative predictions",
        "authoritative": False,
        "seed": int(seed),
        "label": label,
    }
