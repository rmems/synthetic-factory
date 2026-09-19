#!/usr/bin/env python3
"""The two simulators, kept side by side on purpose.

`simulate_fixed_point` is structurally identical to `simulate_float` so that
every observed difference is attributable to the number format rather than to a
different algorithm. That invariant is maintained by reading the two loops
against each other, which is why they share a module and why neither loop's
expression text may be reflowed: float results depend on evaluation order.
"""

from __future__ import annotations

import sys

if __package__:
    # Import-twin helpers join the package import lock; import-order tests cover this edge.
    from . import _assert_direct_sibling, _expose_package_sibling  # pylint: disable=cyclic-import

    _assert_direct_sibling("neuro_oracle_simulate")
    from .neuro_oracle_observation import _decode_action, _spike_events  # noqa: E402
    from .neuro_oracle_model import (  # noqa: E402
        normalize_model,
        normalize_stimulus,
    )
    from .neuro_oracle_q88 import (  # noqa: E402
        q88_mul,
        q88_saturate,
        q88_to_float,
    )
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "neuro_oracle_simulate"
    )
    from neuro_oracle_observation import _decode_action, _spike_events  # noqa: E402
    from neuro_oracle_model import (  # noqa: E402
        normalize_model,
        normalize_stimulus,
    )
    from neuro_oracle_q88 import (  # noqa: E402
        q88_mul,
        q88_saturate,
        q88_to_float,
    )

def _lif_step_neuron_float(neuron_input, model, state):
    """One neuron's float64 LIF update for one timestep.

    ``neuron_input`` is ``(i, row)``: the neuron index and the stimulus row.
    ``state`` is the ``(membrane, refractory, previous)`` triple the loop
    owns; ``membrane[i]``/``refractory[i]`` are mutated in place. Returns 1
    if the neuron fires this step, else 0. Split out of ``simulate_float``'s
    nested loop with the exact same operations in the exact same order, so
    this does not change floating-point evaluation order or results.
    """
    i, row = neuron_input
    membrane, refractory, previous = state
    if refractory[i] > 0:
        refractory[i] -= 1
        membrane[i] = 0.0
        return 0
    drive = _lif_drive(i, row, model, previous)
    membrane[i] = model["decay"][i] * membrane[i] + drive
    if membrane[i] >= model["threshold"][i]:
        if model["reset"] == "zero":
            membrane[i] = 0.0
        else:
            membrane[i] -= model["threshold"][i]
        refractory[i] = model["refractory_steps"]
        return 1
    return 0


def _lif_recurrent_terms(i, model, previous):
    """The w_rec terms a neuron sees this step, empty without recurrence."""
    if model["w_rec"] is None:
        return []
    return [model["w_rec"][i][k] for k in range(len(previous)) if previous[k]]


def _lif_drive(i, row, model, previous):
    """One neuron's summed input drive for one timestep.

    The accumulation order (bias, then w_in left-to-right, then w_rec
    left-to-right) is preserved exactly from the original inline loop so
    floating-point results are identical.
    """
    drive = model["bias"][i]
    for term in [
        *[model["w_in"][i][j] for j in range(model["inputs"]) if row[j]],
        *_lif_recurrent_terms(i, model, previous),
    ]:
        drive += term
    return drive


def simulate_float(model, stimulus):
    """float64 LIF reference. Deterministic; consults no RNG."""
    model = normalize_model(model)
    stimulus = normalize_stimulus(stimulus, model["inputs"])
    neurons = model["neurons"]
    membrane = [0.0] * neurons
    refractory = [0] * neurons
    previous = [0] * neurons
    spike_grid = []
    membrane_trace = []
    for step in range(stimulus["steps"]):
        row = stimulus["events"][step]
        fired = [
            _lif_step_neuron_float((i, row), model, (membrane, refractory, previous))
            for i in range(neurons)
        ]
        previous = fired
        spike_grid.append(fired)
        membrane_trace.append([round(value, 9) for value in membrane])
    return {
        "spikes": spike_grid,
        "spike_events": _spike_events(spike_grid, model["dt_ms"]),
        "membrane": {"observable": True, "units": "mV_model", "trace": membrane_trace},
        "action": _decode_action(spike_grid, model["action_labels"]),
        "arithmetic": {"format": "float64", "saturation_events": 0},
    }


def _q88_recurrent_terms(i, q_model, previous):
    """The w_rec terms a neuron sees this step, empty without recurrence."""
    if q_model["w_rec"] is None:
        return []
    return [
        q_model["w_rec"][i][k]
        for k in range(q_model["neurons"])
        if previous[k]
    ]


