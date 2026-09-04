"""Family 3: synaptic-delay-causal-trajectories  (oracle: synaptic-mesh).

A spiking mesh with per-edge conduction delays is run before and after one
edge intervention; the record keeps both trajectories and the causal delta
between them. The checks treat spike_counts and first_arrival_ms as primitive
evidence and re-derive everything else from them, and a reference record is
additionally authenticated by re-running the reference simulation.
"""

from . import canon, generators, oracles, sim
from .family_common import TIME_UNITS, _guess, _measurement_matches

MESH_UNITS = {
    "first_arrival_ms": TIME_UNITS,
    "propagation_delay_ms": TIME_UNITS,
    "propagation_delay_delta_ms": TIME_UNITS,
    "firing_order": "node ids ordered by first spike time",
    "downstream_activation": "node ids that spiked at least once",
    "spike_counts": "spikes",
    "duration_ms": TIME_UNITS,
}


def mesh_request(scenario, intervention):
    return {
        "configuration": {
            "duration_ms": scenario["duration_ms"],
            "dt_ms": 0.5,
            "node_defaults": dict(sim.MESH_NODE_DEFAULTS),
            "source": scenario["source"],
            "sink": scenario["sink"],
        },
        "data": {
            "nodes": list(scenario["nodes"]),
            "edges_before": [dict(edge) for edge in scenario["edges"]],
            "edges_after": generators.apply_mesh_intervention(scenario, intervention),
            "events": generators.mesh_events(scenario),
        },
    }


def _mesh_reference(request):
    config = request["configuration"]
    data = request["data"]
    nodes = [sim.mesh_node(node_id) for node_id in data["nodes"]]
    source, sink = config["source"], config["sink"]

    def run(edges):
        raw = sim.simulate_mesh(
            sim.MeshNetwork(nodes, edges),
            data["events"],
            config["duration_ms"],
            limits=sim.MeshLimits(dt_ms=config["dt_ms"]),
        )
        summary = sim.mesh_causal_summary(raw, source, sink)
        summary["spike_budget_exhausted"] = raw["spike_budget_exhausted"]
        summary["total_spikes"] = raw["total_spikes"]
        summary["energy_pJ"] = raw["total_spikes"] * sim.ENERGY_PJ_PER_SPIKE
        return summary

    before = run(data["edges_before"])
    after = run(data["edges_after"])
    measured = {
        "before": before,
        "after": after,
        "delta": sim.mesh_causal_delta(before, after),
    }
    return measured, MESH_UNITS


def _mesh_oracle(environ=None):
    return oracles.bind(
        runtime="synaptic-mesh",
        identity=oracles.OracleIdentity(
            oracle_id="mesh-ref",
            oracle_type="network-simulation",
            description=(
                "Delta-synapse spiking mesh with per-edge conduction delays and "
                "inhibition, standing in for synaptic-mesh plus a compatible runtime"
            ),
        ),
        reference_fn=_mesh_reference,
        environ=environ,
    )


def _mesh_propose(rng):
    scenario = generators.propose_mesh_scenario(rng)
    intervention = generators.propose_mesh_intervention(rng, scenario)
    return scenario, intervention, generators.predict_mesh_effect(scenario, intervention)


def _mesh_rerun_findings(record, measured, findings):
    """Authenticate a reference record against a re-run of the reference.

    spike_counts/first_arrival_ms are treated as primitive evidence by the
    per-side checks; everything else (total_spikes, energy_pJ, firing_order,
    ...) is only checked for consistency *with them*, not against an
    independent rerun. A reference record's trajectory is reproducible from
    oracle.configuration alone, so rerun it and compare directly. Named-
    runtime results are authenticated through their own reproduction path.
    """
    rerun_request = mesh_request(record["scenario"], record["intervention"])
    recomputed, _units = _mesh_reference(rerun_request)
    for side in ("before", "after"):
        if canon.normalize(measured[side]) != canon.normalize(recomputed[side]):
            findings.append(f"{side} does not match the rerun of the reference simulation")


def _mesh_endpoint_findings(record, side, state, findings):
    if state["source"] != record["scenario"]["source"]:
        findings.append(f"{side}.source does not match scenario.source")
    if state["sink"] != record["scenario"]["sink"]:
        findings.append(f"{side}.sink does not match scenario.sink")


