#!/usr/bin/env python3
"""Unit tests for the deterministic pieces underneath the oracle boundary.

These cover the RNG, the canonical JSON layer, and each reference simulator.
The simulators stand in for runtimes that are not installed, so their job is to
be *deterministic and internally consistent*; these tests check exactly that,
and never that they agree with `axon-encoder`, `neuromod`, or any other absent
runtime.
"""

import math
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from oracle_grounded import canon, sim  # noqa: E402
from oracle_grounded.rng import Rng, seed_from_label  # noqa: E402


class DeterministicRng(unittest.TestCase):
    def test_same_seed_gives_the_same_stream(self):
        left = [Rng(7).random() for _ in range(5)]
        right = [Rng(7).random() for _ in range(5)]
        self.assertEqual(left, right)

    def test_different_seeds_diverge(self):
        self.assertNotEqual(
            [Rng(7).next_u64() for _ in range(3)],
            [Rng(8).next_u64() for _ in range(3)],
        )

    def test_random_stays_in_the_unit_interval(self):
        stream = Rng(11)
        for _ in range(500):
            value = stream.random()
            self.assertGreaterEqual(value, 0.0)
            self.assertLess(value, 1.0)

    def test_randint_is_inclusive_and_covers_its_range(self):
        stream = Rng(3)
        seen = {stream.randint(2, 5) for _ in range(200)}
        self.assertEqual(seen, {2, 3, 4, 5})

    def test_randint_rejects_an_empty_range(self):
        with self.assertRaises(ValueError):
            Rng(1).randint(5, 4)

    def test_sample_returns_distinct_items(self):
        picked = Rng(5).sample(range(10), 4)
        self.assertEqual(len(picked), 4)
        self.assertEqual(len(set(picked)), 4)

    def test_sample_refuses_to_overdraw(self):
        with self.assertRaises(ValueError):
            Rng(5).sample(range(3), 4)

    def test_derive_is_stable_and_label_dependent(self):
        base = Rng(99)
        self.assertEqual(base.derive("a").next_u64(), Rng(99).derive("a").next_u64())
        self.assertNotEqual(base.derive("a").next_u64(), base.derive("b").next_u64())

    def test_seed_from_label_is_deterministic(self):
        self.assertEqual(seed_from_label(1, "x"), seed_from_label(1, "x"))
        self.assertNotEqual(seed_from_label(1, "x"), seed_from_label(1, "y"))

    def test_symmetric_noise_is_centred(self):
        stream = Rng(21)
        values = [stream.symmetric_noise() for _ in range(2000)]
        self.assertTrue(all(-1.0 < value < 1.0 for value in values))
        self.assertLess(abs(sum(values) / len(values)), 0.05)


class CanonicalJson(unittest.TestCase):
    def test_key_order_does_not_change_the_digest(self):
        self.assertEqual(
            canon.digest({"a": 1, "b": 2}),
            canon.digest({"b": 2, "a": 1}),
        )

    def test_floats_are_rounded_to_canonical_precision(self):
        self.assertEqual(canon.normalize({"x": 0.1 + 0.2}), {"x": 0.3})

    def test_negative_zero_is_normalised(self):
        self.assertEqual(canon.canonical_json({"x": -0.0}), '{"x":0.0}')

    def test_non_finite_numbers_are_refused(self):
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.assertRaises(canon.NonFiniteNumber):
                canon.canonical_json({"x": value})

    def test_unsupported_types_are_refused(self):
        with self.assertRaises(TypeError):
            canon.canonical_json({"x": {1, 2}})

    def test_normalize_survives_a_round_trip(self):
        payload = {"a": [1.0000001, {"b": -0.0}], "c": "text", "d": None, "e": True}
        once = canon.normalize(payload)
        self.assertEqual(once, canon.normalize(once))

    def test_is_digest_accepts_only_sha256_strings(self):
        self.assertTrue(canon.is_digest(canon.digest({})))
        self.assertFalse(canon.is_digest("sha256:short"))
        self.assertFalse(canon.is_digest("deadbeef"))
        self.assertFalse(canon.is_digest(None))

    def test_digest_files_is_order_independent(self):
        here = Path(__file__).resolve().parent.parent / "pipelines" / "oracle_grounded"
        paths = [str(here / "sim.py"), str(here / "canon.py")]
        self.assertEqual(canon.digest_files(paths), canon.digest_files(reversed(paths)))


def ramp_signal(count=64):
    return [index / (count - 1) for index in range(count)]


