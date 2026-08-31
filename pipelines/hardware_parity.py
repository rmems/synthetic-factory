#!/usr/bin/env python3
"""`hardware-parity-spike-trajectories` generator, oracle driver, and validator.

The question this family answers is behavioural, not procedural:

    does a known software Spikenaut execution still do the same thing after
    Q8.8 export and execution on the deployment target?

A successful export, a successful build, and a successful board load are not
evidence of that. Only paired spike trains are.

What actually runs here
-----------------------
The software side is the float64 LIF reference in ``neuro_oracle``. The
deployment side is whichever adapter the caller names. In this repository the
only deployment-side adapter that can execute is the **Q8.8 fixed-point
reference model** -- a model of an FPGA datapath, not an FPGA. Records emitted
against it say ``fixed_point_reference_model`` and their reason codes say
``ORACLE_UNAVAILABLE`` for the hardware leg. The validator refuses to accept a
record claiming ``fpga_hardware`` or ``recorded_capture`` unless it carries
board revision, bitstream hash, capture manifest digest, and a measured
latency -- values only a real run can produce.

Every number in ``result.parity`` is recomputed from the recorded spike and
membrane traces during validation, so a record cannot assert an agreement its
own traces do not support.

Usage:
  python3 pipelines/hardware_parity.py availability
  python3 pipelines/hardware_parity.py generate <out_dir> [--round N] [--steps N]
                                       [--repeats N] [--target NAME] [--capture PATH]
  python3 pipelines/hardware_parity.py validate <path>
  python3 pipelines/hardware_parity.py training-view <path>
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import sys
from pathlib import Path

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

import oracle_contract as contract  # noqa: E402
from neuro_oracle import (  # noqa: E402
    CAPTURE_DETERMINISM_MEANING,
    PHYSICAL_TARGETS,
    Q88_MAX_RAW,
    Q88_MIN_RAW,
    Q88_STEP,
    REFERENCE_DETERMINISM_MEANING,
    TARGET_FIXED_POINT_MODEL,
    TARGET_FPGA_HARDWARE,
    FixedPointReferenceAdapter,
    FpgaHardwareAdapter,
    OracleUnavailable,
    RecordedCaptureAdapter,
    SoftwareFloatAdapter,
    availability_report,
    digest,
    get_adapter,
    normalize_model,
    normalize_stimulus,
    q88_to_float,
    quantize_model,
    run_digest,
    stimulus_fixture,
)

SCHEMA_VERSION = "1.0.0"
VALIDATOR = "pipelines/hardware_parity.py"
FACTORY_SLUG = "hardware-parity-spike-trajectories"
RECORD_KIND = contract.KIND_HARDWARE_PARITY

# A membrane difference larger than four Q8.8 least-significant bits is worth a
# reason code even when the spike trains agree: it says the two datapaths are
# drifting and the agreement may not survive a longer window.
MEMBRANE_TOLERANCE = 4 * Q88_STEP
# Float comparison tolerance when re-deriving recorded metrics.
METRIC_TOL = 1e-9
VALIDATION_DATA_ERRORS = (
    TypeError,
    ValueError,
    OverflowError,
    RecursionError,
    UnicodeError,
    KeyError,
    IndexError,
    AttributeError,
)

# The one pairing this family measures. Free text here would let a record
# advertise an execution (e.g. a live FPGA) that its adapter legs do not
# substantiate, so validation pins it to this canonical value.
ORACLE_PAIRING = "software_simulator <-> deployment_target"

GENERATOR_BLOCK = {
    "name": "synthetic-factory.hardware_parity.scenario_catalog",
    "model": "deterministic-stdlib-catalog",
    "role": "proposes test configurations and perturbations",
    "produced": ["scenario", "intervention", "candidate_prediction"],
    "may_certify_oracle_result": False,
    "note": (
        "Scenarios in this fixture are authored by a deterministic in-repo catalog, "
        "not by a language model. Whoever authors them, the generator block never "
        "supplies result fields."
    ),
}


# ── Scenario catalog ──────────────────────────────────────────────────


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


# ── Parity metrics ────────────────────────────────────────────────────


def _first_spike_steps(spike_grid, neurons):
    firsts = [None] * neurons
    for step, row in enumerate(spike_grid):
        for neuron in range(neurons):
            if row[neuron] and firsts[neuron] is None:
                firsts[neuron] = step
    return firsts


def _rectangular(grid):
    """True when `grid` is a non-empty list of equal-length non-empty rows.

    Ragged grids are rejected up front rather than indexed into: a short row
    would otherwise raise mid-comparison and take down the scan of an entire
    run directory instead of reporting one bad record.
    """
    if not isinstance(grid, list) or not grid:
        return False
    if not all(isinstance(row, list) for row in grid):
        return False
    width = len(grid[0])
    return width > 0 and all(len(row) == width for row in grid)


def spike_bitmap_metrics(software, hardware):
    """Cell-by-cell agreement over the (timestep, neuron) spike bitmap."""
    if not software or not hardware:
        return {"comparable": False, "reason": "empty spike grid"}
    if not _rectangular(software) or not _rectangular(hardware):
        return {"comparable": False, "reason": "spike grid is ragged or malformed"}
    if len(software) != len(hardware) or len(software[0]) != len(hardware[0]):
        return {"comparable": False, "reason": "spike grids have different shapes"}
    steps = len(software)
    neurons = len(software[0])
    matches = 0
    false_positive = 0
    false_negative = 0
    both = 0
    either = 0
    for step in range(steps):
        for neuron in range(neurons):
            a = software[step][neuron]
            b = hardware[step][neuron]
            if a == b:
                matches += 1
            elif b and not a:
                false_positive += 1
            else:
                false_negative += 1
            if a or b:
                either += 1
            if a and b:
                both += 1
    cells = steps * neurons
    return {
        "comparable": True,
        "cells": cells,
        "matching_cells": matches,
        "agreement": matches / cells,
        "hamming_distance": false_positive + false_negative,
        "hardware_only_spikes": false_positive,
        "software_only_spikes": false_negative,
        "jaccard": (both / either) if either else 1.0,
        "software_spike_count": sum(sum(row) for row in software),
        "hardware_spike_count": sum(sum(row) for row in hardware),
    }


def timing_metrics(software, hardware, dt_ms):
    """First-spike timing error over neurons that fired on both sides."""
    if not _rectangular(software) or not _rectangular(hardware):
        return {"comparable": False, "reason": "spike grid is ragged or malformed"}
    if len(software) != len(hardware) or len(software[0]) != len(hardware[0]):
        return {"comparable": False, "reason": "spike grids have different shapes"}
    neurons = len(software[0])
    soft_first = _first_spike_steps(software, neurons)
    hard_first = _first_spike_steps(hardware, neurons)
    deltas = []
    only_software = 0
    only_hardware = 0
    for neuron in range(neurons):
        a = soft_first[neuron]
        b = hard_first[neuron]
        if a is None and b is None:
            continue
        if a is None:
            only_hardware += 1
        elif b is None:
            only_software += 1
        else:
            deltas.append(abs(a - b))
    return {
        "comparable": True,
        "unit": "timesteps",
        "dt_ms": dt_ms,
        "compared_neurons": len(deltas),
        "max_abs_step_error": max(deltas) if deltas else 0,
        "mean_abs_step_error": (sum(deltas) / len(deltas)) if deltas else 0.0,
        "max_abs_ms_error": (max(deltas) * dt_ms) if deltas else 0.0,
        "neurons_firing_software_only": only_software,
        "neurons_firing_hardware_only": only_hardware,
    }


MEMBRANE_UNITS = "mV_model"


def _membrane_incomparable_reason(software_membrane, hardware_membrane, soft, hard):
    """Why the two membrane traces cannot be compared, or None if they can."""
    if not (software_membrane or {}).get("observable") or not (
        hardware_membrane or {}
    ).get("observable"):
        return "at least one side does not expose membrane state"
    if (
        (software_membrane or {}).get("units") != MEMBRANE_UNITS
        or (hardware_membrane or {}).get("units") != MEMBRANE_UNITS
    ):
        # A recorded capture is untrusted input and may label its observable
        # trace with another unit (or omit it). Comparing numeric values
        # across units would produce a numerically valid but dimensionally
        # meaningless error, so treat a unit mismatch the same as a missing
        # trace rather than silently comparing raw numbers.
        return f"both membrane traces must be {MEMBRANE_UNITS!r} units"
    if (
        not _rectangular(soft)
        or not _rectangular(hard)
        or len(soft) != len(hard)
        or len(soft[0]) != len(hard[0])
    ):
        # Carries a reason code for the same purpose as the branch above:
        # deleting membrane evidence must never be quieter than reporting it.
        return "membrane traces have different shapes"
    return None


def membrane_metrics(software_membrane, hardware_membrane):
    """Membrane error where both sides expose an observable trace."""
    soft = (software_membrane or {}).get("trace")
    hard = (hardware_membrane or {}).get("trace")
    reason = _membrane_incomparable_reason(
        software_membrane, hardware_membrane, soft, hard
    )
    if reason is not None:
        return {
            "observable": False,
            "reason_code": "MEMBRANE_DIVERGENCE",
            "reason": reason,
        }
    diffs = [abs(a - b) for row_a, row_b in zip(soft, hard) for a, b in zip(row_a, row_b)]
    return {
        "observable": True,
        "units": MEMBRANE_UNITS,
        "samples": len(diffs),
        "max_abs_error": max(diffs) if diffs else 0.0,
        "mean_abs_error": (sum(diffs) / len(diffs)) if diffs else 0.0,
        "tolerance": MEMBRANE_TOLERANCE,
        "within_tolerance": (max(diffs) if diffs else 0.0) <= MEMBRANE_TOLERANCE,
    }


def quantization_metrics(deployment_run):
    """Restate the recorded Q8.8 conversion error as parity evidence.

    Two independent kinds of saturation matter and are counted separately:
    *export* saturation, where a parameter does not fit the format, and
    *runtime* saturation, where every parameter fits but a partial sum does
    not. The second kind leaves the exported weights looking perfectly
    faithful, so it has to be reported from the run rather than the export.
    """
    provenance = (deployment_run or {}).get("quantization")
    runtime_saturation = ((deployment_run or {}).get("arithmetic") or {}).get(
        "saturation_events"
    )
    if not provenance:
        return {
            "available": False,
            "reason": "deployment side did not report a quantization provenance",
            "runtime_saturation_events": runtime_saturation,
        }
    return {
        "available": True,
        "format": provenance.get("format"),
        "parameter_count": provenance.get("parameter_count"),
        "max_abs_error": provenance.get("max_abs_error"),
        "mean_abs_error": provenance.get("mean_abs_error"),
        "saturated_parameter_count": provenance.get("saturated_parameter_count"),
        "runtime_saturation_events": runtime_saturation,
        "step": provenance.get("step"),
    }


def repeatability_metrics(software_run, hardware_run):
    """Determinism of each side, kept distinct from hardware repeatability."""
    software_det = software_run.get("determinism", {})
    hardware_det = hardware_run.get("determinism", {})
    physical = hardware_run.get("execution_target") in PHYSICAL_TARGETS
    return {
        "software": {
            "repeats": software_run.get("repeats"),
            "distinct_digests": software_det.get("distinct_digests"),
            "identical_repeats": software_det.get("identical_repeats"),
        },
        "deployment": {
            "repeats": hardware_run.get("repeats"),
            "distinct_digests": hardware_det.get("distinct_digests"),
            "identical_repeats": hardware_det.get("identical_repeats"),
        },
        "hardware_repeatability_measured": physical,
        "meaning": hardware_det.get("meaning"),
    }


def compute_parity(scenario, software_run, hardware_run):
    """All parity metrics for one paired run, plus the verdict they support."""
    dt_ms = scenario["stimulus"]["dt_ms"]
    bitmap = spike_bitmap_metrics(software_run.get("spikes"), hardware_run.get("spikes"))
    timing = timing_metrics(
        software_run.get("spikes"), hardware_run.get("spikes"), dt_ms
    )
    membrane = membrane_metrics(software_run.get("membrane"), hardware_run.get("membrane"))
    quantization = quantization_metrics(hardware_run)
    repeatability = repeatability_metrics(software_run, hardware_run)
    software_action = software_run.get("action", {})
    hardware_action = hardware_run.get("action", {})
    action = {
        "software": software_action.get("label"),
        "deployment": hardware_action.get("label"),
        "software_counts": software_action.get("counts"),
        "deployment_counts": hardware_action.get("counts"),
        "agree": software_action.get("label") == hardware_action.get("label"),
        "decode_rule": software_action.get("rule"),
    }

    reason_codes = []
    if not bitmap.get("comparable") or bitmap.get("hamming_distance", 1) > 0:
        reason_codes.append("SPIKE_BITMAP_DISAGREEMENT")
    if not action["agree"]:
        reason_codes.append("ACTION_DISAGREEMENT")
    if membrane.get("observable") and not membrane.get("within_tolerance"):
        reason_codes.append("MEMBRANE_DIVERGENCE")
    if not membrane.get("observable") and membrane.get("reason_code"):
        reason_codes.append(membrane["reason_code"])
    if quantization.get("saturated_parameter_count") or quantization.get(
        "runtime_saturation_events"
    ):
        reason_codes.append("QUANTIZATION_SATURATION")
    if not repeatability["hardware_repeatability_measured"]:
        reason_codes.append("REPEATABILITY_UNPROVEN")
    if not (hardware_run.get("latency") or {}).get("measured"):
        reason_codes.append("LATENCY_NOT_MEASURED")
    if hardware_run.get("execution_target") not in PHYSICAL_TARGETS:
        reason_codes.append("ORACLE_UNAVAILABLE")
    else:
        # A physical run is not reproducible from software -- that is why it
        # was run on hardware. Its traces therefore rest on the integrity of
        # the capture and on the board provenance, and were not re-derived.
        # This code makes that limitation visible on every hardware-claiming
        # record instead of leaving such a record looking unqualified.
        reason_codes.append("DEPLOYMENT_TRACE_NOT_REDERIVABLE")

    behavioural_mismatch = (
        "SPIKE_BITMAP_DISAGREEMENT" in reason_codes or "ACTION_DISAGREEMENT" in reason_codes
    )
    verdict = contract.VERDICT_MISMATCH if behavioural_mismatch else contract.VERDICT_MATCH
    parity = {
        "spike_bitmap": bitmap,
        "action": action,
        "timing": timing,
        "membrane": membrane,
        "quantization": quantization,
        "repeatability": repeatability,
        "verdict_rule": (
            "verdict is `mismatch` iff the spike bitmaps differ or the decoded actions "
            "differ; membrane, quantization, repeatability and latency findings are "
            "always carried as reason codes even when the verdict is `match`"
        ),
    }
    return parity, verdict, sorted(set(reason_codes))


# ── Record construction ───────────────────────────────────────────────


def _slim_run(run):
    """The oracle payload as stored on the record.

    The full Q8.8 model is dropped (it is exactly re-derivable from the float
    model, and validation re-derives it), but every observation is kept.
    """
    keep = (
        "adapter",
        "execution_target",
        "runtime_class",
        "repeats",
        "repeat_digests",
        "determinism",
        "latency",
        "output_digest",
        "spikes",
        "spike_events",
        "membrane",
        "action",
        "arithmetic",
        "quantization",
        "hardware",
        "bitstream",
        "capture",
    )
    return {key: run[key] for key in keep if key in run}


def run_pair(scenario, deployment_adapter, software_adapter=None, repeats=3):
    """Execute both sides of the pair against the identical input fixture."""
    software_adapter = software_adapter or SoftwareFloatAdapter()
    model = scenario["model_float"]
    stimulus = scenario["stimulus"]
    software_run = software_adapter.run(model, stimulus, repeats=repeats)
    try:
        deployment_run = deployment_adapter.run(model, stimulus, repeats=repeats)
        unavailable = None
    except OracleUnavailable as exc:
        deployment_run = None
        unavailable = {
            "adapter": deployment_adapter.name,
            "execution_target": deployment_adapter.execution_target,
            "reason_code": exc.reason_code,
            "detail": exc.detail,
        }
        if isinstance(deployment_adapter, RecordedCaptureAdapter):
            unavailable["adapter_config"] = {
                "capture_path": str(deployment_adapter.capture_path)
            }
    return software_run, deployment_run, unavailable


def build_record(scenario, software_run, deployment_run, unavailable, round_number,
                 fpga_status):
    """Assemble one envelope record from a paired run."""
    # Deep-copied so no two records (and no two fields of one record) share a
    # mutable sub-object: an edit to one would otherwise silently rewrite the
    # other, which is precisely the failure mode these records exist to catch.
    fixture = copy.deepcopy(scenario["input_fixture"])
    oracle = {
        "pairing": ORACLE_PAIRING,
        "input_fixture": fixture,
        "identical_input_fixture": True,
        "software": None,
        "deployment": None,
        "unavailable": [],
        "environment": {
            "fpga_hardware": fpga_status,
            "note": (
                "the availability probe is recorded on every record so a reader can "
                "tell an unexecuted hardware leg from an omitted one"
            ),
        },
    }
    requested_deployment = None
    if unavailable:
        oracle["unavailable"].append(unavailable)
        requested_deployment = {
            key: copy.deepcopy(unavailable[key])
            for key in ("adapter", "execution_target", "adapter_config")
            if key in unavailable
        }
        oracle["requested_deployment"] = requested_deployment

    prediction = {
        "source": "generator",
        "authoritative": False,
        "hypothesis": scenario["hypothesis"],
        "expected_verdict": (
            contract.VERDICT_MATCH if scenario["stress"] == "none"
            else contract.VERDICT_MISMATCH
        ),
    }
    # A run that touched silicon is hardware-in-the-loop; one that did not is
    # simulated. Deriving this from the target that actually executed keeps the
    # record from describing one execution two different ways.
    deployment_target = (deployment_run or {}).get("execution_target")
    scenario_evidence = {
        "model": scenario["model_float"],
        "stimulus": scenario["stimulus"],
    }
    if requested_deployment is not None:
        scenario_evidence["requested_deployment"] = requested_deployment
    provenance = {
        "kind": "hil" if deployment_target in PHYSICAL_TARGETS else "simulated",
        "tool": VALIDATOR,
        "tool_version": SCHEMA_VERSION,
        "contract_version": contract.CONTRACT_VERSION,
        "scenario_sha256": digest(scenario_evidence),
        "units": {
            "time": "ms",
            "membrane": "mV_model",
            "weights": "dimensionless",
            "latency": "ms",
        },
    }

    record = {
        "id": f"{scenario['id']}-r{round_number:02d}",
        "record_kind": RECORD_KIND,
        "dataset": contract.DATASET_FOR_KIND[RECORD_KIND],
        "schema_version": SCHEMA_VERSION,
        "generator": copy.deepcopy(GENERATOR_BLOCK),
        "scenario": {
            "id": scenario["id"],
            "name": scenario["name"],
            "family": scenario["family"],
            "stress": scenario["stress"],
            "description": scenario["description"],
            "model_float": scenario["model_float"],
            "model_sha256": scenario["model_sha256"],
            "stimulus": scenario["stimulus"],
            "input_fixture": copy.deepcopy(fixture),
        },
        "intervention": copy.deepcopy(scenario["intervention"]),
        "candidate_prediction": prediction,
        "oracle": oracle,
        "result": None,
        "provenance": provenance,
        "validation": {
            "validator": VALIDATOR,
            "validator_version": SCHEMA_VERSION,
            "checks": [
                "envelope_contract",
                "identical_input_fixture",
                "q88_conversion_reproducible",
                "parity_metrics_recomputed_from_traces",
                "verdict_consistent_with_traces",
            ],
            # No cached pass. A stored "validated" stamp is exactly what a
            # tampered record would forge, so the checks are named here and
            # re-run by the reader instead.
            "status": "revalidate_on_read",
        },
        "meta": {"round": round_number, "factory": FACTORY_SLUG},
    }

    if deployment_run is None:
        oracle["software"] = _slim_run(software_run)
        record["result"] = _unpaired_result(software_run, unavailable)
        return record

    oracle["software"] = _slim_run(software_run)
    oracle["deployment"] = _slim_run(deployment_run)
    record["result"] = _paired_result(scenario, software_run, deployment_run)
    return record


def _unpaired_result(software_run, unavailable):
    """The result block for a round whose deployment oracle never ran."""
    unavailable_digest = _unavailable_evidence_digest(unavailable)
    return {
        "oracle_backed": True,
        "verdict": contract.VERDICT_INCONCLUSIVE,
        "reason_codes": ["ORACLE_UNAVAILABLE"],
        "derived_from": [software_run["output_digest"], unavailable_digest],
        "parity": None,
        "summary": _summarize_unpaired(unavailable),
    }


def _paired_result(scenario, software_run, deployment_run):
    """The result block computed from both executed oracle legs."""
    parity, verdict, reason_codes = compute_parity(scenario, software_run, deployment_run)
    derived_from = [software_run["output_digest"], deployment_run["output_digest"]]
    capture_digest = _capture_evidence_digest(deployment_run)
    if capture_digest is not None:
        derived_from.append(capture_digest)
    return {
        "oracle_backed": True,
        "verdict": verdict,
        "reason_codes": reason_codes,
        "derived_from": derived_from,
        "parity": parity,
        "summary": _summarize(scenario, parity, verdict, deployment_run),
    }


def _summarize(scenario, parity, verdict, deployment_run):
    bitmap = parity["spike_bitmap"]
    target = deployment_run.get("execution_target")
    agreement = bitmap.get("agreement")
    agreement_text = f"{agreement:.4f}" if isinstance(agreement, float) else "n/a"
    return (
        f"{scenario['name']}: software float64 vs {target}. "
        f"spike bitmap agreement {agreement_text}, "
        f"hamming {bitmap.get('hamming_distance')}, "
        f"action {parity['action']['software']!r} vs {parity['action']['deployment']!r}, "
        f"max membrane error {parity['membrane'].get('max_abs_error')}, "
        f"verdict {verdict}."
    )


def _summarize_unpaired(unavailable):
    reason = unavailable.get("reason_code") if isinstance(unavailable, dict) else "unknown"
    return (
        "no paired run: the deployment-side oracle did not execute "
        f"({reason}). This record carries the software leg as evidence and makes no "
        "parity claim."
    )


def _unavailable_evidence_digest(unavailable):
    """Fingerprint the exact deployment diagnostic used instead of a run.

    The family validator separately replays the selected adapter's availability
    probe and requires this object to match it. Domain-separating the object here
    makes that authenticated diagnostic a first-class lineage item alongside the
    software output digest.
    """
    if not isinstance(unavailable, dict):
        raise TypeError("deployment diagnostic must be an object")
    return digest(
        {
            "evidence_kind": "deployment_unavailable_diagnostic",
            "diagnostic": unavailable,
        }
    )


def _capture_evidence_digest(deployment_run):
    """Fingerprint a physical capture's provenance for the lineage list.

    ``deployment_run["output_digest"]`` covers only the behavioural outcome
    (spikes/events/membrane/action/arithmetic). Two captures with identical
    behaviour but different board identity, bitstream, or capture source
    would otherwise collapse to the same ``result.derived_from`` lineage.
    Returns ``None`` for a non-physical (e.g. fixed-point model) deployment,
    which has no capture envelope to fingerprint.
    """
    capture = deployment_run.get("capture") if isinstance(deployment_run, dict) else None
    if not isinstance(capture, dict):
        return None
    return digest(
        {
            "evidence_kind": "capture_physical_provenance",
            "hardware": deployment_run.get("hardware"),
            "bitstream": deployment_run.get("bitstream"),
            "capture_manifest_sha256": capture.get("manifest_sha256"),
            "capture_source_sha256": capture.get("source_sha256"),
            "latency": deployment_run.get("latency"),
        }
    )


def _expected_summary(record):
    """Re-derive supervised prose from structured, validated evidence."""
    oracle = record.get("oracle") or {}
    result = record.get("result") or {}
    deployment = oracle.get("deployment")
    if deployment is None:
        unavailable = oracle.get("unavailable") or []
        return _summarize_unpaired(unavailable[0] if unavailable else None)
    parity = result.get("parity")
    if not isinstance(parity, dict) or not isinstance(deployment, dict):
        return None
    return _summarize(
        record.get("scenario") or {},
        parity,
        result.get("verdict"),
        deployment,
    )


def generate_records(round_number=1, steps=12, deployment_adapter=None, repeats=3,
                     env=None):
    """Generate one round of paired records for the whole scenario catalog."""
    deployment_adapter = deployment_adapter or FixedPointReferenceAdapter()
    fpga_status = availability_report(env=env)["spikenaut_fpga"]
    records = []
    for scenario in build_scenarios(steps=steps):
        software_run, deployment_run, unavailable = run_pair(
            scenario, deployment_adapter, repeats=repeats
        )
        records.append(
            build_record(
                scenario, software_run, deployment_run, unavailable, round_number,
                fpga_status,
            )
        )
    return records


# ── Validation ────────────────────────────────────────────────────────

# Metadata a record must carry before a physical-target parity claim is
# believed. None of it can be produced without an actual run.
REQUIRED_HARDWARE_FIELDS = (
    ("hardware", "revision"),
    ("hardware", "board_serial"),
    ("bitstream", "sha256"),
    ("bitstream", "toolchain"),
    ("capture", "manifest_sha256"),
)


def _metric_mismatch(path, where, recorded, recomputed):
    """The one mismatch message shared by every scalar branch below."""
    return (
        f"{where}: {path} recorded {recorded!r} but traces give {recomputed!r} "
        "[PARITY_METRIC_MISMATCH]"
    )


def _metrics_equal_dict(recorded, recomputed, path, where):
    if not isinstance(recorded, dict):
        return [f"{where}: {path} must be an object [PARITY_METRIC_MISMATCH]"]
    errors = [
        f"{where}: {path}.{key} is unexpected [PARITY_METRIC_MISMATCH]"
        for key in recorded.keys() - recomputed.keys()
    ]
    for key, value in recomputed.items():
        if key not in recorded:
            errors.append(f"{where}: {path}.{key} is missing [PARITY_METRIC_MISMATCH]")
            continue
        errors += _metrics_equal(recorded[key], value, f"{path}.{key}", where)
    return errors


def _metrics_equal_list(recorded, recomputed, path, where):
    if not isinstance(recorded, list):
        return [f"{where}: {path} must be an array [PARITY_METRIC_MISMATCH]"]
    errors = []
    if len(recorded) != len(recomputed):
        errors.append(
            f"{where}: {path} has {len(recorded)} items but traces give "
            f"{len(recomputed)} [PARITY_METRIC_MISMATCH]"
        )
    for index, (left, right) in enumerate(zip(recorded, recomputed)):
        errors += _metrics_equal(left, right, f"{path}[{index}]", where)
    return errors


def _metrics_equal_float(recorded, recomputed, path, where):
    """Exact-typed finite floats compared under the metric tolerance."""
    if not isinstance(recorded, float) or not math.isfinite(recorded):
        return [
            f"{where}: {path} must be a finite float matching {recomputed!r}, got "
            f"{recorded!r} [PARITY_METRIC_MISMATCH]"
        ]
    if not math.isfinite(recomputed) or abs(recorded - recomputed) > METRIC_TOL:
        return [_metric_mismatch(path, where, recorded, recomputed)]
    return []


def _metrics_equal_scalar(recorded, recomputed, path, where):
    # JSON numbers still arrive as distinct Python integer and float values,
    # while `bool` is a subclass of `int`. Keep those types exact and reject
    # non-finite floats before applying a tolerance; otherwise True can stand
    # in for 1 and NaN compares equal to every finite metric here.
    if isinstance(recomputed, bool):
        matched = isinstance(recorded, bool) and recorded is recomputed
    elif isinstance(recomputed, int):
        matched = (
            isinstance(recorded, int)
            and not isinstance(recorded, bool)
            and recorded == recomputed
        )
    elif isinstance(recomputed, float):
        return _metrics_equal_float(recorded, recomputed, path, where)
    else:
        matched = recorded == recomputed
    if matched:
        return []
    return [_metric_mismatch(path, where, recorded, recomputed)]


def _metrics_equal(recorded, recomputed, path, where):
    """Deep-compare a recorded metric block against a recomputed one."""
    if isinstance(recomputed, dict):
        return _metrics_equal_dict(recorded, recomputed, path, where)
    if isinstance(recomputed, list):
        return _metrics_equal_list(recorded, recomputed, path, where)
    return _metrics_equal_scalar(recorded, recomputed, path, where)


def _check_input_fixture(record, where):
    """Both sides must provably have run the same encoded input."""
    errors = []
    scenario = record.get("scenario") or {}
    stimulus = scenario.get("stimulus")
    fixture = scenario.get("input_fixture") or {}
    oracle_fixture = (record.get("oracle") or {}).get("input_fixture") or {}
    identical = (record.get("oracle") or {}).get("identical_input_fixture")
    if not isinstance(stimulus, dict) or not isinstance(stimulus.get("events"), list):
        return [f"{where}: scenario.stimulus.events missing [INPUT_FIXTURE_MISMATCH]"]
    try:
        recomputed = digest(stimulus["events"])
    except (TypeError, ValueError, OverflowError) as exc:
        return [
            f"{where}: scenario.stimulus.events is not canonical finite JSON: {exc} "
            "[INPUT_FIXTURE_MISMATCH]"
        ]
    if fixture.get("sha256") != recomputed:
        errors.append(
            f"{where}: scenario.input_fixture.sha256 does not match the recorded events "
            "[INPUT_FIXTURE_MISMATCH]"
        )
    if not contract.strict_json_equal(oracle_fixture, fixture):
        errors.append(
            f"{where}: oracle.input_fixture must exactly match "
            "scenario.input_fixture; the two sides cannot be shown to have run "
            "the same input "
            "[INPUT_FIXTURE_MISMATCH]"
        )
    if identical is not True:
        errors.append(
            f"{where}: oracle.identical_input_fixture must be exactly true "
            "[INPUT_FIXTURE_MISMATCH]"
        )
    if stimulus.get("steps") != len(stimulus["events"]):
        errors.append(f"{where}: stimulus.steps disagrees with the event grid "
                      "[INPUT_FIXTURE_MISMATCH]")
    return errors


def _materialized_catalog_scenario(scenario, where):
    """Rebuild the catalog scenario a record claims, or say why it cannot be.

    Returns ``(expected, errors)``; ``expected`` is None whenever the claim
    cannot even be bound to a catalog entry.
    """
    scenario_id = scenario.get("id")
    spec = _SCENARIO_SPEC_BY_ID.get(scenario_id)
    if spec is None:
        return None, [
            f"{where}: scenario.id {scenario_id!r} is not in the hardware-parity "
            "catalog [SCENARIO_LABEL_MISMATCH]"
        ]
    stimulus = scenario.get("stimulus")
    steps = stimulus.get("steps") if isinstance(stimulus, dict) else None
    if not isinstance(steps, int) or isinstance(steps, bool) or steps < 1:
        return None, [
            f"{where}: scenario.stimulus.steps must be a positive integer before "
            f"scenario {scenario_id!r} can be bound to the catalog "
            "[SCENARIO_LABEL_MISMATCH]"
        ]
    events = stimulus.get("events") if isinstance(stimulus, dict) else None
    if not isinstance(events, list) or steps != len(events):
        # A record-declared `steps` this far out of line with its own event
        # grid is already invalid; bind it to trusted evidence (the actual
        # event count) before using it as an allocation bound below, rather
        # than letting an untrusted huge integer reach build_scenario().
        return None, [
            f"{where}: scenario.stimulus.steps disagrees with the event grid before "
            f"scenario {scenario_id!r} can be bound to the catalog "
            "[SCENARIO_LABEL_MISMATCH]"
        ]
    try:
        return build_scenario(spec, steps=steps), []
    except (ValueError, TypeError, KeyError, IndexError, OverflowError) as exc:
        return None, [
            f"{where}: catalog scenario {scenario_id!r} cannot be materialized: {exc} "
            "[SCENARIO_LABEL_MISMATCH]"
        ]


def _catalog_prediction_errors(record, expected, scenario_id, where):
    """The generator's prediction and intervention must be the catalog's."""
    errors = []
    prediction = record.get("candidate_prediction")
    expected_prediction = {
        "hypothesis": expected["hypothesis"],
        "expected_verdict": (
            contract.VERDICT_MATCH
            if expected["stress"] == "none"
            else contract.VERDICT_MISMATCH
        ),
    }
    for key, expected_value in expected_prediction.items():
        if not isinstance(prediction, dict) or not contract.strict_json_equal(
            prediction.get(key), expected_value
        ):
            errors.append(
                f"{where}: candidate_prediction.{key} does not match catalog "
                f"scenario {scenario_id!r} [SCENARIO_LABEL_MISMATCH]"
            )
    if not contract.strict_json_equal(record.get("intervention"), expected["intervention"]):
        errors.append(
            f"{where}: intervention does not match catalog scenario {scenario_id!r} "
            "[SCENARIO_LABEL_MISMATCH]"
        )
    return errors


def _check_catalog_scenario(record, where):
    """Bind every prompt- and execution-facing field to the catalog id."""
    scenario = record.get("scenario")
    if not isinstance(scenario, dict):
        return [f"{where}: scenario must be an object [SCENARIO_LABEL_MISMATCH]"]
    expected, errors = _materialized_catalog_scenario(scenario, where)
    if expected is None:
        return errors
    scenario_id = scenario.get("id")
    expected_scenario = {
        key: value
        for key, value in expected.items()
        if key not in ("hypothesis", "intervention")
    }
    for key, expected_value in expected_scenario.items():
        if not contract.strict_json_equal(scenario.get(key), expected_value):
            errors.append(
                f"{where}: scenario.{key} does not match catalog scenario "
                f"{scenario_id!r} [SCENARIO_LABEL_MISMATCH]"
            )
    errors += _catalog_prediction_errors(record, expected, scenario_id, where)
    return errors


def _record_naming_errors(record, where):
    """The id, meta, and generator blocks must name this factory exactly."""
    errors = []
    scenario = record.get("scenario")
    meta = record.get("meta")
    scenario_id = scenario.get("id") if isinstance(scenario, dict) else None
    round_number = meta.get("round") if isinstance(meta, dict) else None
    if isinstance(round_number, int) and not isinstance(round_number, bool):
        expected_id = f"{scenario_id}-r{round_number:02d}"
        if record.get("id") != expected_id:
            errors.append(
                f"{where}: id must be {expected_id!r} for this scenario and round "
                "[ENVELOPE_MALFORMED]"
            )
    if not contract.strict_json_equal(
        meta, {"round": round_number, "factory": FACTORY_SLUG}
    ):
        errors.append(
            f"{where}: meta must exactly identify factory {FACTORY_SLUG!r} and its "
            "round [ENVELOPE_MALFORMED]"
        )
    if not contract.strict_json_equal(record.get("generator"), GENERATOR_BLOCK):
        errors.append(
            f"{where}: generator does not match the hardware scenario catalog "
            "[ENVELOPE_MALFORMED]"
        )
    return errors


def _check_record_identity(record, where):
    """Bind the family, round, producer, and validator identities."""
    oracle = record.get("oracle")
    errors = _record_naming_errors(record, where)
    deployment = oracle.get("deployment") if isinstance(oracle, dict) else None
    deployment_target = (
        deployment.get("execution_target") if isinstance(deployment, dict) else None
    )
    provenance = record.get("provenance")
    expected_provenance_identity = {
        "kind": "hil" if deployment_target in PHYSICAL_TARGETS else "simulated",
        "tool": VALIDATOR,
        "tool_version": SCHEMA_VERSION,
        "contract_version": contract.CONTRACT_VERSION,
        "units": {
            "time": "ms",
            "membrane": "mV_model",
            "weights": "dimensionless",
            "latency": "ms",
        },
    }
    if not isinstance(provenance, dict) or any(
        not contract.strict_json_equal(provenance.get(key), value)
        for key, value in expected_provenance_identity.items()
    ):
        errors.append(
            f"{where}: provenance identity does not match the hardware validator "
            "[ENVELOPE_MALFORMED]"
        )
    expected_validation = {
        "validator": VALIDATOR,
        "validator_version": SCHEMA_VERSION,
        "checks": [
            "envelope_contract",
            "identical_input_fixture",
            "q88_conversion_reproducible",
            "parity_metrics_recomputed_from_traces",
            "verdict_consistent_with_traces",
        ],
        "status": "revalidate_on_read",
    }
    if not contract.strict_json_equal(record.get("validation"), expected_validation):
        errors.append(
            f"{where}: validation block does not match the hardware validator contract "
            "[ENVELOPE_MALFORMED]"
        )
    return errors


def _check_fpga_environment(record, where):
    """Shape-check the recorded FPGA probe; re-probe only live FPGA claims.

    Q8.8 and capture records store the generating-host probe as provenance.
    Requiring that sidecar to equal the current process environment would
    reject intact evidence after ``SPIKENAUT_FPGA_*`` or the bitstream path
    changes. Live ``fpga_hardware`` execution still requires the current
    adapter to be available. Unavailable FPGA diagnostics are authenticated
    by ``_check_unavailable_deployment`` against the selected adapter.
    """
    oracle = record.get("oracle")
    environment = oracle.get("environment") if isinstance(oracle, dict) else None
    if not isinstance(environment, dict):
        return [
            f"{where}: oracle.environment must be an object "
            "[ENVELOPE_MALFORMED]"
        ]
    recorded = environment.get("fpga_hardware")
    if not isinstance(recorded, dict):
        return [
            f"{where}: oracle.environment.fpga_hardware must be an object "
            "[ENVELOPE_MALFORMED]"
        ]
    errors = []
    if not isinstance(recorded.get("available"), bool):
        errors.append(
            f"{where}: oracle.environment.fpga_hardware.available must be a boolean "
            "[ENVELOPE_MALFORMED]"
        )
    if recorded.get("available") is False:
        reason = recorded.get("reason_code")
        if not isinstance(reason, str) or not reason.strip():
            errors.append(
                f"{where}: unavailable fpga_hardware probe must name a reason_code "
                "[ENVELOPE_MALFORMED]"
            )
    current = availability_report().get("spikenaut_fpga")
    current_available = isinstance(current, dict) and current.get("available") is True
    if recorded.get("available") is True and not current_available:
        # FpgaHardwareAdapter.run() always raises regardless of what
        # availability() reports, so no adapter code path in this repository
        # can produce a truthful ``available: true`` probe today. Unlike
        # reason_code/detail (which legitimately drift with the generating
        # host's environment and are intentionally not re-checked above),
        # a bare ``true`` is never intact evidence to preserve.
        errors.append(
            f"{where}: oracle.environment.fpga_hardware.available is true but no "
            "current adapter probe corroborates it [ORACLE_UNAVAILABLE]"
        )
    deployment = oracle.get("deployment")
    if (
        isinstance(deployment, dict)
        and deployment.get("adapter") == FpgaHardwareAdapter.name
        and deployment.get("runtime_class") == FpgaHardwareAdapter.runtime_class
        and not current_available
    ):
        errors.append(
            f"{where}: a live {FpgaHardwareAdapter.name!r} deployment requires the "
            "current adapter probe to report available [ORACLE_UNAVAILABLE]"
        )
    return errors


def _check_quantization(record, where):
    """Re-derive the Q8.8 conversion from the float model and compare."""
    deployment = (record.get("oracle") or {}).get("deployment")
    if not isinstance(deployment, dict):
        return []
    recorded = deployment.get("quantization")
    model = (record.get("scenario") or {}).get("model_float")
    if not recorded:
        return [
            f"{where}: deployment side reports no Q8.8 conversion provenance "
            "[Q88_PROVENANCE_MISSING]"
        ]
    if not isinstance(model, dict):
        return [f"{where}: scenario.model_float missing [Q88_PROVENANCE_MISSING]"]
    for key in ("format", "fractional_bits", "rounding", "saturation_policy"):
        if key not in recorded:
            return [
                f"{where}: quantization provenance missing {key!r} "
                "[Q88_PROVENANCE_MISSING]"
            ]
    if recorded.get("fractional_bits") != 8 or recorded.get("format") != "Q8.8":
        return [
            f"{where}: quantization provenance is not Q8.8 [Q88_PROVENANCE_MISMATCH]"
        ]
    try:
        _, recomputed = quantize_model(model)
    except (
        ValueError,
        TypeError,
        KeyError,
        IndexError,
        AttributeError,
        OverflowError,
    ) as exc:
        return [f"{where}: scenario.model_float is not simulable: {exc}"]
    errors = _metrics_equal(
        recorded,
        recomputed,
        "oracle.deployment.quantization",
        where,
    )
    return [
        error.replace("[PARITY_METRIC_MISMATCH]", "[Q88_PROVENANCE_MISMATCH]")
        for error in errors
    ]


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


def _matrix_cell_valid(cell, binary, integer):
    """Exact-typed cell domains: `bool` never impersonates an int."""
    if binary:
        return type(cell) is int and cell in (0, 1)
    if integer:
        return type(cell) is int
    return type(cell) in (int, float) and (type(cell) is int or math.isfinite(cell))


def _matrix_cell_domain(binary, integer):
    if binary:
        return "an exact integer 0 or 1"
    if integer:
        return "an exact integer"
    return "a finite JSON number"


def _matrix_row_errors(row, row_index, columns, path, where, binary, integer):
    """One row's shape and cell-domain findings."""
    if not isinstance(row, list) or len(row) != columns:
        observed = len(row) if isinstance(row, list) else None
        return [
            f"{where}: {path}[{row_index}] must have exactly {columns} cells, "
            f"got {observed!r} [ENVELOPE_MALFORMED]"
        ]
    return [
        f"{where}: {path}[{row_index}][{column_index}] must be "
        f"{_matrix_cell_domain(binary, integer)}, got {cell!r} "
        "[ENVELOPE_MALFORMED]"
        for column_index, cell in enumerate(row)
        if not _matrix_cell_valid(cell, binary, integer)
    ]


