#!/usr/bin/env python3
"""`nir-cross-runtime-equivalence` generator, runtimes, and validator.

The question this family answers is whether a neuromorphic graph *means* the
same thing after it crosses a runtime boundary. Successful serialization and
successful parsing are not evidence of that; matching event streams are.

What actually runs here
-----------------------
No upstream NIR runtime is installed in this repository's environment and none
is vendored: ``nir``, ``nirtorch``, ``snntorch``, ``norse``, ``lava`` and
``sinabs`` are all absent, and there is no ``nir-rs`` build. Those runtimes are
therefore declared as adapters that report ``unavailable`` with a reason code,
and a record produced without them says so on its face.

What *is* executed is a pair of in-repo interpreters:

``nir_reference_v1``
    Reset by subtraction, ``Delay`` counted in whole timesteps, cycles broken
    in node insertion order, and ``LI`` supported.

``nir_reference_v1_altorder``
    Reset to zero, ``Delay`` counted as N-1 timesteps, cycles broken in
    reverse-name order, and ``LI`` unsupported.

Every one of those four differences is a documented, real interoperability
hazard between neuromorphic runtimes rather than an invented bug. But the pair
is still two implementations from one repository: a record produced from them
is evidence about *those conventions*, and is not evidence about ``nir-rs`` or
any upstream backend. The ``runtime_class`` field on every runtime entry says
which kind of evidence it is.

Mismatches are the product here. Nothing in this module repairs, retries, or
filters a divergence.

Usage:
  python3 pipelines/nir_equivalence.py availability
  python3 pipelines/nir_equivalence.py generate <out_dir> [--round N] [--steps N]
  python3 pipelines/nir_equivalence.py validate <path>
  python3 pipelines/nir_equivalence.py training-view <path>
"""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import shutil
import sys
from pathlib import Path

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

import oracle_contract as contract  # noqa: E402
from neuro_oracle import canonical_json, digest  # noqa: E402

SCHEMA_VERSION = "1.0.0"
VALIDATOR = "pipelines/nir_equivalence.py"
FACTORY_SLUG = "nir-cross-runtime-equivalence"
RECORD_KIND = contract.KIND_NIR_EQUIVALENCE

NUMERIC_TOL = 1e-9

STATUS_EXECUTED = "executed"
STATUS_UNSUPPORTED = "unsupported"
STATUS_UNAVAILABLE = "unavailable"
RUNTIME_STATUSES = (STATUS_EXECUTED, STATUS_UNSUPPORTED, STATUS_UNAVAILABLE)
# `in_repo_reference` results are re-executed during validation.
# `upstream_runtime` results cannot be, which is why only the former may ever
# be marked executed here.
RUNTIME_CLASSES = ("in_repo_reference", "upstream_runtime")

STATEFUL_TYPES = frozenset({"LIF", "IF", "LI", "Delay"})
ALL_KNOWN_TYPES = frozenset(
    {"Input", "Output", "Affine", "Linear", "LIF", "IF", "LI", "Delay", "Threshold"}
)

GENERATOR_BLOCK = {
    "name": "synthetic-factory.nir_equivalence.graph_catalog",
    "model": "deterministic-stdlib-catalog",
    "role": "proposes graphs, boundary values, and unsupported constructs",
    "produced": ["scenario", "intervention", "candidate_prediction"],
    "may_certify_oracle_result": False,
    "note": (
        "The catalog authors graphs. It never authors outputs: every event trace on "
        "a record comes from an interpreter and is re-executed during validation."
    ),
}


class UnsupportedConstruct(Exception):
    """A runtime refusing a construct on purpose. This is a diagnostic, not a bug."""

    def __init__(self, node, node_type, detail):
        super().__init__(f"{node} ({node_type}): {detail}")
        self.node = node
        self.node_type = node_type
        self.detail = detail


class GraphError(ValueError):
    """A graph that is malformed rather than merely unsupported."""


# ── Graph serialization ───────────────────────────────────────────────


def serialize(graph):
    """Canonical NIR-shaped JSON text for a graph."""
    return canonical_json(graph)


def parse(text):
    """Parse canonical graph text back into a graph object."""
    graph = json.loads(text)
    if not isinstance(graph, dict) or "nodes" not in graph or "edges" not in graph:
        raise GraphError("graph must be an object with `nodes` and `edges`")
    return graph


def structural_digest(graph):
    """Structure-only digest: node types, declared sizes, and the edge set.

    Deliberately independent of parameter values and of key ordering, so a
    structure comparison answers "is this the same graph" rather than "is this
    the same file".
    """
    if not isinstance(graph, dict):
        raise GraphError("graph must be an object")
    nodes = graph.get("nodes")
    edges = graph.get("edges")
    if not isinstance(nodes, dict):
        raise GraphError("graph.nodes must be an object")
    if not isinstance(edges, list):
        raise GraphError("graph.edges must be an array")
    for name, node in nodes.items():
        if not isinstance(name, str) or not isinstance(node, dict):
            raise GraphError("graph nodes must map string names to objects")
    if any(
        not isinstance(edge, list)
        or len(edge) != 2
        or not all(isinstance(item, str) for item in edge)
        for edge in edges
    ):
        raise GraphError("graph edges must be [source, target] string pairs")
    structure = {
        "nodes": sorted(
            [name, node.get("type"), node.get("size"), node.get("shape")]
            for name, node in nodes.items()
        ),
        "edges": sorted([source, target] for source, target in edges),
    }
    return digest(structure)


def _roundtrip_with_codec(graph, serializer, parser):
    """Parse/write parity through one explicitly selected codec adapter."""
    try:
        first = serializer(graph)
        reparsed = parser(first)
        second = serializer(reparsed)
        before = structural_digest(graph)
        after = structural_digest(reparsed)
    except (json.JSONDecodeError, GraphError, TypeError, ValueError) as exc:
        return {
            "parse_ok": False,
            "canonical_stable": False,
            "structure_stable": False,
            "reason_code": "ROUNDTRIP_PARSE_FAILURE",
            "detail": str(exc),
            "structure_digest": None,
        }
    return {
        "parse_ok": True,
        "canonical_stable": first == second,
        "structure_stable": before == after,
        "reason_code": None if (first == second and before == after)
        else "ROUNDTRIP_STRUCTURE_MISMATCH",
        "structure_digest": after,
    }


def roundtrip(graph):
    """Parse/write parity through the module's canonical NIR JSON codec."""
    return _roundtrip_with_codec(graph, serialize, parse)


# ── Graph topology ────────────────────────────────────────────────────


def _successors(graph):
    out = {name: [] for name in graph["nodes"]}
    for source, target in graph["edges"]:
        if source not in out:
            raise GraphError(f"edge from unknown node {source!r}")
        if target not in graph["nodes"]:
            raise GraphError(f"edge to unknown node {target!r}")
        out[source].append(target)
    return out


def evaluation_order(graph, cycle_break_order):
    """Topological order plus the back edges that had to be cut to get one.

    Which edges become back edges depends on the order nodes are visited, and
    real runtimes do not agree on that order. ``cycle_break_order`` makes the
    choice explicit and comparable instead of incidental.
    """
    names = list(graph["nodes"])
    if cycle_break_order == "reverse_name":
        names = sorted(names, reverse=True)
    elif cycle_break_order != "insertion":
        raise GraphError(f"unknown cycle_break_order {cycle_break_order!r}")
    successors = _successors(graph)
    rank = {name: index for index, name in enumerate(names)}
    state = {name: 0 for name in names}
    order = []
    recurrent = set()

    def visit(node):
        state[node] = 1
        for nxt in sorted(successors[node], key=lambda item: rank[item]):
            if state[nxt] == 0:
                visit(nxt)
            elif state[nxt] == 1:
                recurrent.add((node, nxt))
        state[node] = 2
        order.append(node)

    for name in names:
        if state[name] == 0:
            visit(name)
    order.reverse()
    return order, recurrent


# ── Runtimes ──────────────────────────────────────────────────────────