class Encoders(unittest.TestCase):
    def setUp(self):
        self.config = sim.encoder_config()
        self.signal = ramp_signal()

    def test_every_encoding_produces_a_measurable_reconstruction(self):
        for encoding in sim.ENCODINGS:
            with self.subTest(encoding=encoding):
                measured = sim.run_encoder(self.signal, encoding, self.config)
                self.assertEqual(len(measured["reconstruction"]), len(self.signal))
                self.assertGreater(measured["spike_count"], 0)
                self.assertGreaterEqual(measured["information_retention"], 0.0)
                self.assertLessEqual(measured["information_retention"], 1.0)
                self.assertAlmostEqual(
                    measured["energy_pJ"],
                    measured["spike_count"] * sim.ENERGY_PJ_PER_SPIKE,
                )

    def test_spike_times_are_non_decreasing(self):
        for encoding in sim.ENCODINGS:
            with self.subTest(encoding=encoding):
                measured = sim.run_encoder(self.signal, encoding, self.config)
                times = [spike["t_ms"] for spike in measured["spikes"]]
                self.assertEqual(times, sorted(times))

    def test_encoding_is_deterministic(self):
        first = sim.run_encoder(self.signal, "delta", self.config)
        second = sim.run_encoder(self.signal, "delta", self.config)
        self.assertEqual(canon.digest(first), canon.digest(second))

    def test_unknown_encoding_is_refused(self):
        with self.assertRaises(ValueError):
            sim.run_encoder(self.signal, "morse", self.config)

    def test_rate_code_spike_count_tracks_signal_level(self):
        low = sim.run_encoder([0.1] * 32, "rate", self.config)["spike_count"]
        high = sim.run_encoder([0.9] * 32, "rate", self.config)["spike_count"]
        self.assertGreater(high, low)

    def test_latency_code_fires_earlier_for_larger_values(self):
        early = sim.encode_latency([0.9], self.config)[0]["t_ms"]
        late = sim.encode_latency([0.2], self.config)[0]["t_ms"]
        self.assertLess(early, late)

    def test_delta_code_is_silent_on_a_flat_signal_at_its_reference(self):
        flat = [self.config["delta_init"]] * 40
        self.assertEqual(sim.encode_delta(flat, self.config), [])

    def test_delta_code_emits_off_spikes_when_the_signal_falls(self):
        falling = [0.9] * 4 + [0.05] * 4
        channels = {s["channel"] for s in sim.encode_delta(falling, self.config)}
        self.assertIn("delta_off", channels)

    def test_temporal_code_emits_a_reference_and_a_phase_spike_per_sample(self):
        spikes = sim.encode_temporal([0.0, 0.5, 1.0], self.config)
        self.assertEqual(sum(1 for s in spikes if s["channel"] == "temporal_ref"), 3)
        self.assertEqual(sum(1 for s in spikes if s["channel"] == "temporal_phase"), 3)

    def test_identical_encodings_tie(self):
        comparison = sim.compare_encodings(self.signal, "rate", "rate", self.config)
        self.assertIsNone(comparison["winner"])
        self.assertEqual(comparison["winner_basis"], "tie")
        self.assertEqual(comparison["retention_margin"], 0.0)

    def test_the_winner_follows_the_measured_margin(self):
        comparison = sim.compare_encodings(self.signal, "temporal", "rate", self.config)
        if comparison["winner_basis"] == "information_retention":
            expected = "temporal" if comparison["retention_margin"] > 0 else "rate"
            self.assertEqual(comparison["winner"], expected)

    def test_pearson_is_none_for_a_constant_series(self):
        self.assertIsNone(sim.pearson([1.0, 1.0, 1.0], [1.0, 2.0, 3.0]))

    def test_pearson_is_one_for_a_perfect_match(self):
        self.assertAlmostEqual(sim.pearson([1.0, 2.0, 3.0], [2.0, 4.0, 6.0]), 1.0)


