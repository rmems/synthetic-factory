#!/usr/bin/env python3
"""The in-repo NIR interpreter and its per-node kernels.

One class and the three step functions it runs. The two reference runtimes are
this interpreter under different declared conventions, which is what makes a
divergence between them attributable to the convention.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

if __package__:
    # Import-twin helpers join the package import lock; import-order tests cover this edge.
    from . import _assert_direct_sibling, _expose_package_sibling  # pylint: disable=cyclic-import

    _assert_direct_sibling("nir_equivalence_interpreter")
    from .nir_equivalence_observation import OutputObservation, final_membrane
    from .nir_equivalence_kernels import (  # noqa: E402
        _integrate_membrane,
        _sum_drive_parts,
        _step_affine,
        _step_delay,
    )
    from .nir_equivalence_graph import (  # noqa: E402
        GraphError,
        _roundtrip_with_codec,
        evaluation_order,
        parse,
        serialize,
    )
    from .nir_equivalence_terms import (  # noqa: E402
        ALL_KNOWN_TYPES,
        STATEFUL_TYPES,
    )
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "nir_equivalence_interpreter"
    )
    from nir_equivalence_observation import OutputObservation, final_membrane
    from nir_equivalence_kernels import (  # noqa: E402
        _integrate_membrane,
        _sum_drive_parts,
        _step_affine,
        _step_delay,
    )
    from nir_equivalence_graph import (  # noqa: E402
        GraphError,
        _roundtrip_with_codec,
        evaluation_order,
        parse,
        serialize,
    )
    from nir_equivalence_terms import (  # noqa: E402
        ALL_KNOWN_TYPES,
        STATEFUL_TYPES,
    )

class UnsupportedConstruct(Exception):
    """A runtime refusing a construct on purpose. This is a diagnostic, not a bug."""

    def __init__(self, node, node_type, detail):
        super().__init__(f"{node} ({node_type}): {detail}")
        self.node = node
        self.node_type = node_type
        self.detail = detail


@dataclass(frozen=True)
class RuntimeConventions:
    """The three independent semantic choices of a reference runtime."""

    reset: str
    delay_unit: str
    cycle_break_order: str

    def as_dict(self):
        return {
            "reset": self.reset,
            "delay_unit": self.delay_unit,
            "cycle_break_order": self.cycle_break_order,
        }


class NirReferenceRuntime:
    """A deterministic in-repo NIR interpreter with declared conventions."""

    runtime_class = "in_repo_reference"

    def __init__(self, name, conventions, supported_types):
        self.name = name
        self.conventions = conventions.as_dict()
        self.supported_types = tuple(sorted(supported_types))

    def availability(self):
        return {"available": True, "reason_code": None, "detail": "stdlib interpreter"}

    def serialize_graph(self, graph):
        """Serialize through this runtime's declared interchange adapter."""
        return serialize(graph)

    def parse_graph(self, text):
        """Parse through this runtime's declared interchange adapter."""
        return parse(text)

    def roundtrip_graph(self, graph):
        report = _roundtrip_with_codec(graph, self.serialize_graph, self.parse_graph)
        report["runtime"] = self.name
        report["adapter"] = f"{self.name}.nir_json"
        return report

    # -- node semantics -------------------------------------------------

    def _check_supported(self, graph):
        for name, node in graph["nodes"].items():
            node_type = node.get("type")
            if node_type not in self.supported_types:
                known = node_type in ALL_KNOWN_TYPES
                raise UnsupportedConstruct(
                    name,
                    node_type,
                    (
                        f"{self.name} does not implement {node_type!r}"
                        if known
                        else f"{node_type!r} is not a construct this runtime recognises"
                    ),
                )

    def _init_state(self, graph):
        state = {}
        for name, node in graph["nodes"].items():
            node_type = node.get("type")
            if node_type not in STATEFUL_TYPES:
                continue
            state[name] = self._node_initial_state(name, node)
        return state

    def _node_initial_state(self, name, node):
        node_type = node.get("type")
        size = int(node.get("size", 0))
        if size < 1:
            raise GraphError(f"node {name!r} of type {node_type} needs size >= 1")
        if node_type == "Delay":
            return self._delay_initial_state(node, size)
        return {"v": [0.0] * size}

    def _delay_initial_state(self, node, size):
        depth = int(node.get("delay", 0))
        if self.conventions["delay_unit"] == "steps_minus_one":
            depth = max(depth - 1, 0)
        return {"buffer": [[0.0] * size for _ in range(depth)]}

    def _node_step(self, named_node, drive, state, dt_s):
        name, node = named_node
        node_type = node["type"]
        if node_type in ("Input", "Output"):
            return list(drive)
        if node_type in ("Affine", "Linear"):
            return _step_affine(name, node, drive)
        if node_type == "Threshold":
            threshold = float(node["threshold"])
            return [1.0 if value >= threshold else 0.0 for value in drive]
        if node_type == "Delay":
            return _step_delay(name, drive, state)
        if node_type in ("LIF", "LI", "IF"):
            return self._step_neuron(named_node, drive, state, dt_s)
        raise UnsupportedConstruct(name, node_type, "no implementation")

    def _step_neuron(self, named_node, drive, state, dt_s):
        """Integrate one LIF/LI/IF node and emit its output for this step."""
        name, node = named_node
        membrane = state[name]["v"]
        _integrate_membrane(named_node, membrane, drive, dt_s)
        if node["type"] == "LI":
            return list(membrane)
        return self._emit_spikes(membrane, float(node["v_threshold"]))

    def _emit_spikes(self, membrane, threshold):
        """Threshold the membrane and apply this runtime's reset convention."""
        reset_to_zero = self.conventions["reset"] == "zero"
        spikes = []
        for index in range(len(membrane)):
            if membrane[index] >= threshold:
                spikes.append(1.0)
                if reset_to_zero:
                    membrane[index] = 0.0
                else:
                    membrane[index] -= threshold
            else:
                spikes.append(0.0)
        return spikes

    # -- execution ------------------------------------------------------

    @staticmethod
    def _io_nodes(graph):
        """The declared Output and Input node names; both must be present."""
        output_nodes = [
            name for name, node in graph["nodes"].items() if node["type"] == "Output"
        ]
        input_nodes = [
            name for name, node in graph["nodes"].items() if node["type"] == "Input"
        ]
        if not output_nodes or not input_nodes:
            raise GraphError("graph needs at least one Input and one Output node")
        return output_nodes, input_nodes

    @staticmethod
    def _declared_sizes(graph):
        """Every node's declared output width.

        Every node declares its output width explicitly. Inferring it would
        make a recurrent edge's first read depend on inference order.
        """
        sizes = {}
        for name, node in graph["nodes"].items():
            size = node.get("size")
            if size is None and node.get("shape"):
                size = node["shape"][0]
            if not _positive_integer_size(size):
                raise GraphError(f"node {name!r} must declare an integer size >= 1")
            sizes[name] = size
        return sizes

    @staticmethod
    def _summed_drive(name, sources, previous, current):
        """Sum a node's incoming vectors in declared edge order."""
        parts = []
        for source, is_recurrent in sources:
            parts.append(previous[source] if is_recurrent else current[source])
        return _sum_drive_parts(name, parts)

    def execute(self, graph, stimulus):
        """Run one graph against one stimulus. Raises on unsupported constructs."""
        return _GraphExecution(self, graph, stimulus).run()


