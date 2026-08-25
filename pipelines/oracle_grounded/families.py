"""The five dataset families of issue #77.

Each family binds three things that stay separate in the record:

1. a generator that proposes a scenario, an intervention, and a guess,
2. an oracle adapter that measures what actually happens,
3. family-specific checks that a record must pass to be accepted.

``build_request`` is the reproduction contract: given the stored scenario and
intervention it rebuilds exactly the request the oracle was handed, so
``validate`` can re-run the oracle and compare the measurement byte for byte.
"""

from . import canon, generators, oracles, sim

ENCODER_FAMILY = "spike-encoder-equivalence-pairs"
NEURON_FAMILY = "neuron-dynamics-counterfactuals"
MESH_FAMILY = "synaptic-delay-causal-trajectories"
CREDIT_FAMILY = "neuromodulator-credit-assignment"
MEMORY_FAMILY = "temporal-memory-spike-challenges"

FAMILY_NAMES = (
    ENCODER_FAMILY,
    NEURON_FAMILY,
    MESH_FAMILY,
    CREDIT_FAMILY,
    MEMORY_FAMILY,
)

# Stored records are rounded to canon.PRECISION decimals, so an arithmetic
# identity between three stored numbers can be off by a few ulps of that
# rounding. Anything this package actually measures is orders of magnitude
# larger, so the identity checks stay meaningful at this tolerance.
ROUNDING_TOL = 5 * 10**-canon.PRECISION

TIME_UNITS = "millisecond"
ENERGY_UNITS = "picojoule"
RATE_UNITS = "hertz"
DIMENSIONLESS = "dimensionless"


def _measurement_matches(actual, expected):
    """Compare a stored scalar with a value derived from stored measurements."""
    if actual is None or expected is None:
        return actual is expected
    if isinstance(actual, bool) or isinstance(expected, bool):
        return actual is expected
    if isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
        return abs(actual - expected) <= ROUNDING_TOL
    return actual == expected


class FamilySpec:
    """Everything the pipeline needs to know about one dataset family."""

    def __init__(
        self, name, runtimes, oracle_type, propose, build_request, build_oracle, checks, score
    ):
        self.name = name
        self.runtimes = tuple(runtimes)
        self.oracle_type = oracle_type
        self.propose = propose
        self.build_request = build_request
        self._build_oracle = build_oracle
        self.checks = checks
        self.score = score

    def oracle(self, environ=None):
        return self._build_oracle(environ)


# --------------------------------------------------------------------------
# Family 1: spike-encoder-equivalence-pairs  (oracle: axon-encoder)
# --------------------------------------------------------------------------

ENCODER_UNITS = {
    "spike_count": "spikes",
    "mean_rate_hz": RATE_UNITS,
    "energy_pJ": ENERGY_UNITS,
    "rmse": "normalized sensor units",
    "mean_abs_error": "normalized sensor units",
    "max_abs_error": "normalized sensor units",
    "pearson_r": DIMENSIONLESS,
    "information_retention": "dimensionless, 1 - rmse clipped to [0, 1]",
    "retention_per_spike": "retention per spike",
    "representation_excerpt.t_ms": TIME_UNITS,
    "retention_margin": "dimensionless, retention(a) - retention(b)",
    "energy_margin_pJ": ENERGY_UNITS,
}


def _trim_encoding(measured):
    """Swap the full spike train for a digest; keep a bounded excerpt."""
    trimmed = dict(measured)
    spikes = trimmed.pop("spikes")
    trimmed["spike_train_digest"] = canon.digest(spikes)
    return trimmed


def encoder_request(scenario, intervention):
    del intervention  # this family perturbs the sensor, not the oracle
    return {
        "configuration": {
            "encoder": sim.encoder_config(
                {
                    "sample_ms": scenario["sample_ms"],
                    "excerpt_spikes": 24,
                }
            ),
            "tie_epsilon": 0.005,
            "encoding_pair": list(scenario["encoding_pair"]),
        },
        "data": {"signal": list(scenario["signal"])},
    }


