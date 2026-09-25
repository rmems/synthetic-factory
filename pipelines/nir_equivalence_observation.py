"""Observe NIR output values without turning analog magnitudes into spikes."""

from __future__ import annotations

import sys

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("nir_equivalence_observation")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "nir_equivalence_observation"
    )


def _spiking_signals(graph):
    """Spike emitters and transparent paths whose inputs are all spike signals."""
    pending = _transparent_inputs(graph)
    known = set(pending) | {name for name, node in graph["nodes"].items()
                            if node["type"] in {"LIF", "IF", "Threshold"}}
    while pending:
        analog = _analog_pending(pending, known)
        if not analog:
            break
        known.difference_update(analog)
        for name in analog:
            del pending[name]
    return known


def _analog_pending(pending, known):
    """Transparent nodes not (yet) established as spike-carrying."""
    return {name for name, sources in pending.items()
            if not sources or sources - known}


def _transparent_inputs(graph):
    pending = {}
    for name, node in graph["nodes"].items():
        if node["type"] in {"Output", "Delay"}:
            pending[name] = {source for source, target in graph["edges"] if target == name}
    return pending


class OutputObservation:
    """Capture display traces and discrete output events from the same timestep."""

    def __init__(self, graph, output_node):
        self.spiking = output_node in _spiking_signals(graph)
        self.trace = []
        self.events = []

    def append(self, values):
        step = len(self.trace)
        if self.spiking:
            self.events.extend({"t_step": step, "channel": channel}
                               for channel, value in enumerate(values) if value >= 1.0)
        self.trace.append([round(value, 12) for value in values])


def final_membrane(state):
    """Only neuron membrane state is part of this observation contract."""
    return {name: {"v": [round(item, 12) for item in blob["v"]]}
            for name, blob in sorted(state.items()) if "v" in blob}


if __package__:
    _expose_package_sibling(__name__)
