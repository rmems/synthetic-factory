"""Focused cases split from test_oracle_grounded_record.py."""

from test_oracle_grounded_record import (
    build,
    canon,
    families,
    record,
    unittest,
)


class DeclaredStatusCase05(unittest.TestCase):
    def rejected_memory_record(self):
        for index in range(24):
            item = build(families.MEMORY_FAMILY, index)
            if item["validation"]["status"] == "rejected":
                return item
        self.skipTest("no rejected temporal-memory record in the first 24 proposals")
        return None
    def test_a_rejected_record_keeps_a_clean_envelope(self):
        item = self.rejected_memory_record()
        layers = record.classify(item)
        self.assertEqual(layers["envelope"], [])
        self.assertEqual(layers["status"], [])
        self.assertTrue(layers["family"])


class FamilyInvariantsCase01(unittest.TestCase):
    def test_temporal_dependence_is_required(self):
        item = build(families.MEMORY_FAMILY)
        measured = item["result"]["measured"]
        if measured["temporal_dependence"]["demonstrated"]:
            self.assertEqual(item["validation"]["status"], "accepted")
        else:
            self.assertEqual(item["validation"]["status"], "rejected")
            self.assertTrue(any("temporal dependence" in r for r in item["validation"]["reasons"]))


class FamilyInvariantsCase02(unittest.TestCase):
    def test_a_forged_temporal_dependence_flag_is_caught(self):
        item = build(families.MEMORY_FAMILY)
        measured = item["result"]["measured"]
        measured["temporal_dependence"]["demonstrated"] = not measured["temporal_dependence"][
            "demonstrated"
        ]
        findings = record.validate_record(item)
        # Either the hash no longer covers the result, or the gate now disagrees
        # with the declared status. Both are fatal.
        self.assertTrue(findings)


class FamilyInvariantsCase03(unittest.TestCase):
    def test_temporal_dependence_is_derived_from_the_ablation_responses(self):
        item = next(
            build(families.MEMORY_FAMILY, index)
            for index in range(24)
            if build(families.MEMORY_FAMILY, index)["validation"]["status"] == "accepted"
        )
        measured = item["result"]["measured"]
        for probe in measured["probes"].values():
            probe["response"] = measured["baseline"]["response"]
            probe["state_retained_at_probe"] = measured["baseline"][
                "state_retained_at_probe"
            ]
        measured["temporal_dependence"]["demonstrated"] = True
        measured["temporal_dependence"]["changed_by"] = ["cue_ablation"]
        item["result_hash"] = canon.digest(item["result"])
        findings = record.validate_record(item, check_declared_status=False)
        self.assertTrue(any("demonstrated" in f for f in findings), findings)
        self.assertTrue(any("changed_by" in f for f in findings), findings)


class FamilyInvariantsCase04(unittest.TestCase):
    def test_retained_latch_state_counts_as_temporal_dependence(self):
        baseline = {"response": "none", "state_retained_at_probe": True}
        same = {"response": "none", "state_retained_at_probe": True}
        latch_gone = {"response": "none", "state_retained_at_probe": False}
        self.assertFalse(families._memory_ablation_changed(baseline, same))
        self.assertTrue(families._memory_ablation_changed(baseline, latch_gone))
        self.assertTrue(
            families._memory_ablation_changed(
                {"response": "A", "state_retained_at_probe": True},
                {"response": "none", "state_retained_at_probe": True},
            )
        )


class FamilyInvariantsCase05(unittest.TestCase):
    def test_the_cue_ablation_control_is_always_present(self):
        for index in range(6):
            item = build(families.MEMORY_FAMILY, index)
            with self.subTest(index=index):
                self.assertIn("cue_ablation", item["result"]["measured"]["probes"])


class FamilyInvariantsCase06(unittest.TestCase):
    def test_an_ambiguous_response_is_rejected(self):
        item = build(families.MEMORY_FAMILY)
        item["result"]["measured"]["baseline"]["response_ambiguous"] = True
        item["result_hash"] = canon.digest(item["result"])
        findings = record.validate_record(item, check_declared_status=False)
        self.assertTrue(any("ambiguous" in f for f in findings), findings)


class FamilyInvariantsCase07(unittest.TestCase):
    def test_the_neuron_intervention_changes_exactly_one_parameter(self):
        for index in range(6):
            item = build(families.NEURON_FAMILY, index)
            configuration = item["oracle"]["configuration"]
            changed = [
                key
                for key in configuration["before"]
                if configuration["before"][key] != configuration["after"][key]
            ]
            with self.subTest(index=index):
                self.assertEqual(changed, [configuration["intervened_parameter"]])


class FamilyInvariantsCase08(unittest.TestCase):
    def test_a_second_changed_neuron_parameter_is_caught(self):
        item = build(families.NEURON_FAMILY)
        item["oracle"]["configuration"]["after"]["v_rest"] = 0.25
        findings = record.validate_record(item, check_declared_status=False)
        self.assertTrue(any("configuration" in f for f in findings), findings)


class FamilyInvariantsCase09(unittest.TestCase):
    def test_an_inconsistent_neuron_delta_is_caught(self):
        item = build(families.NEURON_FAMILY)
        item["result"]["measured"]["delta"]["spike_count_delta"] += 3
        item["result_hash"] = canon.digest(item["result"])
        findings = record.validate_record(item, check_declared_status=False)
        self.assertTrue(any("spike_count_delta" in f for f in findings), findings)


class FamilyInvariantsCase10(unittest.TestCase):
    def test_every_redundant_neuron_delta_is_recomputed(self):
        for field in (
            "mean_rate_delta_hz",
            "first_spike_shift_ms",
            "mean_isi_delta_ms",
            "v_mean_delta",
        ):
            item = build(families.NEURON_FAMILY)
            item["result"]["measured"]["delta"][field] = 123.456
            item["result_hash"] = canon.digest(item["result"])
            findings = record.validate_record(item, check_declared_status=False)
            with self.subTest(field=field):
                self.assertTrue(any(field in f for f in findings), findings)


class FamilyInvariantsCase11(unittest.TestCase):
    def test_an_encoder_winner_outside_the_pair_is_caught(self):
        item = build(families.ENCODER_FAMILY)
        pair = item["scenario"]["encoding_pair"]
        outsider = next(e for e in ("rate", "latency", "delta", "temporal") if e not in pair)
        item["result"]["measured"]["winner"] = outsider
        item["result_hash"] = canon.digest(item["result"])
        findings = record.validate_record(item, check_declared_status=False)
        self.assertTrue(any("not one of the compared encodings" in f for f in findings))

