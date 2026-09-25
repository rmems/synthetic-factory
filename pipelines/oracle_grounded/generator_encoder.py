"""Encoder scenario proposals."""

import math

from . import sim
from .generator_common import PERTURBATIONS, SIGNAL_FAMILIES

# --------------------------------------------------------------------------
# Family 1: sensor scenarios for encoder comparison
# --------------------------------------------------------------------------


def _baseline_signal(rng, sample_count, params):
    return [
        params["level"] + params["noise"] * rng.symmetric_noise()
        for _ in range(sample_count)
    ]


def _burst_signal(rng, sample_count, params):
    values = []
    for index in range(sample_count):
        inside = any(
            start <= index < start + params["burst_width"]
            for start in params["burst_starts"]
        )
        base = params["high"] if inside else params["low"]
        values.append(base + params["noise"] * rng.symmetric_noise())
    return values


def _drift_signal(rng, sample_count, params):
    start, end = params["start"], params["end"]
    return [
        start
        + (end - start) * index / max(1, sample_count - 1)
        + params["noise"] * rng.symmetric_noise()
        for index in range(sample_count)
    ]


def _outlier_signal(rng, sample_count, params):
    values = []
    for index in range(sample_count):
        value = params["level"] + params["noise"] * rng.symmetric_noise()
        values.append(params["outlier_level"] if index in params["outlier_at"] else value)
    return values


def _periodic_signal(rng, sample_count, params):
    values = []
    for index in range(sample_count):
        phase = 2.0 * math.pi * params["cycles"] * index / sample_count
        values.append(
            params["offset"]
            + params["amplitude"] * math.sin(phase)
            + params["noise"] * rng.symmetric_noise()
        )
    return values


def _sparse_signal(rng, sample_count, params):
    values = []
    for index in range(sample_count):
        if index in params["event_at"]:
            values.append(params["event_level"])
        else:
            values.append(params["floor"] + params["noise"] * rng.symmetric_noise())
    return values


_SIGNAL_BUILDERS = {
    "baseline": _baseline_signal,
    "burst": _burst_signal,
    "drift": _drift_signal,
    "outlier": _outlier_signal,
    "periodic": _periodic_signal,
    "sparse_events": _sparse_signal,
}


def make_signal(family, rng, sample_count, params):
    """A sensor trace in [0, 1], one value per sample period."""
    try:
        builder = _SIGNAL_BUILDERS[family]
    except KeyError as exc:
        raise ValueError(f"unknown signal family: {family}") from exc
    return [sim.clamp(value, 0.0, 1.0) for value in builder(rng, sample_count, params)]


def _no_perturbation(values, _rng, _params):
    return list(values)


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


_PERTURBATION_FNS = {
    "none": _no_perturbation,
    "additive_noise": _additive_noise,
    "dropout": _dropout,
    "quantization": _quantization,
    "gain_drift": _gain_drift,
}


def apply_perturbation(values, perturbation, rng, params):
    """Sensor-side degradation. Still generator territory: it is the scenario."""
    try:
        apply = _PERTURBATION_FNS[perturbation]
    except KeyError as exc:
        raise ValueError(f"unknown perturbation: {perturbation}") from exc
    return apply(values, rng, params)


def _baseline_params(rng, _sample_count):
    return {"level": rng.uniform(0.35, 0.65), "noise": rng.uniform(0.02, 0.12)}


def _burst_params(rng, sample_count):
    return {
        "low": rng.uniform(0.05, 0.2),
        "high": rng.uniform(0.75, 0.98),
        "burst_width": rng.randint(3, 7),
        "burst_starts": sorted(rng.sample(range(2, sample_count - 8), rng.randint(1, 3))),
        "noise": rng.uniform(0.01, 0.06),
    }


def _drift_params(rng, _sample_count):
    return {
        "start": rng.uniform(0.05, 0.35),
        "end": rng.uniform(0.6, 0.95),
        "noise": rng.uniform(0.01, 0.06),
    }


def _outlier_params(rng, sample_count):
    return {
        "level": rng.uniform(0.3, 0.6),
        "noise": rng.uniform(0.01, 0.05),
        "outlier_at": sorted(rng.sample(range(sample_count), rng.randint(2, 5))),
        "outlier_level": rng.uniform(0.9, 1.0),
    }


def _periodic_params(rng, _sample_count):
    return {
        "offset": rng.uniform(0.4, 0.6),
        "amplitude": rng.uniform(0.2, 0.4),
        "cycles": rng.randint(2, 7),
        "noise": rng.uniform(0.01, 0.05),
    }


def _sparse_params(rng, sample_count):
    return {
        "floor": rng.uniform(0.0, 0.06),
        "event_level": rng.uniform(0.7, 1.0),
        "event_at": sorted(rng.sample(range(sample_count), rng.randint(2, 6))),
        "noise": rng.uniform(0.0, 0.02),
    }


_SCENARIO_PARAMS = {
    "baseline": _baseline_params,
    "burst": _burst_params,
    "drift": _drift_params,
    "outlier": _outlier_params,
    "periodic": _periodic_params,
    "sparse_events": _sparse_params,
}


def _perturbation_params(rng, perturbation):
    if perturbation == "additive_noise":
        return {"level": rng.uniform(0.05, 0.25)}
    if perturbation == "dropout":
        return {"keep_probability": rng.uniform(0.6, 0.95)}
    if perturbation == "quantization":
        return {"steps": rng.randint(3, 8)}
    if perturbation == "gain_drift":
        return {"span": rng.uniform(0.1, 0.4)}
    return {}


def propose_encoder_scenario(rng, sample_count=64, sample_ms=10.0):
    family = rng.choice(SIGNAL_FAMILIES)
    params = _SCENARIO_PARAMS[family](rng, sample_count)
    perturbation = rng.choice(PERTURBATIONS)
    perturbation_params = _perturbation_params(rng, perturbation)
    clean = make_signal(family, rng, sample_count, params)
    observed = apply_perturbation(clean, perturbation, rng, perturbation_params)
    encodings = rng.sample(sim.ENCODINGS, 2)
    return {
        "signal_family": family,
        "signal_parameters": params,
        "perturbation": {"kind": perturbation, "parameters": perturbation_params},
        "sample_count": sample_count,
        "sample_ms": sample_ms,
        "signal": observed,
        "encoding_pair": list(encodings),
        "question": (
            f"Which encoding preserves more of this {family} sensor trace: "
            f"{encodings[0]} or {encodings[1]}?"
        ),
    }


# Structural intuitions only. They are wrong often enough to be worth scoring.
_ENCODER_HUNCH = {
    "baseline": "rate",
    "burst": "delta",
    "drift": "delta",
    "outlier": "latency",
    "periodic": "temporal",
    "sparse_events": "delta",
}


def predict_encoder_winner(scenario):
    pair = scenario["encoding_pair"]
    hunch = _ENCODER_HUNCH.get(scenario["signal_family"])
    winner = hunch if hunch in pair else pair[0]
    return {
        "kind": "non_authoritative_guess",
        "predicted_winner": winner,
        "basis": (
            f"structural hunch for {scenario['signal_family']} signals; "
            "no encoder was executed to produce this"
        ),
    }