class NirReferenceRuntime:
    """A deterministic in-repo NIR interpreter with declared conventions."""

    runtime_class = "in_repo_reference"

    def __init__(self, name, reset, delay_unit, cycle_break_order, supported_types):
        self.name = name
        self.conventions = {
            "reset": reset,
            "delay_unit": delay_unit,
            "cycle_break_order": cycle_break_order,
        }
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
            size = int(node.get("size", 0))
            if size < 1:
                raise GraphError(f"node {name!r} of type {node_type} needs size >= 1")
            if node_type == "Delay":
                depth = int(node.get("delay", 0))
                if self.conventions["delay_unit"] == "steps_minus_one":
                    depth = max(depth - 1, 0)
                state[name] = {"buffer": [[0.0] * size for _ in range(depth)]}
            else:
                state[name] = {"v": [0.0] * size}
        return state

    def _node_step(self, name, node, drive, state, dt_s):
        node_type = node["type"]
        if node_type in ("Input", "Output"):
            return list(drive)
        if node_type in ("Affine", "Linear"):
            weight = node["weight"]
            bias = node.get("bias") or [0.0] * len(weight)
            if any(len(row) != len(drive) for row in weight):
                raise GraphError(f"node {name!r}: weight columns do not match its input")
            return [
                sum(row[k] * drive[k] for k in range(len(drive))) + bias[index]
                for index, row in enumerate(weight)
            ]
        if node_type == "Threshold":
            threshold = float(node["threshold"])
            return [1.0 if value >= threshold else 0.0 for value in drive]
        if node_type == "Delay":
            buffer = state[name]["buffer"]
            if not buffer:
                return list(drive)
            out = buffer.pop(0)
            buffer.append(list(drive))
            return out
        if node_type in ("LIF", "LI", "IF"):
            membrane = state[name]["v"]
            resistance = float(node.get("r", 1.0))
            if node_type == "IF":
                for index in range(len(membrane)):
                    membrane[index] += resistance * drive[index]
            else:
                tau = float(node["tau"])
                if tau <= 0:
                    raise GraphError(f"node {name!r}: tau must be > 0")
                v_leak = float(node.get("v_leak", 0.0))
                factor = dt_s / tau
                for index in range(len(membrane)):
                    membrane[index] += factor * (
                        (v_leak - membrane[index]) + resistance * drive[index]
                    )
            if node_type == "LI":
                return list(membrane)
            threshold = float(node["v_threshold"])
            spikes = []
            for index in range(len(membrane)):
                if membrane[index] >= threshold:
                    spikes.append(1.0)
                    if self.conventions["reset"] == "zero":
                        membrane[index] = 0.0
                    else:
                        membrane[index] -= threshold
                else:
                    spikes.append(0.0)
            return spikes
        raise UnsupportedConstruct(name, node_type, "no implementation")

    # -- execution ------------------------------------------------------

    def execute(self, graph, stimulus):
        """Run one graph against one stimulus. Raises on unsupported constructs."""
        self._check_supported(graph)
        order, recurrent = evaluation_order(graph, self.conventions["cycle_break_order"])
        state = self._init_state(graph)
        dt_s = float(graph.get("dt_s", 1e-3))
        incoming = {name: [] for name in graph["nodes"]}
        for source, target in graph["edges"]:
            incoming[target].append((source, (source, target) in recurrent))
        output_nodes = [
            name for name, node in graph["nodes"].items() if node["type"] == "Output"
        ]
        input_nodes = [
            name for name, node in graph["nodes"].items() if node["type"] == "Input"
        ]
        if not output_nodes or not input_nodes:
            raise GraphError("graph needs at least one Input and one Output node")
        # Every node declares its output width explicitly. Inferring it would make
        # a recurrent edge's first read depend on inference order.
        sizes = {}
        for name, node in graph["nodes"].items():
            size = node.get("size")
            if size is None and node.get("shape"):
                size = node["shape"][0]
            if not isinstance(size, int) or isinstance(size, bool) or size < 1:
                raise GraphError(f"node {name!r} must declare an integer size >= 1")
            sizes[name] = size
        previous = {name: [0.0] * sizes[name] for name in graph["nodes"]}

        trace = []
        for step in range(stimulus["steps"]):
            current = {}
            for name in order:
                node = graph["nodes"][name]
                if node["type"] == "Input":
                    drive = [float(value) for value in stimulus["events"][step]]
                else:
                    parts = []
                    for source, is_recurrent in incoming[name]:
                        parts.append(previous[source] if is_recurrent else current[source])
                    if not parts:
                        raise GraphError(f"node {name!r} has no inputs")
                    width = len(parts[0])
                    if any(len(part) != width for part in parts):
                        raise GraphError(f"node {name!r} sums inputs of different widths")
                    drive = [sum(part[k] for part in parts) for k in range(width)]
                current[name] = self._node_step(name, node, drive, state, dt_s)
            previous = current
            trace.append([round(value, 12) for value in current[output_nodes[0]]])

        events = [
            {"t_step": step, "channel": channel}
            for step, row in enumerate(trace)
            for channel, value in enumerate(row)
            if value >= 1.0
        ]
        final_state = {
            name: {key: [round(item, 12) for item in value] if isinstance(value, list)
                   else value
                   for key, value in blob.items() if key == "v"}
            for name, blob in sorted(state.items())
            if "v" in blob
        }
        return {
            "steps": stimulus["steps"],
            "output_node": output_nodes[0],
            "output_trace": trace,
            "spike_events": events,
            "spike_count": len(events),
            "final_membrane": final_state,
            "evaluation_order": list(order),
            "recurrent_edges": sorted([source, target] for source, target in recurrent),
        }


class UnavailableRuntime:
    """An upstream runtime that is not present. It has no fallback path."""

    runtime_class = "upstream_runtime"

    def __init__(self, name, module=None, executable=None, detail=""):
        self.name = name
        self.module = module
        self.executable = executable
        self.detail = detail

    def availability(self):
        if self.module and importlib.util.find_spec(self.module) is not None:
            return {
                "available": False,
                "reason_code": "RUNTIME_ADAPTER_NOT_IMPLEMENTED",
                "detail": (
                    f"the {self.module!r} package is importable but this repository "
                    f"ships no adapter for it; {self.detail}"
                ),
            }
        if self.executable and shutil.which(self.executable):
            return {
                "available": False,
                "reason_code": "RUNTIME_ADAPTER_NOT_IMPLEMENTED",
                "detail": (
                    f"{self.executable!r} is on PATH but this repository ships no "
                    f"adapter for it; {self.detail}"
                ),
            }
        return {
            "available": False,
            "reason_code": "RUNTIME_NOT_INSTALLED",
            "detail": f"{self.name} is not installed in this environment; {self.detail}",
        }

    def execute(self, graph, stimulus):
        status = self.availability()
        raise RuntimeUnavailable(self.name, status["reason_code"], status["detail"])


class RuntimeUnavailable(Exception):
    def __init__(self, runtime, reason_code, detail):
        super().__init__(f"{runtime}: {reason_code}: {detail}")
        self.runtime = runtime
        self.reason_code = reason_code
        self.detail = detail


REFERENCE_V1 = NirReferenceRuntime(
    name="nir_reference_v1",
    reset="subtract",
    delay_unit="steps",
    cycle_break_order="insertion",
    supported_types=ALL_KNOWN_TYPES,
)
REFERENCE_ALT = NirReferenceRuntime(
    name="nir_reference_v1_altorder",
    reset="zero",
    delay_unit="steps_minus_one",
    cycle_break_order="reverse_name",
    supported_types=ALL_KNOWN_TYPES - {"LI"},
)
UPSTREAM_RUNTIMES = (
    UnavailableRuntime(
        "nir_rs",
        executable="nir-rs",
        detail="the authority-contract oracle for this family",
    ),
    UnavailableRuntime(
        "nir_python",
        module="nir",
        detail="reference NIR serialization library",
    ),
    UnavailableRuntime(
        "nirtorch_snntorch",
        module="snntorch",
        detail="upstream-compatible execution backend",
    ),
)
IN_REPO_RUNTIMES = (REFERENCE_V1, REFERENCE_ALT)


