"""Generator side: scenarios, interventions, and non-authoritative guesses.

Everything in this module is what a generator (GPT-5.6-Sol, Fable, Grok, or
the deterministic stand-in used for fixtures) is allowed to author. None of it
is a measurement. The candidate predictions are cheap structural heuristics
deliberately kept separate from the simulators in ``sim.py``, so that scoring a
candidate against the oracle is a real test and not a tautology.

If a hosted model replaces these functions, the contract it must satisfy is
unchanged: emit ``scenario``, ``intervention``, and ``candidate_prediction``,
and never emit anything under ``result``.
"""

import math

from . import sim

GENERATOR_NAME = "deterministic-scenario-generator"
GENERATOR_VERSION = "1.0.0"

SIGNAL_FAMILIES = ("baseline", "burst", "drift", "outlier", "periodic", "sparse_events")
PERTURBATIONS = ("none", "additive_noise", "dropout", "quantization", "gain_drift")


def generator_block(seed, label, model=None):
    """The provenance block for whoever proposed the scenario."""
    return {
        "name": model or GENERATOR_NAME,
        "version": GENERATOR_VERSION,
        "role": "proposes scenarios, interventions, and non-authoritative predictions",
        "authoritative": False,
        "seed": int(seed),
        "label": label,
    }


# --------------------------------------------------------------------------
# Family 1: sensor scenarios for encoder comparison
# --------------------------------------------------------------------------


def make_signal(family, rng, sample_count, params):
    """A sensor trace in [0, 1], one value per sample period."""
    values = []
    if family == "baseline":
        level = params["level"]
        for _ in range(sample_count):
            values.append(level + params["noise"] * rng.symmetric_noise())
    elif family == "burst":
        burst_starts = params["burst_starts"]
        width = params["burst_width"]
        for index in range(sample_count):
            inside = any(start <= index < start + width for start in burst_starts)
            base = params["high"] if inside else params["low"]
            values.append(base + params["noise"] * rng.symmetric_noise())
    elif family == "drift":
        start, end = params["start"], params["end"]
        for index in range(sample_count):
            fraction = index / max(1, sample_count - 1)
            noise = params["noise"] * rng.symmetric_noise()
            values.append(start + (end - start) * fraction + noise)
    elif family == "outlier":
        for index in range(sample_count):
            value = params["level"] + params["noise"] * rng.symmetric_noise()
            if index in params["outlier_at"]:
                value = params["outlier_level"]
            values.append(value)
    elif family == "periodic":
        for index in range(sample_count):
            phase = 2.0 * math.pi * params["cycles"] * index / sample_count
            values.append(
                params["offset"]
                + params["amplitude"] * math.sin(phase)
                + params["noise"] * rng.symmetric_noise()
            )
    elif family == "sparse_events":
        for index in range(sample_count):
            if index in params["event_at"]:
                values.append(params["event_level"])
            else:
                values.append(params["floor"] + params["noise"] * rng.symmetric_noise())
    else:
        raise ValueError(f"unknown signal family: {family}")
    return [sim.clamp(value, 0.0, 1.0) for value in values]


def apply_perturbation(values, perturbation, rng, params):
    """Sensor-side degradation. Still generator territory: it is the scenario."""
    if perturbation == "none":
        return list(values)
    if perturbation == "additive_noise":
        level = params["level"]
        return [sim.clamp(value + level * rng.symmetric_noise(), 0.0, 1.0) for value in values]
    if perturbation == "dropout":
        keep = params["keep_probability"]
        return [value if rng.random() < keep else 0.0 for value in values]
    if perturbation == "quantization":
        steps = params["steps"]
        return [
            sim.clamp(round(value * (steps - 1)) / (steps - 1), 0.0, 1.0) for value in values
        ]
    if perturbation == "gain_drift":
        span = params["span"]
        count = len(values)
        return [
            sim.clamp(value * (1.0 - span + 2.0 * span * index / max(1, count - 1)), 0.0, 1.0)
            for index, value in enumerate(values)
        ]
    raise ValueError(f"unknown perturbation: {perturbation}")


