"""Family 4: neuromodulator-credit-assignment  (limbic-critic -> plasticity-lab).

A reward outcome is turned into modulator levels by the critic stage, and the
plasticity stage applies the three-factor update those levels dictate, re-
running the circuit to measure the behavioural consequence. The checks bind
each retained weight delta to the executed update rule, and only reference
stages are additionally compared against recomputed STDP traces and circuit
replays.
"""

from dataclasses import dataclass
from itertools import pairwise

from . import canon, generators, oracles, sim
from .family_common import (
    DIMENSIONLESS,
    RATE_UNITS,
    TIME_UNITS,
    _guess,
    _measurement_matches,
    _stage_is_reference,
)

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


def credit_request(scenario, _intervention):
    # The outcome itself is the intervention here, so nothing else reaches
    # the request.
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
        identity=oracles.OracleIdentity(
            oracle_id="critic-ref",
            oracle_type="critic",
            description="Reference reward critic mapping an outcome to modulator levels",
        ),
        reference_fn=_critic_reference,
        environ=environ,
    )
    plasticity = oracles.bind(
        runtime="plasticity-lab",
        identity=oracles.OracleIdentity(
            oracle_id="plasticity-ref",
            oracle_type="plasticity",
            description=(
                "Reference three-factor STDP that applies the weight update and "
                "re-runs the circuit to measure the post-update behaviour"
            ),
        ),
        reference_fn=_plasticity_reference,
        environ=environ,
    )
    return oracles.ChainOracle(
        # Built from the resolved adapters so a half-bound chain does not claim
        # to be the all-reference one.
        oracles.OracleIdentity(
            oracle_id=f"{critic.oracle_id}+{plasticity.oracle_id}",
            oracle_type="critic-plasticity-chain",
            description="limbic-critic -> plasticity-lab oracle path",
        ),
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


def _credit_critic_findings(record, critic):
    """(findings, critic_factors) for the critic stage.

    The documented boundary leaves agreement with the named runtimes
    unverified: only a reference critic stage is authenticated by rerunning
    the reference. The returned factors are the modulator levels the executed
    critic stage actually reported -- for a reference critic the recomputed
    values, so a forged retained level cannot feed the plasticity checks.
    """
    if not _stage_is_reference(record, "critic"):
        return [], critic
    findings = []
    outcome = record["scenario"]["outcome"]
    critic_config = record["oracle"]["configuration"]["critic"]
    expected_critic = sim.run_critic(outcome, critic_config)
    for field in (
        "reward_prediction_error",
        "dopamine_phasic",
        "dopamine",
        "serotonin",
        "acetylcholine",
        "norepinephrine",
        "valence",
    ):
        if not _measurement_matches(critic.get(field), expected_critic[field]):
            findings.append(
                f"critic.{field} does not match the value derived from the "
                "scenario outcome and critic configuration"
            )
    return findings, expected_critic


@dataclass(frozen=True)
class _WeightUpdateFactors:
    """Everything one weight's retained update is checked against."""

    start: float
    end: float
    delta: float
    bound_trace: float
    critic_factors: dict
    plasticity: dict
    plasticity_config: dict


def _credit_rule_findings(index, factors, findings):
    """Bind one weight's retained delta and after-weight to the update rule."""
    raw_delta = (
        factors.plasticity_config["learning_rate"]
        * factors.bound_trace
        * factors.critic_factors["dopamine_phasic"]
        * factors.plasticity["modulatory_gain"]
    )
    derived_after = sim.clamp(
        factors.start + raw_delta,
        factors.plasticity_config["w_min"],
        factors.plasticity_config["w_max"],
    )
    derived_delta = derived_after - factors.start
    if not _measurement_matches(factors.delta, derived_delta):
        findings.append(
            f"weight {index} delta does not match learning_rate * eligibility "
            "* dopamine_phasic * modulatory_gain with configured bounds"
        )
    if not _measurement_matches(factors.end, factors.start + derived_delta):
        findings.append(
            f"weight {index} does not satisfy after = before + delta "
            "derived from the retained learning rule"
        )
    return derived_delta


def _credit_vectors_consistent(plasticity, circuit):
    lengths = {
        len(plasticity["weights_before"]),
        len(plasticity["weights_after"]),
        len(plasticity["weight_deltas"]),
        len(plasticity["eligibility"]),
        len(circuit["initial_weights"]),
        len(circuit["pre_spike_times_ms"]),
    }
    return lengths == {circuit["pre_neuron_count"]}


def _credit_bound_trace(index, trace, expected_traces, findings):
    """The eligibility the update rule is checked against for one weight."""
    if expected_traces is None:
        return trace
    if not _measurement_matches(trace, expected_traces[index]):
        findings.append(
            f"weight {index} eligibility does not match the STDP trace "
            "derived from the pre-synaptic trains and pre-update spikes"
        )
    return expected_traces[index]


def _credit_update_findings(record, plasticity, critic_factors):
    """(findings, derived_deltas, expected_pre, expected_post) for the update.

    A named plasticity stage owns its spike timing, so its retained
    eligibility is the factor the update rule is checked against; only a
    reference stage is additionally compared against the recomputed STDP
    traces and circuit replays.
    """
    findings = []
    before = plasticity["weights_before"]
    scenario_circuit = record["scenario"]["circuit"]
    if before != scenario_circuit["initial_weights"]:
        findings.append("plasticity.weights_before does not match scenario.initial_weights")
    if not _credit_vectors_consistent(plasticity, scenario_circuit):
        findings.append("plasticity weight vectors have inconsistent lengths")
        return findings, [], None, None
    plasticity_config = record["oracle"]["configuration"]["plasticity"]
    pre_spikes = scenario_circuit["pre_spike_times_ms"]
    plasticity_is_reference = _stage_is_reference(record, "plasticity")
    expected_pre = None
    expected_traces = None
    if plasticity_is_reference:
        expected_pre = sim.plasticity_circuit(before, pre_spikes, plasticity_config)
        expected_traces = sim.eligibility_traces(
            before, pre_spikes, expected_pre["spike_times_ms"], plasticity_config
        )
    derived_deltas = []
    zipped = zip(
        before,
        plasticity["weights_after"],
        plasticity["weight_deltas"],
        plasticity["eligibility"],
        strict=True,
    )
    for index, (start, end, delta, trace) in enumerate(zipped):
        factors = _WeightUpdateFactors(
            start=start,
            end=end,
            delta=delta,
            bound_trace=_credit_bound_trace(index, trace, expected_traces, findings),
            critic_factors=critic_factors,
            plasticity=plasticity,
            plasticity_config=plasticity_config,
        )
        derived_deltas.append(_credit_rule_findings(index, factors, findings))
    expected_post = None
    if plasticity_is_reference:
        expected_post = sim.plasticity_circuit(plasticity["weights_after"], pre_spikes, plasticity_config)
    return findings, derived_deltas, expected_pre, expected_post


def _credit_one_behavior_findings(name, behavior, duration_ms, findings):
    times = behavior["spike_times_ms"]
    if any(later < earlier for earlier, later in pairwise(times)):
        findings.append(f"plasticity.{name}.spike_times_ms is not ordered")
    if any(time_ms < 0 or time_ms >= duration_ms for time_ms in times):
        findings.append(f"plasticity.{name}.spike_times_ms leaves the simulated duration")
    expected_summary = {
        "spike_count": len(times),
        "first_spike_ms": times[0] if times else None,
        "output_rate_hz": len(times) / (duration_ms / 1000.0),
    }
    for field, expected in expected_summary.items():
        if not _measurement_matches(behavior.get(field), expected):
            findings.append(f"plasticity.{name}.{field} does not match spike_times_ms")


def _credit_replay_findings(name, behavior, recomputed, findings):
    summary_keys = ("spike_count", "spike_times_ms", "first_spike_ms", "output_rate_hz")
    retained = {key: behavior.get(key) for key in summary_keys}
    measured = {key: recomputed.get(key) for key in summary_keys}
    if canon.normalize(retained) != canon.normalize(measured):
        findings.append(
            f"plasticity.{name} does not match a re-run of the circuit "
            "at the retained weights"
        )


def _credit_behavior_delta_findings(plasticity, findings):
    pre = plasticity["pre_update_behavior"]
    post = plasticity["post_update_behavior"]
    expected_behavior_delta = {
        "spike_count_delta": post["spike_count"] - pre["spike_count"],
        "output_rate_delta_hz": post["output_rate_hz"] - pre["output_rate_hz"],
        "first_spike_shift_ms": sim.optional_delta(post["first_spike_ms"], pre["first_spike_ms"]),
    }
    behavior_delta = plasticity.get("behavior_delta")
    if not isinstance(behavior_delta, dict):
        findings.append("plasticity.behavior_delta must be an object")
        return
    for field, expected in expected_behavior_delta.items():
        if not _measurement_matches(behavior_delta.get(field), expected):
            findings.append(
                f"plasticity.behavior_delta.{field} does not match the pre/post behavior"
            )


def _credit_behavior_findings(plasticity, plasticity_config, expected_pre, expected_post):
    """Findings on the retained pre/post circuit behaviour summaries."""
    if "post_update_behavior" not in plasticity or "pre_update_behavior" not in plasticity:
        return ["plasticity must report behaviour before and after the update"]
    findings = []
    duration_ms = plasticity_config["duration_ms"]
    sides = (
        ("pre_update_behavior", plasticity["pre_update_behavior"], expected_pre),
        ("post_update_behavior", plasticity["post_update_behavior"], expected_post),
    )
    for name, behavior, recomputed in sides:
        _credit_one_behavior_findings(name, behavior, duration_ms, findings)
        if recomputed is not None:
            _credit_replay_findings(name, behavior, recomputed, findings)
    _credit_behavior_delta_findings(plasticity, findings)
    return findings


def _credit_scenario_train_findings(record, findings):
    scenario_circuit = record["scenario"]["circuit"]
    for index, times in enumerate(scenario_circuit["pre_spike_times_ms"]):
        if any(later < earlier for earlier, later in pairwise(times)):
            findings.append(f"scenario pre-synaptic spike train {index} is not ordered")
        if any(time_ms < 0 or time_ms >= scenario_circuit["duration_ms"] for time_ms in times):
            findings.append(
                f"scenario pre-synaptic spike train {index} leaves the circuit duration"
            )


def _credit_gain_findings(record, plasticity, critic_factors, findings):
    # The gain coefficients belong to the plasticity configuration in records
    # produced by this family.
    plasticity_config = record["oracle"]["configuration"]["plasticity"]
    expected_gain = (
        1.0
        + plasticity_config["modulatory_gain_ach"] * critic_factors["acetylcholine"]
        + plasticity_config["modulatory_gain_ne"] * critic_factors["norepinephrine"]
    )
    if not _measurement_matches(plasticity["modulatory_gain"], expected_gain):
        findings.append("plasticity.modulatory_gain does not match critic modulators")
    if plasticity["update_rule"] != "dw = lr * eligibility * dopamine_phasic * modulatory_gain":
        findings.append("plasticity.update_rule does not name the executed update")


def _credit_applied_findings(plasticity, derived_deltas, findings):
    applied = (
        any(abs(delta) > sim.WEIGHT_UPDATE_EPS for delta in derived_deltas)
        if len(derived_deltas) == len(plasticity["weight_deltas"])
        else False
    )
    if plasticity["update_applied"] != applied:
        findings.append("plasticity.update_applied disagrees with the weight deltas")


def _credit_checks(record):
    measured = record["result"]["measured"]
    critic = measured.get("critic")
    plasticity = measured.get("plasticity")
    if not isinstance(critic, dict) or not isinstance(plasticity, dict):
        return ["result.measured must carry both a critic and a plasticity stage"]

    findings, critic_factors = _credit_critic_findings(record, critic)
    update_findings, derived_deltas, expected_pre, expected_post = _credit_update_findings(
        record, plasticity, critic_factors
    )
    findings.extend(update_findings)
    _credit_scenario_train_findings(record, findings)
    _credit_gain_findings(record, plasticity, critic_factors, findings)
    _credit_applied_findings(plasticity, derived_deltas, findings)
    plasticity_config = record["oracle"]["configuration"]["plasticity"]
    findings.extend(
        _credit_behavior_findings(plasticity, plasticity_config, expected_pre, expected_post)
    )
    return findings


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