def _encoder_reference(request):
    config = request["configuration"]
    pair = config["encoding_pair"]
    comparison = sim.compare_encodings(
        request["data"]["signal"],
        pair[0],
        pair[1],
        config["encoder"],
        tie_epsilon=config["tie_epsilon"],
    )
    measured = {
        "encoding_a": _trim_encoding(comparison["a"]),
        "encoding_b": _trim_encoding(comparison["b"]),
        "winner": comparison["winner"],
        "winner_basis": comparison["winner_basis"],
        "retention_margin": comparison["retention_margin"],
        "energy_margin_pJ": comparison["energy_margin_pJ"],
    }
    return measured, ENCODER_UNITS


def _encoder_oracle(environ=None):
    return oracles.bind(
        runtime="axon-encoder",
        oracle_id="encoder-ref",
        oracle_type="spike-encoder",
        description=(
            "Deterministic rate / latency / delta / temporal encoders with matched "
            "decoders, standing in for axon-encoder"
        ),
        reference_fn=_encoder_reference,
        environ=environ,
    )


def _encoder_propose(rng):
    scenario = generators.propose_encoder_scenario(rng)
    return scenario, None, generators.predict_encoder_winner(scenario)


def _encoder_checks(record):
    measured = record["result"]["measured"]
    pair = record["scenario"]["encoding_pair"]
    findings = []
    winner = measured["winner"]
    if winner is not None and winner not in pair:
        findings.append(f"winner {winner!r} is not one of the compared encodings {pair}")
    for side in ("encoding_a", "encoding_b"):
        retention = measured[side]["information_retention"]
        if not 0.0 <= retention <= 1.0:
            findings.append(f"{side}.information_retention out of range: {retention}")
        if measured[side]["spike_count"] < 0:
            findings.append(f"{side}.spike_count is negative")
        decoded = measured[side]["reconstruction"]
        if len(decoded) != record["scenario"]["sample_count"]:
            findings.append(f"{side}.reconstruction length does not match sample_count")
    retention_gap = (
        measured["encoding_a"]["information_retention"]
        - measured["encoding_b"]["information_retention"]
    )
    if not _measurement_matches(measured["retention_margin"], retention_gap):
        findings.append("retention_margin does not match the two measured retentions")
    tie_epsilon = record["oracle"]["configuration"]["tie_epsilon"]
    if abs(retention_gap) >= tie_epsilon:
        expected_basis = "information_retention"
        expected_winner = pair[0] if retention_gap > 0 else pair[1]
    elif measured["encoding_a"]["spike_count"] != measured["encoding_b"]["spike_count"]:
        expected_basis = "spike_count_tiebreak"
        expected_winner = (
            pair[0]
            if measured["encoding_a"]["spike_count"]
            < measured["encoding_b"]["spike_count"]
            else pair[1]
        )
    else:
        expected_basis = "tie"
        expected_winner = None
    if measured["winner_basis"] != expected_basis:
        findings.append(
            f"winner_basis {measured['winner_basis']!r} does not match the measured "
            f"retention and spike counts ({expected_basis!r})"
        )
    if winner != expected_winner:
        findings.append(
            f"winner {winner!r} does not match the measured {expected_basis} decision"
        )
    return findings


# --------------------------------------------------------------------------
# Family 2: neuron-dynamics-counterfactuals  (oracle: neuromod)
# --------------------------------------------------------------------------

NEURON_UNITS = {
    "spike_times_ms": TIME_UNITS,
    "first_spike_ms": TIME_UNITS,
    "last_spike_ms": TIME_UNITS,
    "mean_isi_ms": TIME_UNITS,
    "mean_rate_hz": RATE_UNITS,
    "cv_isi": DIMENSIONLESS,
    "adaptation_index": "dimensionless, last ISI / first ISI",
    "v_mean": "normalized membrane units (v_threshold = 1)",
    "v_max": "normalized membrane units (v_threshold = 1)",
    "v_min": "normalized membrane units (v_threshold = 1)",
    "v_trace": "normalized membrane units, sampled every v_trace_stride_ms",
    "v_trace_stride_ms": TIME_UNITS,
    "duration_ms": TIME_UNITS,
    "spike_count_delta": "spikes",
    "first_spike_shift_ms": TIME_UNITS,
}