def _matrix_errors(value, rows, columns, path, where, *, binary=False, integer=False):
    if not isinstance(value, list) or len(value) != rows:
        observed = len(value) if isinstance(value, list) else None
        return [
            f"{where}: {path} must have exactly {rows} rows, got {observed!r} "
            "[ENVELOPE_MALFORMED]"
        ]
    errors = []
    for row_index, row in enumerate(value):
        errors += _matrix_row_errors(
            row, row_index, columns, path, where, binary, integer
        )
    return errors


def _q88_raw_correspondence_errors(trace, raw, path, where):
    """Bind float membrane traces to signed Q8.8 integers."""
    errors = []
    for row_index, (trace_row, raw_row) in enumerate(zip(trace, raw)):
        for column_index, (value, raw_value) in enumerate(zip(trace_row, raw_row)):
            cell = f"{path}.trace_q88_raw[{row_index}][{column_index}]"
            if raw_value < Q88_MIN_RAW or raw_value > Q88_MAX_RAW:
                errors.append(
                    f"{where}: {cell} is outside the signed Q8.8 int16 range "
                    f"[{Q88_MIN_RAW}, {Q88_MAX_RAW}] [Q88_PROVENANCE_MISMATCH]"
                )
                continue
            expected = q88_to_float(raw_value)
            if not contract.strict_json_equal(value, expected):
                errors.append(
                    f"{where}: {path}.trace[{row_index}][{column_index}] is not "
                    "raw/256 of the retained Q8.8 integer [Q88_PROVENANCE_MISMATCH]"
                )
    return errors


