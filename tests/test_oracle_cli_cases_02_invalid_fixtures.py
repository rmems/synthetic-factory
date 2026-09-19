"""Focused cases split from test_oracle_grounded_cli.py."""

from test_oracle_grounded_cli import (
    GOLDEN,
    INVALID,
    VALIDATE,
    defect_pairs,
    families,
    json,
    record,
    run_cli,
    unittest,
)


class InvalidFixturesCase02(unittest.TestCase):
    def test_every_malformed_generator_record_is_rejected(self):
        pairs = defect_pairs("malformed-generator")
        self.assertGreaterEqual(len(pairs), 7)
        for defect, item in pairs:
            with self.subTest(defect=defect):
                self.assertTrue(
                    record.validate_record(item),
                    f"{defect} was accepted",
                )


class InvalidFixturesCase03(unittest.TestCase):
    def test_each_defect_is_caught_for_the_stated_reason(self):
        expected = {
            "missing_result": "$.result",
            "result_not_attributed_to_declared_oracle": "produced_by",
            "result_hash_does_not_cover_result": "result_hash",
            "oracle_commit_unknown": "commit",
            "oracle_module_digest_missing": "module_digest",
            "publishable_reason_claims_the_named_runtime": "publishable_reason",
            "empty_measurement": "measured",
            "no_executed_stages": "stages",
            "reference_run_relabelled_as_named_runtime": "named runtime",
            "generator_authored_a_measurement_key": "oracle-reserved keys",
            "scenario_edited_after_proposal_hash": "proposal_hash",
            "generator_claims_authority": "authoritative",
            "candidate_prediction_posing_as_ground_truth": "non_authoritative_guess",
            "empty_scenario": "$.scenario",
            "failing_record_relabelled_accepted": "recomputed status",
            "rejection_reason_rewritten": "do not match the recomputed findings",
        }
        seen = set()
        for name in ("invalid-oracle", "malformed-generator"):
            for defect, item in defect_pairs(name):
                seen.add(defect)
                findings = " | ".join(record.validate_record(item))
                with self.subTest(defect=defect):
                    self.assertIn(expected[defect], findings)
        self.assertEqual(seen, set(expected))


class InvalidFixturesCase04(unittest.TestCase):
    def test_the_validator_cli_fails_on_the_invalid_fixtures(self):
        completed = run_cli(VALIDATE, INVALID)
        self.assertEqual(completed.returncode, 1)
        report = json.loads(completed.stdout)
        self.assertEqual(report["records"], 0)
        self.assertFalse(report["manifest_valid"])
        self.assertIn("required run manifest is missing", completed.stderr)


class ValidateCliCase01(unittest.TestCase):
    def test_the_golden_run_validates_clean(self):
        completed = run_cli(VALIDATE, GOLDEN)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual(report["invalid"], 0)
        self.assertEqual(report["parse_failures"], 0)
        self.assertEqual(report["records"], report["accepted"] + report["rejected"])
        # Historical fixture replay is deterministic diagnostic evidence;
        # unresolved checkout provenance never grants publication authority.
        self.assertEqual(report["publishable"], 0)
        self.assertEqual(report["named_runtime"], 0)
        self.assertEqual(report["mixed_oracle"], 0)
        self.assertEqual(report["reference_oracle"], report["records"])
        self.assertEqual(sorted(report["by_family"]), sorted(families.FAMILY_NAMES))


class ValidateCliCase02(unittest.TestCase):
    def test_reproduce_re_runs_every_oracle(self):
        completed = run_cli(VALIDATE, "--reproduce", GOLDEN)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual(report["reproduce"], {"reproduced": report["records"]})


class ValidateCliCase03(unittest.TestCase):
    def test_a_family_filter_narrows_the_run(self):
        completed = run_cli(VALIDATE, "--family", families.MESH_FAMILY, GOLDEN)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual(list(report["by_family"]), [families.MESH_FAMILY])
        self.assertGreater(report["skipped"], 0)
