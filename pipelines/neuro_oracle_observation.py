#!/usr/bin/env python3
"""The behavioural observations a run retains: spike events and the decoded action.

What a record says the run *did*, as distinct from how it was computed. Both
simulators and the capture replayer project through these, so the two sides of
a parity comparison are always describing the same kind of thing.
"""

from __future__ import annotations

from pathlib import Path
import sys

_PIPELINES = Path(__file__).resolve().parent

if __package__:
    # Import-twin helpers join the package import lock; import-order tests cover this edge.
    from . import _assert_direct_sibling, _expose_package_sibling  # pylint: disable=cyclic-import

    _assert_direct_sibling("neuro_oracle_observation")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "neuro_oracle_observation"
    )
    if str(_PIPELINES) not in sys.path:
        sys.path.insert(0, str(_PIPELINES))

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


if __package__:
    _expose_package_sibling(__name__)