def _mesh_shape_findings(record, side, state, findings):
    nodes = set(record["scenario"]["nodes"])
    if set(state["first_arrival_ms"]) != nodes:
        findings.append(f"{side}.first_arrival_ms keys do not match scenario.nodes")
    if set(state["spike_counts"]) != nodes:
        findings.append(f"{side}.spike_counts keys do not match scenario.nodes")
    unknown = [node for node in state["firing_order"] if node not in nodes]
    if unknown:
        findings.append(f"{side}.firing_order names unknown nodes: {unknown}")
    if len(set(state["firing_order"])) != len(state["firing_order"]):
        findings.append(f"{side}.firing_order repeats a node")


def _mesh_keys_complete(record, state):
    nodes = set(record["scenario"]["nodes"])
    return set(state["first_arrival_ms"]) == nodes and set(state["spike_counts"]) == nodes


def _mesh_node_findings(record, side, state, findings):
    arrivals = state["first_arrival_ms"]
    counts = state["spike_counts"]
    for node in record["scenario"]["nodes"]:
        fired = counts[node] > 0
        if (arrivals[node] is not None) is not fired:
            findings.append(f"{side}.first_arrival_ms[{node}] disagrees with spike_counts")
        arrival = arrivals[node]
        if arrival is not None and not 0 <= arrival < record["scenario"]["duration_ms"]:
            findings.append(
                f"{side}.first_arrival_ms[{node}] lies outside the simulated duration"
            )


def _mesh_rollup_findings(record, side, state, findings):
    node_order = record["scenario"]["nodes"]
    arrivals = state["first_arrival_ms"]
    counts = state["spike_counts"]
    expected_order = sorted(
        (node for node in node_order if arrivals[node] is not None),
        key=lambda node: (arrivals[node], node),
    )
    if state["firing_order"] != expected_order:
        findings.append(f"{side}.firing_order does not match first_arrival_ms")
    expected_activation = [node for node in node_order if counts[node] > 0]
    if state["downstream_activation"] != expected_activation:
        findings.append(f"{side}.downstream_activation does not match spike_counts")
    expected_total = sum(counts.values())
    if state["total_spikes"] != expected_total:
        findings.append(f"{side}.total_spikes does not match spike_counts")
    expected_energy = expected_total * sim.ENERGY_PJ_PER_SPIKE
    if not _measurement_matches(state["energy_pJ"], expected_energy):
        findings.append(f"{side}.energy_pJ does not match total_spikes")


def _mesh_tail_findings(record, side, state, findings):
    sink = record["scenario"]["sink"]
    reached = state["first_arrival_ms"].get(sink) is not None
    if reached != state["sink_reached"]:
        findings.append(f"{side}.sink_reached disagrees with first_arrival_ms[{sink}]")
    if state["spike_budget_exhausted"]:
        findings.append(f"{side} hit the spike budget; the trajectory is truncated")
    delay = state["propagation_delay_ms"]
    source_time = state["first_arrival_ms"].get(record["scenario"]["source"])
    sink_time = state["first_arrival_ms"].get(sink)
    expected_delay = (
        None if source_time is None or sink_time is None else sink_time - source_time
    )
    if not _measurement_matches(delay, expected_delay):
        findings.append(f"{side}.propagation_delay_ms does not match sink minus source arrival")


def _mesh_side_findings(record, side, state, findings):
    _mesh_endpoint_findings(record, side, state, findings)
    _mesh_shape_findings(record, side, state, findings)
    if _mesh_keys_complete(record, state):
        _mesh_node_findings(record, side, state, findings)
        _mesh_rollup_findings(record, side, state, findings)
    _mesh_tail_findings(record, side, state, findings)


def _mesh_delta_findings(measured, findings):
    delta = measured["delta"]
    expected_delta = sim.mesh_causal_delta(measured["before"], measured["after"])
    for field, expected in expected_delta.items():
        if not _measurement_matches(delta.get(field), expected):
            findings.append(
                f"delta.{field} does not match the value derived from before/after states"
            )
    before_delay = measured["before"]["propagation_delay_ms"]
    after_delay = measured["after"]["propagation_delay_ms"]
    expected_delay_delta = (
        None if before_delay is None or after_delay is None else after_delay - before_delay
    )
    if not _measurement_matches(delta.get("propagation_delay_delta_ms"), expected_delay_delta):
        findings.append("delta.propagation_delay_delta_ms does not match the before/after delays")


def _mesh_checks(record):
    measured = record["result"]["measured"]
    findings = []
    if record["oracle"]["implementation"] != "named-runtime":
        _mesh_rerun_findings(record, measured, findings)
    for side in ("before", "after"):
        _mesh_side_findings(record, side, measured[side], findings)
    _mesh_delta_findings(measured, findings)
    return findings


def _score_mesh(record):
    predicted = _guess(record, "predicted_sink_reached")
    if predicted is None:
        return None
    return predicted == record["result"]["measured"]["after"]["sink_reached"]
