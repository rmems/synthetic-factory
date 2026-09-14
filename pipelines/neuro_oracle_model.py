#!/usr/bin/env python3
"""The model and stimulus contracts: what a well-formed input looks like.

Normalization is strict and raises rather than repairing, so a scenario cannot
reach a simulator in a shape the other simulator would read differently.
"""

from __future__ import annotations

from pathlib import Path
import sys

_PIPELINES = Path(__file__).resolve().parent

if __package__:
    # Import-twin helpers join the package import lock; import-order tests cover this edge.
    from . import _assert_direct_sibling, _expose_package_sibling  # pylint: disable=cyclic-import

    _assert_direct_sibling("neuro_oracle_model")
    from .neuro_oracle_digest import digest  # noqa: E402
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "neuro_oracle_model"
    )
    if str(_PIPELINES) not in sys.path:
        sys.path.insert(0, str(_PIPELINES))
    from neuro_oracle_digest import digest  # noqa: E402

RESET_MODES = ("zero", "subtract")
DEFAULT_ACTION_LABELS = ("hold", "advance", "retreat", "halt")


def _is_positive_count(value):
    """An exact int >= 1. bool is an int in Python and is refused here."""
    return isinstance(value, int) and not isinstance(value, bool) and value >= 1


def _model_header(model):
    """Required keys and the scalars every other field is sized against."""
    required = ("name", "neurons", "inputs", "w_in", "bias", "threshold", "decay")
    missing = [key for key in required if key not in model]
    if missing:
        raise ValueError(f"model missing keys: {missing}")
    neurons = model["neurons"]
    inputs = model["inputs"]
    # Exact integers, not int(): 1.9 would quietly become one neuron and a
    # string or bool would be accepted, so whenever the matrices happened to
    # fit the coerced size the oracle ran a model other than the one declared.
    if not _is_positive_count(neurons) or not _is_positive_count(inputs):
        raise ValueError("neurons and inputs must be exact integers >= 1")
    reset = model.get("reset", "subtract")
    if reset not in RESET_MODES:
        raise ValueError(f"reset must be one of {RESET_MODES}, got {reset!r}")
    return neurons, inputs, reset


def _model_matrix(model, name, rows, cols):
    """An optional rows x cols weight matrix, copied to floats."""
    value = model.get(name)
    if value is None:
        return None
    if len(value) != rows or any(len(row) != cols for row in value):
        raise ValueError(f"{name} must be {rows}x{cols}")
    return [[float(cell) for cell in row] for row in value]


def _model_vector(model, name, length):
    """A required per-neuron vector, copied to floats."""
    value = model[name]
    if len(value) != length:
        raise ValueError(f"{name} must have length {length}")
    return [float(cell) for cell in value]


def _check_normalized_model(normalized, labels, neurons):
    """Post-conditions that need the assembled model to check."""
    if normalized["w_in"] is None:
        raise ValueError("w_in is required")
    if normalized["refractory_steps"] < 0:
        raise ValueError("refractory_steps must be >= 0")
    if normalized["dt_ms"] <= 0:
        raise ValueError("dt_ms must be > 0")
    if len(labels) != neurons:
        raise ValueError("action_labels must have one label per neuron")


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
        "w_in": _model_matrix(model, "w_in", neurons, inputs),
        "w_rec": _model_matrix(model, "w_rec", neurons, neurons),
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


def normalize_stimulus(stimulus, inputs):
    """Validate an encoded input fixture against the model input width."""
    events = stimulus["events"]
    steps = int(stimulus.get("steps", len(events)))
    if steps != len(events):
        raise ValueError("stimulus.steps disagrees with len(events)")
    if steps < 1:
        raise ValueError("stimulus needs at least one step")
    grid = []
    for index, row in enumerate(events):
        if len(row) != inputs:
            raise ValueError(f"stimulus step {index} must have {inputs} channels")
        if any(cell not in (0, 1) for cell in row):
            raise ValueError(f"stimulus step {index} must be binary")
        grid.append([int(cell) for cell in row])
    return {
        "name": str(stimulus["name"]),
        "encoding": str(stimulus.get("encoding", "binary_event_grid")),
        "dt_ms": float(stimulus.get("dt_ms", 1.0)),
        "steps": steps,
        "channels": inputs,
        "events": grid,
    }


def stimulus_fixture(stimulus):
    """The identical-input contract: the digest both sides must agree on."""
    return {
        "name": stimulus["name"],
        "encoding": stimulus["encoding"],
        "steps": stimulus["steps"],
        "channels": stimulus["channels"],
        "dt_ms": stimulus["dt_ms"],
        "sha256": digest(stimulus["events"]),
    }


if __package__:
    _expose_package_sibling(__name__)
