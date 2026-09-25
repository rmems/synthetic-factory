#!/usr/bin/env python3
"""The model and stimulus contracts: what a well-formed input looks like.

Normalization is strict and raises rather than repairing, so a scenario cannot
reach a simulator in a shape the other simulator would read differently.
"""

from __future__ import annotations

import sys

if __package__:
    # Import-twin helpers join the package import lock; import-order tests cover this edge.
    from . import _assert_direct_sibling, _expose_package_sibling  # pylint: disable=cyclic-import

    _assert_direct_sibling("neuro_oracle_model")
    from .neuro_oracle_digest import digest  # noqa: E402
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "neuro_oracle_model"
    )
    from neuro_oracle_digest import digest  # noqa: E402

RESET_MODES = ("zero", "subtract")
DEFAULT_ACTION_LABELS = ("hold", "advance", "retreat", "halt")


def _is_positive_count(value):
    """An exact int >= 1. bool is an int in Python and is refused here."""
    return isinstance(value, int) and not isinstance(value, bool) and value >= 1


def _require(condition, message):
    """Raise ValueError(message) unless condition holds."""
    if not condition:
        raise ValueError(message)


def _model_header(model):
    """Required keys and the scalars every other field is sized against."""
    required = ("name", "neurons", "inputs", "w_in", "bias", "threshold", "decay")
    missing = [key for key in required if key not in model]
    _require(not missing, f"model missing keys: {missing}")
    neurons = model["neurons"]
    inputs = model["inputs"]
    # Exact integers, not int(): 1.9 would quietly become one neuron and a
    # string or bool would be accepted, so whenever the matrices happened to
    # fit the coerced size the oracle ran a model other than the one declared.
    _require(
        _is_positive_count(neurons) and _is_positive_count(inputs),
        "neurons and inputs must be exact integers >= 1",
    )
    reset = model.get("reset", "subtract")
    _require(
        reset in RESET_MODES,
        f"reset must be one of {RESET_MODES}, got {reset!r}",
    )
    return neurons, inputs, reset


def _matrix_shape(value, shape):
    """True when `value` is a ``(rows, cols)``-shaped list-of-lists."""
    rows, cols = shape
    return len(value) == rows and all(len(row) == cols for row in value)


def _model_matrix(model, name, shape):
    """An optional ``(rows, cols)`` weight matrix, copied to floats.

    ``shape`` packs the required ``(rows, cols)``.
    """
    value = model.get(name)
    if value is None:
        return None
    _require(_matrix_shape(value, shape), f"{name} must be {shape[0]}x{shape[1]}")
    return [[float(cell) for cell in row] for row in value]


def _model_vector(model, name, length):
    """A required per-neuron vector, copied to floats."""
    value = model[name]
    _require(len(value) == length, f"{name} must have length {length}")
    return [float(cell) for cell in value]


def _check_normalized_model(normalized, labels, neurons):
    """Post-conditions that need the assembled model to check."""
    _require(normalized["w_in"] is not None, "w_in is required")
    _require(
        normalized["refractory_steps"] >= 0, "refractory_steps must be >= 0"
    )
    _require(normalized["dt_ms"] > 0, "dt_ms must be > 0")
    _require(
        len(labels) == neurons,
        "action_labels must have one label per neuron",
    )


def normalize_model(model):
    """Validate and copy a model dict into canonical form.

    Raises ValueError on a malformed model rather than silently coercing, so a
    generator cannot smuggle a mis-shaped network past the oracle.
    """
    neurons, inputs, reset = _model_header(model)
    labels = list(model.get("action_labels", DEFAULT_ACTION_LABELS[:neurons]))
    normalized = {
        "name": str(model["name"]),
        "neurons": neurons,
        "inputs": inputs,
        "w_in": _model_matrix(model, "w_in", (neurons, inputs)),
        "w_rec": _model_matrix(model, "w_rec", (neurons, neurons)),
        "bias": _model_vector(model, "bias", neurons),
        "threshold": _model_vector(model, "threshold", neurons),
        "decay": _model_vector(model, "decay", neurons),
        "refractory_steps": int(model.get("refractory_steps", 0)),
        "reset": reset,
        "dt_ms": float(model.get("dt_ms", 1.0)),
        "action_labels": labels,
    }
    _check_normalized_model(normalized, labels, neurons)
    return normalized


def _stimulus_steps(stimulus, event_count):
    """A positive step count that agrees with the recorded event grid."""
    steps = int(stimulus.get("steps", event_count))
    _require(steps == event_count, "stimulus.steps disagrees with len(events)")
    _require(steps >= 1, "stimulus needs at least one step")
    return steps


def normalize_stimulus(stimulus, inputs):
    """Validate an encoded input fixture against the model input width."""
    events = stimulus["events"]
    return {
        "name": str(stimulus["name"]),
        "encoding": str(stimulus.get("encoding", "binary_event_grid")),
        "dt_ms": float(stimulus.get("dt_ms", 1.0)),
        "steps": _stimulus_steps(stimulus, len(events)),
        "channels": inputs,
        "events": [_binary_row(index, row, inputs) for index, row in enumerate(events)],
    }


def _binary_row(index, row, inputs):
    """One grid row: exactly ``inputs`` binary cells, normalized to ints."""
    _require(
        len(row) == inputs,
        f"stimulus step {index} must have {inputs} channels",
    )
    _require(
        all(cell in (0, 1) for cell in row),
        f"stimulus step {index} must be binary",
    )
    return [int(cell) for cell in row]


def stimulus_fixture(stimulus):
    """The identical-input contract: the digest both sides must agree on."""
    fixture = {
        "name": stimulus["name"],
        "encoding": stimulus["encoding"],
        "steps": stimulus["steps"],
        "channels": stimulus["channels"],
        "dt_ms": stimulus["dt_ms"],
    }
    return {**fixture, "sha256": digest({**fixture, "events": stimulus["events"]})}


if __package__:
    _expose_package_sibling(__name__)
