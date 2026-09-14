#!/usr/bin/env python3
"""Parity metrics: what the two recorded runs actually agree and disagree on.

Every number here is recomputed from the recorded spike and membrane traces
during validation, so this module is the definition of the agreement a record
is allowed to claim, not a summary of one.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from neuro_oracle import PHYSICAL_TARGETS  # noqa: E402
from hardware_parity_terms import MEMBRANE_TOLERANCE, contract  # noqa: E402

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


def _spike_grid_shape_reason(software, hardware):
    """Why two spike grids cannot be laid over each other, or None if they can.

    Shape only. An empty grid is reported separately by the bitmap metric
    under its own reason, so the caller decides whether emptiness deserves a
    distinct report before asking about shape.
    """
    if not _rectangular(software) or not _rectangular(hardware):
        return "spike grid is ragged or malformed"
    if len(software) != len(hardware) or len(software[0]) != len(hardware[0]):
        return "spike grids have different shapes"
    return None


def _spike_cells(software, hardware):
    """The two grids paired cell by cell in (timestep, neuron) order.

    Both grids are rectangular and identically shaped by the time this runs,
    so the pairing visits every cell exactly once, in the order nested
    (step, neuron) indexing would have visited them.
    """
    for software_row, hardware_row in zip(software, hardware):
        yield from zip(software_row, hardware_row)


def _spike_cell_tally(software, hardware):
    """Per-cell agreement counts over two identically shaped spike grids."""
    matches = 0
    false_positive = 0
    false_negative = 0
    both = 0
    either = 0
    for a, b in _spike_cells(software, hardware):
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
    return matches, false_positive, false_negative, both, either


def spike_bitmap_metrics(software, hardware):
    """Cell-by-cell agreement over the (timestep, neuron) spike bitmap."""
    if not software or not hardware:
        return {"comparable": False, "reason": "empty spike grid"}
    reason = _spike_grid_shape_reason(software, hardware)
    if reason is not None:
        return {"comparable": False, "reason": reason}
    matches, false_positive, false_negative, both, either = _spike_cell_tally(
        software, hardware
    )
    cells = len(software) * len(software[0])
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
    reason = _spike_grid_shape_reason(software, hardware)
    if reason is not None:
        return {"comparable": False, "reason": reason}
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


def _parity_metrics(scenario, software_run, hardware_run):
    """Every parity measurement for one paired run, before any verdict."""
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
    return {
        "spike_bitmap": bitmap,
        "action": {
            "software": software_action.get("label"),
            "deployment": hardware_action.get("label"),
            "software_counts": software_action.get("counts"),
            "deployment_counts": hardware_action.get("counts"),
            "agree": software_action.get("label") == hardware_action.get("label"),
            "decode_rule": software_action.get("rule"),
        },
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


def _deployment_qualification_codes(repeatability, hardware_run):
    """What the deployment side leaves unproven, whatever its traces show."""
    codes = []
    if not repeatability["hardware_repeatability_measured"]:
        codes.append("REPEATABILITY_UNPROVEN")
    if not (hardware_run.get("latency") or {}).get("measured"):
        codes.append("LATENCY_NOT_MEASURED")
    if hardware_run.get("execution_target") not in PHYSICAL_TARGETS:
        codes.append("ORACLE_UNAVAILABLE")
    else:
        # A physical run is not reproducible from software -- that is why it
        # was run on hardware. Its traces therefore rest on the integrity of
        # the capture and on the board provenance, and were not re-derived.
        # This code makes that limitation visible on every hardware-claiming
        # record instead of leaving such a record looking unqualified.
        codes.append("DEPLOYMENT_TRACE_NOT_REDERIVABLE")
    return codes


def _parity_reason_codes(parity, hardware_run):
    """Every finding one paired run carries, in the order they are raised.

    The two behavioural disagreements come first because the verdict is
    drawn from them; the deployment qualifications that follow are carried
    even on a `match`, so silence is never mistaken for evidence.
    """
    bitmap = parity["spike_bitmap"]
    membrane = parity["membrane"]
    quantization = parity["quantization"]
    codes = []
    if not bitmap.get("comparable") or bitmap.get("hamming_distance", 1) > 0:
        codes.append("SPIKE_BITMAP_DISAGREEMENT")
    if not parity["action"]["agree"]:
        codes.append("ACTION_DISAGREEMENT")
    if membrane.get("observable") and not membrane.get("within_tolerance"):
        codes.append("MEMBRANE_DIVERGENCE")
    if not membrane.get("observable") and membrane.get("reason_code"):
        codes.append(membrane["reason_code"])
    if quantization.get("saturated_parameter_count") or quantization.get(
        "runtime_saturation_events"
    ):
        codes.append("QUANTIZATION_SATURATION")
    return codes + _deployment_qualification_codes(
        parity["repeatability"], hardware_run
    )


def compute_parity(scenario, software_run, hardware_run):
    """All parity metrics for one paired run, plus the verdict they support."""
    parity = _parity_metrics(scenario, software_run, hardware_run)
    reason_codes = _parity_reason_codes(parity, hardware_run)
    behavioural_mismatch = (
        "SPIKE_BITMAP_DISAGREEMENT" in reason_codes or "ACTION_DISAGREEMENT" in reason_codes
    )
    verdict = contract.VERDICT_MISMATCH if behavioural_mismatch else contract.VERDICT_MATCH
    return parity, verdict, sorted(set(reason_codes))

