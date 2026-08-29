#!/usr/bin/env python3
"""Deterministic neuromorphic oracle boundary for the parity dataset families.

This module owns the *oracle interface* used by the hardware-parity and
NIR-equivalence families. It deliberately separates three things that are easy
to conflate:

1. A **software float reference simulator** (float64 LIF) — available here.
2. A **Q8.8 fixed-point reference model** of the same datapath — available
   here. It is a *model of* an FPGA datapath, not an FPGA.
3. A **real FPGA execution target** — an adapter that probes for a board and
   reports unavailability with a reason code when there is none. It never
   fabricates spikes, latency, or board metadata.

The distinction is load-bearing: a record produced against the fixed-point
reference model must say ``fixed_point_reference_model``, and the validators in
``hardware_parity`` refuse ``fpga_hardware`` provenance without the board,
bitstream, and capture metadata that only a real run can supply.

Stdlib only. Every simulator here is bit-deterministic for a given model and
stimulus: no RNG is consulted during execution, and repeat runs exist to
measure *hardware* variability, not to add noise.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import stat
from pathlib import Path

SCHEMA_VERSION = "1.0.0"
MAX_CAPTURE_BYTES = 16 * 1024 * 1024

# The determinism.meaning text every in-repo reference adapter's _envelope()
# emits. oracle.software is always a reference adapter (never a physical
# capture), so validators can bind its meaning text to this exact constant
# instead of trusting whatever text the record declares.
REFERENCE_DETERMINISM_MEANING = (
    "bit-determinism of this reference implementation; it is not "
    "evidence about run-to-run variability of physical hardware"
)

# ── Q8.8 fixed-point format ───────────────────────────────────────────
# Signed 16-bit, 8 fractional bits: value = raw / 256, raw in [-32768, 32767].
Q88_FRACTIONAL_BITS = 8
Q88_SCALE = 1 << Q88_FRACTIONAL_BITS
Q88_MIN_RAW = -(1 << 15)
Q88_MAX_RAW = (1 << 15) - 1
Q88_MIN_VALUE = Q88_MIN_RAW / Q88_SCALE
Q88_MAX_VALUE = Q88_MAX_RAW / Q88_SCALE
Q88_STEP = 1.0 / Q88_SCALE
Q88_ROUNDING = "half_away_from_zero"
Q88_SATURATION_POLICY = "saturate"

# Execution targets. Only `fpga_hardware` is a claim about physical silicon.
TARGET_SOFTWARE_FLOAT = "software_float"
TARGET_FIXED_POINT_MODEL = "fixed_point_reference_model"
TARGET_RECORDED_CAPTURE = "recorded_capture"
TARGET_FPGA_HARDWARE = "fpga_hardware"
EXECUTION_TARGETS = (
    TARGET_SOFTWARE_FLOAT,
    TARGET_FIXED_POINT_MODEL,
    TARGET_RECORDED_CAPTURE,
    TARGET_FPGA_HARDWARE,
)
# Targets that are physical silicon, or a recording of physical silicon. These
# require full board/bitstream provenance before any parity claim is accepted.
PHYSICAL_TARGETS = frozenset({TARGET_FPGA_HARDWARE, TARGET_RECORDED_CAPTURE})

# Environment variable that must name a character device for the FPGA adapter
# to even attempt a run. Absent -> unavailable, never simulated in its place.
FPGA_DEVICE_ENV = "SPIKENAUT_FPGA_DEVICE"
FPGA_BITSTREAM_ENV = "SPIKENAUT_FPGA_BITSTREAM"

RESET_MODES = ("zero", "subtract")
DEFAULT_ACTION_LABELS = ("hold", "advance", "retreat", "halt")


class OracleUnavailable(Exception):
    """Raised when an oracle cannot execute. Carries a machine reason code."""

    def __init__(self, reason_code, detail):
        super().__init__(f"{reason_code}: {detail}")
        self.reason_code = reason_code
        self.detail = detail


def canonical_json(obj):
    """Stable JSON text used for every digest in the parity families."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(obj):
    """sha256 of the canonical JSON encoding, prefixed with the algorithm."""
    return "sha256:" + hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def _reject_json_constant(value):
    """Reject Python's non-standard NaN/Infinity JSON extensions.

    Mirrors ``canonical_json``'s ``allow_nan=False`` on the read side: a
    capture file smuggling ``NaN``/``Infinity`` must fail to parse rather
    than load a value ``digest()`` (which forbids non-finite floats) can
    never re-derive.
    """
    raise ValueError(f"non-standard JSON numeric constant {value}")


