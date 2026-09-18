"""Neuromodulator credit family wiring and invariant checks."""

from . import generators, oracles, sim
from .family_credit_checks import CreditChecks
from .family_common import DIMENSIONLESS, RATE_UNITS, TIME_UNITS

# --------------------------------------------------------------------------
# Family 4: neuromodulator-credit-assignment  (limbic-critic -> plasticity-lab)
# --------------------------------------------------------------------------

NORMALIZED_LEVEL_UNITS = "dimensionless, normalized level in [0, 1]"

CRITIC_UNITS = {
    "reward_prediction_error": "reward units (received - expected)",
    "dopamine_phasic": "dimensionless, signed burst/dip in [-1, 1]",
    "dopamine": NORMALIZED_LEVEL_UNITS,
    "serotonin": NORMALIZED_LEVEL_UNITS,
    "acetylcholine": NORMALIZED_LEVEL_UNITS,
    "norepinephrine": NORMALIZED_LEVEL_UNITS,
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


_FAMILY_CREDIT_CHECKS = CreditChecks()
_credit_behavior_delta_findings = _FAMILY_CREDIT_CHECKS._credit_behavior_delta_findings
_credit_behavior_findings = _FAMILY_CREDIT_CHECKS._credit_behavior_findings
_credit_behavior_summary_findings = _FAMILY_CREDIT_CHECKS._credit_behavior_summary_findings
_credit_checks = _FAMILY_CREDIT_CHECKS._credit_checks
_credit_critic_findings = _FAMILY_CREDIT_CHECKS._credit_critic_findings
_credit_rule_findings = _FAMILY_CREDIT_CHECKS._credit_rule_findings
_credit_scenario_findings = _FAMILY_CREDIT_CHECKS._credit_scenario_findings
_credit_update_findings = _FAMILY_CREDIT_CHECKS._credit_update_findings
_credit_update_metadata_findings = _FAMILY_CREDIT_CHECKS._credit_update_metadata_findings
_stage_is_reference = _FAMILY_CREDIT_CHECKS._stage_is_reference