def _intervened_parameters(baseline, intervention):
    """Apply the proposed intervention to the neuron configuration."""
    parameter = intervention["parameter"]
    updated = dict(baseline)
    if intervention["operation"] != "scale":
        raise ValueError(f"unsupported neuron intervention: {intervention['operation']}")
    updated[parameter] = baseline.get(parameter, sim.NEURON_DEFAULTS[parameter]) * intervention[
        "factor"
    ]
    return updated


def neuron_request(scenario, intervention):
    before = sim.neuron_config(scenario["baseline_parameters"])
    before["dt_ms"] = scenario["dt_ms"]
    after = _intervened_parameters(before, intervention)
    return {
        "configuration": {
            "before": before,
            "after": after,
            "intervened_parameter": intervention["parameter"],
            "trace_points": 48,
        },
        "data": {"current": generators.build_current(scenario)},
    }


def _neuron_reference(request):
    config = request["configuration"]
    current = request["data"]["current"]
    points = config["trace_points"]
    before = sim.simulate_neuron(config["before"], current, trace_points=points)
    after = sim.simulate_neuron(config["after"], current, trace_points=points)
    measured = {
        "before": before,
        "after": after,
        "delta": sim.compare_neuron_states(before, after),
    }
    return measured, NEURON_UNITS


def _neuron_oracle(environ=None):
    return oracles.bind(
        runtime="neuromod",
        oracle_id="lif-ref",
        oracle_type="neuron-simulation",
        description=(
            "Adaptive leaky integrate-and-fire neuron with neuromodulatory gain and "
            "threshold shift, standing in for the neuromod simulation"
        ),
        reference_fn=_neuron_reference,
        environ=environ,
    )


def _neuron_propose(rng):
    scenario = generators.propose_neuron_scenario(rng)
    intervention = generators.propose_neuron_intervention(rng, scenario)
    return scenario, intervention, generators.predict_neuron_effect(scenario, intervention)


def _neuron_checks(record):
    measured = record["result"]["measured"]
    findings = []
    before = measured["before"]
    after = measured["after"]
    delta = measured["delta"]
    expected_delta = sim.compare_neuron_states(before, after)
    for field, expected in expected_delta.items():
        actual = delta.get(field)
        if not _measurement_matches(actual, expected):
            findings.append(
                f"delta.{field} does not match the value derived from before/after states"
            )
    for side, state in (("before", before), ("after", after)):
        times = state["spike_times_ms"]
        if any(later < earlier for earlier, later in zip(times, times[1:])):
            findings.append(f"{side}.spike_times_ms is not non-decreasing")
        if state["spike_count"] != len(times):
            findings.append(f"{side}.spike_count does not match spike_times_ms")
    configuration = record["oracle"]["configuration"]
    parameter = configuration["intervened_parameter"]
    changed = [
        key
        for key in configuration["before"]
        if configuration["before"][key] != configuration["after"].get(key)
    ]
    if changed != [parameter]:
        findings.append(
            f"intervention should change exactly {parameter!r}, but changed {changed}"
        )
    return findings


# --------------------------------------------------------------------------
# Family 3: synaptic-delay-causal-trajectories  (oracle: synaptic-mesh)
# --------------------------------------------------------------------------

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
            nodes, edges, data["events"], config["duration_ms"], dt_ms=config["dt_ms"]
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
        oracle_id="mesh-ref",
        oracle_type="network-simulation",
        description=(
            "Delta-synapse spiking mesh with per-edge conduction delays and "
            "inhibition, standing in for synaptic-mesh plus a compatible runtime"
        ),
        reference_fn=_mesh_reference,
        environ=environ,
    )


def _mesh_propose(rng):
    scenario = generators.propose_mesh_scenario(rng)
    intervention = generators.propose_mesh_intervention(rng, scenario)
    return scenario, intervention, generators.predict_mesh_effect(scenario, intervention)