def _q88_input_drive(i, row, q_model, previous):
    """Bias plus input and recurrent drive for one neuron, in Q8.8.

    Returns the accumulator and the number of saturation events it cost. The
    saturation order (bias, then w_in left-to-right, then w_rec left-to-right)
    mirrors ``_lif_drive`` so each observed difference is attributable to the
    number format.
    """
    accumulator = q_model["bias"][i]
    saturation = 0
    for term in [
        *[q_model["w_in"][i][j] for j in range(q_model["inputs"]) if row[j]],
        *_q88_recurrent_terms(i, q_model, previous),
    ]:
        accumulator, hit = q88_saturate(accumulator + term)
        saturation += int(hit)
    return accumulator, saturation


def _q88_step_row(row, q_model, state):
    """All neurons' Q8.8 updates for one timestep: ``(fired, saturations)``.

    ``state`` is the ``(membrane, refractory, previous)`` triple the outer
    loop owns. The fixed-point loop carries a per-step saturation counter
    that has no float-side analogue, so the row step is factored here rather
    than inline as in ``simulate_float``.
    """
    steps = [
        _q88_step_neuron((i, row), q_model, state)
        for i in range(q_model["neurons"])
    ]
    return [fired_i for fired_i, _sat in steps], sum(sat for _fired, sat in steps)


def _q88_step_neuron(neuron_input, q_model, state):
    """One neuron's Q8.8 LIF update for one timestep.

    ``neuron_input`` is ``(i, row)``: the neuron index and the stimulus row.
    ``state`` is the ``(membrane, refractory, previous)`` triple the loop
    owns; ``membrane[i]``/``refractory[i]`` are mutated in place. Returns
    ``(fired, saturation_events)`` where the saturation events are counted in
    the order they occur: drive, decay multiply, saturating add, reset. The
    operation order mirrors ``_lif_step_neuron_float`` exactly.
    """
    i, row = neuron_input
    membrane, refractory, previous = state
    if refractory[i] > 0:
        refractory[i] -= 1
        membrane[i] = 0
        return 0, 0
    accumulator, saturation = _q88_input_drive(i, row, q_model, previous)
    leaked, hit = q88_mul(q_model["decay"][i], membrane[i])
    saturation += int(hit)
    membrane[i], hit = q88_saturate(leaked + accumulator)
    saturation += int(hit)
    fired, fire_saturation = _q88_apply_threshold(i, q_model, membrane, refractory)
    return fired, saturation + fire_saturation


def _q88_apply_threshold(i, q_model, membrane, refractory):
    """Fire, reset, and arm the refractory counter for one neuron.

    Mutates ``membrane`` and ``refractory`` in place, and returns the spike bit
    alongside the saturation events the reset cost.
    """
    if membrane[i] < q_model["threshold"][i]:
        return 0, 0
    saturation = 0
    if q_model["reset"] == "zero":
        membrane[i] = 0
    else:
        membrane[i], hit = q88_saturate(membrane[i] - q_model["threshold"][i])
        saturation += int(hit)
    refractory[i] = q_model["refractory_steps"]
    return 1, saturation


def simulate_fixed_point(q_model, stimulus):
    """Q8.8 integer LIF reference model of an FPGA datapath.

    Structurally identical to :func:`simulate_float` so that every observed
    difference is attributable to the number format rather than to a different
    algorithm.
    """
    stimulus = normalize_stimulus(stimulus, q_model["inputs"])
    neurons = q_model["neurons"]
    membrane = [0] * neurons
    refractory = [0] * neurons
    previous = [0] * neurons
    spike_grid = []
    membrane_trace = []
    membrane_raw = []
    saturation_events = 0
    for step in range(stimulus["steps"]):
        fired, step_saturation = _q88_step_row(
            stimulus["events"][step], q_model, (membrane, refractory, previous)
        )
        saturation_events += step_saturation
        previous = fired
        spike_grid.append(fired)
        membrane_raw.append(list(membrane))
        membrane_trace.append([q88_to_float(value) for value in membrane])
    return {
        "spikes": spike_grid,
        "spike_events": _spike_events(spike_grid, q_model["dt_ms"]),
        "membrane": {
            "observable": True,
            "units": "mV_model",
            "trace": membrane_trace,
            "trace_q88_raw": membrane_raw,
        },
        "action": _decode_action(spike_grid, q_model["action_labels"]),
        "arithmetic": {"format": "Q8.8", "saturation_events": saturation_events},
    }


if __package__:
    _expose_package_sibling(__name__)