def _positive_integer_size(size):
    if not isinstance(size, int) or isinstance(size, bool):
        return False
    return size >= 1


class _GraphExecution:
    """State and ordered traversal for a single interpreter invocation."""

    def __init__(self, runtime, graph, stimulus):
        self.runtime = runtime
        self.graph = graph
        self.stimulus = stimulus
        runtime._check_supported(graph)
        self.order, self.recurrent = evaluation_order(
            graph, runtime.conventions["cycle_break_order"]
        )
        self.state = runtime._init_state(graph)
        self.dt_s = float(graph.get("dt_s", 1e-3))
        self.incoming = _incoming_edges(graph, self.recurrent)
        output_nodes, _input_nodes = runtime._io_nodes(graph)
        self.output_node = output_nodes[0]
        sizes = runtime._declared_sizes(graph)
        self.previous = {name: [0.0] * sizes[name] for name in graph["nodes"]}
        self.observation = OutputObservation(graph, self.output_node)

    def run(self):
        for step in range(self.stimulus["steps"]):
            self.previous = self._evaluate_step(step)
            self.observation.append(self.previous[self.output_node])
        return {
            "steps": self.stimulus["steps"],
            "output_node": self.output_node,
            "output_trace": self.observation.trace,
            "spike_events": self.observation.events,
            "spike_count": len(self.observation.events),
            "final_membrane": final_membrane(self.state),
            "evaluation_order": list(self.order),
            "recurrent_edges": sorted([source, target] for source, target in self.recurrent),
        }

    def _evaluate_step(self, step):
        current = {}
        for name in self.order:
            node = self.graph["nodes"][name]
            drive = self._node_drive(name, node, current, step)
            current[name] = self.runtime._node_step(
                (name, node), drive, self.state, self.dt_s
            )
        return current

    def _node_drive(self, name, node, current, step):
        if node["type"] == "Input":
            return [float(value) for value in self.stimulus["events"][step]]
        return self.runtime._summed_drive(name, self.incoming[name], self.previous, current)


def _incoming_edges(graph, recurrent):
    incoming = {name: [] for name in graph["nodes"]}
    for source, target in graph["edges"]:
        incoming[target].append((source, (source, target) in recurrent))
    return incoming


if __package__:
    _expose_package_sibling(__name__)
