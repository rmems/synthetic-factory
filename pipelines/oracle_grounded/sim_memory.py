"""Deterministic recurrent-memory reference simulation."""

import math
from .sim_common import ENERGY_PJ_PER_SPIKE
from .sim_mesh import mesh_node, simulate_mesh

# --------------------------------------------------------------------------
# Family 5 oracle: recurrent memory network (stand-in for a validated rSNN)
# --------------------------------------------------------------------------

MEMORY_DEFAULTS = {
    "loop_delay_ms": 10.0,
    "loop_weight": 1.2,
    "inhibition": 0.9,
    # readout_weight and gate_weight are chosen so that neither the loop drive
    # nor the probe burst can fire an output neuron alone: the loop asymptote
    # is readout_weight / (1 - exp(-loop_delay / output_tau)) and the probe
    # asymptote is gate_weight / (1 - exp(-probe_interval / output_tau)), both
    # below v_threshold = 1.0, while their sum clears it.
    "readout_weight": 0.40,
    "gate_weight": 0.19,
    "distractor_weight": 0.45,
    "latch_adaptation_b": 0.02,
    "latch_tau_w_ms": 60.0,
    "latch_tau_ms": 8.0,
    "output_tau_ms": 8.0,
    "cue_amplitude": 1.2,
    "probe_amplitude": 1.2,
    "reset_amplitude": 2.0,
    "probe_pulses": 15,
    "probe_interval_ms": 2.0,
    "response_window_ms": 45.0,
    "dt_ms": 0.5,
}


def memory_config(overrides=None):
    config = dict(MEMORY_DEFAULTS)
    if overrides:
        config.update(overrides)
    return config


def memory_network(config):
    """Two mutually inhibiting delay loops read out through a probe gate.

    A cue starts one loop reverberating. The loop's own spike-frequency
    adaptation is what eventually kills it, so retention is a measured
    property of the parameters rather than a hand-set label. The output
    neurons need the loop drive *and* the probe gate within one membrane time
    constant, so neither alone can produce a response.
    """
    latch = {
        "tau_ms": config["latch_tau_ms"],
        "adaptation_b": config["latch_adaptation_b"],
        "tau_w_ms": config["latch_tau_w_ms"],
        "t_refractory_ms": 2.0,
    }
    nodes = [
        mesh_node("MA", **latch),
        mesh_node("MB", **latch),
        mesh_node("D", tau_ms=5.0, t_refractory_ms=2.0),
        mesh_node("G", tau_ms=5.0, t_refractory_ms=1.5),
        mesh_node("OA", tau_ms=config["output_tau_ms"], t_refractory_ms=4.0),
        mesh_node("OB", tau_ms=config["output_tau_ms"], t_refractory_ms=4.0),
    ]
    loop_delay = config["loop_delay_ms"]
    edges = [
        {"src": "MA", "dst": "MA", "weight": config["loop_weight"], "delay_ms": loop_delay},
        {"src": "MB", "dst": "MB", "weight": config["loop_weight"], "delay_ms": loop_delay},
        {"src": "MA", "dst": "MB", "weight": -config["inhibition"], "delay_ms": 1.0},
        {"src": "MB", "dst": "MA", "weight": -config["inhibition"], "delay_ms": 1.0},
        {"src": "MA", "dst": "OA", "weight": config["readout_weight"], "delay_ms": 1.0},
        {"src": "MB", "dst": "OB", "weight": config["readout_weight"], "delay_ms": 1.0},
        {"src": "G", "dst": "OA", "weight": config["gate_weight"], "delay_ms": 1.0},
        {"src": "G", "dst": "OB", "weight": config["gate_weight"], "delay_ms": 1.0},
        {"src": "D", "dst": "MA", "weight": config["distractor_weight"], "delay_ms": 1.0},
        {"src": "D", "dst": "MB", "weight": config["distractor_weight"], "delay_ms": 1.0},
    ]
    return nodes, edges


def memory_events(task, config):
    """Translate a task description into external stimulation events."""
    events = []
    cue = task.get("cue")
    if cue in ("A", "B"):
        events.append(
            {
                "target": "MA" if cue == "A" else "MB",
                "t_ms": task["cue_ms"],
                "amplitude": config["cue_amplitude"],
            }
        )
    for time_ms in task.get("distractor_ms", ()):
        events.append({"target": "D", "t_ms": time_ms, "amplitude": config["cue_amplitude"]})
    # A reset drives both latches below the point where the next delayed loop
    # spike can re-fire them, so it genuinely clears the stored state.
    reset_ms = task.get("reset_ms")
    if reset_ms is not None:
        for target in ("MA", "MB"):
            events.append(
                {"target": target, "t_ms": reset_ms, "amplitude": -config["reset_amplitude"]}
            )
    # The probe is a short burst, not a single pulse: a single instantaneous
    # gate spike would only coincide with the loop drive at a lucky phase, so
    # a one-pulse probe would make the answer depend on probe timing rather
    # than on what is stored.
    for index in range(int(config["probe_pulses"])):
        events.append(
            {
                "target": "G",
                "t_ms": task["probe_ms"] + index * config["probe_interval_ms"],
                "amplitude": config["probe_amplitude"],
            }
        )
    events.sort(key=lambda item: (item["t_ms"], item["target"]))
    return events


