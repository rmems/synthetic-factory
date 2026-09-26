"""Focused cases split from test_oracle_grounded_record.py."""

from test_oracle_grounded_record import (
    build,
    canon,
    copy,
    families,
    record,
    relabel_as_named_runtime,
    result_findings,
    sim,
    unittest,
)


class FamilyInvariantsCase36(unittest.TestCase):
    def test_memory_response_labels_are_derived_for_baseline_and_every_control(self):
        item = next(
            build(families.MEMORY_FAMILY, index)
            for index in range(24)
            if len(build(families.MEMORY_FAMILY, index)["result"]["measured"]["probes"]) > 1
        )
        measured = item["result"]["measured"]
        trials = [("baseline", measured["baseline"]), *sorted(measured["probes"].items())]
        for name, _trial in trials:
            candidate = copy.deepcopy(item)
            target = (
                candidate["result"]["measured"]["baseline"]
                if name == "baseline"
                else candidate["result"]["measured"]["probes"][name]
            )
            target["response"] = "B" if target["response"] != "B" else "A"
            target["response_latency_ms"] = 0.0
            findings = result_findings(candidate)
            with self.subTest(trial=name):
                self.assertTrue(
                    any(f"{name}.response does not match" in f for f in findings),
                    findings,
                )


class FamilyInvariantsCase37(unittest.TestCase):
    def test_memory_ambiguity_is_derived_from_both_output_counts(self):
        item = build(families.MEMORY_FAMILY)
        trial = item["result"]["measured"]["baseline"]
        trial["output_spike_counts"] = {"OA": 1, "OB": 1}
        trial["response"] = "none"
        trial["response_latency_ms"] = None
        trial["response_ambiguous"] = False
        findings = result_findings(item)
        self.assertTrue(
            any("baseline.response_ambiguous does not match" in f for f in findings),
            findings,
        )


class FamilyInvariantsCase38(unittest.TestCase):
    def test_a_mesh_sink_flag_that_contradicts_the_arrivals_is_caught(self):
        item = build(families.MESH_FAMILY)
        before = item["result"]["measured"]["before"]
        before["sink_reached"] = not before["sink_reached"]
        item["result_hash"] = canon.digest(item["result"])
        findings = record.validate_record(item, check_declared_status=False)
        self.assertTrue(any("sink_reached" in f for f in findings), findings)


class FamilyInvariantsCase39(unittest.TestCase):
    def test_mesh_spike_counts_are_bound_to_the_recomputed_trajectory(self):
        # spike_counts is treated as primitive evidence elsewhere in these
        # checks: only its dependents (total_spikes, energy_pJ) are verified
        # against it, not against an independent rerun. Increasing an
        # already-active node's count and keeping those dependents
        # self-consistent with the forgery still passes every other check.
        item = next(
            build(families.MESH_FAMILY, index)
            for index in range(24)
            if any(
                count > 0
                for count in build(families.MESH_FAMILY, index)["result"]["measured"]["before"][
                    "spike_counts"
                ].values()
            )
        )
        before = item["result"]["measured"]["before"]
        node = next(n for n, count in before["spike_counts"].items() if count > 0)
        before["spike_counts"][node] += 1
        before["total_spikes"] += 1
        before["energy_pJ"] = before["total_spikes"] * sim.ENERGY_PJ_PER_SPIKE
        findings = result_findings(item)
        self.assertTrue(
            any("before does not match the rerun of the reference simulation" in f for f in findings),
            findings,
        )


class FamilyInvariantsCase40(unittest.TestCase):
    def test_a_named_runtime_mesh_result_is_not_required_to_match_the_reference(self):
        item = relabel_as_named_runtime(build(families.MESH_FAMILY))
        before = item["result"]["measured"]["before"]
        node = next(iter(before["spike_counts"]))
        before["spike_counts"][node] += 1
        before["total_spikes"] += 1
        before["energy_pJ"] = before["total_spikes"] * sim.ENERGY_PJ_PER_SPIKE
        findings = result_findings(item)
        self.assertFalse(
            [f for f in findings if "does not match the rerun of the reference simulation" in f],
            findings,
        )


class FamilyInvariantsCase41(unittest.TestCase):
    def test_mesh_propagation_delays_are_derived_from_arrival_times(self):
        item = build(families.MESH_FAMILY)
        measured = item["result"]["measured"]
        measured["before"]["propagation_delay_ms"] = 999.0
        measured["after"]["propagation_delay_ms"] = 998.0
        measured["delta"]["propagation_delay_delta_ms"] = -1.0
        item["result_hash"] = canon.digest(item["result"])
        findings = record.validate_record(item, check_declared_status=False)
        self.assertTrue(any("sink minus source arrival" in f for f in findings), findings)

        item = build(families.MESH_FAMILY)
        item["result"]["measured"]["delta"]["propagation_delay_delta_ms"] = 999.0
        item["result_hash"] = canon.digest(item["result"])
        findings = record.validate_record(item, check_declared_status=False)
        self.assertTrue(any("before/after delays" in f for f in findings), findings)


class FamilyInvariantsCase42(unittest.TestCase):
    def test_family_checks_survive_a_structurally_odd_record(self):
        item = build(families.MESH_FAMILY)
        item["result"]["measured"]["before"] = {}
        item["result_hash"] = canon.digest(item["result"])
        layers = record.classify(item)
        self.assertTrue(layers["envelope"] or layers["family"])


class FamilyInvariantsCase43(unittest.TestCase):
    def test_attribute_errors_from_malformed_family_shapes_become_findings(self):
        item = build(families.NEURON_FAMILY)
        item["oracle"]["configuration"]["after"] = []
        layers = record.classify(item)
        self.assertTrue(any("configuration" in f for f in layers["envelope"]))


class AuthoritativeRecordSemanticsCase01(unittest.TestCase):
    def test_the_declared_candidate_score_and_layer_checks_are_authenticated(self):
        item = build(families.ENCODER_FAMILY)
        score = item["validation"]["candidate_prediction_correct"]
        item["validation"]["candidate_prediction_correct"] = not score
        findings = record.validate_record(item)
        self.assertTrue(any("candidate_prediction_correct" in f for f in findings), findings)

        item = build(families.ENCODER_FAMILY)
        item["validation"]["checks"]["envelope"] = False
        findings = record.validate_record(item)
        self.assertTrue(any("validation.checks" in f for f in findings), findings)

        item = build(families.ENCODER_FAMILY)
        item["validation"]["checks"]["invented"] = True
        findings = record.validate_record(item)
        self.assertTrue(any("invented" in f for f in findings), findings)

        item = build(families.ENCODER_FAMILY)
        item["validation"]["reasons"] = ["accepted because I said so"]
        findings = record.validate_record(item)
        self.assertTrue(any("validation.reasons" in f for f in findings), findings)

