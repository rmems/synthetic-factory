"""Cross-runtime comparison and record generation for nir_equivalence."""

import copy
import json
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import nir_equivalence_support  # noqa: E402,F401

import nir_equivalence as nir  # noqa: E402
import oracle_contract as contract  # noqa: E402

class Comparison(unittest.TestCase):
    def test_convention_delta_lists_only_differences(self):
        scenario = nir.build_scenario(nir.GRAPH_SPECS[0], steps=4)
        entries = [
            nir.execute_runtime(runtime, scenario) for runtime in nir.IN_REPO_RUNTIMES
        ]
        delta = {item["convention"] for item in nir.convention_delta(entries)}
        self.assertEqual(delta, {"reset", "delay_unit", "cycle_break_order"})

    def test_attribution_only_names_conventions_the_graph_exercises(self):
        for spec in nir.GRAPH_SPECS:
            scenario = nir.build_scenario(spec, steps=10)
            entries = [
                nir.execute_runtime(runtime, scenario)
                for runtime in (*nir.IN_REPO_RUNTIMES, *nir.UPSTREAM_RUNTIMES)
            ]
            comparison = nir.compare_runtimes(scenario, entries)
            relevant = set(comparison["attribution"]["relevant_conventions"])
            types = {node["type"] for node in scenario["graph"]["nodes"].values()}
            with self.subTest(graph=spec["id"]):
                if "Delay" not in types:
                    self.assertNotIn("delay_unit", relevant)
                if not types & {"LIF", "IF"}:
                    self.assertNotIn("reset", relevant)

    def test_internal_state_divergence_does_not_flip_the_verdict(self):
        # Event outputs can agree while membrane state has already drifted.
        records = nir.generate_records(round_number=1, steps=10)
        drifted = [
            record
            for record in records
            if "DIVERGENCE_INTERNAL_STATE" in record["result"]["reason_codes"]
            and record["result"]["verdict"] == contract.VERDICT_MATCH
        ]
        self.assertTrue(drifted, "expected at least one match with state drift")

    def test_numeric_noise_within_tolerance_does_not_require_equal_digests(self):
        scenario = nir.build_scenarios(steps=4)[0]
        first = nir.execute_runtime(nir.REFERENCE_V1, scenario)
        second = copy.deepcopy(first)
        second["runtime"] = "within_tolerance"
        second["outputs"]["output_trace"][0][0] += nir.NUMERIC_TOL / 2
        second["output_digest"] = "sha256:" + "1" * 64
        pair = nir._compare_pair(first, second)
        self.assertTrue(pair["agree"], pair)

    def test_event_streams_are_compared_exactly(self):
        scenario = nir.build_scenarios(steps=4)[0]
        first = nir.execute_runtime(nir.REFERENCE_V1, scenario)
        second = copy.deepcopy(first)
        second["runtime"] = "different_events"
        if second["outputs"]["spike_events"]:
            second["outputs"]["spike_events"][0]["t_step"] += 1
        else:
            second["outputs"]["spike_events"].append({"t_step": 0, "channel": 0})
        second["outputs"]["spike_count"] = len(second["outputs"]["spike_events"])
        pair = nir._compare_pair(first, second)
        self.assertFalse(pair["agree"])
        self.assertIn("DIVERGENCE_EVENT_STREAM", pair["reason_codes"])

    def test_fewer_than_two_executed_runtimes_is_never_a_match(self):
        comparison = {
            "executed_runtimes": ["only_one"],
            "executed_count": 1,
            "parse_write_parity": {"per_runtime": {}, "agree": True},
            "structure_parity": {"digests": {}, "agree": True},
            "output_parity": {"comparable": False, "agree": None, "pairs": []},
            "unsupported": [],
            "unavailable": [],
        }
        verdict, codes = nir.verdict_for(comparison)
        self.assertEqual(verdict, contract.VERDICT_INCONCLUSIVE)
        self.assertIn("NO_EXECUTED_RUNTIME_PAIR", codes)

    def test_unsupported_construct_yields_the_unsupported_verdict(self):
        comparison = {
            "executed_runtimes": [],
            "executed_count": 0,
            "parse_write_parity": {"per_runtime": {}, "agree": True},
            "structure_parity": {"digests": {}, "agree": True},
            "output_parity": {"comparable": False, "agree": None, "pairs": []},
            "unsupported": [{"runtime": "a", "reason_code": "UNSUPPORTED_CONSTRUCT"}],
            "unavailable": [],
        }
        verdict, codes = nir.verdict_for(comparison)
        self.assertEqual(verdict, contract.VERDICT_UNSUPPORTED)
        self.assertIn("UNSUPPORTED_CONSTRUCT", codes)


class Generation(unittest.TestCase):
    def test_generated_records_validate(self):
        records = nir.generate_records(round_number=1, steps=6)
        self.assertEqual(nir.validate_records(records), [])

    def test_generation_is_deterministic(self):
        first = nir.generate_records(round_number=1, steps=6)
        second = nir.generate_records(round_number=1, steps=6)
        self.assertEqual(json.dumps(first, sort_keys=True),
                         json.dumps(second, sort_keys=True))

    def test_catalog_covers_feed_forward_recurrent_and_unsupported(self):
        classes = {spec["class"] for spec in nir.GRAPH_SPECS}
        self.assertIn("feed_forward", classes)
        self.assertIn("recurrent", classes)
        self.assertIn("delay_sensitive", classes)
        self.assertIn("boundary", classes)
        self.assertIn("unusual_parameters", classes)
        self.assertIn("unsupported", classes)

    def test_catalog_produces_every_verdict_kind(self):
        verdicts = {
            record["result"]["verdict"]
            for record in nir.generate_records(round_number=1, steps=10)
        }
        self.assertIn(contract.VERDICT_MATCH, verdicts)
        self.assertIn(contract.VERDICT_MISMATCH, verdicts)
        self.assertIn(contract.VERDICT_UNSUPPORTED, verdicts)

    def test_evidence_scope_is_stated_on_every_record(self):
        for record in nir.generate_records(round_number=1, steps=4):
            self.assertIn("in-repo", record["oracle"]["evidence_scope"])
            self.assertIn("nir-rs", record["oracle"]["evidence_scope"])

    def test_evidence_scope_matches_the_actual_executed_count(self):
        for record in nir.generate_records(round_number=1, steps=4):
            executed = record["result"]["comparison"]["executed_count"]
            scope = record["oracle"]["evidence_scope"]
            with self.subTest(record=record["id"], executed=executed):
                if executed >= 2:
                    self.assertIn("executed in-repo runtimes", scope)
                elif executed == 1:
                    self.assertIn("only one in-repo runtime executed", scope)
                else:
                    self.assertIn("no in-repo runtime executed", scope)



if __name__ == "__main__":
    unittest.main()
