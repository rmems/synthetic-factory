#!/usr/bin/env python3
"""The graph catalog: the declarative scenarios and their stimuli.

Each entry names a construct implementations tend to treat differently --
reset convention, delay units, recurrent cycle order, boundary parameters --
and spells the graph out rather than deriving it.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

_PIPELINES = Path(__file__).resolve().parent

if __package__:
    # Import-twin helpers join the package import lock; import-order tests cover this edge.
    from . import _assert_direct_sibling, _expose_package_sibling  # pylint: disable=cyclic-import

    _assert_direct_sibling("nir_equivalence_catalog")
    from .neuro_oracle import digest  # noqa: E402
    from .nir_equivalence_graph import structural_digest  # noqa: E402
    from .nir_equivalence_terms import FACTORY_SLUG  # noqa: E402
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "nir_equivalence_catalog"
    )
    if str(_PIPELINES) not in sys.path:
        sys.path.insert(0, str(_PIPELINES))
    from neuro_oracle import digest  # noqa: E402
    from nir_equivalence_graph import structural_digest  # noqa: E402
    from nir_equivalence_terms import FACTORY_SLUG  # noqa: E402

def _catalog_digest():
    """Digest of the graph catalog identity (ids + classes + graphs)."""
    catalog = [
        {
            "id": scenario["id"],
            "name": scenario["name"],
            "family": scenario["family"],
            "class": scenario["class"],
            "graph": scenario["graph"],
        }
        for scenario in build_scenarios(steps=10)
    ]
    return digest({"factory": FACTORY_SLUG, "catalog": catalog})


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

_GRAPH_CATALOG_BY_ID = {
    spec["id"]: {
        "name": spec["name"],
        "family": FACTORY_SLUG,
        "class": spec["class"],
        "description": spec["description"],
        "hypothesis": spec["hypothesis"],
        "graph_sha256": digest(spec["graph"]),
        "channels": spec["graph"]["nodes"]["in"]["shape"][0],
        "pattern": tuple(spec["pattern"]),
        "intervention": copy.deepcopy(spec["intervention"]),
    }
    for spec in GRAPH_SPECS
}


def _catalog_entry(scenario_id):
    if not isinstance(scenario_id, str):
        return None
    return _GRAPH_CATALOG_BY_ID.get(scenario_id)


def _catalog_stimulus(scenario_id, steps):
    catalog = _catalog_entry(scenario_id)
    if (
        catalog is None
        or not isinstance(steps, int)
        or isinstance(steps, bool)
        or steps < 1
    ):
        return None
    return _stimulus(
        f"{scenario_id}-stimulus",
        steps,
        catalog["channels"],
        catalog["pattern"],
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


# The shortest window that still exercises every catalogued divergence.
# Measured, not derived: below six steps the delay-semantics and
# reset-convention scenarios have not reached the step where the two
# runtimes disagree, so a shorter round reports their designed mismatch as
# a match -- and validates, because each verdict is true of its window.
# `test_shorter_windows_are_refused_at_generation` pins the boundary.
MINIMUM_STEPS = 6


def build_scenarios(steps=10):
    if not isinstance(steps, int) or isinstance(steps, bool) or steps < MINIMUM_STEPS:
        raise ValueError(
            f"steps must be an integer >= {MINIMUM_STEPS}; a shorter window reports "
            "catalogued divergences as matches"
        )
    return [build_scenario(spec, steps=steps) for spec in GRAPH_SPECS]


if __package__:
    _expose_package_sibling(__name__)
