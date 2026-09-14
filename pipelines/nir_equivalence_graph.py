#!/usr/bin/env python3
"""A NIR graph as a data structure: codec, structural digest, topology.

Knows nothing about runtimes, records or validation -- which is what makes the
round-trip check meaningful rather than circular.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from neuro_oracle import (  # noqa: E402
    canonical_json,
    digest,
)


class GraphError(ValueError):
    """A graph that is malformed rather than merely unsupported."""


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
    # GraphError and json.JSONDecodeError are ValueError subclasses, so a
    # malformed graph and an unparseable payload land in this arm too.
    except (TypeError, ValueError) as exc:
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