def _scenario_observation_window(scenario):
    """The `(neurons, labels, steps, dt_ms)` window, or None if unusable."""
    model = scenario.get("model_float") if isinstance(scenario, dict) else None
    stimulus = scenario.get("stimulus") if isinstance(scenario, dict) else None
    if not isinstance(model, dict) or not isinstance(stimulus, dict):
        return None
    neurons = model.get("neurons")
    labels = model.get("action_labels")
    steps = stimulus.get("steps")
    dt_ms = stimulus.get("dt_ms")
    if (
        not isinstance(neurons, int)
        or isinstance(neurons, bool)
        or neurons < 1
        or not isinstance(steps, int)
        or isinstance(steps, bool)
        or steps < 1
        or not isinstance(labels, list)
        or len(labels) != neurons
        or not all(isinstance(label, str) for label in labels)
        or type(dt_ms) not in (int, float)
        or (type(dt_ms) is float and not math.isfinite(dt_ms))
    ):
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


def _observed_membrane_errors(membrane, window, path, where):
    """The membrane trace, and its Q8.8 raw correspondence when retained."""
    neurons, _labels, steps, _dt_ms = window
    if not isinstance(membrane, dict) or type(membrane.get("observable")) is not bool:
        return [
            f"{where}: {path}.membrane must declare an exact boolean observable flag "
            "[ENVELOPE_MALFORMED]"
        ]
    if not membrane["observable"]:
        if membrane.get("trace") is not None:
            return [
                f"{where}: {path}.membrane.trace must be null when membrane state is "
                "not observable [ENVELOPE_MALFORMED]"
            ]
        return []
    trace_errors = _matrix_errors(
        membrane.get("trace"),
        steps,
        neurons,
        f"{path}.membrane.trace",
        where,
    )
    errors = list(trace_errors)
    if "trace_q88_raw" in membrane:
        raw_errors = _matrix_errors(
            membrane.get("trace_q88_raw"),
            steps,
            neurons,
            f"{path}.membrane.trace_q88_raw",
            where,
            integer=True,
        )
        errors += raw_errors
        if not trace_errors and not raw_errors:
            errors += _q88_raw_correspondence_errors(
                membrane.get("trace"),
                membrane.get("trace_q88_raw"),
                f"{path}.membrane",
                where,
            )
    return errors