def memory_response_from_counts(output_spike_counts):
    """Derive the categorical response from the retained OA/OB primitives.

    A single active readout selects its label.  Neither readout means no
    response; both readouts is an unresolved, ambiguous response and therefore
    also carries the neutral ``none`` label rather than choosing one by
    iteration order.
    """
    if not isinstance(output_spike_counts, dict):
        raise ValueError("output_spike_counts must be an object")
    if set(output_spike_counts) != {"OA", "OB"}:
        raise ValueError("output_spike_counts must contain exactly OA and OB")
    counts = {}
    for node_id in ("OA", "OB"):
        value = output_spike_counts[node_id]
        if (
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or (isinstance(value, float) and not math.isfinite(value))
            or value != math.trunc(value)
            or value < 0
        ):
            raise ValueError(f"output_spike_counts.{node_id} must be a non-negative integer")
        counts[node_id] = value
    active_a = counts["OA"] > 0
    active_b = counts["OB"] > 0
    if active_a and not active_b:
        return "A", False
    if active_b and not active_a:
        return "B", False
    return "none", active_a and active_b


def run_memory_task(task, config):
    """Simulate one delayed-dependency trial and read the network's answer."""
    nodes, edges = memory_network(config)
    events = memory_events(task, config)
    duration_ms = task["probe_ms"] + config["response_window_ms"] + 5.0
    result = simulate_mesh(nodes, edges, events, duration_ms, dt_ms=config["dt_ms"])
    probe_ms = task["probe_ms"]
    window_end = probe_ms + config["response_window_ms"]
    responses = []
    for node_id in ("OA", "OB"):
        for time_ms in result["spikes_by_node"][node_id]:
            if probe_ms <= time_ms <= window_end:
                responses.append((time_ms, node_id))
    responses.sort()
    # Retain exactly the primitive used for the categorical answer: output
    # spikes inside the declared response window.  Counting whole-trial spikes
    # here would let an unrelated pre/post-window event select a label whose
    # latency cannot be derived from the retained response evidence.
    output_spike_counts = {
        node_id: sum(1 for _time_ms, observed in responses if observed == node_id)
        for node_id in ("OA", "OB")
    }
    response, ambiguous = memory_response_from_counts(output_spike_counts)
    if response == "none":
        latency = None
    else:
        response_node = "OA" if response == "A" else "OB"
        response_time = next(time_ms for time_ms, node_id in responses if node_id == response_node)
        latency = response_time - probe_ms
    latch_alive = _latch_alive(result, probe_ms, config)
    return {
        "response": response,
        "response_latency_ms": latency,
        "response_ambiguous": ambiguous,
        "output_spike_counts": output_spike_counts,
        "memory_spike_counts": {
            "MA": len(result["spikes_by_node"]["MA"]),
            "MB": len(result["spikes_by_node"]["MB"]),
        },
        # Retain the primitive that actually supports the state-at-probe label.
        # A loop may keep spiking after the probe; the final trial spike cannot
        # establish whether it was alive when the probe arrived.
        "latch_last_spike_ms": {
            node_id: next(
                (
                    time_ms
                    for time_ms in reversed(result["spikes_by_node"][node_id])
                    if time_ms <= probe_ms
                ),
                None,
            )
            for node_id in ("MA", "MB")
        },
        "state_retained_at_probe": latch_alive,
        "total_spikes": result["total_spikes"],
        "energy_pJ": result["total_spikes"] * ENERGY_PJ_PER_SPIKE,
        "duration_ms": duration_ms,
        "spike_budget_exhausted": result["spike_budget_exhausted"],
    }


def _latch_alive(result, probe_ms, config):
    """A latch counts as alive if it spiked within one loop period of the probe."""
    horizon = config["loop_delay_ms"] * 1.5
    for node_id in ("MA", "MB"):
        for time_ms in result["spikes_by_node"][node_id]:
            if probe_ms - horizon <= time_ms <= probe_ms:
                return True
    return False
