"""Deterministic delayed-spiking-mesh reference simulation."""

import math
from .sim_neuron import _optional_delta

# --------------------------------------------------------------------------
# Families 3 and 5 oracle: delayed spiking mesh (stand-in for `synaptic-mesh`)
# --------------------------------------------------------------------------

MESH_NODE_DEFAULTS = {
    "v_rest": 0.0,
    "v_reset": 0.0,
    "v_threshold": 1.0,
    "tau_ms": 8.0,
    "t_refractory_ms": 2.0,
    "adaptation_b": 0.0,
    "tau_w_ms": 50.0,
    "v_floor": -1.5,
}


def mesh_node(node_id, **overrides):
    node = dict(MESH_NODE_DEFAULTS)
    node.update(overrides)
    node["id"] = node_id
    return node


MAX_MESH_STEPS = 10_000


def _require_positive_mesh_number(value):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError("mesh duration and timestep must be finite positive numbers")
    try:
        valid = math.isfinite(value) and value > 0
    except OverflowError:
        valid = False
    if not valid:
        raise ValueError("mesh duration and timestep must be finite positive numbers")


def mesh_step_count(duration_ms, dt_ms=0.5, maximum=MAX_MESH_STEPS):
    """Bound direct mesh execution before state allocation or time stepping."""
    for value in (duration_ms, dt_ms):
        _require_positive_mesh_number(value)
    ratio = duration_ms / dt_ms
    if not math.isfinite(ratio) or ratio > maximum:
        raise ValueError(f"mesh simulation exceeds {maximum} steps")
    return int(round(ratio))


def _mesh_state(nodes):
    state = {}
    for node in nodes:
        merged = dict(MESH_NODE_DEFAULTS)
        merged.update(node)
        merged.update(v=merged["v_rest"], w=0.0, refractory_left=0, spikes=[])
        state[node["id"]] = merged
    return state


def _mesh_outgoing(edges, state, order):
    outgoing = {node_id: [] for node_id in order}
    for edge in edges:
        if edge["src"] not in state or edge["dst"] not in state:
            raise ValueError(f"edge references unknown node: {edge}")
        outgoing[edge["src"]].append(edge)
    return outgoing


def _schedule(pending, steps, step, node_id, amount):
    if 0 <= step < steps:
        pending.setdefault(step, []).append((node_id, amount))


def _schedule_events(events, state, pending, steps, dt_ms):
    for event in events:
        if event["target"] not in state:
            raise ValueError(f"event references unknown node: {event}")
        step = int(round(event["t_ms"] / dt_ms))
        _schedule(pending, steps, step, event["target"], event["amplitude"])


def _leak_mesh_state(state, order, dt_ms):
    for node_id in order:
        cell = state[node_id]
        if cell["refractory_left"] > 0:
            cell["refractory_left"] -= 1
            cell["v"] = min(cell["v"], cell["v_reset"])
        else:
            cell["v"] += (-(cell["v"] - cell["v_rest"])) * (dt_ms / cell["tau_ms"])


def _deliver_mesh_inputs(state, deliveries):
    for node_id, amount in deliveries:
        cell = state[node_id]
        if cell["refractory_left"] <= 0 or amount < 0:
            cell["v"] += amount
            if cell["v"] < cell["v_floor"]:
                cell["v"] = cell["v_floor"]


def _firing_nodes(state, order, dt_ms):
    fired = []
    for node_id in order:
        cell = state[node_id]
        cell["w"] += (-cell["w"]) * (dt_ms / cell["tau_w_ms"])
        threshold = cell["v_threshold"] + cell["w"]
        if cell["refractory_left"] <= 0 and cell["v"] >= threshold:
            fired.append(node_id)
    return fired