def _observed_arithmetic_errors(arithmetic, path, where):
    """The Q8.8 saturation attestation carried by one observation."""
    saturation_events = (
        arithmetic.get("saturation_events") if isinstance(arithmetic, dict) else None
    )
    if (
        not isinstance(arithmetic, dict)
        or arithmetic.get("format") != "Q8.8"
        or not isinstance(saturation_events, int)
        or isinstance(saturation_events, bool)
        or saturation_events < 0
    ):
        return [
            f"{where}: {path}.arithmetic must declare Q8.8 and an exact "
            "nonnegative saturation_events integer [ENVELOPE_MALFORMED]"
        ]
    return []


def _physical_observation_errors(observation, scenario, path, where):
    """Validate one retained physical observation against its execution window."""
    if not isinstance(observation, dict):
        return [f"{where}: {path} must be an object [ENVELOPE_MALFORMED]"]
    model = scenario.get("model_float") if isinstance(scenario, dict) else None
    stimulus = scenario.get("stimulus") if isinstance(scenario, dict) else None
    if not isinstance(model, dict) or not isinstance(stimulus, dict):
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


def _repeat_projection(observation):
    """The comparable half of a retained observation, or None if malformed."""
    if not isinstance(observation, dict):
        return None
    return {
        key: observation.get(key)
        for key in ("spikes", "spike_events", "membrane", "action", "arithmetic")
    }


