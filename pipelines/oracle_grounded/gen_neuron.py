"""Generator side of family 2: neuron-dynamics-counterfactuals.

Proposes a stimulus and baseline parameter set, validates a stored scenario
back into a bounded sample count, rebuilds the stimulus waveform, and offers a
textbook sign-of-effect hunch for an intervention. The waveform builder is
shared with the oracle so both sides integrate exactly the same current.
"""

import math

from . import sim

STIMULI = ("step", "pulse_train", "ramp")
# A retained scenario must be small enough to validate and reproduce without
# turning one JSON record into an unbounded allocation.  Generated fixtures use
# 600 samples; this ceiling leaves ample headroom for real evaluation records.
MAX_NEURON_STEPS = 1_000_000


def _step_stimulus_params(rng, duration_ms):
    return {
        "amplitude": rng.uniform(1.1, 2.4),
        "onset_ms": rng.uniform(10.0, 40.0),
        "offset_ms": duration_ms - rng.uniform(10.0, 60.0),
    }


def _pulse_train_stimulus_params(rng, _duration_ms):
    return {
        "amplitude": rng.uniform(1.6, 3.2),
        "period_ms": rng.uniform(15.0, 45.0),
        "width_ms": rng.uniform(4.0, 12.0),
        "onset_ms": rng.uniform(5.0, 25.0),
    }


def _ramp_stimulus_params(rng, _duration_ms):
    return {
        "peak": rng.uniform(1.4, 3.0),
        "onset_ms": rng.uniform(5.0, 30.0),
    }


_STIMULUS_PARAM_BUILDERS = {
    "step": _step_stimulus_params,
    "pulse_train": _pulse_train_stimulus_params,
}


def propose_neuron_scenario(rng, duration_ms=300.0, dt_ms=0.5):
    stimulus = rng.choice(STIMULI)
    param_builder = _STIMULUS_PARAM_BUILDERS.get(stimulus, _ramp_stimulus_params)
    params = param_builder(rng, duration_ms)
    baseline = {
        "v_threshold": rng.uniform(0.85, 1.25),
        "tau_m_ms": rng.uniform(8.0, 20.0),
        "adaptation_b": rng.uniform(0.02, 0.14),
        "t_refractory_ms": rng.uniform(1.5, 5.0),
        "input_scale": rng.uniform(0.8, 1.3),
        "neuromod_gain": 1.0,
    }
    return {
        "stimulus": {"kind": stimulus, "parameters": params},
        "duration_ms": duration_ms,
        "dt_ms": dt_ms,
        "baseline_parameters": baseline,
        "question": "How does the intervention change this neuron's spiking?",
    }


def _finite_number(value, name):
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a finite number")
    if not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number")
    if not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    return value


def _require_positive_timing(duration_ms, dt_ms):
    if duration_ms <= 0:
        raise ValueError("duration_ms and dt_ms must be positive")
    if dt_ms <= 0:
        raise ValueError("duration_ms and dt_ms must be positive")


def _bounded_step_count(duration_ms, dt_ms):
    _require_positive_timing(duration_ms, dt_ms)
    ratio = duration_ms / dt_ms
    if not 1 <= ratio <= MAX_NEURON_STEPS:
        raise ValueError(f"duration_ms / dt_ms must be in [1, {MAX_NEURON_STEPS}]")
    steps = int(round(ratio))
    if not 1 <= steps <= MAX_NEURON_STEPS:
        raise ValueError(f"rounded neuron sample count must be in [1, {MAX_NEURON_STEPS}]")
    return steps


# Parameters every stimulus kind must carry to be reproducible.
_REQUIRED_STIMULUS_PARAMS = {
    "step": ("amplitude", "onset_ms", "offset_ms"),
    "pulse_train": ("amplitude", "period_ms", "width_ms", "onset_ms"),
    "ramp": ("peak", "onset_ms"),
}


def _check_step_window(values, onset_ms, duration_ms):
    if not onset_ms < values["offset_ms"] <= duration_ms:
        raise ValueError("step offset_ms must follow onset_ms and stay in the trial")


def _check_pulse_train_window(values):
    period_ms = values["period_ms"]
    width_ms = values["width_ms"]
    if period_ms <= 0:
        raise ValueError("pulse_train period_ms must be positive")
    if not 0 < width_ms <= period_ms:
        raise ValueError("pulse_train width_ms must be in (0, period_ms]")


