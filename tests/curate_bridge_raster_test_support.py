"""Shared builders for the Bridge raster-contract regression test modules.

Re-exports the ``test_curate_bridge`` builders those modules use (importing it also
puts ``pipelines/`` on ``sys.path``) and adds the zero-spike reference record.
"""

from __future__ import annotations

try:
    from tests.test_curate_bridge import (
        bridge,
        curate_bridge,
        decide,
        event,
        gate_snn_fixture,
    )
except ModuleNotFoundError:
    from test_curate_bridge import (  # type: ignore[no-redef]
        bridge,
        curate_bridge,
        decide,
        event,
        gate_snn_fixture,
    )

__all__ = [
    "bridge",
    "curate_bridge",
    "decide",
    "event",
    "gate_snn_fixture",
    "zero_spike_record",
]


def zero_spike_record():
    """The reference record retuned to a legitimately zero-spike raster.

    ``round(1 * 1.0 * 0.02)`` is 0, so the budget, the 23 pJ/spike energy and
    both declared totals are all exactly zero -- the case where an
    absolute-tolerance comparison alone would accept a negative energy.
    """

    record = gate_snn_fixture()
    record["raster"].update(
        {
            "neurons": 1,
            "mean_rate_hz": 1.0,
            "window_ms": 20,
            "window_s": 0.02,
            "spikes": 0,
            "energy_pJ": 0,
            "energy_uJ": 0,
            "excerpt": [{"t_us": 5000, "neuron_id": 0}],
        }
    )
    return record