def propose_encoder_scenario(rng, sample_count=64, sample_ms=10.0):
    family = rng.choice(SIGNAL_FAMILIES)
    if family == "baseline":
        params = {"level": rng.uniform(0.35, 0.65), "noise": rng.uniform(0.02, 0.12)}
    elif family == "burst":
        params = {
            "low": rng.uniform(0.05, 0.2),
            "high": rng.uniform(0.75, 0.98),
            "burst_width": rng.randint(3, 7),
            "burst_starts": sorted(rng.sample(range(2, sample_count - 8), rng.randint(1, 3))),
            "noise": rng.uniform(0.01, 0.06),
        }
    elif family == "drift":
        params = {
            "start": rng.uniform(0.05, 0.35),
            "end": rng.uniform(0.6, 0.95),
            "noise": rng.uniform(0.01, 0.06),
        }
    elif family == "outlier":
        params = {
            "level": rng.uniform(0.3, 0.6),
            "noise": rng.uniform(0.01, 0.05),
            "outlier_at": sorted(rng.sample(range(sample_count), rng.randint(2, 5))),
            "outlier_level": rng.uniform(0.9, 1.0),
        }
    elif family == "periodic":
        params = {
            "offset": rng.uniform(0.4, 0.6),
            "amplitude": rng.uniform(0.2, 0.4),
            "cycles": rng.randint(2, 7),
            "noise": rng.uniform(0.01, 0.05),
        }
    else:
        params = {
            "floor": rng.uniform(0.0, 0.06),
            "event_level": rng.uniform(0.7, 1.0),
            "event_at": sorted(rng.sample(range(sample_count), rng.randint(2, 6))),
            "noise": rng.uniform(0.0, 0.02),
        }

    perturbation = rng.choice(PERTURBATIONS)
    if perturbation == "additive_noise":
        perturbation_params = {"level": rng.uniform(0.05, 0.25)}
    elif perturbation == "dropout":
        perturbation_params = {"keep_probability": rng.uniform(0.6, 0.95)}
    elif perturbation == "quantization":
        perturbation_params = {"steps": rng.randint(3, 8)}
    elif perturbation == "gain_drift":
        perturbation_params = {"span": rng.uniform(0.1, 0.4)}
    else:
        perturbation_params = {}

    clean = make_signal(family, rng, sample_count, params)
    observed = apply_perturbation(clean, perturbation, rng, perturbation_params)
    encodings = rng.sample(sim.ENCODINGS, 2)
    return {
        "signal_family": family,
        "signal_parameters": params,
        "perturbation": {"kind": perturbation, "parameters": perturbation_params},
        "sample_count": sample_count,
        "sample_ms": sample_ms,
        "signal": observed,
        "encoding_pair": list(encodings),
        "question": (
            f"Which encoding preserves more of this {family} sensor trace: "
            f"{encodings[0]} or {encodings[1]}?"
        ),
    }


# Structural intuitions only. They are wrong often enough to be worth scoring.
_ENCODER_HUNCH = {
    "baseline": "rate",
    "burst": "delta",
    "drift": "delta",
    "outlier": "latency",
    "periodic": "temporal",
    "sparse_events": "delta",
}


def predict_encoder_winner(scenario):
    pair = scenario["encoding_pair"]
    hunch = _ENCODER_HUNCH.get(scenario["signal_family"])
    winner = hunch if hunch in pair else pair[0]
    return {
        "kind": "non_authoritative_guess",
        "predicted_winner": winner,
        "basis": (
            f"structural hunch for {scenario['signal_family']} signals; "
            "no encoder was executed to produce this"
        ),
    }


# --------------------------------------------------------------------------
# Family 2: neuron parameter interventions
# --------------------------------------------------------------------------

STIMULI = ("step", "pulse_train", "ramp")


