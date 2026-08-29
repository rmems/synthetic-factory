#!/usr/bin/env python3
"""In-process tests for oracle_validate's run-level decision logic.

The end-to-end suite drives ``oracle_validate.py`` as a subprocess, which
proves the CLI contract but leaves the run-level reasoning
(``_manifest_metadata_errors``, ``validate_run``, ``main``) unmeasured. These
tests call the same code in process against the committed golden run, so every
manifest-binding rule is exercised against real snapshots and real parsed
records rather than a hand-built stub.

Each metadata test mutates one field of a deep copy of the golden manifest and
asserts the specific finding that mutation must produce. The golden run itself
must validate with no findings at all, which pins the accept path.
"""

import copy
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

import oracle_validate  # noqa: E402

GOLDEN = REPO / "tests" / "fixtures" / "oracle-grounded" / "golden-r01"


def _load_golden():
    """Authenticate and parse the golden run once for the whole module."""
    manifest, snapshots, errors = oracle_validate.authenticate_manifest(GOLDEN)
    if errors:
        raise AssertionError(f"golden run failed authentication: {errors}")
    records = []
    seen_ids = {}
    for snapshot in snapshots:
        _totals, _errors, parsed = oracle_validate.validate_file(
            snapshot, False, False, set(), seen_ids=seen_ids
        )
        records.extend(parsed)
    return manifest, snapshots, records


class GoldenRunFixture(unittest.TestCase):
    """Shared golden-run inputs for the run-level checks."""

    @classmethod
    def setUpClass(cls):
        cls.manifest, cls.snapshots, cls.records = _load_golden()

    def metadata_errors(self, mutate=None):
        manifest = copy.deepcopy(self.manifest)
        if mutate is not None:
            mutate(manifest)
        return oracle_validate._manifest_metadata_errors(
            manifest, self.snapshots, self.records, GOLDEN
        )

    def assert_reports(self, mutate, fragment):
        errors = self.metadata_errors(mutate)
        matched = [error for error in errors if fragment in error]
        self.assertTrue(matched, f"expected a finding containing {fragment!r}, got {errors}")


class ManifestMetadataAcceptTest(GoldenRunFixture):
    """The committed golden run must bind cleanly to its manifest."""

    def test_golden_manifest_metadata_has_no_findings(self):
        self.assertEqual(self.metadata_errors(), [])

    def test_golden_run_parses_every_declared_file(self):
        self.assertEqual(len(self.snapshots), 10)
        self.assertEqual(len(self.records), 20)


class ManifestHeaderFieldTest(GoldenRunFixture):
    """Scalar manifest header fields are range- and type-checked."""

    def test_round_below_range_is_rejected(self):
        self.assert_reports(lambda m: m.__setitem__("round", 0), "round must be an integer")

    def test_round_above_range_is_rejected(self):
        self.assert_reports(
            lambda m: m.__setitem__("round", oracle_validate.MAX_ROUND + 1),
            "round must be an integer",
        )

    def test_non_integer_seed_is_rejected(self):
        self.assert_reports(lambda m: m.__setitem__("seed", "seed"), "seed must be an integer")

    def test_boolean_seed_is_rejected(self):
        self.assert_reports(lambda m: m.__setitem__("seed", True), "seed must be an integer")

    def test_zero_count_per_family_is_rejected(self):
        self.assert_reports(
            lambda m: m.__setitem__("count_per_family", 0),
            "count_per_family must be an integer",
        )

    def test_unresolvable_oracle_commit_is_rejected(self):
        self.assert_reports(
            lambda m: m.__setitem__("oracle_commit", "0" * 40),
            "oracle_commit does not resolve",
        )

    def test_malformed_oracle_commit_is_rejected(self):
        self.assert_reports(
            lambda m: m.__setitem__("oracle_commit", "not-a-commit"),
            "oracle_commit must be a resolved lowercase",
        )

    def test_non_boolean_oracle_dirty_is_rejected(self):
        self.assert_reports(
            lambda m: m.__setitem__("oracle_dirty", "yes"),
            "oracle_dirty must be boolean or null",
        )

    def test_non_digest_module_digest_is_rejected(self):
        self.assert_reports(
            lambda m: m.__setitem__("module_digest", "nope"),
            "module_digest must be a sha256 digest",
        )


class ManifestFamiliesTest(GoldenRunFixture):
    """The declared families block must match the captured directories."""

    def test_non_object_families_is_rejected(self):
        self.assert_reports(lambda m: m.__setitem__("families", []), "families must be an object")

    def test_empty_families_is_rejected(self):
        self.assert_reports(
            lambda m: m.__setitem__("families", {}),
            "families must declare at least one family",
        )

    def test_family_key_mismatch_is_rejected(self):
        def mutate(manifest):
            manifest["families"]["not-a-real-family"] = {}

        self.assert_reports(mutate, "families keys do not match captured family directories")

    def test_altered_family_summary_is_rejected(self):
        def mutate(manifest):
            family = sorted(manifest["families"])[0]
            manifest["families"][family]["proposed"] = 999

        self.assert_reports(mutate, "do not match the captured records")

    def test_round_mismatch_against_captured_files_is_rejected(self):
        self.assert_reports(lambda m: m.__setitem__("round", 2), "does not match manifest round")