def _capture_repeat_errors(payload, scenario, where):
    """Every retained repeat must be well formed and match its digest."""
    repeat_outputs = payload.get("repeat_outputs")
    repeat_digests = payload.get("repeat_digests")
    if not isinstance(repeat_outputs, list) or not repeat_outputs:
        return [
            f"{where}: capture payload must retain one repeat_outputs entry per "
            "repeat digest [REPEATABILITY_UNPROVEN]"
        ]
    if not isinstance(repeat_digests, list) or len(repeat_outputs) != len(
        repeat_digests
    ):
        return [
            f"{where}: capture repeat_outputs and repeat_digests must have identical "
            "cardinality [REPEATABILITY_UNPROVEN]"
        ]
    errors = []
    for index, (repeat_output, repeat_digest) in enumerate(
        zip(repeat_outputs, repeat_digests)
    ):
        errors += _physical_observation_errors(
            repeat_output,
            scenario,
            f"capture.source.payload.repeat_outputs[{index}]",
            where,
        )
        try:
            expected_digest = run_digest(repeat_output)
        except (KeyError, TypeError, ValueError, AttributeError, OverflowError) as exc:
            errors.append(
                f"{where}: capture repeat output {index} is malformed: {exc} "
                "[REPEATABILITY_UNPROVEN]"
            )
            continue
        if repeat_digest != expected_digest:
            errors.append(
                f"{where}: capture repeat_digests[{index}] is not derived from "
                f"repeat_outputs[{index}] [REPEATABILITY_UNPROVEN]"
            )
    primary_projection = _repeat_projection(payload)
    if not contract.strict_json_equal(
        _repeat_projection(repeat_outputs[0]), primary_projection
    ):
        errors.append(
            f"{where}: capture payload must equal its first retained repeat "
            "observation [REPEATABILITY_UNPROVEN]"
        )
    return errors


def _capture_output_digest_errors(deployment, payload, repeat_digests, where):
    """The deployment's digests must derive from the captured payload."""
    try:
        payload_output_digest = run_digest(payload)
    except (KeyError, TypeError, ValueError, AttributeError, OverflowError) as exc:
        return [f"{where}: capture payload is malformed: {exc} [ENVELOPE_MALFORMED]"]
    errors = []
    if deployment.get("output_digest") != payload_output_digest:
        errors.append(
            f"{where}: deployment output_digest is not derived from the captured "
            "payload [HW_PROVENANCE_MISSING]"
        )
    expected_repeats = list(repeat_digests) if isinstance(repeat_digests, list) else []
    if deployment.get("repeat_digests") != expected_repeats:
        errors.append(
            f"{where}: deployment repeat_digests are not the captured repeats "
            "[REPEATABILITY_UNPROVEN]"
        )
    return errors


def _capture_manifest_binding_errors(capture, manifest, record, where):
    """capture.recorded_at and the input fixture must bind to the manifest."""
    errors = []
    recorded_at = capture.get("recorded_at")
    manifest_recorded_at = manifest.get("recorded_at")
    if (
        not isinstance(recorded_at, str)
        or not recorded_at.strip()
        or recorded_at != manifest_recorded_at
    ):
        errors.append(
            f"{where}: capture.recorded_at is not bound to "
            "capture.source.manifest.recorded_at [HW_PROVENANCE_MISSING]"
        )
    fixture_sha = ((record.get("scenario") or {}).get("input_fixture") or {}).get(
        "sha256"
    )
    if manifest.get("input_fixture_sha256") != fixture_sha:
        errors.append(
            f"{where}: capture manifest names a different input fixture "
            "[INPUT_FIXTURE_MISMATCH]"
        )
    return errors


def _capture_adapter_identity_errors(source, deployment, where):
    """The capture's adapter identity must agree with the deployment's."""
    source_adapter = source.get("adapter")
    source_runtime = source.get("runtime_class")
    deployment_identity = (
        deployment.get("adapter"),
        deployment.get("runtime_class"),
    )
    if deployment_identity == (
        FpgaHardwareAdapter.name,
        FpgaHardwareAdapter.runtime_class,
    ) and (source_adapter, source_runtime) != deployment_identity:
        return [
            f"{where}: live FPGA evidence must bind capture.source.adapter and "
            "capture.source.runtime_class to the live board adapter "
            "[HW_PROVENANCE_MISSING]"
        ]
    if source_adapter is not None or source_runtime is not None:
        if (source_adapter, source_runtime) != deployment_identity:
            return [
                f"{where}: capture source adapter identity disagrees with the "
                "deployment [HW_PROVENANCE_MISSING]"
            ]
    return []


def _capture_identity_errors(source, deployment, payload, where):
    """Execution target, adapter identity, board/bitstream, and quantization."""
    errors = []
    if source.get("execution_target") != deployment.get("execution_target"):
        errors.append(
            f"{where}: capture source execution_target disagrees with the deployment "
            "[HW_TARGET_UNKNOWN]"
        )
    errors += _capture_adapter_identity_errors(source, deployment, where)
    for key in ("hardware", "bitstream"):
        if source.get(key) != deployment.get(key):
            errors.append(
                f"{where}: oracle.deployment.{key} does not match capture.source.{key} "
                "[HW_PROVENANCE_MISSING]"
            )
    source_quantization = source.get("quantization") or payload.get("quantization")
    # Strict JSON typing: an ordinary `!=` treats False as 0, letting a
    # capture source violate the documented quantization types while still
    # binding to the deployment.
    if not contract.strict_json_equal(source_quantization, deployment.get("quantization")):
        errors.append(
            f"{where}: deployment quantization is not the conversion stored with the "
            "capture [Q88_PROVENANCE_MISMATCH]"
        )
    return errors


def _capture_projection_errors(deployment, payload, where):
    """Each observation on the deployment must be the one stored in the payload."""
    normalized_payload = {
        "spikes": payload.get("spikes"),
        "spike_events": payload.get("spike_events"),
        "membrane": payload.get(
            "membrane", {"observable": False, "units": "mV_model", "trace": None}
        ),
        "action": payload.get("action"),
        "arithmetic": payload.get("arithmetic"),
        "latency": payload.get("latency"),
    }
    errors = []
    for key, expected in normalized_payload.items():
        # Strict JSON typing: `True == 1` under an ordinary comparison, so a
        # payload observation could violate its documented shape (for example
        # latency.measured as an integer) while still projecting onto the
        # deployment.
        if not contract.strict_json_equal(deployment.get(key), expected):
            errors.append(
                f"{where}: oracle.deployment.{key} is not the observation stored in "
                "capture.source.payload [HW_PROVENANCE_MISSING]"
            )
    return errors


def _check_capture_chain(record, deployment, where):
    """Bind a physical claim to the replay source stored by the adapter.

    This verifies the record-level digest chain and catches a reference-model
    record relabelled as hardware.  It deliberately does not claim to prove
    that the source file came from a real board; that still requires the
    out-of-band attestation documented in ``docs/parity-oracles.md``.
    """
    errors = []
    capture = deployment.get("capture")
    if not isinstance(capture, dict):
        return [
            f"{where}: a physical target needs a capture object with replay source "
            "bytes [HW_PROVENANCE_MISSING]"
        ]
    source = capture.get("source")
    if not isinstance(source, dict):
        return [
            f"{where}: oracle.deployment.capture.source is required to re-check the "
            "capture digest chain [HW_PROVENANCE_MISSING]"
        ]
    try:
        source_sha = digest(source)
    except (TypeError, ValueError, OverflowError) as exc:
        return [f"{where}: capture source is not canonical JSON: {exc}"]
    if capture.get("source_sha256") != source_sha:
        errors.append(
            f"{where}: capture.source_sha256 does not identify capture.source "
            "[HW_PROVENANCE_MISSING]"
        )

    manifest = source.get("manifest")
    payload = source.get("payload")
    if not isinstance(manifest, dict) or not isinstance(payload, dict):
        return errors + [
            f"{where}: capture.source must contain object-valued manifest and payload "
            "[HW_PROVENANCE_MISSING]"
        ]
    try:
        manifest_sha = digest(manifest)
        payload_sha = digest(payload)
    except (TypeError, ValueError, OverflowError) as exc:
        return errors + [
            f"{where}: capture manifest or payload is not canonical finite JSON: "
            f"{exc} [ENVELOPE_MALFORMED]"
        ]
    if capture.get("manifest_sha256") != manifest_sha:
        errors.append(
            f"{where}: capture.manifest_sha256 does not identify the stored manifest "
            "[HW_PROVENANCE_MISSING]"
        )
    if (
        capture.get("payload_sha256") != payload_sha
        or manifest.get("payload_sha256") != payload_sha
    ):
        errors.append(
            f"{where}: capture payload digest is not bound to the stored manifest "
            "[HW_PROVENANCE_MISSING]"
        )
    errors += _capture_manifest_binding_errors(capture, manifest, record, where)
    scenario = record.get("scenario")
    errors += _physical_observation_errors(
        payload, scenario, "capture.source.payload", where
    )
    errors += _capture_identity_errors(source, deployment, payload, where)
    errors += _capture_projection_errors(deployment, payload, where)
    repeat_digests = payload.get("repeat_digests")
    errors += _capture_repeat_errors(payload, scenario, where)
    errors += _capture_output_digest_errors(deployment, payload, repeat_digests, where)
    return errors