def _mesh_checks(record):
    measured = record["result"]["measured"]
    nodes = set(record["scenario"]["nodes"])
    sink = record["scenario"]["sink"]
    findings = []
    for side in ("before", "after"):
        state = measured[side]
        unknown = [node for node in state["firing_order"] if node not in nodes]
        if unknown:
            findings.append(f"{side}.firing_order names unknown nodes: {unknown}")
        if len(set(state["firing_order"])) != len(state["firing_order"]):
            findings.append(f"{side}.firing_order repeats a node")
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
            findings.append(
                f"{side}.propagation_delay_ms does not match sink minus source arrival"
            )
    delta = measured["delta"]
    if delta["sink_reachability_changed"] != (
        measured["before"]["sink_reached"] != measured["after"]["sink_reached"]
    ):
        findings.append("delta.sink_reachability_changed is inconsistent")
    before_delay = measured["before"]["propagation_delay_ms"]
    after_delay = measured["after"]["propagation_delay_ms"]
    expected_delta = (
        None if before_delay is None or after_delay is None else after_delay - before_delay
    )
    if not _measurement_matches(delta.get("propagation_delay_delta_ms"), expected_delta):
        findings.append(
            "delta.propagation_delay_delta_ms does not match the before/after delays"
        )
    return findings


# --------------------------------------------------------------------------
# Family 4: neuromodulator-credit-assignment  (limbic-critic -> plasticity-lab)
# --------------------------------------------------------------------------

CRITIC_UNITS = {
    "reward_prediction_error": "reward units (received - expected)",
    "dopamine_phasic": "dimensionless, signed burst/dip in [-1, 1]",
    "dopamine": "dimensionless, normalized level in [0, 1]",
    "serotonin": "dimensionless, normalized level in [0, 1]",
    "acetylcholine": "dimensionless, normalized level in [0, 1]",
    "norepinephrine": "dimensionless, normalized level in [0, 1]",
}

PLASTICITY_UNITS = {
    "weights_before": "synaptic weight, normalized to v_threshold = 1",
    "weights_after": "synaptic weight, normalized to v_threshold = 1",
    "weight_deltas": "synaptic weight change",
    "eligibility": "dimensionless STDP eligibility at reward time",
    "modulatory_gain": DIMENSIONLESS,
    "pre_update_behavior.spike_times_ms": TIME_UNITS,
    "post_update_behavior.spike_times_ms": TIME_UNITS,
    "output_rate_hz": RATE_UNITS,
    "first_spike_shift_ms": TIME_UNITS,
}


def credit_request(scenario, intervention):
    del intervention  # the outcome itself is the intervention here
    circuit = scenario["circuit"]
    return {
        "configuration": {
            "critic": sim.critic_config(),
            "plasticity": sim.plasticity_config({"duration_ms": circuit["duration_ms"]}),
        },
        "data": {
            "outcome": dict(scenario["outcome"]),
            "initial_weights": list(circuit["initial_weights"]),
            "pre_spike_times_ms": [list(times) for times in circuit["pre_spike_times_ms"]],
        },
    }


def _critic_reference(request):
    measured = sim.run_critic(request["data"]["outcome"], request["configuration"])
    return measured, CRITIC_UNITS


def _plasticity_reference(request):
    measured = sim.run_plasticity(
        request["data"]["initial_weights"],
        request["data"]["pre_spike_times_ms"],
        request["modulators"],
        request["configuration"],
    )
    return measured, PLASTICITY_UNITS