def availability_report():
    report = {}
    for runtime in (*IN_REPO_RUNTIMES, *UPSTREAM_RUNTIMES):
        status = dict(runtime.availability())
        status["runtime_class"] = runtime.runtime_class
        report[runtime.name] = status
    return report


# ── Graph catalog ─────────────────────────────────────────────────────


def _stimulus(name, steps, channels, pattern):
    events = []
    for step in range(steps):
        events.append(
            [
                1.0 if period and (step - offset) >= 0 and (step - offset) % period == 0
                else 0.0
                for period, offset in pattern
            ]
        )
    return {
        "name": name,
        "encoding": "binary_event_grid",
        "steps": steps,
        "channels": channels,
        "events": events,
    }


GRAPH_SPECS = (
    {
        "id": "nir-feedforward-threshold",
        "name": "stateless feed-forward threshold",
        "class": "feed_forward",
        "description": (
            "Affine followed by a stateless Threshold. No membrane, no reset, no delay "
            "and no cycle, so none of the conventions the two runtimes differ on can "
            "apply. This is the equivalence control."
        ),
        "hypothesis": "both runtimes agree exactly",
        "graph": {
            "name": "ff-threshold",
            "dt_s": 0.001,
            "nodes": {
                "in": {"type": "Input", "shape": [3], "size": 3},
                "fc": {
                    "type": "Affine",
                    "size": 2,
                    "weight": [[1.0, 0.5, 0.0], [0.0, 0.5, 1.0]],
                    "bias": [0.0, 0.25],
                },
                "thr": {"type": "Threshold", "size": 2, "threshold": 1.0},
                "out": {"type": "Output", "size": 2},
            },
            "edges": [["in", "fc"], ["fc", "thr"], ["thr", "out"]],
        },
        "pattern": [(2, 0), (3, 0), (4, 1)],
        "intervention": None,
    },
    {
        "id": "nir-feedforward-subthreshold-lif",
        "name": "sub-threshold feed-forward LIF",
        "class": "feed_forward",
        "description": (
            "A feed-forward LIF whose drive never reaches threshold. Membrane dynamics "
            "are exercised but no reset ever fires, so the reset convention has no "
            "opportunity to matter."
        ),
        "hypothesis": "both runtimes agree; no spikes are produced",
        "graph": {
            "name": "ff-lif-sub",
            "dt_s": 0.001,
            "nodes": {
                "in": {"type": "Input", "shape": [3], "size": 3},
                "fc": {
                    "type": "Affine",
                    "size": 2,
                    "weight": [[0.4, 0.2, 0.0], [0.0, 0.2, 0.4]],
                    "bias": [0.0, 0.0],
                },
                "lif": {
                    "type": "LIF",
                    "size": 2,
                    "tau": 0.02,
                    "r": 1.0,
                    "v_leak": 0.0,
                    "v_threshold": 5.0,
                },
                "out": {"type": "Output", "size": 2},
            },
            "edges": [["in", "fc"], ["fc", "lif"], ["lif", "out"]],
        },
        "pattern": [(1, 0), (2, 0), (3, 0)],
        "intervention": None,
    },
    {
        "id": "nir-reset-convention",
        "name": "supra-threshold reset convention",
        "class": "reset_sensitive",
        "description": (
            "Drive pushes the membrane well past threshold, so the residue left by "
            "reset-by-subtraction versus reset-to-zero changes every later timestep."
        ),
        "hypothesis": "the runtimes diverge on spike timing after the first spike",
        "graph": {
            "name": "reset-sensitive",
            "dt_s": 0.001,
            "nodes": {
                "in": {"type": "Input", "shape": [2], "size": 2},
                "fc": {
                    "type": "Affine",
                    "size": 2,
                    "weight": [[8.0, 0.0], [0.0, 8.0]],
                    "bias": [0.0, 0.0],
                },
                "lif": {
                    "type": "LIF",
                    "size": 2,
                    "tau": 0.002,
                    "r": 1.0,
                    "v_leak": 0.0,
                    "v_threshold": 1.0,
                },
                "out": {"type": "Output", "size": 2},
            },
            "edges": [["in", "fc"], ["fc", "lif"], ["lif", "out"]],
        },
        "pattern": [(1, 0), (2, 0)],
        "intervention": {
            "kind": "convention_probe",
            "detail": "reset-by-subtraction vs reset-to-zero",
            "applies_to": "LIF.reset",
        },
    },
    {
        "id": "nir-delay-semantics",
        "name": "delay unit semantics",
        "class": "delay_sensitive",
        "description": (
            "A Delay node declared as 2. One runtime reads that as two whole timesteps "
            "and the other as N-1, which is the classic off-by-one when a delay written "
            "in seconds is re-expressed in timesteps."
        ),
        "hypothesis": "output is shifted by exactly one timestep",
        "graph": {
            "name": "delay-line",
            "dt_s": 0.001,
            "nodes": {
                "in": {"type": "Input", "shape": [2], "size": 2},
                "dly": {"type": "Delay", "size": 2, "delay": 2},
                "thr": {"type": "Threshold", "size": 2, "threshold": 0.5},
                "out": {"type": "Output", "size": 2},
            },
            "edges": [["in", "dly"], ["dly", "thr"], ["thr", "out"]],
        },
        "pattern": [(3, 0), (4, 1)],
        "intervention": {
            "kind": "convention_probe",
            "detail": "Delay counted in steps vs steps-minus-one",
            "applies_to": "Delay.delay",
        },
    },
    {
        "id": "nir-recurrent-cycle",
        "name": "recurrent cycle break order",
        "class": "recurrent",
        "description": (
            "Two LIF populations excite each other. The cycle has to be cut somewhere "
            "to get an evaluation order, and which edge is cut decides which population "
            "reads a stale value."
        ),
        "hypothesis": "cycle break order changes the event stream",
        "graph": {
            "name": "recurrent-pair",
            "dt_s": 0.001,
            "nodes": {
                "in": {"type": "Input", "shape": [2], "size": 2},
                "a_lif": {
                    "type": "LIF",
                    "size": 2,
                    "tau": 0.004,
                    "r": 1.0,
                    "v_leak": 0.0,
                    "v_threshold": 0.35,
                },
                "b_lif": {
                    "type": "LIF",
                    "size": 2,
                    "tau": 0.004,
                    "r": 1.0,
                    "v_leak": 0.0,
                    "v_threshold": 0.35,
                },
                "out": {"type": "Output", "size": 2},
            },
            "edges": [
                ["in", "a_lif"],
                ["a_lif", "b_lif"],
                ["b_lif", "a_lif"],
                ["b_lif", "out"],
            ],
        },
        "pattern": [(1, 0), (2, 0)],
        "intervention": {
            "kind": "topology_probe",
            "detail": "a_lif <-> b_lif mutual excitation forms a cycle",
            "applies_to": "edges",
        },
    },
    {
        "id": "nir-boundary-values",
        "name": "boundary parameter values",
        "class": "boundary",
        "description": (
            "tau equal to dt (a full membrane replacement each step), a zero threshold, "
            "and a zero-weight column. Valid NIR, but every one of these sits on a "
            "boundary that implementations tend to guard differently."
        ),
        "hypothesis": "both runtimes fire every timestep; reset residue may differ",
        "graph": {
            "name": "boundary",
            "dt_s": 0.001,
            "nodes": {
                "in": {"type": "Input", "shape": [2], "size": 2},
                "fc": {
                    "type": "Affine",
                    "size": 2,
                    "weight": [[1.0, 0.0], [0.0, 0.0]],
                    "bias": [0.0, 0.0],
                },
                "lif": {
                    "type": "LIF",
                    "size": 2,
                    "tau": 0.001,
                    "r": 1.0,
                    "v_leak": 0.0,
                    "v_threshold": 0.0,
                },
                "out": {"type": "Output", "size": 2},
            },
            "edges": [["in", "fc"], ["fc", "lif"], ["lif", "out"]],
        },
        "pattern": [(2, 0), (0, 0)],
        "intervention": {
            "kind": "boundary_probe",
            "detail": "tau == dt, v_threshold == 0, an all-zero weight row",
            "applies_to": "LIF",
        },
    },
    {
        "id": "nir-unusual-but-valid",
        "name": "unusual but valid neuron parameters",
        "class": "unusual_parameters",
        "description": (
            "A negative resting potential, a resistance well above one, and a negative "
            "input weight. Nothing here is out of spec, but the combination is far "
            "outside the range most runtimes are tested on."
        ),
        "hypothesis": "membrane goes negative before any spike is produced",
        "graph": {
            "name": "unusual-params",
            "dt_s": 0.001,
            "nodes": {
                "in": {"type": "Input", "shape": [2], "size": 2},
                "fc": {
                    "type": "Affine",
                    "size": 2,
                    "weight": [[2.5, -1.5], [-1.5, 2.5]],
                    "bias": [-0.2, -0.2],
                },
                "lif": {
                    "type": "LIF",
                    "size": 2,
                    "tau": 0.003,
                    "r": 3.5,
                    "v_leak": -0.7,
                    "v_threshold": 0.6,
                },
                "out": {"type": "Output", "size": 2},
            },
            "edges": [["in", "fc"], ["fc", "lif"], ["lif", "out"]],
        },
        "pattern": [(1, 0), (3, 1)],
        "intervention": {
            "kind": "parameter_probe",
            "detail": "v_leak=-0.7, r=3.5, mixed-sign weights",
            "applies_to": "LIF",
        },
    },
    {
        "id": "nir-partial-coverage-li",
        "name": "runtime-specific coverage gap",
        "class": "coverage_gap",
        "description": (
            "A non-spiking leaky integrator. One runtime implements LI and the other "
            "declares it unsupported, which is the ordinary case of two backends "
            "covering different slices of the same specification."
        ),
        "hypothesis": "one runtime executes and one returns a coverage diagnostic",
        "graph": {
            "name": "leaky-integrator",
            "dt_s": 0.001,
            "nodes": {
                "in": {"type": "Input", "shape": [2], "size": 2},
                "li": {"type": "LI", "size": 2, "tau": 0.005, "r": 1.0, "v_leak": 0.0},
                "out": {"type": "Output", "size": 2},
            },
            "edges": [["in", "li"], ["li", "out"]],
        },
        "pattern": [(1, 0), (2, 0)],
        "intervention": {
            "kind": "coverage_probe",
            "detail": "LI is supported by nir_reference_v1 only",
            "applies_to": "nodes.li",
        },
    },
    {
        "id": "nir-unsupported-cubalif",
        "name": "intentionally unsupported CubaLIF",
        "class": "unsupported",
        "description": (
            "A current-based LIF, which neither in-repo runtime implements. The record "
            "exists to prove that an unsupported construct produces a diagnostic with a "
            "reason code rather than a silently substituted approximation."
        ),
        "hypothesis": "both runtimes return UNSUPPORTED_CONSTRUCT",
        "graph": {
            "name": "cuba-lif",
            "dt_s": 0.001,
            "nodes": {
                "in": {"type": "Input", "shape": [2], "size": 2},
                "cuba": {
                    "type": "CubaLIF",
                    "size": 2,
                    "tau_mem": 0.01,
                    "tau_syn": 0.005,
                    "r": 1.0,
                    "v_leak": 0.0,
                    "v_threshold": 1.0,
                },
                "out": {"type": "Output", "size": 2},
            },
            "edges": [["in", "cuba"], ["cuba", "out"]],
        },
        "pattern": [(1, 0), (2, 0)],
        "intervention": {
            "kind": "unsupported_probe",
            "detail": "CubaLIF is outside both runtimes' declared coverage",
            "applies_to": "nodes.cuba",
        },
    },
)