class NeuronDynamics(unittest.TestCase):
    def setUp(self):
        self.config = sim.neuron_config()
        self.steps = int(300.0 / self.config["dt_ms"])

    def drive(self, amplitude):
        return [amplitude] * self.steps

    def test_a_stronger_drive_produces_more_spikes(self):
        weak = sim.simulate_neuron(self.config, self.drive(1.2))
        strong = sim.simulate_neuron(self.config, self.drive(3.0))
        self.assertGreater(strong["spike_count"], weak["spike_count"])

    def test_raising_the_threshold_reduces_firing(self):
        base = sim.simulate_neuron(self.config, self.drive(2.0))
        raised = sim.simulate_neuron(
            sim.neuron_config({"v_threshold": 4.0}), self.drive(2.0)
        )
        self.assertLess(raised["spike_count"], base["spike_count"])

    def test_a_subthreshold_drive_never_fires(self):
        quiet = sim.simulate_neuron(self.config, self.drive(0.2))
        self.assertEqual(quiet["spike_count"], 0)
        self.assertIsNone(quiet["first_spike_ms"])
        self.assertIsNone(quiet["mean_isi_ms"])

    def test_the_refractory_period_bounds_the_rate(self):
        config = sim.neuron_config({"t_refractory_ms": 10.0})
        measured = sim.simulate_neuron(config, self.drive(6.0))
        intervals = [
            b - a for a, b in zip(measured["spike_times_ms"], measured["spike_times_ms"][1:])
        ]
        self.assertTrue(all(gap >= 10.0 for gap in intervals), intervals)

    def test_adaptation_slows_a_neuron_down(self):
        adapting = sim.simulate_neuron(
            sim.neuron_config({"adaptation_b": 0.4}), self.drive(3.0)
        )
        flat = sim.simulate_neuron(
            sim.neuron_config({"adaptation_b": 0.0}), self.drive(3.0)
        )
        self.assertLess(adapting["spike_count"], flat["spike_count"])

    def test_spike_count_matches_spike_times(self):
        measured = sim.simulate_neuron(self.config, self.drive(2.5))
        self.assertEqual(measured["spike_count"], len(measured["spike_times_ms"]))

    def test_the_trace_is_downsampled_to_the_requested_budget(self):
        measured = sim.simulate_neuron(self.config, self.drive(2.0), trace_points=20)
        self.assertLessEqual(len(measured["v_trace"]), 20)
        self.assertGreater(measured["v_trace_stride_ms"], 0)

    def test_simulation_is_deterministic(self):
        first = sim.simulate_neuron(self.config, self.drive(2.0))
        second = sim.simulate_neuron(self.config, self.drive(2.0))
        self.assertEqual(canon.digest(first), canon.digest(second))

    def test_the_comparison_reports_the_direction_of_the_change(self):
        quiet = sim.simulate_neuron(self.config, self.drive(0.2))
        loud = sim.simulate_neuron(self.config, self.drive(3.0))
        up = sim.compare_neuron_states(quiet, loud)
        self.assertEqual(up["direction"], "increases_firing")
        self.assertTrue(up["unsilenced"])
        down = sim.compare_neuron_states(loud, quiet)
        self.assertEqual(down["direction"], "decreases_firing")
        self.assertTrue(down["silenced"])
        same = sim.compare_neuron_states(quiet, quiet)
        self.assertEqual(same["direction"], "unchanged_firing")

    def test_every_intervention_target_names_a_real_parameter(self):
        for target, parameter in sim.INTERVENTION_TARGETS.items():
            with self.subTest(target=target):
                self.assertIn(parameter, sim.NEURON_DEFAULTS)


