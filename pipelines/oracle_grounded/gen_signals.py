"""Sensor-trace synthesis for the encoder family's generator side.

A scenario needs a signal before it can ask which encoding preserves it.
These builders produce that signal — one value per sample period, clamped to
[0, 1] — and the perturbations that degrade it. Both are generator territory:
the degraded trace *is* the scenario, not a measurement of anything.
"""

import math

from . import sim

SIGNAL_FAMILIES = ("baseline", "burst", "drift", "outlier", "periodic", "sparse_events")
PERTURBATIONS = ("none", "additive_noise", "dropout", "quantization", "gain_drift")


def _baseline_values(rng, sample_count, params):
    level = params["level"]
    values = []
    for _ in range(sample_count):
        values.append(level + params["noise"] * rng.symmetric_noise())
    return values


def _burst_values(rng, sample_count, params):
    burst_starts = params["burst_starts"]
    width = params["burst_width"]
    values = []
    for index in range(sample_count):
        inside = any(start <= index < start + width for start in burst_starts)
        base = params["high"] if inside else params["low"]
        values.append(base + params["noise"] * rng.symmetric_noise())
    return values


def _drift_values(rng, sample_count, params):
    start, end = params["start"], params["end"]
    values = []
    for index in range(sample_count):
        fraction = index / max(1, sample_count - 1)
        noise = params["noise"] * rng.symmetric_noise()
        values.append(start + (end - start) * fraction + noise)
    return values


def _outlier_values(rng, sample_count, params):
    values = []
    for index in range(sample_count):
        value = params["level"] + params["noise"] * rng.symmetric_noise()
        if index in params["outlier_at"]:
            value = params["outlier_level"]
        values.append(value)
    return values


def _periodic_values(rng, sample_count, params):
    values = []
    for index in range(sample_count):
        phase = 2.0 * math.pi * params["cycles"] * index / sample_count
        values.append(
            params["offset"]
            + params["amplitude"] * math.sin(phase)
            + params["noise"] * rng.symmetric_noise()
        )
    return values


def _sparse_event_values(rng, sample_count, params):
    values = []
    for index in range(sample_count):
        if index in params["event_at"]:
            values.append(params["event_level"])
        else:
            values.append(params["floor"] + params["noise"] * rng.symmetric_noise())
    return values


_SIGNAL_BUILDERS = {
    "baseline": _baseline_values,
    "burst": _burst_values,
    "drift": _drift_values,
    "outlier": _outlier_values,
    "periodic": _periodic_values,
    "sparse_events": _sparse_event_values,
}


def make_signal(family, rng, sample_count, params):
    """A sensor trace in [0, 1], one value per sample period."""
    builder = _SIGNAL_BUILDERS.get(family)
    if builder is None:
        raise ValueError(f"unknown signal family: {family}")
    values = builder(rng, sample_count, params)
    return [sim.clamp(value, 0.0, 1.0) for value in values]


def _additive_noise(values, rng, params):
    level = params["level"]
    return [sim.clamp(value + level * rng.symmetric_noise(), 0.0, 1.0) for value in values]


def _dropout(values, rng, params):
    keep = params["keep_probability"]
    return [value if rng.random() < keep else 0.0 for value in values]


def _quantization(values, _rng, params):
    steps = params["steps"]
    return [sim.clamp(round(value * (steps - 1)) / (steps - 1), 0.0, 1.0) for value in values]


def _gain_drift(values, _rng, params):
    span = params["span"]
    count = len(values)
    return [
        sim.clamp(value * (1.0 - span + 2.0 * span * index / max(1, count - 1)), 0.0, 1.0)
        for index, value in enumerate(values)
    ]


_PERTURBERS = {
    "additive_noise": _additive_noise,
    "dropout": _dropout,
    "quantization": _quantization,
    "gain_drift": _gain_drift,
}


def apply_perturbation(values, perturbation, rng, params):
    """Sensor-side degradation. Still generator territory: it is the scenario."""
    if perturbation == "none":
        return list(values)
    perturber = _PERTURBERS.get(perturbation)
    if perturber is None:
        raise ValueError(f"unknown perturbation: {perturbation}")
    return perturber(values, rng, params)