def build_scenario(spec, steps=10):
    graph = json.loads(json.dumps(spec["graph"]))
    channels = graph["nodes"]["in"]["shape"][0]
    stimulus = _stimulus(f"{spec['id']}-stimulus", steps, channels, spec["pattern"])
    return {
        "id": spec["id"],
        "name": spec["name"],
        "family": FACTORY_SLUG,
        "class": spec["class"],
        "description": spec["description"],
        "hypothesis": spec["hypothesis"],
        "graph": graph,
        "graph_sha256": digest(graph),
        "structure_digest": structural_digest(graph),
        "stimulus": stimulus,
        "input_fixture": {
            "name": stimulus["name"],
            "steps": stimulus["steps"],
            "channels": stimulus["channels"],
            "sha256": digest(stimulus["events"]),
        },
        "intervention": spec["intervention"],
    }


def build_scenarios(steps=10):
    return [build_scenario(spec, steps=steps) for spec in GRAPH_SPECS]


# ── Execution across runtimes ─────────────────────────────────────────


def execute_runtime(runtime, scenario):
    """Run one runtime and return its entry, executed or not."""
    entry = {
        "runtime": runtime.name,
        "runtime_class": runtime.runtime_class,
        "conventions": dict(getattr(runtime, "conventions", {})),
        "supported_types": list(getattr(runtime, "supported_types", ())),
        "status": None,
    }
    status = runtime.availability()
    if not status["available"]:
        entry["status"] = STATUS_UNAVAILABLE
        entry["reason_code"] = status["reason_code"]
        entry["detail"] = status["detail"]
        return entry
    # Parse/write evidence belongs to the runtime adapter that performed it.
    # A module-level JSON round trip copied onto every entry would agree by
    # construction while proving nothing about either runtime boundary.
    entry["roundtrip"] = runtime.roundtrip_graph(scenario["graph"])
    try:
        outputs = runtime.execute(scenario["graph"], scenario["stimulus"])
    except UnsupportedConstruct as exc:
        entry["status"] = STATUS_UNSUPPORTED
        entry["reason_code"] = "UNSUPPORTED_CONSTRUCT"
        entry["detail"] = exc.detail
        entry["unsupported_node"] = exc.node
        entry["unsupported_type"] = exc.node_type
        return entry
    except (GraphError, RuntimeUnavailable) as exc:
        entry["status"] = STATUS_UNAVAILABLE
        entry["reason_code"] = getattr(exc, "reason_code", "RUNTIME_GRAPH_ERROR")
        entry["detail"] = str(exc)
        return entry
    entry["status"] = STATUS_EXECUTED
    entry["outputs"] = outputs
    entry["output_digest"] = digest(
        {"trace": outputs["output_trace"], "events": outputs["spike_events"]}
    )
    return entry


def _executed(entries):
    return [
        entry
        for entry in entries
        if isinstance(entry, dict) and entry.get("status") == STATUS_EXECUTED
    ]


def convention_delta(entries):
    """Which declared conventions differ between the executed runtimes."""
    executed = _executed(entries)
    keys = set()
    for entry in executed:
        keys.update(entry.get("conventions") or {})
    delta = []
    for key in sorted(keys):
        values = {
            entry["runtime"]: (entry.get("conventions") or {}).get(key)
            for entry in executed
        }
        if len(set(values.values())) > 1:
            delta.append({"convention": key, "values": values})
    return delta


CONVENTION_REASON = {
    "reset": "DIVERGENCE_RESET_CONVENTION",
    "delay_unit": "DIVERGENCE_DELAY_SEMANTICS",
    "cycle_break_order": "DIVERGENCE_RECURRENT_ORDER",
}


def relevant_conventions(graph, entries):
    """Which differing conventions this graph can actually exercise.

    Two runtimes may declare several different conventions while a given graph
    contains no construct that any of them govern. Listing all of them as
    candidate causes of an observed divergence would be noise dressed as
    analysis, so a convention is only a candidate when the graph contains the
    construct it applies to and, for reset, when a spike actually fired.
    """
    nodes = (graph or {}).get("nodes") or {}
    types = {node.get("type") for node in nodes.values()}
    executed = _executed(entries)
    spiked = any(
        ((entry.get("outputs") or {}).get("spike_count") or 0) > 0 for entry in executed
    )
    has_recurrence = any(
        (entry.get("outputs") or {}).get("recurrent_edges") for entry in executed
    )
    relevant = set()
    if types & {"LIF", "IF"} and spiked:
        relevant.add("reset")
    if "Delay" in types:
        relevant.add("delay_unit")
    if has_recurrence:
        relevant.add("cycle_break_order")
    return relevant