class DelayMesh(unittest.TestCase):
    def chain(self, delay_ms=5.0, weight=1.2):
        nodes = [sim.mesh_node("A"), sim.mesh_node("B")]
        edges = [{"src": "A", "dst": "B", "weight": weight, "delay_ms": delay_ms}]
        events = [{"target": "A", "t_ms": 2.0, "amplitude": 1.5}]
        return nodes, edges, events

    def test_propagation_delay_follows_the_edge_delay(self):
        for delay in (3.0, 8.0):
            nodes, edges, events = self.chain(delay_ms=delay)
            result = sim.simulate_mesh(nodes, edges, events, 60.0)
            summary = sim.mesh_causal_summary(result, "A", "B")
            self.assertTrue(summary["sink_reached"])
            self.assertAlmostEqual(summary["propagation_delay_ms"], delay, delta=1.0)

    def test_removing_the_edge_stops_the_sink_from_firing(self):
        nodes, _edges, events = self.chain()
        result = sim.simulate_mesh(nodes, [], events, 60.0)
        summary = sim.mesh_causal_summary(result, "A", "B")
        self.assertFalse(summary["sink_reached"])
        self.assertIsNone(summary["propagation_delay_ms"])

    def test_a_subthreshold_weight_does_not_recruit_the_sink(self):
        nodes, edges, events = self.chain(weight=0.2)
        result = sim.simulate_mesh(nodes, edges, events, 60.0)
        self.assertEqual(result["spike_counts"]["B"], 0)

    def test_inhibition_suppresses_a_downstream_node(self):
        nodes = [sim.mesh_node(name) for name in ("A", "I", "B")]
        excite = [
            {"src": "A", "dst": "B", "weight": 0.7, "delay_ms": 4.0},
            {"src": "A", "dst": "B", "weight": 0.7, "delay_ms": 4.5},
        ]
        events = [{"target": "A", "t_ms": 2.0, "amplitude": 1.5}]
        without = sim.simulate_mesh(nodes, excite, events, 60.0)
        inhibited = excite + [{"src": "I", "dst": "B", "weight": -1.0, "delay_ms": 1.0}]
        events_with_i = events + [{"target": "I", "t_ms": 4.0, "amplitude": 1.5}]
        with_inhibition = sim.simulate_mesh(nodes, inhibited, events_with_i, 60.0)
        self.assertGreater(without["spike_counts"]["B"], with_inhibition["spike_counts"]["B"])

    def test_firing_order_lists_each_node_once_in_time_order(self):
        nodes, edges, events = self.chain()
        result = sim.simulate_mesh(nodes, edges, events, 60.0)
        self.assertEqual(result["firing_order"], ["A", "B"])

    def test_an_unknown_edge_endpoint_is_refused(self):
        with self.assertRaises(ValueError):
            sim.simulate_mesh(
                [sim.mesh_node("A")],
                [{"src": "A", "dst": "Z", "weight": 1.0, "delay_ms": 1.0}],
                [],
                10.0,
            )

    def test_an_unknown_event_target_is_refused(self):
        with self.assertRaises(ValueError):
            sim.simulate_mesh(
                [sim.mesh_node("A")], [], [{"target": "Z", "t_ms": 1.0, "amplitude": 1.0}], 10.0
            )

    def test_a_runaway_loop_is_bounded_and_reported(self):
        nodes = [sim.mesh_node("A", t_refractory_ms=0.5)]
        edges = [{"src": "A", "dst": "A", "weight": 5.0, "delay_ms": 0.5}]
        events = [{"target": "A", "t_ms": 1.0, "amplitude": 2.0}]
        result = sim.simulate_mesh(nodes, edges, events, 5000.0, max_spikes=50)
        self.assertTrue(result["spike_budget_exhausted"])
        self.assertLessEqual(result["total_spikes"], 51)

    def test_the_causal_delta_names_suppressed_and_recruited_nodes(self):
        nodes, edges, events = self.chain()
        before = sim.mesh_causal_summary(sim.simulate_mesh(nodes, edges, events, 60.0), "A", "B")
        after = sim.mesh_causal_summary(sim.simulate_mesh(nodes, [], events, 60.0), "A", "B")
        delta = sim.mesh_causal_delta(before, after)
        self.assertEqual(delta["suppressed_nodes"], ["B"])
        self.assertEqual(delta["recruited_nodes"], [])
        self.assertTrue(delta["sink_reachability_changed"])


