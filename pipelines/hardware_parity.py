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
  python3 pipelines/hardware_parity.py generate <out_dir> [--round N] [--seed N]
                                       [--target NAME] [--capture PATH]
  python3 pipelines/hardware_parity.py validate <path>
  python3 pipelines/hardware_parity.py training-view <path>
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

import oracle_contract as contract  # noqa: E402
from neuro_oracle import (  # noqa: E402
    PHYSICAL_TARGETS,
    Q88_STEP,
    TARGET_FIXED_POINT_MODEL,
    FixedPointReferenceAdapter,
    OracleUnavailable,
    RecordedCaptureAdapter,
    SoftwareFloatAdapter,
    availability_report,
    digest,
    get_adapter,
    normalize_model,
    normalize_stimulus,
    quantize_model,
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


def spike_bitmap_metrics(software, hardware):
    """Cell-by-cell agreement over the (timestep, neuron) spike bitmap."""
    if not software or not hardware:
        return {"comparable": False, "reason": "empty spike grid"}
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
    if not software or not hardware or len(software[0]) != len(hardware[0]):
        return {"comparable": False, "reason": "spike grids have different widths"}
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


def membrane_metrics(software_membrane, hardware_membrane):
    """Membrane error where both sides expose an observable trace."""
    soft = (software_membrane or {}).get("trace")
    hard = (hardware_membrane or {}).get("trace")
    if not (software_membrane or {}).get("observable") or not (
        hardware_membrane or {}
    ).get("observable"):
        return {
            "observable": False,
            "reason_code": "MEMBRANE_DIVERGENCE",
            "reason": "at least one side does not expose membrane state",
        }
    if not soft or not hard or len(soft) != len(hard) or len(soft[0]) != len(hard[0]):
        return {"observable": False, "reason": "membrane traces have different shapes"}
    diffs = [abs(a - b) for row_a, row_b in zip(soft, hard) for a, b in zip(row_a, row_b)]
    return {
        "observable": True,
        "units": "mV_model",
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
    return software_run, deployment_run, unavailable


def build_record(scenario, software_run, deployment_run, unavailable, round_number,
                 fpga_status):
    """Assemble one envelope record from a paired run."""
    # Deep-copied so no two records (and no two fields of one record) share a
    # mutable sub-object: an edit to one would otherwise silently rewrite the
    # other, which is precisely the failure mode these records exist to catch.
    fixture = copy.deepcopy(scenario["input_fixture"])
    oracle = {
        "pairing": "software_simulator <-> deployment_target",
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
    if unavailable:
        oracle["unavailable"].append(unavailable)

    prediction = {
        "source": "generator",
        "authoritative": False,
        "hypothesis": scenario["hypothesis"],
        "expected_verdict": (
            contract.VERDICT_MATCH if scenario["stress"] == "none"
            else contract.VERDICT_MISMATCH
        ),
    }
    provenance = {
        "kind": "simulated",
        "tool": VALIDATOR,
        "tool_version": SCHEMA_VERSION,
        "contract_version": contract.CONTRACT_VERSION,
        "scenario_sha256": digest(
            {"model": scenario["model_float"], "stimulus": scenario["stimulus"]}
        ),
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
        record["result"] = {
            "oracle_backed": True,
            "verdict": contract.VERDICT_INCONCLUSIVE,
            "reason_codes": ["ORACLE_UNAVAILABLE"],
            "derived_from": [software_run["output_digest"]],
            "parity": None,
            "summary": (
                "no paired run: the deployment-side oracle did not execute "
                f"({unavailable['reason_code'] if unavailable else 'unknown'}). "
                "This record carries the software leg as evidence and makes no "
                "parity claim."
            ),
        }
        return record

    oracle["software"] = _slim_run(software_run)
    oracle["deployment"] = _slim_run(deployment_run)
    parity, verdict, reason_codes = compute_parity(scenario, software_run, deployment_run)
    record["result"] = {
        "oracle_backed": True,
        "verdict": verdict,
        "reason_codes": reason_codes,
        "derived_from": [software_run["output_digest"], deployment_run["output_digest"]],
        "parity": parity,
        "summary": _summarize(scenario, parity, verdict, deployment_run),
    }
    return record


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


def _metrics_equal(recorded, recomputed, path, where):
    """Deep-compare a recorded metric block against a recomputed one."""
    errors = []
    if isinstance(recomputed, dict):
        if not isinstance(recorded, dict):
            return [f"{where}: {path} must be an object [PARITY_METRIC_MISMATCH]"]
        for key, value in recomputed.items():
            if key not in recorded:
                errors.append(
                    f"{where}: {path}.{key} is missing [PARITY_METRIC_MISMATCH]"
                )
                continue
            errors += _metrics_equal(recorded[key], value, f"{path}.{key}", where)
        return errors
    if isinstance(recomputed, float) and isinstance(recorded, (int, float)):
        if abs(recorded - recomputed) > METRIC_TOL:
            errors.append(
                f"{where}: {path} recorded {recorded!r} but traces give {recomputed!r} "
                "[PARITY_METRIC_MISMATCH]"
            )
        return errors
    if recorded != recomputed:
        errors.append(
            f"{where}: {path} recorded {recorded!r} but traces give {recomputed!r} "
            "[PARITY_METRIC_MISMATCH]"
        )
    return errors


def _check_input_fixture(record, where):
    """Both sides must provably have run the same encoded input."""
    errors = []
    scenario = record.get("scenario") or {}
    stimulus = scenario.get("stimulus")
    fixture = scenario.get("input_fixture") or {}
    oracle_fixture = (record.get("oracle") or {}).get("input_fixture") or {}
    if not isinstance(stimulus, dict) or not isinstance(stimulus.get("events"), list):
        return [f"{where}: scenario.stimulus.events missing [INPUT_FIXTURE_MISMATCH]"]
    recomputed = digest(stimulus["events"])
    if fixture.get("sha256") != recomputed:
        errors.append(
            f"{where}: scenario.input_fixture.sha256 does not match the recorded events "
            "[INPUT_FIXTURE_MISMATCH]"
        )
    if oracle_fixture.get("sha256") != recomputed:
        errors.append(
            f"{where}: oracle.input_fixture.sha256 does not match the recorded events; "
            "the two sides cannot be shown to have run the same input "
            "[INPUT_FIXTURE_MISMATCH]"
        )
    if stimulus.get("steps") != len(stimulus["events"]):
        errors.append(f"{where}: stimulus.steps disagrees with the event grid "
                      "[INPUT_FIXTURE_MISMATCH]")
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
    except ValueError as exc:
        return [f"{where}: scenario.model_float is not simulable: {exc}"]
    errors = []
    for key in (
        "parameter_count",
        "saturated_parameter_count",
        "rounding",
        "saturation_policy",
        "step",
    ):
        if recorded.get(key) != recomputed[key]:
            errors.append(
                f"{where}: quantization.{key} recorded {recorded.get(key)!r} but "
                f"re-deriving from the float model gives {recomputed[key]!r} "
                "[Q88_PROVENANCE_MISMATCH]"
            )
    recorded_params = {
        entry.get("parameter"): entry for entry in recorded.get("parameters", [])
    }
    for entry in recomputed["parameters"]:
        stored = recorded_params.get(entry["parameter"])
        if stored is None:
            errors.append(
                f"{where}: quantization provenance omits {entry['parameter']} "
                "[Q88_PROVENANCE_MISMATCH]"
            )
            continue
        if stored.get("q88_raw") != entry["q88_raw"] or stored.get("saturated") != entry[
            "saturated"
        ]:
            errors.append(
                f"{where}: quantization of {entry['parameter']} recorded "
                f"{stored.get('q88_raw')!r}/{stored.get('saturated')!r} but re-derives to "
                f"{entry['q88_raw']!r}/{entry['saturated']!r} [Q88_PROVENANCE_MISMATCH]"
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
        return []
    errors = []
    for section, key in REQUIRED_HARDWARE_FIELDS:
        block = deployment.get(section)
        if not isinstance(block, dict) or not block.get(key):
            errors.append(
                f"{where}: {target} claim needs oracle.deployment.{section}.{key} "
                "[HW_PROVENANCE_MISSING]"
            )
    latency = deployment.get("latency") or {}
    if latency.get("measured") is not True or not isinstance(
        latency.get("value_ms"), (int, float)
    ):
        errors.append(
            f"{where}: {target} claim needs a measured latency in ms "
            "[HW_PROVENANCE_MISSING]"
        )
    repeats = deployment.get("repeats")
    if not isinstance(repeats, int) or repeats < 2:
        errors.append(
            f"{where}: {target} claim needs at least 2 repeated runs to say anything "
            "about determinism [REPEATABILITY_UNPROVEN]"
        )
    return errors


def validate_record(record, where):
    """Full validation of one hardware-parity record."""
    oracle = record.get("oracle") if isinstance(record, dict) else None
    digests = None
    if isinstance(oracle, dict):
        digests = [
            side["output_digest"]
            for side in (oracle.get("software"), oracle.get("deployment"))
            if isinstance(side, dict) and side.get("output_digest")
        ]
    errors = contract.check_envelope(record, where, oracle_digests=digests)
    if not isinstance(record, dict) or record.get("record_kind") != RECORD_KIND:
        return errors
    errors += _check_input_fixture(record, where)
    errors += _check_physical_claim(record, where)

    result = record.get("result") or {}
    software = (oracle or {}).get("software")
    deployment = (oracle or {}).get("deployment")

    if deployment is None:
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
        if "ORACLE_UNAVAILABLE" not in (result.get("reason_codes") or []):
            errors.append(
                f"{where}: an unpaired record must carry ORACLE_UNAVAILABLE "
                "[ORACLE_UNAVAILABLE]"
            )
        if not (oracle or {}).get("unavailable"):
            errors.append(
                f"{where}: oracle.unavailable must explain why no pair executed "
                "[ORACLE_UNAVAILABLE]"
            )
        return errors

    if not isinstance(software, dict):
        errors.append(f"{where}: oracle.software missing [ENVELOPE_MALFORMED]")
        return errors

    errors += _check_quantization(record, where)

    scenario = record.get("scenario") or {}
    try:
        parity, verdict, reason_codes = compute_parity(scenario, software, deployment)
    except (KeyError, TypeError, ValueError) as exc:
        return errors + [f"{where}: parity metrics are not recomputable: {exc}"]

    recorded_parity = result.get("parity")
    if not isinstance(recorded_parity, dict):
        errors.append(f"{where}: result.parity must be an object [PARITY_METRIC_MISMATCH]")
    else:
        for section in ("spike_bitmap", "action", "timing", "membrane", "quantization"):
            errors += _metrics_equal(
                recorded_parity.get(section), parity[section], f"result.parity.{section}",
                where,
            )
    if result.get("verdict") != verdict:
        errors.append(
            f"{where}: result.verdict is {result.get('verdict')!r} but the recorded "
            f"traces support {verdict!r} [PARITY_VERDICT_INCONSISTENT]"
        )
    missing_codes = sorted(set(reason_codes) - set(result.get("reason_codes") or []))
    if missing_codes:
        errors.append(
            f"{where}: result.reason_codes omits {missing_codes} that the traces "
            "require [PARITY_VERDICT_INCONSISTENT]"
        )
    return errors


def validate_records(records, source="record"):
    errors = []
    for index, record in enumerate(records, 1):
        errors += validate_record(record, f"{source}:{index}")
    return errors


# ── Training view ─────────────────────────────────────────────────────


def training_view(record):
    """A supervised view that carries the parity verdict on its face."""
    scenario = record.get("scenario") or {}
    result = record.get("result") or {}
    oracle = record.get("oracle") or {}
    targets = [
        side.get("execution_target")
        for side in (oracle.get("software"), oracle.get("deployment"))
        if isinstance(side, dict)
    ]
    prompt = (
        f"A Spikenaut network ({scenario.get('name')}) is exported to Q8.8 and executed on "
        f"the deployment target under stress '{scenario.get('stress')}'. Identical encoded "
        f"input fixture {(scenario.get('input_fixture') or {}).get('sha256')}. "
        "Does the behaviour survive the export?"
    )
    completion = result.get("summary")
    view = contract.build_training_view(record, prompt, completion, targets)
    view["stress"] = scenario.get("stress")
    view["scenario_id"] = scenario.get("id")
    return view


def build_training_views(records, source="record"):
    """Build views for every record and prove none of them softened a failure."""
    views = [training_view(record) for record in records]
    errors = []
    for index, (record, view) in enumerate(zip(records, views), 1):
        errors += contract.training_view_errors(record, view, f"{source}:{index}")
    errors += contract.view_set_errors(records, views, source)
    return views, errors


# ── CLI ───────────────────────────────────────────────────────────────


def read_jsonl(path):
    records = []
    errors = []
    for lineno, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            errors.append(f"{Path(path).name}:{lineno}: JSON parse error: {exc}")
    return records, errors


def write_jsonl(path, records):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def _load_deployment_adapter(target, capture):
    if capture:
        return RecordedCaptureAdapter(capture)
    if target is None or target == FixedPointReferenceAdapter.name:
        return FixedPointReferenceAdapter()
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


def main(argv=None):
    args = parse_args(argv)
    if args.command == "availability":
        print(json.dumps(availability_report(), indent=2, sort_keys=True))
        return 0
    if args.command == "generate":
        try:
            adapter = _load_deployment_adapter(args.target, args.capture)
        except KeyError as exc:
            print(f"hardware_parity: {exc}", file=sys.stderr)
            return 2
        records = generate_records(
            round_number=args.round,
            steps=args.steps,
            deployment_adapter=adapter,
            repeats=args.repeats,
        )
        errors = validate_records(records, source="generated")
        out = Path(args.out_dir) / FACTORY_SLUG / f"batch-r{args.round:02d}.jsonl"
        if errors:
            for error in errors:
                print("ERROR:", error, file=sys.stderr)
            print("hardware_parity: refusing to write invalid records", file=sys.stderr)
            return 1
        write_jsonl(out, records)
        verdicts = {}
        for record in records:
            verdict = record["result"]["verdict"]
            verdicts[verdict] = verdicts.get(verdict, 0) + 1
        print(json.dumps({"written": str(out), "records": len(records),
                          "by_verdict": verdicts}, indent=2, sort_keys=True))
        return 0
    records, parse_errors = read_jsonl(args.path)
    if args.command == "validate":
        errors = parse_errors + validate_records(records, source=Path(args.path).name)
        print(json.dumps({"records": len(records), "errors": len(errors)}, indent=2))
        for error in errors:
            print("ERROR:", error, file=sys.stderr)
        return 1 if errors else 0
    views, errors = build_training_views(records, source=Path(args.path).name)
    if parse_errors or errors:
        for error in parse_errors + errors:
            print("ERROR:", error, file=sys.stderr)
        return 1
    for view in views:
        print(json.dumps(view, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