def compare_runtimes(scenario, entries):
    """Compare every executed runtime pairwise and classify what differs."""
    executed = _executed(entries)
    unsupported = [
        {
            "runtime": entry["runtime"],
            "reason_code": entry.get("reason_code"),
            "node": entry.get("unsupported_node"),
            "node_type": entry.get("unsupported_type"),
            "detail": entry.get("detail"),
        }
        for entry in entries
        if entry["status"] == STATUS_UNSUPPORTED
    ]
    unavailable = [
        {
            "runtime": entry["runtime"],
            "runtime_class": entry["runtime_class"],
            "reason_code": entry.get("reason_code"),
            "detail": entry.get("detail"),
        }
        for entry in entries
        if entry["status"] == STATUS_UNAVAILABLE
    ]

    roundtrip_block = {
        "per_runtime": {
            entry["runtime"]: entry.get("roundtrip")
            for entry in entries
            if entry.get("roundtrip") is not None
        },
    }
    roundtrip_block["agree"] = all(
        value and value.get("parse_ok") and value.get("canonical_stable")
        and value.get("structure_stable")
        for value in roundtrip_block["per_runtime"].values()
    ) if roundtrip_block["per_runtime"] else False

    structure_digests = {
        entry["runtime"]: (entry.get("roundtrip") or {}).get("structure_digest")
        for entry in entries
        if entry.get("roundtrip") is not None
    }
    structure_block = {
        "digests": structure_digests,
        "declared": scenario["structure_digest"],
        "agree": (
            len(set(structure_digests.values())) <= 1
            and all(
                value == scenario["structure_digest"] for value in structure_digests.values()
            )
        )
        if structure_digests
        else False,
    }

    pairs = []
    for index_a in range(len(executed)):
        for index_b in range(index_a + 1, len(executed)):
            pairs.append(_compare_pair(executed[index_a], executed[index_b]))

    delta = convention_delta(entries)
    output_agree = all(pair["agree"] for pair in pairs) if pairs else None
    state_agree = (
        all(pair["state_agree"] for pair in pairs) if pairs else None
    )
    relevant = relevant_conventions(scenario.get("graph"), entries)
    candidate_causes = []
    if output_agree is False or state_agree is False:
        for item in delta:
            code = CONVENTION_REASON.get(item["convention"])
            if code and item["convention"] in relevant:
                candidate_causes.append(code)

    return {
        "executed_runtimes": [entry["runtime"] for entry in executed],
        "executed_count": len(executed),
        "parse_write_parity": roundtrip_block,
        "structure_parity": structure_block,
        "output_parity": {
            "comparable": bool(pairs),
            "agree": output_agree,
            "pairs": pairs,
            "tolerance": NUMERIC_TOL,
        },
        "state_parity": {
            "comparable": bool(pairs),
            "agree": state_agree,
            "note": (
                "internal membrane state at the end of the window. It can diverge while "
                "the event outputs agree, which means the agreement may not survive a "
                "longer stimulus"
            ),
        },
        "unsupported": unsupported,
        "unavailable": unavailable,
        "convention_delta": delta,
        "attribution": {
            "candidate_reason_codes": sorted(set(candidate_causes)),
            "relevant_conventions": sorted(relevant),
            "basis": (
                "declared convention differences that this graph actually exercises; a "
                "candidate explanation for the observed divergence, not a proven cause"
            ),
        },
    }


def _state_error(entry_a, entry_b):
    """Largest end-of-window membrane difference across shared nodes.

    Returns ``(max_error, comparable)``. Nodes present on only one side make
    the comparison incomparable rather than silently partial.
    """
    state_a = (entry_a.get("outputs") or {}).get("final_membrane") or {}
    state_b = (entry_b.get("outputs") or {}).get("final_membrane") or {}
    if set(state_a) != set(state_b):
        return None, False
    max_error = 0.0
    for name, blob_a in state_a.items():
        values_a = blob_a.get("v") or []
        values_b = (state_b[name] or {}).get("v") or []
        if len(values_a) != len(values_b):
            return None, False
        for value_a, value_b in zip(values_a, values_b):
            max_error = max(max_error, abs(value_a - value_b))
    return max_error, True


def _compare_pair(entry_a, entry_b):
    # Executed entries are shape-checked by _check_runtimes before validation
    # reaches here, but compare_runtimes is also called on freshly generated
    # entries, so missing keys degrade to "not comparable" rather than raising
    # and taking down the scan of a whole run directory.
    trace_a = (entry_a.get("outputs") or {}).get("output_trace")
    trace_b = (entry_b.get("outputs") or {}).get("output_trace")
    if not isinstance(trace_a, list) or not isinstance(trace_b, list):
        return {
            "a": entry_a.get("runtime"),
            "b": entry_b.get("runtime"),
            "agree": False,
            "shape_match": False,
            "spike_count_a": (entry_a.get("outputs") or {}).get("spike_count"),
            "spike_count_b": (entry_b.get("outputs") or {}).get("spike_count"),
            "digest_a": entry_a.get("output_digest"),
            "digest_b": entry_b.get("output_digest"),
            "state_comparable": False,
            "max_abs_state_error": None,
            "state_agree": False,
            "first_divergent_step": 0,
            "max_abs_error": None,
            "reason_codes": ["COMPARISON_MISMATCH"],
        }
    state_error, state_comparable = _state_error(entry_a, entry_b)
    pair = {
        "a": entry_a["runtime"],
        "b": entry_b["runtime"],
        "spike_count_a": entry_a["outputs"]["spike_count"],
        "spike_count_b": entry_b["outputs"]["spike_count"],
        "digest_a": entry_a["output_digest"],
        "digest_b": entry_b["output_digest"],
        "state_comparable": state_comparable,
        "max_abs_state_error": state_error,
        "state_agree": bool(state_comparable and state_error <= NUMERIC_TOL),
    }
    if len(trace_a) != len(trace_b) or (
        trace_a and trace_b and len(trace_a[0]) != len(trace_b[0])
    ):
        pair.update(
            {
                "agree": False,
                "shape_match": False,
                "first_divergent_step": 0,
                "max_abs_error": None,
                "reason_codes": ["COMPARISON_MISMATCH"],
            }
        )
        return pair
    first_divergent = None
    max_error = 0.0
    for step, (row_a, row_b) in enumerate(zip(trace_a, trace_b)):
        for value_a, value_b in zip(row_a, row_b):
            error = abs(value_a - value_b)
            max_error = max(max_error, error)
            if error > NUMERIC_TOL and first_divergent is None:
                first_divergent = step
    reason_codes = []
    events_a = entry_a["outputs"].get("spike_events")
    events_b = entry_b["outputs"].get("spike_events")
    events_agree = events_a == events_b
    if not events_agree:
        reason_codes.append("DIVERGENCE_EVENT_STREAM")
    if pair["spike_count_a"] != pair["spike_count_b"]:
        reason_codes.append("DIVERGENCE_SPIKE_COUNT")
    if max_error > NUMERIC_TOL:
        reason_codes.append("DIVERGENCE_NUMERIC_TOLERANCE")
    # Internal state divergence is reported but does not by itself make the
    # verdict a mismatch: the verdict is about the event stream that leaves the
    # graph, which is what a downstream consumer sees.
    if not pair["state_agree"]:
        reason_codes.append("DIVERGENCE_INTERNAL_STATE")
    behavioural = [
        code for code in reason_codes if code != "DIVERGENCE_INTERNAL_STATE"
    ]
    pair.update(
        {
            # Whole-output digests are evidence identifiers, not a numerical
            # comparator: traces that differ within NUMERIC_TOL legitimately
            # hash differently. Event streams remain exact, while numeric
            # traces use the declared tolerance.
            "agree": not behavioural and events_agree,
            "shape_match": True,
            "first_divergent_step": first_divergent,
            "max_abs_error": max_error,
            "reason_codes": sorted(set(reason_codes)),
        }
    )
    return pair


