"""Generator side of family 4: neuromodulator-credit-assignment.

Proposes a reward situation — an outcome with expectation, surprise, risk,
novelty and effort, plus the pre-synaptic circuit it lands on — and a valence
hunch from the sign of the reward-prediction error. No critic or plasticity
rule runs here; the busiest-train guess exists to be scored, not trusted.
"""

from . import sim

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