def _replayed_adapter_probe(record, oracle, requested, where):
    """Re-derive the selected adapter's current diagnostic.

    Returns ``(current, fatal)``: the probe result to authenticate against,
    or a fatal error list when the diagnostic cannot be replayed at all.
    """
    adapter_name = requested.get("adapter")
    if adapter_name != RecordedCaptureAdapter.name:
        return availability_report().get(adapter_name), []
    config = requested.get("adapter_config")
    capture_path = config.get("capture_path") if isinstance(config, dict) else None
    if not isinstance(capture_path, str) or not capture_path:
        return None, [
            f"{where}: recorded_capture unavailability must retain its capture "
            "path [ORACLE_UNAVAILABLE]"
        ]
    adapter = RecordedCaptureAdapter(capture_path)
    scenario = record.get("scenario") or {}
    software = oracle.get("software") or {}
    try:
        adapter.run(
            scenario.get("model_float"),
            scenario.get("stimulus"),
            repeats=software.get("repeats", 1),
        )
    except OracleUnavailable as exc:
        return {
            "available": False,
            "execution_target": adapter.execution_target,
            "reason_code": exc.reason_code,
            "detail": exc.detail,
        }, []
    except (
        ValueError,
        TypeError,
        KeyError,
        IndexError,
        AttributeError,
        OverflowError,
    ) as exc:
        return None, [
            f"{where}: recorded_capture diagnostic is not reproducible: {exc} "
            "[ORACLE_UNAVAILABLE]"
        ]
    return {
        "available": True,
        "execution_target": adapter.execution_target,
        "reason_code": None,
        "detail": "capture executes for the recorded scenario",
    }, []


def _check_unavailable_deployment(record, where):
    """Authenticate the diagnostic used in place of a deployment run."""
    oracle = record.get("oracle") or {}
    unavailable = oracle.get("unavailable")
    if not isinstance(unavailable, list) or len(unavailable) != 1:
        return [
            f"{where}: oracle.unavailable must contain exactly one deployment "
            "diagnostic [ORACLE_UNAVAILABLE]"
        ]
    entry = unavailable[0]
    if not isinstance(entry, dict):
        return [
            f"{where}: oracle.unavailable[0] must be an object [ORACLE_UNAVAILABLE]"
        ]

    requested = oracle.get("requested_deployment")
    if not isinstance(requested, dict):
        return [
            f"{where}: oracle.requested_deployment must bind the selected adapter "
            "[ORACLE_UNAVAILABLE]"
        ]
    errors = []
    for key in ("adapter", "execution_target", "adapter_config"):
        if entry.get(key) != requested.get(key):
            errors.append(
                f"{where}: oracle.unavailable[0].{key} does not match the selected "
                f"adapter recorded in oracle.requested_deployment [ORACLE_UNAVAILABLE]"
            )

    adapter_name = requested.get("adapter")
    current, fatal = _replayed_adapter_probe(record, oracle, requested, where)
    if fatal:
        return fatal
    if not isinstance(current, dict) or current.get("available") is not False:
        return [
            f"{where}: unavailable deployment names adapter {adapter_name!r}, which "
            "does not currently report unavailable [ORACLE_UNAVAILABLE]"
        ]
    for key in ("execution_target", "reason_code", "detail"):
        if entry.get(key) != current.get(key):
            errors.append(
                f"{where}: oracle.unavailable[0].{key} is {entry.get(key)!r}, but "
                f"adapter {adapter_name!r} reports {current.get(key)!r} "
                "[ORACLE_UNAVAILABLE]"
            )
    expected_entry = {
        key: copy.deepcopy(requested[key])
        for key in ("adapter", "execution_target", "adapter_config")
        if key in requested
    }
    expected_entry.update(
        {
            "reason_code": current.get("reason_code"),
            "detail": current.get("detail"),
        }
    )
    if not contract.strict_json_equal(entry, expected_entry):
        errors.append(
            f"{where}: oracle.unavailable[0] must exactly match the current "
            "selected-adapter diagnostic [ORACLE_UNAVAILABLE]"
        )
    return errors


def _is_canonical_sha256(value):
    """True only for the canonical lowercase ``sha256:<64hex>`` spelling."""
    return (
        isinstance(value, str)
        and len(value) == 71
        and value.startswith("sha256:")
        and all(character in "0123456789abcdef" for character in value[7:])
    )


def _reference_latency_claim_errors(deployment, target, where):
    """A non-physical target must not report measured hardware latency."""
    latency = deployment.get("latency")
    if target == TARGET_FIXED_POINT_MODEL and (
        not isinstance(latency, dict)
        or latency.get("measured") is not False
        or latency.get("value_ms") is not None
        or latency.get("reason_code") != "LATENCY_NOT_MEASURED_REFERENCE_MODEL"
    ):
        return [
            f"{where}: the fixed-point reference model cannot report measured "
            "hardware latency [LATENCY_NOT_MEASURED]"
        ]
    return []


def _physical_adapter_identity_errors(deployment, target, where):
    """Only the adapters that can substantiate the target may be named."""
    adapter_identity = (
        deployment.get("adapter"),
        deployment.get("runtime_class"),
    )
    allowed_identities = {
        (RecordedCaptureAdapter.name, RecordedCaptureAdapter.runtime_class)
    }
    if target == TARGET_FPGA_HARDWARE:
        allowed_identities.add(
            (FpgaHardwareAdapter.name, FpgaHardwareAdapter.runtime_class)
        )
    if adapter_identity not in allowed_identities:
        return [
            f"{where}: retained physical evidence uses unsupported adapter identity "
            f"{adapter_identity!r}; allowed for target {target!r}: "
            f"{sorted(allowed_identities)!r} "
            "[HW_PROVENANCE_MISSING]"
        ]
    return []


def _physical_provenance_field_errors(deployment, target, where):
    """Board, bitstream, latency, and repeat-count evidence for the claim."""
    errors = []
    for section, key in REQUIRED_HARDWARE_FIELDS:
        block = deployment.get(section)
        value = block.get(key) if isinstance(block, dict) else None
        if not isinstance(value, str) or not value.strip():
            errors.append(
                f"{where}: {target} claim needs oracle.deployment.{section}.{key} "
                "[HW_PROVENANCE_MISSING]"
            )
    bitstream = deployment.get("bitstream")
    bitstream_sha256 = bitstream.get("sha256") if isinstance(bitstream, dict) else None
    if bitstream_sha256 and not _is_canonical_sha256(bitstream_sha256):
        errors.append(
            f"{where}: {target} claim needs canonical lowercase "
            "oracle.deployment.bitstream.sha256 in sha256:<64hex> form "
            "[HW_PROVENANCE_MISSING]"
        )
    latency = deployment.get("latency") or {}
    value_ms = latency.get("value_ms")
    if (
        latency.get("measured") is not True
        or not isinstance(value_ms, (int, float))
        or isinstance(value_ms, bool)
        or not math.isfinite(value_ms)
        or value_ms < 0
    ):
        errors.append(
            f"{where}: {target} claim needs a measured latency in ms "
            "[HW_PROVENANCE_MISSING]"
        )
    repeats = deployment.get("repeats")
    if not isinstance(repeats, int) or isinstance(repeats, bool) or repeats < 2:
        errors.append(
            f"{where}: {target} claim needs at least 2 repeated runs to say anything "
            "about determinism [REPEATABILITY_UNPROVEN]"
        )
    return errors


def _check_physical_claim(record, where):
    """A physical-target record needs board, bitstream, and capture metadata."""
    deployment = (record.get("oracle") or {}).get("deployment")
    if not isinstance(deployment, dict):
        return []
    target = deployment.get("execution_target")
    # A missing target is treated as unknown rather than waved through: it is
    # exactly what deleting an inconvenient label would look like.
    if target not in (TARGET_FIXED_POINT_MODEL, *PHYSICAL_TARGETS):
        return [
            f"{where}: unknown deployment execution_target {target!r} [HW_TARGET_UNKNOWN]"
        ]
    if target not in PHYSICAL_TARGETS:
        return _reference_latency_claim_errors(deployment, target, where)
    errors = _physical_adapter_identity_errors(deployment, target, where)
    errors += _physical_provenance_field_errors(deployment, target, where)
    # A run on physical silicon is hardware-in-the-loop by definition. A record
    # that claims a board while still declaring itself `simulated` is not
    # describing one execution consistently, and the mismatch is exactly what a
    # relabelled reference-model run looks like.
    kind = (record.get("provenance") or {}).get("kind")
    if kind != "hil":
        errors.append(
            f"{where}: a {target} claim requires provenance.kind 'hil', got {kind!r} "
            "[HW_PROVENANCE_MISSING]"
        )
    errors += _physical_observation_errors(
        deployment, record.get("scenario"), "oracle.deployment", where
    )
    errors += _check_capture_chain(record, deployment, where)
    return errors


def _compare_side(recorded, fresh, label, where):
    """Compare one recorded oracle run against a fresh re-simulation."""
    errors = []
    for key in (
        "spikes",
        "spike_events",
        "action",
        "membrane",
        "arithmetic",
        "latency",
    ):
        section_errors = _metrics_equal(
            recorded.get(key), fresh[key], f"oracle.{label}.{key}", where
        )
        if section_errors:
            reason_code = (
                "MEMBRANE_DIVERGENCE"
                if key == "membrane"
                else "PARITY_METRIC_MISMATCH"
            )
            errors.append(
                f"{where}: oracle.{label}.{key} does not match a re-simulation "
                f"[{reason_code}]"
            )
        if key == "membrane":
            section_errors = [
                error.replace("[PARITY_METRIC_MISMATCH]", "[MEMBRANE_DIVERGENCE]")
                for error in section_errors
            ]
        errors += section_errors
    expected = run_digest(fresh)
    if recorded.get("output_digest") != expected:
        errors.append(
            f"{where}: oracle.{label}.output_digest is not the digest of a "
            "re-simulation [PARITY_METRIC_MISMATCH]"
        )
    return errors


def _check_reference_identity(run, adapter_type, label, where):
    """Bind a reference result to the exact in-repo adapter that produced it."""
    errors = []
    expected = {
        "adapter": adapter_type.name,
        "execution_target": adapter_type.execution_target,
        "runtime_class": adapter_type.runtime_class,
    }
    for key, value in expected.items():
        if run.get(key) != value:
            reason_code = (
                "HW_TARGET_UNKNOWN"
                if key == "execution_target"
                else "HW_PROVENANCE_MISSING"
            )
            errors.append(
                f"{where}: oracle.{label}.{key} must be {value!r}, got "
                f"{run.get(key)!r} [{reason_code}]"
            )
    return errors