def verdict_for(comparison):
    """Derive the verdict and observed reason codes from a comparison block."""
    reason_codes = []
    if comparison["unsupported"]:
        reason_codes.append("UNSUPPORTED_CONSTRUCT")
    if comparison["unavailable"]:
        reason_codes.append("ORACLE_UNAVAILABLE")
    if comparison["parse_write_parity"]["per_runtime"] and not comparison[
        "parse_write_parity"
    ]["agree"]:
        for value in comparison["parse_write_parity"]["per_runtime"].values():
            if value and value.get("reason_code"):
                reason_codes.append(value["reason_code"])
    if comparison["structure_parity"]["digests"] and not comparison["structure_parity"][
        "agree"
    ]:
        reason_codes.append("STRUCTURE_DIGEST_MISMATCH")
    for pair in comparison["output_parity"]["pairs"]:
        reason_codes.extend(pair["reason_codes"])

    if comparison["executed_count"] < 2:
        reason_codes.append("NO_EXECUTED_RUNTIME_PAIR")
        verdict = (
            contract.VERDICT_UNSUPPORTED
            if comparison["unsupported"]
            else contract.VERDICT_INCONCLUSIVE
        )
        return verdict, sorted(set(reason_codes))
    agree = (
        comparison["output_parity"]["agree"]
        and comparison["structure_parity"]["agree"]
        and comparison["parse_write_parity"]["agree"]
    )
    return (
        contract.VERDICT_MATCH if agree else contract.VERDICT_MISMATCH,
        sorted(set(reason_codes)),
    )


# ── Record construction ───────────────────────────────────────────────


def _evidence_scope(entries):
    executed = [entry["runtime"] for entry in _executed(entries)]
    if len(executed) >= 2:
        execution = f"executed in-repo runtimes {executed!r}"
    elif len(executed) == 1:
        execution = f"only one in-repo runtime executed: {executed[0]!r}"
    else:
        execution = "no in-repo runtime executed this graph"
    return (
        f"{execution}; nir-rs and the other upstream NIR runtimes were unavailable, "
        "so this record is evidence only about the runtimes and diagnostics that "
        "actually executed"
    )


def build_record(scenario, entries, round_number):
    comparison = compare_runtimes(scenario, entries)
    verdict, reason_codes = verdict_for(comparison)
    executed = _executed(entries)
    prediction = {
        "source": "generator",
        "authoritative": False,
        "hypothesis": scenario["hypothesis"],
        "expected_verdict": _expected_verdict(scenario["class"]),
    }
    record = {
        "id": f"{scenario['id']}-r{round_number:02d}",
        "record_kind": RECORD_KIND,
        "dataset": contract.DATASET_FOR_KIND[RECORD_KIND],
        "schema_version": SCHEMA_VERSION,
        # Deep-copied so no two records (and no two fields of one record) share
        # a mutable sub-object: an edit to one would otherwise silently rewrite
        # the other, which is precisely the failure mode these records catch.
        "generator": copy.deepcopy(GENERATOR_BLOCK),
        "scenario": {
            "id": scenario["id"],
            "name": scenario["name"],
            "family": scenario["family"],
            "class": scenario["class"],
            "description": scenario["description"],
            "graph": scenario["graph"],
            "graph_sha256": scenario["graph_sha256"],
            "structure_digest": scenario["structure_digest"],
            "stimulus": scenario["stimulus"],
            "input_fixture": copy.deepcopy(scenario["input_fixture"]),
        },
        "intervention": copy.deepcopy(scenario["intervention"]),
        "candidate_prediction": prediction,
        "oracle": {
            "pairing": "cross-runtime NIR execution",
            "runtimes": entries,
            "identical_input_fixture": True,
            "input_fixture": copy.deepcopy(scenario["input_fixture"]),
            "evidence_scope": _evidence_scope(entries),
        },
        "result": {
            "oracle_backed": True,
            "verdict": verdict,
            "reason_codes": reason_codes,
            "derived_from": [entry["output_digest"] for entry in executed],
            "comparison": comparison,
            "summary": _summarize(scenario, comparison, verdict),
        },
        "provenance": {
            "kind": "simulated",
            "tool": VALIDATOR,
            "tool_version": SCHEMA_VERSION,
            "contract_version": contract.CONTRACT_VERSION,
            "scenario_sha256": digest(
                {"graph": scenario["graph"], "stimulus": scenario["stimulus"]}
            ),
            "units": {"time": "timesteps", "dt": "s", "membrane": "V_model"},
        },
        "validation": {
            "validator": VALIDATOR,
            "validator_version": SCHEMA_VERSION,
            "checks": [
                "envelope_contract",
                "structure_digest_recomputed_from_graph",
                "in_repo_runtime_outputs_re_executed",
                "comparison_recomputed_from_outputs",
                "divergence_preserved",
            ],
            # No cached pass. A stored "validated" stamp is exactly what a
            # tampered record would forge, so the checks are named here and
            # re-run by the reader instead.
            "status": "revalidate_on_read",
        },
        "meta": {"round": round_number, "factory": FACTORY_SLUG},
    }
    if not executed:
        record["result"]["derived_from"] = [
            digest({"runtime": entry["runtime"], "reason": entry.get("reason_code")})
            for entry in entries
        ]
    return record


def _expected_verdict(graph_class):
    if graph_class == "unsupported":
        return contract.VERDICT_UNSUPPORTED
    if graph_class in ("feed_forward",):
        return contract.VERDICT_MATCH
    if graph_class == "coverage_gap":
        return contract.VERDICT_UNSUPPORTED
    return contract.VERDICT_MISMATCH


def _summarize(scenario, comparison, verdict):
    executed = ", ".join(comparison["executed_runtimes"]) or "none"
    pairs = comparison["output_parity"]["pairs"]
    detail = ""
    if pairs:
        pair = pairs[0]
        detail = (
            f" spike counts {pair['spike_count_a']} vs {pair['spike_count_b']},"
            f" first divergent step {pair['first_divergent_step']},"
            f" max abs error {pair['max_abs_error']}."
        )
    elif comparison["unsupported"]:
        detail = " " + "; ".join(
            f"{item['runtime']} rejected {item['node_type']} at node {item['node']}"
            for item in comparison["unsupported"]
        ) + "."
    return (
        f"{scenario['name']}: executed on [{executed}]."
        f"{detail} verdict {verdict}."
    )


def generate_records(round_number=1, steps=10):
    records = []
    runtimes = (*IN_REPO_RUNTIMES, *UPSTREAM_RUNTIMES)
    for scenario in build_scenarios(steps=steps):
        entries = [execute_runtime(runtime, scenario) for runtime in runtimes]
        records.append(build_record(scenario, entries, round_number))
    return records


# ── Validation ────────────────────────────────────────────────────────

ALL_RUNTIMES = (*IN_REPO_RUNTIMES, *UPSTREAM_RUNTIMES)
EXPECTED_RUNTIME_NAMES = tuple(runtime.name for runtime in ALL_RUNTIMES)
_RUNTIME_BY_NAME = {runtime.name: runtime for runtime in IN_REPO_RUNTIMES}
_ALL_RUNTIME_BY_NAME = {runtime.name: runtime for runtime in ALL_RUNTIMES}


