#!/usr/bin/env python3
"""The scenario catalog: the declarative stress cases this family measures.

Data, and the two builders that materialize it. Each spec names one way a Q8.8
datapath can diverge from float64 -- rounding, saturation, accumulator order,
reset convention -- and the parameters are spelled out rather than derived so
a reviewer can see what each case actually stresses.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from neuro_oracle import (  # noqa: E402
    digest,
    normalize_model,
    normalize_stimulus,
    stimulus_fixture,
)
from hardware_parity_terms import FACTORY_SLUG  # noqa: E402

def _grid(steps, channels, pattern):
    """Build a binary event grid from a per-channel period/offset pattern."""
    rows = []
    for step in range(steps):
        row = []
        for channel in range(channels):
            period, offset = pattern[channel]
            row.append(1 if period and (step - offset) >= 0 and (step - offset) % period == 0
                       else 0)
        rows.append(row)
    return rows


SCENARIO_SPECS = (
    {
        "id": "hp-representable-margin",
        "name": "exactly representable margin",
        "stress": "none",
        "description": (
            "Every weight, bias and threshold is an exact multiple of 1/256 and the "
            "leak is zero, so the Q8.8 datapath has no rounding to do. This is the "
            "control case: if it ever diverges, the divergence is not quantization."
        ),
        "hypothesis": "spike trains and action agree exactly",
        "model": {
            "name": "relay-gate-4",
            "neurons": 4,
            "inputs": 3,
            "w_in": [
                [0.5, 0.25, 0.0],
                [0.25, 0.5, 0.0],
                [0.0, 0.25, 0.5],
                [0.125, 0.125, 0.125],
            ],
            "w_rec": None,
            "bias": [0.0625, 0.0625, 0.0625, 0.0625],
            "threshold": [0.5625, 0.75, 0.5625, 0.375],
            "decay": [0.0, 0.0, 0.0, 0.0],
            "refractory_steps": 0,
            "reset": "subtract",
            "dt_ms": 1.0,
        },
        "pattern": [(1, 0), (2, 0), (3, 0)],
        "intervention": None,
    },
    {
        "id": "hp-knife-edge-threshold",
        "name": "knife-edge threshold",
        "stress": "quantization_rounding",
        "description": (
            "Neurons 0 and 3 have a weight that rounds down and a threshold that rounds "
            "up, so the float membrane reaches threshold one timestep before the Q8.8 "
            "membrane does. Neurons 1 and 2 use exactly representable values as an "
            "in-scenario control."
        ),
        "hypothesis": "first-spike timing diverges on neurons 0 and 3 only",
        "model": {
            "name": "knife-edge-4",
            "neurons": 4,
            "inputs": 3,
            "w_in": [
                [0.501, 0.0, 0.0],
                [0.5, 0.0, 0.0],
                [0.25, 0.0, 0.0],
                [0.126, 0.0, 0.0],
            ],
            "w_rec": None,
            "bias": [0.0, 0.0, 0.0, 0.0],
            "threshold": [1.002, 1.0, 0.75, 0.504],
            "decay": [1.0, 1.0, 1.0, 1.0],
            "refractory_steps": 0,
            "reset": "subtract",
            "dt_ms": 1.0,
        },
        "pattern": [(1, 0), (0, 0), (0, 0)],
        "intervention": {
            "kind": "parameter_perturbation",
            "detail": (
                "w=0.501 quantizes down to 128/256 while threshold 1.002 quantizes up "
                "to 257/256, opening a one-LSB gap at the decision boundary"
            ),
            "applies_to": "threshold",
        },
    },
    {
        "id": "hp-weight-saturation",
        "name": "weight range saturation",
        "stress": "q88_range_overflow",
        "description": (
            "Neuron 0 has an excitatory weight outside the Q8.8 range, so export clamps "
            "it and the deployed neuron receives far less drive than the trained one. "
            "Neurons 2 and 3 stay inside the range as a control."
        ),
        "hypothesis": "clamped export silences a neuron that fires in software",
        "model": {
            "name": "wide-dynamic-range-4",
            "neurons": 4,
            "inputs": 3,
            "w_in": [
                [190.0, -70.0, 0.0],
                [64.0, -16.0, 0.0],
                [0.5, 0.25, 0.0],
                [0.125, 0.125, 0.125],
            ],
            "w_rec": None,
            "bias": [0.0, 0.0, 0.0, 0.0],
            "threshold": [100.0, 40.0, 0.5, 0.25],
            "decay": [0.0, 0.0, 0.0, 0.0],
            "refractory_steps": 0,
            "reset": "subtract",
            "dt_ms": 1.0,
        },
        "pattern": [(1, 0), (1, 0), (2, 0)],
        "intervention": {
            "kind": "parameter_perturbation",
            "detail": "w_in[0][0]=190.0 exceeds the Q8.8 maximum 127.99609375",
            "applies_to": "w_in",
        },
    },
    {
        "id": "hp-accumulator-saturation",
        "name": "accumulator ordering saturation",
        "stress": "q88_accumulator_overflow",
        "description": (
            "Neuron 0 sums two large excitatory inputs before a large inhibitory one. "
            "Each weight is individually representable, but the partial sum saturates, "
            "so the inhibition subtracts from a clamped accumulator. Order of "
            "accumulation, not the weights, is what breaks parity."
        ),
        "hypothesis": "the deployed neuron loses drive that the float neuron keeps",
        "model": {
            "name": "accumulator-order-4",
            "neurons": 4,
            "inputs": 3,
            "w_in": [
                [120.0, 120.0, -120.0],
                [40.0, 40.0, -40.0],
                [0.5, 0.25, 0.0],
                [0.125, 0.125, 0.125],
            ],
            "w_rec": None,
            "bias": [0.0, 0.0, 0.0, 0.0],
            "threshold": [100.0, 35.0, 0.5, 0.25],
            "decay": [0.0, 0.0, 0.0, 0.0],
            "refractory_steps": 0,
            "reset": "subtract",
            "dt_ms": 1.0,
        },
        "pattern": [(1, 0), (1, 0), (1, 0)],
        "intervention": {
            "kind": "parameter_perturbation",
            "detail": "120 + 120 = 240 exceeds the Q8.8 accumulator range before -120 lands",
            "applies_to": "w_in",
        },
    },
    {
        "id": "hp-recurrent-inhibition",
        "name": "recurrent lateral inhibition",
        "stress": "recurrent_feedback",
        "description": (
            "Lateral inhibition feeds each timestep's quantization residue back into the "
            "next one, so a sub-LSB difference has a path by which it can compound "
            "instead of washing out."
        ),
        "hypothesis": "error accumulates across the recurrent loop",
        "model": {
            "name": "lateral-inhibition-4",
            "neurons": 4,
            "inputs": 3,
            "w_in": [
                [0.4003, 0.1001, 0.0],
                [0.0, 0.4003, 0.1001],
                [0.1001, 0.0, 0.4003],
                [0.2002, 0.2002, 0.0],
            ],
            "w_rec": [
                [0.0, -0.3007, -0.3007, 0.0],
                [-0.3007, 0.0, -0.3007, 0.0],
                [-0.3007, -0.3007, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0],
            ],
            "bias": [0.0503, 0.0503, 0.0503, 0.0],
            "threshold": [0.7001, 0.7001, 0.7001, 1.0],
            "decay": [0.8501, 0.8501, 0.8501, 0.5],
            "refractory_steps": 1,
            "reset": "subtract",
            "dt_ms": 1.0,
        },
        "pattern": [(1, 0), (2, 1), (3, 2)],
        "intervention": {
            "kind": "topology_perturbation",
            "detail": "lateral inhibition enabled between neurons 0-2",
            "applies_to": "w_rec",
        },
    },
    {
        "id": "hp-refractory-boundary",
        "name": "refractory boundary",
        "stress": "refractory_state_machine",
        "description": (
            "Drive reaches threshold in float one timestep before it does in Q8.8, and a "
            "two-step refractory window then propagates that single shift through the "
            "rest of the train instead of letting it be reabsorbed."
        ),
        "hypothesis": "a one-step timing error becomes a whole shifted train",
        "model": {
            "name": "refractory-gate-4",
            "neurons": 4,
            "inputs": 3,
            "w_in": [
                [0.201, 0.0, 0.0],
                [0.25, 0.0, 0.0],
                [0.0, 0.201, 0.0],
                [0.0, 0.0, 0.25],
            ],
            "w_rec": None,
            "bias": [0.0, 0.0, 0.0, 0.0],
            "threshold": [0.603, 0.75, 0.603, 0.75],
            "decay": [1.0, 1.0, 1.0, 1.0],
            "refractory_steps": 2,
            "reset": "zero",
            "dt_ms": 1.0,
        },
        "pattern": [(1, 0), (1, 0), (1, 0)],
        "intervention": {
            "kind": "parameter_perturbation",
            "detail": "refractory_steps raised from 0 to 2 so a timing shift cannot be reabsorbed",
            "applies_to": "refractory_steps",
        },
    },
)


_SCENARIO_SPEC_BY_ID = {spec["id"]: spec for spec in SCENARIO_SPECS}


def build_scenario(spec, steps=12):
    """Materialise one scenario, including the encoded input fixture."""
    model = normalize_model(spec["model"])
    stimulus = normalize_stimulus(
        {
            "name": f"{spec['id']}-stimulus",
            "encoding": "binary_event_grid",
            "dt_ms": model["dt_ms"],
            "steps": steps,
            "events": _grid(steps, model["inputs"], spec["pattern"]),
        },
        model["inputs"],
    )
    return {
        "id": spec["id"],
        "name": spec["name"],
        "family": FACTORY_SLUG,
        "stress": spec["stress"],
        "description": spec["description"],
        "hypothesis": spec["hypothesis"],
        "model_float": model,
        "model_sha256": digest(model),
        "stimulus": stimulus,
        "input_fixture": stimulus_fixture(stimulus),
        "intervention": spec["intervention"],
    }


def build_scenarios(steps=12):
    return [build_scenario(spec, steps=steps) for spec in SCENARIO_SPECS]