def propose_neuron_scenario(rng, duration_ms=300.0, dt_ms=0.5):
    stimulus = rng.choice(STIMULI)
    if stimulus == "step":
        params = {
            "amplitude": rng.uniform(1.1, 2.4),
            "onset_ms": rng.uniform(10.0, 40.0),
            "offset_ms": duration_ms - rng.uniform(10.0, 60.0),
        }
    elif stimulus == "pulse_train":
        params = {
            "amplitude": rng.uniform(1.6, 3.2),
            "period_ms": rng.uniform(15.0, 45.0),
            "width_ms": rng.uniform(4.0, 12.0),
            "onset_ms": rng.uniform(5.0, 25.0),
        }
    else:
        params = {
            "peak": rng.uniform(1.4, 3.0),
            "onset_ms": rng.uniform(5.0, 30.0),
        }
    baseline = {
        "v_threshold": rng.uniform(0.85, 1.25),
        "tau_m_ms": rng.uniform(8.0, 20.0),
        "adaptation_b": rng.uniform(0.02, 0.14),
        "t_refractory_ms": rng.uniform(1.5, 5.0),
        "input_scale": rng.uniform(0.8, 1.3),
        "neuromod_gain": 1.0,
    }
    return {
        "stimulus": {"kind": stimulus, "parameters": params},
        "duration_ms": duration_ms,
        "dt_ms": dt_ms,
        "baseline_parameters": baseline,
        "question": "How does the intervention change this neuron's spiking?",
    }


def build_current(scenario):
    """Stimulus waveform, one sample per dt. Shared by generator and oracle."""
    dt_ms = scenario["dt_ms"]
    steps = int(round(scenario["duration_ms"] / dt_ms))
    kind = scenario["stimulus"]["kind"]
    params = scenario["stimulus"]["parameters"]
    current = []
    for index in range(steps):
        time_ms = index * dt_ms
        if kind == "step":
            inside = params["onset_ms"] <= time_ms < params["offset_ms"]
            value = params["amplitude"] if inside else 0.0
        elif kind == "pulse_train":
            if time_ms < params["onset_ms"]:
                value = 0.0
            else:
                phase = (time_ms - params["onset_ms"]) % params["period_ms"]
                value = params["amplitude"] if phase < params["width_ms"] else 0.0
        else:
            if time_ms < params["onset_ms"]:
                value = 0.0
            else:
                span = max(1e-9, scenario["duration_ms"] - params["onset_ms"])
                value = params["peak"] * (time_ms - params["onset_ms"]) / span
        current.append(value)
    return current


_NEURON_OPERATIONS = {
    "threshold": ("scale", (0.6, 1.5)),
    "decay": ("scale", (0.5, 2.0)),
    "adaptation": ("scale", (0.2, 3.0)),
    "refractory": ("scale", (0.5, 3.0)),
    "input_intensity": ("scale", (0.5, 1.8)),
    "neuromodulatory_state": ("scale", (0.6, 1.6)),
}


def propose_neuron_intervention(rng, scenario):
    target = rng.choice(sorted(sim.INTERVENTION_TARGETS))
    operation, (low, high) = _NEURON_OPERATIONS[target]
    factor = rng.uniform(low, high)
    return {
        "target": target,
        "parameter": sim.INTERVENTION_TARGETS[target],
        "operation": operation,
        "factor": factor,
        "description": f"{operation} {sim.INTERVENTION_TARGETS[target]} by {factor:.3f}",
    }


def predict_neuron_effect(scenario, intervention):
    """Sign-of-effect hunch from the textbook direction of each knob."""
    target = intervention["target"]
    factor = intervention["factor"]
    raises_rate = {
        "threshold": factor < 1.0,
        "decay": factor > 1.0,
        "adaptation": factor < 1.0,
        "refractory": factor < 1.0,
        "input_intensity": factor > 1.0,
        "neuromodulatory_state": factor > 1.0,
    }[target]
    return {
        "kind": "non_authoritative_guess",
        "predicted_direction": "increases_firing" if raises_rate else "decreases_firing",
        "basis": f"textbook sign of {target}; no simulation was run to produce this",
    }


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


# --------------------------------------------------------------------------
# Family 4: reward / outcome situations
# --------------------------------------------------------------------------

SITUATIONS = (
    "relay_gate_accepted_a_bounded_action",
    "relay_gate_blocked_an_unsafe_action",
    "sensor_fusion_recovered_after_dropout",
    "actuator_retry_succeeded_late",
    "novel_stimulus_explored",
    "energy_budget_overrun",
)


