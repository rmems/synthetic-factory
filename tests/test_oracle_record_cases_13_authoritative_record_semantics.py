"""Focused cases split from test_oracle_grounded_record.py."""

from test_oracle_grounded_record import (
    build,
    copy,
    families,
    proposal_findings,
    result_findings,
    unittest,
)


class AuthoritativeRecordSemanticsCase15(unittest.TestCase):
    def test_every_mesh_label_and_summary_is_recomputed(self):
        item = build(families.MESH_FAMILY)
        state = item["result"]["measured"]["before"]
        mutations = {
            "source": "forged-source",
            "sink": "forged-sink",
            "firing_order": list(reversed(state["firing_order"])),
            "downstream_activation": list(reversed(state["downstream_activation"])),
            "total_spikes": state["total_spikes"] + 1,
            "energy_pJ": state["energy_pJ"] + 1,
        }
        for field, forged in mutations.items():
            candidate = build(families.MESH_FAMILY)
            candidate["result"]["measured"]["before"][field] = forged
            findings = result_findings(candidate)
            with self.subTest(field=field):
                self.assertTrue(any(field in finding for finding in findings), findings)


class AuthoritativeRecordSemanticsCase16(unittest.TestCase):
    def test_mesh_arrivals_cannot_be_shifted_outside_the_run(self):
        item = build(families.MESH_FAMILY)
        duration = item["scenario"]["duration_ms"]
        for side in ("before", "after"):
            arrivals = item["result"]["measured"][side]["first_arrival_ms"]
            for node, time_ms in list(arrivals.items()):
                if time_ms is not None:
                    arrivals[node] = time_ms + duration * 4
        findings = result_findings(item)
        self.assertTrue(any("outside the simulated duration" in f for f in findings), findings)

        boundary = build(families.MESH_FAMILY)
        arrivals = boundary["result"]["measured"]["before"]["first_arrival_ms"]
        node = next(node for node, time_ms in arrivals.items() if time_ms is not None)
        arrivals[node] = duration
        findings = result_findings(boundary)
        self.assertTrue(any("outside the simulated duration" in f for f in findings), findings)

        expected_delta = item["result"]["measured"]["delta"]
        for field, value in expected_delta.items():
            candidate = build(families.MESH_FAMILY)
            delta = candidate["result"]["measured"]["delta"]
            if isinstance(value, bool):
                delta[field] = not value
            elif isinstance(value, list):
                delta[field] = value + ["forged-node"]
            else:
                delta[field] = 123.0 if value is None else value + 123.0
            findings = result_findings(candidate)
            with self.subTest(delta=field):
                self.assertTrue(any(field in finding for finding in findings), findings)


class AuthoritativeRecordSemanticsCase17(unittest.TestCase):
    def test_credit_labels_vectors_and_behavior_summaries_are_recomputed(self):
        item = build(families.CREDIT_FAMILY)
        plasticity = item["result"]["measured"]["plasticity"]
        plasticity["weights_before"][0] += 0.25
        findings = result_findings(item)
        self.assertTrue(any("weights_before" in f for f in findings), findings)

        item = build(families.CREDIT_FAMILY)
        item["result"]["measured"]["plasticity"]["eligibility"].pop()
        findings = result_findings(item)
        self.assertTrue(any("inconsistent lengths" in f for f in findings), findings)

        for field in ("spike_count", "first_spike_ms", "output_rate_hz"):
            item = build(families.CREDIT_FAMILY)
            behavior = item["result"]["measured"]["plasticity"]["pre_update_behavior"]
            behavior[field] = 0.25 if behavior[field] is None else behavior[field] + 1
            findings = result_findings(item)
            with self.subTest(behavior=field):
                self.assertTrue(any(field in finding for finding in findings), findings)

        item = build(families.CREDIT_FAMILY)
        item["result"]["measured"]["plasticity"]["modulatory_gain"] += 0.5
        findings = result_findings(item)
        self.assertTrue(any("modulatory_gain" in f for f in findings), findings)

        item = build(families.CREDIT_FAMILY)
        item["result"]["measured"]["plasticity"]["update_rule"] = "trust me"
        findings = result_findings(item)
        self.assertTrue(any("update_rule" in f for f in findings), findings)

        item = build(families.CREDIT_FAMILY)
        critic = item["result"]["measured"]["critic"]
        critic["valence"] = "negative" if critic["valence"] != "negative" else "positive"
        findings = result_findings(item)
        self.assertTrue(any("critic.valence" in f for f in findings), findings)


class AuthoritativeRecordSemanticsCase18(unittest.TestCase):
    def test_temporal_controls_and_all_derivable_summaries_are_recomputed(self):
        item = next(
            build(families.MEMORY_FAMILY, index)
            for index in range(24)
            if build(families.MEMORY_FAMILY, index)["scenario"]["distractor_ms"]
        )
        scenario_mutations = {
            "delay_ms": item["scenario"]["delay_ms"] + 1,
            "distractor_count": item["scenario"]["distractor_count"] + 1,
            "event_sparsity": item["scenario"]["event_sparsity"] + 1,
        }
        for field, forged in scenario_mutations.items():
            candidate = copy.deepcopy(item)
            candidate["scenario"][field] = forged
            findings = proposal_findings(candidate)
            with self.subTest(scenario=field):
                self.assertTrue(
                    any(
                        field in finding or "generator.seed does not reproduce" in finding
                        for finding in findings
                    ),
                    findings,
                )

        trial_mutations = {
            "state_retained_at_probe": not item["result"]["measured"]["baseline"][
                "state_retained_at_probe"
            ],
            "energy_pJ": item["result"]["measured"]["baseline"]["energy_pJ"] + 1,
            "duration_ms": item["result"]["measured"]["baseline"]["duration_ms"] + 1,
        }
        for field, forged in trial_mutations.items():
            candidate = copy.deepcopy(item)
            candidate["result"]["measured"]["baseline"][field] = forged
            findings = result_findings(candidate)
            with self.subTest(trial=field):
                self.assertTrue(any(field in finding for finding in findings), findings)

        candidate = copy.deepcopy(item)
        candidate["result"]["measured"]["delay_ms"] += 1
        findings = result_findings(candidate)
        self.assertTrue(any("measured.delay_ms" in f for f in findings), findings)

        candidate = copy.deepcopy(item)
        invariant = candidate["result"]["measured"]["distractor_invariant"]
        candidate["result"]["measured"]["distractor_invariant"] = not invariant
        findings = result_findings(candidate)
        self.assertTrue(any("distractor_invariant" in f for f in findings), findings)

        candidate = copy.deepcopy(item)
        del candidate["result"]["measured"]["probes"]["distractor_swap"]
        findings = result_findings(candidate)
        self.assertTrue(any("control probes" in f for f in findings), findings)

