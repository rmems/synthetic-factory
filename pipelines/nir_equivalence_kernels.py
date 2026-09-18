#!/usr/bin/env python3
"""Per-node arithmetic: one timestep of one NIR node type.

The kernels the interpreter runs, away from the graph walking that decides
when to run them. Affine, delay and membrane integration are where a
convention actually bites -- reset mode, delay units, leak order -- so they
are worth reading without the traversal around them.
"""

from __future__ import annotations

import sys

if __package__:
    # Import-twin helpers join the package import lock; import-order tests cover this edge.
    from . import _assert_direct_sibling, _expose_package_sibling  # pylint: disable=cyclic-import

    _assert_direct_sibling("nir_equivalence_kernels")
    from .nir_equivalence_graph import (  # noqa: E402
        GraphError,
    )
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "nir_equivalence_kernels"
    )
    from nir_equivalence_graph import (  # noqa: E402
        GraphError,
    )

def _sum_drive_parts(name, parts):
    if not parts:
        raise GraphError(f"node {name!r} has no inputs")
    width = len(parts[0])
    if any(len(part) != width for part in parts):
        raise GraphError(f"node {name!r} sums inputs of different widths")
    return [sum(part[k] for part in parts) for k in range(width)]


def _step_affine(name, node, drive):
    """Affine/Linear node: weight @ drive + bias."""
    weight = node["weight"]
    bias = node.get("bias") or [0.0] * len(weight)
    if any(len(row) != len(drive) for row in weight):
        raise GraphError(f"node {name!r}: weight columns do not match its input")
    return [
        sum(row[k] * drive[k] for k in range(len(drive))) + bias[index]
        for index, row in enumerate(weight)
    ]


def _step_delay(name, drive, state):
    """Delay node: emit the buffered value and push the current drive."""
    buffer = state[name]["buffer"]
    if not buffer:
        return list(drive)
    out = buffer.pop(0)
    buffer.append(list(drive))
    return out


def _integrate_membrane(named_node, membrane, drive, dt_s):
    """Advance a neuron's membrane one step, in place.

    IF integrates the drive directly; LIF/LI additionally leak toward v_leak
    over the node's tau.
    """
    name, node = named_node
    resistance = float(node.get("r", 1.0))
    if node["type"] == "IF":
        for index in range(len(membrane)):
            membrane[index] += resistance * drive[index]
        return
    tau = float(node["tau"])
    if tau <= 0:
        raise GraphError(f"node {name!r}: tau must be > 0")
    v_leak = float(node.get("v_leak", 0.0))
    factor = dt_s / tau
    for index in range(len(membrane)):
        membrane[index] += factor * (
            (v_leak - membrane[index]) + resistance * drive[index]
        )


if __package__:
    _expose_package_sibling(__name__)
