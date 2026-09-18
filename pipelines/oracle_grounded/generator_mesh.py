"""Synaptic mesh scenario proposals."""


# --------------------------------------------------------------------------
# Family 3: mesh topology and delay interventions
# --------------------------------------------------------------------------

MESH_INTERVENTIONS = (
    "delay_change",
    "edge_removal",
    "sign_flip",
    "weight_change",
    "add_recurrent_edge",
)

_MESH_TEMPLATE = (
    ("N0", "N1", 1.15, 2.0),
    ("N0", "N2", 0.65, 5.0),
    ("N1", "N3", 0.70, 3.0),
    ("N2", "N3", 0.70, 2.0),
    ("N3", "N5", 1.20, 4.0),
    ("N1", "N4", 1.10, 6.0),
    ("N4", "N5", 0.60, 2.0),
    ("N2", "N4", -0.50, 3.0),
)


def propose_mesh_scenario(rng, duration_ms=140.0):
    edges = []
    for src, dst, weight, delay in _MESH_TEMPLATE:
        edges.append(
            {
                "src": src,
                "dst": dst,
                "weight": weight * rng.uniform(0.85, 1.15),
                "delay_ms": max(0.5, delay * rng.uniform(0.7, 1.4)),
            }
        )
    pulse_count = rng.randint(2, 4)
    interval = rng.uniform(4.0, 9.0)
    onset = rng.uniform(2.0, 8.0)
    return {
        "nodes": ["N0", "N1", "N2", "N3", "N4", "N5"],
        "edges": edges,
        "source": "N0",
        "sink": "N5",
        "stimulus": {
            "target": "N0",
            "pulse_count": pulse_count,
            "interval_ms": interval,
            "amplitude": rng.uniform(1.1, 1.4),
            "onset_ms": onset,
        },
        "duration_ms": duration_ms,
        "question": "How does the perturbation change propagation from N0 to N5?",
    }


def mesh_events(scenario):
    stimulus = scenario["stimulus"]
    return [
        {
            "target": stimulus["target"],
            "t_ms": stimulus["onset_ms"] + index * stimulus["interval_ms"],
            "amplitude": stimulus["amplitude"],
        }
        for index in range(int(stimulus["pulse_count"]))
    ]


def propose_mesh_intervention(rng, scenario):
    kind = rng.choice(MESH_INTERVENTIONS)
    edge_index = rng.randint(0, len(scenario["edges"]) - 1)
    edge = scenario["edges"][edge_index]
    if kind == "delay_change":
        payload = {"new_delay_ms": max(0.5, edge["delay_ms"] * rng.uniform(0.3, 3.0))}
    elif kind == "weight_change":
        payload = {"weight_factor": rng.uniform(0.3, 2.0)}
    elif kind == "add_recurrent_edge":
        payload = {
            "src": "N3",
            "dst": "N1",
            "weight": rng.uniform(0.5, 1.2),
            "delay_ms": rng.uniform(2.0, 9.0),
        }
    else:
        payload = {}
    return {
        "kind": kind,
        "edge_index": edge_index if kind != "add_recurrent_edge" else None,
        "edge": None if kind == "add_recurrent_edge" else dict(edge),
        "parameters": payload,
        "description": f"{kind} on edge {edge['src']}->{edge['dst']}"
        if kind != "add_recurrent_edge"
        else "add_recurrent_edge N3->N1",
    }


def apply_mesh_intervention(scenario, intervention):
    """Produce the perturbed edge list. Structural, not a measurement."""
    edges = [dict(edge) for edge in scenario["edges"]]
    kind = intervention["kind"]
    if kind == "add_recurrent_edge":
        edges.append(dict(intervention["parameters"]))
        return edges
    index = intervention["edge_index"]
    if kind == "edge_removal":
        edges.pop(index)
    elif kind == "delay_change":
        edges[index]["delay_ms"] = intervention["parameters"]["new_delay_ms"]
    elif kind == "sign_flip":
        edges[index]["weight"] = -edges[index]["weight"]
    elif kind == "weight_change":
        edges[index]["weight"] *= intervention["parameters"]["weight_factor"]
    else:
        raise ValueError(f"unknown mesh intervention: {kind}")
    return edges


def predict_mesh_effect(scenario, intervention):
    """Shortest-path guess over excitatory edges, ignoring all dynamics."""
    edges = apply_mesh_intervention(scenario, intervention)
    best = _shortest_excitatory_path(edges, scenario["source"], scenario["sink"])
    return {
        "kind": "non_authoritative_guess",
        "predicted_sink_reached": best is not None,
        "predicted_propagation_delay_ms": best,
        "basis": (
            "sum of delays along the shortest positive-weight path; ignores "
            "thresholds, summation and inhibition, and no simulation was run"
        ),
    }


def _shortest_excitatory_path(edges, source, sink):
    distances = {source: 0.0}
    # Bellman-Ford style relaxation; the graph is tiny and may be cyclic.
    for _ in range(len(edges) + 1):
        changed = False
        for edge in edges:
            if edge["weight"] <= 0 or edge["src"] not in distances:
                continue
            candidate = distances[edge["src"]] + edge["delay_ms"]
            if candidate < distances.get(edge["dst"], float("inf")) - 1e-12:
                distances[edge["dst"]] = candidate
                changed = True
        if not changed:
            break
    return distances.get(sink)