def _record_firings(state, outgoing, pending, steps, step, dt_ms, fired):
    for node_id in fired:
        cell = state[node_id]
        cell["spikes"].append(step * dt_ms)
        cell["v"] = cell["v_reset"]
        cell["w"] += cell["adaptation_b"]
        cell["refractory_left"] = max(0, int(round(cell["t_refractory_ms"] / dt_ms)))
        for edge in outgoing[node_id]:
            # The current step's pending inputs have already been consumed.
            # Deliver zero/sub-step delays on the next integration step rather
            # than silently scheduling them in the past.
            delay_steps = max(1, int(round(edge["delay_ms"] / dt_ms)))
            arrival = step + delay_steps
            _schedule(pending, steps, arrival, edge["dst"], edge["weight"])


def _mesh_summary(state, order, total_spikes, duration_ms, dt_ms, truncated):
    by_node = {node_id: state[node_id]["spikes"] for node_id in order}
    all_spikes = sorted(
        ((time_ms, node_id) for node_id, times in by_node.items() for time_ms in times),
        key=lambda item: (item[0], item[1]),
    )
    first_spike = {node_id: (times[0] if times else None) for node_id, times in by_node.items()}
    firing_order = list(dict.fromkeys(node_id for _time, node_id in all_spikes))
    return {
        "nodes": order,
        "spikes_by_node": by_node,
        "spike_counts": {node_id: len(times) for node_id, times in by_node.items()},
        "first_spike_ms": first_spike,
        "firing_order": firing_order,
        "activated": [node_id for node_id in order if by_node[node_id]],
        "total_spikes": total_spikes,
        "duration_ms": duration_ms,
        "dt_ms": dt_ms,
        "spike_budget_exhausted": truncated,
    }


def simulate_mesh(nodes, edges, events, duration_ms, dt_ms=0.5, max_spikes=4000):
    """Run a bounded delta-synapse LIF network with per-edge delays."""
    steps = mesh_step_count(duration_ms, dt_ms)
    order = [node["id"] for node in nodes]
    state = _mesh_state(nodes)
    outgoing = _mesh_outgoing(edges, state, order)
    pending = {}
    _schedule_events(events, state, pending, steps, dt_ms)
    total_spikes = 0
    truncated = False
    for step in range(steps):
        _leak_mesh_state(state, order, dt_ms)
        _deliver_mesh_inputs(state, pending.pop(step, ()))
        fired = _firing_nodes(state, order, dt_ms)
        _record_firings(state, outgoing, pending, steps, step, dt_ms, fired)
        total_spikes += len(fired)
        if total_spikes > max_spikes:
            truncated = True
            break
    return _mesh_summary(state, order, total_spikes, duration_ms, dt_ms, truncated)


def mesh_causal_summary(result, source, sink):
    """Propagation targets the issue names: arrival, order, reach, delay."""
    first = result["first_spike_ms"]
    for role, node_id in (("source", source), ("sink", sink)):
        if node_id not in first:
            raise ValueError(f"unknown {role} node {node_id!r}")
    source_time = first.get(source)
    sink_time = first.get(sink)
    if source_time is None or sink_time is None:
        propagation = None
    else:
        propagation = sink_time - source_time
    return {
        "source": source,
        "sink": sink,
        "first_arrival_ms": first,
        "firing_order": result["firing_order"],
        "downstream_activation": result["activated"],
        "propagation_delay_ms": propagation,
        "sink_reached": sink_time is not None,
        "spike_counts": result["spike_counts"],
    }


def mesh_causal_delta(before, after):
    activated_before = set(before["downstream_activation"])
    activated_after = set(after["downstream_activation"])
    order_changed = before["firing_order"] != after["firing_order"]
    return {
        "suppressed_nodes": sorted(activated_before - activated_after),
        "recruited_nodes": sorted(activated_after - activated_before),
        "firing_order_changed": order_changed,
        "propagation_delay_delta_ms": _optional_delta(
            after["propagation_delay_ms"], before["propagation_delay_ms"]
        ),
        "sink_reached_before": before["sink_reached"],
        "sink_reached_after": after["sink_reached"],
        "sink_reachability_changed": before["sink_reached"] != after["sink_reached"],
    }