class CriticAndPlasticity(unittest.TestCase):
    def setUp(self):
        self.critic_config = sim.critic_config()
        self.plasticity_config = sim.plasticity_config()
        self.pre = [[10.0, 30.0, 50.0], [12.0, 34.0], [8.0, 60.0, 90.0], [20.0]]
        self.weights = [0.6, 0.5, 0.7, 0.4]

    def test_reward_prediction_error_is_received_minus_expected(self):
        measured = sim.run_critic(
            {"expected_value": 0.3, "received_reward": 0.8}, self.critic_config
        )
        self.assertAlmostEqual(measured["reward_prediction_error"], 0.5)
        self.assertEqual(measured["valence"], "positive")
        self.assertGreater(measured["dopamine_phasic"], 0.0)

    def test_a_disappointing_outcome_dips_dopamine(self):
        measured = sim.run_critic(
            {"expected_value": 0.9, "received_reward": 0.1}, self.critic_config
        )
        self.assertEqual(measured["valence"], "negative")
        self.assertLess(measured["dopamine_phasic"], 0.0)

    def test_a_met_expectation_is_neutral(self):
        measured = sim.run_critic(
            {"expected_value": 0.5, "received_reward": 0.5}, self.critic_config
        )
        self.assertEqual(measured["valence"], "neutral")
        self.assertEqual(measured["dopamine_phasic"], 0.0)

    def test_modulator_levels_stay_normalised(self):
        for expected, received in ((0.0, 1.0), (1.0, 0.0), (0.5, 0.5)):
            measured = sim.run_critic(
                {
                    "expected_value": expected,
                    "received_reward": received,
                    "risk": 1.0,
                    "novelty": 1.0,
                    "effort": 1.0,
                },
                self.critic_config,
            )
            for level in ("dopamine", "serotonin", "acetylcholine", "norepinephrine"):
                with self.subTest(level=level, expected=expected):
                    self.assertGreaterEqual(measured[level], 0.0)
                    self.assertLessEqual(measured[level], 1.0)

    def test_the_update_is_applied_and_the_arithmetic_closes(self):
        modulators = sim.run_critic(
            {"expected_value": 0.2, "received_reward": 0.9}, self.critic_config
        )
        measured = sim.run_plasticity(
            self.weights, self.pre, modulators, self.plasticity_config
        )
        self.assertTrue(measured["update_applied"])
        for before, after, delta in zip(
            measured["weights_before"], measured["weights_after"], measured["weight_deltas"]
        ):
            self.assertAlmostEqual(before + delta, after, places=9)

    def test_post_update_behaviour_is_a_measurement_of_the_updated_circuit(self):
        modulators = sim.run_critic(
            {"expected_value": 0.1, "received_reward": 1.0}, self.critic_config
        )
        measured = sim.run_plasticity(
            self.weights, self.pre, modulators, self.plasticity_config
        )
        # Re-run the circuit at the updated weights: it must reproduce exactly
        # what the record publishes as post_update_behavior.
        replay = sim._plasticity_circuit(
            measured["weights_after"], self.pre, self.plasticity_config
        )
        self.assertEqual(replay, measured["post_update_behavior"])

    def test_a_neutral_outcome_leaves_the_weights_alone(self):
        modulators = sim.run_critic(
            {"expected_value": 0.5, "received_reward": 0.5}, self.critic_config
        )
        measured = sim.run_plasticity(
            self.weights, self.pre, modulators, self.plasticity_config
        )
        self.assertFalse(measured["update_applied"])
        self.assertEqual(measured["weights_before"], measured["weights_after"])

    def test_reward_and_punishment_move_the_weights_in_opposite_directions(self):
        # Which way a given synapse moves is set by its eligibility sign, which
        # depends on spike timing; flipping the reward flips the third factor
        # and therefore every delta, symmetrically.
        rewarded = sim.run_plasticity(
            self.weights,
            self.pre,
            sim.run_critic({"expected_value": 0.1, "received_reward": 0.9}, self.critic_config),
            self.plasticity_config,
        )
        punished = sim.run_plasticity(
            self.weights,
            self.pre,
            sim.run_critic({"expected_value": 0.9, "received_reward": 0.1}, self.critic_config),
            self.plasticity_config,
        )
        self.assertNotEqual(sum(rewarded["weight_deltas"]), 0.0)
        self.assertLess(
            sum(rewarded["weight_deltas"]) * sum(punished["weight_deltas"]), 0.0
        )
        for up, down in zip(rewarded["weight_deltas"], punished["weight_deltas"]):
            self.assertAlmostEqual(up, -down, places=9)

    def test_weights_are_clamped_to_their_bounds(self):
        config = sim.plasticity_config({"learning_rate": 50.0, "w_max": 1.5, "w_min": 0.0})
        measured = sim.run_plasticity(
            self.weights,
            self.pre,
            sim.run_critic({"expected_value": 0.0, "received_reward": 1.0}, self.critic_config),
            config,
        )
        for weight in measured["weights_after"]:
            self.assertGreaterEqual(weight, 0.0)
            self.assertLessEqual(weight, 1.5)

    def test_eligibility_is_positive_when_the_post_spike_follows_the_pre_spike(self):
        config = sim.plasticity_config()
        traces = sim.eligibility_traces([1.0], [[10.0]], [15.0], config)
        self.assertGreater(traces[0], 0.0)

    def test_eligibility_is_negative_when_the_post_spike_leads(self):
        config = sim.plasticity_config()
        traces = sim.eligibility_traces([1.0], [[20.0]], [15.0], config)
        self.assertLess(traces[0], 0.0)