def _reexecute_reference_sides(record, where):
    """Re-run every in-repo simulator and compare against what was recorded.

    This is the anti-fabrication gate for this family. Recomputing the parity
    metrics from the record's own traces is not enough on its own: copying one
    side's traces onto the other would then produce a self-consistent record
    asserting a match that never happened. Both in-repo simulators are
    deterministic, so the traces themselves are re-derivable and are re-derived.

    A physical deployment target cannot be re-simulated -- that is the whole
    point of running on hardware -- so for those the software leg is re-derived
    and the deployment leg rests on the capture digest chain and the board
    provenance that :func:`_check_physical_claim` demands. The record says
    which of the two it is, and never implies more.
    """
    errors = []
    scenario = record.get("scenario") or {}
    model = scenario.get("model_float")
    stimulus = scenario.get("stimulus")
    if not isinstance(model, dict) or not isinstance(stimulus, dict):
        return [
            f"{where}: scenario.model_float and scenario.stimulus are required to "
            "re-derive the recorded runs [ENVELOPE_MALFORMED]"
        ]
    oracle = record.get("oracle") or {}

    software = oracle.get("software")
    if isinstance(software, dict):
        errors += _check_reference_identity(
            software, SoftwareFloatAdapter, "software", where
        )
        try:
            fresh = SoftwareFloatAdapter().run(model, stimulus, repeats=1)
        except (
            ValueError,
            KeyError,
            TypeError,
            IndexError,
            AttributeError,
            OverflowError,
        ) as exc:
            return errors + [
                f"{where}: the recorded model and stimulus are not simulable: {exc}"
            ]
        errors += _compare_side(software, fresh, "software", where)

    deployment = oracle.get("deployment")
    if isinstance(deployment, dict):
        if deployment.get("execution_target") == TARGET_FIXED_POINT_MODEL:
            errors += _check_reference_identity(
                deployment, FixedPointReferenceAdapter, "deployment", where
            )
            try:
                fresh = FixedPointReferenceAdapter().run(
                    model, stimulus, repeats=1
                )
            except (
                ValueError,
                KeyError,
                TypeError,
                IndexError,
                AttributeError,
                OverflowError,
            ) as exc:
                return errors + [
                    f"{where}: the recorded model is not quantizable/simulable: {exc}"
                ]
            errors += _compare_side(deployment, fresh, "deployment", where)
    return errors


def _check_determinism(
    run, label, where, require_rederived_repeats=False, expected_meaning=None
):
    """Cross-check a declared determinism block against its own repeat digests.

    ``determinism`` is a claim; ``repeat_digests`` is the evidence for it.
    Without this, a record could assert perfect repeatability over digests
    that plainly disagree. When ``expected_meaning`` is given, the recorded
    ``determinism.meaning`` text must match it exactly, so a side that can
    only ever be a reference adapter (the software side is never a physical
    capture) cannot claim its bit-determinism is instead measured hardware
    variability.
    """
    errors, digests = _repeat_digest_evidence_errors(
        run, label, where, require_rederived_repeats
    )
    if digests is None:
        return errors
    determinism = run.get("determinism")
    if not isinstance(determinism, dict):
        return errors + [
            f"{where}: oracle.{label}.determinism must be an object "
            "[REPEATABILITY_UNPROVEN]"
        ]
    errors += _determinism_claim_errors(
        determinism, digests, label, where, expected_meaning
    )
    return errors


def _repeat_digest_evidence_errors(run, label, where, require_rederived_repeats):
    """The repeat-digest evidence itself: shape, count, and re-derivation.

    Returns ``(errors, digests)``; ``digests`` is None when the evidence is
    too malformed for any determinism claim to be graded against it.
    """
    digests = run.get("repeat_digests")
    if not isinstance(digests, list) or not digests:
        return [
            f"{where}: oracle.{label}.repeat_digests must list one digest per repeat "
            "[REPEATABILITY_UNPROVEN]"
        ], None
    malformed = [
        (index, value)
        for index, value in enumerate(digests)
        if not _is_canonical_sha256(value)
    ]
    if malformed:
        return [
            f"{where}: oracle.{label}.repeat_digests[{index}] must be a canonical "
            f"lowercase sha256:<64hex> string, got {value!r} "
            "[REPEATABILITY_UNPROVEN]"
            for index, value in malformed
        ], None
    errors = []
    repeats = run.get("repeats")
    valid_repeats = (
        isinstance(repeats, int) and not isinstance(repeats, bool) and repeats >= 1
    )
    if not valid_repeats or repeats != len(digests):
        errors.append(
            f"{where}: oracle.{label}.repeats is {repeats!r} but {len(digests)} repeat "
            "digests were recorded [REPEATABILITY_UNPROVEN]"
        )
    if run.get("output_digest") not in digests:
        errors.append(
            f"{where}: oracle.{label}.output_digest is absent from its own "
            "repeat_digests [REPEATABILITY_UNPROVEN]"
        )
    if require_rederived_repeats and valid_repeats and repeats == len(digests):
        # The `repeats == len(digests)` guard binds the multiplication bound
        # to the trusted evidence (the actual digest list length) already
        # checked above, rather than an untrusted `repeats` integer that
        # could otherwise reach this allocation on its own when it disagrees.
        expected = [run.get("output_digest")] * repeats
        if digests != expected:
            errors.append(
                f"{where}: deterministic oracle.{label}.repeat_digests must repeat "
                "the re-derived output_digest exactly [REPEATABILITY_UNPROVEN]"
            )
    return errors, digests


def _determinism_claim_errors(determinism, digests, label, where, expected_meaning):
    """Grade the declared determinism block against its digest evidence."""
    errors = []
    distinct = len(set(digests))
    recorded_distinct = determinism.get("distinct_digests")
    # `bool` is an `int` subclass, so `True == 1`: an ordinary comparison
    # would accept a Boolean where the documented evidence shape is an exact
    # integer count.
    if (
        not isinstance(recorded_distinct, int)
        or isinstance(recorded_distinct, bool)
        or recorded_distinct != distinct
    ):
        errors.append(
            f"{where}: oracle.{label}.determinism.distinct_digests claims "
            f"{recorded_distinct!r} but the repeat digests contain "
            f"{distinct} [REPEATABILITY_UNPROVEN]"
        )
    if determinism.get("identical_repeats") is not (distinct == 1):
        errors.append(
            f"{where}: oracle.{label}.determinism.identical_repeats disagrees with its "
            "own repeat digests [REPEATABILITY_UNPROVEN]"
        )
    if expected_meaning is not None and determinism.get("meaning") != expected_meaning:
        errors.append(
            f"{where}: oracle.{label}.determinism.meaning does not match its "
            "adapter-owned canonical text [REPEATABILITY_UNPROVEN]"
        )
    return errors


def _record_oracle_digests(oracle):
    """The ordered evidence lineage this record's oracle output supports."""
    digests = [
        side["output_digest"]
        for side in (oracle.get("software"), oracle.get("deployment"))
        if isinstance(side, dict) and side.get("output_digest")
    ]
    if oracle.get("deployment") is None:
        unavailable = oracle.get("unavailable")
        if isinstance(unavailable, list) and len(unavailable) == 1:
            try:
                digests.append(_unavailable_evidence_digest(unavailable[0]))
            except (TypeError, ValueError, OverflowError):
                pass
    else:
        try:
            capture_digest = _capture_evidence_digest(oracle.get("deployment"))
        except (TypeError, ValueError, OverflowError):
            capture_digest = None
        if capture_digest is not None:
            digests.append(capture_digest)
    return digests


def _scenario_binding_errors(record, oracle, scenario, where):
    """provenance.scenario_sha256 must identify the recorded model+stimulus."""
    scenario_evidence = {
        "model": scenario.get("model_float"),
        "stimulus": scenario.get("stimulus"),
    }
    if oracle.get("deployment") is None:
        scenario_evidence["requested_deployment"] = oracle.get(
            "requested_deployment"
        )
    try:
        expected_scenario_digest = digest(scenario_evidence)
    except (TypeError, ValueError, OverflowError) as exc:
        return [
            f"{where}: scenario is not canonical JSON: {exc} [ENVELOPE_MALFORMED]"
        ]
    provenance = record.get("provenance")
    if (
        not isinstance(provenance, dict)
        or provenance.get("scenario_sha256") != expected_scenario_digest
    ):
        return [
            f"{where}: provenance.scenario_sha256 does not identify the recorded "
            "model and stimulus [ENVELOPE_MALFORMED]"
        ]
    return []


def _unpaired_result_errors(record, software, result, where):
    """The result contract for a record whose deployment oracle never ran."""
    if not isinstance(software, dict):
        return [f"{where}: oracle.software missing [ENVELOPE_MALFORMED]"]
    errors = _reexecute_reference_sides(record, where)
    errors += _check_determinism(
        software,
        "software",
        where,
        require_rederived_repeats=True,
        expected_meaning=REFERENCE_DETERMINISM_MEANING,
    )
    if result.get("verdict") != contract.VERDICT_INCONCLUSIVE:
        errors.append(
            f"{where}: no deployment-side run, so the verdict must be "
            f"{contract.VERDICT_INCONCLUSIVE!r} [PARITY_VERDICT_INCONSISTENT]"
        )
    if result.get("parity") is not None:
        errors.append(
            f"{where}: parity metrics present without a deployment-side run "
            "[GENERATOR_SUBSTITUTED_FOR_ORACLE]"
        )
    if result.get("reason_codes") != ["ORACLE_UNAVAILABLE"]:
        errors.append(
            f"{where}: an unpaired record must carry exactly ORACLE_UNAVAILABLE "
            "[ORACLE_UNAVAILABLE]"
        )
    errors += _check_unavailable_deployment(record, where)
    expected_summary = _expected_summary(record)
    if result.get("summary") != expected_summary:
        errors.append(
            f"{where}: result.summary is not derived from the unavailable-oracle "
            "evidence [PARITY_METRIC_MISMATCH]"
        )
    return errors


def _recorded_parity_errors(result, parity, verdict, reason_codes, where):
    """The recorded result must reproduce the freshly recomputed parity."""
    errors = []
    recorded_parity = result.get("parity")
    if not isinstance(recorded_parity, dict):
        errors.append(f"{where}: result.parity must be an object [PARITY_METRIC_MISMATCH]")
    else:
        for section in (
            "spike_bitmap",
            "action",
            "timing",
            "membrane",
            "quantization",
            "repeatability",
            "verdict_rule",
        ):
            errors += _metrics_equal(
                recorded_parity.get(section), parity[section], f"result.parity.{section}",
                where,
            )
    if result.get("verdict") != verdict:
        errors.append(
            f"{where}: result.verdict is {result.get('verdict')!r} but the recorded "
            f"traces support {verdict!r} [PARITY_VERDICT_INCONSISTENT]"
        )
    recorded_codes = result.get("reason_codes")
    if recorded_codes != reason_codes:
        errors.append(
            f"{where}: result.reason_codes records {recorded_codes!r} but re-deriving "
            f"gives {reason_codes!r} [PARITY_VERDICT_INCONSISTENT]"
        )
    return errors