def _round_half_away(value):
    """Round half away from zero.

    Python's ``round`` is banker's rounding, which would make the float and
    fixed-point paths disagree for reasons unrelated to the format under test.
    Hardware Q8.8 converters overwhelmingly round half away from zero, so that
    is what the recorded conversion provenance claims -- and does.
    """
    if not math.isfinite(value):
        raise ValueError(f"cannot quantize non-finite value {value!r}")
    if value >= 0:
        return math.floor(value + 0.5)
    return math.ceil(value - 0.5)


def q88_quantize(value):
    """Quantize a float to Q8.8. Returns ``(raw_int, saturated_bool)``."""
    raw = _round_half_away(float(value) * Q88_SCALE)
    if raw < Q88_MIN_RAW:
        return Q88_MIN_RAW, True
    if raw > Q88_MAX_RAW:
        return Q88_MAX_RAW, True
    return raw, False


def q88_to_float(raw):
    """Exact dequantization of a Q8.8 raw integer."""
    return raw / Q88_SCALE


def q88_saturate(raw):
    """Clamp an accumulator to the Q8.8 range. Returns ``(raw, saturated)``."""
    if raw < Q88_MIN_RAW:
        return Q88_MIN_RAW, True
    if raw > Q88_MAX_RAW:
        return Q88_MAX_RAW, True
    return raw, False


def q88_mul(a_raw, b_raw):
    """Q8.8 * Q8.8 -> Q8.8 with round-half-away-from-zero and saturation."""
    product = a_raw * b_raw
    half = 1 << (Q88_FRACTIONAL_BITS - 1)
    if product >= 0:
        shifted = (product + half) >> Q88_FRACTIONAL_BITS
    else:
        shifted = -((-product + half) >> Q88_FRACTIONAL_BITS)
    return q88_saturate(shifted)


# ── Model / stimulus contracts ────────────────────────────────────────


def _model_header(model):
    """Required keys and the scalars every other field is sized against."""
    required = ("name", "neurons", "inputs", "w_in", "bias", "threshold", "decay")
    missing = [key for key in required if key not in model]
    if missing:
        raise ValueError(f"model missing keys: {missing}")
    neurons = int(model["neurons"])
    inputs = int(model["inputs"])
    if neurons < 1 or inputs < 1:
        raise ValueError("model needs at least one neuron and one input")
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


# ── Q8.8 conversion provenance ────────────────────────────────────────


def quantize_model(model):
    """Quantize a float model to Q8.8 and record full conversion provenance.

    Returns ``(q_model, provenance)``. ``q_model`` carries raw integers;
    ``provenance`` carries, for every scalar, the float source, the raw
    integer, the dequantized value, the absolute error, and whether the
    conversion saturated. Nothing about the conversion is left implicit.
    """
    model = normalize_model(model)
    entries = []
    saturated_count = 0

    def _convert(path, value):
        nonlocal saturated_count
        raw, saturated = q88_quantize(value)
        if saturated:
            saturated_count += 1
        entries.append(
            {
                "parameter": path,
                "float": value,
                "q88_raw": raw,
                "q88_value": q88_to_float(raw),
                "abs_error": abs(value - q88_to_float(raw)),
                "saturated": saturated,
            }
        )
        return raw

    q_model = {
        "name": model["name"],
        "neurons": model["neurons"],
        "inputs": model["inputs"],
        "refractory_steps": model["refractory_steps"],
        "reset": model["reset"],
        "dt_ms": model["dt_ms"],
        "w_in": [
            [_convert(f"w_in[{i}][{j}]", cell) for j, cell in enumerate(row)]
            for i, row in enumerate(model["w_in"])
        ],
        "w_rec": (
            [
                [_convert(f"w_rec[{i}][{j}]", cell) for j, cell in enumerate(row)]
                for i, row in enumerate(model["w_rec"])
            ]
            if model["w_rec"] is not None
            else None
        ),
        "bias": [_convert(f"bias[{i}]", cell) for i, cell in enumerate(model["bias"])],
        "threshold": [
            _convert(f"threshold[{i}]", cell) for i, cell in enumerate(model["threshold"])
        ],
        "decay": [_convert(f"decay[{i}]", cell) for i, cell in enumerate(model["decay"])],
        "action_labels": list(model["action_labels"]),
    }
    errors = [entry["abs_error"] for entry in entries]
    provenance = {
        "format": "Q8.8",
        "signed": True,
        "total_bits": 16,
        "fractional_bits": Q88_FRACTIONAL_BITS,
        "step": Q88_STEP,
        "representable_range": [Q88_MIN_VALUE, Q88_MAX_VALUE],
        "rounding": Q88_ROUNDING,
        "saturation_policy": Q88_SATURATION_POLICY,
        "units": {"weights": "dimensionless", "threshold": "mV_model", "decay": "ratio"},
        "parameters": entries,
        "parameter_count": len(entries),
        "saturated_parameter_count": saturated_count,
        "max_abs_error": max(errors) if errors else 0.0,
        "mean_abs_error": (sum(errors) / len(errors)) if errors else 0.0,
        "source_model_sha256": digest(model),
    }
    return q_model, provenance


