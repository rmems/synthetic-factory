"""Focused cases split from test_oracle_grounded_record.py."""

from test_oracle_grounded_record import (
    build,
    families,
    math,
    relabel_as_named_runtime,
    result_findings,
    unittest,
)


class FamilyInvariantsCase28(unittest.TestCase):
    def test_a_named_runtime_encoder_result_is_not_required_to_match_the_reference(self):
        # The named-runtime protocol does not require agreement with this
        # Python reference -- that disagreement is exactly what makes
        # testing a real runtime meaningful. Only reference-implementation
        # records are authenticated by rerunning the reference here; a
        # named-runtime record is authenticated through its own reproduction
        # path (record.reproduce against the actual bound adapter) instead.
        item = relabel_as_named_runtime(build(families.ENCODER_FAMILY))
        state = item["result"]["measured"]["encoding_a"]
        signal = item["scenario"]["signal"]
        state["reconstruction"] = [value + 0.01 for value in signal]
        findings = result_findings(item)
        gated = (
            "representation_excerpt is not the prefix",
            "spike_train_digest does not match the recomputed",
            "reconstruction does not match the recomputed decode",
            "spike_count does not match the recomputed encode",
        )
        self.assertFalse(
            [f for f in findings if any(message in f for message in gated)],
            findings,
        )


class FamilyInvariantsCase29(unittest.TestCase):
    def test_impossible_neuron_voltage_summaries_are_rejected(self):
        item = build(families.NEURON_FAMILY)
        item["result"]["measured"]["before"]["v_min"] = 10.0
        item["result"]["measured"]["before"]["v_max"] = -10.0
        findings = result_findings(item)
        self.assertTrue(any("v_min is greater than v_max" in finding for finding in findings), findings)


class FamilyInvariantsCase30(unittest.TestCase):
    def test_neuron_trace_is_bound_to_the_rerun_of_the_reference_simulation(self):
        # The per-sample bounds check alone only requires each retained trace
        # sample to lie within its own retained v_min/v_max -- replacing the
        # whole trace with a constant inside those bounds (v_mean always is)
        # still passes that check. Only comparing against an independent
        # rerun of the reference simulation catches the forged trace.
        item = build(families.NEURON_FAMILY)
        before = item["result"]["measured"]["before"]
        before["v_trace"] = [before["v_mean"]] * len(before["v_trace"])
        findings = result_findings(item)
        self.assertTrue(
            any(
                "before does not match the rerun of the reference simulation" in f
                for f in findings
            ),
            findings,
        )


class FamilyInvariantsCase31(unittest.TestCase):
    def test_a_named_runtime_neuron_result_is_not_required_to_match_the_reference(self):
        item = relabel_as_named_runtime(build(families.NEURON_FAMILY))
        before = item["result"]["measured"]["before"]
        before["v_trace"] = [before["v_mean"]] * len(before["v_trace"])
        findings = result_findings(item)
        self.assertFalse(
            [f for f in findings if "does not match the rerun of the reference simulation" in f],
            findings,
        )


class FamilyInvariantsCase32(unittest.TestCase):
    def test_the_credit_chain_reports_both_stages(self):
        item = build(families.CREDIT_FAMILY)
        self.assertEqual(
            [stage["oracle_id"] for stage in item["oracle"]["stages"]],
            ["critic-ref", "plasticity-ref"],
        )
        self.assertEqual(sorted(item["result"]["measured"]), ["critic", "plasticity"])
        self.assertEqual(item["oracle"]["requested_runtime"], ["limbic-critic", "plasticity-lab"])


class FamilyInvariantsCase33(unittest.TestCase):
    def test_memory_response_latency_is_derived_from_the_first_readout_spike(self):
        item = next(
            build(families.MEMORY_FAMILY, index)
            for index in range(24)
            if build(families.MEMORY_FAMILY, index)["result"]["measured"]["baseline"]["response"]
            in ("A", "B")
        )
        trial = item["result"]["measured"]["baseline"]
        original = trial["response_latency_ms"]
        window = item["oracle"]["configuration"]["response_window_ms"]
        forged = 0.0 if not math.isclose(original, 0.0) else min(1.0, window)
        self.assertIsNotNone(original)
        self.assertNotEqual(original, forged)
        self.assertGreaterEqual(forged, 0.0)
        self.assertLessEqual(forged, window)
        trial["response_latency_ms"] = forged
        findings = result_findings(item)
        self.assertTrue(
            any("response_latency_ms" in f and "first readout spike" in f for f in findings),
            findings,
        )


class FamilyInvariantsCase34(unittest.TestCase):
    def test_memory_trial_is_bound_to_the_complete_reference_replay(self):
        # memory_spike_counts is otherwise only checked for its key set, not
        # against an independent rerun: a forged count alone is still
        # self-consistent with every other retained field (it does not feed
        # response/response_ambiguous, which come from output_spike_counts).
        item = next(
            build(families.MEMORY_FAMILY, index)
            for index in range(24)
            if build(families.MEMORY_FAMILY, index)["result"]["measured"]["baseline"]["response"]
            in ("A", "B")
        )
        trial = item["result"]["measured"]["baseline"]
        trial["memory_spike_counts"]["MA"] += 1
        findings = result_findings(item)
        self.assertTrue(
            any("baseline does not match the complete reference replay" in f for f in findings),
            findings,
        )


class FamilyInvariantsCase35(unittest.TestCase):
    def test_a_named_runtime_memory_result_is_not_required_to_match_the_reference(self):
        base = next(
            build(families.MEMORY_FAMILY, index)
            for index in range(24)
            if build(families.MEMORY_FAMILY, index)["result"]["measured"]["baseline"]["response"]
            in ("A", "B")
        )
        item = relabel_as_named_runtime(base)
        trial = item["result"]["measured"]["baseline"]
        trial["memory_spike_counts"]["MA"] += 1
        findings = result_findings(item)
        self.assertFalse(
            [f for f in findings if "does not match the complete reference replay" in f],
            findings,
        )