def _credit_oracle(environ=None):
    critic = oracles.bind(
        runtime="limbic-critic",
        oracle_id="critic-ref",
        oracle_type="critic",
        description="Reference reward critic mapping an outcome to modulator levels",
        reference_fn=_critic_reference,
        environ=environ,
    )
    plasticity = oracles.bind(
        runtime="plasticity-lab",
        oracle_id="plasticity-ref",
        oracle_type="plasticity",
        description=(
            "Reference three-factor STDP that applies the weight update and "
            "re-runs the circuit to measure the post-update behaviour"
        ),
        reference_fn=_plasticity_reference,
        environ=environ,
    )
    return oracles.ChainOracle(
        # Built from the resolved adapters so a half-bound chain does not claim
        # to be the all-reference one.
        oracle_id=f"{critic.oracle_id}+{plasticity.oracle_id}",
        oracle_type="critic-plasticity-chain",
        description="limbic-critic -> plasticity-lab oracle path",
        steps=[
            (
                "critic",
                critic,
                lambda request: {
                    "configuration": request["configuration"]["critic"],
                    "data": request["data"],
                },
            ),
            (
                "plasticity",
                plasticity,
                lambda request: {
                    "configuration": request["configuration"]["plasticity"],
                    "data": request["data"],
                    "modulators": request["critic"],
                },
            ),
        ],
    )


def _credit_propose(rng):
    scenario = generators.propose_reward_scenario(rng)
    return scenario, None, generators.predict_reward_effect(scenario)


def _credit_checks(record):
    measured = record["result"]["measured"]
    findings = []
    critic = measured.get("critic")
    plasticity = measured.get("plasticity")
    if not isinstance(critic, dict) or not isinstance(plasticity, dict):
        return ["result.measured must carry both a critic and a plasticity stage"]

    outcome = record["scenario"]["outcome"]
    expected_rpe = outcome["received_reward"] - outcome["expected_value"]
    if abs(critic["reward_prediction_error"] - expected_rpe) > ROUNDING_TOL:
        findings.append("critic.reward_prediction_error does not match the scenario outcome")
    for level in ("dopamine", "serotonin", "acetylcholine", "norepinephrine"):
        if not 0.0 <= critic[level] <= 1.0:
            findings.append(f"critic.{level} is outside [0, 1]")

    before = plasticity["weights_before"]
    after = plasticity["weights_after"]
    deltas = plasticity["weight_deltas"]
    if not (len(before) == len(after) == len(deltas)):
        findings.append("plasticity weight vectors have inconsistent lengths")
    else:
        for index, (start, end, delta) in enumerate(zip(before, after, deltas)):
            if abs((start + delta) - end) > ROUNDING_TOL:
                findings.append(f"weight {index} does not satisfy after = before + delta")
    applied = any(abs(delta) > sim.WEIGHT_UPDATE_EPS for delta in deltas)
    if plasticity["update_applied"] != applied:
        findings.append("plasticity.update_applied disagrees with the weight deltas")
    if "post_update_behavior" not in plasticity or "pre_update_behavior" not in plasticity:
        findings.append("plasticity must report behaviour before and after the update")
    else:
        pre = plasticity["pre_update_behavior"]
        post = plasticity["post_update_behavior"]
        expected_behavior_delta = {
            "spike_count_delta": post["spike_count"] - pre["spike_count"],
            "output_rate_delta_hz": post["output_rate_hz"] - pre["output_rate_hz"],
            "first_spike_shift_ms": sim._optional_delta(
                post["first_spike_ms"], pre["first_spike_ms"]
            ),
        }
        behavior_delta = plasticity.get("behavior_delta")
        if not isinstance(behavior_delta, dict):
            findings.append("plasticity.behavior_delta must be an object")
        else:
            for field, expected in expected_behavior_delta.items():
                if not _measurement_matches(behavior_delta.get(field), expected):
                    findings.append(
                        f"plasticity.behavior_delta.{field} does not match the "
                        "pre/post behavior"
                    )
    return findings


# --------------------------------------------------------------------------
# Family 5: temporal-memory-spike-challenges  (oracle: recurrent SNN)
# --------------------------------------------------------------------------

MEMORY_UNITS = {
    "response": "output identity: A, B, or none",
    "response_latency_ms": TIME_UNITS,
    "output_spike_counts": "spikes",
    "memory_spike_counts": "spikes",
    "latch_last_spike_ms": TIME_UNITS,
    "duration_ms": TIME_UNITS,
    "energy_pJ": ENERGY_UNITS,
    "retention_horizon_ms": TIME_UNITS,
}