def _check_runtimes(record, where):
    errors = []
    runtimes = ((record.get("oracle") or {}).get("runtimes")) or []
    if not isinstance(runtimes, list) or not runtimes:
        return [f"{where}: oracle.runtimes must be a non-empty array [ENVELOPE_MALFORMED]"]
    names = [
        entry.get("runtime") if isinstance(entry, dict) else None for entry in runtimes
    ]
    if names != list(EXPECTED_RUNTIME_NAMES):
        errors.append(
            f"{where}: oracle.runtimes must contain the complete ordered inventory "
            f"{list(EXPECTED_RUNTIME_NAMES)!r}, got {names!r} "
            "[RUNTIME_STATUS_UNKNOWN]"
        )
    for entry in runtimes:
        name = entry.get("runtime") if isinstance(entry, dict) else None
        label = f"{where}.oracle.runtimes[{name!r}]"
        if not isinstance(entry, dict):
            errors.append(f"{where}: every runtime entry must be an object")
            continue
        expected_runtime = _ALL_RUNTIME_BY_NAME.get(name)
        if expected_runtime is None:
            errors.append(
                f"{label}: runtime is outside the declared inventory "
                "[RUNTIME_STATUS_UNKNOWN]"
            )
            continue
        expected_class = expected_runtime.runtime_class
        if entry.get("runtime_class") != expected_class:
            errors.append(
                f"{label}: runtime_class must be {expected_class!r}, got "
                f"{entry.get('runtime_class')!r} [RUNTIME_STATUS_UNKNOWN]"
            )
        expected_conventions = dict(getattr(expected_runtime, "conventions", {}))
        if entry.get("conventions") != expected_conventions:
            errors.append(
                f"{label}: conventions do not match the selected runtime implementation "
                "[COMPARISON_MISMATCH]"
            )
        expected_supported = list(getattr(expected_runtime, "supported_types", ()))
        if entry.get("supported_types") != expected_supported:
            errors.append(
                f"{label}: supported_types do not match the selected runtime "
                "implementation [COMPARISON_MISMATCH]"
            )
        if entry.get("status") not in RUNTIME_STATUSES:
            errors.append(
                f"{label}: status must be one of {list(RUNTIME_STATUSES)} "
                "[RUNTIME_STATUS_UNKNOWN]"
            )
        if entry.get("status") in (STATUS_UNAVAILABLE, STATUS_UNSUPPORTED):
            if entry.get("outputs") is not None or entry.get("output_digest") is not None:
                errors.append(
                    f"{label}: a runtime that did not execute must not carry outputs "
                    "[UNAVAILABLE_RUNTIME_HAS_OUTPUT]"
                )
            if not entry.get("reason_code"):
                errors.append(
                    f"{label}: a runtime that did not execute needs a reason code "
                    "[RUNTIME_STATUS_UNKNOWN]"
                )
        if entry.get("status") == STATUS_EXECUTED:
            outputs = entry.get("outputs")
            if not isinstance(outputs, dict):
                errors.append(f"{label}: an executed runtime must carry outputs")
            else:
                missing = [
                    key
                    for key in ("output_trace", "spike_events", "spike_count")
                    if key not in outputs
                ]
                if missing:
                    errors.append(
                        f"{label}: executed outputs are missing {missing} "
                        "[ENVELOPE_MALFORMED]"
                    )
            if not entry.get("output_digest"):
                errors.append(f"{label}: an executed runtime must carry an output digest")
            # An `executed` claim naming a runtime this validator cannot
            # re-execute is unfalsifiable. Without this, a record could name
            # nir_rs -- which is not installed -- as having produced a trace,
            # and nothing downstream would contradict it.
            if entry.get("runtime") not in _RUNTIME_BY_NAME:
                errors.append(
                    f"{label}: only runtimes this validator can re-execute may be "
                    f"marked {STATUS_EXECUTED!r}; {entry.get('runtime')!r} is not one "
                    f"of {sorted(_RUNTIME_BY_NAME)} [RUNTIME_STATUS_UNKNOWN]"
                )
        availability = expected_runtime.availability()
        if not availability["available"]:
            if entry.get("status") != STATUS_UNAVAILABLE:
                errors.append(
                    f"{label}: unavailable runtime must be recorded as "
                    f"{STATUS_UNAVAILABLE!r}, not {entry.get('status')!r} "
                    "[RUNTIME_STATUS_UNKNOWN]"
                )
            if entry.get("reason_code") not in {
                "RUNTIME_NOT_INSTALLED",
                "RUNTIME_ADAPTER_NOT_IMPLEMENTED",
            }:
                errors.append(
                    f"{label}: unavailable upstream runtime has an invalid reason_code "
                    "[RUNTIME_STATUS_UNKNOWN]"
                )
            if not isinstance(entry.get("detail"), str) or not entry["detail"].strip():
                errors.append(
                    f"{label}: unavailable upstream runtime needs a non-empty detail "
                    "[RUNTIME_STATUS_UNKNOWN]"
                )
            if entry.get("roundtrip") is not None:
                errors.append(
                    f"{label}: an unavailable runtime cannot claim parse/write evidence "
                    "[RUNTIME_STATUS_UNKNOWN]"
                )
    return errors


def _reexecute_in_repo_runtimes(record, where):
    """Re-run every in-repo runtime and compare digests with what was recorded.

    This is the anti-fabrication gate for this family: an output trace that the
    interpreter does not reproduce cannot survive validation. Runtimes that are
    not in-repo cannot be re-executed here, and the record says so rather than
    pretending they were checked.
    """
    errors = []
    scenario = record.get("scenario") or {}
    graph = scenario.get("graph")
    stimulus = scenario.get("stimulus")
    if not isinstance(graph, dict) or not isinstance(stimulus, dict):
        return [f"{where}: scenario.graph and scenario.stimulus are required"]
    for entry in ((record.get("oracle") or {}).get("runtimes")) or []:
        if not isinstance(entry, dict):
            continue
        runtime = _RUNTIME_BY_NAME.get(entry.get("runtime"))
        if runtime is None:
            continue
        label = f"{where}.oracle.runtimes[{entry.get('runtime')!r}]"
        try:
            outputs = runtime.execute(graph, stimulus)
        except UnsupportedConstruct as exc:
            if entry.get("status") != STATUS_UNSUPPORTED:
                errors.append(
                    f"{label}: runtime actually rejects this graph ({exc.node_type}) but "
                    f"the record says {entry.get('status')!r} [UNSUPPORTED_NOT_DIAGNOSED]"
                )
            expected_diagnostic = {
                "reason_code": "UNSUPPORTED_CONSTRUCT",
                "unsupported_node": exc.node,
                "unsupported_type": exc.node_type,
                "detail": exc.detail,
            }
            for key, expected in expected_diagnostic.items():
                if entry.get(key) != expected:
                    errors.append(
                        f"{label}: {key} recorded {entry.get(key)!r} but the runtime "
                        f"reported {expected!r} [UNSUPPORTED_NOT_DIAGNOSED]"
                    )
            fresh_roundtrip = runtime.roundtrip_graph(graph)
            if entry.get("roundtrip") != fresh_roundtrip:
                errors.append(
                    f"{label}: recorded parse/write parity does not match this runtime's "
                    "adapter [ROUNDTRIP_STRUCTURE_MISMATCH]"
                )
            continue
        except GraphError as exc:
            errors.append(f"{label}: graph is not executable: {exc}")
            continue
        if entry.get("status") != STATUS_EXECUTED:
            errors.append(
                f"{label}: runtime executes this graph but the record says "
                f"{entry.get('status')!r} [RUNTIME_STATUS_UNKNOWN]"
            )
            continue
        recomputed = digest(
            {"trace": outputs["output_trace"], "events": outputs["spike_events"]}
        )
        if entry.get("output_digest") != recomputed:
            errors.append(
                f"{label}: recorded output digest does not match a re-execution "
                "[COMPARISON_MISMATCH]"
            )
        # The whole outputs object, not just the trace: `spike_count` and
        # `final_membrane` also feed the comparison, so checking only the trace
        # would leave both editable -- and editing them deletes divergence
        # diagnostics from a family whose entire product is divergence.
        if entry.get("outputs") != outputs:
            differing = sorted(
                key
                for key in set(outputs) | set(entry.get("outputs") or {})
                if (entry.get("outputs") or {}).get(key) != outputs.get(key)
            )
            errors.append(
                f"{label}: recorded outputs do not match a re-execution; differing "
                f"fields {differing} [COMPARISON_MISMATCH]"
            )
        fresh_roundtrip = runtime.roundtrip_graph(graph)
        if entry.get("roundtrip") != fresh_roundtrip:
            errors.append(
                f"{label}: recorded parse/write parity does not match this runtime's "
                "adapter "
                "[ROUNDTRIP_STRUCTURE_MISMATCH]"
            )
    return errors