class RecurrentMemory(unittest.TestCase):
    def task(self, **overrides):
        base = {
            "cue": "A",
            "cue_ms": 20.0,
            "probe_ms": 200.0,
            "distractor_ms": [60.0, 110.0],
            "reset_ms": None,
        }
        base.update(overrides)
        return base

    def test_a_retained_cue_selects_the_matching_output(self):
        config = sim.memory_config({"latch_adaptation_b": 0.02})
        for cue in ("A", "B"):
            with self.subTest(cue=cue):
                measured = sim.run_memory_task(self.task(cue=cue), config)
                self.assertEqual(measured["response"], cue)
                self.assertFalse(measured["response_ambiguous"])
                self.assertTrue(measured["state_retained_at_probe"])
                self.assertGreaterEqual(measured["response_latency_ms"], 0.0)

    def test_removing_the_cue_removes_the_response(self):
        config = sim.memory_config({"latch_adaptation_b": 0.02})
        ablated = sim.run_memory_task(self.task(cue=None), config)
        self.assertEqual(ablated["response"], "none")
        self.assertIsNone(ablated["response_latency_ms"])

    def test_the_probe_alone_cannot_drive_an_output(self):
        config = sim.memory_config({"latch_adaptation_b": 0.02})
        measured = sim.run_memory_task(
            self.task(cue=None, distractor_ms=[]), config
        )
        self.assertEqual(measured["output_spike_counts"], {"OA": 0, "OB": 0})

    def test_a_fatiguing_loop_forgets_before_a_long_probe(self):
        config = sim.memory_config({"latch_adaptation_b": 0.07})
        measured = sim.run_memory_task(
            self.task(probe_ms=400.0, distractor_ms=[]), config
        )
        self.assertEqual(measured["response"], "none")
        self.assertFalse(measured["state_retained_at_probe"])

    def test_a_slower_fatiguing_loop_holds_the_same_cue(self):
        config = sim.memory_config({"latch_adaptation_b": 0.015})
        measured = sim.run_memory_task(
            self.task(probe_ms=400.0, distractor_ms=[]), config
        )
        self.assertEqual(measured["response"], "A")

    def test_a_reset_clears_the_stored_state(self):
        config = sim.memory_config({"latch_adaptation_b": 0.02})
        held = sim.run_memory_task(self.task(distractor_ms=[]), config)
        cleared = sim.run_memory_task(self.task(distractor_ms=[], reset_ms=100.0), config)
        self.assertEqual(held["response"], "A")
        self.assertEqual(cleared["response"], "none")

    def test_weak_distractors_do_not_disturb_the_stored_cue(self):
        config = sim.memory_config({"latch_adaptation_b": 0.02, "distractor_weight": 0.45})
        plain = sim.run_memory_task(self.task(distractor_ms=[]), config)
        noisy = sim.run_memory_task(
            self.task(distractor_ms=[50.0, 80.0, 120.0, 160.0]), config
        )
        self.assertEqual(plain["response"], noisy["response"])

    def test_longer_delays_cost_more_energy(self):
        config = sim.memory_config({"latch_adaptation_b": 0.015})
        short = sim.run_memory_task(self.task(probe_ms=120.0, distractor_ms=[]), config)
        long = sim.run_memory_task(self.task(probe_ms=400.0, distractor_ms=[]), config)
        self.assertGreater(long["energy_pJ"], short["energy_pJ"])
        self.assertAlmostEqual(
            long["energy_pJ"], long["total_spikes"] * sim.ENERGY_PJ_PER_SPIKE
        )

    def test_the_trial_is_deterministic(self):
        config = sim.memory_config()
        first = sim.run_memory_task(self.task(), config)
        second = sim.run_memory_task(self.task(), config)
        self.assertEqual(canon.digest(first), canon.digest(second))

    def test_output_neurons_need_both_the_loop_and_the_gate(self):
        # Each drive alone must stay below threshold, or a "response" would not
        # be evidence that the cue is still circulating.
        config = sim.memory_config()
        loop_asymptote = config["readout_weight"] / (
            1.0 - math.exp(-config["loop_delay_ms"] / config["output_tau_ms"])
        )
        probe_asymptote = config["gate_weight"] / (
            1.0 - math.exp(-config["probe_interval_ms"] / config["output_tau_ms"])
        )
        threshold = sim.MESH_NODE_DEFAULTS["v_threshold"]
        self.assertLess(loop_asymptote, threshold)
        self.assertLess(probe_asymptote, threshold)
        # The probe plateau plus a single loop arrival must clear threshold,
        # otherwise a retained cue could not produce a response at all.
        self.assertGreater(probe_asymptote + config["readout_weight"], threshold)


if __name__ == "__main__":
    unittest.main()