def _paired_result_errors(record, oracle, software, deployment, result, where):
    """The result contract for a record with both oracle legs executed."""
    errors = []
    # A paired record has no unavailable oracle to diagnose; anything but an
    # empty list is either a fabricated diagnostic contradicting the completed
    # deployment or a shape violation consumers cannot rely on.
    if oracle.get("unavailable") != []:
        errors.append(
            f"{where}: a paired record must carry exactly an empty "
            "oracle.unavailable list [ENVELOPE_MALFORMED]"
        )
    errors += _check_quantization(record, where)
    errors += _reexecute_reference_sides(record, where)
    errors += _check_determinism(
        software,
        "software",
        where,
        require_rederived_repeats=True,
        expected_meaning=REFERENCE_DETERMINISM_MEANING,
    )
    # The deployment side binds to its adapter-owned meaning just like both
    # reference sides: a fixed-point reference deployment must describe
    # bit-determinism, and a capture-backed one must describe the measured
    # variability of its recorded runs. Without the bind, a deterministic
    # simulator could relabel its repeats as measured hardware variability
    # and mirror that text into result.parity.repeatability unchallenged.
    # An unknown target is already [HW_TARGET_UNKNOWN]; grading it against
    # the capture text keeps the claim checked rather than skipped.
    errors += _check_determinism(
        deployment,
        "deployment",
        where,
        require_rederived_repeats=(
            deployment.get("execution_target") == TARGET_FIXED_POINT_MODEL
        ),
        expected_meaning=(
            REFERENCE_DETERMINISM_MEANING
            if deployment.get("execution_target") == TARGET_FIXED_POINT_MODEL
            else CAPTURE_DETERMINISM_MEANING
        ),
    )

    scenario = record.get("scenario") or {}
    try:
        parity, verdict, reason_codes = compute_parity(scenario, software, deployment)
    except (
        KeyError,
        TypeError,
        ValueError,
        IndexError,
        AttributeError,
        OverflowError,
    ) as exc:
        return errors + [f"{where}: parity metrics are not recomputable: {exc}"]

    errors += _recorded_parity_errors(result, parity, verdict, reason_codes, where)
    expected_summary = _expected_summary(record)
    if result.get("summary") != expected_summary:
        errors.append(
            f"{where}: result.summary is not derived from the validated parity evidence "
            "[PARITY_METRIC_MISMATCH]"
        )
    return errors


def _validate_record(record, where):
    """Full validation of one hardware-parity record."""
    oracle = record.get("oracle") if isinstance(record, dict) else None
    digests = _record_oracle_digests(oracle) if isinstance(oracle, dict) else None
    errors = contract.check_envelope(record, where, oracle_digests=digests)
    if not isinstance(record, dict) or record.get("record_kind") != RECORD_KIND:
        return errors
    # A truthy non-dict `oracle` would sail past every `(x or {}).get(...)`
    # below and raise deep inside a metric function, so stop it here.
    if not isinstance(oracle, dict):
        return errors + [f"{where}: oracle must be an object [ENVELOPE_MALFORMED]"]
    # Execution-facing oracle metadata is validated, not trusted: free text
    # here could advertise a pairing the checked adapter legs never ran.
    if oracle.get("pairing") != ORACLE_PAIRING:
        errors.append(
            f"{where}: oracle.pairing must be the canonical {ORACLE_PAIRING!r} "
            "[ENVELOPE_MALFORMED]"
        )
    scenario = record.get("scenario")
    if not isinstance(scenario, dict):
        return errors
    errors += _scenario_binding_errors(record, oracle, scenario, where)
    errors += _check_input_fixture(record, where)
    errors += _check_catalog_scenario(record, where)
    errors += _check_record_identity(record, where)
    errors += _check_fpga_environment(record, where)
    errors += _check_physical_claim(record, where)

    result = record.get("result")
    if not isinstance(result, dict):
        return errors
    software = oracle.get("software")
    deployment = oracle.get("deployment")

    if deployment is None:
        return errors + _unpaired_result_errors(record, software, result, where)
    if not isinstance(software, dict):
        errors.append(f"{where}: oracle.software missing [ENVELOPE_MALFORMED]")
        return errors
    if not isinstance(deployment, dict):
        return errors + [
            f"{where}: oracle.deployment must be an object or absent [ENVELOPE_MALFORMED]"
        ]
    return errors + _paired_result_errors(
        record, oracle, software, deployment, result, where
    )


def validate_record(record, where):
    """Validate one record without allowing hostile nesting to abort a scan."""
    try:
        return _validate_record(record, where)
    except VALIDATION_DATA_ERRORS as exc:
        return [
            f"{where}: record contains malformed evidence: "
            f"{exc} [ENVELOPE_MALFORMED]"
        ]


def validate_records(records, source="record"):
    errors = []
    for index, record in enumerate(records, 1):
        errors += validate_record(record, f"{source}:{index}")
    return errors


# ── Training view ─────────────────────────────────────────────────────


def training_view(record):
    """A supervised view that carries the parity verdict on its face."""
    scenario = record.get("scenario") or {}
    oracle = record.get("oracle") or {}
    targets = [
        side.get("execution_target")
        for side in (oracle.get("software"), oracle.get("deployment"))
        if isinstance(side, dict)
    ]
    deployment = oracle.get("deployment")
    fixture_sha = (scenario.get("input_fixture") or {}).get("sha256")
    if isinstance(deployment, dict):
        prompt = (
            f"A Spikenaut network ({scenario.get('name')}) is exported to Q8.8 and "
            f"executed on the deployment target under stress {scenario.get('stress')!r}. "
            f"Identical encoded input fixture {fixture_sha}. Does the behaviour survive "
            "the export?"
        )
    else:
        requested = (oracle.get("requested_deployment") or {}).get("adapter")
        prompt = (
            f"A Spikenaut network ({scenario.get('name')}) executed only on the software "
            f"reference under stress {scenario.get('stress')!r}, using encoded input "
            f"fixture {fixture_sha}. Requested deployment adapter {requested!r} did not "
            "execute. Is paired deployment parity established?"
        )
    completion = _expected_summary(record)
    view = contract.build_training_view(record, prompt, completion, targets)
    view["stress"] = scenario.get("stress")
    view["scenario_id"] = scenario.get("id")
    return view


def training_view_errors(record, view, where):
    """Authenticate the complete hardware-parity training projection."""
    errors = contract.training_view_errors(record, view, where)
    try:
        expected = training_view(record)
    except VALIDATION_DATA_ERRORS as exc:
        return errors + [
            f"{where}: cannot rederive the hardware training view: {exc} "
            "[TRAINING_VIEW_HIDES_FAILURE]"
        ]
    if not contract.strict_json_equal(view, expected):
        errors.append(
            f"{where}: training view must exactly match the validator-derived "
            "hardware projection [TRAINING_VIEW_HIDES_FAILURE]"
        )
    return errors


def build_training_views(records, source="record"):
    """Build views for every record and prove none of them softened a failure."""
    validation_errors = validate_records(records, source=source)
    if validation_errors:
        return [], validation_errors
    # Authenticate the batch against the fixed scenario catalog before
    # projecting it: a pre-filtered input would otherwise pass every view/set
    # check against its own subset while silently dropping the failures the
    # round produced. Runs after per-record validation, which bound each
    # scenario id and round to its own evidence.
    errors = contract.catalog_batch_errors(
        records, [spec["id"] for spec in SCENARIO_SPECS], source
    )
    views = [training_view(record) for record in records]
    for index, (record, view) in enumerate(zip(records, views), 1):
        errors += training_view_errors(record, view, f"{source}:{index}")
    errors += contract.view_set_errors(records, views, source)
    return views, errors


# ── CLI ───────────────────────────────────────────────────────────────


def read_jsonl(path):
    records = []
    errors = []
    source = Path(path)
    try:
        text = source.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return [], [f"{source}: cannot read file: {exc}"]
    for lineno, raw_line in enumerate(text.split("\n"), 1):
        line = raw_line[:-1] if raw_line.endswith("\r") else raw_line
        if not line.strip():
            continue
        try:
            records.append(
                json.loads(
                    line,
                    parse_constant=contract.reject_json_constant,
                    parse_float=contract.reject_nonfinite_float,
                )
            )
        # RecursionError: a syntactically valid but absurdly nested line must
        # be a line-level parse error, not a traceback that aborts the scan.
        except (json.JSONDecodeError, ValueError, RecursionError) as exc:
            errors.append(f"{Path(path).name}:{lineno}: JSON parse error: {exc}")
    return records, errors


def write_jsonl(path, records):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "".join(json.dumps(record, sort_keys=True) + "\n" for record in records)
    with path.open("x", encoding="utf-8") as handle:
        handle.write(payload)


def _load_deployment_adapter(target, capture):
    if capture:
        return RecordedCaptureAdapter(capture)
    if target is None or target == FixedPointReferenceAdapter.name:
        return FixedPointReferenceAdapter()
    if target == RecordedCaptureAdapter.name:
        raise KeyError(f"target {target!r} requires --capture PATH")
    return get_adapter(target)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("availability", help="report which oracles can execute here")
    gen = sub.add_parser("generate", help="write one round of paired records")
    gen.add_argument("out_dir")
    gen.add_argument("--round", type=int, default=1)
    gen.add_argument("--steps", type=int, default=12)
    gen.add_argument("--repeats", type=int, default=3)
    gen.add_argument("--target", default=None, help="deployment-side adapter name")
    gen.add_argument("--capture", default=None, help="recorded hardware capture JSON")
    val = sub.add_parser("validate", help="validate a JSONL file of records")
    val.add_argument("path")
    view = sub.add_parser("training-view", help="emit training views for a JSONL file")
    view.add_argument("path")
    return parser.parse_args(argv)


def _cmd_generate(args):
    """Write one validated round, refusing bad arguments and overwrites."""
    if args.steps < 1:
        print(
            f"hardware_parity: --steps must be a positive integer, got {args.steps}",
            file=sys.stderr,
        )
        return 2
    out = Path(args.out_dir) / FACTORY_SLUG / f"batch-r{args.round:02d}.jsonl"
    raw_error = contract.raw_tree_destination_error(out)
    if raw_error:
        print(f"hardware_parity: {raw_error}", file=sys.stderr)
        return 2
    if out.exists():
        print(
            f"hardware_parity: refusing to overwrite existing round {out}",
            file=sys.stderr,
        )
        return 2
    try:
        adapter = _load_deployment_adapter(args.target, args.capture)
    except (KeyError, TypeError) as exc:
        print(f"hardware_parity: {exc}", file=sys.stderr)
        return 2
    records = generate_records(
        round_number=args.round,
        steps=args.steps,
        deployment_adapter=adapter,
        repeats=args.repeats,
    )
    errors = validate_records(records, source="generated")
    if errors:
        for error in errors:
            print("ERROR:", error, file=sys.stderr)
        print("hardware_parity: refusing to write invalid records", file=sys.stderr)
        return 1
    try:
        write_jsonl(out, records)
    except FileExistsError:
        print(
            f"hardware_parity: refusing to overwrite existing round {out}",
            file=sys.stderr,
        )
        return 2
    verdicts = {}
    for record in records:
        verdict = record["result"]["verdict"]
        verdicts[verdict] = verdicts.get(verdict, 0) + 1
    print(json.dumps({"written": str(out), "records": len(records),
                      "by_verdict": verdicts}, indent=2, sort_keys=True))
    return 0


def _cmd_validate(records, parse_errors, source):
    errors = parse_errors + validate_records(records, source=source)
    print(json.dumps({"records": len(records), "errors": len(errors)}, indent=2))
    for error in errors:
        print("ERROR:", error, file=sys.stderr)
    return 1 if errors else 0


def _cmd_training_view(records, parse_errors, source):
    views, errors = build_training_views(records, source=source)
    if parse_errors or errors:
        for error in parse_errors + errors:
            print("ERROR:", error, file=sys.stderr)
        return 1
    for view in views:
        print(json.dumps(view, sort_keys=True))
    return 0


def main(argv=None):
    args = parse_args(argv)
    if args.command == "availability":
        print(json.dumps(availability_report(), indent=2, sort_keys=True))
        return 0
    if args.command == "generate":
        return _cmd_generate(args)
    records, parse_errors = read_jsonl(args.path)
    if args.command == "validate":
        return _cmd_validate(records, parse_errors, Path(args.path).name)
    return _cmd_training_view(records, parse_errors, Path(args.path).name)


if __name__ == "__main__":
    raise SystemExit(main())
