"""Deterministic critic and plasticity reference simulation."""

import math
from .sim_common import WEIGHT_UPDATE_EPS, clamp
from .sim_mesh import MeshBounds, mesh_node, simulate_mesh
from .sim_neuron import _optional_delta

# --------------------------------------------------------------------------
# Family 4 oracle: critic -> plasticity (stand-in for limbic-critic + plasticity-lab)
# --------------------------------------------------------------------------

CRITIC_DEFAULTS = {
    "rpe_gain": 1.4,
    "tonic_dopamine": 0.35,
    "serotonin_baseline": 0.5,
    "risk_weight": 0.35,
    "novelty_weight": 0.6,
    "effort_weight": 0.25,
    "arousal_gain": 1.1,
}


def critic_config(overrides=None):
    config = dict(CRITIC_DEFAULTS)
    if overrides:
        config.update(overrides)
    return config


def run_critic(outcome, config):
    """Map an outcome to modulator levels.

    Units: ``reward_prediction_error`` is in reward units; ``dopamine_phasic``
    is a signed normalised burst/dip in [-1, 1]; the tonic modulator levels are
    normalised to [0, 1]. These are the reference critic's definitions, not a
    claim about `limbic-critic`.
    """
    expected = float(outcome["expected_value"])
    received = float(outcome["received_reward"])
    risk = clamp(float(outcome.get("risk", 0.0)), 0.0, 1.0)
    novelty = clamp(float(outcome.get("novelty", 0.0)), 0.0, 1.0)
    effort = clamp(float(outcome.get("effort", 0.0)), 0.0, 1.0)

    rpe = received - expected
    phasic = math.tanh(config["rpe_gain"] * rpe)
    dopamine = clamp(config["tonic_dopamine"] + 0.5 * phasic, 0.0, 1.0)
    serotonin = clamp(
        config["serotonin_baseline"]
        - config["risk_weight"] * risk
        + config["effort_weight"] * (1.0 - effort),
        0.0,
        1.0,
    )
    acetylcholine = clamp(config["novelty_weight"] * novelty + 0.2 * risk, 0.0, 1.0)
    arousal = math.tanh(config["arousal_gain"] * abs(rpe))
    norepinephrine = clamp(arousal * 0.8 + 0.2 * risk, 0.0, 1.0)
    if rpe > 1e-9:
        valence = "positive"
    elif rpe < -1e-9:
        valence = "negative"
    else:
        valence = "neutral"
    return {
        "reward_prediction_error": rpe,
        "dopamine_phasic": phasic,
        "dopamine": dopamine,
        "serotonin": serotonin,
        "acetylcholine": acetylcholine,
        "norepinephrine": norepinephrine,
        "valence": valence,
    }


PLASTICITY_DEFAULTS = {
    "learning_rate": 0.12,
    "a_plus": 1.0,
    "a_minus": 0.8,
    "tau_plus_ms": 18.0,
    "tau_minus_ms": 22.0,
    "tau_eligibility_ms": 240.0,
    "w_min": 0.0,
    "w_max": 1.5,
    "synapse_delay_ms": 1.0,
    "dt_ms": 0.5,
    "modulatory_gain_ach": 0.5,
    "modulatory_gain_ne": 0.3,
    "duration_ms": 220.0,
}


def plasticity_config(overrides=None):
    config = dict(PLASTICITY_DEFAULTS)
    if overrides:
        config.update(overrides)
    return config


def _plasticity_circuit(weights, pre_spikes, config, readout_overrides=None):
    """Run the pre-synaptic trains into the readout neuron at these weights."""
    readout = mesh_node("readout", tau_ms=10.0, v_threshold=1.0, t_refractory_ms=3.0)
    if readout_overrides:
        readout.update(readout_overrides)
    events = []
    for index, times in enumerate(pre_spikes):
        weight = weights[index]
        for time_ms in times:
            events.append(
                {
                    "target": "readout",
                    "t_ms": time_ms + config["synapse_delay_ms"],
                    "amplitude": weight,
                }
            )
    events.sort(key=lambda item: (item["t_ms"], item["amplitude"]))
    bounds = MeshBounds(config["duration_ms"], dt_ms=config["dt_ms"])
    result = simulate_mesh([readout], [], events, bounds)
    post = result["spikes_by_node"]["readout"]
    duration_s = config["duration_ms"] / 1000.0
    return {
        "spike_count": len(post),
        "spike_times_ms": post,
        "first_spike_ms": post[0] if post else None,
        "output_rate_hz": len(post) / duration_s if duration_s else 0.0,
    }


def _pair_contribution(config, gap, post_time):
    """One pre/post pair's STDP contribution, decayed to the reward time."""
    if gap > 0:
        contribution = config["a_plus"] * math.exp(-gap / config["tau_plus_ms"])
    elif gap < 0:
        contribution = -config["a_minus"] * math.exp(gap / config["tau_minus_ms"])
    else:
        return 0.0
    reward_time = config["duration_ms"]
    return contribution * math.exp(-(reward_time - post_time) / config["tau_eligibility_ms"])


def _synapse_trace(pre_times, post_spikes, config):
    total = 0.0
    for pre_time in pre_times:
        for post_time in post_spikes:
            total += _pair_contribution(config, post_time - pre_time, post_time)
    return total


def eligibility_traces(weights, pre_spikes, post_spikes, config):
    """Per-synapse STDP eligibility, decayed to the reward time.

    Pair-based STDP: a post spike after a pre spike potentiates, a post spike
    before a pre spike depresses. The pair contribution is then decayed by the
    eligibility time constant from the post spike to the end of the episode,
    which is when the modulator arrives.
    """
    return [
        _synapse_trace(pre_spikes[index], post_spikes, config)
        for index in range(len(weights))
    ]


def run_plasticity(weights, pre_spikes, modulators, config):
    """Three-factor update that is actually applied, then re-measured.

    The returned ``weights_after`` are written into a second run of the same
    circuit on the same input, so ``post_update_behavior`` is a measurement of
    the updated network rather than an extrapolation.
    """
    before = _plasticity_circuit(weights, pre_spikes, config)
    traces = eligibility_traces(weights, pre_spikes, before["spike_times_ms"], config)
    gain = (
        1.0
        + config["modulatory_gain_ach"] * modulators["acetylcholine"]
        + config["modulatory_gain_ne"] * modulators["norepinephrine"]
    )
    deltas = []
    updated = []
    for index, weight in enumerate(weights):
        raw_delta = config["learning_rate"] * traces[index] * modulators["dopamine_phasic"] * gain
        new_weight = clamp(weight + raw_delta, config["w_min"], config["w_max"])
        deltas.append(new_weight - weight)
        updated.append(new_weight)
    after = _plasticity_circuit(updated, pre_spikes, config)
    applied = any(abs(delta) > WEIGHT_UPDATE_EPS for delta in deltas)
    return {
        "weights_before": list(weights),
        "weights_after": updated,
        "weight_deltas": deltas,
        "eligibility": traces,
        "modulatory_gain": gain,
        "update_applied": applied,
        "update_rule": "dw = lr * eligibility * dopamine_phasic * modulatory_gain",
        "pre_update_behavior": before,
        "post_update_behavior": after,
        "behavior_delta": {
            "spike_count_delta": after["spike_count"] - before["spike_count"],
            "output_rate_delta_hz": after["output_rate_hz"] - before["output_rate_hz"],
            "first_spike_shift_ms": _optional_delta(
                after["first_spike_ms"], before["first_spike_ms"]
            ),
        },
    }