def propose_reward_scenario(rng, pre_count=4, duration_ms=220.0):
    situation = rng.choice(SITUATIONS)
    expected = rng.uniform(0.1, 0.8)
    surprise = rng.uniform(-0.7, 0.7)
    pre_spikes = []
    for index in range(pre_count):
        count = rng.randint(2, 6)
        times = sorted(rng.uniform(5.0, duration_ms - 20.0) for _ in range(count))
        pre_spikes.append(times)
    return {
        "situation": situation,
        "outcome": {
            "expected_value": expected,
            "received_reward": sim.clamp(expected + surprise, 0.0, 1.0),
            "risk": rng.uniform(0.0, 1.0),
            "novelty": rng.uniform(0.0, 1.0),
            "effort": rng.uniform(0.0, 1.0),
        },
        "circuit": {
            "pre_neuron_count": pre_count,
            "pre_spike_times_ms": pre_spikes,
            "initial_weights": [rng.uniform(0.2, 0.9) for _ in range(pre_count)],
            "duration_ms": duration_ms,
        },
        "question": "What modulator state and weight update does this outcome produce?",
    }


def predict_reward_effect(scenario):
    outcome = scenario["outcome"]
    delta = outcome["received_reward"] - outcome["expected_value"]
    trains = scenario["circuit"]["pre_spike_times_ms"]
    busiest = max(range(len(trains)), key=lambda index: (len(trains[index]), -index))
    return {
        "kind": "non_authoritative_guess",
        "predicted_valence": "positive" if delta > 0 else ("negative" if delta < 0 else "neutral"),
        "predicted_weight_direction": (
            "potentiation" if delta > 0 else ("depression" if delta < 0 else "none")
        ),
        "predicted_strongest_synapse": busiest,
        "basis": (
            "valence from the sign of received minus expected reward; strongest "
            "synapse guessed as the busiest pre-synaptic train, which ignores spike "
            "timing relative to the readout. No critic or plasticity run."
        ),
    }


# --------------------------------------------------------------------------
# Family 5: delayed-dependency memory tasks
# --------------------------------------------------------------------------


def propose_memory_scenario(rng):
    cue = rng.choice(("A", "B"))
    cue_ms = rng.uniform(15.0, 35.0)
    delay_ms = rng.choice((80.0, 150.0, 240.0, 360.0, 520.0, 700.0))
    probe_ms = cue_ms + delay_ms
    distractor_count = rng.randint(0, 4)
    distractors = sorted(
        rng.uniform(cue_ms + 20.0, probe_ms - 15.0) for _ in range(distractor_count)
    ) if probe_ms - 15.0 > cue_ms + 20.0 else []
    reset_ms = None
    if rng.random() < 0.25 and probe_ms - 25.0 > cue_ms + 25.0:
        reset_ms = rng.uniform(cue_ms + 25.0, probe_ms - 25.0)
    network = {
        "loop_delay_ms": rng.choice((8.0, 10.0, 12.0, 14.0)),
        "latch_adaptation_b": rng.choice((0.015, 0.02, 0.03, 0.04, 0.055)),
        "distractor_weight": rng.choice((0.35, 0.45, 0.6, 1.1)),
    }
    return {
        "cue": cue,
        "cue_ms": cue_ms,
        "probe_ms": probe_ms,
        "delay_ms": delay_ms,
        "distractor_ms": distractors,
        "distractor_count": len(distractors),
        "reset_ms": reset_ms,
        "event_sparsity": (len(distractors) + 1) / max(1.0, delay_ms / 100.0),
        "network_variant": network,
        "question": (
            f"After a {delay_ms:.0f} ms delay with {len(distractors)} distractors"
            f"{' and a reset pulse' if reset_ms is not None else ''}, "
            "which output does the network select at the probe?"
        ),
    }


def predict_memory_response(scenario):
    """Assumes the cue survives unless it was explicitly reset."""
    if scenario["reset_ms"] is not None:
        predicted = "none"
    else:
        predicted = scenario["cue"]
    return {
        "kind": "non_authoritative_guess",
        "predicted_response": predicted,
        "basis": (
            "assumes perfect retention unless a reset pulse is present; "
            "makes no use of the loop parameters and runs no simulation"
        ),
    }