class ManifestAvailabilityTest(GoldenRunFixture):
    """oracle_availability must agree with the probes captured in records."""

    def test_non_object_availability_is_rejected(self):
        self.assert_reports(
            lambda m: m.__setitem__("oracle_availability", "none"),
            "oracle_availability must be an object",
        )

    def test_wrong_protocol_is_rejected(self):
        self.assert_reports(
            lambda m: m["oracle_availability"].__setitem__("protocol", "bogus"),
            "oracle_availability is malformed",
        )

    def test_runtime_set_mismatch_is_rejected(self):
        def mutate(manifest):
            manifest["oracle_availability"]["runtimes"] = []

        self.assert_reports(mutate, "oracle_availability runtimes do not match families")

    def test_non_string_runtime_name_is_rejected(self):
        def mutate(manifest):
            manifest["oracle_availability"]["runtimes"][0]["runtime"] = 7

        self.assert_reports(mutate, "runtime names must be strings")

    def test_all_bound_disagreement_is_rejected(self):
        def mutate(manifest):
            availability = manifest["oracle_availability"]
            availability["all_bound"] = not availability.get("all_bound")

        self.assert_reports(mutate, "oracle_availability.all_bound disagrees")

    def test_unbound_disagreement_is_rejected(self):
        def mutate(manifest):
            manifest["oracle_availability"]["unbound"] = ["invented-runtime"]

        self.assert_reports(mutate, "oracle_availability.unbound disagrees")


class ValidateRunTest(unittest.TestCase):
    """validate_run aggregates per-file totals into the run report."""

    def test_golden_run_reports_no_errors(self):
        report, errors = oracle_validate.validate_run(GOLDEN)
        self.assertEqual(errors, [])
        self.assertTrue(report["manifest_valid"])

    def test_golden_run_totals(self):
        report, _errors = oracle_validate.validate_run(GOLDEN)
        self.assertEqual(report["files"], 10)
        self.assertEqual(report["records"], 20)
        self.assertEqual(report["accepted"] + report["rejected"], 20)
        self.assertEqual(report["parse_failures"], 0)

    def test_by_family_counts_cover_every_family(self):
        report, _errors = oracle_validate.validate_run(GOLDEN)
        self.assertEqual(sum(report["by_family"].values()), report["records"])
        self.assertEqual(len(report["by_family"]), 5)

    def test_reproduce_adds_a_reproduce_block(self):
        report, _errors = oracle_validate.validate_run(GOLDEN, reproduce=True)
        self.assertIn("reproduce", report)

    def test_report_omits_reproduce_block_by_default(self):
        report, _errors = oracle_validate.validate_run(GOLDEN)
        self.assertNotIn("reproduce", report)

    def test_family_filter_restricts_counted_records(self):
        report, _errors = oracle_validate.validate_run(
            GOLDEN, selected={"neuron-dynamics-counterfactuals"}
        )
        self.assertEqual(list(report["by_family"]), ["neuron-dynamics-counterfactuals"])
        self.assertGreater(report["skipped"], 0)

    def test_metadata_exception_is_contained_as_a_finding(self):
        boom = mock.patch.object(
            oracle_validate,
            "_manifest_metadata_errors",
            side_effect=RuntimeError("boom"),
        )
        with boom:
            report, errors = oracle_validate.validate_run(GOLDEN)
        self.assertFalse(report["manifest_valid"])
        self.assertTrue(any("raised an internal exception: RuntimeError" in e for e in errors))


class MainExitCodeTest(unittest.TestCase):
    """main() maps validation outcomes onto CLI exit codes."""

    def run_main(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = oracle_validate.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_missing_run_dir_is_usage_error(self):
        code, _out, err = self.run_main()
        self.assertEqual(code, 2)
        self.assertIn("a run directory is required", err)

    def test_non_directory_is_usage_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "absent"
            code, _out, err = self.run_main(str(missing))
        self.assertEqual(code, 2)
        self.assertIn("not a directory", err)

    def test_unknown_family_is_usage_error(self):
        code, _out, err = self.run_main(str(GOLDEN), "--family", "no-such-family")
        self.assertEqual(code, 2)
        self.assertIn("unknown families: no-such-family", err)

    def test_golden_run_exits_zero_and_prints_report(self):
        code, out, _err = self.run_main(str(GOLDEN))
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["records"], 20)

    def test_findings_exit_one_and_are_printed(self):
        with mock.patch.object(
            oracle_validate, "validate_run", return_value=({"records": 0}, ["first", "second"])
        ):
            code, _out, err = self.run_main(str(GOLDEN))
        self.assertEqual(code, 1)
        self.assertIn("first", err)
        self.assertIn("second", err)

    def test_findings_beyond_the_limit_are_summarised(self):
        findings = [f"finding-{index}" for index in range(5)]
        with mock.patch.object(
            oracle_validate, "validate_run", return_value=({"records": 0}, findings)
        ):
            code, _out, err = self.run_main(str(GOLDEN), "--max-findings", "2")
        self.assertEqual(code, 1)
        self.assertIn("finding-1", err)
        self.assertNotIn("finding-4", err)
        self.assertIn("... 3 more findings", err)

    def test_negative_finding_limit_hides_every_finding(self):
        with mock.patch.object(
            oracle_validate, "validate_run", return_value=({"records": 0}, ["only"])
        ):
            code, _out, err = self.run_main(str(GOLDEN), "--max-findings", "-5")
        self.assertEqual(code, 1)
        self.assertNotIn("only", err)
        self.assertIn("... 1 more findings", err)


if __name__ == "__main__":
    unittest.main()
