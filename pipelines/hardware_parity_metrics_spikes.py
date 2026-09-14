#!/usr/bin/env python3
"""Do the two runs spike in the same cells, at the same steps?

The bitmap and timing halves of the agreement. Both are shape-strict: a
ragged or mis-sized grid is a stated reason, never a silent zero.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))


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
