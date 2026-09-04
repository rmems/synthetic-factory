"""Deterministic reference simulators used as stand-in oracles.

None of the runtimes named in issue #77 (`axon-encoder`, `neuromod`,
`synaptic-mesh`, `limbic-critic`, `plasticity-lab`, a validated recurrent SNN)
are installed in this environment, and the repository's own notes already
record that the crates.io packages are unavailable. Rather than fake their
output, this module supplies small, fully specified, stdlib-only simulators
that occupy the same position in the pipeline.

They are labelled `implementation: "reference"` in every record they produce.
A reference measurement is a real measurement of a real (if small) model; it
is *not* a measurement from the named runtime, and `record.py` refuses to mark
such records publishable.

Every function here is pure and deterministic: same inputs, same floats.
"""

import math
from itertools import pairwise

# Loihi-2-class energy constant, the same 23 pJ/spike already used by
# schemas/raster.schema.json so the two families report comparable numbers.
ENERGY_PJ_PER_SPIKE = 23.0

ENCODINGS = ("rate", "latency", "delta", "temporal")

# Smallest weight change that counts as an applied update. It sits just above
# the rounding step of the stored records so that "the update was applied"
# means the same thing to the simulator and to the validator.
WEIGHT_UPDATE_EPS = 5e-6


def clamp(value, low, high):
    return low if value < low else (high if value > high else value)


def pearson(left, right):
    """Pearson r, or None when either series is constant (r undefined)."""
    count = len(left)
    if count != len(right) or count < 2:
        return None
    mean_l = sum(left) / count
    mean_r = sum(right) / count
    cov = sum((a - mean_l) * (b - mean_r) for a, b in zip(left, right, strict=True))
    var_l = math.sqrt(sum((a - mean_l) ** 2 for a in left))
    var_r = math.sqrt(sum((b - mean_r) ** 2 for b in right))
    if var_l == 0.0 or var_r == 0.0:
        return None
    return cov / (var_l * var_r)


def rmse(left, right):
    count = len(left)
    if count != len(right) or not count:
        raise ValueError("rmse requires two non-empty, equal-length series")
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(left, right, strict=True)) / count)


# --------------------------------------------------------------------------
# Family 1 oracle: spike encoders (stand-in for `axon-encoder`)
# --------------------------------------------------------------------------

ENCODER_DEFAULTS = {
    "sample_ms": 10.0,
    "substeps": 8,
    "max_rate_hz": 800.0,
    "latency_span": 0.9,
    "latency_floor": 0.02,
    "delta_theta": 0.125,
    "delta_init": 0.5,
    "temporal_bins": 8,
    "excerpt_spikes": 24,
}


def encoder_config(overrides=None):
    config = dict(ENCODER_DEFAULTS)
    if overrides:
        config.update(overrides)
    return config


def encode_rate(signal, config):
    """Delta-sigma rate code: one channel, spike count proportional to value.

    A leaky accumulator is charged by ``value`` each micro-step and emits a
    spike whenever it crosses 1.0, carrying the remainder forward. This is
    deterministic where a Poisson rate code would not be.
    """
    sample_ms = config["sample_ms"]
    substeps = int(config["substeps"])
    micro_ms = sample_ms / substeps
    gain = config["max_rate_hz"] * micro_ms / 1000.0
    accumulator = 0.0
    spikes = []
    for index, raw in enumerate(signal):
        value = clamp(raw, 0.0, 1.0)
        for step in range(substeps):
            accumulator += value * gain
            if accumulator >= 1.0:
                accumulator -= 1.0
                spikes.append({"channel": "rate", "t_ms": index * sample_ms + step * micro_ms})
    return spikes