# ── Simulators ────────────────────────────────────────────────────────


def _spike_events(spike_grid, dt_ms):
    events = []
    for step, row in enumerate(spike_grid):
        for neuron, fired in enumerate(row):
            if fired:
                events.append(
                    {"t_step": step, "t_ms": round(step * dt_ms, 6), "neuron_id": neuron}
                )
    return events


def _decode_action(spike_grid, labels):
    """Population argmax decode; ties resolve to the lowest neuron index."""
    counts = [0] * len(labels)
    for row in spike_grid:
        for neuron, fired in enumerate(row):
            if fired:
                counts[neuron] += 1
    if max(counts) == 0:
        return {"index": None, "label": "no_spike", "counts": counts, "rule": "argmax_count"}
    best = 0
    for index in range(1, len(counts)):
        if counts[index] > counts[best]:
            best = index
    return {"index": best, "label": labels[best], "counts": counts, "rule": "argmax_count"}


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


# ── Adapters ──────────────────────────────────────────────────────────


def run_digest(outcome):
    """Fingerprint the complete retained behavioural observation."""
    return digest(
        {
            key: outcome[key]
            for key in ("spikes", "spike_events", "membrane", "action", "arithmetic")
        }
    )


class OracleAdapter:
    """Interface every parity oracle implements.

    ``availability()`` must be answerable without executing anything, and an
    adapter that reports ``available: False`` must raise
    :class:`OracleUnavailable` from ``run`` rather than returning a plausible
    substitute. That is the whole point of the boundary.
    """

    name = "abstract"
    execution_target = None
    runtime_class = "abstract"

    def availability(self):
        raise NotImplementedError

    def run(self, model, stimulus, repeats=1):
        raise NotImplementedError

    def _envelope(self, outcome, repeats, latency, extra=None):
        fingerprint = run_digest(outcome)
        payload = {
            "adapter": self.name,
            "execution_target": self.execution_target,
            "runtime_class": self.runtime_class,
            "repeats": repeats,
            "repeat_digests": [fingerprint] * repeats,
            "determinism": {
                "identical_repeats": True,
                "distinct_digests": 1,
                "meaning": REFERENCE_DETERMINISM_MEANING,
            },
            "latency": latency,
            "output_digest": fingerprint,
        }
        payload.update(outcome)
        if extra:
            payload.update(extra)
        return payload


class SoftwareFloatAdapter(OracleAdapter):
    """The software side of the parity pair."""

    name = "spikenaut_software_float"
    execution_target = TARGET_SOFTWARE_FLOAT
    runtime_class = "in_repo_reference"

    def availability(self):
        return {"available": True, "reason_code": None, "detail": "stdlib float64 simulator"}

    def run(self, model, stimulus, repeats=1):
        outcome = simulate_float(model, stimulus)
        latency = {
            "measured": False,
            "value_ms": None,
            "reason_code": "LATENCY_NOT_MEASURED_SOFTWARE",
            "detail": "wall-clock time of a Python simulator is not a hardware latency",
            "modeled_steps": len(outcome["spikes"]),
        }
        return self._envelope(outcome, repeats, latency)