# How far a distractor is displaced when testing distractor invariance.
DISTRACTOR_SHIFT_MS = 7.0


def memory_request(scenario, intervention):
    del intervention
    config = sim.memory_config(scenario["network_variant"])
    return {
        "configuration": config,
        "data": {
            "task": {
                "cue": scenario["cue"],
                "cue_ms": scenario["cue_ms"],
                "probe_ms": scenario["probe_ms"],
                "distractor_ms": list(scenario["distractor_ms"]),
                "reset_ms": scenario["reset_ms"],
            }
        },
    }


def _shift_distractors(task):
    """Move every distractor later, keeping it strictly inside the delay."""
    limit = task["probe_ms"] - 5.0
    shifted = []
    for time_ms in task["distractor_ms"]:
        moved = time_ms + DISTRACTOR_SHIFT_MS
        if moved >= limit:
            moved = max(task["cue_ms"] + 5.0, time_ms - DISTRACTOR_SHIFT_MS)
        shifted.append(moved)
    return sorted(shifted)


def _memory_reference(request):
    config = request["configuration"]
    task = request["data"]["task"]
    baseline = sim.run_memory_task(task, config)

    probes = {}
    ablated = dict(task, cue=None)
    probes["cue_ablation"] = sim.run_memory_task(ablated, config)
    if task.get("reset_ms") is not None:
        no_reset = dict(task, reset_ms=None)
        probes["reset_ablation"] = sim.run_memory_task(no_reset, config)
    if task["distractor_ms"]:
        swapped = dict(task, distractor_ms=_shift_distractors(task))
        probes["distractor_swap"] = sim.run_memory_task(swapped, config)

    differing = sorted(
        name
        for name, result in probes.items()
        if name != "distractor_swap" and result["response"] != baseline["response"]
    )
    measured = {
        "baseline": baseline,
        "probes": probes,
        "temporal_dependence": {
            "demonstrated": bool(differing),
            "changed_by": differing,
            "method": (
                "re-ran the same network with the cue removed (and, when present, "
                "with the reset removed); a record counts as temporally dependent "
                "only if that changes the measured response"
            ),
        },
        "distractor_invariant": (
            probes["distractor_swap"]["response"] == baseline["response"]
            if "distractor_swap" in probes
            else None
        ),
        "delay_ms": task["probe_ms"] - task["cue_ms"],
    }
    return measured, MEMORY_UNITS


def _memory_oracle(environ=None):
    return oracles.bind(
        runtime="recurrent-snn",
        oracle_id="rsnn-ref",
        oracle_type="recurrent-snn",
        description=(
            "Two mutually inhibiting delay loops read out through a probe gate; "
            "retention is limited by the loops' own spike-frequency adaptation"
        ),
        reference_fn=_memory_reference,
        environ=environ,
    )


def _memory_propose(rng):
    scenario = generators.propose_memory_scenario(rng)
    return scenario, None, generators.predict_memory_response(scenario)


def _memory_checks(record):
    measured = record["result"]["measured"]
    baseline = measured["baseline"]
    findings = []
    if baseline["response"] not in ("A", "B", "none"):
        findings.append(f"unexpected response: {baseline['response']!r}")
    if baseline["response_ambiguous"]:
        findings.append("both readouts fired on the same step; the response is ambiguous")
    latency = baseline["response_latency_ms"]
    if latency is not None and latency < 0:
        findings.append("response_latency_ms is negative")
    if baseline["spike_budget_exhausted"]:
        findings.append("the trial hit the spike budget; the trajectory is truncated")
    probes = measured["probes"]
    differing = sorted(
        name
        for name in ("cue_ablation", "reset_ablation")
        if name in probes and probes[name]["response"] != baseline["response"]
    )
    dependence = measured["temporal_dependence"]
    if dependence.get("demonstrated") != bool(differing):
        findings.append(
            "temporal_dependence.demonstrated does not match the ablation responses"
        )
    if dependence.get("changed_by") != differing:
        findings.append("temporal_dependence.changed_by does not match the changed controls")
    if not differing:
        findings.append(
            "no temporal dependence: removing the earlier events left the measured "
            "response unchanged"
        )
    if "cue_ablation" not in probes:
        findings.append("the cue-ablation control is missing")
    return findings


