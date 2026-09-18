"""Focused cases split from test_oracle_grounded_record.py."""

from test_oracle_grounded_record import (
    build,
    copy,
    families,
    forge_consistent_eligibility,
    record,
    relabel_as_named_runtime,
    relabel_plasticity_stage_as_named,
    result_findings,
    sim,
    unittest,
)


class FamilyInvariantsCase21(unittest.TestCase):
    def test_a_named_runtime_critic_result_is_not_required_to_match_the_reference(self):
        # The documented boundary leaves agreement with limbic-critic
        # unverified: a bound runtime returning a different in-range modulator
        # level is authenticated through its own reproduction path, not by
        # equality with sim.run_critic.
        item = relabel_as_named_runtime(build(families.CREDIT_FAMILY))
        critic = item["result"]["measured"]["critic"]
        critic["serotonin"] = (
            round(critic["serotonin"] + 0.07, 6)
            if critic["serotonin"] <= 0.9
            else round(critic["serotonin"] - 0.07, 6)
        )
        findings = result_findings(item)
        self.assertFalse(
            [f for f in findings if "derived from the scenario outcome" in f],
            findings,
        )


class FamilyInvariantsCase22(unittest.TestCase):
    def test_a_named_runtime_plasticity_result_is_not_required_to_match_the_reference(self):
        # A named plasticity-lab owns its spike timing and eligibility; only
        # the retained update rule still binds its outputs together.
        item = forge_consistent_eligibility(
            relabel_as_named_runtime(build(families.CREDIT_FAMILY))
        )
        findings = result_findings(item)
        gated = (
            "does not match the STDP trace",
            "does not match a re-run of the circuit",
        )
        self.assertFalse(
            [f for f in findings if any(message in f for message in gated)],
            findings,
        )


class FamilyInvariantsCase23(unittest.TestCase):
    def test_a_named_runtime_plasticity_update_must_still_follow_its_own_factors(self):
        # Scoping the reference rerun away must not unhook the update rule: a
        # named-runtime delta that contradicts the record's own retained
        # eligibility, dopamine, and gain is still rejected.
        item = relabel_as_named_runtime(build(families.CREDIT_FAMILY))
        plasticity = item["result"]["measured"]["plasticity"]
        plasticity["weight_deltas"][0] += 0.25
        plasticity["weights_after"][0] += 0.25
        findings = result_findings(item)
        self.assertTrue(
            any("weight 0 delta does not match" in f for f in findings),
            findings,
        )


class FamilyInvariantsCase24(unittest.TestCase):
    def test_a_mixed_chain_still_recomputes_the_reference_critic_stage(self):
        item = relabel_plasticity_stage_as_named(build(families.CREDIT_FAMILY))
        self.assertEqual(record.validate_record(item, check_declared_status=False), [])
        tolerated = forge_consistent_eligibility(copy.deepcopy(item))
        findings = result_findings(tolerated)
        self.assertFalse(
            [f for f in findings if "does not match the STDP trace" in f],
            findings,
        )
        forged = relabel_plasticity_stage_as_named(build(families.CREDIT_FAMILY))
        forged["result"]["measured"]["critic"]["serotonin"] = 0.0
        findings = result_findings(forged)
        self.assertTrue(
            any("critic.serotonin" in f for f in findings),
            findings,
        )


class FamilyInvariantsCase25(unittest.TestCase):
    def test_encoder_excerpt_is_bound_to_the_recomputed_spike_train(self):
        item = build(families.ENCODER_FAMILY)
        excerpt = item["result"]["measured"]["encoding_a"]["representation_excerpt"]
        self.assertTrue(excerpt)
        excerpt[0]["t_ms"] = excerpt[0]["t_ms"] + 1.0
        findings = result_findings(item)
        self.assertTrue(
            any("representation_excerpt is not the prefix" in finding for finding in findings),
            findings,
        )


class FamilyInvariantsCase26(unittest.TestCase):
    def test_encoder_reconstruction_is_bound_to_the_recomputed_decode(self):
        # The excerpt/digest checks authenticate the spike train, and the old
        # per-field checks only prove ``reconstruction`` is self-consistent
        # with the *other* stored metrics -- not that it is the true decode.
        # Forge a different decode and recompute every dependent field (and
        # the cross-side winner decision) exactly as a self-consistent forger
        # would, then confirm only comparing against the recomputed decode
        # itself catches it.
        item = build(families.ENCODER_FAMILY)
        measured = item["result"]["measured"]
        state = measured["encoding_a"]
        scenario = item["scenario"]
        signal = scenario["signal"]
        forged_decoded = [0.0 for _ in signal]
        errors = [abs(actual - guess) for actual, guess in zip(signal, forged_decoded, strict=True)]
        forged_rmse = sim.rmse(signal, forged_decoded)
        forged_retention = sim.clamp(1.0 - forged_rmse, 0.0, 1.0)
        state["reconstruction"] = forged_decoded
        state["rmse"] = forged_rmse
        state["mean_abs_error"] = sum(errors) / len(errors) if errors else 0.0
        state["max_abs_error"] = max(errors) if errors else 0.0
        state["pearson_r"] = sim.pearson(signal, forged_decoded)
        state["information_retention"] = forged_retention
        state["retention_per_spike"] = (
            forged_retention / state["spike_count"] if state["spike_count"] else None
        )
        # Keep the cross-side decision self-consistent too, so only the new
        # per-side recompute check (not a stale winner/margin) fires.
        retention_gap = state["information_retention"] - measured["encoding_b"]["information_retention"]
        measured["retention_margin"] = retention_gap
        tie_epsilon = item["oracle"]["configuration"]["tie_epsilon"]
        pair = scenario["encoding_pair"]
        if abs(retention_gap) >= tie_epsilon:
            measured["winner_basis"] = "information_retention"
            measured["winner"] = pair[0] if retention_gap > 0 else pair[1]
        elif state["spike_count"] != measured["encoding_b"]["spike_count"]:
            measured["winner_basis"] = "spike_count_tiebreak"
            measured["winner"] = (
                pair[0] if state["spike_count"] < measured["encoding_b"]["spike_count"] else pair[1]
            )
        else:
            measured["winner_basis"] = "tie"
            measured["winner"] = None
        findings = result_findings(item)
        self.assertEqual(
            [f for f in findings if "reconstruction" in f],
            ["encoding_a.reconstruction does not match the recomputed decode"],
            findings,
        )


class FamilyInvariantsCase27(unittest.TestCase):
    def test_encoder_spike_count_is_bound_to_the_recomputed_encode(self):
        item = build(families.ENCODER_FAMILY)
        item["result"]["measured"]["encoding_a"]["spike_count"] += 1
        findings = result_findings(item)
        self.assertTrue(
            any("spike_count does not match the recomputed encode" in f for f in findings),
            findings,
        )