def _stimulus_kind_and_params(stimulus):
    if not isinstance(stimulus, dict):
        raise ValueError("stimulus must be an object")
    kind = stimulus.get("kind")
    params = stimulus.get("parameters")
    if kind not in STIMULI:
        raise ValueError("stimulus kind or parameters are invalid")
    if not isinstance(params, dict):
        raise ValueError("stimulus kind or parameters are invalid")
    return kind, params


def _validate_stimulus(stimulus, duration_ms):
    kind, params = _stimulus_kind_and_params(stimulus)
    required = _REQUIRED_STIMULUS_PARAMS[kind]
    values = {
        name: _finite_number(params.get(name), f"stimulus.parameters.{name}") for name in required
    }
    onset_ms = values["onset_ms"]
    if not 0 <= onset_ms < duration_ms:
        raise ValueError("stimulus onset_ms must be inside the trial")
    if kind == "step":
        _check_step_window(values, onset_ms, duration_ms)
    elif kind == "pulse_train":
        _check_pulse_train_window(values)


def neuron_sample_count(scenario):
    """Validate a neuron stimulus and return its bounded sample count."""
    if not isinstance(scenario, dict):
        raise ValueError("neuron scenario must be an object")
    duration_ms = _finite_number(scenario.get("duration_ms"), "duration_ms")
    dt_ms = _finite_number(scenario.get("dt_ms"), "dt_ms")
    steps = _bounded_step_count(duration_ms, dt_ms)
    _validate_stimulus(scenario.get("stimulus"), duration_ms)
    return steps


def _step_sample(time_ms, params, _duration_ms):
    inside = params["onset_ms"] <= time_ms < params["offset_ms"]
    return params["amplitude"] if inside else 0.0


def _pulse_train_sample(time_ms, params, _duration_ms):
    if time_ms < params["onset_ms"]:
        return 0.0
    phase = (time_ms - params["onset_ms"]) % params["period_ms"]
    return params["amplitude"] if phase < params["width_ms"] else 0.0


def _ramp_sample(time_ms, params, duration_ms):
    if time_ms < params["onset_ms"]:
        return 0.0
    span = max(1e-9, duration_ms - params["onset_ms"])
    return params["peak"] * (time_ms - params["onset_ms"]) / span


_CURRENT_SAMPLERS = {
    "step": _step_sample,
    "pulse_train": _pulse_train_sample,
}


def build_current(scenario):
    """Stimulus waveform, one sample per dt. Shared by generator and oracle."""
    dt_ms = scenario["dt_ms"]
    steps = neuron_sample_count(scenario)
    kind = scenario["stimulus"]["kind"]
    params = scenario["stimulus"]["parameters"]
    duration_ms = scenario["duration_ms"]
    sample = _CURRENT_SAMPLERS.get(kind, _ramp_sample)
    return [sample(index * dt_ms, params, duration_ms) for index in range(steps)]


_NEURON_OPERATIONS = {
    "threshold": ("scale", (0.6, 1.5)),
    "decay": ("scale", (0.5, 2.0)),
    "adaptation": ("scale", (0.2, 3.0)),
    "refractory": ("scale", (0.5, 3.0)),
    "input_intensity": ("scale", (0.5, 1.8)),
    "neuromodulatory_state": ("scale", (0.6, 1.6)),
}


def propose_neuron_intervention(rng, _scenario):
    target = rng.choice(sorted(sim.INTERVENTION_TARGETS))
    operation, (low, high) = _NEURON_OPERATIONS[target]
    factor = rng.uniform(low, high)
    return {
        "target": target,
        "parameter": sim.INTERVENTION_TARGETS[target],
        "operation": operation,
        "factor": factor,
        "description": f"{operation} {sim.INTERVENTION_TARGETS[target]} by {factor:.3f}",
    }


def predict_neuron_effect(_scenario, intervention):
    """Sign-of-effect hunch from the textbook direction of each knob."""
    target = intervention["target"]
    factor = intervention["factor"]
    raises_rate = {
        "threshold": factor < 1.0,
        "decay": factor > 1.0,
        "adaptation": factor < 1.0,
        "refractory": factor < 1.0,
        "input_intensity": factor > 1.0,
        "neuromodulatory_state": factor > 1.0,
    }[target]
    return {
        "kind": "non_authoritative_guess",
        "predicted_direction": "increases_firing" if raises_rate else "decreases_firing",
        "basis": f"textbook sign of {target}; no simulation was run to produce this",
    }
