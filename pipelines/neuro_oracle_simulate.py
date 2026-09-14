#!/usr/bin/env python3
"""The two simulators, kept side by side on purpose.

`simulate_fixed_point` is structurally identical to `simulate_float` so that
every observed difference is attributable to the number format rather than to a
different algorithm. That invariant is maintained by reading the two loops
against each other, which is why they share a module and why neither loop's
expression text may be reflowed: float results depend on evaluation order.
"""

from __future__ import annotations

from pathlib import Path
import sys

_PIPELINES = Path(__file__).resolve().parent

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
    if str(_PIPELINES) not in sys.path:
        sys.path.insert(0, str(_PIPELINES))
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

def _lif_step_neuron_float(i, row, model, membrane, refractory, previous, neurons):
    """One neuron's float64 LIF update for one timestep.

    Mutates ``membrane[i]``/``refractory[i]`` in place; returns 1 if the
    neuron fires this step, else 0. Split out of ``simulate_float``'s nested
    loop with the exact same operations in the exact same order, so this
    does not change floating-point evaluation order or results.
    """
    if refractory[i] > 0:
        refractory[i] -= 1
        membrane[i] = 0.0
        return 0
    drive = model["bias"][i]
    for j in range(model["inputs"]):
        if row[j]:
            drive += model["w_in"][i][j]
    if model["w_rec"] is not None:
        for k in range(neurons):
            if previous[k]:
                drive += model["w_rec"][i][k]
    membrane[i] = model["decay"][i] * membrane[i] + drive
    if membrane[i] >= model["threshold"][i]:
        if model["reset"] == "zero":
            membrane[i] = 0.0
        else:
            membrane[i] -= model["threshold"][i]
        refractory[i] = model["refractory_steps"]
        return 1
    return 0


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
            _lif_step_neuron_float(i, row, model, membrane, refractory, previous, neurons)
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


def _q88_input_drive(i, row, q_model, previous, neurons):
    """Bias plus input and recurrent drive for one neuron, in Q8.8.

    Returns the accumulator and the number of saturation events it cost.
    """
    accumulator = q_model["bias"][i]
    saturation = 0
    for j in range(q_model["inputs"]):
        if row[j]:
            accumulator, hit = q88_saturate(accumulator + q_model["w_in"][i][j])
            saturation += int(hit)
    if q_model["w_rec"] is not None:
        for k in range(neurons):
            if previous[k]:
                accumulator, hit = q88_saturate(accumulator + q_model["w_rec"][i][k])
                saturation += int(hit)
    return accumulator, saturation


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
        row = stimulus["events"][step]
        fired = [0] * neurons
        for i in range(neurons):
            if refractory[i] > 0:
                refractory[i] -= 1
                membrane[i] = 0
                continue
            accumulator, drive_saturation = _q88_input_drive(
                i, row, q_model, previous, neurons
            )
            saturation_events += drive_saturation
            leaked, hit = q88_mul(q_model["decay"][i], membrane[i])
            saturation_events += int(hit)
            membrane[i], hit = q88_saturate(leaked + accumulator)
            saturation_events += int(hit)
            fired[i], fire_saturation = _q88_apply_threshold(
                i, q_model, membrane, refractory
            )
            saturation_events += fire_saturation
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
