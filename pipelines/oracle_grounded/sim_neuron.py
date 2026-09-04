"""Family 2 oracle: adaptive LIF neuron (stand-in for ``neuromod``).

A forward-Euler leaky integrate-and-fire neuron with spike-frequency
adaptation and neuromodulatory gain/threshold hooks, plus the summary and
before/after comparison used to measure an intervention's consequence.
Every function is pure and deterministic: same inputs, same floats.
"""

import math
from itertools import pairwise

from .sim_core import optional_delta

NEURON_DEFAULTS = {
    "v_rest": 0.0,
    "v_reset": 0.0,
    "v_threshold": 1.0,
    "tau_m_ms": 12.0,
    "r_m": 1.0,
    "t_refractory_ms": 3.0,
    "adaptation_b": 0.08,
    "tau_w_ms": 60.0,
    "input_scale": 1.0,
    "neuromod_gain": 1.0,
    "neuromod_threshold_shift": 0.0,
    "dt_ms": 0.5,
    "v_floor": -2.0,
}

# Which neuron parameter each intervention target moves. Interventions are
# proposed by the generator; the mapping (and therefore the physics) is
# oracle-side.
INTERVENTION_TARGETS = {
    "threshold": "v_threshold",
    "decay": "tau_m_ms",
    "adaptation": "adaptation_b",
    "refractory": "t_refractory_ms",
    "input_intensity": "input_scale",
    "neuromodulatory_state": "neuromod_gain",
}


def neuron_config(overrides=None):
    config = dict(NEURON_DEFAULTS)
    if overrides:
        config.update(overrides)
    return config


def _leaked_membrane(membrane, current, adaptation, config):
    """Leak toward rest under drive, then apply the hard membrane floor."""
    step = (-(membrane - config["v_rest"]) + current - adaptation) * (
        config["dt_ms"] / config["tau_m_ms"]
    )
    updated = membrane + step
    if updated < config["v_floor"]:
        return config["v_floor"]
    return updated


def _refractory_steps(config):
    return max(0, int(round(config["t_refractory_ms"] / config["dt_ms"])))


def _step_neuron(state, current, config, threshold):
    """One forward-Euler step, in this order: expire refractory, leak, inject,
    adapt-decay, threshold test. Mutates ``state``; returns the membrane value
    to trace (pre-reset) and whether the neuron spiked."""
    if state["refractory_left"] > 0:
        state["refractory_left"] -= 1
        state["v"] = config["v_reset"]
    else:
        state["v"] = _leaked_membrane(state["v"], current, state["w"], config)
    state["w"] += (-state["w"]) * (config["dt_ms"] / config["tau_w_ms"])
    trace_value = state["v"]
    spiked = state["refractory_left"] <= 0 and state["v"] >= threshold
    if spiked:
        state["v"] = config["v_reset"]
        state["w"] += config["adaptation_b"]
        state["refractory_left"] = _refractory_steps(config)
    return trace_value, spiked


def simulate_neuron(config, input_current, trace_points=48):
    """Adaptive exponential-free LIF, forward Euler.

    ``input_current`` is one value per ``dt_ms`` step.
    """
    threshold = config["v_threshold"] + config["neuromod_threshold_shift"]
    state = {"v": config["v_rest"], "w": 0.0, "refractory_left": 0}
    spikes = []
    trace = []
    for index, raw in enumerate(input_current):
        current = raw * config["input_scale"] * config["neuromod_gain"] * config["r_m"]
        trace_value, spiked = _step_neuron(state, current, config, threshold)
        trace.append(trace_value)
        if spiked:
            spikes.append(index * config["dt_ms"])
    return _neuron_summary(spikes, trace, config, (len(input_current), trace_points))


def _cv_isi(intervals, mean_isi):
    """Coefficient of variation of the ISIs, or None when it is undefined."""
    spread_defined = len(intervals) > 1 and bool(mean_isi)
    if not spread_defined:
        return None
    variance = sum((item - mean_isi) ** 2 for item in intervals) / len(intervals)
    return math.sqrt(variance) / mean_isi


def _adaptation_index(intervals):
    """Last-to-first ISI ratio, or None when there are too few intervals."""
    ratio_defined = len(intervals) >= 2 and bool(intervals[0])
    if not ratio_defined:
        return None
    return intervals[-1] / intervals[0]


def _neuron_summary(spikes, trace, config, span):
    steps, trace_points = span
    dt_ms = config["dt_ms"]
    duration_ms = steps * dt_ms
    intervals = [b - a for a, b in pairwise(spikes)]
    mean_isi = (sum(intervals) / len(intervals)) if intervals else None
    stride = max(1, math.ceil(len(trace) / trace_points)) if trace else 1
    return {
        "spike_count": len(spikes),
        "spike_times_ms": spikes,
        "first_spike_ms": spikes[0] if spikes else None,
        "last_spike_ms": spikes[-1] if spikes else None,
        "mean_rate_hz": len(spikes) / (duration_ms / 1000.0) if duration_ms else 0.0,
        "mean_isi_ms": mean_isi,
        "cv_isi": _cv_isi(intervals, mean_isi),
        "adaptation_index": _adaptation_index(intervals),
        "v_mean": (sum(trace) / len(trace)) if trace else None,
        "v_max": max(trace) if trace else None,
        "v_min": min(trace) if trace else None,
        "v_trace": trace[::stride],
        "v_trace_stride_ms": stride * dt_ms,
        "duration_ms": duration_ms,
    }


def compare_neuron_states(before, after):
    """The measured consequence of an intervention, as a signed delta."""
    delta_count = after["spike_count"] - before["spike_count"]
    if delta_count > 0:
        direction = "increases_firing"
    elif delta_count < 0:
        direction = "decreases_firing"
    else:
        direction = "unchanged_firing"
    return {
        "spike_count_delta": delta_count,
        "mean_rate_delta_hz": after["mean_rate_hz"] - before["mean_rate_hz"],
        "first_spike_shift_ms": optional_delta(after["first_spike_ms"], before["first_spike_ms"]),
        "mean_isi_delta_ms": optional_delta(after["mean_isi_ms"], before["mean_isi_ms"]),
        "v_mean_delta": optional_delta(after["v_mean"], before["v_mean"]),
        "direction": direction,
        "silenced": before["spike_count"] > 0 and after["spike_count"] == 0,
        "unsilenced": before["spike_count"] == 0 and after["spike_count"] > 0,
    }