class FixedPointReferenceAdapter(OracleAdapter):
    """Q8.8 model of an FPGA datapath. Explicitly *not* an FPGA."""

    name = "spikenaut_q88_reference_model"
    execution_target = TARGET_FIXED_POINT_MODEL
    runtime_class = "in_repo_reference"

    def availability(self):
        return {
            "available": True,
            "reason_code": None,
            "detail": "stdlib Q8.8 integer datapath model; no hardware involved",
        }

    def run(self, model, stimulus, repeats=1):
        q_model, provenance = quantize_model(model)
        outcome = simulate_fixed_point(q_model, stimulus)
        latency = {
            "measured": False,
            "value_ms": None,
            "reason_code": "LATENCY_NOT_MEASURED_REFERENCE_MODEL",
            "detail": "a datapath model has no physical latency to report",
            "modeled_steps": len(outcome["spikes"]),
        }
        return self._envelope(
            outcome, repeats, latency, {"quantization": provenance, "q_model": q_model}
        )


class RecordedCaptureAdapter(OracleAdapter):
    """Replays a previously recorded hardware capture from disk.

    The capture's own ``execution_target`` is preserved verbatim, and the
    payload digest is verified against the manifest before anything is
    returned, so a hand-edited capture cannot be replayed as a real run.
    """

    name = "recorded_capture"
    runtime_class = "recorded_capture"

    def __init__(self, capture_path):
        self.capture_path = Path(capture_path)
        self.execution_target = None
        self._capture = None
        self._error = None
        try:
            path_metadata = self.capture_path.lstat()
            if not stat.S_ISREG(path_metadata.st_mode):
                raise OSError("capture path is not a regular file")
            if path_metadata.st_size > MAX_CAPTURE_BYTES:
                raise OSError(
                    f"capture is {path_metadata.st_size} bytes; limit is "
                    f"{MAX_CAPTURE_BYTES}"
                )
            flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(
                os, "O_NOFOLLOW", 0
            )
            descriptor = os.open(self.capture_path, flags)
            try:
                metadata = os.fstat(descriptor)
                if not stat.S_ISREG(metadata.st_mode):
                    raise OSError("capture path is not a regular file")
                if (metadata.st_dev, metadata.st_ino) != (
                    path_metadata.st_dev,
                    path_metadata.st_ino,
                ):
                    raise OSError("capture path changed while it was being opened")
                if metadata.st_size > MAX_CAPTURE_BYTES:
                    raise OSError(
                        f"capture is {metadata.st_size} bytes; limit is "
                        f"{MAX_CAPTURE_BYTES}"
                    )
                with os.fdopen(descriptor, "rb", closefd=False) as handle:
                    payload = handle.read(MAX_CAPTURE_BYTES + 1)
                if len(payload) > MAX_CAPTURE_BYTES:
                    raise OSError(f"capture exceeds {MAX_CAPTURE_BYTES} bytes")
            finally:
                os.close(descriptor)
            self._capture = json.loads(
                payload.decode("utf-8"), parse_constant=_reject_json_constant
            )
        except FileNotFoundError:
            self._error = ("CAPTURE_FILE_ABSENT", f"no capture at {self.capture_path}")
        except OSError as exc:
            self._error = (
                "CAPTURE_UNREADABLE",
                f"cannot read {self.capture_path}: {exc}",
            )
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
            self._error = ("CAPTURE_UNREADABLE", str(exc))
        if self._capture is not None:
            if not isinstance(self._capture, dict):
                self._error = ("CAPTURE_UNREADABLE", "capture must be a JSON object")
            else:
                self.execution_target = self._capture.get("execution_target")
                if self.execution_target not in EXECUTION_TARGETS:
                    self._error = (
                        "CAPTURE_TARGET_UNKNOWN",
                        f"execution_target {self.execution_target!r} is not a known target",
                    )

    def availability(self):
        if self._error:
            return {"available": False, "reason_code": self._error[0], "detail": self._error[1]}
        return {
            "available": True,
            "reason_code": None,
            "detail": f"capture {self.capture_path.name}",
        }

    def run(self, model, stimulus, repeats=1):
        if self._error:
            raise OracleUnavailable(*self._error)
        capture = self._capture
        manifest = capture.get("manifest") or {}
        if not isinstance(manifest, dict):
            raise OracleUnavailable(
                "CAPTURE_UNREADABLE", "capture manifest must be a JSON object"
            )
        payload = capture.get("payload")
        if not isinstance(payload, dict):
            raise OracleUnavailable(
                "CAPTURE_UNREADABLE", "capture payload must be a JSON object"
            )
        try:
            actual = digest(payload)
        except (TypeError, ValueError, OverflowError) as exc:
            raise OracleUnavailable(
                "CAPTURE_UNREADABLE",
                f"capture payload is not canonical finite JSON: {exc}",
            ) from exc
        if manifest.get("payload_sha256") != actual:
            raise OracleUnavailable(
                "CAPTURE_DIGEST_MISMATCH",
                f"capture payload digest {actual} != manifest "
                f"{manifest.get('payload_sha256')}",
            )
        model = normalize_model(model)
        fixture = stimulus_fixture(normalize_stimulus(stimulus, model["inputs"]))
        if manifest.get("input_fixture_sha256") != fixture["sha256"]:
            raise OracleUnavailable(
                "CAPTURE_INPUT_FIXTURE_MISMATCH",
                "capture was taken against a different encoded input fixture",
            )
        # The Q8.8 export is what was loaded onto the board. Report its absence
        # before checking the retained observation so the failure identifies
        # the actual missing provenance rather than a secondary shape detail.
        quantization = capture.get("quantization") or payload.get("quantization")
        if not quantization:
            raise OracleUnavailable(
                "CAPTURE_QUANTIZATION_MISSING",
                "capture must record the Q8.8 conversion that produced the bitstream",
            )
        missing = [
            key
            for key in (
                "spikes",
                "spike_events",
                "membrane",
                "action",
                "arithmetic",
                "repeat_outputs",
                "repeat_digests",
            )
            if key not in payload
        ]
        if missing:
            raise OracleUnavailable(
                "CAPTURE_UNREADABLE", f"capture payload is missing {missing}"
            )
        try:
            fingerprint = run_digest(payload)
        except (KeyError, TypeError, AttributeError) as exc:
            raise OracleUnavailable(
                "CAPTURE_UNREADABLE", f"capture payload is malformed: {exc}"
            ) from exc
        repeat_outputs = payload["repeat_outputs"]
        repeat_digests = payload["repeat_digests"]
        if (
            not isinstance(repeat_outputs, list)
            or not repeat_outputs
            or not isinstance(repeat_digests, list)
            or len(repeat_outputs) != len(repeat_digests)
        ):
            raise OracleUnavailable(
                "CAPTURE_UNREADABLE",
                "capture repeat_outputs and repeat_digests must be nonempty arrays "
                "with identical cardinality",
            )
        for index, (repeat_output, recorded_digest) in enumerate(
            zip(repeat_outputs, repeat_digests)
        ):
            try:
                expected_digest = run_digest(repeat_output)
            except (KeyError, TypeError, ValueError, AttributeError) as exc:
                raise OracleUnavailable(
                    "CAPTURE_UNREADABLE",
                    f"capture repeat_outputs[{index}] is malformed: {exc}",
                ) from exc
            if recorded_digest != expected_digest:
                raise OracleUnavailable(
                    "CAPTURE_DIGEST_MISMATCH",
                    f"capture repeat_digests[{index}] is not derived from "
                    f"repeat_outputs[{index}]",
                )
        primary = {
            key: payload.get(key)
            for key in ("spikes", "spike_events", "membrane", "action", "arithmetic")
        }
        first = (
            {
                key: repeat_outputs[0].get(key)
                for key in (
                    "spikes",
                    "spike_events",
                    "membrane",
                    "action",
                    "arithmetic",
                )
            }
            if isinstance(repeat_outputs[0], dict)
            else None
        )
        try:
            first_json = canonical_json(first)
            primary_json = canonical_json(primary)
        except (TypeError, ValueError, OverflowError) as exc:
            raise OracleUnavailable(
                "CAPTURE_UNREADABLE",
                f"capture retained observation is not canonical finite JSON: {exc}",
            ) from exc
        if first_json != primary_json:
            raise OracleUnavailable(
                "CAPTURE_DIGEST_MISMATCH",
                "capture payload does not match its first retained repeat output",
            )
        return {
            "quantization": quantization,
            "adapter": self.name,
            "execution_target": self.execution_target,
            "runtime_class": self.runtime_class,
            "repeats": len(repeat_digests),
            "repeat_digests": repeat_digests,
            "determinism": {
                "identical_repeats": len(set(repeat_digests)) == 1,
                "distinct_digests": len(set(repeat_digests)),
                "meaning": "run-to-run variability observed during the recorded capture",
            },
            "latency": payload.get("latency"),
            "output_digest": fingerprint,
            "spikes": payload["spikes"],
            "spike_events": payload["spike_events"],
            "membrane": payload["membrane"],
            "action": payload["action"],
            "arithmetic": payload["arithmetic"],
            "hardware": capture.get("hardware"),
            "bitstream": capture.get("bitstream"),
            "capture": {
                "path": self.capture_path.name,
                # Keep the replay source on the record so validation can
                # re-check the same digest chain the adapter checked.  A bare
                # manifest label is not evidence: without these source bytes a
                # fixed-point record could be relabelled as a capture and
                # decorated with plausible-looking hashes.
                "source_sha256": digest(capture),
                "manifest_sha256": digest(manifest),
                "payload_sha256": actual,
                "recorded_at": manifest.get("recorded_at"),
                "source": capture,
            },
        }