def decode_rate(spikes, sample_count, config):
    sample_ms = config["sample_ms"]
    per_sample = config["max_rate_hz"] * sample_ms / 1000.0
    counts = [0] * sample_count
    for spike in spikes:
        index = int(spike["t_ms"] // sample_ms)
        if 0 <= index < sample_count:
            counts[index] += 1
    return [clamp(count / per_sample, 0.0, 1.0) for count in counts]


def encode_latency(signal, config):
    """Time-to-first-spike: a larger value spikes earlier inside its window."""
    sample_ms = config["sample_ms"]
    span = config["latency_span"]
    floor = config["latency_floor"]
    spikes = []
    for index, raw in enumerate(signal):
        value = clamp(raw, 0.0, 1.0)
        if value < floor:
            continue
        offset = (1.0 - value) * sample_ms * span
        spikes.append({"channel": "latency", "t_ms": index * sample_ms + offset})
    return spikes


def decode_latency(spikes, sample_count, config):
    sample_ms = config["sample_ms"]
    span = config["latency_span"]
    decoded = [0.0] * sample_count
    seen = [False] * sample_count
    for spike in spikes:
        index = int(spike["t_ms"] // sample_ms)
        if not (0 <= index < sample_count) or seen[index]:
            continue
        seen[index] = True
        offset = spike["t_ms"] - index * sample_ms
        decoded[index] = clamp(1.0 - offset / (sample_ms * span), 0.0, 1.0)
    return decoded


def encode_delta(signal, config):
    """ON/OFF change code: spikes only when the value moves by a threshold."""
    sample_ms = config["sample_ms"]
    theta = config["delta_theta"]
    reference = config["delta_init"]
    spikes = []
    for index, raw in enumerate(signal):
        value = clamp(raw, 0.0, 1.0)
        guard = 0
        while value - reference >= theta and guard < 16:
            reference += theta
            spikes.append({"channel": "delta_on", "t_ms": index * sample_ms})
            guard += 1
        while reference - value >= theta and guard < 16:
            reference -= theta
            spikes.append({"channel": "delta_off", "t_ms": index * sample_ms})
            guard += 1
    return spikes


def decode_delta(spikes, sample_count, config):
    sample_ms = config["sample_ms"]
    theta = config["delta_theta"]
    level = config["delta_init"]
    by_sample = [[] for _ in range(sample_count)]
    for spike in spikes:
        index = int(spike["t_ms"] // sample_ms)
        if 0 <= index < sample_count:
            by_sample[index].append(spike["channel"])
    decoded = []
    for channels in by_sample:
        for channel in channels:
            level += theta if channel == "delta_on" else -theta
        decoded.append(clamp(level, 0.0, 1.0))
    return decoded


def encode_temporal(signal, config):
    """Phase code: a reference spike plus a phase spike whose lag is the value."""
    sample_ms = config["sample_ms"]
    bins = int(config["temporal_bins"])
    bin_ms = sample_ms / bins
    spikes = []
    for index, raw in enumerate(signal):
        value = clamp(raw, 0.0, 1.0)
        base = index * sample_ms
        phase = int(math.floor(value * (bins - 1) + 0.5))
        spikes.append({"channel": "temporal_ref", "t_ms": base})
        spikes.append({"channel": "temporal_phase", "t_ms": base + phase * bin_ms})
    return spikes


def decode_temporal(spikes, sample_count, config):
    sample_ms = config["sample_ms"]
    bins = int(config["temporal_bins"])
    bin_ms = sample_ms / bins
    decoded = [0.0] * sample_count
    for spike in spikes:
        if spike["channel"] != "temporal_phase":
            continue
        index = int(spike["t_ms"] // sample_ms)
        if not (0 <= index < sample_count):
            continue
        phase = round((spike["t_ms"] - index * sample_ms) / bin_ms)
        decoded[index] = clamp(phase / (bins - 1), 0.0, 1.0)
    return decoded


_ENCODERS = {
    "rate": (encode_rate, decode_rate),
    "latency": (encode_latency, decode_latency),
    "delta": (encode_delta, decode_delta),
    "temporal": (encode_temporal, decode_temporal),
}


def run_encoder(signal, encoding, config):
    """Encode, decode, and measure one encoding family against the signal."""
    if encoding not in _ENCODERS:
        raise ValueError(f"unknown encoding: {encoding}")
    encode, decode = _ENCODERS[encoding]
    spikes = encode(signal, config)
    spikes.sort(key=lambda item: (item["t_ms"], item["channel"]))
    decoded = decode(spikes, len(signal), config)
    errors = [abs(a - b) for a, b in zip(signal, decoded, strict=True)]
    error = rmse(signal, decoded)
    retention = clamp(1.0 - error, 0.0, 1.0)
    count = len(spikes)
    excerpt = spikes[: int(config["excerpt_spikes"])]
    duration_ms = len(signal) * config["sample_ms"]
    return {
        "encoding": encoding,
        "spike_count": count,
        "channels": sorted({spike["channel"] for spike in spikes}),
        "mean_rate_hz": (count / (duration_ms / 1000.0)) if duration_ms else 0.0,
        "energy_pJ": count * ENERGY_PJ_PER_SPIKE,
        "rmse": error,
        "max_abs_error": max(errors) if errors else 0.0,
        "mean_abs_error": (sum(errors) / len(errors)) if errors else 0.0,
        "pearson_r": pearson(signal, decoded),
        "information_retention": retention,
        "retention_per_spike": (retention / count) if count else None,
        "reconstruction": decoded,
        "representation_excerpt": excerpt,
        "representation_excerpt_truncated": count > len(excerpt),
        "spike_train_digest": None,  # filled in by the adapter over the full train
        "spikes": spikes,
    }


def compare_encodings(signal, encoding_a, encoding_b, config, tie_epsilon=0.005):
    """Run two encodings on one signal and let the measurements pick a winner."""
    left = run_encoder(signal, encoding_a, config)
    right = run_encoder(signal, encoding_b, config)
    gap = left["information_retention"] - right["information_retention"]
    if abs(gap) >= tie_epsilon:
        winner = encoding_a if gap > 0 else encoding_b
        basis = "information_retention"
    elif left["spike_count"] != right["spike_count"]:
        winner = encoding_a if left["spike_count"] < right["spike_count"] else encoding_b
        basis = "spike_count_tiebreak"
    else:
        winner = None
        basis = "tie"
    return {
        "a": left,
        "b": right,
        "winner": winner,
        "winner_basis": basis,
        "retention_margin": gap,
        "energy_margin_pJ": left["energy_pJ"] - right["energy_pJ"],
        "tie_epsilon": tie_epsilon,
    }


# --------------------------------------------------------------------------
# Family 2 oracle: adaptive LIF neuron (stand-in for `neuromod`)
# --------------------------------------------------------------------------

NEURON_DEFAULTS = {
    "v_rest": 0.0,
    "v_reset": 0.0,
    "v_threshold": 1.0,
    "tau_m_ms": 12.0,
    "r_m": 1.0,
    "t_refractory_ms": 3.0,
    "adaptation_b": 0.08,
    "tau_w_ms": 60.0,
    "input_scale": 1.0,
    "neuromod_gain": 1.0,
    "neuromod_threshold_shift": 0.0,
    "dt_ms": 0.5,
    "v_floor": -2.0,
}

# Which neuron parameter each intervention target moves. Interventions are
# proposed by the generator; the mapping (and therefore the physics) is
# oracle-side.
INTERVENTION_TARGETS = {
    "threshold": "v_threshold",
    "decay": "tau_m_ms",
    "adaptation": "adaptation_b",
    "refractory": "t_refractory_ms",
    "input_intensity": "input_scale",
    "neuromodulatory_state": "neuromod_gain",
}


def neuron_config(overrides=None):
    config = dict(NEURON_DEFAULTS)
    if overrides:
        config.update(overrides)
    return config


def simulate_neuron(config, input_current, trace_points=48):
    """Adaptive exponential-free LIF, forward Euler.

    Per step, in this order: expire refractory, leak, inject, adapt-decay,
    threshold test. ``input_current`` is one value per ``dt_ms`` step.
    """
    dt_ms = config["dt_ms"]
    tau_m = config["tau_m_ms"]
    tau_w = config["tau_w_ms"]
    v_rest = config["v_rest"]
    v_reset = config["v_reset"]
    v_floor = config["v_floor"]
    threshold = config["v_threshold"] + config["neuromod_threshold_shift"]
    refractory_steps = max(0, int(round(config["t_refractory_ms"] / dt_ms)))

    membrane = v_rest
    adaptation = 0.0
    refractory_left = 0
    spikes = []
    trace = []
    for index, raw in enumerate(input_current):
        current = raw * config["input_scale"] * config["neuromod_gain"] * config["r_m"]
        if refractory_left > 0:
            refractory_left -= 1
            membrane = v_reset
        else:
            membrane += (-(membrane - v_rest) + current - adaptation) * (dt_ms / tau_m)
            if membrane < v_floor:
                membrane = v_floor
        adaptation += (-adaptation) * (dt_ms / tau_w)
        trace.append(membrane)
        if refractory_left <= 0 and membrane >= threshold:
            spikes.append(index * dt_ms)
            membrane = v_reset
            adaptation += config["adaptation_b"]
            refractory_left = refractory_steps
    return _neuron_summary(spikes, trace, config, len(input_current), trace_points)


def _neuron_summary(spikes, trace, config, steps, trace_points):
    dt_ms = config["dt_ms"]
    duration_ms = steps * dt_ms
    intervals = [b - a for a, b in pairwise(spikes)]
    mean_isi = (sum(intervals) / len(intervals)) if intervals else None
    if intervals and len(intervals) > 1 and mean_isi:
        variance = sum((item - mean_isi) ** 2 for item in intervals) / len(intervals)
        cv_isi = math.sqrt(variance) / mean_isi
    else:
        cv_isi = None
    stride = max(1, math.ceil(len(trace) / trace_points)) if trace else 1
    return {
        "spike_count": len(spikes),
        "spike_times_ms": spikes,
        "first_spike_ms": spikes[0] if spikes else None,
        "last_spike_ms": spikes[-1] if spikes else None,
        "mean_rate_hz": len(spikes) / (duration_ms / 1000.0) if duration_ms else 0.0,
        "mean_isi_ms": mean_isi,
        "cv_isi": cv_isi,
        "adaptation_index": (
            (intervals[-1] / intervals[0]) if len(intervals) >= 2 and intervals[0] else None
        ),
        "v_mean": (sum(trace) / len(trace)) if trace else None,
        "v_max": max(trace) if trace else None,
        "v_min": min(trace) if trace else None,
        "v_trace": trace[::stride],
        "v_trace_stride_ms": stride * dt_ms,
        "duration_ms": duration_ms,
    }


def compare_neuron_states(before, after):
    """The measured consequence of an intervention, as a signed delta."""
    delta_count = after["spike_count"] - before["spike_count"]
    if delta_count > 0:
        direction = "increases_firing"
    elif delta_count < 0:
        direction = "decreases_firing"
    else:
        direction = "unchanged_firing"
    return {
        "spike_count_delta": delta_count,
        "mean_rate_delta_hz": after["mean_rate_hz"] - before["mean_rate_hz"],
        "first_spike_shift_ms": _optional_delta(after["first_spike_ms"], before["first_spike_ms"]),
        "mean_isi_delta_ms": _optional_delta(after["mean_isi_ms"], before["mean_isi_ms"]),
        "v_mean_delta": _optional_delta(after["v_mean"], before["v_mean"]),
        "direction": direction,
        "silenced": before["spike_count"] > 0 and after["spike_count"] == 0,
        "unsilenced": before["spike_count"] == 0 and after["spike_count"] > 0,
    }


def _optional_delta(after, before):
    if after is None or before is None:
        return None
    return after - before


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


def simulate_mesh(nodes, edges, events, duration_ms, dt_ms=0.5, max_spikes=4000):
    """Delta-synapse LIF network with per-edge conduction delays.

    Each step, in this order: expire refractory, leak, deliver every injection
    scheduled for this step, decay adaptation, then test threshold. A spike at
    step *t* on edge (src -> dst, delay d) schedules ``weight`` into *dst* at
    ``t + round(d/dt)``, so a self-edge is a reverberating loop whose lifetime
    is set by the loop weight against the adapting threshold.

    ``max_spikes`` bounds a runaway excitatory network; hitting it is reported
    rather than silently truncated.
    """
    steps = int(round(duration_ms / dt_ms))
    order = [node["id"] for node in nodes]
    state = {}
    for node in nodes:
        merged = dict(MESH_NODE_DEFAULTS)
        merged.update(node)
        merged["v"] = merged["v_rest"]
        merged["w"] = 0.0
        merged["refractory_left"] = 0
        merged["spikes"] = []
        state[node["id"]] = merged
    for edge in edges:
        if edge["src"] not in state or edge["dst"] not in state:
            raise ValueError(f"edge references unknown node: {edge}")

    outgoing = {node_id: [] for node_id in order}
    for edge in edges:
        outgoing[edge["src"]].append(edge)

    pending = {}

    def schedule(step, node_id, amount):
        if 0 <= step < steps:
            pending.setdefault(step, []).append((node_id, amount))

    for event in events:
        if event["target"] not in state:
            raise ValueError(f"event references unknown node: {event}")
        schedule(int(round(event["t_ms"] / dt_ms)), event["target"], event["amplitude"])

    truncated = False
    total_spikes = 0
    for step in range(steps):
        for node_id in order:
            cell = state[node_id]
            if cell["refractory_left"] > 0:
                cell["refractory_left"] -= 1
                cell["v"] = cell["v_reset"]
            else:
                cell["v"] += (-(cell["v"] - cell["v_rest"])) * (dt_ms / cell["tau_ms"])
        for node_id, amount in pending.pop(step, ()):  # deterministic insertion order
            cell = state[node_id]
            if cell["refractory_left"] <= 0:
                cell["v"] += amount
                if cell["v"] < cell["v_floor"]:
                    cell["v"] = cell["v_floor"]
        fired = []
        for node_id in order:
            cell = state[node_id]
            cell["w"] += (-cell["w"]) * (dt_ms / cell["tau_w_ms"])
            if cell["refractory_left"] <= 0 and cell["v"] >= cell["v_threshold"] + cell["w"]:
                fired.append(node_id)
        for node_id in fired:
            cell = state[node_id]
            cell["spikes"].append(step * dt_ms)
            cell["v"] = cell["v_reset"]
            cell["w"] += cell["adaptation_b"]
            cell["refractory_left"] = max(0, int(round(cell["t_refractory_ms"] / dt_ms)))
            total_spikes += 1
            for edge in outgoing[node_id]:
                schedule(
                    step + int(round(edge["delay_ms"] / dt_ms)),
                    edge["dst"],
                    edge["weight"],
                )
        if total_spikes > max_spikes:
            truncated = True
            break

    by_node = {node_id: state[node_id]["spikes"] for node_id in order}
    all_spikes = sorted(
        ((t, node_id) for node_id, times in by_node.items() for t in times),
        key=lambda item: (item[0], item[1]),
    )
    first_spike = {node_id: (times[0] if times else None) for node_id, times in by_node.items()}
    firing_order = []
    for _time, node_id in all_spikes:
        if node_id not in firing_order:
            firing_order.append(node_id)
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
        "propagation_delay_delta_ms": _optional_delta(
            after["propagation_delay_ms"], before["propagation_delay_ms"]
        ),
        "sink_reached_before": before["sink_reached"],
        "sink_reached_after": after["sink_reached"],
        "sink_reachability_changed": before["sink_reached"] != after["sink_reached"],
    }


# --------------------------------------------------------------------------
# Family 4 oracle: critic -> plasticity (stand-in for limbic-critic + plasticity-lab)
# --------------------------------------------------------------------------

CRITIC_DEFAULTS = {
    "rpe_gain": 1.4,
    "tonic_dopamine": 0.35,
    "serotonin_baseline": 0.5,
    "risk_weight": 0.35,
    "novelty_weight": 0.6,
    "effort_weight": 0.25,
    "arousal_gain": 1.1,
}


def critic_config(overrides=None):
    config = dict(CRITIC_DEFAULTS)
    if overrides:
        config.update(overrides)
    return config


def run_critic(outcome, config):
    """Map an outcome to modulator levels.

    Units: ``reward_prediction_error`` is in reward units; ``dopamine_phasic``
    is a signed normalised burst/dip in [-1, 1]; the tonic modulator levels are
    normalised to [0, 1]. These are the reference critic's definitions, not a
    claim about `limbic-critic`.
    """
    expected = float(outcome["expected_value"])
    received = float(outcome["received_reward"])
    risk = clamp(float(outcome.get("risk", 0.0)), 0.0, 1.0)
    novelty = clamp(float(outcome.get("novelty", 0.0)), 0.0, 1.0)
    effort = clamp(float(outcome.get("effort", 0.0)), 0.0, 1.0)

    rpe = received - expected
    phasic = math.tanh(config["rpe_gain"] * rpe)
    dopamine = clamp(config["tonic_dopamine"] + 0.5 * phasic, 0.0, 1.0)
    serotonin = clamp(
        config["serotonin_baseline"]
        - config["risk_weight"] * risk
        + config["effort_weight"] * (1.0 - effort),
        0.0,
        1.0,
    )
    acetylcholine = clamp(config["novelty_weight"] * novelty + 0.2 * risk, 0.0, 1.0)
    arousal = math.tanh(config["arousal_gain"] * abs(rpe))
    norepinephrine = clamp(arousal * 0.8 + 0.2 * risk, 0.0, 1.0)
    return {
        "reward_prediction_error": rpe,
        "dopamine_phasic": phasic,
        "dopamine": dopamine,
        "serotonin": serotonin,
        "acetylcholine": acetylcholine,
        "norepinephrine": norepinephrine,
        "valence": "positive" if rpe > 1e-9 else ("negative" if rpe < -1e-9 else "neutral"),
    }


PLASTICITY_DEFAULTS = {
    "learning_rate": 0.12,
    "a_plus": 1.0,
    "a_minus": 0.8,
    "tau_plus_ms": 18.0,
    "tau_minus_ms": 22.0,
    "tau_eligibility_ms": 240.0,
    "w_min": 0.0,
    "w_max": 1.5,
    "synapse_delay_ms": 1.0,
    "dt_ms": 0.5,
    "modulatory_gain_ach": 0.5,
    "modulatory_gain_ne": 0.3,
    "duration_ms": 220.0,
}


def plasticity_config(overrides=None):
    config = dict(PLASTICITY_DEFAULTS)
    if overrides:
        config.update(overrides)
    return config


def _plasticity_circuit(weights, pre_spikes, config, readout_overrides=None):
    """Run the pre-synaptic trains into the readout neuron at these weights."""
    readout = mesh_node("readout", tau_ms=10.0, v_threshold=1.0, t_refractory_ms=3.0)
    if readout_overrides:
        readout.update(readout_overrides)
    events = []
    for index, times in enumerate(pre_spikes):
        weight = weights[index]
        for time_ms in times:
            events.append(
                {
                    "target": "readout",
                    "t_ms": time_ms + config["synapse_delay_ms"],
                    "amplitude": weight,
                }
            )
    events.sort(key=lambda item: (item["t_ms"], item["amplitude"]))
    result = simulate_mesh([readout], [], events, config["duration_ms"], dt_ms=config["dt_ms"])
    post = result["spikes_by_node"]["readout"]
    duration_s = config["duration_ms"] / 1000.0
    return {
        "spike_count": len(post),
        "spike_times_ms": post,
        "first_spike_ms": post[0] if post else None,
        "output_rate_hz": len(post) / duration_s if duration_s else 0.0,
    }


def eligibility_traces(weights, pre_spikes, post_spikes, config):
    """Per-synapse STDP eligibility, decayed to the reward time.

    Pair-based STDP: a post spike after a pre spike potentiates, a post spike
    before a pre spike depresses. The pair contribution is then decayed by the
    eligibility time constant from the post spike to the end of the episode,
    which is when the modulator arrives.
    """
    reward_time = config["duration_ms"]
    tau_plus = config["tau_plus_ms"]
    tau_minus = config["tau_minus_ms"]
    tau_e = config["tau_eligibility_ms"]
    traces = []
    for index in range(len(weights)):
        total = 0.0
        for pre_time in pre_spikes[index]:
            for post_time in post_spikes:
                gap = post_time - pre_time
                if gap > 0:
                    contribution = config["a_plus"] * math.exp(-gap / tau_plus)
                elif gap < 0:
                    contribution = -config["a_minus"] * math.exp(gap / tau_minus)
                else:
                    continue
                total += contribution * math.exp(-(reward_time - post_time) / tau_e)
        traces.append(total)
    return traces


def run_plasticity(weights, pre_spikes, modulators, config):
    """Three-factor update that is actually applied, then re-measured.

    The returned ``weights_after`` are written into a second run of the same
    circuit on the same input, so ``post_update_behavior`` is a measurement of
    the updated network rather than an extrapolation.
    """
    before = _plasticity_circuit(weights, pre_spikes, config)
    traces = eligibility_traces(weights, pre_spikes, before["spike_times_ms"], config)
    gain = (
        1.0
        + config["modulatory_gain_ach"] * modulators["acetylcholine"]
        + config["modulatory_gain_ne"] * modulators["norepinephrine"]
    )
    deltas = []
    updated = []
    for index, weight in enumerate(weights):
        raw_delta = config["learning_rate"] * traces[index] * modulators["dopamine_phasic"] * gain
        new_weight = clamp(weight + raw_delta, config["w_min"], config["w_max"])
        deltas.append(new_weight - weight)
        updated.append(new_weight)
    after = _plasticity_circuit(updated, pre_spikes, config)
    applied = any(abs(delta) > WEIGHT_UPDATE_EPS for delta in deltas)
    return {
        "weights_before": list(weights),
        "weights_after": updated,
        "weight_deltas": deltas,
        "eligibility": traces,
        "modulatory_gain": gain,
        "update_applied": applied,
        "update_rule": "dw = lr * eligibility * dopamine_phasic * modulatory_gain",
        "pre_update_behavior": before,
        "post_update_behavior": after,
        "behavior_delta": {
            "spike_count_delta": after["spike_count"] - before["spike_count"],
            "output_rate_delta_hz": after["output_rate_hz"] - before["output_rate_hz"],
            "first_spike_shift_ms": _optional_delta(
                after["first_spike_ms"], before["first_spike_ms"]
            ),
        },
    }


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
