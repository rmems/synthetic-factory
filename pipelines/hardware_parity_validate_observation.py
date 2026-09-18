#!/usr/bin/env python3
"""Re-deriving what each side observed from the traces it recorded.

Spikes, action, membrane and the arithmetic observations. This is the half of
the anti-fabrication gate that stops a record copying one side's traces onto
the other and calling the result a match.
"""

from __future__ import annotations

import math
import sys

if __package__:
    # Import-twin helpers join the package import lock; import-order tests cover this edge.
    from . import _assert_direct_sibling, _expose_package_sibling  # pylint: disable=cyclic-import

    _assert_direct_sibling("hardware_parity_validate_observation")
    from .hardware_parity_terms import contract  # noqa: E402
    from .hardware_parity_validate_quantization import (  # noqa: E402
        _matrix_errors,
        _q88_raw_correspondence_errors,
    )
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "hardware_parity_validate_observation"
    )
    from hardware_parity_terms import contract  # noqa: E402
    from hardware_parity_validate_quantization import (  # noqa: E402
        _matrix_errors,
        _q88_raw_correspondence_errors,
    )

def _expected_spike_events(spikes, dt_ms):
    return [
        {
            "t_step": step,
            "t_ms": round(step * dt_ms, 6),
            "neuron_id": neuron,
        }
        for step, row in enumerate(spikes)
        for neuron, fired in enumerate(row)
        if fired == 1
    ]


def _expected_action(spikes, labels):
    counts = [sum(row[neuron] for row in spikes) for neuron in range(len(labels))]
    if max(counts, default=0) == 0:
        return {
            "index": None,
            "label": "no_spike",
            "counts": counts,
            "rule": "argmax_count",
        }
    best = max(range(len(counts)), key=lambda index: (counts[index], -index))
    return {
        "index": best,
        "label": labels[best],
        "counts": counts,
        "rule": "argmax_count",
    }


def _invalid_observed_integer(value, lower_bound):
    """Preserve the observation's lower-bound comparison, excluding booleans."""
    return not isinstance(value, int) or isinstance(value, bool) or value < lower_bound


def _matching_action_labels(labels, neurons):
    return (
        isinstance(labels, list)
        and len(labels) == neurons
        and all(isinstance(label, str) for label in labels)
    )


def _usable_dt_ms(value):
    # Integers need no float conversion: arbitrarily large integral dt is valid.
    if type(value) is int:
        return True
    return type(value) is float and math.isfinite(value)


def _scenario_components(scenario):
    if not isinstance(scenario, dict):
        return None
    model = scenario.get("model_float")
    stimulus = scenario.get("stimulus")
    if not isinstance(model, dict) or not isinstance(stimulus, dict):
        return None
    return model, stimulus


def _scenario_observation_window(scenario):
    """The `(neurons, labels, steps, dt_ms)` window, or None if unusable."""
    components = _scenario_components(scenario)
    if components is None:
        return None
    model, stimulus = components
    neurons = model.get("neurons")
    labels = model.get("action_labels")
    steps = stimulus.get("steps")
    dt_ms = stimulus.get("dt_ms")
    if _invalid_observed_integer(neurons, 1) or _invalid_observed_integer(steps, 1):
        return None
    if not _matching_action_labels(labels, neurons):
        return None
    if not _usable_dt_ms(dt_ms):
        return None
    return neurons, labels, steps, dt_ms


def _observed_spike_errors(observation, window, path, where):
    """The spike bitmap, and the events/action projections derived from it."""
    neurons, labels, steps, dt_ms = window
    spikes = observation.get("spikes")
    errors = _matrix_errors(
        spikes, steps, neurons, f"{path}.spikes", where, binary=True
    )
    if errors:
        return errors
    expected_events = _expected_spike_events(spikes, dt_ms)
    if not contract.strict_json_equal(
        observation.get("spike_events"), expected_events
    ):
        errors.append(
            f"{where}: {path}.spike_events does not exactly encode its spike "
            "bitmap [ENVELOPE_MALFORMED]"
        )
    expected_action = _expected_action(spikes, labels)
    if not contract.strict_json_equal(observation.get("action"), expected_action):
        errors.append(
            f"{where}: {path}.action does not decode from its spike bitmap "
            "[ENVELOPE_MALFORMED]"
        )
    return errors


def _unobservable_membrane_errors(membrane, path, where):
    if membrane.get("trace") is not None:
        return [
            f"{where}: {path}.membrane.trace must be null when membrane state is "
            "not observable [ENVELOPE_MALFORMED]"
        ]
    return []


def _observable_membrane_errors(membrane, dimensions, path, where):
    """Validate both matrices before comparing Q8.8 correspondence."""
    neurons, steps = dimensions
    trace_errors = _matrix_errors(
        membrane.get("trace"), steps, neurons, f"{path}.membrane.trace", where,
    )
    if "trace_q88_raw" not in membrane:
        return trace_errors
    raw_errors = _matrix_errors(
        membrane.get("trace_q88_raw"), steps, neurons,
        f"{path}.membrane.trace_q88_raw", where, integer=True,
    )
    if trace_errors or raw_errors:
        return trace_errors + raw_errors
    return _q88_raw_correspondence_errors(
        membrane.get("trace"), membrane.get("trace_q88_raw"), f"{path}.membrane", where,
    )


def _observed_membrane_errors(membrane, window, path, where):
    """The membrane trace, and its Q8.8 raw correspondence when retained."""
    neurons, _labels, steps, _dt_ms = window
    if not isinstance(membrane, dict) or type(membrane.get("observable")) is not bool:
        return [
            f"{where}: {path}.membrane must declare an exact boolean observable flag "
            "[ENVELOPE_MALFORMED]"
        ]
    if not membrane["observable"]:
        return _unobservable_membrane_errors(membrane, path, where)
    return _observable_membrane_errors(membrane, (neurons, steps), path, where)


def _q88_saturation_declared(arithmetic):
    if not isinstance(arithmetic, dict) or arithmetic.get("format") != "Q8.8":
        return False
    return not _invalid_observed_integer(arithmetic.get("saturation_events"), 0)


def _observed_arithmetic_errors(arithmetic, path, where):
    """The Q8.8 saturation attestation carried by one observation."""
    if not _q88_saturation_declared(arithmetic):
        return [
            f"{where}: {path}.arithmetic must declare Q8.8 and an exact "
            "nonnegative saturation_events integer [ENVELOPE_MALFORMED]"
        ]
    return []


def _physical_observation_errors(observation, scenario, path, where):
    """Validate one retained physical observation against its execution window."""
    if not isinstance(observation, dict):
        return [f"{where}: {path} must be an object [ENVELOPE_MALFORMED]"]
    if _scenario_components(scenario) is None:
        return [
            f"{where}: scenario model and stimulus are required to validate {path} "
            "[ENVELOPE_MALFORMED]"
        ]
    window = _scenario_observation_window(scenario)
    if window is None:
        return [
            f"{where}: scenario dimensions cannot validate {path} "
            "[ENVELOPE_MALFORMED]"
        ]
    errors = _observed_spike_errors(observation, window, path, where)
    errors += _observed_membrane_errors(
        observation.get("membrane"), window, path, where
    )
    errors += _observed_arithmetic_errors(observation.get("arithmetic"), path, where)
    return errors


if __package__:
    _expose_package_sibling(__name__)
