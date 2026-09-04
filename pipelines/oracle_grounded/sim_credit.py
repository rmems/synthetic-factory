"""Family 4 oracle: critic -> plasticity (stand-in for limbic-critic + plasticity-lab).

The reference critic maps an outcome to modulator levels; the plasticity side
computes STDP eligibility traces, applies the three-factor update, and then
re-measures the updated circuit so the reported behaviour change is a
measurement rather than an extrapolation. Every function is pure and
deterministic: same inputs, same floats.
"""

import math

from .sim_core import clamp, optional_delta
from .sim_mesh import MeshLimits, MeshNetwork, mesh_node, simulate_mesh

# Smallest weight change that counts as an applied update. It sits just above
# the rounding step of the stored records so that "the update was applied"
# means the same thing to the simulator and to the validator.
WEIGHT_UPDATE_EPS = 5e-6

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
    return {
        "reward_prediction_error": rpe,
        "dopamine_phasic": phasic,
        "dopamine": dopamine,
        "serotonin": serotonin,
        "acetylcholine": acetylcholine,
        "norepinephrine": norepinephrine,
        "valence": "positive" if rpe > 1e-9 else ("negative" if rpe < -1e-9 else "neutral"),
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


def plasticity_circuit(weights, pre_spikes, config, readout_overrides=None):
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
    result = simulate_mesh(
        MeshNetwork([readout], []),
        events,
        config["duration_ms"],
        limits=MeshLimits(dt_ms=config["dt_ms"]),
    )
    post = result["spikes_by_node"]["readout"]
    duration_s = config["duration_ms"] / 1000.0
    return {
        "spike_count": len(post),
        "spike_times_ms": post,
        "first_spike_ms": post[0] if post else None,
        "output_rate_hz": len(post) / duration_s if duration_s else 0.0,
    }


def _pair_contribution(gap, config):
    """One pre/post pair's STDP contribution, or None for a coincident pair."""
    if gap > 0:
        return config["a_plus"] * math.exp(-gap / config["tau_plus_ms"])
    if gap < 0:
        return -config["a_minus"] * math.exp(gap / config["tau_minus_ms"])
    return None


def _synapse_eligibility(pre_times, post_spikes, config):
    """One synapse's pair contributions, decayed to the reward time."""
    reward_time = config["duration_ms"]
    tau_e = config["tau_eligibility_ms"]
    total = 0.0
    for pre_time in pre_times:
        for post_time in post_spikes:
            contribution = _pair_contribution(post_time - pre_time, config)
            if contribution is None:
                continue
            total += contribution * math.exp(-(reward_time - post_time) / tau_e)
    return total


def eligibility_traces(weights, pre_spikes, post_spikes, config):
    """Per-synapse STDP eligibility, decayed to the reward time.

    Pair-based STDP: a post spike after a pre spike potentiates, a post spike
    before a pre spike depresses. The pair contribution is then decayed by the
    eligibility time constant from the post spike to the end of the episode,
    which is when the modulator arrives.
    """
    return [
        _synapse_eligibility(pre_spikes[index], post_spikes, config)
        for index in range(len(weights))
    ]


def run_plasticity(weights, pre_spikes, modulators, config):
    """Three-factor update that is actually applied, then re-measured.

    The returned ``weights_after`` are written into a second run of the same
    circuit on the same input, so ``post_update_behavior`` is a measurement of
    the updated network rather than an extrapolation.
    """
    before = plasticity_circuit(weights, pre_spikes, config)
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
    after = plasticity_circuit(updated, pre_spikes, config)
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
            "first_spike_shift_ms": optional_delta(
                after["first_spike_ms"], before["first_spike_ms"]
            ),
        },
    }
