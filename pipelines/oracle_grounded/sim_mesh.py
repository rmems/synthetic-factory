"""Families 3 and 5 oracle: delayed spiking mesh (stand-in for ``synaptic-mesh``).

A delta-synapse LIF network with per-edge conduction delays, plus the causal
summaries that turn a run into the arrival/order/reach/delay facts the mesh
family stores. Every function is pure and deterministic: same inputs, same
floats.
"""

from dataclasses import dataclass

from .sim_core import optional_delta

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


@dataclass(frozen=True)
class MeshNetwork:
    """The static topology of one mesh run: node dicts plus delayed edges."""

    nodes: list
    edges: list


@dataclass(frozen=True)
class MeshLimits:
    """Integration step and the spike budget that bounds a runaway network."""

    dt_ms: float = 0.5
    max_spikes: int = 4000


def _initial_cells(nodes):
    """Per-node integration state, defaults merged under the node overrides."""
    state = {}
    for node in nodes:
        merged = dict(MESH_NODE_DEFAULTS)
        merged.update(node)
        merged["v"] = merged["v_rest"]
        merged["w"] = 0.0
        merged["refractory_left"] = 0
        merged["spikes"] = []
        state[node["id"]] = merged
    return state


def _outgoing_edges(edges, state, order):
    """Edges grouped by source node, validated against the known nodes."""
    for edge in edges:
        if edge["src"] not in state or edge["dst"] not in state:
            raise ValueError(f"edge references unknown node: {edge}")
    outgoing = {node_id: [] for node_id in order}
    for edge in edges:
        outgoing[edge["src"]].append(edge)
    return outgoing


class _MeshSim:
    """Mutable state of one mesh integration, advanced phase by phase.

    Each step, in this order: expire refractory, leak, deliver every injection
    scheduled for this step, decay adaptation, then test threshold. A spike at
    step *t* on edge (src -> dst, delay d) schedules ``weight`` into *dst* at
    ``t + round(d/dt)``, so a self-edge is a reverberating loop whose lifetime
    is set by the loop weight against the adapting threshold.
    """

    def __init__(self, network, steps, dt_ms):
        self.steps = steps
        self.dt_ms = dt_ms
        self.order = [node["id"] for node in network.nodes]
        self.state = _initial_cells(network.nodes)
        self.outgoing = _outgoing_edges(network.edges, self.state, self.order)
        self.pending = {}
        self.total_spikes = 0

    def schedule(self, step, node_id, amount):
        if 0 <= step < self.steps:
            self.pending.setdefault(step, []).append((node_id, amount))

    def add_events(self, events):
        for event in events:
            if event["target"] not in self.state:
                raise ValueError(f"event references unknown node: {event}")
            self.schedule(
                int(round(event["t_ms"] / self.dt_ms)), event["target"], event["amplitude"]
            )

    def _leak_phase(self):
        for node_id in self.order:
            cell = self.state[node_id]
            if cell["refractory_left"] > 0:
                cell["refractory_left"] -= 1
                cell["v"] = cell["v_reset"]
            else:
                cell["v"] += (-(cell["v"] - cell["v_rest"])) * (self.dt_ms / cell["tau_ms"])

    def _deliver_phase(self, step):
        for node_id, amount in self.pending.pop(step, ()):  # deterministic insertion order
            cell = self.state[node_id]
            if cell["refractory_left"] <= 0:
                cell["v"] += amount
                if cell["v"] < cell["v_floor"]:
                    cell["v"] = cell["v_floor"]

    def _fire_candidates(self):
        fired = []
        for node_id in self.order:
            cell = self.state[node_id]
            cell["w"] += (-cell["w"]) * (self.dt_ms / cell["tau_w_ms"])
            if cell["refractory_left"] <= 0 and cell["v"] >= cell["v_threshold"] + cell["w"]:
                fired.append(node_id)
        return fired

    def _fire_phase(self, step):
        for node_id in self._fire_candidates():
            cell = self.state[node_id]
            cell["spikes"].append(step * self.dt_ms)
            cell["v"] = cell["v_reset"]
            cell["w"] += cell["adaptation_b"]
            cell["refractory_left"] = max(0, int(round(cell["t_refractory_ms"] / self.dt_ms)))
            self.total_spikes += 1
            for edge in self.outgoing[node_id]:
                self.schedule(
                    step + int(round(edge["delay_ms"] / self.dt_ms)),
                    edge["dst"],
                    edge["weight"],
                )

    def run(self, max_spikes):
        """Advance every step; True when the spike budget was exhausted."""
        for step in range(self.steps):
            self._leak_phase()
            self._deliver_phase(step)
            self._fire_phase(step)
            if self.total_spikes > max_spikes:
                return True
        return False


def _firing_order(all_spikes):
    order = []
    for _time, node_id in all_spikes:
        if node_id not in order:
            order.append(node_id)
    return order


def _mesh_result(run, duration_ms, truncated):
    by_node = {node_id: run.state[node_id]["spikes"] for node_id in run.order}
    all_spikes = sorted(
        ((t, node_id) for node_id, times in by_node.items() for t in times),
        key=lambda item: (item[0], item[1]),
    )
    first_spike = {node_id: (times[0] if times else None) for node_id, times in by_node.items()}
    return {
        "nodes": run.order,
        "spikes_by_node": by_node,
        "spike_counts": {node_id: len(times) for node_id, times in by_node.items()},
        "first_spike_ms": first_spike,
        "firing_order": _firing_order(all_spikes),
        "activated": [node_id for node_id in run.order if by_node[node_id]],
        "total_spikes": run.total_spikes,
        "duration_ms": duration_ms,
        "dt_ms": run.dt_ms,
        "spike_budget_exhausted": truncated,
    }


def simulate_mesh(network, events, duration_ms, limits=None):
    """Run one delayed-mesh integration and summarise its spikes.

    ``network`` is a :class:`MeshNetwork`; ``limits`` a :class:`MeshLimits`
    (integration step and spike budget), defaulted when omitted. Hitting
    ``max_spikes`` is reported as ``spike_budget_exhausted`` rather than
    silently truncated.
    """
    if limits is None:
        limits = MeshLimits()
    steps = int(round(duration_ms / limits.dt_ms))
    run = _MeshSim(network, steps, limits.dt_ms)
    run.add_events(events)
    truncated = run.run(limits.max_spikes)
    return _mesh_result(run, duration_ms, truncated)


def mesh_causal_summary(result, source, sink):
    """Propagation targets the issue names: arrival, order, reach, delay."""
    first = result["first_spike_ms"]
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
        "propagation_delay_delta_ms": optional_delta(
            after["propagation_delay_ms"], before["propagation_delay_ms"]
        ),
        "sink_reached_before": before["sink_reached"],
        "sink_reached_after": after["sink_reached"],
        "sink_reachability_changed": before["sink_reached"] != after["sink_reached"],
    }