# --------------------------------------------------------------------------
# Candidate scoring: was the generator's guess right? Never authoritative,
# but it is what makes these records useful as evaluation data.
# --------------------------------------------------------------------------


def _guess(record, key):
    candidate = record.get("candidate_prediction")
    if not isinstance(candidate, dict):
        return None
    return candidate.get(key)


def _score_encoder(record):
    predicted = _guess(record, "predicted_winner")
    return None if predicted is None else predicted == record["result"]["measured"]["winner"]


def _score_neuron(record):
    predicted = _guess(record, "predicted_direction")
    if predicted is None:
        return None
    return predicted == record["result"]["measured"]["delta"]["direction"]


def _score_mesh(record):
    predicted = _guess(record, "predicted_sink_reached")
    if predicted is None:
        return None
    return predicted == record["result"]["measured"]["after"]["sink_reached"]


def _score_credit(record):
    """Scored on which synapse moves most, not on valence or net direction.

    Valence is the sign of received minus expected, which is exactly how the
    critic defines it, and the net weight direction follows that sign whenever
    causal pre-post pairs dominate — both would be near-tautological. Which
    synapse gains the most depends on spike timing relative to the readout,
    which the generator does not simulate.
    """
    predicted = _guess(record, "predicted_strongest_synapse")
    if predicted is None:
        return None
    deltas = record["result"]["measured"]["plasticity"]["weight_deltas"]
    if not deltas or all(abs(delta) <= sim.WEIGHT_UPDATE_EPS for delta in deltas):
        return None
    strongest = max(range(len(deltas)), key=lambda index: (abs(deltas[index]), -index))
    return predicted == strongest


def _score_memory(record):
    predicted = _guess(record, "predicted_response")
    if predicted is None:
        return None
    return predicted == record["result"]["measured"]["baseline"]["response"]


SPECS = {
    ENCODER_FAMILY: FamilySpec(
        name=ENCODER_FAMILY,
        runtimes=("axon-encoder",),
        oracle_type="spike-encoder",
        propose=_encoder_propose,
        build_request=encoder_request,
        build_oracle=_encoder_oracle,
        checks=_encoder_checks,
        score=_score_encoder,
    ),
    NEURON_FAMILY: FamilySpec(
        name=NEURON_FAMILY,
        runtimes=("neuromod",),
        oracle_type="neuron-simulation",
        propose=_neuron_propose,
        build_request=neuron_request,
        build_oracle=_neuron_oracle,
        checks=_neuron_checks,
        score=_score_neuron,
    ),
    MESH_FAMILY: FamilySpec(
        name=MESH_FAMILY,
        runtimes=("synaptic-mesh",),
        oracle_type="network-simulation",
        propose=_mesh_propose,
        build_request=mesh_request,
        build_oracle=_mesh_oracle,
        checks=_mesh_checks,
        score=_score_mesh,
    ),
    CREDIT_FAMILY: FamilySpec(
        name=CREDIT_FAMILY,
        runtimes=("limbic-critic", "plasticity-lab"),
        oracle_type="critic-plasticity-chain",
        propose=_credit_propose,
        build_request=credit_request,
        build_oracle=_credit_oracle,
        checks=_credit_checks,
        score=_score_credit,
    ),
    MEMORY_FAMILY: FamilySpec(
        name=MEMORY_FAMILY,
        runtimes=("recurrent-snn",),
        oracle_type="recurrent-snn",
        propose=_memory_propose,
        build_request=memory_request,
        build_oracle=_memory_oracle,
        checks=_memory_checks,
        score=_score_memory,
    ),
}

ALL_RUNTIMES = tuple(
    dict.fromkeys(runtime for spec in SPECS.values() for runtime in spec.runtimes)
)


def spec_for(family):
    if family not in SPECS:
        raise KeyError(f"unknown dataset family: {family}")
    return SPECS[family]