class FpgaHardwareAdapter(OracleAdapter):
    """Real FPGA execution target.

    This adapter has no fallback. If no board is declared and reachable it
    reports unavailability with a reason code and ``run`` raises. There is no
    code path in this module by which an ``fpga_hardware`` result can be
    produced without a board.
    """

    name = "spikenaut_fpga"
    execution_target = TARGET_FPGA_HARDWARE
    runtime_class = "physical_hardware"

    def __init__(self, env=None):
        self.env = os.environ if env is None else env

    def availability(self):
        device = self.env.get(FPGA_DEVICE_ENV)
        if not device:
            return {
                "available": False,
                "reason_code": "FPGA_DEVICE_NOT_DECLARED",
                "detail": (
                    f"{FPGA_DEVICE_ENV} is unset; no board is claimed and none is assumed"
                ),
            }
        if not Path(device).exists():
            return {
                "available": False,
                "reason_code": "FPGA_DEVICE_ABSENT",
                "detail": f"declared device {device} does not exist",
            }
        if not self.env.get(FPGA_BITSTREAM_ENV):
            return {
                "available": False,
                "reason_code": "FPGA_BITSTREAM_NOT_DECLARED",
                "detail": (
                    f"{FPGA_BITSTREAM_ENV} is unset; a parity run without a pinned "
                    "bitstream hash is not attributable"
                ),
            }
        return {
            "available": False,
            "reason_code": "FPGA_DRIVER_NOT_IMPLEMENTED",
            "detail": (
                "device and bitstream are declared but this repository ships no board "
                "transport; implement one before claiming fpga_hardware"
            ),
        }

    def run(self, model, stimulus, repeats=1):
        status = self.availability()
        raise OracleUnavailable(status["reason_code"], status["detail"])


ADAPTERS = {
    SoftwareFloatAdapter.name: SoftwareFloatAdapter,
    FixedPointReferenceAdapter.name: FixedPointReferenceAdapter,
    FpgaHardwareAdapter.name: FpgaHardwareAdapter,
}


def get_adapter(name, **kwargs):
    """Construct an adapter by name. Captures are addressed by path."""
    if name == RecordedCaptureAdapter.name:
        return RecordedCaptureAdapter(**kwargs)
    if name not in ADAPTERS:
        raise KeyError(f"unknown oracle adapter {name!r}")
    return ADAPTERS[name](**kwargs)


def availability_report(env=None):
    """What can actually run here, and the reason code for what cannot."""
    report = {}
    for name, factory in ADAPTERS.items():
        adapter = factory(env=env) if factory is FpgaHardwareAdapter else factory()
        status = dict(adapter.availability())
        status["execution_target"] = adapter.execution_target
        status["runtime_class"] = adapter.runtime_class
        report[name] = status
    return report


def main(argv=None):
    """``python3 pipelines/neuro_oracle.py`` prints the availability report."""
    print(json.dumps(availability_report(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
