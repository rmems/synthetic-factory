"""Focused cases split from test_oracle_grounded_cli.py."""

from test_oracle_grounded_cli import (
    GOLDEN,
    Path,
    VALIDATE,
    build,
    canon,
    families,
    json,
    relabel_as_named_runtime,
    run_cli,
    tempfile,
    unittest,
    write_test_manifest,
)


class ValidateCliCase04(unittest.TestCase):
    def test_require_runtime_rejects_the_reference_fixture(self):
        completed = run_cli(VALIDATE, "--require-runtime", GOLDEN)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("named runtime was required", completed.stderr)


class ValidateCliCase05(unittest.TestCase):
    def test_a_malformed_line_is_reported_not_raised(self):
        with tempfile.TemporaryDirectory(prefix="oracle-bad-") as temp:
            path = Path(temp) / "family" / "accepted-r01.jsonl"
            path.parent.mkdir(parents=True)
            path.write_text('not json\n{"schema": "oracle-grounded/v1"}\n[]\n')
            write_test_manifest(temp)
            completed = run_cli(VALIDATE, temp)
            self.assertEqual(completed.returncode, 1)
            report = json.loads(completed.stdout)
            self.assertEqual(report["parse_failures"], 2)
            self.assertIn("JSON parse error", completed.stderr)


class ValidateCliCase06(unittest.TestCase):
    def test_a_record_filed_under_the_wrong_verdict_is_fatal(self):
        item = next(
            build(families.MEMORY_FAMILY, index)
            for index in range(24)
            if build(families.MEMORY_FAMILY, index)["validation"]["status"] == "rejected"
        )
        with tempfile.TemporaryDirectory(prefix="oracle-wrong-verdict-") as temp:
            path = Path(temp) / families.MEMORY_FAMILY / "accepted-r01.jsonl"
            path.parent.mkdir(parents=True)
            path.write_text(canon.dumps_record(item) + "\n")
            write_test_manifest(temp)
            completed = run_cli(VALIDATE, temp)
            self.assertEqual(completed.returncode, 1)
            self.assertIn("reserved for 'accepted' records", completed.stderr)


class ValidateCliCase07(unittest.TestCase):
    def test_requested_reproduction_fails_when_the_runtime_is_unavailable(self):
        item = relabel_as_named_runtime(build(families.ENCODER_FAMILY))
        with tempfile.TemporaryDirectory(prefix="oracle-unavailable-") as temp:
            path = Path(temp) / families.ENCODER_FAMILY / "accepted-r01.jsonl"
            path.parent.mkdir(parents=True)
            path.write_text(canon.dumps_record(item) + "\n")
            write_test_manifest(temp)
            completed = run_cli(VALIDATE, "--reproduce", temp)
            self.assertEqual(completed.returncode, 1)
            report = json.loads(completed.stdout)
            self.assertEqual(report["reproduce"], {"unavailable": 1})
            self.assertIn("reproduction was unavailable", completed.stderr)


class ValidateCliCase08(unittest.TestCase):
    def test_reproduction_failures_stay_in_their_own_bucket(self):
        # A failed reproduction still fails the run, but the record was
        # already tallied as accepted or rejected: charging "invalid" too
        # would make accepted + rejected + invalid exceed records.
        item = relabel_as_named_runtime(build(families.ENCODER_FAMILY))
        with tempfile.TemporaryDirectory(prefix="oracle-reproduce-count-") as temp:
            path = Path(temp) / families.ENCODER_FAMILY / "accepted-r01.jsonl"
            path.parent.mkdir(parents=True)
            path.write_text(canon.dumps_record(item) + "\n")
            write_test_manifest(temp)
            completed = run_cli(VALIDATE, "--reproduce", temp)
            self.assertEqual(completed.returncode, 1)
            report = json.loads(completed.stdout)
            self.assertEqual(report["reproduce"], {"unavailable": 1})
            self.assertEqual(report["invalid"], 0)
            self.assertEqual(
                report["accepted"] + report["rejected"] + report["invalid"],
                report["records"],
            )
