#!/usr/bin/env python3
"""Do the two runs spike in the same cells, at the same steps?

The bitmap and timing halves of the agreement. Both are shape-strict: a
ragged or mis-sized grid is a stated reason, never a silent zero.
"""

from __future__ import annotations

import sys

if __package__:
    # Import-twin helpers join the package import lock; import-order tests cover this edge.
    from . import _assert_direct_sibling, _expose_package_sibling  # pylint: disable=cyclic-import

    _assert_direct_sibling("hardware_parity_metrics_spikes")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "hardware_parity_metrics_spikes"
    )

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
    if not (isinstance(grid, list) and grid and _list_rows(grid)):
        return False
    return _uniform_row_width(grid)


def _list_rows(grid):
    """Every element of `grid` is itself a list."""
    return all(isinstance(row, list) for row in grid)


def _uniform_row_width(grid):
    """Every row shares ``grid[0]``'s width, which must be non-zero."""
    width = len(grid[0])
    return width > 0 and all(len(row) == width for row in grid)


def _spike_grid_shape_reason(software, hardware):
    """Why two spike grids cannot be laid over each other, or None if they can.

    Shape only. An empty grid is reported separately by the bitmap metric
    under its own reason, so the caller decides whether emptiness deserves a
    distinct report before asking about shape.
    """
    if not (_rectangular(software) and _rectangular(hardware)):
        return "spike grid is ragged or malformed"
    if (len(software), len(software[0])) != (len(hardware), len(hardware[0])):
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
    tally = {"matches": 0, "false_positive": 0, "false_negative": 0,
             "both": 0, "either": 0}
    for a, b in _spike_cells(software, hardware):
        _tally_cell(tally, a, b)
    return (
        tally["matches"],
        tally["false_positive"],
        tally["false_negative"],
        tally["both"],
        tally["either"],
    )


# A hardware-only firing is a false positive; every other non-match —
# software-only or a disagreement where both fired — is a false negative.
_MISMATCH_BUCKET = {
    (False, True): "false_positive",
}


def _tally_cell(tally, a, b):
    """Accumulate one (software, hardware) spike pair into the agreement buckets."""
    fired_a, fired_b = bool(a), bool(b)
    key = "matches" if a == b else _MISMATCH_BUCKET.get(
        (fired_a, fired_b), "false_negative"
    )
    tally[key] += 1
    tally["either"] += int(fired_a or fired_b)
    tally["both"] += int(fired_a and fired_b)


def spike_bitmap_metrics(software, hardware):
    """Cell-by-cell agreement over the (timestep, neuron) spike bitmap."""
    if not software or not hardware:
        return {"comparable": False, "reason": "empty spike grid"}
    reason = _spike_grid_shape_reason(software, hardware)
    if reason is not None:
        return {"comparable": False, "reason": reason}
    return _bitmap_report(software, hardware)


def _bitmap_report(software, hardware):
    """The comparable-grid report: agreement, distance, Jaccard, and counts."""
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


def _paired_first_spike_deltas(pairs):
    """Step deltas over the neurons that fired on both sides."""
    return [
        abs(a - b)
        for a, b in pairs
        if a is not None and b is not None
    ]


def _single_sided_counts(pairs):
    """How many neurons fired on exactly one side of the pair."""
    only_software = sum(
        1 for a, b in pairs if a is not None and b is None
    )
    only_hardware = sum(
        1 for a, b in pairs if a is None and b is not None
    )
    return only_software, only_hardware


def _first_spike_deltas(soft_first, hard_first):
    """Per-neuron first-spike deltas plus the single-sided counts."""
    pairs = list(zip(soft_first, hard_first))
    only_software, only_hardware = _single_sided_counts(pairs)
    return _paired_first_spike_deltas(pairs), only_software, only_hardware


def timing_metrics(software, hardware, dt_ms):
    """First-spike timing error over neurons that fired on both sides."""
    reason = _spike_grid_shape_reason(software, hardware)
    if reason is not None:
        return {"comparable": False, "reason": reason}
    neurons = len(software[0])
    soft_first = _first_spike_steps(software, neurons)
    hard_first = _first_spike_steps(hardware, neurons)
    deltas, only_software, only_hardware = _first_spike_deltas(
        soft_first, hard_first
    )
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


if __package__:
    _expose_package_sibling(__name__)
