"""Focused cases split from test_oracle_grounded_record.py."""

from test_oracle_grounded_record import (
    build,
    canon,
    families,
    record,
    result_findings,
    sim,
    unittest,
)


class FamilyInvariantsCase12(unittest.TestCase):
    def test_encoder_tiebreak_and_tie_winners_are_recomputed(self):
        item = next(
            build(families.ENCODER_FAMILY, index)
            for index in range(200)
            if build(families.ENCODER_FAMILY, index)["result"]["measured"]["winner_basis"]
            == "spike_count_tiebreak"
        )
        measured = item["result"]["measured"]
        pair = item["scenario"]["encoding_pair"]
        measured["winner"] = pair[1] if measured["winner"] == pair[0] else pair[0]
        item["result_hash"] = canon.digest(item["result"])
        findings = record.validate_record(item, check_declared_status=False)
        self.assertTrue(any("spike_count_tiebreak" in f for f in findings), findings)

        item = build(families.ENCODER_FAMILY)
        measured = item["result"]["measured"]
        measured["encoding_b"]["information_retention"] = measured["encoding_a"][
            "information_retention"
        ]
        measured["encoding_b"]["spike_count"] = measured["encoding_a"]["spike_count"]
        measured["retention_margin"] = 0.0
        measured["winner_basis"] = "tie"
        measured["winner"] = item["scenario"]["encoding_pair"][0]
        item["result_hash"] = canon.digest(item["result"])
        findings = record.validate_record(item, check_declared_status=False)
        self.assertTrue(any("measured tie decision" in f for f in findings), findings)


class FamilyInvariantsCase13(unittest.TestCase):
    def test_an_unknown_encoder_winner_basis_is_rejected(self):
        item = build(families.ENCODER_FAMILY)
        item["result"]["measured"]["winner_basis"] = "trust-me"
        item["result_hash"] = canon.digest(item["result"])
        findings = record.validate_record(item, check_declared_status=False)
        self.assertTrue(any("winner_basis" in f for f in findings), findings)


class FamilyInvariantsCase14(unittest.TestCase):
    def test_a_broken_weight_identity_is_caught(self):
        item = build(families.CREDIT_FAMILY)
        item["result"]["measured"]["plasticity"]["weights_after"][0] += 0.5
        item["result_hash"] = canon.digest(item["result"])
        findings = record.validate_record(item, check_declared_status=False)
        self.assertTrue(any("after = before + delta" in f for f in findings), findings)


class FamilyInvariantsCase15(unittest.TestCase):
    def test_self_consistent_forged_weight_deltas_do_not_bypass_the_learning_rule(self):
        item = build(families.CREDIT_FAMILY)
        plasticity = item["result"]["measured"]["plasticity"]
        plasticity["weight_deltas"] = [0.0] * len(plasticity["weights_before"])
        plasticity["weights_after"] = list(plasticity["weights_before"])
        plasticity["update_applied"] = False
        item["result_hash"] = canon.digest(item["result"])
        findings = record.validate_record(item, check_declared_status=False)
        rule_findings = [finding for finding in findings if "retained learning rule" in finding]
        self.assertEqual(len(rule_findings), len(plasticity["weights_before"]), findings)


class FamilyInvariantsCase16(unittest.TestCase):
    def test_every_plasticity_behavior_delta_is_recomputed(self):
        for field in (
            "spike_count_delta",
            "output_rate_delta_hz",
            "first_spike_shift_ms",
        ):
            item = build(families.CREDIT_FAMILY)
            item["result"]["measured"]["plasticity"]["behavior_delta"][field] = 999
            item["result_hash"] = canon.digest(item["result"])
            findings = record.validate_record(item, check_declared_status=False)
            with self.subTest(field=field):
                self.assertTrue(any(field in f for f in findings), findings)


class FamilyInvariantsCase17(unittest.TestCase):
    def test_a_forged_update_applied_flag_is_caught(self):
        item = build(families.CREDIT_FAMILY)
        plasticity = item["result"]["measured"]["plasticity"]
        plasticity["update_applied"] = not plasticity["update_applied"]
        item["result_hash"] = canon.digest(item["result"])
        findings = record.validate_record(item, check_declared_status=False)
        self.assertTrue(any("update_applied" in f for f in findings), findings)


class FamilyInvariantsCase18(unittest.TestCase):
    def test_critic_modulators_are_recomputed_from_the_outcome(self):
        item = next(
            build(families.CREDIT_FAMILY, index)
            for index in range(24)
            if build(families.CREDIT_FAMILY, index)["validation"]["status"] == "accepted"
        )
        item["result"]["measured"]["critic"]["serotonin"] = 0.0
        findings = result_findings(item)
        self.assertTrue(any("critic.serotonin" in finding for finding in findings), findings)


class FamilyInvariantsCase19(unittest.TestCase):
    def test_eligibility_is_recomputed_before_the_weight_update(self):
        item = next(
            build(families.CREDIT_FAMILY, index)
            for index in range(24)
            if build(families.CREDIT_FAMILY, index)["validation"]["status"] == "accepted"
        )
        plasticity = item["result"]["measured"]["plasticity"]
        critic = item["result"]["measured"]["critic"]
        config = item["oracle"]["configuration"]["plasticity"]
        forged = [trace + 1.0 for trace in plasticity["eligibility"]]
        plasticity["eligibility"] = forged
        deltas = []
        updated = []
        for start, trace in zip(plasticity["weights_before"], forged, strict=True):
            raw_delta = (
                config["learning_rate"] * trace * critic["dopamine_phasic"] * plasticity["modulatory_gain"]
            )
            new_weight = sim.clamp(start + raw_delta, config["w_min"], config["w_max"])
            deltas.append(new_weight - start)
            updated.append(new_weight)
        plasticity["weight_deltas"] = deltas
        plasticity["weights_after"] = updated
        findings = result_findings(item)
        self.assertTrue(any("eligibility" in finding for finding in findings), findings)


class FamilyInvariantsCase20(unittest.TestCase):
    def test_post_update_behavior_is_re_run_from_the_updated_circuit(self):
        item = next(
            build(families.CREDIT_FAMILY, index)
            for index in range(24)
            if build(families.CREDIT_FAMILY, index)["validation"]["status"] == "accepted"
        )
        post = item["result"]["measured"]["plasticity"]["post_update_behavior"]
        post["spike_times_ms"] = []
        post["spike_count"] = 0
        post["first_spike_ms"] = None
        post["output_rate_hz"] = 0.0
        findings = result_findings(item)
        self.assertTrue(
            any("post_update_behavior" in finding and "re-run" in finding for finding in findings),
            findings,
        )