def validate_record(record, where):
    oracle = record.get("oracle") if isinstance(record, dict) else None
    digests = None
    if isinstance(oracle, dict) and isinstance(oracle.get("runtimes"), list):
        executed = [
            entry
            for entry in oracle["runtimes"]
            if isinstance(entry, dict) and entry.get("status") == STATUS_EXECUTED
        ]
        if executed:
            digests = [entry.get("output_digest") for entry in executed]
    errors = contract.check_envelope(record, where, oracle_digests=digests)
    if not isinstance(record, dict) or record.get("record_kind") != RECORD_KIND:
        return errors
    # A truthy non-dict `oracle` would sail past every `(x or {}).get(...)`
    # below and raise deep inside the comparison, so stop it here.
    if not isinstance(oracle, dict):
        return errors + [f"{where}: oracle must be an object [ENVELOPE_MALFORMED]"]
    errors += _check_runtimes(record, where)

    scenario = record.get("scenario") or {}
    if not isinstance(scenario, dict):
        return errors + [f"{where}: scenario must be an object [ENVELOPE_MALFORMED]"]
    graph = scenario.get("graph")
    graph_shape_valid = False
    if isinstance(graph, dict):
        try:
            fresh_structure_digest = structural_digest(graph)
        except GraphError as exc:
            errors.append(f"{where}: malformed scenario.graph: {exc} [ENVELOPE_MALFORMED]")
            fresh_structure_digest = None
        else:
            graph_shape_valid = True
        if (
            fresh_structure_digest is not None
            and scenario.get("structure_digest") != fresh_structure_digest
        ):
            errors.append(
                f"{where}: scenario.structure_digest does not match the recorded graph "
                "[STRUCTURE_DIGEST_MISMATCH]"
            )
        if scenario.get("graph_sha256") != digest(graph):
            errors.append(
                f"{where}: scenario.graph_sha256 does not match the recorded graph "
                "[STRUCTURE_DIGEST_MISMATCH]"
            )
    else:
        errors.append(f"{where}: scenario.graph must be an object [ENVELOPE_MALFORMED]")
    stimulus = scenario.get("stimulus")
    if isinstance(stimulus, dict):
        fixture = scenario.get("input_fixture") or {}
        oracle_fixture = oracle.get("input_fixture") or {}
        recomputed_fixture = digest(stimulus.get("events"))
        if not isinstance(fixture, dict) or fixture.get("sha256") != recomputed_fixture:
            errors.append(
                f"{where}: scenario.input_fixture.sha256 does not match the recorded "
                "stimulus [INPUT_FIXTURE_MISMATCH]"
            )
        if (
            not isinstance(oracle_fixture, dict)
            or oracle_fixture.get("sha256") != recomputed_fixture
        ):
            errors.append(
                f"{where}: oracle.input_fixture.sha256 does not match the executed "
                "stimulus [INPUT_FIXTURE_MISMATCH]"
            )
        if oracle.get("identical_input_fixture") is not True:
            errors.append(
                f"{where}: oracle.identical_input_fixture must be exactly true "
                "[INPUT_FIXTURE_MISMATCH]"
            )
    else:
        errors.append(
            f"{where}: scenario.stimulus must be an object [ENVELOPE_MALFORMED]"
        )
    runtimes = oracle.get("runtimes") or []
    if oracle.get("evidence_scope") != _evidence_scope(
        [entry for entry in runtimes if isinstance(entry, dict)]
    ):
        errors.append(
            f"{where}: oracle.evidence_scope does not describe the runtimes that "
            "actually executed [COMPARISON_MISMATCH]"
        )

    if not graph_shape_valid:
        return errors
    errors += _reexecute_in_repo_runtimes(record, where)
    if errors:
        return errors

    entries = oracle["runtimes"]
    recomputed = compare_runtimes(
        {"structure_digest": scenario.get("structure_digest"), "graph": graph}, entries
    )
    verdict, reason_codes = verdict_for(recomputed)
    result = record.get("result") or {}
    if not isinstance(result, dict):
        return errors + [f"{where}: result must be an object [ENVELOPE_MALFORMED]"]
    recorded = result.get("comparison")
    if not isinstance(recorded, dict):
        errors.append(f"{where}: result.comparison must be an object [COMPARISON_MISMATCH]")
    elif recorded != recomputed:
        errors.append(
            f"{where}: result.comparison does not exactly match the re-executed "
            "runtime evidence [COMPARISON_MISMATCH]"
        )
    if result.get("verdict") != verdict:
        errors.append(
            f"{where}: result.verdict is {result.get('verdict')!r} but the recorded "
            f"outputs support {verdict!r} [DIVERGENCE_SUPPRESSED]"
        )
    if result.get("reason_codes") != reason_codes:
        errors.append(
            f"{where}: result.reason_codes records {result.get('reason_codes')!r} but "
            f"re-execution gives {reason_codes!r} [DIVERGENCE_SUPPRESSED]"
        )
    if recomputed["executed_count"] >= 2 and recomputed["output_parity"]["agree"] is False:
        if result.get("verdict") == contract.VERDICT_MATCH:
            errors.append(
                f"{where}: outputs diverge but the verdict claims a match "
                "[DIVERGENCE_SUPPRESSED]"
            )
    expected_summary = _summarize(scenario, recomputed, verdict)
    if result.get("summary") != expected_summary:
        errors.append(
            f"{where}: result.summary is not derived from the re-executed comparison "
            "[COMPARISON_MISMATCH]"
        )
    return errors


def validate_records(records, source="record"):
    errors = []
    for index, record in enumerate(records, 1):
        errors += validate_record(record, f"{source}:{index}")
    return errors


# ── Training view ─────────────────────────────────────────────────────


def training_view(record):
    scenario = record.get("scenario") or {}
    result = record.get("result") or {}
    oracle = record.get("oracle") or {}
    runtimes = oracle.get("runtimes") or []
    targets = [
        f"{entry.get('runtime')}:{entry.get('status')}"
        for entry in runtimes
        if isinstance(entry, dict)
    ]
    executed = list((result.get("comparison") or {}).get("executed_runtimes") or [])
    if len(executed) >= 2:
        execution_claim = f"was executed across runtimes {executed!r}"
    elif len(executed) == 1:
        execution_claim = f"executed on only one runtime, {executed[0]!r}"
    else:
        execution_claim = "did not execute on any runtime"
    prompt = (
        f"NIR graph '{scenario.get('name')}' (class {scenario.get('class')}) "
        f"{execution_claim} against stimulus "
        f"{(scenario.get('input_fixture') or {}).get('sha256')}. "
        "What does the available evidence establish about runtime equivalence?"
    )
    completion = _summarize(
        scenario,
        result.get("comparison") or {},
        result.get("verdict"),
    )
    view = contract.build_training_view(record, prompt, completion, targets)
    view["graph_class"] = scenario.get("class")
    view["scenario_id"] = scenario.get("id")
    view["executed_runtimes"] = list(
        (result.get("comparison") or {}).get("executed_runtimes") or []
    )
    view["evidence_scope"] = oracle.get("evidence_scope")
    return view


def build_training_views(records, source="record"):
    validation_errors = validate_records(records, source=source)
    if validation_errors:
        return [], validation_errors
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


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("availability", help="report which runtimes can execute here")
    gen = sub.add_parser("generate", help="write one round of cross-runtime records")
    gen.add_argument("out_dir")
    gen.add_argument("--round", type=int, default=1)
    gen.add_argument("--steps", type=int, default=10)
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
        records = generate_records(round_number=args.round, steps=args.steps)
        errors = validate_records(records, source="generated")
        if errors:
            for error in errors:
                print("ERROR:", error, file=sys.stderr)
            print("nir_equivalence: refusing to write invalid records", file=sys.stderr)
            return 1
        out = Path(args.out_dir) / FACTORY_SLUG / f"batch-r{args.round:02d}.jsonl"
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
