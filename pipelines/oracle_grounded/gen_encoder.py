"""Generator side of family 1: spike-encoder-equivalence-pairs.

Proposes a sensor scenario — a signal family, a perturbation, and the pair of
encodings under comparison — plus a structural hunch about the winner. The
hunch never runs an encoder; scoring it against the oracle stays a real test.
"""

from . import sim
from .gen_signals import PERTURBATIONS, SIGNAL_FAMILIES, apply_perturbation, make_signal


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


def _sparse_event_params(rng, sample_count):
    return {
        "floor": rng.uniform(0.0, 0.06),
        "event_level": rng.uniform(0.7, 1.0),
        "event_at": sorted(rng.sample(range(sample_count), rng.randint(2, 6))),
        "noise": rng.uniform(0.0, 0.02),
    }


_SIGNAL_PARAM_BUILDERS = {
    "baseline": _baseline_params,
    "burst": _burst_params,
    "drift": _drift_params,
    "outlier": _outlier_params,
    "periodic": _periodic_params,
}


def _additive_noise_params(rng):
    return {"level": rng.uniform(0.05, 0.25)}


def _dropout_params(rng):
    return {"keep_probability": rng.uniform(0.6, 0.95)}


def _quantization_params(rng):
    return {"steps": rng.randint(3, 8)}


def _gain_drift_params(rng):
    return {"span": rng.uniform(0.1, 0.4)}


_PERTURBATION_PARAM_BUILDERS = {
    "additive_noise": _additive_noise_params,
    "dropout": _dropout_params,
    "quantization": _quantization_params,
    "gain_drift": _gain_drift_params,
}


def _perturbation_params(perturbation, rng):
    builder = _PERTURBATION_PARAM_BUILDERS.get(perturbation)
    if builder is None:
        return {}
    return builder(rng)


def propose_encoder_scenario(rng, sample_count=64, sample_ms=10.0):
    family = rng.choice(SIGNAL_FAMILIES)
    param_builder = _SIGNAL_PARAM_BUILDERS.get(family, _sparse_event_params)
    params = param_builder(rng, sample_count)

    perturbation = rng.choice(PERTURBATIONS)
    perturbation_params = _perturbation_params(perturbation, rng)

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
