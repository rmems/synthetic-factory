"""Deterministic adaptive-LIF neuron reference simulation."""

import math
from itertools import pairwise


# --------------------------------------------------------------------------
# Family 2 oracle: adaptive LIF neuron (stand-in for `neuromod`)
# --------------------------------------------------------------------------

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


class _NeuronRun:
    """Mutable in-flight state for one forward-Euler LIF integration."""

    def __init__(self, config):
        self.dt_ms = config["dt_ms"]
        self.tau_m = config["tau_m_ms"]
        self.tau_w = config["tau_w_ms"]
        self.v_rest = config["v_rest"]
        self.v_reset = config["v_reset"]
        self.v_floor = config["v_floor"]
        self.threshold = config["v_threshold"] + config["neuromod_threshold_shift"]
        self.refractory_steps = max(0, int(round(config["t_refractory_ms"] / self.dt_ms)))
        self.input_scale = config["input_scale"] * config["neuromod_gain"] * config["r_m"]
        self.adaptation_b = config["adaptation_b"]
        self.membrane = self.v_rest
        self.adaptation = 0.0
        self.refractory_left = 0
        self.spikes = []
        self.trace = []

    def _leak_and_inject(self, current):
        if self.refractory_left > 0:
            self.refractory_left -= 1
            self.membrane = self.v_reset
            return
        self.membrane += (
            -(self.membrane - self.v_rest) + current - self.adaptation
        ) * (self.dt_ms / self.tau_m)
        if self.membrane < self.v_floor:
            self.membrane = self.v_floor

    def step(self, index, raw):
        current = raw * self.input_scale
        self._leak_and_inject(current)
        self.adaptation += (-self.adaptation) * (self.dt_ms / self.tau_w)
        self.trace.append(self.membrane)
        if self.refractory_left <= 0 and self.membrane >= self.threshold:
            self.spikes.append(index * self.dt_ms)
            self.membrane = self.v_reset
            self.adaptation += self.adaptation_b
            self.refractory_left = self.refractory_steps


def simulate_neuron(config, input_current, trace_points=48):
    """Adaptive exponential-free LIF, forward Euler.

    Per step, in this order: expire refractory, leak, inject, adapt-decay,
    threshold test. ``input_current`` is one value per ``dt_ms`` step.
    """
    run = _NeuronRun(config)
    for index, raw in enumerate(input_current):
        run.step(index, raw)
    return _neuron_summary(run, len(input_current), trace_points)


def _cv_isi(intervals, mean_isi):
    if len(intervals) <= 1 or not mean_isi:
        return None
    variance = sum((item - mean_isi) ** 2 for item in intervals) / len(intervals)
    return math.sqrt(variance) / mean_isi


def _adaptation_index(intervals):
    if len(intervals) < 2 or not intervals[0]:
        return None
    return intervals[-1] / intervals[0]


def _neuron_summary(run, steps, trace_points):
    spikes = run.spikes
    trace = run.trace
    duration_ms = steps * run.dt_ms
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
        "v_trace_stride_ms": stride * run.dt_ms,
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
        "first_spike_shift_ms": _optional_delta(after["first_spike_ms"], before["first_spike_ms"]),
        "mean_isi_delta_ms": _optional_delta(after["mean_isi_ms"], before["mean_isi_ms"]),
        "v_mean_delta": _optional_delta(after["v_mean"], before["v_mean"]),
        "direction": direction,
        "silenced": before["spike_count"] > 0 and after["spike_count"] == 0,
        "unsilenced": before["spike_count"] == 0 and after["spike_count"] > 0,
    }


def _optional_delta(after, before):
    if after is None or before is None:
        return None
    return after - before
